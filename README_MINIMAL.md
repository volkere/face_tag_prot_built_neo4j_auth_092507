# Zeitkalkül Metadata Recognizer - Minimal Version

## Leichtgewichtige Version ohne Neo4j

Diese Branch enthält eine minimalisierte Version der App ohne Neo4j-Graphdatenbank-Integration.

### Entfernte Features

- **Neo4j-Integration**: Keine Graph-Datenbank-Abhängigkeiten
- **Neo4j Browser**: Keine interaktive Graph-Visualisierung
- **Komplexe Abfragen**: Vereinfachte Datenanalyse ohne Graph-Features

### Verfügbare Features

- **Enroll**: Erstellen von Gesichts-Embeddings
- **Annotate**: Foto-Analyse mit Metadaten
- **Analyze**: Basis-Statistiken und Visualisierungen
- **Train**: KI-Training mit Metadaten
- **Authentifizierung**: Passwort-basierte Sicherheit
- **Internet-Zugang**: ngrok-Integration

### Installation

#### Windows
```cmd
install_windows.bat
```

#### macOS/Linux
```bash
pip install -r requirements.txt
```

### Verwendung

#### Windows
```cmd
start_app.bat
```

#### macOS/Linux
```bash
streamlit run streamlit_app.py
```

### Vorteile

- **Geringere Abhängigkeiten**: Weniger Pakete zu installieren
- **Schnellerer Start**: Keine Neo4j-Datenbank-Initialisierung
- **Einfachere Wartung**: Weniger Komponenten
- **Bessere Performance**: Fokus auf Kern-Features

### Systemanforderungen

- Python 3.9+
- Mindestens 2GB RAM (reduziert von 4GB)
- Standard Python-Pakete ohne Graph-Datenbanken

### Dokumentation

Siehe Haupt-README.md für detaillierte Anweisungen zu den verfügbaren Features.
