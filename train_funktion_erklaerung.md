# Train-Funktion - Vollständige Erklärung

## 1. Überblick und Zweck

Die Train-Funktion ist ein fortschrittliches System zur Verbesserung der Gesichtserkennung durch Integration von Metadaten. Anstatt nur auf Bilddaten zu vertrauen, nutzt sie zusätzliche Informationen wie:

- **Kamerametadaten** (Modell, Einstellungen, GPS)
- **Zeitliche Informationen** (Aufnahmezeit, Jahreszeit)
- **Standortdaten** (GPS-Koordinaten, Land, Stadt)
- **Technische Parameter** (ISO, Blende, Brennweite)

## 2. Hauptkomponenten

### A. Streamlit UI (pages/3_Train.py)

**Datenquellen:**
- **JSON-Dateien hochladen**: Bereits annotierte Trainingsdaten
- **Musterfotos generieren**: Automatische Generierung aus Fotos

**Konfiguration:**
- **Validierungs-Split**: 10-50% der Daten für Validierung
- **Metadaten-Gewichtungen**: Anpassbare Gewichtung verschiedener Metadaten-Typen
- **Modell-Name**: Benutzerdefinierter Name für das trainierte Modell

### B. CLI-Tool (train_enhanced_model.py)

**Kommandozeilen-Interface:**
```bash
python train_enhanced_model.py \
  --input training_data.json \
  --output models/my_model.pkl \
  --validation-split 0.2 \
  --age-weight 0.3 \
  --gender-weight 0.25 \
  --location-weight 0.2 \
  --temporal-weight 0.15 \
  --technical-weight 0.1
```

## 3. Trainingsprozess

### Phase 1: Datenvorbereitung

**JSON-Validierung:**
- Überprüfung der erforderlichen Felder
- Validierung der Datentypen
- Bounding Box-Validierung

**Metadaten-Extraktion:**
- Automatische Extraktion aus Fotos (falls gewählt)
- Umfassende Metadaten-Sammlung
- Normalisierung und Encoding

### Phase 2: Metadaten-Encoding

**Demografische Metadaten:**
- Alter: Normalisiert auf 0-1 Skala
- Geschlecht: One-hot Encoding
- Altersgruppen: Kategorisierung

**Standort-Metadaten:**
- GPS-Koordinaten: Normalisiert (lat/90, lon/180)
- Höhe: Normalisiert auf Mount Everest (8848m)
- Länder: Top 10 Länder One-hot Encoding

**Zeitliche Metadaten:**
- Stunde: Normalisiert (0-24)
- Wochentag: One-hot Encoding (7 Tage)
- Monat: One-hot Encoding (12 Monate)
- Jahreszeit: One-hot Encoding (4 Jahreszeiten)

**Technische Metadaten:**
- Bildqualität: 0-1 Skala
- Kamera-Modelle: Top 8 Hersteller
- Brennweite: Normalisiert auf 200mm
- ISO: Normalisiert auf 6400
- Blende: Normalisiert auf f/22

### Phase 3: Modell-Training

**Drei separate Modelle:**
1. **Alters-Modell**: RandomForest für Altersvorhersage
2. **Geschlechts-Modell**: RandomForest für Geschlechtsklassifikation
3. **Qualitäts-Modell**: RandomForest für Qualitätsbewertung

**Training-Algorithmus:**
```python
def train_with_metadata(self, training_data):
    # Metadaten extrahieren
    X_metadata = []
    y_age = []
    y_gender = []
    y_quality = []
    
    for item in training_data:
        metadata_features = self.metadata_encoder.encode_all_metadata(metadata)
        X_metadata.append(metadata_features)
        
        # Labels extrahieren
        for person in persons:
            y_age.append(person['age'])
            y_gender.append(person['gender'])
            y_quality.append(person['quality_score'])
    
    # Modelle trainieren
    self.age_model.fit(X_metadata, y_age)
    self.gender_model.fit(X_metadata, y_gender)
    self.quality_model.fit(X_metadata, y_quality)
```

