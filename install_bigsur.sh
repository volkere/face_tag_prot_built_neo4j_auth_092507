#!/bin/bash

# Installation Script für macOS Big Sur mit Intel-Chip
# Dieses Script installiert alle Abhängigkeiten kompatibel für Big Sur

echo "🚀 Installation für macOS Big Sur mit Intel-Chip"
echo "================================================"

# Prüfe macOS Version
echo "📋 System-Informationen:"
echo "macOS Version: $(sw_vers -productVersion)"
echo "Architektur: $(uname -m)"
echo ""

# Prüfe Python Version
echo "🐍 Python-Informationen:"
python3 --version
echo ""

# Erstelle virtuelle Umgebung
echo "📦 Erstelle virtuelle Umgebung..."
python3 -m venv venv_bigsur
source venv_bigsur/bin/activate

# Upgrade pip
echo "⬆️ Upgrade pip..."
pip install --upgrade pip

# Installiere Homebrew falls nicht vorhanden
if ! command -v brew &> /dev/null; then
    echo "🍺 Installiere Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Installiere System-Abhängigkeiten
echo "🔧 Installiere System-Abhängigkeiten..."
brew install cmake
brew install dlib
brew install opencv

# Installiere Python-Abhängigkeiten
echo "📚 Installiere Python-Abhängigkeiten..."
pip install -r requirements_bigsur.txt

# Zusätzliche Installationen für Big Sur
echo "🔧 Zusätzliche Installationen für Big Sur..."

# Installiere alternative Face Recognition falls InsightFace Probleme macht
pip install face-recognition

# Installiere kompatible ONNX Runtime
pip install onnxruntime==1.12.1

# Teste Installation
echo "🧪 Teste Installation..."
python3 -c "
import streamlit as st
import cv2
import numpy as np
import pandas as pd
import plotly
import face_recognition
import neo4j
print('✅ Alle Abhängigkeiten erfolgreich installiert!')
"

echo ""
echo "✅ Installation abgeschlossen!"
echo ""
echo "📝 Nächste Schritte:"
echo "1. Aktiviere die virtuelle Umgebung: source venv_bigsur/bin/activate"
echo "2. Starte die App: streamlit run streamlit_app.py"
echo ""
echo "⚠️ Hinweise für Big Sur:"
echo "- Falls InsightFace Probleme macht, wird automatisch face-recognition verwendet"
echo "- ONNX Runtime läuft im CPU-Modus (langsamer aber kompatibel)"
echo "- OpenCV verwendet die Homebrew-Version für bessere Kompatibilität"
