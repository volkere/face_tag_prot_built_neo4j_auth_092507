
import io, os, zipfile, tempfile, pickle
from typing import List, Dict
import streamlit as st
import numpy as np
import cv2
import sys

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.face_recognizer import FaceEngine, GalleryDB
from app.location import extract_comprehensive_metadata
from streamlit_styles import apply_custom_css

# Wende kleinere Schriftgrößen an
apply_custom_css()

st.title("Enroll: Embeddings erstellen")
st.caption("Erzeuge eine embeddings.pkl aus einer Galerie-ZIP oder manuell pro Person.")

with st.sidebar:
    det = st.slider("Detector size", 320, 1024, 640, 64)
    extract_exif = st.checkbox("EXIF-Metadaten extrahieren", value=False, help="Erfasst Kamera-Daten, GPS und Zeitstempel für verbesserte Erkennung")

if "engine_enroll" not in st.session_state or st.session_state.get("det_enroll") != det:
    st.session_state["engine_enroll"] = FaceEngine(det_size=(det, det))
    st.session_state["det_enroll"] = det

tab_zip, tab_manual, tab_converted, tab_pbf_processor, tab_mapping = st.tabs(["Galerie-ZIP hochladen", "Manuell pro Person", "Aus konvertierten Daten", "PBF-DAMS Processor", "Aus Zuordnungs-Datei"])

with tab_zip:
    st.markdown("**ZIP-Struktur:** `PersonA/*.jpg`, `PersonB/*.png`, …")
    st.markdown("*Hinweis: Wenn EXIF-Metadaten aktiviert sind, werden auch Bilder ohne erkannte Gesichter verarbeitet.*")
    zip_file = st.file_uploader("Galerie-ZIP auswählen", type=["zip"])
    if zip_file is not None:
        with tempfile.TemporaryDirectory() as tmpdir:
            z = zipfile.ZipFile(zip_file)
            z.extractall(tmpdir)
            db = GalleryDB()
            count_imgs = 0
            exif_count = 0
            faces_found = 0
            no_faces_with_exif = 0
            for root, dirs, files in os.walk(tmpdir):
                for fn in files:
                    if fn.lower().endswith((".jpg",".jpeg",".png",".bmp",".webp",".tif",".tiff")):
                        p = os.path.join(root, fn)
                        img = cv2.imread(p)
                        if img is None:
                            continue
                        
                        # Prüfe Bildgröße - OpenCV benötigt gültige Dimensionen
                        h, w = img.shape[:2]
                        if h < 50 or w < 50:
                            st.warning(f"Bild zu klein ({w}x{h}px): {fn}. Überspringe.")
                            continue
                        
                        try:
                            faces = st.session_state["engine_enroll"].analyze(img)
                        except Exception as e:
                            st.warning(f"Fehler beim Analysieren von {fn}: {e}. Überspringe.")
                            continue
                        person = os.path.basename(os.path.dirname(p))
                        
                        # EXIF-Metadaten extrahieren wenn aktiviert
                        metadata = None
                        if extract_exif:
                            try:
                                exif_data = extract_comprehensive_metadata(p)
                                if exif_data:
                                    metadata = {
                                        'exif': exif_data,
                                        'source_image': fn
                                    }
                                    exif_count += 1
                            except Exception as e:
                                pass
                        
                        # Gesichter gefunden - wie bisher verarbeiten
                        if faces:
                            faces.sort(key=lambda f: (f['bbox'][2]-f['bbox'][0])*(f['bbox'][3]-f['bbox'][1]), reverse=True)
                            if extract_exif and metadata:
                                # Erweitere Metadaten mit Gesichtsattributen
                                metadata.update({
                                    'age': faces[0].get('age'),
                                    'gender': faces[0].get('gender'),
                                    'quality_score': faces[0].get('quality_score'),
                                    'emotion': faces[0].get('emotion'),
                                    'eye_status': faces[0].get('eye_status'),
                                    'mouth_status': faces[0].get('mouth_status')
                                })
                            db.add(person, faces[0]["embedding"], metadata)
                            faces_found += 1
                            count_imgs += 1
                        # Keine Gesichter, aber EXIF-Daten vorhanden
                        elif extract_exif and metadata:
                            # Erstelle Dummy-Embedding für Metadaten-Speicherung
                            dummy_embedding = np.zeros((512,), dtype=np.float32)
                            db.add(person, dummy_embedding, metadata)
                            no_faces_with_exif += 1
                            count_imgs += 1
            
            success_msg = f"Verarbeitet: {count_imgs} Bild(er), davon {faces_found} mit Gesichtern"
            if extract_exif:
                success_msg += f", {exif_count} mit EXIF-Metadaten"
                if no_faces_with_exif > 0:
                    success_msg += f" ({no_faces_with_exif} ohne Gesichter)"
            st.success(success_msg)
            
            b = io.BytesIO()
            pickle.dump({"people": db.people, "metadata": db.face_metadata}, b, protocol=pickle.HIGHEST_PROTOCOL)
            st.download_button("embeddings.pkl herunterladen", data=b.getvalue(), file_name="embeddings.pkl", mime="application/octet-stream")

