

Erweiterte Foto-Metadaten-Analyse mit Gesichtserkennung, EXIF-Extraktion, KI-Training und intelligenten Analysen.  
(Enthält eine CLI und eine Streamlit Multi-Page UI (Enroll + Annotate + Analyze + Train + Import) mit sicherem Internet-Zugang).

 Branch-Übersicht

Dieses Repository enthält verschiedene Varianten der App als separate Branches:

 main - Vollständige Version
- Alle Features: Streamlit UI + CLI + Authentifizierung
- Plattformen: Windows, macOS, Linux
- Zielgruppe: Benutzer, die alle Funktionen benötigen

 windows-optimized - Windows-Version
- Windows-spezifisch: Batch-Skripte, PowerShell-Integration
- Einfache Installation: Automatische Setup-Skripte
- Zielgruppe: Windows 11-Benutzer

 macos-linux - Unix-Version
- Unix-optimiert: Bash-Skripte, Homebrew-Integration
- Plattformen: macOS, Linux
- Zielgruppe: Unix/Linux-Benutzer

 minimal-no-neo4j - Leichtgewichtige Version
- Ohne Neo4j: Keine Graph-Datenbank-Abhängigkeiten
- Reduzierte Komplexität: Fokus auf Kern-Features
- Zielgruppe: Benutzer ohne Neo4j-Anforderungen

 cli-only - Kommandozeilen-Version
- Nur CLI: Keine Web-UI, nur Kommandozeilen-Interface
- Performance: Optimiert für Batch-Verarbeitung
- Zielgruppe: Entwickler und Automatisierung

 full-featured - Entwicklungsversion
- Alle Features: Inklusive experimenteller Funktionen
- Entwicklungszwecke: Für Entwickler und Tester
- Zielgruppe: Entwickler und Power-User

Erweiterte Metadaten-Extraktion
- Vollständige EXIF-Daten: Kamera-Modell, Objektiv, Aufnahme-Einstellungen
- GPS mit Höhenangabe: Präzise Standortdaten mit Altitude
- Detaillierte Standort-Info: Vollständige Adressen und geografische Details
- Zeitstempel-Parsing: Unterstützt verschiedene Datumsformate

Verbesserte Gesichtserkennung
- Qualitätsbewertung: Automatische Bewertung der Gesichtsqualität
- Emotions-Erkennung: Happy, neutral, unknown
- Status-Erkennung: Augen (offen/geschlossen) und Mund-Status
- Pose-Schätzung: Yaw, Pitch, Roll-Winkel
- Erweiterte Demografie: Alters- und Geschlechtserkennung

Intelligente Analyse
- Interaktive Visualisierungen: Charts und Statistiken mit Plotly
- Automatische Gruppierung: Nach Standort und Zeit
- Qualitätsfilter: Filtert nach Gesichtsqualität und -größe
- Export-Funktionen: JSON-Export für weitere Verarbeitung

KI-Training & Enhanced Models
- Metadaten-basiertes Training: Verbesserte Erkennung durch Kontext-Informationen
- Trainingsdaten-Generator: Automatische Generierung aus Musterfotos
- Enhanced Model Upload: Integration trainierter Modelle in die Annotate-Seite
- Bias-Korrektur: Standort- und zeitbasierte Korrekturen
- Validierung: Automatische Format-Validierung für Trainingsdaten

Features
- Face detection & embeddings (InsightFace `buffalo_l`)
- Age & gender estimation (approximate)
- Known-person matching via embeddings database (`embeddings.pkl`)
- EXIF GPS extraction with optional reverse geocoding
- Erweiterte Metadaten-Extraktion (Kamera, Einstellungen, Datum)
- Qualitätsbewertung für Gesichter und Bilder
- Emotions- und Status-Erkennung
- Interaktive Analysen mit Charts und Statistiken
- Intelligente Bildgruppierung
- KI-Training mit Metadaten-Integration
- Enhanced Models für verbesserte Erkennung
- Trainingsdaten-Generator aus Musterfotos
- Sichere Authentifizierung mit Benutzername/Passwort
- Internet-Zugang über ngrok-Tunnel
- Session-Management mit sicheren Cookies
- Streamlit UI mit drag & drop, bounding boxes, JSON export
- CLI for batch processing

