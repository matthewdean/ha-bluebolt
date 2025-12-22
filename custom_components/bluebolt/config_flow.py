"""Config flow for BlueBOLT integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .device import BlueBoltDevice

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    device = BlueBoltDevice(
        host=data[CONF_HOST],
        mac=data[CONF_MAC],
    )

    if not await device.connect():
        raise CannotConnect

    info = await device.get_device_info()

    return {
        "title": data.get(CONF_NAME) or data[CONF_HOST],
        "firmware": info.get("firmware", "Unknown"),
    }


class BlueBoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BlueBOLT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID to prevent duplicate entries
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}_{user_input[CONF_MAC]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_MAC): str,
                vol.Optional(CONF_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, import_data: Dict[str, Any]) -> FlowResult:
        """Handle import from YAML configuration."""
        try:
            info = await validate_input(self.hass, import_data)
        except CannotConnect:
            _LOGGER.error(
                "Cannot connect to BlueBOLT device at %s", import_data[CONF_HOST]
            )
            return self.async_abort(reason="cannot_connect")
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception during YAML import")
            return self.async_abort(reason="unknown")

        # Set unique ID to prevent duplicate entries
        await self.async_set_unique_id(
            f"{import_data[CONF_HOST]}_{import_data[CONF_MAC]}"
        )
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=info["title"],
            data=import_data,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

