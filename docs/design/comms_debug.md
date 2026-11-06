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
| Serial bridge | USB-to-UART bridge with decoupling and 3.3 V MCU-side I/O. CP2102N or equivalent. |
| UART wiring | MCU `SCI_TX` (U1 pin 1, GPIO29 / SCIA_TX) -> bridge RX; bridge TX -> MCU `SCI_RX` (U1 pin 2, GPIO28 / SCIA_RX). |
| Power | USB must not power the board. Bridge I/O uses board `+3V3`; ensure USB/UART connections cannot back-power the MCU when the board is off. |
| Debug connector | J4 TI-compatible JTAG header carrying `TCK`, `TMS`, `TDI`, `TDO`, `XRSn`, target-voltage reference and GND; pinout must match the debugger. |
| Reset | Share active-low `XRSn` with MCU and enable sheets; debugger reset must be compatible with the existing open-drain reset network. |
| Host link | Text commands and status at approximately 10-50 updates/s: state, fault, input/output voltage, current, temperature, duty and frequency. Serial work must not delay the control interrupt. |

### Chosen parts and values

| Item | Chosen parts / values |
|---|---|
| USB connector | J3 **TYPE-C-31-M-12** ([C165948](https://jlcpcb.com/partdetail/C165948)); 2 × **5.1 kΩ** CC pull-downs (C23186); **USBLC6-2SC6** ESD protection (C7519). |
| Serial bridge | **CP2102N-A02-GQFN24R** ([C969151](https://jlcpcb.com/partdetail/C969151)); **100 nF** (C14663) and proposed **10 µF** (C96446) decoupling; bulk quantity pending effective-capacitance check. |
| UART wiring | `SCI_TX` (U1.1) -> bridge RX; bridge TX -> `SCI_RX` (U1.2). |
| Power | Board `+3V3`; USB VBUS sense divider: **22.1 kΩ** upper (C25961), **47.5 kΩ** lower (C23061). USB VBUS stays separate from board supply rails. |
| Debug connector | J4 **FTR-110-03-G-D-06-TR** ([C3332048](https://jlcpcb.com/partdetail/Samtec-FTR_110_03_G_D_06TR/C3332048)), cTI-20; external **TI XDS110 / TMDSEMU110-U**. JLC Extended, Economic-compatible; assembly support fixture required. |
| Reset | J4 pin 15 -> `XRSn`; existing MCU **4.7 kΩ + 22 nF** network. Bridge `RSTb`: separate **1 kΩ** pull-up (C21190). |
| Host link | Text commands/status at **10-50 updates/s**; UART baud rate and framing TBD. |

### Sheet interfaces

Directions below are relative to **comms_debug**. Use hierarchical labels with these exact names.

| Signal | Direction | Connection |
|---|---|---|
| `SCI_TX` | in | MCU -> bridge RX |
| `SCI_RX` | out | Bridge TX -> MCU |
| `TCK`, `TMS`, `TDI` | out | Debugger -> MCU |
| `TDO` | in | MCU -> debugger |
| `XRSn` | bidir | MCU, enable and debugger reset |

**Before schematic freeze:** verify bridge decoupling, header pinout and board-off back-power behavior, and agree the UART baud rate/framing with firmware. Define commands and range/state checks in `firmware/PROTOCOL.md`; see [firmware requirements, section 5.7](../firmware/firmware-requirements.md#57-talk-to-the-laptop).

---
