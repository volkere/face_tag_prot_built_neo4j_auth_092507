
import streamlit as st
import hashlib
import time

# Seite konfigurieren
st.set_page_config(page_title="Photo Metadata Suite", layout="wide")

# Einfache Authentifizierung
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "admin123" or st.session_state["password"] == "user123":
            st.session_state["password_correct"] = True
            st.session_state["username"] = "admin" if st.session_state["password"] == "admin123" else "user"
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated successfully.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.title("Zeitkalkül Metadata Recognizer - Login")
    st.markdown("Bitte geben Sie Ihr Passwort ein:")
    
    st.text_input(
        "Passwort", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Passwort nicht korrekt")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Logout-Button in der Sidebar
with st.sidebar:
    st.write(f'Willkommen *{st.session_state["username"]}*')
    if st.button('Logout'):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

st.title("Zeitkalkül Metadata Recognizer")

st.markdown("""
Wähle links eine Seite:

- **Enroll**: Embeddings für Personen-Erkennung erstellen
- **Annotate**: Fotos mit erweiterten Metadaten analysieren  
- **Analyze**: Erweiterte Statistiken und Visualisierungen
- **Train**: KI-Training mit Metadaten für bessere Genauigkeit
- **Neo4j**: Datenbank-Integration für komplexe Abfragen
- **Neo4j Browser**: Interaktive Graph-Visualisierung

### Neue Features:

**Erweiterte Metadaten-Extraktion:**
- Vollständige EXIF-Daten (Kamera, Einstellungen, Datum)
- GPS-Koordinaten mit Höhenangabe
- Detaillierte Standort-Informationen

**Verbesserte Gesichtserkennung:**
- Qualitätsbewertung für jedes Gesicht
- Emotions-Erkennung (happy, neutral, unknown)
- Augen- und Mundstatus-Erkennung
- Pose-Schätzung und Symmetrie-Analyse

**Neo4j Datenbank-Integration:**
- Import von JSON-Daten in Neo4j-Graphdatenbank
- Komplexe Abfragen nach Personen, Emotionen, Standorten
- Interaktive Statistiken und Visualisierungen
- Graph-basierte Beziehungsanalyse

**Neo4j Browser:**
- Interaktive Graph-Visualisierung mit Plotly
- Cypher-Query-Interface mit Beispiel-Abfragen
- Verschiedene Layout-Typen (Spring, Circular, Hierarchical)
- Abfrage-Historie und wiederholbare Abfragen
- Anpassbare Darstellung (Knoten-Größe, Labels, Eigenschaften)

**Erweiterte Analyse:**
- Interaktive Charts und Statistiken
- Automatische Bildgruppierung nach Standort/Zeit
- Qualitätsfilter und -bewertung
- Export-Funktionen

### Optimierungen für bessere Metadaten-Erkennung:

1. **Qualitätsfilter**: Filtert Bilder nach Gesichtsqualität und -größe
2. **Erweiterte EXIF-Parsing**: Unterstützt mehr Metadaten-Formate
3. **Intelligente Gruppierung**: Gruppiert ähnliche Bilder automatisch
4. **Visualisierungen**: Zeigt Trends und Muster in Ihren Fotos
5. **Export-Funktionen**: Speichert alle Analysen für weitere Verarbeitung
6. **Graph-Datenbank**: Ermöglicht komplexe Beziehungsabfragen
""")
