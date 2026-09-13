"""Build a partial SDK development archive, never a full deployment release."""

import hashlib
import json
import re
import uuid
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
ALLOWLIST = frozenset(
    {
        'README.md',
        'sdk/javascript/client.js',
        'sdk/javascript/package.json',
        'sdk/python/nsh_client.py',
        'postman/collection.json',
        'contracts/openapi.json',
        'contracts/api-catalogue.json',
    }
)
FORBIDDEN_CONTENT = (
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
    re.compile(
        rb'(?i)\b(?:DB_PASSWORD|REDIS_PASSWORD|JWT_SECRET_KEY|BOT_HMAC_KEY)\s*[\"\']?\s*[:=]\s*[\"\']?[^\s\"\'$<>]'
    ),
)


def validate_bundle_files(files: dict[str, bytes]) -> None:
    for name, content in files.items():
        if name not in ALLOWLIST:
            raise ValueError(f'File not in bundle allowlist: {name}')
        if any(pattern.search(content) for pattern in FORBIDDEN_CONTENT):
            # Never include the matched value in error output.
            raise ValueError(f'Potential credential detected in allowed file: {name}')


def build_bundle(files: dict[str, bytes], output_dir: Path) -> Path:
    validate_bundle_files(files)
    manifest = {
        'bundleVersion': '0.1.0',
        'developmentOnly': True,
        'fullObjectiveComplete': False,
        'realWechatVerified': False,
        'backendIncluded': False,
        'authorizationAuditComplete': False,
        'files': {
            name: {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            for name, content in sorted(files.items())
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f'nsh-integration-foundation-0.1.0-{uuid.uuid4().hex[:8]}.zip'
    # Exclusive creation: never overwrite an existing user archive.
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(f'{checksum}  {output.name}\n', encoding='ascii')
    return output


def main() -> None:
    sdk = PROJECT / 'integration-sdk'
    contracts = PROJECT / '.artifacts' / 'integration-contract'
    paths = {
        'README.md': sdk / 'README.md',
        'sdk/javascript/client.js': sdk / 'javascript' / 'client.js',
        'sdk/javascript/package.json': sdk / 'javascript' / 'package.json',
        'sdk/python/nsh_client.py': sdk / 'python' / 'nsh_client.py',
        'postman/collection.json': sdk / 'postman' / 'collection.json',
        'contracts/openapi.json': contracts / 'openapi.json',
        'contracts/api-catalogue.json': contracts / 'api-catalogue.json',
    }
    files = {name: path.read_bytes() for name, path in paths.items()}
    print(build_bundle(files, contracts))


if __name__ == '__main__':
    main()