### Phase 4: Bias-Korrektur

**Standort-Alter-Bias:**
- Durchschnittsalter pro Land
- Geografische Korrekturen

**Zeit-Geschlecht-Bias:**
- Geschlechtsverteilung pro Stunde
- Tageszeit-basierte Korrekturen

**Technische-Qualität-Bias:**
- Qualitätskorrelation mit Kamera-Einstellungen
- Hardware-spezifische Anpassungen

## 4. Vorhersage-Enhancement

**Metadaten-Integration:**
```python
def _enhance_with_metadata(base_prediction, metadata, metadata_features):
    enhanced = base_prediction.copy()
    
    # Alters-Korrektur
    if self.age_model is not None:
        predicted_age = self.age_model.predict([metadata_features])[0]
        enhanced['age'] = int(0.7 * base_age + 0.3 * predicted_age)
    
    # Geschlechts-Korrektur
    if self.gender_model is not None:
        predicted_gender = self.gender_model.predict([metadata_features])[0]
        if confidence > 0.8:
            enhanced['gender'] = predicted_gender
    
    # Standort-basierte Korrektur
    if location in self.location_age_bias:
        enhanced['age'] = int(0.9 * enhanced['age'] + 0.1 * location_bias)
    
    return enhanced
```

## 5. Erwartete Verbesserungen

| Metrik | Verbesserung | Begründung |
|--------|-------------|------------|
| **Alterserkennung** | +15-25% | Standort- und zeitbasierte Korrekturen |
| **Geschlechtserkennung** | +10-20% | Tageszeit- und Kontext-Integration |
| **Standort-Vorhersagen** | +20-30% | Geografische Bias-Erkennung |

## 6. Workflow

1. **Daten hochladen** (JSON oder Fotos)
2. **Metadaten extrahieren** und validieren
3. **Trainingsdaten analysieren** (Statistiken, Verteilungen)
4. **Modelle trainieren** mit Metadaten-Integration
5. **Validierung** mit Testdaten
6. **Modell speichern** und herunterladen
7. **Integration** in die Annotate-Seite

## 7. Besondere Features

**Intelligente Korrekturen:**
- Metadaten-Bias-Erkennung
- Gewichtete Vorhersage-Kombination
- Kontinuierliches Lernen

**Visualisierung:**
- Kamera-Modelle Verteilung
- Altersverteilung
- Geschlechtsverteilung
- Standort-Verteilung

**Flexibilität:**
- Anpassbare Metadaten-Gewichtungen
- Verschiedene Datenquellen
- CLI und UI Interface

## 8. Detaillierte Funktionsweise

### A. Datenanalyse-Funktionen

**analyze_training_data():**
```python
def analyze_training_data(training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analysiert Trainingsdaten und extrahiert Statistiken
    
    Args:
        training_data: Liste von Trainingsdaten-Einträgen
        
    Returns:
        Dictionary mit Statistiken
    """
    stats = {
        'camera_models': {},
        'lenses': {},
        'iso_values': [],
        'aperture_values': [],
        'shutter_speeds': [],
        'focal_lengths': [],
        'emotions': {},
        'genders': {},
        'age_groups': {},
        'quality_scores': [],
        'locations': {}
    }
    
    # Metadaten analysieren
    for item in training_data:
        metadata = item.get('metadata', {})
        
        # Kamera-Modell
        if 'camera_model' in metadata:
            model = metadata['camera_model']
            stats['camera_models'][model] = stats['camera_models'].get(model, 0) + 1
        
        # Gesichts-Analyse
        persons = item.get('persons', [])
        for person in persons:
            # Emotion
            if 'emotion' in person:
                emotion = person['emotion']
                stats['emotions'][emotion] = stats['emotions'].get(emotion, 0) + 1
            
            # Geschlecht
            if 'gender' in person:
                gender = person['gender']
                stats['genders'][gender] = stats['genders'].get(gender, 0) + 1
            
            # Alter (in Gruppen)
            if 'age' in person:
                age = person['age']
                if age < 18:
                    group = '0-17'
                elif age < 30:
                    group = '18-29'
                elif age < 50:
                    group = '30-49'
                elif age < 70:
                    group = '50-69'
                else:
                    group = '70+'
                stats['age_groups'][group] = stats['age_groups'].get(group, 0) + 1
    
    return stats
```

