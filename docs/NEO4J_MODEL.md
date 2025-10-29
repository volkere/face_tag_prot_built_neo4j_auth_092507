 Neo4j Datenmodell für Gesichtserkennungs-Daten

 Übersicht

Dieses Dokument beschreibt das Neo4j-Datenmodell für die Speicherung und Abfrage von Gesichtserkennungs-Daten. Das Modell ermöglicht es, komplexe Beziehungen zwischen Bildern, Gesichtern, Personen und Standorten zu modellieren.

 Entitäten (Nodes)

 1. Image (Bild)
Repräsentiert ein einzelnes Bild mit seinen Metadaten.

Eigenschaften:
- `id`: Eindeutige UUID
- `filename`: Dateiname des Bildes
- `datetime`: Aufnahmedatum und -zeit
- `camera_make`: Kamerahersteller
- `camera_model`: Kameramodell
- `lens`: Objektiv
- `focal_length`: Brennweite
- `f_number`: Blende
- `iso`: ISO-Wert
- `exposure_time`: Belichtungszeit
- `image_width`: Bildbreite in Pixeln
- `image_height`: Bildhöhe in Pixeln
- `created_at`: Erstellungszeitstempel

Beispiel:
```cypher
CREATE (i:Image {
    id: "550e8400-e29b-41d4-a716-446655440000",
    filename: "IMG_2024_001.jpg",
    datetime: "2024-01-15T14:30:00",
    camera_make: "Canon",
    camera_model: "EOS R5",
    lens: "RF 24-70mm f/2.8L IS USM",
    focal_length: 50,
    f_number: 2.8,
    iso: 400,
    exposure_time: "1/125",
    image_width: 3840,
    image_height: 2160,
    created_at: datetime()
})
```

 2. Face (Gesicht)
Repräsentiert ein erkanntes Gesicht mit seinen Eigenschaften.

Eigenschaften:
- `id`: Eindeutige UUID
- `age`: Geschätztes Alter
- `gender`: Geschlecht (male/female)
- `emotion`: Erkannte Emotion (happy/neutral/sad/angry/surprised/unknown)
- `quality_score`: Qualitätsbewertung (0.0-1.0)
- `eye_status`: Augenstatus (open/closed/partially_open)
- `mouth_status`: Mundstatus (open/closed)
- `bbox_x1`: Bounding Box X1-Koordinate
- `bbox_y1`: Bounding Box Y1-Koordinate
- `bbox_x2`: Bounding Box X2-Koordinate
- `bbox_y2`: Bounding Box Y2-Koordinate
- `similarity`: Ähnlichkeit zu bekannter Person (0.0-1.0)
- `created_at`: Erstellungszeitstempel

Beispiel:
```cypher
CREATE (f:Face {
    id: "550e8400-e29b-41d4-a716-446655440001",
    age: 35,
    gender: "male",
    emotion: "happy",
    quality_score: 0.85,
    eye_status: "open",
    mouth_status: "open",
    bbox_x1: 100,
    bbox_y1: 150,
    bbox_x2: 200,
    bbox_y2: 250,
    similarity: 0.92,
    created_at: datetime()
})
```

 3. Person (Person)
Repräsentiert eine identifizierte Person.

Eigenschaften:
- `id`: Eindeutige UUID
- `name`: Name der Person
- `created_at`: Erstellungszeitstempel
- `first_seen`: Erstes Auftreten
- `last_seen`: Letztes Auftreten

Beispiel:
```cypher
CREATE (p:Person {
    id: "550e8400-e29b-41d4-a716-446655440002",
    name: "Max Mustermann",
    created_at: datetime(),
    first_seen: datetime(),
    last_seen: datetime()
})
```

 4. Location (Standort)
Repräsentiert einen geografischen Standort.

Eigenschaften:
- `id`: Eindeutige UUID
- `full_address`: Vollständige Adresse
- `country`: Land
- `state`: Bundesland/Staat
- `city`: Stadt
- `latitude`: Breitengrad
- `longitude`: Längengrad
- `created_at`: Erstellungszeitstempel

Beispiel:
```cypher
CREATE (l:Location {
    id: "550e8400-e29b-41d4-a716-446655440003",
    full_address: "Unter den Linden 1, 10117 Berlin, Deutschland",
    country: "Deutschland",
    state: "Berlin",
    city: "Berlin",
    latitude: 52.5170365,
    longitude: 13.3888599,
    created_at: datetime()
})
```

 Beziehungen (Relationships)

 1. APPEARS_IN
Verbindet ein Gesicht mit dem Bild, in dem es erscheint.

Richtung: `(Face)-[APPEARS_IN]->(Image)`

Eigenschaften:
- `created_at`: Erstellungszeitstempel

Beispiel:
```cypher
MATCH (f:Face {id: "face-id"}), (i:Image {id: "image-id"})
CREATE (f)-[r:APPEARS_IN {created_at: datetime()}]->(i)
```

 2. BELONGS_TO
Verbindet ein Gesicht mit einer identifizierten Person.

Richtung: `(Face)-[BELONGS_TO]->(Person)`

Eigenschaften:
- `created_at`: Erstellungszeitstempel

