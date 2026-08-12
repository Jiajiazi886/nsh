[CmdletBinding()]
param(
    [string]$Tag = (Get-Date -Format 'yyyyMMddHHmmss'),
    [string]$OutputRoot = (Join-Path $PSScriptRoot 'releases'),
    [ValidateSet('linux/amd64', 'linux/arm64')]
    [string]$Platform = 'linux/amd64',
    [switch]$UseLocalBaseImages,
    [string]$FrontendBaseImage = 'nginx:1.27-alpine',
    [string]$BackendBaseImage = 'python:3.10',
    [string]$DatabaseDump = '',
    [string]$DataManifest = '',
    [string]$UserFilesDirectory = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$prodEnv = Join-Path $PSScriptRoot 'prod.env'
$composeFile = Join-Path $PSScriptRoot 'docker-compose.bundle.my.yml'
$releaseDirectory = Join-Path $OutputRoot "nsh-$Tag"
$buildDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

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

function Assert-DockerImage {
    param([string]$Image)

    & docker image inspect $Image *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Required local Docker image was not found: $Image"
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker Desktop is required on this computer. Start Docker Desktop, then run this script again.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is required so the release can be tied to an exact source revision.'
}

Push-Location $projectRoot
try {
    $buildRevision = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $buildRevision) {
        throw 'Unable to read the current Git revision.'
    }
    $buildBranch = (& git branch --show-current).Trim()
    $trackedChanges = & git status --porcelain --untracked-files=no
    if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect the Git worktree.' }
    if ($trackedChanges) {
        throw 'Tracked files have uncommitted changes. Commit them before building so images match one exact Git revision.'
    }
}
finally {
    Pop-Location
}
if (-not (Test-Path -LiteralPath $prodEnv)) {
    throw "Missing $prodEnv. Run .\\deploy\\New-ProductionEnv.ps1 first, then configure MIMO_API_KEY if needed."
}
if ((Get-Content -LiteralPath $prodEnv -Raw) -match 'CHANGE_ME') {
    throw "Replace every CHANGE_ME value in $prodEnv before packaging."
}

foreach ($resource in @('ruoyi-network', 'nsh-redis-data', 'nsh-backend-logs', 'nsh-backend-vf-admin')) {
    $resourceKind = if ($resource -eq 'ruoyi-network') { 'network' } else { 'volume' }
    & docker $resourceKind inspect $resource *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Required shared Docker $resourceKind was not found: $resource"
    }
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
$frontendBuildArguments = @('buildx', 'build', '--platform', $Platform, '--load')
if (-not $UseLocalBaseImages) { $frontendBuildArguments += '--pull' }
$frontendBuildArguments += @(
    '--tag', "nsh-frontend:$Tag",
    '--build-arg', "BASE_IMAGE=$FrontendBaseImage",
    '--build-arg', "BUILD_REVISION=$buildRevision",
    '--build-arg', "BUILD_DATE=$buildDate",
    '--file', (Join-Path $projectRoot 'ruoyi-fastapi-frontend/Dockerfile.prod'),
    (Join-Path $projectRoot 'ruoyi-fastapi-frontend')
)
if ($UseLocalBaseImages) { Assert-DockerImage $FrontendBaseImage }
Invoke-Docker @frontendBuildArguments

Write-Host "Building $Platform backend image: nsh-backend-my:$Tag" -ForegroundColor Cyan
$backendBuildArguments = @('buildx', 'build', '--platform', $Platform, '--load')
if (-not $UseLocalBaseImages) { $backendBuildArguments += '--pull' }
$backendBuildArguments += @(
    '--tag', "nsh-backend-my:$Tag",
    '--build-arg', "BASE_IMAGE=$BackendBaseImage",
    '--build-arg', "BUILD_REVISION=$buildRevision",
    '--build-arg', "BUILD_DATE=$buildDate",
    '--file', (Join-Path $projectRoot 'ruoyi-fastapi-backend/Dockerfile.my'),
    (Join-Path $projectRoot 'ruoyi-fastapi-backend')
)
if ($UseLocalBaseImages) { Assert-DockerImage $BackendBaseImage }
Invoke-Docker @backendBuildArguments

