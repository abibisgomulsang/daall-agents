# 수영 봇 — Windows 자동 시작 등록 스크립트
# 사장님 윈도우 로그인 시 봇이 백그라운드로 자동 시작
# 실행: PowerShell에서 → cd bot/ → .\install-windows.ps1

$ErrorActionPreference = 'Stop'

$BotDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $BotDir 'start.js'
$LogDir = Join-Path $env:USERPROFILE '.suyeong-bot\logs'
$WrapperScript = Join-Path $BotDir 'run-bot-silent.vbs'

if (-not (Test-Path $StartScript)) {
    Write-Error "start.js 못 찾음: $StartScript"
    exit 1
}

# Node.js 확인
$NodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $NodeExe) {
    Write-Error "Node.js 가 설치되어 있지 않습니다. https://nodejs.org 에서 LTS 설치 후 다시 실행."
    exit 1
}

Write-Host "✅ Node.js: $NodeExe"

# 로그 폴더 생성
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# VBS 래퍼 — 콘솔 창 안 보이게 백그라운드 실행 + 로그 파일에 출력
$VbsContent = @"
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strLogFile = objShell.ExpandEnvironmentStrings("%USERPROFILE%\.suyeong-bot\logs\bot.log")
strCmd = """$NodeExe"" """ + "$($StartScript -replace '\\', '\\')" + """ >> """ + strLogFile + """ 2>&1"
objShell.Run "cmd /c " & strCmd, 0, False
"@

Set-Content -Path $WrapperScript -Value $VbsContent -Encoding ASCII
Write-Host "✅ 래퍼 스크립트 생성: $WrapperScript"

# 기존 작업 삭제 (있으면)
$TaskName = "Suyeong Bot"
schtasks /query /tn $TaskName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "기존 스케줄 작업 제거 중..."
    schtasks /delete /tn $TaskName /f | Out-Null
}

# 스케줄 작업 등록 — 로그인 시 자동 시작
$Action = "wscript.exe `"$WrapperScript`""
schtasks /create /tn $TaskName /tr $Action /sc ONLOGON /rl LIMITED /f | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 등록 완료!" -ForegroundColor Green
    Write-Host "   작업명:  $TaskName"
    Write-Host "   트리거:  사장님 Windows 로그인 시"
    Write-Host "   로그:    $LogDir\bot.log"
    Write-Host ""
    Write-Host "지금 한 번 실행하려면:" -ForegroundColor Yellow
    Write-Host "   schtasks /run /tn `"$TaskName`""
    Write-Host ""
    Write-Host "중지/제거하려면:" -ForegroundColor Yellow
    Write-Host "   .\uninstall-windows.ps1"
} else {
    Write-Error "스케줄 등록 실패"
    exit 1
}
