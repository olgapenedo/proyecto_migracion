"""Static checks for generated dbt models; SQL and repository code are never executed."""
from __future__ import annotations

import json
import csv
import io
import re
import sys
from pathlib import Path
from typing import Any

import sqlglot
import yaml
from sqlglot.optimizer.scope import build_scope, Scope
from jinja2 import StrictUndefined, nodes
from jinja2.sandbox import SandboxedEnvironment


def _render_model(sql: str, incremental: bool) -> tuple[str, set[str]]:
    dependencies: set[str] = set()
    env = SandboxedEnvironment(undefined=StrictUndefined)
    env.globals.clear()
    env.filters.clear()
    tree = env.parse(sql)
    allowed_nodes = (nodes.Template, nodes.Output, nodes.TemplateData, nodes.Call,
                     nodes.Name, nodes.Const, nodes.Keyword, nodes.List, nodes.If)
    for node in [tree, *tree.find_all(nodes.Node)]:
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported Jinja construct: {type(node).__name__}")
        if isinstance(node, nodes.Name) and node.name not in {
            "ref", "source", "config", "is_incremental", "this"
        }:
            raise ValueError(f"Unsupported Jinja name: {node.name}")
        if isinstance(node, nodes.Call):
            if not isinstance(node.node, nodes.Name) or node.node.name not in {
                "ref", "source", "config", "is_incremental"
            }:
                raise ValueError("Unsupported Jinja function")
            if node.dyn_args or node.dyn_kwargs:
                raise ValueError("Dynamic Jinja arguments are forbidden")

    def ref(name: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("Invalid ref name")
        dependencies.add(f"ref:{name.casefold()}")
        return f'"ref_{name}"'

    def source(name: str, table: str) -> str:
        if not all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part) for part in (name, table)):
            raise ValueError("Invalid source name")
        dependencies.add(f"source:{name.casefold()}.{table.casefold()}")
        return f'"source_{name}_{table}"'

    def config(**kwargs: Any) -> str:
        allowed = {"materialized", "unique_key", "incremental_strategy", "on_schema_change", "alias"}
        if set(kwargs) - allowed:
            raise ValueError("Unsupported dbt config")
        if kwargs.get("materialized", "view") not in {"view", "table", "incremental", "ephemeral"}:
            raise ValueError("Unsupported materialization")
        if kwargs.get("materialized") == "incremental" and not kwargs.get("unique_key"):
            raise ValueError("Incremental model requires unique_key")
        for key, value in kwargs.items():
            if not isinstance(value, (str, list)) or (isinstance(value, list) and
                    not all(isinstance(item, str) for item in value)):
                raise ValueError(f"Unsupported dbt config value: {key}")
        return ""

    env.globals.update(ref=ref, source=source, config=config,
                       is_incremental=lambda: incremental, this='"target_model"')
    return env.from_string(sql).render(), dependencies


def projected_columns(query, relation_columns=None):
    """Resolve stars using parsed CTE/subqueries or independently parsed relations."""
    scope = build_scope(query)
    if scope is None:
        raise ValueError("Unable to resolve query columns")
    def columns(current):
        if current.set_operation_scopes:
            return columns(current.set_operation_scopes[0])
        result = []
        for projection in current.expression.selects:
            if not projection.is_star:
                result.append(projection.alias_or_name)
                continue
            star = projection.this if isinstance(projection, sqlglot.exp.Column) else projection
            if any(star.args.values()):
                raise ValueError("Wildcard modifiers require explicit column projection")
            alias = projection.table if isinstance(projection, sqlglot.exp.Column) else None
            sources = current.selected_sources
            selected = [sources[alias]] if alias and alias in sources else list(sources.values()) if not alias else []
            if not selected:
                raise ValueError("Unresolved wildcard relation")
            for _, source in selected:
                if isinstance(source, Scope):
                    result.extend(columns(source))
                elif relation_columns:
                    result.extend(relation_columns(source.name))
                else:
                    raise ValueError("Wildcard needs declared relation columns")
        return result
    return columns(scope)


def project_column_resolver(root, project, incremental, dialect, active=None):
    """Read upstream model SQL or source YAML, never infer stars from the contract."""
    active = set() if active is None else active
    def resolve(name):
        if name in active:
            raise ValueError("Cyclic wildcard model dependency")
        if name.startswith('ref_'):
            model = name[4:]
            candidates = list((project/'models').rglob(model+'.sql'))
            if len(candidates) == 1:
                active.add(name)
                try:
                    rendered, _ = _render_model(candidates[0].read_text(), incremental)
                    query = sqlglot.parse_one(rendered, read=dialect)
                    return projected_columns(query, resolve)
                finally:
                    active.remove(name)
            seeds = list((project/'seeds').rglob(model+'.csv'))
            if len(seeds) == 1:
                return next(csv.reader(io.StringIO(seeds[0].read_text())))
        for path in (project/'models').rglob('*.yml'):
            doc = yaml.safe_load(path.read_text()) or {}
            for source in doc.get('sources', []):
                for table in source.get('tables', []):
                    if name == 'source_'+source['name']+'_'+table['name']:
                        names = [c['name'] for c in table.get('columns', [])]
                        if names:
                            return names
        raise ValueError("Cannot resolve wildcard from model SQL, seed headers or source DDL")
    return resolve


