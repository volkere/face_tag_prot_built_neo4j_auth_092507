#!/usr/bin/env python3
"""
Skript zum Starten der Streamlit-App mit ngrok-Tunnel
"""

import subprocess
import time
import threading
import requests
import json

def start_streamlit():
    """Startet die Streamlit-App"""
    print("Starte Streamlit-App...")
    subprocess.run(["streamlit", "run", "streamlit_app.py", "--server.port", "8501"])

def start_ngrok():
    """Startet ngrok-Tunnel"""
    print("Starte ngrok-Tunnel...")
    time.sleep(5)  # Warten bis Streamlit gestartet ist
    
    # ngrok starten
    ngrok_process = subprocess.Popen([
        "ngrok", "http", "8501", "--log=stdout"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Warten und URL extrahieren
    time.sleep(3)
    
    try:
        # ngrok API abfragen um die URL zu bekommen
        response = requests.get("http://localhost:4040/api/tunnels")
        data = response.json()
        
        if data['tunnels']:
            public_url = data['tunnels'][0]['public_url']
            print(f"\n{'='*60}")
            print(f"ÖFFENTLICHE URL: {public_url}")
            print(f"{'='*60}")
            print(f"LOGIN-DATEN:")
            print(f"   Benutzername: admin")
            print(f"   Passwort: admin123")
            print(f"   ODER")
            print(f"   Benutzername: user")
            print(f"   Passwort: user123")
            print(f"{'='*60}")
            print(f"WICHTIG: Diese URL ist temporär und wird beim Beenden des Tunnels ungültig!")
            print(f"{'='*60}\n")
        else:
            print("Fehler: Keine ngrok-URL gefunden")
            
    except Exception as e:
        print(f"Fehler beim Abrufen der ngrok-URL: {e}")
    
    return ngrok_process

def main():
    """Hauptfunktion"""
    print("Zeitkalkül Metadata Recognizer - Internet-Zugang")
    print("=" * 50)
    
    # Streamlit in separatem Thread starten
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    streamlit_thread.start()
    
    # ngrok starten
    ngrok_process = start_ngrok()
    
    try:
        print("Drücken Sie Ctrl+C zum Beenden...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBeende Anwendung...")
        ngrok_process.terminate()
        print("Tunnel geschlossen.")

if __name__ == "__main__":
    main()
