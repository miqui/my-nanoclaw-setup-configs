#!/usr/bin/env python3
"""
validate.py — Structural validation for OpenAPI 3.2 documents.

Checks:
  - File parses as YAML or JSON.
  - Top-level `openapi` field is `3.2.x`.
  - Required top-level fields are present (`info`, `paths` or `webhooks` or `components`).
  - `info.title`, `info.version` are present and non-empty.
  - All internal `$ref`s resolve.
  - No duplicate `operationId`s.
  - No 3.0-era nullability patterns (`nullable: true`, singular `example` inside Schema Objects, boolean `exclusiveMinimum` / `exclusiveMaximum`).
  - Path templating is well-formed.

Note: This is structural sanity, not full schema validation. For that, use a
dedicated tool like `openapi-spec-validator` or `redocly lint` once you have
3.2 support installed.

Usage:
  python validate.py path/to/openapi.yaml
  python validate.py path/to/openapi.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install --break-system-packages pyyaml")
    sys.exit(2)


PATH_TEMPLATE_RE = re.compile(r"\{([^}]+)\}")
VALID_PATH_PARAM_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Failure(Exception):
    pass


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    # YAML by default — covers .yaml, .yml, and unsuffixed
    return yaml.safe_load(text)


def check_version(doc: dict, errors: list[str]) -> None:
    v = doc.get("openapi")
    if not isinstance(v, str):
        errors.append("Missing top-level `openapi` string field.")
        return
    if not v.startswith("3.2"):
        errors.append(f"Expected openapi 3.2.x, got {v!r}. This validator targets 3.2.")


def check_info(doc: dict, errors: list[str]) -> None:
    info = doc.get("info")
    if not isinstance(info, dict):
        errors.append("Missing or non-object `info`.")
        return
    for key in ("title", "version"):
        val = info.get(key)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"`info.{key}` is required and must be a non-empty string.")


def check_top_level_content(doc: dict, errors: list[str]) -> None:
    if not any(k in doc for k in ("paths", "webhooks", "components")):
        errors.append("Document must contain at least one of `paths`, `webhooks`, or `components`.")


def walk(node: Any, path: list[Any], visit):
    visit(node, path)
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [k], visit)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + [i], visit)


def collect_refs_and_definitions(doc: dict):
    refs: list[tuple[str, list[Any]]] = []

    def visit(node, path):
        if isinstance(node, dict) and "$ref" in node and isinstance(node["$ref"], str):
            refs.append((node["$ref"], path))

    walk(doc, [], visit)
    return refs


def resolve_internal_ref(doc: dict, ref: str) -> bool:
    if not ref.startswith("#/"):
        # External refs: out of scope for structural check; assume valid.
        return True
    parts = ref[2:].split("/")
    cur: Any = doc
    for p in parts:
        # decode JSON-pointer escapes
        p = p.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        elif isinstance(cur, list):
            try:
                cur = cur[int(p)]
            except (ValueError, IndexError):
                return False
        else:
            return False
    return True


def check_refs(doc: dict, errors: list[str]) -> None:
    for ref, path in collect_refs_and_definitions(doc):
        if not resolve_internal_ref(doc, ref):
            errors.append(f"Unresolved $ref `{ref}` at {format_path(path)}.")


def check_operation_ids(doc: dict, errors: list[str]) -> None:
    seen: dict[str, list[str]] = {}

    HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace", "query"}

    paths = doc.get("paths") or {}
    if not isinstance(paths, dict):
        return
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() in HTTP_METHODS and isinstance(op, dict):
                op_id = op.get("operationId")
                if isinstance(op_id, str):
                    seen.setdefault(op_id, []).append(f"{method.upper()} {path}")
            if method == "additionalOperations" and isinstance(op, dict):
                for ext_method, ext_op in op.items():
                    if isinstance(ext_op, dict):
                        op_id = ext_op.get("operationId")
                        if isinstance(op_id, str):
                            seen.setdefault(op_id, []).append(f"{ext_method} {path} (additionalOperations)")

    for op_id, locations in seen.items():
        if len(locations) > 1:
            errors.append(f"Duplicate operationId `{op_id}` at: {', '.join(locations)}")


def check_legacy_patterns(doc: dict, errors: list[str]) -> None:
    """Flag 3.0-era patterns that should be migrated when bumping to 3.2."""
    found_nullable: list[str] = []
    found_singular_example: list[str] = []
    found_bool_exclusive: list[str] = []

    def visit(node, path):
        if not isinstance(node, dict):
            return
        # Schema Object detection: nodes inside `schemas`, `properties`, or where `type` is set.
        looks_like_schema = "type" in node or "properties" in node or "items" in node or "$ref" in node

        if "nullable" in node:
            found_nullable.append(format_path(path))
        if looks_like_schema and "example" in node and "examples" not in node:
            # Per JSON Schema 2020-12 + OAS 3.1+, schemas should use `examples` (array).
            found_singular_example.append(format_path(path))
        for key in ("exclusiveMinimum", "exclusiveMaximum"):
            if isinstance(node.get(key), bool):
                found_bool_exclusive.append(f"{format_path(path)} ({key})")

    walk(doc, [], visit)

    for loc in found_nullable:
        errors.append(f"Legacy `nullable: true` at {loc}. Use `type: [..., \"null\"]`.")
    for loc in found_singular_example:
        errors.append(f"Singular `example` inside Schema Object at {loc}. Use `examples` (array).")
    for loc in found_bool_exclusive:
        errors.append(f"Boolean `exclusiveMinimum`/`exclusiveMaximum` at {loc}. Use a numeric value.")


def check_path_templating(doc: dict, errors: list[str]) -> None:
    paths = doc.get("paths") or {}
    if not isinstance(paths, dict):
        return
    HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace", "query"}
    for path, item in paths.items():
        if not isinstance(path, str) or not path.startswith("/"):
            errors.append(f"Path `{path}` must start with `/`.")
            continue
        if not isinstance(item, dict):
            continue
        templated = PATH_TEMPLATE_RE.findall(path)
        for name in templated:
            if not VALID_PATH_PARAM_NAME.match(name):
                errors.append(f"Path parameter name `{{{name}}}` in `{path}` is not a valid identifier.")
        # Each templated name must be declared as a path parameter
        declared = set()
        for params_source in (item.get("parameters") or [],):
            for p in params_source:
                if isinstance(p, dict) and p.get("in") == "path" and isinstance(p.get("name"), str):
                    declared.add(p["name"])
        for method, op in item.items():
            if method.lower() in HTTP_METHODS and isinstance(op, dict):
                for p in op.get("parameters") or []:
                    if isinstance(p, dict) and p.get("in") == "path" and isinstance(p.get("name"), str):
                        declared.add(p["name"])
        for name in templated:
            if name not in declared:
                errors.append(f"Path `{path}` templates `{{{name}}}` but does not declare it as a parameter.")


def format_path(parts: list[Any]) -> str:
    return "/" + "/".join(str(p) for p in parts) if parts else "/"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <openapi.yaml | openapi.json>")
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    try:
        doc = load(path)
    except Exception as e:
        print(f"PARSE ERROR: {e}")
        return 1

    if not isinstance(doc, dict):
        print("ERROR: top-level document must be an object/map.")
        return 1

    errors: list[str] = []
    check_version(doc, errors)
    check_info(doc, errors)
    check_top_level_content(doc, errors)
    check_refs(doc, errors)
    check_operation_ids(doc, errors)
    check_legacy_patterns(doc, errors)
    check_path_templating(doc, errors)

    if errors:
        print(f"FAIL: {len(errors)} issue(s) in {path}\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {path} parses as a valid-looking OAS 3.2 document.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
