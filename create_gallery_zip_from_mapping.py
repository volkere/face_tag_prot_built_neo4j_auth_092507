#!/usr/bin/env python3
"""
Erstellt eine Galerie-ZIP-Datei aus einer PBF-DAMS Zuordnungs-JSON.

Die ZIP-Struktur entspricht den Anforderungen der Enroll-Seite:
- PersonA/*.jpg
- PersonB/*.jpg
- etc.

Für jede Region wird das Gesicht aus dem Bild ausgeschnitten und in den entsprechenden Personen-Ordner kopiert.
"""
import json
import os
import zipfile
import shutil
import tempfile
import cv2
import numpy as np
from pathlib import Path

def clean_person_name(name):
    """Bereinigt Personennamen (entfernt ':' am Anfang, etc.)"""
    if not name:
        return None
    # Entferne führenden Doppelpunkt
    clean = name.lstrip(':')
    # Ersetze ungültige Zeichen für Dateinamen
    clean = clean.replace('/', '_').replace('\\', '_').replace(':', '_')
    clean = clean.replace('*', '_').replace('?', '_').replace('"', '_')
    clean = clean.replace('<', '_').replace('>', '_').replace('|', '_')
    return clean.strip()

def extract_face_region(img, x_abs, y_abs, width_px, height_px, padding=0.1):
    """Schneidet eine Gesichtsregion aus einem Bild aus"""
    h, w = img.shape[:2]
    
    # Koordinaten in Integer umwandeln
    x1 = int(x_abs)
    y1 = int(y_abs)
    x2 = int(x_abs + width_px)
    y2 = int(y_abs + height_px)
    
    # Padding hinzufügen (optional)
    if padding > 0:
        padding_x = int(width_px * padding)
        padding_y = int(height_px * padding)
        x1 = max(0, x1 - padding_x)
        y1 = max(0, y1 - padding_y)
        x2 = min(w, x2 + padding_x)
        y2 = min(h, y2 + padding_y)
    
    # Grenzen prüfen
    x1 = max(0, min(x1, w-1))
    y1 = max(0, min(y1, h-1))
    x2 = max(x1+1, min(x2, w))
    y2 = max(y1+1, min(y2, h))
    
    # Region ausschneiden
    face_crop = img[y1:y2, x1:x2]
    
    return face_crop, (x1, y1, x2, y2)

