"""Identity and Access Management (IAM) bounded context package.

Handles device registration, look-up, and API-key-based authentication for
smart band devices, following a Domain-Driven Design layered architecture:

- **domain**: ``Device`` aggregate root and ``AuthService`` domain service.
- **application**: ``AuthApplicationService`` that orchestrates authentication
  use-cases.
- **infrastructure**: Peewee ORM models and repository implementations for
  persisting device data.
- **interfaces**: Flask Blueprint exposing authentication helpers used by
  other bounded contexts.
"""
