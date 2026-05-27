import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SandiSolarSwitch(hub, 200, "Inverter On/Off", "mdi:power"),
        SandiSolarSwitch(hub, 210, "AC Charge Enable", "mdi:transmission-tower"),
    ]

    async_add_entities(entities)


class SandiSolarSwitch(SwitchEntity):
    """Switch entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True

    def __init__(self, hub, register, name, icon):
        self._hub = hub
        self._register = register
        self._attr_name = name
        self._attr_unique_id = f"sandisolar_switch_{register}"
        self._attr_icon = icon

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU 6.5K",
        }

    @property
    def is_on(self):
        val = self._hub._cache.get(self._register)
        return bool(val) if val is not None else False

    async def async_update(self):
        await self._hub.read_holding_register(self._register)

    async def async_turn_on(self):
        await self._hub.write_holding_register(self._register, 1)

    async def async_turn_off(self):
        await self._hub.write_holding_register(self._register, 0)
