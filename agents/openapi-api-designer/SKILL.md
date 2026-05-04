---
name: openapi-3.2-designer
description: Design HTTP REST APIs with the OpenAPI 3.2.0 specification. Use this skill whenever the user wants to design, generate, draft, scaffold, or refactor an OpenAPI document, API contract, REST API spec, or service definition — including from product ideas, business capabilities, user stories, or domain models. Trigger even when "OpenAPI" isn't named: "design an API for X", "spec out endpoints for Y", "I need a REST API that does Z", "API contract", "API definition", or "API for AI agents / MCP / tool use" all count. Produces YAML (preferred) or JSON OpenAPI 3.2 documents grounded in the user's business capabilities and REST style guide, and deliberately enriched with semantic context so the spec is highly usable by both human developers and AI agents. Do NOT use for AsyncAPI, GraphQL, or gRPC/protobuf — only HTTP REST with OAS 3.2.
---

# OpenAPI 3.2 Designer

Design REST APIs as **OpenAPI 3.2.0** documents from three inputs: a product idea, the business capabilities it serves, and (optionally) a REST style guide. The output is optimized for two audiences at once: human developers who will implement and integrate, and AI agents (MCP servers, tool-use LLMs, codegen) that will consume the spec to call the API correctly.

The authoritative reference for syntax is the spec itself:
**https://spec.openapis.org/oas/v3.2.0.html** — when in doubt, read it. Do not invent fields.

---

## When to use this skill

Trigger on any request that asks to produce an API contract — even when phrased loosely. Examples:

- "Design an API for booking flights."
- "Spec out a REST API that exposes our orders capability."
- "I need an OpenAPI document for this idea: ..."
- "Convert these business capabilities into endpoints."
- "Draft an API our agents can call."
- "Create an OAS 3.2 spec for ..."

Skip this skill when:
- The user asks for AsyncAPI, GraphQL SDL, gRPC, or protobuf — those have their own contracts.
- The user wants implementation code, not the contract. (Generate the spec first; offer codegen as a follow-up.)
- The user only wants to **lint** or **validate** an existing spec — point them at `scripts/lint.py` and `scripts/validate.py` directly.

---

## Inputs to gather (before writing any YAML)

Get these explicitly. If the user hasn't provided one, ask once with concrete options — don't write the spec around assumptions.

1. **The idea / problem** — one to three sentences of what the API enables.
2. **Business capabilities** — *the most important input*. A capability is a stable thing the business does (e.g. "Schedule Management", "Passenger Identity", "Baggage Tracking"). Capabilities anchor resource boundaries, tag hierarchies, and ownership. See `references/business-capability-mapping.md`.
3. **REST style guide** — the user's house rules (naming, versioning, errors, pagination, auth). If absent, default to `references/rest-style-guide-default.md` and *say so explicitly* in the response so the user can override.
4. **Consumer profile** — humans only, or AI agents too? If AI agents are consumers, apply the full semantic-context checklist in `references/semantic-context-for-ai.md`. Default to assuming both.
5. **Output format** — YAML by default. Only emit JSON if explicitly requested.

If three or more of these are missing for a non-trivial API, ask before generating. For a small API (one or two resources), reasonable defaults are fine — note them inline.

---

## The design process

Follow this in order. It mirrors how an experienced API architect actually works, and the order matters: capabilities decide resources, resources decide operations, operations decide schemas — not the other way around.

### Step 1 — Capture intent

Restate the problem and the business capabilities back to the user in two or three bullets before you design anything. This catches misalignment early and gives the user a chance to correct framing. If a capability sounds like a UI screen ("Booking Page"), push back — it's probably not a capability, it's a feature. See `references/business-capability-mapping.md`.

### Step 2 — Map capabilities to resources

For each capability, identify the **stable nouns** it owns. Those nouns become resources (collections + items). A capability typically owns 1–5 resources; if it owns 20, it's actually several capabilities. Resource boundaries should match capability boundaries — if two capabilities both want to "own" the same resource, that's a domain split that needs a conversation, not a design decision you make silently.

