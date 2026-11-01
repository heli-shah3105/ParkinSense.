param(
    [Parameter(Position=0)]
    [string]$AudioPath = "output\processed_audio\UA_CF02\UA_CF02_000000.wav",
    [Parameter(Position=1)]
    [string]$SpeakerId = "",
    [switch]$Timestamps
)

$condaPython = "C:\Users\Heli P Shah\ANACONDA\envs\dysarthric\python.exe"
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "VOCALAID AI - TRANSCRIBE AUDIO CLIP" -ForegroundColor Cyan
Write-Host "Audio: $AudioPath" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$extraArgs = @()
if ($SpeakerId) {
    $extraArgs += "--speaker_id", $SpeakerId
}
if ($Timestamps) {
    $extraArgs += "--timestamps"
}

if (Test-Path $condaPython) {
    & $condaPython step6_inference.py --audio $AudioPath @extraArgs
} else {
    python step6_inference.py --audio $AudioPath @extraArgs
}
