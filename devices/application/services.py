"""Application services for the Devices bounded context.

Orchestrates the device-registry use-cases: syncing the local replica from the backend's
registry pull, and reading it back to serve/authenticate devices. Contains no domain
logic — it maps the registry payload to entities and delegates persistence to the repository.
"""
from devices.domain.entities import Device, SafetyThresholds
from devices.infrastructure.repositories import DeviceRepository


class DeviceRegistryApplicationService:
    """Coordinates the local device-registry replica."""

    def __init__(self):
        """Initialise the service with its repository collaborator."""
        self.device_repository = DeviceRepository()

    def sync_from_registry(self, registry: dict) -> int:
        """Replace the local replica with a fresh ``GET /edge/registry`` payload.

        Args:
            registry: the parsed registry response (``organizationId`` plus ``devices``,
                each with ``deviceId``, ``code``, ``name``, ``apiKey`` and ``thresholds``).

        Returns:
            int: the number of devices synced.
        """
        devices = [self._to_entity(entry) for entry in registry.get("devices", [])]
        self.device_repository.replace_all(devices)
        return len(devices)

    def list_devices(self) -> list[Device]:
        """Return every device in the local replica."""
        return self.device_repository.find_all()

    def authenticate(self, api_key: str) -> Device | None:
        """Resolve a device by its ``X-API-Key`` credential, or ``None`` if unknown."""
        if not api_key:
            return None
        return self.device_repository.find_by_api_key(api_key)

    @staticmethod
    def _to_entity(entry: dict) -> Device:
        thresholds = entry["thresholds"]
        return Device(
            device_id=entry["deviceId"],
            code=entry["code"],
            name=entry.get("name"),
            api_key=entry["apiKey"],
            thresholds=SafetyThresholds(
                warn_temperature_c=thresholds["warnTemperatureC"],
                crit_temperature_c=thresholds["critTemperatureC"],
                warn_gas_ppm=thresholds["warnGasPpm"],
                crit_gas_ppm=thresholds["critGasPpm"],
            ),
        )
