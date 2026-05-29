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

# =====================================================================
#  MAPY STAVŮ
# =====================================================================

GRID_STATUS_MAP = {
    0: "Waiting",
    1: "Grid mode",
    2: "Off‑grid mode",
    3: "Fault",
    4: "Flashing",
    5: "Bypass",
    6: "Self‑charging",
}

WARNING_MAIN_MAP = {
    0: "OK",
    103: "Grid unavailable",
    104: "Grid voltage out of range",
    105: "Grid frequency out of range",
    302: "Low battery",
    304: "Abnormal BMS information",
    305: "Low battery voltage alarm",
    502: "Abnormal memory read/write",
}

WARNING_SUB_MAP = {
    0: "OK",
}

FAULT_WORD0_MAP = {
    0: "No fault",
}

BATTERY_STATUS_MAP = {
    0: "OK",
    1: "Charging",
    2: "Discharging",
    3: "Idle",
}

# =====================================================================
#  BASE CLASS
# =====================================================================

class BaseSandiSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hub, key, name: str):
        self._hub = hub
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sandisolar_sensor_{name}"

    @property
    def device_info(self):
        return {
        "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
        "name": self._hub.get_cached("device_name") or "SANDISOLAR SD-PRO-EU",
        "manufacturer": "SANDISOLAR",
        "model": self._hub.get_cached("device_model") or "SD-PRO-EU 6.5K",
        }

# =====================================================================
#  SIMPLE SENSOR
# =====================================================================

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

        if self._decimals == 0:
            self._attr_native_value = int(val)
        else:
            self._attr_native_value = float(f"{val:.{self._decimals}f}")

# =====================================================================
#  ENERGY SENSOR
# =====================================================================

