# 수영 봇 — Windows 자동 시작 등록 해제

$TaskName = "Suyeong Bot"

# 작업 확인
schtasks /query /tn $TaskName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "등록된 작업이 없습니다."
    exit 0
}

# 작업 종료 후 삭제
schtasks /end /tn $TaskName 2>$null | Out-Null
schtasks /delete /tn $TaskName /f
Write-Host "✅ 스케줄 작업 제거 완료"

# 실행 중인 봇 프로세스 종료 (선택)
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and $_.CommandLine -match 'suyeong|bot.js'
} | ForEach-Object {
    Write-Host "Node 프로세스 종료: PID $($_.Id)"
    Stop-Process -Id $_.Id -Force
}

Write-Host ""
Write-Host "ws-suyeong 데이터 / openclaw.json 키는 그대로 유지됩니다."
