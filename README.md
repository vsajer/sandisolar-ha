# SANDISOLAR / SD-PRO-EU – Modbus RTU Integration for Home Assistant

Hybridní měnič **SANDISOLAR SD-PRO-EU** v Home Assistantu bez cloudu — přes **Modbus RTU / RS485**.

<img width="250" height="250" alt="SandiSolar_HA" src="https://github.com/vsajer/sandisolar-ha/blob/main/custom_components/sandisolar_modbus_rtu/brand/logo.png" />

[![HACS](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://github.com/hacs/integration)
[![Integration version](https://img.shields.io/badge/dynamic/json?label=version&query=%24.version&url=https%3A%2F%2Fraw.githubusercontent.com%2Fvsajer%2Fsandisolar-ha%2Fmain%2Fcustom_components%2Fsandisolar_modbus_rtu%2Fmanifest.json)](https://github.com/vsajer/sandisolar-ha/blob/main/custom_components/sandisolar_modbus_rtu/manifest.json)
[![License](https://img.shields.io/github/license/vsajer/sandisolar-ha)](https://github.com/vsajer/sandisolar-ha/blob/main/LICENSE)

Native Home Assistant integration for the **SANDISOLAR SD-PRO-EU Hybrid Inverter** using **Modbus RTU over RS485**.

Umožňuje sledovat výrobu z panelů, baterii, síť, EPS výstup, teploty, výstrahy, chybové stavy a energetické čítače. Zároveň dovoluje ovládat vybrané funkce měniče přímo z Home Assistantu.

> ⚠️ Integrace komunikuje přímo s měničem. Pokročilé volby můžou změnit jeho chování. Neklikej na všechno jen proto, že to svítí.

---

## ✨ Hlavní funkce

### 📊 Monitoring

- PV1 / PV2 napětí a proud
- Celkový PV výkon
- Baterie: napětí, proud, SOC, SOH, teplota
- Nabíjecí / vybíjecí výkon baterie
- Síť: napětí, proud, frekvence, import/export výkon
- EPS: napětí, proud, aktivní a zdánlivý výkon
- Teploty měniče: base, boost, LLC, ambient
- Stav měniče, stav baterie, chybové a varovné kódy

### ⚡ Energetické čítače

- PV Energy Today / Total
- Battery Charge / Discharge Energy Today / Total
- Grid Import / Export Energy Today / Total
- EPS Energy Today / Total
- Energy Sold / Bought Today / Total
- Self To Load Energy Today / Total

### 🧮 Vypočítané senzory

- AVG PV Power
- AVG Battery Power  
  - kladná hodnota = baterie se nabíjí
  - záporná hodnota = baterie se vybíjí
- AVG Grid Power
- AVG EPS Load
- Battery SOC Real
- Battery SOC Speed
- Battery Power Speed
- Battery Charge ETA
- EPS Energy Hour

Průměrované hodnoty jsou vhodné pro stabilnější automatizace, řízení přebytků, bojler, EMHASS a dashboardy.

---

## 🔋 Battery FCC / RM fallback

Některé BMS neposílají přes Modbus hodnoty **FCC** nebo **RM**. Integrace je umí dopočítat z ručně nastavené kapacity baterie.

```text
Battery FCC = Battery Capacity Manual × Battery SOH / 100
```

Pokud SOH není dostupné:

```text
Battery FCC = Battery Capacity Manual
```

Pokud BMS neposílá RM:

```text
Battery RM = Battery FCC × Battery SOC / 100
```

Díky tomu zůstávají bateriové výpočty použitelné i s BMS, která neposílá kompletní data.

---

## ⏱️ Battery Charge ETA

Integrace odhaduje, kdy baterie dosáhne nastaveného **Battery End of Charge SOC**.

Možné stavy:

- `Will be full at 14:35`
- `Not today`
- `Was full at 13:02`

ETA používá hysteresi, takže po dosažení cílového SOC nezačne ukazovat blbosti při drobném poklesu baterie. Malá věc, velká úleva pro nervy.

---

## ⚙️ Ovládání a nastavení

### Switch

- Inverter Power
- EPS Enable
- Bypass Enable
- UPS Mode
- Battery AC Charging
- Generator Charging
- Beeper
- Bluetooth

### Number

- Battery Charge Limit
- Battery Discharge Limit
- Battery End of Charge SOC
- On-Grid / Off-Grid Discharge SOC
- On-Grid / Off-Grid Recovery SOC
- AC Charge Current Limit
- Battery Capacity Manual
- SecEPS ON SOC
- SecEPS SWITCH SOC
- SecEPS ON PV Power Min

Number entity používají přímé zadání čísla místo sliderů. Přesné nastavení si zaslouží víc než „tref se palcem“.

### Select

- Source Priority
- Charge Priority
- GEN Port Work Mode
- AC Input Type / advanced mode

---

## 🧰 Pokročilé a diagnostické entity

Některé volby jsou označené jako pokročilé nebo diagnostické a můžou být ve výchozím stavu vypnuté:

- ADV - Island Mode
- ADV - Grid Feedback
- ADV - Split Phase Output
- ADV - Overload To Bypass
- ADV - Fast MPPT
- ADV - Zero Power Output
- ADV - Active Overload Enable
- ADV - DRMS Enable
- ADV - VFRT Enable
- ADV - AC Input Type

Diagnostika zahrnuje:

- Inverter Status
- Battery Status
- Fault Code Decoder
- Warning Main / Sub Code
- Warning Main / Sub Text
- Total Work Time
- Raw / unknown select value handling

Neznámé hodnoty se pokud možno zobrazí jako raw hodnota, aby šly lépe řešit rozdíly mezi firmware.

---

## 🌍 Překlady

Integrace podporuje překlady stavů, varování a chyb podle jazyka Home Assistantu.

Aktuálně zahrnuté jazyky:

- English
- Czech
- German
- Polish
- Slovak

Přeložené jsou hlavně:

- Inverter Status
- Battery Status
- Fault Code Decoder
- Warning Main Text
- Warning Sub Text
- Battery Charge ETA

Pokud jazyk není dostupný, použije se angličtina.

---

## 🖼️ Screenshots

### Dashboard overview

![Dashboard overview](docs/images/1.png)

### Device page

![Device page](docs/images/2.png)

### RS485 / CAN port

![RS485 CAN port](docs/images/Port_RS485_CAN.png)

### USB-RS485 adapter

![USB RS485 adapter](docs/images/USB_RS485.png)

---

## 📋 Supported Entity Types

| Platform   | Examples |
| ---------- | -------- |
| Sensor     | PV power, battery SOC, grid power, EPS power, temperatures, energy counters |
| Number     | Charge limit, discharge limit, SOC limits, battery capacity manual |
| Switch     | Inverter power, EPS, bypass, UPS mode, AC charging, generator charging |
| Select     | Source priority, charge priority, GEN port work mode, AC input type |
| Diagnostic | Fault codes, warnings, inverter status, battery status |
| Calculated | AVG PV Power, AVG Battery Power, AVG Grid Power, AVG EPS Load, Battery Charge ETA |

---

## 📦 Installation via HACS

1. Open **HACS**
2. Select **Integrations**
3. Click **⋮ → Custom repositories**
4. Add repository:

```text
https://github.com/vsajer/sandisolar-ha
```

Category:

```text
Integration
```

5. Install the integration
6. Restart Home Assistant
7. Add integration in **Settings → Devices & Services → Add Integration**
8. Select **SANDISOLAR Modbus RTU**

---

## ⚙️ Configuration

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

Doporučení:

- použij kroucený pár
- u delšího vedení použij stíněný kabel
- u dlouhé RS485 linky použij zakončovací odpor 120 Ω
- na jedné RS485 sběrnici měj jen jednoho Modbus mastera

> ⚠️ Modbus RTU počítá s jedním masterem. Originální WiFi logger a Home Assistant RS485 adaptér můžou při současném provozu dělat konflikty.

Pokud komunikace nefunguje, zkus prohodit A/B vodiče na USB-RS485 adaptéru. Značení RS485 je občas loterie v montérkách.

---

## ⚡ PV přebytky a optimalizace

Pro řízení přebytků a energetickou optimalizaci jsou nejužitečnější tyto senzory:

| Sensor             | Purpose |
| ------------------ | ------- |
| AVG PV Power       | Vyhlazená výroba z panelů |
| AVG Battery Power  | Kladně = nabíjení, záporně = vybíjení |
| AVG Grid Power     | Vyhlazený import/export ze sítě |
| AVG EPS Load       | Vyhlazená zátěž EPS / domu |
| Battery SOC Real   | Použitelný SOC podle nastavených limitů |
| Battery Charge ETA | Odhad času do cílového nabití |

Typické použití:

- řízení bojleru podle přebytků
- ochrana baterie
- off-grid optimalizace
- zero-export logika
- EMHASS plánování

---

## 🧩 Compatibility

Tested with:

- SANDISOLAR SD-PRO-EU 6.5K
- Modbus RTU Protocol V2.14
- Home Assistant 2025+

Firmware a Modbus mapa se můžou mezi modely lišit. Proto integrace u některých registrů zachází opatrně a u neznámých hodnot se snaží ukázat raw data.

---

## 🛠️ Troubleshooting

### Integration does not connect

Zkontroluj:

- správný serial port, například `/dev/ttyUSB0`
- baud rate, obvykle `9600`
- slave ID, obvykle `1`
- A/B zapojení RS485
- oprávnění USB-RS485 adaptéru
- že na RS485 sběrnici není druhý Modbus master

### Values are unavailable

Zkus:

- restartovat Home Assistant
- zkontrolovat Modbus kabeláž
- prohodit A/B vodiče
- snížit update interval
- dočasně odpojit originální WiFi logger

### Original inverter app stopped showing live data

Originální WiFi logger a RS485 adaptér se můžou hádat o komunikaci.

Zkus:

1. Disable Home Assistant integration
2. Disconnect USB-RS485 adapter
3. Restart inverter / WiFi logger
4. Wait several minutes
5. Check original app again

### GEN Port Work Mode shows unknown value

Některé firmware můžou vracet nedokumentované hodnoty. Integrace je pokud možno zobrazí jako raw / unknown, aby šly dohledat a doplnit.

### Battery FCC / RM shows calculated values

Pokud BMS neposílá FCC nebo RM, integrace je dopočítá z:

- Battery Capacity Manual
- Battery SOH
- Battery SOC

To je očekávané chování.

---

## 📝 Notes

Integrace se dál vyvíjí. Některé pokročilé funkce vycházejí z dostupné Modbus dokumentace a pozorovaného chování měniče.

Při hlášení problému přidej:

- model měniče
- firmware version
- Modbus protocol version, pokud je známá
- relevantní Home Assistant logy
- raw register values, pokud jsou dostupné

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Vláďa (@vsajer)**  
Czech Republic 🇨🇿

---

## ❤️ Support

Pokud ti integrace pomohla:

- ⭐ Star the repository
- Report issues
- Share screenshots and test results
- Contribute register definitions
- Improve translations and documentation

Pull requests are welcome.
