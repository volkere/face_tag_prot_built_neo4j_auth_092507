
import io, json, tempfile
from typing import List, Dict, Any, Optional
import streamlit as st
import numpy as np
from PIL import Image
import cv2
import pandas as pd
import sys
import os
import pickle
import joblib

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.face_recognizer import FaceEngine, GalleryDB
from app.location import extract_exif_gps, reverse_geocode, extract_comprehensive_metadata, get_location_details
from streamlit_styles import apply_custom_css

# Wende kleinere Schriftgrößen an
apply_custom_css()

# Neue Annotation-Features - verwende eingebaute Streamlit-Funktionen

# Versuche Enhanced Face Engine zu importieren
try:
    from app.enhanced_face_engine import EnhancedFaceEngine
    ENHANCED_ENGINE_AVAILABLE = True
except ImportError:
    ENHANCED_ENGINE_AVAILABLE = False

st.title("Annotate: Fotos analysieren")
st.caption("Erweiterte Gesichtserkennung, Metadaten-Extraktion und Standortanalyse")

# Benutzerführung
with st.expander("Anleitung", expanded=False):
    st.markdown("""
    **So verwenden Sie diese Seite:**
    
    1. **Bilder hochladen**: Wählen Sie Bilder in der Sidebar aus
    2. **Einstellungen anpassen**: Konfigurieren Sie die Erkennungsparameter
    3. **Verarbeitung**: Die App analysiert automatisch alle Bilder
    4. **Download**: Nach der Verarbeitung erscheint ein Download-Button am Ende
    5. **Analyse**: Laden Sie die JSON-Datei in der 'Analyze'-Seite hoch
    
    **Tipp**: Der Download-Button erscheint erst nach der Verarbeitung aller Bilder!
    """)

with st.sidebar:
    st.header("Einstellungen")
    
    # Gesichtserkennung
    st.subheader("Gesichtserkennung")
    det = st.slider("Detector size", 320, 1024, 640, 64, key="det_annot")
    threshold = st.slider("Identity threshold (cosine)", 0.3, 0.9, 0.55, 0.01)
    
    # Metadaten
    st.subheader("Metadaten")
    extract_full_metadata = st.checkbox("Vollständige EXIF-Metadaten extrahieren", value=True)
    do_reverse = st.checkbox("Reverse geocode GPS (Internet)", value=False)
    show_location_details = st.checkbox("Detaillierte Standortinfos", value=False)
    
    # Qualitätsfilter
    st.subheader("Qualitätsfilter")
    min_quality = st.slider("Min. Gesichtsqualität", 0.0, 1.0, 0.3, 0.05)
    min_face_size = st.slider("Min. Gesichtsgröße (Pixel)", 50, 200, 80, 10)
    
    # Erweiterte Erkennungsparameter
    st.subheader("Erweiterte Erkennung")
    enable_pose_analysis = st.checkbox("Pose-Analyse aktivieren", value=True)
    enable_symmetry_check = st.checkbox("Symmetrie-Prüfung aktivieren", value=True)
    enable_noise_analysis = st.checkbox("Rausch-Analyse aktivieren", value=True)
    
    # Enhanced Model Upload
    st.subheader("Enhanced Model")
    enhanced_model_file = st.file_uploader("Enhanced Model (.pkl)", type=["pkl"], key="enhanced_model_upload", help="Laden Sie ein trainiertes Enhanced Model hoch für bessere Metadaten-Integration")
    use_enhanced_model = st.checkbox("Enhanced Recognition aktivieren", value=False, help="Verwendet das hochgeladene Enhanced Model für verbesserte Erkennung")
    
    # Datei-Upload
    st.subheader("Dateien")
    gallery_file = st.file_uploader("Embeddings DB (embeddings.pkl)", type=["pkl"], key="db_upload")
    training_identity_file = st.file_uploader(
        "Trainings-Identitäten (JSON/PKL)",
        type=["json", "pkl"],
        key="training_identity_upload",
        help="Laden Sie hier die Trainingsdaten oder das Modell hoch, das auf der Train-Seite erzeugt wurde."
    )
    files = st.file_uploader("Bilder hochladen", type=["jpg","jpeg","png","bmp","webp","tif","tiff"], accept_multiple_files=True)
    
    # Neue Annotation-Features Info
    st.divider()
    st.subheader("Neue Features")
    st.info("""
    **Interaktive Annotation-Bearbeitung**: 
    Nach der Verarbeitung können Sie alle Annotationen direkt in der Tabelle bearbeiten!
    
    **Farbige Metadaten**: 
    Metadaten werden jetzt mit farbigen Hervorhebungen angezeigt.
    """)

if "engine_annot" not in st.session_state or st.session_state.get("det_annot_state") != det:
    st.session_state["engine_annot"] = FaceEngine(det_size=(det, det))
    st.session_state["det_annot_state"] = det

TRAINING_EMBEDDING_KEYS = ["embedding", "face_embedding", "vector", "face_vector"]
TRAINING_NAME_KEYS = ["identifier", "person_identifier", "name", "label", "person_label"]


def merge_gallery_databases(target: GalleryDB, source: GalleryDB):
    """Fügt alle Personen aus source in target ein."""
    for name, embeddings in source.people.items():
        for emb in embeddings:
            target.add(name, emb)
        if name in source.face_metadata:
            target.face_metadata.setdefault(name, []).extend(source.face_metadata[name])


def _extract_person_name(person: Dict[str, Any]) -> Optional[str]:
    for key in TRAINING_NAME_KEYS:
        value = person.get(key)
        if value:
            return value
    nested = person.get("person")
    if isinstance(nested, dict):
        for key in TRAINING_NAME_KEYS:
            value = nested.get(key)
            if value:
                return value
    return None


def _extract_person_embedding(person: Dict[str, Any]) -> Optional[np.ndarray]:
    for key in TRAINING_EMBEDDING_KEYS:
        if key in person and person[key] is not None:
            try:
                emb_array = np.array(person[key], dtype=np.float32)
                if emb_array.ndim == 1:
                    return emb_array
            except Exception:
                continue
    nested = person.get("person")
    if isinstance(nested, dict):
        for key in TRAINING_EMBEDDING_KEYS:
            if key in nested and nested[key] is not None:
                try:
                    emb_array = np.array(nested[key], dtype=np.float32)
                    if emb_array.ndim == 1:
                        return emb_array
                except Exception:
                    continue
    return None


