param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendRoot = Join-Path $Root "backend"
$FrontendRoot = Join-Path $Root "frontend"
$DeliveryPanelRoot = Join-Path $Root "delivery-panel"
$ShopOwnerPanelRoot = Join-Path $Root "shop-owner-panel"
$PythonExe = Join-Path $BackendRoot ".venv\Scripts\python.exe"
$FrontendUrl = "http://127.0.0.1:5173"
$DeliveryPanelUrl = "http://127.0.0.1:5174"
$ShopOwnerPanelUrl = "http://127.0.0.1:5175"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Test-PythonDependencies {
    param([string]$PythonPath)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PythonPath -c "import fastapi, sqlalchemy, alembic, jwt, pwdlib, pydantic_settings" 1>$null 2>$null
        return $LASTEXITCODE -eq 0
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Invoke-InDirectory {
    param(
        [string]$Path,
        [scriptblock]$Script
    )

    Push-Location $Path
    try {
        & $Script
    }
    finally {
        Pop-Location
    }
}

function Test-TcpPort {
    param([int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $result = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(500)) {
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

function Wait-ForTcpPort {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 20
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-TcpPort $Port) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }

    return $false
}

if (-not (Test-Path $BackendRoot)) {
    throw "Backend folder not found: $BackendRoot"
}

if (-not (Test-Path $FrontendRoot)) {
    throw "Frontend folder not found: $FrontendRoot"
}

if (-not (Test-Path $DeliveryPanelRoot)) {
    throw "Delivery panel folder not found: $DeliveryPanelRoot"
}

if (-not (Test-Path $ShopOwnerPanelRoot)) {
    throw "Shop owner panel folder not found: $ShopOwnerPanelRoot"
}

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "sqlite:///./dev.db"
}

Write-Step "Preparing backend"

if (-not (Test-Path $PythonExe)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python was not found and backend .venv does not exist. Install Python or create backend\.venv first."
    }

    Invoke-InDirectory $BackendRoot {
        Invoke-Checked $pythonCommand.Source @("-m", "venv", ".venv")
    }
}

Invoke-InDirectory $BackendRoot {
    if (-not (Test-PythonDependencies $PythonExe)) {
        Write-Step "Installing backend dependencies"
        Invoke-Checked $PythonExe @("-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements-dev.txt")

        if (-not (Test-PythonDependencies $PythonExe)) {
            Write-Step "Repairing backend virtual environment"
            Invoke-Checked $PythonExe @("-m", "pip", "install", "--disable-pip-version-check", "--force-reinstall", "-r", "requirements-dev.txt")
        }

        if (-not (Test-PythonDependencies $PythonExe)) {
            throw "Backend dependencies are still not importable. Delete backend\.venv and run .\run-dev.ps1 again."
        }
    }

    if ($env:DATABASE_URL -match "^sqlite:///\./(.+\.db)$") {
        $sqliteDbPath = Join-Path $BackendRoot $Matches[1]
        if (Test-Path $sqliteDbPath) {
            & $PythonExe -c "import sqlite3, sys; p = r'''$sqliteDbPath'''; con = sqlite3.connect(p); tables = {row[0] for row in con.execute('select name from sqlite_master').fetchall()}; versions = con.execute('select version_num from alembic_version').fetchall() if 'alembic_version' in tables else []; con.close(); sys.exit(0 if 'categories' in tables and not versions else 1)"
            if ($LASTEXITCODE -eq 0) {
                Write-Step "Completing existing local SQLite database"
                Invoke-Checked $PythonExe @("-c", "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)")
                Invoke-Checked $PythonExe @("-m", "alembic", "stamp", "head")
            }
        }
    }

    Write-Step "Applying database migrations"
    Invoke-Checked $PythonExe @("-m", "alembic", "upgrade", "head")

    Write-Step "Seeding product catalog"
    Invoke-Checked $PythonExe @("-m", "app.seed")
}

Write-Step "Preparing frontend"

$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    throw "npm.cmd was not found. Install Node.js first."
}

Invoke-InDirectory $FrontendRoot {
    if (-not (Test-Path "node_modules")) {
        Write-Step "Installing frontend dependencies"
        Invoke-Checked $npmCommand.Source @("install")
    }
}

if ($CheckOnly) {
    Write-Step "Check complete"
    Write-Host "Backend, frontend, delivery panel, and shop owner panel are ready to run." -ForegroundColor Green
    exit 0
}

Write-Step "Starting backend and frontend"

$backendCommand = @"
`$env:DATABASE_URL = '$($env:DATABASE_URL)'
Set-Location '$BackendRoot'
& '$PythonExe' -m uvicorn app.main:app --reload
"@

$frontendCommand = @"
Set-Location '$FrontendRoot'
npm.cmd run dev -- --host 127.0.0.1
"@

$deliveryPanelCommand = @"
Set-Location '$DeliveryPanelRoot'
npm.cmd run dev
"@

$shopOwnerPanelCommand = @"
Set-Location '$ShopOwnerPanelRoot'
npm.cmd run dev
"@

if (Test-TcpPort 8000) {
    Write-Host "Backend is already running on http://127.0.0.1:8000"
}
else {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-NoProfile", "-Command", $backendCommand
}

if (Test-TcpPort 5173) {
    Write-Host "Frontend is already running on $FrontendUrl"
}
else {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-NoProfile", "-Command", $frontendCommand
}

if (Test-TcpPort 5174) {
    Write-Host "Delivery panel is already running on $DeliveryPanelUrl"
}
else {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-NoProfile", "-Command", $deliveryPanelCommand
}

if (Test-TcpPort 5175) {
    Write-Host "Shop owner panel is already running on $ShopOwnerPanelUrl"
}
else {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-NoProfile", "-Command", $shopOwnerPanelCommand
}

Wait-ForTcpPort 8000 | Out-Null
Wait-ForTcpPort 5173 | Out-Null
Wait-ForTcpPort 5174 | Out-Null
Wait-ForTcpPort 5175 | Out-Null
Start-Process $FrontendUrl
Start-Process $DeliveryPanelUrl
Start-Process $ShopOwnerPanelUrl

Write-Host ""
Write-Host "CampusKart is starting." -ForegroundColor Green
Write-Host "Frontend: $FrontendUrl"
Write-Host "Delivery panel: $DeliveryPanelUrl"
Write-Host "Shop owner panel: $ShopOwnerPanelUrl"
Write-Host "Backend docs: http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Close the PowerShell server windows to stop the app."
