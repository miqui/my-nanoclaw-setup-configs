# OpenAPI 3.2 essentials

This is the working subset of OAS 3.2 you'll reach for most often. The spec is the source of truth — when something here is unclear, read **https://spec.openapis.org/oas/v3.2.0.html** directly.

3.2 is a feature release on top of 3.1. Every valid 3.1 document is (almost) a valid 3.2 document. The interesting changes are additive and worth using deliberately.

## Table of contents

1. The version line and `$self`
2. Tag Object — hierarchies with `parent`, `kind`, `summary`
3. `additionalOperations` and the QUERY method
4. `querystring` parameter location
5. Streaming with `itemSchema` and sequential media types
6. Example `dataValue` / `serializedValue`
7. `components.mediaTypes` — reusable payload shapes
8. Server `name`
9. OAuth 2.0 device flow, metadata URLs, deprecated flag
10. Response `summary`
11. JSON Schema 2020-12 reminders (carried from 3.1)

---

## 1. Version and `$self`

```yaml
openapi: 3.2.0
$self: https://specs.example.com/orders-api/v1
info:
  title: Orders API
  version: 1.0.0
```

`$self` is a top-level URI identifying *this* document. It's optional but useful when:

- The spec is published at a canonical URL distinct from the runtime API.
- You're splitting into multiple documents and want stable identifiers.
- You want references to resolve against a known base instead of the retrieval URL.

For single-file specs served alongside the API, omit it.

## 2. Tag Object — hierarchies

The Tag Object now carries `summary`, `parent`, and `kind` in addition to `name` and `description`. This replaces the vendor-extension `x-tagGroups` patterns that older specs used.

```yaml
tags:
  - name: passenger-experience
    summary: Passenger Experience
    description: Capabilities that touch the passenger journey from search to arrival.
    kind: nav
  - name: bookings
    summary: Bookings
    description: Create, view, and modify bookings.
    parent: passenger-experience
    kind: nav
  - name: check-in
    summary: Check-in
    description: Online and kiosk check-in flows.
    parent: passenger-experience
    kind: nav
  - name: bookings-collection
    summary: Bookings — collection
    parent: bookings
    kind: nav
```

Recommended rule: capability tags get `kind: nav` and no `parent`. Resource tags use `parent: <capability>`. Cross-cutting tags (e.g. `audit`, `admin`) use `kind: badge`.

`kind` values commonly seen in tooling: `nav` (appears in navigation), `badge` (decorative label), `audience` (consumer-segment hint). Tools that don't recognize a `kind` value should fall back to flat tag display, so it's safe to use.

## 3. `additionalOperations` and the QUERY method

OAS 3.2 acknowledges HTTP methods beyond the standard set. There are two paths:

**QUERY method** — formally supported as a first-class operation. Use for read-only searches that need a body (filter grammars, vector queries):

```yaml
paths:
  /flights/search:
    query:
      operationId: searchFlights
      summary: Search flights
      description: Read-only search with a structured filter body.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FlightSearchRequest'
      responses:
        '200':
          description: Search results.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FlightSearchResponse'
```

**`additionalOperations`** — for genuinely non-standard methods like `LINK`, `UNLINK`, `PURGE`. Avoid unless your backend really uses them.

```yaml
paths:
  /caches/{key}:
    additionalOperations:
      PURGE:
        operationId: purgeCacheKey
        summary: Purge a cache key
        responses:
          '204':
            description: Purged.
```

If you're tempted to invent a custom verb, first try a sub-resource `POST /resources/{id}/actions/<verb>`. It's better understood by every consumer.

## 4. `querystring` parameter location

For complex query strings — e.g. RHS-bracket filters, RSQL, or nested grammars — the new `in: querystring` location lets you describe the full thing as a single parameter rather than enumerating every key.

```yaml
parameters:
  - name: filter
    in: querystring
    description: |
      RSQL filter expression. See the filter grammar guide.
      Example: `status==active;createdAt=ge=2026-01-01`.
    schema:
      type: string
    examples:
      simple:
        value: 'status==active'
      compound:
        value: 'status==active;createdAt=ge=2026-01-01'
```

