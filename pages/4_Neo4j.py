"""
Neo4j Datenbank-Integration
Importiert JSON-Dateien in Neo4j und ermöglicht Abfragen der Gesichtserkennungs-Daten
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import logging
import sys
import os

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.neo4j_connector import Neo4jManager
from streamlit_styles import apply_custom_css

# Wende kleinere Schriftgrößen an
apply_custom_css()

st.set_page_config(page_title="Neo4j Integration")

st.title("Neo4j Datenbank-Integration")
st.caption("Import und Abfrage von Gesichtserkennungs-Daten in Neo4j")

# Initialisiere Neo4j Manager
if "neo4j_manager" not in st.session_state:
    st.session_state.neo4j_manager = Neo4jManager()

# Sidebar für Datenbankverbindung
with st.sidebar:
    st.header("Datenbankverbindung")
    
    # Verbindungsstatus
    if st.session_state.neo4j_manager.connected:
        st.success("Verbunden mit Neo4j")
    else:
        st.error("Nicht verbunden")
    
    # Verbindungseinstellungen
    with st.expander("Verbindungseinstellungen", expanded=not st.session_state.neo4j_manager.connected):
        uri = st.text_input("URI", value="bolt://localhost:7687", help="Neo4j-Verbindungs-URI")
        username = st.text_input("Benutzername", value="neo4j")
        password = st.text_input("Passwort", type="password", value="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verbinden"):
                with st.spinner("Verbinde mit Neo4j..."):
                    success = st.session_state.neo4j_manager.connect(uri, username, password)
                    if success:
                        st.success("Erfolgreich verbunden!")
                        st.rerun()
                    else:
                        st.error("Verbindung fehlgeschlagen!")
        
        with col2:
            if st.button("Trennen"):
                st.session_state.neo4j_manager.disconnect()
                st.rerun()

# Hauptinhalt
if not st.session_state.neo4j_manager.connected:
    st.info("Bitte verbinden Sie sich zuerst mit der Neo4j-Datenbank in der Sidebar.")
    
    # Anleitung
    with st.expander("Neo4j Setup-Anleitung", expanded=True):
        st.markdown("""
        **So richten Sie Neo4j ein:**
        
        1. **Neo4j installieren:**
           - Docker: `docker run -p 7474:7474 -p 7687:7687 neo4j:latest`
           - Oder Neo4j Desktop herunterladen
        
        2. **Standard-Verbindung:**
           - URI: `bolt://localhost:7687`
           - Benutzername: `neo4j`
           - Passwort: `password` (oder Ihr gewähltes Passwort)
        
        3. **Web-Interface:**
           - Öffnen Sie http://localhost:7474
           - Melden Sie sich mit Ihren Anmeldedaten an
        
        4. **Python-Treiber installieren:**
           ```bash
           pip install neo4j
           ```
        """)
    
    st.stop()

# Haupttabs
tab1, tab2, tab3, tab4 = st.tabs(["Import", "Statistiken", "Abfragen", "Verwaltung"])

with tab1:
    st.header("JSON-Daten importieren")
    
    # Datei-Upload
    uploaded_file = st.file_uploader(
        "JSON-Datei hochladen", 
        type=["json"],
        help="Laden Sie eine JSON-Datei hoch, die von der Annotate-Seite erstellt wurde"
    )
    
    if uploaded_file is not None:
        try:
            # Lade JSON-Daten
            json_data = json.load(uploaded_file)
            
            if not isinstance(json_data, list):
                json_data = [json_data]
            
            st.success(f"JSON-Datei geladen: {len(json_data)} Bilder")
            
            # Zeige Vorschau
            with st.expander("Datenvorschau", expanded=False):
                st.json(json_data[0] if json_data else {})
            
            # Import-Button
            if st.button("In Neo4j importieren", type="primary"):
                with st.spinner("Importiere Daten in Neo4j..."):
                    try:
                        stats = st.session_state.neo4j_manager.import_json_data(json_data)
                        
                        st.success("Import erfolgreich!")
                        
                        # Zeige Statistiken
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Bilder", stats.get('images_created', 0))
                        with col2:
                            st.metric("Gesichter", stats.get('faces_created', 0))
                        with col3:
                            st.metric("Personen", stats.get('persons_created', 0))
                        with col4:
                            st.metric("Standorte", stats.get('locations_created', 0))
                        with col5:
                            st.metric("Beziehungen", stats.get('relationships_created', 0))
                    
                    except Exception as e:
                        st.error(f"Fehler beim Import: {e}")

        except Exception as e:
            st.error(f"Fehler beim Laden der JSON-Datei: {e}")

with tab2:
    st.header("Datenbank-Statistiken")
    
    if st.button("Statistiken aktualisieren"):
        with st.spinner("Lade Statistiken..."):
            try:
                stats = st.session_state.neo4j_manager.get_statistics()
                
                # Grundstatistiken
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Bilder", stats.get('total_images', 0))
                with col2:
                    st.metric("Gesichter", stats.get('total_faces', 0))
                with col3:
                    st.metric("Personen", stats.get('total_persons', 0))
                with col4:
                    st.metric("Standorte", stats.get('total_locations', 0))
                
                # Qualitätsstatistiken
                quality_stats = stats.get('quality_distribution', {})
                if quality_stats:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Ø Qualität", f"{quality_stats.get('avg_quality', 0):.2f}")
                    with col2:
                        st.metric("Min. Qualität", f"{quality_stats.get('min_quality', 0):.2f}")
                    with col3:
                        st.metric("Max. Qualität", f"{quality_stats.get('max_quality', 0):.2f}")
                
                # Emotionsverteilung
                emotion_dist = stats.get('emotion_distribution', {})
                if emotion_dist:
                    st.subheader("Emotionsverteilung")
                    
                    # Erstelle DataFrame für Plot
                    emotion_df = pd.DataFrame([
                        {'Emotion': emotion, 'Anzahl': count} 
                        for emotion, count in emotion_dist.items()
                    ])
                    
                    if not emotion_df.empty:
                        fig = px.pie(emotion_df, values='Anzahl', names='Emotion', 
                                   title="Verteilung der Emotionen")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabelle
                        st.dataframe(emotion_df, use_container_width=True)
                
                # Geschlechtsverteilung
                gender_dist = stats.get('gender_distribution', {})
                if gender_dist:
                    st.subheader("Geschlechtsverteilung")
                    
                    gender_df = pd.DataFrame([
                        {'Geschlecht': gender, 'Anzahl': count} 
                        for gender, count in gender_dist.items()
                    ])
                    
                    if not gender_df.empty:
                        fig = px.bar(gender_df, x='Geschlecht', y='Anzahl', 
                                   title="Verteilung der Geschlechter")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabelle
                        st.dataframe(gender_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Fehler beim Laden der Statistiken: {e}")

with tab3:
    st.header("Datenbank-Abfragen")
    
    # Abfrage-Typen
    query_type = st.selectbox(
        "Abfrage-Typ",
        ["Gesichter nach Person", "Gesichter nach Emotion", "Gesichter nach Standort"]
    )
    
    if query_type == "Gesichter nach Person":
        st.subheader("Gesichter nach Person suchen")
        
        # Person auswählen
        person_name = st.text_input("Personenname", placeholder="z.B. Max Mustermann")
        
        if st.button("Suchen"):
            if person_name:
                with st.spinner("Suche Gesichter..."):
                    try:
                        results = st.session_state.neo4j_manager.query_faces_by_person(person_name)
                        
                        if results:
                            st.success(f"{len(results)} Gesichter gefunden")
                            
                            # Zeige Ergebnisse
                            for i, result in enumerate(results):
                                with st.expander(f"Gesicht {i+1}", expanded=False):
                                    face = result.get('f', {})
                                    image = result.get('i', {})
                                    person = result.get('p', {})
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write("**Gesichtsdaten:**")
                                        st.write(f"Alter: {face.get('age', 'N/A')}")
                                        st.write(f"Geschlecht: {face.get('gender', 'N/A')}")
                                        st.write(f"Emotion: {face.get('emotion', 'N/A')}")
                                        st.write(f"Qualität: {face.get('quality_score', 'N/A')}")
                                    
                                    with col2:
                                        st.write("**Bilddaten:**")
                                        st.write(f"Datei: {image.get('filename', 'N/A')}")
                                        st.write(f"Datum: {image.get('datetime', 'N/A')}")
                                        st.write(f"Kamera: {image.get('camera_make', 'N/A')} {image.get('camera_model', 'N/A')}")
                        else:
                            st.info("Keine Gesichter für diese Person gefunden")
                    
                    except Exception as e:
                        st.error(f"Fehler bei der Suche: {e}")
            else:
                st.warning("Bitte geben Sie einen Personenname ein")
    
    elif query_type == "Gesichter nach Emotion":
        st.subheader("Gesichter nach Emotion suchen")
        
        emotion = st.selectbox(
            "Emotion",
            ["happy", "neutral", "sad", "angry", "surprised", "unknown"]
        )
        
        if st.button("Suchen"):
            with st.spinner("Suche Gesichter..."):
                try:
                    results = st.session_state.neo4j_manager.query_faces_by_emotion(emotion)
                    
                    if results:
                        st.success(f"{len(results)} Gesichter mit Emotion '{emotion}' gefunden")
                        
                        # Zeige Ergebnisse
                        for i, result in enumerate(results[:10]):  # Limitiere auf 10 Ergebnisse
                            with st.expander(f"Gesicht {i+1}", expanded=False):
                                face = result.get('f', {})
                                image = result.get('i', {})
                                person = result.get('p', {})
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Gesichtsdaten:**")
                                    st.write(f"Alter: {face.get('age', 'N/A')}")
                                    st.write(f"Geschlecht: {face.get('gender', 'N/A')}")
                                    st.write(f"Emotion: {face.get('emotion', 'N/A')}")
                                    st.write(f"Qualität: {face.get('quality_score', 'N/A')}")
                                
                                with col2:
                                    st.write("**Bilddaten:**")
                                    st.write(f"Datei: {image.get('filename', 'N/A')}")
                                    st.write(f"Datum: {image.get('datetime', 'N/A')}")
                                    if person:
                                        st.write(f"Person: {person.get('name', 'N/A')}")
                    else:
                        st.info(f"Keine Gesichter mit Emotion '{emotion}' gefunden")
                
                except Exception as e:
                    st.error(f"Fehler bei der Suche: {e}")
    
    elif query_type == "Gesichter nach Standort":
        st.subheader("Gesichter nach Standort suchen")
        
        col1, col2 = st.columns(2)
        with col1:
            country = st.text_input("Land", placeholder="z.B. Deutschland")
        with col2:
            city = st.text_input("Stadt", placeholder="z.B. Berlin")
        
        if st.button("Suchen"):
            with st.spinner("Suche Gesichter..."):
                try:
                    results = st.session_state.neo4j_manager.query_faces_by_location(country, city)
                    
                    if results:
                        location_filter = []
                        if country:
                            location_filter.append(f"Land: {country}")
                        if city:
                            location_filter.append(f"Stadt: {city}")
                        
                        st.success(f"{len(results)} Gesichter gefunden ({', '.join(location_filter)})")
                        
                        # Zeige Ergebnisse
                        for i, result in enumerate(results[:10]):  # Limitiere auf 10 Ergebnisse
                            with st.expander(f"Gesicht {i+1}", expanded=False):
                                face = result.get('f', {})
                                image = result.get('i', {})
                                location = result.get('l', {})
                                person = result.get('p', {})
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Gesichtsdaten:**")
                                    st.write(f"Alter: {face.get('age', 'N/A')}")
                                    st.write(f"Geschlecht: {face.get('gender', 'N/A')}")
                                    st.write(f"Emotion: {face.get('emotion', 'N/A')}")
                                    st.write(f"Qualität: {face.get('quality_score', 'N/A')}")
                                
                                with col2:
                                    st.write("**Standortdaten:**")
                                    st.write(f"Adresse: {location.get('full_address', 'N/A')}")
                                    st.write(f"Land: {location.get('country', 'N/A')}")
                                    st.write(f"Stadt: {location.get('city', 'N/A')}")
                                    if person:
                                        st.write(f"Person: {person.get('name', 'N/A')}")
                    else:
                        st.info("Keine Gesichter an diesem Standort gefunden")
                
                except Exception as e:
                    st.error(f"Fehler bei der Suche: {e}")

with tab4:
    st.header("Datenbank-Verwaltung")
    
    st.warning("Vorsicht: Diese Aktionen können nicht rückgängig gemacht werden!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Datenbank-Status")
        if st.button("Status prüfen"):
            with st.spinner("Prüfe Datenbank-Status..."):
                try:
                    stats = st.session_state.neo4j_manager.get_statistics()
                    
                    st.info("Datenbank-Status:")
                    st.write(f"• Bilder: {stats.get('total_images', 0)}")
                    st.write(f"• Gesichter: {stats.get('total_faces', 0)}")
                    st.write(f"• Personen: {stats.get('total_persons', 0)}")
                    st.write(f"• Standorte: {stats.get('total_locations', 0)}")
                
                except Exception as e:
                    st.error(f"Fehler beim Prüfen des Status: {e}")
    
    with col2:
        st.subheader("Datenbank leeren")
        st.error("Diese Aktion löscht ALLE Daten!")
        
        confirm_text = st.text_input(
            "Bestätigen Sie mit 'LÖSCHEN'", 
            placeholder="LÖSCHEN eingeben"
        )
        
        if st.button("Datenbank leeren", disabled=confirm_text != "LÖSCHEN"):
            with st.spinner("Leere Datenbank..."):
                try:
                    st.session_state.neo4j_manager.clear_database()
                    st.success("Datenbank erfolgreich geleert!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Fehler beim Leeren der Datenbank: {e}")

# Footer
st.divider()
st.caption("""
**Neo4j Integration für Gesichtserkennungs-Daten**

Diese Seite ermöglicht es, die von der Annotate-Seite produzierten JSON-Dateien 
in eine Neo4j-Datenbank zu importieren und komplexe Abfragen auf die Daten 
durchzuführen.

**Verfügbare Entitäten:**
- **Image**: Bilder mit Metadaten (Kamera, Datum, etc.)
- **Face**: Gesichter mit Eigenschaften (Alter, Geschlecht, Emotion, etc.)
- **Person**: Identifizierte Personen
- **Location**: Standorte mit GPS-Koordinaten

**Verfügbare Beziehungen:**
- **APPEARS_IN**: Gesicht erscheint in Bild
- **BELONGS_TO**: Gesicht gehört zu Person
- **TAKEN_AT**: Bild wurde an Standort aufgenommen
""")
