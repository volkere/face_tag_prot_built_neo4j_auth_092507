"""
Gemeinsame CSS-Styles für alle Streamlit-Pages
"""
import streamlit as st


def apply_custom_css():
    """
    Wendet kleinere Schriftgrößen auf die Streamlit-App an.
    Diese Funktion sollte in jeder Page aufgerufen werden.
    """
    st.markdown("""
    <style>
        /* Reduziere alle Schriftgrößen */
        html, body, [class*="css"] {
            font-size: 14px !important;
        }
        
        /* Titel */
        h1, .css-10trblm {
            font-size: 1.5rem !important;
        }
        
        /* Überschriften */
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 1rem !important;
        }
        
        /* Normaler Text */
        p, .stMarkdown, .css-nahz7x, div[data-testid="stMarkdownContainer"] {
            font-size: 0.85rem !important;
        }
        
        /* Input-Felder */
        .stTextInput label, .stSelectbox label, .stCheckbox label, .stRadio label {
            font-size: 0.8rem !important;
        }
        
        .stTextInput input, .stSelectbox select {
            font-size: 0.85rem !important;
        }
        
        /* Buttons */
        .stButton button {
            font-size: 0.85rem !important;
        }
        
        /* Tabelle */
        .dataframe, .stDataFrame, [data-testid="stDataFrame"] {
            font-size: 0.75rem !important;
        }
        
        /* Metriken */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
        }
        
        /* Sidebar */
        .css-1d391kg, [data-testid="stSidebar"] {
            font-size: 0.85rem !important;
        }
        
        /* Code-Blöcke */
        code, pre {
            font-size: 0.8rem !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-size: 0.85rem !important;
        }
        
        /* File Uploader */
        .stFileUploader label {
            font-size: 0.8rem !important;
        }
        
        /* Slider */
        .stSlider label {
            font-size: 0.8rem !important;
        }
    </style>
    """, unsafe_allow_html=True)




