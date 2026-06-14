"""Binary sensor platform for BlueBOLT integration."""
from dataclasses import dataclass
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import BlueBoltDataUpdateCoordinator
from .entity import BlueBoltEntity


@dataclass(frozen=True, kw_only=True)
class BlueBoltBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a BlueBOLT binary sensor."""

    # The status value that means the sensor is "on" (e.g. a problem is present).
    on_value: int


BINARY_SENSORS: tuple[BlueBoltBinarySensorDescription, ...] = (
    BlueBoltBinarySensorDescription(
        key="surge_protection_ok",
        name="Surge Protection",
        device_class=BinarySensorDeviceClass.SAFETY,
        on_value=0,  # 0 = no surge protection (unsafe)
    ),
    BlueBoltBinarySensorDescription(
        key="power_ok",
        name="Power Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_value=0,  # 0 = power fault (over/under-voltage)
    ),
    BlueBoltBinarySensorDescription(
        key="overvoltage",
        name="Overvoltage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_value=1,
    ),
    BlueBoltBinarySensorDescription(
        key="undervoltage",
        name="Undervoltage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_value=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlueBOLT binary sensor entities."""
    coordinator: BlueBoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    async_add_entities(
        BlueBoltBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
        if description.key in data
    )


class BlueBoltBinarySensor(BlueBoltEntity, BinarySensorEntity):
    """A power-quality / safety status flag reported by the device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    entity_description: BlueBoltBinarySensorDescription

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
        description: BlueBoltBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_id}_{description.key}"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the flag is in its 'on' state."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        return value == self.entity_description.on_value
