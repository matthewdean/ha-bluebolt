"""Switch platform for BlueBOLT integration."""
import asyncio
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up BlueBOLT switch entities."""
    coordinator: BlueBoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device.device_type
    num_switches = max_outlets(device_type)

    entities = [
        BlueBoltOutletSwitch(coordinator, entry, outlet_id)
        for outlet_id in range(1, num_switches + 1)
    ]

    async_add_entities(entities)


class BlueBoltOutletSwitch(BlueBoltEntity, SwitchEntity):
    """Representation of a BlueBOLT outlet switch."""

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
        outlet_id: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, entry)
        self._outlet_id = outlet_id

        device_type = coordinator.device.device_type
        device_config = DEVICE_CONFIG.get(device_type, {})
        self._is_bank = "outlet_banks" in device_config

        custom_outlet_names = entry.data.get("outlets", {})
        custom_bank_names = entry.data.get("outlet_banks", {})

        # Check both int and string keys (JSON serialization converts int → string)
        if outlet_id in custom_outlet_names or str(outlet_id) in custom_outlet_names:
            self._attr_name = custom_outlet_names.get(
                outlet_id, custom_outlet_names.get(str(outlet_id))
            )
        elif outlet_id in custom_bank_names or str(outlet_id) in custom_bank_names:
            self._attr_name = custom_bank_names.get(
                outlet_id, custom_bank_names.get(str(outlet_id))
            )
        elif self._is_bank:
            self._attr_name = f"Outlet Bank {outlet_id}"
        else:
            self._attr_name = f"Outlet {outlet_id}"

        self._pending_state = None
        self._pending_task = None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        if self._is_bank:
            return f"{self._device_id}_outlet_bank_{self._outlet_id}"
        return f"{self._device_id}_outlet_{self._outlet_id}"

    @property
    def is_on(self) -> bool:
        """Return true if outlet is on."""
        if self._pending_state is not None:
            return self._pending_state
        outlets = self.coordinator.data.get("outlets", {})
        return outlets.get(self._outlet_id, False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the outlet on."""
        if self._pending_task:
            self._pending_task.cancel()

        self._pending_state = True
        self.async_write_ha_state()

        await self.coordinator.device.set_outlet(self._outlet_id, True)
        self._pending_task = asyncio.create_task(self._clear_pending_state())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the outlet off."""
        if self._pending_task:
            self._pending_task.cancel()

        self._pending_state = False
        self.async_write_ha_state()

        await self.coordinator.device.set_outlet(self._outlet_id, False)
        self._pending_task = asyncio.create_task(self._clear_pending_state())

    async def _clear_pending_state(self) -> None:
        """Clear pending state after delay and refresh."""
        await asyncio.sleep(5)
        self._pending_state = None
        self._pending_task = None
        await self.coordinator.async_request_refresh()
