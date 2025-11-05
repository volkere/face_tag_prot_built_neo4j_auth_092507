# 🔄 Datenfluss: PBF-DAMS ↔ PBA_Tagg

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Benutzer Interface                           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Streamlit App (PBA_Tagg)          Port: 8501                 │ │
│  │  http://localhost:8501                                        │ │
│  │                                                               │ │
│  │  Pages:                                                       │ │
│  │  ├─ 0_Enroll.py          (Face Recognition Training)         │ │
│  │  ├─ 1_Annotate.py        (Manuelle Annotation)               │ │
│  │  ├─ 2_Analyze.py         (Bild-Analyse)                      │ │
│  │  ├─ 3_Train.py           (Modell-Training)                   │ │
│  │  ├─ 4_Neo4j.py           (Graph-DB Integration)              │ │
│  │  ├─ 5_Neo4j_Browser.py   (Graph-Visualisierung)             │ │
│  │  └─ 6_PBF_DAMS_Export.py ◄── NEU! (Regions-Export)          │ │
│  │                                                               │ │
│  │  ┌──────────────────────────────────────────────┐            │ │
│  │  │  Suchmaske                                   │            │ │
│  │  │  ├─ Filter nach Foto                         │            │ │
│  │  │  ├─ Filter nach Person                       │            │ │
│  │  │  ├─ Filter nach Optionen                     │            │ │
│  │  │  └─ "Daten abrufen" Button                   │            │ │
│  │  └──────────────────────────────────────────────┘            │ │
│  │                       │                                       │ │
│  │                       │ HTTP GET Request                      │ │
│  │                       │ (via app/pbf_dams_client.py)         │ │
│  │                       ▼                                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ REST API Call
                          │ GET /api/v1/exports/image-regions/
                          │ ?photo=...&person=...
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PBF-DAMS Backend                                 │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Django App (PBF-DAMS)            Port: 8000                  │ │
│  │  http://localhost:8000                                        │ │
│  │                                                               │ │
│  │  API Endpoints:                                               │ │
│  │  ├─ /api/v1/content/photo/{id}    (Einzelne Fotos)          │ │
│  │  ├─ /api/v1/content/person/{id}   (Einzelne Personen)       │ │
│  │  └─ /api/v1/exports/image-regions/ ◄── NEU! (Bulk-Export)   │ │
│  │                                                               │ │
│  │  ┌──────────────────────────────────────────────┐            │ │
│  │  │  ImageRegionsExportView                      │            │ │
│  │  │  (api_frontend/views/exports/)               │            │ │
│  │  │                                               │            │ │
│  │  │  1. Filter anwenden                          │            │ │
│  │  │  2. ImageRegionTag queryset erstellen        │            │ │
│  │  │  3. Serialisieren                            │            │ │
│  │  │  4. JSON Response                            │            │ │
│  │  └──────────────────────────────────────────────┘            │ │
│  │                       │                                       │ │
│  │                       ▼                                       │ │
│  │  ┌──────────────────────────────────────────────┐            │ │
│  │  │  PostgreSQL Datenbank                        │            │ │
│  │  │                                               │            │ │
│  │  │  Tabellen:                                   │            │ │
│  │  │  ├─ resources_imageregiontag                 │            │ │
│  │  │  ├─ resources_digitalphoto                   │            │ │
│  │  │  ├─ resources_person                         │            │ │
│  │  │  └─ resources_photo                          │            │ │
│  │  └──────────────────────────────────────────────┘            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ JSON Response
                          │ {"count": 10, "regions": [...]}
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Streamlit Verarbeitung                           │
│                                                                     │
│  1. Response empfangen                                              │
│  2. JSON parsen                                                     │
│  3. In Pandas DataFrame konvertieren                                │
│  4. In Tabelle anzeigen                                             │
│  5. Export-Optionen anbieten:                                       │
│     ├─ JSON-Download                                                │
│     └─ CSV-Download                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Datenfluss im Detail

### 1. Upload & Metadaten-Extraktion (PBF-DAMS)

```
Fotograf taggt Gesichter in Adobe Bridge
                ↓
        XMP-Metadaten werden in Bilddatei gespeichert
                ↓
        Foto wird in PBF-DAMS hochgeladen
                ↓
        Django DigitalPhoto.save() wird aufgerufen
                ↓
        update_image_regions() extrahiert XMP-Daten
                ↓
        ImageRegionTag-Objekte werden erstellt
                ↓
        In PostgreSQL gespeichert
```

### 2. Export-Anfrage (PBA_Tagg → PBF-DAMS)

```
Nutzer öffnet "PBF-DAMS Export" Page in Streamlit
                ↓
        Setzt Filter (optional): Foto, Person
                ↓
        Klickt "Daten abrufen"
                ↓
        Streamlit ruft PBFDAMSClient.get_regions()
                ↓
        HTTP GET zu /api/v1/exports/image-regions/
                ↓
        Django ImageRegionsExportView verarbeitet Request
                ↓
        Queryset wird gefiltert
                ↓
        ImageRegionTagSerializer serialisiert Daten
                ↓
        JSON Response zurück an Streamlit
```

