"""
Import (RestAPI) Page

Ermöglicht das Abrufen und Importieren von Image-Region-Daten
(XMP-Metadaten) aus dem PBF-DAMS Django Backend über REST API.
"""
import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
import sys
import os

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from pbf_dams_client import PBFDAMSClient, RegionData
from streamlit_styles import apply_custom_css

st.set_page_config(
    page_title="Import (RestAPI)",
    page_icon="",
    layout="wide"
)

# Wende kleinere Schriftgrößen an
apply_custom_css()

st.title("Import (RestAPI)")
st.markdown("""
Importiere Image-Region-Daten (XMP-Metadaten) aus dem PBF-DAMS über REST API.
Diese Daten zeigen, wo welche Personen auf Fotos markiert sind.
""")

# Sidebar: Konfiguration
with st.sidebar:
    st.header("Konfiguration")
    
    # Server-URL
    server_url = st.text_input(
        "PBF-DAMS Server URL",
        value="http://localhost:8000",
        help="URL des PBF-DAMS Django Servers"
    )
    
    # Client initialisieren
    client = PBFDAMSClient(base_url=server_url)
    
    # Verbindungstest
    if st.button("Verbindung testen"):
        with st.spinner("Teste Verbindung..."):
            if client.test_connection():
                st.success("Verbindung erfolgreich!")
            else:
                st.error("Verbindung fehlgeschlagen. Prüfe die Server-URL.")
    
    st.divider()
    
    # Statistiken
    st.header("Statistiken")
    if st.button("Statistiken laden"):
        with st.spinner("Lade Statistiken..."):
            try:
                stats = client.get_statistics()
                st.metric("Gesamt-Regions", stats["total_regions"])
                st.metric("Unique Fotos", stats["unique_photos"])
                st.metric("Unique Personen", stats["unique_persons"])
                st.metric(
                    "Ø Regions/Foto", 
                    f"{stats['avg_regions_per_photo']:.1f}"
                )
            except Exception as e:
                st.error(f"Fehler beim Laden der Statistiken: {e}")

# Hauptbereich: Suchmaske
st.header("Suchmaske")

col1, col2, col3 = st.columns(3)

with col1:
    # Filter nach Foto
    search_by_photo = st.checkbox("Nach Foto filtern")
    photo_identifier = None
    
    if search_by_photo:
        photo_identifier = st.text_input(
            "Foto-Identifier",
            placeholder="z.B. macb_30035212_44",
            help="Identifier des Fotos im PBF-DAMS"
        )
        
        # Oder Auswahl aus Liste
        if st.button("Foto-Liste laden"):
            with st.spinner("Lade Fotos..."):
                try:
                    photos = client.get_photos_list()
                    if photos:
                        st.session_state["photos_list"] = photos
                        st.success(f"{len(photos)} Fotos gefunden")
                    else:
                        st.warning("Keine Fotos gefunden")
                except Exception as e:
                    st.error(f"Fehler: {e}")
        
        if "photos_list" in st.session_state:
            selected_photo = st.selectbox(
                "Oder wähle aus der Liste:",
                options=[""] + st.session_state["photos_list"]
            )
            if selected_photo:
                photo_identifier = selected_photo

with col2:
    # Filter nach Person
    search_by_person = st.checkbox("Nach Person filtern")
    person_identifier = None
    
    if search_by_person:
        person_identifier = st.text_input(
            "Person-Identifier",
            placeholder="z.B. pina_bausch",
            help="Identifier der Person im PBF-DAMS"
        )
        
        # Oder Auswahl aus Liste
        if st.button("Personen-Liste laden"):
            with st.spinner("Lade Personen..."):
                try:
                    persons = client.get_persons_list()
                    if persons:
                        st.session_state["persons_list"] = persons
                        st.success(f"{len(persons)} Personen gefunden")
                    else:
                        st.warning("Keine Personen gefunden")
                except Exception as e:
                    st.error(f"Fehler: {e}")
        
        if "persons_list" in st.session_state:
            persons_dict = {p["label"]: p["identifier"] for p in st.session_state["persons_list"]}
            selected_person_name = st.selectbox(
                "Oder wähle aus der Liste:",
                options=[""] + list(persons_dict.keys())
            )
            if selected_person_name:
                person_identifier = persons_dict[selected_person_name]

with col3:
    # Erweiterte Optionen
    st.subheader("Optionen")
    include_unidentified = st.checkbox(
        "Private Personen inkludieren",
        value=False,
        help="Auch nicht-öffentliche Personen exportieren"
    )

# Such-Button
st.divider()

