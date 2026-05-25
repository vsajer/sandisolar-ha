"""Sensor platform for SANDISOLAR Modbus RTU integration."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import SandiSolarEntity
from .hub import SandiSolarModbusHub
from .modbus_map import INPUT_REGISTERS

_LOGGER: logging.Logger = logging.getLogger(__name__)

UNIT_MAPPING = {
    "V": UnitOfElectricPotential.VOLT,
    "A": UnitOfElectricCurrent.AMPERE,
    "W": UnitOfPower.WATT,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "Hz": UnitOfFrequency.HERTZ,
    "°C": UnitOfTemperature.CELSIUS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    hub: SandiSolarModbusHub = hass.data[DOMAIN][entry.entry_id]

    entities = []
    use_czech = entry.options.get("use_czech_names", False)

    for key, reg_def in INPUT_REGISTERS.items():
        entities.append(SandiSolarSensor(hub, reg_def, key, use_czech))

    async_add_entities(entities)


class SandiSolarSensor(SandiSolarEntity, SensorEntity):
    """Representation of a SANDISOLAR sensor."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def,
        key: str,
        use_czech: bool = False,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hub, reg_def, use_czech)
        self._key = key
        self._attr_native_unit_of_measurement = UNIT_MAPPING.get(reg_def.unit) if reg_def.unit else None

        if reg_def.unit in ["kWh", "W", "A", "V"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None

    async def async_update(self) -> None:
        """Update the entity."""
        try:
            value = await self._hub.read_input_register(self._key)
            if value is not None:
                self._attr_native_value = value
                self._hub._cache[self._key] = value
                self._attr_available = True
            else:
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Error updating sensor %s: %s", self.name, err)
            self._attr_available = False

    @property
    def extra_state_attributes(self):
        """Return additional attributes for this sensor."""
        return self._hub.get_attributes_for(self._key)
