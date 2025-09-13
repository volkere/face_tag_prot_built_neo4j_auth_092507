@echo off
echo ===============================================
echo   Zeitkalkuel Metadata Recognizer - Windows
echo   Start mit Internet-Zugang (ngrok)
echo ===============================================
echo.

REM Prüfen ob Python verfügbar ist
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH.
    echo Führen Sie zuerst install_windows.bat aus.
    pause
    exit /b 1
)

REM Prüfen ob ngrok verfügbar ist
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: ngrok ist nicht installiert.
    echo.
    echo Installation von ngrok:
    echo 1. Besuchen Sie https://ngrok.com/download
    echo 2. Laden Sie die Windows-Version herunter
    echo 3. Entpacken Sie ngrok.exe in einen Ordner im PATH
    echo 4. Oder kopieren Sie ngrok.exe in dieses Verzeichnis
    echo.
    echo Alternativ können Sie die App lokal starten mit: start_app.bat
    pause
    exit /b 1
)

echo Starte Streamlit App im Hintergrund...
start /B python -m streamlit run streamlit_app.py --server.port 8501

echo Warte 5 Sekunden bis Streamlit gestartet ist...
timeout /t 5 /nobreak >nul

echo Teste Streamlit-Verbindung...
curl -s http://localhost:8501 >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNUNG: Streamlit antwortet nicht. Versuche es trotzdem...
)

echo.
echo Starte ngrok Tunnel...
echo ===============================================
echo.

REM Starte ngrok und zeige URL
ngrok http 8501 --log=stdout

echo.
echo ===============================================
echo App beendet.
pause
