"""
Annotate-Seite für macOS Big Sur mit Intel-Chip
Kompatible Version mit Fallback-Optionen
"""

import streamlit as st
import cv2
import numpy as np
import json
import os
from pathlib import Path
import logging
from typing import List, Dict, Any
import sys

# Füge den app-Ordner zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

# Versuche Face Recognizer zu importieren
try:
    from app.face_recognizer import FaceRecognizer
    FACE_RECOGNIZER_TYPE = "InsightFace"
except ImportError:
    try:
        from app.face_recognizer_bigsur import FaceRecognizerBigSur as FaceRecognizer
        FACE_RECOGNIZER_TYPE = "BigSur"
    except ImportError:
        st.error("❌ Kein Face Recognizer verfügbar")
        st.stop()

# Versuche Location zu importieren
try:
    from app.location import LocationExtractor
    LOCATION_AVAILABLE = True
except ImportError:
    LOCATION_AVAILABLE = False

st.set_page_config(page_title="Annotate - Big Sur", layout="wide")

st.title("📸 Photo Annotation")
st.caption(f"Big Sur Edition - Face Recognizer: {FACE_RECOGNIZER_TYPE}")

# System-Informationen
with st.expander("System-Informationen", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Face Recognizer:** {FACE_RECOGNIZER_TYPE}")
        st.write(f"**Location:** {'Verfügbar' if LOCATION_AVAILABLE else 'Nicht verfügbar'}")
    with col2:
        st.write(f"**OpenCV:** {cv2.__version__}")
        st.write(f"**NumPy:** {np.__version__}")

# Initialisiere Face Recognizer
@st.cache_resource
def get_face_recognizer():
    """Lädt den Face Recognizer"""
    try:
        return FaceRecognizer()
    except Exception as e:
        st.error(f"Fehler beim Laden des Face Recognizers: {e}")
        return None

face_recognizer = get_face_recognizer()
if face_recognizer is None:
    st.error("❌ Face Recognizer konnte nicht geladen werden")
    st.stop()

# Initialisiere Location Extractor
location_extractor = None
if LOCATION_AVAILABLE:
    try:
        location_extractor = LocationExtractor()
    except Exception as e:
        st.warning(f"Location Extractor nicht verfügbar: {e}")

# Sidebar-Einstellungen
with st.sidebar:
    st.header("Einstellungen")
    
    # Face Recognition Einstellungen
    st.subheader("Gesichtserkennung")
    enable_face_detection = st.checkbox("Gesichtserkennung aktivieren", value=True)
    enable_person_recognition = st.checkbox("Personenerkennung aktivieren", value=True)
    
    # Erweiterte Features (falls verfügbar)
    if FACE_RECOGNIZER_TYPE == "InsightFace":
        enable_emotion_detection = st.checkbox("Emotionserkennung aktivieren", value=True)
        enable_pose_analysis = st.checkbox("Pose-Analyse aktivieren", value=True)
        enable_symmetry_check = st.checkbox("Symmetrie-Prüfung aktivieren", value=True)
        enable_noise_analysis = st.checkbox("Rausch-Analyse aktivieren", value=True)
    else:
        enable_emotion_detection = st.checkbox("Emotionserkennung aktivieren", value=True, disabled=True)
        enable_pose_analysis = st.checkbox("Pose-Analyse aktivieren", value=False, disabled=True)
        enable_symmetry_check = st.checkbox("Symmetrie-Prüfung aktivieren", value=False, disabled=True)
        enable_noise_analysis = st.checkbox("Rausch-Analyse aktivieren", value=False, disabled=True)
        st.info("Erweiterte Features nur mit InsightFace verfügbar")
    
    # Location-Einstellungen
    st.subheader("Standort")
    enable_location = st.checkbox("Standort-Extraktion aktivieren", value=LOCATION_AVAILABLE, disabled=not LOCATION_AVAILABLE)
    
    # Qualitätsfilter
    st.subheader("Qualitätsfilter")
    min_quality = st.slider("Mindestqualität", 0.0, 1.0, 0.3, 0.1)
    min_face_size = st.slider("Mindest-Gesichtsgröße (Pixel)", 50, 200, 80, 10)

# Hauptbereich
st.header("Bilder hochladen")

# Datei-Upload
uploaded_files = st.file_uploader(
    "Wählen Sie Bilder aus",
    type=['jpg', 'jpeg', 'png', 'tiff', 'bmp'],
    accept_multiple_files=True,
    help="Unterstützte Formate: JPG, PNG, TIFF, BMP"
)

if uploaded_files:
    st.write(f"**{len(uploaded_files)} Bilder ausgewählt**")
    
    # Verarbeitungsoptionen
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Verarbeitung starten", type="primary"):
            process_images(uploaded_files, face_recognizer, location_extractor, {
                'enable_face_detection': enable_face_detection,
                'enable_person_recognition': enable_person_recognition,
                'enable_emotion_detection': enable_emotion_detection,
                'enable_pose_analysis': enable_pose_analysis,
                'enable_symmetry_check': enable_symmetry_check,
                'enable_noise_analysis': enable_noise_analysis,
                'enable_location': enable_location,
                'min_quality': min_quality,
                'min_face_size': min_face_size
            })
    
    with col2:
        if st.button("Alle Ergebnisse löschen"):
            if 'results' in st.session_state:
                del st.session_state.results
            st.rerun()

def process_images(uploaded_files, face_recognizer, location_extractor, settings):
    """Verarbeitet die hochgeladenen Bilder"""
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            # Status aktualisieren
            status_text.text(f"Verarbeite: {uploaded_file.name}")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            # Lade Bild
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if img_bgr is None:
                st.warning(f"Konnte Bild nicht laden: {uploaded_file.name}")
                continue
            
            # Extrahiere Metadaten
            metadata = {}
            if settings['enable_location'] and location_extractor:
                try:
                    location_data = location_extractor.extract_location_from_bytes(file_bytes)
                    if location_data:
                        metadata['location'] = location_data
                except Exception as e:
                    st.warning(f"Standort-Extraktion fehlgeschlagen für {uploaded_file.name}: {e}")
            
            # Gesichtserkennung
            persons = []
            if settings['enable_face_detection']:
                try:
                    persons = face_recognizer.detect_faces(img_bgr)
                    
                    # Filtere nach Qualität und Größe
                    filtered_persons = []
                    for person in persons:
                        bbox = person.get('bbox', [])
                        if len(bbox) >= 4:
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]
                            face_size = min(width, height)
                            
                            if (person.get('quality_score', 0) >= settings['min_quality'] and 
                                face_size >= settings['min_face_size']):
                                filtered_persons.append(person)
                    
                    persons = filtered_persons
                    
                except Exception as e:
                    st.warning(f"Gesichtserkennung fehlgeschlagen für {uploaded_file.name}: {e}")
            
            # Erstelle Ergebnis
            result = {
                'image': uploaded_file.name,
                'metadata': metadata,
                'persons': persons,
                'processing_info': {
                    'face_recognizer_type': FACE_RECOGNIZER_TYPE,
                    'settings': settings,
                    'timestamp': str(pd.Timestamp.now())
                }
            }
            
            results.append(result)
            
        except Exception as e:
            st.error(f"Fehler bei {uploaded_file.name}: {e}")
    
    # Speichere Ergebnisse
    st.session_state.results = results
    
    # Zeige Zusammenfassung
    st.success(f"Verarbeitung abgeschlossen! {len(results)} Bilder verarbeitet.")
    
    # Zeige Statistiken
    total_faces = sum(len(result['persons']) for result in results)
    st.metric("Gesichter erkannt", total_faces)
    
    # Download-Button
    if results:
        json_data = json.dumps(results, indent=2, ensure_ascii=False)
        st.download_button(
            label="Ergebnisse als JSON herunterladen",
            data=json_data,
            file_name="annotation_results.json",
            mime="application/json"
        )