if st.button("Daten abrufen", type="primary", use_container_width=True):
    with st.spinner("Rufe Daten von PBF-DAMS ab..."):
        try:
            # API-Call
            data = client.get_regions(
                photo=photo_identifier if search_by_photo else None,
                person=person_identifier if search_by_person else None,
                include_unidentified=include_unidentified
            )
            
            st.session_state["export_data"] = data
            st.session_state["export_timestamp"] = datetime.now()
            
            st.success(f"{data['count']} Regions erfolgreich abgerufen!")
            
        except requests.exceptions.ConnectionError:
            st.error("❌ **Verbindungsfehler**: Kann nicht mit PBF-DAMS Server verbinden.")
            st.info("**Mögliche Ursachen:**")
            st.write("- Server läuft nicht (Django-Server starten)")
            st.write("- Falsche Server-URL in der Konfiguration")
            st.write("- Netzwerkprobleme")
        except requests.exceptions.Timeout:
            st.error("❌ **Timeout**: Server antwortet nicht rechtzeitig.")
            st.info("Server ist möglicherweise überlastet oder nicht erreichbar.")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ **HTTP-Fehler**: {e}")
            if e.response.status_code == 404:
                st.info("API-Endpoint nicht gefunden. Prüfe die Server-URL und API-Pfade.")
            elif e.response.status_code == 500:
                st.info("Server-Fehler. Prüfe die Django-Server-Logs.")
        except ValueError as e:
            st.error(f"❌ **Datenformat-Fehler**: {e}")
            st.info("**Mögliche Ursachen:**")
            st.write("- Server gibt kein JSON zurück")
            st.write("- API-Endpoint gibt leere Antwort zurück")
            st.write("- Server ist nicht korrekt konfiguriert")
        except Exception as e:
            st.error(f"❌ **Unbekannter Fehler**: {e}")
            st.info("Prüfe die Server-Logs für weitere Details.")

# Ergebnisse anzeigen
if "export_data" in st.session_state:
    data = st.session_state["export_data"]
    
    st.divider()
    st.header("Ergebnisse")
    
    # Zusammenfassung
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Gefundene Regions", data["count"])
    
    with col2:
        # Unique Fotos zählen
        unique_photos = len(set(
            r.get("photo_identifier") 
            for r in data["regions"] 
            if r.get("photo_identifier")
        ))
        st.metric("Unique Fotos", unique_photos)
    
    with col3:
        # Unique Personen zählen
        unique_persons = len(set(
            r.get("person", {}).get("identifier") 
            for r in data["regions"] 
            if r.get("person", {}).get("identifier")
        ))
        st.metric("Unique Personen", unique_persons)
    
    # Daten-Tabelle
    if data["regions"]:
        st.subheader("Regions-Daten")
        
        # Konvertiere zu DataFrame
        rows = []
        for region in data["regions"]:
            rd = RegionData(region)
            rows.append({
                "Foto": rd.photo_identifier,
                "Foto Name": rd.photo_label,
                "Person": rd.person_name,
                "Person ID": rd.person_identifier,
                "X": f"{rd.coordinates['x']:.4f}",
                "Y": f"{rd.coordinates['y']:.4f}",
                "Breite": f"{rd.coordinates['width']:.4f}",
                "Höhe": f"{rd.coordinates['height']:.4f}",
                "Rotation": f"{rd.coordinates['rotation']:.1f}°",
                "Bild Breite": rd.dimensions['width'],
                "Bild Höhe": rd.dimensions['height']
            })
        
        df = pd.DataFrame(rows)
        
        # Interaktive Tabelle
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # Export-Optionen
        st.subheader("Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON-Export
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            st.download_button(
                label="Als JSON herunterladen",
                data=json_str,
                file_name=f"pbf_dams_regions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # CSV-Export
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="Als CSV herunterladen",
                data=csv,
                file_name=f"pbf_dams_regions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Raw JSON anzeigen (expandable)
        with st.expander("Raw JSON anzeigen"):
            st.json(data)
    
    else:
        st.info("Keine Regions gefunden mit den aktuellen Suchkriterien.")
    
    # Timestamp
    if "export_timestamp" in st.session_state:
        st.caption(f"Abgerufen am: {st.session_state['export_timestamp'].strftime('%d.%m.%Y %H:%M:%S')}")

# Hilfe-Bereich
st.divider()

with st.expander("Hilfe & Dokumentation"):
    st.markdown("""
    ### Wie funktioniert der Import?
    
    1. **PBF-DAMS Server muss laufen** auf dem konfigurierten Port (Standard: 8000)
    2. **Filter wählen** (optional): Nach Foto, Person oder beide
    3. **Daten abrufen** via "Daten abrufen"-Button
    4. **Ergebnisse anzeigen** in Tabellenform
    5. **Export** als JSON oder CSV
    
    ### Was sind Regions?
    
    **Regions** sind markierte Bereiche in Fotos, die Personen (meist Gesichter) kennzeichnen.
    Sie enthalten:
    - Position (x, y)
    - Größe (width, height)
    - Rotation
    - Verknüpfung zur Person
    - Verknüpfung zum Foto
    
    ### Beispiel-Queries:
    
    - **Alle Regions abrufen**: Keine Filter setzen
    - **Fotos einer Person**: Person-Filter verwenden (z.B. "pina_bausch")
    - **Alle Personen auf einem Foto**: Foto-Filter verwenden (z.B. "macb_30035212_44")
    - **Spezifische Kombination**: Beide Filter kombinieren
    
    ### Koordinaten-System:
    
    Die Koordinaten sind **relativ** (0.0 bis 1.0):
    - `x = 0.5` bedeutet 50% von links
    - `y = 0.5` bedeutet 50% von oben
    - `width = 0.1` bedeutet 10% der Bildbreite
    
    ### API-Endpunkt:
    
    ```
    GET {server_url}/api/v1/exports/image-regions/
    ```
    
    **Parameter:**
    - `photo` - Foto-Identifier
    - `person` - Person-Identifier  
    - `include_unidentified` - Private Personen inkludieren
    
    ### Weitere Dokumentation:
    
    Siehe `pbf-dams/IMAGE_REGIONS_EXPORT_TEST_GUIDE.md`
    """)

# Info-Box am Ende
st.info("""
Tipp: Nutze die Personen- und Foto-Listen-Buttons, um verfügbare Identifiers zu sehen,
anstatt sie manuell einzugeben.
""")

