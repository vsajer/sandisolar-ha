import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import (
    UnitOfElectricCurrent,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfPower,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

    entities = [
        # -------------------------------------------------------------
        # Charge / Discharge Limits (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "charge_limit",
            "Charge Limit",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-charging",
        ),
        SandiSolarNumber(
            hub,
            "discharge_limit",
            "Discharge Limit",
            PERCENTAGE,
            0,
            100,
            1,
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
            1,
            "mdi:battery-heart",
        ),

        # -------------------------------------------------------------
        # SOC Limits (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "on_grid_discharge_soc",
            "On-Grid Discharge SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:transmission-tower",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_discharge_soc",
            "Off-Grid Discharge SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:home-lightning-bolt",
        ),
        SandiSolarNumber(
            hub,
            "on_grid_recovery_soc",
            "On-Grid Recovery SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-sync",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_recovery_soc",
            "Off-Grid Recovery SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-sync",
        ),

        # -------------------------------------------------------------
        # AC Charge Current Limit
        # scale řeší modbus_map.py: RegisterDef(189, 0.1)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "ac_charge_current_limit",
            "AC Charge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            0,
            100,
            0.1,
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
            1,
            "mdi:toggle-switch",
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_off_soc",
            "SecEPS OFF SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:toggle-switch-off",
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_on_vbat",
            "SecEPS ON Voltage",
            UnitOfElectricPotential.VOLT,
            40,
            60,
            0.1,
            "mdi:home-lightning-bolt",
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_off_vbat",
            "SecEPS OFF Voltage",
            UnitOfElectricPotential.VOLT,
            40,
            60,
            0.1,
            "mdi:home-lightning-bolt",
        ),

        # -------------------------------------------------------------
        # SecEPS ON PV Power Min
        # scale řeší modbus_map.py: RegisterDef(223, 10)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_pv_power_min",
            "SecEPS ON PV Power Min",
            UnitOfPower.WATT,
            0,
            10000,
            10,
            "mdi:solar-power",
        ),
    ]

    async_add_entities(entities)


class SandiSolarNumber(NumberEntity):
    """Number entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True
    _attr_mode = "slider"

    def __init__(
        self,
        hub,
        key,
        name,
        unit,
        min_value,
        max_value,
        step,
        icon,
    ):
        self._hub = hub
        self._key = key

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_number_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_icon = icon
        self._attr_available = True

        self._state = None

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU",
        }

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        val = await self._hub.read_holding_register(self._key)

        if val is None:
            self._attr_available = False
            self._state = None
            return

        self._attr_available = True

        if isinstance(val, float):
            self._state = round(val, 3)
        else:
            self._state = int(val)

    async def async_set_native_value(self, value: float):
        ok = await self._hub.write_holding_register(self._key, value)

        if ok:
            self._state = value
            self._attr_available = True
        else:
            self._attr_available = False

        self.async_write_ha_state()
