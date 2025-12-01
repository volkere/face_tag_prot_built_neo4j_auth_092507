"""
PBF-DAMS Mapping zu Embeddings Converter

Erstellt Embeddings direkt aus PBF-DAMS-Zuordnungsdateien mit vorhandenen Personen-Namen und Koordinaten.
"""
import io, os, pickle
import streamlit as st
import numpy as np
import cv2
import sys
import json

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.face_recognizer import FaceEngine, GalleryDB
from streamlit_styles import apply_custom_css

# Wende kleinere Schriftgrößen an
apply_custom_css()

st.title("PBF-DAMS Mapping zu Embeddings")
st.caption("Erstellt Embeddings direkt aus PBF-DAMS-Zuordnungsdateien mit vorhandenen Personen-Namen.")

with st.sidebar:
    det = st.slider("Detector size", 320, 1024, 640, 64)

if "engine_mapping" not in st.session_state or st.session_state.get("det_mapping") != det:
    st.session_state["engine_mapping"] = FaceEngine(det_size=(det, det))
    st.session_state["det_mapping"] = det

st.success("""
**Perfekt für Ihre faces_20251127_141817.json!**
Diese Funktion ist speziell für PBF-DAMS-Exportdateien mit:
- Personennamen in regions[].name (z.B. ":tsai-chin_yu")
- Koordinaten (x_abs, y_abs, width_px, height_px)
- Bildpfaden
""")

# Datei-Upload
mapping_file = st.file_uploader(
    "PBF-DAMS Zuordnungs-Datei hochladen", 
    type=["json"], 
    key="mapping_pbf",
    help="Laden Sie Ihre faces_20251127_141817.json oder ähnliche Datei hoch"
)

