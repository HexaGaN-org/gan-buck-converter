# Comms and Debug — Design Notes

Sheet: `sheets/comms_debug.kicad_sch`

**Owner:** Yunxi He · **Reviewer:** [NAME] · **Last updated:** 2026-11-11

---

## Purpose and requirements

Connect the MCU to a host laptop over USB serial, and to a JTAG debugger for programming and debugging.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Comms and debug** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

## Concise specifications

| Item | Required specification |
|---|---|
| USB connector | USBC1 USB-C, USB 2.0 device; CC pull-down resistors and ESD protection on D+/D−. |
| Serial bridge | USB-to-UART bridge with decoupling and 3.3 V MCU-side I/O. CP2102N or equivalent. |
| UART wiring | MCU `SCI_TX` (U1 pin 1, GPIO29 / SCIA_TX) -> bridge RX; bridge TX -> MCU `SCI_RX` (U1 pin 2, GPIO28 / SCIA_RX). |
| Power | USB must not power the board. Bridge I/O uses board `+3V3`; ensure USB/UART connections cannot back-power the MCU when the board is off. |
| Debug connector | H1 TI-compatible JTAG header carrying `TCK`, `TMS`, `TDI`, `TDO`, `XRSn`, target-voltage reference and GND; pinout must match the debugger. |
| Reset | Share active-low `XRSn` with MCU and enable sheets; debugger reset must be compatible with the existing open-drain reset network. |
| Host link | Text commands and status at approximately 10-50 updates/s: state, fault, input/output voltage, current, temperature, duty and frequency. Serial work must not delay the control interrupt. |

### Chosen parts and values

| Item | Chosen parts / values |
|---|---|
| USB connector | USBC1 **TYPE-C-31-M-12** ([C165948](https://jlcpcb.com/partdetail/C165948)); 2 × **5.1 kΩ** CC pull-downs (C23186); D701 **USBLC6-2SC6** ESD protection (C7519). |
| Serial bridge | U703 **CP2102N-A02-GQFN24R** ([C969151](https://jlcpcb.com/partdetail/C969151)); **100 nF** (C14663) and **4.7 µF** (C107368) decoupling at each supply pin; verify effective capacitance. |
| UART wiring | `SCI_TX` (U1.1) -> bridge RX; bridge TX -> `SCI_RX` (U1.2). |
| Power | Board `+3V3`; USB VBUS sense divider: **22.1 kΩ** upper (C25961), **47.5 kΩ** lower (C23061). USB VBUS stays separate from board supply rails. |
| Debug connector | H1 **FTR-110-03-G-D-06-TR** ([C3332048](https://jlcpcb.com/partdetail/Samtec-FTR_110_03_G_D_06TR/C3332048)), cTI-20; external **TI XDS110 / TMDSEMU110-U**. JLC Extended, Economic-compatible; assembly support fixture required. |
| Reset | H1 pin 15 -> `XRSn`; existing MCU **4.7 kΩ + 22 nF** network. Bridge `RSTb`: separate **1.02 kΩ** pull-up (R717, C705734). |
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

### Saved-schematic interface check (2026-11-11)

The KiCad XML netlist confirms that U703 VIO (5), VDD (6), and VREGIN (7) all connect to board `+3V3`. Their 100 nF and 4.7 uF local capacitor pairs are present. USB VBUS connects to D701 pin 5 and C11, then reaches only U703 VBUS sense pin 8 through R716 22.1 kOhm and R715 47.5 kOhm. It has no direct copper connection to board `+3V3`, VIO, VDD, or VREGIN. The divider output is about 3.41 V at 5.0 V VBUS and 3.58 V at 5.25 V VBUS. This matches the [Silicon Labs CP2102N self-powered reference](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf), including its required current-limited VBUS divider. Silicon Labs explicitly notes that the unpowered VBUS pin may exceed its usual `VIO + 2.5 V` limit, but the divider limits leakage. This establishes the intended static path; it does not measure actual board-off rail voltage or leakage. Effective capacitance of each 4.7 uF part at 3.3 V remains to be verified.

H1's saved netlist matches the [TI CTI-20/XDS110 mapping](https://www.ti.com/lit/ug/sprui94/sprui94.pdf) and [TI C2000 connection guide](https://www.ti.com/lit/an/spracz9a/spracz9a.pdf): 1=TMS, 3=TDI, 5=`+3V3` through R720 100 Ohm as VTRef, 7=TDO, 9=RTCK tied to 11=TCK, 13/14=EMU0/EMU1 with 4.7 kOhm pull-ups, and 15=`XRSn`. Pin 4 (TDIS), ground pins 8/10/12/16/20, and unused EMU2/3/4 pins 17/18/19 return to board GND. Pin 2 (TRST) is unconnected; pin 6 is the absent key position in the chosen footprint. The connector footprint still needs an orientation and mating-cable check at placement.

**Board-off acceptance test:** With J201 and J202 unpowered, connect USB alone, then the selected XDS110 alone, then both. Measure `+3V3` at TP205, U703 VIO/VDD, and `XRSn`; confirm that `+3V3` stays below 0.3 V, the MCU does not boot, and no gate is enabled. Repeat during connection and disconnection. If the rail rises or reset releases, add isolation before full-power operation. Use the floating-output 48 V bench setup from [input_supply.md](input_supply.md#grounding-and-scope-measurements) when USB/JTAG and grounded instruments are attached; their grounds connect to board GND.

**Before firmware freeze:** agree UART baud rate/framing and define commands and range/state checks in `firmware/PROTOCOL.md`; see [firmware requirements, section 5.7](../firmware/firmware-requirements.md#57-talk-to-the-laptop). Physical U1 assignments are recorded in [pinmux-hardware.md](../firmware/pinmux-hardware.md); a compiled TI SysConfig file is still pending.

---
