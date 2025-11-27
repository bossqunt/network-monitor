# Network Monitor - Quick Start Script
# Run this script to set up and start the network monitor

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Network Monitor - Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.7+" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Setup database
Write-Host ""
Write-Host "Setting up database..." -ForegroundColor Yellow
python setup_db.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database setup complete" -ForegroundColor Green
} else {
    Write-Host "✗ Database setup failed" -ForegroundColor Red
    Write-Host "Please check MySQL credentials in config.yaml" -ForegroundColor Yellow
    exit 1
}

# Start the monitor
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting Network Monitor..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
python network_monitor.py
