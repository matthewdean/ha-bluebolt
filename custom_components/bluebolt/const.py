DOMAIN = "bluebolt"
DEFAULT_PORT = 57010
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 5

DEVICE_TYPE_M4315 = "M4315-PRO"
DEVICE_TYPE_M4320 = "M4320-PRO"
DEVICE_TYPE_MB1500 = "MB1500"
DEVICE_TYPE_F1500 = "F1500-UPS"

DEVICE_CLASS_MAP = {
    "km4315": DEVICE_TYPE_M4315,
    "km4320": DEVICE_TYPE_M4320,
    "kmb1500": DEVICE_TYPE_MB1500,
    "kf1500": DEVICE_TYPE_F1500,
}

DEVICE_CONFIG = {
    DEVICE_TYPE_M4315: {
        "model": "M4315-PRO",
        "manufacturer": "Panamax",
        "outlets": 8,
        "has_temperature_sensor": True,
        "has_ups_sensors": False,
    },
    DEVICE_TYPE_M4320: {
        "model": "M4320-PRO",
        "manufacturer": "Panamax",
        "outlets": 8,
        "has_temperature_sensor": True,
        "has_ups_sensors": False,
    },
    DEVICE_TYPE_MB1500: {
        "model": "MB1500",
        "manufacturer": "Panamax",
        "outlet_banks": 4,
        "has_temperature_sensor": False,
        "has_ups_sensors": True,
    },
    DEVICE_TYPE_F1500: {
        "model": "F1500-UPS",
        "manufacturer": "Furman",
        "outlet_banks": 4,
        "has_temperature_sensor": False,
        "has_ups_sensors": True,
    },
}
