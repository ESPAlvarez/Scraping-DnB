@echo off
REM ——————————————————————————————
REM run_tasks.bat
REM Orquestación total (batch, subset o single-country + diff) vía dnb-step1
REM ——————————————————————————————

REM 1) Ir a la raíz del proyecto
cd /d "%~dp0"

REM 2) Activar entorno virtual
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 3) Parsear parámetros
setlocal enabledelayedexpansion
set MODE=batch
set DIFF=
set COUNTRIES=
set COUNTRY=

:parse_args
if "%~1"=="" goto execute

if "%~1"=="--diff" (
    set DIFF=--diff
    shift & goto parse_args
)
if "%~1"=="--country" (
    set MODE=single
    shift
    set COUNTRY=%~1
    shift & goto parse_args
)
if "%~1"=="--countries" (
    set MODE=subset
    shift
    :collect_countries
    if "%~1"=="" goto parse_args
    if "%~1:~0,2%"=="--" goto parse_args
    set COUNTRIES=!COUNTRIES! %~1
    shift
    goto collect_countries
)
REM Parámetro desconocido: lo ignoramos para no romper
shift & goto parse_args

:execute
REM 4) Ejecutar según modo, usando el entry-point dnb-step1
if "%MODE%"=="batch" (
    echo [TASKS] Modo batch A->Z %DIFF%…
    dnb-step1 %DIFF%
    goto end
)

if "%MODE%"=="subset" (
    echo [TASKS] Modo subset: países%COUNTRIES% %DIFF%…
    dnb-step1 --countries %COUNTRIES% %DIFF%
    goto end
)

if "%MODE%"=="single" (
    echo [TASKS] Re-scrape país %COUNTRY% %DIFF%…
    dnb-step1 --country %COUNTRY% %DIFF%
    goto end
)

REM Fallback
echo Parámetro no válido. Uso:
echo     run_tasks.bat [--diff]                             ^(batch^)
echo     run_tasks.bat --countries France Germany [--diff]
echo     run_tasks.bat --country Spain [--diff]

:end
echo Hecho.
pause
