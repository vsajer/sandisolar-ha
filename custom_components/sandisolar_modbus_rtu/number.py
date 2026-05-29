import logging
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfElectricCurrent, PERCENTAGE, UnitOfElectricPotential, UnitOfPower

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

        # -------------------------------------------------------------
        # AC Charge Current Limit (0.1 A units)
        # -------------------------------------------------------------
        SandiSolarScaledNumber(
            hub,
            "ac_charge_current_limit",
            "AC Charge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            0,
            50,
            10,  # scale factor (0.1A → ×10)
            "mdi:current-ac",
        ),

        # -------------------------------------------------------------
        # SecEPS thresholds
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_soc",
            "SecEPS ON SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:toggle-switch",
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_off_soc",
            "SecEPS OFF SOC",
            PERCENTAGE,
            0,
            100,
            "mdi:toggle-switch-off",
        ),
        SandiSolarScaledNumber(
            hub,
            "sec_eps_on_vbat",
            "SecEPS ON Voltage",
            UnitOfElectricPotential.VOLT,
            40,
            60,
            10,  # 0.1V → ×10
            "mdi:home-lightning-bolt",
        ),
        SandiSolarScaledNumber(
            hub,
            "sec_eps_off_vbat",
            "SecEPS OFF Voltage",
            UnitOfElectricPotential.VOLT,
            40,
            60,
            10,
            "mdi:home-lightning-bolt",
        ),

        # -------------------------------------------------------------
        # SecEPS ON PV Power Min (10W units)
        # -------------------------------------------------------------
        SandiSolarScaledNumber(
            hub,
            "sec_eps_on_pv_power_min",
            "SecEPS ON PV Power Min",
            UnitOfPower.WATT,
            0,
            10000,
            0.1,  # 10W → value/10
            "mdi:solar-power",
        ),
    ]

    async_add_entities(entities)


# =====================================================================
# BASIC NUMBER (no scaling)
# =====================================================================

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
        val = await self._hub.read_holding_register(self._key)
        if val is not None:
            self._state = int(val)

    async def async_set_native_value(self, value: float):
        int_value = int(value)
        await self._hub.write_holding_register(self._key, int_value)
        self._state = int_value
        self.async_write_ha_state()


# =====================================================================
# SCALED NUMBER (for 0.1A, 0.1V, 10W registers)
# =====================================================================

class SandiSolarScaledNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = "slider"

    def __init__(self, hub, key, name, unit, min_value, max_value, scale, icon):
        self._hub = hub
        self._key = key
        self._scale = scale

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
        val = await self._hub.read_holding_register(self._key)
        if val is not None:
            self._state = val / self._scale

    async def async_set_native_value(self, value: float):
        raw = int(value * self._scale)
        await self._hub.write_holding_register(self._key, raw)
        self._state = value
        self.async_write_ha_state()
