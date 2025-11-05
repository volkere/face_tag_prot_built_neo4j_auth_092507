
import io, json, tempfile
from typing import List, Dict, Any
import streamlit as st
import numpy as np
from PIL import Image
import cv2
import pandas as pd
import sys
import os

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

db = None
if gallery_file is not None:
    import pickle
    try:
        db = GalleryDB()
        data = pickle.load(gallery_file)
        if isinstance(data, dict):
            db.people = data.get('people', {})
            db.face_metadata = data.get('metadata', {})
        else:
            db.people = data
        st.success(f"Embeddings geladen: {len(db.people)} Personen.")
    except Exception as e:
        st.error(f"Fehler beim Laden der Embeddings: {e}")

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
        
        # Farbe basierend auf Qualität
        quality = p.get('quality_score', 0.5)
        if quality > 0.7:
            color = (0, 255, 0)  # Grün für hohe Qualität
        elif quality > 0.4:
            color = (0, 255, 255)  # Gelb für mittlere Qualität
        else:
            color = (0, 0, 255)  # Rot für niedrige Qualität
        
        cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
        
        # Label mit erweiterten Informationen
        label_parts = []
        
        # Name und Ähnlichkeit
        if p.get("name"):
            sim = f" ({p['similarity']:.2f})" if p.get("similarity") is not None else ""
            label_parts.append(p["name"] + sim)
        
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
            camera_text += f"**Hersteller:** :red[{metadata['camera_make']}]"
        if metadata.get('camera_model'):
            if camera_text:
                camera_text += " | "
            camera_text += f"**Modell:** :blue[{metadata['camera_model']}]"
        
        if camera_text:
            st.markdown(camera_text)
    
    # Aufnahme-Einstellungen
    if any(key in metadata for key in ['focal_length', 'f_number', 'iso', 'exposure_time']):
        settings_text = ""
        if metadata.get('focal_length'):
            settings_text += f"**Brennweite:** :green[{metadata['focal_length']}mm]"
        if metadata.get('f_number'):
            if settings_text:
                settings_text += " | "
            settings_text += f"**Blende:** :orange[f/{metadata['f_number']}]"
        if metadata.get('iso'):
            if settings_text:
                settings_text += " | "
            settings_text += f"**ISO:** :violet[{metadata['iso']}]"
        if metadata.get('exposure_time'):
            if settings_text:
                settings_text += " | "
            settings_text += f"**Belichtung:** :red[1/{metadata['exposure_time']}s]"
        
        if settings_text:
            st.markdown(settings_text)
    
    # Standort
    if metadata.get('gps'):
        gps = metadata['gps']
        location_text = f"**Standort:** :red[{gps['lat']:.4f}°N] :blue[{gps['lon']:.4f}°E]"
        if gps.get('altitude'):
            location_text += f" | **Höhe:** :green[{gps['altitude']:.1f}m]"
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
    
    st.success(f"✅ {len(edited_df)} Annotationen bearbeitet!")
    return updated_results

results: List[Dict[str, Any]] = []

# Status-Anzeige für Enhanced Model
if enhanced_engine is not None:
    st.success("Enhanced Model aktiv - Metadaten-Integration läuft!")
elif use_enhanced_model:
    st.warning("Enhanced Model nicht geladen - verwende Standard-Engine")

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
            if db:
                n, s = db.match(f["embedding"], threshold=threshold)
                name, sim = (n, s)
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
        
        # Bildanzeige
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Original", use_container_width=True)
        with col2:
            boxed = draw_boxes(img_bgr, persons)
            st.image(cv2.cvtColor(boxed, cv2.COLOR_BGR2RGB), caption="Erkannte Gesichter", use_container_width=True)
        
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
    
    # Download-Button
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
