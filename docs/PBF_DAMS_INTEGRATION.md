# PBF-DAMS Integration

Dokumentation zur Integration zwischen der Streamlit App (PBA_Tagg) und dem PBF-DAMS Django Backend.

## 🔄 Datenfluss

```
┌─────────────────────┐           ┌──────────────────────┐
│   PBF-DAMS          │           │   PBA_Tagg           │
│   (Django)          │  ◄─────   │   (Streamlit)        │
│                     │   HTTP    │                      │
│  - PostgreSQL       │   API     │  - Suchmaske         │
│  - Image Regions    │           │  - Export-Funktion   │
│  - XMP-Metadaten    │           │  - Daten-Anzeige     │
└─────────────────────┘           └──────────────────────┘
       localhost:8000                   localhost:8501
```

**Datenfluss:**
1. Nutzer öffnet Streamlit App (PBA_Tagg)
2. Suchmaske in Page "PBF-DAMS Export"
3. Filter setzen (Foto, Person, etc.)
4. Button "Daten abrufen" klicken
5. Streamlit ruft Django REST API auf
6. Daten werden in Tabelle angezeigt
7. Export als JSON oder CSV

## 📁 Neue Dateien

### 1. API-Client
**Datei:** `app/pbf_dams_client.py`

```python
from app.pbf_dams_client import PBFDAMSClient

client = PBFDAMSClient(base_url="http://localhost:8000")
regions = client.get_regions(person="pina_bausch")
```

**Funktionen:**
- `get_regions()` - Holt Region-Daten mit optionalen Filtern
- `get_photos_list()` - Liste aller Fotos mit Regions
- `get_persons_list()` - Liste aller Personen mit Regions
- `test_connection()` - Verbindungstest
- `get_statistics()` - Statistiken über Regions

### 2. Streamlit Page
**Datei:** `pages/6_PBF_DAMS_Export.py`

Die neue Page erscheint automatisch in der Streamlit-Navigation.

**Features:**
- ✅ Suchmaske mit Filtern
- ✅ Foto-Liste zum Auswählen
- ✅ Personen-Liste zum Auswählen
- ✅ Ergebnis-Tabelle
- ✅ JSON-Download
- ✅ CSV-Download
- ✅ Statistiken
- ✅ Verbindungstest

### 3. Requirements
**Datei:** `requirements.txt`

Neue Dependency hinzugefügt:
```
requests>=2.31.0
```

## 🚀 Installation & Setup

### 1. Requirements installieren

```bash
cd /Users/volkerenkrodt/Documents/PBA_Tagg/face_tag_prot_built_neo4j_auth_092507
pip install -r requirements.txt
```

Oder mit venv:

```bash
cd /Users/volkerenkrodt/Documents/PBA_Tagg/face_tag_prot_built_neo4j_auth_092507
source venv/bin/activate  # oder: .\venv\Scripts\activate auf Windows
pip install requests
```

### 2. PBF-DAMS Server starten

```bash
cd /Users/volkerenkrodt/Documents/pbf-dams/app
pipenv run python manage.py runserver
```

Server läuft auf: `http://localhost:8000`

### 3. Streamlit App starten

```bash
cd /Users/volkerenkrodt/Documents/PBA_Tagg/face_tag_prot_built_neo4j_auth_092507
streamlit run streamlit_app.py
```

App läuft auf: `http://localhost:8501`

### 4. PBF-DAMS Export Page öffnen

In der Streamlit App:
1. Einloggen (falls Auth aktiv)
2. Navigation: "PBF-DAMS Export" Page
3. Verbindung testen
4. Suchen & Exportieren

## 📖 Verwendung

### Beispiel 1: Alle Regions abrufen

1. Öffne Page "PBF-DAMS Export"
2. Klicke "🚀 Daten abrufen" (ohne Filter)
3. Ergebnisse werden angezeigt
4. Download als JSON oder CSV

### Beispiel 2: Fotos einer bestimmten Person

1. Hake "Nach Person filtern" an
2. Klicke "👥 Personen-Liste laden"
3. Wähle Person aus Dropdown (z.B. "Pina Bausch")
4. Klicke "🚀 Daten abrufen"
5. Siehe alle Fotos, auf denen die Person markiert ist

### Beispiel 3: Alle Personen auf einem Foto

