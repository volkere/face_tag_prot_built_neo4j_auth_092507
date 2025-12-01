"""
Import (Manuell) Page

Führt Django-Management-Befehle aus, um Regions-Daten aus PBF-DAMS zu exportieren.
"""
import streamlit as st
import subprocess
import os
import json
import tempfile
from datetime import datetime
import sys

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from streamlit_styles import apply_custom_css

st.set_page_config(
    page_title="Import (Manuell)",
    page_icon="",
    layout="wide"
)

BASE_DIR = os.path.dirname(__file__)
EXPORT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "exported"))
CONVERTED_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "converted"))
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)

# Wende kleinere Schriftgrößen an
apply_custom_css()

st.title("Import (Manuell)")
st.markdown("""
Manueller Import: Exportiere und konvertiere Image-Region-Daten (XMP-Metadaten) aus dem PBF-DAMS Django Backend
mit Hilfe von Django-Management-Befehlen.

**WICHTIG:** Beim Export werden **ALLE Regionen aus RegionList** exportiert (keine Limitierung).
""")

# Sidebar: Konfiguration
with st.sidebar:
    st.header("Konfiguration")
    
    # Django-Projekt-Pfad
    django_project_path = st.text_input(
        "Django-Projekt Pfad",
        value="/Users/volkerenkrodt/Documents/pbf-dams/app",
        help="Pfad zum PBF-DAMS Django-Projekt (mit manage.py)"
    )
    
    # Pipenv aktivieren
    use_pipenv = st.checkbox(
        "Pipenv verwenden",
        value=True,
        help="Wenn aktiviert, wird 'pipenv run' verwendet"
    )
    
    # Verbindungstest
    if st.button("Pfad prüfen"):
        manage_py_path = os.path.join(django_project_path, "manage.py")
        if os.path.exists(manage_py_path):
            st.success("manage.py gefunden!")
        else:
            st.error(f"manage.py nicht gefunden in: {django_project_path}")

# Tabs für Export, Konvertierung und Gesichts-Ordner
tab1, tab2, tab3 = st.tabs(
    ["Export-aus-PBF-DAMS", "Konvertierung zu Trainingsformat", "Export-aus-Fotos"]
)

