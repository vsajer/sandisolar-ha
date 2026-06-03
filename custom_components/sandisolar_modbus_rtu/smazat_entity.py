"""Base entity for SANDISOLAR Modbus RTU integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import EntityCategory

from .hub import SandiSolarModbusHub
from .modbus_map import RegisterDefinition

DOMAIN = "sandisolar_modbus_rtu"
SANDISOLAR_DEVICE_NAME = "🟢 SANDISOLAR SD-PRO-EU"


class SandiSolarEntity(Entity):
    """Base entity for all SANDISOLAR Modbus entities."""

    def __init__(
        self,
        hub: SandiSolarModbusHub,
        reg_def: RegisterDefinition,
        use_czech: bool = False,
    ) -> None:
        self._hub = hub
        self._reg_def = reg_def
        self._use_czech = use_czech

        self._attr_should_poll = True
        self._attr_available = True
        self._attr_icon = reg_def.icon

        if reg_def.writable:
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "sandisolar_main_device")},
            name=SANDISOLAR_DEVICE_NAME,
            manufacturer="SANDISOLAR",
            model="SD-PRO-EU",
            hw_version="Modbus RTU",
            sw_version="1.0.0",
        )

    @property
    def name(self) -> str:
        return self._reg_def.name_cs if self._use_czech else self._reg_def.name_en

    @property
    def unique_id(self) -> str:
        return f"sandisolar_{self._reg_def.key}"

    @property
    def icon(self) -> str | None:
        return self._reg_def.icon

    @property
    def extra_state_attributes(self):
        return {}