Beispiel:
```cypher
MATCH (f:Face {id: "face-id"}), (p:Person {id: "person-id"})
CREATE (f)-[r:BELONGS_TO {created_at: datetime()}]->(p)
```

 3. TAKEN_AT
Verbindet ein Bild mit dem Standort, an dem es aufgenommen wurde.

Richtung: `(Image)-[TAKEN_AT]->(Location)`

Eigenschaften:
- `created_at`: Erstellungszeitstempel

Beispiel:
```cypher
MATCH (i:Image {id: "image-id"}), (l:Location {id: "location-id"})
CREATE (i)-[r:TAKEN_AT {created_at: datetime()}]->(l)
```

 Constraints und Indizes

 Constraints (Eindeutigkeit)
```cypher
CREATE CONSTRAINT image_id_unique FOR (i:Image) REQUIRE i.id IS UNIQUE
CREATE CONSTRAINT person_id_unique FOR (p:Person) REQUIRE p.id IS UNIQUE
CREATE CONSTRAINT face_id_unique FOR (f:Face) REQUIRE f.id IS UNIQUE
CREATE CONSTRAINT location_id_unique FOR (l:Location) REQUIRE l.id IS UNIQUE
```

 Indizes (Performance)
```cypher
CREATE INDEX image_filename FOR (i:Image) ON (i.filename)
CREATE INDEX person_name FOR (p:Person) ON (p.name)
CREATE INDEX face_quality FOR (f:Face) ON (f.quality_score)
CREATE INDEX face_emotion FOR (f:Face) ON (f.emotion)
CREATE INDEX face_age FOR (f:Face) ON (f.age)
CREATE INDEX face_gender FOR (f:Face) ON (f.gender)
CREATE INDEX location_country FOR (l:Location) ON (l.country)
CREATE INDEX image_datetime FOR (i:Image) ON (i.datetime)
```

 Beispiel-Abfragen

 1. Alle Gesichter einer Person finden
```cypher
MATCH (p:Person {name: "Max Mustermann"})-[:BELONGS_TO]-(f:Face)-[:APPEARS_IN]-(i:Image)
RETURN f, i, p
ORDER BY i.datetime DESC
```

 2. Alle Gesichter mit bestimmter Emotion finden
```cypher
MATCH (f:Face {emotion: "happy"})-[:APPEARS_IN]-(i:Image)
OPTIONAL MATCH (f)-[:BELONGS_TO]-(p:Person)
RETURN f, i, p
ORDER BY f.quality_score DESC
```

 3. Alle Gesichter an einem bestimmten Standort finden
```cypher
MATCH (f:Face)-[:APPEARS_IN]-(i:Image)-[:TAKEN_AT]-(l:Location)
WHERE l.country = "Deutschland" AND l.city = "Berlin"
OPTIONAL MATCH (f)-[:BELONGS_TO]-(p:Person)
RETURN f, i, l, p
ORDER BY i.datetime DESC
```

 4. Statistiken abrufen
```cypher
// Gesamtanzahl der Bilder
MATCH (i:Image) RETURN count(i) as total_images

// Emotionsverteilung
MATCH (f:Face) RETURN f.emotion as emotion, count(f) as count

// Geschlechtsverteilung
MATCH (f:Face) RETURN f.gender as gender, count(f) as count

// Qualitätsstatistiken
MATCH (f:Face) 
RETURN avg(f.quality_score) as avg_quality, 
       min(f.quality_score) as min_quality, 
       max(f.quality_score) as max_quality
```

 5. Komplexe Abfrage: Personen mit hoher Gesichtsqualität
```cypher
MATCH (p:Person)-[:BELONGS_TO]-(f:Face)
WHERE f.quality_score > 0.8
WITH p, collect(f) as faces, avg(f.quality_score) as avg_quality
RETURN p.name, count(faces) as face_count, avg_quality
ORDER BY avg_quality DESC
```

 Datenmodell-Diagramm

```
    APPEARS_IN        TAKEN_AT    
    Face           Image        Location   
                                                                          
 - id                           - id                          - id        
 - age                          - filename                    - country   
 - gender                       - datetime                    - city      
 - emotion                      - camera_                    - latitude  
 - quality                      - image_                     - longitude 
 - bbox_                                                                 
 - similarity                                                             
                                   
       
        BELONGS_TO
       

   Person    
             
 - id        
 - name      
 - first_seen
 - last_seen 

```

 Vorteile des Neo4j-Modells

1. Flexibilität: Einfache Erweiterung um neue Entitäten und Beziehungen
2. Performance: Optimierte Abfragen für Graph-Traversierung
3. Skalierbarkeit: Effiziente Speicherung und Abfrage großer Datenmengen
4. Komplexe Abfragen: Natürliche Modellierung von Beziehungen zwischen Entitäten
5. Visualisierung: Einfache Darstellung von Beziehungen in Graph-Form

 Migration und Wartung

 Datenbank leeren
```cypher
MATCH (n) DETACH DELETE n
```

 Backup erstellen
```bash
neo4j-admin dump --database=neo4j --to=/path/to/backup.dump
```

 Backup wiederherstellen
```bash
neo4j-admin load --database=neo4j --from=/path/to/backup.dump
```
