# Comms and Debug — Design Notes

Sheet: `sheets/comms_debug.kicad_sch`

**Owner:** [NAME] · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Connect the MCU to a host laptop over USB serial, and to a JTAG debugger for programming and debugging.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Comms and debug** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- USB-C, USB 2.0 device, with ESD protection on D+/D− and CC pull-down resistors.
- A USB-to-UART bridge connected to the MCU's SCI.
- USB power does not run the board, and a connected laptop cannot back-power the MCU while the board is off.
- A TI-compatible JTAG header, including `XRSN`.
- Inputs and outputs: `SCI_TX` / `SCI_RX`, `TCK` / `TMS` / `TDI` / `TDO` and `XRSN` to and from mcu.

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
