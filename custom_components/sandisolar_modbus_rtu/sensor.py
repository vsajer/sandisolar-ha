import logging

from homeassistant.components.sensor import SensorEntity
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
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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


class BaseSandiSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hub, key, name: str):
        self._hub = hub
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sandisolar_sensor_{key}_{name.lower().replace(' ', '_')}"

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU",
        }


class SimpleSensor(BaseSandiSensor):
    def __init__(self, hub, key, name, unit, device_class, icon, decimals=1):
        super().__init__(hub, key, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._decimals = decimals

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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

    def __init__(self, hub, key, name, icon):
        super().__init__(hub, key, name)
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = icon
        self._last_value = None

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

        if val is None:
            return

        if self._last_value is not None and val < self._last_value:
            val = self._last_value

        self._last_value = val
        self._attr_native_value = round(val, 1)


class BatteryPowerSensor(BaseSandiSensor):
    _attr_icon = "mdi:battery-sync"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER

    async def async_update(self):
        discharge = await self._hub.read_input_register("battery_discharge_power")
        charge = await self._hub.read_input_register("battery_charge_power")

        if discharge is None or charge is None:
            self._attr_native_value = None
            return

        self._attr_native_value = int(charge - discharge)


class WorkTimeSensor(BaseSandiSensor):
    _attr_icon = "mdi:clock-time-eight"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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
    _attr_native_unit_of_measurement = None

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

        if val is None:
            self._attr_native_value = None
            return

        self._attr_native_value = int(val)


class WarningMainTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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
    _attr_native_unit_of_measurement = None

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

        if val is None:
            self._attr_native_value = None
            return

        self._attr_native_value = int(val)


class WarningSubTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)

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

    entities = [
        SimpleSensor(hub, "pv1_voltage", "PV1 Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:solar-power", 1),
        SimpleSensor(hub, "pv1_current", "PV1 Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:solar-power", 1),
        SimpleSensor(hub, "pv2_voltage", "PV2 Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:solar-power", 1),
        SimpleSensor(hub, "pv2_current", "PV2 Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:solar-power", 1),
        SimpleSensor(hub, "pv_power_total", "PV Total Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:solar-power", 0),

        EnergySensor(hub, "pv_energy_today", "PV Energy Today", "mdi:solar-power"),
        EnergySensor(hub, "pv_energy_total", "PV Energy Total", "mdi:solar-power"),

        SimpleSensor(hub, "battery_voltage", "Battery Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:battery", 1),
        SimpleSensor(hub, "battery_soc", "Battery SOC",
                     PERCENTAGE, SensorDeviceClass.BATTERY, "mdi:battery-high", 0),
        SimpleSensor(hub, "battery_temp", "Battery Temperature",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", 1),
        SimpleSensor(hub, "battery_current", "Battery Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-dc", 2),

        BatteryPowerSensor(hub, "battery_power", "Battery Power"),

        SimpleSensor(hub, "bms_max_charge_current", "BMS Max Charge Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:battery-plus", 1),
        SimpleSensor(hub, "bms_max_discharge_current", "BMS Max Discharge Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:battery-minus", 1),
        SimpleSensor(hub, "bms_fcc", "Battery FCC", "Ah", None, "mdi:battery-heart", 1),
        SimpleSensor(hub, "bms_rm", "Battery RM", "Ah", None, "mdi:battery-clock", 1),
        SimpleSensor(hub, "bms_cycle_count", "Battery Cycle Count", None, None, "mdi:counter", 0),
        SimpleSensor(hub, "bms_soh", "Battery SOH", PERCENTAGE, None, "mdi:battery-check", 0),

        EnergySensor(hub, "battery_charge_energy_today", "Battery Charge Energy Today", "mdi:battery-charging"),
        EnergySensor(hub, "battery_charge_energy_total", "Battery Charge Energy Total", "mdi:battery-charging"),
        EnergySensor(hub, "battery_discharge_energy_today", "Battery Discharge Energy Today", "mdi:battery-minus"),
        EnergySensor(hub, "battery_discharge_energy_total", "Battery Discharge Energy Total", "mdi:battery-minus"),

        SimpleSensor(hub, "grid_voltage", "Grid Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:transmission-tower", 1),
        SimpleSensor(hub, "grid_current", "Grid Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:transmission-tower", 1),
        SimpleSensor(hub, "grid_frequency", "Grid Frequency",
                     UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, "mdi:sine-wave", 2),
        SimpleSensor(hub, "grid_power", "Grid Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:transmission-tower", 0),

        EnergySensor(hub, "grid_in_energy_today", "Grid Import Energy Today", "mdi:transmission-tower-import"),
        EnergySensor(hub, "grid_in_energy_total", "Grid Import Energy Total", "mdi:transmission-tower-import"),
        EnergySensor(hub, "grid_out_energy_today", "Grid Export Energy Today", "mdi:transmission-tower-export"),
        EnergySensor(hub, "grid_out_energy_total", "Grid Export Energy Total", "mdi:transmission-tower-export"),

        SimpleSensor(hub, "eps_voltage", "EPS Voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:home-lightning-bolt", 1),
        SimpleSensor(hub, "eps_current", "EPS Current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:home-lightning-bolt", 1),
        SimpleSensor(hub, "eps_power", "EPS Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:home-lightning-bolt", 0),
        SimpleSensor(hub, "eps_active_power", "EPS Active Power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", 0),
        SimpleSensor(hub, "eps_apparent_power", "EPS Apparent Power",
                     UnitOfApparentPower.VOLT_AMPERE, None, "mdi:flash-outline", 0),

        EnergySensor(hub, "eps_energy_today", "EPS Energy Today", "mdi:home-lightning-bolt"),
        EnergySensor(hub, "eps_energy_total", "EPS Energy Total", "mdi:home-lightning-bolt"),

        GridStatusTextSensor(hub, "inverter_status", "Inverter Status"),
        BatteryStatusTextSensor(hub, "battery_status", "Battery Status"),

        FaultWord0TextSensor(hub, "fault_word0", "Fault Word0 Text"),

        WarningMainCodeSensor(hub, "warning_main", "Warning Main Code"),
        WarningMainTextSensor(hub, "warning_main", "Warning Main Text"),
        WarningSubCodeSensor(hub, "warning_sub", "Warning Sub Code"),
        WarningSubTextSensor(hub, "warning_sub", "Warning Sub Text"),

        WorkTimeSensor(hub, "total_work_time", "Total Work Time"),
    ]

    async_add_entities(entities)
