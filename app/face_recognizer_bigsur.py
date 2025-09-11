"""
Face Recognition für macOS Big Sur mit Intel-Chip
Alternative Implementierung mit face-recognition und dlib
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
import face_recognition
from PIL import Image
import os

class FaceRecognizerBigSur:
    """Face Recognition für macOS Big Sur mit Intel-Chip"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.known_faces = []
        self.known_names = []
        
        # Lade bekannte Gesichter
        self._load_known_faces()
    
    def _load_known_faces(self):
        """Lädt bekannte Gesichter aus dem faces-Ordner"""
        faces_dir = "faces"
        if not os.path.exists(faces_dir):
            os.makedirs(faces_dir)
            self.logger.info(f"Erstelle Ordner: {faces_dir}")
            return
        
        for filename in os.listdir(faces_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(faces_dir, filename)
                try:
                    # Lade Bild
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)
                    
                    if face_encodings:
                        self.known_faces.append(face_encodings[0])
                        self.known_names.append(os.path.splitext(filename)[0])
                        self.logger.info(f"Geladen: {filename}")
                    else:
                        self.logger.warning(f"Kein Gesicht gefunden in: {filename}")
                        
                except Exception as e:
                    self.logger.error(f"Fehler beim Laden von {filename}: {e}")
        
        self.logger.info(f"{len(self.known_faces)} bekannte Gesichter geladen")
    
    def detect_faces(self, img_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Erkennt Gesichter in einem Bild
        
        Args:
            img_bgr: BGR-Bild (OpenCV-Format)
            
        Returns:
            Liste von Gesichts-Dictionaries
        """
        try:
            # Konvertiere BGR zu RGB
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            
            # Finde Gesichter
            face_locations = face_recognition.face_locations(img_rgb)
            face_encodings = face_recognition.face_encodings(img_rgb, face_locations)
            
            persons = []
            
            for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # Konvertiere face_recognition Format zu OpenCV Format
                top, right, bottom, left = face_location
                bbox = [left, top, right, bottom]
                
                # Erkenne Person
                name, similarity = self._recognize_person(face_encoding)
                
                # Schätze Alter und Geschlecht (vereinfacht)
                age, gender = self._estimate_age_gender(img_bgr, bbox)
                
                # Bewerte Gesichtsqualität
                quality_score = self._assess_face_quality(img_bgr, bbox)
                
                # Erkenne Emotion (vereinfacht)
                emotion = self._estimate_emotion(img_bgr, bbox)
                
                # Erkenne Augen- und Mund-Status
                eye_status = self._detect_eye_status(img_bgr, bbox)
                mouth_status = self._detect_mouth_status(img_bgr, bbox)
                
                person_data = {
                    'bbox': bbox,
                    'prob': 1.0,  # face_recognition gibt keine Wahrscheinlichkeit zurück
                    'name': name,
                    'similarity': similarity,
                    'age': age,
                    'gender': gender,
                    'emotion': emotion,
                    'quality_score': quality_score,
                    'eye_status': eye_status,
                    'mouth_status': mouth_status,
                    'landmarks': self._get_landmarks(img_rgb, face_location)
                }
                
                persons.append(person_data)
            
            return persons
            
        except Exception as e:
            self.logger.error(f"Fehler bei Gesichtserkennung: {e}")
            return []
    
    def _recognize_person(self, face_encoding: np.ndarray) -> Tuple[str, float]:
        """Erkennt eine Person basierend auf Gesichts-Encoding"""
        if not self.known_faces:
            return "Unknown", 0.0
        
        try:
            # Berechne Distanzen zu bekannten Gesichtern
            distances = face_recognition.face_distance(self.known_faces, face_encoding)
            
            # Finde das beste Match
            min_distance = min(distances)
            best_match_index = np.argmin(distances)
            
            # Konvertiere Distanz zu Ähnlichkeit (0-1)
            similarity = max(0, 1 - min_distance)
            
            if similarity > 0.6:  # Schwellenwert
                return self.known_names[best_match_index], similarity
            else:
                return "Unknown", similarity
                
        except Exception as e:
            self.logger.error(f"Fehler bei Personenerkennung: {e}")
            return "Unknown", 0.0
    
    def _estimate_age_gender(self, img_bgr: np.ndarray, bbox: List[int]) -> Tuple[int, str]:
        """Schätzt Alter und Geschlecht (vereinfachte Implementierung)"""
        try:
            # Extrahiere Gesichtsregion
            x1, y1, x2, y2 = bbox
            face_img = img_bgr[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return 30, "unknown"
            
            # Vereinfachte Schätzung basierend auf Gesichtsform
            height, width = face_img.shape[:2]
            aspect_ratio = width / height
            
            # Sehr einfache Heuristik
            if aspect_ratio > 0.8:
                gender = "male"
                age = 35
            else:
                gender = "female"
                age = 30
            
            return age, gender
            
        except Exception as e:
            self.logger.error(f"Fehler bei Alter/Geschlecht-Schätzung: {e}")
            return 30, "unknown"
    
    def _assess_face_quality(self, img_bgr: np.ndarray, bbox: List[int]) -> float:
        """Bewertet die Qualität eines Gesichts"""
        try:
            x1, y1, x2, y2 = bbox
            face_img = img_bgr[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return 0.0
            
            # Konvertiere zu Graustufen
            gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Bewerte Schärfe (Laplacian Variance)
            laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            sharpness_score = min(1.0, laplacian_var / 1000.0)
            
            # Bewerte Helligkeit
            brightness = np.mean(gray_face) / 255.0
            brightness_score = 1.0 - abs(brightness - 0.5) * 2
            
            # Bewerte Kontrast
            contrast = np.std(gray_face) / 255.0
            contrast_score = min(1.0, contrast * 4)
            
            # Kombiniere Scores
            quality = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            return max(0.0, min(1.0, quality))
            
        except Exception as e:
            self.logger.error(f"Fehler bei Qualitätsbewertung: {e}")
            return 0.5
    
    def _estimate_emotion(self, img_bgr: np.ndarray, bbox: List[int]) -> str:
        """Schätzt Emotion (vereinfachte Implementierung)"""
        try:
            x1, y1, x2, y2 = bbox
            face_img = img_bgr[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return "unknown"
            
            # Konvertiere zu Graustufen
            gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Sehr einfache Heuristik basierend auf Mundregion
            height, width = gray_face.shape
            mouth_region = gray_face[int(height * 0.6):, :]
            
            # Analysiere Mundregion
            mouth_mean = np.mean(mouth_region)
            mouth_std = np.std(mouth_region)
            
            # Einfache Klassifikation
            if mouth_std > 30:
                return "happy"
            elif mouth_mean > 120:
                return "neutral"
            else:
                return "unknown"
                
        except Exception as e:
            self.logger.error(f"Fehler bei Emotionserkennung: {e}")
            return "unknown"
    
    def _detect_eye_status(self, img_bgr: np.ndarray, bbox: List[int]) -> str:
        """Erkennt Augen-Status"""
        try:
            x1, y1, x2, y2 = bbox
            face_img = img_bgr[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return "unknown"
            
            # Konvertiere zu Graustufen
            gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Augenregion (obere Hälfte des Gesichts)
            height, width = gray_face.shape
            eye_region = gray_face[:int(height * 0.5), :]
            
            # Einfache Heuristik
            eye_brightness = np.mean(eye_region)
            
            if eye_brightness > 100:
                return "open"
            else:
                return "closed"
                
        except Exception as e:
            self.logger.error(f"Fehler bei Augen-Status-Erkennung: {e}")
            return "unknown"
    
    def _detect_mouth_status(self, img_bgr: np.ndarray, bbox: List[int]) -> str:
        """Erkennt Mund-Status"""
        try:
            x1, y1, x2, y2 = bbox
            face_img = img_bgr[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return "unknown"
            
            # Konvertiere zu Graustufen
            gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Mundregion (untere Hälfte des Gesichts)
            height, width = gray_face.shape
            mouth_region = gray_face[int(height * 0.6):, :]
            
            # Einfache Heuristik
            mouth_std = np.std(mouth_region)
            
            if mouth_std > 25:
                return "open"
            else:
                return "closed"
                
        except Exception as e:
            self.logger.error(f"Fehler bei Mund-Status-Erkennung: {e}")
            return "unknown"
    
    def _get_landmarks(self, img_rgb: np.ndarray, face_location: Tuple) -> List[List[int]]:
        """Extrahiert Gesichtslandmarks"""
        try:
            landmarks = face_recognition.face_landmarks(img_rgb, [face_location])
            if landmarks:
                # Konvertiere zu einfachem Format
                landmark_list = []
                for landmark_set in landmarks[0].values():
                    for point in landmark_set:
                        landmark_list.append([point[0], point[1]])
                return landmark_list
            return []
            
        except Exception as e:
            self.logger.error(f"Fehler bei Landmark-Extraktion: {e}")
            return []
    
    def add_known_face(self, img_bgr: np.ndarray, name: str) -> bool:
        """Fügt ein bekanntes Gesicht hinzu"""
        try:
            # Konvertiere BGR zu RGB
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            
            # Finde Gesichter
            face_locations = face_recognition.face_locations(img_rgb)
            face_encodings = face_recognition.face_encodings(img_rgb, face_locations)
            
            if face_encodings:
                self.known_faces.append(face_encodings[0])
                self.known_names.append(name)
                
                # Speichere auch als Datei
                faces_dir = "faces"
                os.makedirs(faces_dir, exist_ok=True)
                
                # Speichere das Gesicht
                face_img = Image.fromarray(img_rgb)
                face_path = os.path.join(faces_dir, f"{name}.jpg")
                face_img.save(face_path)
                
                self.logger.info(f"Gesicht hinzugefügt: {name}")
                return True
            else:
                self.logger.warning(f"Kein Gesicht gefunden für: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Gesichts: {e}")
            return False
