---
name: api-deprecation-handler
description: >
  Translate OpenAPI deprecation signals into actionable output. Use this skill whenever
  the user wants to add, interpret, or migrate API deprecation markers — including
  `deprecated: true` flags, `x-sunset` / `x-deprecation` extensions, Sunset and
  Deprecation HTTP response headers (RFC 8594 / RFC 9745 / RFC 8288), or lifecycle
  transition plans. Trigger on: "mark this operation deprecated", "add a sunset date",
  "what does this Sunset header mean", "how do I deprecate an API without breaking
  callers", "generate a deprecation notice", "migration guide for a deprecated endpoint".
  Do NOT use for: general OpenAPI design (use openapi-3.2-designer), linting an existing
  spec for other issues, or writing client code to handle 410 responses.
---

# API Deprecation Handler

Add, interpret, and communicate API deprecation signals across the full lifecycle:
spec authorship → gateway configuration → client migration notice.

The authoritative RFCs are:
- **RFC 9745** — `Deprecation` header field
- **RFC 8594** — `Sunset` header field
- **RFC 8288** — `Link` header relations (`rel=successor-version`, `rel=deprecation`)

Do not invent extension semantics beyond what these RFCs and OAS 3.2 define.
See `references/rfc-deprecation-cheatsheet.md` for quick field reference.

---

## When to use this skill

| User says | Use this skill |
|---|---|
| "Mark `searchFlights` as deprecated" | Yes |
| "Add a sunset date of 2026-03-01 to this operation" | Yes |
| "What does `Sunset: Sat, 01 Mar 2026 00:00:00 GMT` mean?" | Yes |
| "Generate a deprecation notice email for our consumers" | Yes |
| "How long should my deprecation window be?" | Yes |
| "Design a new bookings API from scratch" | No → use openapi-3.2-designer |
| "Lint my spec for missing descriptions" | No → point to Spectral |
| "Write a retry handler for 429s" | No → out of scope |

---

## Inputs to gather

Ask once if not provided. Default values are noted.

| Input | Required | Default |
|---|---|---|
| The operation(s) to deprecate (operationId or path+method) | Yes | — |
| Deprecation date (when deprecated was/will be set) | Recommended | today |
| Sunset date (when the operation will be removed) | Recommended | deprecation + 6 months |
| Replacement operation or URL | Recommended | null |
| Consumer audience (internal teams / external partners / public) | Recommended | assume all three |
| Output needed (spec patch, header config, notice, or all) | Yes | all |

If the user provides an operation without a sunset date, **always ask** — do not silently
default. A missing sunset is the most common cause of indefinite deprecation limbo.

---

## Steps

### Step 1 — Parse the target operation

Identify the operation from the user's spec or description. Extract:
- `operationId`
- `summary`
- Current request/response shape (to inform migration notice)
- Any existing `deprecated`, `x-sunset`, or `x-deprecation` fields

If the spec is not provided, ask for it. Do not proceed on a partial or assumed shape.

### Step 2 — Compute lifecycle dates

```
deprecated_date  = user-provided | today
sunset_date      = user-provided | deprecated_date + 6 months
deprecation_window = sunset_date - deprecated_date  (in days)
```

Flag if `deprecation_window < 30 days` — that is shorter than any reasonable migration window.
Flag if `deprecation_window > 730 days` — ask whether the long window is intentional.

Audience-adjusted minimums (from `references/deprecation-windows.md`):
- Internal consumers only: 30 days minimum
- External partners: 90 days minimum
- Public / open: 180 days minimum

### Step 3 — Generate spec patch

Produce a minimal YAML patch for the target operation. Apply these fields:

```yaml
# On the operation object
deprecated: true
x-deprecation:
  date: <deprecated_date>          # ISO-8601
  sunset: <sunset_date>            # ISO-8601
  replacement: <operationId | URL | null>
  migration-guide: <URL | null>
  reason: <one sentence | null>
```

If OAS 3.2 `info.x-lifecycle` is present on the root document, also update it.

Do not patch any other part of the spec. Output the patch as a fenced YAML block
the user can apply directly. See `references/spec-patch-examples.md` for worked examples.

### Step 4 — Generate gateway / middleware header config

Produce config snippets for the two most common gateways unless the user specifies one.
See `references/gateway-configs.md` for full templates.

**AWS API Gateway (response headers mapping)**:
```yaml
responseParameters:
  method.response.header.Deprecation: "'<deprecated_date_rfc7231>'"
  method.response.header.Sunset: "'<sunset_date_rfc7231>'"
  method.response.header.Link: "'<migration_url>; rel=\"successor-version\"'"
```

**Kong (response-transformer plugin)**:
```yaml
plugins:
  - name: response-transformer
    config:
      add:
        headers:
          - "Deprecation: <deprecated_date_rfc7231>"
          - "Sunset: <sunset_date_rfc7231>"
          - "Link: <migration_url>; rel=\"successor-version\""
```

Date format note: RFC 9745 requires `Deprecation` as an HTTP-date or `@<unix-timestamp>`.
RFC 8594 requires `Sunset` as HTTP-date. Always emit both formats in the output so the user
can pick. See `references/rfc-deprecation-cheatsheet.md` §3.

### Step 5 — Generate consumer notice

Draft a deprecation notice sized for the stated audience. Structure:

```
Subject: [API Deprecation] <operationId> — Sunset <sunset_date>

What's changing:
  <operationId> (<method> <path>) is deprecated as of <deprecated_date>.
  It will be removed on <sunset_date>.

Why:
  <reason | "See migration guide for details.">

What you should do:
  Migrate to <replacement_operationId | URL> before <sunset_date>.
  Migration guide: <URL | "Contact the API team for assistance.">

Impact if you do nothing:
  Requests to this endpoint will return 410 Gone after <sunset_date>.

Questions?
  <contact placeholder>
```

Adjust tone: internal notices can be terse; external/public notices should be formal and
include a grace period acknowledgement. See `references/notice-templates.md` for full variants.

---

## Output format

Default output is **all three artefacts** unless the user asks for a specific one:

1. **Spec patch** — fenced YAML block, ready to apply
2. **Gateway config** — fenced YAML block(s), labelled by gateway
3. **Consumer notice** — fenced Markdown block

Precede each block with a one-line summary of what it does and where it goes.
If the user provides a file, offer to write the patch to disk via the file tool.

---

## Constraints

- **Never infer sunset from git blame or commit dates.** Only use dates the user provides or
  explicitly confirms.
- **Never remove operations from a spec.** Deprecation adds markers; removal is a separate
  breaking change that requires its own process.
- **Never downgrade `deprecated: true` back to `false`** unless the user explicitly says the
  deprecation is being reversed — and if so, also remove all `x-deprecation` fields.
- **Do not produce `410 Gone` response code snippets** as part of this skill. That is a
  gateway enforcement concern, not a spec annotation concern.

---

## Reference map

Read on demand, not upfront:

- `references/rfc-deprecation-cheatsheet.md` — field-by-field quick reference for RFC 9745,
  RFC 8594, RFC 8288 `Link` relations.
- `references/deprecation-windows.md` — audience-adjusted minimum windows and rationale.
- `references/gateway-configs.md` — full header-injection templates for AWS API Gateway,
  Kong, Apigee, and NGINX.
- `references/spec-patch-examples.md` — worked before/after YAML patches for common cases.
- `references/notice-templates.md` — full notice variants for internal, partner, and public
  audiences; includes changelog and status-page formats.
