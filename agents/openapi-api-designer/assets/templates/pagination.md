# Pagination — cursor (preferred) and offset.
# Drop into components.

components:
  parameters:
    PageSize:
      name: pageSize
      in: query
      description: Maximum number of items to return on this page.
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 25
      example: 25

    Cursor:
      name: cursor
      in: query
      description: |
        Opaque cursor from a previous response's `page.nextCursor`.
        Omit on the first request. Cursors are stable across the dataset
        version that produced them; resorting or schema changes invalidate them.
      required: false
      schema:
        type: string
      example: eyJpZCI6ImFiYzEyMyIsInRzIjoiMjAyNi0wNS0wNFQxMjowMDowMFoifQ

    # Use offset only if you have a small bounded dataset.
    Offset:
      name: offset
      in: query
      description: Zero-indexed offset. Use cursor pagination for unbounded sets.
      required: false
      schema:
        type: integer
        minimum: 0
        default: 0
      example: 0

  schemas:
    PageMeta:
      type: object
      title: PageMeta
      description: |
        Pagination metadata returned with every paginated response.
      required: [pageSize]
      properties:
        nextCursor:
          type: [string, "null"]
          description: |
            Opaque cursor for the next page. `null` when there are no more results.
            Pass back as the `cursor` query parameter on the next request.
        pageSize:
          type: integer
          description: Number of items returned on this page (≤ requested pageSize).
        totalCount:
          type: [integer, "null"]
          description: |
            Optional total count of items in the collection. Server may omit
            (return null) for large datasets where counting is expensive.

    OffsetPageMeta:
      type: object
      title: OffsetPageMeta
      description: Offset pagination metadata.
      required: [offset, pageSize, totalCount]
      properties:
        offset:
          type: integer
          description: Zero-indexed offset of this page.
        pageSize:
          type: integer
          description: Items returned on this page.
        totalCount:
          type: integer
          description: Total items in the collection.
