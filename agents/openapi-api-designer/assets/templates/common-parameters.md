# Common reusable parameters — drop into components.parameters.

components:
  parameters:
    IdempotencyKey:
      name: Idempotency-Key
      in: header
      required: false
      description: |
        Client-generated key (UUID recommended) to make this request idempotent.
        Same key + same body returns the same response within the retention
        window (24 hours). Same key + different body returns 409.
      schema:
        type: string
        format: uuid
        minLength: 16
        maxLength: 64
      example: 5f8d3c1a-7b2e-4f9a-8c1d-2e3f4a5b6c7d

    IfMatch:
      name: If-Match
      in: header
      required: true
      description: |
        ETag of the resource the client expects to update. Server compares
        and returns 412 Precondition Failed if the resource has changed.
      schema:
        type: string
      example: '"3f9a1b2c"'

    IfNoneMatch:
      name: If-None-Match
      in: header
      required: false
      description: |
        Conditional GET: server returns 304 Not Modified if the resource's
        ETag matches.
      schema:
        type: string
      example: '"3f9a1b2c"'

    AcceptLanguage:
      name: Accept-Language
      in: header
      required: false
      description: Preferred language for human-readable response fields.
      schema:
        type: string
      example: en-US

    XRequestId:
      name: X-Request-Id
      in: header
      required: false
      description: |
        Client-supplied correlation id, echoed in the response and logs.
        UUID recommended.
      schema:
        type: string
      example: 9f1e2d3c-4b5a-6c7d-8e9f-0a1b2c3d4e5f

    Fields:
      name: fields
      in: query
      required: false
      description: |
        Comma-separated list of top-level fields to include in the response.
        Reduces payload size for partial reads.
      schema:
        type: string
      example: id,name,status

    Sort:
      name: sort
      in: query
      required: false
      description: |
        Comma-separated list of fields to sort by. Prefix with `-` for
        descending order. Example: `sort=createdAt,-totalAmount`.
      schema:
        type: string
      example: -createdAt
