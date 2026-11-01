@echo off
setlocal
echo ======================================================================
echo VOCALAID AI - LAUNCHING INTERACTIVE WEB PLATFORM
echo Local URL: http://127.0.0.1:8080 (or http://localhost:8080)
echo ======================================================================

set CONDA_ENV=dysarthric
set CONDA_ACTIVATE=C:\Users\Heli P Shah\ANACONDA\Scripts\activate.bat

if exist "%CONDA_ACTIVATE%" (
    call "%CONDA_ACTIVATE%" %CONDA_ENV%
)

python app.py
pause