1. Hake "Nach Foto filtern" an
2. Gib Foto-Identifier ein (z.B. `macb_30035212_44`)
3. Oder: Klicke "📋 Foto-Liste laden" und wähle aus
4. Klicke "🚀 Daten abrufen"
5. Siehe alle Personen auf diesem Foto

### Beispiel 4: Spezifische Person auf spezifischem Foto

1. Aktiviere beide Filter
2. Wähle Foto UND Person
3. Klicke "🚀 Daten abrufen"
4. Siehe ob diese Person auf diesem Foto markiert ist

## 🔧 API-Endpunkte

Die Integration nutzt den neu implementierten Export-Endpunkt:

```
GET http://localhost:8000/api/v1/exports/image-regions/
```

**Query-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `format` | string | Immer "json" für Streamlit |
| `photo` | string | Filter nach Foto-Identifier |
| `person` | string | Filter nach Person-Identifier |
| `include_unidentified` | boolean | Private Personen inkludieren |

**Response-Format:**

```json
{
  "count": 2,
  "export_format": "json",
  "regions": [
    {
      "type": {...},
      "x": 0.5,
      "y": 0.5,
      "width": 0.1,
      "height": 0.1,
      "rotation": 0.0,
      "person": {
        "identifier": "pina_bausch",
        "label": "Pina Bausch",
        "type": {...},
        "url": "/person/pina_bausch"
      },
      "photo_identifier": "macb_30035212_44",
      "photo_label": "Macbeth Foto",
      "ref_width": 5632,
      "ref_height": 3755
    }
  ]
}
```

## 🧪 Testen der Integration

### Verbindungstest

```python
from app.pbf_dams_client import PBFDAMSClient

client = PBFDAMSClient()
if client.test_connection():
    print("✅ Verbindung OK")
else:
    print("❌ Verbindung fehlgeschlagen")
```

### Daten abrufen

```python
# Alle Regions
data = client.get_regions()
print(f"Gefunden: {data['count']} Regions")

# Nach Person filtern
data = client.get_regions(person="pina_bausch")
for region in data['regions']:
    rd = RegionData(region)
    print(f"{rd.person_name} auf {rd.photo_identifier}")

# Nach Foto filtern
data = client.get_regions(photo="macb_30035212_44")
print(f"Personen auf Foto: {len(data['regions'])}")
```

### Listen abrufen

```python
# Alle Fotos
photos = client.get_photos_list()
print(f"Fotos mit Regions: {len(photos)}")

# Alle Personen
persons = client.get_persons_list()
for person in persons:
    print(f"{person['label']} ({person['identifier']})")

# Statistiken
stats = client.get_statistics()
print(f"Total: {stats['total_regions']} Regions")
print(f"Fotos: {stats['unique_photos']}")
print(f"Personen: {stats['unique_persons']}")
```

## ⚠️ Troubleshooting

### Problem: "Kann nicht verbinden"

**Lösung:**
1. Prüfe ob PBF-DAMS Server läuft:
   ```bash
   lsof -i :8000
   ```
2. Starte Server falls nötig:
   ```bash
   cd /Users/volkerenkrodt/Documents/pbf-dams/app
   pipenv run python manage.py runserver
   ```

### Problem: "Keine Daten gefunden"

**Lösung:**
1. Prüfe ob Regions in PBF-DAMS existieren:
   ```bash
   curl http://localhost:8000/api/v1/exports/image-regions/ | jq '.count'
   ```
2. Falls 0: Lade Testdaten oder erstelle Image-Region-Tags im Django Admin

### Problem: "404 Not Found"

**Lösung:**
1. Prüfe ob Export-Endpunkt aktiviert ist:
   ```bash
   curl http://localhost:8000/api/v1/exports/image-regions/
   ```
2. Sollte JSON zurückgeben, nicht 404

### Problem: "Connection Timeout"

**Lösung:**
1. Erhöhe Timeout in Streamlit:
   ```python
   client = PBFDAMSClient(base_url="http://localhost:8000")
   data = client.get_regions(timeout=60)  # 60 Sekunden
   ```

### Problem: "Encoding-Fehler im CSV"

**Lösung:**
- CSV-Export nutzt `utf-8-sig` für korrekte Umlaute
- Öffne CSV mit Excel/Numbers → Encoding UTF-8 wählen

## 🔒 Sicherheit & Berechtigungen

### Authentifizierung

**PBF-DAMS:**
- Export-Endpunkt ist aktuell **ohne Auth**
- Nur für Test/Development
- Für Produktion: OAuth-Token oder Session-Auth hinzufügen

