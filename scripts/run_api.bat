@echo off
setlocal

cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup first...
    call scripts\setup.bat
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" app\main.py
