"""Client for the edge application's link to its edge gateway.

This edge application *is* the edge device: it holds the edge API key (its identity).
It calls the gateway (a dumb forwarder) at ``GATEWAY_URL``, sending its key as
``X-Edge-Api-Key``; the gateway passes that header through to the backend. On boot the
app calls ``GET {GATEWAY_URL}/me`` to confirm it is authenticated and linked to an org.
"""
import os

import requests

API_KEY_HEADER = "X-Edge-Api-Key"
REQUEST_TIMEOUT_SECONDS = 10


def gateway_url() -> str:
    """Return the configured edge gateway base URL.

    Raises:
        RuntimeError: if ``GATEWAY_URL`` is missing or blank.
    """
    url = os.environ.get("GATEWAY_URL", "").strip()
    if not url:
        raise RuntimeError("Missing required environment variable: GATEWAY_URL")
    return url.rstrip("/")


def _auth_headers() -> dict:
    """Build the auth header carrying this edge device's identity key."""
    return {API_KEY_HEADER: os.environ.get("EDGE_API_KEY", "").strip()}


def fetch_identity() -> dict:
    """Call ``GET {GATEWAY_URL}/edge/me`` and return this edge's identity + organization.

    The gateway is a pass-through, so we call the backend's real path (``/edge/me``)
    through it.

    Raises:
        requests.RequestException: if the gateway is unreachable or rejects the key.
    """
    response = requests.get(
        f"{gateway_url()}/edge/me", headers=_auth_headers(), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def fetch_registry() -> dict:
    """Call ``GET {GATEWAY_URL}/edge/registry`` and return this org's device registry.

    The response carries the organization id and its in-service IoT devices, each with
    its apiKey (the ``device → edge`` credential) and safety thresholds. The gateway is a
    pass-through, so we call the backend's real path (``/edge/registry``) through it.

    Raises:
        requests.RequestException: if the gateway is unreachable or rejects the key.
    """
    response = requests.get(
        f"{gateway_url()}/edge/registry", headers=_auth_headers(), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def forward_readings(readings: list[dict]) -> None:
    """POST a batch of buffered readings to ``{GATEWAY_URL}/edge/readings``.

    The gateway passes the ``X-Edge-Api-Key`` header through to the backend, which resolves
    this edge's organization and records the batch. Each entry must already be in the
    backend's shape (``deviceCode``, ``temperatureC``, ``gasPpm``, ``severity``,
    ``occurredAt``).

    Raises:
        requests.RequestException: if the gateway is unreachable or the backend rejects the
            batch (non-2xx) — the caller keeps the readings buffered and retries later.
    """
    response = requests.post(
        f"{gateway_url()}/edge/readings",
        headers={**_auth_headers(), "Content-Type": "application/json"},
        json={"readings": readings},
        timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()


def verify_linkage() -> None:
    """Best-effort boot check: log whether this edge is linked to an organization.

    Failures are logged but do not stop the app — the edge can still serve cached
    devices locally while the backend/gateway is unavailable.
    """
    try:
        identity = fetch_identity()
        org_id = identity.get("organizationId")
        edge_id = identity.get("edgeDeviceId")
        name = identity.get("name")
        print("=" * 60)
        print("  EDGE CONNECTED")
        print(f"  Name         : {name}")
        print(f"  Edge ID      : {edge_id}")
        print(f"  Organization : {org_id}")
        print("=" * 60)
    except requests.RequestException as error:
        print("=" * 60)
        print("  EDGE CONNECTION FAILED")
        print(f"  {error}")
        print("=" * 60)
        raise
