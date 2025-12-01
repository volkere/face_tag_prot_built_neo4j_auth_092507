Face Tagging Metadata Recognizer - Codebase Übersicht

Zweck des Projekts

Ein intelligentes System zur Gesichtserkennung und Metadaten-Analyse von Fotos mit:
- Automatischer Gesichtserkennung und Embedding-Erstellung
- EXIF-Metadaten-Extraktion (Kamera, GPS, Datum/Zeit)
- Metadaten-basiertes KI-Training für verbesserte Erkennung
- Neo4j Graph-Datenbank-Integration für komplexe Abfragen
- Streamlit Multi-Page UI mit Authentifizierung
- CLI für Batch-Verarbeitung

Kern-Architektur

Drei-Schichten-System:
1. Frontend: Streamlit UI (streamlit_app.py + pages/)
2. Backend: Python Engine (app/)
3. Datenbank: Neo4j für Graph-Daten + Embeddings-Dateien

Haupt-Komponenten

1. FaceEngine (app/face_recognizer.py)
- Basis-Gesichtserkennung mit InsightFace (buffalo_l)
- Gesichts-Detection, Embeddings, Landmarks
- Alters- und Geschlechtserkennung
- Qualitätsbewertung, Emotion-Erkennung
- Augen- und Mundstatus-Erkennung
- Pose-Schätzung (Yaw, Pitch, Roll)

2. EnhancedFaceEngine (app/enhanced_face_engine.py)
- Erweiterte Gesichtserkennung mit Metadaten-Integration
- Trainiert Metadaten-basierte Modelle für bessere Vorhersagen
- Bias-Korrektur für Standort, Zeit, Kamera
- Integration mit RandomForest-Klassifikatoren
- Vorhersage-Enhancement durch Kontext-Informationen

3. Metadata Management
- app/location.py: EXIF-GPS, Reverse-Geocoding, umfassende Metadaten
- app/utils.py: Qualitätsbewertung, Cosine-Similarity, Datum-Parsing
- Extract-Images: Vollständige Kamera-Info, Aufnahme-Einstellungen

4. Streamlit UI (streamlit_app.py + pages/)

Login-System:
- Einfache Passwort-Authentifizierung
- Session-Management mit Cookies
- Rollen: admin, user

Seite 0 - Enroll (pages/0_Enroll.py):
- Erstellt Embeddings für Personen-Erkennung
- Unterstützt ZIP-Upload oder manuellen Upload
- Speichert embeddings.pkl für spätere Verwendung
- Gallery-Datenbank für bekannte Gesichter

Seite 1 - Annotate (pages/1_Annotate.py):
- Hauptanalyse-Seite für Foto-Verarbeitung
- Upload von Fotos einzeln oder per ZIP
- Optional: Enhanced Model Upload
- Extrahiert Gesichter, Metadaten, EXIF-Daten
- Bounding Boxes mit erweiterten Attributen
- Interaktiver Editor für Annotationen
- Farbige Metadaten-Darstellung
- JSON-Export der Ergebnisse
- Qualitätsfilter und Visualisierungen

Seite 2 - Analyze (pages/2_Analyze.py):
- Statistiken und Visualisierungen
- Chart-basierte Analysen mit Plotly
- Gruppierung nach Standort, Zeit, Qualität
- Emotions- und Demografie-Statistiken
- Interaktive Karten mit GPS-Daten
- Export-Funktionalität

Seite 3 - Train (pages/3_Train.py):
- KI-Training mit Metadaten-Integration
- Upload von JSON-Trainingsdaten
- Trainingsdaten-Generator aus Musterfotos
- Hyperparameter-Tuning-UI
- Modell-Vergleich und Analytics
- Training-Historie und Metriken
- Export trainierter Modelle

Seite 4 - Neo4j (pages/4_Neo4j.py):
- Import von JSON-Daten in Neo4j
- Graph-Datenbank-Verwaltung
- Abfrage-Interface mit Cypher
- Performance-Metriken

Seite 5 - Neo4j Browser (pages/5_Neo4j_Browser.py):
- Interaktive Graph-Visualisierung
- Verschiedene Layout-Typen
- Anpassbare Darstellung
- Abfrage-Historie

5. CLI (app/main.py)
- Zwei Haupt-Kommandos: enroll, annotate
- Batch-Verarbeitung von Ordnern
- Recursive Folder-Scanning
- Reverse-Geocoding-Option
- JSON-Output für Ergebnisse

6. Neo4j Integration (app/neo4j_connector.py)
- Graph-Datenbank-Connection-Manager
- Import von JSON-Daten in Neo4j
- Cypher-Abfrage-Generator
- Relationship-Management
- Daten-Migration und -Validierung

Datenmodell (Neo4j)

