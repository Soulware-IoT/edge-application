"""Interface (REST API) layer for the Readings bounded context.

Exposes a Flask Blueprint (``readings_api``) for devices to submit safety readings. The
device authenticates with its ``X-API-Key``; the edge resolves the device from its local
registry replica, classifies and buffers the reading, and returns immediately. Forwarding
to the backend happens asynchronously via the outbox flusher.
"""
import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from readings.application.services import ReadingIngestionApplicationService

readings_api = Blueprint("readings_api", __name__)

# Module-level singleton; safe because Flask handles one request at a time per worker.
reading_service = ReadingIngestionApplicationService()


def _readings_debug_enabled() -> bool:
    """Whether to print each reading a device submits. Separate from EDGE_DEBUG (which
    dumps the device registry replica) so reading traffic can be watched independently."""
    return os.environ.get("READINGS_DEBUG", "").strip().lower() in ("1", "true", "yes")


def _print_reading(api_key: str, data: dict, reading) -> None:
    """Print every piece of data for a reading a device just submitted (debug aid):
    the (masked) credential, the raw payload as received, each resolved field, and the
    exact JSON the flusher will forward to the backend."""
    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    offset = now.strftime("%z")
    masked_key = f"...{api_key[-4:]}" if api_key and len(api_key) >= 4 else "(set)"
    forwarded = {
        "deviceCode": reading.device_code,
        "temperatureC": reading.temperature_c,
        "gasPpm": reading.gas_ppm,
        "severity": reading.severity,
        "occurredAt": reading.occurred_at,
    }

    print("\n" + "=" * 60)
    print(f"[EDGE][READING] {timestamp} {offset} — Reading received from device:")
    print(f"  X-API-Key       : {masked_key}")
    print(f"  Raw payload     : {json.dumps(data)}")
    print(f"  Device Code     : {reading.device_code}")
    print(f"  Temperature     : {reading.temperature_c} °C")
    print(f"  Gas             : {reading.gas_ppm} ppm")
    print(f"  Severity        : {reading.severity}  (computed by edge)")
    print(f"  Occurred At     : {reading.occurred_at}")
    print(f"  Forwarded JSON  : {json.dumps(forwarded)}")
    print("=" * 60)


@readings_api.route("/api/v1/readings", methods=["POST"])
def ingest_reading():
    """Accept a safety reading from an authenticated device.

    **Request headers:**

    - ``X-API-Key`` *(required)*: the device's credential.
    - ``Content-Type: application/json`` *(required)*.

    **Request body (JSON):**

    .. code-block:: json

        { "temperature_c": 65, "gas_ppm": 4000.0, "occurred_at": "2026-06-20T01:00:05Z" }

    - ``temperature_c`` *(int, required)*, ``gas_ppm`` *(float, required)*.
    - ``occurred_at`` *(str, optional)*: ISO-8601; defaults to now (UTC) when omitted.

    **Responses:**

    - ``202 Accepted`` – buffered; body echoes the device code, computed severity, timestamp.
    - ``400 Bad Request`` – a required field is missing or invalid.
    - ``401 Unauthorized`` – the ``X-API-Key`` is missing or does not match a known device.
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "Missing X-API-Key"}), 401

    data = request.json or {}
    try:
        temperature_c = int(data["temperature_c"])
        gas_ppm = float(data["gas_ppm"])
        occurred_at = data.get("occurred_at")
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Missing or invalid reading fields"}), 400

    reading = reading_service.ingest(api_key, temperature_c, gas_ppm, occurred_at)
    if reading is None:
        return jsonify({"error": "Invalid X-API-Key"}), 401

    if _readings_debug_enabled():
        _print_reading(api_key, data, reading)

    return jsonify({
        "deviceCode": reading.device_code,
        "severity": reading.severity,
        "occurredAt": reading.occurred_at,
    }), 202
