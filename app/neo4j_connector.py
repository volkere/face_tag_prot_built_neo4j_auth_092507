"""
Neo4j Datenbankanbindung für Gesichtserkennungs-Daten
Importiert JSON-Dateien und erstellt Entitäten für Gesichter, Personen, Bilder und Metadaten
"""

from __future__ import annotations
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j-Treiber nicht verfügbar. Installieren Sie mit: pip install neo4j")

class Neo4jConnector:
    """Neo4j-Datenbankanbindung für Gesichtserkennungs-Daten"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        """
        Initialisiert Neo4j-Verbindung
        
        Args:
            uri: Neo4j-Verbindungs-URI
            username: Benutzername
            password: Passwort
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j-Treiber nicht verfügbar. Installieren Sie mit: pip install neo4j")
        
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        
    def connect(self) -> bool:
        """Stellt Verbindung zur Neo4j-Datenbank her"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Teste Verbindung
            with self.driver.session() as session:
                session.run("RETURN 1")
            logging.info("Erfolgreich mit Neo4j verbunden")
            return True
        except Exception as e:
            logging.error(f"Fehler bei Neo4j-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Schließt Verbindung zur Neo4j-Datenbank"""
        if self.driver:
            self.driver.close()
            logging.info("Neo4j-Verbindung geschlossen")
    
    def create_constraints_and_indexes(self):
        """Erstellt Constraints und Indizes für optimale Performance"""
        constraints_and_indexes = [
            # Constraints
            "CREATE CONSTRAINT image_id_unique IF NOT EXISTS FOR (i:Image) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT face_id_unique IF NOT EXISTS FOR (f:Face) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            
            # Indizes
            "CREATE INDEX image_filename IF NOT EXISTS FOR (i:Image) ON (i.filename)",
            "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX face_quality IF NOT EXISTS FOR (f:Face) ON (f.quality_score)",
            "CREATE INDEX face_emotion IF NOT EXISTS FOR (f:Face) ON (f.emotion)",
            "CREATE INDEX face_age IF NOT EXISTS FOR (f:Face) ON (f.age)",
            "CREATE INDEX face_gender IF NOT EXISTS FOR (f:Face) ON (f.gender)",
            "CREATE INDEX location_country IF NOT EXISTS FOR (l:Location) ON (l.country)",
            "CREATE INDEX image_datetime IF NOT EXISTS FOR (i:Image) ON (i.datetime)"
        ]
        
        with self.driver.session() as session:
            for query in constraints_and_indexes:
                try:
                    session.run(query)
                except Exception as e:
                    logging.warning(f"Fehler beim Erstellen von Constraint/Index: {e}")
    
    def import_json_data(self, json_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Importiert JSON-Daten in Neo4j
        
        Args:
            json_data: Liste von Bild-Analyse-Daten
            
        Returns:
            Dictionary mit Import-Statistiken
        """
        if not self.driver:
            raise RuntimeError("Keine Verbindung zur Neo4j-Datenbank")
        
        stats = {
            'images_created': 0,
            'faces_created': 0,
            'persons_created': 0,
            'locations_created': 0,
            'relationships_created': 0
        }
        
        with self.driver.session() as session:
            for image_data in json_data:
                try:
                    # Erstelle Image-Entität
                    image_id = self._create_image_entity(session, image_data)
                    if image_id:
                        stats['images_created'] += 1
                    
                    # Erstelle Location-Entität (falls vorhanden)
                    location_id = self._create_location_entity(session, image_data.get('location'))
                    if location_id:
                        stats['locations_created'] += 1
                        # Verknüpfe Image mit Location
                        self._create_relationship(session, image_id, location_id, "TAKEN_AT")
                        stats['relationships_created'] += 1
                    
                    # Verarbeite Gesichter
                    for person_data in image_data.get('persons', []):
                        # Erstelle Face-Entität
                        face_id = self._create_face_entity(session, person_data, image_id)
                        if face_id:
                            stats['faces_created'] += 1
                        
                        # Erstelle Person-Entität (falls Name vorhanden)
                        if person_data.get('name'):
                            person_id = self._create_person_entity(session, person_data)
                            if person_id:
                                stats['persons_created'] += 1
                                # Verknüpfe Face mit Person
                                self._create_relationship(session, face_id, person_id, "BELONGS_TO")
                                stats['relationships_created'] += 1
                        
                        # Verknüpfe Face mit Image
                        if face_id and image_id:
                            self._create_relationship(session, face_id, image_id, "APPEARS_IN")
                            stats['relationships_created'] += 1
                
                except Exception as e:
                    logging.error(f"Fehler beim Importieren von Bild {image_data.get('image', 'unknown')}: {e}")
        
        return stats
    
    def _create_image_entity(self, session, image_data: Dict[str, Any]) -> Optional[str]:
        """Erstellt Image-Entität in Neo4j"""
        image_id = str(uuid.uuid4())
        
        # Extrahiere Metadaten
        metadata = image_data.get('metadata', {})
        
        query = """
        CREATE (i:Image {
            id: $id,
            filename: $filename,
            datetime: $datetime,
            camera_make: $camera_make,
            camera_model: $camera_model,
            lens: $lens,
            focal_length: $focal_length,
            f_number: $f_number,
            iso: $iso,
            exposure_time: $exposure_time,
            image_width: $image_width,
            image_height: $image_height,
            created_at: datetime()
        })
        RETURN i.id as id
        """
        
        result = session.run(query, {
            'id': image_id,
            'filename': image_data.get('image', ''),
            'datetime': metadata.get('datetime'),
            'camera_make': metadata.get('camera_make'),
            'camera_model': metadata.get('camera_model'),
            'lens': metadata.get('lens'),
            'focal_length': metadata.get('focal_length'),
            'f_number': metadata.get('f_number'),
            'iso': metadata.get('iso'),
            'exposure_time': metadata.get('exposure_time'),
            'image_width': metadata.get('image_width'),
            'image_height': metadata.get('image_height')
        })
        
        record = result.single()
        return record['id'] if record else None
    
    def _create_face_entity(self, session, person_data: Dict[str, Any], image_id: str) -> Optional[str]:
        """Erstellt Face-Entität in Neo4j"""
        face_id = str(uuid.uuid4())
        
        # Extrahiere Bounding Box
        bbox = person_data.get('bbox', [])
        
        query = """
        CREATE (f:Face {
            id: $id,
            age: $age,
            gender: $gender,
            emotion: $emotion,
            quality_score: $quality_score,
            eye_status: $eye_status,
            mouth_status: $mouth_status,
            bbox_x1: $bbox_x1,
            bbox_y1: $bbox_y1,
            bbox_x2: $bbox_x2,
            bbox_y2: $bbox_y2,
            similarity: $similarity,
            created_at: datetime()
        })
        RETURN f.id as id
        """
        
        result = session.run(query, {
            'id': face_id,
            'age': person_data.get('age'),
            'gender': person_data.get('gender'),
            'emotion': person_data.get('emotion'),
            'quality_score': person_data.get('quality_score'),
            'eye_status': person_data.get('eye_status'),
            'mouth_status': person_data.get('mouth_status'),
            'bbox_x1': bbox[0] if len(bbox) > 0 else None,
            'bbox_y1': bbox[1] if len(bbox) > 1 else None,
            'bbox_x2': bbox[2] if len(bbox) > 2 else None,
            'bbox_y2': bbox[3] if len(bbox) > 3 else None,
            'similarity': person_data.get('similarity')
        })
        
        record = result.single()
        return record['id'] if record else None
    
    def _create_person_entity(self, session, person_data: Dict[str, Any]) -> Optional[str]:
        """Erstellt Person-Entität in Neo4j"""
        person_id = str(uuid.uuid4())
        
        query = """
        MERGE (p:Person {name: $name})
        ON CREATE SET 
            p.id = $id,
            p.created_at = datetime(),
            p.first_seen = datetime()
        ON MATCH SET 
            p.last_seen = datetime()
        RETURN p.id as id
        """
        
        result = session.run(query, {
            'id': person_id,
            'name': person_data.get('name')
        })
        
        record = result.single()
        return record['id'] if record else None
    
    def _create_location_entity(self, session, location_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Erstellt Location-Entität in Neo4j"""
        if not location_data:
            return None
        
        location_id = str(uuid.uuid4())
        
        query = """
        CREATE (l:Location {
            id: $id,
            full_address: $full_address,
            country: $country,
            state: $state,
            city: $city,
            latitude: $latitude,
            longitude: $longitude,
            created_at: datetime()
        })
        RETURN l.id as id
        """
        
        result = session.run(query, {
            'id': location_id,
            'full_address': location_data.get('full_address'),
            'country': location_data.get('country'),
            'state': location_data.get('state'),
            'city': location_data.get('city'),
            'latitude': location_data.get('latitude'),
            'longitude': location_data.get('longitude')
        })
        
        record = result.single()
        return record['id'] if record else None
    
    def _create_relationship(self, session, from_id: str, to_id: str, relationship_type: str, properties: Dict = None):
        """Erstellt Beziehung zwischen Entitäten"""
        if not from_id or not to_id:
            return
        
        properties = properties or {}
        properties['created_at'] = datetime.now().isoformat()
        
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $from_id AND b.id = $to_id
        CREATE (a)-[r:{relationship_type} $properties]->(b)
        RETURN r
        """
        
        session.run(query, {
            'from_id': from_id,
            'to_id': to_id,
            'properties': properties
        })
    
    def query_faces_by_person(self, person_name: str) -> List[Dict[str, Any]]:
        """Sucht alle Gesichter einer Person"""
        query = """
        MATCH (p:Person {name: $name})-[:BELONGS_TO]-(f:Face)-[:APPEARS_IN]-(i:Image)
        RETURN f, i, p
        ORDER BY i.datetime DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, {'name': person_name})
            return [record.data() for record in result]
    
    def query_faces_by_emotion(self, emotion: str) -> List[Dict[str, Any]]:
        """Sucht alle Gesichter mit bestimmter Emotion"""
        query = """
        MATCH (f:Face {emotion: $emotion})-[:APPEARS_IN]-(i:Image)
        OPTIONAL MATCH (f)-[:BELONGS_TO]-(p:Person)
        RETURN f, i, p
        ORDER BY f.quality_score DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, {'emotion': emotion})
            return [record.data() for record in result]
    
    def query_faces_by_location(self, country: str = None, city: str = None) -> List[Dict[str, Any]]:
        """Sucht alle Gesichter an bestimmten Orten"""
        where_clause = []
        params = {}
        
        if country:
            where_clause.append("l.country = $country")
            params['country'] = country
        
        if city:
            where_clause.append("l.city = $city")
            params['city'] = city
        
        where_str = " AND ".join(where_clause) if where_clause else "1=1"
        
        query = f"""
        MATCH (f:Face)-[:APPEARS_IN]-(i:Image)-[:TAKEN_AT]-(l:Location)
        WHERE {where_str}
        OPTIONAL MATCH (f)-[:BELONGS_TO]-(p:Person)
        RETURN f, i, l, p
        ORDER BY i.datetime DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, params)
            return [record.data() for record in result]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Datenbank-Statistiken zurück"""
        queries = {
            'total_images': "MATCH (i:Image) RETURN count(i) as count",
            'total_faces': "MATCH (f:Face) RETURN count(f) as count",
            'total_persons': "MATCH (p:Person) RETURN count(p) as count",
            'total_locations': "MATCH (l:Location) RETURN count(l) as count",
            'emotion_distribution': "MATCH (f:Face) RETURN f.emotion as emotion, count(f) as count",
            'gender_distribution': "MATCH (f:Face) RETURN f.gender as gender, count(f) as count",
            'quality_distribution': "MATCH (f:Face) RETURN avg(f.quality_score) as avg_quality, min(f.quality_score) as min_quality, max(f.quality_score) as max_quality"
        }
        
        stats = {}
        with self.driver.session() as session:
            for key, query in queries.items():
                result = session.run(query)
                if key in ['emotion_distribution', 'gender_distribution']:
                    stats[key] = {record['emotion'] or record['gender']: record['count'] for record in result}
                else:
                    record = result.single()
                    stats[key] = record['count'] if record else 0
        
        return stats
    
    def clear_database(self):
        """Löscht alle Daten aus der Datenbank"""
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query)
        logging.info("Datenbank geleert")
    
    def execute_cypher_query(self, query: str, parameters: Dict = None) -> List[Dict[str, Any]]:
        """Führt eine Cypher-Abfrage aus und gibt Ergebnisse zurück"""
        if not self.driver:
            raise RuntimeError("Keine Verbindung zur Neo4j-Datenbank")
        
        parameters = parameters or {}
        
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
    
    def get_graph_data(self, query: str, parameters: Dict = None) -> Dict[str, Any]:
        """
        Führt eine Cypher-Abfrage aus und gibt Graph-Daten für Visualisierung zurück
        
        Returns:
            Dictionary mit 'nodes' und 'edges' für Graph-Visualisierung
        """
        if not self.driver:
            raise RuntimeError("Keine Verbindung zur Neo4j-Datenbank")
        
        parameters = parameters or {}
        
        with self.driver.session() as session:
            result = session.run(query, parameters)
            
            nodes = []
            edges = []
            node_ids = set()
            edge_ids = set()
            
            for record in result:
                # Debug: Zeige Record-Struktur
                logging.debug(f"Record: {record}")
                
                # Verarbeite alle Felder im Record
                for key, value in record.items():
                    logging.debug(f"Key: {key}, Value type: {type(value)}, Value: {value}")
                    
                    # Prüfe ob es ein Neo4j-Node-Objekt ist
                    if hasattr(value, 'element_id') and hasattr(value, 'labels') and hasattr(value, 'properties'):
                        # Neo4j-Node-Objekt
                        logging.debug(f"Found Neo4j Node: {value}")
                        self._process_neo4j_node(value, nodes, node_ids)
                    
                    # Prüfe ob es ein Neo4j-Relationship-Objekt ist
                    elif hasattr(value, 'type') and hasattr(value, 'nodes'):
                        # Neo4j-Relationship-Objekt
                        logging.debug(f"Found Neo4j Relationship: {value}")
                        self._process_neo4j_relationship(value, edges, edge_ids)
                    
                    # Prüfe ob es ein Tuple ist (Beziehung in Tuple-Format)
                    elif isinstance(value, tuple) and len(value) == 3:
                        # Tuple-Format: (start_node, relationship_type, end_node)
                        logging.debug(f"Found Tuple Relationship: {value}")
                        self._process_tuple_relationship(value, nodes, edges, node_ids, edge_ids)
                    
                    # Spezielle Behandlung für verschachtelte Daten (z.B. {"n": {...}})
                    elif isinstance(value, dict):
                        # Prüfe ob es ein verschachteltes Format ist (z.B. {"n": {...}})
                        if len(value) == 1 and any(k in value for k in ['n', 'r', 'a', 'b', 'f', 'i', 'p', 'l']):
                            # Extrahiere den verschachtelten Wert
                            nested_value = list(value.values())[0]
                            logging.debug(f"Found nested value: {nested_value}")
                            
                            if isinstance(nested_value, dict):
                                # Verarbeite den verschachtelten Wert
                                self._process_node_or_relationship(nested_value, nodes, edges, node_ids, edge_ids)
                        else:
                            # Verarbeite direktes Dictionary
                            self._process_node_or_relationship(value, nodes, edges, node_ids, edge_ids)
            
            logging.info(f"Extracted {len(nodes)} nodes and {len(edges)} edges")
            return {
                'nodes': nodes,
                'edges': edges,
                'query': query,
                'parameters': parameters
            }
    
    def _process_neo4j_node(self, node_obj, nodes: list, node_ids: set):
        """Verarbeitet ein Neo4j-Node-Objekt"""
        try:
            # Extrahiere Node-ID
            node_id = node_obj.element_id or str(node_obj.id) if hasattr(node_obj, 'id') else None
            logging.debug(f"Neo4j Node ID: {node_id}")
            
            if node_id and node_id not in node_ids:
                node_ids.add(node_id)
                
                # Extrahiere Labels
                labels = list(node_obj.labels) if hasattr(node_obj, 'labels') else []
                node_type = labels[0] if labels else 'Unknown'
                
                # Extrahiere Eigenschaften
                properties = dict(node_obj.properties) if hasattr(node_obj, 'properties') else {}
                
                logging.debug(f"Neo4j Node type: {node_type}, Labels: {labels}")
                
                # Erstelle Node-Daten
                node_data = {
                    'id': node_id,
                    'label': self._get_node_label(properties, node_type),
                    'type': node_type,
                    'color': self._get_node_color(node_type),
                    'size': self._get_node_size(node_type),
                    'properties': properties
                }
                nodes.append(node_data)
                logging.debug(f"Added Neo4j node: {node_data}")
        except Exception as e:
            logging.error(f"Fehler beim Verarbeiten des Neo4j-Nodes: {e}")
    
    def _process_neo4j_relationship(self, rel_obj, edges: list, edge_ids: set):
        """Verarbeitet ein Neo4j-Relationship-Objekt"""
        try:
            # Extrahiere Beziehungsdaten
            rel_type = rel_obj.type if hasattr(rel_obj, 'type') else 'RELATES_TO'
            
            # Extrahiere Start- und End-Node aus dem nodes-Tuple
            if hasattr(rel_obj, 'nodes') and len(rel_obj.nodes) == 2:
                start_node, end_node = rel_obj.nodes
                start_id = start_node.element_id if hasattr(start_node, 'element_id') else None
                end_id = end_node.element_id if hasattr(end_node, 'element_id') else None
            else:
                start_id = rel_obj.start_node.element_id if hasattr(rel_obj, 'start_node') else None
                end_id = rel_obj.end_node.element_id if hasattr(rel_obj, 'end_node') else None
            
            if start_id and end_id and rel_type:
                edge_id = f"{start_id}-{rel_type}-{end_id}"
                
                if edge_id not in edge_ids:
                    edge_ids.add(edge_id)
                    
                    # Extrahiere Eigenschaften
                    properties = dict(rel_obj.properties) if hasattr(rel_obj, 'properties') else {}
                    
                    edge_data = {
                        'id': edge_id,
                        'source': start_id,
                        'target': end_id,
                        'type': rel_type,
                        'properties': properties
                    }
                    edges.append(edge_data)
                    logging.debug(f"Added Neo4j relationship: {edge_data}")
        except Exception as e:
            logging.error(f"Fehler beim Verarbeiten der Neo4j-Beziehung: {e}")
    
    def _process_tuple_relationship(self, tuple_value, nodes: list, edges: list, node_ids: set, edge_ids: set):
        """Verarbeitet eine Beziehung im Tuple-Format: (start_node, relationship_type, end_node)"""
        try:
            start_node_data, rel_type, end_node_data = tuple_value
            
            # Verarbeite Start-Node
            if isinstance(start_node_data, dict):
                self._process_node_or_relationship(start_node_data, nodes, edges, node_ids, edge_ids)
            
            # Verarbeite End-Node
            if isinstance(end_node_data, dict):
                self._process_node_or_relationship(end_node_data, nodes, edges, node_ids, edge_ids)
            
            # Erstelle Beziehung
            if isinstance(start_node_data, dict) and isinstance(end_node_data, dict):
                start_id = start_node_data.get('id')
                end_id = end_node_data.get('id')
                
                if start_id and end_id and rel_type:
                    edge_id = f"{start_id}-{rel_type}-{end_id}"
                    
                    if edge_id not in edge_ids:
                        edge_ids.add(edge_id)
                        
                        edge_data = {
                            'id': edge_id,
                            'source': start_id,
                            'target': end_id,
                            'type': rel_type,
                            'properties': {}
                        }
                        edges.append(edge_data)
                        logging.debug(f"Added tuple relationship: {edge_data}")
        except Exception as e:
            logging.error(f"Fehler beim Verarbeiten der Tuple-Beziehung: {e}")
    
    def _process_node_or_relationship(self, value: dict, nodes: list, edges: list, node_ids: set, edge_ids: set):
        """Verarbeitet einen Wert als Node oder Beziehung"""
        # Debug: Prüfe ob es ein Node ist
        is_node = self._is_node(value)
        logging.debug(f"Is node: {is_node}, Value keys: {list(value.keys())}")
        
        # Prüfe ob es ein Node ist (verschiedene Neo4j-Formate)
        if is_node:
            node_id = self._get_node_id(value)
            logging.debug(f"Node ID: {node_id}")
            
            if node_id and node_id not in node_ids:
                node_ids.add(node_id)
                
                # Bestimme Node-Typ und Farbe
                labels = self._get_node_labels(value)
                node_type = labels[0] if labels else 'Unknown'
                color = self._get_node_color(node_type)
                
                logging.debug(f"Node type: {node_type}, Labels: {labels}")
                
                # Erstelle Node-Daten
                node_data = {
                    'id': node_id,
                    'label': self._get_node_label(value, node_type),
                    'type': node_type,
                    'color': color,
                    'size': self._get_node_size(node_type),
                    'properties': self._get_node_properties(value)
                }
                nodes.append(node_data)
                logging.debug(f"Added node: {node_data}")
        
        # Prüfe ob es eine Beziehung ist
        elif self._is_relationship(value):
            start_id = self._get_relationship_start(value)
            end_id = self._get_relationship_end(value)
            rel_type = self._get_relationship_type(value)
            
            if start_id and end_id and rel_type:
                edge_id = f"{start_id}-{rel_type}-{end_id}"
                
                if edge_id not in edge_ids:
                    edge_ids.add(edge_id)
                    
                    edge_data = {
                        'id': edge_id,
                        'source': start_id,
                        'target': end_id,
                        'type': rel_type,
                        'properties': self._get_relationship_properties(value)
                    }
                    edges.append(edge_data)
                    logging.debug(f"Added edge: {edge_data}")
    
    def _is_node(self, value: dict) -> bool:
        """Prüft ob ein Dictionary ein Neo4j-Node ist"""
        # Verschiedene Neo4j-Formate
        return (
            ('id' in value and 'labels' in value) or  # Standard-Format
            ('elementId' in value) or  # Neo4j 5.x Format
            ('identity' in value and 'labels' in value) or  # Ältere Versionen
            ('id' in value and any(key in value for key in ['filename', 'name', 'age', 'gender', 'country', 'city', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'quality_score', 'emotion', 'eye_status', 'mouth_status'])) or  # Fallback für Daten ohne labels
            ('id' in value and 'created_at' in value)  # Fallback für alle Knoten mit ID und created_at
        )
    
    def _is_relationship(self, value: dict) -> bool:
        """Prüft ob ein Dictionary eine Neo4j-Beziehung ist"""
        return (
            ('type' in value and 'start' in value and 'end' in value) or  # Standard-Format
            ('type' in value and 'startNodeElementId' in value and 'endNodeElementId' in value) or  # Neo4j 5.x
            ('type' in value and 'startNode' in value and 'endNode' in value)  # Ältere Versionen
        )
    
    def _get_node_id(self, value: dict) -> str:
        """Extrahiert Node-ID aus verschiedenen Neo4j-Formaten"""
        return (
            value.get('id') or 
            value.get('elementId') or 
            value.get('identity') or 
            str(value.get('id', ''))
        )
    
    def _get_node_labels(self, value: dict) -> list:
        """Extrahiert Node-Labels aus verschiedenen Neo4j-Formaten"""
        labels = value.get('labels', [])
        if not labels:
            # Fallback: Versuche Typ aus Eigenschaften zu bestimmen
            if 'filename' in value:
                labels = ['Image']
            elif 'name' in value and 'age' not in value:
                labels = ['Person']
            elif 'age' in value or 'gender' in value or 'bbox_x1' in value or 'quality_score' in value:
                labels = ['Face']
            elif 'country' in value or 'city' in value:
                labels = ['Location']
            else:
                labels = ['Unknown']
        return labels
    
    def _get_node_properties(self, value: dict) -> dict:
        """Extrahiert Node-Eigenschaften"""
        exclude_keys = ['id', 'labels', 'elementId', 'identity']
        return {k: v for k, v in value.items() if k not in exclude_keys}
    
    def _get_relationship_start(self, value: dict) -> str:
        """Extrahiert Start-Node-ID einer Beziehung"""
        return (
            value.get('start') or 
            value.get('startNodeElementId') or 
            value.get('startNode') or 
            str(value.get('start', ''))
        )
    
    def _get_relationship_end(self, value: dict) -> str:
        """Extrahiert End-Node-ID einer Beziehung"""
        return (
            value.get('end') or 
            value.get('endNodeElementId') or 
            value.get('endNode') or 
            str(value.get('end', ''))
        )
    
    def _get_relationship_type(self, value: dict) -> str:
        """Extrahiert Beziehungstyp"""
        return value.get('type', 'RELATES_TO')
    
    def _get_relationship_properties(self, value: dict) -> dict:
        """Extrahiert Beziehungs-Eigenschaften"""
        exclude_keys = ['type', 'start', 'end', 'startNodeElementId', 'endNodeElementId', 'startNode', 'endNode']
        return {k: v for k, v in value.items() if k not in exclude_keys}
    
    def _get_node_color(self, node_type: str) -> str:
        """Gibt Farbe für Node-Typ zurück"""
        colors = {
            'Image': '#FF6B6B',      # Rot
            'Face': '#4ECDC4',       # Türkis
            'Person': '#45B7D1',     # Blau
            'Location': '#96CEB4',   # Grün
            'Unknown': '#D3D3D3'     # Grau
        }
        return colors.get(node_type, colors['Unknown'])
    
    def _get_node_size(self, node_type: str) -> int:
        """Gibt Größe für Node-Typ zurück"""
        sizes = {
            'Image': 25,
            'Face': 20,
            'Person': 30,
            'Location': 25,
            'Unknown': 15
        }
        return sizes.get(node_type, sizes['Unknown'])
    
    def _get_node_label(self, node_data: Dict, node_type: str) -> str:
        """Erstellt Label für Node"""
        if node_type == 'Person':
            return node_data.get('name', 'Unknown Person')
        elif node_type == 'Image':
            return node_data.get('filename', 'Unknown Image')
        elif node_type == 'Location':
            city = node_data.get('city', '')
            country = node_data.get('country', '')
            return f"{city}, {country}" if city and country else (city or country or 'Unknown Location')
        elif node_type == 'Face':
            age = node_data.get('age', '')
            gender = node_data.get('gender', '')
            emotion = node_data.get('emotion', '')
            return f"{age}J {gender} {emotion}".strip()
        else:
            return f"{node_type} {node_data.get('id', '')[:8]}"
    
    def get_sample_queries(self) -> List[Dict[str, str]]:
        """Gibt Beispiel-Cypher-Abfragen zurück"""
        return [
            {
                'name': 'Alle Knoten anzeigen',
                'query': 'MATCH (n) RETURN n LIMIT 20',
                'description': 'Zeigt alle Knoten in der Datenbank (Bilder, Gesichter, Personen, Standorte)'
            },
            {
                'name': 'Alle Bilder',
                'query': 'MATCH (i:Image) RETURN i LIMIT 20',
                'description': 'Zeigt alle Bild-Knoten'
            },
            {
                'name': 'Alle Gesichter',
                'query': 'MATCH (f:Face) RETURN f LIMIT 20',
                'description': 'Zeigt alle Gesichts-Knoten'
            },
            {
                'name': 'Alle Personen',
                'query': 'MATCH (p:Person) RETURN p LIMIT 20',
                'description': 'Zeigt alle Personen-Knoten'
            },
            {
                'name': 'Alle Standorte',
                'query': 'MATCH (l:Location) RETURN l LIMIT 20',
                'description': 'Zeigt alle Standort-Knoten'
            },
            {
                'name': 'Gesichter mit hoher Qualität',
                'query': 'MATCH (f:Face) WHERE f.quality_score > 0.5 RETURN f LIMIT 20',
                'description': 'Zeigt Gesichter mit Qualitätsbewertung über 0.5'
            },
            {
                'name': 'Gesichter mit Emotionen',
                'query': 'MATCH (f:Face) WHERE f.emotion IS NOT NULL AND f.emotion <> "unknown" RETURN f LIMIT 20',
                'description': 'Zeigt Gesichter mit erkannten Emotionen'
            },
            {
                'name': 'Alle Beziehungen',
                'query': 'MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 30',
                'description': 'Zeigt alle Beziehungen in der Datenbank'
            },
            {
                'name': 'Bilder mit Gesichtern (falls Beziehungen existieren)',
                'query': 'MATCH (f:Face)-[r:APPEARS_IN]->(i:Image) RETURN f, r, i LIMIT 20',
                'description': 'Zeigt Gesichter und ihre Bilder (nur wenn Beziehungen vorhanden)'
            },
            {
                'name': 'Personen mit Gesichtern (falls Beziehungen existieren)',
                'query': 'MATCH (p:Person)<-[r:BELONGS_TO]-(f:Face) RETURN p, r, f LIMIT 20',
                'description': 'Zeigt Personen und ihre Gesichter (nur wenn Beziehungen vorhanden)'
            },
            {
                'name': 'Alle Beziehungen (n1->n2)',
                'query': 'MATCH (n1)-[r]->(n2) RETURN r, n1, n2 LIMIT 25',
                'description': 'Zeigt alle Beziehungen zwischen Knoten (wie im Desktop getestet)'
            }
        ]

class Neo4jManager:
    """Manager-Klasse für Neo4j-Operationen"""
    
    def __init__(self):
        self.connector = None
        self.connected = False
    
    def connect(self, uri: str = "bolt://localhost:7687", 
                username: str = "neo4j", 
                password: str = "password") -> bool:
        """Stellt Verbindung zur Neo4j-Datenbank her"""
        try:
            self.connector = Neo4jConnector(uri, username, password)
            self.connected = self.connector.connect()
            
            if self.connected:
                self.connector.create_constraints_and_indexes()
            
            return self.connected
        except Exception as e:
            logging.error(f"Fehler bei Neo4j-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Schließt Verbindung zur Neo4j-Datenbank"""
        if self.connector:
            self.connector.disconnect()
            self.connected = False
    
    def import_json_file(self, json_file_path: str) -> Dict[str, int]:
        """Importiert JSON-Datei in Neo4j"""
        if not self.connected:
            raise RuntimeError("Keine Verbindung zur Neo4j-Datenbank")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return self.connector.import_json_data(data)
            else:
                return self.connector.import_json_data([data])
        except Exception as e:
            logging.error(f"Fehler beim Importieren der JSON-Datei: {e}")
            return {}
    
    def import_json_data(self, json_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Importiert JSON-Daten in Neo4j"""
        if not self.connected:
            raise RuntimeError("Keine Verbindung zur Neo4j-Datenbank")
        
        return self.connector.import_json_data(json_data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Datenbank-Statistiken zurück"""
        if not self.connected:
            return {}
        
        return self.connector.get_statistics()
    
    def query_faces_by_person(self, person_name: str) -> List[Dict[str, Any]]:
        """Sucht alle Gesichter einer Person"""
        if not self.connected:
            return []
        
        return self.connector.query_faces_by_person(person_name)
    
    def query_faces_by_emotion(self, emotion: str) -> List[Dict[str, Any]]:
        """Sucht alle Gesichter mit bestimmter Emotion"""
        if not self.connected:
            return []
        
        return self.connector.query_faces_by_emotion(emotion)
    
    def query_faces_by_location(self, country: str = None, city: str = None) -> List[Dict[str, Any]]:
        """Sucht alle Gesichter an bestimmten Orten"""
        if not self.connected:
            return []
        
        return self.connector.query_faces_by_location(country, city)
    
    def clear_database(self):
        """Löscht alle Daten aus der Datenbank"""
        if not self.connected:
            return
        
        self.connector.clear_database()
    
    def execute_cypher_query(self, query: str, parameters: Dict = None) -> List[Dict[str, Any]]:
        """Führt eine Cypher-Abfrage aus"""
        if not self.connected:
            return []
        
        return self.connector.execute_cypher_query(query, parameters)
    
    def get_graph_data(self, query: str, parameters: Dict = None) -> Dict[str, Any]:
        """Gibt Graph-Daten für Visualisierung zurück"""
        if not self.connected:
            return {'nodes': [], 'edges': [], 'query': query, 'parameters': parameters}
        
        return self.connector.get_graph_data(query, parameters)
    
    def get_sample_queries(self) -> List[Dict[str, str]]:
        """Gibt Beispiel-Cypher-Abfragen zurück"""
        if not self.connected:
            return []
        
        return self.connector.get_sample_queries()
