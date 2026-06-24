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

SETTINGS_REFRESH_INTERVAL_OPTIONS = [
    {"value": "10", "label": "10 sekund"},
    {"value": "15", "label": "15 sekund"},
    {"value": "30", "label": "30 sekund"},
    {"value": "60", "label": "60 sekund"},
    {"value": "120", "label": "120 sekund"},
    {"value": "300", "label": "300 sekund"},
]

WRITE_VERIFY_DELAY_OPTIONS = [
    {"value": "0.2", "label": "0,2 s"},
    {"value": "0.5", "label": "0,5 s"},
    {"value": "1.0", "label": "1,0 s"},
    {"value": "2.0", "label": "2,0 s"},
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


def _default_select(value, allowed, fallback):
    value = str(value)

    if value not in allowed:
        return fallback

    return value


def _number_box(min_value, max_value, step, unit=None):
    config = selector.NumberSelectorConfig(
        min=min_value,
        max=max_value,
        step=step,
        mode=selector.NumberSelectorMode.BOX,
    )

    if unit is not None:
        config["unit_of_measurement"] = unit

    return selector.NumberSelector(config)


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

        default_update_interval = _default_select(
            DEFAULT_SCAN_INTERVAL,
            ["5", "10", "15", "30", "60"],
            "10",
        )

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
            settings_refresh_interval = int(user_input["settings_refresh_interval"])
            eta_full_real_soc_threshold = float(
                user_input["eta_full_real_soc_threshold"]
            )

            if update_interval < 5:
                errors["update_interval"] = "invalid_update_interval"

            if settings_refresh_interval < 10:
                errors["settings_refresh_interval"] = "invalid_update_interval"

            if eta_full_real_soc_threshold < 90 or eta_full_real_soc_threshold > 100:
                errors["eta_full_real_soc_threshold"] = "invalid_eta_threshold"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        "update_interval": update_interval,
                        "settings_refresh_interval": settings_refresh_interval,
                        "write_verify_delay": float(user_input["write_verify_delay"]),
                        "eta_full_real_soc_threshold": eta_full_real_soc_threshold,
                        "avg_pv_alpha": float(user_input["avg_pv_alpha"]),
                        "avg_battery_alpha": float(user_input["avg_battery_alpha"]),
                        "avg_grid_alpha": float(user_input["avg_grid_alpha"]),
                        "avg_eps_alpha": float(user_input["avg_eps_alpha"]),
                    },
                )

        options = self.entry.options

        current_update_interval = _default_select(
            options.get(
                "update_interval",
                self.entry.data.get("update_interval", DEFAULT_SCAN_INTERVAL),
            ),
            ["5", "10", "15", "30", "60"],
            "10",
        )

        current_settings_refresh_interval = _default_select(
            options.get("settings_refresh_interval", 30),
            ["10", "15", "30", "60", "120", "300"],
            "30",
        )

        current_write_verify_delay = _default_select(
            options.get("write_verify_delay", 0.5),
            ["0.2", "0.5", "1.0", "2.0"],
            "0.5",
        )

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
                ),
                vol.Required(
                    "settings_refresh_interval",
                    default=current_settings_refresh_interval,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SETTINGS_REFRESH_INTERVAL_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "write_verify_delay",
                    default=current_write_verify_delay,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=WRITE_VERIFY_DELAY_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "eta_full_real_soc_threshold",
                    default=float(options.get("eta_full_real_soc_threshold", 98.0)),
                ): _number_box(90, 100, 0.5, "%"),
                vol.Required(
                    "avg_pv_alpha",
                    default=float(options.get("avg_pv_alpha", 0.15)),
                ): _number_box(0.05, 0.80, 0.01),
                vol.Required(
                    "avg_battery_alpha",
                    default=float(options.get("avg_battery_alpha", 0.18)),
                ): _number_box(0.05, 0.80, 0.01),
                vol.Required(
                    "avg_grid_alpha",
                    default=float(options.get("avg_grid_alpha", 0.25)),
                ): _number_box(0.05, 0.80, 0.01),
                vol.Required(
                    "avg_eps_alpha",
                    default=float(options.get("avg_eps_alpha", 0.25)),
                ): _number_box(0.05, 0.80, 0.01),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