Resources become the top-level structure of `paths` *and* of the `tags` hierarchy (use OAS 3.2's `parent` on tags). Capability becomes the parent tag (`kind: nav`); resources become child tags. This is what makes the spec navigable for both humans and codegen.

### Step 3 — Define operations and schemas

For each resource decide which operations it supports (collection ops on `/widgets`, item ops on `/widgets/{widgetId}`, sub-resource ops where genuinely owned by the parent). Conform to the style guide for verbs, status codes, pagination, and errors. Schemas follow from operations: define request/response bodies as components under `#/components/schemas` so they can be reused.

Use templates as starting points — copy from `assets/templates/` rather than handwriting boilerplate:
- `openapi-skeleton.yaml` — top-level scaffold with `info`, `servers`, `tags`, `components`.
- `resource-collection.yaml` — standard collection + item CRUD shape.
- `pagination.yaml` — cursor and offset patterns.
- `errors.yaml` — RFC 9457 `application/problem+json` responses.
- `security-schemes.yaml` — OAuth2 (including 3.2's device flow), JWT bearer, API key.
- `common-parameters.yaml` — reusable `If-Match`, `Idempotency-Key`, etc.

### Step 4 — Enrich for semantic context

This is the step that distinguishes a spec an AI agent can use successfully from one it can't. Apply the full checklist from `references/semantic-context-for-ai.md`. Highlights:

- Every operation has a `summary` (≤ 8 words) **and** a `description` (1–3 sentences explaining intent, side-effects, idempotency).
- Every `operationId` is `verbResource` style (`searchFlights`, `cancelBooking`) — not `op_42` or `getById`.
- Every parameter and schema property has a `description`. Schemas have a `title`.
- Use `examples` (3.2 supports `dataValue`/`serializedValue`) on request bodies and responses — at least one realistic, named example per status code.
- Use the controlled `x-` vocabulary in `assets/extension-vocabulary.yaml`: `x-business-capability`, `x-domain`, `x-use-case`, `x-idempotent`, `x-side-effects`, `x-ai-hints`. These are the hooks tool-using agents and MCP generators look for.
- Tag hierarchy reflects capabilities (use 3.2's `parent` and `kind` on the Tag Object).
- Add `externalDocs` on the root and on each tag pointing at the canonical capability/runbook documentation.

### Step 5 — Validate, lint, and output

Before handing the spec back:

1. Run `python scripts/validate.py <file>` — confirms it parses as valid OAS 3.2.
2. Run `python scripts/lint.py <file>` — checks the semantic-context rules (descriptions present, operationIds stylistic, examples on responses, tag hierarchy populated).
3. Fix anything the linter flags. Don't suppress without telling the user.
4. Save as `.yaml` (preferred) or `.json` to `/mnt/user-data/outputs/`.
5. Hand off via the `present_files` tool so the user can download.

---

## OpenAPI 3.2 — what's actually different (and what to use)

These are the 3.2 features worth using deliberately. None of them are required, but they remove the need for vendor extensions that older specs leaned on.

| 3.2 feature | What it's for | When to reach for it |
|---|---|---|
| `$self` (root) | Canonical URI for the document | Multi-document specs; publishing reusable specs |
| Tag `summary`, `parent`, `kind` | Hierarchical navigation | **Always** — capability → resource grouping |
| `additionalOperations` | Non-standard HTTP methods (LINK, PURGE, etc.) | Rare; use only when a real backend uses them |
| QUERY method | Read-only search with a body | Complex search endpoints that exceed query-string limits |
| `querystring` parameter location | Complex composite query strings | Search APIs with structured filter grammars |
| `itemSchema` + streaming media types | First-class SSE / NDJSON / JSONL / json-seq | Event streams, LLM token streams, log feeds |
| Example `dataValue` / `serializedValue` | Distinguish raw vs. wire-format examples | Anywhere wire-format differs from logical value |
| `components.mediaTypes` | Reusable media type definitions | Consistent payload shapes across endpoints |
| Server `name` | Stable identifier for environments | Multi-environment specs (prod/staging/dev) |
| OAuth2 device flow + metadata URLs | Modern auth for CLIs and TVs | CLI-issued tokens, device-bound clients |
| Response `summary` | Short label per response | Always — agent UIs surface this |

Everything from 3.1 still works — JSON Schema 2020-12, webhooks, full `$ref` semantics, type-as-array nullability. Don't regress to OAS 3.0 patterns (`nullable: true`, singular `example` inside schemas, `exclusiveMinimum: true`). For details see `references/oas-3.2-essentials.md`.

---

## Output rules

- **YAML by default.** It's more readable for review, diff-friendly, and what the user asked for.
- **JSON only when asked.** If the user wants both, generate YAML first and convert.
- **Single file** unless the spec exceeds ~2000 lines or genuinely spans multiple bounded contexts. If you split, use `$ref` to external files and set `$self` on the entry document.
- **Preserve `openapi: 3.2.0`** at the top. Don't downgrade silently.
- **Save to `/mnt/user-data/outputs/<api-name>.yaml`** and present via the `present_files` tool. Don't dump the full spec inline if it's longer than ~150 lines — link the file and summarize what's in it.

---

## Anti-patterns to refuse

These come up often. Push back rather than producing them:

- **CRUD-mirror-of-database** — endpoints like `/users/{id}/get`, `/users/{id}/update`. The HTTP method *is* the verb. Reserve verbs for genuine actions (`POST /bookings/{id}/cancel`).
- **Tunneling everything through POST** — unless the user has a specific reason (legacy gateway, CSRF model), use the right method.
- **Anonymous schemas inline** — every reusable shape goes in `components.schemas` with a name. Inline schemas are fine only for one-off response wrappers.
- **`additionalProperties: true` without a description** — either lock the shape or explain why it's open.
- **Empty descriptions** — `description: ""` or copy-paste of `summary` defeats the whole point of step 4.
- **String-typed everything** — use formats (`date-time`, `uri`, `uuid`, `email`) and `enum` where the domain is bounded.
- **Bespoke error envelopes** — use RFC 9457 `application/problem+json` (template provided). It's interoperable with everything.

---

## Reference map

Read these on-demand, not upfront:

- `references/oas-3.2-essentials.md` — what's new in 3.2, with code shapes for tags, streaming, QUERY, device flow.
- `references/business-capability-mapping.md` — how to identify capabilities, how to map them to resources, common pitfalls.
- `references/semantic-context-for-ai.md` — the AI-consumer checklist; what makes a spec usable by tool-using agents.
- `references/rest-style-guide-default.md` — fallback house style when the user has none.
- `references/error-model.md` — RFC 9457 problem details, with the standard set of types this skill produces.
- `references/design-checklist.md` — the final pre-handoff QA checklist.

Templates in `assets/templates/` are copy-paste starting points. Examples in `assets/examples/` are full reference specs. The `x-` vocabulary in `assets/extension-vocabulary.yaml` is the canonical list — don't invent new `x-` keys without adding them there first.

---

## Quick start (when the user just wants a small API)

For a one-or-two-resource API where the user has been clear, you can compress the process:

1. Copy `assets/templates/openapi-skeleton.yaml`.
2. Fill `info`, `servers`, and one tag per capability (with `parent`/`kind`).
3. Add one `paths` entry per resource using `assets/templates/resource-collection.yaml` as a model.
4. Reference `assets/templates/errors.yaml` and `assets/templates/security-schemes.yaml` from `components`.
5. Run validate + lint.
6. Save and present.

For anything bigger — multiple capabilities, more than five resources, streaming, or complex auth — run the full five-step process. Speed at the cost of capability-to-resource alignment is a false economy.
