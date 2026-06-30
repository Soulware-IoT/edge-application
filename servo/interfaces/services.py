"""Interface (REST API) layer for servo commands.

Receives servo commands forwarded by the edge gateway from the backend.
For now logs the command; MQTT publishing to the embedded system will be added here.
"""
from flask import Blueprint, jsonify, request

servo_api = Blueprint("servo_api", __name__)


@servo_api.route("/servo", methods=["POST"])
def handle_servo():
    """Accept a servo command from the edge gateway.

    **Request body (JSON):**

    .. code-block:: json

        { "iotDeviceId": "<uuid>", "command": "start|stop" }

    **Responses:**

    - ``200 OK`` – command received.
    - ``400 Bad Request`` – missing required fields.
    """
    body = request.get_json(silent=True) or {}
    iot_device_id = body.get("iotDeviceId")
    command = body.get("command")

    if not iot_device_id or not command:
        return jsonify({"error": "Missing required fields: iotDeviceId, command"}), 400

    # TODO: publish via MQTT to the embedded system that controls this device
    print(f"[SERVO] device={iot_device_id} command={command}")

    return "", 200
