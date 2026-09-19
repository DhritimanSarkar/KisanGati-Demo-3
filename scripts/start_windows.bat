@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
)

echo Installing/updating dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt

echo Starting KisanGati...
.venv\Scripts\python.exe app.py
pause