### 3. Darstellung & Export (PBA_Tagg)

```
JSON Response empfangen
                ↓
        Pandas DataFrame erstellen
                ↓
        Tabelle in Streamlit anzeigen
                ↓
        Nutzer kann:
        ├─ Daten durchsuchen
        ├─ Als JSON exportieren
        └─ Als CSV exportieren
```

## 🗄️ Datenbank-Schema

### PBF-DAMS (PostgreSQL)

```sql
resources_imageregiontag
├─ id (PK)
├─ digitized_image_item_id (FK → resources_digitalphoto)
├─ person_relation_id (FK → resources_person)
├─ person (VARCHAR) - Identifier als String
├─ x (FLOAT) - Relative Position
├─ y (FLOAT)
├─ width (FLOAT)
├─ height (FLOAT)
├─ rotation (FLOAT)
├─ ref_width (INT) - Original-Bildbreite
├─ ref_height (INT)
├─ type (VARCHAR) - "FA" für Face
├─ created_at (TIMESTAMP)
└─ updated_at (TIMESTAMP)

resources_person
├─ id (PK)
├─ identifier (VARCHAR, UNIQUE) - z.B. "pina_bausch"
├─ label (VARCHAR) - z.B. "Pina Bausch"
├─ visibility (VARCHAR) - "PU" (public) oder "PR" (private)
└─ status (VARCHAR) - "AP" (approved) oder andere

resources_photo
├─ id (PK)
├─ identifier (VARCHAR, UNIQUE) - z.B. "macb_30035212_44"
└─ label (VARCHAR)
```

### PBA_Tagg (Neo4j) - Optional

Regions können auch in Neo4j importiert werden:

```cypher
// Person-Knoten
(:Person {identifier: "pina_bausch", name: "Pina Bausch"})

// Foto-Knoten  
(:Photo {identifier: "macb_30035212_44", label: "Macbeth Foto"})

// Relation mit Koordinaten
(:Person)-[:TAGGED_IN {x: 0.5, y: 0.5, width: 0.1, height: 0.1}]->(:Photo)
```

## 🔌 API-Schnittstelle

### Request

```http
GET /api/v1/exports/image-regions/?person=pina_bausch HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Response

```json
{
  "count": 15,
  "export_format": "json",
  "regions": [
    {
      "type": {
        "name": "imageregiontag",
        "label": "Image Region Tag"
      },
      "x": 0.5,
      "y": 0.5,
      "width": 0.1,
      "height": 0.1,
      "rotation": 0.0,
      "person": {
        "identifier": "pina_bausch",
        "label": "Pina Bausch",
        "type": {
          "name": "person",
          "label": "Person"
        },
        "url": "/person/pina_bausch"
      },
      "photo_identifier": "macb_30035212_44",
      "photo_label": "Macbeth, Aufführung 1985",
      "ref_width": 5632,
      "ref_height": 3755
    },
    // ... weitere 14 Regions
  ]
}
```

## 🎨 Streamlit UI-Komponenten

### Suchmaske
```python
# Filter-Checkboxen
search_by_photo = st.checkbox("Nach Foto filtern")
search_by_person = st.checkbox("Nach Person filtern")

# Dropdown-Listen
selected_person = st.selectbox("Person wählen:", persons_list)

# Such-Button
if st.button("🚀 Daten abrufen"):
    data = client.get_regions(person=selected_person)
```

### Ergebnis-Tabelle
```python
# Pandas DataFrame
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, height=400)
```

### Download-Buttons
```python
# JSON-Download
st.download_button(
    label="📥 Als JSON herunterladen",
    data=json_str,
    file_name="regions.json",
    mime="application/json"
)

# CSV-Download
st.download_button(
    label="📥 Als CSV herunterladen",
    data=csv_str,
    file_name="regions.csv",
    mime="text/csv"
)
```

## 🧩 Komponenten-Diagramm

```
PBA_Tagg (Streamlit)
│
├── pages/
│   └── 6_PBF_DAMS_Export.py ──┐
│                               │ nutzt
├── app/                        │
│   ├── pbf_dams_client.py ◄───┘
│   │   └── PBFDAMSClient
│   │       ├── get_regions()
│   │       ├── get_photos_list()
│   │       ├── get_persons_list()
│   │       └── test_connection()
│   │
│   └── RegionData (Helper-Klasse)
│       ├── person_name
│       ├── coordinates
│       └── dimensions
│
└── requirements.txt
    └── requests>=2.31.0 (NEU!)