def create_gallery_zip_from_mapping(json_path, output_zip_path, extract_faces=True, min_face_size=30):
    """
    Erstellt eine Galerie-ZIP aus einer PBF-DAMS Zuordnungs-JSON.
    
    Args:
        json_path: Pfad zur JSON-Datei
        output_zip_path: Pfad für die Ausgabe-ZIP-Datei
        extract_faces: Wenn True, schneidet Gesichter aus. Wenn False, kopiert ganze Bilder.
        min_face_size: Minimale Gesichtsgröße in Pixel
    """
    
    print(f"Lade JSON-Datei: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Statistiken
    total_images = len(data) if isinstance(data, list) else 0
    images_with_regions = 0
    total_regions = 0
    unique_persons = set()
    processed_images = {}
    skipped_regions = 0
    
    # Sammle alle Personen und ihre Regionen
    person_regions = {}  # person_name -> [(image_path, region_data, bbox), ...]
    
    print(f"\nAnalysiere {total_images} Bilder...")
    
    for item in data:
        if not isinstance(item, dict) or 'regions' not in item:
            continue
        
        image_path = item.get('image')
        regions = item.get('regions', [])
        
        if not image_path or not isinstance(regions, list) or len(regions) == 0:
            continue
        
        images_with_regions += 1
        
        # Prüfe ob Bild existiert
        if not os.path.exists(image_path):
            print(f"  Warnung: Bild nicht gefunden: {image_path}")
            continue
        
        for region in regions:
            if not isinstance(region, dict):
                continue
            
            person_name = region.get('name')
            if not person_name:
                continue
            
            # Name bereinigen
            clean_name = clean_person_name(person_name)
            if not clean_name:
                continue
            
            unique_persons.add(clean_name)
            total_regions += 1
            
            # Prüfe Regionsgröße
            width_px = region.get('width_px')
            height_px = region.get('height_px')
            
            if width_px and height_px:
                if width_px < min_face_size or height_px < min_face_size:
                    skipped_regions += 1
                    continue
            
            # Region zur Liste hinzufügen
            if clean_name not in person_regions:
                person_regions[clean_name] = []
            
            person_regions[clean_name].append({
                'image_path': image_path,
                'region': region,
                'original_name': person_name
            })
    
    print(f"\nStatistiken:")
    print(f"  - Bilder mit Regionen: {images_with_regions}")
    print(f"  - Regionen gesamt: {total_regions}")
    print(f"  - Einzigartige Personen: {len(unique_persons)}")
    print(f"  - Übersprungene Regionen (zu klein): {skipped_regions}")
    
    if len(unique_persons) == 0:
        print("\n❌ Keine Personen gefunden! Beende.")
        return False
    
    # Zeige Personen-Übersicht
    print(f"\nGefundene Personen ({len(unique_persons)}):")
    for person_name in sorted(unique_persons):
        region_count = len(person_regions[person_name])
        print(f"  - {person_name}: {region_count} Region(en)")
    
    # Erstelle temporäres Verzeichnis
    print(f"\nErstelle temporäres Verzeichnis...")
    with tempfile.TemporaryDirectory() as tmpdir:
        
        # Verarbeite jede Person
        for person_name, regions_list in person_regions.items():
            person_dir = os.path.join(tmpdir, person_name)
            os.makedirs(person_dir, exist_ok=True)
            
            print(f"\nVerarbeite {person_name} ({len(regions_list)} Regionen)...")
            
            for idx, region_data in enumerate(regions_list):
                image_path = region_data['image_path']
                region = region_data['region']
                
                try:
                    # Bild laden
                    img = cv2.imread(image_path)
                    if img is None:
                        print(f"  ⚠️  Konnte Bild nicht laden: {image_path}")
                        continue
                    
                    # Dateiname für das Gesicht
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    face_filename = f"{base_name}_{idx+1:03d}.jpg"
                    face_path = os.path.join(person_dir, face_filename)
                    
                    if extract_faces:
                        # Gesicht aus Region ausschneiden
                        x_abs = region.get('x_abs')
                        y_abs = region.get('y_abs')
                        width_px = region.get('width_px')
                        height_px = region.get('height_px')
                        
                        if None in [x_abs, y_abs, width_px, height_px]:
                            # Falls Koordinaten fehlen, kopiere das ganze Bild
                            shutil.copy2(image_path, face_path)
                            print(f"  ℹ️  Ganze Bild kopiert (Koordinaten fehlen): {face_filename}")
                        else:
                            # Gesicht ausschneiden
                            face_crop, bbox = extract_face_region(
                                img, x_abs, y_abs, width_px, height_px, padding=0.1
                            )
                            
                            if face_crop.size > 0:
                                crop_h, crop_w = face_crop.shape[:2]
                                # Überspringe zu kleine Crops (weniger als 50x50 Pixel)
                                if crop_h < 50 or crop_w < 50:
                                    print(f"  ⚠️  Gesicht zu klein ({crop_w}x{crop_h}px): {face_filename}. Überspringe.")
                                    continue
                                
                                cv2.imwrite(face_path, face_crop)
                                print(f"  ✓ Gesicht extrahiert: {face_filename} ({crop_w}x{crop_h}px)")
                            else:
                                print(f"  ⚠️  Leere Region: {face_filename}")
                                # Fallback: Kopiere ganzes Bild
                                shutil.copy2(image_path, face_path)
                    else:
                        # Kopiere das ganze Bild
                        shutil.copy2(image_path, face_path)
                        print(f"  ✓ Bild kopiert: {face_filename}")
                
                except Exception as e:
                    print(f"  ❌ Fehler bei {image_path}: {e}")
                    continue
        
        # Erstelle ZIP-Datei
        print(f"\nErstelle ZIP-Datei: {output_zip_path}")
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Relativer Pfad innerhalb der ZIP
                    arcname = os.path.relpath(file_path, tmpdir)
                    zipf.write(file_path, arcname)
                    print(f"  + {arcname}")
        
        # Statistiken nach Verarbeitung
        print(f"\n✅ ZIP-Datei erstellt: {output_zip_path}")
        
        # Prüfe was in der ZIP ist
        with zipfile.ZipFile(output_zip_path, 'r') as zipf:
            file_list = zipf.namelist()
            persons_in_zip = set()
            total_files = 0
            
            for file_path in file_list:
                if '/' in file_path:
                    person_name = file_path.split('/')[0]
                    persons_in_zip.add(person_name)
                    total_files += 1
            
            print(f"\nZIP-Inhalt:")
            print(f"  - Personen: {len(persons_in_zip)}")
            print(f"  - Dateien gesamt: {total_files}")
            
            for person_name in sorted(persons_in_zip):
                person_files = [f for f in file_list if f.startswith(f"{person_name}/")]
                print(f"  - {person_name}: {len(person_files)} Datei(en)")
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Erstellt eine Galerie-ZIP aus einer PBF-DAMS Zuordnungs-JSON"
    )
    parser.add_argument(
        'json_path',
        help='Pfad zur PBF-DAMS JSON-Datei'
    )
    parser.add_argument(
        '-o', '--output',
        help='Ausgabe-ZIP-Datei (Standard: gallery_from_mapping.zip)',
        default='gallery_from_mapping.zip'
    )
    parser.add_argument(
        '--extract-faces',
        action='store_true',
        help='Schneide Gesichter aus (Standard: True)',
        default=True
    )
    parser.add_argument(
        '--copy-full-images',
        action='store_true',
        help='Kopiere ganze Bilder statt Gesichter auszuschneiden',
        default=False
    )
    parser.add_argument(
        '--min-face-size',
        type=int,
        default=30,
        help='Minimale Gesichtsgröße in Pixel (Standard: 30)'
    )
    
    args = parser.parse_args()
    
    extract_faces = not args.copy_full_images
    
    success = create_gallery_zip_from_mapping(
        json_path=args.json_path,
        output_zip_path=args.output,
        extract_faces=extract_faces,
        min_face_size=args.min_face_size
    )
    
    if success:
        print(f"\n🎉 Fertig! ZIP-Datei: {args.output}")
        print(f"\nSie können diese ZIP-Datei jetzt in der Enroll-Seite verwenden:")
        print(f"  Tab: 'Galerie-ZIP hochladen'")
        print(f"  Datei: {args.output}")
    else:
        print("\n❌ Fehler beim Erstellen der ZIP-Datei.")
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())

