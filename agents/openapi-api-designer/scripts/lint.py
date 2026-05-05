#!/usr/bin/env python3
"""
lint.py — Semantic-context linter for OpenAPI 3.2 documents.

Where validate.py asks "does it parse?", this asks "is it usable by an AI
agent and a human integrator?". It enforces the rules from
references/semantic-context-for-ai.md and references/design-checklist.md.

Rules (severity in brackets):

  [error]   E001 every operation has a `summary`
  [error]   E002 every operation has a non-empty `description`
  [error]   E003 every operation has an `operationId` matching ^[a-z][A-Za-z0-9]*$
  [error]   E004 every operation has at least one `tag`
  [error]   E005 every operation declares `x-business-capability`
  [error]   E006 every operation declares `x-idempotent`
  [error]   E007 every operation declares `x-side-effects`
  [error]   E008 every parameter has a non-empty `description`
  [error]   E009 every documented response has a `description`
  [error]   E010 error responses (4xx/5xx) use `application/problem+json`
  [error]   E011 every Schema Object in components.schemas has a `title` and `description`
  [warn]    W101 every operation has at least one `x-use-case` entry
  [warn]    W102 every parameter has an `example` or `examples`
  [warn]    W103 request bodies have at least one named example
  [warn]    W104 documented responses (2xx) include at least one example
  [warn]    W105 tags form a hierarchy (some tags have `parent`)
  [warn]    W106 every tag has both `summary` and `description`
  [warn]    W107 root has `externalDocs`
  [info]    I201 streaming responses use `itemSchema`

Usage:
  python lint.py path/to/openapi.yaml
  python lint.py --strict path/to/openapi.yaml      # warnings cause non-zero exit
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install --break-system-packages pyyaml")
    sys.exit(2)


HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace", "query"}
OP_ID_RE = re.compile(r"^[a-z][A-Za-z0-9]*$")
STREAMING_MEDIA_TYPES = {
    "text/event-stream",
    "application/jsonl",
    "application/x-ndjson",
    "application/json-seq",
}


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def is_non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def iter_operations(doc: dict):
    """Yield (path, method, op) tuples, including additionalOperations."""
    paths = doc.get("paths") or {}
    if not isinstance(paths, dict):
        return
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() in HTTP_METHODS and isinstance(op, dict):
                yield path, method.lower(), op
            if method == "additionalOperations" and isinstance(op, dict):
                for ext_method, ext_op in op.items():
                    if isinstance(ext_op, dict):
                        yield path, ext_method.lower(), ext_op


def lint(doc: dict) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    # Operation-level checks
    for path, method, op in iter_operations(doc):
        prefix = f"{method.upper()} {path}"

        if not is_non_empty_str(op.get("summary")):
            errors.append(f"E001 {prefix}: missing or empty `summary`.")
        if not is_non_empty_str(op.get("description")):
            errors.append(f"E002 {prefix}: missing or empty `description`.")

        op_id = op.get("operationId")
        if not isinstance(op_id, str):
            errors.append(f"E003 {prefix}: missing `operationId`.")
        elif not OP_ID_RE.match(op_id):
            errors.append(
                f"E003 {prefix}: operationId `{op_id}` should be camelCase verbResource style."
            )

        tags = op.get("tags")
        if not (isinstance(tags, list) and tags):
            errors.append(f"E004 {prefix}: missing `tags`.")

        if not is_non_empty_str(op.get("x-business-capability")):
            errors.append(f"E005 {prefix}: missing `x-business-capability`.")

        if "x-idempotent" not in op or not isinstance(op["x-idempotent"], bool):
            errors.append(f"E006 {prefix}: missing or non-boolean `x-idempotent`.")

        if not is_non_empty_str(op.get("x-side-effects")):
            errors.append(f"E007 {prefix}: missing `x-side-effects`.")

        # parameters
        for p in op.get("parameters") or []:
            if isinstance(p, dict) and "$ref" not in p:
                pname = p.get("name", "<unnamed>")
                pwhere = f"{prefix} parameter `{pname}`"
                if not is_non_empty_str(p.get("description")):
                    errors.append(f"E008 {pwhere}: missing `description`.")
                if "example" not in p and "examples" not in p:
                    warnings.append(f"W102 {pwhere}: no `example` or `examples` provided.")

        # request body
        rb = op.get("requestBody")
        if isinstance(rb, dict):
            content = rb.get("content") or {}
            for mt, m in content.items():
                if isinstance(m, dict):
                    has_named_example = isinstance(m.get("examples"), dict) and len(m["examples"]) >= 1
                    has_value = "example" in m
                    if not (has_named_example or has_value):
                        warnings.append(
                            f"W103 {prefix} requestBody[{mt}]: no example or examples."
                        )

        # responses
        responses = op.get("responses") or {}
        for status, resp in responses.items():
            if not isinstance(resp, dict):
                continue
            if "$ref" in resp:
                continue  # referenced — assume the referenced response is well-formed
            rwhere = f"{prefix} response {status}"
            if not is_non_empty_str(resp.get("description")):
                errors.append(f"E009 {rwhere}: missing `description`.")

            content = resp.get("content") or {}
            # error responses must use application/problem+json
            if isinstance(status, str) and status.startswith(("4", "5")):
                if content and "application/problem+json" not in content:
                    errors.append(
                        f"E010 {rwhere}: error responses must offer `application/problem+json`."
                    )

            # 2xx success responses should have an example
            if isinstance(status, str) and status.startswith("2"):
                has_example = False
                for mt, m in content.items():
                    if isinstance(m, dict):
                        if "example" in m or (isinstance(m.get("examples"), dict) and m["examples"]):
                            has_example = True
                            break
                if content and not has_example:
                    warnings.append(f"W104 {rwhere}: no example provided.")

            # streaming responses should use itemSchema
            for mt, m in content.items():
                if mt in STREAMING_MEDIA_TYPES and isinstance(m, dict):
                    if "itemSchema" not in m:
                        info.append(
                            f"I201 {rwhere} {mt}: streaming media type without `itemSchema` (3.2 feature)."
                        )

        # x-use-case
        uc = op.get("x-use-case")
        if not (isinstance(uc, list) and uc):
            warnings.append(f"W101 {prefix}: missing or empty `x-use-case`.")

    # components.schemas — title + description
    components = doc.get("components") or {}
    schemas = components.get("schemas") or {}
    if isinstance(schemas, dict):
        for name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            if not is_non_empty_str(schema.get("title")):
                errors.append(f"E011 components.schemas.{name}: missing `title`.")
            if not is_non_empty_str(schema.get("description")):
                errors.append(f"E011 components.schemas.{name}: missing `description`.")

    # tags — hierarchy and metadata
    tags = doc.get("tags") or []
    if isinstance(tags, list) and tags:
        any_parent = any(isinstance(t, dict) and "parent" in t for t in tags)
        if not any_parent:
            warnings.append("W105 tags: no hierarchy detected (consider OAS 3.2 `parent` on tags).")
        for t in tags:
            if isinstance(t, dict):
                tn = t.get("name", "<unnamed>")
                if not is_non_empty_str(t.get("summary")):
                    warnings.append(f"W106 tag `{tn}`: missing `summary`.")
                if not is_non_empty_str(t.get("description")):
                    warnings.append(f"W106 tag `{tn}`: missing `description`.")

    # root externalDocs
    if "externalDocs" not in doc:
        warnings.append("W107 root: missing `externalDocs`.")

    return errors, warnings, info


def main(argv: list[str]) -> int:
    strict = False
    args = argv[1:]
    if args and args[0] == "--strict":
        strict = True
        args = args[1:]
    if len(args) != 1:
        print(f"Usage: {argv[0]} [--strict] <openapi.yaml | openapi.json>")
        return 2

    path = Path(args[0])
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

    errors, warnings, info = lint(doc)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")
    if info:
        print(f"\nINFO ({len(info)}):")
        for i in info:
            print(f"  {i}")

    if not (errors or warnings or info):
        print(f"OK: {path} passes the semantic-context lint.")
        return 0

    print()
    print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s), {len(info)} info.")

    if errors:
        return 1
    if strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
