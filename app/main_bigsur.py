"""
Hauptanwendung für macOS Big Sur mit Intel-Chip
Kompatible Version mit alternativen Abhängigkeiten
"""

import sys
import os
import logging
from pathlib import Path

# Füge den app-Ordner zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent))

def check_compatibility():
    """Prüft System-Kompatibilität"""
    import platform
    
    system = platform.system()
    version = platform.mac_ver()[0]
    architecture = platform.machine()
    
    print(f"System: {system} {version}")
    print(f"Architektur: {architecture}")
    
    if system == "Darwin" and version.startswith("11."):  # Big Sur
        print("✅ macOS Big Sur erkannt")
        return True
    elif system == "Darwin":
        print("⚠️ Andere macOS-Version - möglicherweise kompatibel")
        return True
    else:
        print("❌ Nicht-macOS-System")
        return False

def import_with_fallback():
    """Importiert Module mit Fallback-Optionen"""
    try:
        # Versuche InsightFace zu importieren
        import insightface
        from app.face_recognizer import FaceRecognizer
        print("✅ InsightFace verfügbar - verwende Standard-Implementierung")
        return FaceRecognizer()
    except ImportError:
        print("⚠️ InsightFace nicht verfügbar - verwende Big Sur-Implementierung")
        try:
            from app.face_recognizer_bigsur import FaceRecognizerBigSur
            return FaceRecognizerBigSur()
        except ImportError as e:
            print(f"❌ Fehler beim Import der Big Sur-Implementierung: {e}")
            return None

def main():
    """Hauptfunktion"""
    print("🚀 Photo Metadata Suite - Big Sur Edition")
    print("=" * 50)
    
    # Prüfe Kompatibilität
    if not check_compatibility():
        print("❌ System nicht kompatibel")
        return 1
    
    # Importiere mit Fallback
    face_recognizer = import_with_fallback()
    if face_recognizer is None:
        print("❌ Kein Face Recognizer verfügbar")
        return 1
    
    print("✅ Face Recognizer erfolgreich geladen")
    
    # Teste grundlegende Funktionalität
    try:
        import cv2
        import numpy as np
        import streamlit
        
        print("✅ Alle Abhängigkeiten verfügbar")
        
        # Starte Streamlit
        print("🌐 Starte Streamlit-App...")
        os.system("streamlit run streamlit_app.py")
        
    except ImportError as e:
        print(f"❌ Fehlende Abhängigkeit: {e}")
        print("📋 Führen Sie das Installations-Script aus:")
        print("   ./install_bigsur.sh")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
