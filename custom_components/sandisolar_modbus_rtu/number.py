"""Number platform for SANDISOLAR Modbus RTU integration."""

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import SandiSolarEntity
from .hub import SandiSolarModbusHub
from .modbus_map import HOLDING_REGISTERS

_LOGGER: logging.Logger = logging.getLogger(__name__)

# Registers that should be numbers (with min/max)
NUMBER_REGISTERS = {
    "ac_charge_soc_limit",
    "ac_charge_current",
    "battery_discharge_soc_limit",
    "battery_discharge_current",
    "grid_feed_in_power_limit",
    "battery_charge_power_limit",
    "battery_discharge_power_limit",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    hub: SandiSolarModbusHub = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    use_czech = entry.options.get("use_czech_names", False)
    
    for key, reg_def in HOLDING_REGISTERS.items():
        if key in NUMBER_REGISTERS and reg_def.writable:
            entities.append(SandiSolarNumber(hub, reg_def, key, use_czech))
    
    async_add_entities(entities)


class SandiSolarNumber(SandiSolarEntity, NumberEntity):
    """Representation of a SANDISOLAR number."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def,
        key: str,
        use_czech: bool = False,
    ) -> None:
        """Initialize the number."""
        super().__init__(hub, reg_def, use_czech)
        self._key = key
        self._attr_native_unit_of_measurement = reg_def.unit
        self._attr_native_min_value = reg_def.min_value
        self._attr_native_max_value = reg_def.max_value
        self._attr_native_step = reg_def.scale
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        result = await self._hub.write_holding_register(self._key, value)
        if result:
            self._attr_native_value = value
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the entity."""
        try:
            value = await self._hub.read_holding_register(self._key)
            if value is not None:
                self._attr_native_value = value
            else:
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Error updating number %s: %s", self.name, err)
            self._attr_available = False