Knoten (Nodes):
- Image: Bild-Metadaten (Kamera, Einstellungen, Datum)
- Face: Gesichts-Eigenschaften (Alter, Geschlecht, Emotion, Qualität)
- Person: Identifizierte Person
- Location: Geografischer Standort

Beziehungen (Relationships):
- (Face)-[APPEARS_IN]->(Image)
- (Face)-[BELONGS_TO]->(Person)
- (Image)-[TAKEN_AT]->(Location)

Trainings-System

Enhanced Model Training:
- Metadaten-Encoder für verschiedene Feature-Typen
- RandomForest-Klassifikatoren für Alter, Geschlecht, Qualität
- Bias-Detection und -Korrektur
- Validierung mit Train/Test-Split
- Metriken: Accuracy, MAE, F1-Score

Trainingsdaten-Format:
- JSON mit image, metadata, persons
- Vollständige EXIF-Daten
- Qualitätsbewertungen
- Bounding Boxes
- Verschiedene Attribute

Expected Improvements:
- Alterserkennung: +15-25%
- Geschlechtserkennung: +10-20%
- Standort-basierte Vorhersagen: +20-30%

Technologie-Stack

Core Libraries:
- Streamlit >=1.36.0: Web UI Framework
- InsightFace >=0.7.3: Gesichtserkennung (buffalo_l)
- OpenCV >=4.9.0: Bildverarbeitung
- ONNX Runtime >=1.18.0: Deep Learning Inference
- Pillow >=10.3.0: Bild-I/O und EXIF
- Piexif >=1.1.3: EXIF-Parsing

Machine Learning:
- scikit-learn >=1.4.2: Klassifikatoren, Skalierung
- NumPy >=1.26.4: Numerische Operationen
- Joblib >=1.3.0: Modell-Serialisierung

Visualisierung:
- Plotly >=5.15.0: Interaktive Charts
- Pandas >=2.0.0: Datenmanipulation
- NetworkX >=3.0: Graph-Analysen

Datenbank:
- Neo4j >=5.0.0: Graph-Datenbank

Geolokalisierung:
- Geopy >=2.4.1: Reverse-Geocoding

Utilities:
- TQDM >=4.66.4: Progress Bars

Dateistruktur

face_tag_prot_built_neo4j_auth_092507/
├── app/                          Python-Paket (Backend)
│   ├── __init__.py
│   ├── enhanced_face_engine.py   Erweiterte Gesichtserkennung
│   ├── face_recognizer.py        Basis-Gesichtserkennung
│   ├── location.py               Metadaten-Extraktion
│   ├── main.py                   CLI-Interface
│   ├── neo4j_connector.py        Neo4j-Integration
│   └── utils.py                  Hilfsfunktionen
├── pages/                         Streamlit-Seiten
│   ├── 0_Enroll.py               Embeddings erstellen
│   ├── 1_Annotate.py             Foto-Analyse
│   ├── 2_Analyze.py              Statistiken
│   ├── 3_Train.py                KI-Training
│   ├── 4_Neo4j.py                Neo4j-Import
│   └── 5_Neo4j_Browser.py        Graph-Visualisierung
├── docs/                          Dokumentation
│   ├── ARCHITECTURE.md           Technische Architektur
│   ├── BRANCH_OVERVIEW.md        Git-Branch-Übersicht
│   ├── INSTALL.md                Installations-Anleitung
│   ├── NEO4J_MODEL.md            Neo4j-Datenmodell
│   ├── PRIVACY.md                Datenschutz
│   ├── TRAINING.md               Training-Details
│   ├── USAGE_CLI.md              CLI-Nutzung
│   ├── USAGE_UI.md               UI-Nutzung
│   ├── json_format_fuer_training.md
│   ├── train_funktion_erklaerung.md
│   ├── embeddings_verwendung.md
│   └── enhanced_model_erklaerung.md
├── models/                        Trainierte Modelle
│   ├── enhanced_model_*.pkl      Enhanced Models
│   └── embeddings.pkl            Personen-Embeddings
├── streamlit_app.py               Haupt-Streamlit-App
├── train_enhanced_model.py        Training-Skript
├── create_hashes.py               Password-Hashing
├── generate_password_hash.py      Passwort-Generator
├── config.yaml                    Auth-Konfiguration (alt)
├── requirements.txt               Python-Dependencies
├── pyproject.toml                 Paket-Metadaten
└── README.md                      Projekt-README

Workflow

Typischer Workflow:

1. Einrichtung:
   - pip install -r requirements.txt
   - Neo4j starten (optional)
   - streamlit run streamlit_app.py

2. Enroll (Erstmalig):
   - Personenfotos hochladen
   - Embeddings erstellen
   - embeddings.pkl herunterladen

3. Annotate (Hauptfunktion):
   - Fotos hochladen
   - Optional: embeddings.pkl für Personen-Erkennung
   - Optional: Enhanced Model für bessere Ergebnisse
   - Gesichter und Metadaten analysieren
   - JSON-Export

