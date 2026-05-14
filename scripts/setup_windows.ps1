param(
    [switch]$InstallCodex
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== AI_COMPANY Windows setup ==="

$folders = @(
    "00_inbox",
    "01_products",
    "02_marketing",
    "03_images",
    "04_smartstore",
    "05_naver_ads",
    "06_apps",
    "07_agents",
    "08_reports",
    "09_approval",
    "10_meetings",
    "11_memory",
    "12_logs",
    "data"
)

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "Created: $folder"
    }
}

function Check-Command($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        Write-Host "[MISSING] $name"
    } else {
        Write-Host "[OK] $name -> $($cmd.Source)"
    }
}

Check-Command "git"
Check-Command "python"
Check-Command "node"
Check-Command "npm"
Check-Command "docker"
Check-Command "ollama"
Check-Command "codex"

if (-not (Test-Path ".git")) {
    git init
    Write-Host "Initialized Git repository."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Fill secrets manually."
}

if ($InstallCodex) {
    Check-Command "npm"
    Write-Host "Installing Codex CLI..."
    npm i -g @openai/codex
}

Write-Host ""
Write-Host "Next:"
Write-Host "1. python -m venv .venv"
Write-Host "2. .\.venv\Scripts\activate"
Write-Host "3. pip install -r requirements.txt"
Write-Host "4. codex --cd $PWD --ask-for-approval on-request"
