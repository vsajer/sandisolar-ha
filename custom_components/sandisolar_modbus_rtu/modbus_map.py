from dataclasses import dataclass

@dataclass
class RegisterDef:
    address: int
    scale: float = 1.0
    count: int = 1
    signed: bool = False


INPUT_REGISTERS = {
    # PV
    "pv1_voltage": RegisterDef(64, 0.1),
    "pv1_current": RegisterDef(65, 0.1),
    "pv2_voltage": RegisterDef(66, 0.1),
    "pv2_current": RegisterDef(67, 0.1),

    "pv_power_total": RegisterDef(250, 0.1, count=2),

    "pv_energy_today": RegisterDef(379, 0.1, count=2),
    "pv_energy_total": RegisterDef(381, 0.1, count=2),

    # Battery
    "battery_voltage": RegisterDef(127, 0.1),
    "battery_soc": RegisterDef(128, 1),
    "battery_current": RegisterDef(141, 0.01, signed=True),
    "battery_temp": RegisterDef(142, 0.1, signed=True),

    "battery_discharge_power": RegisterDef(349, 0.1, count=2),
    "battery_charge_power": RegisterDef(351, 0.1, count=2),

    "battery_charge_energy_today": RegisterDef(383, 0.1, count=2),
    "battery_charge_energy_total": RegisterDef(385, 0.1, count=2),
    "battery_discharge_energy_today": RegisterDef(387, 0.1, count=2),
    "battery_discharge_energy_total": RegisterDef(389, 0.1, count=2),

    # Grid
    "grid_voltage": RegisterDef(42, 0.1),
    "grid_current": RegisterDef(43, 0.1, signed=True),
    "grid_frequency": RegisterDef(51, 0.01),
    "grid_power": RegisterDef(322, 0.1, count=2, signed=True),

    "grid_out_energy_today": RegisterDef(411, 0.1, count=2),
    "grid_out_energy_total": RegisterDef(413, 0.1, count=2),
    "grid_in_energy_today": RegisterDef(415, 0.1, count=2),
    "grid_in_energy_total": RegisterDef(417, 0.1, count=2),

    # EPS
    "eps_frequency": RegisterDef(54, 0.01),
    "eps_voltage": RegisterDef(55, 0.1),
    "eps_current": RegisterDef(56, 0.1),
    "eps_apparent_power": RegisterDef(332, 0.1, count=2),
    "eps_active_power": RegisterDef(334, 0.1, count=2),

    "eps_energy_today": RegisterDef(407, 0.1, count=2),
    "eps_energy_total": RegisterDef(409, 0.1, count=2),

    # Load (POZOR: stejné registry jako EPS – ověř!)
    "load_energy_today": RegisterDef(407, 0.1, count=2),
    "load_energy_total": RegisterDef(409, 0.1, count=2),

    # Temperatures
    "inv_temp": RegisterDef(10, 0.1, signed=True),
    "boost_temp": RegisterDef(11, 0.1, signed=True),
    "llc_temp": RegisterDef(12, 0.1, signed=True),
    "ambient_temp": RegisterDef(14, 0.1, signed=True),

    # Faults & warnings
    "fault_word0": RegisterDef(24),
    "fault_word1": RegisterDef(25),
    "warning_main": RegisterDef(33),
    "warning_sub": RegisterDef(35),
}


HOLDING_REGISTERS = {
    "on_off": RegisterDef(0),
    "charge_limit": RegisterDef(137),
    "discharge_limit": RegisterDef(138),
    "ac_charge_enable": RegisterDef(145),

    "charge_priority": RegisterDef(181),
    "source_priority": RegisterDef(182),
}
"""Register map for SANDISOLAR SD-PRO-EU Modbus RTU integration."""

from dataclasses import dataclass
from typing import Optional, Dict


# ---------------------------------------------------------------------------
# Register Definition
# ---------------------------------------------------------------------------

