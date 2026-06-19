"""Shared database infrastructure for the Cocina360 Edge Application.

Provides a single :class:`peewee.SqliteDatabase` instance (``db``) that ORM models
will share once bounded contexts are modelled, so every model operates on the same
physical database file.

The :func:`init_db` helper opens a connection and creates any missing tables. It is
modelled here but not yet called at boot (see ``app.py``) — there are no models to
register at this baseline.

Note:
    The ``db`` object is not connected until :func:`init_db` is called. Peewee's
    ``SqliteDatabase`` manages the connection lifecycle via its own thread-local storage.
"""
from peewee import SqliteDatabase

# Shared SQLite database instance for this edge's local store / replica.
db = SqliteDatabase('cocina360_edge.db')


def init_db() -> None:
    """Open the database connection and create all required tables.

    Register each bounded context's models in the ``create_tables`` call (via deferred
    imports, to avoid circular dependencies) as they are added. Idempotent: ``safe=True``
    suppresses ``CREATE TABLE`` errors for pre-existing tables.

    Side effects:
        - Opens a connection to ``cocina360_edge.db`` (creating the file if absent).
        - Creates any registered tables if absent.
        - Closes the connection afterwards.
    """
    db.connect()
    # No models registered yet; add them here as bounded contexts are modelled, e.g.:
    #   from iam.infrastructure.models import Device
    #   db.create_tables([Device], safe=True)
    db.create_tables([], safe=True)
    db.close()
