@echo off
echo ===============================================
echo   Zeitkalkuel Metadata Recognizer - Windows
echo   Start Script
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

REM Prüfen ob Streamlit verfügbar ist
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Streamlit ist nicht installiert.
    echo Führen Sie zuerst install_windows.bat aus.
    pause
    exit /b 1
)

echo Starte Streamlit App...
echo.
echo Lokale URL: http://localhost:8501
echo.
echo Drücken Sie Ctrl+C um die App zu beenden.
echo.

REM Starte Streamlit App
python -m streamlit run streamlit_app.py --server.port 8501

pause
