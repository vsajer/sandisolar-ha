import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # -------------------------------------------------------------
        # Core inverter switches (existují v HOLDING_REGISTERS)
        # -------------------------------------------------------------
        SandiSolarSwitch(hub, "inverter_on_off", "Inverter On/Off", "mdi:power"),
        SandiSolarSwitch(hub, "ac_charge_enable", "AC Charge Enable", "mdi:transmission-tower"),
        SandiSolarSwitch(hub, "eps_enable", "EPS Enable", "mdi:home-lightning-bolt"),
        SandiSolarSwitch(hub, "bypass_enable", "Bypass Mode", "mdi:transfer"),
        SandiSolarSwitch(hub, "ups_enable", "UPS Mode", "mdi:car-battery"),

        # -------------------------------------------------------------
        # Additional binary features (NEEXISTUJÍ, ale zachováváme je)
        # -------------------------------------------------------------
        SandiSolarSwitch(hub, "beeper_on_off", "Beeper", "mdi:volume-high"),
        SandiSolarSwitch(hub, "grid_charge_enable", "Grid Charge Enable", "mdi:transmission-tower-import"),
        SandiSolarSwitch(hub, "pv_wakeup_enable", "PV Wake‑Up Enable", "mdi:weather-sunny-alert"),
    ]

    async_add_entities(entities)


class SandiSolarSwitch(SwitchEntity):
    """Switch entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True

    def __init__(self, hub, key, name, icon):
        self._hub = hub
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sandisolar_switch_{key}"
        self._attr_icon = icon
        self._state = None

    # -----------------------------------------------------
    # DEVICE INFO
    # -----------------------------------------------------

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU 6.5K",
        }

    # -----------------------------------------------------
    # STATE
    # -----------------------------------------------------

    @property
    def is_on(self):
        return bool(self._state)

    # -----------------------------------------------------
    # UPDATE (READ)
    # -----------------------------------------------------

    async def async_update(self):
        """Read the holding register value."""
        try:
            val = await self._hub.read_holding_register(self._key)
        except Exception as e:
            _LOGGER.error("SANDISOLAR: Switch read error for %s: %s", self._key, e)
            self._state = False
            return

        if val is None:
            # Register does not exist → keep switch but disable it
            self._state = False
        else:
            self._state = bool(val)

    # -----------------------------------------------------
    # WRITE
    # -----------------------------------------------------

    async def async_turn_on(self):
        ok = await self._hub.write_holding_register(self._key, 1)
        if ok:
            self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        ok = await self._hub.write_holding_register(self._key, 0)
        if ok:
            self._state = False
        self.async_write_ha_state()
