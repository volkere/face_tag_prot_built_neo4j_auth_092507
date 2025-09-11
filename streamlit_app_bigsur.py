"""
Streamlit App für macOS Big Sur mit Intel-Chip
Kompatible Version mit Fallback-Optionen
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Füge den app-Ordner zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Versuche Face Recognizer zu importieren
try:
    from app.face_recognizer import FaceRecognizer
    FACE_RECOGNIZER_AVAILABLE = True
    FACE_RECOGNIZER_TYPE = "InsightFace"
except ImportError:
    try:
        from app.face_recognizer_bigsur import FaceRecognizerBigSur as FaceRecognizer
        FACE_RECOGNIZER_AVAILABLE = True
        FACE_RECOGNIZER_TYPE = "BigSur"
    except ImportError:
        FACE_RECOGNIZER_AVAILABLE = False
        FACE_RECOGNIZER_TYPE = "None"

# Versuche Neo4j zu importieren
try:
    from app.neo4j_connector import Neo4jManager
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

st.set_page_config(
    page_title="Photo Metadata Suite - Big Sur Edition",
    page_icon="📸",
    layout="wide"
)

st.title("📸 Photo Metadata Suite")
st.caption("Big Sur Edition - Kompatible Version für macOS Big Sur mit Intel-Chip")

# System-Informationen
with st.expander("System-Informationen", expanded=False):
    import platform
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**System:** {platform.system()} {platform.mac_ver()[0]}")
        st.write(f"**Architektur:** {platform.machine()}")
        st.write(f"**Python:** {platform.python_version()}")
    
    with col2:
        st.write(f"**Face Recognizer:** {FACE_RECOGNIZER_TYPE}")
        st.write(f"**Neo4j:** {'Verfügbar' if NEO4J_AVAILABLE else 'Nicht verfügbar'}")
        st.write(f"**Streamlit:** {st.__version__}")

# Warnung falls nicht alle Features verfügbar
if not FACE_RECOGNIZER_AVAILABLE:
    st.error("⚠️ Face Recognition nicht verfügbar. Führen Sie das Installations-Script aus: ./install_bigsur.sh")
    st.stop()

if not NEO4J_AVAILABLE:
    st.warning("⚠️ Neo4j nicht verfügbar. Neo4j-Features sind deaktiviert.")

# Hauptnavigation
if FACE_RECOGNIZER_AVAILABLE:
    st.sidebar.title("Navigation")
    
    pages = ["Enroll", "Annotate", "Analyze", "Train"]
    
    if NEO4J_AVAILABLE:
        pages.extend(["Neo4j", "Neo4j Browser"])
    
    selected_page = st.sidebar.selectbox("Seite auswählen", pages)
    
    # Lade die entsprechende Seite
    if selected_page == "Enroll":
        try:
            from pages import Enroll
            Enroll.main()
        except ImportError:
            st.error("Enroll-Seite nicht verfügbar")
    
    elif selected_page == "Annotate":
        try:
            from pages import Annotate
            Annotate.main()
        except ImportError:
            st.error("Annotate-Seite nicht verfügbar")
    
    elif selected_page == "Analyze":
        try:
            from pages import Analyze
            Analyze.main()
        except ImportError:
            st.error("Analyze-Seite nicht verfügbar")
    
    elif selected_page == "Train":
        try:
            from pages import Train
            Train.main()
        except ImportError:
            st.error("Train-Seite nicht verfügbar")
    
    elif selected_page == "Neo4j" and NEO4J_AVAILABLE:
        try:
            from pages import Neo4j
            Neo4j.main()
        except ImportError:
            st.error("Neo4j-Seite nicht verfügbar")
    
    elif selected_page == "Neo4j Browser" and NEO4J_AVAILABLE:
        try:
            from pages import Neo4j_Browser
            Neo4j_Browser.main()
        except ImportError:
            st.error("Neo4j Browser-Seite nicht verfügbar")

else:
    st.error("❌ Keine Face Recognition verfügbar")
    st.info("📋 Installationsanweisungen:")
    st.code("""
# 1. Führen Sie das Installations-Script aus:
./install_bigsur.sh

# 2. Aktivieren Sie die virtuelle Umgebung:
source venv_bigsur/bin/activate

# 3. Starten Sie die App:
streamlit run streamlit_app_bigsur.py
    """)

# Footer
st.markdown("---")
st.markdown("**Photo Metadata Suite - Big Sur Edition**")
st.markdown("Kompatible Version für macOS Big Sur mit Intel-Chip")
