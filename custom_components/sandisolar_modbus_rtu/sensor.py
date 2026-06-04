import json
import logging
from collections import deque
from datetime import timedelta
from pathlib import Path

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfApparentPower,
    UnitOfTime,
    PERCENTAGE,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SENSOR_UPDATE_INTERVAL = timedelta(seconds=10)

AVG_SAMPLE_INTERVAL_SECONDS = 60
AVG_SAMPLE_COUNT = 15

EPS_ENERGY_SAMPLE_INTERVAL_SECONDS = 300
EPS_ENERGY_SAMPLE_COUNT = 13

DEFAULT_BATTERY_CAPACITY_AH = 316
DEFAULT_END_OF_CHARGE_SOC = 98
CHARGE_ETA_MAX_HOURS = 12
CHARGE_ETA_HYSTERESIS = 2

TRANSLATIONS_DIR = Path(__file__).parent / "translations"
_TRANSLATION_CACHE = {}


GRID_STATUS_MAP = {
    0: "Waiting",
    1: "Grid mode",
    2: "Off-grid mode",
    3: "Fault",
    4: "Flashing",
    5: "Bypass",
    6: "Self-charging",
}


FAULT_WORD0_MAP = {
    0: "No fault",
    103: "Inverter DC offset is too high",
    105: "Bypass AC output is overloaded",
    200: "Off-grid output voltage is too low",
    201: "Off-grid output voltage is too high",
    202: "Off-grid output has a short circuit",
    203: "Off-grid output is overloaded",
    204: "Abnormal off-grid output DC component offset",
    301: "Battery open circuit",
    305: "Battery overvoltage",
    306: "Battery overcurrent",
    307: "Battery communication fault",
    308: "BMS fault",
    400: "PV overvoltage",
    403: "PV short circuit",
    404: "PV reverse connection",
    500: "Abnormal BUS voltage",
    501: "Abnormal BUS voltage sampling",
    502: "Abnormal communication in the device",
    505: "Abnormal connection of the temperature sensor",
    506: "Device over-temperature",
    507: "Abnormal relay",
    509: "Anti-counter-current output timeout",
    510: "Mismatched software version",
    511: "Fan fault",
    513: "Parallel abnormality",
}


WARNING_MAIN_MAP = {
    0: "OK",
    103: "Grid unavailable",
    104: "Overrange voltage of grid",
    105: "Overrange frequency of grid",
    106: "No output voltage from the generator",
    107: "Overrange output voltage of the generator",
    108: "Overrange output frequency of the generator",
    302: "Low battery",
    304: "Abnormal BMS information",
    305: "Low battery voltage alarm",
    502: "Abnormal memory reading and writing",
}


WARNING_SUB_MAP = {
    0: "OK",
}


BATTERY_STATUS_MAP = {
    0: "Normal",
    1: "Charging",
    2: "Discharging",
    3: "Standby",
}


SENSOR_KEYS = [
    "pv1_voltage",
    "pv1_current",
    "pv2_voltage",
    "pv2_current",
    "pv_power_total",
    "pv_energy_today",
    "pv_energy_total",

    "battery_voltage",
    "battery_soc",
    "battery_temp",
    "battery_current",
    "battery_discharge_power",
    "battery_charge_power",
    "bms_max_charge_current",
    "bms_max_discharge_current",
    "bms_fcc",
    "bms_rm",
    "bms_cycle_count",
    "bms_soh",
    "battery_charge_energy_today",
    "battery_charge_energy_total",
    "battery_discharge_energy_today",
    "battery_discharge_energy_total",

    "inv_temp",
    "boost_temp",
    "llc_temp",
    "ambient_temp",

    "grid_voltage",
    "grid_current",
    "grid_frequency",
    "grid_power",
    "grid_in_energy_today",
    "grid_in_energy_total",
    "grid_out_energy_today",
    "grid_out_energy_total",
    "energy_sold_today",
    "energy_sold_total",
    "energy_bought_today",
    "energy_bought_total",
    "energy_self_to_load_today",
    "energy_self_to_load_total",

    "eps_voltage",
    "eps_current",
    "eps_power",
    "eps_active_power",
    "eps_apparent_power",
    "eps_energy_today",
    "eps_energy_total",

    "inverter_status",
    "battery_status",
    "fault_word0",
    "warning_main",
    "warning_sub",
    "total_work_time",
]


def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def _normalize_language(language: str) -> str:
    """Normalize Home Assistant language code."""
    return (language or "en").split("-")[0].lower()


def _load_language_file_sync(language: str) -> dict:
    """Load integration translation JSON file synchronously.

    This function must only be called through hass.async_add_executor_job().
    """

    language = _normalize_language(language)
    path = TRANSLATIONS_DIR / f"{language}.json"

    if not path.exists():
        path = TRANSLATIONS_DIR / "en.json"

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as err:
        _LOGGER.warning(
            "SANDISOLAR: Failed to load translation file %s: %s",
            path,
            err,
        )
        return {}


async def _async_preload_translations(hass) -> None:
    """Preload translation files outside the event loop."""

    languages = {
        "en",
        "cs",
        "de",
        "pl",
        "sk",
        _normalize_language(hass.config.language),
    }

    for language in languages:
        if not language:
            continue

        if language in _TRANSLATION_CACHE:
            continue

        data = await hass.async_add_executor_job(
            _load_language_file_sync,
            language,
        )
        _TRANSLATION_CACHE[language] = data

    if "en" not in _TRANSLATION_CACHE:
        _TRANSLATION_CACHE["en"] = await hass.async_add_executor_job(
            _load_language_file_sync,
            "en",
        )


