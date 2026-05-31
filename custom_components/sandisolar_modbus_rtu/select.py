import logging

from homeassistant.components.select import SelectEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SOURCE_PRIORITY_OPTIONS = {
    "SOL – Solar First": 0,
    "UTI – Grid First": 1,
    "SBU – Solar → Battery → Grid": 2,
    "OSO – On-Grid Solar Output": 10,
}

CHARGE_PRIORITY_OPTIONS = {
    "CSO – Solar Only": 0,
    "SNU – Solar → Utility": 1,
    "OSO – Utility → Solar": 2,
}

GEN_PORT_WORK_MODE_OPTIONS = {
    "0 – Default": 0,
    "1 – Generator Enable": 1,
    "2 – Generator Force": 2,
    "3 – SmartLoad Output": 3,
    "4 – On Grid Always On": 4,
    "5 – Off Grid Immediately Off": 5,
    "6 – AC Couple on SecEPS Side": 6,
}

LCD_OPTIONS = {
    "All Off": 0,
    "LCD Always On": 2,
    "LCD Sleep Mode": 4,
    "Touch Wake-Up Only": 8,
    "Default Auto-Off + Touch Wake-Up": 9,
    "All On": 15,
}


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

    entities = [
        SandiSolarSelect(
            hub,
            "source_priority",
            "Source Priority",
            SOURCE_PRIORITY_OPTIONS,
            "mdi:solar-power",
        ),
        SandiSolarSelect(
            hub,
            "charge_priority",
            "Charge Priority",
            CHARGE_PRIORITY_OPTIONS,
            "mdi:battery-charging",
        ),
        SandiSolarSelect(
            hub,
            "gen_port_work_mode",
            "GEN Port Work Mode",
            GEN_PORT_WORK_MODE_OPTIONS,
            "mdi:dip-switch",
        ),
        SandiSolarSelect(
            hub,
            "lcd_settings_bitmask",
            "LCD Settings",
            LCD_OPTIONS,
            "mdi:monitor",
        ),
    ]

    async_add_entities(entities)


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
        self._attr_available = True

        self._state = None

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU",
        }

    def _get_display_value(self, value: int) -> int:
        """Return value used for matching current select option.

        Register 201 - lcd_settings_bitmask - is a bitmask.
        LCD options use only lower 4 bits.
        Higher bits may contain other enabled functions, for example
        generator, dual load / SecEPS-related flags, grid feedback, etc.

        Without this mask Home Assistant can show the select as unknown.
        """
        if self._key == "lcd_settings_bitmask":
            return value & 0x0F

        return value

    @property
    def current_option(self):
        if self._state is None:
            return None

        display_value = self._get_display_value(int(self._state))

        for label, value in self._mapping.items():
            if value == display_value:
                return label

        return None

    async def async_update(self):
        val = await self._hub.read_holding_register(self._key)

        if val is None:
            self._attr_available = False
            self._state = None
            return

        self._attr_available = True
        self._state = int(val)

    async def async_select_option(self, option: str):
        if option not in self._mapping:
            _LOGGER.error(
                "SANDISOLAR: Invalid select option %s for %s",
                option,
                self._key,
            )
            return

        selected_value = int(self._mapping[option])

        if self._key == "lcd_settings_bitmask":
            current_raw = await self._hub.read_holding_register(self._key)

            if current_raw is None:
                _LOGGER.error(
                    "SANDISOLAR: Cannot read current LCD bitmask before write"
                )
                self._attr_available = False
                self.async_write_ha_state()
                return

            current_raw = int(current_raw)

            # Register 201 is a bitmask.
            # Change only lower 4 bits used by LCD settings.
            # Preserve bits 4-15 so SecEPS / SmartLoad / other flags stay untouched.
            value = (current_raw & ~0x0F) | selected_value

            _LOGGER.debug(
                "SANDISOLAR: LCD bitmask write: current=%s selected=%s new=%s",
                current_raw,
                selected_value,
                value,
            )
        else:
            value = selected_value

        ok = await self._hub.write_holding_register(self._key, value)

        if ok:
            self._state = value
            self._attr_available = True
        else:
            self._attr_available = False

        self.async_write_ha_state()
