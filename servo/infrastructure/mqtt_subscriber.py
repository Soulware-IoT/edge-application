"""MQTT subscriber: receives servo commands published by the edge gateway.

Subscribes to this edge's own topic (keyed by its device code) on the shared broker —
an outbound connection that works even behind NAT/CGNAT, unlike an inbound HTTP request.
For now it just logs the command; publishing to the embedded system via a local MQTT
broker is a future step.
"""
import json
import os

import paho.mqtt.client as mqtt

SERVO_TOPIC_TEMPLATE = "cocina360/edge/{edge_code}/servo"

_client: mqtt.Client | None = None


def _mqtt_config() -> tuple[str, int, str, str]:
    host = os.environ.get("MQTT_HOST", "").strip()
    if not host:
        raise RuntimeError("Missing required environment variable: MQTT_HOST")
    port = int(os.environ.get("MQTT_PORT", "8883"))
    username = os.environ.get("MQTT_USERNAME", "").strip()
    password = os.environ.get("MQTT_PASSWORD", "").strip()
    if not username or not password:
        raise RuntimeError("Missing required environment variables: MQTT_USERNAME / MQTT_PASSWORD")
    return host, port, username, password


def _on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code != 0:
        print(f"[SERVO] MQTT connection failed: {reason_code}")
        return
    topic = userdata["topic"]
    client.subscribe(topic)
    print(f"[SERVO] Subscribed to {topic}")


def _on_message(client, userdata, message):
    body = json.loads(message.payload.decode("utf-8"))
    iot_device_id = body.get("iotDeviceId")
    command = body.get("command")
    # TODO: publish via MQTT to the embedded system that controls this device
    print(f"[SERVO] device={iot_device_id} command={command}")


def start_servo_subscriber(edge_code: str) -> None:
    """Start the background MQTT subscriber once (idempotent).

    Listens for servo commands addressed to this edge's own topic.
    """
    global _client
    if _client is not None:
        return
    host, port, username, password = _mqtt_config()
    topic = SERVO_TOPIC_TEMPLATE.format(edge_code=edge_code)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={"topic": topic})
    client.username_pw_set(username, password)
    client.tls_set()
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect(host, port)
    client.loop_start()

    _client = client
    print(f"[SERVO] MQTT subscriber starting for topic {topic}")