def build_gallery_from_training_json(data: Any) -> Optional[GalleryDB]:
    """Baut eine GalleryDB aus den Trainingsdaten (JSON) auf."""
    if data is None:
        return None
    records = []
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        if "entries" in data and isinstance(data["entries"], list):
            records = data["entries"]
        elif "regions" in data and isinstance(data["regions"], list):
            records = data["regions"]
        else:
            records = [data]
    else:
        return None

    gallery = GalleryDB()
    added = 0
    for record in records:
        persons = record.get("persons") or record.get("regions") or []
        if isinstance(persons, dict):
            persons = [persons]
        for person in persons:
            name = _extract_person_name(person)
            embedding = _extract_person_embedding(person)
            if name and embedding is not None:
                gallery.add(name, embedding)
                added += 1
    return gallery if added > 0 else None


def build_gallery_from_training_pickle(data: Any) -> Optional[GalleryDB]:
    """Baut eine GalleryDB aus einer Pickle-Datei auf."""
    if data is None:
        return None

    gallery = GalleryDB()
    added = 0

    if isinstance(data, GalleryDB):
        return data

    if isinstance(data, dict):
        # Direkte Gallery-Struktur
        if "people" in data:
            for name, embeddings in data.get("people", {}).items():
                for emb in embeddings:
                    try:
                        gallery.add(name, np.array(emb, dtype=np.float32))
                        added += 1
                    except Exception:
                        continue
            if added > 0:
                if "metadata" in data:
                    gallery.face_metadata = data.get("metadata", {})
                return gallery

        # Trainingsdatensatz innerhalb eines Dicts
        if "training_data" in data and isinstance(data["training_data"], (list, dict)):
            return build_gallery_from_training_json(data["training_data"])

        # Allgemeine Daten (z.B. Ergebnisse aus convert_to_training_format)
        gallery_from_json = build_gallery_from_training_json(data)
        if gallery_from_json:
            return gallery_from_json

    return gallery if added > 0 else None


def load_training_identity_file(uploaded_file) -> Optional[GalleryDB]:
    """Lädt Trainings-Identitäten aus JSON oder PKL-Dateien."""
    if uploaded_file is None:
        return None

    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    try:
        if file_ext == ".json":
            uploaded_file.seek(0)
            try:
                data = json.load(uploaded_file)
                return build_gallery_from_training_json(data)
            except json.JSONDecodeError as e:
                st.error(f"Fehler beim Laden der JSON-Datei: Ungültiges JSON-Format. {e}")
                return None
        elif file_ext == ".pkl":
            uploaded_file.seek(0)
            raw_bytes = uploaded_file.read()
            
            # Prüfe ob Datei leer ist
            if len(raw_bytes) == 0:
                st.error("Die PKL-Datei ist leer.")
                return None
            
            # Prüfe ob es ein gültiges Pickle-Format ist
            try:
                # Versuche zuerst mit joblib (für scikit-learn Modelle)
                bio = io.BytesIO(raw_bytes)
                try:
                    data = joblib.load(bio)
                    
                    # Prüfe ob es ein Enhanced Model ist (enthält trainierte Modelle, keine Embeddings)
                    if isinstance(data, dict):
                        # Enhanced Model erkennt man an den Schlüsseln: age_model, gender_model, quality_model
                        if any(key in data for key in ['age_model', 'gender_model', 'quality_model']):
                            st.error("❌ Diese Datei ist ein Enhanced Model (trainierte KI-Modelle), keine Trainings-Identitäten!")
                            st.info("""
                            **Unterschied:**
                            - **Enhanced Model**: Enthält trainierte Modelle für bessere Metadaten-Integration
                              → Laden Sie diese unter "Enhanced Model" in der Sidebar hoch
                            - **Trainings-Identitäten**: Enthält Person-Embeddings für Gesichtserkennung
                              → Laden Sie diese hier unter "Trainings-Identitäten" hoch
                            
                            **Richtige Dateien für Trainings-Identitäten:**
                            - `embeddings.pkl` aus der Enroll-Seite
                            - Konvertierte JSON/PKL-Dateien aus dem PBF-DAMS Export (mit Person-Namen und Embeddings)
                            """)
                            return None
                    
                    # Versuche als Trainings-Identitäten zu laden
                    gallery = build_gallery_from_training_pickle(data)
                    if gallery and len(gallery.people) > 0:
                        return gallery
                    else:
                        st.warning("Die PKL-Datei konnte geladen werden, enthält aber keine Person-Embeddings.")
                        st.info("Möglicherweise ist dies ein Enhanced Model. Laden Sie es stattdessen unter 'Enhanced Model' hoch.")
                        return None
                        
                except Exception as joblib_error:
                    # joblib hat fehlgeschlagen, versuche pickle
                    bio.seek(0)
                    try:
                        data = pickle.loads(raw_bytes)
                        gallery = build_gallery_from_training_pickle(data)
                        if gallery and len(gallery.people) > 0:
                            return gallery
                        else:
                            st.warning("Die PKL-Datei konnte geladen werden, enthält aber keine Person-Embeddings.")
                            return None
                    except (pickle.UnpicklingError, EOFError) as pickle_error:
                        # Beide Methoden haben fehlgeschlagen
                        st.error(f"Fehler beim Laden der PKL-Datei: Die Datei ist kein gültiges Pickle- oder Joblib-Format.")
                        st.error(f"Joblib-Fehler: {joblib_error}")
                        st.error(f"Pickle-Fehler: {pickle_error}")
                        st.info("""
                        **Mögliche Ursachen:**
                        1. Die Datei ist beschädigt
                        2. Die Datei ist ein Enhanced Model (laden Sie es unter 'Enhanced Model' hoch)
                        3. Die Datei hat ein anderes Format
                        
                        **Erwartete Dateien für Trainings-Identitäten:**
                        - `embeddings.pkl` aus der Enroll-Seite
                        - Konvertierte JSON/PKL-Dateien mit Person-Namen und Embeddings
                        """)
                        return None
                        
            except Exception as e:
                st.error(f"Unerwarteter Fehler beim Laden der PKL-Datei: {e}")
                import traceback
                st.code(traceback.format_exc())
                return None
        else:
            st.warning(f"Unbekanntes Dateiformat: {file_ext}. Erwartet: .json oder .pkl")
            return None
    except Exception as exc:
        st.error(f"Trainings-Identitäten konnten nicht geladen werden: {exc}")
        st.info("Bitte prüfen Sie, ob die Datei das richtige Format hat (JSON oder PKL).")
    finally:
        uploaded_file.seek(0)
    return None