**validate_training_data_format():**
```python
def validate_training_data_format(data):
    """
    Validiert das Format der Trainingsdaten
    
    Args:
        data: Trainingsdaten-Dictionary oder Liste
        
    Returns:
        bool: True wenn Format gültig ist
    """
    if isinstance(data, list):
        for item in data:
            if not validate_training_data_format(item):
                return False
        return True
    
    if not isinstance(data, dict):
        return False
    
    # Erforderliche Felder prüfen
    required_fields = ['image', 'metadata', 'persons']
    for field in required_fields:
        if field not in data:
            return False
    
    # Personen-Liste prüfen
    if not isinstance(data['persons'], list):
        return False
    
    # Mindestens eine Person sollte vorhanden sein
    if len(data['persons']) == 0:
        return False
    
    return True
```

### B. Trainingsdaten-Generierung

**generate_training_data_from_photos():**
```python
def generate_training_data_from_photos(photos, engine):
    """
    Generiert Trainingsdaten aus hochgeladenen Musterfotos
    
    Args:
        photos: Liste von hochgeladenen Foto-Dateien
        engine: FaceEngine für Gesichtserkennung
        
    Returns:
        Liste von Trainingsdaten-Dictionaries
    """
    training_data = []
    
    for photo in photos:
        try:
            # Bild laden
            data = photo.read()
            image = Image.open(io.BytesIO(data)).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Gesichtserkennung
            faces = engine.analyze(img_bgr)
            
            # Metadaten extrahieren
            metadata = extract_comprehensive_metadata(image)
            
            # Trainingsdaten-Eintrag erstellen
            training_entry = {
                "image": photo.name,
                "metadata": metadata,
                "persons": []
            }
            
            # Gesichter zu Trainingsdaten hinzufügen
            for face in faces:
                person_data = {
                    "age": face.get('age', 25),  # Standard-Alter falls nicht erkannt
                    "gender": face.get('gender', 'unknown'),
                    "quality_score": face.get('quality_score', 0.5),
                    "bbox": face.get('bbox', [0, 0, 100, 100]),
                    "emotion": face.get('emotion', 'neutral'),
                    "pose": face.get('pose', {})
                }
                training_entry["persons"].append(person_data)
            
            training_data.append(training_entry)
            
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten von {photo.name}: {e}")
    
    return training_data
```

### C. Trainings-Ergebnisse

**display_training_results():**
```python
def display_training_results(results: Dict[str, Any]):
    """Zeigt Trainings-Ergebnisse an"""
    st.subheader("Trainings-Ergebnisse")
    
    # Metriken
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'training' in results and 'age_accuracy' in results['training']:
            st.metric("Alter-Genauigkeit", f"{results['training']['age_accuracy']:.3f}")
    
    with col2:
        if 'training' in results and 'gender_accuracy' in results['training']:
            st.metric("Geschlecht-Genauigkeit", f"{results['training']['gender_accuracy']:.3f}")
    
    with col3:
        if 'training' in results and 'quality_accuracy' in results['training']:
            st.metric("Qualität-Genauigkeit", f"{results['training']['quality_accuracy']:.3f}")
    
    # Detaillierte Ergebnisse
    with st.expander("Detaillierte Ergebnisse", expanded=False):
        if 'training' in results:
            st.write("**Training-Metriken:**")
            for metric, value in results['training'].items():
                st.write(f"- {metric}: {value:.3f}")
        
        if 'validation' in results:
            st.write("**Validierungs-Metriken:**")
            for metric, value in results['validation'].items():
                st.write(f"- {metric}: {value:.3f}")
        
        if 'improvement' in results:
            st.write("**Verbesserungen:**")
            for metric, improvement in results['improvement'].items():
                st.write(f"- {metric}: {improvement:+.3f}")
```

