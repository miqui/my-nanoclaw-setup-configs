# Default REST style guide

When the user hasn't supplied a house style guide, use this. **Tell them you're using it** — surface the choice so they can override anywhere it conflicts with their conventions. This guide is intentionally opinionated; if you don't have a reason to differ, follow it.

## Versioning

- Major version in the URL path: `/v1/...`. Breaking changes require a new major version.
- Minor and patch versions are signalled in `info.version` only — they never appear in the URL.
- Deprecated operations carry `deprecated: true`, the `Deprecation` header (RFC 9745), and the `Sunset` header (RFC 8594) when the removal date is known.

```yaml
servers:
  - name: production
    url: https://api.example.com/v1
```

## Naming

- **Resources** are plural nouns in kebab-case: `/bookings`, `/loyalty-accounts`, `/baggage-events`.
- **Path parameters** are camelCase: `/bookings/{bookingId}`. Always typed; prefer `format: uuid` or a domain-specific format.
- **Query parameters** are camelCase: `pageSize`, `cursor`, `filter`.
- **Header names** follow HTTP conventions (`Idempotency-Key`, `If-Match`, `Last-Modified`).
- **Enum values** are SCREAMING_SNAKE_CASE for stable codes (`CONFIRMED`, `CANCELLED`); kebab-case if they appear in URLs.
- **JSON properties** are camelCase. Don't mix snake_case in.

## HTTP methods

Method | Used for | Idempotent | Safe
---|---|---|---
GET | Read | yes | yes
POST | Create, or invoke a non-idempotent action | no | no
PUT | Replace the entire resource | yes | no
PATCH | Partial update; use `application/merge-patch+json` (RFC 7396) or `application/json-patch+json` (RFC 6902) | depends | no
DELETE | Remove | yes | no
QUERY | Read-only search with a body (OAS 3.2) | yes | yes

For genuine actions on a resource, use `POST /resource/{id}/actions/<verb>` (e.g. `POST /bookings/{id}/actions/cancel`). Never put verbs in resource names (`/cancelBooking`).

## Status codes

Use the standard meanings — don't get creative.

Code | Meaning
---|---
200 OK | Read or replace succeeded
201 Created | Resource created; include `Location` header
202 Accepted | Async accepted; include a status URL
204 No Content | Mutation succeeded with no body
301 / 308 | Permanent redirect (308 preserves method)
303 See Other | After-action redirect to a result
400 Bad Request | Validation failed
401 Unauthorized | No / invalid credentials
403 Forbidden | Authenticated but not authorized
404 Not Found | Resource does not exist (or is hidden from this caller)
409 Conflict | Optimistic-lock failure, idempotency-key reuse, state machine conflict
410 Gone | Resource permanently removed
412 Precondition Failed | `If-Match` / `If-None-Match` failure
422 Unprocessable Entity | Semantic validation failure (request was well-formed but invalid)
428 Precondition Required | Caller should send `If-Match` / `Idempotency-Key`
429 Too Many Requests | Rate limited; include `Retry-After`
500 Internal Server Error | Unhandled server error
503 Service Unavailable | Temporary outage; include `Retry-After`

## Pagination

Default to **cursor pagination** for any collection that may grow unbounded. Offset pagination is acceptable for small bounded sets.

```yaml
parameters:
  - name: pageSize
    in: query
    schema: { type: integer, minimum: 1, maximum: 100, default: 25 }
  - name: cursor
    in: query
    description: Opaque cursor from a previous response's `nextCursor`.
    schema: { type: string }
```

Response wrapper:

```yaml
type: object
required: [data, page]
properties:
  data:
    type: array
    items: { $ref: '#/components/schemas/Booking' }
  page:
    type: object
    properties:
      nextCursor: { type: string, nullable: true }
      pageSize: { type: integer }
```

## Filtering and sorting

- Simple equality filters: `?status=CONFIRMED&channel=WEB`.
- Multiple values: repeat the param (`?status=CONFIRMED&status=ON_HOLD`) or comma-separate (`?status=CONFIRMED,ON_HOLD`) — pick one and stick to it across the API.
- Sort: `?sort=createdAt,-totalAmount` (prefix `-` for descending).
- For complex filtering, use OAS 3.2's `in: querystring` parameter with a documented grammar (RSQL recommended).

## Errors

Return `application/problem+json` (RFC 9457) — never bespoke envelopes. See `error-model.md`.

```json
{
  "type": "https://errors.example.com/payment-declined",
  "title": "Payment declined",
  "status": 402,
  "detail": "Card was declined by the issuer.",
  "instance": "/bookings/abc123/payments/xyz",
  "code": "payment.declined",
  "errors": [
    { "field": "payment.cvv", "code": "invalid", "message": "CVV check failed" }
  ]
}
```

## Idempotency

Mutating operations that create resources or trigger external side-effects accept an `Idempotency-Key` header. Server stores the key for at least 24 hours and replays the same response.

```yaml
- name: Idempotency-Key
  in: header
  required: false
  description: |
    Client-generated key to make this request idempotent. Same key + same body
    returns the same response; same key + different body returns 409.
  schema: { type: string, format: uuid }
```

## Concurrency control

For updates on resources that can change between reads:

- Server returns `ETag` on read.
- Client sends `If-Match: <etag>` on update.
- Mismatch returns 412.

## Caching

- `Cache-Control` on all GETs.
- `ETag` for validators on resources.
- `Last-Modified` when collection ordering is time-based.

## Authentication and authorization

- Default to OAuth 2.0 with the authorization-code flow for end-user APIs.
- Add the device-authorization flow (OAS 3.2) for CLI / IoT clients.
- Service-to-service uses client-credentials with scoped tokens.
- Scopes are namespaced: `read:bookings`, `write:bookings`, `admin:bookings`. Document each scope at `securityScheme.scopes`.

## Webhooks

Use the OpenAPI `webhooks` section. Webhook events are first-class operations from the server's perspective. Document delivery semantics (at-least-once vs at-most-once), retry behaviour, and signature verification.

## Date and time

- Always ISO 8601 / RFC 3339 in UTC: `2026-05-04T13:42:00Z`.
- `format: date-time` for instants.
- `format: date` for calendar dates.
- Don't pass durations as strings of seconds; use ISO 8601 duration (`P3D`, `PT15M`).

## Money

```yaml
Money:
  type: object
  required: [amount, currency]
  properties:
    amount:
      type: string
      pattern: '^-?[0-9]+(\.[0-9]+)?$'
      description: Decimal string. Avoid floats — they lose precision.
    currency:
      type: string
      pattern: '^[A-Z]{3}$'
      description: ISO 4217 currency code.
```

## Identifiers

- External-facing IDs: UUIDv4 or ULID. Never database primary keys.
- IDs are strings, never integers, even when they look numeric.
- Resource URLs are stable; renaming a resource type is a breaking change.

## Localization

- `Accept-Language` request header drives response language for human-readable text.
- Server response includes `Content-Language`.
- Money amounts are *not* localized at the API layer. Format on the client.

## Defaults this skill applies

When you can't ask the user, use these:

- API path prefix: `/v1`.
- Pagination: cursor, default `pageSize` 25, max 100.
- Errors: `application/problem+json`.
- Auth: OAuth 2.0 authorization-code flow + device flow.
- Idempotency: header-based with 24-hour window.
- Date format: RFC 3339 UTC.

State the assumptions in the response so the user can override.
