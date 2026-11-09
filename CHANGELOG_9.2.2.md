# Sandisolar HA 9.2.2

- `Grid Power` now reports an estimated AC input consumption (V × |A| × |PF|) when connected to grid. Existing unique ID is preserved.
- Added `Grid Power Register 328 Raw` for the original Modbus input register 328.
- `AVG Grid Power` now uses the same estimated AC input power instead of raw register 328.
- For confirmed off-grid status with low grid voltage, estimate returns 0 W; ambiguous states return unavailable.
- Register 328 mapping and energy counter mappings are unchanged. Import/export direction cannot be inferred from this estimate.
- This is not a revenue-grade meter and should not be used for billing or integrated as verified import energy.
