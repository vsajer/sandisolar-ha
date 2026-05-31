import logging
from datetime import timedelta

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
    PERCENTAGE,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SENSOR_UPDATE_INTERVAL = timedelta(seconds=10)


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
                # Neházej hned None, pokud máme poslední známou hodnotu.
                # Tím se senzory nebudou zbytečně rozpadat při jednom výpadku Modbusu.
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

            # SANDISOLAR někdy po zaokrouhlení pošle trochu menší hodnotu.
            # Malý pokles blokujeme, velký pokles necháme kvůli denním resetům.
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
        text = FAULT_WORD0_MAP.get(code, "Unknown fault code")

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
        text = WARNING_MAIN_MAP.get(code, "Unknown warning code")

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
        text = WARNING_SUB_MAP.get(code, "Unknown sub-warning code")

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
        self._attr_native_value = BATTERY_STATUS_MAP.get(
            code,
            f"Raw BMS status: {code}",
        )


class GridStatusTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:transmission-tower"

    def _update_from_data(self):
        val = self._get_value()

        if val is None:
            self._attr_native_value = None
            return

        code = int(val)
        self._attr_native_value = GRID_STATUS_MAP.get(
            code,
            "Unknown inverter status",
        )


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"] if isinstance(data, dict) else data

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

        EnergySensor(coordinator, "pv_energy_today", "PV Energy Today", "mdi:solar-power"),
        EnergySensor(coordinator, "pv_energy_total", "PV Energy Total", "mdi:solar-power"),

        SimpleSensor(coordinator, "battery_voltage", "Battery Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:battery", 1),
        SimpleSensor(coordinator, "battery_soc", "Battery SOC",
                     PERCENTAGE, SensorDeviceClass.BATTERY, "mdi:battery-high", 0),
        SimpleSensor(coordinator, "battery_temp", "Battery Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", 1),
        SimpleSensor(coordinator, "battery_current", "Battery Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-dc", 2),

        BatteryPowerSensor(coordinator, "battery_power", "Battery Power"),

        SimpleSensor(coordinator, "bms_max_charge_current", "BMS Max Charge Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:battery-plus", 1),
        SimpleSensor(coordinator, "bms_max_discharge_current", "BMS Max Discharge Current",
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

        EnergySensor(coordinator, "grid_in_energy_today", "Grid Import Energy Today", "mdi:transmission-tower-import"),
        EnergySensor(coordinator, "grid_in_energy_total", "Grid Import Energy Total", "mdi:transmission-tower-import"),

        EnergySensor(coordinator, "grid_out_energy_today", "Grid Export Energy Today", "mdi:transmission-tower-export"),
        EnergySensor(coordinator, "grid_out_energy_total", "Grid Export Energy Total", "mdi:transmission-tower-export"),

        EnergySensor(coordinator, "energy_sold_today", "Energy Sold Today", "mdi:cash-plus"),
        EnergySensor(coordinator, "energy_sold_total", "Energy Sold Total", "mdi:cash-plus"),
        EnergySensor(coordinator, "energy_bought_today", "Energy Bought Today", "mdi:cash-minus"),
        EnergySensor(coordinator, "energy_bought_total", "mdi:cash-minus"),
        EnergySensor(coordinator, "energy_self_to_load_today", "Energy Self To Load Today", "mdi:home-lightning-bolt"),
        EnergySensor(coordinator, "energy_self_to_load_total", "Energy Self To Load Total", "mdi:home-lightning-bolt"),

        SimpleSensor(coordinator, "eps_voltage", "EPS Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:home-lightning-bolt", 1),
        SimpleSensor(coordinator, "eps_current", "EPS Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:home-lightning-bolt", 1),
        SimpleSensor(coordinator, "eps_power", "EPS Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:home-lightning-bolt", 0),
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
