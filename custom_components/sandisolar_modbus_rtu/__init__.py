"""SANDISOLAR Modbus RTU Integration for Home Assistant."""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady

from .hub import SandiSolarModbusHub

_LOGGER: logging.Logger = logging.getLogger(__name__)

DOMAIN: Final = "sandisolar_modbus_rtu"
PLATFORMS: Final = ["sensor", "switch", "number"]

SANDISOLAR_LOGO = "🟢 SANDISOLAR"


# ---------------------------------------------------------------------------
# SETUP ENTRY
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SANDISOLAR Modbus RTU from a config entry."""

    _LOGGER.debug("Setting up %s Modbus RTU integration", SANDISOLAR_LOGO)

    hub = SandiSolarModbusHub(hass, entry)

    try:
        await hub.async_init()
    except Exception as err:
        _LOGGER.error("Failed to initialize SANDISOLAR hub: %s", err)
        raise ConfigEntryNotReady(f"Cannot connect to SANDISOLAR device: {err}") from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = hub

    # Register service: dump registers
    async def handle_dump_registers(call: ServiceCall) -> None:
        dump = await hub.dump_all_registers()
        _LOGGER.warning("SERVICE DUMP REGISTERS:\n%s", dump)

    hass.services.async_register(DOMAIN, "dump_registers", handle_dump_registers)

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("%s Modbus RTU integration setup complete", SANDISOLAR_LOGO)
    return True


# ---------------------------------------------------------------------------
# UNLOAD ENTRY
# ---------------------------------------------------------------------------

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    hub: SandiSolarModbusHub = hass.data[DOMAIN][entry.entry_id]
    await hub.close()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
