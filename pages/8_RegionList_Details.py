"""
RegionList Details Page

Extrahiert RegionList-Daten (XMP-Metadaten) aus Bildern in einem Verzeichnis.
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from streamlit_styles import apply_custom_css

st.set_page_config(
    page_title="RegionList Details",
    page_icon="",
    layout="wide"
)

# Wende kleinere Schriftgrößen an
apply_custom_css()

st.title("RegionList Details Extraktion")
st.markdown("""
Extrahiert RegionList-Daten (XMP-Metadaten) aus Bildern in einem ausgewählten Verzeichnis.
RegionList enthält Informationen über annotierte Regionen in Bildern (z.B. Gesichter, Personen).
""")

# Sidebar: Konfiguration
with st.sidebar:
    st.header("Konfiguration")
    
    # Verzeichnis-Auswahl
    st.subheader("Verzeichnis-Auswahl")
    directory_path = st.text_input(
        "Verzeichnis-Pfad",
        value="",
        placeholder="/pfad/zum/verzeichnis",
        help="Pfad zum Verzeichnis mit Bildern"
    )
    
    # Button zum Verzeichnis auswählen (falls möglich)
    if st.button("Verzeichnis durchsuchen"):
        st.info("Verwenden Sie das Textfeld oben, um den Pfad einzugeben")
    
    # Rekursiv durchsuchen
    recursive = st.checkbox(
        "Rekursiv durchsuchen",
        value=False,
        help="Durchsucht auch Unterverzeichnisse"
    )
    
    # Dateiformate
    st.subheader("Dateiformate")
    supported_formats = st.multiselect(
        "Unterstützte Formate",
        ["jpg", "jpeg", "png", "tif", "tiff", "xmp"],
        default=["jpg", "jpeg", "png", "tif", "tiff"],
        help="Dateiformate, die durchsucht werden sollen"
    )
    
    # Output-Konfiguration
    st.subheader("Output-Konfiguration")
    BASE_DIR = os.path.dirname(__file__)
    OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "exported"))
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    output_filename = st.text_input(
        "Output-Dateiname",
        value=f"regionlist_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        help="Name der Output-Datei"
    )
    
    output_format = st.selectbox(
        "Output-Format",
        ["JSON", "CSV"],
        help="Format der Output-Datei"
    )


def extract_regionlist_from_image(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Extrahiert RegionList-Daten aus einem Bild.
    
    Args:
        image_path: Pfad zum Bild
        
    Returns:
        Dictionary mit RegionList-Daten oder None
    """
    try:
        # Versuche verschiedene Methoden zur XMP-Extraktion
        
        # Methode 1: Exifread (unterstützt XMP)
        try:
            import exifread
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                
                # Suche nach XMP-Tags mit RegionList
                regionlist_data = {}
                xmp_tags = {k: v for k, v in tags.items() if 'XMP' in k or 'RegionList' in k or 'Region' in k}
                
                if xmp_tags:
                    regionlist_data['xmp_tags'] = {k: str(v) for k, v in xmp_tags.items()}
                    regionlist_data['source'] = 'exifread'
        except ImportError:
            pass
        except Exception as e:
            st.warning(f"Exifread-Fehler für {image_path}: {e}")
        
        # Methode 2: Pillow - Prüfe auf XMP in EXIF
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            img = Image.open(image_path)
            exif = img._getexif()
            
            if exif:
                exif_data = {TAGS.get(k, k): v for k, v in exif.items()}
                
                # Suche nach XMP-Markern in EXIF
                for key, value in exif_data.items():
                    if isinstance(value, (str, bytes)):
                        value_str = str(value) if isinstance(value, str) else value.decode('utf-8', errors='ignore')
                        if 'RegionList' in value_str or 'xmp:RegionList' in value_str:
                            return {
                                'image_path': image_path,
                                'xmp_found_in_exif': True,
                                'exif_key': key,
                                'source': 'pillow_exif'
                            }
        except Exception as e:
            pass
        
        # Methode 3: Direkte XMP-Datei lesen (falls vorhanden)
        xmp_path = image_path.rsplit('.', 1)[0] + '.xmp'
        if os.path.exists(xmp_path):
            try:
                with open(xmp_path, 'r', encoding='utf-8') as f:
                    xmp_content = f.read()
                    
                    # Einfaches Parsing nach RegionList
                    if 'RegionList' in xmp_content or 'rdf:Description' in xmp_content:
                        return {
                            'image_path': image_path,
                            'xmp_file': xmp_path,
                            'xmp_content': xmp_content,
                            'source': 'xmp_file'
                        }
            except Exception as e:
                pass
        
        # Methode 4: piexif für erweiterte EXIF/XMP
        try:
            import piexif
            exif_dict = piexif.load(image_path)
            
            # Prüfe auf XMP-Daten in EXIF
            if '0th' in exif_dict:
                # Suche nach XMP-Markern
                for key, value in exif_dict['0th'].items():
                    if isinstance(value, bytes):
                        try:
                            value_str = value.decode('utf-8', errors='ignore')
                            if 'RegionList' in value_str or 'xmp:RegionList' in value_str:
                                return {
                                    'image_path': image_path,
                                    'xmp_found_in_exif': True,
                                    'exif_key': key,
                                    'source': 'piexif'
                                }
                        except:
                            pass
        except ImportError:
            pass
        except Exception as e:
            pass
        
        # Wenn nichts gefunden wurde, aber XMP-Tags vorhanden sind
        if 'regionlist_data' in locals() and regionlist_data:
            regionlist_data['image_path'] = image_path
            return regionlist_data
        
        return None
        
    except Exception as e:
        return {
            'image_path': image_path,
            'error': str(e)
        }


