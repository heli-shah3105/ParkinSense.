$condaPython = "C:\Users\Heli P Shah\ANACONDA\envs\dysarthric\python.exe"
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "VOCALAID AI - LAUNCHING INTERACTIVE WEB PLATFORM" -ForegroundColor Cyan
Write-Host "Local URL: http://127.0.0.1:8080 (or http://localhost:8080)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

if (Test-Path $condaPython) {
    & $condaPython app.py
} else {
    python app.py
}
