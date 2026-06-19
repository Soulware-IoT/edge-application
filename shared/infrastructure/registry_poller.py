"""Background poller that keeps the local device-registry replica in sync.

The edge is a headless API, so rather than fetch the registry per request it polls the
backend (through the gateway) on a fixed interval and persists the result into the local
SQLite replica via the Devices application service. The replica is the edge's local
source of truth for which IoT devices to serve and how to authenticate them; it survives
backend/gateway outages between polls.

Polling runs on a daemon thread so it never blocks process shutdown. Failures are logged
and the previous replica is kept — the edge keeps serving the last known registry.
"""
import os
import threading
import time
from datetime import datetime

import requests

from devices.application.services import DeviceRegistryApplicationService
from shared.infrastructure.gateway_client import fetch_registry

DEFAULT_POLL_SECONDS = 5

_thread: threading.Thread | None = None
_registry_service = DeviceRegistryApplicationService()


def _debug_enabled() -> bool:
    """Whether to dump the local replica's contents after each sync."""
    return os.environ.get("EDGE_DEBUG", "").strip().lower() in ("1", "true", "yes")


def _print_local_replica() -> None:
    """Read the devices back from local storage and print them (debug aid)."""
    devices = _registry_service.list_devices()

    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    offset = now.strftime("%z")

    print("\n" + "=" * 60)
    print(f"[EDGE][DEBUG] {timestamp} {offset} — Local replica holds {len(devices)} device(s):")

    for i, device in enumerate(devices, start=1):
        thresholds = device.thresholds

    print("=" * 60)
    print(f"Device #{i}")
    print(f"  Code              : {device.code}")
    print(f"  Name              : {device.name or 'unnamed'}")
    print(f"  Device ID         : {device.device_id}")
    print(f"  API Key           : {device.api_key}")
    print(f"  Temp Warn         : {thresholds.warn_temperature_c} °C")
    print(f"  Temp Critical     : {thresholds.crit_temperature_c} °C")
    print(f"  Gas Warn          : {thresholds.warn_gas_ppm} ppm")
    print(f"  Gas Critical      : {thresholds.crit_gas_ppm} ppm")

    print("=" * 60)


def poll_interval_seconds() -> int:
    """Return the configured poll interval, defaulting to every few seconds."""
    raw = os.environ.get("REGISTRY_POLL_SECONDS", "").strip()
    try:
        value = int(raw)
        return value if value > 0 else DEFAULT_POLL_SECONDS
    except ValueError:
        return DEFAULT_POLL_SECONDS


def _poll_loop(interval: int) -> None:
    while True:
        try:
            registry = fetch_registry()
            count = _registry_service.sync_from_registry(registry)
            print(f"[EDGE] Registry synced: {count} active device(s)")
            if _debug_enabled():
                _print_local_replica()
        except requests.RequestException as error:
            print(f"[EDGE] Registry sync failed (serving last known registry): {error}")
        time.sleep(interval)


def start_registry_polling() -> None:
    """Start the background registry poller once (idempotent)."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    interval = poll_interval_seconds()
    _thread = threading.Thread(
        target=_poll_loop, args=(interval,), name="registry-poller", daemon=True)
    _thread.start()
    print(f"[EDGE] Registry poller started (every {interval}s)")
