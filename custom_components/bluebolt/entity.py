"""Base entity for the BlueBOLT integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_CONFIG, DOMAIN
from .coordinator import BlueBoltDataUpdateCoordinator


class BlueBoltEntity(CoordinatorEntity):
    """Base class providing shared device info and identity.

    Entity and device identity are keyed off the device's own hardware id
    (``device.device_id``) rather than the config entry id, so they survive the
    integration being removed and re-added.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def _device_id(self) -> str:
        """Stable hardware identifier used to key entities and the device."""
        return self.coordinator.device.device_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.device
        device_config = DEVICE_CONFIG.get(device.device_type, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._entry.data.get("name", self._entry.data[CONF_HOST]),
            manufacturer=device_config.get("manufacturer", "Unknown"),
            model=device_config.get("model", "Unknown"),
            sw_version=device.firmware_version,
            hw_version=device.hardware_version,
            serial_number=device.serial_number,
        )
