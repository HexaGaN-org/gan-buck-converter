# MCU — Design Notes

Sheet: `sheets/mcu.kicad_sch`

**Owner:** Yunxi He · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Run the converter's control loop and software protections on the TMS320F280039C (64-pin LQFP), with everything it needs to start and run reliably.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **MCU** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- Generate one high-resolution ePWM A/B pair with dead time (`MCU_PWMH`, `MCU_PWML`) at the chosen switching frequency.
- Put `ISENSE` and `VOUT_SENSE` on CMPSS-capable ADC pins routed to the ePWM trip zone, so overcurrent (cycle by cycle) and overvoltage shut the PWM down in hardware.
- Sample `VIN_SENSE` and `TEMP_SENSE` for undervoltage lockout and overtemperature, and `I_IN_SENSE` for input power and the input-current limit (any ADC pin).
- Support the staged control bring-up: open loop, then voltage mode, then average current mode.
- Drive `MCU_EN` and `WDI`, read `STAGE_EN_FB`, and share the open-drain `XRSN`.
- Connect SCI and JTAG to comms_debug.
- Boot from flash by default, with boot pins free of other functions.
- Join `AGND` to `GND` at exactly one net tie, at the ADC reference.
- Every pin assignment matches the frozen SysConfig pin-mux. Change `pinmux.syscfg` first, then the schematic.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-03 | MCU: TI TMS320F280039C, 64-pin LQFP (PM) | Smaller C2000 parts (F28002x / F28003x family members) | Same device as the universal control board, so SysConfig setup, C2000Ware firmware, the LAUNCHXL-F280039C LaunchPad and the team's experience carry over. The 64-pin package keeps schematic and layout simple while keeping what a buck needs: high-resolution PWM, CMPSS comparators for cycle-by-cycle limiting, and a fast ADC. Firmware bring-up can start on the LaunchPad before boards arrive | All sheets: pin-mux frozen in SysConfig before layout. Confirm stock before schematic freeze | Accepted |

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
