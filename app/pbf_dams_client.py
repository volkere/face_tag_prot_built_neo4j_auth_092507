"""
PBF-DAMS API Client

Verbindet Streamlit App mit dem PBF-DAMS Django Backend
zum Abrufen von Image-Region-Daten (XMP-Metadaten).
"""
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PBFDAMSClient:
    """
    Client zum Abrufen von Image-Region-Daten aus PBF-DAMS.
    
    Verwendung:
        client = PBFDAMSClient(base_url="http://localhost:8000")
        regions = client.get_regions()
        regions_by_person = client.get_regions(person="pina_bausch")
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialisiert den Client.
        
        Args:
            base_url: Basis-URL des PBF-DAMS Servers (Standard: localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/v1/exports/image-regions/"
        self.session = requests.Session()
        
    def get_regions(
        self,
        photo: Optional[str] = None,
        person: Optional[str] = None,
        include_unidentified: bool = False,
        timeout: int = 30,
        max_results: Optional[int] = None
    ) -> Dict:
        """
        Holt Image-Region-Daten von PBF-DAMS.
        
        Args:
            photo: Optional - Filter nach Foto-Identifier
            person: Optional - Filter nach Person-Identifier
            include_unidentified: Auch nicht-identifizierte/private Personen inkludieren
            timeout: Request-Timeout in Sekunden
            max_results: Optional - Begrenzung der Anzahl zurückgegebener Regions
            
        Returns:
            Dictionary mit:
                - count: Anzahl der Regions
                - export_format: "json"
                - regions: Liste von Region-Objekten
                
        Raises:
            requests.RequestException: Bei Netzwerk-/API-Fehlern
        """
        params = {
            "format": "json"
        }
        
        if max_results:
            params["limit"] = max_results
        
        if photo:
            params["photo"] = photo
            
        if person:
            params["person"] = person
            
        if include_unidentified:
            params["include_unidentified"] = "true"
        
        try:
            logger.info(f"Fetching regions from {self.api_endpoint} with params: {params}")
            response = self.session.get(
                self.api_endpoint,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Prüfe ob Response leer ist
            if not response.content:
                raise ValueError("Server returned empty response")
            
            # Prüfe Content-Type
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                raise ValueError(f"Server returned non-JSON response. Content-Type: {content_type}. Response: {response.text[:200]}")
            
            try:
                data = response.json()
            except ValueError as e:
                raise ValueError(f"Invalid JSON response from server. Response: {response.text[:200]}") from e
            
            logger.info(f"Successfully fetched {data.get('count', 0)} regions")
            
            regions = data.get("regions", [])
            total_available = data.get("count", len(regions))
            
            if max_results is not None:
                if len(regions) > max_results:
                    regions = regions[:max_results]
                data["regions"] = regions
                data["count"] = len(regions)
                data["total_available"] = total_available
            else:
                data["count"] = total_available
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while connecting to {self.api_endpoint}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to {self.api_endpoint}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {response.status_code}: {response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def get_photos_list(self, timeout: int = 30) -> List[str]:
        """
        Holt Liste aller Foto-Identifiers mit Regions.
        
        Returns:
            Liste von Foto-Identifiers
        """
        try:
            data = self.get_regions(timeout=timeout)
            photo_ids = set()
            
            for region in data.get("regions", []):
                if photo_id := region.get("photo_identifier"):
                    photo_ids.add(photo_id)
            
            return sorted(list(photo_ids))
        except Exception as e:
            logger.error(f"Error fetching photos list: {e}")
            return []
    
    def get_persons_list(self, timeout: int = 30) -> List[Dict[str, str]]:
        """
        Holt Liste aller Personen mit Regions.
        
        Returns:
            Liste von Dictionaries mit person_identifier und person_label
        """
        try:
            data = self.get_regions(timeout=timeout)
            persons = {}
            
            for region in data.get("regions", []):
                if person := region.get("person"):
                    identifier = person.get("identifier")
                    label = person.get("label")
                    if identifier and label:
                        persons[identifier] = label
            
            return [
                {"identifier": k, "label": v} 
                for k, v in sorted(persons.items(), key=lambda x: x[1])
            ]
        except Exception as e:
            logger.error(f"Error fetching persons list: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Testet die Verbindung zum PBF-DAMS Server.
        
        Returns:
            True wenn Verbindung erfolgreich, False sonst
        """
        try:
            response = self.session.get(
                self.api_endpoint,
                params={"format": "json"},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Holt Statistiken über die Regions-Daten.
        
        Returns:
            Dictionary mit Statistiken
        """
        try:
            data = self.get_regions()
            regions = data.get("regions", [])
            
            # Zähle Fotos
            photos = set()
            persons = set()
            
            for region in regions:
                if photo_id := region.get("photo_identifier"):
                    photos.add(photo_id)
                if person := region.get("person"):
                    if person_id := person.get("identifier"):
                        persons.add(person_id)
            
            return {
                "total_regions": data.get("count", 0),
                "unique_photos": len(photos),
                "unique_persons": len(persons),
                "avg_regions_per_photo": data.get("count", 0) / len(photos) if photos else 0
            }
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return {
                "total_regions": 0,
                "unique_photos": 0,
                "unique_persons": 0,
                "avg_regions_per_photo": 0
            }


class RegionData:
    """
    Hilfsklasse zum einfacheren Zugriff auf Region-Daten.
    """
    
    def __init__(self, region_dict: Dict):
        self.data = region_dict
    
    @property
    def person_name(self) -> Optional[str]:
        """Name der Person"""
        if person := self.data.get("person"):
            return person.get("label")
        return None
    
    @property
    def person_identifier(self) -> Optional[str]:
        """Identifier der Person"""
        if person := self.data.get("person"):
            return person.get("identifier")
        return None
    
    @property
    def photo_identifier(self) -> Optional[str]:
        """Identifier des Fotos"""
        return self.data.get("photo_identifier")
    
    @property
    def photo_label(self) -> Optional[str]:
        """Label/Name des Fotos"""
        return self.data.get("photo_label")
    
    @property
    def coordinates(self) -> Dict[str, float]:
        """Koordinaten der Region"""
        return {
            "x": self.data.get("x", 0.0),
            "y": self.data.get("y", 0.0),
            "width": self.data.get("width", 0.0),
            "height": self.data.get("height", 0.0),
            "rotation": self.data.get("rotation", 0.0)
        }
    
    @property
    def dimensions(self) -> Dict[str, int]:
        """Referenz-Dimensionen des Original-Bildes"""
        return {
            "width": self.data.get("ref_width", 0),
            "height": self.data.get("ref_height", 0)
        }
    
    def to_dict(self) -> Dict:
        """Gibt die rohen Daten zurück"""
        return self.data




