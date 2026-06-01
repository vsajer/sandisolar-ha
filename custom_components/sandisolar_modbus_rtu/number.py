import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import (
    UnitOfElectricCurrent,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfPower,
    EntityCategory,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
        # Charge / Discharge Limits (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "charge_limit",
            "Charge Limit",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-charging",
        ),
        SandiSolarNumber(
            hub,
            "discharge_limit",
            "Discharge Limit",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-minus",
        ),

        # -------------------------------------------------------------
        # End of Charge SOC (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "end_of_charge_soc",
            "End of Charge SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-heart",
        ),

        # -------------------------------------------------------------
        # SOC Limits (%)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "on_grid_discharge_soc",
            "On-Grid Discharge SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:transmission-tower",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_discharge_soc",
            "Off-Grid Discharge SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:home-lightning-bolt",
        ),
        SandiSolarNumber(
            hub,
            "on_grid_recovery_soc",
            "On-Grid Recovery SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-sync",
        ),
        SandiSolarNumber(
            hub,
            "off_grid_recovery_soc",
            "Off-Grid Recovery SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:battery-sync",
        ),

        # -------------------------------------------------------------
        # AC Charge Current Limit
        # scale řeší modbus_map.py: RegisterDef(189, 0.1)
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "ac_charge_current_limit",
            "AC Charge Current Limit",
            UnitOfElectricCurrent.AMPERE,
            10,
            100,
            0.1,
            "mdi:current-ac",
        ),

        # -------------------------------------------------------------
        # SecEPS thresholds - SOC
        #
        # Důležité:
        # v modbus_map.py musí být:
        # "sec_eps_on_soc": RegisterDef(219)
        # "sec_eps_off_soc": RegisterDef(221)
        #
        # Ne RegisterDef(..., 0.01), jinak se z 73 % stane 7300 nebo 0.73.
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_soc",
            "SecEPS ON SOC",
            PERCENTAGE,
            0,
            100,
            1,
            "mdi:toggle-switch",
        ),
        SandiSolarNumber(
            hub,
            "sec_eps_off_soc",
            "SecEPS SWITCH SOC",
            PERCENTAGE,
            0,
            100,
            0.1,
            "mdi:toggle-switch-off",
        ),

        # -------------------------------------------------------------
        # SecEPS thresholds - Voltage
        #
        # Tyhle jsou schované jako Advanced / Config.
        # Pro lithium/BMS režim jsou spíš pokročilé nastavení.
        # -------------------------------------------------------------
        #SandiSolarNumber(
        #    hub,
        #    "sec_eps_on_vbat",
        #    "ADV - SecEPS ON Voltage",
        #    UnitOfElectricPotential.VOLT,
        #    40,
        #    70,
        #    0.1,
        #    "mdi:alert-circle-outline",
        #    advanced=True,
        #),
        #SandiSolarNumber(
        #    hub,
        #    "sec_eps_off_vbat",
        #    "ADV - SecEPS OFF Voltage",
        #    UnitOfElectricPotential.VOLT,
        #    40,
        #    70,
        #    0.1,
        #    "mdi:alert-circle-outline",
        #    advanced=True,
        #),

        # -------------------------------------------------------------
        # SecEPS ON PV Power Min
        # scale řeší modbus_map.py: RegisterDef(223, 10)
        #
        # Měnič odmítal 10000 W, proto UI omezujeme na 0–3000 W.
        # Výchozí hodnota v dokumentaci bývá okolo 3000 W.
        # -------------------------------------------------------------
        SandiSolarNumber(
            hub,
            "sec_eps_on_pv_power_min",
            "SecEPS ON PV Power Min",
            UnitOfPower.WATT,
            0,
            3000,
            10,
            "mdi:solar-power",
        ),
    ]

    async_add_entities(entities)


class SandiSolarNumber(NumberEntity):
    """Number entity for SANDISOLAR SD-PRO-EU."""

    _attr_has_entity_name = True
    _attr_mode = "slider"

    # Tohle jsou konfigurační hodnoty, ne živé senzory.
    # Nechceme, aby každá number entita pořád sama pollovala Modbus.
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
        """Read initial value once when entity is added to Home Assistant."""
        await self.async_update()
        self.async_write_ha_state()

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
            self._state = None
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
        """Write value immediately and update local Home Assistant state."""

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

        # Okamžitě ukaž novou hodnotu v HA.
        # Skutečné potvrzení přijde až při dalším ručním / startovacím čtení,
        # ale zbytečně teď nezahlcujeme Modbus.
        self._state = self._normalize_value(write_value)
        self._attr_available = True
        self.async_write_ha_state()