def collect_images(directory: str, formats: List[str], recursive: bool = False) -> List[str]:
    """
    Sammelt alle Bild-Dateien aus einem Verzeichnis.
    
    Args:
        directory: Verzeichnis-Pfad
        formats: Liste von Dateiformaten (ohne Punkt)
        recursive: Ob rekursiv durchsucht werden soll
        
    Returns:
        Liste von Dateipfaden
    """
    images = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return images
    
    format_patterns = [f".{fmt.lower()}" for fmt in formats]
    
    if recursive:
        for pattern in format_patterns:
            images.extend(directory_path.rglob(f"*{pattern}"))
            images.extend(directory_path.rglob(f"*{pattern.upper()}"))
    else:
        for pattern in format_patterns:
            images.extend(directory_path.glob(f"*{pattern}"))
            images.extend(directory_path.glob(f"*{pattern.upper()}"))
    
    return [str(img) for img in images]


# Hauptbereich
if directory_path and os.path.exists(directory_path):
    if st.button("RegionList-Daten extrahieren", type="primary", use_container_width=True):
        # Bilder sammeln
        with st.spinner("Suche nach Bildern..."):
            images = collect_images(directory_path, supported_formats, recursive)
        
        if not images:
            st.warning(f"Keine Bilder gefunden in: {directory_path}")
        else:
            st.info(f"Gefunden: {len(images)} Bild(er)")
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # RegionList-Daten extrahieren
            results = []
            processed = 0
            
            for idx, image_path in enumerate(images):
                status_text.text(f"Verarbeite {os.path.basename(image_path)}... ({idx+1}/{len(images)})")
                
                regionlist_data = extract_regionlist_from_image(image_path)
                if regionlist_data:
                    results.append(regionlist_data)
                
                processed += 1
                progress_bar.progress(processed / len(images))
            
            status_text.text(f"Fertig! {len(results)} Bild(er) mit RegionList-Daten gefunden.")
            
            # Ergebnisse anzeigen
            if results:
                st.success(f"✅ {len(results)} Bild(er) mit RegionList-Daten gefunden!")
                
                # Statistiken
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Verarbeitete Bilder", len(images))
                with col2:
                    st.metric("Bilder mit RegionList", len(results))
                with col3:
                    st.metric("Erfolgsrate", f"{len(results)/len(images)*100:.1f}%")
                
                # Vorschau
                with st.expander("Vorschau der RegionList-Daten", expanded=False):
                    if len(results) > 0:
                        st.json(results[0])
                
                # Output-Datei speichern
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                if output_format == "JSON":
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Daten gespeichert: {output_path}")
                    
                    # Download-Button
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            "RegionList-Daten herunterladen",
                            data=f.read(),
                            file_name=output_filename,
                            mime="application/json",
                            use_container_width=True
                        )
                
                elif output_format == "CSV":
                    # Konvertiere zu CSV
                    import pandas as pd
                    
                    # Flache Struktur für CSV
                    csv_data = []
                    for result in results:
                        row = {
                            'image_path': result.get('image_path', ''),
                            'source': result.get('source', ''),
                            'has_regionlist': 'regionlist' in result or 'xmp_content' in result,
                            'error': result.get('error', '')
                        }
                        
                        # Versuche RegionList-Daten zu extrahieren
                        if 'regionlist' in result:
                            row['regionlist_data'] = json.dumps(result['regionlist'])
                        elif 'xmp_content' in result:
                            row['xmp_content'] = result['xmp_content'][:500]  # Erste 500 Zeichen
                        
                        csv_data.append(row)
                    
                    df = pd.DataFrame(csv_data)
                    csv_path = output_path.rsplit('.', 1)[0] + '.csv'
                    df.to_csv(csv_path, index=False, encoding='utf-8')
                    
                    st.success(f"✅ CSV-Datei gespeichert: {csv_path}")
                    
                    # Download-Button
                    with open(csv_path, 'rb') as f:
                        st.download_button(
                            "RegionList-Daten (CSV) herunterladen",
                            data=f.read(),
                            file_name=output_filename.rsplit('.', 1)[0] + '.csv',
                            mime="text/csv",
                            use_container_width=True
                        )
            else:
                st.warning("⚠️ Keine RegionList-Daten in den Bildern gefunden.")
                st.info("""
                **Mögliche Ursachen:**
                - Die Bilder enthalten keine XMP-Metadaten
                - RegionList-Daten sind nicht im erwarteten Format
                - XMP-Bibliotheken fehlen (exifread, piexif)
                
                **Tipp:** Installieren Sie zusätzliche Bibliotheken:
                ```bash
                pip install exifread piexif
                ```
                """)

