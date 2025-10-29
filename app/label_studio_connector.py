"""
Label Studio Connector für Face Tagging App
Ermöglicht Export/Import von Annotationsdaten zu/von Label Studio
"""

import json
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st

try:
    from label_studio_sdk import Client
    LABEL_STUDIO_AVAILABLE = True
except ImportError:
    LABEL_STUDIO_AVAILABLE = False
    st.warning("Label Studio SDK nicht verfügbar. Installieren Sie: pip install label-studio-sdk")

class LabelStudioConnector:
    """Connector für Label Studio Integration"""
    
    def __init__(self, url: str = "http://localhost:8080", api_key: str = None):
        self.url = url
        self.api_key = api_key
        self.client = None
        
        if LABEL_STUDIO_AVAILABLE and api_key:
            try:
                self.client = Client(url=url, api_key=api_key)
                self.client.check_connection()
            except Exception as e:
                st.error(f"Label Studio Verbindung fehlgeschlagen: {e}")
                self.client = None
    
    def is_connected(self) -> bool:
        """Prüft ob Label Studio erreichbar ist"""
        if not self.client:
            return False
        try:
            self.client.check_connection()
            return True
        except:
            return False
    
    def convert_to_labelstudio_format(self, face_data: List[Dict]) -> List[Dict]:
        """Konvertiert Face Tagging Daten zu Label Studio Format"""
        labelstudio_data = []
        
        for item in face_data:
            # Basis-Item für Label Studio
            ls_item = {
                "data": {
                    "image": f"/data/local-files/?d={item['image']}"
                },
                "annotations": [],
                "predictions": []
            }
            
            # Personen als Annotations
            persons = item.get('persons', [])
            for person_idx, person in enumerate(persons):
                bbox = person.get('bbox', [0, 0, 100, 100])
                x1, y1, x2, y2 = bbox
                
                # Bounding Box in Label Studio Format (Prozent der Bildgröße)
                # Für jetzt verwenden wir feste Werte, da wir die Bildgröße nicht kennen
                width_percent = 20.0  # 20% der Bildbreite
                height_percent = 30.0  # 30% der Bildhöhe
                x_percent = 40.0  # 40% von links
                y_percent = 30.0  # 30% von oben
                
                # Label Studio Bounding Box Format
                annotation = {
                    "result": [
                        {
                            "value": {
                                "x": x_percent,
                                "y": y_percent,
                                "width": width_percent,
                                "height": height_percent,
                                "rotation": 0,
                                "rectanglelabels": ["face"]
                            },
                            "id": f"face_{person_idx}",
                            "from_name": "label",
                            "to_name": "image",
                            "type": "rectanglelabels"
                        }
                    ],
                    "ground_truth": False,
                    "model_version": "face_tagging_v1",
                    "score": person.get('prob', 0.5)
                }
                
                # Zusätzliche Metadaten als Text
                metadata_text = f"Age: {person.get('age', 'N/A')}, "
                metadata_text += f"Gender: {person.get('gender', 'N/A')}, "
                metadata_text += f"Quality: {person.get('quality_score', 0.5):.2f}"
                
                annotation["result"].append({
                    "value": {
                        "text": [metadata_text]
                    },
                    "id": f"text_{person_idx}",
                    "from_name": "text",
                    "to_name": "image",
                    "type": "textarea"
                })
                
                ls_item["annotations"].append(annotation)
            
            labelstudio_data.append(ls_item)
        
        return labelstudio_data
    
    def convert_from_labelstudio_format(self, ls_data: List[Dict]) -> List[Dict]:
        """Konvertiert Label Studio Daten zurück zu Face Tagging Format"""
        face_data = []
        
        for item in ls_data:
            # Bild-Name extrahieren
            image_path = item.get('data', {}).get('image', '')
            image_name = os.path.basename(image_path.split('=')[-1]) if '=' in image_path else 'unknown.jpg'
            
            # Personen aus Annotations extrahieren
            persons = []
            annotations = item.get('annotations', [])
            
            for annotation in annotations:
                results = annotation.get('result', [])
                
                # Bounding Box finden
                bbox_result = None
                text_result = None
                
                for result in results:
                    if result.get('type') == 'rectanglelabels':
                        bbox_result = result
                    elif result.get('type') == 'textarea':
                        text_result = result
                
                if bbox_result:
                    # Bounding Box konvertieren
                    value = bbox_result.get('value', {})
                    x = value.get('x', 0)
                    y = value.get('y', 0)
                    width = value.get('width', 100)
                    height = value.get('height', 100)
                    
                    # Zurück zu Pixel-Koordinaten (vereinfacht)
                    bbox = [int(x), int(y), int(x + width), int(y + height)]
                    
                    # Metadaten aus Text extrahieren
                    age = 25  # Standard
                    gender = 'unknown'
                    quality_score = 0.5
                    
                    if text_result:
                        text = text_result.get('value', {}).get('text', [''])[0]
                        # Einfache Text-Parsing
                        if 'Age:' in text:
                            try:
                                age_part = text.split('Age:')[1].split(',')[0].strip()
                                age = int(age_part)
                            except:
                                pass
                        
                        if 'Gender:' in text:
                            try:
                                gender_part = text.split('Gender:')[1].split(',')[0].strip()
                                gender = gender_part.lower()
                            except:
                                pass
                        
                        if 'Quality:' in text:
                            try:
                                quality_part = text.split('Quality:')[1].split(',')[0].strip()
                                quality_score = float(quality_part)
                            except:
                                pass
                    
                    person = {
                        "bbox": bbox,
                        "prob": annotation.get('score', 0.5),
                        "name": None,
                        "similarity": None,
                        "age": age,
                        "gender": gender,
                        "quality_score": quality_score,
                        "emotion": "unknown",
                        "eye_status": "unknown",
                        "mouth_status": "unknown"
                    }
                    persons.append(person)
            
            face_item = {
                "image": image_name,
                "metadata": {},
                "location": None,
                "persons": persons
            }
            face_data.append(face_item)
        
        return face_data
    
    def export_to_labelstudio(self, face_data: List[Dict], project_id: int) -> bool:
        """Exportiert Face Tagging Daten zu Label Studio"""
        if not self.client:
            st.error("Label Studio nicht verbunden")
            return False
        
        try:
            # Konvertieren zu Label Studio Format
            ls_data = self.convert_to_labelstudio_format(face_data)
            
            # Zu Label Studio hochladen
            project = self.client.get_project(project_id)
            
            # Zuerst Tasks erstellen, dann Annotations hinzufügen
            for item in ls_data:
                # Task erstellen
                task = project.create_task(
                    data=item['data']
                )
                
                # Annotation hinzufügen (falls vorhanden)
                if item.get('annotations'):
                    for annotation in item['annotations']:
                        project.create_annotation(
                            task_id=task.id,
                            result=annotation.get('result', []),
                            ground_truth=annotation.get('ground_truth', False),
                            model_version=annotation.get('model_version', 'face_tagging_v1'),
                            score=annotation.get('score', 0.5)
                        )
            
            st.success(f"Erfolgreich {len(ls_data)} Items zu Label Studio exportiert")
            return True
            
        except Exception as e:
            st.error(f"Export fehlgeschlagen: {e}")
            return False
    
    def import_from_labelstudio(self, project_id: int) -> List[Dict]:
        """Importiert annotierte Daten von Label Studio"""
        if not self.client:
            st.error("Label Studio nicht verbunden")
            return []
        
        try:
            project = self.client.get_project(project_id)
            tasks = project.get_tasks()
            
            # Konvertieren zu Face Tagging Format
            face_data = self.convert_from_labelstudio_format(tasks)
            
            st.success(f"Erfolgreich {len(face_data)} Items von Label Studio importiert")
            return face_data
            
        except Exception as e:
            st.error(f"Import fehlgeschlagen: {e}")
            return []
    
    def create_face_tagging_project(self, title: str = "Face Tagging Project") -> Optional[int]:
        """Erstellt ein neues Label Studio Projekt für Face Tagging"""
        if not self.client:
            st.error("Label Studio nicht verbunden")
            return None
        
        try:
            # Label Studio Konfiguration für Face Tagging
            config = """
<View>
  <Image name="image" value="$image" zoom="true"/>
  <RectangleLabels name="label" toName="image">
    <Label value="face" background="red"/>
  </RectangleLabels>
  <TextArea name="text" toName="image" placeholder="Metadaten: Age: 25, Gender: male, Quality: 0.8"/>
</View>
"""
            
            project = self.client.create_project(
                title=title,
                label_config=config
            )
            
            st.success(f"Label Studio Projekt erstellt: {project.id}")
            return project.id
            
        except Exception as e:
            st.error(f"Projekt-Erstellung fehlgeschlagen: {e}")
            return None
    
    def get_projects(self) -> List[Dict]:
        """Gibt alle verfügbaren Label Studio Projekte zurück"""
        if not self.client:
            return []
        
        try:
            projects = self.client.get_projects()
            return [
                {
                    "id": project.id,
                    "title": project.title,
                    "created_at": project.created_at,
                    "task_count": len(project.get_tasks())
                }
                for project in projects
            ]
        except Exception as e:
            st.error(f"Projekte laden fehlgeschlagen: {e}")
            return []
    
    def export_json_file(self, face_data: List[Dict], filename: str = None) -> str:
        """Exportiert Face Tagging Daten als JSON-Datei"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"face_tagging_export_{timestamp}.json"
        
        filepath = os.path.join("exports", filename)
        os.makedirs("exports", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(face_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def import_json_file(self, filepath: str) -> List[Dict]:
        """Importiert Face Tagging Daten aus JSON-Datei"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            else:
                return [data]
                
        except Exception as e:
            st.error(f"JSON-Import fehlgeschlagen: {e}")
            return []

def test_labelstudio_connection(url: str = "http://localhost:8080", api_key: str = None) -> bool:
    """Testet Label Studio Verbindung"""
    try:
        connector = LabelStudioConnector(url, api_key)
        return connector.is_connected()
    except:
        return False
