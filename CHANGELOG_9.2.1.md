# Sandisolar HA 9.2.1 – Grid diagnostics and SecEPS safety

## Based on real AO-6KSL-G3 measurements
- AOHAI application: grid 237.6 V / 4.8 A / 1110.8 W active / 1140.5 VA apparent.
- HA: grid 238 V / 4.5 A / 0 W at a nearby but not identical time.
- V2.14 Input 328 is *power to grid*, so zero export can be normal while consuming power.

## Changes
- Keep existing `grid_power` unique ID, but correct Input 328 decoding to unsigned uint32 as specified in V2.14.
- Add Input 2 inverter AC voltage, 5 inverter AC current, 52 grid power factor, 284 inverter output apparent power, 286 inverter output active power, 288 inverter output reactive power, and 320 power to user total.
- Add read-only **Grid Active Power Estimate** (`U * abs(I) * abs(PF)`) and **Grid Apparent Power Estimate** (`U * abs(I)`). These are *estimates*, not independently measured import power and cannot be used to determine export direction.
- Preserve existing `GEN Port Work Mode` mapping, and show raw unknown value 2700. Do not write unverified enum values.
- Block writes to SecEPS SOC/voltage settings until the map is verified on AO-6KSL-G3. The SOC number entities are made unavailable; their diagnostic raw readings remain visible as attributes. Voltage numbers display readings but refuse writes. This is intentional safety protection.
- Preserve previous fault code/subcode sensors, raw words, and history. Improve fault history state restoration order.
- Keep original entity unique IDs and Home Assistant statistics identifiers.

## Known limitations / safety
- AOHAI shows `SecEPS ON SOC=120%` and `SecEPS SWITCH SOC=0.78%` in 9.2.0. This contradicts valid SOC ranges; no safe automatic correction can be inferred from the V2.14 table. Do not write these settings until verified.
- A reading of 2700 in Holding 216 is not a valid documented enum (0–6), even though the vendor workbook itself includes 2700 in a sample column. It is not silently mapped to `Default`.
- The grid active estimate is NOT an authoritative meter reading; direction cannot be inferred from unsigned current alone. Original AOHAI grid active power register not independently identified.
- Grid Import Energy 415/417 and Bought Energy 423/425 are distinct counters in V2.14; do not substitute them without validating meanings.
- `Fault 203(1)` has not been captured live; polling may miss short faults. No unverified subcode translation is added.
- No changes to battery protection limits, GEN mode or inverter operating mode.
- Not tested on a physical inverter. Back up HA before installing; inspect new values after restart.

## Install
Copy `custom_components/sandisolar_modbus_rtu/` into HA `/config/custom_components/` and restart HA. Do not upload the ZIP as a single Python file. In HACS GitHub repository use tag `v9.2.1` after testing.
