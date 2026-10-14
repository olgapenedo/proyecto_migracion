"""Agent-managed dbt Core v1 runtimes and profiles for parse-only validation."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any

import yaml

# Trusted installation recipes, NOT a registry of supported dbt platforms.
# Repository text and LLM output can never supply arbitrary package names/URLs.
RECIPES = {
    'snowflake': ('dbt-snowflake', 'snowflake'),
    'bigquery': ('dbt-bigquery', 'bigquery'),
    'postgresql': ('dbt-postgres', 'postgres'),
    'postgres': ('dbt-postgres', 'postgres'),
    'sqlserver': ('dbt-sqlserver', 'sqlserver'),
    'microsoftsqlserver': ('dbt-sqlserver', 'sqlserver'),
    'redshift': ('dbt-redshift', 'redshift'),
    'duckdb': ('dbt-duckdb', 'duckdb'),
    'databricks': ('dbt-databricks', 'databricks'),
    'apachespark': ('dbt-spark', 'spark'),
}


class DbtPreparationError(RuntimeError):
    """Safe diagnostic without pip output, credentials or repository content."""


def recipe(adapter: str) -> tuple[str, str]:
    key = re.sub(r'[^a-z0-9]', '', adapter.lower())
    if key not in RECIPES:
        raise DbtPreparationError('No hay receta de instalación verificada para este adaptador; no se instalarán paquetes sugeridos por el repositorio o el LLM.')
    return RECIPES[key]


def runtime_env() -> dict[str, str]:
    allowed = {'PATH', 'HOME', 'USER', 'TMPDIR', 'SYSTEMROOT', 'SSL_CERT_FILE',
               'REQUESTS_CA_BUNDLE', 'HTTPS_PROXY', 'HTTP_PROXY', 'NO_PROXY'}
    env = {k:v for k,v in os.environ.items() if k in allowed or k.startswith('DBT_')}
    env['DBT_SEND_ANONYMOUS_USAGE_STATS'] = 'false'
    return env


def prepare_dbt_runtime(adapter: str, cache_dir: Path | None = None) -> dict[str, Any]:
    package, profile_type = recipe(adapter)
    cache = cache_dir or Path(__file__).resolve().parent / '.cache' / 'dbt-runtimes'
    root = cache / f'py{sys.version_info.major}{sys.version_info.minor}' / package
    bin_dir = root / ('Scripts' if os.name == 'nt' else 'bin')
    python = bin_dir / ('python.exe' if os.name == 'nt' else 'python')
    executable = bin_dir / ('dbt.exe' if os.name == 'nt' else 'dbt')
    marker = root / 'agent-runtime.json'
    requirements = ['dbt-core>=1.9,<2', f'{package}>=1.9,<2']
    # Stamp is written only after install and dbt --version both succeed.
    ready = False
    if marker.is_file() and executable.is_file() and python.is_file():
        try:
            ready = json.loads(marker.read_text()).get('requirements') == requirements
        except (ValueError, OSError):
            pass
    if not ready:
        print(f'Preparando dbt para {adapter}: {package} (entorno separado)...', flush=True)
        try:
            venv.EnvBuilder(with_pip=True).create(root)
            result = subprocess.run([str(python), '-m', 'pip', '--isolated', 'install',
                '--disable-pip-version-check', '--index-url', 'https://pypi.org/simple', *requirements],
                capture_output=True, text=True, timeout=600, check=False, env=runtime_env())
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DbtPreparationError(f'No se pudo preparar {package}: creación del entorno o descarga fallida. Comprueba red y compatibilidad de Python.') from exc
        if result.returncode:
            raise DbtPreparationError(f'La instalación de {package} falló. Comprueba acceso a PyPI y compatibilidad con Python {sys.version_info.major}.{sys.version_info.minor}.')
    try:
        check = subprocess.run([str(executable), '--version'], capture_output=True,
            text=True, timeout=60, check=False, env=runtime_env())
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DbtPreparationError(f'No se puede iniciar el runtime de {package}.') from exc
    if check.returncode:
        raise DbtPreparationError(f'El runtime de {package} no supera dbt --version.')
    if not ready:
        marker.write_text(json.dumps({'requirements': requirements}, indent=2))
    return {'adapter': adapter, 'package': package, 'profile_type': profile_type,
            'executable': str(executable), 'reused': ready}


def parse_only_output(profile_type: str) -> dict[str, Any]:
    """Synthetic adapter-valid settings, used only by dbt parse (no warehouse IO)."""
    common: dict[str, Any] = {'type': profile_type, 'threads': 1, 'schema': 'parse_only'}
    if profile_type == 'snowflake':
        return {**common, 'account': 'parse-only', 'user': 'parse-only',
                'password': 'parse-only-placeholder', 'database': 'PARSE_ONLY', 'warehouse': 'PARSE_ONLY'}
    if profile_type == 'bigquery':
        return {'type':'bigquery', 'method':'oauth', 'project':'parse-only-project',
                'dataset':'parse_only', 'threads':1}
    if profile_type in {'postgres', 'redshift'}:
        return {**common, 'host':'127.0.0.1', 'port':5432, 'user':'parse_only',
                'password':'parse-only-placeholder', 'dbname':'parse_only'}
    if profile_type == 'duckdb':
        return {**common, 'path':':memory:'}
    if profile_type == 'databricks':
        return {**common, 'host':'parse-only.example.invalid',
                'http_path':'/sql/1.0/warehouses/parse-only', 'token':'parse-only-placeholder'}
    if profile_type == 'spark':
        return {**common, 'method':'thrift', 'host':'127.0.0.1', 'port':10000}
    if profile_type == 'sqlserver':
        return {**common, 'driver':'ODBC Driver 18 for SQL Server', 'server':'127.0.0.1',
                'database':'parse_only', 'user':'parse_only', 'password':'parse-only-placeholder'}
    raise DbtPreparationError('No hay plantilla de perfil parse-only verificada para este adaptador.')


def prepare_parse_profile(profile_name: str, adapter: str, destination: Path,
                          supplied_dir: str | None = None) -> str:
    """Copy only the requested local profile, or generate a parse-only fallback.

    Never write to ~/.dbt; never read profiles from the repository being analyzed.
    An explicitly configured profile is respected, not silently repaired.
    """
    _, profile_type = recipe(adapter)
    if not re.fullmatch(r'[a-z][a-z0-9_]*', profile_name):
        raise DbtPreparationError('Nombre de perfil generado inválido.')
    selected = None
    if supplied_dir:
        local_file = Path(supplied_dir).expanduser().resolve() / 'profiles.yml'
        if local_file.is_file():
            try:
                payload = yaml.safe_load(local_file.read_text()) or {}
                if not isinstance(payload, dict):
                    raise ValueError('Invalid mapping')
                selected = payload.get(profile_name)
                if selected is not None and not isinstance(selected, dict):
                    raise ValueError('Invalid profile')
            except (OSError, ValueError, yaml.YAMLError) as exc:
                raise DbtPreparationError('El profiles.yml local no es válido; no se reemplazará su configuración.') from exc
    if selected is None:
        selected = {'target':'parse_only', 'outputs':{'parse_only':parse_only_output(profile_type)}}
        mode = 'generated_parse_only'
    else:
        mode = 'provided_local'
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / 'profiles.yml'
    output.write_text(yaml.safe_dump({profile_name:selected}, sort_keys=False))
    output.chmod(0o600)
    return mode
