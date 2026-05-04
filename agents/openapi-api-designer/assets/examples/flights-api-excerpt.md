# Flights API — reference excerpt
#
# A small but complete OAS 3.2 spec demonstrating:
#   - Capability/resource tag hierarchy (3.2 parent/kind)
#   - QUERY method (3.2) for search-with-body
#   - Streaming response with itemSchema (3.2)
#   - OAuth2 device flow (3.2)
#   - RFC 9457 problem details
#   - Full x- semantic vocabulary
#
# This isn't a complete airline API — it shows the patterns. Copy
# the shapes, not the domain.

openapi: 3.2.0
$self: https://specs.example.com/flights-api/v1

info:
  title: Flights API
  version: 1.0.0
  summary: Search and book flights.
  description: |
    HTTP interface to the **Search** and **Booking** capabilities for the
    flights product line. Consumed by web, mobile, kiosk, and AI agent
    clients. All non-public endpoints require OAuth2 with appropriate scopes.
  contact:
    name: Flights Platform Team
    email: flights-platform@example.com
  license:
    name: Proprietary
    identifier: LicenseRef-Proprietary
  x-business-capability: flights
  x-owner: flights-platform-team

externalDocs:
  url: https://docs.example.com/capabilities/flights
  description: Flights capability runbook.

servers:
  - name: production
    url: https://api.example.com/v1
    description: Production.
  - name: staging
    url: https://staging.api.example.com/v1
    description: Staging mirror.

tags:
  # Capability tags
  - name: search-capability
    summary: Search
    description: Find flights matching criteria. Read-only.
    kind: nav
  - name: booking-capability
    summary: Booking
    description: Commit to a flight, manage bookings.
    kind: nav

  # Resource tags
  - name: flight-search
    summary: Flight search
    parent: search-capability
    kind: nav
  - name: bookings
    summary: Bookings
    parent: booking-capability
    kind: nav

security:
  - oauthAuthCode: [read:flights]

paths:
  /flights/search:
    query:
      operationId: searchFlights
      summary: Search flights
      description: |
        Read-only search. Supports a structured filter body that can express
        more than fits in a query string (multi-leg itineraries, fare class
        constraints, amenity filters).
      tags: [flight-search]
      x-business-capability: flights
      x-domain: search
      x-use-case:
        - Find flights for a one-way or round trip
        - Find flights matching multi-leg constraints
      x-idempotent: true
      x-side-effects: none
      x-rate-limit:
        dimension: user
        requestsPerMinute: 60
        burst: 10
      x-mcp:
        exposeAsTool: true
        toolName: search_flights
        toolDescription: |
          Search available flights matching origin, destination, dates,
          and passenger constraints. Returns a list of itineraries with
          prices, durations, and booking tokens.
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/FlightSearchRequest' }
            examples:
              roundTrip:
                summary: Round trip, 1 adult
                value:
                  origin: ATL
                  destination: MIA
                  departureDate: '2026-08-12'
                  returnDate: '2026-08-19'
                  passengers: { adults: 1 }
              multiCity:
                summary: Multi-city, 2 adults
                value:
                  legs:
                    - origin: ATL
                      destination: MIA
                      departureDate: '2026-08-12'
                    - origin: MIA
                      destination: SFO
                      departureDate: '2026-08-15'
                    - origin: SFO
                      destination: ATL
                      departureDate: '2026-08-20'
                  passengers: { adults: 2 }
      responses:
        '200':
          summary: Search results
          description: Itineraries matching the search criteria.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/FlightSearchResponse' }
              examples:
                fewResults: { $ref: '#/components/examples/FlightSearchSmallResult' }
        '400': { $ref: '#/components/responses/BadRequest' }
        '422': { $ref: '#/components/responses/UnprocessableEntity' }
        '429': { $ref: '#/components/responses/TooManyRequests' }

  /flights/search/stream:
    get:
      operationId: streamFlightSearch
      summary: Stream flight search results
      description: |
        Server-sent event stream. Use when results take long to compute and
        the client wants partial results as they arrive. Each event is a
        partial page of itineraries; the final event has `final: true`.
      tags: [flight-search]
      x-business-capability: flights
      x-use-case:
        - Show progressive search results in a UI
      x-idempotent: true
      x-side-effects: none
      x-stream:
        kind: sse
        eventTypes: [search.partial, search.complete, search.error]
      parameters:
        - name: searchId
          in: query
          required: true
          description: |
            Search id returned by `searchFlights`. Stream replays results
            for that search as they're computed.
          schema: { type: string, format: uuid }
      responses:
        '200':
          summary: Stream open
          description: SSE stream of search events.
          content:
            text/event-stream:
              itemSchema: { $ref: '#/components/schemas/FlightSearchEvent' }

  /bookings:
    post:
      operationId: createBooking
      summary: Create booking
      description: |
        Creates a confirmed booking. Idempotent when `Idempotency-Key` is
        supplied. Charges the supplied payment method on success.
      tags: [bookings]
      x-business-capability: flights
      x-domain: booking
      x-use-case:
        - Confirm a held itinerary with payment
        - Book directly without a hold
      x-idempotent: true
      x-side-effects: |
        Reserves seat inventory, charges the payment method, emits a
        `booking.created` event.
      x-ai-hints:
        - Always supply Idempotency-Key for retry safety.
        - On 402 payment-declined, do not retry without a different payment method.
      parameters:
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateBookingRequest' }
      responses:
        '201':
          summary: Booking created
          description: |
            Booking confirmed. The `Location` header points at the canonical
            booking resource. Use that URL to retrieve, modify, or cancel.
          headers:
            Location:
              schema: { type: string, format: uri }
              description: URL of the new booking.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Booking' }
          links:
            getBooking:
              operationId: getBooking
              parameters:
                bookingId: '$response.body#/id'
        '400': { $ref: '#/components/responses/BadRequest' }
        '402':
          summary: Payment declined
          description: |
            Card was declined. Problem `type` is
            `https://errors.example.com/payment-declined`. The booking was
            not created and no inventory was reserved.
          content:
            application/problem+json:
              schema: { $ref: '#/components/schemas/Problem' }
        '409': { $ref: '#/components/responses/Conflict' }
        '422': { $ref: '#/components/responses/UnprocessableEntity' }

  /bookings/{bookingId}:
    parameters:
      - name: bookingId
        in: path
        required: true
        description: Stable booking identifier.
        schema: { type: string, format: uuid }
        example: 7c2a9f0e-1b3a-4d2c-9b8e-1f0e2d3c4b5a
    get:
      operationId: getBooking
      summary: Get booking
      description: Retrieve a booking by id.
      tags: [bookings]
      x-business-capability: flights
      x-use-case:
        - Display booking details
      x-idempotent: true
      x-side-effects: none
      responses:
        '200':
          summary: Booking
          description: The booking.
          headers:
            ETag:
              schema: { type: string }
              description: Validator for optimistic concurrency.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Booking' }
        '404': { $ref: '#/components/responses/NotFound' }

