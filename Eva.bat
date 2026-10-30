@echo off
REM Doble clic: Eva muestra el resumen del día y abre el modo conversación.
cd /d "%~dp0"
python eva.py hoy --rapido
echo.
choice /m "Quieres conversar con Eva (usa Ollama)"
if errorlevel 2 goto fin
python eva.py chat
:fin
pause
