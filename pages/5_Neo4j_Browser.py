"""
Neo4j Browser - Graph-Visualisierung
Interaktiver Browser für Neo4j-Datenbank mit Graph-Visualisierung
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import networkx as nx
import logging
import sys
import os

# Füge app-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.neo4j_connector import Neo4jManager
from streamlit_styles import apply_custom_css

# Wende kleinere Schriftgrößen an
apply_custom_css()

# Aktiviere Debug-Logging
logging.basicConfig(level=logging.DEBUG)

st.set_page_config(page_title="Neo4j Browser", layout="wide")

st.title("Neo4j Browser")
st.caption("Interaktiver Graph-Browser für Neo4j-Datenbank")

# Initialisiere Neo4j Manager
if "neo4j_manager" not in st.session_state:
    st.session_state.neo4j_manager = Neo4jManager()

# Prüfe Verbindung
if not st.session_state.neo4j_manager.connected:
    st.error("Keine Verbindung zur Neo4j-Datenbank. Bitte verbinden Sie sich zuerst in der Neo4j-Seite.")
    st.info("Gehen Sie zur 'Neo4j'-Seite und stellen Sie eine Verbindung her.")
    st.stop()

# Sidebar für Abfrage-Einstellungen
with st.sidebar:
    st.header("Abfrage-Einstellungen")
    
    # Beispiel-Abfragen
    sample_queries = st.session_state.neo4j_manager.get_sample_queries()
    
    st.subheader("Beispiel-Abfragen")
    selected_sample = st.selectbox(
        "Wählen Sie eine Beispiel-Abfrage:",
        [""] + [q['name'] for q in sample_queries],
        help="Wählen Sie eine vordefinierte Abfrage aus"
    )
    
    if selected_sample:
        selected_query = next(q for q in sample_queries if q['name'] == selected_sample)
        st.text_area("Beschreibung:", selected_query['description'], height=60, disabled=True)
    
    # Graph-Einstellungen
    st.subheader("Graph-Einstellungen")
    
    max_nodes = st.slider("Max. Knoten", 10, 100, 50, help="Begrenzt die Anzahl der angezeigten Knoten")
    node_size_multiplier = st.slider("Knoten-Größe", 0.5, 3.0, 1.0, 0.1, help="Skaliert die Knoten-Größe")
    show_labels = st.checkbox("Labels anzeigen", value=True, help="Zeigt Labels auf den Knoten")
    show_properties = st.checkbox("Eigenschaften anzeigen", value=False, help="Zeigt Eigenschaften in Tooltips")
    
    # Layout-Optionen
    layout_type = st.selectbox(
        "Layout-Typ",
        ["spring", "circular", "hierarchical", "force"],
        help="Bestimmt das Layout des Graphen"
    )

# Hauptinhalt
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Cypher-Abfrage")
    
    # Abfrage-Eingabe
    if selected_sample:
        default_query = selected_query['query']
    else:
        default_query = "MATCH (n) RETURN n LIMIT 20"
    
    query = st.text_area(
        "Cypher-Abfrage:",
        value=default_query,
        height=150,
        help="Geben Sie eine Cypher-Abfrage ein oder wählen Sie eine Beispiel-Abfrage"
    )
    
    # Abfrage-Parameter
    st.subheader("Abfrage-Parameter")
    param_input = st.text_area(
        "Parameter (JSON):",
        value="{}",
        height=100,
        help="Geben Sie Parameter als JSON ein (z.B. {\"name\": \"Max Mustermann\"})"
    )
    
    # Abfrage ausführen
    col_exec1, col_exec2, col_exec3 = st.columns([1, 1, 2])
    with col_exec1:
        execute_query = st.button("Abfrage ausführen", type="primary")
    
    with col_exec2:
        debug_mode = st.checkbox("Debug-Modus", help="Zeigt Rohdaten der Abfrage an")
    
    with col_exec3:
        if st.button("Graph zurücksetzen"):
            if "graph_data" in st.session_state:
                del st.session_state.graph_data
            st.rerun()

with col2:
    st.header("Abfrage-Info")
    
    if selected_sample:
        st.info(f"**Ausgewählte Abfrage:** {selected_sample}")
        st.write(f"**Beschreibung:** {selected_query['description']}")
    
    # Abfrage-Statistiken
    if "graph_data" in st.session_state:
        graph_data = st.session_state.graph_data
        st.metric("Knoten", len(graph_data.get('nodes', [])))
        st.metric("Kanten", len(graph_data.get('edges', [])))
        
        # Node-Typ-Verteilung
        if graph_data.get('nodes'):
            node_types = {}
            for node in graph_data['nodes']:
                node_type = node.get('type', 'Unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node_types:
                st.subheader("Knoten-Typen")
                for node_type, count in node_types.items():
                    st.write(f"• {node_type}: {count}")

# Abfrage ausführen
if execute_query:
    try:
        # Parse Parameter
        try:
            parameters = json.loads(param_input) if param_input.strip() else {}
        except json.JSONDecodeError:
            st.error("Ungültige JSON-Parameter")
            parameters = {}
        
        with st.spinner("Führe Abfrage aus..."):
            # Führe Abfrage aus
            graph_data = st.session_state.neo4j_manager.get_graph_data(query, parameters)
            
            # Debug-Modus: Zeige Rohdaten
            if debug_mode:
                st.subheader("Debug-Informationen")
                
                # Zeige auch die Rohdaten der Abfrage
                try:
                    raw_results = st.session_state.neo4j_manager.execute_cypher_query(query, parameters)
                    st.write("**Rohdaten der Abfrage:**")
                    st.json(raw_results[:5])  # Zeige nur die ersten 5 Ergebnisse
                    
                    if raw_results:
                        st.write(f"**Anzahl Rohdaten:** {len(raw_results)}")
                        st.write("**Erste Rohdaten-Struktur:**")
                        if raw_results[0]:
                            for key, value in raw_results[0].items():
                                st.write(f"- {key}: {type(value).__name__} = {value}")
                except Exception as e:
                    st.error(f"Fehler beim Abrufen der Rohdaten: {e}")
                
                st.write("**Extrahierte Graph-Daten:**")
                st.json({
                    'nodes_count': len(graph_data.get('nodes', [])),
                    'edges_count': len(graph_data.get('edges', [])),
                    'sample_nodes': graph_data.get('nodes', [])[:3],
                    'sample_edges': graph_data.get('edges', [])[:3]
                })
                
                # Zusätzliche Debug-Informationen
                st.write("**Debug-Analyse der Rohdaten:**")
                if raw_results:
                    first_result = raw_results[0]
                    st.write("**Erste Rohdaten-Struktur:**")
                    for key, value in first_result.items():
                        st.write(f"- **{key}**: {type(value).__name__}")
                        if isinstance(value, dict):
                            st.write(f"  - Keys: {list(value.keys())}")
                            # Prüfe ob es ein Node ist
                            is_node = ('id' in value and any(k in value for k in ['filename', 'age', 'gender', 'bbox_x1', 'quality_score', 'created_at']))
                            st.write(f"  - Ist Node: {is_node}")
                            if is_node:
                                # Bestimme Typ
                                if 'filename' in value:
                                    node_type = 'Image'
                                elif 'age' in value or 'gender' in value or 'bbox_x1' in value:
                                    node_type = 'Face'
                                elif 'name' in value and 'age' not in value:
                                    node_type = 'Person'
                                elif 'country' in value or 'city' in value:
                                    node_type = 'Location'
                                else:
                                    node_type = 'Unknown'
                                st.write(f"  - Erkannte Typ: {node_type}")
            
            if graph_data.get('nodes'):
                st.session_state.graph_data = graph_data
                st.success(f"Abfrage erfolgreich! {len(graph_data['nodes'])} Knoten gefunden.")
            else:
                st.warning("Keine Knoten gefunden. Überprüfen Sie Ihre Abfrage.")
                if debug_mode:
                    st.info("Tipp: Aktivieren Sie den Debug-Modus, um die Rohdaten zu sehen und das Problem zu identifizieren.")
                
    except Exception as e:
        st.error(f"Fehler bei der Abfrage: {e}")

# Graph-Visualisierung
if "graph_data" in st.session_state:
    graph_data = st.session_state.graph_data
    
    if graph_data.get('nodes'):
        st.header("Graph-Visualisierung")
        
        # Erstelle NetworkX-Graph
        G = nx.Graph()
        
        # Füge Knoten hinzu
        for node in graph_data['nodes'][:max_nodes]:  # Begrenze auf max_nodes
            G.add_node(
                node['id'],
                label=node['label'],
                type=node['type'],
                color=node['color'],
                size=node['size'] * node_size_multiplier,
                properties=node.get('properties', {})
            )
        
        # Füge Kanten hinzu (falls vorhanden)
        for edge in graph_data.get('edges', []):
            G.add_edge(edge['source'], edge['target'])
        
        # Erstelle Layout
        if layout_type == "spring":
            pos = nx.spring_layout(G, k=3, iterations=50)
        elif layout_type == "circular":
            pos = nx.circular_layout(G)
        elif layout_type == "hierarchical":
            pos = nx.spring_layout(G, k=2, iterations=30)
        else:  # force
            pos = nx.spring_layout(G, k=1, iterations=100)
        
        # Erstelle Plotly-Graph
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Erstelle Kanten-Trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Erstelle Knoten-Trace
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        node_hover_text = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = G.nodes[node]
            node_text.append(node_data['label'] if show_labels else '')
            node_colors.append(node_data['color'])
            node_sizes.append(node_data['size'])
            
            # Hover-Text
            hover_parts = [f"<b>{node_data['label']}</b>", f"Typ: {node_data['type']}"]
            if show_properties and node_data.get('properties'):
                for key, value in node_data['properties'].items():
                    if value is not None:
                        hover_parts.append(f"{key}: {value}")
            node_hover_text.append("<br>".join(hover_parts))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text' if show_labels else 'markers',
            hoverinfo='text',
            hovertext=node_hover_text,
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )
        
        # Erstelle Figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Neo4j Graph-Visualisierung',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Interaktiver Graph - Zoomen und Verschieben möglich",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color='gray', size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white'
                       ))
        
        # Zeige Graph
        st.plotly_chart(fig, use_container_width=True, height=600)
        
        # Legende
        st.subheader("Legende")
        col_legend1, col_legend2, col_legend3, col_legend4 = st.columns(4)
        
        with col_legend1:
            st.markdown("**Image** - Bilder")
        with col_legend2:
            st.markdown("**Person** - Personen")
        with col_legend3:
            st.markdown("**Face** - Gesichter")
        with col_legend4:
            st.markdown("**Location** - Standorte")
        
        # Detaillierte Knoten-Informationen
        with st.expander("Knoten-Details", expanded=False):
            if graph_data.get('nodes'):
                # Erstelle DataFrame für Knoten
                nodes_df = pd.DataFrame([
                    {
                        'ID': node['id'][:8] + '...',
                        'Typ': node['type'],
                        'Label': node['label'],
                        'Eigenschaften': len(node.get('properties', {}))
                    }
                    for node in graph_data['nodes']
                ])
                
                st.dataframe(nodes_df, use_container_width=True)
                
                # Einzelne Knoten-Details
                selected_node = st.selectbox(
                    "Knoten auswählen:",
                    [f"{node['type']}: {node['label']}" for node in graph_data['nodes']]
                )
                
                if selected_node:
                    node_index = next(i for i, node in enumerate(graph_data['nodes']) 
                                    if f"{node['type']}: {node['label']}" == selected_node)
                    selected_node_data = graph_data['nodes'][node_index]
                    
                    st.json(selected_node_data)
    
    else:
        st.info("Keine Knoten zum Anzeigen verfügbar.")

# Abfrage-Historie
with st.expander("Abfrage-Historie", expanded=False):
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    
    # Füge aktuelle Abfrage zur Historie hinzu
    if execute_query and "graph_data" in st.session_state:
        current_query = {
            'query': query,
            'parameters': parameters,
            'nodes_found': len(graph_data.get('nodes', [])),
            'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Prüfe ob Abfrage bereits in Historie ist
        if not any(h['query'] == query for h in st.session_state.query_history):
            st.session_state.query_history.insert(0, current_query)
            # Begrenze Historie auf 10 Einträge
            st.session_state.query_history = st.session_state.query_history[:10]
    
    if st.session_state.query_history:
        for i, hist_query in enumerate(st.session_state.query_history):
            with st.container():
                col_hist1, col_hist2, col_hist3 = st.columns([3, 1, 1])
                
                with col_hist1:
                    st.code(hist_query['query'], language='cypher')
                
                with col_hist2:
                    st.write(f"**{hist_query['nodes_found']} Knoten**")
                
                with col_hist3:
                    st.write(f"**{hist_query['timestamp']}**")
                
                if st.button(f"Wiederholen", key=f"repeat_{i}"):
                    st.session_state.graph_data = st.session_state.neo4j_manager.get_graph_data(
                        hist_query['query'], 
                        hist_query['parameters']
                    )
                    st.rerun()
                
                st.divider()
    else:
        st.info("Noch keine Abfragen in der Historie.")

# Footer
st.divider()
st.caption("""
**Neo4j Browser - Graph-Visualisierung**

Dieser Browser ermöglicht es, Cypher-Abfragen auszuführen und die Ergebnisse als interaktiven Graph zu visualisieren.

**Verfügbare Features:**
- **Interaktive Graph-Visualisierung** mit Plotly
- **Verschiedene Layout-Typen** (Spring, Circular, Hierarchical, Force)
- **Anpassbare Darstellung** (Knoten-Größe, Labels, Eigenschaften)
- **Abfrage-Historie** für wiederholte Abfragen
- **Beispiel-Abfragen** für schnellen Einstieg

**Tipps:**
- Verwenden Sie LIMIT in Ihren Abfragen für bessere Performance
- Experimentieren Sie mit verschiedenen Layout-Typen
- Nutzen Sie die Hover-Funktion für detaillierte Informationen
- Speichern Sie nützliche Abfragen in der Historie
""")
