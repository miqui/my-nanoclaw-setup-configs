---
name: openapi-api-designer
description: Design HTTP APIs from business capabilities and emit an OpenAPI 3.2.0 document in YAML (preferred) or JSON.
trigger: "design an openapi spec, design an api, openapi-api-designer"
---

# Skill: openapi-api-designer

Design HTTP APIs from business capabilities and emit an OpenAPI 3.2.0 document in YAML (preferred) or JSON.

## Purpose

This skill enables an AI agent to:

- Take business capabilities, domain concepts, and non-functional requirements.
- Apply a given REST API style guide for paths, naming, pagination, errors, and status codes.
- Optimize the resulting API contract for AI/semantic usage with rich descriptions and examples.
- Produce a syntactically valid OpenAPI Specification v3.2.0 document suitable for documentation, client/server generation, and AI agents.[web:15][web:17]

## Inputs

The skill is defined as a JSON-schema tool in `skill.json` with the following key fields:

- `api_name` – Human-friendly name for the API.
- `api_version` – Version string for `info.version` and optionally the path (for example, `v1`).
- `business_capabilities` – Array of paragraphs describing capabilities and use cases.
- `domain_model` – Optional narrative of entities and relationships.
- `style_guide` – REST API style guide text or URL (naming, pagination, errors, status codes, etc.).
- `ai_semantic_best_practices` – Guidelines for LLM-friendly contracts (descriptions, examples, tagging).
- `non_functional_requirements` – Optional performance/consistency/tenancy requirements.
- `security_requirements` – Optional description of authn/z patterns to be modeled as `securitySchemes`.
- `output_format` – `"yaml"` (default) or `"json"`.
- `level_of_detail` – `"skeleton"`, `"standard"`, or `"rich"`.

See `skill.json` for the full JSON schema.

## Behavior

The behavior prompt is defined in `prompt.md` and instructs the agent to:

- Use contract-first, capability-driven design.
- Treat the REST style guide as authoritative.
- Conform to the OpenAPI 3.2.0 structure (`openapi`, `info`, `servers`, `paths`, `components`, etc.).[web:15][web:17]
- Provide clear, natural-language descriptions and realistic examples to enhance AI/semantic understanding.[web:18][web:25]
- Reflect non-functional and security requirements.

The agent must output only a single OpenAPI 3.2.0 document, with no extra commentary.

## Output

The skill returns a complete OpenAPI 3.2.0 document:

- Root field `openapi: 3.2.0`.
- Populated `info`, `servers`, optional `tags`.
- `paths` with operations, parameters, request bodies, and responses.
- `components` with `schemas`, `responses`, `parameters`, `requestBodies`, and `securitySchemes` as needed.[web:15][web:17]

The file can be persisted as `*.yaml` or `*.json` and validated with any OpenAPI 3.x-aware tooling.
