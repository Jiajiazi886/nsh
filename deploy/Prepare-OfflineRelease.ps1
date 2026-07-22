[CmdletBinding()]
param(
    [string]$Tag = (Get-Date -Format 'yyyyMMddHHmmss'),
    [string]$OutputRoot = (Join-Path $PSScriptRoot 'releases'),
    [ValidateSet('linux/amd64', 'linux/arm64')]
    [string]$Platform = 'linux/amd64'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$prodEnv = Join-Path $PSScriptRoot 'prod.env'
$composeFile = Join-Path $PSScriptRoot 'docker-compose.bundle.my.yml'
$releaseDirectory = Join-Path $OutputRoot "nsh-$Tag"

function Invoke-Docker {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: docker $($Arguments -join ' ')" }
}

function Build-FrontendAssets {
    $frontendDirectory = Join-Path $projectRoot 'ruoyi-fastapi-frontend'
    Push-Location $frontendDirectory
    try {
        & npm run build:docker
        if ($LASTEXITCODE -ne 0) { throw 'Local frontend build failed.' }
    }
    finally {
        Pop-Location
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker Desktop is required on this computer. Start Docker Desktop, then run this script again.'
}
if (-not (Test-Path -LiteralPath $prodEnv)) {
    throw "Missing $prodEnv. Run .\\deploy\\New-ProductionEnv.ps1 first, then configure MIMO_API_KEY if needed."
}
if ((Get-Content -LiteralPath $prodEnv -Raw) -match 'CHANGE_ME') {
    throw "Replace every CHANGE_ME value in $prodEnv before packaging."
}

$dockerOs = (& docker info --format '{{.OSType}}').Trim()
if ($LASTEXITCODE -ne 0 -or $dockerOs -ne 'linux') {
    throw 'Docker must be running in Linux container mode to build images for Aliyun Linux.'
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
if (Test-Path -LiteralPath $releaseDirectory) {
    throw "Release directory already exists: $releaseDirectory. Use a different -Tag."
}

Write-Host 'Building frontend static assets locally.' -ForegroundColor Cyan
Build-FrontendAssets

Write-Host "Packaging $Platform frontend image: nsh-frontend:$Tag" -ForegroundColor Cyan
Invoke-Docker buildx build --platform $Platform --load --pull --tag "nsh-frontend:$Tag" --file (Join-Path $projectRoot 'ruoyi-fastapi-frontend/Dockerfile.prod') (Join-Path $projectRoot 'ruoyi-fastapi-frontend')

Write-Host "Building $Platform backend image: nsh-backend-my:$Tag" -ForegroundColor Cyan
Invoke-Docker buildx build --platform $Platform --load --pull --tag "nsh-backend-my:$Tag" --file (Join-Path $projectRoot 'ruoyi-fastapi-backend/Dockerfile.my') (Join-Path $projectRoot 'ruoyi-fastapi-backend')

Write-Host 'Downloading MySQL and Redis images locally for the offline package.' -ForegroundColor Cyan
Invoke-Docker pull --platform $Platform mysql:8.0
Invoke-Docker pull --platform $Platform redis:7

New-Item -ItemType Directory -Force -Path (Join-Path $releaseDirectory 'sql') | Out-Null
Copy-Item -LiteralPath $composeFile -Destination (Join-Path $releaseDirectory 'docker-compose.yml')
Copy-Item -LiteralPath (Join-Path $projectRoot 'ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql') -Destination (Join-Path $releaseDirectory 'sql/ruoyi-fastapi.sql')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'BAOTA-README.md') -Destination (Join-Path $releaseDirectory 'BAOTA-README.md')

$envContent = Get-Content -LiteralPath $prodEnv -Raw
$envContent = [regex]::Replace($envContent, '(?m)^APP_IMAGE_TAG=.*$', "APP_IMAGE_TAG=$Tag")
if ($envContent -notmatch '(?m)^APP_IMAGE_TAG=') { $envContent += "`nAPP_IMAGE_TAG=$Tag`n" }
$envContent | Set-Content -LiteralPath (Join-Path $releaseDirectory 'prod.env') -Encoding utf8NoBOM

Write-Host 'Exporting Docker images. This can create a large images.tar file.' -ForegroundColor Cyan
Invoke-Docker save --output (Join-Path $releaseDirectory 'images.tar') "nsh-frontend:$Tag" "nsh-backend-my:$Tag" mysql:8.0 redis:7

$manifestPath = Join-Path $releaseDirectory 'SHA256SUMS.txt'
Get-ChildItem -LiteralPath $releaseDirectory -Recurse -File |
    Where-Object { $_.Name -ne 'SHA256SUMS.txt' } |
    ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $relativePath = $_.FullName.Substring($releaseDirectory.Length + 1).Replace('\', '/')
        "$hash  $relativePath"
    } | Set-Content -LiteralPath $manifestPath -Encoding ascii

Write-Host ''
Write-Host "Offline release created: $releaseDirectory" -ForegroundColor Green
Write-Host 'Upload this whole directory. The server only needs docker load and docker compose up -d; it will not build images.' -ForegroundColor Green
