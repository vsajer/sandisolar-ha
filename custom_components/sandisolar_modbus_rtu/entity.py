"""Base entity for SANDISOLAR Modbus RTU integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .hub import SandiSolarModbusHub
from .modbus_map import RegisterDefinition

DOMAIN = "sandisolar_modbus_rtu"
SANDISOLAR_DEVICE_NAME = "🟢 SANDISOLAR SD-PRO-EU"


class SandiSolarEntity(Entity):
    """Base entity for SANDISOLAR devices."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def: RegisterDefinition,
        use_czech: bool = False,
    ) -> None:
        """Initialize the entity."""
        self._hub = hub
        self._reg_def = reg_def
        self._use_czech = use_czech
        self._attr_should_poll = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, "sandisolar")},
            name=SANDISOLAR_DEVICE_NAME,
            manufacturer="SANDISOLAR",
            model="SD-PRO-EU",
            hw_version="Modbus RTU",
            sw_version="1.0.0",
        )

    @property
    def name(self) -> str:
        """Return entity name."""
        if self._use_czech:
            return self._reg_def.name_cs
        return self._reg_def.name_en

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"sandisolar_{self._reg_def.address}"

    @property
    def icon(self) -> str | None:
        """Return entity icon."""
        return self._reg_def.icon