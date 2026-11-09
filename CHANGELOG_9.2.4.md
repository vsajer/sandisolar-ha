# Sandisolar HA 9.2.4

- Grid Power now reads Input registers **320–321** directly (scale 0.1 W), confirmed by AO-6KSL-G3 live comparison.
- AVG Grid Power now averages this direct reading, not an estimate.
- Removed experimental grid power entities: Grid Power Direct Register 458, Grid Power Register 328 Raw, Grid Active Power Estimate, Grid Apparent Power Estimate, and duplicate Power To User Total.
- Removed polling of experimental 328 and 458 registers for grid power.
- Re-enabled SecEPS number writes for registers 219–222 with range checks, SOC sanity validation, and post-write readback. **SecEPS SOC decoding is still unverified on this firmware.** Writes to invalid SOC values remain blocked to prevent unsafe changes.
- Preserved Grid Power and AVG Grid Power unique IDs; other energy counters are unchanged.
- Removing entities from the integration does not automatically delete their existing HA entity registry records; remove orphaned entities from Settings > Devices & services > Entities if desired.

**Warning:** Validate SecEPS threshold semantics against AOHAI before changing them. Voltage and SOC parameters affect power supply switching. This release has not been live-tested.