def _get_language_data(language: str) -> dict:
    """Get already loaded translation data from cache only."""

    language = _normalize_language(language)

    if language in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[language]

    return _TRANSLATION_CACHE.get("en", {})


def _translated_state(language: str, section: str, code, fallback: str) -> str:
    """Translate state/warning/fault text by code."""

    data = _get_language_data(language)

    try:
        return data["states"][section][str(int(code))]
    except Exception:
        return fallback


def _translated_unknown(language: str, key: str, fallback: str) -> str:
    """Translate unknown fallback text."""

    data = _get_language_data(language)

    try:
        return data["states"]["unknown"][key]
    except Exception:
        return fallback


class SandiSolarSensorCoordinator(DataUpdateCoordinator):
    """Coordinator for SANDISOLAR sensors."""

    def __init__(self, hass, hub, keys):
        super().__init__(
            hass,
            _LOGGER,
            name="SANDISOLAR sensor coordinator",
            update_interval=SENSOR_UPDATE_INTERVAL,
        )
        self.hub = hub
        self.keys = keys

    async def _async_update_data(self):
        """Read all sensor values into one shared data dict."""

        previous_data = self.data or {}
        data = dict(previous_data)

        for key in self.keys:
            val = await self.hub.read_input_register(key)

            if val is None:
                if key in previous_data:
                    data[key] = previous_data[key]
                else:
                    data[key] = None
                continue

            data[key] = val

        return data


class BaseSandiSensor(CoordinatorEntity, SensorEntity):
    """Base SANDISOLAR sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name: str):
        super().__init__(coordinator)

        self._key = key
        self._attr_name = name
        self._attr_unique_id = (
            f"sandisolar_sensor_{key}_{name.lower().replace(' ', '_')}"
        )

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU",
        }

    def _get_value(self, key=None):
        """Get value from coordinator data."""
        data = self.coordinator.data or {}
        return data.get(key or self._key)

    def _get_cached_holding(self, key, default=None):
        """Get cached holding register value from hub."""
        return _safe_float(self.coordinator.hub.get_cached(key), default)

    def _language(self):
        """Return current Home Assistant language."""
        return self.coordinator.hass.config.language or "en"

    def _tr_state(self, section: str, code, fallback: str) -> str:
        """Translate state text."""
        return _translated_state(
            self._language(),
            section,
            code,
            fallback,
        )

    def _tr_unknown(self, key: str, fallback: str) -> str:
        """Translate unknown text."""
        return _translated_unknown(
            self._language(),
            key,
            fallback,
        )

    async def async_added_to_hass(self):
        """Entity added to Home Assistant."""
        await super().async_added_to_hass()
        self._update_from_data()
        self.async_write_ha_state()

    def _handle_coordinator_update(self):
        """Handle updated data from coordinator."""
        self._update_from_data()
        super()._handle_coordinator_update()

    def _update_from_data(self):
        """Update entity state from coordinator data."""
        raise NotImplementedError


class SimpleSensor(BaseSandiSensor):
    def __init__(self, coordinator, key, name, unit, device_class, icon, decimals=1):
        super().__init__(coordinator, key, name)

        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._decimals = decimals

        if device_class in (
            SensorDeviceClass.POWER,
            SensorDeviceClass.VOLTAGE,
            SensorDeviceClass.CURRENT,
            SensorDeviceClass.FREQUENCY,
            SensorDeviceClass.TEMPERATURE,
            SensorDeviceClass.BATTERY,
        ):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        self._attr_native_value = (
            int(val) if self._decimals == 0 else round(val, self._decimals)
        )


class EnergySensor(BaseSandiSensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, key, name, icon):
        super().__init__(coordinator, key, name)

        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = icon
        self._last_value = None

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        if self._last_value is not None and val < self._last_value:
            diff = self._last_value - val

            if diff <= 0.5:
                val = self._last_value

        self._last_value = val
        self._attr_native_value = round(val, 1)


class BatteryPowerSensor(BaseSandiSensor):
    _attr_icon = "mdi:battery-sync"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _update_from_data(self):
        discharge = self._get_value("battery_discharge_power")
        charge = self._get_value("battery_charge_power")

        if discharge is None or charge is None:
            self._attr_native_value = None
            return

        self._attr_native_value = int(charge - discharge)


class TimedAveragePowerSensor(BaseSandiSensor):
    """Virtual smoothed power sensor using EMA filter."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator,
        key,
        name,
        source,
        icon,
        alpha=0.30,
        spike_limit_w=1500,
    ):
        super().__init__(coordinator, key, name)

        self._source = source
        self._attr_icon = icon
        self._alpha = alpha
        self._spike_limit_w = spike_limit_w
        self._ema_value = None
        self._last_raw_value = None
        self._samples = 0

    def _source_value(self):
        if self._source == "pv":
            return self._get_value("pv_power_total")

        if self._source == "grid":
            return self._get_value("grid_power")

        if self._source == "eps":
            return self._get_value("eps_power")

        if self._source == "battery":
            charge = self._get_value("battery_charge_power")
            discharge = self._get_value("battery_discharge_power")

            if charge is None or discharge is None:
                return None

            return float(charge) - float(discharge)

        return None

    def _update_from_data(self):
        raw_value = self._source_value()

        if raw_value is None:
            self._attr_native_value = None
            return

        raw_value = float(raw_value)

        if self._ema_value is None:
            self._ema_value = raw_value
            self._last_raw_value = raw_value
            self._samples = 1
        else:
            value_for_filter = raw_value

            # Limit one-shot jumps so short spikes or communication noise do not
            # throw the filtered value too far away from reality.
            if (
                self._last_raw_value is not None
                and self._spike_limit_w is not None
                and abs(raw_value - self._last_raw_value) > self._spike_limit_w
            ):
                if raw_value > self._last_raw_value:
                    value_for_filter = self._last_raw_value + self._spike_limit_w
                else:
                    value_for_filter = self._last_raw_value - self._spike_limit_w

            self._ema_value = (
                self._ema_value
                + self._alpha * (value_for_filter - self._ema_value)
            )

            self._last_raw_value = raw_value
            self._samples += 1

        self._attr_native_value = int(round(self._ema_value))

        self._attr_extra_state_attributes = {
            "source": self._source,
            "filter": "ema",
            "alpha": self._alpha,
            "samples": self._samples,
            "instant_value": round(raw_value, 1),
            "filtered_value": round(self._ema_value, 1),
            "spike_limit_w": self._spike_limit_w,
        }


