from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .hub import SandiSolarModbusHub
from .const import DOMAIN, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Load config
    port = entry.data["port"]
    baudrate = entry.data["baudrate"]
    slave = entry.data["slave"]

    # Create hub
    hub = SandiSolarModbusHub(hass, port, baudrate, slave)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    # Connect Modbus
    await hub.connect()

    # Load platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        if hasattr(hub, "close"):
            await hub.close()

    return unload_ok
