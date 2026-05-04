# Security schemes — drop into components.securitySchemes.
# Includes 3.2's OAuth2 device authorization flow.

components:
  securitySchemes:
    oauthAuthCode:
      type: oauth2
      description: |
        OAuth 2.0 authorization-code flow with PKCE. Default for end-user
        web and mobile clients.
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          refreshUrl: https://auth.example.com/token
          scopes:
            read:widgets: Read widgets
            write:widgets: Create and modify widgets
            admin:widgets: Administrative actions on widgets

    oauthClientCredentials:
      type: oauth2
      description: |
        OAuth 2.0 client-credentials flow. For service-to-service calls.
      flows:
        clientCredentials:
          tokenUrl: https://auth.example.com/token
          scopes:
            read:widgets: Read widgets
            write:widgets: Create and modify widgets

    oauthDevice:
      type: oauth2
      description: |
        OAuth 2.0 device authorization grant (RFC 8628). For CLI tools, IoT
        devices, and other clients without a browser. Available in OAS 3.2.
      flows:
        deviceAuthorization:
          deviceAuthorizationUrl: https://auth.example.com/device_authorization
          tokenUrl: https://auth.example.com/token
          scopes:
            read:widgets: Read widgets

    bearerJwt:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        Pre-issued bearer JWT. Token signature must be verifiable against the
        published JWKS. Used when a token is minted out-of-band (e.g. by a
        gateway) and the API only needs to verify it.

    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
      description: |
        Static API key for server-to-server calls inside a trusted network.
        Avoid for end-user clients — use OAuth2 instead.

    # Mark legacy flows deprecated explicitly. OAS 3.2 supports the deprecated
    # flag on security schemes.
    oauthLegacyImplicit:
      type: oauth2
      deprecated: true
      description: |
        DEPRECATED. Use `oauthAuthCode` with PKCE for new integrations.
      flows:
        implicit:
          authorizationUrl: https://auth.example.com/authorize
          scopes:
            read:widgets: Read widgets
