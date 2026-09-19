@echo off
cd /d "%~dp0.."
python -m py_compile app.py
if %ERRORLEVEL% EQU 0 (
  echo Syntax check passed.
) else (
  echo Syntax check failed.
)
pause
