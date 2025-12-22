"""Switch platform for BlueBOLT integration."""
import asyncio
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
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
    """Set up BlueBOLT switch entities."""
    coordinator: BlueBoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device.device_type
    device_config = DEVICE_CONFIG.get(device_type, {})

    num_switches = device_config.get("outlets") or device_config.get("outlet_banks", 8)

    entities = [
        BlueBoltOutletSwitch(coordinator, entry, outlet_id)
        for outlet_id in range(1, num_switches + 1)
    ]

    async_add_entities(entities)


class BlueBoltOutletSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a BlueBOLT outlet switch."""

    def __init__(
        self,
        coordinator: BlueBoltDataUpdateCoordinator,
        entry: ConfigEntry,
        outlet_id: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._outlet_id = outlet_id
        self._attr_has_entity_name = True

        device_type = coordinator.device.device_type
        device_config = DEVICE_CONFIG.get(device_type, {})

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
        elif "outlet_banks" in device_config:
            self._attr_name = f"Outlet Bank {outlet_id}"
        else:
            self._attr_name = f"Outlet {outlet_id}"

        self._pending_state = None
        self._pending_task = None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        device_type = self.coordinator.device.device_type
        device_config = DEVICE_CONFIG.get(device_type, {})
        if "outlet_banks" in device_config:
            return f"{self._entry.entry_id}_outlet_bank_{self._outlet_id}"
        return f"{self._entry.entry_id}_outlet_{self._outlet_id}"

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
