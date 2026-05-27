import voluptuous as vol
import glob
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


async def async_list_serial_ports(hass):
    """Scan serial ports without blocking event loop."""
    def _scan():
        return sorted(
            glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        )
    return await hass.async_add_executor_job(_scan)


async def async_get_pymodbus_version(hass):
    """Detect pymodbus version safely inside HA runtime."""
    def _check():
        try:
            import pymodbus
            return pymodbus.__version__
        except Exception as e:
            return f"NOT FOUND ({e})"
    return await hass.async_add_executor_job(_check)


class SandiSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial setup screen."""
        ports = await async_list_serial_ports(self.hass)
        pymodbus_version = await async_get_pymodbus_version(self.hass)

        if user_input is not None:
            return self.async_create_entry(
                title=f"SANDISOLAR SD-PRO-EU (pymodbus {pymodbus_version})",
                data={
                    "port": user_input["port"],
                    "baudrate": user_input["baudrate"],
                    "slave": user_input["slave"],
                    "update_interval": user_input["update_interval"],
                    "pymodbus_version": pymodbus_version,
                },
            )

        # USB port selection
        if ports:
            port_selector = vol.In(ports)
            default_port = ports[0]
        else:
            port_selector = str
            default_port = "/dev/ttyUSB0"

        # UI schema including pymodbus detection
        schema = vol.Schema(
            {
                vol.Optional(
                    "pymodbus_info",
                    default=f"Detected pymodbus: {pymodbus_version}"
                ): str,

                vol.Required("port", default=default_port): port_selector,
                vol.Required("baudrate", default=9600): int,
                vol.Required("slave", default=1): int,
                vol.Required("update_interval", default=10): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SandiSolarOptionsFlow(config_entry)


class SandiSolarOptionsFlow(config_entries.OptionsFlow):
    """Options screen."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    "update_interval",
                    default=self.entry.options.get(
                        "update_interval",
                        self.entry.data.get("update_interval", 10),
                    ),
                ): int
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
