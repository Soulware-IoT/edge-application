"""Peewee ORM model for the Readings bounded context.

Defines the ``readings_outbox`` table: the durable local buffer of readings awaiting
forwarding to the backend. A background flusher drains unsent rows and marks them sent,
so readings survive backend/gateway outages (at-least-once delivery). Infrastructure
layer — accessed only through the repository.
"""
from datetime import datetime, timezone

from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
)

from shared.infrastructure.database import db


class ReadingOutbox(Model):
    """ORM mapping for the ``readings_outbox`` table.

    Attributes:
        id (AutoField): Auto-incrementing primary key; also the flush order.
        device_code (CharField): Hardware code of the device the reading belongs to.
        temperature_c (IntegerField): Temperature sample in degrees Celsius.
        gas_ppm (FloatField): Gas concentration sample in PPM.
        severity (CharField): Edge-computed severity (SAFE/WARNING/CRITICAL).
        occurred_at (CharField): ISO-8601 timestamp, forwarded to the backend verbatim.
        sent (BooleanField): False until the flusher confirms the backend accepted it.
        created_at (DateTimeField): When the edge buffered the reading.
    """

    id = AutoField()
    device_code = CharField(index=True)
    temperature_c = IntegerField()
    gas_ppm = FloatField()
    severity = CharField()
    occurred_at = CharField()
    sent = BooleanField(default=False, index=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        """Peewee metadata: binds the model to the shared database and names the table."""

        database = db
        table_name = "readings_outbox"
