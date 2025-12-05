# Whale Tracker Discord Bot - PowerShell Run Script

Write-Host "🐋 Starting Whale Tracker Discord Bot..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found. Copy .env.template to .env and configure." -ForegroundColor Yellow
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "Please edit .env with your Discord webhook URL before running." -ForegroundColor Yellow
    Write-Host "Press any key to continue anyway, or Ctrl+C to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host ""
Write-Host "🚀 Starting FastAPI server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "❤️  Health check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🧪 Test alert: curl -X POST http://localhost:8000/test-alert" -ForegroundColor Cyan
Write-Host ""

# Start uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
