"""Flask application entry point for the Cocina360 Edge Application.

A headless API for IoT devices. On process start it verifies linkage to the backend
via the edge gateway. Database initialization is modelled in code but intentionally
not called yet — no bounded-context services/tables are modelled at this baseline.

Typical usage::

    python app.py
    # or
    flask --app app run
"""

import os

from dotenv import load_dotenv

load_dotenv()

from flask import Flask

from shared.infrastructure.database import init_db
from shared.infrastructure.gateway_client import verify_linkage
from shared.infrastructure.registry_poller import start_registry_polling
from shared.infrastructure.readings_flusher import start_readings_flushing
from readings.interfaces.services import readings_api
from servo.interfaces.services import servo_api

app = Flask(__name__)
app.register_blueprint(readings_api)
app.register_blueprint(servo_api)


def bootstrap():
    """Run once at process start (the edge is a headless API, not request-driven).

    - Initializes the local SQLite replica (creates the ``devices`` table if absent).
    - Verifies linkage to the backend via the edge gateway (``GET /edge/me``).
    - Starts the background poller that keeps the local device registry in sync
      (``GET /edge/registry`` every few seconds).
    - Starts the background flusher that forwards buffered readings to the backend
      (``POST /edge/readings``).
    """
    try:
        init_db()
        verify_linkage()
        start_registry_polling()
        start_readings_flushing()
    except Exception as e:
        print(e)
        raise


# Run at import time so bootstrap happens on process start, for both
# `python app.py` and `flask run`.
bootstrap()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
