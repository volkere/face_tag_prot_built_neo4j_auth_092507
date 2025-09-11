# 🚀 Photo Metadata Suite - macOS Big Sur Edition

[![macOS Big Sur](https://img.shields.io/badge/macOS-Big%20Sur%20(11.x)-blue.svg)](https://www.apple.com/macos/big-sur/)
[![Intel Chip](https://img.shields.io/badge/Architecture-Intel%20Chip-green.svg)](https://www.intel.com/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

**Kompatible Version für macOS Big Sur mit Intel-Chip**

## 📋 Überblick

Diese Version der Photo Metadata Suite ist speziell für macOS Big Sur mit Intel-Chip optimiert und bietet:

- ✅ **Gesichtserkennung** mit face-recognition + dlib
- ✅ **Alter/Geschlecht-Schätzung** 
- ✅ **Emotion-Erkennung**
- ✅ **Neo4j Graph-Datenbank Integration**
- ✅ **Streamlit Web-Interface**
- ✅ **Automatische Fallback-Mechanismen**

## ⚡ Schnellstart

### 1. Repository klonen
```bash
git clone https://github.com/volkere/zeitkalkuel_prot_built_neo4j_intel.git
cd zeitkalkuel_prot_built_neo4j_intel
```

### 2. Automatische Installation
```bash
chmod +x install_bigsur.sh
./install_bigsur.sh
```

### 3. App starten
```bash
source venv_bigsur/bin/activate
streamlit run streamlit_app_bigsur.py
```

## 🔧 Systemanforderungen

- **macOS:** Big Sur (11.x) oder neuer
- **Architektur:** Intel-Chip (nicht Apple Silicon)
- **Python:** 3.9 oder neuer
- **RAM:** Mindestens 4GB
- **Speicher:** Mindestens 2GB freier Speicher

## 📁 Projektstruktur

```
├── app/
│   ├── face_recognizer_bigsur.py    # Big Sur Face Recognition
│   ├── main_bigsur.py               # Big Sur Hauptanwendung
│   ├── neo4j_connector.py           # Neo4j Integration
│   └── ...
├── pages/
│   ├── 0_Enroll.py                  # Gesichter registrieren
│   ├── 1_Annotate_BigSur.py         # Big Sur Annotate-Seite
│   ├── 2_Analyze.py                 # Analyse
│   ├── 3_Train.py                   # Training
│   ├── 4_Neo4j.py                   # Neo4j Verwaltung
│   └── 5_Neo4j_Browser.py           # Neo4j Graph Browser
├── docs/
│   └── NEO4J_MODEL.md               # Neo4j Datenmodell
├── requirements_bigsur.txt          # Big Sur Abhängigkeiten
├── install_bigsur.sh               # Installations-Script
├── streamlit_app_bigsur.py         # Big Sur Streamlit App
├── README_BigSur.md                # Detaillierte Dokumentation
└── BIGSUR_SETUP.md                 # Setup-Anleitung
```

## 🛠️ Installation

### Automatisch (Empfohlen)
```bash
./install_bigsur.sh
```

### Manuell
```bash
# 1. Homebrew installieren
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. System-Abhängigkeiten
brew install cmake dlib opencv

# 3. Python-Umgebung
python3 -m venv venv_bigsur
source venv_bigsur/bin/activate
pip install --upgrade pip
pip install -r requirements_bigsur.txt
```

## 🚀 Verwendung

### Standard-App
```bash
streamlit run streamlit_app_bigsur.py
```

### Big Sur-Annotate-Seite
```bash
streamlit run pages/1_Annotate_BigSur.py
```

## 🔄 Fallback-Mechanismen

### Face Recognition
1. **Primär:** InsightFace (falls verfügbar)
2. **Fallback:** face-recognition + dlib (für Big Sur)
3. **Features:** Gesichtserkennung, Alter/Geschlecht, Emotion

### Abhängigkeiten
- **OpenCV:** 4.5.x statt 4.9.x
- **NumPy:** 1.21.x statt 1.26.x
- **Streamlit:** 1.28.x statt 1.36.x
- **Neo4j:** 4.4.x statt 5.0.x

## 📊 Features

### ✅ Verfügbar
- Gesichtserkennung mit face-recognition
- Alter/Geschlecht-Schätzung
- Emotion-Erkennung (3 Emotionen)
- Gesichtsqualitätsbewertung
- EXIF-Daten-Extraktion
- Neo4j Graph-Datenbank Integration
- Streamlit Web-Interface
- Automatische Fallback-Mechanismen

### ⚠️ Eingeschränkt
- **Performance:** Langsamer als auf neueren Systemen
- **Genauigkeit:** Vereinfachte Algorithmen für Kompatibilität
- **Pose-Analyse:** Nicht verfügbar
- **Symmetrie-Prüfung:** Nicht verfügbar

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

## 📚 Dokumentation

- **[README_BigSur.md](README_BigSur.md)** - Detaillierte Dokumentation
- **[BIGSUR_SETUP.md](BIGSUR_SETUP.md)** - Komplette Setup-Anleitung
- **[docs/NEO4J_MODEL.md](docs/NEO4J_MODEL.md)** - Neo4j Datenmodell

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 📞 Support

Bei Problemen:
1. Prüfen Sie die [Troubleshooting-Sektion](#-troubleshooting)
2. Überprüfen Sie die [Dokumentation](#-dokumentation)
3. Erstellen Sie ein [Issue](https://github.com/volkere/zeitkalkuel_prot_built_neo4j_intel/issues)

## 🎯 Roadmap

- [ ] Apple Silicon Support
- [ ] Erweiterte Emotion-Erkennung
- [ ] Performance-Optimierungen
- [ ] Docker-Support
- [ ] CI/CD Pipeline

---

**Entwickelt für macOS Big Sur mit Intel-Chip** 🚀
