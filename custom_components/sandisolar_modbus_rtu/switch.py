import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SYSTEM_FLAGS_REGISTER = "lcd_settings_bitmask"


SYSTEM_FLAG_SWITCHES = [
    {
        "key": "eco_mode",
        "name": "Eco Mode",
        "bit": 0,
        "icon": "mdi:leaf",
    },
    {
        "key": "overload_restart",
        "name": "Overload Auto Restart",
        "bit": 1,
        "icon": "mdi:restart-alert",
    },
    {
        "key": "overtemp_restart",
        "name": "Over Temperature Auto Restart",
        "bit": 2,
        "icon": "mdi:thermometer-alert",
    },
    {
        "key": "input_change_reminder",
        "name": "Input Change Reminder",
        "bit": 3,
        "icon": "mdi:bell-alert",
    },
    {
        "key": "split_phase_output",
        "name": "Split Phase Output",
        "bit": 4,
        "icon": "mdi:sine-wave",
    },
    {
        "key": "generator_auto_input",
        "name": "Generator Auto Input",
        "bit": 5,
        "icon": "mdi:engine",
    },
    {
        "key": "dual_channel_load",
        "name": "Dual Channel Load",
        "bit": 6,
        "icon": "mdi:electric-switch",
    },
    {
        "key": "grid_feedback",
        "name": "Grid Feedback",
        "bit": 7,
        "icon": "mdi:transmission-tower-export",
    },
]


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

    entities = [
        SandiSolarBitmaskSwitch(
            hub=hub,
            register_key=SYSTEM_FLAGS_REGISTER,
            key=item["key"],
            name=item["name"],
            bit=item["bit"],
            icon=item["icon"],
        )
        for item in SYSTEM_FLAG_SWITCHES
    ]

    async_add_entities(entities)


class SandiSolarBitmaskSwitch(SwitchEntity):
    """Switch entity for one bit inside SANDISOLAR bitmask register."""

    _attr_has_entity_name = True

    def __init__(self, hub, register_key, key, name, bit, icon):
        self._hub = hub
        self._register_key = register_key
        self._key = key
        self._bit = bit
        self._mask = 1 << bit

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_switch_{register_key}_{key}"
        self._attr_icon = icon
        self._attr_available = True

        self._raw_value = None

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU",
        }

    @property
    def is_on(self):
        if self._raw_value is None:
            return None

        return bool(int(self._raw_value) & self._mask)

    async def async_update(self):
        val = await self._hub.read_holding_register(self._register_key)

        if val is None:
            self._attr_available = False
            self._raw_value = None
            return

        self._attr_available = True
        self._raw_value = int(val)

    async def async_turn_on(self, **kwargs):
        await self._set_bit(True)

    async def async_turn_off(self, **kwargs):
        await self._set_bit(False)

    async def _set_bit(self, enabled: bool):
        current_raw = await self._hub.read_holding_register(self._register_key)

        if current_raw is None:
            _LOGGER.error(
                "SANDISOLAR: Cannot read bitmask register %s before write",
                self._register_key,
            )
            self._attr_available = False
            self.async_write_ha_state()
            return

        current_raw = int(current_raw)

        if enabled:
            new_value = current_raw | self._mask
        else:
            new_value = current_raw & ~self._mask

        _LOGGER.debug(
            "SANDISOLAR: Bitmask write %s bit=%s enabled=%s current=%s new=%s",
            self._register_key,
            self._bit,
            enabled,
            current_raw,
            new_value,
        )

        ok = await self._hub.write_holding_register(
            self._register_key,
            new_value,
        )

        if ok:
            self._raw_value = new_value
            self._attr_available = True
        else:
            self._attr_available = False

        self.async_write_ha_state()
