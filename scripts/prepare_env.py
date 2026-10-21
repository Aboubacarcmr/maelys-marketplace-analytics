"""Initialise des mots de passe pédagogiques sans les committer dans Git."""
from pathlib import Path
import base64
import os
import secrets

root = Path(__file__).resolve().parents[1]
source = root / '.env.example'
dest = root / '.env'
if dest.exists():
    print('Le fichier .env existe déjà : inchangé.')
    raise SystemExit(0)
values = {
    'AIRFLOW_UID': str(os.getuid()) if hasattr(os,'getuid') else '50000',
    'AIRFLOW_ADMIN_PASSWORD': secrets.token_urlsafe(18),
    'AIRFLOW_FERNET_KEY': base64.urlsafe_b64encode(os.urandom(32)).decode(),
    'AIRFLOW_JWT_SECRET': secrets.token_urlsafe(35),
    'AIRFLOW_PASSWORD': secrets.token_urlsafe(18),
    'DWH_PASSWORD': secrets.token_urlsafe(18),
    'MINIO_ROOT_PASSWORD': secrets.token_urlsafe(18),
    'METABASE_ADMIN_PASSWORD': secrets.token_urlsafe(18),
}
lines = []
for line in source.read_text().splitlines():
    if '=' in line and not line.strip().startswith('#'):
        key = line.split('=',1)[0]
        if key in values:
            line = f'{key}={values[key]}'
    lines.append(line)
dest.write_text('\n'.join(lines)+'\n')
dest.chmod(0o600)
print('Fichier .env créé avec des secrets aléatoires. Ne pas publier.')
print('Pour voir les identifiants : grep -E "^(AIRFLOW_ADMIN_|METABASE_ADMIN_|MINIO_ROOT_)" .env')
