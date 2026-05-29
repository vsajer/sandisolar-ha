from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .hub import SandiSolarModbusHub
from .coordinator import SandiSolarCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Setup SANDISOLAR integration from UI."""

    hub = SandiSolarModbusHub(hass, entry)
    await hub.async_init()

    coordinator = SandiSolarCoordinator(hass, hub)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)

        hub = data["hub"]
        await hub.close()

    return unload_ok
