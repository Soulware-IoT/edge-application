"""Domain entities for the Devices bounded context.

The edge keeps a local replica of its organization's IoT device registry. ``Device`` is
the aggregate root of that replica: the backend is its source of truth (synced via the
registry poller), and the edge reads it to serve and authenticate physical devices
locally, including across backend/gateway outages.
"""


class SafetyThresholds:
    """Value object holding a device's four calibration limits.

    Temperatures are in degrees Celsius, gas concentrations in parts per million (PPM);
    for each metric the warning limit sits below the critical limit. Replicated from the
    backend, so it is treated as data here (no re-validation of the warn < crit invariant).

    Attributes:
        warn_temperature_c (int): Temperature warning limit.
        crit_temperature_c (int): Temperature critical limit.
        warn_gas_ppm (float): Gas warning limit.
        crit_gas_ppm (float): Gas critical limit.
    """

    def __init__(
        self,
        warn_temperature_c: int,
        crit_temperature_c: int,
        warn_gas_ppm: float,
        crit_gas_ppm: float,
    ):
        self.warn_temperature_c = warn_temperature_c
        self.crit_temperature_c = crit_temperature_c
        self.warn_gas_ppm = warn_gas_ppm
        self.crit_gas_ppm = crit_gas_ppm


class Device:
    """Aggregate root: one in-service IoT device as known to this edge.

    Attributes:
        device_id (str): The backend's surrogate id for the device (primary key).
        code (str): The device's hardware code (e.g. ``'COCINA-3F9A2B7C'``).
        name (str | None): Human-readable name assigned when the device was claimed.
        api_key (str): The ``device → edge`` credential presented as ``X-API-Key``.
        thresholds (SafetyThresholds): The calibration limits the edge serves to the device.
    """

    def __init__(
        self,
        device_id: str,
        code: str,
        name: str | None,
        api_key: str,
        thresholds: SafetyThresholds,
    ):
        self.device_id = device_id
        self.code = code
        self.name = name
        self.api_key = api_key
        self.thresholds = thresholds
