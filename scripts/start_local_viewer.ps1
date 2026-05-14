param(
    [int]$Port = 8765,
    [switch]$OpenBrowser,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$LogDir = Join-Path $Root "12_logs"
$OutLog = Join-Path $LogDir "local_viewer_out.log"
$ErrLog = Join-Path $LogDir "local_viewer_err.log"
$PidFile = Join-Path $LogDir "local_viewer.pid"

function Test-LocalPort {
    param([int]$PortToCheck)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect("127.0.0.1", $PortToCheck, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(250)) {
            return $false
        }
        $client.EndConnect($result)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Test-LocalViewerApi {
    param([int]$PortToCheck)
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$PortToCheck/api/health" -TimeoutSec 1
        return ($response.ok -eq $true)
    }
    catch {
        return $false
    }
}

function Stop-ExistingPythonServer {
    param([int]$PortToStop)
    $connection = Get-NetTCPConnection -State Listen -LocalPort $PortToStop -ErrorAction SilentlyContinue | Select-Object -First 1
    $owningProcess = $null
    if ($null -ne $connection) {
        $owningProcess = $connection.OwningProcess
    }

    if ($null -eq $owningProcess) {
        $netstatLine = netstat -ano | Select-String "127.0.0.1:$PortToStop" | Select-String "LISTENING" | Select-Object -First 1
        if ($null -ne $netstatLine) {
            $parts = ($netstatLine.ToString() -split "\s+") | Where-Object { $_ }
            $owningProcess = [int]$parts[-1]
        }
    }

    if ($null -eq $owningProcess) {
        return
    }

    $process = Get-Process -Id $owningProcess -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        return
    }

    if ($process.ProcessName -notlike "python*") {
        throw "Port $PortToStop is already used by $($process.ProcessName). Choose another port."
    }

    Stop-Process -Id $process.Id -Force
    Start-Sleep -Milliseconds 500
}

if (-not (Test-Path $Python)) {
    $Python = "python"
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if ($Restart) {
    Stop-ExistingPythonServer -PortToStop $Port
}

if ((Test-LocalPort -PortToCheck $Port) -and -not (Test-LocalViewerApi -PortToCheck $Port)) {
    Stop-ExistingPythonServer -PortToStop $Port
}

if (-not (Test-LocalPort -PortToCheck $Port)) {
    $args = @(
        "-u",
        (Join-Path $Root "scripts\local_viewer_server.py"),
        "--host",
        "127.0.0.1",
        "--port",
        "$Port"
    )
    $process = Start-Process `
        -WindowStyle Hidden `
        -FilePath $Python `
        -ArgumentList $args `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog `
        -PassThru
    $process.Id | Set-Content -Path $PidFile -Encoding UTF8

    for ($i = 0; $i -lt 20; $i++) {
        if (Test-LocalPort -PortToCheck $Port) {
            break
        }
        Start-Sleep -Milliseconds 250
    }

    for ($i = 0; $i -lt 20; $i++) {
        if (Test-LocalViewerApi -PortToCheck $Port) {
            break
        }
        Start-Sleep -Milliseconds 250
    }
}

$SimulatorUrl = "http://127.0.0.1:$Port/06_apps/ai_office_simulator/index.html"
$DashboardUrl = "http://127.0.0.1:$Port/06_apps/dry_run_dashboard/index.html"

Write-Host "AI Office Simulator:"
Write-Host $SimulatorUrl
Write-Host ""
Write-Host "Dry-run Dashboard:"
Write-Host $DashboardUrl

if ($OpenBrowser) {
    Start-Process $SimulatorUrl
}
