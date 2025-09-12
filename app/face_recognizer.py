
from __future__ import annotations
import pickle, os, glob
from typing import Dict, List, Optional
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from .utils import cosine_similarity

class FaceEngine:
    def __init__(self, det_size=(640,640)):
        self.app = FaceAnalysis(name='buffalo_l')
        self.app.prepare(ctx_id=-1, det_size=det_size)

    def analyze(self, img_bgr):
        faces = self.app.get(img_bgr)
        results = []
        for f in faces:
            box = f.bbox.astype(int).tolist()
            prob = float(getattr(f, "det_score", 1.0))
            gender = getattr(f, "gender", None)
            gender_str = "male" if gender == 0 else ("female" if gender == 1 else None)
            age = int(getattr(f, "age", -1)) if getattr(f, "age", None) is not None else None
            emb = f.embedding.astype(np.float32)
            
            # Erweiterte Attribute
            face_attributes = self._extract_face_attributes(f, img_bgr, box)
            
            results.append({
                "bbox": box,
                "prob": prob,
                "embedding": emb,
                "age": age if age and age >= 0 else None,
                "gender": gender_str,
                **face_attributes
            })
        return results
    
    def _extract_face_attributes(self, face, img_bgr, bbox):
        """Extrahiert erweiterte Gesichtsattribute"""
        attributes = {}
        
        # Pose-Schätzung (falls verfügbar)
        if hasattr(face, 'pose'):
            attributes['pose'] = {
                'yaw': float(getattr(face.pose, 'yaw', 0)),
                'pitch': float(getattr(face.pose, 'pitch', 0)),
                'roll': float(getattr(face.pose, 'roll', 0))
            }
        
        # Landmarks für Qualitätsbewertung
        if hasattr(face, 'kps') and face.kps is not None:
            landmarks = face.kps.astype(np.int32)
            attributes['landmarks'] = landmarks.tolist()
            
            # Qualitätsbewertung basierend auf Landmarks
            quality_score = self._assess_face_quality(img_bgr, bbox, landmarks)
            attributes['quality_score'] = quality_score
        
        # Emotion-Schätzung (einfache Implementierung)
        emotion = self._estimate_emotion(img_bgr, bbox)
        if emotion:
            attributes['emotion'] = emotion
        
        # Augen-Status
        eye_status = self._detect_eye_status(img_bgr, bbox)
        if eye_status:
            attributes['eye_status'] = eye_status
        
        # Mund-Status
        mouth_status = self._detect_mouth_status(img_bgr, bbox)
        if mouth_status:
            attributes['mouth_status'] = mouth_status
        
        return attributes
    
    def _assess_face_quality(self, img_bgr, bbox, landmarks):
        """Bewertet die Qualität des Gesichts mit erweiterten Metriken"""
        try:
            x1, y1, x2, y2 = bbox
            face_roi = img_bgr[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return 0.0
            
            # Größe des Gesichts
            face_area = (x2 - x1) * (y2 - y1)
            img_area = img_bgr.shape[0] * img_bgr.shape[1]
            size_score = min(face_area / img_area * 100, 1.0)
            
            # Schärfe (Laplacian Variance) - verbessert
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 800, 1.0)  # Angepasst für bessere Erkennung
            
            # Helligkeit - verbessert
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 120) / 120  # Optimiert für Gesichter
            
            # Kontrast - verbessert
            contrast = np.std(gray)
            contrast_score = min(contrast / 60, 1.0)  # Angepasst
            
            # Neue Qualitätsmetriken
            # Symmetrie basierend auf Landmarks
            symmetry_score = self._assess_symmetry(landmarks) if landmarks is not None else 0.5
            
            # Pose-Qualität (Frontalität)
            pose_score = self._assess_pose_quality(landmarks) if landmarks is not None else 0.5
            
            # Rauschen
            noise_score = self._assess_noise_level(gray)
            
            # Gesamtqualität mit erweiterten Gewichtungen
            quality = (size_score * 0.25 + sharpness_score * 0.25 + 
                      brightness_score * 0.15 + contrast_score * 0.15 +
                      symmetry_score * 0.1 + pose_score * 0.05 + noise_score * 0.05)
            
            return float(max(0.0, min(1.0, quality)))
            
        except Exception:
            return 0.5
    
    def _assess_symmetry(self, landmarks):
        """Bewertet Gesichtssymmetrie basierend auf Landmarks"""
        try:
            if landmarks is None or len(landmarks) < 5:
                return 0.5
            
            # Vereinfachte Symmetrie-Bewertung
            # Linke und rechte Augenpunkte
            left_eye = landmarks[0] if len(landmarks) > 0 else None
            right_eye = landmarks[1] if len(landmarks) > 1 else None
            
            if left_eye is not None and right_eye is not None:
                # Berechne Symmetrie basierend auf Augenposition
                eye_distance = abs(left_eye[0] - right_eye[0])
                eye_height_diff = abs(left_eye[1] - right_eye[1])
                
                # Symmetrie-Score (je kleiner die Differenz, desto symmetrischer)
                symmetry = 1.0 - min(eye_height_diff / 50.0, 1.0)
                return max(0.0, symmetry)
            
            return 0.5
        except Exception:
            return 0.5
    
    def _assess_pose_quality(self, landmarks):
        """Bewertet Pose-Qualität (Frontalität)"""
        try:
            if landmarks is None or len(landmarks) < 5:
                return 0.5
            
            # Vereinfachte Pose-Bewertung
            # Prüfe ob Gesicht frontal ist
            nose = landmarks[2] if len(landmarks) > 2 else None
            left_eye = landmarks[0] if len(landmarks) > 0 else None
            right_eye = landmarks[1] if len(landmarks) > 1 else None
            
            if nose is not None and left_eye is not None and right_eye is not None:
                # Berechne ob Nase zwischen den Augen liegt
                eye_center_x = (left_eye[0] + right_eye[0]) / 2
                nose_offset = abs(nose[0] - eye_center_x)
                
                # Pose-Score (je näher die Nase am Augenmittelpunkt, desto frontaler)
                pose_quality = 1.0 - min(nose_offset / 30.0, 1.0)
                return max(0.0, pose_quality)
            
            return 0.5
        except Exception:
            return 0.5
    
    def _assess_noise_level(self, gray_face):
        """Bewertet Rauschlevel im Gesicht"""
        try:
            # Berechne Rauschlevel mit Sobel-Operator
            sobel_x = cv2.Sobel(gray_face, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray_face, cv2.CV_64F, 0, 1, ksize=3)
            noise_level = np.mean(np.sqrt(sobel_x**2 + sobel_y**2))
            
            # Normalisiere Rauschlevel (je niedriger, desto besser)
            noise_score = max(0.0, 1.0 - noise_level / 100.0)
            return noise_score
        except Exception:
            return 0.5
    
    def _estimate_emotion(self, img_bgr, bbox):
        """Einfache Emotionsschätzung basierend auf Gesichtsgeometrie"""
        try:
            x1, y1, x2, y2 = bbox
            face_roi = img_bgr[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return None
            
            # Graustufen-Konvertierung
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Haar Cascade für Augen
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 3)
            
            # Haar Cascade für Mund
            mouth_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
            mouths = mouth_cascade.detectMultiScale(gray, 1.1, 3)
            
            # Einfache Emotionslogik
            if len(eyes) >= 2 and len(mouths) > 0:
                return "happy"
            elif len(eyes) >= 2:
                return "neutral"
            else:
                return "unknown"
                
        except Exception:
            return None
    
    def _detect_eye_status(self, img_bgr, bbox):
        """Verbesserte Augen-Status-Erkennung (offen/geschlossen)"""
        try:
            x1, y1, x2, y2 = bbox
            face_roi = img_bgr[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return None
            
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Mehrere Erkennungsmethoden kombinieren
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eye_glasses_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
            
            # Standard-Augen-Erkennung
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 3)
            eyes_glasses = eye_glasses_cascade.detectMultiScale(gray, 1.1, 3)
            
            # Kombiniere Ergebnisse
            total_eyes = len(eyes) + len(eyes_glasses)
            
            # Erweiterte Analyse basierend auf Augenregion
            eye_region_analysis = self._analyze_eye_region(gray)
            
            # Entscheidung basierend auf mehreren Faktoren
            if total_eyes >= 2:
                if eye_region_analysis == "bright":
                    return "open"
                elif eye_region_analysis == "dark":
                    return "closed"
                else:
                    return "open"  # Standard bei erkannten Augen
            elif total_eyes == 1:
                return "partially_open"
            else:
                # Keine Augen erkannt - analysiere Augenregion
                if eye_region_analysis == "dark":
                    return "closed"
                elif eye_region_analysis == "bright":
                    return "open"
                else:
                    return "unknown"
                
        except Exception:
            return None
    
    def _analyze_eye_region(self, gray_face):
        """Analysiert Augenregion für Helligkeit und Kontrast"""
        try:
            height, width = gray_face.shape
            
            # Augenregion (obere 40% des Gesichts)
            eye_region = gray_face[:int(height*0.4), :]
            
            if eye_region.size == 0:
                return "unknown"
            
            # Berechne Durchschnittshelligkeit
            avg_brightness = np.mean(eye_region)
            
            # Berechne Kontrast
            contrast = np.std(eye_region)
            
            # Klassifiziere basierend auf Helligkeit und Kontrast
            if avg_brightness > 120 and contrast > 30:
                return "bright"  # Offene Augen (hell und kontrastreich)
            elif avg_brightness < 80 and contrast < 20:
                return "dark"    # Geschlossene Augen (dunkel und wenig Kontrast)
            else:
                return "mixed"   # Unbestimmt
                
        except Exception:
            return "unknown"
    
    def _detect_mouth_status(self, img_bgr, bbox):
        """Verbesserte Mund-Status-Erkennung (offen/geschlossen)"""
        try:
            x1, y1, x2, y2 = bbox
            face_roi = img_bgr[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return None
            
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Mehrere Erkennungsmethoden
            mouth_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
            mouths = mouth_cascade.detectMultiScale(gray, 1.1, 3)
            
            # Mundregion-Analyse
            mouth_region_analysis = self._analyze_mouth_region(gray)
            
            # Kombiniere Ergebnisse
            if len(mouths) > 0:
                # Mund erkannt - prüfe ob wirklich offen
                if mouth_region_analysis == "open":
                    return "open"
                elif mouth_region_analysis == "closed":
                    return "closed"
                else:
                    return "open"  # Standard bei erkanntem Mund
            else:
                # Kein Mund erkannt - basiere auf Region-Analyse
                if mouth_region_analysis == "open":
                    return "open"
                elif mouth_region_analysis == "closed":
                    return "closed"
                else:
                    return "unknown"
                
        except Exception:
            return None
    
    def _analyze_mouth_region(self, gray_face):
        """Analysiert Mundregion für Öffnungsstatus"""
        try:
            height, width = gray_face.shape
            
            # Mundregion (untere 30% des Gesichts)
            mouth_region = gray_face[int(height*0.7):, :]
            
            if mouth_region.size == 0:
                return "unknown"
            
            # Berechne horizontale Gradienten (wichtig für Mundöffnung)
            sobel_x = cv2.Sobel(mouth_region, cv2.CV_64F, 1, 0, ksize=3)
            horizontal_gradients = np.mean(np.abs(sobel_x))
            
            # Berechne vertikale Gradienten
            sobel_y = cv2.Sobel(mouth_region, cv2.CV_64F, 0, 1, ksize=3)
            vertical_gradients = np.mean(np.abs(sobel_y))
            
            # Berechne Textur-Varianz
            texture_variance = np.var(mouth_region)
            
            # Klassifiziere basierend auf Gradienten und Textur
            if horizontal_gradients > 25 and texture_variance > 150:
                return "open"    # Starke horizontale Gradienten und hohe Varianz = offener Mund
            elif horizontal_gradients < 15 and texture_variance < 100:
                return "closed"  # Schwache Gradienten und niedrige Varianz = geschlossener Mund
            else:
                return "mixed"   # Unbestimmt
                
        except Exception:
            return "unknown"

class GalleryDB:
    def __init__(self):
        self.people: Dict[str, List[np.ndarray]] = {}
        self.face_metadata: Dict[str, List[Dict]] = {}  # Erweiterte Metadaten

    def add(self, name: str, embedding: np.ndarray, metadata: Optional[Dict] = None):
        self.people.setdefault(name, []).append(embedding.astype(np.float32))
        if metadata:
            self.face_metadata.setdefault(name, []).append(metadata)

    def save(self, path: str):
        data = {
            'people': self.people,
            'metadata': self.face_metadata
        }
        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(path: str) -> 'GalleryDB':
        db = GalleryDB()
        with open(path, "rb") as f:
            data = pickle.load(f)
            if isinstance(data, dict):
                db.people = data.get('people', {})
                db.face_metadata = data.get('metadata', {})
            else:
                # Rückwärtskompatibilität
                db.people = data
        return db

    def match(self, embedding: np.ndarray, threshold: float = 0.55):
        best_name, best_sim = None, -1.0
        for name, embs in self.people.items():
            sims = [cosine_similarity(embedding, e) for e in embs]
            if sims:
                sim = float(np.mean(sims))
                if sim > best_sim:
                    best_sim, best_name = sim, name
        if best_sim >= threshold:
            return best_name, best_sim
        return None, best_sim
    
    def get_person_metadata(self, name: str) -> List[Dict]:
        """Gibt Metadaten für eine Person zurück"""
        return self.face_metadata.get(name, [])

def build_gallery_from_folder(gallery_dir: str, det_size=(640,640)) -> 'GalleryDB':
    engine = FaceEngine(det_size=det_size)
    db = GalleryDB()
    exts = (".jpg",".jpeg",".png",".bmp",".webp",".tif",".tiff")
    for person in sorted(os.listdir(gallery_dir)):
        person_dir = os.path.join(gallery_dir, person)
        if not os.path.isdir(person_dir):
            continue
        paths = []
        for ext in exts:
            paths.extend(glob.glob(os.path.join(person_dir, f"*{ext}")))
        for p in paths:
            img = cv2.imread(p)
            if img is None:
                continue
            faces = engine.analyze(img)
            if not faces:
                continue
            faces.sort(key=lambda f: (f['bbox'][2]-f['bbox'][0])*(f['bbox'][3]-f['bbox'][1]), reverse=True)
            
            # Erweiterte Metadaten speichern
            face_data = faces[0]
            metadata = {
                'age': face_data.get('age'),
                'gender': face_data.get('gender'),
                'quality_score': face_data.get('quality_score'),
                'emotion': face_data.get('emotion'),
                'eye_status': face_data.get('eye_status'),
                'mouth_status': face_data.get('mouth_status'),
                'source_image': p
            }
            
            db.add(person, face_data["embedding"], metadata)
    return db
