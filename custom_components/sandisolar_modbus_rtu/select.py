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
            "source_priority",
            "Source Priority",
            SOURCE_PRIORITY_OPTIONS,
            "mdi:solar-power"
        ),
        SandiSolarSelect(
            hub,
            "charge_priority",
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

    def __init__(self, hub, key, name, mapping, icon):
        self._hub = hub
        self._key = key
        self._mapping = mapping

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_select_{key}"
        self._attr_options = list(mapping.keys())
        self._attr_icon = icon

        self._state = None

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
        if self._state is None:
            return None

        for label, value in self._mapping.items():
            if value == self._state:
                return label

        return None

    # -----------------------------------------------------
    # UPDATE (READ)
    # -----------------------------------------------------

    async def async_update(self):
        """Read holding register value."""
        val = await self._hub.read_holding_register(self._key)
        if val is not None:
            self._state = int(val)

    # -----------------------------------------------------
    # WRITE
    # -----------------------------------------------------

    async def async_select_option(self, option: str):
        """Write new value to holding register."""
        value = self._mapping[option]
        await self._hub.write_holding_register(self._key, value)
        self._state = value
        self.async_write_ha_state()
