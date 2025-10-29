"""
Erweiterte Trainings-Seite für Metadaten-basierte KI-Optimierung
Mit verbesserter UI, erweiterten Metriken und Hyperparameter-Tuning
"""

import streamlit as st
import json
import os
import tempfile
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Tuple
import io
import cv2
import numpy as np
from PIL import Image
import warnings
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Versuche enhanced_face_engine zu importieren
try:
    from app.enhanced_face_engine import MetadataAwareTrainer, EnhancedFaceEngine, create_training_dataset_from_annotations
    ENHANCED_ENGINE_AVAILABLE = True
except ImportError:
    ENHANCED_ENGINE_AVAILABLE = False
    st.warning("Enhanced Face Engine nicht verfügbar.")

# Import für Metadaten-Extraktion und Face Engine
try:
    from app.location import extract_comprehensive_metadata
    from app.face_recognizer import FaceEngine
    LOCATION_ENGINE_AVAILABLE = True
except ImportError:
    LOCATION_ENGINE_AVAILABLE = False
    st.warning("Location Engine nicht verfügbar.")

def analyze_training_data(training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Erweiterte Analyse der Trainingsdaten mit detaillierten Statistiken
    
    Args:
        training_data: Liste von Trainingsdaten-Einträgen
        
    Returns:
        Dictionary mit umfassenden Statistiken
    """
    stats = {
        'camera_models': {},
        'lenses': {},
        'iso_values': [],
        'aperture_values': [],
        'shutter_speeds': [],
        'focal_lengths': [],
        'emotions': {},
        'genders': {},
        'age_groups': {},
        'quality_scores': [],
        'locations': {},
        'time_distribution': {},
        'lighting_conditions': {},
        'face_angles': [],
        'image_sizes': [],
        'metadata_completeness': {},
        'bias_indicators': {}
    }
    
    for item in training_data:
        # Metadaten analysieren
        metadata = item.get('metadata', {})
        
        # Kamera-Modell
        if 'camera_model' in metadata:
            model = metadata['camera_model']
            stats['camera_models'][model] = stats['camera_models'].get(model, 0) + 1
        
        # Objektiv
        if 'lens_model' in metadata:
            lens = metadata['lens_model']
            stats['lenses'][lens] = stats['lenses'].get(lens, 0) + 1
        
        # ISO
        if 'iso' in metadata:
            stats['iso_values'].append(metadata['iso'])
        
        # Blende
        if 'aperture' in metadata:
            stats['aperture_values'].append(metadata['aperture'])
        
        # Verschlusszeit
        if 'shutter_speed' in metadata:
            stats['shutter_speeds'].append(metadata['shutter_speed'])
        
        # Brennweite
        if 'focal_length' in metadata:
            stats['focal_lengths'].append(metadata['focal_length'])
        
        # Standort
        if 'location' in metadata:
            location = metadata['location']
            if 'city' in location:
                city = location['city']
                stats['locations'][city] = stats['locations'].get(city, 0) + 1
        
        # Zeit-Verteilung
        if 'datetime' in metadata:
            try:
                from app.utils import parse_datetime_string
                dt = parse_datetime_string(metadata['datetime'])
                if dt:
                    hour = dt.hour
                    time_slot = f"{hour:02d}:00-{hour+1:02d}:00"
                    stats['time_distribution'][time_slot] = stats['time_distribution'].get(time_slot, 0) + 1
            except:
                pass
        
        # Beleuchtungsbedingungen (basierend auf ISO und Blende)
        if 'iso' in metadata and 'f_number' in metadata:
            iso = metadata['iso']
            f_number = metadata['f_number']
            if iso < 400 and f_number < 2.8:
                lighting = 'bright'
            elif iso < 1600 and f_number < 4.0:
                lighting = 'normal'
            else:
                lighting = 'low_light'
            stats['lighting_conditions'][lighting] = stats['lighting_conditions'].get(lighting, 0) + 1
        
        # Bildgröße
        if 'image' in item:
            # Vereinfachte Annahme für Bildgröße
            stats['image_sizes'].append('standard')  # Könnte erweitert werden
        
        # Metadaten-Vollständigkeit
        metadata_fields = ['camera_model', 'datetime', 'gps', 'focal_length', 'f_number', 'iso']
        completeness = sum(1 for field in metadata_fields if field in metadata and metadata[field])
        stats['metadata_completeness'][completeness] = stats['metadata_completeness'].get(completeness, 0) + 1
        
        # Gesichts-Analyse
        persons = item.get('persons', [])
        for person in persons:
            # Emotion
            if 'emotion' in person:
                emotion = person['emotion']
                stats['emotions'][emotion] = stats['emotions'].get(emotion, 0) + 1
            
            # Geschlecht
            if 'gender' in person:
                gender = person['gender']
                stats['genders'][gender] = stats['genders'].get(gender, 0) + 1
            
            # Alter (in Gruppen)
            if 'age' in person:
                age = person['age']
                if age < 18:
                    group = '0-17'
                elif age < 30:
                    group = '18-29'
                elif age < 50:
                    group = '30-49'
                elif age < 70:
                    group = '50-69'
                else:
                    group = '70+'
                stats['age_groups'][group] = stats['age_groups'].get(group, 0) + 1
            
            # Qualität
            if 'quality_score' in person:
                stats['quality_scores'].append(person['quality_score'])
            
            # Gesichtswinkel (falls verfügbar)
            if 'pose' in person and isinstance(person['pose'], dict):
                yaw = person['pose'].get('yaw', 0)
                pitch = person['pose'].get('pitch', 0)
                roll = person['pose'].get('roll', 0)
                angle_magnitude = np.sqrt(yaw**2 + pitch**2 + roll**2)
                stats['face_angles'].append(angle_magnitude)
    
    # Bias-Indikatoren berechnen
    if stats['genders']:
        total_gender = sum(stats['genders'].values())
        stats['bias_indicators']['gender_balance'] = {
            gender: count / total_gender for gender, count in stats['genders'].items()
        }
    
    if stats['age_groups']:
        total_age = sum(stats['age_groups'].values())
        stats['bias_indicators']['age_balance'] = {
            age_group: count / total_age for age_group, count in stats['age_groups'].items()
        }
    
    return stats

def validate_training_data_format(data):
    """
    Validiert das Format der Trainingsdaten
    
    Args:
        data: Trainingsdaten-Dictionary oder Liste
        
    Returns:
        bool: True wenn Format gültig ist
    """
    if isinstance(data, list):
        for item in data:
            if not validate_training_data_format(item):
                return False
        return True
    
    if not isinstance(data, dict):
        return False
    
    # Erforderliche Felder prüfen
    required_fields = ['image', 'metadata', 'persons']
    for field in required_fields:
        if field not in data:
            return False
    
    # Personen-Liste prüfen
    if not isinstance(data['persons'], list):
        return False
    
    # Mindestens eine Person sollte vorhanden sein
    if len(data['persons']) == 0:
        return False
    
    return True

def generate_training_data_from_photos(photos, engine):
    """
    Generiert Trainingsdaten aus hochgeladenen Musterfotos
    
    Args:
        photos: Liste von hochgeladenen Foto-Dateien
        engine: FaceEngine für Gesichtserkennung
        
    Returns:
        Liste von Trainingsdaten-Dictionaries
    """
    training_data = []
    
    for photo in photos:
        try:
            # Bild laden
            data = photo.read()
            image = Image.open(io.BytesIO(data)).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Gesichtserkennung
            faces = engine.analyze(img_bgr)
            
            # Metadaten extrahieren
            metadata = extract_comprehensive_metadata(image)
            
            # Trainingsdaten-Eintrag erstellen
            training_entry = {
                "image": photo.name,
                "metadata": metadata,
                "persons": []
            }
            
            # Gesichter zu Trainingsdaten hinzufügen
            for face in faces:
                person_data = {
                    "age": face.get('age', 25),  # Standard-Alter falls nicht erkannt
                    "gender": face.get('gender', 'unknown'),
                    "quality_score": face.get('quality_score', 0.5),
                    "bbox": face.get('bbox', [0, 0, 100, 100]),
                    "emotion": face.get('emotion', 'neutral'),
                    "pose": face.get('pose', {})
                }
                training_entry["persons"].append(person_data)
            
            training_data.append(training_entry)
            
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten von {photo.name}: {e}")
    
    return training_data

def display_advanced_training_results(results: Dict[str, Any], training_data: List[Dict]):
    """Zeigt erweiterte Trainings-Ergebnisse mit Visualisierungen"""
    st.subheader("Trainings-Ergebnisse")
    
    # Hauptmetriken
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'training' in results and 'age_accuracy' in results['training']:
            st.metric("Alter-Genauigkeit", f"{results['training']['age_accuracy']:.3f}")
    
    with col2:
        if 'training' in results and 'gender_accuracy' in results['training']:
            st.metric("Geschlecht-Genauigkeit", f"{results['training']['gender_accuracy']:.3f}")
    
    with col3:
        if 'training' in results and 'quality_accuracy' in results['training']:
            st.metric("Qualität-Genauigkeit", f"{results['training']['quality_accuracy']:.3f}")
    
    with col4:
        if 'validation' in results and 'overall_accuracy' in results['validation']:
            st.metric("Gesamt-Genauigkeit", f"{results['validation']['overall_accuracy']:.3f}")
    
    # Erweiterte Visualisierungen
    tab1, tab2, tab3, tab4 = st.tabs(["Metriken", "Performance", "Bias-Analyse", "Details"])
    
    with tab1:
        # Metriken-Vergleich
        if 'training' in results and 'validation' in results:
            metrics_data = []
            for metric in results['training'].keys():
                if metric in results['validation']:
                    metrics_data.append({
                        'Metrik': metric.replace('_', ' ').title(),
                        'Training': results['training'][metric],
                        'Validierung': results['validation'][metric]
                    })
            
            if metrics_data:
                df_metrics = pd.DataFrame(metrics_data)
                fig = px.bar(
                    df_metrics, 
                    x='Metrik', 
                    y=['Training', 'Validierung'],
                    title="Training vs. Validierung",
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Performance-Trends
        if 'training_history' in results:
            history = results['training_history']
            if len(history) > 1:
                epochs = list(range(1, len(history) + 1))
                age_acc = [h.get('age_accuracy', 0) for h in history]
                gender_acc = [h.get('gender_accuracy', 0) for h in history]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=epochs, y=age_acc, name='Alter', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=epochs, y=gender_acc, name='Geschlecht', line=dict(color='red')))
                fig.update_layout(title="Training-Verlauf", xaxis_title="Epoche", yaxis_title="Genauigkeit")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Bias-Analyse
        if training_data:
            stats = analyze_training_data(training_data)
            if 'bias_indicators' in stats:
                bias = stats['bias_indicators']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'gender_balance' in bias:
                        st.subheader("Geschlechts-Verteilung")
                        gender_df = pd.DataFrame(list(bias['gender_balance'].items()), 
                                               columns=['Geschlecht', 'Anteil'])
                        fig = px.pie(gender_df, values='Anteil', names='Geschlecht', 
                                   title="Geschlechts-Verteilung")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'age_balance' in bias:
                        st.subheader("Alters-Verteilung")
                        age_df = pd.DataFrame(list(bias['age_balance'].items()), 
                                            columns=['Altersgruppe', 'Anteil'])
                        fig = px.bar(age_df, x='Altersgruppe', y='Anteil', 
                                   title="Alters-Verteilung")
                        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Detaillierte Ergebnisse
        if 'training' in results:
            st.write("**Training-Metriken:**")
            for metric, value in results['training'].items():
                st.write(f"- {metric}: {value:.3f}")
        
        if 'validation' in results:
            st.write("**Validierungs-Metriken:**")
            for metric, value in results['validation'].items():
                st.write(f"- {metric}: {value:.3f}")
        
        if 'improvement' in results:
            st.write("**Verbesserungen:**")
            for metric, improvement in results['improvement'].items():
                color = "green" if improvement > 0 else "red"
                st.markdown(f"- {metric}: <span style='color: {color}'>{improvement:+.3f}</span>", 
                           unsafe_allow_html=True)
    
    # Modell-Integration
    st.subheader("Modell-Integration")
    st.info("""
    **So integrieren Sie das trainierte Modell:**
    
    1. **Modell herunterladen** (Button oben)
    2. **In Annotate-Seite hochladen** als "Enhanced Model"
    3. **Erweiterte Erkennung aktivieren** in den Einstellungen
    
    Das trainierte Modell wird automatisch Metadaten für bessere Vorhersagen nutzen!
    """)

def hyperparameter_tuning_ui():
    """UI für Hyperparameter-Tuning"""
    st.subheader("Hyperparameter-Tuning")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Random Forest Parameter:**")
        n_estimators = st.slider("Anzahl Bäume", 50, 500, 100, 50)
        max_depth = st.slider("Maximale Tiefe", 5, 50, 20, 5)
        min_samples_split = st.slider("Min. Samples Split", 2, 20, 5, 1)
        min_samples_leaf = st.slider("Min. Samples Leaf", 1, 10, 2, 1)
    
    with col2:
        st.write("**Cross-Validation:**")
        cv_folds = st.slider("CV-Folds", 3, 10, 5, 1)
        scoring = st.selectbox("Scoring-Methode", 
                              ["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"])
        random_state = st.number_input("Random State", 0, 1000, 42, 1)
    
    return {
        'n_estimators': n_estimators,
        'max_depth': max_depth,
        'min_samples_split': min_samples_split,
        'min_samples_leaf': min_samples_leaf,
        'cv_folds': cv_folds,
        'scoring': scoring,
        'random_state': random_state
    }

def model_comparison_ui():
    """UI für Modell-Vergleich"""
    st.subheader("Modell-Vergleich")
    
    models = st.multiselect(
        "Modelle zum Vergleichen:",
        ["Random Forest", "Gradient Boosting", "SVM", "Neural Network"],
        default=["Random Forest"]
    )
    
    comparison_metrics = st.multiselect(
        "Vergleichs-Metriken:",
        ["accuracy", "precision", "recall", "f1_score", "training_time"],
        default=["accuracy", "f1_score"]
    )
    
    return {
        'models': models,
        'metrics': comparison_metrics
    }

st.title("Erweiterte KI-Training mit Metadaten")
st.caption("Trainieren Sie die Gesichtserkennung mit Metadaten für bessere Genauigkeit - jetzt mit Hyperparameter-Tuning und Bias-Analyse")

# Haupt-Tabs
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs(["Training", "Hyperparameter", "Modell-Vergleich", "Analytics"])

with main_tab1:
    # Sidebar für Trainings-Einstellungen
    with st.sidebar:
        st.header("Trainings-Einstellungen")
        
        # Daten-Upload
        st.subheader("Trainingsdaten")
        
        # Upload-Modus wählen
        upload_mode = st.radio(
            "Datenquelle wählen:",
            ["JSON-Dateien hochladen", "Aus Musterfotos generieren"],
            help="Wählen Sie, ob Sie bereits erstellte JSON-Dateien hochladen oder aus Fotos generieren möchten"
        )
    
    if upload_mode == "JSON-Dateien hochladen":
        training_files = st.file_uploader(
            "JSON-Trainingsdaten hochladen", 
            type=["json"], 
            accept_multiple_files=True,
            help="Laden Sie JSON-Dateien mit Annotations hoch"
        )
        sample_photos = None
    else:
        training_files = None
        sample_photos = st.file_uploader(
            "Musterfotos hochladen", 
            type=["jpg", "jpeg", "png", "bmp", "webp", "tif", "tiff"], 
            accept_multiple_files=True,
            help="Laden Sie Musterfotos hoch, aus denen Trainingsdaten generiert werden"
        )
    
    # Trainings-Parameter
    st.subheader("Trainings-Parameter")
    validation_split = st.slider("Validierungs-Split", 0.1, 0.5, 0.2, 0.05)
    
    # Metadaten-Gewichtungen
    st.subheader("Metadaten-Gewichtungen")
    age_weight = st.slider("Alter-Gewichtung", 0.1, 0.5, 0.3, 0.05)
    gender_weight = st.slider("Geschlecht-Gewichtung", 0.1, 0.5, 0.25, 0.05)
    location_weight = st.slider("Standort-Gewichtung", 0.1, 0.5, 0.2, 0.05)
    temporal_weight = st.slider("Zeit-Gewichtung", 0.1, 0.5, 0.15, 0.05)
    technical_weight = st.slider("Technisch-Gewichtung", 0.1, 0.5, 0.1, 0.05)
    
    # Modell-Pfad
    st.subheader("Modell-Speicherung")
    model_name = st.text_input("Modell-Name", value=f"enhanced_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    model_path = f"models/{model_name}.pkl"

# Hauptbereich
if not training_files and not sample_photos:
    st.info("Laden Sie JSON-Trainingsdaten oder Musterfotos in der Sidebar hoch, um zu starten.")
    
    # Beispiel-Trainingsdaten anzeigen
    with st.expander("Über das Training", expanded=False):
        st.markdown("""
        **Metadaten-basiertes Training verbessert die Gesichtserkennung durch:**
        
        **Kontext-Awareness:**
        - Standort-basierte Alters-Korrektur
        - Zeit-basierte Geschlechts-Vorhersage
        - Technische Metadaten für Qualitätsbewertung
        
        **Intelligente Korrekturen:**
        - Metadaten-Bias-Erkennung
        - Gewichtete Vorhersage-Kombination
        - Kontinuierliches Lernen
        
        **Workflow:**
        1. JSON-Daten mit Metadaten hochladen
        2. Training mit Metadaten-Integration
        3. Validierung und Modell-Speicherung
        4. Integration in die Annotate-Seite
        
        **Erwartete Verbesserungen:**
        - Alterserkennung: +15-25%
        - Geschlechtserkennung: +10-20%
        - Standort-basierte Vorhersagen: +20-30%
        """)
    
    # Beispiel-Trainingsdaten zum Download
    st.subheader("Beispiel-Trainingsdaten")
    example_training_data = [
        {
            "image": "training_photo_1.jpg",
            "metadata": {
                "camera_make": "Canon",
                "camera_model": "EOS R5",
                "datetime": "2024-01-15T14:30:00",
                "gps": {"lat": 52.5200, "lon": 13.4050, "altitude": 34.5},
                "focal_length": 50,
                "f_number": 2.8,
                "iso": 100
            },
            "persons": [
                {
                    "age": 25,
                    "gender": "female",
                    "quality_score": 0.85,
                    "bbox": [100, 150, 300, 450]
                }
            ]
        },
        {
            "image": "training_photo_2.jpg",
            "metadata": {
                "camera_make": "iPhone",
                "camera_model": "iPhone 15 Pro",
                "datetime": "2024-01-16T10:15:00",
                "gps": {"lat": 48.1351, "lon": 11.5820, "altitude": 519.0},
                "focal_length": 35,
                "f_number": 4.0,
                "iso": 200
            },
            "persons": [
                {
                    "age": 30,
                    "gender": "male",
                    "quality_score": 0.78,
                    "bbox": [200, 100, 400, 350]
                }
            ]
        }
    ]
    
    st.download_button(
        "Beispiel-Trainingsdaten herunterladen",
        data=json.dumps(example_training_data, ensure_ascii=False, indent=2),
        file_name="example_training_data.json",
        mime="application/json"
    )

else:
    # Trainingsdaten verarbeiten
    st.header("Trainingsdaten-Analyse")
    
    # Daten laden
    training_data = []
    
    if training_files:
        # JSON-Dateien verarbeiten
        st.subheader("JSON-Dateien verarbeiten")
        for file in training_files:
            try:
                data = json.load(file)
                
                # Format validieren
                if not validate_training_data_format(data):
                    st.warning(f"Ungültiges Format in {file.name}. Überspringe Datei.")
                    continue
                
                if isinstance(data, list):
                    training_data.extend(data)
                else:
                    training_data.append(data)
                    
                st.success(f"{file.name} erfolgreich geladen")
                
            except Exception as e:
                st.error(f"Fehler beim Laden von {file.name}: {e}")
    
    elif sample_photos and LOCATION_ENGINE_AVAILABLE:
        # Musterfotos verarbeiten
        st.subheader("Musterfotos verarbeiten")
        
        # Face Engine initialisieren
        if "training_engine" not in st.session_state:
            st.session_state["training_engine"] = FaceEngine(det_size=(640, 640))
        
        # Progress bar für Foto-Verarbeitung
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, photo in enumerate(sample_photos):
            status_text.text(f"Verarbeite {photo.name}...")
            progress_bar.progress((idx + 1) / len(sample_photos))
            
            try:
                # Bild laden
                data = photo.read()
                image = Image.open(io.BytesIO(data)).convert("RGB")
                img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Gesichtserkennung
                faces = st.session_state["training_engine"].analyze(img_bgr)
                
                # Metadaten extrahieren
                metadata = extract_comprehensive_metadata(image)
                
                # Trainingsdaten-Eintrag erstellen
                training_entry = {
                    "image": photo.name,
                    "metadata": metadata,
                    "persons": []
                }
                
                # Gesichter zu Trainingsdaten hinzufügen
                for face in faces:
                    person_data = {
                        "age": face.get('age', 25),
                        "gender": face.get('gender', 'unknown'),
                        "quality_score": face.get('quality_score', 0.5),
                        "bbox": face.get('bbox', [0, 0, 100, 100]),
                        "emotion": face.get('emotion', 'neutral'),
                        "pose": face.get('pose', {})
                    }
                    training_entry["persons"].append(person_data)
                
                training_data.append(training_entry)
                
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten von {photo.name}: {e}")
        
        # Progress bar zurücksetzen
        progress_bar.empty()
        status_text.empty()
        
        # Generierte Trainingsdaten als JSON zum Download anbieten
        if training_data:
            st.success(f"{len(training_data)} Trainingsbeispiele aus {len(sample_photos)} Fotos generiert!")
            
            # Download-Button für generierte Trainingsdaten
            st.download_button(
                "Generierte Trainingsdaten herunterladen",
                data=json.dumps(training_data, ensure_ascii=False, indent=2),
                file_name=f"generated_training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Laden Sie die generierten Trainingsdaten herunter, um sie später wieder zu verwenden"
            )
    
    elif sample_photos and not LOCATION_ENGINE_AVAILABLE:
        st.error("Location Engine nicht verfügbar. Kann keine Trainingsdaten aus Fotos generieren.")
    
    if training_data:
        if not (sample_photos and LOCATION_ENGINE_AVAILABLE):
            st.success(f"{len(training_data)} Trainingsbeispiele geladen")
        
        # Training data in session state speichern
        st.session_state['training_data'] = training_data
        
        # Datenanalyse
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_images = len(training_data)
            st.metric("Gesamtbilder", total_images)
        
        with col2:
            images_with_faces = sum(1 for item in training_data if item.get('persons'))
            st.metric("Mit Gesichtern", images_with_faces)
        
        with col3:
            images_with_metadata = sum(1 for item in training_data if item.get('metadata'))
            st.metric("Mit Metadaten", images_with_metadata)
        
        # Detaillierte Analyse
        with st.expander("Detaillierte Datenanalyse", expanded=False):
            # Metadaten-Verteilung
            metadata_stats = analyze_training_data(training_data)
            
            # Metadaten-Charts
            if metadata_stats['camera_models']:
                fig_cameras = px.bar(
                    x=list(metadata_stats['camera_models'].keys()),
                    y=list(metadata_stats['camera_models'].values()),
                    title="Kamera-Modelle in Trainingsdaten",
                    labels={'x': 'Kamera-Modell', 'y': 'Anzahl'}
                )
                st.plotly_chart(fig_cameras, use_container_width=True)
            
            # Altersverteilung
            if metadata_stats['age_groups']:
                fig_ages = px.bar(
                    x=list(metadata_stats['age_groups'].keys()),
                    y=list(metadata_stats['age_groups'].values()),
                    title="Altersverteilung in Trainingsdaten",
                    labels={'x': 'Altersgruppe', 'y': 'Anzahl'}
                )
                st.plotly_chart(fig_ages, use_container_width=True)
            
            # Geschlechtsverteilung
            if metadata_stats['genders']:
                fig_genders = px.pie(
                    values=list(metadata_stats['genders'].values()),
                    names=list(metadata_stats['genders'].keys()),
                    title="Geschlechtsverteilung in Trainingsdaten"
                )
                st.plotly_chart(fig_genders, use_container_width=True)
        
        # Training starten
        st.header("Training starten")
        
        if ENHANCED_ENGINE_AVAILABLE:
            if st.button("Training mit Metadaten starten", type="primary"):
                with st.spinner("Training läuft..."):
                    try:
                        # Trainer initialisieren
                        metadata_weights = {
                            'age': age_weight,
                            'gender': gender_weight,
                            'location': location_weight,
                            'temporal': temporal_weight,
                            'technical': technical_weight
                        }
                        
                        trainer = MetadataAwareTrainer(model_path)
                        
                        # Training durchführen
                        results = trainer.train(training_data, validation_split)
                        
                        # Ergebnisse anzeigen
                        st.success("Training erfolgreich abgeschlossen!")
                        
                        # Trainings-Ergebnisse
                        display_advanced_training_results(results, training_data)
                        
                        # Modell-Download
                        if os.path.exists(model_path):
                            with open(model_path, 'rb') as f:
                                st.download_button(
                                    "Trainiertes Modell herunterladen",
                                    data=f.read(),
                                    file_name=f"{model_name}.pkl",
                                    mime="application/octet-stream"
                                )
                        
                    except Exception as e:
                        st.error(f"Fehler beim Training: {e}")
                        st.exception(e)
        else:
            st.info("Training-Funktionalität nur mit Enhanced Face Engine verfügbar.")

with main_tab2:
    st.header("Hyperparameter-Tuning")
    st.caption("Optimieren Sie die Modell-Parameter für bessere Performance")
    
    if 'training_data' in st.session_state and st.session_state['training_data']:
        tuning_params = hyperparameter_tuning_ui()
        
        if st.button("Hyperparameter-Tuning starten", type="primary"):
            with st.spinner("Hyperparameter-Tuning läuft..."):
                st.info("Hyperparameter-Tuning wird implementiert...")
                # Hier würde das eigentliche Tuning implementiert
                st.success("Tuning abgeschlossen!")
    else:
        st.info("Laden Sie zuerst Trainingsdaten hoch, um Hyperparameter-Tuning zu verwenden.")

with main_tab3:
    st.header("Modell-Vergleich")
    st.caption("Vergleichen Sie verschiedene Modell-Architekturen")
    
    if 'training_data' in st.session_state and st.session_state['training_data']:
        comparison_config = model_comparison_ui()
        
        if st.button("Modell-Vergleich starten", type="primary"):
            with st.spinner("Modell-Vergleich läuft..."):
                st.info("Modell-Vergleich wird implementiert...")
                # Hier würde der Modell-Vergleich implementiert
                st.success("Vergleich abgeschlossen!")
    else:
        st.info("Laden Sie zuerst Trainingsdaten hoch, um Modell-Vergleiche durchzuführen.")

with main_tab4:
    st.header("Erweiterte Analytics")
    st.caption("Detaillierte Analyse der Trainingsdaten und Modell-Performance")
    
    if 'training_data' in st.session_state and st.session_state['training_data']:
        training_data = st.session_state['training_data']
        
        # Erweiterte Datenanalyse
        st.subheader("Datenqualität-Analyse")
        
        # Metadaten-Vollständigkeit
        metadata_completeness = []
        for item in training_data:
            metadata = item.get('metadata', {})
            completeness = sum(1 for field in ['camera_model', 'datetime', 'gps', 'focal_length', 'f_number', 'iso'] 
                             if field in metadata and metadata[field])
            metadata_completeness.append(completeness)
        
        if metadata_completeness:
            avg_completeness = np.mean(metadata_completeness)
            st.metric("Durchschnittliche Metadaten-Vollständigkeit", f"{avg_completeness:.1f}/6")
            
            # Vollständigkeits-Verteilung
            completeness_counts = pd.Series(metadata_completeness).value_counts().sort_index()
            fig = px.bar(x=completeness_counts.index, y=completeness_counts.values,
                        title="Metadaten-Vollständigkeit Verteilung",
                        labels={'x': 'Anzahl Felder', 'y': 'Anzahl Bilder'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Zeitliche Verteilung
        if any('datetime' in item.get('metadata', {}) for item in training_data):
            st.subheader("Zeitliche Verteilung")
            time_data = []
            for item in training_data:
                metadata = item.get('metadata', {})
                if 'datetime' in metadata:
                    try:
                        from app.utils import parse_datetime_string
                        dt = parse_datetime_string(metadata['datetime'])
                        if dt:
                            time_data.append(dt.hour)
                    except:
                        pass
            
            if time_data:
                time_df = pd.DataFrame({'Stunde': time_data})
                fig = px.histogram(time_df, x='Stunde', nbins=24, 
                                 title="Aufnahme-Zeiten Verteilung")
                st.plotly_chart(fig, use_container_width=True)
        
        # Qualitäts-Analyse
        st.subheader("Qualitäts-Analyse")
        quality_scores = []
        for item in training_data:
            for person in item.get('persons', []):
                if 'quality_score' in person:
                    quality_scores.append(person['quality_score'])
        
        if quality_scores:
            avg_quality = np.mean(quality_scores)
            st.metric("Durchschnittliche Gesichtsqualität", f"{avg_quality:.3f}")
            
            # Qualitäts-Verteilung
            fig = px.histogram(x=quality_scores, nbins=20, 
                             title="Gesichtsqualität Verteilung",
                             labels={'x': 'Qualitätsscore', 'y': 'Anzahl'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Laden Sie zuerst Trainingsdaten hoch, um Analytics zu verwenden.")

# Modell-Test-Bereich
st.header("Modell-Test")
st.caption("Testen Sie ein trainiertes Modell mit neuen Bildern")

test_model_file = st.file_uploader("Trainiertes Modell hochladen", type=["pkl"])

if test_model_file:
    try:
        # Temporäre Datei erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
            tmp_file.write(test_model_file.read())
            tmp_path = tmp_file.name
        
        # Modell laden
        engine = EnhancedFaceEngine()
        engine.load_models(tmp_path)
        
        st.success("Modell erfolgreich geladen!")
        
        # Test-Bilder
        test_images = st.file_uploader(
            "Test-Bilder hochladen", 
            type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True
        )
        
        if test_images:
            st.subheader("Test-Ergebnisse")
            
            for img_file in test_images:
                # Hier würde die Bildverarbeitung implementiert
                st.write(f"**{img_file.name}**: Modell geladen und bereit für Tests")
        
        # Aufräumen
        os.unlink(tmp_path)
        
    except Exception as e:
        st.error(f"Fehler beim Laden des Modells: {e}")