class BatteryPowerSpeedSensor(BaseSandiSensor):
    """Virtual sensor estimating battery SOC speed from average battery power."""

    _attr_native_unit_of_measurement = "%/h"
    _attr_icon = "mdi:speedometer"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator,
        key,
        name,
        sample_interval_seconds=AVG_SAMPLE_INTERVAL_SECONDS,
        sample_count=AVG_SAMPLE_COUNT,
    ):
        super().__init__(coordinator, key, name)

        self._sample_interval_seconds = sample_interval_seconds
        self._sample_count = sample_count
        self._samples = deque(maxlen=sample_count)
        self._last_sample_time = None

    def _battery_net_power(self):
        charge = self._get_value("battery_charge_power")
        discharge = self._get_value("battery_discharge_power")

        if charge is None or discharge is None:
            return None

        return float(charge) - float(discharge)

    def _battery_capacity_ah(self):
        fcc = _safe_float(self._get_value("bms_fcc"))
        manual = self._get_cached_holding("battery_capacity_manual")
        rm = _safe_float(self._get_value("bms_rm"))

        if fcc is not None and fcc > 0:
            return fcc, "bms_fcc"

        if manual is not None and manual > 0:
            return manual, "battery_capacity_manual"

        if rm is not None and rm > 0:
            return rm, "bms_rm"

        return DEFAULT_BATTERY_CAPACITY_AH, "default"

    def _maybe_add_sample(self, value, now):
        if value is None:
            return

        if self._last_sample_time is None:
            self._samples.append(float(value))
            self._last_sample_time = now
            return

        elapsed = (now - self._last_sample_time).total_seconds()

        if elapsed >= self._sample_interval_seconds:
            self._samples.append(float(value))
            self._last_sample_time = now

    def _update_from_data(self):
        now = dt_util.utcnow()
        power = self._battery_net_power()
        voltage = _safe_float(self._get_value("battery_voltage"))
        capacity_ah, capacity_source = self._battery_capacity_ah()

        self._maybe_add_sample(power, now)

        if not self._samples or voltage is None or voltage <= 0 or capacity_ah <= 0:
            self._attr_native_value = None
            return

        avg_power = sum(self._samples) / len(self._samples)

        ah_per_hour = avg_power / voltage
        percent_per_hour = (ah_per_hour / capacity_ah) * 100

        self._attr_native_value = round(percent_per_hour, 2)

        self._attr_extra_state_attributes = {
            "average_battery_power_w": round(avg_power, 1),
            "battery_voltage_v": round(voltage, 2),
            "battery_capacity_ah": round(capacity_ah, 1),
            "battery_capacity_source": capacity_source,
            "samples": len(self._samples),
            "max_samples": self._sample_count,
            "sample_interval_seconds": self._sample_interval_seconds,
        }


class BatterySocSpeedSensor(BaseSandiSensor):
    """Virtual sensor calculating SOC speed from real SOC changes."""

    _attr_native_unit_of_measurement = "%/h"
    _attr_icon = "mdi:battery-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator,
        key,
        name,
        sample_interval_seconds=AVG_SAMPLE_INTERVAL_SECONDS,
        sample_count=AVG_SAMPLE_COUNT,
    ):
        super().__init__(coordinator, key, name)

        self._sample_interval_seconds = sample_interval_seconds
        self._sample_count = sample_count
        self._samples = deque(maxlen=sample_count)
        self._last_sample_time = None

    def _maybe_add_sample(self, soc, now):
        if soc is None:
            return

        if self._last_sample_time is None:
            self._samples.append((now, float(soc)))
            self._last_sample_time = now
            return

        elapsed = (now - self._last_sample_time).total_seconds()

        if elapsed >= self._sample_interval_seconds:
            self._samples.append((now, float(soc)))
            self._last_sample_time = now

    def _update_from_data(self):
        now = dt_util.utcnow()
        soc = _safe_float(self._get_value("battery_soc"))

        self._maybe_add_sample(soc, now)

        if len(self._samples) < 2:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "samples": len(self._samples),
                "max_samples": self._sample_count,
                "status": "waiting_for_samples",
            }
            return

        first_time, first_soc = self._samples[0]
        last_time, last_soc = self._samples[-1]

        elapsed_hours = (last_time - first_time).total_seconds() / 3600

        if elapsed_hours <= 0:
            self._attr_native_value = None
            return

        speed = (last_soc - first_soc) / elapsed_hours
        self._attr_native_value = round(speed, 2)

        self._attr_extra_state_attributes = {
            "samples": len(self._samples),
            "max_samples": self._sample_count,
            "first_soc": round(first_soc, 2),
            "last_soc": round(last_soc, 2),
            "elapsed_minutes": round(elapsed_hours * 60, 1),
        }


