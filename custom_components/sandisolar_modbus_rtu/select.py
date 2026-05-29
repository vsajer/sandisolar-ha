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

GEN_PORT_WORK_MODE_OPTIONS = {
    "0 – Default": 0,
    "1 – Generator Enable": 1,
    "2 – Generator Force": 2,
    "3 – SmartLoad Output": 3,
    "4 – On Grid always on": 4,
    "5 – Off Grid immediately off": 5,
    "6 – AC Couple on SecEPS side": 6,
}

# ---------------------------------------------------------
# LCD BITMASK OPTIONS (reg 201)
# ---------------------------------------------------------

LCD_OPTIONS = {
    "Default (Auto‑Off + Touch Wake‑Up)": 1 | 8,   # 9
    "LCD Always‑On": 2,
    "LCD Sleep Mode": 4,
    "Touch Wake‑Up only": 8,
    "All Off": 0,
    "All On": 1 | 2 | 4 | 8,  # 15
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
        SandiSolarSelect(
            hub,
            "gen_port_work_mode",
            "GEN Port Work Mode",
            GEN_PORT_WORK_MODE_OPTIONS,
            "mdi:dip-switch"
        ),
        SandiSolarSelect(
            hub,
            "lcd_settings",
            "LCD Settings",
            LCD_OPTIONS,
            "mdi:monitor"
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

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU 6.5K",
        }

    @property
    def current_option(self):
        if self._state is None:
            return None

        for label, value in self._mapping.items():
            if value == self._state:
                return label

        return None

    async def async_update(self):
        """Read holding register value."""
        val = await self._hub.read_holding_register(self._key)
        if val is not None:
            self._state = int(val)

    async def async_select_option(self, option: str):
        """Write new value to holding register."""
        value = self._mapping[option]
        await self._hub.write_holding_register(self._key, value)
        self._state = value
        self.async_write_ha_state()
