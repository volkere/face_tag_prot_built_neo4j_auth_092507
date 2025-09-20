# Zeitkalkül Metadata Recognizer - CLI Version

## Kommandozeilen-Interface Version

Diese Branch enthält eine reine CLI-Version der App ohne Streamlit-Web-Interface.

### Verfügbare Features

- **Batch-Verarbeitung**: Verarbeitung großer Bildsammlungen
- **Gesichtserkennung**: Embeddings-Erstellung und Personen-Matching
- **Metadaten-Extraktion**: EXIF-Daten, GPS, Standort-Informationen
- **JSON-Export**: Strukturierte Datenausgabe
- **CLI-Tools**: Kommandozeilen-Interface für alle Funktionen

### Entfernte Features

- **Streamlit-Interface**: Keine Web-UI
- **Interaktive Visualisierungen**: Keine Plotly-Charts
- **Real-time-Analyse**: Batch-Verarbeitung bevorzugt

### Installation

```bash
pip install -r requirements.txt
```

### Verwendung

#### Personen-Datenbank aufbauen
```bash
python -m app.main enroll --gallery ./gallery --db embeddings.pkl
```

#### Fotos analysieren
```bash
python -m app.main annotate --input ./photos --out output.json --recursive --reverse-geocode
```

#### Batch-Verarbeitung
```bash
python -m app.main batch --input ./large_photo_collection --output ./results --workers 4
```

### CLI-Argumente

#### Enroll
- `--gallery`: Pfad zum Galerie-Verzeichnis
- `--db`: Pfad zur Embeddings-Datenbank
- `--recursive`: Rekursives Durchsuchen von Unterverzeichnissen

#### Annotate
- `--input`: Eingabe-Pfad (Datei oder Verzeichnis)
- `--output`: Ausgabe-Pfad für JSON-Datei
- `--recursive`: Rekursives Verarbeiten
- `--reverse-geocode`: GPS-Koordinaten zu Adressen konvertieren
- `--quality-threshold`: Mindest-Qualitätsschwelle

#### Batch
- `--input`: Eingabe-Verzeichnis
- `--output`: Ausgabe-Verzeichnis
- `--workers`: Anzahl paralleler Worker
- `--chunk-size`: Größe der Verarbeitungs-Chunks

### Vorteile

- **Performance**: Optimiert für große Datenmengen
- **Automatisierung**: Ideal für Skripte und Workflows
- **Ressourcenschonend**: Keine Web-UI-Overhead
- **Skalierbar**: Parallele Verarbeitung möglich

### Systemanforderungen

- Python 3.9+
- Mindestens 2GB RAM
- Keine Browser-Abhängigkeiten

### Beispiele

#### Große Sammlung verarbeiten
```bash
python -m app.main batch \
  --input /path/to/photos \
  --output /path/to/results \
  --workers 8 \
  --quality-threshold 0.7
```

#### Spezifische Analyse
```bash
python -m app.main annotate \
  --input single_photo.jpg \
  --output analysis.json \
  --reverse-geocode
```

### Dokumentation

Siehe `docs/USAGE_CLI.md` für detaillierte CLI-Dokumentation.
