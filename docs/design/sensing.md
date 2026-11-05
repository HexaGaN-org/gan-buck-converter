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
- `I_IN_SENSE`: amplify the input shunt (1 mΩ R201, Kelvin pair `I_SH_IN_P` / `I_SH_IN_N`, input_supply #17) with an amplifier whose common mode covers 40–51 V and **survives the 82.4 V clamped surge**. Telemetry and a firmware input-current limit only, so filter it heavily.
- Meet the measurement accuracy the control loop and protections need (target to be set in the specifications).
- Size every RC for the ADC's acquisition time, not only for noise, and clamp every signal to `+3V3` / `GNDA` (there is no separate `+3V3A` rail: input_supply #19).
- `ISENSE` bandwidth sets how fast cycle-by-cycle current limiting can act: keep its filter light. Filter `VIN_SENSE` and `TEMP_SENSE` more heavily.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-05 | Proposed: one current-sense amplifier part for both channels (`ISENSE` and `I_IN_SENSE`), gain ≈ 100, chosen so its common-mode rating covers the input side (operation to 51 V, survival to ≥ 82.4 V) | Gain 200 on the input channel (about 0.13–1.1 V over the load range; better light-load resolution, but a second amplifier part and loading fee) | One unique part for four placements (two shunts, two amplifiers). At gain 100 the input channel spans about 0.07–0.53 V: fine for telemetry and a limit; move it to gain 200 if bench readings at light load are too noisy | mcu: `I_IN_SENSE` on any ADC pin (no CMPSS needed) | Proposed (owner to confirm) |

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
