# OpenAPI 3.2 skeleton — copy this and fill in.
# Every TODO marker is something you must replace before shipping.

openapi: 3.2.0
$self: https://specs.example.com/TODO-api/v1     # optional; remove if single-file

info:
  title: TODO API title
  version: 1.0.0
  summary: TODO one-line tagline
  description: |
    TODO 2–4 sentences. State the business capability, the consumers, and the
    auth model. Link to deeper documentation in `externalDocs` below.
  contact:
    name: TODO team name
    email: api@example.com
    url: https://docs.example.com/teams/TODO
  license:
    name: TODO license (e.g. Apache-2.0, proprietary)
    identifier: Apache-2.0
  x-business-capability: TODO-capability-id
  x-owner: TODO-team-id

externalDocs:
  url: https://docs.example.com/capabilities/TODO
  description: Capability runbook and domain model.

servers:
  - name: production
    url: https://api.example.com/v1
    description: Production.
  - name: staging
    url: https://staging.api.example.com/v1
    description: Staging mirror of production.

tags:
  # Capability tags (top of hierarchy)
  - name: TODO-capability
    summary: TODO Capability label
    description: TODO 1–2 sentences.
    kind: nav

  # Resource tags (children of capabilities)
  - name: TODO-resource
    summary: TODO Resource label
    description: TODO 1–2 sentences.
    parent: TODO-capability
    kind: nav

security:
  - oauthAuthCode: [read:TODO]

paths:
  # See assets/templates/resource-collection.yaml for the standard shape.
  /TODO-resources:
    get:
      operationId: listTODOResources
      summary: TODO summary
      description: TODO 1–3 sentences.
      tags: [TODO-resource]
      x-business-capability: TODO-capability-id
      x-use-case:
        - TODO use case 1
      x-idempotent: true
      x-side-effects: none
      parameters:
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/Cursor'
      responses:
        '200':
          summary: Page of resources
          description: TODO.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TODOResourcePage'
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '429': { $ref: '#/components/responses/TooManyRequests' }
        '500': { $ref: '#/components/responses/InternalError' }

components:
  # Pull in canonical pieces from the other templates:
  #   - errors.yaml          → schemas.Problem, responses.*, examples.*
  #   - pagination.yaml      → parameters.PageSize, parameters.Cursor, schemas.PageMeta
  #   - common-parameters.yaml → IdempotencyKey, IfMatch, etc.
  #   - security-schemes.yaml → oauthAuthCode, oauthDevice, bearerJwt, apiKey
  schemas: {}
  parameters: {}
  responses: {}
  examples: {}
  securitySchemes: {}
  mediaTypes: {}