## 9. CLI-Funktionen

### A. Hauptfunktion

```python
def main():
    parser = argparse.ArgumentParser(
        description="Trainieren Sie die erweiterte Gesichtserkennung mit Metadaten"
    )
    
    parser.add_argument("--input", "-i", required=True,
                       help="Pfad zu JSON-Dateien mit Trainingsdaten")
    parser.add_argument("--output", "-o", default="models/enhanced_model.pkl",
                       help="Ausgabe-Pfad für das trainierte Modell")
    parser.add_argument("--validation-split", "-v", type=float, default=0.2,
                       help="Anteil der Daten für Validierung (0.1-0.5)")
    
    # Metadaten-Gewichtungen
    parser.add_argument("--age-weight", type=float, default=0.3,
                       help="Gewichtung für Alters-Erkennung")
    parser.add_argument("--gender-weight", type=float, default=0.25,
                       help="Gewichtung für Geschlechts-Erkennung")
    parser.add_argument("--location-weight", type=float, default=0.2,
                       help="Gewichtung für Standort-Metadaten")
    parser.add_argument("--temporal-weight", type=float, default=0.15,
                       help="Gewichtung für zeitliche Metadaten")
    parser.add_argument("--technical-weight", type=float, default=0.1,
                       help="Gewichtung für technische Metadaten")
    
    args = parser.parse_args()
    
    # Validierung
    if not os.path.exists(args.input):
        print(f"Eingabe-Pfad existiert nicht: {args.input}")
        sys.exit(1)
    
    if not (0.1 <= args.validation_split <= 0.5):
        print("Validierungs-Split muss zwischen 0.1 und 0.5 liegen")
        sys.exit(1)
    
    # Ausgabe-Verzeichnis erstellen
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    print("Starte Training der erweiterten Gesichtserkennung...")
    print(f"Eingabe: {args.input}")
    print(f"Ausgabe: {args.output}")
    print(f"Validierungs-Split: {args.validation_split}")
    
    try:
        # Trainingsdaten laden
        training_data = load_training_data(args.input)
        
        if not training_data:
            print("Keine Trainingsdaten gefunden!")
            sys.exit(1)
        
        print(f"{len(training_data)} Trainingsbeispiele geladen")
        
        # Metadaten-Gewichtungen
        metadata_weights = {
            'age': args.age_weight,
            'gender': args.gender_weight,
            'location': args.location_weight,
            'temporal': args.temporal_weight,
            'technical': args.technical_weight
        }
        
        if args.verbose:
            print("Metadaten-Gewichtungen:")
            for key, value in metadata_weights.items():
                print(f"  {key}: {value}")
        
        # Trainer initialisieren
        trainer = MetadataAwareTrainer(args.output)
        
        # Training durchführen
        results = trainer.train(training_data, args.validation_split)
        
        # Ergebnisse ausgeben
        print("\n" + "="*50)
        print("TRAINING ERFOLGREICH ABGESCHLOSSEN!")
        print("="*50)
        
        if 'training' in results:
            print("\nTraining-Metriken:")
            for metric, value in results['training'].items():
                print(f"  {metric}: {value:.3f}")
        
        if 'validation' in results:
            print("\nValidierungs-Metriken:")
            for metric, value in results['validation'].items():
                print(f"  {metric}: {value:.3f}")
        
        if 'improvement' in results:
            print("\nVerbesserungen:")
            for metric, improvement in results['improvement'].items():
                print(f"  {metric}: {improvement:+.3f}")
        
        print(f"\nModell gespeichert: {args.output}")
        print("="*50)
        
        # Modell-Info-Datei erstellen
        create_model_info(args.output, results, metadata_weights)
        
    except Exception as e:
        print(f"Fehler beim Training: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
```

### B. Hilfsfunktionen

