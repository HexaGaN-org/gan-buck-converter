# Sensing — Design Notes

Sheet: `sheets/sensing.kicad_sch`

**Owner:** Connor Jin · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Turn the output current, the input and output voltages, and the board temperature into filtered, clamped 0–3 V signals for the MCU's ADC and CMPSS comparators.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Sensing** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- `ISENSE`: cover the full inductor current range, including negative current at light load, with the overcurrent threshold inside 0–3 V and enough bandwidth for cycle-by-cycle current limiting.
- `VOUT_SENSE`: place the overvoltage threshold inside 0–3 V; this signal feeds a CMPSS comparator.
- `VIN_SENSE`: cover the full input range, including the undervoltage-lockout thresholds.
- `TEMP_SENSE`: a thermistor placed beside the GaN FETs, covering the overtemperature threshold.
- Meet the measurement accuracy the control loop and protections need (target to be set in the specifications).
- Size every RC for the ADC's acquisition time, and clamp every signal to `+3V3A` / `AGND`.
- Inputs: `I_SH_P`, `I_SH_N` from power_stage, plus `V_IN` and `V_OUT`. Outputs: `ISENSE`, `VOUT_SENSE`, `VIN_SENSE`, `TEMP_SENSE` to mcu.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

---

## Calculations

One row per calculation. Note where each input came from (specification, datasheet, measurement) in Notes.

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| | | | |

---

## Part selection

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| | | | | | |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| | | | |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

-

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | | | | | |

---

## Open questions

-
