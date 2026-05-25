import os
import logging
from typing import Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from .const import DOMAIN
from .hub import SandiSolarModbusHub

_LOGGER = logging.getLogger(__name__)

SERIAL_PATH = "/dev/serial/by-id/"


async def async_list_serial_ports(hass: HomeAssistant) -> list[str]:
    """List serial ports without blocking the event loop."""
    try:
        items = await hass.async_add_executor_job(os.listdir, SERIAL_PATH)
        return [os.path.join(SERIAL_PATH, item) for item in items]
    except Exception:
        return ["/dev/ttyUSB0"]


class DummyEntry:
    """Minimal fake entry for connection test."""
    def __init__(self, data):
        self.data = data
        self.title = data.get("name", "SANDISOLAR")


class SandiSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SANDISOLAR Modbus RTU."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[dict] = None):
        """Handle the initial step."""
        hass = self.hass

        ports = await async_list_serial_ports(hass)

        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required(CONF_NAME, default="SANDISOLAR"): str,
                    vol.Required("port", default=ports[0]): vol.In(ports),
                    vol.Required("baudrate", default=9600): int,
                    vol.Required("slave_id", default=1): int,
                    vol.Required("update_interval", default=30): int,
                }
            )
            return self.async_show_form(step_id="user", data_schema=schema)

        # Test connection
        try:
            dummy = DummyEntry(user_input)
            hub = SandiSolarModbusHub(hass, dummy)
            await hub.async_init()

        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default=user_input["name"]): str,
                        vol.Required("port", default=user_input["port"]): vol.In(ports),
                        vol.Required("baudrate", default=user_input["baudrate"]): int,
                        vol.Required("slave_id", default=user_input["slave_id"]): int,
                        vol.Required("update_interval", default=user_input["update_interval"]): int,
                    }
                ),
                errors={"base": "cannot_connect"},
            )

        return self.async_create_entry(
            title=user_input["name"],
            data=user_input,
        )
