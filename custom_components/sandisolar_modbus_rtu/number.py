"""Number platform for SANDISOLAR Modbus RTU integration."""

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import SandiSolarEntity
from .hub import SandiSolarModbusHub
from .modbus_map import HOLDING_REGISTERS, RegisterDefinition

_LOGGER: logging.Logger = logging.getLogger(__name__)


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
        # Only registers with min/max values → NumberEntity
        if reg_def.writable and reg_def.min_value is not None and reg_def.max_value is not None:
            entities.append(SandiSolarNumber(hub, reg_def, key, use_czech))

    async_add_entities(entities)


class SandiSolarNumber(SandiSolarEntity, NumberEntity):
    """Representation of a writable numeric Modbus register."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def: RegisterDefinition,
        key: str,
        use_czech: bool = False,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(hub, reg_def, use_czech)
        self._key = key

        self._attr_icon = reg_def.icon
        self._attr_native_min_value = reg_def.min_value
        self._attr_native_max_value = reg_def.max_value
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = reg_def.unit
        self._attr_mode = NumberMode.BOX

        self._attr_native_value = None

    async def async_update(self) -> None:
        """Update the entity."""
        try:
            value = await self._hub.read_holding_register(self._key)
            if value is not None:
                self._attr_native_value = value
                self._hub._cache[self._key] = value
                self._attr_available = True
            else:
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Error updating number %s: %s", self.name, err)
            self._attr_available = False

    async def async_set_native_value(self, value: float) -> None:
        """Write a new value to the register."""
        try:
            success = await self._hub.write_holding_register(self._key, value)
            if success:
                self._attr_native_value = value
                self._hub._cache[self._key] = value
        except Exception as err:
            _LOGGER.error("Error writing number %s: %s", self.name, err)

    @property
    def extra_state_attributes(self):
        """Return additional attributes for this number entity."""
        return self._hub.get_attributes_for(self._key)