db = None
if gallery_file is not None:
    try:
        db = GalleryDB()
        
        # Prüfe Dateityp durch Lesen der ersten Bytes
        gallery_file.seek(0)
        first_bytes = gallery_file.read(10)
        gallery_file.seek(0)
        
        # Prüfe ob es ein Pickle-Format ist (Pickle beginnt typischerweise mit bestimmten Bytes)
        is_pickle = False
        if len(first_bytes) > 0:
            # Pickle-Format erkennt man an bestimmten Start-Bytes
            # Protocol 0-3: beginnt mit bestimmten Bytes, Protocol 4+: beginnt mit \x80
            pickle_markers = [b'\x80', b'c', b'(', b'q', b'\x05']  # Häufige Pickle-Start-Bytes
            if first_bytes[0:1] in [b'\x80'] or (len(first_bytes) > 1 and first_bytes[0:2] in [b'c\x00', b'(q']):
                is_pickle = True
            # Prüfe auch auf JSON (beginnt mit { oder [)
            elif first_bytes[0:1] in [b'{', b'[']:
                is_pickle = False
            else:
                # Versuche es als Pickle
                is_pickle = True
        
        if is_pickle:
            # Versuche zuerst mit joblib (für komprimierte/scikit-learn Dateien)
            try:
                gallery_file.seek(0)
                data = joblib.load(gallery_file)
                
                # Prüfe ob es ein Enhanced Model ist
                if isinstance(data, dict) and any(key in data for key in ['age_model', 'gender_model', 'quality_model']):
                    st.error("❌ Diese Datei ist ein Enhanced Model (trainierte KI-Modelle), keine Embeddings!")
                    st.info("""
                    **Laden Sie Enhanced Models hier hoch:**
                    → In der Sidebar unter "Enhanced Model" (nicht unter "Embeddings")
                    
                    **Für Embeddings verwenden Sie:**
                    - `embeddings.pkl` aus der Enroll-Seite
                    """)
                    db = None
                else:
                    # Versuche als Embeddings zu verarbeiten
                    if isinstance(data, dict):
                        db.people = data.get('people', {})
                        db.face_metadata = data.get('metadata', {})
                    else:
                        db.people = data
                        
            except Exception as joblib_error:
                # joblib hat fehlgeschlagen, versuche pickle
                gallery_file.seek(0)
                try:
                    data = pickle.load(gallery_file)
                    
                    # Prüfe ob es ein Enhanced Model ist
                    if isinstance(data, dict) and any(key in data for key in ['age_model', 'gender_model', 'quality_model']):
                        st.error("❌ Diese Datei ist ein Enhanced Model (trainierte KI-Modelle), keine Embeddings!")
                        st.info("Laden Sie Enhanced Models in der Sidebar unter 'Enhanced Model' hoch (nicht unter 'Embeddings').")
                        db = None
                    else:
                        # Versuche als Embeddings zu verarbeiten
                        if isinstance(data, dict):
                            db.people = data.get('people', {})
                            db.face_metadata = data.get('metadata', {})
                        else:
                            db.people = data
                            
                except (pickle.UnpicklingError, EOFError, ValueError) as e:
                    # Falls Pickle fehlschlägt, versuche als JSON
                    gallery_file.seek(0)
                    try:
                        content = gallery_file.read().decode('utf-8')
                        data = json.loads(content)
                        is_pickle = False
                        
                        # Als Embeddings verarbeiten
                        if isinstance(data, dict):
                            db.people = data.get('people', {})
                            db.face_metadata = data.get('metadata', {})
                        else:
                            db.people = data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        raise ValueError(f"Datei ist weder ein gültiges Pickle- noch JSON-Format. Fehler: {e}")
        else:
            # Versuche als JSON zu laden
            gallery_file.seek(0)
            content = gallery_file.read().decode('utf-8')
            data = json.loads(content)
            
            # Als Embeddings verarbeiten
            if isinstance(data, dict):
                db.people = data.get('people', {})
                db.face_metadata = data.get('metadata', {})
            else:
                db.people = data
        
        # Prüfe ob Embeddings gefunden wurden
        if db and len(db.people) > 0:
            st.success(f"Embeddings geladen: {len(db.people)} Personen.")
        elif db:
            st.warning("Embeddings-Datei geladen, aber keine Personen gefunden.")
            st.info("Möglicherweise ist dies ein Enhanced Model. Laden Sie es stattdessen unter 'Enhanced Model' hoch.")
            
    except json.JSONDecodeError as e:
        st.error(f"Fehler beim Laden der Embeddings: Die Datei ist kein gültiges JSON-Format. {e}")
    except (pickle.UnpicklingError, EOFError) as e:
        st.error(f"Fehler beim Laden der Embeddings: Die Datei ist kein gültiges Pickle-Format. {e}")
        st.info("Tipp: Stellen Sie sicher, dass Sie eine .pkl-Datei aus der Enroll-Seite hochladen.")
    except Exception as e:
        st.error(f"Fehler beim Laden der Embeddings: {e}")
        st.info("Mögliche Ursachen: Datei ist beschädigt, falsches Format, oder Datei ist leer.")

if training_identity_file is not None:
    training_db = load_training_identity_file(training_identity_file)
    if training_db:
        if db is None:
            db = training_db
        else:
            merge_gallery_databases(db, training_db)
        total_identities = sum(len(v) for v in training_db.people.values())
        st.success(f"Trainings-Identitäten geladen ({len(training_db.people)} Personen / {total_identities} Embeddings).")
        st.info("Diese Personen wurden im Train-Modul gelernt und können jetzt automatisch erkannt werden.")
    else:
        st.warning("Die Trainings-Identitäten konnten nicht erkannt werden. Bitte laden Sie eine JSON- oder PKL-Datei aus dem Train-Workflow hoch.")

