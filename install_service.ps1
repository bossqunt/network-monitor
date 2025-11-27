# Network Monitor - Task Scheduler Setup Script
# Run this script as Administrator to create a scheduled task

$taskName = "NetworkMonitor"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "network_monitor.py"
$pythonPath = (Get-Command python).Source
$workingDir = $scriptDir

Write-Host "Creating scheduled task: $taskName" -ForegroundColor Cyan
Write-Host "Script location: $scriptPath" -ForegroundColor Gray
Write-Host "Python path: $pythonPath" -ForegroundColor Gray

# Create action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory $workingDir

# Create trigger (at startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Network monitoring service that tracks ping, traceroute, and speed tests"

Write-Host "Task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To start now: Start-ScheduledTask -TaskName $taskName" -ForegroundColor Yellow
Write-Host "To stop: Stop-ScheduledTask -TaskName $taskName" -ForegroundColor Yellow
Write-Host "To remove: Unregister-ScheduledTask -TaskName $taskName" -ForegroundColor Yellow
