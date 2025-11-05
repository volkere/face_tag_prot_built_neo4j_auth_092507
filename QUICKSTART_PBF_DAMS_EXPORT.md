# 🚀 Quick Start: PBF-DAMS Export

Schnellanleitung zur Nutzung der PBF-DAMS Export-Funktion in der Streamlit App.

## ⚡ In 5 Minuten loslegen

### Schritt 1: PBF-DAMS Server starten

```bash
cd /Users/volkerenkrodt/Documents/pbf-dams/app
pipenv run python manage.py runserver
```

✅ Server läuft auf http://localhost:8000

### Schritt 2: Streamlit App starten

```bash
cd /Users/volkerenkrodt/Documents/PBA_Tagg/face_tag_prot_built_neo4j_auth_092507
streamlit run streamlit_app.py
```

✅ App läuft auf http://localhost:8501

### Schritt 3: In der Streamlit App

1. **Login** (falls Auth aktiv)
   - Passwort: `admin123` oder `user123`

2. **Navigiere zu "PBF-DAMS Export"**
   - In der linken Sidebar
   - Neue Page mit 📤 Icon

3. **Verbindung testen**
   - In der Sidebar: "🔌 Verbindung testen"
   - Sollte "✅ Verbindung erfolgreich!" zeigen

4. **Daten abrufen**
   - Klicke "🚀 Daten abrufen" (ohne Filter = alle Daten)
   - Oder: Filter setzen und dann abrufen

5. **Export**
   - "📥 Als JSON herunterladen"
   - "📥 Als CSV herunterladen"

## 🎯 Häufige Anwendungsfälle

### Alle Fotos von Pina Bausch finden

```
1. ☑️ "Nach Person filtern" aktivieren
2. 👥 "Personen-Liste laden" klicken
3. 📋 "Pina Bausch" aus Dropdown wählen
4. 🚀 "Daten abrufen" klicken
5. 📥 Export als CSV
```

### Alle Personen auf einem Foto sehen

```
1. ☑️ "Nach Foto filtern" aktivieren
2. ⌨️ Foto-ID eingeben (z.B. "macb_30035212_44")
3. 🚀 "Daten abrufen" klicken
4. 👀 Ergebnisse in Tabelle sehen
```

### Statistiken anzeigen

```
1. Sidebar: "🔄 Statistiken laden" klicken
2. Siehe:
   - Gesamt-Regions
   - Unique Fotos
   - Unique Personen
   - Durchschnitt Regions/Foto
```

## 🐛 Troubleshooting

### ❌ "Kann nicht verbinden"

**Problem:** Streamlit kann PBF-DAMS Server nicht erreichen

**Lösung:**
```bash
# Prüfe ob Server läuft
lsof -i :8000

# Wenn nicht, starte ihn:
cd /Users/volkerenkrodt/Documents/pbf-dams/app
pipenv run python manage.py runserver
```

### ❌ "Keine Daten gefunden"

**Problem:** count = 0, obwohl Daten vorhanden sein sollten

**Mögliche Ursachen:**
1. Keine Regions in PBF-DAMS Datenbank
2. Filter zu restriktiv
3. Nur private Personen (werden standardmäßig ausgeblendet)

**Lösung:**
- Versuche ohne Filter
- Aktiviere "Private Personen inkludieren"
- Prüfe in Django Admin ob Regions existieren

### ❌ ModuleNotFoundError: 'requests'

**Problem:** requests-Modul nicht installiert

**Lösung:**
```bash
cd /Users/volkerenkrodt/Documents/PBA_Tagg/face_tag_prot_built_neo4j_auth_092507
pip install requests
# oder mit venv:
source venv/bin/activate
pip install requests
```

## 💡 Tipps & Tricks

### Tipp 1: Listen vorher laden
Lade Foto- und Personen-Listen beim Start, dann kannst du schnell suchen ohne Identifier zu kennen.

### Tipp 2: Ergebnisse speichern
Streamlit behält Ergebnisse im Session State - du kannst mehrmals exportieren ohne neu abzurufen.

### Tipp 3: Große Datasets
Bei >1000 Regions: Nutze Filter, um die Datenmenge zu reduzieren.

### Tipp 4: CSV in Excel
CSV mit UTF-8-Encoding öffnen für korrekte Umlaute.

## 📚 Weiterführende Dokumentation

- **Vollständige Integration-Doku:** `docs/PBF_DAMS_INTEGRATION.md`
- **API-Client Code:** `app/pbf_dams_client.py`
- **Streamlit Page Code:** `pages/6_PBF_DAMS_Export.py`

---

**Viel Erfolg! 🎭**

