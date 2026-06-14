import asyncio
import logging
from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.event import async_track_time_interval

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

# Hodnoty zatím nemáme spolehlivě potvrzené z dokumentace.
# Proto nechávám obecné názvy a raw_value v atributech.
AC_INPUT_TYPE_OPTIONS = {
    "0 – Type 0": 0,
    "1 – Type 1": 1,
    "2 – Type 2": 2,
    "3 – Type 3": 3,
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
            "ac_input_type",
            "ADV - AC Input Type",
            AC_INPUT_TYPE_OPTIONS,
            "mdi:connection",
            advanced=True,
        ),
    ]

    async_add_entities(entities)


class SandiSolarSelect(SelectEntity):
    """Select entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True

    # Polling si řídíme sami přes async_track_time_interval,
    # aby se změny z LCD měniče pravidelně propsaly do HA.
    _attr_should_poll = False

    def __init__(self, hub, key, name, mapping, icon, advanced=False):
        self._hub = hub
        self._key = key
        self._mapping = mapping

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_select_{key}"
        self._attr_options = list(mapping.keys())
        self._attr_icon = icon
        self._attr_available = True
        self._attr_extra_state_attributes = {}

        if advanced:
            self._attr_entity_category = EntityCategory.CONFIG
            self._attr_entity_registry_enabled_default = False

        self._state = None
        self._unknown_option = None

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU",
        }

    @property
    def current_option(self):
        if self._state is None:
            return None

        for label, value in self._mapping.items():
            if int(value) == int(self._state):
                return label

        return self._unknown_option

    async def async_added_to_hass(self):
        """Read initial value and start periodic refresh.

        This is important because select settings can be changed directly
        on the inverter LCD.
        """

        for attempt in range(3):
            await self.async_update()

            if self._state is not None:
                break

            await asyncio.sleep(1 + attempt)

        self.async_write_ha_state()

        interval = int(getattr(self._hub, "update_interval", 10) or 10)

        if interval < 5:
            interval = 5

        async def _periodic_refresh(now):
            await self.async_update()
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                _periodic_refresh,
                timedelta(seconds=interval),
            )
        )

    async def async_update(self):
        """Read current select value from inverter."""
        val = await self._hub.read_holding_register(self._key)

        if val is None:
            cached = self._hub.get_cached(self._key)

            if cached is None:
                self._attr_available = False
                self._attr_extra_state_attributes = {
                    "raw_value": None,
                    "read_error": True,
                }
                return

            val = cached

        self._attr_available = True
        self._state = int(val)

        self._attr_extra_state_attributes = {
            "raw_value": self._state,
            "known_values": dict(self._mapping),
            "read_error": False,
        }

        known_values = [int(v) for v in self._mapping.values()]

        if self._state not in known_values:
            self._unknown_option = f"Unknown ({self._state})"

            if self._unknown_option not in self._attr_options:
                self._attr_options = list(self._mapping.keys()) + [
                    self._unknown_option
                ]
        else:
            self._unknown_option = None
            self._attr_options = list(self._mapping.keys())

    async def async_select_option(self, option: str):
        """Write selected option immediately and update local HA state."""

        # Unknown položka je jen diagnostická, tu nezapisujeme.
        if self._unknown_option is not None and option == self._unknown_option:
            _LOGGER.warning(
                "SANDISOLAR: Refusing to write diagnostic unknown option %s for %s",
                option,
                self._key,
            )
            return

        if option not in self._mapping:
            _LOGGER.error(
                "SANDISOLAR: Invalid select option %s for %s",
                option,
                self._key,
            )
            return

        value = int(self._mapping[option])

        ok = await self._hub.write_holding_register(self._key, value)

        if not ok:
            _LOGGER.error(
                "SANDISOLAR: Failed to write select %s=%s",
                self._key,
                value,
            )
            self._attr_available = False
            self.async_write_ha_state()
            return

        # Po zápisu z HA se pokusíme hned přečíst skutečnou hodnotu z měniče.
        # Když se čtení nepovede, zobrazíme alespoň požadovanou hodnotu.
        real_value = await self._hub.read_holding_register(self._key)

        if real_value is not None:
            self._state = int(real_value)
        else:
            self._state = value

        self._unknown_option = None
        self._attr_options = list(self._mapping.keys())
        self._attr_available = True
        self._attr_extra_state_attributes = {
            "raw_value": self._state,
            "known_values": dict(self._mapping),
            "read_error": False,
        }

        # Když měnič vrátí neznámou hodnotu, přidej diagnostickou volbu.
        known_values = [int(v) for v in self._mapping.values()]

        if self._state not in known_values:
            self._unknown_option = f"Unknown ({self._state})"
            self._attr_options = list(self._mapping.keys()) + [
                self._unknown_option
            ]

        self.async_write_ha_state()
