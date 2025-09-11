# 🚀 macOS Big Sur Setup - Komplette Anleitung

## 📋 Übersicht

Diese Anleitung zeigt, wie Sie die Photo Metadata Suite auf macOS Big Sur mit Intel-Chip installieren und verwenden.

## 🔧 Voraussetzungen

- **macOS Big Sur (11.x)** oder neuer
- **Intel-Chip** (nicht Apple Silicon)
- **Python 3.9+**
- **Homebrew** (wird automatisch installiert)
- **Mindestens 4GB RAM**
- **2GB freier Speicher**

## ⚡ Schnellinstallation

```bash
# 1. Script ausführbar machen
chmod +x install_bigsur.sh

# 2. Installation starten
./install_bigsur.sh

# 3. Virtuelle Umgebung aktivieren
source venv_bigsur/bin/activate

# 4. App starten
streamlit run streamlit_app_bigsur.py
```

## 📁 Neue Dateien für Big Sur

### Core-Dateien
- `app/face_recognizer_bigsur.py` - Alternative Face Recognition
- `app/main_bigsur.py` - Big Sur Hauptanwendung
- `streamlit_app_bigsur.py` - Big Sur Streamlit App

### Konfiguration
- `requirements_bigsur.txt` - Kompatible Abhängigkeiten
- `install_bigsur.sh` - Automatisches Installations-Script
- `README_BigSur.md` - Detaillierte Dokumentation

### Seiten
- `pages/1_Annotate_BigSur.py` - Big Sur Annotate-Seite

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

## 🛠️ Manuelle Installation

Falls das automatische Script nicht funktioniert:

### 1. Homebrew
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

## 🚀 Verwendung

### Standard-App (falls InsightFace verfügbar)
```bash
streamlit run streamlit_app.py
```

### Big Sur-App (mit Fallbacks)
```bash
streamlit run streamlit_app_bigsur.py
```

### Big Sur-Annotate-Seite
```bash
streamlit run pages/1_Annotate_BigSur.py
```

## 🔍 Troubleshooting

### Problem: InsightFace Installation fehlgeschlagen
**Lösung:** Verwenden Sie `streamlit_app_bigsur.py` - automatischer Fallback auf face-recognition.

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

## 📊 Feature-Vergleich

| Feature | Standard | Big Sur |
|---------|----------|---------|
| Gesichtserkennung | ✅ InsightFace | ✅ face-recognition |
| Alter/Geschlecht | ✅ Hochgenau | ✅ Vereinfacht |
| Emotion | ✅ 5 Emotionen | ✅ 3 Emotionen |
| Pose-Analyse | ✅ Vollständig | ❌ Nicht verfügbar |
| Symmetrie | ✅ Berechnet | ❌ Nicht verfügbar |
| Rausch-Analyse | ✅ Berechnet | ❌ Nicht verfügbar |
| Performance | ✅ Schnell | ⚠️ Langsamer |
| Kompatibilität | ⚠️ Neuere Systeme | ✅ Big Sur |

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
- ✅ Kompatible Abhängigkeiten für Big Sur
- ✅ Alternative Face Recognition Implementierung
- ✅ Automatische Fallback-Mechanismen
- ✅ Vereinfachte Installation
- ✅ Getestet auf macOS Big Sur mit Intel-Chip
- ✅ Vollständige Dokumentation
- ✅ Troubleshooting-Guide

## 🎯 Nächste Schritte

1. **Installation:** Führen Sie `./install_bigsur.sh` aus
2. **Aktivierung:** `source venv_bigsur/bin/activate`
3. **Start:** `streamlit run streamlit_app_bigsur.py`
4. **Test:** Laden Sie ein Bild hoch und testen Sie die Gesichtserkennung

Viel Erfolg! 🚀