with tab_manual:
    st.markdown("Name eingeben, Bilder hochladen, **Hinzufügen** klicken.")
    st.markdown("*Hinweis: Mit EXIF-Metadaten werden auch Bilder ohne Gesichter verarbeitet.*")
    if "manual_db" not in st.session_state:
        st.session_state["manual_db"] = GalleryDB()
    name = st.text_input("Name der Person")
    imgs = st.file_uploader("Bilder der Person", type=["jpg","jpeg","png","bmp","webp","tif","tiff"], accept_multiple_files=True)
    if st.button("Hinzufügen", disabled=(not name or not imgs)):
        added = 0
        exif_added = 0
        faces_found = 0
        no_faces_with_exif = 0
        for up in imgs:
            # Speichere Upload temporär für EXIF-Extraktion
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{up.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(up.read())
                tmp_path = tmp_file.name
            
            try:
                data = open(tmp_path, 'rb').read()
                file_bytes = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if img is None:
                    os.unlink(tmp_path)
                    continue
                
                # Prüfe Bildgröße - OpenCV benötigt gültige Dimensionen
                h, w = img.shape[:2]
                if h < 50 or w < 50:
                    os.unlink(tmp_path)
                    continue
                
                try:
                    faces = st.session_state["engine_enroll"].analyze(img)
                except Exception as e:
                    os.unlink(tmp_path)
                    continue
                
                # EXIF-Metadaten extrahieren wenn aktiviert
                metadata = None
                if extract_exif:
                    try:
                        exif_data = extract_comprehensive_metadata(tmp_path)
                        if exif_data:
                            metadata = {
                                'exif': exif_data,
                                'source_image': up.name
                            }
                            exif_added += 1
                    except Exception:
                        pass
                
                # Gesichter gefunden - wie bisher verarbeiten
                if faces:
                    faces.sort(key=lambda f: (f['bbox'][2]-f['bbox'][0])*(f['bbox'][3]-f['bbox'][1]), reverse=True)
                    if extract_exif and metadata:
                        # Erweitere Metadaten mit Gesichtsattributen
                        metadata.update({
                            'age': faces[0].get('age'),
                            'gender': faces[0].get('gender'),
                            'quality_score': faces[0].get('quality_score'),
                            'emotion': faces[0].get('emotion'),
                            'eye_status': faces[0].get('eye_status'),
                            'mouth_status': faces[0].get('mouth_status')
                        })
                    st.session_state["manual_db"].add(name, faces[0]["embedding"], metadata)
                    faces_found += 1
                    added += 1
                # Keine Gesichter, aber EXIF-Daten vorhanden
                elif extract_exif and metadata:
                    # Erstelle Dummy-Embedding für Metadaten-Speicherung
                    dummy_embedding = np.zeros((512,), dtype=np.float32)
                    st.session_state["manual_db"].add(name, dummy_embedding, metadata)
                    no_faces_with_exif += 1
                    added += 1
            finally:
                # Temporäre Datei löschen
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        msg = f"{added} Bild(er) hinzugefügt, davon {faces_found} mit Gesichtern"
        if extract_exif:
            msg += f", {exif_added} mit EXIF-Metadaten"
            if no_faces_with_exif > 0:
                msg += f" ({no_faces_with_exif} ohne Gesichter)"
        st.success(msg)
    if st.session_state["manual_db"].people:
        st.info(f"Aktueller DB-Status: {len(st.session_state['manual_db'].people)} Personen.")
        b = io.BytesIO()
        pickle.dump({"people": st.session_state["manual_db"].people, "metadata": st.session_state["manual_db"].face_metadata}, b, protocol=pickle.HIGHEST_PROTOCOL)
        st.download_button("embeddings.pkl herunterladen", data=b.getvalue(), file_name="embeddings.pkl", mime="application/octet-stream")

with tab_converted:
    st.markdown("**Daten aus PBF-DAMS:**")
    st.markdown("Laden Sie eine JSON-Datei aus PBF-DAMS hoch. Diese kann entweder:")
    st.markdown("- **Konvertierte Daten** mit bereits vorhandenen Embeddings enthalten, oder")
    st.markdown("- **Rohe Export-Daten** mit Bildpfaden, aus denen Embeddings erstellt werden")
    
    converted_file = st.file_uploader("PBF-DAMS JSON-Datei hochladen", type=["json"], key="converted_upload")
    
    if converted_file is not None:
        import json
        try:
            # JSON-Datei laden
            data = json.load(converted_file)
            
            # Debug: Zeige Datenstruktur
            with st.expander("🔍 Datenstruktur-Analyse", expanded=False):
                st.json({"Top-Level-Typ": type(data).__name__, "Keys": list(data.keys()) if isinstance(data, dict) else "Liste", "Anzahl Einträge": len(data) if isinstance(data, (list, dict)) else 0})
                if isinstance(data, list) and len(data) > 0:
                    st.json({"Erstes Element Keys": list(data[0].keys()) if isinstance(data[0], dict) else "Kein Dict"})
                elif isinstance(data, dict) and len(data) > 0:
                    first_key = list(data.keys())[0]
                    if isinstance(data[first_key], list) and len(data[first_key]) > 0:
                        st.json({"Erstes Element in Array": list(data[first_key][0].keys()) if isinstance(data[first_key][0], dict) else "Kein Dict"})
            
            # GalleryDB aus konvertierten Daten erstellen
            db = GalleryDB()
            added = 0
            
            # Unterstützte Schlüssel für Person-Namen
            name_keys = ["identifier", "person_identifier", "name", "label", "person_label", "person_name"]
            # Unterstützte Schlüssel für Embeddings
            embedding_keys = ["embedding", "face_embedding", "vector", "face_vector", "face_embedding_vector"]
            
            # Datenstruktur analysieren - verschiedene mögliche Strukturen
            records = []
            if isinstance(data, list):
                # Direkt eine Liste von Records
                records = data
            elif isinstance(data, dict):
                # Verschiedene mögliche Top-Level-Keys
                if "entries" in data and isinstance(data["entries"], list):
                    records = data["entries"]
                elif "regions" in data and isinstance(data["regions"], list):
                    # Regions sind direkt die Personen
                    records = data["regions"]
                elif "persons" in data and isinstance(data["persons"], list):
                    records = data["persons"]
                elif "data" in data and isinstance(data["data"], list):
                    records = data["data"]
                else:
                    # Versuche alle Listen-Werte zu finden
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            records = value
                            break
                    if not records:
                        records = [data]
            
            # Debug: Zeige gefundene Records
            if len(records) > 0:
                with st.expander("🔍 Gefundene Records", expanded=False):
                    st.info(f"Anzahl Records: {len(records)}")
                    if isinstance(records[0], dict):
                        st.json({"Erster Record Keys": list(records[0].keys())})
            
            # Personen extrahieren
            for record in records:
                # Verschiedene mögliche Strukturen für Personen
                persons = []
                
                # Struktur 1: Record hat direkt "persons" oder "regions" Array
                if isinstance(record, dict):
                    # Prüfe ob Record selbst eine Person ist (hat embedding und identifier)
                    has_embedding = any(key in record for key in embedding_keys)
                    has_name = any(key in record for key in name_keys)
                    
                    if has_embedding and has_name:
                        # Record ist direkt eine Person/Region
                        persons = [record]
                    else:
                        # Record enthält Personen/Regions
                        persons = record.get("persons") or record.get("regions") or []
                        if isinstance(persons, dict):
                            persons = [persons]
                        elif not isinstance(persons, list):
                            # Wenn kein Array, versuche den Record selbst als Person zu behandeln
                            persons = [record]
                elif isinstance(record, (list, tuple)):
                    persons = list(record)
                else:
                    # Record ist direkt eine Person
                    persons = [record]
                
                for person in persons:
                    # Person-Name extrahieren
                    name = None
                    for key in name_keys:
                        value = person.get(key)
                        if value:
                            name = value
                            break
                    
                    # Prüfe auch verschachtelte Struktur
                    if not name:
                        nested = person.get("person")
                        if isinstance(nested, dict):
                            for key in name_keys:
                                value = nested.get(key)
                                if value:
                                    name = value
                                    break
                    
                    # Embedding extrahieren
                    embedding = None
                    for key in embedding_keys:
                        if key in person and person[key] is not None:
                            try:
                                emb_array = np.array(person[key], dtype=np.float32)
                                if emb_array.ndim == 1:
                                    embedding = emb_array
                                    break
                            except Exception:
                                continue
                    
                    # Prüfe auch verschachtelte Struktur
                    if embedding is None:
                        nested = person.get("person")
                        if isinstance(nested, dict):
                            for key in embedding_keys:
                                if key in nested and nested[key] is not None:
                                    try:
                                        emb_array = np.array(nested[key], dtype=np.float32)
                                        if emb_array.ndim == 1:
                                            embedding = emb_array
                                            break
                                    except Exception:
                                        continue
                    
                    # Metadaten extrahieren (falls vorhanden)
                    metadata = None
                    if extract_exif:
                        # Versuche Metadaten aus dem Record zu extrahieren
                        record_metadata = record.get("metadata", {})
                        if record_metadata:
                            metadata = {
                                'exif': record_metadata,
                                'source': 'pbf_dams_converted'
                            }
                    
                    # Zur Datenbank hinzufügen
                    if name and embedding is not None:
                        db.add(name, embedding, metadata)
                        added += 1
            
            if added > 0:
                total_embeddings = sum(len(embs) for embs in db.people.values())
                st.success(f"✅ {added} Personen mit {total_embeddings} Embeddings aus konvertierten Daten geladen!")
                st.info(f"Personen: {', '.join(list(db.people.keys())[:10])}{' ...' if len(db.people) > 10 else ''}")
                
                # embeddings.pkl erstellen
                b = io.BytesIO()
                pickle.dump({"people": db.people, "metadata": db.face_metadata}, b, protocol=pickle.HIGHEST_PROTOCOL)
                st.download_button(
                    "embeddings.pkl herunterladen", 
                    data=b.getvalue(), 
                    file_name="embeddings.pkl", 
                    mime="application/octet-stream"
                )
            else:
                # Prüfe ob es sich um rohe PBF-DAMS-Daten handelt (Bilder ohne Embeddings)
                image_paths = []
                for record in records:
                    if isinstance(record, dict) and "image" in record:
                        image_paths.append(record["image"])
                
                if len(image_paths) > 0:
                    st.warning(f"Keine Embeddings gefunden, aber {len(image_paths)} Bildpfade entdeckt.")
                    st.info("**Dies ist ein roher PBF-DAMS-Export (ohne Gesichtserkennungsdaten).**")
                    
                    st.error("""
                    **WICHTIGER HINWEIS:**
                    
                    Diese Datei enthält nur Bildpfade, aber keine Personen-Identitäten oder Embeddings.
                    
                    **Um Personen zu erkennen, benötigen Sie:**
                    1. **Echte Personen-Embeddings** von bekannten Personen (z.B. eddie_martinez)
                    2. Diese erstellen Sie mit einer **Galerie-ZIP** mit Ordnern pro Person:
                       ```
                       galerie.zip
                       ├── eddie_martinez/
                       │   ├── foto1.jpg
                       │   ├── foto2.jpg
                       └── andere_person/
                           ├── foto3.jpg
                           └── foto4.jpg
                       ```
                    
                    **Workflow:**
                    1. Erstellen Sie eine Galerie-ZIP mit bekannten Personen
                    2. Laden Sie diese im Tab "Galerie-ZIP hochladen" hoch
                    3. Laden Sie die resultierende `embeddings.pkl` in der Annotate-Seite hoch
                    4. Die Annotate-Seite erkennt dann "eddie_martinez" anstatt "Person_dateiname"
                    """)
                    
                    # Zeige erste paar Bildpfade als Information
                    with st.expander("Gefundene Bildpfade (erste 10)", expanded=False):
                        for path in image_paths[:10]:
                            st.text(path)
                        if len(image_paths) > 10:
                            st.text(f"... und {len(image_paths) - 10} weitere")
                    
                    st.info("""
                    **Alternative:** Verwenden Sie diese Bilder, um eine Galerie-ZIP zu erstellen:
                    1. Sortieren Sie die Bilder manuell in Ordner nach Personen
                    2. Erstellen Sie eine ZIP-Datei mit der Struktur: `person_name/foto.jpg`
                    3. Laden Sie diese ZIP hier im ersten Tab hoch
                    """)
                
                else:
                    st.error("⚠️ Keine Personen mit Embeddings oder Bildpfade in der Datei gefunden.")
                    
                    # Debug-Informationen anzeigen
                    st.error("**Debug-Informationen:**")
                    if len(records) > 0:
                        st.write(f"Gefundene Records: {len(records)}")
                        # Zeige Beispiel-Record
                        example_record = records[0] if isinstance(records[0], dict) else {}
                        st.json({"Beispiel-Record": example_record})
                        
                        # Prüfe welche Keys vorhanden sind
                        if isinstance(example_record, dict):
                            found_name_keys = [k for k in name_keys if k in example_record]
                            found_embedding_keys = [k for k in embedding_keys if k in example_record]
                            st.write(f"Gefundene Name-Keys: {found_name_keys}")
                            st.write(f"Gefundene Embedding-Keys: {found_embedding_keys}")
                    
                    st.info("""
                    **Unterstützte Formate:**
                    1. **Konvertierte Daten:** JSON mit `persons`/`regions` Array, jede Person mit `name`/`identifier` und `embedding`
                    2. **Rohe PBF-DAMS-Daten:** JSON mit `image`-Pfaden, aus denen Embeddings erstellt werden
                    
                    **Tipp:** Öffnen Sie die "Datenstruktur-Analyse" oben, um die tatsächliche Struktur zu sehen.
                    """)
                
        except json.JSONDecodeError as e:
            st.error(f"Fehler beim Laden der JSON-Datei: {e}")
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der Datei: {e}")
            import traceback
            st.code(traceback.format_exc())

with tab_pbf_processor:
    st.markdown("**PBF-DAMS Automatische Personenerkennung**")
    st.markdown("Erkennt automatisch Personen in PBF-DAMS-Exportdaten basierend auf einer Referenz-Datenbank.")
    
    st.info("""
    **Dieser Prozess:**
    1. Lädt eine Referenz-Embeddings-Datenbank (bekannte Personen)
    2. Lädt Ihre PBF-DAMS JSON-Datei (z.B. faces_20251127_141817.json)
    3. Erkennt automatisch Personen durch Vergleich mit der Referenz-Datenbank
    4. Erstellt eine erweiterte embeddings.pkl mit allen erkannten Personen
    """)
    
    # Upload der Referenz-Embeddings
    st.subheader("1. Referenz-Datenbank laden")
    reference_file = st.file_uploader(
        "Referenz-Embeddings (embeddings.pkl)", 
        type=["pkl"], 
        key="reference_embeddings",
        help="Laden Sie eine embeddings.pkl mit bekannten Personen hoch (z.B. aus Galerie-ZIP erstellt)"
    )
    
    reference_db = None
    if reference_file is not None:
        try:
            import pickle
            reference_data = pickle.load(reference_file)
            reference_db = GalleryDB()
            if isinstance(reference_data, dict):
                reference_db.people = reference_data.get('people', {})
                reference_db.face_metadata = reference_data.get('metadata', {})
            
            if len(reference_db.people) > 0:
                total_ref_embeddings = sum(len(embs) for embs in reference_db.people.values())
                st.success(f"Referenz-Datenbank geladen: {len(reference_db.people)} Personen mit {total_ref_embeddings} Embeddings")
                st.info(f"Bekannte Personen: {', '.join(list(reference_db.people.keys())[:10])}")
            else:
                st.error("Keine Personen in der Referenz-Datenbank gefunden.")
                reference_db = None
        except Exception as e:
            st.error(f"Fehler beim Laden der Referenz-Datenbank: {e}")
            reference_db = None
    
    # Upload der PBF-DAMS Datei
    st.subheader("2. PBF-DAMS Datei laden")
    pbf_file = st.file_uploader("PBF-DAMS JSON-Datei hochladen", type=["json"], key="pbf_processor")
    
    # Prüfe ob Datei hochgeladen wurde aber Referenz-Datenbank fehlt
    if pbf_file is not None and reference_db is None:
        st.warning("Bitte laden Sie zuerst eine Referenz-Embeddings-Datenbank hoch.")
        st.info("""
        **So erstellen Sie eine Referenz-Datenbank:**
        1. Gehen Sie zum Tab "Galerie-ZIP hochladen"
        2. Erstellen Sie eine ZIP-Datei mit bekannten Personen:
           ```
           referenz.zip
           ├── eddie_martinez/
           │   ├── foto1.jpg
           │   └── foto2.jpg
           └── anna_schmidt/
               └── portrait.jpg
           ```
        3. Laden Sie die ZIP hoch und erstellen Sie embeddings.pkl
        4. Verwenden Sie diese embeddings.pkl hier als Referenz-Datenbank
        """)
    elif pbf_file is not None and reference_db is not None:
        import json
        try:
            # JSON laden
            data = json.load(pbf_file)
            
            # Bildpfade extrahieren
            image_paths = []
            for record in data if isinstance(data, list) else [data]:
                if isinstance(record, dict) and "image" in record:
                    image_paths.append(record["image"])
            
            if len(image_paths) == 0:
                st.error("Keine Bildpfade in der JSON-Datei gefunden.")
            else:
                st.success(f"**{len(image_paths)} Bilder** in der Datei gefunden.")
                
                # Einstellungen
                st.subheader("3. Erkennungseinstellungen")
                col1, col2, col3 = st.columns(3)
                with col1:
                    max_images = st.slider("Max. Anzahl Bilder verarbeiten", 1, min(100, len(image_paths)), min(20, len(image_paths)))
                with col2:
                    face_threshold = st.slider("Min. Gesichtsqualität", 0.0, 1.0, 0.5, 0.05)
                with col3:
                    recognition_threshold = st.slider("Erkennungs-Threshold", 0.3, 0.9, 0.6, 0.01, help="Wie ähnlich muss ein Gesicht sein, um erkannt zu werden")
                
                if st.button("Automatische Personenerkennung starten", key="auto_recognize"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Container für erkannte Gesichter
                    if "recognized_faces" not in st.session_state:
                        st.session_state.recognized_faces = []
                    
                    st.session_state.recognized_faces = []
                    processed = 0
                    total_faces = 0
                    recognized_count = 0
                    unknown_count = 0
                    
                    # Statistiken
                    recognition_stats = {}
                    
                    for i, image_path in enumerate(image_paths[:max_images]):
                        try:
                            status_text.text(f"Verarbeite Bild {i+1}/{max_images}: {os.path.basename(image_path)}")
                            
                            if os.path.exists(image_path):
                                img = cv2.imread(image_path)
                                if img is not None:
                                    # Prüfe Bildgröße - OpenCV benötigt gültige Dimensionen
                                    h, w = img.shape[:2]
                                    if h < 50 or w < 50:
                                        continue
                                    
                                    try:
                                        faces = st.session_state["engine_enroll"].analyze(img)
                                    except Exception as e:
                                        st.warning(f"Fehler beim Analysieren von {os.path.basename(image_path)}: {e}")
                                        continue
                                    
                                    for face in faces:
                                        if face.get('quality_score', 0.5) >= face_threshold:
                                            total_faces += 1
                                            
                                            # Automatische Personenerkennung
                                            recognized_name, similarity = reference_db.match(
                                                face['embedding'], 
                                                threshold=recognition_threshold
                                            )
                                            
                                            # Gesicht ausschneiden für Vorschau
                                            bbox = face['bbox']
                                            x1, y1, x2, y2 = map(int, bbox)
                                            face_crop = img[y1:y2, x1:x2]
                                            face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                                            
                                            if recognized_name:
                                                recognized_count += 1
                                                recognition_stats[recognized_name] = recognition_stats.get(recognized_name, 0) + 1
                                                final_name = recognized_name
                                                status = "recognized"
                                            else:
                                                unknown_count += 1
                                                final_name = f"Unknown_{unknown_count}"
                                                status = "unknown"
                                                similarity = 0.0
                                            
                                            st.session_state.recognized_faces.append({
                                                'image_path': image_path,
                                                'embedding': face['embedding'],
                                                'face_image': face_rgb,
                                                'quality': face.get('quality_score', 0.5),
                                                'age': face.get('age'),
                                                'gender': face.get('gender'),
                                                'bbox': bbox,
                                                'recognized_name': final_name,
                                                'similarity': similarity,
                                                'status': status
                                            })
                                
                                processed += 1
                            
                            progress_bar.progress((i + 1) / max_images)
                            
                        except Exception as e:
                            st.error(f"Fehler bei {image_path}: {e}")
                    
                    status_text.text(f"Automatische Erkennung abgeschlossen!")
                    
                    # Ergebnisse anzeigen
                    st.subheader("4. Erkennungsergebnisse")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Gesichter gefunden", total_faces)
                    with col2:
                        st.metric("Erkannte Personen", recognized_count)
                    with col3:
                        st.metric("Unbekannte Gesichter", unknown_count)
                    with col4:
                        recognition_rate = (recognized_count / total_faces * 100) if total_faces > 0 else 0
                        st.metric("Erkennungsrate", f"{recognition_rate:.1f}%")
                    
                    if recognition_stats:
                        st.success("**Erkannte Personen:**")
                        persons_text = ", ".join([f"{name} ({count}x)" for name, count in sorted(recognition_stats.items(), key=lambda x: x[1], reverse=True)])
                        st.info(persons_text)
                
                # Erkannte Gesichter anzeigen
                if "recognized_faces" in st.session_state and len(st.session_state.recognized_faces) > 0:
                    
                    # Vorschau der Erkennungen
                    with st.expander("Erkennungs-Vorschau (erste 12 Gesichter)", expanded=True):
                        faces_to_show = st.session_state.recognized_faces[:12]
                        faces_per_row = 4
                        
                        for i in range(0, len(faces_to_show), faces_per_row):
                            cols = st.columns(faces_per_row)
                            
                            for j, col in enumerate(cols):
                                face_idx = i + j
                                if face_idx < len(faces_to_show):
                                    face_data = faces_to_show[face_idx]
                                    
                                    with col:
                                        # Gesichtsbild anzeigen
                                        st.image(face_data['face_image'], use_container_width=True)
                                        
                                        # Erkennungsstatus
                                        if face_data['status'] == 'recognized':
                                            st.success(f"**{face_data['recognized_name']}**")
                                            st.caption(f"Ähnlichkeit: {face_data['similarity']:.2f}")
                                        else:
                                            st.warning("**Unbekannt**")
                                        
                                        # Metadaten
                                        st.caption(f"Q: {face_data['quality']:.2f}")
                                        if face_data.get('age'):
                                            st.caption(f"{face_data.get('age')}J, {face_data.get('gender', 'unknown')}")
                    
                    # Erweiterte Embeddings-Datenbank erstellen
                    st.subheader("5. Erweiterte Embeddings-Datenbank erstellen")
                    
                    recognized_faces = [f for f in st.session_state.recognized_faces if f['status'] == 'recognized']
                    
                    if len(recognized_faces) > 0:
                        st.info(f"**{len(recognized_faces)} erkannte Gesichter** werden zur Referenz-Datenbank hinzugefügt.")
                        
                        # Option: Auch unbekannte Gesichter einschließen
                        include_unknown = st.checkbox(
                            "Unbekannte Gesichter als 'Unknown_X' einschließen", 
                            value=False,
                            help="Fügt auch unerkannte Gesichter zur Datenbank hinzu"
                        )
                        
                        if st.button("Erweiterte embeddings.pkl erstellen", key="create_enhanced_embeddings"):
                            # Neue GalleryDB erstellen (Kopie der Referenz-DB)
                            enhanced_db = GalleryDB()
                            
                            # Referenz-Daten kopieren
                            for name, embeddings in reference_db.people.items():
                                for embedding in embeddings:
                                    enhanced_db.add(name, embedding)
                            
                            if hasattr(reference_db, 'face_metadata'):
                                enhanced_db.face_metadata = reference_db.face_metadata.copy()
                            
                            # Neue erkannte Gesichter hinzufügen
                            added_faces = 0
                            for face in st.session_state.recognized_faces:
                                if face['status'] == 'recognized' or (include_unknown and face['status'] == 'unknown'):
                                    # Metadaten erstellen
                                    metadata = {
                                        'source_image': os.path.basename(face['image_path']),
                                        'source': 'pbf_dams_auto_recognized',
                                        'quality_score': face['quality'],
                                        'age': face.get('age'),
                                        'gender': face.get('gender'),
                                        'bbox': face['bbox'],
                                        'similarity': face['similarity'],
                                        'recognition_status': face['status']
                                    }
                                    
                                    enhanced_db.add(face['recognized_name'], face['embedding'], metadata)
                                    added_faces += 1
                            
                            # Statistiken
                            total_persons = len(enhanced_db.people)
                            total_embeddings = sum(len(embs) for embs in enhanced_db.people.values())
                            
                            # embeddings.pkl erstellen
                            b = io.BytesIO()
                            pickle.dump({"people": enhanced_db.people, "metadata": enhanced_db.face_metadata}, b, protocol=pickle.HIGHEST_PROTOCOL)
                            
                            st.success(f"**Erweiterte embeddings.pkl erstellt!**")
                            st.info(f"**{total_persons} Personen** mit **{total_embeddings} Embeddings** (davon {added_faces} neue aus PBF-DAMS)")
                            
                            # Zeige Personen-Übersicht
                            if recognition_stats:
                                st.info(f"**Neue Erkennungen:** {', '.join([f'{name} (+{count})' for name, count in recognition_stats.items()])}")
                            
                            st.download_button(
                                "Erweiterte embeddings.pkl herunterladen",
                                data=b.getvalue(),
                                file_name="embeddings_enhanced_with_pbf_dams.pkl",
                                mime="application/octet-stream"
                            )
                            
                            st.success("""
                            **Perfekt! Jetzt haben Sie eine erweiterte Datenbank mit:**
                            - Alle ursprünglichen Personen aus der Referenz-Datenbank
                            - Automatisch erkannte Personen aus den PBF-DAMS-Bildern
                            - Echte Namen wie "eddie_martinez" anstatt "Person_dateiname"
                            
                            **Verwenden Sie diese in der Annotate-Seite für perfekte Personenerkennung!**
                            """)
                    else:
                        st.warning("Keine Personen automatisch erkannt.")
                        st.info("""
                        **Mögliche Gründe:**
                        - Erkennungs-Threshold zu hoch (versuchen Sie 0.5 oder niedriger)
                        - Personen in PBF-DAMS-Bildern sind nicht in der Referenz-Datenbank
                        - Bildqualität zu schlecht
                        
                        **Lösungen:**
                        - Senken Sie den Erkennungs-Threshold
                        - Erweitern Sie Ihre Referenz-Datenbank mit mehr Personen
                        - Prüfen Sie die Bildqualität in den PBF-DAMS-Daten
                        """)
        
        except json.JSONDecodeError as e:
            st.error(f"Fehler beim Laden der JSON-Datei: {e}")
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der Datei: {e}")
            import traceback
            st.code(traceback.format_exc())
