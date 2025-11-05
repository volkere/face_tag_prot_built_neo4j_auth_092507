Enrollment-Funktion mit EXIF-Metadaten-Integration

Übersicht

Die Enrollment-Funktion wurde erweitert, um optionale EXIF-Metadaten-Extraktion zu ermöglichen. Dies verbessert die Trainingsqualität und ermöglicht dem Enhanced Face Engine, Metadaten-basierte Modelle zu erstellen.

Wichtig: Wenn EXIF-Metadaten aktiviert sind, werden ALLE Bilder verarbeitet - auch solche ohne erkannte Gesichter. Dies ermöglicht das Speichern von reinen Metadaten-Informationen.

Neue Features

EXIF-Metadaten-Extraktion:
- Checkbox in der Sidebar zum Aktivieren der EXIF-Extraktion
- Kamera-Daten (Modell, Hersteller, Objektiv)
- GPS-Koordinaten mit Höhenangabe
- Aufnahme-Einstellungen (ISO, Blende, Brennweite)
- Zeitstempel und Datum
- Zusätzliche Bild-Metadaten

Verarbeitung ohne Gesichter:
- Bilder ohne erkannte Gesichter werden mit Dummy-Embeddings verarbeitet
- Nur wenn EXIF-Metadaten aktiviert sind
- Ermöglicht Metadaten-basierte Trainings ohne Gesichtsbilder
- Dummy-Embeddings sind Null-Vektoren (512 Dimensionen)

Integration:
- Gesichtsattribute werden mit EXIF-Daten kombiniert
- Metadaten werden in embeddings.pkl gespeichert
- Rückwärtskompatibel mit alten Embedding-Dateien

Nutzung

Schritt 1: Aktivieren der EXIF-Extraktion
1. Öffnen Sie die Enroll-Seite
2. Klicken Sie auf "EXIF-Metadaten extrahieren" in der Sidebar
3. Die Checkbox ist standardmäßig deaktiviert

Schritt 2: Bilder hochladen

ZIP-Upload:
- Laden Sie eine ZIP-Datei mit Person-Ordnern hoch
- Struktur: PersonA/*.jpg, PersonB/*.png, etc.
- EXIF-Daten werden automatisch für jedes Bild extrahiert
- Bilder ohne Gesichter werden mit Dummy-Embeddings verarbeitet

Manueller Upload:
- Geben Sie den Namen der Person ein
- Laden Sie einzelne Bilder hoch
- EXIF-Daten werden bei aktivierter Option erfasst
- Bilder ohne Gesichter werden mit Dummy-Embeddings verarbeitet

Schritt 3: Download
- Download "embeddings.pkl" enthält:
  - Gesichts-Embeddings für jede Person (oder Dummy-Embeddings)
  - Vollständige EXIF-Metadaten (wenn aktiviert)
  - Gesichtsattribute (Alter, Geschlecht, Qualität, etc.) wenn vorhanden
  - Statistiken: Anzahl Bilder mit/ohne Gesichter

Metadaten-Struktur

Gespeicherte Metadaten pro Bild MIT Gesicht:
```json
{
  "exif": {
    "datetime": "2024-01-15T14:30:00",
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "lens": "RF 24-70mm f/2.8L",
    "focal_length": 50,
    "f_number": 2.8,
    "iso": 400,
    "exposure_time": "1/125",
    "gps": {
      "lat": 52.5200,
      "lon": 13.4050,
      "altitude": 34.5
    },
    "image_width": 3840,
    "image_height": 2160
  },
  "age": 35,
  "gender": "male",
  "quality_score": 0.85,
  "emotion": "happy",
  "eye_status": "open",
  "mouth_status": "closed",
  "source_image": "personA_001.jpg"
}
```

Metadaten-Struktur OHNE Gesicht (Dummy-Embedding):
```json
{
  "exif": {
    "datetime": "2024-01-15T14:30:00",
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "lens": "RF 24-70mm f/2.8L",
    "focal_length": 50,
    "f_number": 2.8,
    "iso": 400,
    "exposure_time": "1/125",
    "gps": {
      "lat": 52.5200,
      "lon": 13.4050,
      "altitude": 34.5
    },
    "image_width": 3840,
    "image_height": 2160
  },
  "source_image": "landscape_001.jpg"
}
```

Dummy-Embeddings:
- Null-Vektor mit 512 Dimensionen: [0, 0, 0, ..., 0]
- Werden nur gespeichert wenn EXIF-Metadaten vorhanden
- Ermöglichen Metadaten-basierte Analysen ohne Gesichtsbilder

Vorteile für Training

Verbesserte Erkennung:
- Standort-basierte Bias-Korrektur
- Zeit-basierte Vorhersagen
- Kamera-Modell-spezifische Anpassungen
- Technische Metadaten für Qualitätsbewertung

Erweiterte Modell-Features:
- Demografische Metadaten (Alter, Geschlecht)
- Standort-Metadaten (GPS, Höhe)
- Zeitliche Metadaten (Datum, Zeit)
- Technische Metadaten (Kamera, Einstellungen)

Rückwärtskompatibilität

Alte Embedding-Dateien:
- werden weiterhin unterstützt
- können ohne Metadaten geladen werden
- Neue Dateien mit Metadaten funktionieren ebenfalls

Implementierung

Dateien:
- pages/0_Enroll.py: EXIF-Extraktion-UI
- app/location.py: EXIF-Extraktions-Funktionen
- app/face_recognizer.py: GalleryDB mit Metadaten-Support

Technische Details:
- Verwendet extract_comprehensive_metadata() aus app/location.py
- Temporäre Dateien für manuelles Upload
- Fehlerbehandlung für fehlende EXIF-Daten
- Effiziente Metadaten-Struktur

Performance

Ohne EXIF-Extraktion:
- Gleiche Performance wie zuvor
- Keine zusätzliche Verarbeitungszeit

Mit EXIF-Extraktion:
- Minimaler Overhead (<100ms pro Bild)
- Abhängig von Bildgröße und EXIF-Datenmenge
- Parallel-Prozessierung möglich

Best Practices

Datenqualität:
- Verwenden Sie qualitativ hochwertige Fotos
- Sorgen Sie für konsistente Kamera-Einstellungen
- Erfassen Sie ausreichend Bilder pro Person

Metadaten-Konsistenz:
- Verwenden Sie dieselbe Kamera wenn möglich
- Externe GPS-Empfänger für bessere Genauigkeit
- Synchronisieren Sie Kamera-Uhren

Fehlerbehebung

Keine EXIF-Daten:
- Prüfen Sie, ob die Checkbox aktiviert ist
- Überprüfen Sie, ob Bilder EXIF-Daten enthalten
- Bei PNG-Bildern: Manche Formate unterstützen keine EXIF

Extraktions-Fehler:
- Fehler werden stillschweigend behandelt
- Das System funktioniert auch ohne EXIF-Daten
- Gesichts-Embeddings werden trotzdem erstellt

Zukunftige Erweiterungen

Geplante Features:
- Automatische Reverse-Geocoding für GPS
- Kamera-Profil-Erkennung
- Zeit-Serien-Analyse
- Gruppen-Statistiken

Integration:
- Enhanced Face Engine mit Metadaten-Training
- Neo4j-Import mit Metadaten
- Erweiterte Analytics-Tools

