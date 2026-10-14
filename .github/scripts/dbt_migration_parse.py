import json
import subprocess
import sys
import tempfile
from pathlib import Path
import yaml
from dbt_runtime import prepare_dbt_runtime, prepare_parse_profile, runtime_env

root = Path.cwd().resolve()
payload = json.loads(Path(sys.argv[1]).read_text())
if not payload.get('projects'):
    raise ValueError('No dbt projects to validate')
for project in payload['projects']:
    path = (root / project['path']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Unsafe project path')
    # Only the generator-supported files participate in parse.
    if any(path.glob('macros/**/*')) or (path / 'packages.yml').exists() or (path / 'dependencies.yml').exists():
        raise ValueError('Unapproved macros or packages')
    config = yaml.safe_load((path / 'dbt_project.yml').read_text())
    if set(config) - {'name','version','config-version','profile','model-paths','seed-paths'}:
        raise ValueError('Unapproved project configuration')
    runtime = prepare_dbt_runtime(project['adapter'])
    with tempfile.TemporaryDirectory() as directory:
        profiles = Path(directory)
        prepare_parse_profile(config['profile'], project['adapter'], profiles)
        subprocess.run([runtime['executable'], 'parse', '--project-dir', str(path),
            '--profiles-dir', str(profiles), '--no-partial-parse'], check=True,
            timeout=180, env=runtime_env())
