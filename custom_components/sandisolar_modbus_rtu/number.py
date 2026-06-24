import asyncio
import logging
from datetime import timedelta

from homeassistant.components.number import NumberEntity
from homeassistant.const import (
    UnitOfElectricCurrent,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfPower,
    EntityCategory,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


DEFAULT_BATTERY_CAPACITY_AH = 316


def _is_sane_soc(value) -> bool:
    """Return True only for realistic SOC values."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False

    return 0 <= value <= 100


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

    entities = [
        # -------------------------------------------------------------
        # Battery charge / discharge limits (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "charge_limit",
            "Battery Charge Limit",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:battery-charging",
        ),
        SandiSolarNumber(
            hub,
            "discharge_limit",
            "Battery Discharge Limit",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:battery-minus",
        ),

        # -------------------------------------------------------------
        # Battery SOC settings
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "end_of_charge_soc",
            "Battery End of Charge SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:battery-heart",
        ),
        SandiSolarNumber(
            hub,
            "on_grid_discharge_soc",
            "Battery On-Grid Discharge SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:transmission-tower",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_discharge_soc",
            "Battery Off-Grid Discharge SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:home-lightning-bolt",
        ),
        SandiSolarNumber(
            hub,
            "on_grid_recovery_soc",
            "Battery On-Grid Recovery SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:battery-sync",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_recovery_soc",
            "Battery Off-Grid Recovery SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:battery-sync",
        ),

        # -------------------------------------------------------------
        # Battery AC charge current limit
        # scale řeší modbus_map.py: RegisterDef(189, 0.1)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "ac_charge_current_limit",
            "Battery AC Charge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            1,
            100,
            0.1,
            "mdi:current-ac",
        ),

        # -------------------------------------------------------------
        # Local HA-only settings
        # -------------------------------------------------------------
        SandiSolarLocalNumber(
            hub,
            "battery_capacity_manual",
            "Battery Capacity Manual",
            "Ah",
            10,
            1000,
            1,
            "mdi:battery-heart-variant",
            DEFAULT_BATTERY_CAPACITY_AH,
        ),

        # -------------------------------------------------------------
        # SecEPS thresholds - SOC
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_soc",
            "SecEPS ON SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:toggle-switch",
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_off_soc",
            "SecEPS SWITCH SOC",
            PERCENTAGE,
            10,
            100,
            1,
            "mdi:toggle-switch-off",
        ),

        # -------------------------------------------------------------
        # SecEPS thresholds - Voltage
        # Advanced / Config
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_vbat",
            "ADV - SecEPS ON Voltage",
            UnitOfElectricPotential.VOLT,
            40,
            90,
            0.1,
            "mdi:alert-circle-outline",
            advanced=True,
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_off_vbat",
            "ADV - SecEPS OFF Voltage",
            UnitOfElectricPotential.VOLT,
            40,
            90,
            0.1,
            "mdi:alert-circle-outline",
            advanced=True,
        ),

        # -------------------------------------------------------------
        # SecEPS ON PV Power Min
        # scale řeší modbus_map.py: RegisterDef(223, 10)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_pv_power_min",
            "SecEPS ON PV Power Min",
            UnitOfPower.WATT,
            400,
            1000,
            10,
            "mdi:solar-power",
        ),
    ]

    async_add_entities(entities)


class SandiSolarNumber(NumberEntity):
    """Modbus number entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True

    # Číselné zadávání místo posuvníku.
    _attr_mode = "box"

    # Důležité:
    # Nechceme spoléhat jen na HA default polling.
    # Polling si řídíme sami podle hub.update_interval, aby Options flow fungoval.
    _attr_should_poll = False

    def __init__(
        self,
        hub,
        key,
        name,
        unit,
        min_value,
        max_value,
        step,
        icon,
        advanced=False,
    ):
        self._hub = hub
        self._key = key

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_number_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
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
    def native_value(self):
        return self._state

    async def async_added_to_hass(self):
        """Read initial value and start periodic refresh.

        This is important because inverter settings can be changed directly
        on the inverter LCD. Home Assistant must periodically read holding
        registers again, otherwise it keeps old values forever.
        """

        await self.async_update()
        self.async_write_ha_state()

        interval = int(
            getattr(
                self._hub,
                "settings_refresh_interval",
                getattr(self._hub, "update_interval", 10),
            )
            or 10
        )

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

    def _normalize_value(self, value):
        """Normalize value for Home Assistant display."""
        if value is None:
            return None

        if isinstance(value, float):
            return round(value, 3)

        return int(value)

    async def async_update(self):
        """Read current value from inverter."""
        val = await self._hub.read_holding_register(self._key)

        if val is None:
            self._attr_available = False
            return

        self._attr_available = True
        self._state = self._normalize_value(val)

    def _validate_before_write(self, write_value: float) -> bool:
        """Validate value before writing to inverter."""

        # SecEPS OFF SOC must be lower than SecEPS ON SOC.
        if self._key == "sec_eps_off_soc":
            on_soc = self._hub.get_cached("sec_eps_on_soc")

            # Ignore broken cached values like 7300 from previous wrong scaling.
            if _is_sane_soc(on_soc) and write_value >= float(on_soc):
                _LOGGER.error(
                    "SANDISOLAR: Refusing sec_eps_off_soc=%s because it must "
                    "be lower than sec_eps_on_soc=%s",
                    write_value,
                    on_soc,
                )
                return False

        # SecEPS ON SOC must be higher than SecEPS OFF SOC.
        if self._key == "sec_eps_on_soc":
            off_soc = self._hub.get_cached("sec_eps_off_soc")

            # Ignore broken cached values like 7300 from previous wrong scaling.
            if _is_sane_soc(off_soc) and write_value <= float(off_soc):
                _LOGGER.error(
                    "SANDISOLAR: Refusing sec_eps_on_soc=%s because it must "
                    "be higher than sec_eps_off_soc=%s",
                    write_value,
                    off_soc,
                )
                return False

        return True

    async def async_set_native_value(self, value: float):
        """Write value immediately and update Home Assistant state."""

        # Hodnota z HA může přijít jako float i u kroku 1.
        # Škálování řeší hub / modbus_map.py, sem posíláme hodnotu v HA jednotkách.
        write_value = round(float(value), 3)

        if not self._validate_before_write(write_value):
            self.async_write_ha_state()
            return

        ok = await self._hub.write_holding_register(self._key, write_value)

        if not ok:
            _LOGGER.error(
                "SANDISOLAR: Failed to write number %s=%s",
                self._key,
                write_value,
            )
            self._attr_available = False
            self.async_write_ha_state()
            return

        # Po zápisu z HA se pokusíme hned přečíst skutečnou hodnotu z měniče.
        # Když se čtení nepovede, zobrazíme alespoň požadovanou hodnotu.
        await asyncio.sleep(float(getattr(self._hub, "write_verify_delay", 0.5) or 0.5))

        real_value = await self._hub.read_holding_register(self._key)

        if real_value is not None:
            self._state = self._normalize_value(real_value)
        else:
            self._state = self._normalize_value(write_value)

        self._attr_available = True
        self.async_write_ha_state()


class SandiSolarLocalNumber(NumberEntity, RestoreEntity):
    """Local Home Assistant number entity, not written to inverter."""

    _attr_has_entity_name = True
    _attr_mode = "box"
    _attr_should_poll = False

    def __init__(
        self,
        hub,
        key,
        name,
        unit,
        min_value,
        max_value,
        step,
        icon,
        default_value,
        advanced=False,
    ):
        self._hub = hub
        self._key = key
        self._default_value = float(default_value)

        self._attr_name = name
        self._attr_unique_id = f"sandisolar_local_number_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
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
    def native_value(self):
        return self._state

    async def async_added_to_hass(self):
        """Restore local value after Home Assistant restart."""
        last_state = await self.async_get_last_state()

        if last_state is not None and last_state.state not in (
            "unknown",
            "unavailable",
            None,
        ):
            try:
                self._state = round(float(last_state.state), 3)
            except (TypeError, ValueError):
                self._state = self._default_value
        else:
            self._state = self._default_value

        # Ulož do cache hubu, aby to mohly použít virtuální senzory.
        self._hub._cache[self._key] = self._state

        self.async_write_ha_state()

    async def async_set_native_value(self, value: float):
        """Set local value and store it in hub cache."""

        write_value = round(float(value), 3)

        if write_value < self._attr_native_min_value:
            write_value = self._attr_native_min_value

        if write_value > self._attr_native_max_value:
            write_value = self._attr_native_max_value

        self._state = write_value
        self._attr_available = True

        # Tohle je lokální HA hodnota. Nezapisuje se do měniče.
        # Cache používá sensor.py pro výpočty rychlosti a kapacity.
        self._hub._cache[self._key] = self._state

        self.async_write_ha_state()