def _validate_model(root: Path, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    relative = Path(contract.get("path", ""))
    if relative.is_absolute() or ".." in relative.parts:
        return ["model path is unsafe"]
    model_path = (root / relative).resolve()
    if not model_path.is_relative_to(root.resolve()) or not model_path.is_file():
        return [f"model file not found or escapes repository: {relative}"]

    try:
        artifact_type = contract.get("artifact_type")
        expected_columns = contract.get("expected_columns")
        if not isinstance(expected_columns, list) or not all(isinstance(x, str) for x in expected_columns):
            raise ValueError("invalid expected_columns contract")
        if artifact_type == "seed":
            rows = list(csv.reader(io.StringIO(model_path.read_text(encoding="utf-8"))))
            if len(rows) < 2 or rows[0] != expected_columns:
                raise ValueError("seed headers differ from contract or seed has no data rows")
            if len(set(rows[0])) != len(rows[0]) or any(len(row) != len(rows[0]) for row in rows[1:]):
                raise ValueError("seed headers must be unique and every row must match the header")
        elif artifact_type == "model":
            errors.extend(validate_model_contract(
                model_path.read_text(encoding="utf-8"), contract.get("dialect"),
                expected_columns, contract.get("expected_dependencies"),
                project=model_path.parent.parent, root=root
            ))
        else:
            raise ValueError("unsupported artifact_type")
    except Exception as exc:
        errors.append(f"{relative}: {str(exc)[:500]}")
    return errors


def validate_model_contract(sql: str, dialect: str, expected_columns: list[str],
                            expected_dependencies: list[str], *, project: Path | None = None,
                            root: Path | None = None) -> list[str]:
    if not isinstance(dialect, str) or dialect not in sqlglot.Dialect.classes:
        return ["invalid SQL dialect"]
    if not isinstance(expected_dependencies, list) or not all(isinstance(x, str) for x in expected_dependencies):
        return ["invalid expected_dependencies contract"]
    rendered_versions = [
        _render_model(sql, incremental)
        for incremental in (False, True)
    ]
    actual_dependencies = set().union(*(item[1] for item in rendered_versions))
    expected = [name.casefold() for name in expected_columns]
    for incremental, (rendered, _) in enumerate(rendered_versions):
        expressions = [
            expression for expression in sqlglot.parse(
                rendered, read=dialect, error_level=sqlglot.ErrorLevel.RAISE
            ) if expression is not None
        ]
        if len(expressions) != 1 or not isinstance(expressions[0], sqlglot.exp.Query):
            raise ValueError("model must contain exactly one SELECT/query")
        forbidden = (sqlglot.exp.DDL, sqlglot.exp.DML, sqlglot.exp.Command, sqlglot.exp.Into)
        if any(isinstance(node, forbidden) for node in expressions[0].walk()):
            raise ValueError("model contains a write or command")
        resolver = project_column_resolver(root, project, bool(incremental), dialect) if project else None
        actual_columns = [name.casefold() for name in projected_columns(expressions[0], resolver)]
        if actual_columns != expected:
            raise ValueError(
                f"projected columns differ from contract: expected {expected}, found {actual_columns}"
            )
    if actual_dependencies != set(expected_dependencies):
        raise ValueError(
            f"dependencies differ from contract: expected {sorted(expected_dependencies)}, "
            f"found {sorted(actual_dependencies)}"
        )
    return []


def validate_contracts(contracts_path: Path, root: Path | None = None) -> list[str]:
    root = (root or Path.cwd()).resolve()
    payload = json.loads(contracts_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != 1 or not isinstance(payload.get("artifacts"), list):
        return ["invalid migration contract file"]
    artifacts = payload["artifacts"]
    paths = [artifact.get("path") for artifact in artifacts if isinstance(artifact, dict)]
    if len(paths) != len(artifacts) or len(paths) != len(set(paths)):
        return ["migration contracts must list each artifact exactly once"]
    return [error for artifact in artifacts for error in _validate_model(root, artifact)]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: migration_ci_runner.py CONTRACTS.json", file=sys.stderr)
        return 2
    errors = validate_contracts(Path(sys.argv[1]))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("All generated dbt model contracts passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())