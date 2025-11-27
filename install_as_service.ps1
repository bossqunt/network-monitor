# Install as Windows Service using NSSM (Non-Sucking Service Manager)
# First, download NSSM from https://nssm.cc/download

$serviceName = "NetworkMonitor"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "network_monitor.py"
$pythonPath = (Get-Command python).Source
$workingDir = $scriptDir
$nssmPath = "nssm.exe"  # Make sure nssm.exe is in PATH or provide full path

Write-Host "Installing Network Monitor as Windows Service..." -ForegroundColor Cyan
Write-Host "Script location: $scriptPath" -ForegroundColor Gray
Write-Host "Python path: $pythonPath" -ForegroundColor Gray

# Install service
& $nssmPath install $serviceName $pythonPath $scriptPath

# Set working directory
& $nssmPath set $serviceName AppDirectory $workingDir

# Set service to start automatically
& $nssmPath set $serviceName Start SERVICE_AUTO_START

# Set restart options
& $nssmPath set $serviceName AppThrottle 1500
& $nssmPath set $serviceName AppExit Default Restart
& $nssmPath set $serviceName AppRestartDelay 5000

# Redirect logs
& $nssmPath set $serviceName AppStdout "$workingDir\service_output.log"
& $nssmPath set $serviceName AppStderr "$workingDir\service_error.log"

Write-Host "✓ Service installed!" -ForegroundColor Green
Write-Host ""
Write-Host "To start: Start-Service $serviceName" -ForegroundColor Yellow
Write-Host "To stop: Stop-Service $serviceName" -ForegroundColor Yellow
Write-Host "To remove: nssm remove $serviceName confirm" -ForegroundColor Yellow
