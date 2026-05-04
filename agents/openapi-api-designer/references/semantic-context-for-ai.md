# Semantic context for AI consumers

The point of this reference is to make every OpenAPI document this skill produces usable by AI agents — MCP servers, tool-using LLMs, codegen pipelines — not just by humans reading SwaggerUI. AI agents read the spec to decide *whether to call*, *how to call*, and *how to interpret responses*. They have no implicit context. Every gap they encounter becomes a guess, and guesses cause incorrect calls.

The discipline is straightforward but not negotiable: anywhere a human would tolerate ambiguity ("they'll figure it out"), an agent won't. Spell it out.

## The four lenses

When an agent encounters the spec, it asks four questions. The spec needs to answer all four explicitly.

1. **Discovery** — *What can I do here?* Tags, summaries, operationIds, capabilities.
2. **Selection** — *Is this the right operation for the user's intent?* Descriptions, examples, `x-use-case`.
3. **Invocation** — *How do I construct a valid call?* Parameter descriptions, schemas, examples, idempotency hints.
4. **Interpretation** — *What does the response mean?* Response descriptions, response examples, error semantics, links.

Every operation must clear all four. The checklist below is grouped by lens.

## The checklist

### Discovery

- [ ] Root `info.title` is a noun phrase, not a slogan. ("Bookings API", not "Best-in-Class Booking Platform™".)
- [ ] Root `info.description` (≥ 2 sentences) explains the business capability, who consumes the API, and any auth-required-to-call note.
- [ ] `info.x-business-capability` is set.
- [ ] `info.contact` and `externalDocs` point at runbooks an agent can fetch.
- [ ] Tags form a hierarchy via 3.2's `parent` / `kind`. Capability tags at the top, resource tags as children.
- [ ] Every tag has a `summary` (short label) and `description` (1–2 sentences).
- [ ] Every operation declares `tags` (at least one) and a non-default `operationId`.

### Selection

- [ ] Every operation has a `summary` ≤ 8 words. Verb-first: "Search flights", "Cancel booking".
- [ ] Every operation has a `description` of 1–3 sentences explaining intent, side-effects, and idempotency.
- [ ] `operationId` is `verbResource[Qualifier]` style, camelCase, unique. `searchFlights`, `searchFlightsByOrigin`, `cancelBooking`. Not `op_42`, not `getById`, not `searchHandler`.
- [ ] `x-use-case` lists the 1–3 user intents this operation serves. Plain language.
- [ ] `x-side-effects` is `none` for safe operations and a short description for unsafe ones.
- [ ] `x-idempotent: true` on operations that are safe to retry; otherwise `false` with a one-line explanation.
- [ ] Deprecated operations carry `deprecated: true` *and* a `description` paragraph naming the replacement.

### Invocation

- [ ] Every parameter has a `description` (1–2 sentences). Empty string is not a description.
- [ ] Every parameter has either an `example` or `examples` block with realistic values. "abc123" is not realistic.
- [ ] Path parameters use named formats (`uuid`, `date-time`, `iso-currency`) where the domain is constrained.
- [ ] Query parameters with bounded domains use `enum` and explain each value where non-obvious.
- [ ] Request bodies reference a named schema in `components.schemas` — no anonymous inline shapes.
- [ ] Schemas have a `title` and `description`. Each property has a `description`. Each enum value has a doc comment in the description.
- [ ] At least one `examples` entry per request body, named meaningfully (`minimal`, `withOptions`, `bulk`).
- [ ] Operations that need idempotency keys document the `Idempotency-Key` header explicitly via `common-parameters`.
- [ ] Authentication requirements are explicit at the operation level via `security`, not relying solely on global defaults, *if* the operation differs from the global default.
- [ ] `x-ai-hints` carries any guidance an agent needs that the schema can't express — e.g. "always supply `currency` even when amount is 0", "this operation is rate-limited per user, not per app".

### Interpretation

- [ ] Every response has a `summary` (3.2) and a `description`.
- [ ] Every documented status code has at least one named `examples` entry.
- [ ] Error responses use `application/problem+json` and reference the standard `Problem` schema. Distinct error types have distinct `type` URI values listed in the description.
- [ ] Responses with collections include pagination metadata in the schema and document the cursor or page param.
- [ ] Operations that produce navigable next steps include `links` to the relevant follow-up operations.
- [ ] Streaming responses use `itemSchema` (3.2) — never raw `application/json` for an open stream.

