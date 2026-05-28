from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .hub import SandiSolarModbusHub
from .const import DOMAIN

PLATFORMS = ["sensor", "switch", "number", "select"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = SandiSolarModbusHub(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    await hub.async_init()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.close()
    return unload_ok
