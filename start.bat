@echo off
rem Start de Cyberweerbaarheid Monitor (Windows). Dubbelklik op dit bestand.
rem De eerste keer worden de benodigde pakketten geinstalleerd.
cd /d "%~dp0"

set PY=py -3
%PY% --version >nul 2>&1 || set PY=python
%PY% --version >nul 2>&1
if errorlevel 1 (
  echo Python is niet gevonden. Installeer Python 3.11 of nieuwer via https://www.python.org/downloads/
  echo Vink bij de installatie "Add python.exe to PATH" aan.
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
  echo Python 3.11 of nieuwer is nodig.
  pause
  exit /b 1
)

if not exist .venv (
  echo Eerste keer: omgeving aanmaken en pakketten installeren...
  %PY% -m venv .venv
)
.venv\Scripts\python -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo Installeren van de pakketten is mislukt.
  pause
  exit /b 1
)

echo.
echo De app draait op http://127.0.0.1:5000  (stoppen: sluit dit venster of druk Ctrl+C)
start "" http://127.0.0.1:5000
.venv\Scripts\python run.py
pause