class EpsEnergyHourSensor(BaseSandiSensor):
    """Virtual sensor estimating EPS energy consumption per hour."""

    _attr_native_unit_of_measurement = "kWh/h"
    _attr_icon = "mdi:home-lightning-bolt"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator,
        key,
        name,
        sample_interval_seconds=EPS_ENERGY_SAMPLE_INTERVAL_SECONDS,
        sample_count=EPS_ENERGY_SAMPLE_COUNT,
    ):
        super().__init__(coordinator, key, name)

        self._sample_interval_seconds = sample_interval_seconds
        self._sample_count = sample_count
        self._samples = deque(maxlen=sample_count)
        self._last_sample_time = None

    def _maybe_add_sample(self, value, now):
        if value is None:
            return

        if self._last_sample_time is None:
            self._samples.append((now, float(value)))
            self._last_sample_time = now
            return

        elapsed = (now - self._last_sample_time).total_seconds()

        if elapsed >= self._sample_interval_seconds:
            self._samples.append((now, float(value)))
            self._last_sample_time = now

    def _update_from_data(self):
        now = dt_util.utcnow()
        total = _safe_float(self._get_value("eps_energy_total"))

        self._maybe_add_sample(total, now)

        if len(self._samples) < 2:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "samples": len(self._samples),
                "max_samples": self._sample_count,
                "status": "waiting_for_samples",
            }
            return

        first_time, first_value = self._samples[0]
        last_time, last_value = self._samples[-1]

        elapsed_hours = (last_time - first_time).total_seconds() / 3600

        if elapsed_hours <= 0:
            self._attr_native_value = None
            return

        diff = last_value - first_value

        if diff < 0:
            diff = 0

        energy_per_hour = diff / elapsed_hours

        self._attr_native_value = round(energy_per_hour, 3)

        self._attr_extra_state_attributes = {
            "samples": len(self._samples),
            "max_samples": self._sample_count,
            "sample_interval_seconds": self._sample_interval_seconds,
            "elapsed_minutes": round(elapsed_hours * 60, 1),
            "energy_difference_kwh": round(diff, 3),
            "first_total_kwh": round(first_value, 3),
            "last_total_kwh": round(last_value, 3),
        }


