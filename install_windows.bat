@echo off
echo ===============================================
echo   Zeitkalkuel Metadata Recognizer - Windows
echo   Installation Script
echo ===============================================
echo.

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH.
    echo Bitte installieren Sie Python 3.9+ von https://python.org
    echo und stellen Sie sicher, dass "Add Python to PATH" aktiviert ist.
    pause
    exit /b 1
)

echo Python gefunden:
python --version
echo.

REM Prüfen ob pip verfügbar ist
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: pip ist nicht verfügbar.
    echo Bitte installieren Sie pip oder verwenden Sie: python -m ensurepip
    pause
    exit /b 1
)

echo pip gefunden:
pip --version
echo.

echo Installiere Python-Abhängigkeiten...
echo ===============================================

REM Upgrade pip
python -m pip install --upgrade pip

REM Installiere alle erforderlichen Pakete
pip install streamlit
pip install opencv-python
pip install pillow
pip install plotly
pip install pandas
pip install numpy
pip install insightface
pip install onnxruntime
pip install neo4j
pip install python-dateutil
pip install exifread
pip install geopy
pip install requests

echo.
echo ===============================================
echo Installation abgeschlossen!
echo ===============================================
echo.

REM Prüfen ob ngrok installiert ist
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo HINWEIS: ngrok ist nicht installiert.
    echo Für Internet-Zugang installieren Sie ngrok:
    echo 1. Besuchen Sie https://ngrok.com/download
    echo 2. Laden Sie die Windows-Version herunter
    echo 3. Entpacken Sie ngrok.exe in einen Ordner im PATH
    echo 4. Oder kopieren Sie ngrok.exe in dieses Verzeichnis
    echo.
)

echo Starten der Anwendung...
echo Verwenden Sie: start_app.bat
echo.
pause
