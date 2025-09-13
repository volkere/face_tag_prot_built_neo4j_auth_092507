# Windows 11 Setup Guide

## Übersicht

Dieses Dokument beschreibt die Installation und Einrichtung des Zeitkalkül Metadata Recognizer auf Microsoft Windows 11.

## Systemvoraussetzungen

- **Betriebssystem**: Windows 11 (64-bit)
- **Python**: Version 3.9 oder höher
- **RAM**: Mindestens 4GB (8GB empfohlen)
- **Speicherplatz**: Mindestens 2GB freier Speicherplatz
- **Internetverbindung**: Für Download und ngrok-Funktionalität

## Installation

### Schritt 1: Python installieren

1. Besuchen Sie [python.org/downloads](https://python.org/downloads)
2. Laden Sie Python 3.9+ für Windows herunter
3. **Wichtig**: Aktivieren Sie "Add Python to PATH" während der Installation
4. Überprüfen Sie die Installation:
   ```cmd
   python --version
   pip --version
   ```

### Schritt 2: Projekt herunterladen

1. Laden Sie das Projekt herunter oder klonen Sie es:
   ```cmd
   git clone https://github.com/volkere/zeitkalkuel_prot_built_neo4j_auth_092507.git
   cd zeitkalkuel_prot_built_neo4j_auth_092507
   ```

### Schritt 3: Automatische Installation

Führen Sie das Installationsskript aus:
```cmd
install_windows.bat
```

Das Skript:
- Installiert alle Python-Abhängigkeiten
- Überprüft die Installation
- Gibt Anweisungen für ngrok (optional)

## Verwendung

### Lokaler Start

```cmd
start_app.bat
```

Die App ist dann verfügbar unter: `http://localhost:8501`

### Internet-Zugang mit ngrok

#### Automatische ngrok-Installation
```cmd
install_ngrok_windows.bat
```

#### Start mit Internet-Zugang
```cmd
start_with_ngrok_windows.bat
```

#### Manuelle ngrok-Konfiguration
1. Registrieren Sie sich bei [ngrok.com](https://ngrok.com) (kostenlos)
2. Holen Sie sich Ihren Authtoken
3. Konfigurieren Sie ngrok:
   ```cmd
   ngrok config add-authtoken YOUR_TOKEN
   ```

## Login-Daten

- **Administrator**: Passwort `admin123`
- **Benutzer**: Passwort `user123`

## Funktionen

### Enroll
- Erstellen von Gesichts-Embeddings
- Personen-Datenbank aufbauen

### Annotate
- Foto-Analyse mit Metadaten
- Enhanced Model Upload
- Qualitätsbewertung

### Analyze
- Statistiken und Visualisierungen
- Interaktive Charts
- Bildgruppierung

### Train
- KI-Training mit Metadaten
- Trainingsdaten-Generator
- Enhanced Model Training

### Neo4j
- Graph-Datenbank-Integration
- Komplexe Abfragen
- Beziehungsanalyse

### Neo4j Browser
- Interaktive Graph-Visualisierung
- Cypher-Query-Interface
- Verschiedene Layout-Typen

## Fehlerbehebung

### Python nicht gefunden
```
FEHLER: Python ist nicht installiert oder nicht im PATH.
```
**Lösung**: Installieren Sie Python und aktivieren Sie "Add Python to PATH"

### Streamlit nicht installiert
```
FEHLER: Streamlit ist nicht installiert.
```
**Lösung**: Führen Sie `install_windows.bat` aus

### ngrok nicht verfügbar
```
FEHLER: ngrok ist nicht installiert.
```
**Lösung**: Führen Sie `install_ngrok_windows.bat` aus

### Port bereits in Verwendung
```
Port 8501 is already in use
```
**Lösung**: Beenden Sie andere Streamlit-Instanzen oder verwenden Sie einen anderen Port

### ModuleNotFoundError
```
ModuleNotFoundError: No module named 'insightface'
```
**Lösung**: Führen Sie `install_windows.bat` erneut aus

## Performance-Optimierung

### Für bessere Performance:
1. Schließen Sie unnötige Anwendungen
2. Verwenden Sie SSD-Speicher
3. Erhöhen Sie den Arbeitsspeicher
4. Verwenden Sie eine stabile Internetverbindung

### Für große Bildsammlungen:
1. Verarbeiten Sie Bilder in kleineren Chargen
2. Verwenden Sie die Qualitätsfilter
3. Optimieren Sie die Bildgröße vor der Verarbeitung

## Sicherheit

### Passwort-Schutz
- Die App verwendet einfache Passwort-Authentifizierung
- Passwörter sind in der Session gespeichert
- Automatischer Logout bei Browser-Schließung

### Internet-Zugang
- ngrok erstellt sichere, verschlüsselte Tunnel
- URLs sind temporär und ändern sich bei jedem Start
- Nur autorisierte Benutzer können auf die App zugreifen

## Support

Bei Problemen:
1. Überprüfen Sie die Fehlerbehebung oben
2. Stellen Sie sicher, dass alle Voraussetzungen erfüllt sind
3. Führen Sie die Installationsskripte erneut aus
4. Überprüfen Sie die Python-Version und PATH-Einstellungen

## Systemanforderungen im Detail

### Minimale Anforderungen
- Windows 11 (64-bit)
- Python 3.9+
- 4GB RAM
- 2GB freier Speicherplatz
- Internetverbindung

### Empfohlene Anforderungen
- Windows 11 (64-bit)
- Python 3.11+
- 8GB RAM
- 5GB freier Speicherplatz
- Stabile Internetverbindung
- SSD-Speicher

## Lizenz

Siehe `LICENSE` Datei für Details zur Lizenzierung.
