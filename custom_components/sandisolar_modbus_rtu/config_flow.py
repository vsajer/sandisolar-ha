"""Config flow for SANDISOLAR Modbus RTU integration."""

import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .hub import SandiSolarModbusHub

_LOGGER: logging.Logger = logging.getLogger(__name__)

DOMAIN = "sandisolar_modbus_rtu"

CONF_BAUDRATE = "baudrate"
CONF_SLAVE_ID = "slave_id"
CONF_UPDATE_INTERVAL = "update_interval"


class SandiSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SANDISOLAR."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                hub = SandiSolarModbusHub(self.hass, self._create_mock_entry(user_input))
                await hub.async_init()
                await hub.close()
            except Exception as err:
                _LOGGER.error("Connection test failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id("sandisolar")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="SANDISOLAR"): cv.string,
                vol.Required(CONF_PORT): cv.string,
                vol.Required(CONF_BAUDRATE, default=9600): vol.In(
                    [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
                ),
                vol.Required(CONF_SLAVE_ID, default=1): vol.Range(min=0, max=247),
                vol.Required(CONF_UPDATE_INTERVAL, default=30): vol.Range(
                    min=5, max=300
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    def _create_mock_entry(self, data: dict[str, Any]) -> config_entries.ConfigEntry:
        """Create a mock entry for testing."""
        return config_entries.ConfigEntry(
            version=1,
            domain=DOMAIN,
            title=data[CONF_NAME],
            data=data,
            options={},
            entry_id="test",
        )