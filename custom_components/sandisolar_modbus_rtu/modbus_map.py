from dataclasses import dataclass

@dataclass
class RegisterDef:
    """Simple register definition used by the integration.

    - address: Modbus register address (decimal)
    - scale: multiply raw value by this to get real value (default 1.0)
    - count: number of 16-bit registers (for 32-bit values or ASCII blocks)
    - signed: whether the raw value should be interpreted as signed
    """
    address: int
    scale: float = 1.0
    count: int = 1
    signed: bool = False


# =====================================================================
# INPUT REGISTERS (READ-ONLY)
# =====================================================================

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

    # BMS extended
    "bms_max_charge_current": RegisterDef(143, 0.1),
    "bms_max_discharge_current": RegisterDef(144, 0.1),
    "bms_fcc": RegisterDef(145, 0.1),
    "bms_rm": RegisterDef(146, 0.1),
    "bms_cycle_count": RegisterDef(151),
    "bms_soh": RegisterDef(152),

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
    "eps_voltage": RegisterDef(55, 0.1),
    "eps_current": RegisterDef(56, 0.1),
    "eps_apparent_power": RegisterDef(332, 0.1, count=2),
    "eps_active_power": RegisterDef(334, 0.1, count=2),

    "eps_energy_today": RegisterDef(407, 0.1, count=2),
    "eps_energy_total": RegisterDef(409, 0.1, count=2),

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

    # Status text sensors
    "battery_status": RegisterDef(130),
    "inverter_status": RegisterDef(0),

    # ---------------------------------------------------------
    # DEVICE INFO (ASCII)
    # ---------------------------------------------------------
    # device_model and device_name are ASCII blocks (count registers)
    "device_model": RegisterDef(0, scale=1, count=2),
    "device_name": RegisterDef(2, scale=1, count=2),

    # Total work time (uint32)
    "total_work_time": RegisterDef(46, scale=1, count=2),

    # ---------------------------------------------------------
    # FIRMWARE (ASCII + uint16)
    # ---------------------------------------------------------
    "fw_main_version": RegisterDef(28, scale=1, count=3),
    "fw_arm_name": RegisterDef(31, scale=1, count=2),
    "fw_arm_version": RegisterDef(33),
    "fw_dsp_name": RegisterDef(34, scale=1, count=2),
    "fw_dsp1_version": RegisterDef(36),
    "fw_dsp2_version": RegisterDef(37),
    "fw_dsp1_debug": RegisterDef(38),
    "fw_dsp2_debug": RegisterDef(39),
    "fw_arm_debug": RegisterDef(40),
}


# =====================================================================
# HOLDING REGISTERS (READ/WRITE)
# =====================================================================

HOLDING_REGISTERS = {
    # On/Off / basic control
    "inverter_on_off": RegisterDef(0),

    # System / communication
    "device_id": RegisterDef(3),

    # EPS / BYPASS / UPS
    "eps_enable": RegisterDef(108),       # reg 108: EPS enable
    "bypass_enable": RegisterDef(109),    # reg 109: Bypass enable
    "ups_enable": RegisterDef(110),       # reg 110: UPS mode (already present)

    # AC input type (APL / UPS)
    "ac_input_type": RegisterDef(209),    # reg 209: AC input type (APL/UPS)

    # Beeper / LCD
    "lcd_settings_bitmask": RegisterDef(201),  # reg 201: LCD settings bitmask
    "beeper_on_off": RegisterDef(207),         # reg 207: Beeper on/off

    # Battery power settings (percent / limits)
    "charge_limit": RegisterDef(137),      # reg 137: ChargeRate %
    "discharge_limit": RegisterDef(138),   # reg 138: DischargeRate %
    "end_of_charge_soc": RegisterDef(139), # reg 139: Charge Stop SOC (Charge Stop)
    "ac_charge_enable": RegisterDef(145),  # reg 145: AC Charge Enable

    # AC charge current limit (0.1 A units)
    "ac_charge_current_limit": RegisterDef(189, 0.1),  # reg 189: AC charge current limit (scale 0.1A)

    # SOC limits / recovery
    "on_grid_discharge_soc": RegisterDef(140),   # reg 140: Stop Discharge SOC (on-grid)
    "off_grid_discharge_soc": RegisterDef(141),  # reg 141: Stop Discharge SOC (off-grid)
    "on_grid_recovery_soc": RegisterDef(185),    # reg 185: On-grid recovery SOC
    "off_grid_recovery_soc": RegisterDef(187),   # reg 187: Off-grid recovery SOC

    # Smart Load (SecEPS) SOC and voltage thresholds
    "sec_eps_on_soc": RegisterDef(219),    # reg 219: Smart Load ON SOC (%)
    "sec_eps_on_vbat": RegisterDef(220, 0.1),   # reg 220: Smart Load ON Vbat (0.1 V) - optional
    "sec_eps_off_soc": RegisterDef(221),   # reg 221: Smart Load OFF SOC (%)
    "sec_eps_off_vbat": RegisterDef(222, 0.1),  # reg 222: Smart Load OFF Vbat (0.1 V) - optional

    # Smart Load manual override (if device supports direct manual control)
    # NOTE: many devices do not have a dedicated "smart load on/off" holding register.
    # If your device exposes a specific register for manual override, replace the address below
    # with the correct one. Otherwise implement override by writing a special control flag/register.
    "smart_load_override": RegisterDef(223),  # reg 223: manual override (reserved / device dependent)

    # Priority modes / charge source
    "charge_priority": RegisterDef(181),    # reg 181: Charge source priority
    "source_priority": RegisterDef(182),    # reg 182: Source priority

}

# End of modbus_map
