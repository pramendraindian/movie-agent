@echo off
setlocal

cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup first...
    call scripts\setup.bat
    if errorlevel 1 exit /b 1
)

echo Starting FastAPI backend in a separate window...
start "Movie Agent API" cmd /k ""%cd%\.venv\Scripts\python.exe" "%cd%\app\main.py""

echo Waiting for backend to start...
powershell -NoProfile -Command "Start-Sleep -Seconds 3"

echo Starting Streamlit UI...
"%cd%\.venv\Scripts\python.exe" -m streamlit run "%cd%\chatbot_ui.py"
