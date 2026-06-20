"""Domain entities for the Readings bounded context.

A ``Reading`` is one safety sample taken by a physical device and accepted by this edge.
The edge classifies each sample's :class:`SafetySeverity` locally from the device's
replicated thresholds (the backend trusts the edge-computed severity), buffers it, and
later forwards it to the backend. The device's 5s tick is *not* persisted — only readings
the edge decides to forward (e.g. on a safety-state change) become ``Reading`` rows.
"""
from devices.domain.entities import SafetyThresholds


class SafetySeverity:
    """The safety level a reading represents; mirrors the backend's traffic-light logic."""

    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Reading:
    """A single safety reading buffered by the edge for the backend.

    Attributes:
        device_code (str): Hardware code of the device the reading belongs to.
        temperature_c (int): Temperature sample in degrees Celsius.
        gas_ppm (float): Gas concentration sample in parts per million.
        severity (str): One of :class:`SafetySeverity`, computed from the device's thresholds.
        occurred_at (str): ISO-8601 timestamp of when the reading was taken (UTC).
    """

    def __init__(
        self,
        device_code: str,
        temperature_c: int,
        gas_ppm: float,
        severity: str,
        occurred_at: str,
    ):
        self.device_code = device_code
        self.temperature_c = temperature_c
        self.gas_ppm = gas_ppm
        self.severity = severity
        self.occurred_at = occurred_at

    @staticmethod
    def classify(temperature_c: int, gas_ppm: float, thresholds: SafetyThresholds) -> str:
        """Classify a raw sample against a device's calibration limits.

        CRITICAL if either metric reaches its critical limit; otherwise WARNING if either
        reaches its warning limit; otherwise SAFE.
        """
        if temperature_c >= thresholds.crit_temperature_c or gas_ppm >= thresholds.crit_gas_ppm:
            return SafetySeverity.CRITICAL
        if temperature_c >= thresholds.warn_temperature_c or gas_ppm >= thresholds.warn_gas_ppm:
            return SafetySeverity.WARNING
        return SafetySeverity.SAFE
