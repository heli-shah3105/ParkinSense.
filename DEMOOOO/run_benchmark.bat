@echo off
setlocal
echo ======================================================================
echo VOCALAID AI - CLINICAL BENCHMARK EVALUATION
echo ======================================================================

set CONDA_ENV=dysarthric
set CONDA_ACTIVATE=C:\Users\Heli P Shah\ANACONDA\Scripts\activate.bat

if exist "%CONDA_ACTIVATE%" (
    call "%CONDA_ACTIVATE%" %CONDA_ENV%
)

python benchmark.py --heldout_only
pause