# Enhanced Model verarbeiten
enhanced_engine = None
if enhanced_model_file is not None and use_enhanced_model and ENHANCED_ENGINE_AVAILABLE:
    import pickle
    import tempfile
    try:
        # Temporäre Datei für das Enhanced Model erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
            tmp_file.write(enhanced_model_file.getvalue())
            tmp_path = tmp_file.name
        
        # Enhanced Engine initialisieren
        enhanced_engine = EnhancedFaceEngine()
        enhanced_engine.load_models(tmp_path)
        
        # Temporäre Datei löschen
        import os
        os.unlink(tmp_path)
        
        st.success("Enhanced Model erfolgreich geladen!")
        st.info("Das Enhanced Model wird für verbesserte Metadaten-Integration verwendet.")
        
    except Exception as e:
        st.error(f"Fehler beim Laden des Enhanced Models: {e}")
        enhanced_engine = None
elif enhanced_model_file is not None and use_enhanced_model and not ENHANCED_ENGINE_AVAILABLE:
    st.warning("Enhanced Face Engine nicht verfügbar.")
elif use_enhanced_model and enhanced_model_file is None:
    st.warning("Bitte laden Sie zuerst ein Enhanced Model hoch.")

def draw_boxes(img_bgr, persons):
    img = img_bgr.copy()
    for p in persons:
        x1,y1,x2,y2 = map(int, p["bbox"])
        
        # Einheitliche Farbe für alle Bounding Boxes
        color = (255, 255, 255)  # Weiß für alle Boxes
        
        cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
        
        # Label mit erweiterten Informationen
        label_parts = []
        
        # Name und Ähnlichkeit (prominente Anzeige)
        if p.get("name"):
            sim = f" ({p['similarity']:.2f})" if p.get("similarity") is not None else ""
            # Name wird als erstes dargestellt
            label_parts.append(f"{p['name']}{sim}")
        else:
            # Unbekannte Person
            label_parts.append("Unbekannt")
        
        # Demografie
        if p.get("gender"):
            label_parts.append(p["gender"])
        if p.get("age") is not None:
            label_parts.append(f"{p['age']}J")
        
        # Qualität mit erweiterten Metriken
        if p.get("quality_score"):
            quality = p['quality_score']
            if quality > 0.8:
                quality_label = f"Q:*{quality:.2f}"
            elif quality > 0.6:
                quality_label = f"Q:o{quality:.2f}"
            else:
                quality_label = f"Q:.{quality:.2f}"
            label_parts.append(quality_label)
        
        # Emotion
        if p.get("emotion"):
            label_parts.append(p["emotion"])
        
        # Augen/Mund Status mit Symbolen
        status_parts = []
        if p.get("eye_status"):
            eye_symbol = {"open": "E", "closed": "C", "partially_open": "P"}.get(p["eye_status"], "E")
            status_parts.append(f"{eye_symbol}{p['eye_status']}")
        if p.get("mouth_status"):
            mouth_symbol = {"open": "M", "closed": "C"}.get(p["mouth_status"], "M")
            status_parts.append(f"{mouth_symbol}{p['mouth_status']}")
        
        if status_parts:
            label_parts.append(" ".join(status_parts))
        
        # Pose-Informationen (falls verfügbar)
        if p.get("pose"):
            pose = p["pose"]
            if abs(pose.get("yaw", 0)) > 15:
                label_parts.append(f"Y{pose['yaw']:.0f}°")
            if abs(pose.get("pitch", 0)) > 15:
                label_parts.append(f"P{pose['pitch']:.0f}°")
        
        txt = " | ".join(label_parts) if label_parts else f"{p.get('prob', 1.0):.2f}"
        
        # Text-Hintergrund für bessere Lesbarkeit
        (text_width, text_height), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img, (x1, max(0,y1-text_height-8)), (x1+text_width, y1), color, -1)
        cv2.putText(img, txt, (x1, max(0,y1-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2, cv2.LINE_AA)
    
    return img

def display_metadata_card(metadata, title="Metadaten"):
    """Zeigt Metadaten in einer schönen Karte an"""
    with st.expander(f"{title}", expanded=False):
        if not metadata:
            st.info("Keine Metadaten verfügbar")
            return
        
        # Kamera-Informationen
        if any(key in metadata for key in ['camera_make', 'camera_model', 'lens']):
            st.subheader("Kamera")
            col1, col2, col3 = st.columns(3)
            with col1:
                if metadata.get('camera_make'):
                    st.metric("Hersteller", metadata['camera_make'])
            with col2:
                if metadata.get('camera_model'):
                    st.metric("Modell", metadata['camera_model'])
            with col3:
                if metadata.get('lens'):
                    st.metric("Objektiv", metadata['lens'])
        
        # Aufnahme-Einstellungen
        if any(key in metadata for key in ['focal_length', 'f_number', 'iso', 'exposure_time']):
            st.subheader("Aufnahme-Einstellungen")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if metadata.get('focal_length'):
                    st.metric("Brennweite", f"{metadata['focal_length']}mm")
            with col2:
                if metadata.get('f_number'):
                    st.metric("Blende", f"f/{metadata['f_number']}")
            with col3:
                if metadata.get('iso'):
                    st.metric("ISO", metadata['iso'])
            with col4:
                if metadata.get('exposure_time'):
                    st.metric("Belichtung", f"1/{metadata['exposure_time']}s")
        
        # Datum und Zeit
        if metadata.get('datetime'):
            st.subheader("Aufnahmezeit")
            st.info(f"**{metadata['datetime']}**")
        
        # GPS und Standort
        if metadata.get('gps'):
            st.subheader("Standort")
            gps = metadata['gps']
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Breitengrad", f"{gps['lat']:.6f}")
            with col2:
                st.metric("Längengrad", f"{gps['lon']:.6f}")
            
            if gps.get('altitude'):
                st.metric("Höhe", f"{gps['altitude']:.1f}m")
            
            if gps.get('timestamp'):
                st.info(f"GPS-Zeitstempel: {gps['timestamp']}")
        
        # Bildgröße
        if metadata.get('image_width') and metadata.get('image_height'):
            st.subheader("Bildgröße")
            st.metric("Auflösung", f"{metadata['image_width']} × {metadata['image_height']} Pixel")

def display_face_analysis(persons):
    """Zeigt detaillierte Gesichtsanalyse an"""
    if not persons:
        st.info("Keine Gesichter erkannt")
        return
    
    st.subheader("Gesichtsanalyse")
    
    for i, person in enumerate(persons):
        with st.expander(f"Person {i+1}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Basis-Informationen
                st.write("**Identifikation:**")
                if person.get("name"):
                    similarity = person.get('similarity', 0)
                    if similarity > 0.8:
                        st.success(f"{person['name']} ({similarity:.2f})")
                    elif similarity > 0.6:
                        st.warning(f"{person['name']} ({similarity:.2f})")
                    else:
                        st.info(f"? {person['name']} ({similarity:.2f})")
                else:
                    st.warning("? Unbekannte Person")
                
                # Demografie
                st.write("**Demografie:**")
                if person.get("age"):
                    age = person['age']
                    st.write(f"{age} Jahre")
                if person.get("gender"):
                    st.write(f"{person['gender']}")
            
            with col2:
                # Qualität und technische Details
                st.write("**Qualitätsbewertung:**")
                if person.get("quality_score"):
                    quality = person['quality_score']
                    if quality > 0.8:
                        st.success(f"* Exzellent ({quality:.2f})")
                    elif quality > 0.6:
                        st.warning(f"o Gut ({quality:.2f})")
                    elif quality > 0.4:
                        st.info(f". Mittel ({quality:.2f})")
                    else:
                        st.error(f"x Niedrig ({quality:.2f})")
                
                # Pose-Informationen
                if person.get("pose"):
                    pose = person["pose"]
                    st.write("**Pose:**")
                    if abs(pose.get("yaw", 0)) > 15:
                        st.write(f"Y Seitlich: {pose['yaw']:.0f}°")
                    if abs(pose.get("pitch", 0)) > 15:
                        st.write(f"P Neigung: {pose['pitch']:.0f}°")
                    if abs(pose.get("roll", 0)) > 15:
                        st.write(f"R Rotation: {pose['roll']:.0f}°")
            
            with col3:
                # Emotion und Status
                st.write("**Gesichtsausdruck:**")
                if person.get("emotion"):
                    st.write(f"{person['emotion']}")
                
                # Augen-Status
                if person.get("eye_status"):
                    eye_status = person['eye_status']
                    eye_emoji = {
                        "open": "E", "closed": "C", "partially_open": "P"
                    }.get(eye_status, "E")
                    st.write(f"{eye_emoji} Augen: {eye_status}")
                
                # Mund-Status
                if person.get("mouth_status"):
                    mouth_status = person['mouth_status']
                    mouth_emoji = {
                        "open": "M", "closed": "C"
                    }.get(mouth_status, "M")
                    st.write(f"{mouth_emoji} Mund: {mouth_status}")
            
            # Erweiterte Metriken (falls verfügbar)
            if any(key in person for key in ['landmarks', 'symmetry_score', 'noise_score']):
                with st.expander("Technische Details", expanded=False):
                    col4, col5 = st.columns(2)
                    
                    with col4:
                        if person.get("landmarks"):
                            st.write("**Landmarks:**")
                            st.write(f"Anzahl: {len(person['landmarks'])} Punkte")
                        
                        if person.get("symmetry_score"):
                            st.write(f"**Symmetrie:** {person['symmetry_score']:.2f}")
                    
                    with col5:
                        if person.get("noise_score"):
                            st.write(f"**Rauschlevel:** {person['noise_score']:.2f}")
                        
                        if person.get("pose"):
                            pose = person["pose"]
                            st.write("**Pose-Details:**")
                            st.write(f"Yaw: {pose.get('yaw', 0):.1f}°")
                            st.write(f"Pitch: {pose.get('pitch', 0):.1f}°")
                            st.write(f"Roll: {pose.get('roll', 0):.1f}°")

def display_metadata_annotated(metadata):
    """Zeigt Metadaten mit farbigen Hervorhebungen an"""
    if not metadata:
        return
    
    # Kamera-Informationen
    if metadata.get('camera_make') or metadata.get('camera_model'):
        camera_text = ""
        if metadata.get('camera_make'):
            camera_text += f"**Hersteller:** {metadata['camera_make']}"
        if metadata.get('camera_model'):
            if camera_text:
                camera_text += " | "
            camera_text += f"**Modell:** {metadata['camera_model']}"
        
        if camera_text:
            st.markdown(camera_text)
    
    # Aufnahme-Einstellungen
    if any(key in metadata for key in ['focal_length', 'f_number', 'iso', 'exposure_time']):
        settings_text = ""
        if metadata.get('focal_length'):
            settings_text += f"**Brennweite:** {metadata['focal_length']}mm"
        if metadata.get('f_number'):
            if settings_text:
                settings_text += " | "
            settings_text += f"**Blende:** f/{metadata['f_number']}"
        if metadata.get('iso'):
            if settings_text:
                settings_text += " | "
            settings_text += f"**ISO:** {metadata['iso']}"
        if metadata.get('exposure_time'):
            if settings_text:
                settings_text += " | "
            settings_text += f"**Belichtung:** 1/{metadata['exposure_time']}s"
        
        if settings_text:
            st.markdown(settings_text)
    
    # Standort
    if metadata.get('gps'):
        gps = metadata['gps']
        location_text = f"**Standort:** {gps['lat']:.4f}°N {gps['lon']:.4f}°E"
        if gps.get('altitude'):
            location_text += f" | **Höhe:** {gps['altitude']:.1f}m"
        st.markdown(location_text)

def interactive_annotation_editor(results: List[Dict]) -> List[Dict]:
    """Interaktive Annotation-Bearbeitung mit st.data_editor"""
    if not results:
        return results
    
    st.subheader("Interaktive Annotation-Bearbeitung")
    st.info("Bearbeiten Sie die Annotationen direkt in der Tabelle!")
    
    # Erstelle DataFrame mit allen Gesichtern
    faces_data = []
    for idx, result in enumerate(results):
        for person_idx, person in enumerate(result.get('persons', [])):
            faces_data.append({
                "Bild": result['image'],
                "Person ID": f"P{person_idx+1}",
                "Name": person.get('name', '') or '',
                "Alter": person.get('age') or '',
                "Geschlecht": person.get('gender', '') or '',
                "Qualität": round(person.get('quality_score', 0.0), 2) if person.get('quality_score') else 0.0,
                "Emotion": person.get('emotion', '') or '',
                "Ähnlichkeit": round(person.get('similarity', 0.0), 2) if person.get('similarity') else 0.0,
                "Notizen": '',  # Für Benutzer-Annotationen
                "Bild-Index": idx,
                "Person-Index": person_idx
            })
    
    if not faces_data:
        st.warning("Keine Gesichter zum Bearbeiten gefunden")
        return results
    
    df = pd.DataFrame(faces_data)
    
    # Interaktive Bearbeitung
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "Bild": st.column_config.TextColumn(
                "Bild-Name",
                help="Name des Bildes",
                width="medium"
            ),
            "Person ID": st.column_config.TextColumn(
                "Person ID",
                width="small"
            ),
            "Name": st.column_config.TextColumn(
                "Erkannte Person",
                help="Name der erkannten Person (bearbeitbar)",
                width="medium"
            ),
            "Alter": st.column_config.NumberColumn(
                "Alter",
                min_value=0,
                max_value=150,
                step=1,
                help="Geschätztes Alter"
            ),
            "Geschlecht": st.column_config.SelectboxColumn(
                "Geschlecht",
                options=["", "male", "female", "unknown"],
                help="Geschlecht"
            ),
            "Qualität": st.column_config.NumberColumn(
                "Qualität (0-1)",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f",
                help="Gesichtsqualität (0-1)"
            ),
            "Emotion": st.column_config.SelectboxColumn(
                "Emotion",
                options=["", "happy", "neutral", "sad", "angry", "surprised", "unknown"],
                help="Erkannte Emotion"
            ),
            "Ähnlichkeit": st.column_config.NumberColumn(
                "Ähnlichkeit",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f",
                help="Ähnlichkeit zur erkannten Person"
            ),
            "Notizen": st.column_config.TextColumn(
                "Benutzer-Notizen",
                help="Fügen Sie eigene Notizen hinzu",
                width="large"
            )
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Aktualisiere results mit bearbeiteten Daten
    updated_results = results.copy()
    for _, row in edited_df.iterrows():
        img_idx = int(row['Bild-Index'])
        person_idx = int(row['Person-Index'])
        
        if img_idx < len(updated_results) and person_idx < len(updated_results[img_idx].get('persons', [])):
            person = updated_results[img_idx]['persons'][person_idx]
            
            # Aktualisiere Werte
            if pd.notna(row['Name']) and row['Name']:
                person['name'] = row['Name']
            if pd.notna(row['Alter']):
                person['age'] = int(row['Alter'])
            if pd.notna(row['Geschlecht']) and row['Geschlecht']:
                person['gender'] = row['Geschlecht']
            if pd.notna(row['Qualität']):
                person['quality_score'] = float(row['Qualität'])
            if pd.notna(row['Emotion']) and row['Emotion']:
                person['emotion'] = row['Emotion']
            if pd.notna(row['Ähnlichkeit']):
                person['similarity'] = float(row['Ähnlichkeit'])
            if pd.notna(row['Notizen']) and row['Notizen']:
                person['user_notes'] = row['Notizen']
    
    st.success(f"{len(edited_df)} Annotationen bearbeitet!")
    return updated_results

results: List[Dict[str, Any]] = []

# Status-Anzeige für Enhanced Model
if enhanced_engine is not None:
    st.success("Enhanced Model aktiv - Metadaten-Integration läuft!")
elif use_enhanced_model:
    st.warning("Enhanced Model nicht geladen - verwende Standard-Engine")

        # Status-Anzeige für Embeddings/Personenerkennung
if db is not None and len(db.people) > 0:
    total_embeddings = sum(len(embs) for embs in db.people.values())
    st.success(f"Personenerkennung aktiv: {len(db.people)} Personen mit {total_embeddings} Embeddings geladen (Threshold: {threshold:.2f})")
    
    # Zeige geladene Personen
    with st.expander(f"Geladene Personen anzeigen ({len(db.people)} Personen)", expanded=False):
        for person_name, embeddings in db.people.items():
            embedding_count = len(embeddings)
            st.write(f"- **{person_name}**: {embedding_count} Embedding(s)")
            # Zeige Embedding-Dimension für erste Person
            if embeddings and len(embeddings) > 0:
                emb_sample = embeddings[0]
                if isinstance(emb_sample, np.ndarray):
                    st.caption(f"  Dimension: {emb_sample.shape}")
    
    # Threshold-Warnung
    if threshold > 0.7:
        st.warning(f"⚠️ **WARNUNG:** Threshold ({threshold:.2f}) ist sehr hoch! Viele Erkennungen werden möglicherweise verworfen.")
        st.info("💡 **Tipp:** Setzen Sie den Threshold auf **0.5-0.6** für bessere Erkennungsrate.")
elif db is not None and len(db.people) == 0:
    st.warning("Embeddings-Datei geladen, aber keine Personen gefunden. Personenerkennung deaktiviert.")
else:
    st.info("Keine Embeddings geladen. Gesichter werden erkannt, aber keine Personen zugeordnet. Laden Sie `embeddings.pkl` oder Trainings-Identitäten hoch.")

if files:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, up in enumerate(files):
        status_text.text(f"Verarbeite {up.name}...")
        
        data = up.read()
        image = Image.open(io.BytesIO(data)).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Gesichtserkennung
        if enhanced_engine is not None:
            # Enhanced Engine verwenden
            faces = enhanced_engine.analyze_with_metadata(img_bgr, extract_comprehensive_metadata(image))
        else:
            # Standard Engine verwenden
            faces = st.session_state["engine_annot"].analyze(img_bgr)
        
        # Erweiterte Qualitätsfilter anwenden
        filtered_faces = []
        for f in faces:
            face_size = (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1])
            
            # Basis-Qualitätsfilter
            quality_ok = f.get('quality_score', 0.5) >= min_quality
            size_ok = face_size >= min_face_size
            
            # Erweiterte Filter basierend auf Einstellungen
            pose_ok = True
            if enable_pose_analysis and f.get('pose'):
                pose = f['pose']
                # Filtere extreme Posen heraus
                if abs(pose.get('yaw', 0)) > 45 or abs(pose.get('pitch', 0)) > 30:
                    pose_ok = False
            
            symmetry_ok = True
            if enable_symmetry_check and f.get('symmetry_score', 0.5) < 0.3:
                symmetry_ok = False
            
            noise_ok = True
            if enable_noise_analysis and f.get('noise_score', 0.5) < 0.2:
                noise_ok = False
            
            # Alle Filter müssen erfüllt sein
            if (quality_ok and size_ok and pose_ok and 
                symmetry_ok and noise_ok):
                filtered_faces.append(f)
        
        persons = []
        for f in filtered_faces:
            name, sim = (None, None)
            if db and len(db.people) > 0:
                # Personenerkennung durchführen
                n, s = db.match(f["embedding"], threshold=threshold)
                name, sim = (n, s)
                
                # Debug-Info: Zeige auch wenn keine Person erkannt wurde (für erstes Gesicht)
                if idx == 0 and len(persons) == 0 and name is None:
                    if s is not None and s > 0:
                        st.warning(f"⚠️ **Debug:** Beste Ähnlichkeit gefunden: {s:.3f} (Threshold: {threshold:.2f})")
                        st.info(f"💡 **Tipp:** Threshold ist zu hoch! Setzen Sie ihn auf {s:.2f} oder niedriger, um diese Person zu erkennen.")
                        
                        # Zeige Top 3 ähnlichste Personen
                        if db and hasattr(db, 'people'):
                            similarities = []
                            for person_name, embeddings_list in db.people.items():
                                for emb in embeddings_list:
                                    if hasattr(emb, 'shape') and emb.shape == f["embedding"].shape:
                                        try:
                                            sim = 1 - np.linalg.norm(f["embedding"] - emb)
                                            similarities.append((person_name, sim))
                                        except:
                                            pass
                            
                            if similarities:
                                similarities.sort(key=lambda x: x[1], reverse=True)
                                st.info(f"**Top 3 ähnlichste Personen:** {', '.join([f'{name} ({sim:.3f})' for name, sim in similarities[:3]])}")
                    elif s is not None and s == 0:
                        st.warning("⚠️ **Debug:** Keine Ähnlichkeit gefunden (0.0). Embeddings scheinen nicht kompatibel zu sein.")
                        st.info("💡 **Mögliche Ursachen:**")
                        st.write("- Embeddings wurden mit einem anderen Face-Engine-Modell erstellt")
                        st.write("- Embedding-Dimensionen stimmen nicht überein")
                        st.write("- Gesicht wurde nicht korrekt extrahiert")
                        
                        # Zeige Embedding-Dimensionen
                        if hasattr(f["embedding"], 'shape'):
                            st.code(f"Erkanntes Gesicht Embedding Dimension: {f['embedding'].shape}")
                        if db and len(db.people) > 0:
                            first_person = list(db.people.keys())[0]
                            first_embedding = db.people[first_person][0]
                            if hasattr(first_embedding, 'shape'):
                                st.code(f"Geladenes Embedding Dimension: {first_embedding.shape}")
                    else:
                        st.info("Keine Ähnlichkeit gefunden. Stellen Sie sicher, dass die Embeddings zur Person passen.")
            elif db is None or len(db.people) == 0:
                # Keine Embeddings geladen - nur für das erste Bild eine Warnung anzeigen
                if idx == 0 and len(persons) == 0:
                    st.warning("Keine Embeddings geladen! Personen werden nicht erkannt.")
                    st.info("""
                    **Um Personen zu erkennen:**
                    1. Laden Sie `embeddings.pkl` aus der Enroll-Seite hoch (unter "Embeddings DB")
                    2. Oder laden Sie Trainings-Identitäten hoch (unter "Trainings-Identitäten")
                    
                    **Ohne Embeddings:**
                    - Gesichter werden erkannt, aber keine Personen zugeordnet
                    - Sie können Personen manuell in der Annotation-Tabelle zuordnen
                    """)
            persons.append({
                "bbox": f["bbox"],
                "prob": f["prob"],
                "name": name,
                "similarity": sim,
                "age": f["age"],
                "gender": f["gender"],
                "quality_score": f.get("quality_score"),
                "emotion": f.get("emotion"),
                "eye_status": f.get("eye_status"),
                "mouth_status": f.get("mouth_status")
            })

        # Metadaten-Extraktion
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            image.save(tmp.name, format="JPEG")
            
            if extract_full_metadata:
                metadata = extract_comprehensive_metadata(tmp.name)
                gps_data = metadata.get('gps')
            else:
                metadata = {}
                gps_data = extract_exif_gps(tmp.name)
                if gps_data:
                    metadata['gps'] = gps_data
        
        # Standort-Informationen
        location_info = None
        if gps_data and do_reverse:
            if show_location_details:
                location_info = get_location_details(gps_data['lat'], gps_data['lon'])
            else:
                address = reverse_geocode(gps_data['lat'], gps_data['lon'])
                if address:
                    location_info = {'full_address': address}

        record = {
            "image": up.name,
            "metadata": metadata,
            "location": location_info,
            "persons": persons
        }
        results.append(record)

        # Anzeige
        st.header(f"{up.name}")
        
        # Erkannte Personen-Übersicht
        if persons:
            recognized_persons = [p for p in persons if p.get('name')]
            unknown_faces = [p for p in persons if not p.get('name')]
            
            if recognized_persons:
                persons_list = [f"{p['name']} ({p['similarity']:.2f})" for p in recognized_persons]
                st.success(f"**{len(recognized_persons)} Person(en) erkannt:** {', '.join(persons_list)}")
            
            if unknown_faces:
                st.info(f"**{len(unknown_faces)} unbekannte Gesichter** erkannt (keine Übereinstimmung in der Datenbank)")
        else:
            st.warning("Keine Gesichter in diesem Bild erkannt")
        
        # Bildanzeige
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Original", use_container_width=True)
        with col2:
            boxed = draw_boxes(img_bgr, persons)
            st.image(cv2.cvtColor(boxed, cv2.COLOR_BGR2RGB), caption="Erkannte Gesichter", use_container_width=True)
            
            # Namen der erkannten Personen unter dem Bild anzeigen
            if persons:
                recognized_names = [p['name'] for p in persons if p.get('name')]
                unknown_count = len([p for p in persons if not p.get('name')])
                
                if recognized_names:
                    st.success("**Erkannte Personen:**")
                    for i, name in enumerate(recognized_names, 1):
                        similarity = next((p['similarity'] for p in persons if p.get('name') == name), None)
                        if similarity is not None:
                            st.write(f"**{i}.** {name} *(Ähnlichkeit: {similarity:.2f})*")
                        else:
                            st.write(f"**{i}.** {name}")
                
                if unknown_count > 0:
                    st.info(f"**{unknown_count} unbekannte Gesicht(er)** (keine Übereinstimmung gefunden)")
            else:
                st.warning("Keine Gesichter erkannt")
        
        # Metadaten anzeigen
        display_metadata_card(metadata, "Bild-Metadaten")
        
        # Metadaten mit farbigen Hervorhebungen anzeigen (neue Funktion)
        with st.expander("Metadaten (Farbig)", expanded=False):
            display_metadata_annotated(metadata)
        
        # Standort anzeigen
        if location_info:
            with st.expander("Standort-Informationen", expanded=False):
                if location_info.get('full_address'):
                    st.info(f"**Adresse:** {location_info['full_address']}")
                
                if location_info.get('country'):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if location_info.get('country'):
                            st.metric("Land", location_info['country'])
                    with col2:
                        if location_info.get('state'):
                            st.metric("Bundesland", location_info['state'])
                    with col3:
                        if location_info.get('city'):
                            st.metric("Stadt", location_info['city'])
        
        # Gesichtsanalyse anzeigen
        display_face_analysis(persons)
        
        # JSON-Export (kollabiert)
        with st.expander("JSON-Daten", expanded=False):
            st.json(record)
        
        st.divider()
        
        # Fortschritt aktualisieren
        progress_bar.progress((idx + 1) / len(files))
    
    status_text.text("Verarbeitung abgeschlossen!")
    
    # Interaktive Annotation-Bearbeitung (neue Funktion)
    if len(results) > 0:
        st.divider()
        results = interactive_annotation_editor(results)
        st.divider()
    
    # Statistiken berechnen
    total_faces = sum(len(r['persons']) for r in results)
    total_identified = sum(1 for r in results for p in r['persons'] if p.get('name'))
    avg_quality = np.mean([p.get('quality_score', 0) for r in results for p in r['persons'] if p.get('quality_score')])
    
    # Download-Button für alle Ergebnisse
    st.success(f"{len(results)} Bilder erfolgreich verarbeitet")
    
    # Erweiterte Statistiken
    with st.expander("Erkennungsstatistiken", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Gesichter erkannt", total_faces)
        
        with col2:
            identification_rate = (total_identified / total_faces * 100) if total_faces > 0 else 0
            st.metric("Identifikationsrate", f"{identification_rate:.1f}%")
        
        with col3:
            st.metric("Ø Qualität", f"{avg_quality:.2f}" if not np.isnan(avg_quality) else "N/A")
        
        # Detaillierte Aufschlüsselung
        if total_faces > 0:
            st.subheader("Detaillierte Analyse")
            
            # Qualitätsverteilung
            quality_ranges = {'Exzellent (>0.8)': 0, 'Gut (0.6-0.8)': 0, 'Mittel (0.4-0.6)': 0, 'Niedrig (<0.4)': 0}
            for r in results:
                for p in r['persons']:
                    quality = p.get('quality_score', 0)
                    if quality > 0.8:
                        quality_ranges['Exzellent (>0.8)'] += 1
                    elif quality > 0.6:
                        quality_ranges['Gut (0.6-0.8)'] += 1
                    elif quality > 0.4:
                        quality_ranges['Mittel (0.4-0.6)'] += 1
                    else:
                        quality_ranges['Niedrig (<0.4)'] += 1
            
            st.write("**Qualitätsverteilung:**")
            for range_name, count in quality_ranges.items():
                if count > 0:
                    percentage = count / total_faces * 100
                    st.write(f"• {range_name}: {count} ({percentage:.1f}%)")
    
    # Zusammenfassung der erkannten Personen
    st.subheader("Erkannte Personen")
    
    total_recognized = sum(len([p for p in r.get('persons', []) if p.get('name')]) for r in results)
    
    # Erkannte Personen sammeln
    all_recognized_persons = {}
    for result in results:
        for person in result.get('persons', []):
            if person.get('name'):
                name = person['name']
                if name not in all_recognized_persons:
                    all_recognized_persons[name] = 0
                all_recognized_persons[name] += 1
    
    if all_recognized_persons:
        st.success(f"**{len(all_recognized_persons)} verschiedene Personen erkannt** (insgesamt {total_recognized} Erkennungen):")
        
        # Sortiere nach Häufigkeit
        sorted_persons = sorted(all_recognized_persons.items(), key=lambda x: x[1], reverse=True)
        
        # Zeige in Spalten
        cols = st.columns(min(3, len(sorted_persons)))
        for i, (name, count) in enumerate(sorted_persons):
            with cols[i % len(cols)]:
                st.metric(name, f"{count}x erkannt")
        
        # Als Text-Liste
        persons_text = ", ".join([f"{name} ({count}x)" for name, count in sorted_persons])
        st.info(f"**Übersicht:** {persons_text}")
    else:
        st.warning("**Keine Personen erkannt.** Stellen Sie sicher, dass Sie `embeddings.pkl` hochgeladen haben.")
    
    # Download-Button
    st.subheader("Download Ergebnisse")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download results JSON",
                           data=json.dumps(results, ensure_ascii=False, indent=2),
                           file_name="results.json",
                           mime="application/json")
    with col2:
        st.info("Tipp: Laden Sie diese JSON-Datei in der 'Analyze'-Seite hoch für erweiterte Statistiken!")
else:
    st.info("Bilder in der Sidebar hochladen, um zu starten.")
    
    # Download-Button auch ohne Bilder (für Beispiel-Daten)
    st.subheader("Export-Optionen")
    st.info("Nach dem Hochladen und Verarbeiten von Bildern erscheint hier ein Download-Button für die JSON-Ergebnisse.")
    
    # Beispiel-Metadaten anzeigen
    with st.expander("Verfügbare Metadaten", expanded=False):
        st.markdown("""
        **Diese App kann folgende Metadaten extrahieren:**
        
        **Kamera-Informationen:**
        - Hersteller und Modell
        - Objektiv
        - Software
        
        **Aufnahme-Einstellungen:**
        - Brennweite
        - Blende (f-number)
        - ISO-Wert
        - Belichtungszeit
        - Weißabgleich
        - Belichtungsmodus
        
        **Zeitstempel:**
        - Aufnahmedatum und -zeit
        - GPS-Zeitstempel
        
        **Standort:**
        - GPS-Koordinaten
        - Höhe über Meeresspiegel
        - Vollständige Adresse (mit Internetverbindung)
        
        **Gesichtsanalyse:**
        - Alter und Geschlecht
        - Gesichtsqualität
        - Emotionen
        - Augen- und Mundstatus
        - Pose-Schätzung
        """)
