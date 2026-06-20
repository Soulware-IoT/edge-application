"""Shared database infrastructure for the Cocina360 Edge Application.

Provides a single :class:`peewee.SqliteDatabase` instance (``db``) that ORM models
share, so every model operates on the same physical database file. The edge is a
multi-threaded process (Flask request handlers read while the registry poller writes),
so the connection is configured for WAL mode and cross-thread access.

The :func:`init_db` helper opens a connection and creates any missing tables; call it
once at boot before any model is used (see ``app.py``).
"""
import os

from peewee import SqliteDatabase

# Absolute path on a persistent, writable volume in production; relative fallback for
# local runs. WAL mode lets the poller write while request handlers read; check_same_thread
# is disabled because the poller thread and Flask threads share this connection.
DB_PATH = os.environ.get("EDGE_DB_PATH", "cocina360_edge.db")

db = SqliteDatabase(
    DB_PATH,
    pragmas={
        "journal_mode": "wal",     # poller can write while requests read
        "busy_timeout": 5000,      # wait up to 5s on a brief lock instead of failing
        "foreign_keys": 1,
        "synchronous": 1,          # NORMAL: durable enough and fast on WAL
    },
    check_same_thread=False,       # shared across the poller thread and Flask threads
)


def init_db() -> None:
    """Open the database connection and create all required tables.

    Register each local context's models in the ``create_tables`` call (via deferred
    imports, to avoid circular dependencies) as they are added. Idempotent: ``safe=True``
    suppresses ``CREATE TABLE`` errors for pre-existing tables.

    Side effects:
        - Opens a connection to ``EDGE_DB_PATH`` (creating the file if absent).
        - Creates any registered tables if absent.
        - Closes the connection afterwards.
    """
    from devices.infrastructure.models import Device
    from readings.infrastructure.models import ReadingOutbox

    db.connect()
    db.create_tables([Device, ReadingOutbox], safe=True)
    db.close()