components:
  parameters:
    IdempotencyKey:
      name: Idempotency-Key
      in: header
      required: false
      description: |
        Client-generated key (UUID) to make this request idempotent. Same
        key + same body returns the original response within 24 hours.
      schema: { type: string, format: uuid }

  securitySchemes:
    oauthAuthCode:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            read:flights: Read flights and bookings
            write:flights: Create and modify bookings
    oauthDevice:
      type: oauth2
      description: Device authorization grant for CLI clients (OAS 3.2).
      flows:
        deviceAuthorization:
          deviceAuthorizationUrl: https://auth.example.com/device_authorization
          tokenUrl: https://auth.example.com/token
          scopes:
            read:flights: Read flights and bookings

  schemas:
    FlightSearchRequest:
      type: object
      title: FlightSearchRequest
      description: Filter for searching flights. Either `legs` or origin/destination/dates.
      properties:
        origin:
          type: string
          minLength: 3
          maxLength: 3
          description: IATA airport code of the origin.
          examples: [ATL]
        destination:
          type: string
          minLength: 3
          maxLength: 3
          description: IATA airport code of the destination.
          examples: [MIA]
        departureDate:
          type: string
          format: date
          description: Outbound departure date.
        returnDate:
          type: [string, "null"]
          format: date
          description: Return date for round trips. Omit for one-way.
        legs:
          type: array
          description: Multi-city legs. Mutually exclusive with origin/destination/dates.
          items: { $ref: '#/components/schemas/FlightLeg' }
        passengers:
          $ref: '#/components/schemas/PassengerCounts'
        cabin:
          type: string
          enum: [ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST]
          description: |
            Preferred cabin class. `ECONOMY` is standard economy.
            `PREMIUM_ECONOMY` includes upgraded seat pitch.
            `BUSINESS` includes lie-flat where available.
            `FIRST` is the highest cabin (limited routes).

    FlightLeg:
      type: object
      title: FlightLeg
      description: One leg of a multi-city itinerary.
      required: [origin, destination, departureDate]
      properties:
        origin: { type: string, minLength: 3, maxLength: 3 }
        destination: { type: string, minLength: 3, maxLength: 3 }
        departureDate: { type: string, format: date }

    PassengerCounts:
      type: object
      title: PassengerCounts
      description: Number of passengers by type.
      properties:
        adults:
          type: integer
          minimum: 1
          maximum: 9
          description: Passengers aged 12+.
        children:
          type: integer
          minimum: 0
          maximum: 8
          description: Passengers aged 2–11.
        infants:
          type: integer
          minimum: 0
          maximum: 4
          description: Passengers under 2.

    FlightSearchResponse:
      type: object
      title: FlightSearchResponse
      description: Result page for a flight search.
      required: [searchId, itineraries]
      properties:
        searchId:
          type: string
          format: uuid
          description: |
            Stable id for this search. Use with `streamFlightSearch` or to
            request more pages.
        itineraries:
          type: array
          items: { $ref: '#/components/schemas/Itinerary' }

    Itinerary:
      type: object
      title: Itinerary
      description: A bookable itinerary.
      required: [id, totalPrice, segments]
      properties:
        id:
          type: string
          format: uuid
          description: Stable itinerary id; pass to `createBooking`.
        totalPrice:
          $ref: '#/components/schemas/Money'
        segments:
          type: array
          items: { $ref: '#/components/schemas/Segment' }

    Segment:
      type: object
      title: Segment
      description: A single flight segment within an itinerary.
      required: [flightNumber, departure, arrival]
      properties:
        flightNumber: { type: string, examples: [EX1234] }
        departure: { $ref: '#/components/schemas/AirportTime' }
        arrival: { $ref: '#/components/schemas/AirportTime' }

    AirportTime:
      type: object
      title: AirportTime
      description: Airport plus local time.
      required: [airport, time]
      properties:
        airport: { type: string, minLength: 3, maxLength: 3 }
        time: { type: string, format: date-time }

    Money:
      type: object
      title: Money
      description: Monetary amount with explicit currency.
      required: [amount, currency]
      properties:
        amount:
          type: string
          pattern: '^-?[0-9]+(\.[0-9]+)?$'
          description: Decimal as a string. Avoid floats — they lose precision.
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
          description: ISO 4217 currency code.

    FlightSearchEvent:
      type: object
      title: FlightSearchEvent
      description: One event in the SSE stream for a flight search.
      required: [type]
      properties:
        type:
          type: string
          enum: [search.partial, search.complete, search.error]
          description: |
            `search.partial` — partial result; more events to follow.
            `search.complete` — final event for this stream.
            `search.error` — fatal error; stream will close.
        itineraries:
          type: array
          items: { $ref: '#/components/schemas/Itinerary' }
        error:
          $ref: '#/components/schemas/Problem'

    CreateBookingRequest:
      type: object
      title: CreateBookingRequest
      description: Request to confirm an itinerary as a booking.
      required: [itineraryId, passengers, payment]
      properties:
        itineraryId:
          type: string
          format: uuid
          description: Itinerary to book; from `FlightSearchResponse`.
        passengers:
          type: array
          minItems: 1
          items: { $ref: '#/components/schemas/Passenger' }
        payment:
          $ref: '#/components/schemas/Payment'
      x-pii:
        categories: [identity, contact, financial]
        retention: P7Y
        classification: confidential

    Passenger:
      type: object
      title: Passenger
      description: A passenger on the booking.
      required: [givenName, familyName, dateOfBirth]
      properties:
        givenName: { type: string, minLength: 1, maxLength: 64 }
        familyName: { type: string, minLength: 1, maxLength: 64 }
        dateOfBirth: { type: string, format: date }
      x-pii:
        categories: [identity]
        retention: P7Y
        classification: confidential

    Payment:
      type: object
      title: Payment
      description: Payment instrument used for the booking.
      required: [method, token]
      properties:
        method:
          type: string
          enum: [CARD, WALLET, GIFT_CARD]
          description: |
            `CARD` — credit or debit card via tokenized card processor.
            `WALLET` — third-party wallet (Apple Pay, Google Pay).
            `GIFT_CARD` — internally-issued gift card balance.
        token:
          type: string
          description: One-time payment token from the tokenizer.
      x-pii:
        categories: [financial]
        retention: P7Y
        classification: restricted

    Booking:
      type: object
      title: Booking
      description: A confirmed booking.
      required: [id, status, totalPrice, createdAt]
      properties:
        id: { type: string, format: uuid }
        status:
          type: string
          enum: [CONFIRMED, CANCELLED, COMPLETED]
          description: |
            `CONFIRMED` — active booking. `CANCELLED` — cancelled by user
            or operator. `COMPLETED` — travel completed.
        itinerary: { $ref: '#/components/schemas/Itinerary' }
        passengers:
          type: array
          items: { $ref: '#/components/schemas/Passenger' }
        totalPrice: { $ref: '#/components/schemas/Money' }
        createdAt: { type: string, format: date-time }

    Problem:
      type: object
      title: Problem
      description: RFC 9457 problem details.
      required: [type, title, status]
      properties:
        type: { type: string, format: uri }
        title: { type: string }
        status: { type: integer }
        detail: { type: string }
        instance: { type: string, format: uri-reference }
        code: { type: string }

  responses:
    BadRequest:
      description: Malformed request.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
    NotFound:
      description: Resource not found.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
    Conflict:
      description: State conflict.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
    UnprocessableEntity:
      description: Semantic validation failure.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
    TooManyRequests:
      description: Rate limit exceeded.
      headers:
        Retry-After:
          schema: { type: integer }
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }

  examples:
    FlightSearchSmallResult:
      summary: A small result set
      value:
        searchId: 7c2a9f0e-1b3a-4d2c-9b8e-1f0e2d3c4b5a
        itineraries:
          - id: 11111111-2222-3333-4444-555555555555
            totalPrice: { amount: '249.00', currency: USD }
            segments:
              - flightNumber: EX1234
                departure: { airport: ATL, time: '2026-08-12T08:00:00-04:00' }
                arrival:   { airport: MIA, time: '2026-08-12T10:30:00-04:00' }