# TAB 1: EXPORT
with tab1:
    st.header("Export-Konfiguration")
    
    col1, col2 = st.columns(2)

    with col1:
        # Person-Filter
        st.subheader("Person-Filter")
        person_identifier = st.text_input(
            "Person-Identifier",
            value="pina_bausch",
            placeholder="z.B. pina_bausch",
            help="Identifier der Person im PBF-DAMS"
        )
        
        export_all_persons = st.checkbox(
            "Alle Personen exportieren",
            value=False,
            help="Wenn aktiviert, wird --person Parameter weggelassen"
        )

    with col2:
        # Output-Konfiguration
        st.subheader("Output-Konfiguration")
        st.info(f"Exportierte Regions-Dateien werden in **{EXPORT_DIR}** gespeichert.")
        output_filename = st.text_input(
            "Output-Dateiname",
            value=f"regions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            help="Name der Export-Datei"
        )

    # Erweiterte Optionen
    with st.expander("Erweiterte Optionen", expanded=False):
        photo_identifier = st.text_input(
            "Foto-Identifier (optional)",
            value="",
            help="Optional: Nur Regions für ein bestimmtes Foto exportieren"
        )
        
        include_unidentified = st.checkbox(
            "Private Personen inkludieren",
            value=False,
            help="Exportiert auch nicht-öffentliche Personen"
        )
        
        export_all_regions = st.checkbox(
            "Alle Regionen exportieren (keine Limitierung)",
            value=True,
            help="⚠️ WICHTIG: Aktiviert, um sicherzustellen, dass ALLE Regionen aus RegionList exportiert werden"
        )

    # Export-Button
    st.divider()
    
    if st.button("Export starten", type="primary", use_container_width=True, key="export_btn"):
        # Validierung
        manage_py_path = os.path.join(django_project_path, "manage.py")
        if not os.path.exists(manage_py_path):
            st.error(f"manage.py nicht gefunden in: {django_project_path}")
            st.stop()
        
        # Output-Pfad
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Kommando zusammenbauen
        if use_pipenv:
            base_cmd = ["pipenv", "run", "python", "manage.py"]
        else:
            base_cmd = ["python", "manage.py"]
        
        cmd = base_cmd + ["export_for_pba_tagg"]
        
        # Parameter hinzufügen
        if not export_all_persons and person_identifier:
            cmd.extend(["--person", person_identifier])
        
        if photo_identifier:
            cmd.extend(["--photo", photo_identifier])
        
        if include_unidentified:
            cmd.append("--include-unidentified")
        
        # WICHTIG: Sicherstellen, dass alle Regionen exportiert werden
        # Der Django-Befehl export_for_pba_tagg exportiert standardmäßig ALLE Regionen
        # aus RegionList, es sei denn, es werden Filter angewendet (--person, --photo)
        # Es wird KEIN --limit Parameter übergeben, um sicherzustellen, dass alle exportiert werden
        
        cmd.extend(["--output", output_path])
        
        # Kommando anzeigen
        st.code(" ".join(cmd), language="bash")
        
        # Kommando ausführen
        with st.spinner("Export läuft..."):
            try:
                # Wechsle ins Django-Projekt-Verzeichnis
                process = subprocess.Popen(
                    cmd,
                    cwd=django_project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Output-Streaming
                output_container = st.empty()
                output_lines = []
                error_lines = []
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    output_lines = stdout.split('\n')
                if stderr:
                    error_lines = stderr.split('\n')
                
                # Ergebnis anzeigen
                if process.returncode == 0:
                    st.success("Export erfolgreich abgeschlossen!")
                    
                    # Output anzeigen
                    if output_lines:
                        with st.expander("Befehl-Output", expanded=True):
                            for line in output_lines:
                                if line.strip():
                                    st.text(line)
                    
                    # Datei-Info
                    if os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        st.info(f"Datei erstellt: {output_path} ({file_size:,} Bytes)")
                        
                        # JSON-Vorschau
                        try:
                            with open(output_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            st.subheader("Export-Vorschau")
                            
                            # Statistiken
                            col1, col2, col3 = st.columns(3)
                            
                            # Anzahl der exportierten Regionen
                            region_count = 0
                            if isinstance(data, dict):
                                if 'count' in data:
                                    region_count = data.get('count', 0)
                                elif 'regions' in data:
                                    region_count = len(data.get('regions', []))
                            elif isinstance(data, list):
                                region_count = len(data)
                            
                            with col1:
                                st.metric("Exportierte Regions", region_count)
                                
                                # Warnung wenn keine Regionen exportiert wurden
                                if region_count == 0:
                                    st.warning("⚠️ Keine Regionen exportiert! Prüfen Sie die Filter-Einstellungen.")
                                elif export_all_regions:
                                    st.success(f"✅ {region_count} Regionen exportiert (alle aus RegionList)")
                            with col2:
                                if isinstance(data, dict) and 'regions' in data:
                                    unique_photos = len(set(
                                        r.get('photo_identifier', '')
                                        for r in data.get('regions', [])
                                        if r.get('photo_identifier')
                                    ))
                                    st.metric("Unique Fotos", unique_photos)
                            with col3:
                                if isinstance(data, dict) and 'regions' in data:
                                    unique_persons = len(set(
                                        r.get('person', {}).get('identifier', '')
                                        for r in data.get('regions', [])
                                        if r.get('person', {}).get('identifier')
                                    ))
                                    st.metric("Unique Personen", unique_persons)
                            
                            # Download-Button
                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    label="Export-Datei herunterladen",
                                    data=f.read(),
                                    file_name=output_filename,
                                    mime="application/json",
                                    use_container_width=True
                                )
                            
                            # Raw JSON anzeigen (optional)
                            with st.expander("Raw JSON anzeigen"):
                                st.json(data)
                        
                        except json.JSONDecodeError:
                            st.warning("Datei konnte nicht als JSON geparst werden")
                            with open(output_path, 'r', encoding='utf-8') as f:
                                st.text(f.read())
                    else:
                        st.warning(f"Datei nicht gefunden: {output_path}")
                else:
                    st.error("Export fehlgeschlagen!")
                    
                    if error_lines:
                        with st.expander("Fehler-Details", expanded=True):
                            for line in error_lines:
                                if line.strip():
                                    st.error(line)
                    
                    if output_lines:
                        with st.expander("Output", expanded=False):
                            for line in output_lines:
                                if line.strip():
                                    st.text(line)
            
            except FileNotFoundError:
                if use_pipenv:
                    st.error("pipenv nicht gefunden. Ist Pipenv installiert?")
                else:
                    st.error("python nicht gefunden. Ist Python installiert?")
            except Exception as e:
                st.error(f"Fehler beim Ausführen des Befehls: {e}")
    
    # Hilfe-Bereich für Export
    st.divider()
    
    with st.expander("Hilfe & Dokumentation - Export"):
        st.markdown("""
### Wie funktioniert der Export?
    
    1. **Django-Projekt-Pfad** muss korrekt gesetzt sein (Verzeichnis mit manage.py)
    2. **Person-Identifier** eingeben (optional: alle Personen exportieren)
    3. **Output-Dateiname** anpassen (Standard: automatisch generiert)
    4. **Export starten** - Der Django-Management-Befehl wird ausgeführt
    
    ### Befehl-Details
    
    Der ausgeführte Befehl:
    ```bash
    pipenv run python manage.py export_for_pba_tagg \\
        --person <person_identifier> \\
        --output <output_path>
    ```
    
    **WICHTIG:** Es wird **KEIN** `--limit` Parameter übergeben, um sicherzustellen, dass **ALLE Regionen aus RegionList** exportiert werden.
    
    **Parameter:**
    - `--person`: Identifier der Person (optional, wenn "Alle Personen" aktiviert)
    - `--photo`: Identifier eines Fotos (optional, in erweiterten Optionen)
    - `--include-unidentified`: Private Personen inkludieren
    - `--output`: Pfad zur Output-JSON-Datei
    - **KEIN `--limit`**: Alle Regionen werden exportiert (keine Limitierung)
    
    ### Export-Format
    
    Die Export-Datei enthält:
    - Regions-Daten mit Koordinaten
    - Personen-Informationen
    - Foto-Informationen
    - Metadaten (falls verfügbar)
    
    **JSON-Struktur:**
    ```json
    {
      "count": 123,
      "regions": [
        {
          "photo_identifier": "...",
          "person": {
            "identifier": "...",
            "label": "..."
          },
          "x": 0.3,
          "y": 0.4,
          "width": 0.15,
          "height": 0.2,
          ...
        }
      ]
    }
    ```
    
    ### Voraussetzungen
    
    - PBF-DAMS Django-Projekt muss vorhanden sein
    - `manage.py export_for_pba_tagg` Befehl muss existieren
    - Pipenv installiert (wenn "Pipenv verwenden" aktiviert)
    - Django-Server muss nicht laufen (Datenbank-Zugriff erforderlich)
    """)
    
    st.info("""
    **Tipp:** Stellen Sie sicher, dass das Django-Projekt und die Datenbank erreichbar sind.
    Der Export greift direkt auf die Datenbank zu und benötigt keinen laufenden Server.
    """)

# TAB 2: KONVERTIERUNG
with tab2:
    st.header("Konvertierung zu Trainingsformat")
    st.markdown("""
    Konvertiere exportierte Regions-Daten in ein Trainingsformat für PBA_Tagg.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input-Datei")
        # Möglichkeit zum Upload oder Pfad-Eingabe
        input_method = st.radio(
            "Input-Methode:",
            options=["Datei-Upload", "Pfad-Eingabe"],
            horizontal=True
        )
        
        input_file_upload = None
        input_file_path = None
        
        if input_method == "Datei-Upload":
            input_file_upload = st.file_uploader(
                "Regions-JSON-Datei hochladen",
                type=["json"],
                help="Laden Sie eine exportierte Regions-JSON-Datei hoch",
                key="convert_input_upload"
            )
        else:
            input_file_path = st.text_input(
                "Input-Datei Pfad",
                value="",
                placeholder="../pina_regions.json oder /absoluter/pfad/pina_regions.json",
                help="Relativer Pfad (vom Django-Projekt aus) oder absoluter Pfad zur Regions-JSON-Datei",
                key="convert_input_path"
            )
            
            # Beispiel-Pfade anzeigen
            if not input_file_path:
                st.info("""
                **Beispiele für Pfade:**
                - Relativ: `../pina_regions.json` (ein Verzeichnis über dem Django-Projekt)
                - Relativ: `exports/pina_regions.json` (im exports-Ordner des Django-Projekts)
                - Absolut: `/Users/.../pina_regions.json`
                """)
    
    with col2:
        st.subheader("Output-Konfiguration")
        st.info(f"Konvertierte Dateien werden in **{CONVERTED_DIR}** gespeichert.")
        
        # Default-Output-Dateiname basierend auf Input-Datei
        output_key = "convert_output_filename"
        default_output_name = f"regions_converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Wenn Datei hochgeladen wurde, verwende ihren ursprünglichen Namen als Basis
        if input_file_upload is not None:
            original_name = input_file_upload.name
            # Entferne Extension und füge _converted hinzu (aber nicht doppelt)
            base_name = os.path.splitext(original_name)[0]
            # Prüfe ob bereits "_converted" oder "_training" im Namen enthalten ist
            if not (base_name.endswith("_converted") or base_name.endswith("_training")):
                default_output_name = f"{base_name}_converted.json"
            else:
                # Bereits _converted oder _training im Namen, ersetze durch _converted
                if base_name.endswith("_training"):
                    base_name = base_name[:-9]  # Entferne "_training"
                elif base_name.endswith("_converted"):
                    base_name = base_name[:-10]  # Entferne "_converted"
                default_output_name = f"{base_name}_converted.json"
        elif input_file_path and input_file_path.strip():
            # Extrahiere Dateinamen aus dem Pfad
            original_name = os.path.basename(input_file_path.strip())
            if original_name and original_name != "":
                base_name = os.path.splitext(original_name)[0]
                if base_name:
                    # Prüfe ob bereits "_converted" oder "_training" im Namen enthalten ist
                    if not (base_name.endswith("_converted") or base_name.endswith("_training")):
                        default_output_name = f"{base_name}_converted.json"
                    else:
                        # Bereits _converted oder _training im Namen, ersetze durch _converted
                        if base_name.endswith("_training"):
                            base_name = base_name[:-9]  # Entferne "_training"
                        elif base_name.endswith("_converted"):
                            base_name = base_name[:-10]  # Entferne "_converted"
                        default_output_name = f"{base_name}_converted.json"
        
        # Prüfe ob Output-Dateiname bereits in Session State existiert
        # Wenn eine neue Datei hochgeladen wurde, aktualisiere den Namen
        if output_key not in st.session_state or (input_file_upload is not None or (input_file_path and input_file_path.strip())):
            st.session_state[output_key] = default_output_name
        
        training_output_filename = st.text_input(
            "Output-Dateiname",
            value=st.session_state.get(output_key, default_output_name),
            help="Name der konvertierten Export-Datei (wird automatisch aus Input-Dateinamen generiert)",
            key=output_key
        )
    
    # Konvertierungs-Button
    st.divider()
    
    if st.button("Konvertierung starten", type="primary", use_container_width=True, key="convert_btn"):
        # Validierung
        manage_py_path = os.path.join(django_project_path, "manage.py")
        if not os.path.exists(manage_py_path):
            st.error(f"manage.py nicht gefunden in: {django_project_path}")
            st.stop()
        
        # Input-Datei bestimmen
        input_file = None
        temp_input_file = None
        
        if input_method == "Datei-Upload":
            if input_file_upload is None:
                st.error("Bitte laden Sie eine JSON-Datei hoch.")
                st.stop()
            
            # Temporäre Datei erstellen für Upload
            temp_input_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            temp_input_file.write(input_file_upload.read().decode('utf-8'))
            temp_input_file.close()
            input_file = temp_input_file.name
        else:
            if not input_file_path:
                st.error("Bitte geben Sie einen Input-Datei-Pfad ein.")
                st.stop()
            
            # Prüfe ob Pfad relativ oder absolut ist
            if os.path.isabs(input_file_path):
                # Absoluter Pfad
                if not os.path.exists(input_file_path):
                    st.error(f"Input-Datei nicht gefunden: {input_file_path}")
                    st.stop()
                input_file = input_file_path
            else:
                # Relativer Pfad - relativ zum Django-Projekt-Verzeichnis
                input_file_abs = os.path.join(django_project_path, input_file_path)
                if not os.path.exists(input_file_abs):
                    # Versuche auch relativ zum aktuellen Verzeichnis
                    input_file_abs = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", input_file_path))
                    if not os.path.exists(input_file_abs):
                        st.error(f"Input-Datei nicht gefunden: {input_file_path}")
                        st.error(f"Versucht: {os.path.join(django_project_path, input_file_path)}")
                        st.error(f"Versucht: {input_file_abs}")
                        st.stop()
                input_file = input_file_path  # Verwende relativen Pfad für den Befehl
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(CONVERTED_DIR, exist_ok=True)

        output_path = os.path.join(CONVERTED_DIR, training_output_filename)
        
        # Kommando zusammenbauen
        if use_pipenv:
            base_cmd = ["pipenv", "run", "python", "manage.py"]
        else:
            base_cmd = ["python", "manage.py"]
        
        # Output-Pfad: Versuche beide Varianten (absolut und relativ)
        # Der Django-Befehl könnte den Pfad unterschiedlich interpretieren
        output_arg = output_path  # Verwende absoluten Pfad
        
        # Berechne auch relativen Pfad als Alternative
        try:
            rel_path_from_django = os.path.relpath(output_path, django_project_path)
            # Wenn relativer Pfad zu viele ".." enthält, liegt er außerhalb
            # In diesem Fall muss absoluter Pfad verwendet werden
        except ValueError:
            # Pfade sind auf verschiedenen Laufwerken, muss absoluten Pfad verwenden
            rel_path_from_django = None
        
        cmd = base_cmd + ["convert_to_training_format", input_file, "--output", output_arg]
        
        # Kommando anzeigen
        st.code(" ".join(cmd), language="bash")
        
        # Kommando ausführen
        with st.spinner("Konvertierung läuft..."):
            try:
                # Wechsle ins Django-Projekt-Verzeichnis
                process = subprocess.Popen(
                    cmd,
                    cwd=django_project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                stdout, stderr = process.communicate()
                
                output_lines = []
                error_lines = []
                
                if stdout:
                    output_lines = stdout.split('\n')
                if stderr:
                    error_lines = stderr.split('\n')
                
                # Temporäre Datei löschen (wenn erstellt)
                if temp_input_file and os.path.exists(temp_input_file.name):
                    try:
                        os.unlink(temp_input_file.name)
                    except:
                        pass
                
                # Ergebnis anzeigen
                if process.returncode == 0:
                    st.success("Konvertierung erfolgreich abgeschlossen!")
                    
                    # Output anzeigen
                    if output_lines:
                        with st.expander("Befehl-Output", expanded=True):
                            for line in output_lines:
                                if line.strip():
                                    st.text(line)
                    
                    # Datei-Info - prüfe ob Datei im erwarteten Verzeichnis existiert
                    file_found = False
                    
                    # Liste aller möglichen Speicherorte
                    possible_locations = [
                        output_path,  # Erwarteter Speicherort (absoluter Pfad)
                        os.path.join(django_project_path, training_output_filename),  # Django-Verzeichnis
                        os.path.join(django_project_path, os.path.basename(output_path)),  # Nur Dateiname im Django-Verzeichnis
                        os.path.join(django_project_path, "converted", training_output_filename),  # converted-Ordner im Django-Projekt
                        os.path.join(os.getcwd(), training_output_filename),  # Aktuelles Arbeitsverzeichnis
                        os.path.join(CONVERTED_DIR, training_output_filename),  # CONVERTED_DIR nochmal
                    ]
                    
                    # Füge Hinweise aus Befehl-Output hinzu
                    if 'file_path_hints' in locals():
                        possible_locations.extend(file_path_hints)
                    
                    # Füge auch Varianten mit verschiedenen Suffixen hinzu
                    base_filename = os.path.splitext(training_output_filename)[0]
                    
                    # Entferne mögliche Suffixe und füge Varianten hinzu
                    if base_filename.endswith("_converted"):
                        clean_base = base_filename[:-10]
                    elif base_filename.endswith("_training"):
                        clean_base = base_filename[:-9]
                    else:
                        clean_base = base_filename
                    
                    # Füge verschiedene Suffix-Varianten hinzu
                    suffix_variants = [
                        f"{clean_base}_converted.json",
                        f"{clean_base}_training.json",
                        f"{clean_base}.json"
                    ]
                    
                    for variant in suffix_variants:
                        if variant != training_output_filename:  # Nicht den bereits geprüften Namen
                            possible_locations.extend([
                                os.path.join(CONVERTED_DIR, variant),
                                os.path.join(django_project_path, variant),
                                os.path.join(django_project_path, "converted", variant),
                            ])
                    
                    # Prüfe auch relativ zum Django-Projekt-Verzeichnis
                    try:
                        rel_path = os.path.relpath(output_path, django_project_path)
                        possible_locations.append(os.path.join(django_project_path, rel_path))
                    except ValueError:
                        pass
                    
                    # Prüfe alle möglichen Orte
                    found_location = None
                    for loc in possible_locations:
                        if os.path.exists(loc) and os.path.isfile(loc):
                            found_location = loc
                            break
                    
                    if found_location:
                        # Datei wurde gefunden
                        if found_location != output_path:
                            # Verschiebe Datei zum erwarteten Ort
                            import shutil
                            try:
                                # Stelle sicher, dass Ziel-Verzeichnis existiert
                                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                                shutil.move(found_location, output_path)
                                st.warning(f"⚠️ Datei wurde an anderem Ort gefunden ({found_location}) und nach {output_path} verschoben.")
                            except Exception as e:
                                st.warning(f"⚠️ Datei gefunden unter: {found_location}")
                                st.info(f"Konnte nicht verschoben werden: {e}")
                                output_path = found_location  # Verwende gefundenen Pfad
                        file_found = True
                    else:
                        # Datei nicht gefunden - suche nach neu erstellten JSON-Dateien
                        st.warning("⚠️ Datei nicht an erwartetem Ort gefunden. Suche nach neu erstellten Dateien...")
                        
                        # Suche nach JSON-Dateien, die kürzlich im Django-Projekt-Verzeichnis erstellt wurden
                        import time
                        recent_files = []
                        cutoff_time = time.time() - 120  # Letzte 120 Sekunden
                        
                        # Suche auch im CONVERTED_DIR
                        search_dirs = [django_project_path, CONVERTED_DIR, os.path.dirname(output_path)]
                        
                        for search_dir in search_dirs:
                            if not os.path.exists(search_dir):
                                continue
                            try:
                                for root, dirs, files in os.walk(search_dir):
                                    # Begrenze die Suche (nicht zu tief)
                                    depth = root[len(search_dir):].count(os.sep)
                                    if depth > 2:
                                        dirs[:] = []  # Überspringe weitere Unterverzeichnisse
                                        continue
                                    
                                    for file in files:
                                        if file.endswith('.json'):
                                            file_path = os.path.join(root, file)
                                            try:
                                                mtime = os.path.getmtime(file_path)
                                                if mtime > cutoff_time:
                                                    # Prüfe ob Dateiname ähnlich ist
                                                    if (training_output_filename in file or 
                                                        os.path.splitext(training_output_filename)[0] in file or
                                                        'training' in file.lower()):
                                                        recent_files.append((file_path, mtime))
                                            except:
                                                pass
                            except Exception:
                                pass
                        
                        # Sortiere nach Erstellungszeit (neueste zuerst)
                        recent_files.sort(key=lambda x: x[1], reverse=True)
                        
                        if recent_files:
                            st.info(f"Gefundene neu erstellte JSON-Dateien:")
                            for rf_path, rf_time in recent_files[:5]:  # Zeige nur die 5 neuesten
                                st.write(f"- {rf_path} (vor {int(time.time() - rf_time)} Sekunden)")
                                
                                # Versuche zu verschieben (nur die neueste)
                                if not file_found:
                                    try:
                                        import shutil
                                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                                        
                                        # Wenn Datei bereits existiert, benenne um
                                        if os.path.exists(output_path) and rf_path != output_path:
                                            backup_path = output_path + f".backup_{int(time.time())}"
                                            shutil.move(output_path, backup_path)
                                        
                                        shutil.move(rf_path, output_path)
                                        st.success(f"✅ Datei {rf_path} wurde nach {output_path} verschoben.")
                                        file_found = True
                                        break
                                    except Exception as e:
                                        st.warning(f"Konnte {rf_path} nicht verschieben: {e}")
                        
                        if not file_found:
                            # Zeige alle geprüften Orte
                            st.error(f"❌ Datei nicht gefunden!")
                            st.write("**Geprüfte Speicherorte:**")
                            for loc in possible_locations:
                                exists = os.path.exists(loc)
                                st.write(f"- {loc}: {'✅ Exists' if exists else '❌ Nicht gefunden'}")
                            
                            # Zeige Befehl-Output nochmal für Debugging
                            if output_lines:
                                st.info("**Befehl-Output (kann Hinweise auf Speicherort geben):**")
                                for line in output_lines:
                                    if line.strip() and ('output' in line.lower() or 'file' in line.lower() or 'saved' in line.lower()):
                                        st.code(line)
                    
                    if file_found and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        st.success(f"✅ Datei erfolgreich erstellt: {output_path} ({file_size:,} Bytes)")
                        
                        # JSON-Vorschau
                        try:
                            with open(output_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            st.subheader("Trainingsformat-Vorschau")
                            
                            # Statistiken
                            if isinstance(data, list):
                                st.metric("Training-Einträge", len(data))
                                
                                # Beispiel-Eintrag anzeigen
                                if len(data) > 0:
                                    st.subheader("Beispiel-Eintrag")
                                    st.json(data[0] if isinstance(data[0], dict) else {})
                            
                            elif isinstance(data, dict):
                                st.metric("Training-Einträge", data.get('count', 0))
                                if 'entries' in data and len(data['entries']) > 0:
                                    st.subheader("Beispiel-Eintrag")
                                    st.json(data['entries'][0] if isinstance(data['entries'][0], dict) else {})
                            
                            # Download-Button
                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    label="Trainingsformat-Datei herunterladen",
                                    data=f.read(),
                                    file_name=training_output_filename,
                                    mime="application/json",
                                    use_container_width=True
                                )
                            
                            # Raw JSON anzeigen (optional)
                            with st.expander("Raw JSON anzeigen"):
                                st.json(data)
                        
                        except json.JSONDecodeError:
                            st.warning("Datei konnte nicht als JSON geparst werden")
                            with open(output_path, 'r', encoding='utf-8') as f:
                                st.text(f.read())
                    elif not file_found:
                        st.error(f"❌ Datei nicht gefunden unter: {output_path}")
                        st.warning("**Mögliche Ursachen:**")
                        st.write("1. Der Django-Befehl hat die Datei nicht erstellt")
                        st.write("2. Die Datei wurde an einem anderen Ort gespeichert")
                        st.write("3. Prüfen Sie die Fehler-Details oben")
                        st.write(f"**Erwarteter Speicherort:** {output_path}")
                else:
                    st.error("Konvertierung fehlgeschlagen!")
                    
                    if error_lines:
                        with st.expander("Fehler-Details", expanded=True):
                            for line in error_lines:
                                if line.strip():
                                    st.error(line)
                    
                    if output_lines:
                        with st.expander("Output", expanded=False):
                            for line in output_lines:
                                if line.strip():
                                    st.text(line)
            
            except FileNotFoundError:
                if use_pipenv:
                    st.error("pipenv nicht gefunden. Ist Pipenv installiert?")
                else:
                    st.error("python nicht gefunden. Ist Python installiert?")
            except Exception as e:
                st.error(f"Fehler beim Ausführen des Befehls: {e}")
    
    # Hilfe-Bereich für Konvertierung
    st.divider()
    
    with st.expander("Hilfe & Dokumentation - Konvertierung"):
        st.markdown("""
        ### Wie funktioniert die Konvertierung?
        
        1. **Input-Datei** hochladen oder Pfad eingeben (exportierte Regions-JSON)
        2. **Output-Dateiname** anpassen (Standard: automatisch generiert)
        3. **Konvertierung starten** - Der Django-Management-Befehl wird ausgeführt
        
        ### Befehl-Details
        
        Der ausgeführte Befehl:
        ```bash
        pipenv run python manage.py convert_to_training_format \\
            <input_file> \\
            --output <output_path>
        ```
        
        **Parameter:**
        - `input_file`: Pfad zur exportierten Regions-JSON-Datei
        - `--output`: Pfad zur Output-JSON-Datei im Trainingsformat
        
        ### Trainingsformat
        
        Die konvertierte Datei enthält:
        - Strukturiertes Format für PBA_Tagg Training
        - Personen-Daten
        - Foto-Referenzen
        - Region-Koordinaten
        - Metadaten für Training
        
        ### Voraussetzungen
        
        - PBF-DAMS Django-Projekt muss vorhanden sein
        - `manage.py convert_to_training_format` Befehl muss existieren
        - Pipenv installiert (wenn "Pipenv verwenden" aktiviert)
        - Input-Datei muss im Regions-Export-Format vorliegen
        """)
    
    st.info("""
    **Tipp:** Die Konvertierung wandelt Regions-Daten in ein Format um, das direkt für das
    PBA_Tagg Training verwendet werden kann.
    """)

# TAB 3: GESICHTS-ORDNER-EXPORT
with tab3:
    st.header("Gesichts-Ordner-Export")
    st.markdown(
        """
        Exportiert Gesichtsregionen (Name + Koordinaten) direkt aus lokalen Bildern per
        Django-Command `export_face_regions`.
        """
    )

    face_paths_text = st.text_area(
        "Bild-/Ordnerpfade (eine pro Zeile)",
        value="~/bilder/sammlung",
        help="Gib ein oder mehrere Pfade zu Bilddateien oder Ordnern an.",
    )
    face_paths = [p.strip() for p in face_paths_text.splitlines() if p.strip()]

    st.caption("Hinweis: Unterordner werden automatisch durchsucht.")
    face_format = st.selectbox("Ausgabeformat", ["json", "csv"], index=0)

    face_output_filename = st.text_input(
        "Output-Dateiname",
        value=f"faces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{face_format}",
    )

    st.divider()
    if st.button(
        "Gesichts-Export starten",
        type="primary",
        use_container_width=True,
        key="face_export_btn",
    ):
        manage_py_path = os.path.join(django_project_path, "manage.py")
        if not os.path.exists(manage_py_path):
            st.error(f"manage.py nicht gefunden in: {django_project_path}")
            st.stop()

        if not face_paths:
            st.error("Bitte mindestens einen Pfad angeben.")
            st.stop()

        output_path = os.path.join(EXPORT_DIR, face_output_filename)
        os.makedirs(EXPORT_DIR, exist_ok=True)

        if use_pipenv:
            base_cmd = ["pipenv", "run", "python", "manage.py"]
        else:
            base_cmd = ["python", "manage.py"]

        cmd = base_cmd + ["export_face_regions"] + face_paths
        if face_format == "csv":
            cmd.extend(["--format", "csv"])
        cmd.extend(["--output", output_path])

        st.code(" ".join(cmd), language="bash")

        with st.spinner("Gesichts-Export läuft..."):
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=django_project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    st.error("Export fehlgeschlagen!")
                    if stderr:
                        st.error(stderr)
                    if stdout:
                        st.text(stdout)
                else:
                    st.success("Export erfolgreich abgeschlossen!")
                    if stdout:
                        with st.expander("Befehl-Output", expanded=False):
                            st.text(stdout)

                    if os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        st.info(f"Datei erstellt: {output_path} ({file_size:,} Bytes)")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Gesichts-Datei herunterladen",
                                data=f.read(),
                                file_name=face_output_filename,
                                mime="text/csv"
                                if face_format == "csv"
                                else "application/json",
                                use_container_width=True,
                            )
                        if face_format == "json":
                            try:
                                with open(output_path, "r", encoding="utf-8") as f:
                                    preview_data = json.load(f)
                                st.subheader("Vorschau")
                                if isinstance(preview_data, list):
                                    st.json(preview_data[:2])
                                else:
                                    st.json(preview_data)
                            except json.JSONDecodeError:
                                st.warning("JSON konnte nicht geladen werden.")
                    else:
                        st.warning(f"Datei nicht gefunden: {output_path}")
            except Exception as e:
                st.error(f"Fehler beim Ausführen des Befehls: {e}")
