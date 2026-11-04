# Input and Supply — Design Notes

Sheet: `sheets/input_supply.kicad_sch`

**Owner:** [NAME] · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Protect the board from the 48 V input, and generate the low-voltage rails every other sheet runs on (`+5V`, `+3V3`, `+3V3A`), from either the 48 V bus or an external 5 V bench supply.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Input and supply** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- Accept the full input voltage range in the specifications (48 V nominal, maximum below 60 V SELV).
- Carry the input current: 3.3 A at 150 W, with parts sized for the 200 W headroom.
- Clamp input transients below the GaN FETs' voltage rating (a value published by power_stage).
- Protect against reverse polarity on both J1 and J6.
- Supply about 150 mA on `+5V` (GaN driver bias, 3.3 V LDO, USB bridge, LEDs) from an aux regulator rated for at least 300 mA.
- Select between the external 5 V input (priority) and the aux regulator automatically, with reverse-current blocking, and ride through the switchover without resetting the MCU.
- Provide `+3V3` for logic and a filtered `+3V3A` for the MCU's analog supply.
- Allow full low-voltage bring-up from J6 with no 48 V connected.

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
