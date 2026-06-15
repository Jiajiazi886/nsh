param(
  [switch]$Open,
  [switch]$SkipDependencyCheck
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root 'ruoyi-fastapi-backend'
$FrontendDir = Join-Path $Root 'ruoyi-fastapi-frontend'
$PythonExe = Join-Path $BackendDir '.venv\Scripts\python.exe'
$LogDir = Join-Path $Root 'logs\startup'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$BackendOut = Join-Path $LogDir "backend-$Stamp.out.log"
$BackendErr = Join-Path $LogDir "backend-$Stamp.err.log"
$FrontendOut = Join-Path $LogDir "frontend-$Stamp.out.log"
$FrontendErr = Join-Path $LogDir "frontend-$Stamp.err.log"

function Get-ListeningPids {
  param([int]$Port)

  $pattern = "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$"
  netstat -ano |
    Select-String -Pattern $pattern |
    ForEach-Object { [int]$_.Matches[0].Groups[1].Value } |
    Sort-Object -Unique
}

function Test-Port {
  param([int]$Port)
  return @((Get-ListeningPids -Port $Port)).Count -gt 0
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 60
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
        return $true
      }
    } catch {
      Start-Sleep -Seconds 2
    }
  } while ((Get-Date) -lt $deadline)

  return $false
}

function Assert-FileExists {
  param(
    [string]$Path,
    [string]$Message
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    throw $Message
  }
}

function Format-Status {
  param([bool]$Ok)
  if ($Ok) {
    return 'OK'
  }
  return 'FAILED'
}

Write-Host "Project root: $Root"

if (-not $SkipDependencyCheck) {
  Assert-FileExists -Path $PythonExe -Message "Backend virtualenv not found: $PythonExe"

  if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'npm.cmd not found. Please install Node.js first.'
  }

  if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir 'node_modules'))) {
    throw "Frontend dependencies not found. Run npm install in: $FrontendDir"
  }

  if (-not (Test-Port -Port 3306)) {
    Write-Warning 'MySQL port 3306 is not listening. Backend may fail if database is not running.'
  }

  if (-not (Test-Port -Port 6379)) {
    Write-Warning 'Redis port 6379 is not listening. Backend may fail if Redis is not running.'
  }
}

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

if (Test-Port -Port 9099) {
  $pids = (Get-ListeningPids -Port 9099) -join ', '
  Write-Host "Backend already listening on 9099. PID: $pids"
} else {
  Write-Host 'Starting backend on 9099...'
  Start-Process `
    -FilePath $PythonExe `
    -ArgumentList 'app.py' `
    -WorkingDirectory $BackendDir `
    -RedirectStandardOutput $BackendOut `
    -RedirectStandardError $BackendErr `
    -WindowStyle Hidden
}

if (Test-Port -Port 80) {
  $pids = (Get-ListeningPids -Port 80) -join ', '
  Write-Host "Frontend already listening on 80. PID: $pids"
} else {
  Write-Host 'Starting frontend on 80...'
  Start-Process `
    -FilePath 'npm.cmd' `
    -ArgumentList 'run dev -- --host 0.0.0.0 --port 80 --open false' `
    -WorkingDirectory $FrontendDir `
    -RedirectStandardOutput $FrontendOut `
    -RedirectStandardError $FrontendErr `
    -WindowStyle Hidden
}

Write-Host 'Checking services...'
$BackendOk = Wait-HttpOk -Url 'http://127.0.0.1:9099/docs' -TimeoutSeconds 75
$FrontendOk = Wait-HttpOk -Url 'http://127.0.0.1/' -TimeoutSeconds 75
$AnalysisOk = Wait-HttpOk -Url 'http://127.0.0.1/guild/analysis' -TimeoutSeconds 75

Write-Host ''
Write-Host 'Startup result:'
Write-Host "  Backend docs:   http://127.0.0.1:9099/docs        $(Format-Status $BackendOk)"
Write-Host "  Frontend:       http://127.0.0.1/                 $(Format-Status $FrontendOk)"
Write-Host "  Analysis page:  http://127.0.0.1/guild/analysis  $(Format-Status $AnalysisOk)"
Write-Host ''
Write-Host "Backend stdout:  $BackendOut"
Write-Host "Backend stderr:  $BackendErr"
Write-Host "Frontend stdout: $FrontendOut"
Write-Host "Frontend stderr: $FrontendErr"

if ($Open -and $FrontendOk) {
  Start-Process 'http://127.0.0.1/'
}

if (-not ($BackendOk -and $FrontendOk -and $AnalysisOk)) {
  exit 1
}
