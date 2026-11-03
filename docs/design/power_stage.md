# Power Stage — Design Notes

Sheet: `sheets/power_stage.kicad_sch`

**Owner:** [Reza Rahimzadeh] · **Last updated:** [2026-11-03]

---

## Purpose and requirements

Convert the 48 V bus to the 12 V output with a synchronous buck: two discrete enhancement-mode GaN FETs, a GaN half-bridge gate driver, the output inductor and capacitors, and the current-sense shunt.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Power stage** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- 48 V in, 12 V out at up to 12.5 A (150 W), with parts and copper rated for 16.7 A (200 W).
- Switching frequency within 300–500 kHz.
- Meet the efficiency target in the specifications (about 95–96 % expected, roughly 6 W total loss at 150 W) with natural-convection cooling.
- Keep the GaN gate voltage within the FETs' limits under all conditions, including ringing.
- Support the shortest safe dead time, set in the MCU's ePWM.
- Meet the output ripple and load-transient targets in the specifications.
- Provide a Kelvin-connected current-sense shunt whose value lets sensing place the overcurrent threshold within 0–3 V.
- Hold both gates off when the driver is unpowered or `GATE_HI` / `GATE_LO` are undriven.
- Inputs: `GATE_HI`, `GATE_LO` from enable. Outputs: `ISH_P`, `ISH_N` to sensing.

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
