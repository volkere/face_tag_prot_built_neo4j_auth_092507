# Photo Metadata Suite - Big Sur Edition

Kompatible Version für macOS Big Sur mit Intel-Chip.

## 🚀 Schnellstart

### 1. Installation
```bash
# Führen Sie das Installations-Script aus
./install_bigsur.sh
```

### 2. Aktivierung
```bash
# Aktivieren Sie die virtuelle Umgebung
source venv_bigsur/bin/activate
```

### 3. Start
```bash
# Starten Sie die App
streamlit run streamlit_app_bigsur.py
```

## 📋 Systemanforderungen

- **macOS:** Big Sur (11.x) oder neuer
- **Architektur:** Intel-Chip
- **Python:** 3.9 oder neuer
- **RAM:** Mindestens 4GB
- **Speicher:** Mindestens 2GB freier Speicher

## 🔧 Kompatibilitätsanpassungen

### Face Recognition
- **Standard:** InsightFace (falls verfügbar)
- **Fallback:** face-recognition + dlib (für Big Sur)
- **Features:** Gesichtserkennung, Alter/Geschlecht-Schätzung, Emotion-Erkennung

### Abhängigkeiten
- **OpenCV:** 4.5.x (kompatibel mit Big Sur)
- **NumPy:** 1.21.x (stabile Version)
- **Streamlit:** 1.28.x (getestet mit Big Sur)
- **Neo4j:** 4.4.x (kompatible Version)

## 📁 Dateistruktur

```
├── app/
│   ├── face_recognizer_bigsur.py    # Big Sur Face Recognition
│   ├── main_bigsur.py               # Big Sur Hauptanwendung
│   └── ...
├── pages/
│   ├── 0_Enroll.py
│   ├── 1_Annotate.py
│   ├── 2_Analyze.py
│   ├── 3_Train.py
│   ├── 4_Neo4j.py
│   └── 5_Neo4j_Browser.py
├── requirements_bigsur.txt          # Big Sur Abhängigkeiten
├── install_bigsur.sh               # Installations-Script
├── streamlit_app_bigsur.py         # Big Sur Streamlit App
└── README_BigSur.md                # Diese Datei
```

## 🛠️ Installation manuell

Falls das automatische Script nicht funktioniert:

### 1. Homebrew installieren
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. System-Abhängigkeiten
```bash
brew install cmake
brew install dlib
brew install opencv
```

### 3. Python-Umgebung
```bash
python3 -m venv venv_bigsur
source venv_bigsur/bin/activate
pip install --upgrade pip
pip install -r requirements_bigsur.txt
```

## 🔍 Troubleshooting

### Problem: InsightFace Installation fehlgeschlagen
**Lösung:** Die App verwendet automatisch die Big Sur-Implementierung mit face-recognition.

### Problem: OpenCV Fehler
**Lösung:** 
```bash
brew install opencv
pip uninstall opencv-python
pip install opencv-python==4.5.5.64
```

### Problem: dlib Installation fehlgeschlagen
**Lösung:**
```bash
brew install cmake
pip install dlib==19.22.1
```

### Problem: Neo4j Verbindung
**Lösung:** Neo4j-Features sind optional. Die App funktioniert auch ohne Neo4j.

## 📊 Features

### ✅ Verfügbar
- Gesichtserkennung
- Alter/Geschlecht-Schätzung
- Emotion-Erkennung
- Gesichtsqualitätsbewertung
- EXIF-Daten-Extraktion
- Streamlit-Interface
- Neo4j-Integration (optional)

### ⚠️ Eingeschränkt
- **Performance:** Langsamer als auf neueren Systemen
- **Genauigkeit:** Vereinfachte Algorithmen für Kompatibilität
- **Features:** Einige erweiterte Features möglicherweise nicht verfügbar

## 🔄 Updates

Für Updates führen Sie das Installations-Script erneut aus:
```bash
./install_bigsur.sh
```

## 📞 Support

Bei Problemen:
1. Prüfen Sie die Systemanforderungen
2. Führen Sie das Installations-Script erneut aus
3. Überprüfen Sie die Logs in der Streamlit-App
4. Verwenden Sie die Fallback-Implementierungen

## 📝 Changelog

### Version 1.0.0 (Big Sur Edition)
- Kompatible Abhängigkeiten für Big Sur
- Alternative Face Recognition Implementierung
- Automatische Fallback-Mechanismen
- Vereinfachte Installation
- Getestet auf macOS Big Sur mit Intel-Chip
