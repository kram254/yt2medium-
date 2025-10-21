$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "🎥 YouTube to Medium - Quick Start Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11 or higher." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 2: Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 3: Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Created .env file from template" -ForegroundColor Yellow
    Write-Host "   📝 IMPORTANT: Edit .env and add your PROJECT_ID" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Open .env in a text editor and set:" -ForegroundColor Yellow
    Write-Host "   PROJECT_ID=your-google-cloud-project-id" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "   Press Enter after you've configured .env, or Ctrl+C to exit"
}

Write-Host ""
Write-Host "Step 6: Running setup verification..." -ForegroundColor Yellow
python test_setup.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "🎉 Setup Complete! Ready to generate blog posts!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Quick Commands:" -ForegroundColor Yellow
    Write-Host "  Start web app:    python app.py" -ForegroundColor White
    Write-Host "  CLI generation:   python cli.py 'VIDEO_URL'" -ForegroundColor White
    Write-Host "  Batch process:    python batch_process.py sample_urls.txt" -ForegroundColor White
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor Yellow
    Write-Host "  Full guide:       README.md" -ForegroundColor White
    Write-Host "  Setup help:       setup_guide.md" -ForegroundColor White
    Write-Host "  Examples:         examples.md" -ForegroundColor White
    Write-Host ""
    
    $start = Read-Host "Would you like to start the web application now? (y/n)"
    if ($start -eq "y" -or $start -eq "Y") {
        Write-Host ""
        Write-Host "Starting web application..." -ForegroundColor Green
        Write-Host "Access it at: http://localhost:8080" -ForegroundColor Cyan
        Write-Host ""
        python app.py
    }
} else {
    Write-Host ""
    Write-Host "❌ Setup verification failed. Please fix the issues above." -ForegroundColor Red
}
