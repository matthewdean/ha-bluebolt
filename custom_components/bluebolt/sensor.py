"""Sensor platform for BlueBOLT integration."""
from typing import Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_CONFIG, DOMAIN
from .coordinator import BlueBoltDataUpdateCoordinator
from .entity import BlueBoltEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlueBOLT sensor entities."""
    coordinator: BlueBoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device.device_type
    device_config = DEVICE_CONFIG.get(device_type, {})
    data = coordinator.data or {}

    entities = [
        BlueBoltVoltageSensor(coordinator, entry),
        BlueBoltCurrentSensor(coordinator, entry),
        BlueBoltPowerSensor(coordinator, entry),
    ]

    # Created only when the device actually reports them.
    if "apparent_power" in data:
        entities.append(BlueBoltApparentPowerSensor(coordinator, entry))
    if "power_factor" in data:
        entities.append(BlueBoltPowerFactorSensor(coordinator, entry))

    if device_config.get("has_temperature_sensor", False):
        entities.append(BlueBoltTemperatureSensor(coordinator, entry))

    if device_config.get("has_ups_sensors", False):
        entities.extend([
            BlueBoltVoltageOutSensor(coordinator, entry),
            BlueBoltBatteryLevelSensor(coordinator, entry),
            BlueBoltLoadLevelSensor(coordinator, entry),
        ])

    async_add_entities(entities)


class BlueBoltSensorBase(BlueBoltEntity, SensorEntity):
    """Base class for BlueBOLT sensors."""


class BlueBoltVoltageSensor(BlueBoltSensorBase):
    """Voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_name = "Voltage"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._device_id}_voltage"

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
        return f"{self._device_id}_current"

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
        return f"{self._device_id}_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("power")


class BlueBoltApparentPowerSensor(BlueBoltSensorBase):
    """Apparent power sensor."""

    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfApparentPower.VOLT_AMPERE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Apparent Power"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._device_id}_apparent_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("apparent_power")


class BlueBoltPowerFactorSensor(BlueBoltSensorBase):
    """Power factor sensor."""

    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Power Factor"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._device_id}_power_factor"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("power_factor")


class BlueBoltTemperatureSensor(BlueBoltSensorBase):
    """Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_name = "Temperature"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._device_id}_temperature"

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
        return f"{self._device_id}_voltage_out"

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
        return f"{self._device_id}_battery_level"

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
        return f"{self._device_id}_load_level"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        return self.coordinator.data.get("load_level")