**load_training_data():**
```python
def load_training_data(input_path: str) -> List[Dict]:
    """Lädt Trainingsdaten aus JSON-Dateien"""
    training_data = []
    
    if os.path.isfile(input_path):
        # Einzelne Datei
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    training_data.extend(data)
                else:
                    training_data.append(data)
        except Exception as e:
            print(f"Fehler beim Laden von {input_path}: {e}")
    
    elif os.path.isdir(input_path):
        # Verzeichnis - suche nach JSON-Dateien
        import glob
        json_files = glob.glob(os.path.join(input_path, "**/*.json"), recursive=True)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        training_data.extend(data)
                    else:
                        training_data.append(data)
            except Exception as e:
                print(f"Fehler beim Laden von {json_file}: {e}")
    
    return training_data
```

**create_model_info():**
```python
def create_model_info(model_path: str, results: Dict, metadata_weights: Dict):
    """Erstellt eine Info-Datei für das trainierte Modell"""
    info_path = model_path.replace('.pkl', '_info.json')
    
    info = {
        'model_path': model_path,
        'created_at': str(Path(model_path).stat().st_mtime),
        'metadata_weights': metadata_weights,
        'training_results': results,
        'model_type': 'enhanced_face_recognition',
        'version': '1.0.0'
    }
    
    try:
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        print(f"Modell-Info erstellt: {info_path}")
    except Exception as e:
        print(f"Fehler beim Erstellen der Modell-Info: {e}")
```

## 10. Verwendung

### A. Über Streamlit UI

1. Gehen Sie zur "Train" Seite
2. Wählen Sie "JSON-Dateien hochladen" oder "Aus Musterfotos generieren"
3. Laden Sie die Daten hoch
4. Konfigurieren Sie die Metadaten-Gewichtungen
5. Starten Sie das Training
6. Laden Sie das trainierte Modell herunter

### B. Über CLI

```bash
# Einzelne JSON-Datei
python train_enhanced_model.py --input training_data.json --output models/my_model.pkl

# Verzeichnis mit mehreren JSON-Dateien
python train_enhanced_model.py --input training_data/ --output models/my_model.pkl

# Mit angepassten Gewichtungen
python train_enhanced_model.py \
  --input training_data.json \
  --output models/my_model.pkl \
  --validation-split 0.3 \
  --age-weight 0.4 \
  --gender-weight 0.3 \
  --location-weight 0.2 \
  --temporal-weight 0.1 \
  --technical-weight 0.0
```

## 11. Fehlerbehandlung

**Häufige Fehler:**
- **"Enhanced Face Engine nicht verfügbar"**: Abhängigkeiten nicht installiert
- **"Location Engine nicht verfügbar"**: Metadaten-Extraktion nicht möglich
- **"Ungültiges Format"**: JSON-Struktur entspricht nicht den Anforderungen
- **"Keine Trainingsdaten gefunden"**: Eingabepfad enthält keine gültigen Daten

**Lösungsansätze:**
- Abhängigkeiten installieren: `pip install -r requirements.txt`
- JSON-Format überprüfen mit `json_format_fuer_training.md`
- Validierungs-Split anpassen (0.1-0.5)
- Mindestens 10 Trainingsbeispiele pro Kategorie

## 12. Best Practices

**Für bessere Ergebnisse:**
1. **Vielfältige Datenquellen** verwenden
2. **Ausgewogene Verteilung** von Alter, Geschlecht, Standort
3. **Qualitativ hochwertige Metadaten** sicherstellen
4. **Regelmäßige Validierung** durchführen
5. **Iterative Verbesserung** des Modells

**Datenqualität:**
- Mindestens 50-100 Trainingsbeispiele
- Verschiedene Kamera-Modelle und Einstellungen
- Verschiedene Standorte und Zeiten
- Konsistente Annotationen

Die Train-Funktion ist das Herzstück des erweiterten Gesichtserkennungssystems und ermöglicht es, durch intelligente Metadaten-Integration deutlich bessere Ergebnisse zu erzielen.
