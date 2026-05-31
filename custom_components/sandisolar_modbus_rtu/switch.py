import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SYSTEM_FLAGS_REGISTER = "lcd_settings_bitmask"


SYSTEM_FLAG_SWITCHES = [
    {
        "key": "eco_mode",
        "name": "Eco Mode",
        "bit": 0,
        "icon": "mdi:leaf",
        "advanced": False,
    },
    {
        "key": "overload_restart",
        "name": "Overload Auto Restart",
        "bit": 1,
        "icon": "mdi:restart-alert",
        "advanced": False,
    },
    {
        "key": "overtemp_restart",
        "name": "Over Temperature Auto Restart",
        "bit": 2,
        "icon": "mdi:thermometer-alert",
        "advanced": False,
    },
    {
        "key": "input_change_alert",
        "name": "Input Change Alert",
        "bit": 3,
        "icon": "mdi:bell-alert",
        "advanced": False,
    },
    {
        "key": "split_phase_output",
        "name": "ADV - Split Phase Output",
        "bit": 4,
        "icon": "mdi:alert-circle-outline",
        "advanced": True,
    },
    {
        "key": "generator_auto_input",
        "name": "Generator Auto Input",
        "bit": 5,
        "icon": "mdi:engine",
        "advanced": False,
    },
    {
        "key": "sec_eps_output",
        "name": "SecEPS Output",
        "bit": 6,
        "icon": "mdi:power-plug",
        "advanced": False,
    },
    {
        "key": "grid_feedback",
        "name": "ADV - Grid Feedback",
        "bit": 7,
        "icon": "mdi:transmission-tower-export",
        "advanced": True,
    },
]


REGISTER_SWITCHES = [
    {
        "key": "inverter_on_off",
        "name": "Inverter Power",
        "icon": "mdi:power",
        "advanced": False,
    },
    {
        "key": "eps_enable",
        "name": "EPS Enable",
        "icon": "mdi:power-plug-battery",
        "advanced": False,
    },
    {
        "key": "bypass_enable",
        "name": "Bypass Enable",
        "icon": "mdi:transit-connection-horizontal",
        "advanced": False,
    },
    {
        "key": "ups_enable",
        "name": "UPS Mode",
        "icon": "mdi:flash",
        "advanced": False,
    },
    {
        "key": "gen_charge_enable",
        "name": "Generator Charging",
        "icon": "mdi:engine",
        "advanced": False,
    },
    {
        "key": "ac_charge_enable",
        "name": "AC Charging",
        "icon": "mdi:battery-charging",
        "advanced": False,
    },
    {
        "key": "beeper_on_off",
        "name": "Beeper",
        "icon": "mdi:volume-high",
        "advanced": False,
    },
    {
        "key": "overload_to_bypass",
        "name": "ADV - Overload To Bypass",
        "icon": "mdi:alert-outline",
        "advanced": True,
    },
    {
        "key": "bluetooth_enable",
        "name": "Bluetooth",
        "icon": "mdi:bluetooth",
        "advanced": False,
    },
    {
        "key": "active_overload_enable",
        "name": "ADV - Active Overload Enable",
        "icon": "mdi:alert-circle-outline",
        "advanced": True,
    },
    {
        "key": "island_enable",
        "name": "ADV - Island Mode",
        "icon": "mdi:island",
        "advanced": True,
    },
    {
        "key": "vfrt_enable",
        "name": "ADV - VFRT Enable",
        "icon": "mdi:sine-wave",
        "advanced": True,
    },
    {
        "key": "drms_enable",
        "name": "ADV - DRMS Enable",
        "icon": "mdi:connection",
        "advanced": True,
    },
    {
        "key": "zero_power_output_enable",
        "name": "ADV - Zero Power Output",
        "icon": "mdi:transmission-tower-off",
        "advanced": True,
    },
    {
        "key": "fast_mppt_enable",
        "name": "ADV - Fast MPPT",
        "icon": "mdi:solar-power-variant",
        "advanced": True,
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
            advanced=item.get("advanced", False),
        )
        for item in SYSTEM_FLAG_SWITCHES
    ]

    entities.extend(
        [
            SandiSolarRegisterSwitch(
                hub=hub,
                key=item["key"],
                name=item["name"],
                icon=item["icon"],
                advanced=item.get("advanced", False),
            )
            for item in REGISTER_SWITCHES
        ]
    )

    async_add_entities(entities)


class SandiSolarBitmaskSwitch(SwitchEntity):
    """Switch entity for one bit inside SANDISOLAR bitmask register."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hub,
        register_key,
        key,
        name,
        bit,
        icon,
        advanced=False,
    ):
        self._hub = hub
        self._register_key = register_key
        self._key = key
        self._bit = bit
        self._mask = 1 << bit

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_switch_{register_key}_{key}"
        self._attr_icon = icon
        self._attr_available = True

        if advanced:
            self._attr_entity_category = EntityCategory.CONFIG
            self._attr_entity_registry_enabled_default = False

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

    async def async_added_to_hass(self):
        """Read initial value once when entity is added."""
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self):
        """Read current bitmask value from inverter."""
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

        if not ok:
            _LOGGER.error(
                "SANDISOLAR: Failed to write bitmask register %s bit=%s enabled=%s",
                self._register_key,
                self._bit,
                enabled,
            )
            self._attr_available = False
            self.async_write_ha_state()
            return

        # Okamžitě ukaž nový stav v Home Assistantu.
        # Nečteme hned znovu měnič, ať zbytečně necpeme další dotaz do Modbus fronty.
        self._raw_value = new_value
        self._attr_available = True
        self.async_write_ha_state()


class SandiSolarRegisterSwitch(SwitchEntity):
    """Simple 0/1 holding register switch for SANDISOLAR."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub, key, name, icon, advanced=False):
        self._hub = hub
        self._key = key

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_switch_{key}"
        self._attr_icon = icon
        self._attr_available = True

        if advanced:
            self._attr_entity_category = EntityCategory.CONFIG
            self._attr_entity_registry_enabled_default = False

        self._state = None

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
        if self._state is None:
            return None

        return int(self._state) == 1

    async def async_added_to_hass(self):
        """Read initial value once when entity is added."""
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self):
        """Read current switch value from inverter."""
        val = await self._hub.read_holding_register(self._key)

        if val is None:
            self._attr_available = False
            self._state = None
            return

        self._attr_available = True
        self._state = int(val)

    async def async_turn_on(self, **kwargs):
        await self._write_state(1)

    async def async_turn_off(self, **kwargs):
        await self._write_state(0)

    async def _write_state(self, value: int):
        ok = await self._hub.write_holding_register(self._key, value)

        if not ok:
            _LOGGER.error(
                "SANDISOLAR: Failed to write switch %s=%s",
                self._key,
                value,
            )
            self._attr_available = False
            self.async_write_ha_state()
            return

        # Okamžitě ukaž nový stav v Home Assistantu.
        # Skutečný stav se znovu načte až při startu / reloadu integrace,
        # ne hned po zápisu, aby se nezahltil Modbus.
        self._state = value
        self._attr_available = True
        self.async_write_ha_state()
