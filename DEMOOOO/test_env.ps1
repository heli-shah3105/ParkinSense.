$condaPython = "C:\Users\Heli P Shah\ANACONDA\envs\dysarthric\python.exe"
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "VOCALAID AI - VERIFYING ENVIRONMENT AND ADAPTERS" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if (Test-Path $condaPython) {
    & $condaPython test_pipeline.py
} else {
    python test_pipeline.py
}
