@echo off
echo Starting MHM Backend Service...
cd /d "%~dp0\..\.."
python core/service.py
pause 