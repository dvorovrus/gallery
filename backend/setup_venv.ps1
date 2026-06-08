# Setup script for backend virtual environment with Python 3.12

Write-Host "=== Gallery Backend Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.12 is available
$python312 = Get-Command python3.12 -ErrorAction SilentlyContinue
if (-not $python312) {
    $python312 = Get-Command py -ErrorAction SilentlyContinue
    if ($python312) {
        $version = py -3.12 --version 2>&1
        if ($version -like "*3.12*") {
            $pythonCmd = "py -3.12"
        } else {
            Write-Host "ERROR: Python 3.12 not found!" -ForegroundColor Red
            Write-Host "Please install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Yellow
            Write-Host "Current Python versions:" -ForegroundColor Yellow
            py --list
            exit 1
        }
    } else {
        Write-Host "ERROR: Python 3.12 not found!" -ForegroundColor Red
        Write-Host "Please install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
} else {
    $pythonCmd = "python3.12"
}

Write-Host "Found: " -NoNewline
& $pythonCmd.Split()[0] $(if ($pythonCmd.Contains("-3.12")) { "-3.12" }) --version
Write-Host ""

# Remove old venv if exists
if (Test-Path "venv") {
    Write-Host "Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

# Create new venv with Python 3.12
Write-Host "Creating virtual environment with Python 3.12..." -ForegroundColor Cyan
if ($pythonCmd -eq "py -3.12") {
    py -3.12 -m venv venv
} else {
    python3.12 -m venv venv
}

if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Virtual environment created" -ForegroundColor Green
Write-Host ""

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Setup Complete! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Virtual environment is activated. You can now:" -ForegroundColor Cyan
    Write-Host "  1. Configure .env file" -ForegroundColor White
    Write-Host "  2. Run: alembic upgrade head" -ForegroundColor White
    Write-Host "  3. Run: uvicorn main:app --reload" -ForegroundColor White
    Write-Host ""
    Write-Host "To activate venv later: venv\Scripts\activate" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "ERROR: Installation failed!" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Yellow
    exit 1
}
