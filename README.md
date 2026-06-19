# Smart Band Edge Service

`smart_band_edge_service` is a lightweight IoT edge API for ingesting heart-rate
data emitted by smart band devices. The service follows a Domain-Driven Design
(DDD) approach and separates the device-authentication concerns from the health
data ingestion concerns.

At its current stage, the service provides:

- device authentication using `device_id` + `X-API-Key`
- ingestion of heart-rate (`bpm`) measurements
- SQLite persistence through Peewee ORM
- a layered architecture aligned with DDD bounded contexts

## Current Scope

This repository currently implements a focused subset of an IoT-edge solution:

- **Implemented**
  - registration/lookup of a development test device
  - authentication of device-originated requests
  - creation and persistence of health records
  - timestamp normalization to UTC
- **Not implemented yet**
  - activity tracking
  - sleep tracking
  - analytics pipelines
  - cloud synchronization
  - a dedicated health check endpoint such as `GET /status`

Keeping the README aligned with the implemented scope is especially important
in IoT projects, where device contracts and API behavior must remain explicit
and dependable.

## Why DDD for an IoT Edge Service?

In IoT systems, devices, telemetry, authentication, and persistence often grow
quickly and evolve independently. DDD helps keep that complexity manageable by
organizing the code around business capabilities instead of technical concerns.

This service is split into two bounded contexts:

### 1. IAM (Identity and Access Management)

Responsible for identifying devices and validating their credentials.

- **Core concept**: `Device`
- **Primary responsibility**: authenticate incoming requests from smart bands

### 2. Health

Responsible for validating and storing health telemetry.

- **Core concept**: `HealthRecord`
- **Primary responsibility**: accept heart-rate readings and persist them

The Health context depends on IAM only for device validation, which keeps the
telemetry model decoupled from authentication details.

## Layered Architecture

Each bounded context follows the same DDD-inspired structure:

- **Domain**
  - entities and domain services
  - business rules and invariants
  - no framework or ORM concerns
- **Application**
  - orchestration of use cases
  - coordinates repositories and domain services
- **Infrastructure**
  - Peewee models
  - repository implementations
  - persistence details
- **Interfaces**
  - Flask HTTP endpoints and request handling

### Project Structure

```text
smart_band_edge_service/
├── app.py
├── health/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── iam/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── shared/
│   └── infrastructure/
└── docs/
```

## Technical Stories

Technical stories are part of the official project documentation and describe
the integration contract from the smart-band device maker perspective for
unattended device-to-edge interactions.

- Source of truth: [`docs/user-stories.md`](docs/user-stories.md)
- Story style: `As a ... I want to ... so that ...` with Gherkin acceptance
  criteria (`Given/When/Then`)
- Focus: observable edge-service behavior (authentication, validation,
  persistence, bootstrap), not UI behavior

### Story-to-Context Mapping

- **Health bounded context**: `TS-SBE-001`, `TS-SBE-003`, `TS-SBE-004`,
  `TS-SBE-005`
- **IAM bounded context**: `TS-SBE-002`
- **Application bootstrap / shared infrastructure**: `TS-SBE-006`

Use these stories to drive API evolution, regression validation, and backlog
prioritization as the IoT edge capabilities grow.

## Technology Stack

- Python 3.13+
- Flask
- Peewee
- SQLite
- python-dateutil

Exact Python dependencies are declared in [`requirements.txt`](requirements.txt).

## Getting Started

### 1. Create a virtual environment

```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Run the service

```sh
python app.py
```

The Flask application runs in debug mode when started this way.

## Runtime Behavior

The application performs bootstrap work before serving the first request:

- initializes the SQLite database
- creates the `devices` and `health_records` tables if they do not exist
- seeds a development test device if absent

Database initialization is triggered by the Flask `before_request` hook, so the
setup occurs on the first incoming HTTP request handled by the process.

## Development Test Device

For local development, the application seeds the following device if it is not
already present in the database:

- `device_id`: `smart-band-001`
- `api_key`: `test-api-key-123`

> [!WARNING]
> These credentials are hard-coded for local development only. Do not reuse
> them in production or on real IoT deployments.

## API Contract

### Create a health record

`POST /api/v1/health-monitoring/data-records`

Creates a new heart-rate record for an authenticated device.

#### Required headers

- `Content-Type: application/json`
- `X-API-Key: <device api key>`

#### Request body

```json
{
  "device_id": "smart-band-001",
  "bpm": 72.5,
  "created_at": "2025-06-04T18:23:00-05:00"
}
```

#### Request fields

- `device_id` (`string`, required): unique device identifier
- `bpm` (`number`, required): heart rate in beats per minute
- `created_at` (`string`, optional): ISO 8601 timestamp; when omitted, the
  service uses the current UTC time

#### Example request

```sh
curl -X POST http://127.0.0.1:5000/api/v1/health-monitoring/data-records \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: test-api-key-123' \
  -d '{
	"device_id": "smart-band-001",
	"bpm": 72.5,
	"created_at": "2025-06-04T18:23:00-05:00"
  }'
```

#### Success response

`201 Created`

```json
{
  "id": 1,
  "device_id": "smart-band-001",
  "bpm": 72.5,
  "created_at": "2025-06-04T23:23:00+00:00Z"
}
```

#### Error responses

- `400 Bad Request`
  - missing required fields
  - invalid BPM value
  - malformed timestamp
- `401 Unauthorized`
  - missing `device_id`
  - missing `X-API-Key`
  - invalid device/API key pair

## Operational Notes for IoT Projects

When adapting this service for a real IoT solution, consider the following:

- **Credential management**: replace hard-coded development credentials with a
  secure enrollment or provisioning flow.
- **Persistence**: SQLite is suitable for local development and lightweight
  edge deployments, but not ideal for high-write concurrency.
- **Observability**: add structured logging, trace correlation, and a proper
  health check endpoint before production use.
- **Device contracts**: version telemetry payloads carefully so device firmware
  and server-side ingestion remain compatible.
- **Startup lifecycle**: move bootstrap logic out of `before_request` if you
  need deterministic initialization during container startup.

## Documentation

Additional documentation is available in [`docs/`](docs):

- [`docs/user-stories.md`](docs/user-stories.md): technical stories and
  acceptance criteria for unattended smart-band to edge-service interactions.
- [`docs/class-diagram.puml`](docs/class-diagram.puml): PlantUML diagram of
  the bounded contexts, layers, and relationships.

## License

This project is licensed under the MIT License. See [`LICENSE.md`](LICENSE.md)
for details.
