@echo off
setlocal
echo ======================================================================
echo VOCALAID AI - VERIFYING ENVIRONMENT AND ADAPTERS
echo ======================================================================

set CONDA_ENV=dysarthric
set CONDA_ACTIVATE=C:\Users\Heli P Shah\ANACONDA\Scripts\activate.bat

if exist "%CONDA_ACTIVATE%" (
    call "%CONDA_ACTIVATE%" %CONDA_ENV%
)

python test_pipeline.py
pause