## The controlled `x-` vocabulary

Use only the keys defined in `assets/extension-vocabulary.yaml`. New `x-` keys go in that file first, with a description, before they appear in a spec. This prevents vocabulary drift, which is what makes AI consumption hard across multiple specs.

Quick summary of the most-used keys:

- `x-business-capability` — capability id (kebab-case). On `info` and on every operation.
- `x-domain` — bounded context if different from capability.
- `x-use-case` — array of plain-language user intents this operation serves.
- `x-idempotent` — `true` / `false`.
- `x-side-effects` — `none` or a short string describing them.
- `x-ai-hints` — array of strings; agent-only guidance the schema can't express.
- `x-rate-limit` — object describing limits relevant to consumers.
- `x-owner` — team or service owner for routing/escalation.

Stay disciplined here. Three good `x-` keys are worth more than fifteen ad-hoc ones.

## Examples — what good looks like

### A weak operation (don't ship this)

```yaml
/bookings:
  post:
    summary: Create
    operationId: post1
    requestBody:
      content:
        application/json:
          schema:
            type: object
    responses:
      '200':
        description: OK
```

An agent given this has nothing. No verb-noun summary, no schema, no error model, no examples, no capability link, no idempotency signal.

### The same operation, semantically rich

```yaml
/bookings:
  post:
    summary: Create booking
    description: |
      Creates a confirmed booking for one or more passengers on one or more
      flight segments. The operation is **idempotent** when a unique
      `Idempotency-Key` is supplied — repeats with the same key return the
      original booking. Without the header, retries may create duplicates.
    operationId: createBooking
    tags: [bookings]
    x-business-capability: bookings
    x-use-case:
      - Confirm a held itinerary with payment
      - Book a flight directly without holding
    x-idempotent: true
    x-side-effects: |
      Reserves seat inventory, charges the supplied payment method,
      and emits a `booking.created` event.
    x-ai-hints:
      - Always include Idempotency-Key for retry safety.
      - If payment is declined, the booking is not created and no inventory is reserved.
    parameters:
      - $ref: '#/components/parameters/IdempotencyKey'
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/CreateBookingRequest'
          examples:
            roundTripOnePax:
              summary: One passenger, round-trip
              value:
                passengers: [{ givenName: Ada, familyName: Lovelace, type: ADULT }]
                segments:
                  - flightNumber: EX1234
                    departureDate: 2026-08-12
                  - flightNumber: EX1235
                    departureDate: 2026-08-19
                payment: { method: CARD, token: tok_test_abc }
    responses:
      '201':
        summary: Booking created
        description: |
          Booking confirmed. The `Location` header points at the canonical
          booking resource. Use that URL to retrieve, modify, or cancel.
        headers:
          Location:
            schema: { type: string, format: uri }
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Booking'
            examples:
              success:
                $ref: '#/components/examples/BookingSuccessExample'
        links:
          getBooking:
            operationId: getBooking
            parameters:
              bookingId: '$response.body#/id'
      '402':
        summary: Payment required
        description: |
          Payment was declined. Problem `type` is
          `https://errors.example.com/payment-declined`. The booking was
          not created and no inventory was reserved.
        content:
          application/problem+json:
            schema: { $ref: '#/components/schemas/Problem' }
            examples:
              declined: { $ref: '#/components/examples/PaymentDeclined' }
      '409':
        summary: Conflict
        description: |
          Either the held itinerary expired or an `Idempotency-Key` was reused
          with a different request body. See the problem `type`.
        content:
          application/problem+json:
            schema: { $ref: '#/components/schemas/Problem' }
```

This version answers all four agent questions explicitly. It costs more lines, but the cost is paid once and amortized across every consumer.

## Trade-offs to be honest about

- **Verbosity** — the rich version is 4–5× the line count of a thin one. That's fine if humans review it; for very large APIs consider keeping operations slim and pushing prose into capability-level external docs.
- **Drift** — `x-` extensions and prose go stale. Tie them to PR review or a lint rule (`scripts/lint.py` enforces presence, not freshness).
- **Over-promising** — don't write `x-idempotent: true` and a soothing description if the backend doesn't actually support it. Agents will rely on it. Match reality.

When in doubt, **the spec is a contract, not aspirational marketing**. Describe what the API does today.
