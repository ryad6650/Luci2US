@echo off
cd /d "%~dp0"
py scan_app.py
if errorlevel 1 pause
