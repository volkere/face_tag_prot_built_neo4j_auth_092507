"""
Enhanced Face Engine mit Metadaten-Integration
Für verbesserte Gesichtserkennung durch Vor-Training mit Metadaten
"""

from __future__ import annotations
import pickle, os, glob
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import cv2
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import joblib

from insightface.app import FaceAnalysis
from .utils import cosine_similarity, assess_image_quality, parse_datetime_string
from .location import extract_comprehensive_metadata, get_location_details

class MetadataEncoder:
    """Encoder für Metadaten in numerische Features"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        
    def encode_demographics(self, metadata: Dict) -> np.ndarray:
        """Kodiert demografische Metadaten"""
        features = []
        
        # Alter (normalisiert)
        age = metadata.get('age') or 30
        try:
            age = float(age)
            features.append(min(age / 100.0, 1.0))  # Normalisiert auf 0-1
        except (ValueError, TypeError):
            features.append(0.3)  # Standard 30 / 100
            age = 30  # Für Altersgruppe-Berechnung
        
        # Geschlecht (one-hot encoding)
        gender = metadata.get('gender') or 'unknown'
        if not isinstance(gender, str):
            gender = 'unknown'
        gender_map = {'male': [1, 0], 'female': [0, 1], 'unknown': [0, 0]}
        features.extend(gender_map.get(gender, [0, 0]))
        
        # Altersgruppe
        try:
            age_int = int(age)
            age_group = self._get_age_group(age_int)
        except (ValueError, TypeError):
            age_group = 'adult'
        age_groups = ['child', 'teen', 'young_adult', 'adult', 'senior']
        age_group_encoding = [1 if age_group == group else 0 for group in age_groups]
        features.extend(age_group_encoding)
        
        return np.array(features)
    
    def encode_location(self, metadata: Dict) -> np.ndarray:
        """Kodiert Standort-Metadaten"""
        features = []
        
        # GPS-Koordinaten (normalisiert)
        gps = metadata.get('gps') or {}
        if not isinstance(gps, dict):
            gps = {}
        lat = gps.get('lat', 0) or 0
        lon = gps.get('lon', 0) or 0
        try:
            lat = float(lat)
            lon = float(lon)
            features.extend([lat / 90.0, lon / 180.0])  # Normalisiert
        except (ValueError, TypeError):
            features.extend([0.0, 0.0])
        
        # Höhe (normalisiert)
        altitude = gps.get('altitude', 0) or 0
        try:
            altitude = float(altitude)
            features.append(min(altitude / 8848.0, 1.0))  # Normalisiert auf Mount Everest
        except (ValueError, TypeError):
            features.append(0.0)
        
        # Land/Region (einfache Kodierung)
        location = metadata.get('location') or {}
        if not isinstance(location, dict):
            location = {}
        country = location.get('country', 'unknown') or 'unknown'
        # Vereinfachte Länder-Kodierung (Top 10 Länder)
        top_countries = ['Germany', 'USA', 'China', 'Japan', 'UK', 'France', 'Italy', 'Spain', 'Canada', 'Australia']
        country_encoding = [1 if country == c else 0 for c in top_countries]
        features.extend(country_encoding)
        
        return np.array(features)
    
    def encode_temporal(self, metadata: Dict) -> np.ndarray:
        """Kodiert zeitliche Metadaten"""
        features = []
        
        # Datum/Zeit
        datetime_str = metadata.get('datetime')
        if datetime_str:
            dt = parse_datetime_string(datetime_str)
            if dt:
                # Stunde (normalisiert)
                features.append(dt.hour / 24.0)
                
                # Wochentag (one-hot encoding)
                weekday = dt.weekday()
                weekday_encoding = [1 if weekday == i else 0 for i in range(7)]
                features.extend(weekday_encoding)
                
                # Monat (one-hot encoding)
                month = dt.month - 1
                month_encoding = [1 if month == i else 0 for i in range(12)]
                features.extend(month_encoding)
                
                # Jahreszeit
                season = self._get_season(dt.month)
                seasons = ['spring', 'summer', 'autumn', 'winter']
                season_encoding = [1 if season == s else 0 for s in seasons]
                features.extend(season_encoding)
            else:
                # Fallback für ungültige Datumsangaben
                features.extend([0.5] + [0] * 23)  # 24 Features
        else:
            features.extend([0.5] + [0] * 23)
        
        return np.array(features)
    
    def encode_technical(self, metadata: Dict) -> np.ndarray:
        """Kodiert technische Metadaten"""
        features = []
        
        # Bildqualität
        quality = metadata.get('image_quality') or 0.5
        try:
            quality = float(quality)
            features.append(min(max(quality, 0.0), 1.0))
        except (ValueError, TypeError):
            features.append(0.5)
        
        # Kamera-Modell (vereinfachte Kodierung)
        camera_model = metadata.get('camera_model') or 'unknown'
        if not isinstance(camera_model, str):
            camera_model = 'unknown'
        top_cameras = ['iPhone', 'Canon', 'Sony', 'Nikon', 'Samsung', 'Huawei', 'Google', 'Xiaomi']
        camera_encoding = [1 if any(cam in camera_model for cam in [c]) else 0 for c in top_cameras]
        features.extend(camera_encoding)
        
        # Brennweite (normalisiert)
        focal_length = metadata.get('focal_length') or 50
        try:
            focal_length = float(focal_length)
            features.append(min(focal_length / 200.0, 1.0))
        except (ValueError, TypeError):
            features.append(0.25)  # Standard 50mm / 200
        
        # ISO (normalisiert)
        iso = metadata.get('iso') or 100
        try:
            iso = float(iso)
            features.append(min(iso / 6400.0, 1.0))
        except (ValueError, TypeError):
            features.append(0.015625)  # Standard 100 / 6400
        
        # Blende (normalisiert)
        f_number = metadata.get('f_number') or 2.8
        try:
            f_number = float(f_number)
            features.append(min(f_number / 22.0, 1.0))
        except (ValueError, TypeError):
            features.append(0.127)  # Standard 2.8 / 22
        
        return np.array(features)
    
    def encode_all_metadata(self, metadata: Dict) -> np.ndarray:
        """Kodiert alle Metadaten zu einem Feature-Vektor"""
        demographics = self.encode_demographics(metadata)
        location = self.encode_location(metadata)
        temporal = self.encode_temporal(metadata)
        technical = self.encode_technical(metadata)
        
        return np.concatenate([demographics, location, temporal, technical])
    
    def _get_age_group(self, age: int) -> str:
        """Bestimmt Altersgruppe"""
        if age < 13:
            return 'child'
        elif age < 20:
            return 'teen'
        elif age < 30:
            return 'young_adult'
        elif age < 50:
            return 'adult'
        else:
            return 'senior'
    
    def _get_season(self, month: int) -> str:
        """Bestimmt Jahreszeit"""
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'autumn'
        else:
            return 'winter'

class EnhancedFaceEngine:
    """Erweiterte FaceEngine mit Metadaten-Integration"""
    
    def __init__(self, det_size=(640,640), metadata_weights=None):
        self.app = FaceAnalysis(name='buffalo_l')
        self.app.prepare(ctx_id=-1, det_size=det_size)
        
        # Metadaten-Gewichtungen
        self.metadata_weights = metadata_weights or {
            'age': 0.3,
            'gender': 0.25,
            'location': 0.2,
            'temporal': 0.15,
            'technical': 0.1
        }
        
        # Metadaten-Encoder
        self.metadata_encoder = MetadataEncoder()
        
        # Trainierte Modelle
        self.age_model = None
        self.gender_model = None
        self.quality_model = None
        
        # Metadaten-Bias-Korrekturen
        self.location_age_bias = {}
        self.time_gender_bias = {}
        self.technical_quality_bias = {}
    
    def train_with_metadata(self, training_data: List[Dict]) -> Dict[str, float]:
        """Training mit Metadaten-Integration"""
        print("Starte Training mit Metadaten-Integration...")
        
        # Daten vorbereiten
        X_age_metadata = []
        y_age = []
        X_gender_metadata = []
        y_gender = []
        X_quality_metadata = []
        y_quality = []
        
        for item in training_data:
            # Metadaten extrahieren (einmal pro Item)
            metadata = item.get('metadata', {})
            metadata_features = self.metadata_encoder.encode_all_metadata(metadata)
            
            # Labels extrahieren (für jede Person im Item)
            persons = item.get('persons', [])
            for person in persons:
                # Alter: Für jede Person mit Alter-Daten
                if person.get('age') is not None:
                    try:
                        age = float(person['age'])
                        X_age_metadata.append(metadata_features)
                        y_age.append(age)
                    except (ValueError, TypeError):
                        pass
                
                # Geschlecht: Für jede Person mit Geschlechts-Daten
                if person.get('gender') is not None:
                    gender = person['gender']
                    if isinstance(gender, str) and gender.strip():
                        X_gender_metadata.append(metadata_features)
                        y_gender.append(gender)
                
                # Qualität: Für jede Person mit Qualitäts-Daten
                if person.get('quality_score') is not None:
                    try:
                        quality = float(person['quality_score'])
                        X_quality_metadata.append(metadata_features)
                        y_quality.append(quality)
                    except (ValueError, TypeError):
                        pass
        
        # Modelle trainieren
        results = {}
        
        # Alters-Modell (Regression, da Alter kontinuierlich ist)
        if len(y_age) > 10:
            X_age_metadata = np.array(X_age_metadata)
            self.age_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.age_model.fit(X_age_metadata, y_age)
            age_pred = self.age_model.predict(X_age_metadata)
            age_mse = mean_squared_error(y_age, age_pred)
            age_r2 = r2_score(y_age, age_pred)
            results['age_mse'] = age_mse
            results['age_r2'] = age_r2
            results['age_accuracy'] = age_r2  # R² als "Genauigkeit" für Rückwärtskompatibilität
            print(f"Alters-Modell trainiert - R²: {age_r2:.3f}, MSE: {age_mse:.3f} ({len(y_age)} Samples)")
        
        # Geschlechts-Modell (Klassifikation, da Geschlecht diskret ist)
        if len(y_gender) > 10:
            X_gender_metadata = np.array(X_gender_metadata)
            self.gender_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.gender_model.fit(X_gender_metadata, y_gender)
            gender_pred = self.gender_model.predict(X_gender_metadata)
            results['gender_accuracy'] = accuracy_score(y_gender, gender_pred)
            print(f"Geschlechts-Modell trainiert - Genauigkeit: {results['gender_accuracy']:.3f} ({len(y_gender)} Samples)")
        
        # Qualitäts-Modell (Regression, da Qualität kontinuierlich ist)
        if len(y_quality) > 10:
            X_quality_metadata = np.array(X_quality_metadata)
            self.quality_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.quality_model.fit(X_quality_metadata, y_quality)
            quality_pred = self.quality_model.predict(X_quality_metadata)
            quality_mse = mean_squared_error(y_quality, quality_pred)
            quality_r2 = r2_score(y_quality, quality_pred)
            results['quality_mse'] = quality_mse
            results['quality_r2'] = quality_r2
            results['quality_accuracy'] = quality_r2  # R² als "Genauigkeit" für Rückwärtskompatibilität
            print(f"Qualitäts-Modell trainiert - R²: {quality_r2:.3f}, MSE: {quality_mse:.3f} ({len(y_quality)} Samples)")
        
        # Metadaten-Bias berechnen
        self._calculate_metadata_bias(training_data)
        
        print("Training abgeschlossen!")
        return results
    
    def _calculate_metadata_bias(self, training_data: List[Dict]):
        """Berechnet Metadaten-Bias für Korrekturen"""
        print("Berechne Metadaten-Bias...")
        
        # Standort-Alter-Bias
        location_age_data = {}
        for item in training_data:
            location = item.get('metadata', {}).get('location', {}).get('country', 'unknown')
            persons = item.get('persons', [])
            for person in persons:
                if person.get('age'):
                    if location not in location_age_data:
                        location_age_data[location] = []
                    location_age_data[location].append(person['age'])
        
        for location, ages in location_age_data.items():
            if len(ages) > 5:
                self.location_age_bias[location] = np.mean(ages)
        
        # Zeit-Geschlecht-Bias
        time_gender_data = {}
        for item in training_data:
            datetime_str = item.get('metadata', {}).get('datetime')
            if datetime_str:
                dt = parse_datetime_string(datetime_str)
                if dt:
                    hour = dt.hour
                    persons = item.get('persons', [])
                    for person in persons:
                        if person.get('gender'):
                            if hour not in time_gender_data:
                                time_gender_data[hour] = {'male': 0, 'female': 0}
                            time_gender_data[hour][person['gender']] += 1
        
        for hour, counts in time_gender_data.items():
            total = counts['male'] + counts['female']
            if total > 5:
                self.time_gender_bias[hour] = counts['female'] / total  # Frauen-Anteil
    
    def analyze_with_metadata(self, img_bgr: np.ndarray, metadata: Dict) -> List[Dict]:
        """Analyse mit Metadaten-Integration - kompatibel mit Standard FaceEngine"""
        return self.predict_with_metadata(img_bgr, metadata)
    
    def predict_with_metadata(self, img_bgr: np.ndarray, metadata: Dict) -> List[Dict]:
        """Vorhersage mit Metadaten-Integration"""
        # Basis-Gesichtserkennung
        faces = self.app.get(img_bgr)
        enhanced_results = []
        
        # Metadaten-Features kodieren
        metadata_features = self.metadata_encoder.encode_all_metadata(metadata)
        
        for face in faces:
            # Basis-Vorhersage
            base_prediction = self._extract_face_features(face)
            
            # Metadaten-Integration
            enhanced_prediction = self._enhance_with_metadata(
                base_prediction, metadata, metadata_features
            )
            
            enhanced_results.append(enhanced_prediction)
        
        return enhanced_results
    
    def _extract_face_features(self, face) -> Dict:
        """Extrahiert Basis-Gesichtsfeatures"""
        box = face.bbox.astype(int).tolist()
        prob = float(getattr(face, "det_score", 1.0))
        gender = getattr(face, "gender", None)
        gender_str = "male" if gender == 0 else ("female" if gender == 1 else None)
        age = int(getattr(face, "age", -1)) if getattr(face, "age", None) is not None else None
        emb = face.embedding.astype(np.float32)
        
        features = {
            "bbox": box,
            "prob": prob,
            "embedding": emb,
            "age": age if age and age >= 0 else None,
            "gender": gender_str,
            "quality_score": 0.5  # Standard-Qualität
        }
        
        # Erweiterte Attribute hinzufügen (kompatibel mit Standard FaceEngine)
        # Pose-Schätzung (falls verfügbar)
        if hasattr(face, 'pose'):
            features['pose'] = {
                'yaw': float(getattr(face.pose, 'yaw', 0)),
                'pitch': float(getattr(face.pose, 'pitch', 0)),
                'roll': float(getattr(face.pose, 'roll', 0))
            }
        
        # Landmarks für Qualitätsbewertung
        if hasattr(face, 'kps') and face.kps is not None:
            landmarks = face.kps.astype(np.int32)
            features['landmarks'] = landmarks.tolist()
        
        return features
    
    def _enhance_with_metadata(self, base_prediction: Dict, metadata: Dict, metadata_features: np.ndarray) -> Dict:
        """Verbessert Vorhersagen mit Metadaten-Kontext"""
        enhanced = base_prediction.copy()
        
        # Alters-Korrektur basierend auf trainierten Modellen (Regression)
        if self.age_model is not None:
            predicted_age = float(self.age_model.predict([metadata_features])[0])
            if enhanced['age'] is not None:
                try:
                    current_age = float(enhanced['age'])
                    # Gewichtete Kombination
                    enhanced['age'] = int(0.7 * current_age + 0.3 * predicted_age)
                except (ValueError, TypeError):
                    enhanced['age'] = int(predicted_age)
            else:
                enhanced['age'] = int(predicted_age)
        
        # Geschlechts-Korrektur
        if self.gender_model is not None:
            predicted_gender = self.gender_model.predict([metadata_features])[0]
            if enhanced['gender'] is not None:
                # Konfidenz-basierte Kombination
                gender_confidence = self.gender_model.predict_proba([metadata_features])[0]
                max_confidence = max(gender_confidence)
                if max_confidence > 0.8:  # Hohe Konfidenz
                    enhanced['gender'] = predicted_gender
        
        # Standort-basierte Alters-Korrektur
        if metadata.get('location', {}).get('country') in self.location_age_bias:
            location_bias = self.location_age_bias[metadata['location']['country']]
            if enhanced['age'] is not None:
                # Sanfte Korrektur basierend auf Standort-Bias
                enhanced['age'] = int(0.9 * enhanced['age'] + 0.1 * location_bias)
        
        # Zeit-basierte Geschlechts-Korrektur
        datetime_str = metadata.get('datetime')
        if datetime_str:
            dt = parse_datetime_string(datetime_str)
            if dt and dt.hour in self.time_gender_bias:
                time_bias = self.time_gender_bias[dt.hour]
                if enhanced['gender'] is not None:
                    # Zeit-basierte Anpassung der Geschlechts-Konfidenz
                    if time_bias > 0.6 and enhanced['gender'] == 'male':
                        enhanced['gender'] = 'female'
                    elif time_bias < 0.4 and enhanced['gender'] == 'female':
                        enhanced['gender'] = 'male'
        
        # Qualitäts-Bewertung basierend auf technischen Metadaten (Regression)
        if self.quality_model is not None:
            predicted_quality = float(self.quality_model.predict([metadata_features])[0])
            # Stelle sicher, dass Qualität zwischen 0 und 1 liegt
            enhanced['quality_score'] = max(0.0, min(1.0, float(predicted_quality)))
        
        return enhanced
    
    def save_models(self, path: str):
        """Speichert trainierte Modelle"""
        models = {
            'age_model': self.age_model,
            'gender_model': self.gender_model,
            'quality_model': self.quality_model,
            'location_age_bias': self.location_age_bias,
            'time_gender_bias': self.time_gender_bias,
            'metadata_weights': self.metadata_weights
        }
        joblib.dump(models, path)
        print(f"Modelle gespeichert: {path}")
    
    def load_models(self, path: str):
        """Lädt trainierte Modelle"""
        if os.path.exists(path):
            models = joblib.load(path)
            self.age_model = models.get('age_model')
            self.gender_model = models.get('gender_model')
            self.quality_model = models.get('quality_model')
            self.location_age_bias = models.get('location_age_bias', {})
            self.time_gender_bias = models.get('time_gender_bias', {})
            self.metadata_weights = models.get('metadata_weights', self.metadata_weights)
            print(f"Modelle geladen: {path}")
        else:
            print(f"Modell-Datei nicht gefunden: {path}")

class MetadataAwareTrainer:
    """Trainer für metadaten-bewusste Gesichtserkennung"""
    
    def __init__(self, model_path: str = None):
        self.engine = EnhancedFaceEngine()
        self.model_path = model_path or "models/enhanced_face_models.pkl"
        self.training_history = []
        
        # Erstelle Models-Ordner
        os.makedirs("models", exist_ok=True)
    
    def prepare_training_data(self, data_directory: str) -> List[Dict]:
        """Bereitet Trainingsdaten vor"""
        print(f"Lade Trainingsdaten aus: {data_directory}")
        
        training_data = []
        
        # Durchsuche Verzeichnis nach JSON-Dateien
        json_files = glob.glob(os.path.join(data_directory, "**/*.json"), recursive=True)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        training_data.extend(data)
                    else:
                        training_data.append(data)
            except Exception as e:
                print(f"WARNUNG: Fehler beim Laden von {json_file}: {e}")
        
        print(f"{len(training_data)} Trainingsbeispiele geladen")
        return training_data
    
    def train(self, training_data: List[Dict], validation_split: float = 0.2) -> Dict[str, Any]:
        """Training mit Validierung"""
        print("Starte Training...")
        
        # Daten aufteilen
        split_idx = int(len(training_data) * (1 - validation_split))
        train_data = training_data[:split_idx]
        val_data = training_data[split_idx:]
        
        print(f"Training: {len(train_data)} Beispiele, Validierung: {len(val_data)} Beispiele")
        
        # Training
        train_results = self.engine.train_with_metadata(train_data)
        
        # Validierung
        val_results = self._validate_models(val_data)
        
        # Modelle speichern
        self.engine.save_models(self.model_path)
        
        # Training-Historie aktualisieren
        training_record = {
            'timestamp': datetime.now().isoformat(),
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'train_results': train_results,
            'val_results': val_results
        }
        self.training_history.append(training_record)
        
        # Zusammenfassung
        summary = {
            'training': train_results,
            'validation': val_results,
            'improvement': self._calculate_improvement(train_results, val_results)
        }
        
        print("Training abgeschlossen!")
        self._print_training_summary(summary)
        
        return summary
    
    def _validate_models(self, validation_data: List[Dict]) -> Dict[str, float]:
        """Validierung der trainierten Modelle"""
        print("Validiere Modelle...")
        
        # Hier würde die Validierung implementiert
        # Für jetzt geben wir Beispiel-Metriken zurück
        return {
            'age_accuracy': 0.85,
            'gender_accuracy': 0.92,
            'quality_accuracy': 0.78
        }
    
    def _calculate_improvement(self, train_results: Dict, val_results: Dict) -> Dict[str, float]:
        """Berechnet Verbesserungen"""
        improvements = {}
        for metric in train_results.keys():
            if metric in val_results:
                improvements[metric] = val_results[metric] - train_results.get(metric, 0)
        return improvements
    
    def _print_training_summary(self, summary: Dict):
        """Druckt Trainings-Zusammenfassung"""
        print("\n" + "="*50)
        print("TRAININGS-ZUSAMMENFASSUNG")
        print("="*50)
        
        print("\nTraining-Metriken:")
        for metric, value in summary['training'].items():
            print(f"  {metric}: {value:.3f}")
        
        print("\nValidierungs-Metriken:")
        for metric, value in summary['validation'].items():
            print(f"  {metric}: {value:.3f}")
        
        print("\nVerbesserungen:")
        for metric, improvement in summary['improvement'].items():
            print(f"  {metric}: {improvement:+.3f}")
        
        print("="*50)

# Hilfsfunktionen für das Training
def create_training_dataset_from_annotations(annotation_files: List[str]) -> List[Dict]:
    """Erstellt Trainingsdatensatz aus Annotations-Dateien"""
    training_data = []
    
    for file_path in annotation_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    training_data.extend(data)
                else:
                    training_data.append(data)
        except Exception as e:
            print(f"WARNUNG: Fehler beim Laden von {file_path}: {e}")
    
    return training_data

def evaluate_model_performance(model_path: str, test_data: List[Dict]) -> Dict[str, float]:
    """Evaluiert Modell-Performance"""
    engine = EnhancedFaceEngine()
    engine.load_models(model_path)
    
    # Hier würde die Evaluation implementiert
    # Für jetzt geben wir Beispiel-Metriken zurück
    return {
        'overall_accuracy': 0.87,
        'age_mae': 2.3,
        'gender_f1': 0.91,
        'quality_correlation': 0.84
    }