if mapping_file is not None:
    try:
        data = json.load(mapping_file)
        
        st.subheader("Datei-Analyse")
        
        # Statistiken sammeln
        total_images = len(data) if isinstance(data, list) else 0
        images_with_regions = 0
        total_regions = 0
        unique_persons = set()
        
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and 'regions' in item:
                regions = item['regions']
                if isinstance(regions, list) and len(regions) > 0:
                    images_with_regions += 1
                    total_regions += len(regions)
                    
                    for region in regions:
                        if isinstance(region, dict) and 'name' in region:
                            name = region['name']
                            if name:
                                # Entferne führenden Doppelpunkt falls vorhanden
                                clean_name = name.lstrip(':')
                                unique_persons.add(clean_name)
        
        # Statistiken anzeigen
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Bilder gesamt", total_images)
        with col2:
            st.metric("Bilder mit Regionen", images_with_regions)
        with col3:
            st.metric("Regionen gesamt", total_regions)
        with col4:
            st.metric("Einzigartige Personen", len(unique_persons))
        
        if len(unique_persons) > 0:
            st.success("**Gefundene Personen:**")
            persons_preview = list(unique_persons)[:20]  # Zeige erste 20
            st.info(", ".join(persons_preview) + ("..." if len(unique_persons) > 20 else ""))
            
            # Einstellungen
            st.subheader("Verarbeitungseinstellungen")
            col1, col2 = st.columns(2)
            
            with col1:
                max_regions = st.slider(
                    "Max. Regionen verarbeiten", 
                    1, min(500, total_regions), 
                    min(100, total_regions),
                    help="Limitierung für Testzwecke"
                )
            
            with col2:
                min_region_size = st.slider(
                    "Min. Regionsgröße (Breite ODER Höhe in Pixel)", 
                    20, 300, 30,
                    help="Filtert sehr kleine Gesichtsregionen heraus. Typisch: 30-100 Pixel. 10200 ist viel zu groß!"
                )
            
            # Name-Bereinigung
            clean_names = st.checkbox(
                "Namen bereinigen (entfernt ':' am Anfang)", 
                value=True,
                help="Konvertiert ':tsai_chin_yu' zu 'tsai_chin_yu'"
            )
            
            # Warnung wenn Wert zu hoch ist
            if min_region_size > 200:
                st.error(f"⚠️ **WARNUNG:** Min. Regionsgröße ist mit {min_region_size} Pixel viel zu hoch!")
                st.info("""
                **Typische Werte:**
                - **20-50 Pixel:** Kleine Gesichter (empfohlen)
                - **50-100 Pixel:** Mittlere Gesichter  
                - **100-200 Pixel:** Große Gesichter
                
                **Ihr aktueller Wert ({}) ist viel zu groß!** Die meisten Gesichter werden herausgefiltert.
                Setzen Sie den Wert auf **30-50 Pixel** für beste Ergebnisse.
                """.format(min_region_size))
            
            if st.button("Embeddings aus Zuordnungen erstellen", key="create_from_pbf_mapping"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                db = GalleryDB()
                processed_regions = 0
                successful_embeddings = 0
                errors = 0
                filtered_too_small = 0
                filtered_no_coords = 0
                person_counts = {}
                
                for img_idx, item in enumerate(data):
                    if processed_regions >= max_regions:
                        break
                        
                    if not isinstance(item, dict) or 'regions' not in item:
                        continue
                    
                    image_path = item.get('image')
                    regions = item.get('regions', [])
                    
                    if not image_path or not isinstance(regions, list):
                        continue
                    
                    status_text.text(f"Verarbeite Bild {img_idx+1}/{total_images}: {os.path.basename(image_path)}")
                    
                    # Bild laden
                    if os.path.exists(image_path):
                        img = cv2.imread(image_path)
                        if img is None:
                            continue
                        
                        # Prüfe Bildgröße - OpenCV benötigt gültige Dimensionen
                        h_img, w_img = img.shape[:2]
                        if h_img < 50 or w_img < 50:
                            continue
                        
                        for region in regions:
                            if processed_regions >= max_regions:
                                break
                            
                            try:
                                if not isinstance(region, dict):
                                    continue
                                
                                # Person-Name extrahieren
                                person_name = region.get('name')
                                if not person_name:
                                    continue
                                
                                # Name bereinigen
                                if clean_names and person_name.startswith(':'):
                                    person_name = person_name[1:]
                                
                                # Koordinaten extrahieren
                                x_abs = region.get('x_abs')
                                y_abs = region.get('y_abs')
                                width_px = region.get('width_px')
                                height_px = region.get('height_px')
                                
                                if None in [x_abs, y_abs, width_px, height_px]:
                                    filtered_no_coords += 1
                                    continue
                                
                                # Größenfilter
                                if width_px < min_region_size or height_px < min_region_size:
                                    filtered_too_small += 1
                                    continue
                                
                                # Bounding Box berechnen
                                x1 = int(x_abs)
                                y1 = int(y_abs)
                                x2 = int(x_abs + width_px)
                                y2 = int(y_abs + height_px)
                                
                                # Grenzen prüfen
                                h, w = img.shape[:2]
                                x1 = max(0, min(x1, w-1))
                                y1 = max(0, min(y1, h-1))
                                x2 = max(x1+1, min(x2, w))
                                y2 = max(y1+1, min(y2, h))
                                
                                # Gesicht ausschneiden für Vorschau
                                face_crop = img[y1:y2, x1:x2]
                                
                                if face_crop.size > 0:
                                    # WICHTIG: Analysiere das VOLLSTÄNDIGE Bild, nicht den Crop
                                    # Dies stellt sicher, dass die Embeddings kompatibel sind
                                    try:
                                        faces = st.session_state["engine_mapping"].analyze(img)
                                    except Exception as e:
                                        errors += 1
                                        if errors <= 3:
                                            st.error(f"Fehler beim Analysieren von {os.path.basename(image_path)}: {e}")
                                        continue
                                    
                                    if faces and len(faces) > 0:
                                        # Finde das Gesicht, das am besten zu den Koordinaten passt
                                        best_face = None
                                        best_overlap = 0
                                        
                                        target_center_x = (x1 + x2) / 2
                                        target_center_y = (y1 + y2) / 2
                                        
                                        for face in faces:
                                            fx1, fy1, fx2, fy2 = face['bbox']
                                            face_center_x = (fx1 + fx2) / 2
                                            face_center_y = (fy1 + fy2) / 2
                                            
                                            # Berechne Überlappung der Bounding Boxen
                                            overlap_x = max(0, min(x2, fx2) - max(x1, fx1))
                                            overlap_y = max(0, min(y2, fy2) - max(y1, fy1))
                                            overlap_area = overlap_x * overlap_y
                                            
                                            # Berechne Fläche der Region
                                            region_area = (x2 - x1) * (y2 - y1)
                                            
                                            # Berechne IoU (Intersection over Union)
                                            if region_area > 0:
                                                iou = overlap_area / region_area
                                                if iou > best_overlap:
                                                    best_overlap = iou
                                                    best_face = face
                                        
                                        # Falls kein überlappendes Gesicht gefunden, nimm das Gesicht mit dem geringsten Abstand zum Zentrum
                                        if best_face is None or best_overlap < 0.1:
                                            best_face = None
                                            min_distance = float('inf')
                                            for face in faces:
                                                fx1, fy1, fx2, fy2 = face['bbox']
                                                face_center_x = (fx1 + fx2) / 2
                                                face_center_y = (fy1 + fy2) / 2
                                                
                                                distance = np.sqrt((face_center_x - target_center_x)**2 + (face_center_y - target_center_y)**2)
                                                if distance < min_distance:
                                                    min_distance = distance
                                                    best_face = face
                                        
                                        # Falls immer noch kein Gesicht gefunden, nimm das beste basierend auf Qualität
                                        if best_face is None:
                                            best_face = max(faces, key=lambda f: f.get('quality_score', 0))
                                        
                                        # Metadaten erstellen
                                        metadata = {
                                            'source_image': os.path.basename(image_path),
                                            'source': 'pbf_dams_mapping',
                                            'bbox': [x1, y1, x2, y2],
                                            'region_type': region.get('type'),
                                            'quality_score': best_face.get('quality_score'),
                                            'age': best_face.get('age'),
                                            'gender': best_face.get('gender'),
                                            'original_coords': {
                                                'x_rel': region.get('x_rel'),
                                                'y_rel': region.get('y_rel'),
                                                'width_rel': region.get('width_rel'),
                                                'height_rel': region.get('height_rel')
                                            }
                                        }
                                        
                                        # Prüfe Embedding-Format
                                        embedding = best_face['embedding']
                                        if not isinstance(embedding, np.ndarray):
                                            embedding = np.array(embedding, dtype=np.float32)
                                        
                                        # Normalisiere Embedding für Konsistenz
                                        embedding = embedding.astype(np.float32)
                                        embedding_norm = np.linalg.norm(embedding)
                                        if embedding_norm > 0:
                                            embedding = embedding / embedding_norm
                                        
                                        db.add(person_name, embedding, metadata)
                                        successful_embeddings += 1
                                        person_counts[person_name] = person_counts.get(person_name, 0) + 1
                                
                                processed_regions += 1
                                
                            except Exception as e:
                                errors += 1
                                if errors <= 3:  # Zeige nur erste 3 Fehler
                                    st.error(f"Fehler bei Region in {os.path.basename(image_path)}: {e}")
                    
                    # Progress aktualisieren
                    progress = min(processed_regions / max_regions, (img_idx + 1) / total_images)
                    progress_bar.progress(progress)
                
                status_text.text("Verarbeitung abgeschlossen!")
                
                if successful_embeddings > 0:
                    total_embeddings = sum(len(embs) for embs in db.people.values())
                    
                    st.success(f"**{successful_embeddings} Embeddings** erfolgreich erstellt!")
                    st.info(f"**{len(db.people)} Personen** mit {total_embeddings} Embeddings")
                    
                    # Top Personen anzeigen
                    if person_counts:
                        sorted_persons = sorted(person_counts.items(), key=lambda x: x[1], reverse=True)
                        top_persons = sorted_persons[:10]
                        persons_text = ", ".join([f"{name} ({count}x)" for name, count in top_persons])
                        st.info(f"**Top Personen:** {persons_text}")
                    
                    # embeddings.pkl erstellen
                    b = io.BytesIO()
                    pickle.dump({"people": db.people, "metadata": db.face_metadata}, b, protocol=pickle.HIGHEST_PROTOCOL)
                    
                    st.download_button(
                        "embeddings.pkl herunterladen",
                        data=b.getvalue(),
                        file_name="embeddings_from_pbf_mapping.pkl",
                        mime="application/octet-stream"
                    )
                    
                    st.success("""
                    **Perfekt! Embeddings erstellt.**
                    
                    **Wichtig für die Annotate-Seite:**
                    1. Laden Sie diese embeddings.pkl in der **Annotate-Seite** unter "Embeddings DB" hoch
                    2. Setzen Sie den **Threshold auf 0.5-0.6** (nicht höher!)
                    3. Die Personen sollten jetzt automatisch erkannt werden
                    
                    **Falls keine Personen erkannt werden:**
                    - Threshold zu hoch? → Setzen Sie ihn auf 0.4-0.5
                    - Embeddings geladen? → Prüfen Sie die Status-Meldung
                    - Gleiche Bilder? → Verwenden Sie die gleichen Bilder, die in der Zuordnungsdatei stehen
                    """)
                    
                    if errors > 0:
                        st.warning(f"**{errors} Fehler** aufgetreten (siehe oben)")
                    
                    # Debug-Informationen
                    if filtered_too_small > 0 or filtered_no_coords > 0:
                        st.info("**Filter-Statistiken:**")
                        st.write(f"- Herausgefiltert (zu klein): {filtered_too_small} Regionen")
                        st.write(f"- Herausgefiltert (fehlende Koordinaten): {filtered_no_coords} Regionen")
                        if filtered_too_small > 0:
                            st.warning(f"💡 **Tipp:** {filtered_too_small} Regionen wurden herausgefiltert, weil sie kleiner als {min_region_size} Pixel sind. Setzen Sie den Wert niedriger (z.B. 30 Pixel) für mehr Ergebnisse.")
                
                else:
                    st.error("Keine Embeddings erfolgreich erstellt.")
                    
                    # Detaillierte Fehleranalyse
                    st.info("**Fehler-Analyse:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Herausgefiltert (zu klein)", filtered_too_small)
                    with col2:
                        st.metric("Fehlende Koordinaten", filtered_no_coords)
                    with col3:
                        st.metric("Verarbeitungsfehler", errors)
                    
                    if filtered_too_small > 0:
                        st.error(f"**Hauptproblem:** {filtered_too_small} Regionen wurden herausgefiltert, weil Min. Regionsgröße ({min_region_size} Pixel) zu hoch ist!")
                        st.info("""
                        **Lösung:**
                        - Setzen Sie "Min. Regionsgröße" auf **20-30 Pixel** statt {}
                        - Klicken Sie erneut auf "Embeddings erstellen"
                        """.format(min_region_size))
                    else:
                        st.info("""
                        **Mögliche Ursachen:**
                        - Bildpfade existieren nicht oder sind nicht lesbar
                        - Regionskoordinaten sind ungültig
                        - Gesichtserkennung schlägt fehl (schlechte Bildqualität)
                        """)
        
        else:
            st.warning("Keine Personen-Zuordnungen in der Datei gefunden.")
            st.info("""
            **Ihre Datei scheint keine benannten Regionen zu enthalten.**
            Prüfen Sie, ob:
            - Die regions-Arrays Einträge mit 'name' enthalten
            - Die Namen nicht leer sind
            - Die Datei korrekt exportiert wurde
            """)
    
    except json.JSONDecodeError as e:
        st.error(f"Fehler beim Laden der JSON-Datei: {e}")
    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Datei: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("""
    **Laden Sie Ihre PBF-DAMS-Zuordnungsdatei hoch, um zu starten.**
    
    **Beispiel-Pfad:** `/Users/volkerenkrodt/Documents/PBA_Tagg/face_tag_prot_built_neo4j_auth_092507/exported/faces_20251127_141817.json`
    
    **Diese Funktion:**
    1. Lädt Ihre JSON-Datei mit Personen-Zuordnungen
    2. Extrahiert Gesichter basierend auf den vorhandenen Koordinaten
    3. Erstellt Embeddings für jeden benannten Bereich
    4. Generiert eine embeddings.pkl mit echten Namen
    
    **Ergebnis:** Echte Personenerkennung mit Namen wie "tsai_chin_yu" anstatt "Person_dateiname"
    """)
