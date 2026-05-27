import logging
from homeassistant.components.select import SelectEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------
# OPTIONS MAPPING (label → register value)
# ---------------------------------------------------------

SOURCE_PRIORITY_OPTIONS = {
    "SOL – Solar First": 0,
    "UTI – Grid First": 1,
    "SBU – Solar → Battery → Grid": 2,
    "OSO – On-Grid Solar Output": 10,
}

CHARGE_PRIORITY_OPTIONS = {
    "CSO – Charge Solar Only": 0,
    "SNU – Solar → Utility": 1,
    "OSO – Utility → Solar": 2,
}


# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SandiSolarSelect(
            hub,
            400,   # Modbus register
            "Source Priority",
            SOURCE_PRIORITY_OPTIONS,
            "mdi:solar-power"
        ),
        SandiSolarSelect(
            hub,
            401,   # Modbus register
            "Charge Priority",
            CHARGE_PRIORITY_OPTIONS,
            "mdi:battery-charging"
        ),
    ]

    async_add_entities(entities)


# ---------------------------------------------------------
# ENTITY CLASS
# ---------------------------------------------------------

class SandiSolarSelect(SelectEntity):
    """Select entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True

    def __init__(self, hub, register, name, mapping, icon):
        self._hub = hub
        self._register = register
        self._mapping = mapping

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_select_{register}"
        self._attr_options = list(mapping.keys())
        self._attr_icon = icon

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
    # CURRENT OPTION
    # -----------------------------------------------------

    @property
    def current_option(self):
        raw = self._hub._cache.get(self._register)
        if raw is None:
            return None

        for label, value in self._mapping.items():
            if value == raw:
                return label

        return None

    # -----------------------------------------------------
    # UPDATE (READ)
    # -----------------------------------------------------

    async def async_update(self):
        await self._hub.read_holding_register(self._register)

    # -----------------------------------------------------
    # WRITE
    # -----------------------------------------------------

    async def async_select_option(self, option: str):
        value = self._mapping[option]
        await self._hub.write_holding_register(self._register, value)