# Zeige Ergebnisse
if 'results' in st.session_state and st.session_state.results:
    st.header("Verarbeitungsergebnisse")
    
    results = st.session_state.results
    
    # Zusammenfassung
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bilder verarbeitet", len(results))
    with col2:
        total_faces = sum(len(result['persons']) for result in results)
        st.metric("Gesichter erkannt", total_faces)
    with col3:
        if results:
            avg_faces = total_faces / len(results)
            st.metric("Durchschnitt Gesichter/Bild", f"{avg_faces:.1f}")
    
    # Detaillierte Ergebnisse
    for i, result in enumerate(results):
        with st.expander(f"Bild {i+1}: {result['image']}", expanded=False):
            show_image_results(result, face_recognizer)

def show_image_results(result, face_recognizer):
    """Zeigt die Ergebnisse für ein Bild"""
    
    image_name = result['image']
    persons = result['persons']
    
    if not persons:
        st.info("Keine Gesichter erkannt")
        return
    
    st.write(f"**{len(persons)} Gesichter erkannt**")
    
    # Zeige Gesichter
    for j, person in enumerate(persons):
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.write(f"**Gesicht {j+1}**")
                
                # Basis-Informationen
                if person.get('name'):
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
                if person.get('age'):
                    st.write(f"**Alter:** {person['age']} Jahre")
                if person.get('gender'):
                    st.write(f"**Geschlecht:** {person['gender']}")
            
            with col2:
                # Qualität
                if person.get('quality_score'):
                    quality = person['quality_score']
                    if quality > 0.8:
                        st.success(f"* Exzellent ({quality:.2f})")
                    elif quality > 0.6:
                        st.warning(f"o Gut ({quality:.2f})")
                    elif quality > 0.4:
                        st.info(f". Mittel ({quality:.2f})")
                    else:
                        st.error(f"x Niedrig ({quality:.2f})")
                
                # Emotion
                if person.get('emotion'):
                    st.write(f"**Emotion:** {person['emotion']}")
                
                # Status
                if person.get('eye_status'):
                    st.write(f"**Augen:** {person['eye_status']}")
                if person.get('mouth_status'):
                    st.write(f"**Mund:** {person['mouth_status']}")
            
            with col3:
                # Technische Details
                if person.get('bbox'):
                    bbox = person['bbox']
                    st.write(f"**Position:** ({bbox[0]}, {bbox[1]})")
                    st.write(f"**Größe:** {bbox[2]-bbox[0]}x{bbox[3]-bbox[1]}")
                
                # Erweiterte Metriken (falls verfügbar)
                if FACE_RECOGNIZER_TYPE == "InsightFace":
                    if person.get('symmetry_score'):
                        st.write(f"**Symmetrie:** {person['symmetry_score']:.2f}")
                    if person.get('noise_score'):
                        st.write(f"**Rausch:** {person['noise_score']:.2f}")
            
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("**Photo Metadata Suite - Big Sur Edition**")
st.markdown(f"Face Recognizer: {FACE_RECOGNIZER_TYPE}")