**Streamlit:**
- Einfache Passwort-Auth bereits vorhanden
- Für Produktion: Erweitere auf User-Management

### Datenschutz

**Standardverhalten:**
- Nur **öffentliche** Personen werden exportiert
- Private Personen sind ausgeschlossen
- Checkbox "Private Personen inkludieren" nur für Admin

**Empfehlung:**
- Nutze `include_unidentified=False` (Standard)
- Nur Admin sollte private Daten sehen können

## 🚀 Erweiterte Nutzung

### Integration mit bestehenden Pages

Du kannst den Client in anderen Streamlit-Pages nutzen:

```python
# In pages/1_Annotate.py
from app.pbf_dams_client import PBFDAMSClient

client = PBFDAMSClient()
regions = client.get_regions(photo=current_photo_id)

# Zeige vorhandene Tags an
for region in regions['regions']:
    st.write(f"Bereits getaggt: {region['person']['label']}")
```

### Daten in Neo4j importieren

```python
# In pages/4_Neo4j.py
from app.pbf_dams_client import PBFDAMSClient
from app.neo4j_connector import Neo4jConnector

# Daten aus PBF-DAMS holen
client = PBFDAMSClient()
data = client.get_regions()

# In Neo4j speichern
neo4j = Neo4jConnector()
for region in data['regions']:
    neo4j.create_person_photo_relation(
        person_id=region['person']['identifier'],
        photo_id=region['photo_identifier'],
        coordinates=region
    )
```

### Export-Pipeline automatisieren

```python
# Täglicher Export via Cron
import schedule
import time
from app.pbf_dams_client import PBFDAMSClient

def daily_export():
    client = PBFDAMSClient()
    data = client.get_regions()
    
    # Speichere als Backup
    timestamp = datetime.now().strftime('%Y%m%d')
    with open(f'backup/regions_{timestamp}.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Exported {data['count']} regions")

# Täglich um 3 Uhr morgens
schedule.every().day.at("03:00").do(daily_export)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📊 Datenstruktur

### RegionData Helper-Klasse

```python
from app.pbf_dams_client import RegionData

region = RegionData(region_dict)

# Einfacher Zugriff
print(region.person_name)        # "Pina Bausch"
print(region.person_identifier)  # "pina_bausch"
print(region.photo_identifier)   # "macb_30035212_44"
print(region.coordinates)        # {"x": 0.5, "y": 0.5, ...}
print(region.dimensions)         # {"width": 5632, "height": 3755}
```

## 🔗 Weitere Ressourcen

### PBF-DAMS Dokumentation
- **Export-API Guide:** `pbf-dams/IMAGE_REGIONS_EXPORT_TEST_GUIDE.md`
- **Regions Erklärung:** `pbf-dams/REGIONS_ERKLAERUNG.md`
- **API-Dokumentation:** http://localhost:8000/api/docs/

### PBA_Tagg Dokumentation
- **Hauptdoku:** `README.md`
- **Architektur:** `docs/ARCHITECTURE.md`
- **Installation:** `docs/INSTALL.md`

## 🎯 Use Cases

### 1. Qualitätskontrolle
**Ziel:** Prüfen ob alle Personen auf Fotos getaggt sind

```
1. In Streamlit: Foto-Liste laden
2. Für jedes Foto: Regions abrufen
3. Vergleichen mit erwarteten Personen
4. Fehlende Tags identifizieren
```

### 2. Metadaten-Synchronisation
**Ziel:** PBF-DAMS Daten mit Face-Recognition abgleichen

```
1. Regions aus PBF-DAMS laden
2. Gleiche Fotos mit Face-Recognition analysieren
3. Ergebnisse vergleichen
4. Diskrepanzen melden
```

### 3. Statistische Analysen
**Ziel:** Häufigkeiten und Verteilungen analysieren

```
1. Alle Regions exportieren
2. In Pandas DataFrame laden
3. Gruppieren, Aggregieren, Visualisieren
4. Plotly-Charts erstellen
```

### 4. Backup & Archivierung
**Ziel:** Regelmäßige Backups der Metadaten

```
1. Täglicher automatischer Export
2. Versionierung mit Timestamp
3. Speicherung als JSON
4. Optional: Git-Commit der Backups
```

## 🛠️ Entwicklung & Debugging

### Logging aktivieren

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app.pbf_dams_client')
logger.setLevel(logging.DEBUG)
```

