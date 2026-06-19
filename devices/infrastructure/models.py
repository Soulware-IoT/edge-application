"""Peewee ORM model for the Devices bounded context.

Defines the ``devices`` table that persists the local replica of this organization's IoT
device registry. This module belongs to the infrastructure layer; the domain and
application layers never import it directly — access is mediated through the repository.
"""
from peewee import CharField, FloatField, IntegerField, Model

from shared.infrastructure.database import db


class Device(Model):
    """ORM mapping for the ``devices`` table.

    Each row mirrors one in-service device from the backend's ``GET /edge/registry``.

    Attributes:
        device_id (CharField): Natural primary key — the backend's device id.
        code (CharField): The device's unique hardware code.
        name (CharField): Human-readable name (nullable).
        api_key (CharField): The ``device → edge`` credential checked on device calls.
        warn_temperature_c / crit_temperature_c (IntegerField): Temperature limits.
        warn_gas_ppm / crit_gas_ppm (FloatField): Gas limits.
    """

    device_id          = CharField(primary_key=True)
    code               = CharField(unique=True)
    name               = CharField(null=True)
    api_key            = CharField()
    warn_temperature_c = IntegerField()
    crit_temperature_c = IntegerField()
    warn_gas_ppm       = FloatField()
    crit_gas_ppm       = FloatField()

    class Meta:
        """Peewee metadata: binds the model to the shared database and names the table."""

        database   = db
        table_name = 'devices'