class BatteryChargeEtaSensor(BaseSandiSensor):
    """Virtual sensor estimating when battery reaches End of Charge SOC."""

    _attr_icon = "mdi:battery-clock"

    def __init__(
        self,
        coordinator,
        key,
        name,
        sample_interval_seconds=AVG_SAMPLE_INTERVAL_SECONDS,
        sample_count=AVG_SAMPLE_COUNT,
    ):
        super().__init__(coordinator, key, name)

        self._sample_interval_seconds = sample_interval_seconds
        self._sample_count = sample_count
        self._samples = deque(maxlen=sample_count)
        self._last_sample_time = None
        self._charged_at = None
        self._charged_date = None

    def _target_soc(self):
        target = self._get_cached_holding(
            "end_of_charge_soc",
            DEFAULT_END_OF_CHARGE_SOC,
        )

        if target is None:
            return DEFAULT_END_OF_CHARGE_SOC

        return _clamp(float(target), 1, 100)

    def _battery_capacity_ah(self):
        fcc = _safe_float(self._get_value("bms_fcc"))
        manual = self._get_cached_holding("battery_capacity_manual")
        rm = _safe_float(self._get_value("bms_rm"))

        if fcc is not None and fcc > 0:
            return fcc, "bms_fcc"

        if manual is not None and manual > 0:
            return manual, "battery_capacity_manual"

        if rm is not None and rm > 0:
            return rm, "bms_rm"

        return DEFAULT_BATTERY_CAPACITY_AH, "default"

    def _battery_net_power(self):
        charge = self._get_value("battery_charge_power")
        discharge = self._get_value("battery_discharge_power")

        if charge is None or discharge is None:
            return None

        return float(charge) - float(discharge)

    def _maybe_add_sample(self, value, now):
        if value is None:
            return

        if self._last_sample_time is None:
            self._samples.append(float(value))
            self._last_sample_time = now
            return

        elapsed = (now - self._last_sample_time).total_seconds()

        if elapsed >= self._sample_interval_seconds:
            self._samples.append(float(value))
            self._last_sample_time = now

    def _battery_power_speed(self):
        voltage = _safe_float(self._get_value("battery_voltage"))
        capacity_ah, capacity_source = self._battery_capacity_ah()

        if not self._samples or voltage is None or voltage <= 0 or capacity_ah <= 0:
            return None, capacity_ah, capacity_source, None

        avg_power = sum(self._samples) / len(self._samples)
        ah_per_hour = avg_power / voltage
        percent_per_hour = (ah_per_hour / capacity_ah) * 100

        return percent_per_hour, capacity_ah, capacity_source, avg_power

    def _update_from_data(self):
        now_utc = dt_util.utcnow()
        now_local = dt_util.now()

        soc = _safe_float(self._get_value("battery_soc"))
        target = self._target_soc()
        battery_power = self._battery_net_power()

        self._maybe_add_sample(battery_power, now_utc)

        if soc is None:
            self._attr_native_value = None
            return

        soc = float(soc)
        today = now_local.date()

        if self._charged_date is not None and self._charged_date != today:
            self._charged_at = None
            self._charged_date = None

        if soc >= target:
            if self._charged_at is None:
                self._charged_at = now_local
                self._charged_date = today

            self._attr_native_value = f"Bylo nabito v {self._charged_at.strftime('%H:%M')}"
            self._attr_extra_state_attributes = {
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "charged_at": self._charged_at.isoformat(),
                "latched": True,
            }
            return

        if (
            self._charged_at is not None
            and soc >= target - CHARGE_ETA_HYSTERESIS
        ):
            self._attr_native_value = f"Bylo nabito v {self._charged_at.strftime('%H:%M')}"
            self._attr_extra_state_attributes = {
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "charged_at": self._charged_at.isoformat(),
                "latched": True,
                "hysteresis_percent": CHARGE_ETA_HYSTERESIS,
            }
            return

        if soc < target - CHARGE_ETA_HYSTERESIS:
            self._charged_at = None
            self._charged_date = None

        speed, capacity_ah, capacity_source, avg_power = self._battery_power_speed()

        if speed is None:
            self._attr_native_value = "čekám na výpočet"
            self._attr_extra_state_attributes = {
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "samples": len(self._samples),
                "max_samples": self._sample_count,
            }
            return

        if speed <= 0:
            self._attr_native_value = "dnes nebude"
            self._attr_extra_state_attributes = {
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "speed_percent_per_hour": round(speed, 2),
                "average_battery_power_w": None if avg_power is None else round(avg_power, 1),
                "battery_capacity_ah": round(capacity_ah, 1),
                "battery_capacity_source": capacity_source,
            }
            return

        remaining = target - soc
        hours = remaining / speed

        if hours <= 0:
            self._charged_at = now_local
            self._charged_date = today
            self._attr_native_value = f"Bylo nabito v {now_local.strftime('%H:%M')}"
        elif hours > CHARGE_ETA_MAX_HOURS:
            self._attr_native_value = "dnes nebude"
        else:
            finish = now_local + timedelta(hours=hours)
            self._attr_native_value = f"Bude nabito v {finish.strftime('%H:%M')}"

        self._attr_extra_state_attributes = {
            "target_soc": round(target, 1),
            "current_soc": round(soc, 1),
            "remaining_percent": round(max(0, remaining), 1),
            "speed_percent_per_hour": round(speed, 2),
            "estimated_hours": round(hours, 2),
            "average_battery_power_w": None if avg_power is None else round(avg_power, 1),
            "battery_capacity_ah": round(capacity_ah, 1),
            "battery_capacity_source": capacity_source,
            "samples": len(self._samples),
            "max_samples": self._sample_count,
        }


