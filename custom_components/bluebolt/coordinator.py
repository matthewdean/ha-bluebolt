"""DataUpdateCoordinator for BlueBOLT."""
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .device import BlueBoltDevice

_LOGGER = logging.getLogger(__name__)


class BlueBoltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching BlueBOLT data."""

    def __init__(self, hass: HomeAssistant, device: BlueBoltDevice) -> None:
        """Initialize the coordinator."""
        self.device = device

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the device."""
        try:
            status = await self.device.get_status()

            if not status:
                raise UpdateFailed("Failed to get device status")

            return status

        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
