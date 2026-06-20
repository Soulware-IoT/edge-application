"""Repository for the Readings bounded context.

Maps between the :class:`~readings.domain.entities.Reading` domain entity and the
:class:`~readings.infrastructure.models.ReadingOutbox` Peewee model, and exposes the
outbox operations the ingestion endpoint and the background flusher need.
"""
from readings.domain.entities import Reading
from readings.infrastructure.models import ReadingOutbox as ReadingOutboxModel


class ReadingOutboxRepository:
    """Persists readings to the local outbox and drains them for forwarding."""

    @staticmethod
    def enqueue(reading: Reading) -> None:
        """Buffer a reading for later forwarding to the backend."""
        ReadingOutboxModel.create(
            device_code=reading.device_code,
            temperature_c=reading.temperature_c,
            gas_ppm=reading.gas_ppm,
            severity=reading.severity,
            occurred_at=reading.occurred_at,
        )

    @staticmethod
    def fetch_unsent(limit: int = 100) -> list[ReadingOutboxModel]:
        """Return up to ``limit`` unsent rows in insertion order (oldest first)."""
        return list(
            ReadingOutboxModel.select()
            .where(ReadingOutboxModel.sent == False)  # noqa: E712 — peewee needs ==
            .order_by(ReadingOutboxModel.id)
            .limit(limit)
        )

    @staticmethod
    def mark_sent(ids: list[int]) -> None:
        """Mark the given rows as forwarded once the backend has accepted them."""
        if ids:
            ReadingOutboxModel.update(sent=True).where(ReadingOutboxModel.id.in_(ids)).execute()

    @staticmethod
    def count_unsent() -> int:
        """Return how many readings are still waiting to be forwarded."""
        return (
            ReadingOutboxModel.select()
            .where(ReadingOutboxModel.sent == False)  # noqa: E712 — peewee needs ==
            .count()
        )
