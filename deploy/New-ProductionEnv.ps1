[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot 'prod.env'),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if ((Test-Path -LiteralPath $OutputPath) -and -not $Force) {
    throw "Production environment file already exists: $OutputPath. Use -Force only when you intentionally want to replace it."
}

function New-HexSecret {
    param([int]$ByteCount)

    $bytes = New-Object byte[] $ByteCount
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }
    return (([System.BitConverter]::ToString($bytes) -replace '-', '').ToLowerInvariant())
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot 'ruoyi-fastapi-backend/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "The backend virtual environment was not found: $python. Create the local backend environment before generating production keys."
}

$keyGenerator = @'
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode('utf-8')
public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode('utf-8')
print(json.dumps({'private': private_pem, 'public': public_pem}))
'@

$keyPair = (& $python -c $keyGenerator | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or -not $keyPair.private -or -not $keyPair.public) {
    throw 'The local Python environment failed to generate the RSA transport key pair.'
}

$privateKey = $keyPair.private.Trim() -replace "`r?`n", '\n'
$publicKey = $keyPair.public.Trim() -replace "`r?`n", '\n'
$mysqlPassword = New-HexSecret 32
$redisPassword = New-HexSecret 32
$jwtSecret = New-HexSecret 48

    $content = @"
# Generated locally. This file contains deployment secrets: do not commit or share it.
FRONTEND_PORT=12580
APP_IMAGE_TAG=local

APP_NAME=Nsh Guild Console
APP_VERSION=1.9.0

# Baota MySQL 8 runs on the server host. Create this database user in Baota
# using the password below before starting Docker.
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_DATABASE=ruoyi-fastapi
MYSQL_USERNAME=nsh_app
MYSQL_PASSWORD=$mysqlPassword
DOCKER_NETWORK_SUBNET=172.28.0.0/16
REDIS_PASSWORD=$redisPassword

JWT_SECRET_KEY=$jwtSecret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
JWT_REDIS_EXPIRE_MINUTES=30

APP_WORKERS=1
APP_SAME_TIME_LOGIN=true
APP_DEMO_MODE=false
APP_TRUSTED_PROXY_IPS=127.0.0.1,::1
APP_TRUSTED_PROXY_HOPS=1

LOGURU_LEVEL=INFO
LOGURU_STDOUT=true
LOG_FILE_ENABLED=true
LOG_INSTANCE_ID=prod
LOG_SERVICE_NAME=ruoyi-fastapi-backend

# Leave this empty. Configure the runtime key after deployment through
# System Management -> AIKey Management; it is encrypted and saved in MySQL.
MIMO_API_KEY=
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
MIMO_TIMEOUT_SECONDS=60
MIMO_MAX_COMPLETION_TOKENS=2048

TRANSPORT_CRYPTO_ENABLED=true
TRANSPORT_CRYPTO_MODE=optional
TRANSPORT_CRYPTO_KID=prod-1
TRANSPORT_CRYPTO_RSA_KEY_SIZE=4096
TRANSPORT_CRYPTO_PUBLIC_KEY='$publicKey'
TRANSPORT_CRYPTO_PRIVATE_KEY='$privateKey'
"@
$content | Set-Content -LiteralPath $OutputPath -Encoding utf8NoBOM
Write-Host "Created production environment file: $OutputPath" -ForegroundColor Green
Write-Host 'Create the Baota MySQL database/user with MYSQL_* values before starting Docker.' -ForegroundColor Yellow
Write-Host 'Keep MIMO_API_KEY empty. After deployment, configure it in System Management -> AIKey Management.' -ForegroundColor Yellow
