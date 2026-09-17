$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskPowerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$taskOut = Join-Path $taskRoot 'logs\activity-dev\supervisor-lifecycle.out.log'
$taskErr = Join-Path $taskRoot 'logs\activity-dev\supervisor-lifecycle.err.log'

if (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -In 5173, 9101) {
  throw 'Ports 5173 and 9101 must be free before this lifecycle test.'
}

$taskSupervisor = Start-Process -FilePath $taskPowerShell `
  -ArgumentList @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $taskRoot 'start-current-project.ps1')) `
  -WorkingDirectory $taskRoot -RedirectStandardOutput $taskOut `
  -RedirectStandardError $taskErr -PassThru

try {
  $taskReady = $false
  for ($taskTry = 0; $taskTry -lt 90; $taskTry++) {
    if ($taskSupervisor.HasExited) { break }
    try {
      $taskBackend = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:9101/api/v1/auth/config' -TimeoutSec 1
      $taskFrontend = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173/login' -TimeoutSec 1
      if ($taskBackend.StatusCode -eq 200 -and $taskFrontend.StatusCode -eq 200) {
        $taskReady = $true
        break
      }
    } catch {}
    Start-Sleep -Milliseconds 500
  }

  if (-not $taskReady) {
    if (Test-Path -LiteralPath $taskOut) { Get-Content -LiteralPath $taskOut -Tail 30 }
    if (Test-Path -LiteralPath $taskErr) { Get-Content -LiteralPath $taskErr -Tail 30 }
    throw 'The supervisor did not start both services.'
  }

  Write-Output "READY supervisor PID $($taskSupervisor.Id)"
  Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object LocalPort -In 5173, 9101 |
    Select-Object LocalPort, OwningProcess |
    Format-Table
}
finally {
  if (-not $taskSupervisor.HasExited) {
    Stop-Process -Id $taskSupervisor.Id -Force -ErrorAction SilentlyContinue
  }
}

for ($taskTry = 0; $taskTry -lt 50; $taskTry++) {
  $taskRemaining = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalPort -In 5173, 9101)
  if (-not $taskRemaining.Count) { break }
  Start-Sleep -Milliseconds 200
}

$taskRemaining = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object LocalPort -In 5173, 9101)
if ($taskRemaining.Count) {
  $taskRemaining | Select-Object LocalPort, OwningProcess | Format-Table
  throw 'Frontend or backend survived after the supervisor was closed.'
}

Write-Output 'PASS supervisor close automatically stopped frontend and backend; ports are free.'