```

```
PBF-DAMS (Django)
│
├── api_frontend/
│   ├── views/exports/
│   │   └── image_regions_export_view.py
│   │       └── ImageRegionsExportView
│   │           ├── get() - HTTP GET Handler
│   │           ├── _export_json()
│   │           └── _export_csv()
│   │
│   ├── serializers/content/
│   │   └── image_region_tag_serializer.py
│   │       └── ImageRegionTagSerializer
│   │
│   └── urls.py
│       └── path("exports/image-regions/", ...)
│
└── resources/
    ├── models/items/digitized/
    │   └── region_tag.py
    │       └── ImageRegionTag (Model)
    │
    └── utils/parsers/
        └── image.py
            └── update_image_regions()
                └── _extract_image_regions_to_dict()
```

## 🔀 Workflow-Beispiel: Foto-Analyse

```
1. Nutzer in Streamlit
   └─> Wählt "Nach Person filtern"
   └─> Lädt Personen-Liste
   
2. Streamlit → Django API
   └─> GET /api/v1/exports/image-regions/
   └─> Alle Regions werden abgerufen
   
3. Django
   └─> Queryset: ImageRegionTag.objects.all()
   └─> Filter nach PUBLIC + APPROVED
   └─> Serialisiert zu JSON
   
4. Streamlit empfängt Response
   └─> {"count": 150, "regions": [...]}
   └─> Extrahiert unique Personen
   └─> Zeigt in Dropdown
   
5. Nutzer wählt "Pina Bausch"
   
6. Streamlit → Django API
   └─> GET /api/v1/exports/image-regions/?person=pina_bausch
   
7. Django
   └─> Queryset.filter(person_relation__identifier="pina_bausch")
   └─> Findet z.B. 25 Regions
   └─> Serialisiert
   
8. Streamlit zeigt Ergebnisse
   └─> Tabelle mit 25 Zeilen
   └─> Jede Zeile = ein Foto mit Pina Bausch
   └─> Koordinaten, wo sie auf dem Foto ist
   
9. Nutzer exportiert
   └─> Klickt "Als CSV herunterladen"
   └─> Bekommt regions_20251104_173045.csv
```

## 🎭 Anwendungsfall: Tänzer-Recherche

**Scenario:** Forscher will alle Auftritte von Dominique Mercy dokumentieren

```
Step 1: In Streamlit PBF-DAMS Export
        └─> Person-Filter: "dominique_mercy"
        └─> Daten abrufen
        
Step 2: Ergebnisse
        └─> 180 Regions gefunden
        └─> 95 unique Fotos
        └─> Fotos von 1973-2009
        
Step 3: Export als CSV
        └─> Öffnen in Excel
        └─> Sortieren nach Foto
        └─> Gruppieren nach Jahr
        
Step 4: Analyse
        └─> Welche Stücke? (aus Foto-Identifiern)
        └─> Welche Partner? (andere Personen auf selben Fotos)
        └─> Zeitliche Entwicklung
        
Step 5: Neo4j Import (optional)
        └─> Visualisiere Netzwerk
        └─> Dominique ─[PERFORMED_WITH]→ andere Tänzer
```

## 📈 Performance & Skalierung

### Kleine Datasets (<1000 Regions)
```
✅ Einfach: Alle Daten auf einmal laden
✅ Schnell: <1 Sekunde
✅ Übersichtlich: In einer Tabelle
```

### Mittlere Datasets (1000-10000 Regions)
```
⚠️ Filter verwenden: Nach Foto oder Person
⚠️ Pagination erwägen: Nur erste 100 zeigen
✅ Funktioniert gut
```

### Große Datasets (>10000 Regions)
```
❌ Nicht alle auf einmal laden
✅ Immer Filter verwenden
✅ Batch-Processing implementieren
✅ Caching in Streamlit nutzen
```

## 🔐 Sicherheit

### Aktuell (Development)
```
PBF-DAMS API: Kein Auth erforderlich ⚠️
Streamlit: Einfaches Passwort (admin123)
Datenfilter: Nur PUBLIC + APPROVED Personen
```

### Produktion (Empfohlen)
```
PBF-DAMS API: OAuth2-Token ✅
Streamlit: User-Management ✅
HTTPS: SSL-Verschlüsselung ✅
Rate Limiting: Max Requests/Minute ✅
```

## 🛠️ Debugging

### Streamlit Logging

```python
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)

st.write("Debug Info:")
st.write(f"Client URL: {client.base_url}")
st.write(f"Filter: photo={photo_id}, person={person_id}")
```

### Django Logging

```bash
# Terminal wo Django läuft zeigt Requests:
[03/Nov/2025 17:30:45] "GET /api/v1/exports/image-regions/?person=pina_bausch HTTP/1.1" 200 2048
```

### Network Inspection

```bash
# In separatem Terminal
tcpdump -i lo0 -A -s 0 'port 8000'
```

---

**Diese Integration ermöglicht es, die reichhaltigen Metadaten aus PBF-DAMS in der Streamlit App zu nutzen und für Analysen, Forschung und Qualitätskontrolle zu exportieren! 🎯**

