param(
    [switch]$NoAutoExecute,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$LogDir = Join-Path $Root "12_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$OutLog = Join-Path $LogDir "hermes_out.log"
$ErrLog = Join-Path $LogDir "hermes_err.log"
$PidFile = Join-Path $LogDir "hermes.pid"

# 자격 점검
$envCheck = & $Python -m ai_company.main hermes-status 2>&1
Write-Host $envCheck

$args = @("-u", "-m", "ai_company.main", "hermes-run")
if ($NoAutoExecute) {
    $args += "--no-auto-execute"
}

if ($Foreground) {
    Write-Host "Hermes 봇을 포그라운드로 실행합니다. Ctrl+C로 중단하세요."
    & $Python @args
} else {
    $process = Start-Process `
        -FilePath $Python `
        -ArgumentList $args `
        -WindowStyle Hidden `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog `
        -PassThru
    $process.Id | Set-Content -Path $PidFile -Encoding UTF8
    Write-Host "Hermes 봇이 백그라운드에서 실행 중입니다."
    Write-Host "PID: $($process.Id)"
    Write-Host "로그: $OutLog"
    Write-Host ""
    Write-Host "중단 방법:"
    Write-Host "  Stop-Process -Id $($process.Id)"
}