elif directory_path:
    st.error(f"Verzeichnis nicht gefunden: {directory_path}")
else:
    st.info("Bitte geben Sie einen Verzeichnis-Pfad ein, um zu starten.")

# Hilfe-Bereich
st.divider()
with st.expander("Hilfe & Dokumentation"):
    st.markdown("""
    ### Was ist RegionList?
    
    RegionList ist ein XMP-Metadaten-Tag, das annotierte Regionen in Bildern beschreibt.
    Es wird häufig für Gesichtserkennung und Person-Annotation verwendet.
    
    ### Unterstützte Formate
    
    - **JPEG/JPG**: XMP-Metadaten können in JPEG-Dateien eingebettet sein
    - **TIFF/TIF**: Unterstützt XMP-Metadaten
    - **XMP**: Separate XMP-Dateien werden ebenfalls gelesen
    
    ### Extraktions-Methoden
    
    Die App versucht verschiedene Methoden:
    1. **Exifread**: Liest XMP-Tags aus EXIF-Daten
    2. **Pillow XMP**: Nutzt PIL für XMP-Metadaten
    3. **XMP-Dateien**: Liest separate .xmp-Dateien
    4. **Piexif**: Erweiterte EXIF/XMP-Extraktion
    
    ### Output-Formate
    
    - **JSON**: Vollständige RegionList-Daten im JSON-Format
    - **CSV**: Flache Struktur für Tabellenkalkulation
    
    ### Installation zusätzlicher Bibliotheken
    
    Für bessere XMP-Unterstützung:
    ```bash
    pip install exifread piexif
    ```
    """)

