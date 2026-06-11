import glob
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


UPDATE_INTERVAL_OPTIONS = [
    {"value": "5", "label": "5 sekund"},
    {"value": "10", "label": "10 sekund"},
    {"value": "15", "label": "15 sekund"},
    {"value": "30", "label": "30 sekund"},
    {"value": "60", "label": "60 sekund"},
]


async def async_list_serial_ports(hass):
    """List available serial ports."""

    def _scan():
        return sorted(
            glob.glob("/dev/ttyUSB*")
            + glob.glob("/dev/ttyACM*")
            + glob.glob("/dev/serial/by-id/*")
        )

    return await hass.async_add_executor_job(_scan)


class SandiSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SANDISOLAR Modbus RTU."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle initial setup."""
        errors = {}

        ports = await async_list_serial_ports(self.hass)

        if user_input is not None:
            update_interval = int(user_input["update_interval"])

            if user_input["slave"] < 1 or user_input["slave"] > 247:
                errors["slave"] = "invalid_slave"

            if update_interval < 5:
                errors["update_interval"] = "invalid_update_interval"

            if not errors:
                return self.async_create_entry(
                    title=f"SANDISOLAR SD-PRO-EU ({user_input['port']})",
                    data={
                        "port": user_input["port"],
                        "baudrate": user_input["baudrate"],
                        "slave": user_input["slave"],
                        "update_interval": update_interval,
                    },
                )

        if ports:
            port_selector = vol.In(ports)
            default_port = ports[0]
        else:
            port_selector = str
            default_port = "/dev/ttyUSB0"

        default_update_interval = str(DEFAULT_SCAN_INTERVAL)

        if default_update_interval not in ["5", "10", "15", "30", "60"]:
            default_update_interval = "10"

        schema = vol.Schema(
            {
                vol.Required("port", default=default_port): port_selector,
                vol.Required("baudrate", default=9600): vol.In(
                    [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
                ),
                vol.Required("slave", default=1): int,
                vol.Required(
                    "update_interval",
                    default=default_update_interval,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=UPDATE_INTERVAL_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow."""
        return SandiSolarOptionsFlow(config_entry)


class SandiSolarOptionsFlow(config_entries.OptionsFlow):
    """Options flow for SANDISOLAR Modbus RTU."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        errors = {}

        if user_input is not None:
            update_interval = int(user_input["update_interval"])

            if update_interval < 5:
                errors["update_interval"] = "invalid_update_interval"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        "update_interval": update_interval,
                    },
                )

        current_update_interval = self.entry.options.get(
            "update_interval",
            self.entry.data.get(
                "update_interval",
                DEFAULT_SCAN_INTERVAL,
            ),
        )

        current_update_interval = str(current_update_interval)

        if current_update_interval not in ["5", "10", "15", "30", "60"]:
            current_update_interval = "10"

        schema = vol.Schema(
            {
                vol.Required(
                    "update_interval",
                    default=current_update_interval,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=UPDATE_INTERVAL_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
