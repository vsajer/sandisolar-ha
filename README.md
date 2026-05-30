SANDISOLAR / SD‑PRO‑EU – Modbus RTU Integration for Home Assistant
Hybridní měnič SANDISOLAR SD‑PRO‑EU konečně v Home Assistantu — přesné hodnoty, rychlá odezva, plná kontrola.
![SANDISOLAR + Home Assistant](docs/images/banner.png)

[![HACS](https://img.shields.io/badge/HACS-Custom-blue.svg)]()
[![Version](https://img.shields.io/github/v/release/vsajer/sandisolar-ha)]()
[![License](https://img.shields.io/github/license/vsajer/sandisolar-ha)]()

Native Home Assistant integration for the **SANDISOLAR SD-PRO-EU Hybrid Inverter** using **Modbus RTU (RS485)**.

Monitor your solar production, battery, grid import/export and inverter status directly in Home Assistant. Control charging, discharge limits and advanced inverter settings without relying on cloud services.

---

## ✨ Features

### 📊 Real-time Monitoring

* PV1 / PV2 Voltage
* PV1 / PV2 Current
* Total PV Power
* Battery Voltage
* Battery Current
* Battery SOC
* Battery SOH
* Battery Temperature
* Grid Voltage
* Grid Frequency
* Grid Import / Export Power
* EPS Power
* EPS Active Power
* EPS Apparent Power
* Energy Counters

  * PV Energy Today / Total
  * Battery Charge Energy Today / Total
  * Battery Discharge Energy Today / Total
  * Grid Import Energy Today / Total
  * Grid Export Energy Today / Total
  * Self Consumption Energy
  * Energy Sold to Grid
  * Energy Purchased from Grid

### ⚙️ Control Functions

* Inverter ON/OFF
* AC Charge Enable
* EPS Enable
* Bypass Mode
* UPS Mode

### 🎛️ Configuration Parameters

* Charge Current Limit
* Discharge Current Limit
* End Of Charge SOC
* On-Grid Discharge SOC
* Off-Grid Discharge SOC
* AC Charge Current Limit
* Source Priority
* Charge Priority
* Generator Port Mode
* Secondary EPS Parameters

### 🚨 Diagnostics

* Inverter Status
* Battery Status
* Fault Code Decoder
* Warning Code Decoder
* Total Work Time
* BMS Information

---

## 🖼️ Home Assistant Example

Monitor:

* Solar Production
* Battery State
* Grid Import / Export
* Household Consumption
* EPS Backup Output

All values are updated directly through Modbus RTU.

---

## 📦 Installation via HACS

### Add Custom Repository

1. Open **HACS**
2. Select **Integrations**
3. Click **⋮ → Custom Repositories**
4. Add:

```text
https://github.com/vsajer/sandisolar-ha
```

Category:

```text
Integration
```

5. Install
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

| Parameter       | Example      |
| --------------- | ------------ |
| Serial Port     | /dev/ttyUSB0 |
| Baud Rate       | 9600         |
| Slave ID        | 1            |
| Update Interval | 10 s         |

---

## 🔌 RS485 Wiring

| Inverter | USB-RS485 |
| -------- | --------- |
| A        | A (D+)    |
| B        | B (D-)    |

Recommendations:

* Twisted pair cable
* Shielded cable for long runs
* 120 Ω termination resistor for long RS485 lines

---

## 🧩 Compatibility

Tested with:

* SANDISOLAR SD-PRO-EU 6.5K
* Firmware V2.14
* Home Assistant 2025+

## 👨‍💻 Author

**Vláďa (@vsajer)**

Czech Republic 🇨🇿

---

## ❤️ Support

If this project helped you, please consider:

* ⭐ Starring the repository
* Reporting issues
* Sharing improvements
* Contributing new register definitions