@dataclass
class RegisterDefinition:
    key: str
    address: int
    count: int
    scale: float
    unit: Optional[str]
    name_en: str
    name_cs: str
    icon: str
    writable: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None


# ---------------------------------------------------------------------------
# INPUT REGISTERS (READ ONLY)
# ---------------------------------------------------------------------------

INPUT_REGISTERS: Dict[str, RegisterDefinition] = {

    # -----------------------------------------------------------------------
    # PV (Solar)
    # -----------------------------------------------------------------------
    "pv_voltage": RegisterDefinition(
        key="pv_voltage",
        address=64,
        count=1,
        scale=0.1,
        unit="V",
        name_en="PV Voltage",
        name_cs="Napětí FV",
        icon="mdi:solar-power",
    ),
    "pv_current": RegisterDefinition(
        key="pv_current",
        address=65,
        count=1,
        scale=0.1,
        unit="A",
        name_en="PV Current",
        name_cs="Proud FV",
        icon="mdi:current-dc",
    ),
    "pv_power": RegisterDefinition(
        key="pv_power",
        address=250,
        count=1,
        scale=1,
        unit="W",
        name_en="PV Power",
        name_cs="Výkon FV",
        icon="mdi:solar-power",
    ),
    "pv_status": RegisterDefinition(
        key="pv_status",
        address=251,
        count=1,
        scale=1,
        unit=None,
        name_en="PV Status",
        name_cs="Stav FV",
        icon="mdi:information",
    ),

    # -----------------------------------------------------------------------
    # Battery
    # -----------------------------------------------------------------------
    "battery_voltage": RegisterDefinition(
        key="battery_voltage",
        address=70,
        count=1,
        scale=0.1,
        unit="V",
        name_en="Battery Voltage",
        name_cs="Napětí baterie",
        icon="mdi:battery",
    ),
    "battery_current": RegisterDefinition(
        key="battery_current",
        address=71,
        count=1,
        scale=0.1,
        unit="A",
        name_en="Battery Current",
        name_cs="Proud baterie",
        icon="mdi:current-dc",
    ),
    "battery_soc": RegisterDefinition(
        key="battery_soc",
        address=72,
        count=1,
        scale=1,
        unit="%",
        name_en="Battery SOC",
        name_cs="Stav nabití baterie",
        icon="mdi:battery-high",
    ),
    "battery_temperature": RegisterDefinition(
        key="battery_temperature",
        address=73,
        count=1,
        scale=0.1,
        unit="°C",
        name_en="Battery Temperature",
        name_cs="Teplota baterie",
        icon="mdi:thermometer",
    ),
    "battery_status": RegisterDefinition(
        key="battery_status",
        address=74,
        count=1,
        scale=1,
        unit=None,
        name_en="Battery Status",
        name_cs="Stav baterie",
        icon="mdi:information",
    ),

    # -----------------------------------------------------------------------
    # Grid (AC Input)
    # -----------------------------------------------------------------------
    "grid_voltage": RegisterDefinition(
        key="grid_voltage",
        address=80,
        count=1,
        scale=0.1,
        unit="V",
        name_en="Grid Voltage",
        name_cs="Napětí sítě",
        icon="mdi:transmission-tower",
    ),
    "grid_frequency": RegisterDefinition(
        key="grid_frequency",
        address=81,
        count=1,
        scale=0.1,
        unit="Hz",
        name_en="Grid Frequency",
        name_cs="Frekvence sítě",
        icon="mdi:sine-wave",
    ),
    "grid_power": RegisterDefinition(
        key="grid_power",
        address=260,
        count=1,
        scale=1,
        unit="W",
        name_en="Grid Power",
        name_cs="Výkon ze sítě",
        icon="mdi:flash",
    ),
    "grid_status": RegisterDefinition(
        key="grid_status",
        address=261,
        count=1,
        scale=1,
        unit=None,
        name_en="Grid Status",
        name_cs="Stav sítě",
        icon="mdi:information",
    ),

    # -----------------------------------------------------------------------
    # Load (AC Output)
    # -----------------------------------------------------------------------
    "load_power": RegisterDefinition(
        key="load_power",
        address=300,
        count=1,
        scale=1,
        unit="W",
        name_en="Load Power",
        name_cs="Zátěž",
        icon="mdi:home-lightning-bolt",
    ),
    "output_load": RegisterDefinition(
        key="output_load",
        address=301,
        count=1,
        scale=1,
        unit="%",
        name_en="Output Load",
        name_cs="Zatížení výstupu",
        icon="mdi:gauge",
    ),

    # -----------------------------------------------------------------------
    # Inverter Status
    # -----------------------------------------------------------------------
    "inverter_status": RegisterDefinition(
        key="inverter_status",
        address=310,
        count=1,
        scale=1,
        unit=None,
        name_en="Inverter Status",
        name_cs="Stav měniče",
        icon="mdi:information",
    ),
    "temperature": RegisterDefinition(
        key="temperature",
        address=311,
        count=1,
        scale=0.1,
        unit="°C",
        name_en="Inverter Temperature",
        name_cs="Teplota měniče",
        icon="mdi:thermometer",
    ),
    "error_code": RegisterDefinition(
        key="error_code",
        address=312,
        count=1,
        scale=1,
        unit=None,
        name_en="Error Code",
        name_cs="Chybový kód",
        icon="mdi:alert-circle",
    ),
}


