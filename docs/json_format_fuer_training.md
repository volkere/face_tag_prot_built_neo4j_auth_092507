 JSON-Format für Trainingsdaten

 Übersicht

Das JSON-Format für das Training der Face Tagging Metadata Recognizer App besteht aus einem Array von Objekten, wobei jedes Objekt ein Bild mit seinen Metadaten und erkannten Personen repräsentiert.

 Grundstruktur

```json
[
  {
    "image": "dateiname.jpg",
    "metadata": { ... },
    "persons": [ ... ],
    "location": { ... }
  }
]
```

 Vollständiges Beispiel

```json
[
  {
    "image": "beispiel_foto_1.jpg",
    "metadata": {
      "camera_make": "Canon",
      "camera_model": "EOS R5",
      "lens": "RF 24-70mm f/2.8L IS USM",
      "datetime": "2024-01-15T14:30:00",
      "focal_length": 50,
      "f_number": 2.8,
      "iso": 100,
      "exposure_time": 125,
      "image_width": 8192,
      "image_height": 5464,
      "gps": {
        "lat": 52.520008,
        "lon": 13.404954,
        "altitude": 34.5,
        "timestamp": "2024-01-15 14:30:00"
      }
    },
    "persons": [
      {
        "bbox": [100, 150, 300, 450],
        "prob": 0.95,
        "name": "Max Mustermann",
        "similarity": 0.87,
        "age": 30,
        "gender": "male",
        "quality_score": 0.85,
        "emotion": "happy",
        "eye_status": "open",
        "mouth_status": "open"
      }
    ],
    "location": {
      "full_address": "Unter den Linden 1, 10117 Berlin, Deutschland",
      "country": "Deutschland",
      "state": "Berlin",
      "city": "Berlin"
    }
  }
]
```

 Erforderliche Felder

 Hauptebene

- image (string): Dateiname des Bildes
- metadata (object): Kamerametadaten
- persons (array): Liste der erkannten Personen

 Metadaten (metadata)

- camera_make (string): Kamerahersteller
- camera_model (string): Kameramodell
- datetime (string): Aufnahmedatum/-zeit im ISO-Format (YYYY-MM-DDTHH:MM:SS)
- focal_length (number): Brennweite in mm
- f_number (number): Blende (z.B. 2.8)
- iso (number): ISO-Wert
- gps (object): GPS-Koordinaten

 GPS-Objekt (gps)

- lat (number): Breitengrad (Dezimalformat)
- lon (number): Längengrad (Dezimalformat)
- altitude (number): Höhe über Meeresspiegel in Metern
- timestamp (string): Zeitstempel der GPS-Daten

 Personen (persons)

- bbox (array): Bounding Box als [x, y, width, height]
- age (number): Geschätztes Alter
- gender (string): "male", "female", "unknown"
- quality_score (number): Qualitätsbewertung zwischen 0 und 1

 Optionale Felder

 Personen (persons)

- name (string): Name der Person (kann null sein)
- prob (number): Erkennungswahrscheinlichkeit (0-1)
- similarity (number): Ähnlichkeitswert (0-1)
- emotion (string): Emotion ("happy", "sad", "neutral", "angry", "surprised", "fearful", "disgusted")
- eye_status (string): Augenstatus ("open", "closed", "partially_open")
- mouth_status (string): Mundstatus ("open", "closed", "smiling")

 Metadaten (metadata)

- lens (string): Objektivmodell
- exposure_time (number): Verschlusszeit in Sekunden
- image_width (number): Bildbreite in Pixeln
- image_height (number): Bildhöhe in Pixeln

 Standort (location)

- full_address (string): Vollständige Adresse
- country (string): Land
- state (string): Bundesland/Staat
- city (string): Stadt

 Validierung

Das System validiert automatisch:

- Vorhandensein aller erforderlichen Felder
- Korrekte Datentypen
- Mindestens eine Person pro Bild
- Gültige Bounding Box-Koordinaten (positive Werte)
- Qualitätsscores zwischen 0 und 1
- Gültige GPS-Koordinaten (lat: -90 bis 90, lon: -180 bis 180)

 Verwendung

 Einzelne JSON-Datei

```bash
python train_enhanced_model.py --input training_data.json --output models/my_model.pkl
```

 Verzeichnis mit mehreren JSON-Dateien

```bash
python train_enhanced_model.py --input training_data/ --output models/my_model.pkl
```

 Streamlit UI

1. Gehen Sie zur "Train" Seite
2. Wählen Sie "JSON-Dateien hochladen"
3. Laden Sie eine oder mehrere JSON-Dateien hoch
4. Starten Sie das Training

 Tipps für bessere Ergebnisse

1. Konsistente Namenskonventionen für Personen verwenden
2. Qualitätsscores zwischen 0 und 1 halten
3. GPS-Koordinaten im Dezimalformat verwenden (nicht Grad/Minuten/Sekunden)
4. Datumsformat als ISO 8601 (YYYY-MM-DDTHH:MM:SS)
5. Mindestens 50-100 Trainingsbeispiele für gute Ergebnisse
6. Vielfältige Metadaten für bessere Generalisierung
7. Ausgewogene Alters- und Geschlechtsverteilung in den Trainingsdaten

 Beispiel für minimale Trainingsdaten

```json
[
  {
    "image": "person1.jpg",
    "metadata": {
      "camera_make": "iPhone",
      "camera_model": "iPhone 15 Pro",
      "datetime": "2024-01-15T14:30:00",
      "focal_length": 35,
      "f_number": 1.8,
      "iso": 100,
      "gps": {
        "lat": 52.520008,
        "lon": 13.404954,
        "altitude": 34.5,
        "timestamp": "2024-01-15 14:30:00"
      }
    },
    "persons": [
      {
        "bbox": [100, 150, 200, 300],
        "age": 25,
        "gender": "female",
        "quality_score": 0.8
      }
    ]
  }
]
```

 Fehlerbehandlung

Häufige Fehler und deren Behebung:

- "Ungültiges Format": Überprüfen Sie, ob alle erforderlichen Felder vorhanden sind
- "Bounding Box ungültig": Stellen Sie sicher, dass bbox positive Werte enthält
- "GPS-Koordinaten ungültig": Überprüfen Sie lat/lon Werte (lat: -90 bis 90, lon: -180 bis 180)
- "Keine Personen gefunden": Jedes Bild muss mindestens eine Person enthalten

 Metadaten-Gewichtungen

Das Training unterstützt verschiedene Gewichtungen für Metadaten:

- age_weight: Gewichtung für Alters-Erkennung (Standard: 0.3)
- gender_weight: Gewichtung für Geschlechts-Erkennung (Standard: 0.25)
- location_weight: Gewichtung für Standort-Metadaten (Standard: 0.2)
- temporal_weight: Gewichtung für zeitliche Metadaten (Standard: 0.15)
- technical_weight: Gewichtung für technische Metadaten (Standard: 0.1)

Diese Gewichtungen können über die Streamlit UI oder die Kommandozeile angepasst werden.
