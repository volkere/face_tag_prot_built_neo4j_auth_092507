# Zeitkalkül Metadata Recognizer - macOS/Linux Version

## Unix-optimierte Version

Diese Branch enthält die macOS/Linux-optimierte Version der App mit Unix-spezifischen Features.

### Unix-spezifische Features

- **Bash-Skripte**: Unix-kompatible Shell-Skripte
- **Homebrew-Integration**: Automatische ngrok-Installation über Homebrew
- **Unix-Permissions**: Korrekte Dateiberechtigungen
- **macOS/Linux-PATH-Management**: Unix-typische Umgebungsvariablen

### Installation

#### macOS
```bash
# Mit Homebrew
brew install python3 ngrok/ngrok/ngrok
pip3 install -r requirements.txt

# Oder automatisch
./install_macos.sh
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip
pip3 install -r requirements.txt

# Oder automatisch
./install_linux.sh
```

### Verwendung

```bash
# Lokaler Start
./start_app.sh

# Mit Internet-Zugang
./start_ngrok.sh
```

### Systemanforderungen

#### macOS
- macOS 10.15+ (Catalina oder höher)
- Python 3.9+
- Homebrew (optional)
- Mindestens 4GB RAM

#### Linux
- Ubuntu 20.04+ oder ähnliche Distribution
- Python 3.9+
- Mindestens 4GB RAM

### Dokumentation

Siehe Haupt-README.md für detaillierte Anweisungen.
