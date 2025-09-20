# Zeitkalkül Metadata Recognizer - Windows Version

## Windows-optimierte Version

Diese Branch enthält die Windows-optimierte Version der App mit speziellen Features für Microsoft Windows 11.

### Windows-spezifische Features

- **Batch-Skripte**: Automatische Installation und Start-Skripte
- **PowerShell-Integration**: Automatische ngrok-Installation
- **Windows-PATH-Management**: Automatische Umgebungsvariablen-Konfiguration
- **Fehlerbehandlung**: Windows-spezifische Fehlerbehandlung und Benutzerführung

### Installation

```cmd
install_windows.bat
```

### Verwendung

```cmd
REM Lokaler Start
start_app.bat

REM Mit Internet-Zugang
start_with_ngrok_windows.bat
```

### Systemanforderungen

- Windows 11 (64-bit)
- Python 3.9+
- PowerShell 5.1+
- Mindestens 4GB RAM

### Dokumentation

Siehe `WINDOWS_SETUP.md` für detaillierte Anweisungen.
