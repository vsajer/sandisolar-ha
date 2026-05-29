from dataclasses import dataclass


@dataclass
class RegisterDef:
    address: int
    scale: float = 1.0
    count: int = 1
    signed: bool = False


INPUT_REGISTERS = {
    "inverter_status": RegisterDef(0),

    "inv_temp": RegisterDef(10, 0.1, signed=True),
    "boost_temp": RegisterDef(11, 0.1, signed=True),
    "llc_temp": RegisterDef(12, 0.1, signed=True),
    "battery_temp": RegisterDef(142, 0.1, signed=True),
    "ambient_temp": RegisterDef(14, 0.1, signed=True),

    "fault_word0": RegisterDef(24),
    "warning_main": RegisterDef(33),
    "warning_sub": RegisterDef(35),

    "grid_voltage": RegisterDef(42, 0.1),
    "grid_current": RegisterDef(43, 0.1, signed=True),
    "grid_frequency": RegisterDef(51, 0.01),
    "grid_power": RegisterDef(328, 0.1, count=2, signed=True),

    "eps_voltage": RegisterDef(55, 0.1),
    "eps_current": RegisterDef(56, 0.1),
    "eps_power": RegisterDef(330, 0.1, count=2),
    "eps_apparent_power": RegisterDef(332, 0.1, count=2),
    "eps_active_power": RegisterDef(334, 0.1, count=2),
    "eps_energy_today": RegisterDef(407, 0.1, count=2),
    "eps_energy_total": RegisterDef(409, 0.1, count=2),

    "pv1_voltage": RegisterDef(64, 0.1),
    "pv1_current": RegisterDef(65, 0.1),
    "pv2_voltage": RegisterDef(66, 0.1),
    "pv2_current": RegisterDef(67, 0.1),
    "pv_power_total": RegisterDef(250, 0.1, count=2),

    "battery_voltage": RegisterDef(127, 0.1),
    "battery_soc": RegisterDef(128),
    "battery_status": RegisterDef(130),
    "battery_current": RegisterDef(141, 0.01, signed=True),
    "battery_discharge_power": RegisterDef(349, 0.1, count=2),
    "battery_charge_power": RegisterDef(351, 0.1, count=2),

    "bms_max_charge_current": RegisterDef(143, 0.1),
    "bms_max_discharge_current": RegisterDef(144, 0.1),
    "bms_fcc": RegisterDef(145, 0.1),
    "bms_rm": RegisterDef(146, 0.1),
    "bms_cycle_count": RegisterDef(151),
    "bms_soh": RegisterDef(152),

    "pv_energy_today": RegisterDef(379, 0.1, count=2),
    "pv_energy_total": RegisterDef(381, 0.1, count=2),

    "battery_charge_energy_today": RegisterDef(383, 0.1, count=2),
    "battery_charge_energy_total": RegisterDef(385, 0.1, count=2),
    "battery_discharge_energy_today": RegisterDef(387, 0.1, count=2),
    "battery_discharge_energy_total": RegisterDef(389, 0.1, count=2),

    "grid_out_energy_today": RegisterDef(411, 0.1, count=2),
    "grid_out_energy_total": RegisterDef(413, 0.1, count=2),
    "grid_in_energy_today": RegisterDef(415, 0.1, count=2),
    "grid_in_energy_total": RegisterDef(417, 0.1, count=2),

    "total_work_time": RegisterDef(107, scale=1, count=2),
}


HOLDING_REGISTERS = {
    "inverter_on_off": RegisterDef(0),

    "device_id": RegisterDef(3),
    "ac_input_type": RegisterDef(209),

    "eps_enable": RegisterDef(108),
    "bypass_enable": RegisterDef(109),
    "ups_enable": RegisterDef(110),

    "charge_limit": RegisterDef(137),
    "discharge_limit": RegisterDef(138),
    "end_of_charge_soc": RegisterDef(139),

    "on_grid_discharge_soc": RegisterDef(140),
    "off_grid_discharge_soc": RegisterDef(141),

    "ac_charge_enable": RegisterDef(145),

    "charge_priority": RegisterDef(181),
    "source_priority": RegisterDef(182),

    "on_grid_recovery_soc": RegisterDef(185),
    "off_grid_recovery_soc": RegisterDef(187),

    "ac_charge_current_limit": RegisterDef(189, 0.1),

    "lcd_settings_bitmask": RegisterDef(201),
    "beeper_on_off": RegisterDef(207),

    "gen_port_work_mode": RegisterDef(216),
    "sec_eps_on_soc": RegisterDef(219, 0.01),
    "sec_eps_on_vbat": RegisterDef(220, 0.1),
    "sec_eps_off_soc": RegisterDef(221, 0.01),
    "sec_eps_off_vbat": RegisterDef(222, 0.1),
    "sec_eps_on_pv_power_min": RegisterDef(223, 10),
}
