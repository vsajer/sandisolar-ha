# SANDISOLAR / SD-PRO-EU – Modbus RTU Integration for Home Assistant

Hybridní měnič **SANDISOLAR SD-PRO-EU** konečně pořádně v Home Assistantu — bez cloudu, přes **Modbus RTU / RS485**, s rychlou odezvou, přehlednými senzory, ovládáním a pokročilými výpočty.

<img width="250" height="250" alt="SandiSolar_HA" src="https://github.com/vsajer/sandisolar-ha/blob/main/custom_components/sandisolar_modbus_rtu/brand/logo.png" />

[![HACS](https://img.shields.io/badge/HACS-Custom-blue.svg)]()
[![Version](https://img.shields.io/github/v/release/vsajer/sandisolar-ha)]()
[![License](https://img.shields.io/github/license/vsajer/sandisolar-ha)]()

Native Home Assistant integration for the **SANDISOLAR SD-PRO-EU Hybrid Inverter** using **Modbus RTU over RS485**.

Monitor solar production, battery state, grid import/export, EPS backup output, inverter temperatures, alarms and energy counters directly in Home Assistant. Control charging, discharge limits, EPS, bypass, UPS mode and selected advanced inverter parameters without relying on cloud services.

> ⚠️ This integration directly communicates with the inverter over Modbus. Some advanced settings can affect inverter behavior. Use advanced entities only if you know what they do. In other words: do not press every shiny button just because it exists.

---

## ✨ Features

### 📊 Real-time Monitoring

* PV1 / PV2 voltage
* PV1 / PV2 current
* Total PV power
* Battery voltage
* Battery current
* Battery SOC
* Battery SOH
* Battery temperature
* Battery charge / discharge power
* Grid voltage
* Grid current
* Grid frequency
* Grid import / export power
* EPS voltage
* EPS current
* EPS power
* EPS active power
* EPS apparent power

### 🌡️ Inverter Temperatures

* Inverter Base Temperature
* Inverter Boost Temperature
* Inverter LLC Temperature
* Inverter Ambient Temperature

Useful for checking inverter cooling, fan behavior, heat buildup and installation conditions.

### 🔋 Battery & BMS Information

* Battery SOC
* Battery SOC Real
* Battery voltage
* Battery current
* Battery temperature
* Battery SOH
* Battery FCC
* Battery RM
* Battery cycle count
* Battery max charge current
* Battery max discharge current
* Manual battery capacity setting for calculations

### 🧮 Virtual / Calculated Sensors

The integration includes additional calculated sensors for better energy overview:

* AVG PV Power
* AVG Battery Power

  * positive value = battery charging
  * negative value = battery discharging
* AVG Battery Power Speed
* AVG EPS Load
* Battery SOC Speed
* Battery Charge ETA
* EPS Energy Hour
* Battery SOC Real

Average values are sampled over time to avoid jumping values and make automations more stable.

### ⏱️ Battery Charge ETA

The integration can estimate when the battery will reach the configured **Battery End of Charge SOC**.

Possible states:

* `Bude nabito v 14:35`
* `dnes nebude`
* `Bylo nabito v 13:02`

The ETA uses hysteresis after reaching the target SOC, so it does not start showing nonsense when the inverter slightly discharges the battery after reaching the charge target.

### ⚡ Energy Counters

* PV Energy Today / Total
* Battery Charge Energy Today / Total
* Battery Discharge Energy Today / Total
* Grid Import Energy Today / Total
* Grid Export Energy Today / Total
* EPS Energy Today / Total
* Energy Sold Today / Total
* Energy Bought Today / Total
* Self To Load Energy Today / Total

### ⚙️ Control Functions

* Inverter Power
* EPS Enable
* Bypass Enable
* UPS Mode
* Battery AC Charging
* Generator Charging
* Beeper
* Bluetooth

### 🎛️ Configuration Parameters

* Battery Charge Limit
* Battery Discharge Limit
* Battery End of Charge SOC
* Battery On-Grid Discharge SOC
* Battery Off-Grid Discharge SOC
* Battery On-Grid Recovery SOC
* Battery Off-Grid Recovery SOC
* Battery AC Charge Current Limit
* Battery Capacity Manual
* SecEPS ON SOC
* SecEPS SWITCH SOC
* SecEPS ON PV Power Min
* Source Priority
* Charge Priority
* GEN Port Work Mode
* AC Input Type / advanced mode

Number entities use direct numeric input instead of sliders, because precise settings deserve better than “drag and pray”.

### 🧰 Advanced / Diagnostic Entities

Some potentially risky or rarely used options are marked as advanced/config entities and may be disabled by default:

* ADV - Island Mode
* ADV - Grid Feedback
* ADV - Split Phase Output
* ADV - Overload To Bypass
* ADV - Fast MPPT
* ADV - Zero Power Output
* ADV - Active Overload Enable
* ADV - DRMS Enable
* ADV - VFRT Enable
* ADV - AC Input Type

These are intentionally separated from normal controls.

### 🚨 Diagnostics

* Inverter Status
* Battery Status
* Fault Code Decoder
* Warning Main Code
* Warning Main Text
* Warning Sub Code
* Warning Sub Text
* Total Work Time
* Raw / unknown select value handling

The integration can show unknown raw values for select entities instead of silently hiding them, which helps with firmware differences and undocumented Modbus behavior.

---

## 🖼️ Home Assistant Example

Monitor and control:

* Solar production
* Battery charging and discharging
* Battery usable SOC range
* Estimated time to full battery
* Grid import / export
* EPS backup output
* Household load
* Inverter temperatures
* Faults and warnings
* Energy counters
* Advanced inverter settings

All values are read directly through Modbus RTU.

---

## 📦 Installation via HACS

### Add Custom Repository

1. Open **HACS**
2. Select **Integrations**
3. Click **⋮ → Custom repositories**
4. Add:

```text
https://github.com/vsajer/sandisolar-ha
```

Category:

```text
Integration
```

5. Install the integration
6. Restart Home Assistant

---

## ⚙️ Configuration

Navigate to:

```text
Settings → Devices & Services → Add Integration
```

Select:

```text
SANDISOLAR Modbus RTU
```

### Required Settings

| Parameter       | Example        |
| --------------- | -------------- |
| Serial Port     | `/dev/ttyUSB0` |
| Baud Rate       | `9600`         |
| Slave ID        | `1`            |
| Update Interval | `10 s`         |

---

## 🔌 RS485 Wiring

| Inverter | USB-RS485 |
| -------- | --------- |
| A        | A / D+    |
| B        | B / D-    |

Recommendations:

* Use twisted pair cable
* Use shielded cable for longer runs
* Use 120 Ω termination resistor for long RS485 lines
* Avoid multiple Modbus masters on the same RS485 bus

> ⚠️ Modbus RTU expects one master on the bus. Running the original WiFi logger and Home Assistant RS485 adapter at the same time may cause communication conflicts depending on wiring and logger behavior.

---

## 🧩 Compatibility

Tested with:

* SANDISOLAR SD-PRO-EU 6.5K
* Modbus RTU Protocol V2.14
* Home Assistant 2025+

The inverter firmware and Modbus register map may differ between models and firmware versions. Some registers are therefore handled carefully, and unknown values are exposed for diagnostics where possible.

---

## 🛠️ Notes

This integration is still evolving. Some advanced functions are based on observed inverter behavior and available Modbus documentation. If your inverter returns different values, please open an issue and include:

* inverter model
* firmware version
* Modbus protocol version, if known
* relevant Home Assistant logs
* raw register values, if available

---

## 👨‍💻 Author

**Vláďa (@vsajer)**
Czech Republic 🇨🇿

---

## ❤️ Support

If this project helped you, please consider:

* ⭐ Starring the repository
* Reporting issues
* Sharing screenshots and test results
* Contributing new register definitions
* Improving translations and documentation

Pull requests are welcome.
