[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$Server,
    [Parameter(Mandatory)] [string]$User,
    [Parameter(Mandatory)] [string]$ReleaseDirectory,
    [string]$RemoteRoot = '/opt/nsh',
    [int]$Port = 22
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command ssh -ErrorAction SilentlyContinue) -or -not (Get-Command scp -ErrorAction SilentlyContinue)) {
    throw 'Windows OpenSSH (ssh and scp) is required. Install it from Windows Optional Features, then run this script again.'
}

$release = (Resolve-Path -LiteralPath $ReleaseDirectory).Path
if (-not (Test-Path -LiteralPath (Join-Path $release 'images.tar'))) {
    throw "images.tar was not found in $release. Run Prepare-OfflineRelease.ps1 first."
}

$releaseName = Split-Path -Leaf $release
$remoteRelease = "$RemoteRoot/$releaseName"
$target = "$User@$Server"

& ssh -p $Port $target "mkdir -p '$remoteRelease'"
if ($LASTEXITCODE -ne 0) { throw 'Could not create the release directory on the server.' }

Write-Host 'Uploading the offline release. The image archive can be large; this step depends on your upload bandwidth.' -ForegroundColor Cyan
& scp -P $Port -r "$release/*" "${target}:$remoteRelease/"
if ($LASTEXITCODE -ne 0) { throw 'Upload failed.' }

$remoteCommand = @"
set -e
cd '$remoteRelease'
sha256sum -c SHA256SUMS.txt
docker load -i images.tar
docker compose --env-file prod.env -f docker-compose.yml up -d --remove-orphans
docker compose --env-file prod.env -f docker-compose.yml ps
"@
& ssh -p $Port $target $remoteCommand
if ($LASTEXITCODE -ne 0) { throw 'The server failed while loading images or starting the release.' }

Write-Host "Deployment complete. Test it on the server with: curl -I http://127.0.0.1:12580/" -ForegroundColor Green
