"""Sensor platform for BlueBOLT integration."""
from typing import Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_CONFIG, DOMAIN
from .coordinator import BlueBoltDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlueBOLT sensor entities."""
    coordinator: BlueBoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device.device_type
    device_config = DEVICE_CONFIG.get(device_type, {})

    entities = [
        BlueBoltVoltageSensor(coordinator, entry),
        BlueBoltCurrentSensor(coordinator, entry),
        BlueBoltPowerSensor(coordinator, entry),
    ]

    if device_config.get("has_temperature_sensor", False):
        entities.append(BlueBoltTemperatureSensor(coordinator, entry))

    if device_config.get("has_ups_sensors", False):
        entities.extend([
            BlueBoltVoltageOutSensor(coordinator, entry),
            BlueBoltBatteryLevelSensor(coordinator, entry),
            BlueBoltLoadLevelSensor(coordinator, entry),
        ])

    async_add_entities(entities)


class BlueBoltSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for BlueBOLT sensors."""

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_type = self.coordinator.device.device_type
        device_config = DEVICE_CONFIG.get(device_type, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get("name", self._entry.data[CONF_HOST]),
            manufacturer=device_config.get("manufacturer", "Unknown"),
            model=device_config.get("model", "Unknown"),
            sw_version=self.coordinator.device.firmware_version,
        )


class BlueBoltVoltageSensor(BlueBoltSensorBase):
    """Voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_name = "Voltage"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_voltage"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("voltage")


class BlueBoltCurrentSensor(BlueBoltSensorBase):
    """Current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_name = "Current"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_current"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("current")


class BlueBoltPowerSensor(BlueBoltSensorBase):
    """Power sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_name = "Power"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("power")


class BlueBoltTemperatureSensor(BlueBoltSensorBase):
    """Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_name = "Temperature"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_temperature"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("temperature")


class BlueBoltVoltageOutSensor(BlueBoltSensorBase):
    """UPS output voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_name = "Output Voltage"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_voltage_out"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("voltage_out")


class BlueBoltBatteryLevelSensor(BlueBoltSensorBase):
    """UPS battery level sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Battery Level"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_battery_level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        battery_level = self.coordinator.data.get("battery_level")
        return battery_level * 100 if battery_level is not None else None


class BlueBoltLoadLevelSensor(BlueBoltSensorBase):
    """UPS load level sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Load Level"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_load_level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("load_level")
