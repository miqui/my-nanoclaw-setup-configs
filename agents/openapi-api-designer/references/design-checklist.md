# Final design checklist

Run through this before handing the spec back to the user. The first half is structural (will it parse, lint, and generate?); the second half is semantic (will a human or an agent actually be able to use it?). Do both — passing the first without the second produces specs that lint clean but are useless to consumers.

## Structural

- [ ] `openapi: 3.2.0` at the top.
- [ ] `info.title`, `info.version`, `info.description` are all present and non-empty.
- [ ] At least one `servers` entry, each with `name`, `url`, `description`.
- [ ] No anonymous schemas in request/response bodies — every shape lives in `components.schemas` with a `title`.
- [ ] No `nullable: true` (3.0 pattern). Use `type: [string, "null"]`.
- [ ] No singular `example:` inside Schema Objects. Use `examples:` (array).
- [ ] No `exclusiveMinimum: true` (3.0 pattern). Use `exclusiveMinimum: <number>`.
- [ ] Every `$ref` resolves; run `python scripts/validate.py`.
- [ ] No duplicate `operationId`s.
- [ ] Every operation has at least one response.
- [ ] Every error response uses `application/problem+json` referencing `#/components/schemas/Problem`.
- [ ] Path templating is consistent: `{camelCaseName}`, types declared in parameters.

## Semantic — discovery

- [ ] Tags are hierarchical. Every capability has a parent tag with `kind: nav`. Every resource tag has `parent` set.
- [ ] Every tag has both `summary` and `description`.
- [ ] Every operation declares at least one tag — and the tag exists in the top-level `tags` array.
- [ ] `info.x-business-capability` is set.
- [ ] `info.contact` and root `externalDocs` are present.

## Semantic — selection

- [ ] Every operation has a `summary` ≤ 8 words, verb-first.
- [ ] Every operation has a `description` of 1–3 sentences.
- [ ] Every `operationId` follows `verbResource[Qualifier]`, camelCase, unique.
- [ ] `x-business-capability` set on every operation.
- [ ] `x-use-case` (array of strings) on every operation.
- [ ] `x-idempotent` (boolean) on every operation.
- [ ] `x-side-effects` on every non-safe operation.
- [ ] Deprecated operations carry both `deprecated: true` and a description naming the replacement.

## Semantic — invocation

- [ ] Every parameter has a non-empty `description`.
- [ ] Every parameter has either `example` or `examples` with realistic values.
- [ ] Path parameters use `format: uuid` / `format: date-time` / similar where the domain is constrained.
- [ ] Bounded query parameters use `enum`.
- [ ] Every request body has at least one named example in `examples` (`minimal`, `withOptions`, etc.).
- [ ] Mutating operations that should be retry-safe document the `Idempotency-Key` header (`$ref: '#/components/parameters/IdempotencyKey'`).
- [ ] Operations that need optimistic locking document `If-Match`.
- [ ] Schemas have `title` + `description`. Every property has a `description`. Enum values explained inline.

## Semantic — interpretation

- [ ] Every response has `summary` (3.2) and `description`.
- [ ] Every documented status code has at least one named example.
- [ ] Standard error responses (`401`, `403`, `404`, `409`, `422`, `429`, `500`) reference `components.responses` rather than redefining inline.
- [ ] Collections paginate consistently — same parameter names and wrapper shape across the whole spec.
- [ ] Operations producing follow-up state include `links` to the next operations.
- [ ] Streaming responses use `itemSchema` (3.2) — `text/event-stream`, `application/jsonl`, `application/x-ndjson`, or `application/json-seq` as appropriate.

## Security

- [ ] At least one entry in `components.securitySchemes`.
- [ ] Global `security` set, with operation-level overrides only where they actually differ.
- [ ] OAuth2 flows declare each `scope` with a description. Names are namespaced (`read:bookings`).
- [ ] Public endpoints (no auth required) explicitly set `security: []` so the difference is visible.

## Output

- [ ] File saved to `/mnt/user-data/outputs/<api-name>.yaml` (or `.json` if asked).
- [ ] `python scripts/validate.py <file>` passes.
- [ ] `python scripts/lint.py <file>` passes — or any failures are surfaced to the user with rationale.
- [ ] Response message names assumptions and points the user at the spec via `present_files`.

## Handoff message template

```
Here's the OpenAPI 3.2 spec for <API name>.

What I built around:
- Capabilities: <list>
- Resources: <list>
- Style guide: <user's, or "the default skill style guide — happy to swap in yours">

Highlights:
- <N> operations across <M> resources
- Auth: <scheme(s)>
- Pagination: <cursor / offset>
- Streaming: <yes/no — what>

Anything I assumed that you want to override?
```

Keep the handoff message short. The spec carries the detail; the chat is for orientation and decisions.
