@echo off
setlocal

for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"

rem Stop only Node/Python processes whose command line contains this project path.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $root=[IO.Path]::GetFullPath($env:PROJECT_ROOT); $names=@('node.exe','python.exe','pythonw.exe'); for($round=0; $round -lt 2; $round++){ $targets=@(Get-CimInstance Win32_Process | Where-Object { $names -contains $_.Name -and $_.CommandLine -and $_.CommandLine.Contains($root) }); foreach($target in $targets){ Stop-Process -Id $target.ProcessId -Force -ErrorAction SilentlyContinue }; if($targets.Count -gt 0){ Start-Sleep -Seconds 2 } }; $remaining=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { @(80,9100) -contains $_.LocalPort }); if($remaining){ Write-Host 'Ports 80 or 9100 are still occupied by an unrelated process.'; exit 1 }; Write-Host 'Project stopped. Ports 80 and 9100 are free.'"

if errorlevel 1 (
    echo Unrelated software is still using port 80 or 9100.
    pause
    exit /b 1
)

exit /b 0
