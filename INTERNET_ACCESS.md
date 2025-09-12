# Internet-Zugang für Zeitkalkül Metadata Recognizer

Diese Anleitung zeigt, wie Sie die Streamlit-App temporär über das Internet zugänglich machen können.

## Voraussetzungen

- ngrok ist installiert (`brew install ngrok/ngrok/ngrok`)
- streamlit-authenticator ist installiert (`pip install streamlit-authenticator`)
- Python 3.9+ ist installiert

## Login-Daten

Die App ist mit einem Authentifizierungssystem geschützt:

### Administrator-Zugang:
- **Benutzername:** `admin`
- **Passwort:** `admin123`

### Benutzer-Zugang:
- **Benutzername:** `user`
- **Passwort:** `user123`

## Starten der App mit Internet-Zugang

### Option 1: Bash-Skript (Empfohlen)
```bash
./start_ngrok.sh
```

### Option 2: Python-Skript
```bash
python3 start_with_ngrok.py
```

### Option 3: Manuell
```bash
# Terminal 1: Streamlit starten
streamlit run streamlit_app.py --server.port 8501

# Terminal 2: ngrok starten
ngrok http 8501
```

## Was passiert?

1. **Streamlit-App startet** auf Port 8501
2. **ngrok-Tunnel wird erstellt** und macht die App öffentlich zugänglich
3. **Öffentliche URL wird angezeigt** (z.B. `https://abc123.ngrok.io`)
4. **Login-Daten werden angezeigt**

## Sicherheitshinweise

⚠️ **WICHTIG:**
- Die ngrok-URL ist **temporär** und wird beim Beenden ungültig
- Verwenden Sie **starke Passwörter** in Produktionsumgebungen
- Die App ist nur so lange zugänglich, wie der Tunnel aktiv ist
- Beenden Sie den Tunnel mit `Ctrl+C`

## Beenden

Drücken Sie `Ctrl+C` in dem Terminal, in dem Sie das Skript gestartet haben.

## Fehlerbehebung

### "ngrok not found"
```bash
brew install ngrok/ngrok/ngrok
```

### "streamlit-authenticator not found"
```bash
pip install streamlit-authenticator
```

### "Port 8501 already in use"
```bash
# Andere Streamlit-Instanz beenden oder anderen Port verwenden
streamlit run streamlit_app.py --server.port 8502
ngrok http 8502
```

## Features der geschützten App

- ✅ **Sichere Authentifizierung** mit Benutzername/Passwort
- ✅ **Session-Management** mit Cookies
- ✅ **Logout-Funktion** in der Sidebar
- ✅ **Vollständige Funktionalität** aller Seiten
- ✅ **Temporärer Internet-Zugang** über ngrok

## Unterstützte Seiten

- **Enroll**: Embeddings für Personen-Erkennung erstellen
- **Annotate**: Fotos mit erweiterten Metadaten analysieren
- **Analyze**: Erweiterte Statistiken und Visualisierungen
- **Train**: KI-Training mit Metadaten für bessere Genauigkeit
- **Neo4j**: Datenbank-Integration für komplexe Abfragen
- **Neo4j Browser**: Interaktive Graph-Visualisierung