4. Train (Optional):
   - Trainingsdaten (JSON) vorbereiten
   - Enhanced Model trainieren
   - Modell exportieren und in Annotate verwenden

5. Analyze:
   - Hochgeladene JSON-Daten visualisieren
   - Statistiken erstellen
   - Charts und Karten anzeigen

6. Neo4j (Optional):
   - JSON-Daten in Neo4j importieren
   - Graph-Visualisierung
   - Cypher-Abfragen ausführen

CLI Workflow:

1. Enroll:
   python -m app.main enroll --gallery ./gallery --db embeddings.pkl

2. Annotate:
   python -m app.main annotate --input ./photos --out output.json

3. Training:
   python train_enhanced_model.py --input training.json --output model.pkl

Features und Funktionen

Gesichtserkennung:
- Detection mit Bounding Boxes
- Embedding-Erstellung für Similarity-Search
- Alterserkennung (approximativ)
- Geschlechtserkennung
- Qualitätsbewertung (0-1)
- Emotion-Erkennung (happy, neutral, etc.)
- Augen- und Mundstatus
- Pose-Schätzung

Metadaten-Extraktion:
- EXIF GPS-Koordinaten
- Reverse-Geocoding zu Adressen
- Kamera-Modell und -Hersteller
- Objektiv-Information
- Aufnahme-Einstellungen (ISO, Blende, Brennweite)
- Zeitstempel-Parsing
- Bildgröße und -format

Metadaten-basiertes Training:
- Encoder für Demografie, Standort, Zeit, Technik
- RandomForest-Klassifikatoren
- Bias-Erkennung und -Korrektur
- Validierung und Metriken
- Hyperparameter-Tuning

Visualisierung:
- Interaktive Plotly-Charts
- GPS-Karten mit Standorten
- Statistiken und Verteilungen
- Graph-Visualisierung (Neo4j)

Export/Import:
- JSON-Export aller Analysen
- Neo4j-Import für Graph-DB
- Embeddings-Speicherung (.pkl)
- Modell-Export (.pkl)

Authentifizierung:
- Passwort-basiertes Login
- Session-Management
- Rollen: admin, user
- Secure Cookies

Internet-Zugang:
- ngrok-Integration
- Temporäre öffentliche URLs
- Autmatische Tunnel-Verwaltung

Sicherheit und Datenschutz

- Einfache Passwort-Authentifizierung
- Session-Management
- Neo4j-Connection-Sicherheit
- Datenschutz-Hinweise in docs/PRIVACY.md
- Verantwortungsvolle Nutzung

Wichtige Hinweise:
- Gesichtserkennung kann voreingenommen sein
- Rechtliche Compliance erforderlich
- Lokale Gesetze beachten
- Einwilligung für Bildverarbeitung

Nächste Schritte für Entwicklung

Potential Areas:
1. Erweiterte Gesichtserkennung (Masken, Verkleidungen)
2. Realtime-Video-Analyse
3. Multi-Face-Tracking über Sequenzen
4. Cloud-Deployment (Docker, Kubernetes)
5. Mobile-App für Foto-Upload
6. API-Endpoints für externe Integration
7. Erweiterte BI-Analytics
8. Continuous Learning mit Feedback-Loop
9. A/B-Testing für Modelle
10. Erweiterte Sicherheit (2FA, OAuth)

Test-Coverage:
- Unit-Tests für Core-Funktionen
- Integration-Tests für UI
- Performance-Tests für Batch-Verarbeitung

Documentation:
- API-Dokumentation
- Code-Beispiele
- Video-Tutorials
- Best Practices Guide

Monitoring:
- Logging-Integration
- Performance-Metriken
- Error-Tracking
- Usage-Analytics

Hinweise für Entwickler

Codebase-Navigation:
- Core-Logic: app/face_recognizer.py, app/enhanced_face_engine.py
- UI: streamlit_app.py, pages/
- Database: app/neo4j_connector.py
- CLI: app/main.py

Wichtige Funktionen:
- FaceEngine.analyze(): Basis-Gesichtserkennung
- EnhancedFaceEngine.predict_with_metadata(): Erweiterte Vorhersage
- extract_comprehensive_metadata(): Metadaten-Extraktion
- GalleryDB.match(): Ähnlichkeits-Suche

Testen:
- CLI: python -m app.main annotate --input test.jpg --out test.json
- UI: streamlit run streamlit_app.py
- Training: python train_enhanced_model.py --input data.json

Debugging:
- Logs in Streamlit-Console
- JSON-Output für manuelle Inspektion
- Neo4j-Browser für Graph-Debugging

Performance:
- Batch-Processing für große Mengen
- Parallelisierung bei Neo4j-Import
- Caching für Embeddings

Wartung:
- Requirements-Updates regelmäßig
- Modelle neu trainieren
- Neo4j-Backups
- Dokumentation aktuell halten



