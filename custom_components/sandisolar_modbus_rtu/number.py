import logging
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfElectricCurrent

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SandiSolarNumber(
            hub,
            300,   # Modbus register
            "Charge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            0,
            200,
            "mdi:battery-charging",
        ),
        SandiSolarNumber(
            hub,
            301,   # Modbus register
            "Discharge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            0,
            200,
            "mdi:battery-minus",
        ),
    ]

    async_add_entities(entities)


class SandiSolarNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = "slider"

    def __init__(self, hub, register, name, unit, min_value, max_value, icon):
        self._hub = hub
        self._register = register

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_number_{register}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
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
    def native_value(self):
        return self._hub._cache.get(self._register)

    async def async_update(self):
        await self._hub.read_holding_register(self._register)

    async def async_set_native_value(self, value: float):
        await self._hub.write_holding_register(self._register, int(value))