Use sparingly. Standard `in: query` parameters are still right for typical filtering.

## 5. Streaming — `itemSchema` and sequential media types

Streams are now first-class. Recognized sequential media types include `text/event-stream`, `application/jsonl`, `application/x-ndjson`, and `application/json-seq`. Use `itemSchema` to describe each element of the stream.

```yaml
paths:
  /events:
    get:
      operationId: streamEvents
      summary: Stream events
      description: Server-sent event stream of domain events.
      responses:
        '200':
          description: Stream open.
          content:
            text/event-stream:
              itemSchema:
                $ref: '#/components/schemas/Event'
```

For LLM token streams, agent step-streams, or log feeds, `text/event-stream` with an `itemSchema` is the right shape.

## 6. Example `dataValue` and `serializedValue`

The Example Object adds `dataValue` (the logical value) and `serializedValue` (the on-the-wire representation). Use this when wire format differs from the logical model — `multipart/form-data`, custom encodings, base64-encoded binary.

```yaml
components:
  examples:
    avatarUpload:
      summary: Avatar upload
      dataValue:
        userId: '123'
        avatar: '<binary PNG>'
      serializedValue: |
        --boundary
        Content-Disposition: form-data; name="userId"

        123
        --boundary
        Content-Disposition: form-data; name="avatar"; filename="me.png"
        Content-Type: image/png

        <binary>
        --boundary--
```

For plain JSON request/response examples, the older `value` keyword still works.

## 7. `components.mediaTypes` — reusable payload shapes

Define a media type once with its schema, examples, and encoding, then reference it from multiple operations.

```yaml
components:
  mediaTypes:
    json-problem:
      schema:
        $ref: '#/components/schemas/Problem'
      examples:
        notFound:
          $ref: '#/components/examples/NotFoundProblem'
paths:
  /widgets/{id}:
    get:
      responses:
        '404':
          description: Not found.
          content:
            application/problem+json:
              $ref: '#/components/mediaTypes/json-problem'
```

Pairs especially well with the RFC 9457 error template.

## 8. Server `name`

Stable identifiers for environments — useful for tooling that needs to pick an environment by id rather than positional index.

```yaml
servers:
  - name: production
    url: https://api.example.com/v1
    description: Production.
  - name: staging
    url: https://staging.api.example.com/v1
    description: Staging mirror.
```

## 9. OAuth 2.0 — device flow, metadata URLs, deprecated flag

3.2 adds the OAuth 2.0 device authorization grant and lets you point at server metadata (RFC 8414) instead of duplicating endpoint URLs. Older flows can be marked `deprecated: true`.

```yaml
components:
  securitySchemes:
    oauthDevice:
      type: oauth2
      description: OAuth 2.0 device authorization grant.
      flows:
        deviceAuthorization:
          deviceAuthorizationUrl: https://auth.example.com/device_authorization
          tokenUrl: https://auth.example.com/token
          scopes:
            read:bookings: Read bookings
            write:bookings: Modify bookings
    oauthAuthCode:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            read:bookings: Read bookings
    oauthLegacyImplicit:
      type: oauth2
      deprecated: true
      flows:
        implicit:
          authorizationUrl: https://auth.example.com/authorize
          scopes:
            read:bookings: Read bookings
```

## 10. Response `summary`

A short label that complements `description`. Surfaces in agent-facing UIs.

```yaml
responses:
  '200':
    summary: Booking created
    description: |
      The booking was created. The response Location header points at the
      canonical booking resource.
    headers:
      Location:
        schema:
          type: string
          format: uri
```

## 11. JSON Schema 2020-12 reminders

These came in with 3.1 and still apply:

- Use type-as-array for null: `type: [string, "null"]` — not `nullable: true`.
- Use `examples` (array) inside Schema Objects, not singular `example`.
- `exclusiveMinimum` / `exclusiveMaximum` take a number, not a boolean.
- `contentEncoding` and `contentMediaType` describe binary/encoded payloads.
- `$ref` is fully JSON-Schema-compliant — siblings are now allowed where the schema dialect permits.

If you're migrating from 3.0, fix all four before bumping the version.
