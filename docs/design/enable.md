# Enable — Design Notes

Sheet: `sheets/enable.kicad_sch`

**Owner:** [NAME] · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Guarantee in hardware that the GaN half-bridge can switch only when the enable switch is on, the watchdog is healthy, reset is released, and the MCU requests switching. Firmware can request switching but never force it.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Enable** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- `STAGE_EN` = enable switch on AND `WD_OK` AND `RESET_OK` AND `MCU_EN`.
- `HS_PWM` / `LS_PWM` = `MCU_PWMH` / `MCU_PWML` AND `STAGE_EN`.
- Both gates off in every undriven, floating, power-up and reset state.
- A windowed watchdog: kicks that are too slow or too fast both count as failures.
- Matched gating delay between the high-side and low-side paths, so gating does not eat into dead time.
- Provide `STAGE_EN_FB` so firmware can read whether the stage is enabled.
- Inputs: `MCU_PWMH`, `MCU_PWML`, `MCU_EN`, `WDI` from mcu, and J5. Outputs: `HS_PWM`, `LS_PWM` to power_stage; `STAGE_EN_FB` to mcu; `XRSN` shared.

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
