"""Application services for the Readings bounded context.

Orchestrates reading ingestion: authenticate the device by its ``X-API-Key`` against the
local registry replica, classify the sample's severity from that device's thresholds, and
buffer it in the outbox for forwarding. No HTTP/ORM concerns here — those live in the
interface and infrastructure layers.
"""
from datetime import datetime, timezone

from devices.application.services import DeviceRegistryApplicationService
from readings.domain.entities import Reading
from readings.infrastructure.repositories import ReadingOutboxRepository


class ReadingIngestionApplicationService:
    """Coordinates the *ingest reading* use-case."""

    def __init__(self):
        """Initialise the service with its collaborators."""
        self.devices = DeviceRegistryApplicationService()
        self.outbox = ReadingOutboxRepository()

    def ingest(
        self,
        api_key: str,
        temperature_c: int,
        gas_ppm: float,
        occurred_at: str | None = None,
    ) -> Reading | None:
        """Authenticate the device, classify the reading, and buffer it.

        Args:
            api_key: The device's ``X-API-Key`` credential.
            temperature_c: Temperature sample in degrees Celsius.
            gas_ppm: Gas concentration sample in PPM.
            occurred_at: Optional ISO-8601 timestamp; defaults to now (UTC) when omitted.

        Returns:
            The buffered :class:`Reading`, or ``None`` if the API key is unknown.
        """
        device = self.devices.authenticate(api_key)
        if device is None:
            return None

        severity = Reading.classify(temperature_c, gas_ppm, device.thresholds)
        occurred = occurred_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        reading = Reading(device.code, temperature_c, gas_ppm, severity, occurred)
        self.outbox.enqueue(reading)
        return reading
