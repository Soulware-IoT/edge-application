"""Background flusher that forwards buffered readings to the backend.

The ingestion endpoint only writes readings to the local outbox, so this daemon drains
that outbox on a fixed interval: it pulls unsent rows, POSTs them (through the gateway) to
the backend's ``/edge/readings``, and marks them sent once accepted. This decouples device
ingestion from backend availability — readings survive backend/gateway outages and are
retried until delivered (at-least-once).

Runs on a daemon thread so it never blocks shutdown. On failure the batch stays unsent and
is retried on the next tick; rows already marked sent are never resent.
"""
import os
import threading
import time

import requests

from readings.infrastructure.repositories import ReadingOutboxRepository
from shared.infrastructure.gateway_client import forward_readings

DEFAULT_FLUSH_SECONDS = 5
DEFAULT_BATCH_SIZE = 100

_thread: threading.Thread | None = None
_outbox = ReadingOutboxRepository()


def flush_interval_seconds() -> int:
    """Return the configured flush interval, defaulting to every few seconds."""
    raw = os.environ.get("READINGS_FLUSH_SECONDS", "").strip()
    try:
        value = int(raw)
        return value if value > 0 else DEFAULT_FLUSH_SECONDS
    except ValueError:
        return DEFAULT_FLUSH_SECONDS


def flush_batch_size() -> int:
    """Return the configured per-request batch size, defaulting to a sensible value."""
    raw = os.environ.get("READINGS_FLUSH_BATCH_SIZE", "").strip()
    try:
        value = int(raw)
        return value if value > 0 else DEFAULT_BATCH_SIZE
    except ValueError:
        return DEFAULT_BATCH_SIZE


def _to_payload(row) -> dict:
    """Map an outbox row to the backend's reading shape."""
    return {
        "deviceCode": row.device_code,
        "temperatureC": row.temperature_c,
        "gasPpm": row.gas_ppm,
        "severity": row.severity,
        "occurredAt": row.occurred_at,
    }


def _drain(batch_size: int) -> int:
    """Forward all currently-unsent readings in batches; return how many were sent.

    Each batch is marked sent only after the backend accepts it, so a mid-drain failure
    (which propagates) leaves the remaining readings buffered for the next tick.
    """
    total = 0
    while True:
        rows = _outbox.fetch_unsent(batch_size)
        if not rows:
            break
        forward_readings([_to_payload(row) for row in rows])
        _outbox.mark_sent([row.id for row in rows])
        total += len(rows)
        if len(rows) < batch_size:
            break
    return total


def _flush_loop(interval: int, batch_size: int) -> None:
    while True:
        try:
            sent = _drain(batch_size)
            if sent:
                print(f"[EDGE] Forwarded {sent} reading(s) to backend")
        except requests.RequestException as error:
            print(f"[EDGE] Reading flush failed (will retry, readings kept): {error}")
        time.sleep(interval)


def start_readings_flushing() -> None:
    """Start the background readings flusher once (idempotent)."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    interval = flush_interval_seconds()
    batch_size = flush_batch_size()
    _thread = threading.Thread(
        target=_flush_loop, args=(interval, batch_size), name="readings-flusher", daemon=True)
    _thread.start()
    print(f"[EDGE] Readings flusher started (every {interval}s, batch {batch_size})")