class BatteryChargeEtaMinutesSensor(BaseSandiSensor):
    """Virtual numeric countdown sensor until End of Charge SOC is reached."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-sand"

    def __init__(
        self,
        coordinator,
        key,
        name,
        sample_interval_seconds=AVG_SAMPLE_INTERVAL_SECONDS,
        sample_count=AVG_SAMPLE_COUNT,
    ):
        super().__init__(coordinator, key, name)

        self._sample_interval_seconds = sample_interval_seconds
        self._sample_count = sample_count
        self._samples = deque(maxlen=sample_count)
        self._last_sample_time = None
        self._charged_at = None
        self._charged_date = None

    def _target_soc(self):
        target = self._get_cached_holding(
            "end_of_charge_soc",
            DEFAULT_END_OF_CHARGE_SOC,
        )

        if target is None:
            return DEFAULT_END_OF_CHARGE_SOC

        return _clamp(float(target), 1, 100)

    def _battery_capacity_ah(self):
        fcc = _safe_float(self._get_value("bms_fcc"), 0)
        manual = self._get_cached_holding("battery_capacity_manual")
        rm = _safe_float(self._get_value("bms_rm"), 0)
        soh = _safe_float(self._get_value("bms_soh"), 0)

        if fcc is not None and fcc > 0:
            return fcc, "bms_fcc"

        if manual is not None and manual > 0:
            if soh is not None and soh > 0:
                return (
                    manual * soh / 100,
                    "battery_capacity_manual_minus_soh",
                )

            return manual, "battery_capacity_manual"

        if rm is not None and rm > 0:
            return rm, "bms_rm"

        return DEFAULT_BATTERY_CAPACITY_AH, "default"

    def _battery_net_power(self):
        charge = self._get_value("battery_charge_power")
        discharge = self._get_value("battery_discharge_power")

        if charge is None or discharge is None:
            return None

        return float(charge) - float(discharge)

    def _maybe_add_sample(self, value, now):
        if value is None:
            return

        if self._last_sample_time is None:
            self._samples.append(float(value))
            self._last_sample_time = now
            return

        elapsed = (now - self._last_sample_time).total_seconds()

        if elapsed >= self._sample_interval_seconds:
            self._samples.append(float(value))
            self._last_sample_time = now

    def _battery_power_speed(self):
        voltage = _safe_float(self._get_value("battery_voltage"))
        capacity_ah, capacity_source = self._battery_capacity_ah()

        if not self._samples or voltage is None or voltage <= 0 or capacity_ah <= 0:
            return None, capacity_ah, capacity_source, None

        avg_power = sum(self._samples) / len(self._samples)
        ah_per_hour = avg_power / voltage
        percent_per_hour = (ah_per_hour / capacity_ah) * 100

        return percent_per_hour, capacity_ah, capacity_source, avg_power

    def _update_from_data(self):
        now_utc = dt_util.utcnow()
        now_local = dt_util.now()

        soc = _safe_float(self._get_value("battery_soc"))
        target = self._target_soc()
        battery_power = self._battery_net_power()

        self._maybe_add_sample(battery_power, now_utc)

        if soc is None:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "status": "battery_soc_unavailable",
            }
            return

        soc = float(soc)
        today = now_local.date()

        if self._charged_date is not None and self._charged_date != today:
            self._charged_at = None
            self._charged_date = None

        if soc >= target:
            if self._charged_at is None:
                self._charged_at = now_local
                self._charged_date = today

            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "status": "charged",
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "charged_at": self._charged_at.isoformat(),
                "latched": True,
            }
            return

        if (
            self._charged_at is not None
            and soc >= target - CHARGE_ETA_HYSTERESIS
        ):
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "status": "charged_latched",
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "charged_at": self._charged_at.isoformat(),
                "latched": True,
                "hysteresis_percent": CHARGE_ETA_HYSTERESIS,
            }
            return

        if soc < target - CHARGE_ETA_HYSTERESIS:
            self._charged_at = None
            self._charged_date = None

        speed, capacity_ah, capacity_source, avg_power = self._battery_power_speed()

        if speed is None:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "status": "waiting_for_calculation",
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "samples": len(self._samples),
                "max_samples": self._sample_count,
            }
            return

        if speed <= 0:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "status": "not_charging",
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "speed_percent_per_hour": round(speed, 2),
                "average_battery_power_w": (
                    None if avg_power is None else round(avg_power, 1)
                ),
                "battery_capacity_ah": round(capacity_ah, 1),
                "battery_capacity_source": capacity_source,
            }
            return

        remaining = max(0, target - soc)
        hours = remaining / speed

        if hours > CHARGE_ETA_MAX_HOURS:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "status": "not_today",
                "target_soc": round(target, 1),
                "current_soc": round(soc, 1),
                "remaining_percent": round(remaining, 1),
                "speed_percent_per_hour": round(speed, 2),
                "estimated_hours": round(hours, 2),
                "max_hours": CHARGE_ETA_MAX_HOURS,
                "average_battery_power_w": (
                    None if avg_power is None else round(avg_power, 1)
                ),
                "battery_capacity_ah": round(capacity_ah, 1),
                "battery_capacity_source": capacity_source,
                "samples": len(self._samples),
                "max_samples": self._sample_count,
            }
            return

        minutes = int(round(hours * 60))

        if remaining > 0 and minutes < 1:
            minutes = 1

        finish = now_local + timedelta(minutes=minutes)

        self._attr_native_value = minutes
        self._attr_extra_state_attributes = {
            "status": "ok",
            "target_soc": round(target, 1),
            "current_soc": round(soc, 1),
            "remaining_percent": round(remaining, 1),
            "speed_percent_per_hour": round(speed, 2),
            "estimated_hours": round(hours, 2),
            "estimated_finish_time": finish.isoformat(),
            "average_battery_power_w": (
                None if avg_power is None else round(avg_power, 1)
            ),
            "battery_capacity_ah": round(capacity_ah, 1),
            "battery_capacity_source": capacity_source,
            "samples": len(self._samples),
            "max_samples": self._sample_count,
        }


class BatterySocRealSensor(BaseSandiSensor):
    """Virtual sensor showing usable SOC between discharge limit and EOC."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-sync"

    def _target_soc(self):
        target = self._get_cached_holding(
            "end_of_charge_soc",
            DEFAULT_END_OF_CHARGE_SOC,
        )

        if target is None:
            return DEFAULT_END_OF_CHARGE_SOC

        return _clamp(float(target), 1, 100)

    def _lower_soc(self, inverter_status):
        on_grid = self._get_cached_holding("on_grid_discharge_soc", 0)
        off_grid = self._get_cached_holding("off_grid_discharge_soc", 0)

        if int(inverter_status) == 2:
            return _clamp(float(off_grid), 0, 100), "off_grid_discharge_soc"

        return _clamp(float(on_grid), 0, 100), "on_grid_discharge_soc"

    def _update_from_data(self):
        soc = _safe_float(self._get_value("battery_soc"))
        inverter_status = _safe_float(self._get_value("inverter_status"), 0)

        if soc is None:
            self._attr_native_value = None
            return

        target = self._target_soc()
        lower, lower_source = self._lower_soc(inverter_status)

        if target <= lower:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "error": "target_soc_must_be_higher_than_lower_limit",
                "target_soc": round(target, 1),
                "lower_limit": round(lower, 1),
                "lower_source": lower_source,
            }
            return

        real_soc = ((float(soc) - lower) / (target - lower)) * 100
        real_soc = _clamp(real_soc, 0, 100)

        self._attr_native_value = round(real_soc, 1)
        self._attr_extra_state_attributes = {
            "battery_soc": round(float(soc), 1),
            "real_soc": round(real_soc, 1),
            "lower_limit": round(lower, 1),
            "upper_limit": round(target, 1),
            "lower_source": lower_source,
            "inverter_status": int(inverter_status),
            "mode": "off-grid" if int(inverter_status) == 2 else "on-grid",
        }


