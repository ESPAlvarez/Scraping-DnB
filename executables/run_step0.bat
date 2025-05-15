@echo off
REM ——————————————————————————————
REM run_step0.bat
REM Prescraping: extraer sub-industrias y agrupar por país
REM ——————————————————————————————

REM 1) Asegurarse de estar en la carpeta raíz del proyecto
cd /d "%~dp0"

REM 2) Activar el entorno virtual (si existe)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 3) Ejecutar Step0
REM Lanza el entry_point definido en setup.py: dnb-step0
echo Ejecutando prescraping (Step0)…
dnb-step0

REM 4) Salir
echo Hecho.
pause
