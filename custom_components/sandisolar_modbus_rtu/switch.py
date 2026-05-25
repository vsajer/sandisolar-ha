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
from .modbus_map import HOLDING_REGISTERS, RegisterDefinition

_LOGGER: logging.Logger = logging.getLogger(__name__)


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
        if reg_def.writable and reg_def.min_value == 0 and reg_def.max_value == 1:
            entities.append(SandiSolarSwitch(hub, reg_def, key, use_czech))

    async_add_entities(entities)


class SandiSolarSwitch(SandiSolarEntity, SwitchEntity):
    """Representation of a writable ON/OFF register as a switch."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def: RegisterDefinition,
        key: str,
        use_czech: bool = False,
    ) -> None:
        """Initialize the switch."""
        super().__init__(hub, reg_def, use_czech)
        self._key = key
        self._attr_icon = reg_def.icon
        self._attr_is_on = False

    async def async_update(self) -> None:
        """Update switch state."""
        try:
            value = await self._hub.read_holding_register(self._key)
            if value is not None:
                self._attr_is_on = bool(int(value))
                self._hub._cache[self._key] = value
                self._attr_available = True
            else:
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Error updating switch %s: %s", self.name, err)
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            success = await self._hub.write_holding_register(self._key, 1)
            if success:
                self._attr_is_on = True
                self._hub._cache[self._key] = 1
        except Exception as err:
            _LOGGER.error("Error turning ON %s: %s", self.name, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            success = await self._hub.write_holding_register(self._key, 0)
            if success:
                self._attr_is_on = False
                self._hub._cache[self._key] = 0
        except Exception as err:
            _LOGGER.error("Error turning OFF %s: %s", self.name, err)

    @property
    def extra_state_attributes(self):
        """Return additional attributes for this switch."""
        return self._hub.get_attributes_for(self._key)
