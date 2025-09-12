#!/bin/bash

echo "Zeitkalkül Metadata Recognizer - Internet-Zugang"
echo "================================================"

# Streamlit im Hintergrund starten
echo "Starte Streamlit-App..."
streamlit run streamlit_app.py --server.port 8501 &
STREAMLIT_PID=$!

# Kurz warten
sleep 5

# ngrok starten
echo "Starte ngrok-Tunnel..."
ngrok http 8501 &
NGROK_PID=$!

# Kurz warten
sleep 3

# URL abrufen
echo ""
echo "============================================================"
echo "🌐 ÖFFENTLICHE URL:"
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['tunnels']:
    print(data['tunnels'][0]['public_url'])
else:
    print('Fehler: Keine URL gefunden')
"
echo "============================================================"
echo "📋 LOGIN-DATEN:"
echo "   Benutzername: admin"
echo "   Passwort: admin123"
echo "   ODER"
echo "   Benutzername: user"
echo "   Passwort: user123"
echo "============================================================"
echo "⚠️  WICHTIG: Diese URL ist temporär und wird beim Beenden ungültig!"
echo "============================================================"
echo ""
echo "Drücken Sie Ctrl+C zum Beenden..."

# Auf Ctrl+C warten
trap 'echo "Beende Anwendung..."; kill $STREAMLIT_PID $NGROK_PID; exit' INT

# Warten
wait
