# Comms and Debug — Design Notes

Sheet: `sheets/comms_debug.kicad_sch`

**Owner:** Yunxi He · **Reviewer:** [NAME] · **Last updated:** 2026-11-05

---

## Purpose and requirements

Connect the MCU to a host laptop over USB serial, and to a JTAG debugger for programming and debugging.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Comms and debug** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

## Concise specifications

| Item | Required specification |
|---|---|
| USB connector | J3 USB-C, USB 2.0 device; CC pull-down resistors and ESD protection on D+/D−. |
| Serial bridge | USB-to-UART bridge with decoupling and 3.3 V MCU-side I/O. CP2102N or equivalent; exact part remains TBD. |
| UART wiring | MCU `SCI_TX` (U1 pin 1, GPIO29 / SCIA_TX) -> bridge RX; bridge TX -> MCU `SCI_RX` (U1 pin 2, GPIO28 / SCIA_RX). |
| Power | USB must not power the board. Bridge I/O uses board `+3V3`; ensure USB/UART connections cannot back-power the MCU when the board is off. |
| Debug connector | J4 TI-compatible JTAG header carrying `TCK`, `TMS`, `TDI`, `TDO`, `XRSn`, target-voltage reference and GND. Exact header/debugger pinout remains TBD. |
| Reset | Share active-low `XRSn` with MCU and enable sheets; debugger reset must be compatible with the existing open-drain reset network. |
| Host link | Text commands and status at approximately 10-50 updates/s: state, fault, input/output voltage, current, temperature, duty and frequency. Serial work must not delay the control interrupt. |

### Sheet interfaces

Directions below are relative to **comms_debug**. Use hierarchical labels with these exact names.

| Signal | Direction | Connection |
|---|---|---|
| `SCI_TX` | in | MCU -> bridge RX |
| `SCI_RX` | out | Bridge TX -> MCU |
| `TCK`, `TMS`, `TDI` | out | Debugger -> MCU |
| `TDO` | in | MCU -> debugger |
| `XRSn` | bidir | MCU, enable and debugger reset |

**Before schematic freeze:** choose the bridge and JTAG header/debugger, verify board-off back-power behavior, and agree the UART baud rate/framing with firmware. Define commands and range/state checks in `firmware/PROTOCOL.md`; see [firmware requirements, section 5.7](../firmware/firmware-requirements.md#57-talk-to-the-laptop).

---
