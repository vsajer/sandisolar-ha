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
        """Initialize the entity."""
        self._hub = hub
        self._reg_def = reg_def
        self._use_czech = use_czech

        self._attr_should_poll = True
        self._attr_available = True
        self._attr_icon = reg_def.icon

        # Optional: service entities (limits, switches) can be marked as config
        if reg_def.writable:
            self._attr_entity_category = EntityCategory.CONFIG

    # ----------------------------------------------------------------------
    # DEVICE INFO
    # ----------------------------------------------------------------------
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for grouping entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, "sandisolar_main_device")},
            name=SANDISOLAR_DEVICE_NAME,
            manufacturer="SANDISOLAR",
            model="SD-PRO-EU",
            hw_version="Modbus RTU",
            sw_version="1.0.0",
        )

    # ----------------------------------------------------------------------
    # ENTITY NAME
    # ----------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Return entity name."""
        return self._reg_def.name_cs if self._use_czech else self._reg_def.name_en

    # ----------------------------------------------------------------------
    # UNIQUE ID
    # ----------------------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        # Use key instead of address → stable across firmware changes
        return f"sandisolar_{self._reg_def.key}"

    # ----------------------------------------------------------------------
    # ICON
    # ----------------------------------------------------------------------
    @property
    def icon(self) -> str | None:
        """Return entity icon."""
        return self._reg_def.icon

    # ----------------------------------------------------------------------
    # ATTRIBUTES (shared for all entity types)
    # ----------------------------------------------------------------------
    @property
    def extra_state_attributes(self):
        """Return additional attributes from hub cache."""
        return self._hub.get_attributes_for(self._reg_def.key)
