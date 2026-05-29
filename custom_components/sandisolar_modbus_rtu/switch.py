import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

    entities = [
        SandiSolarSwitch(
            hub,
            "inverter_on_off",
            "Inverter On/Off",
            "mdi:power",
        ),
        SandiSolarSwitch(
            hub,
            "ac_charge_enable",
            "AC Charge Enable",
            "mdi:transmission-tower-import",
        ),
        SandiSolarSwitch(
            hub,
            "eps_enable",
            "EPS Enable",
            "mdi:home-lightning-bolt",
        ),
        SandiSolarSwitch(
            hub,
            "bypass_enable",
            "Bypass Mode",
            "mdi:transfer",
        ),
        SandiSolarSwitch(
            hub,
            "ups_enable",
            "UPS Mode",
            "mdi:car-battery",
        ),
        SandiSolarSwitch(
            hub,
            "beeper_on_off",
            "Beeper",
            "mdi:volume-high",
        ),
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
    def is_on(self):
        if self._state is None:
            return None

        return bool(self._state)

    async def async_update(self):
        """Read holding register value."""
        val = await self._hub.read_holding_register(self._key)

        if val is None:
            _LOGGER.warning(
                "SANDISOLAR: Switch %s is unavailable",
                self._key,
            )
            self._attr_available = False
            self._state = None
            return

        self._attr_available = True
        self._state = bool(int(val))

    async def async_turn_on(self, **kwargs):
        """Turn switch on."""
        ok = await self._hub.write_holding_register(self._key, 1)

        if ok:
            self._state = True
            self._attr_available = True
            self.async_write_ha_state()
        else:
            self._attr_available = False
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn switch off."""
        ok = await self._hub.write_holding_register(self._key, 0)

        if ok:
            self._state = False
            self._attr_available = True
            self.async_write_ha_state()
        else:
            self._attr_available = False
            self.async_write_ha_state()
