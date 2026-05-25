SANDISOLAR / SD‑PRO‑EU – Modbus RTU Integration for Home Assistant
Hybridní měnič SANDISOLAR SD‑PRO‑EU konečně v Home Assistantu — přesné hodnoty, rychlá odezva, plná kontrola.

![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/github/v/release/vsajer/sandisolar-ha)
![Downloads](https://img.shields.io/github/downloads/vsajer/sandisolar-ha/total)
![License](https://img.shields.io/github/license/vsajer/sandisolar-ha)

Hybridní měnič **SANDISOLAR SD‑PRO‑EU** konečně v Home Assistantu — přesné hodnoty, rychlá odezva, plná kontrola.

🟢 Features / Funkce
English
Monitoring
PV voltage, current, power

Battery voltage, current, SOC

Grid voltage, frequency, power

Load power

Control
Inverter ON/OFF

AC charge enable

Battery discharge enable

SOC limits

AC charge current

Česky
Monitoring
FV napětí, proud, výkon

Baterie: napětí, proud, SOC

Síť: napětí, frekvence, výkon

Zátěž: aktuální výkon

Ovládání
Zapnutí / vypnutí měniče

Povolení AC nabíjení

Povolení vybíjení baterie

Limity SOC

AC nabíjecí proud

🛠️ Installation via HACS / Instalace přes HACS
English
Open HACS → Integrations

Click Custom repositories

Add repository URL:

Kód
https://github.com/vsajer/sandisolar-ha
Category: Integration

Install the integration

Restart Home Assistant

Add integration:
Settings → Devices & Services → Add Integration → SANDISOLAR Modbus RTU

Česky
Otevřete HACS → Integrations

Klikněte na Custom repositories

Přidejte URL repozitáře:

Kód
https://github.com/vsajer/sandisolar-ha
Kategorie: Integration

Nainstalujte integraci

Restartujte Home Assistant

Přidejte integraci:
Nastavení → Zařízení a služby → Přidat integraci → SANDISOLAR Modbus RTU

⚙️ Configuration / Konfigurace
English
Required fields:

Device Name

Serial Port (e.g. /dev/ttyUSB0)

Baud Rate (default 9600)

Slave ID (default 1)

Update Interval (default 30s)

Optional:

Czech entity names

Custom polling interval

Česky
Povinné položky:

Název zařízení

Sériový port (např. /dev/ttyUSB0)

Baudrate (výchozí 9600)

Slave ID (výchozí 1)

Interval aktualizace (výchozí 30s)

Volitelné:

Česká jména entit

Vlastní interval aktualizace

📊 Supported Entities / Podporované entity
Sensors / Senzory
PV Voltage / Current / Power

Battery Voltage / Current / SOC

Grid Voltage / Frequency / Power

Load Power

Switches / Přepínače
Inverter ON/OFF

AC Charge Enable

Battery Discharge Enable

Number Controls / Číselné hodnoty
AC Charge SOC Limit

Battery Discharge SOC Limit

AC Charge Current

🧪 Troubleshooting / Řešení problémů
English
Device not detected
Check /dev/ttyUSB0 vs /dev/ttyUSB1

Ensure user has access to serial ports

Try reconnecting USB adapter

No data
Wrong baudrate

Wrong slave ID

RS485 A/B swapped

Česky
Zařízení se nezobrazuje
Zkontrolujte /dev/ttyUSB0 vs /dev/ttyUSB1

Ověřte oprávnění k sériovým portům

Odpojte a znovu připojte USB převodník

Žádná data
Špatný baudrate

Špatné slave ID

Prohozené vodiče A/B

---

# 📡 RS485 Wiring Diagram / Schéma zapojení RS485

## English  
Connect the inverter to the USB–RS485 adapter as follows:

- **A → A (RTX+)**  
- **B → B (RTX–)**  
- Use shielded twisted pair  
- Add 120 Ω termination resistor for long cables  

🧑‍💻 Author / Autor
Created by Vlaďa (@vsajer)  
Czech Republic 🇨🇿
Modbus, Home Assistant, Hybrid Inverters
