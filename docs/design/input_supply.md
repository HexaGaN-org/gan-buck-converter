# Input and Supply — Design Notes

Sheet: `sheets/input_supply.kicad_sch`

**Owner:** Reza Rahimzadeh · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Protect the board from the 48 V input, and generate the low-voltage rails every other sheet runs on (`+5V`, `+3V3`, `+3V3A`), from either the 48 V bus or an external 5 V bench supply.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Input and supply** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- Accept the full input voltage range in the specifications (48 V nominal, maximum below 60 V SELV).
- Carry the input current: 3.3 A at 150 W, with parts sized for the 200 W headroom.
- Clamp input transients below the switch-node limit published by power_stage: **90 V** (the LM5113-Q1's HS rating), including ringing. Choose the TVS clamp voltage, the fuse rating and that limit together; GaN has essentially no avalanche capability, so the clamp must stop a transient before it gets there.
- Protect against reverse polarity on both J1 and J6.
- Supply about 150 mA on `+5V` (GaN driver bias, 3.3 V LDO, USB bridge, LEDs) from an aux regulator rated for at least 300 mA.
- Select between the external 5 V input (priority) and the aux regulator automatically, with reverse-current blocking, and ride through the switchover without resetting the MCU: size the `+5V` output capacitance for the mux's switchover time. If the MCU does reset, the enable sheet holds both gates off, so the failure is safe.
- Set the mux's priority threshold so a sagging or disconnected bench supply is detected cleanly.
- Rate J6 for at least 0.5 A, with a fuse or PTC.
- Provide `+3V3` for logic and a filtered `+3V3A` for the MCU's analog supply.
- Allow full low-voltage bring-up from J6 with no 48 V connected.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-03 | 5 V source selection with a two-input power mux (TPS2121-class), external input J6 has priority | Schottky diode-OR; a jumper | The mux selects automatically with milliohms of drop and blocks reverse current, so the bench supply can never back-feed the 48 V bus. A Schottky OR drops 0.3–0.5 V, which can push the GaN driver's bias out of its 4.5–5.5 V range. Plugging in a bench supply is deliberate, so it wins; unplugging hands the rail back to the aux regulator | power_stage: `+5V` must stay within 4.5–5.5 V | Accepted |

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

- Put a test point on each mux input and on `+5V`.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Low-voltage bring-up | Current-limited 5 V bench supply on J6, no 48 V connected | MCU, firmware, sensing and enable logic all work | | |
| 2 | 48 V hand-over | Apply 48 V with J6 connected, then unplug J6 | `+5V` stays in regulation; the MCU does not reset | | |

---

## Open questions

-
