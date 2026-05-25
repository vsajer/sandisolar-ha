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
    # PV
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

    # Battery
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

    # Grid
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

    # Load
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
}


# ---------------------------------------------------------------------------
# HOLDING REGISTERS (READ + WRITE)
# ---------------------------------------------------------------------------

HOLDING_REGISTERS: Dict[str, RegisterDefinition] = {
    # Switches
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

    # Number entities
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