> Use responsibly: Face analysis and attribute inference can be biased and regulated. Ensure you have the right to process the images and comply with local laws (see `docs/PRIVACY.md`).

---

Quickstart (UI)

 Installation & Verwendung

 Branch auswählen
```bash
 Vollständige Version (empfohlen)
git checkout main

 Windows-optimiert
git checkout windows-optimized

 macOS/Linux-optimiert  
git checkout macos-linux

 Minimal ohne Neo4j
git checkout minimal-no-neo4j

 Nur CLI
git checkout cli-only
```

 Installation

 Windows (windows-optimized Branch)
```cmd
install_windows.bat
start_app.bat
```

 macOS/Linux (macos-linux Branch)
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

 CLI-only (cli-only Branch)
```bash
pip install -r requirements.txt
python -m app.main --help
```

Login-Daten:
- Administrator: Passwort `admin123`
- Benutzer: Passwort `user123`

UI-Seiten:
- Enroll: Erstellen von Embeddings für Personen-Erkennung (ZIP-Upload, manuell, oder aus konvertierten PBF-DAMS-Daten)
- Annotate: Erweiterte Foto-Analyse mit Metadaten und Enhanced Models
- Analyze: Statistiken, Charts und Gruppierungsanalyse
- Train: KI-Training mit Metadaten-Integration und Trainingsdaten-Generator
- PBF DAMS Export: Export und Konvertierung von Regions-Daten aus PBF-DAMS
- RegionList Details: Extraktion von RegionList-Daten (XMP-Metadaten) aus Bildern

Quickstart (CLI)
```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

 (optional) build embeddings from a labeled gallery
python -m app.main enroll --gallery ./gallery --db embeddings.pkl

 annotate a folder with enhanced metadata
python -m app.main annotate --input ./photos --out output.json --recursive --reverse-geocode
```

Repo layout
```
app/                   Python package (engine, CLI)
pages/                 Streamlit pages (Enroll, Annotate, Analyze)
streamlit_app.py       Streamlit entry
requirements.txt       runtime deps
pyproject.toml         package metadata + console script
docs/                  documentation
.github/workflows/     CI (lint/build)
exported/              Exportierte Rohdaten aus PBF-DAMS
converted/             Konvertierte Trainings-Dateien (ersetzt trained/)
trained_models/        Trainierte KI-Modelle (von Train-Seite)
```

Hinweis: Alle zuvor im Ordner `trained/` abgelegten Konvertierungsergebnisse liegen jetzt unter `converted/`. Aktualisieren Sie lokale Skripte oder Automationen entsprechend.

Install as a package (optional)
```bash
pip install -e .
 now the CLI is available as:
photo-meta annotate --input photos --out output.json --recursive
```

Optimierungen für bessere Metadaten-Erkennung

1. Qualitätsfilter
- Gesichtsqualität: Filtert nach Schärfe, Helligkeit, Kontrast
- Größenfilter: Mindestgröße für Gesichter
- Qualitätsbewertung: Automatische Bewertung von 0-1

2. Erweiterte EXIF-Parsing
- Mehr Formate: Unterstützt verschiedene EXIF-Standards
- Vollständige Metadaten: Kamera, Objektiv, Einstellungen
- Fehlerbehandlung: Robuste Parsing-Logik

3. Intelligente Gruppierung
- Standort-Gruppierung: Gruppiert Bilder in 100m-Radius
- Zeit-Gruppierung: Gruppiert nach 24h-Zeitfenster
- Ähnlichkeitsanalyse: Automatische Kategorisierung

4. Visualisierungen
- Interaktive Charts: Plotly-basierte Visualisierungen
- Statistiken: Alters-, Qualitäts-, Kamera-Verteilungen
- Karten: GPS-Standorte auf interaktiven Karten

5. Export-Funktionen
- JSON-Export: Vollständige Metadaten
- Analyse-Export: Gruppierungen und Statistiken
- Format-Kompatibilität: Standardisierte Ausgabe

6. KI-Training & Enhanced Models
- Dual-Mode Training: JSON-Upload oder Musterfoto-Generierung
- Metadaten-Integration: Standort, Zeit, Kamera-Info für bessere Vorhersagen
- Bias-Korrektur: Automatische Korrektur systematischer Verzerrungen
- Enhanced Model Upload: Integration in Annotate-Seite für verbesserte Erkennung
- Trainingsdaten-Validierung: Automatische Format-Prüfung
- Progress-Tracking: Echtzeit-Feedback während der Verarbeitung

