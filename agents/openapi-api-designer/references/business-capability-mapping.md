# Business capability mapping

Capabilities are the most important input to API design. Done right, they decide your resource model, your tag hierarchy, your team boundaries, and your versioning strategy *for years*. Done wrong, you ship endpoints that mirror today's UI and have to reshape the whole surface in 18 months.

This reference covers what a capability is, how to recognize one, how to map capabilities to OpenAPI structure, and the failure modes to watch for.

## What a business capability is

A capability is **a stable thing the business does**. Stable meaning: it survives reorgs, system replacements, and product pivots. It's defined by *what value is delivered*, not by *how* or *who*.

Tests for whether something is a capability:

- **Stability**: Would this still exist if the company switched its tech stack tomorrow? If yes, capability candidate.
- **Outcome focus**: Can you describe it as a noun phrase about a business outcome ("Baggage Tracking", "Loyalty Accrual")? Or only as a process ("Process the bag through the system")? Outcomes are capabilities; processes are workflows that *use* capabilities.
- **Ownership**: Could a single team own this end-to-end? If three teams have to coordinate every change, it's probably actually two or three capabilities.
- **Vocabulary**: Does the business already have a name for it? Capabilities tend to have names that exist before software does.

## What a capability isn't

These come up constantly. Push back when you see them:

- **Screens / UIs** — "Booking Page", "Search Results View". These consume capabilities, they aren't capabilities.
- **Departments** — "Marketing", "Operations". Too coarse; a department spans many capabilities.
- **Integrations** — "Stripe Connector", "Salesforce Sync". These are implementations of payment or CRM capabilities.
- **Technical layers** — "Database", "Cache", "Queue". Plumbing, not capability.
- **Projects** — "Q3 Migration". Time-bound work, not durable capability.

When the user lists "Booking Page" as a capability, the polite move is "I think Booking Page is a UI surface that uses the Booking, Pricing, and Inventory capabilities — does that match how your team thinks about it?"

## Mapping capabilities to OpenAPI structure

Once capabilities are nailed, the OpenAPI structure flows out of them.

### Capability → tag hierarchy

Each top-level capability becomes a parent tag with `kind: nav`. Each resource it owns becomes a child tag with `parent: <capability>`.

```yaml
tags:
  - name: bookings-capability
    summary: Bookings
    description: Create, view, and modify bookings.
    kind: nav
  - name: bookings
    summary: Booking resource
    parent: bookings-capability
    kind: nav
  - name: booking-events
    summary: Booking events
    parent: bookings-capability
    kind: nav
```

This gives navigation structure that mirrors the business — readers find what they need by capability name, not by alphabetical paths.

### Capability → resource boundaries

Each capability owns 1–5 resources. Resources are the **stable nouns** the capability is responsible for.

For "Bookings", the nouns might be: `Booking`, `BookingEvent`, `BookingHold`. That's three resources, all under one capability.

For "Passenger Identity", the nouns might be: `Passenger`, `IdentityDocument`, `BiometricEnrollment`. Different capability, different resources.

If you can't decide which capability owns a resource, it usually means:

- The resource doesn't exist yet — you're conflating two things. Split it.
- The capabilities aren't well-defined. Go back and clarify.
- It's a genuinely shared resource — define it once and let multiple capabilities reference it via `$ref` or links. Don't duplicate.

### Capability → `x-business-capability` extension

Every operation should declare its capability via `x-business-capability`. This is what enables capability-level governance, capability-level metrics, and capability-level access control. See `assets/extension-vocabulary.yaml`.

```yaml
paths:
  /bookings:
    post:
      operationId: createBooking
      x-business-capability: bookings
      tags: [bookings]
```

### Capability → `info` and `externalDocs`

The top-level `info.description` and `externalDocs` should orient the reader: which capability does this API serve, what business outcome does it deliver, and where do they read more.

```yaml
info:
  title: Bookings API
  version: 1.0.0
  description: |
    HTTP interface to the **Bookings** capability — creating, retrieving,
    and modifying bookings across all channels (web, mobile, agent, kiosk).
  x-business-capability: bookings
externalDocs:
  url: https://docs.example.com/capabilities/bookings
  description: Bookings capability runbook and domain model.
```

## Common failure modes

### "Everything is one big capability"

If the user gives you "Customer 360" or "Platform" as the only capability, the API will end up as a kitchen sink. Push for sub-capabilities. A capability should fit on one slide; "everything we do for customers" doesn't.

### "Every endpoint is its own capability"

The opposite mistake. If `createBooking` and `cancelBooking` are different capabilities, the user is conflating capability with operation. Roll up.

### Capabilities defined by team

"Team Alpha owns this, Team Beta owns that." Tempting, because it matches reality today. But teams reorg; capabilities don't. Capture both — capability is durable, team is captured in `x-owner` for routing.

### Resources that span capabilities

A `Customer` might be touched by Sales, Support, and Billing. The right move is **one** Customer resource owned by one capability (probably "Customer Identity"), with the others integrating via reference, not duplication. Decide ownership; don't ship three Customer resources.

## What good looks like

For an airline-industry example:

| Capability | Owned resources |
|---|---|
| Schedule Management | Flight, Schedule, Equipment |
| Booking | Booking, BookingHold, BookingEvent |
| Passenger Identity | Passenger, IdentityDocument |
| Check-in | CheckIn, BoardingPass |
| Baggage | BagTag, BagEvent |
| Loyalty | LoyaltyAccount, LoyaltyTransaction |

Each capability fits on one slide. Each resource has one owner. The OpenAPI tag hierarchy mirrors this map. The `x-business-capability` on every operation makes capability-level governance trivial.

Compare to a *bad* version: "Customer API" with 60 endpoints, one tag, no hierarchy. Same business, way harder to use, evolve, or govern.

## When you don't have capabilities yet

Sometimes the user shows up with an idea and no capability map. That's fine — propose one inline.

> "Before I write the spec: I'm reading two capabilities here — **Search** (finding flights matching criteria) and **Booking** (committing to a flight and paying). Search is read-only; Booking is transactional. The spec will be organized around those two. Push back if that splits things wrong for your team."

Get a yes (or a correction) before generating. Surfacing the model is cheap; reshaping a 1500-line spec is not.