### Test-Daten erstellen

In PBF-DAMS (Django Admin):
1. Öffne http://localhost:8000/admin/
2. Login als Admin
3. Navigiere zu "Image Region Tags"
4. Erstelle Test-Regions
5. Oder: Lade Foto mit XMP-Metadaten hoch

### Manueller API-Test

```bash
# Test ohne Filter
curl http://localhost:8000/api/v1/exports/image-regions/ | jq '.'

# Test mit Person-Filter
curl "http://localhost:8000/api/v1/exports/image-regions/?person=pina_bausch" | jq '.count'

# Test mit Foto-Filter
curl "http://localhost:8000/api/v1/exports/image-regions/?photo=macb_30035212_44" | jq '.regions[].person.label'
```

## ⚡ Performance-Tipps

### 1. Caching in Streamlit

```python
import streamlit as st

@st.cache_data(ttl=300)  # Cache für 5 Minuten
def load_regions(photo_id=None):
    client = PBFDAMSClient()
    return client.get_regions(photo=photo_id)

# Nutzt Cache bei wiederholten Aufrufen
data = load_regions("macb_30035212_44")
```

### 2. Batch-Processing

```python
# Statt einzelner Requests pro Foto
for photo_id in photo_ids:
    client.get_regions(photo=photo_id)  # Langsam!

# Besser: Alle auf einmal, dann filtern
all_data = client.get_regions()
for photo_id in photo_ids:
    photo_regions = [
        r for r in all_data['regions'] 
        if r['photo_identifier'] == photo_id
    ]
```

### 3. Async Requests (optional)

Für viele parallele Requests:

```python
import asyncio
import aiohttp

async def fetch_regions_async(photo_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_one(session, photo_id) 
            for photo_id in photo_ids
        ]
        return await asyncio.gather(*tasks)
```

## 🔐 Produktion-Setup

### Für Production-Deployment:

**1. Umgebungsvariablen**

```python
# config.yaml erweitern
pbf_dams:
  base_url: ${PBF_DAMS_URL:http://localhost:8000}
  api_token: ${PBF_DAMS_TOKEN}
  timeout: 30
```

**2. Authentifizierung hinzufügen**

```python
class PBFDAMSClient:
    def __init__(self, base_url, api_token=None):
        self.session = requests.Session()
        if api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {api_token}'
            })
```

**3. Error Handling verbessern**

```python
try:
    data = client.get_regions()
except requests.ConnectionError:
    st.error("Server nicht erreichbar")
    st.stop()
except requests.Timeout:
    st.warning("Timeout - versuche es erneut")
    st.stop()
```

**4. Rate Limiting**

```python
import time

class PBFDAMSClient:
    def __init__(self, ...):
        self.last_request = 0
        self.min_interval = 0.1  # Max 10 req/sec
    
    def get_regions(self, ...):
        # Rate limiting
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        # Request...
        self.last_request = time.time()
```

## 📈 Monitoring

### Metriken tracken

```python
import streamlit as st

# In Streamlit Session State
if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0
    st.session_state.api_errors = 0

# Bei jedem Request
st.session_state.api_calls += 1

# Bei Errors
except Exception:
    st.session_state.api_errors += 1

# In Sidebar anzeigen
st.sidebar.metric("API Calls", st.session_state.api_calls)
st.sidebar.metric("API Errors", st.session_state.api_errors)
```

## 📝 Changelog

### Version 1.0 (2025-11-04)
- ✅ Initial Release
- ✅ PBFDAMSClient implementiert
- ✅ Streamlit Page "PBF-DAMS Export" erstellt
- ✅ JSON-Export funktioniert
- ⚠️ CSV-Export hat URL-Routing-Problem (siehe bekannte Probleme)

### Bekannte Probleme
- CSV-Download direkt von API nicht funktionsfähig
- Workaround: JSON in Streamlit laden, dann als CSV exportieren ✅

### Geplante Features
- [ ] OAuth-Authentifizierung
- [ ] Batch-Download mehrerer Fotos
- [ ] Visualisierung der Regions auf Fotos
- [ ] Integration mit Face-Recognition Pipeline
- [ ] Automatischer Sync PBF-DAMS ↔ Neo4j

---

**Entwickelt für:** Pina Bausch Foundation  
**Letzte Aktualisierung:** 4. November 2025  
**Maintainer:** Volker Enkrodt

