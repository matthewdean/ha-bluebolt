"""Button platform for BlueBOLT integration."""
from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_CONFIG, DOMAIN, max_outlets
from .coordinator import BlueBoltDataUpdateCoordinator
from .entity import BlueBoltEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlueBOLT button entities."""
    coordinator: BlueBoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device.device_type
    device_config = DEVICE_CONFIG.get(device_type, {})

    num_outlets = max_outlets(device_type)
    is_bank = "outlet_banks" in device_config

    entities: list[ButtonEntity] = [
        BlueBoltCycleOutletButton(coordinator, entry, outlet_id, is_bank)
        for outlet_id in range(1, num_outlets + 1)
    ]
    entities.append(BlueBoltRebootButton(coordinator, entry))

    async_add_entities(entities)


class BlueBoltCycleOutletButton(BlueBoltEntity, ButtonEntity):
    """Power-cycle a single outlet (off, then back on).

    Categorized as CONFIG so it sits with Reboot under Configuration instead of
    cluttering the main controls. It is a disruptive action, so guard it with a
    per-card confirmation dialog on the dashboard.
    """

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
        outlet_id: int,
        is_bank: bool,
    ) -> None:
        """Initialize the power-cycle button."""
        super().__init__(coordinator, entry)
        self._outlet_id = outlet_id
        label = "Outlet Bank" if is_bank else "Outlet"
        self._attr_name = f"Power Cycle {label} {outlet_id}"
        suffix = "outlet_bank" if is_bank else "outlet"
        self._attr_unique_id = f"{self._device_id}_cycle_{suffix}_{outlet_id}"

    async def async_press(self) -> None:
        """Power-cycle the outlet."""
        await self.coordinator.device.cycle_outlet(self._outlet_id)
        await self.coordinator.async_request_refresh()


class BlueBoltRebootButton(BlueBoltEntity, ButtonEntity):
    """Reboot the entire device."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Reboot"

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the reboot button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_reboot"

    async def async_press(self) -> None:
        """Reboot the device."""
        await self.coordinator.device.reboot()
        await self.coordinator.async_request_refresh()
