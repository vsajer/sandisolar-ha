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


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # PV
    entities += [
        SimpleSensor(
            hub,
            "pv1_voltage",
            "PV1_voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            "mdi:solar-power",
        ),
        SimpleSensor(
            hub,
            "pv1_current",
            "PV1_current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            "mdi:solar-power",
        ),
        SimpleSensor(
            hub,
            "pv2_voltage",
            "PV2_voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            "mdi:solar-power",
        ),
        SimpleSensor(
            hub,
            "pv2_current",
            "PV2_current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            "mdi:solar-power",
        ),
        SimpleSensor(
            hub,
            "pv_power_total",
            "PV_power_total",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            "mdi:solar-power",
        ),
        EnergySensor(
            hub,
            "pv_energy_today",
            "PV_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:solar-power",
        ),
        EnergySensor(
            hub,
            "pv_energy_total",
            "PV_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:solar-power",
        ),
    ]

    # Battery
    entities += [
        SimpleSensor(
            hub,
            "battery_voltage",
            "Battery_voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            "mdi:battery",
        ),
        SimpleSensor(
            hub,
            "battery_soc",
            "Battery_soc",
            PERCENTAGE,
            SensorDeviceClass.BATTERY,
            "mdi:battery-high",
        ),
        SimpleSensor(
            hub,
            "battery_temp",
            "Battery_temp",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            "mdi:thermometer",
        ),
        SimpleSensor(
            hub,
            "battery_current",
            "Battery_amp",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            "mdi:current-dc",
        ),
        BatteryPowerSensor(
            hub,
            "battery_power",
            "Battery_power",
        ),
        EnergySensor(
            hub,
            "battery_charge_energy_today",
            "Battery_charge_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:battery-charging",
        ),
        EnergySensor(
            hub,
            "battery_charge_energy_total",
            "Battery_charge_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:battery-charging",
        ),
        EnergySensor(
            hub,
            "battery_discharge_energy_today",
            "Battery_discharge_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:battery-minus",
        ),
        EnergySensor(
            hub,
            "battery_discharge_energy_total",
            "Battery_discharge_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:battery-minus",
        ),
    ]

    # Grid
    entities += [
        SimpleSensor(
            hub,
            "grid_voltage",
            "Grid_voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            "mdi:transmission-tower",
        ),
        SimpleSensor(
            hub,
            "grid_current",
            "Grid_current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            "mdi:transmission-tower",
        ),
        SimpleSensor(
            hub,
            "grid_frequency",
            "Grid_frequency",
            UnitOfFrequency.HERTZ,
            SensorDeviceClass.FREQUENCY,
            "mdi:sine-wave",
        ),
        SimpleSensor(
            hub,
            "grid_power",
            "Grid_power",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            "mdi:transmission-tower",
        ),
        EnergySensor(
            hub,
            "grid_in_energy_today",
            "Grid_in_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:transmission-tower-import",
        ),
        EnergySensor(
            hub,
            "grid_in_energy_total",
            "Grid_in_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:transmission-tower-import",
        ),
        EnergySensor(
            hub,
            "grid_out_energy_today",
            "Grid_out_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:transmission-tower-export",
        ),
        EnergySensor(
            hub,
            "grid_out_energy_total",
            "Grid_out_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:transmission-tower-export",
        ),
    ]

    # EPS
    entities += [
        SimpleSensor(
            hub,
            "eps_voltage",
            "EPS_voltage",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            "mdi:home-lightning-bolt",
        ),
        SimpleSensor(
            hub,
            "eps_current",
            "EPS_current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            "mdi:home-lightning-bolt",
        ),
        SimpleSensor(
            hub,
            "eps_active_power",
            "EPS_active_power",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            "mdi:flash",
        ),
        SimpleSensor(
            hub,
            "eps_apparent_power",
            "EPS_apparent_power",
            UnitOfApparentPower.VOLT_AMPERE,
            None,
            "mdi:flash-outline",
        ),
        EnergySensor(
            hub,
            "eps_energy_today",
            "EPS_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:home-lightning-bolt",
        ),
        EnergySensor(
            hub,
            "eps_energy_total",
            "EPS_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:home-lightning-bolt",
        ),
    ]

    # Load
    entities += [
        EnergySensor(
            hub,
            "load_energy_today",
            "Load_energy_today",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:home-lightning-bolt",
        ),
        EnergySensor(
            hub,
            "load_energy_total",
            "Load_energy_total",
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:home-lightning-bolt",
        ),
    ]

    # Inverter temperatures
    entities += [
        SimpleSensor(
            hub,
            "inv_temp",
            "Inverter_inv_temp",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            "mdi:thermometer",
        ),
        SimpleSensor(
            hub,
            "boost_temp",
            "Inverter_boost_temp",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            "mdi:thermometer",
        ),
        SimpleSensor(
            hub,
            "llc_temp",
            "Inverter_llc_temp",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            "mdi:thermometer",
        ),
        AmbientTempSensor(
            hub,
            "ambient_temp",
            "Inverter_ambient_temp",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            "mdi:thermometer",
        ),
    ]

    # Faults & warnings
    entities += [
        FaultSensor(hub, "fault_word0", "Fault_word0"),
        WarningMainSensor(hub, "warning_main", "Warning_main"),
        WarningSubSensor(hub, "warning_sub", "Warning_sub"),
    ]

    async_add_entities(entities)


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
            "name": "SANDISOLAR SD-PRO-EU",
            "manufacturer": "SANDISOLAR",
            "model": "SD-PRO-EU 6.5K",
        }


class SimpleSensor(BaseSandiSensor):
    def __init__(self, hub, key, name, unit, device_class, icon):
        super().__init__(hub, key, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon

    async def async_update(self):
        self._attr_native_value = await self._hub.read_input_register(self._key)


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
            _LOGGER.debug(
                "EnergySensor %s: new value %.3f < last value %.3f, keeping last",
                self._key,
                val,
                self._last_value,
            )
            val = self._last_value

        self._last_value = val
        self._attr_native_value = val


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

        self._attr_native_value = discharge - charge


class AmbientTempSensor(SimpleSensor):
    async def async_update(self):
        val = await self._hub.read_input_register(self._key)
        self._attr_native_value = None if val == 0 else val


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
