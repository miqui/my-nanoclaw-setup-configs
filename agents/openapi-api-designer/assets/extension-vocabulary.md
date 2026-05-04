# Controlled x- extension vocabulary
#
# These are the only x- extensions this skill emits. New keys go here first,
# with a description and an applies-to list, before they appear in any spec.
# Vocabulary drift is what makes AI consumption hard across multiple specs;
# stay disciplined.

vocabulary:

  x-business-capability:
    type: string
    pattern: '^[a-z][a-z0-9-]*$'
    description: |
      Business capability identifier (kebab-case). The capability this
      element belongs to. Anchors capability-level governance, metrics,
      ownership, and access control.
    applies-to: [info, operation, schema, tag]
    required: true on info, true on every operation
    example: bookings

  x-domain:
    type: string
    pattern: '^[a-z][a-z0-9-]*$'
    description: |
      Bounded context this element belongs to, when distinct from the
      capability. Most APIs don't need this; use only when one capability
      spans multiple bounded contexts.
    applies-to: [info, operation, schema]
    example: passenger-experience

  x-use-case:
    type: array
    items: { type: string }
    description: |
      Plain-language user intents this operation serves. One bullet per
      distinct intent. Used by AI agents during operation selection.
    applies-to: [operation]
    example:
      - Book a flight directly with a card
      - Confirm a held itinerary

  x-idempotent:
    type: boolean
    description: |
      Whether the operation is safe to retry with the same input and produce
      the same effect. Required on every operation. Operations supporting
      idempotency via header should set true *and* document the
      Idempotency-Key parameter.
    applies-to: [operation]
    required: true
    example: true

  x-side-effects:
    type: string
    description: |
      Short description of side-effects. Use the literal string `none` for
      safe operations (most GETs). For unsafe operations, name the side
      effects in plain language — what gets persisted, what events are
      emitted, what external systems are called.
    applies-to: [operation]
    required: true
    example: |
      Reserves seat inventory and emits a `booking.created` event.

  x-ai-hints:
    type: array
    items: { type: string }
    description: |
      Guidance an agent needs that the schema cannot express. Use sparingly;
      schema-expressible constraints belong in the schema. Good targets:
      retry semantics on specific error types, cross-field invariants,
      rate-limit dimensions, common pitfalls.
    applies-to: [operation, schema]
    example:
      - Always include Idempotency-Key for retry safety.
      - On 402 with type payment-declined, do not retry without a new payment method.

  x-rate-limit:
    type: object
    properties:
      dimension: { type: string, description: 'Per-key dimension (user, app, ip).' }
      requestsPerMinute: { type: integer }
      burst: { type: integer }
    description: |
      Rate limit hints surfaced to consumers. Not a contract — actual limits
      may differ — but useful for client-side throttling.
    applies-to: [operation, info]
    example:
      dimension: user
      requestsPerMinute: 60
      burst: 10

  x-owner:
    type: string
    description: |
      Team or service owner identifier. Used for routing, escalation, and
      ownership reporting.
    applies-to: [info, operation]
    example: bookings-platform-team

  x-stability:
    type: string
    enum: [experimental, beta, stable, deprecated]
    description: |
      Stability promise for this element. `experimental` may change without
      notice; `beta` may have breaking changes with one minor version of
      warning; `stable` follows full breaking-change policy; `deprecated`
      is paired with `deprecated: true` and a description naming the
      replacement.
    applies-to: [operation, schema]
    example: stable

  x-pii:
    type: object
    properties:
      categories:
        type: array
        items:
          type: string
          enum: [identity, contact, location, financial, health, biometric, government-id]
      retention: { type: string, description: 'Retention window, e.g. P30D.' }
      classification: { type: string, enum: [public, internal, confidential, restricted] }
    description: |
      Data sensitivity declaration. Required on schemas that carry PII so
      data-handling tooling, agents, and reviewers can enforce minimization
      and redaction policies.
    applies-to: [schema, parameter]
    example:
      categories: [identity, contact]
      retention: P7Y
      classification: confidential

  x-stream:
    type: object
    properties:
      kind: { type: string, enum: [sse, ndjson, jsonl, json-seq] }
      eventTypes: { type: array, items: { type: string } }
    description: |
      Streaming-response metadata. Complements OAS 3.2's itemSchema by
      naming the event-type vocabulary an agent should expect.
    applies-to: [response]
    example:
      kind: sse
      eventTypes: [search.partial, search.complete, search.error]

  x-mcp:
    type: object
    properties:
      exposeAsTool: { type: boolean }
      toolName: { type: string }
      toolDescription: { type: string }
    description: |
      MCP (Model Context Protocol) hints for tools that auto-generate MCP
      servers from OpenAPI specs. Lets an API author declare which
      operations should be surfaced as tools and how they should be named.
    applies-to: [operation]
    example:
      exposeAsTool: true
      toolName: search_flights
      toolDescription: Search available flights matching origin, destination, and dates.

# Forbidden keys — these often appear in older specs but produce vocabulary
# drift. Don't emit them; replace with the keys above.
forbidden:
  - x-google-backend         # vendor-specific, doesn't belong in source spec
  - x-amazon-apigateway-*    # ditto
  - x-summary                # use response.summary (3.2)
  - x-tagGroups              # use Tag.parent / Tag.kind (3.2)
  - x-internal               # use x-stability or split spec
