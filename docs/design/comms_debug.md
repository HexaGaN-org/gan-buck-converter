# Comms and Debug — Design Notes

Sheet: `sheets/comms_debug.kicad_sch`

**Owner:** Yunxi He · **Reviewer:** [NAME] · **Last updated:** [YYYY-MM-DD]

---

## Purpose and requirements

Connect the MCU to a host laptop over USB serial, and to a JTAG debugger for programming and debugging.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Comms and debug** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- USB-C, USB 2.0 device, with ESD protection on D+/D− and CC pull-down resistors.
- A USB-to-UART bridge connected to the MCU's SCI.
- USB power does not run the board, and a connected laptop cannot back-power the MCU while the board is off: power the bridge's I/O from `+3V3`.
- A TI-compatible JTAG header, including `XRSN`.

---
