import logging
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfElectricCurrent, PERCENTAGE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # -------------------------------------------------------------
        # Charge / Discharge Current Limits (A)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "charge_limit",
            "Charge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            0,
            100,
            "mdi:battery-charging",
        ),
        SandiSolarNumber(
            hub,
            "discharge_limit",
            "Discharge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            0,
            100,
            "mdi:battery-minus",
        ),

        # -------------------------------------------------------------
        # End of Charge SOC (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "end_of_charge_soc",
            "End of Charge SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:battery-heart",
        ),

        # -------------------------------------------------------------
        # SOC Limits (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "on_grid_discharge_soc",
            "On‑Grid Discharge SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:transmission-tower",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_discharge_soc",
            "Off‑Grid Discharge SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:home-lightning-bolt",
        ),
        SandiSolarNumber(
            hub,
            "on_grid_recovery_soc",
            "On‑Grid Recovery SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:battery-sync",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_recovery_soc",
            "Off‑Grid Recovery SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:battery-sync",
        ),
    ]

    async_add_entities(entities)


class SandiSolarNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = "slider"

    def __init__(self, hub, key, name, unit, min_value, max_value, icon):
        self._hub = hub
        self._key = key

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_number_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_icon = icon

        self._state = None

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
        return self._state

    async def async_update(self):
        """Read holding register value."""
        val = await self._hub.read_holding_register(self._key)
        if val is not None:
            self._state = int(val)

    async def async_set_native_value(self, value: float):
        """Write new value to holding register."""
        int_value = int(value)
        await self._hub.write_holding_register(self._key, int_value)
        self._state = int_value
        self.async_write_ha_state()
