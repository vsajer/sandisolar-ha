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
from .const import DOMAIN
from .modbus_map import INPUT_REGISTERS

_LOGGER = logging.getLogger(__name__)

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


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # PV
    entities += [
        SimpleSensor(hub, "pv1_voltage", "PV Voltage 1", UnitOfElectricPotential.VOLT, "voltage", "mdi:solar-power"),
        SimpleSensor(hub, "pv1_current", "PV Current 1", UnitOfElectricCurrent.AMPERE, "current", "mdi:solar-power"),
        SimpleSensor(hub, "pv2_voltage", "PV Voltage 2", UnitOfElectricPotential.VOLT, "voltage", "mdi:solar-power"),
        SimpleSensor(hub, "pv2_current", "PV Current 2", UnitOfElectricCurrent.AMPERE, "current", "mdi:solar-power"),
        SimpleSensor(hub, "pv_power_total", "PV Power Total", UnitOfPower.WATT, "power", "mdi:solar-power"),
        SimpleSensor(hub, "pv_energy_today", "PV Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:solar-power", total=True),
        SimpleSensor(hub, "pv_energy_total", "PV Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:solar-power", total=True),
    ]

    # Battery
    entities += [
        SimpleSensor(hub, "battery_voltage", "Battery Voltage", UnitOfElectricPotential.VOLT, "voltage", "mdi:battery"),
        SimpleSensor(hub, "battery_soc", "Battery State Of Charge", PERCENTAGE, "battery", "mdi:battery-high"),
        SimpleSensor(hub, "battery_temp", "Battery Temperature", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer"),
        BatteryPowerSensor(hub, "battery_power", "Battery Power"),
        SimpleSensor(hub, "battery_charge_energy_today", "Battery Charge Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:battery-charging", total=True),
        SimpleSensor(hub, "battery_charge_energy_total", "Battery Charge Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:battery-charging", total=True),
        SimpleSensor(hub, "battery_discharge_energy_today", "Battery Discharge Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:battery-minus", total=True),
        SimpleSensor(hub, "battery_discharge_energy_total", "Battery Discharge Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:battery-minus", total=True),
    ]

    # Grid
    entities += [
        SimpleSensor(hub, "grid_voltage", "Grid Voltage", UnitOfElectricPotential.VOLT, "voltage", "mdi:transmission-tower"),
        SimpleSensor(hub, "grid_current", "Grid Current", UnitOfElectricCurrent.AMPERE, "current", "mdi:transmission-tower"),
        SimpleSensor(hub, "grid_frequency", "Grid Frequency", UnitOfFrequency.HERTZ, "frequency", "mdi:sine-wave"),
        SimpleSensor(hub, "grid_power", "Grid Power", UnitOfPower.WATT, "power", "mdi:transmission-tower"),
        SimpleSensor(hub, "grid_in_energy_today", "Grid In Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:transmission-tower-import", total=True),
        SimpleSensor(hub, "grid_in_energy_total", "Grid In Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:transmission-tower-import", total=True),
        SimpleSensor(hub, "grid_out_energy_today", "Grid Out Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:transmission-tower-export", total=True),
        SimpleSensor(hub, "grid_out_energy_total", "Grid Out Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:transmission-tower-export", total=True),
    ]

    # EPS
    entities += [
        SimpleSensor(hub, "eps_voltage", "EPS Voltage", UnitOfElectricPotential.VOLT, "voltage", "mdi:home-lightning-bolt"),
        SimpleSensor(hub, "eps_current", "EPS Current", UnitOfElectricCurrent.AMPERE, "current", "mdi:home-lightning-bolt"),
        SimpleSensor(hub, "eps_active_power", "EPS Active Power", UnitOfPower.WATT, "power", "mdi:flash"),
        SimpleSensor(hub, "eps_apparent_power", "EPS Apparent Power", UnitOfApparentPower.VOLT_AMPERE, None, "mdi:flash-outline"),
        SimpleSensor(hub, "eps_energy_today", "EPS Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:home-lightning-bolt", total=True),
        SimpleSensor(hub, "eps_energy_total", "EPS Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:home-lightning-bolt", total=True),
    ]

    # Load
    entities += [
        SimpleSensor(hub, "load_energy_today", "Load Energy Today", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:home-lightning-bolt", total=True),
        SimpleSensor(hub, "load_energy_total", "Load Energy Total", UnitOfEnergy.KILO_WATT_HOUR, "energy", "mdi:home-lightning-bolt", total=True),
    ]

    # Temperatures
    entities += [
        SimpleSensor(hub, "inv_temp", "Inverter Temperature", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer"),
        SimpleSensor(hub, "boost_temp", "Boost Temperature", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer"),
        SimpleSensor(hub, "llc_temp", "LLC Temperature", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer"),
        AmbientTempSensor(hub, "ambient_temp", "Ambient Temperature", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer"),
    ]

    # Faults & warnings
    entities += [
        FaultSensor(hub, "fault_word0", "Fault Word 0"),
        WarningMainSensor(hub, "warning_main", "Warning Main"),
        WarningSubSensor(hub, "warning_sub", "Warning Sub"),
    ]

    async_add_entities(entities)


# -------------------------------------------------------------------
# BASE SENSOR CLASS
# -------------------------------------------------------------------

class BaseSandiSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hub, key, name):
        self._hub = hub
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sandisolar_sensor_{key}"

    @property
    def device_info(self):
        return {
            "identifiers": {("sandisolar_modbus_rtu", "sdproeu_main")},
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU 6.5K",
        }


# -------------------------------------------------------------------
# SIMPLE SENSOR
# -------------------------------------------------------------------

class SimpleSensor(BaseSandiSensor):
    def __init__(self, hub, key, name, unit, device_class, icon, total=False):
        super().__init__(hub, key, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        if total:
            self._attr_state_class = "total_increasing"

    async def async_update(self):
        self._attr_native_value = await self._hub.read_input_register(self._key)


# -------------------------------------------------------------------
# BATTERY POWER SENSOR
# -------------------------------------------------------------------

class BatteryPowerSensor(BaseSandiSensor):
    _attr_icon = "mdi:battery-sync"
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    async def async_update(self):
        discharge = await self._hub.read_input_register("battery_discharge_power")
        charge = await self._hub.read_input_register("battery_charge_power")

        if discharge is None or charge is None:
            self._attr_native_value = None
            return

        self._attr_native_value = discharge - charge


# -------------------------------------------------------------------
# AMBIENT TEMP SENSOR
# -------------------------------------------------------------------

class AmbientTempSensor(SimpleSensor):
    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = None if val == 0 else val


# -------------------------------------------------------------------
# FAULT SENSOR
# -------------------------------------------------------------------

class FaultSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert-circle"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = val
        self._attr_extra_state_attributes = {
            "type": "bitmask",
            "raw_value": val,
        }


# -------------------------------------------------------------------
# WARNING MAIN SENSOR
# -------------------------------------------------------------------

class WarningMainSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = val
        self._attr_extra_state_attributes = {
            "message": WARNING_MAIN_MAP.get(val, "Unknown"),
        }


# -------------------------------------------------------------------
# WARNING SUB SENSOR
# -------------------------------------------------------------------

class WarningSubSensor(BaseSandiSensor):
    _attr_icon = "mdi:alert"

    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = val
        self._attr_extra_state_attributes = {
            "message": "Sub-warning code",
        }
