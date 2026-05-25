"""Switch platform for SANDISOLAR Modbus RTU integration."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import SandiSolarEntity
from .hub import SandiSolarModbusHub
from .modbus_map import HOLDING_REGISTERS

_LOGGER: logging.Logger = logging.getLogger(__name__)

SWITCH_REGISTERS = {
    "inverter_onoff",
    "ac_charge_enable",
    "battery_discharge_enable",
    "grid_feed_in_enable",
    "load_enable",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    hub: SandiSolarModbusHub = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    use_czech = entry.options.get("use_czech_names", False)
    
    for key, reg_def in HOLDING_REGISTERS.items():
        if key in SWITCH_REGISTERS:
            entities.append(SandiSolarSwitch(hub, reg_def, key, use_czech))
    
    async_add_entities(entities)


class SandiSolarSwitch(SandiSolarEntity, SwitchEntity):
    """Representation of a SANDISOLAR switch."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def,
        key: str,
        use_czech: bool = False,
    ) -> None:
        """Initialize the switch."""
        super().__init__(hub, reg_def, use_czech)
        self._key = key
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        result = await self._hub.write_holding_register(self._key, 1)
        if result:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        result = await self._hub.write_holding_register(self._key, 0)
        if result:
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the entity."""
        try:
            value = await self._hub.read_holding_register(self._key)
            if value is not None:
                self._attr_is_on = bool(value)
            else:
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Error updating switch %s: %s", self.name, err)
            self._attr_available = False