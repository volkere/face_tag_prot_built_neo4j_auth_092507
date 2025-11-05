
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

tab_zip, tab_manual = st.tabs(["Galerie-ZIP hochladen", "Manuell pro Person"])

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
                        faces = st.session_state["engine_enroll"].analyze(img)
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
                faces = st.session_state["engine_enroll"].analyze(img)
                
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
