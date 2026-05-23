@echo off
setlocal

cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 exit /b 1
)

echo Installing Python dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo Downloading NLTK data...
".venv\Scripts\python.exe" download_nltk.py
if errorlevel 1 exit /b 1

if not exist "data.pth" (
    echo Training intent model...
    ".venv\Scripts\python.exe" train.py
    if errorlevel 1 exit /b 1
) else (
    echo data.pth already exists; skipping training.
)

echo.
echo Setup complete. Use scripts\run_app.bat to start the backend and Streamlit UI.