class WorkTimeSensor(BaseSandiSensor):
    _attr_icon = "mdi:clock-time-eight"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        total_minutes = int(val * 0.5)
        days = total_minutes // 1440
        hours = (total_minutes % 1440) // 60
        minutes = total_minutes % 60

        self._attr_native_value = f"{days}d {hours}h {minutes}m"


class FaultWord0TextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert-circle"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        code = int(val)
        fallback = FAULT_WORD0_MAP.get(code, "Unknown fault code")
        text = self._tr_state("fault_word0", code, fallback)

        if code not in FAULT_WORD0_MAP:
            text = self._tr_unknown("fault_code", fallback)

        self._attr_native_value = f"{code} - {text}"
        self._attr_extra_state_attributes = {
            "raw_value": code,
            "message": text,
        }


class WarningMainCodeSensor(BaseSandiSensor):
    _attr_icon = "mdi:numeric"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        self._attr_native_value = int(val)


class WarningMainTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        code = int(val)
        fallback = WARNING_MAIN_MAP.get(code, "Unknown warning code")
        text = self._tr_state("warning_main", code, fallback)

        if code not in WARNING_MAIN_MAP:
            text = self._tr_unknown("warning_code", fallback)

        self._attr_native_value = f"{code} - {text}"
        self._attr_extra_state_attributes = {
            "raw_value": code,
            "message": text,
        }


class WarningSubCodeSensor(BaseSandiSensor):
    _attr_icon = "mdi:numeric"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        self._attr_native_value = int(val)


class WarningSubTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        code = int(val)
        fallback = WARNING_SUB_MAP.get(code, "Unknown sub-warning code")
        text = self._tr_state("warning_sub", code, fallback)

        if code not in WARNING_SUB_MAP:
            text = self._tr_unknown("sub_warning_code", fallback)

        self._attr_native_value = f"{code} - {text}"
        self._attr_extra_state_attributes = {
            "raw_value": code,
            "message": text,
        }


class BatteryStatusTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:battery"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        code = int(val)
        fallback = BATTERY_STATUS_MAP.get(
            code,
            f"Raw BMS status: {code}",
        )
        text = self._tr_state("battery_status", code, fallback)

        if code not in BATTERY_STATUS_MAP:
            unknown = self._tr_unknown("battery_status", "Unknown BMS status")
            text = f"{unknown}: {code}"

        self._attr_native_value = text
        self._attr_extra_state_attributes = {
            "raw_value": code,
            "message": text,
        }


class GridStatusTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:transmission-tower"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        code = int(val)
        fallback = GRID_STATUS_MAP.get(
            code,
            "Unknown inverter status",
        )
        text = self._tr_state("inverter_status", code, fallback)

        if code not in GRID_STATUS_MAP:
            text = self._tr_unknown("inverter_status", fallback)

        self._attr_native_value = text
        self._attr_extra_state_attributes = {
            "raw_value": code,
            "message": text,
        }


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

    await _async_preload_translations(hass)

    coordinator = SandiSolarSensorCoordinator(
        hass=hass,
        hub=hub,
        keys=SENSOR_KEYS,
    )

    await coordinator.async_config_entry_first_refresh()

    entities = [
        SimpleSensor(coordinator, "pv1_voltage", "PV1 Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:solar-power", 1),
        SimpleSensor(coordinator, "pv1_current", "PV1 Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:solar-power", 1),
        SimpleSensor(coordinator, "pv2_voltage", "PV2 Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:solar-power", 1),
        SimpleSensor(coordinator, "pv2_current", "PV2 Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:solar-power", 1),
        SimpleSensor(coordinator, "pv_power_total", "PV Total Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:solar-power", 0),

        TimedAveragePowerSensor(
            coordinator,
            "avg_pv_power",
            "AVG PV Power",
            "pv",
            "mdi:solar-power",
            alpha=0.25,
            spike_limit_w=2000,
        ),

        EnergySensor(coordinator, "pv_energy_today", "PV Energy Today", "mdi:solar-power"),
        EnergySensor(coordinator, "pv_energy_total", "PV Energy Total", "mdi:solar-power"),

        SimpleSensor(coordinator, "battery_voltage", "Battery Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:battery", 1),
        SimpleSensor(coordinator, "battery_soc", "Battery SOC",
                     PERCENTAGE, SensorDeviceClass.BATTERY, "mdi:battery-high", 0),
        BatterySocRealSensor(coordinator, "battery_soc_real", "Battery SOC Real"),
        SimpleSensor(coordinator, "battery_temp", "Battery Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", 1),
        SimpleSensor(coordinator, "battery_current", "Battery Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-dc", 2),

        BatteryPowerSensor(coordinator, "battery_power", "Battery Power"),
        TimedAveragePowerSensor(
            coordinator,
            "avg_battery_power",
            "AVG Battery Power",
            "battery",
            "mdi:battery-sync",
            alpha=0.25,
            spike_limit_w=1500,
        ),
        BatteryPowerSpeedSensor(coordinator, "avg_battery_power_speed", "AVG Battery Power Speed"),
        BatterySocSpeedSensor(coordinator, "battery_soc_speed", "Battery SOC Speed"),
        BatteryChargeEtaSensor(coordinator, "battery_charge_eta", "Battery Charge ETA"),
        BatteryChargeEtaMinutesSensor(
            coordinator,
            "battery_charge_eta_minutes",
            "Battery Charge ETA Minutes",
        ),

        SimpleSensor(coordinator, "inv_temp", "Inverter Base Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", 1),
        SimpleSensor(coordinator, "boost_temp", "Inverter Boost Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer-high", 1),
        SimpleSensor(coordinator, "llc_temp", "Inverter LLC Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer-lines", 1),
        SimpleSensor(coordinator, "ambient_temp", "Inverter Ambient Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:home-thermometer-outline", 1),

        SimpleSensor(coordinator, "bms_max_charge_current", "Battery Max Charge Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:battery-plus", 1),
        SimpleSensor(coordinator, "bms_max_discharge_current", "Battery Max Discharge Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:battery-minus", 1),
        SimpleSensor(coordinator, "bms_fcc", "Battery FCC", "Ah", None, "mdi:battery-heart", 1),
        SimpleSensor(coordinator, "bms_rm", "Battery RM", "Ah", None, "mdi:battery-clock", 1),
        SimpleSensor(coordinator, "bms_cycle_count", "Battery Cycle Count", None, None, "mdi:counter", 0),
        SimpleSensor(coordinator, "bms_soh", "Battery SOH", PERCENTAGE, None, "mdi:battery-check", 0),

        EnergySensor(coordinator, "battery_charge_energy_today", "Battery Charge Energy Today", "mdi:battery-charging"),
        EnergySensor(coordinator, "battery_charge_energy_total", "Battery Charge Energy Total", "mdi:battery-charging"),
        EnergySensor(coordinator, "battery_discharge_energy_today", "Battery Discharge Energy Today", "mdi:battery-minus"),
        EnergySensor(coordinator, "battery_discharge_energy_total", "Battery Discharge Energy Total", "mdi:battery-minus"),

        SimpleSensor(coordinator, "grid_voltage", "Grid Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:transmission-tower", 1),
        SimpleSensor(coordinator, "grid_current", "Grid Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:transmission-tower", 1),
        SimpleSensor(coordinator, "grid_frequency", "Grid Frequency",
                     UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, "mdi:sine-wave", 2),
        SimpleSensor(coordinator, "grid_power", "Grid Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:transmission-tower", 0),
        TimedAveragePowerSensor(
            coordinator,
            "avg_grid_power",
            "AVG Grid Power",
            "grid",
            "mdi:transmission-tower",
            alpha=0.35,
            spike_limit_w=1500,
        ),

        EnergySensor(coordinator, "grid_in_energy_today", "Grid Import Energy Today", "mdi:transmission-tower-import"),
        EnergySensor(coordinator, "grid_in_energy_total", "Grid Import Energy Total", "mdi:transmission-tower-import"),

        EnergySensor(coordinator, "grid_out_energy_today", "Grid Export Energy Today", "mdi:transmission-tower-export"),
        EnergySensor(coordinator, "grid_out_energy_total", "Grid Export Energy Total", "mdi:transmission-tower-export"),

        EnergySensor(coordinator, "energy_sold_today", "Energy Sold Today", "mdi:cash-plus"),
        EnergySensor(coordinator, "energy_sold_total", "Energy Sold Total", "mdi:cash-plus"),
        EnergySensor(coordinator, "energy_bought_today", "Energy Bought Today", "mdi:cash-minus"),
        EnergySensor(coordinator, "energy_bought_total", "Energy Bought Total", "mdi:cash-minus"),
        EnergySensor(coordinator, "energy_self_to_load_today", "Energy Self To Load Today", "mdi:home-lightning-bolt"),
        EnergySensor(coordinator, "energy_self_to_load_total", "Energy Self To Load Total", "mdi:home-lightning-bolt"),

        SimpleSensor(coordinator, "eps_voltage", "EPS Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:home-lightning-bolt", 1),
        SimpleSensor(coordinator, "eps_current", "EPS Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:home-lightning-bolt", 1),
        SimpleSensor(coordinator, "eps_power", "EPS Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:home-lightning-bolt", 0),
        TimedAveragePowerSensor(
            coordinator,
            "avg_eps_load",
            "AVG EPS Load",
            "eps",
            "mdi:home-lightning-bolt",
            alpha=0.30,
            spike_limit_w=1500,
        ),
        EpsEnergyHourSensor(coordinator, "eps_energy_hour", "EPS Energy Hour"),
        SimpleSensor(coordinator, "eps_active_power", "EPS Active Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", 0),
        SimpleSensor(coordinator, "eps_apparent_power", "EPS Apparent Power",
                     UnitOfApparentPower.VOLT_AMPERE, None, "mdi:flash-outline", 0),

        EnergySensor(coordinator, "eps_energy_today", "EPS Energy Today", "mdi:home-lightning-bolt"),
        EnergySensor(coordinator, "eps_energy_total", "EPS Energy Total", "mdi:home-lightning-bolt"),

        GridStatusTextSensor(coordinator, "inverter_status", "Inverter Status"),
        BatteryStatusTextSensor(coordinator, "battery_status", "Battery Status"),

        FaultWord0TextSensor(coordinator, "fault_word0", "Fault Word0 Text"),

        WarningMainCodeSensor(coordinator, "warning_main", "Warning Main Code"),
        WarningMainTextSensor(coordinator, "warning_main", "Warning Main Text"),
        WarningSubCodeSensor(coordinator, "warning_sub", "Warning Sub Code"),
        WarningSubTextSensor(coordinator, "warning_sub", "Warning Sub Text"),

        WorkTimeSensor(coordinator, "total_work_time", "Total Work Time"),
    ]

    async_add_entities(entities)