class EnergySensor(BaseSandiSensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, hub, key, name, unit, icon):
        super().__init__(hub, key, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._last_value = None

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        if val is None:
            return

        if self._last_value is not None and val < self._last_value:
            val = self._last_value

        self._last_value = val
        self._attr_native_value = float(f"{val:.1f}")

# =====================================================================
#  SPECIAL SENSORS
# =====================================================================

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

# =====================================================================
#  TEXT SENSORS
# =====================================================================

class FaultSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert-circle"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = val
        self._attr_extra_state_attributes = {
            "raw_value": val,
            "message": FAULT_WORD0_MAP.get(val, "Unknown fault code"),
        }

class WarningMainSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = val
        self._attr_extra_state_attributes = {
            "message": WARNING_MAIN_MAP.get(val, "Unknown warning code"),
        }

class WarningSubSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = val
        self._attr_extra_state_attributes = {
            "message": WARNING_SUB_MAP.get(val, "Unknown sub-warning code"),
        }

class WarningMainTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = WARNING_MAIN_MAP.get(val, "Unknown warning code")

class WarningSubTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = WARNING_SUB_MAP.get(val, "Unknown sub-warning code")

class FaultWord0TextSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert-circle"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = FAULT_WORD0_MAP.get(val, "Unknown fault code")

class BatteryStatusTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:battery"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = BATTERY_STATUS_MAP.get(val, "Unknown battery status")

class GridStatusTextSensor(BaseSandiSensor):
    _attr_icon = "mdi:transmission-tower"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = GRID_STATUS_MAP.get(val, "Unknown grid status")

# =====================================================================
#  BMS EXTENDED SENSORS
# =====================================================================

class BmsSimpleSensor(BaseSandiSensor):
    """Generic BMS sensor with scaling."""
    def __init__(self, hub, key, name, unit, icon, decimals=1):
        super().__init__(hub, key, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._decimals = decimals

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        if val is None:
            self._attr_native_value = None
            return
        self._attr_native_value = float(f"{val:.{self._decimals}f}")

class BmsIntSensor(BaseSandiSensor):
    """Integer BMS sensor."""
    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = int(val) if val is not None else None

# =====================================================================
#  SETUP ENTRY
# =====================================================================

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # PV
    entities += [
        SimpleSensor(hub, "pv1_voltage", "PV1_voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:solar-power", decimals=1),
        SimpleSensor(hub, "pv1_current", "PV1_current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:solar-power", decimals=1),

        SimpleSensor(hub, "pv2_voltage", "PV2_voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:solar-power", decimals=1),
        SimpleSensor(hub, "pv2_current", "PV2_current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:solar-power", decimals=1),

        SimpleSensor(hub, "pv_power_total", "PV_power_total",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:solar-power", decimals=0),

        EnergySensor(hub, "pv_energy_today", "PV_energy_today",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-power"),
        EnergySensor(hub, "pv_energy_total", "PV_energy_total",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-power"),
    ]

    # Battery
    entities += [
        SimpleSensor(hub, "battery_voltage", "Battery_voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:battery", decimals=1),

        SimpleSensor(hub, "battery_soc", "Battery_soc",
                     PERCENTAGE, SensorDeviceClass.BATTERY, "mdi:battery-high", decimals=0),

        SimpleSensor(hub, "battery_temp", "Battery_temp",
                     UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", decimals=1),

        SimpleSensor(hub, "battery_current", "Battery_current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-dc", decimals=1),

        BatteryPowerSensor(hub, "battery_power", "Battery_power"),

        EnergySensor(hub, "battery_charge_energy_today", "Battery_charge_energy_today",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-charging"),
        EnergySensor(hub, "battery_charge_energy_total", "Battery_charge_energy_total",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-charging"),

        EnergySensor(hub, "battery_discharge_energy_today", "Battery_discharge_energy_today",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-minus"),
        EnergySensor(hub, "battery_discharge_energy_total", "Battery_discharge_energy_total",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-minus"),
    ]

    # Grid
    entities += [
        SimpleSensor(hub, "grid_voltage", "Grid_voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:transmission-tower", decimals=1),
        SimpleSensor(hub, "grid_current", "Grid_current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:transmission-tower", decimals=1),
        SimpleSensor(hub, "grid_frequency", "Grid_frequency",
                     UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, "mdi:sine-wave", decimals=2),

        SimpleSensor(hub, "grid_power", "Grid_power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:transmission-tower", decimals=0),

        EnergySensor(hub, "grid_in_energy_today", "Grid_in_energy_today",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-import"),
        EnergySensor(hub, "grid_in_energy_total", "Grid_in_energy_total",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-import"),

        EnergySensor(hub, "grid_out_energy_today", "Grid_out_energy_today",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-export"),
        EnergySensor(hub, "grid_out_energy_total", "Grid_out_energy_total",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-export"),
    ]

    # EPS
    entities += [
        SimpleSensor(hub, "eps_voltage", "EPS_voltage",
                     UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:home-lightning-bolt", decimals=1),

        SimpleSensor(hub, "eps_current", "EPS_current",
                     UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:home-lightning-bolt", decimals=1),

        SimpleSensor(hub, "eps_active_power", "EPS_active_power",
                     UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", decimals=0),

        SimpleSensor(hub, "eps_apparent_power", "EPS_apparent_power",
                     UnitOfApparentPower.VOLT_AMPERE, None, "mdi:flash-outline", decimals=0),

        EnergySensor(hub, "eps_energy_today", "EPS_energy_today",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:home-lightning-bolt"),
        EnergySensor(hub, "eps_energy_total", "EPS_energy_total",
                     UnitOfEnergy.KILO_WATT_HOUR, "mdi:home-lightning-bolt"),
    ]

    # Faults & warnings
    entities += [
        FaultSensor(hub, "fault_word0", "Fault_word0"),
        FaultWord0TextSensor(hub, "fault_word0", "Fault_word0_text"),

        WarningMainSensor(hub, "warning_main", "Warning_main"),
        WarningMainTextSensor(hub, "warning_main", "Warning_main_text"),

        WarningSubSensor(hub, "warning_sub", "Warning_sub"),
        WarningSubTextSensor(hub, "warning_sub", "Warning_sub_text"),

        BatteryStatusTextSensor(hub, "battery_status", "Battery_status_text"),
        GridStatusTextSensor(hub, "inverter_status", "Grid_status_text"),
    ]

    # BMS extended
    entities += [
        BmsSimpleSensor(hub, "bms_fcc", "Battery_FCC_Ah",
                        UnitOfElectricCurrent.AMPERE, "mdi:battery-heart", decimals=1),

        BmsSimpleSensor(hub, "bms_rm", "Battery_RM_Ah",
                        UnitOfElectricCurrent.AMPERE, "mdi:battery-clock", decimals=1),

        BmsIntSensor(hub, "bms_soh", "Battery_SOH"),

        BmsIntSensor(hub, "bms_cycle_count", "Battery_Cycle_Count"),

        BmsSimpleSensor(hub, "bms_max_charge_current", "Battery_Max_Charge_Current",
                        UnitOfElectricCurrent.AMPERE, "mdi:battery-plus", decimals=1),

        BmsSimpleSensor(hub, "bms_max_discharge_current", "Battery_Max_Discharge_Current",
                        UnitOfElectricCurrent.AMPERE, "mdi:battery-minus", decimals=1),
    ]
 # Device info sensors
    entities += [
        SimpleSensor(hub, "device_model", "Device_Model",
                     None, None, "mdi:identifier", decimals=0),

        SimpleSensor(hub, "device_name", "Device_Name",
                     None, None, "mdi:label", decimals=0),

        SimpleSensor(hub, "total_work_time", "Total_Work_Time",
                     "h", None, "mdi:clock-time-eight", decimals=0),
    ]
    async_add_entities(entities)
