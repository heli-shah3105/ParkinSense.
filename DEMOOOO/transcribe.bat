@echo off
setlocal
echo ======================================================================
echo VOCALAID AI - TRANSCRIBE AUDIO CLIP
echo ======================================================================

set CONDA_ENV=dysarthric
set CONDA_ACTIVATE=C:\Users\Heli P Shah\ANACONDA\Scripts\activate.bat

if exist "%CONDA_ACTIVATE%" (
    call "%CONDA_ACTIVATE%" %CONDA_ENV%
)

if "%~1"=="" (
    echo Usage: transcribe.bat path\to\audio.wav [--speaker_id SPEAKER_ID] [--timestamps]
    echo Example: transcribe.bat output\processed_audio\UA_CF02\UA_CF02_000000.wav
    pause
    exit /b 1
)

python step6_inference.py --audio "%~1" %2 %3 %4 %5
pause
