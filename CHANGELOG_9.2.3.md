# Sandisolar HA 9.2.3 — Direct grid power diagnostics

- Added **Grid Power Direct Register 458**, reading Modbus Input 458–459 as signed 32-bit, scale 0.1 W.
- Vendor V2.14 specifies positive values as import and negative values as export (`sdwParallelGridPower`).
- This is a **parallel-system grid power register**; behavior on a single AO-6KSL-G3 inverter has NOT been verified. A value of zero during active import may mean this register is unsupported for this configuration.
- Kept **Grid Power** and **Grid Active Power Estimate** unchanged until live verification. No existing entity IDs or energy counters were changed.
- No new write operations or control entities.

## Validation

With AC contactor closed and steady ~1.2 kW import, compare `Grid Power Direct Register 458` with AOHAI Grid and `Grid Active Power Estimate`. If the direct sensor is near +1200 W, the register likely works for this inverter. With AC input isolated, it should be near 0 W. Do not assume a zero value confirms no import until verified.
