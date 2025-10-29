 Embeddings Verwendung - Komplette Anleitung

 Wie und wo verwende ich die Embeddings?

 Kurzfassung:

1. Enroll → `embeddings.pkl` erstellen (Personen-Datenbank)
2. Annotate → `embeddings.pkl` hochladen → Gesichter identifizieren
3. Ergebnisse verwenden → Filtern, Statistiken, Visualisierungen

---

 Detaillierte Anleitung:

 Schritt 1: Embeddings erstellen (Enroll)

Seite: Enroll

Option A - Galerie-ZIP:
- Erstelle eine ZIP-Datei mit Ordnern pro Person
- Lade die ZIP in "Galerie-ZIP hochladen" hoch
- Die App erstellt `embeddings.pkl` automatisch
- Download die `embeddings.pkl` Datei

Option B - Manuell:
- Gib den Namen ein → Lade Bilder hoch → Klicke "Hinzufügen"
- Wiederhole für weitere Personen
- Download die `embeddings.pkl` am Ende

Ergebnis: `embeddings.pkl` auf Ihrem Computer

---

 Schritt 2: Embeddings verwenden (Annotate)

Seite: Annotate

Wie:
1. In der Sidebar unter "Dateien":
   - "Embeddings DB (embeddings.pkl)" → Lade deine `embeddings.pkl` hoch
2. Identity Threshold anpassen:
   - 0.55 = Standard (empfohlen)
   - 0.7-0.9 = Sehr sicher (weniger Treffer)
   - 0.4-0.5 = Mehr Treffer (kann Fehler machen)
3. Lade deine Bilder hoch
4. Klicke auf "Analyse starten" bzw. automatische Verarbeitung

Was passiert:
- Die App vergleicht jedes erkannte Gesicht mit den Embeddings
- Wenn ähnlich → zeigt Name und Ähnlichkeit (z.B. "Thomas 0.87")
- Wenn nicht ähnlich → zeigt "Unbekannt"

Beispiel:
```
Person: "Thomas" → Embedding Ähnlichkeit: 0.87
Person: "Maria" → Embedding Ähnlichkeit: 0.92
Person: "Unbekannt" → Embedding Ähnlichkeit: 0.42
```

Die Namen erscheinen auf den Bildern und in der Tabelle!

---

 Schritt 3: Ergebnisse verwenden

A) Ergebnisse speichern:
- Nach der Verarbeitung: "Download results JSON" klicken
- Speichere als `results.json`

B) Ergebnisse analysieren:
- Seite: Analyze
  - Lade `results.json` hoch
  - Sehe Statistiken, Altersverteilung, Geschlechtsverteilung, Standort-Karten

C) In Neo4j importieren:
- Seite: Neo4j
  - Lade `results.json` hoch
  - Visualisiere als Graph
  - Führe komplexe Abfragen aus

---

 Praktisches Beispiel:

 Beispiel 1: Familien-Archiv

```
1. Enroll: Registriere alle Familienmitglieder
   - Oma (20 Fotos)
   - Opa (15 Fotos)
   - Mama (25 Fotos)
   - Papa (30 Fotos)
   
2. Annotate: Analysiere alte Fotos
   - Upload: embeddings.pkl
   - Upload: 100 alte Familiengalerie-Fotos
   - Ergebnis: Alle Gesichter werden automatisch erkannt und benannt!
   
3. Analyze: Sehe Statistiken
   - Wer ist am häufigsten auf den Fotos?
   - Altersverteilung über die Jahre
```

 Beispiel 2: Event-Archiv

```
1. Enroll: Registriere Gäste
   - Person 1 (10 Fotos)
   - Person 2 (12 Fotos)
   - Person 3 (8 Fotos)
   
2. Annotate: Analysiere Event-Fotos
   - Upload: embeddings.pkl
   - Upload: 50 Event-Fotos
   - Ergebnis: Automatische Gästeliste mit Standort und Zeit
   
3. Neo4j: Visualisiere Zusammenhänge
   - Wer war mit wem zusammen?
   - Zeitliche Abfolge der Gesichter
```

---

 Wo befinden sich die Dateien?

```
Deine Dateien:
 embeddings.pkl          ← Personen-Datenbank (von Enroll)
 results.json             ← Analyse-Ergebnisse (von Annotate)
 galerie.zip             ← Ursprungsdaten für Embeddings
 analyse_bilder/
     foto1.jpg
     foto2.jpg
     ...
```

---

 Wichtig:

 Embeddings einmal erstellen → können immer wieder verwendet werden

 Mehr Fotos pro Person → bessere Erkennung

 Gute Bildqualität → bessere Embeddings

 Threshold anpassen → niedrig = mehr Treffer, hoch = sicherer

 Workflow-Zusammenfassung:

```
Enroll → embeddings.pkl erstellen → Download
         ↓
Annotate → embeddings.pkl hochladen → Bilder analysieren → results.json downloaden
         ↓
Analyze/Neo4j → results.json hochladen → Statistiken/Visualisierungen
```