# ---------------------------------------------------------------------------
# HOLDING REGISTERS (READ + WRITE)
# ---------------------------------------------------------------------------

HOLDING_REGISTERS: Dict[str, RegisterDefinition] = {

    # -----------------------------------------------------------------------
    # Switches (ON/OFF)
    # -----------------------------------------------------------------------
    "inverter_onoff": RegisterDefinition(
        key="inverter_onoff",
        address=0,
        count=1,
        scale=1,
        unit=None,
        name_en="Inverter ON/OFF",
        name_cs="Měnič zap/vyp",
        icon="mdi:power",
        writable=True,
        min_value=0,
        max_value=1,
    ),
    "ac_charge_enable": RegisterDefinition(
        key="ac_charge_enable",
        address=145,
        count=1,
        scale=1,
        unit=None,
        name_en="AC Charge Enable",
        name_cs="Povolit AC nabíjení",
        icon="mdi:power-plug",
        writable=True,
        min_value=0,
        max_value=1,
    ),
    "battery_discharge_enable": RegisterDefinition(
        key="battery_discharge_enable",
        address=146,
        count=1,
        scale=1,
        unit=None,
        name_en="Battery Discharge Enable",
        name_cs="Povolit vybíjení baterie",
        icon="mdi:battery-arrow-down",
        writable=True,
        min_value=0,
        max_value=1,
    ),

    # -----------------------------------------------------------------------
    # Limits / Numbers
    # -----------------------------------------------------------------------
    "ac_charge_soc_limit": RegisterDefinition(
        key="ac_charge_soc_limit",
        address=150,
        count=1,
        scale=1,
        unit="%",
        name_en="AC Charge SOC Limit",
        name_cs="Limit SOC pro AC nabíjení",
        icon="mdi:battery-charging-80",
        writable=True,
        min_value=0,
        max_value=100,
    ),
    "battery_discharge_soc_limit": RegisterDefinition(
        key="battery_discharge_soc_limit",
        address=151,
        count=1,
        scale=1,
        unit="%",
        name_en="Battery Discharge SOC Limit",
        name_cs="Limit SOC pro vybíjení",
        icon="mdi:battery-arrow-down",
        writable=True,
        min_value=0,
        max_value=100,
    ),
    "ac_charge_current": RegisterDefinition(
        key="ac_charge_current",
        address=152,
        count=1,
        scale=1,
        unit="A",
        name_en="AC Charge Current",
        name_cs="AC nabíjecí proud",
        icon="mdi:current-ac",
        writable=True,
        min_value=0,
        max_value=50,
    ),
}
