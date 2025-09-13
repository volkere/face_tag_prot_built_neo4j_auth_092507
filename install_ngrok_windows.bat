@echo off
echo ===============================================
echo   ngrok Installation für Windows
echo ===============================================
echo.

echo Dieses Skript hilft Ihnen bei der Installation von ngrok.
echo.

echo Option 1: Automatische Installation (empfohlen)
echo - Lädt ngrok herunter und installiert es automatisch
echo.

echo Option 2: Manuelle Installation
echo - Zeigt Anweisungen für manuelle Installation
echo.

set /p choice="Wählen Sie eine Option (1 oder 2): "

if "%choice%"=="1" goto auto_install
if "%choice%"=="2" goto manual_install
echo Ungültige Auswahl.
goto end

:auto_install
echo.
echo Automatische Installation von ngrok...
echo.

REM Erstelle ngrok-Verzeichnis
if not exist "%USERPROFILE%\ngrok" mkdir "%USERPROFILE%\ngrok"

REM Prüfe ob PowerShell verfügbar ist
powershell -Command "Get-Command Invoke-WebRequest" >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: PowerShell ist nicht verfügbar.
    echo Bitte verwenden Sie die manuelle Installation.
    goto manual_install
)

echo Lade ngrok herunter...
powershell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile '%USERPROFILE%\ngrok\ngrok.zip'"

if not exist "%USERPROFILE%\ngrok\ngrok.zip" (
    echo FEHLER: Download fehlgeschlagen.
    echo Bitte verwenden Sie die manuelle Installation.
    goto manual_install
)

echo Entpacke ngrok...
powershell -Command "Expand-Archive -Path '%USERPROFILE%\ngrok\ngrok.zip' -DestinationPath '%USERPROFILE%\ngrok' -Force"

REM Kopiere ngrok.exe ins aktuelle Verzeichnis
copy "%USERPROFILE%\ngrok\ngrok.exe" "ngrok.exe" >nul 2>&1

echo.
echo ngrok erfolgreich installiert!
echo.
echo Um ngrok zu verwenden:
echo 1. Registrieren Sie sich bei https://ngrok.com (kostenlos)
echo 2. Holen Sie sich Ihren Authtoken
echo 3. Führen Sie aus: ngrok config add-authtoken YOUR_TOKEN
echo.
goto end

:manual_install
echo.
echo ===============================================
echo   Manuelle Installation von ngrok
echo ===============================================
echo.
echo 1. Besuchen Sie https://ngrok.com/download
echo 2. Klicken Sie auf "Download for Windows"
echo 3. Entpacken Sie die heruntergeladene ZIP-Datei
echo 4. Kopieren Sie ngrok.exe in dieses Verzeichnis
echo 5. Oder fügen Sie den ngrok-Ordner zu Ihrem PATH hinzu
echo.
echo Nach der Installation:
echo 1. Registrieren Sie sich bei https://ngrok.com (kostenlos)
echo 2. Holen Sie sich Ihren Authtoken
echo 3. Führen Sie aus: ngrok config add-authtoken YOUR_TOKEN
echo.

:end
echo.
echo Verwenden Sie start_with_ngrok_windows.bat um die App mit Internet-Zugang zu starten.
echo.
pause
