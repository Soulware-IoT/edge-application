# Technical Stories — Smart Band Edge Service

## Overview

This document captures the technical stories for the Smart Band Edge Service,
an IoT edge application that receives telemetry from smart-band devices through
HTTP endpoints. In this context, interactions are unattended: each device
submits health records autonomously, without direct end-user participation at
the moment of transmission.

The stories are written from the perspective of a smart-band device maker. This
perspective emphasizes the integration contract on which the device and its
firmware depend, including authentication, telemetry validation, timestamp
handling, persistence guarantees, and service readiness.

The acceptance criteria focus on observable edge-service behavior rather than
user interface details. They reflect the current implemented scope of the
solution and align with the Domain-Driven Design approach used in the project,
particularly the Health and IAM bounded contexts and their domain,
application, infrastructure, and interface layers.

### TS-SBE-001 — Ingest an Authenticated Health Record
As a smart-band device maker, I want each device to submit heart-rate readings autonomously to the health ingestion endpoint so that the edge service validates and persists each record reliably.

Acceptance criteria:
- Scenario: Successful create
  - Given a smart-band device submits a `POST` request to `/api/v1/health-monitoring/data-records`
  - And the request includes the required telemetry attributes
  - And the request includes valid device credentials
  - When the edge service validates and persists the health record
  - Then the edge service returns a response with status `201 Created`
  - And the response includes the created record with `id`, `device_id`, `bpm`, and `created_at`

- Scenario: Missing required fields
  - Given a smart-band device submits a `POST` request to `/api/v1/health-monitoring/data-records`
  - And the request omits a required telemetry attribute
  - When the edge service validates the payload
  - Then the edge service returns a response with status `400 Bad Request`
  - And the response includes an error payload describing missing required fields

---

### TS-SBE-002 — Enforce Device Authentication by API Key
As a smart-band device maker, I want each device request to be authenticated with an API key so that only registered devices can submit telemetry to the edge service.

Acceptance criteria:
- Scenario: Missing authentication data
  - Given a smart-band device submits a request to a protected endpoint
  - And the request omits the required device credentials
  - When the edge service executes IAM authentication
  - Then the edge service returns a response with status `401 Unauthorized`
  - And the response indicates missing `device_id` or `X-API-Key`

- Scenario: Invalid credential pair
  - Given a smart-band device submits a request to a protected endpoint
  - And the device identifier and API key do not match any registered device
  - When the edge service executes IAM authentication
  - Then the edge service returns a response with status `401 Unauthorized`
  - And the response indicates an invalid device ID or API key

---

### TS-SBE-003 — Validate BPM Domain Rules
As a smart-band device maker, I want the service to validate BPM values sent by each device against domain constraints so that invalid physiological data is rejected before persistence.

Acceptance criteria:
- Scenario: BPM outside the accepted range
  - Given a smart-band device submits a `POST` request to `/api/v1/health-monitoring/data-records`
  - And the `bpm` value is outside the range `0..200`
  - When the domain service validates the payload
  - Then the edge service returns a response with status `400 Bad Request`
  - And the response includes an error payload for invalid data format

- Scenario: BPM is not numeric
  - Given a smart-band device submits a `POST` request to `/api/v1/health-monitoring/data-records`
  - And the `bpm` value is not numeric
  - When the domain service attempts to parse `bpm`
  - Then the edge service returns a response with status `400 Bad Request`
  - And the response includes an error payload for invalid data format

---

### TS-SBE-004 — Normalize Device Timestamps to UTC
As a smart-band device maker, I want the service to normalize timestamps sent by each device to UTC so that stored telemetry remains consistent across device time zones.

Acceptance criteria:
- Scenario: Timestamp provided with time-zone offset
  - Given a smart-band device submits a `POST` request to `/api/v1/health-monitoring/data-records`
  - And the `created_at` value is provided in valid ISO 8601 format with an offset
  - When the edge service parses the timestamp through the domain service
  - Then the value is converted and stored as UTC
  - And the response includes the normalized `created_at` value

- Scenario: Timestamp omitted
  - Given a smart-band device submits a `POST` request to `/api/v1/health-monitoring/data-records`
  - And the request omits `created_at`
  - When the edge service creates the health record through the domain service
  - Then `created_at` is set using the current UTC time
  - And the record is persisted with that generated timestamp

---

### TS-SBE-005 — Persist Accepted Health Records
As a smart-band device maker, I want each accepted telemetry record from a device to become durable and identifiable so that ingestion remains reliable and traceable.

Acceptance criteria:
- Scenario: Accepted record becomes durable
  - Given the edge service holds a valid `HealthRecord` domain entity without an `id`
  - When the edge service completes persistence
  - Then the record is stored in local persistence
  - And the returned domain entity includes the assigned `id`

- Scenario: Application service orchestrates domain and persistence
  - Given a smart-band device submits a valid authenticated request
  - And the request contains accepted `bpm` and timestamp values
  - When the edge service executes the create-health-record use case
  - Then it validates the device through the IAM repository
  - And it delegates entity creation to the domain service
  - And it persists the record through the health repository

---

### TS-SBE-006 — Bootstrap Database and Seed Test Device on First Request
As a smart-band device maker, I want the edge service to prepare its local storage on the first request so that a device can begin sending records without manual database preparation.

Acceptance criteria:
- Scenario: First request bootstraps storage
  - Given the edge service receives its first HTTP request after startup
  - When the edge service executes its startup setup hook
  - Then local storage is initialized
  - And the required storage structures are created if missing
  - And the default test device (`smart-band-001`) is made available if absent

- Scenario: Subsequent requests skip bootstrap work
  - Given the edge service already handled at least one request in the current process
  - When another request is received
  - Then the edge service does not run initialization again
  - And request handling proceeds without repeating bootstrap operations






