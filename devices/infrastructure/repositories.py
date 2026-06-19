"""Repository for the Devices bounded context.

Maps between the :class:`~devices.domain.entities.Device` domain entity and the
:class:`~devices.infrastructure.models.Device` Peewee model. Application services work
only with domain entities and stay isolated from ORM and database details.
"""
from typing import Optional

from devices.domain.entities import Device, SafetyThresholds
from devices.infrastructure.models import Device as DeviceModel
from shared.infrastructure.database import db


class DeviceRepository:
    """Persists and reconstructs :class:`~devices.domain.entities.Device` entities."""

    @staticmethod
    def _to_entity(row: DeviceModel) -> Device:
        """Map an ORM row to a domain entity."""
        return Device(
            device_id=row.device_id,
            code=row.code,
            name=row.name,
            api_key=row.api_key,
            thresholds=SafetyThresholds(
                warn_temperature_c=row.warn_temperature_c,
                crit_temperature_c=row.crit_temperature_c,
                warn_gas_ppm=row.warn_gas_ppm,
                crit_gas_ppm=row.crit_gas_ppm,
            ),
        )

    @staticmethod
    def replace_all(devices: list[Device]) -> None:
        """Replace the local replica with ``devices`` (the backend's current registry).

        Upserts every supplied device and removes any local row no longer present, so
        deactivated/unclaimed devices drop out. Runs in a single transaction for atomicity.
        """
        rows = [
            {
                "device_id": device.device_id,
                "code": device.code,
                "name": device.name,
                "api_key": device.api_key,
                "warn_temperature_c": device.thresholds.warn_temperature_c,
                "crit_temperature_c": device.thresholds.crit_temperature_c,
                "warn_gas_ppm": device.thresholds.warn_gas_ppm,
                "crit_gas_ppm": device.thresholds.crit_gas_ppm,
            }
            for device in devices
        ]
        keep_ids = [row["device_id"] for row in rows]

        with db.atomic():
            if rows:
                DeviceModel.insert_many(rows).on_conflict_replace().execute()
                DeviceModel.delete().where(DeviceModel.device_id.not_in(keep_ids)).execute()
            else:
                DeviceModel.delete().execute()

    @staticmethod
    def find_all() -> list[Device]:
        """Return every device in the local replica."""
        return [DeviceRepository._to_entity(row) for row in DeviceModel.select()]

    @staticmethod
    def find_by_api_key(api_key: str) -> Optional[Device]:
        """Resolve a device by its apiKey (the ``device → edge`` credential)."""
        row = DeviceModel.get_or_none(DeviceModel.api_key == api_key)
        return DeviceRepository._to_entity(row) if row else None