if ($UseLocalBaseImages) {
    Write-Host 'Reusing the local Redis image for the offline package.' -ForegroundColor Cyan
    Assert-DockerImage 'redis:7'
}
else {
    Write-Host 'Downloading the Redis image locally for the offline package.' -ForegroundColor Cyan
    Invoke-Docker pull --platform $Platform redis:7
}

New-Item -ItemType Directory -Force -Path (Join-Path $releaseDirectory 'sql') | Out-Null
Copy-Item -LiteralPath $composeFile -Destination (Join-Path $releaseDirectory 'docker-compose.yml')
Copy-Item -LiteralPath (Join-Path $projectRoot 'ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql') -Destination (Join-Path $releaseDirectory 'sql/ruoyi-fastapi.sql')
Copy-Item -LiteralPath (Join-Path $projectRoot 'ruoyi-fastapi-backend/sql/20260725_reset_admin_credentials.sql') -Destination (Join-Path $releaseDirectory 'sql/20260725_reset_admin_credentials.sql')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'BAOTA-README.md') -Destination (Join-Path $releaseDirectory 'BAOTA-README.md')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'site-config.example.env') -Destination (Join-Path $releaseDirectory 'site-config.example.env')

if ($DatabaseDump) {
    if (-not (Test-Path -LiteralPath $DatabaseDump -PathType Leaf)) {
        throw "Database dump was not found: $DatabaseDump"
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $releaseDirectory 'local-data') | Out-Null
    Copy-Item -LiteralPath $DatabaseDump -Destination (Join-Path $releaseDirectory 'local-data/database.local-data.sql')
}
if ($DataManifest) {
    if (-not (Test-Path -LiteralPath $DataManifest -PathType Leaf)) {
        throw "Data manifest was not found: $DataManifest"
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $releaseDirectory 'local-data') | Out-Null
    Copy-Item -LiteralPath $DataManifest -Destination (Join-Path $releaseDirectory 'local-data/DATA-MANIFEST.json')
}
if ($UserFilesDirectory) {
    if (-not (Test-Path -LiteralPath $UserFilesDirectory -PathType Container)) {
        throw "User files directory was not found: $UserFilesDirectory"
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $releaseDirectory 'local-data/vf_admin') | Out-Null
    Get-ChildItem -LiteralPath $UserFilesDirectory -Force | Copy-Item -Destination (Join-Path $releaseDirectory 'local-data/vf_admin') -Recurse -Force
}

@"
RELEASE_TAG=$Tag
SOURCE_REPOSITORY=https://github.com/Jiajiazi886/nsh.git
SOURCE_BRANCH=$buildBranch
SOURCE_COMMIT=$buildRevision
BUILD_PLATFORM=$Platform
BUILD_DATE_UTC=$buildDate
FRONTEND_IMAGE=nsh-frontend:$Tag
BACKEND_IMAGE=nsh-backend-my:$Tag
REDIS_IMAGE=redis:7
"@ | Set-Content -LiteralPath (Join-Path $releaseDirectory 'BUILD-INFO.txt') -Encoding ascii

$envContent = Get-Content -LiteralPath $prodEnv -Raw
$envContent = [regex]::Replace($envContent, '(?m)^APP_IMAGE_TAG=.*$', "APP_IMAGE_TAG=$Tag")
if ($envContent -notmatch '(?m)^APP_IMAGE_TAG=') { $envContent += "`nAPP_IMAGE_TAG=$Tag`n" }
$envContent | Set-Content -LiteralPath (Join-Path $releaseDirectory 'prod.env') -Encoding utf8NoBOM

Write-Host 'Exporting Docker images. This can create a large images.tar file.' -ForegroundColor Cyan
Invoke-Docker save --output (Join-Path $releaseDirectory 'images.tar') "nsh-frontend:$Tag" "nsh-backend-my:$Tag" redis:7

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
