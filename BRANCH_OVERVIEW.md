# Branch-Übersicht

## 📁 Verfügbare Branches

Dieses Repository enthält verschiedene Varianten der Zeitkalkül Metadata Recognizer App als separate Branches:

### 🌟 **main** - Vollständige Version
**Empfohlen für die meisten Benutzer**

- ✅ **Alle Features**: Streamlit UI + CLI + Neo4j + Authentifizierung
- ✅ **Plattformen**: Windows, macOS, Linux
- ✅ **Internet-Zugang**: ngrok-Integration
- ✅ **Sicherheit**: Passwort-Authentifizierung
- ✅ **Dokumentation**: Vollständige README und Setup-Anleitungen

**Zielgruppe**: Benutzer, die alle Funktionen benötigen

---

### 🪟 **windows-optimized** - Windows-Version
**Optimiert für Microsoft Windows 11**

- ✅ **Windows-spezifisch**: Batch-Skripte (.bat)
- ✅ **PowerShell-Integration**: Automatische ngrok-Installation
- ✅ **Einfache Installation**: Ein-Klick-Setup
- ✅ **Fehlerbehandlung**: Windows-spezifische Fehlerbehandlung
- ✅ **PATH-Management**: Automatische Umgebungsvariablen

**Zielgruppe**: Windows 11-Benutzer

**Installation**:
```cmd
install_windows.bat
start_app.bat
```

---

### 🐧 **macos-linux** - Unix-Version
**Optimiert für macOS und Linux**

- ✅ **Unix-optimiert**: Bash-Skripte (.sh)
- ✅ **Homebrew-Integration**: Automatische ngrok-Installation
- ✅ **Unix-Permissions**: Korrekte Dateiberechtigungen
- ✅ **PATH-Management**: Unix-typische Umgebungsvariablen

**Zielgruppe**: macOS/Linux-Benutzer

**Installation**:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

### ⚡ **minimal-no-neo4j** - Leichtgewichtige Version
**Ohne Graph-Datenbank-Abhängigkeiten**

- ✅ **Reduzierte Abhängigkeiten**: Keine Neo4j-Pakete
- ✅ **Schnellerer Start**: Keine Datenbank-Initialisierung
- ✅ **Einfachere Wartung**: Weniger Komponenten
- ✅ **Bessere Performance**: Fokus auf Kern-Features
- ❌ **Entfernt**: Neo4j-Integration, Graph-Visualisierung

**Zielgruppe**: Benutzer ohne Neo4j-Anforderungen

**Vorteile**:
- Geringere Systemanforderungen (2GB RAM statt 4GB)
- Schnellere Installation
- Weniger Komplexität

---

### 💻 **cli-only** - Kommandozeilen-Version
**Nur für Kommandozeilen-Interface**

- ✅ **Performance**: Optimiert für Batch-Verarbeitung
- ✅ **Automatisierung**: Ideal für Skripte und Workflows
- ✅ **Ressourcenschonend**: Keine Web-UI-Overhead
- ✅ **Skalierbar**: Parallele Verarbeitung möglich
- ❌ **Entfernt**: Streamlit UI, Interaktive Visualisierungen

**Zielgruppe**: Entwickler und Automatisierung

**Verwendung**:
```bash
python -m app.main enroll --gallery ./gallery --db embeddings.pkl
python -m app.main annotate --input ./photos --out output.json
```

---

### 🔧 **full-featured** - Entwicklungsversion
**Inklusive experimenteller Funktionen**

- ✅ **Alle Features**: Wie main, aber mit zusätzlichen Entwicklungsfeatures
- ✅ **Experimentell**: Neue, noch nicht stabile Funktionen
- ✅ **Entwicklungszwecke**: Für Entwickler und Tester
- ⚠️ **Warnung**: Möglicherweise instabil

**Zielgruppe**: Entwickler und Power-User

---

## 🚀 Branch-Wechsel

### Aktuellen Branch anzeigen
```bash
git branch
```

### Branch wechseln
```bash
git checkout <branch-name>
```

### Alle Branches anzeigen
```bash
git branch -a
```

### Branch aus Remote holen
```bash
git checkout -b <branch-name> origin/<branch-name>
```

## 📋 Feature-Vergleich

| Feature | main | windows | macos-linux | minimal | cli-only |
|---------|------|---------|-------------|---------|----------|
| Streamlit UI | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLI Interface | ✅ | ✅ | ✅ | ✅ | ✅ |
| Neo4j Integration | ✅ | ✅ | ✅ | ❌ | ✅ |
| Authentifizierung | ✅ | ✅ | ✅ | ✅ | ❌ |
| Internet-Zugang | ✅ | ✅ | ✅ | ✅ | ❌ |
| Windows-Skripte | ✅ | ✅ | ❌ | ✅ | ❌ |
| Unix-Skripte | ✅ | ❌ | ✅ | ✅ | ❌ |
| Batch-Verarbeitung | ✅ | ✅ | ✅ | ✅ | ✅ |

## 🎯 Empfehlungen

### Für Einsteiger
- **Windows**: `windows-optimized`
- **macOS/Linux**: `macos-linux`

### Für Entwickler
- **Vollständig**: `main`
- **Performance**: `cli-only`
- **Experimentell**: `full-featured`

### Für Produktionsumgebung
- **Stabil**: `main`
- **Minimal**: `minimal-no-neo4j`

### Für Automatisierung
- **Batch-Verarbeitung**: `cli-only`
- **Skripte**: `cli-only`

## 📖 Weitere Informationen

- **Haupt-README**: Siehe `README.md` für allgemeine Informationen
- **Branch-spezifisch**: Jeder Branch hat eigene README-Dateien
- **Dokumentation**: Siehe `docs/` Verzeichnis für detaillierte Anleitungen