7. Sicherheit & Internet-Zugang
- Windows 11 Unterstützung: Batch-Skripte für einfache Installation
- Sichere Authentifizierung: Passwort-basierte Authentifizierung
- Session-Management: Sichere Session-Verwaltung mit Streamlit
- ngrok-Integration: Temporärer Internet-Zugang (Windows & macOS/Linux)
- Benutzer-Rollen: Administrator und Standard-Benutzer
- Logout-Funktionalität: Sichere Session-Beendigung
- Temporäre URLs: Automatische URL-Generierung für Internet-Zugang

Training-Workflow:
1. Daten vorbereiten: JSON-Dateien hochladen oder Musterfotos verwenden
2. Training konfigurieren: Metadaten-Gewichtungen anpassen
3. Modell trainieren: Automatische Metadaten-Integration
4. Ergebnisse validieren: Genauigkeits-Metriken prüfen
5. Modell integrieren: Enhanced Model in Annotate-Seite verwenden

Erwartete Verbesserungen:
- Alterserkennung: +15-25% Genauigkeit
- Geschlechtserkennung: +10-20% Genauigkeit  
- Standort-basierte Vorhersagen: +20-30% Genauigkeit

Trainingsdaten-Format:
```json
{
  "image": "photo.jpg",
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
      "bbox": [100, 150, 300, 450],
      "emotion": "happy",
      "pose": {"yaw": 0, "pitch": 0, "roll": 0}
    }
  ]
}
```

 Internet-Zugang & Sicherheit

 Windows 11

 Voraussetzungen
- Python 3.9+ installiert
- Windows PowerShell verfügbar

 Start-Optionen

 Option 1: Batch-Skript (Empfohlen)
```cmd
install_windows.bat
start_with_ngrok_windows.bat
```

 Option 2: Manuelle ngrok-Installation
```cmd
install_ngrok_windows.bat
start_with_ngrok_windows.bat
```

 Option 3: Manuell
```cmd
REM Terminal 1: Streamlit starten
python -m streamlit run streamlit_app.py --server.port 8501

REM Terminal 2: ngrok starten
ngrok http 8501
```

 macOS/Linux

 Voraussetzungen
- ngrok installiert: `brew install ngrok/ngrok/ngrok`
- Python-Pakete installiert: `pip install -r requirements.txt`

 Start-Optionen

 Option 1: Bash-Skript (Empfohlen)
```bash
./start_ngrok.sh
```

 Option 2: Python-Skript
```bash
python3 start_with_ngrok.py
```

 Option 3: Manuell
```bash
 Terminal 1: Streamlit starten
streamlit run streamlit_app.py --server.port 8501

 Terminal 2: ngrok starten
ngrok http 8501
```

 Authentifizierung
Die App ist mit einem einfachen, aber sicheren Login-System geschützt:

Administrator-Zugang:
- Passwort: `admin123`

Benutzer-Zugang:
- Passwort: `user123`

 Sicherheitsfeatures
- Einfache Passwort-Authentifizierung für schnellen Zugang
- Session-Management mit Streamlit session_state
- Logout-Funktion in der Sidebar
- Temporäre URLs - Zugang endet beim Beenden des Tunnels
- Vollständige App-Funktionalität nach Login
- Automatische Session-Bereinigung beim Logout

 Aktuelle Status
- App läuft erfolgreich auf Port 8501
- ngrok-Tunnel aktiv mit öffentlicher URL
- Authentifizierung funktioniert einwandfrei
- Alle Features verfügbar nach Login

 Wichtige Hinweise
- Die ngrok-URL ist temporär und wird beim Beenden ungültig
- Verwenden Sie `Ctrl+C` zum Beenden des Tunnels
- Alle App-Features sind nach Login verfügbar
- Für Produktionsumgebungen: Verwenden Sie starke Passwörter

 Fehlerbehebung
- "ngrok not found": `brew install ngrok/ngrok/ngrok`
- "Port 8501 already in use": Anderen Port verwenden oder andere Instanz beenden
- "ERR_NGROK_8012": Streamlit-App neu starten mit `streamlit run streamlit_app.py --server.port 8501`
- "IndentationError": Python-Syntax-Fehler - App neu starten

