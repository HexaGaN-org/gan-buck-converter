# Schematic Hierarchy — 48 V → 12 V GaN Synchronous Buck

This document is the contract between sheets: what each sheet is responsible for, what it contains, and every signal that crosses between sheets. How each sheet is designed inside (decisions, calculations, parts) lives in its design note in [design/](design/). For what the board is and does, see the [README](../README.md); for the design targets, see [specifications.md](specifications.md).

> **Status:** Draft for schematic capture. Signal names are final once the MCU pin-mux is frozen in `firmware/pinmux.syscfg`. Update this document in the same commit as any change to a sheet boundary or interface signal.

**Current capture:** The MCU sheet is populated and exposes 16 matching parent-sheet pins with open wire stubs. The other five sheets are empty in this working tree. The interfaces below remain the design contract; destination circuits and complete top-sheet signal paths are unfinished. The reset interface is named `XRSn`, matching the current MCU sheet.

---

## Sheet tree

```
gan-buck-converter.kicad_sch      1  Top sheet (sheet symbols only)
├── input_supply.kicad_sch        2  48 V input, protection, auxiliary rails
├── power_stage.kicad_sch         3  GaN FETs, gate driver, inductor, output
├── sensing.kicad_sch             4  Current, voltage and temperature sensing
├── mcu.kicad_sch                 5  Microcontroller and its support circuits
├── enable.kicad_sch              6  Hardware enable and watchdog
└── comms_debug.kicad_sch         7  USB serial and JTAG
```

The top sheet lives in the KiCad project folder, `hardware/gan-buck-converter/`. All sub-sheets live in its `sheets/` subfolder.

## How the sheets connect

**input_supply** protects the 48 V input and makes the low-voltage rails everything else runs on. **power_stage** is the converter itself: it takes the 48 V bus, switches it with a half-bridge of discrete GaN FETs and their gate driver, and delivers 12 V. **sensing** turns the power stage's current, the input and output voltages, and the board temperature into clean 0–3 V signals for the MCU. The **mcu** sheet runs the control loop and generates PWM, but its PWM never reaches the power stage directly: it passes through the **enable** sheet, which gates both PWM signals off unless the hardware enable switch is on, the watchdog is healthy, and the MCU is requesting switching. **comms_debug** connects the MCU to a laptop and a debugger.

---

## Connectors

| Ref | Sheet | Function |
|---|---|---|
| J1 | input_supply | 48 V input |
| J301 | power_stage | 12 V output |
| J3 | comms_debug | USB-C to a host laptop |
| J4 | comms_debug | JTAG debug header |
| J5 | enable | Hardware enable switch (or E-stop) input |
| J6 | input_supply | External 5 V input from a bench supply, for low-voltage bring-up |

---

## Signal glossary

Every signal that crosses a sheet boundary. Active-low signals end in `_N`.

**Power nets** (global, via power symbols)

Which library each power symbol comes from is in [CONTRIBUTING.md](../CONTRIBUTING.md).

| Net | Meaning |
|---|---|
| `V_IN` | Protected 48 V input bus |
| `V_OUT` | 12 V output |
| `+5V_AUX` | Output of the onboard 48 V → 5 V auxiliary regulator |
| `+5V_EXT` | 5 V from the external header J6 |
| `+5V` | The selected 5 V rail (via the power mux): GaN driver bias and the 3.3 V LDO input |
| `+3V3` | 3.3 V digital supply |
| `+3V3A` | Filtered 3.3 V for the MCU's analog circuits (VDDA) |
| `GND` | Board ground (power and signal share one ground plane) |
| `GNDA` | MCU analog ground; joins `GND` at exactly one point |

**Power stage to sensing**

| Signal | Meaning |
|---|---|
| `I_SH_P`, `I_SH_N` | Kelvin connections across the current-sense shunt |

**Sensing to MCU**

| Signal | Meaning |
|---|---|
| `I_SENSE` | Inductor (output) current, scaled to 0–3 V. Feeds a CMPSS comparator for cycle-by-cycle overcurrent |
| `VOUT_SENSE` | Output voltage, divided to 0–3 V. Feeds a CMPSS comparator for overvoltage |
| `VIN_SENSE` | Input voltage, divided to 0–3 V. Used for undervoltage lockout and feedforward |
| `TEMP_SENSE` | Thermistor voltage near the GaN stage |

**PWM and enable**

| Signal | Meaning |
|---|---|
| `MCU_PWMH`, `MCU_PWML` | High-side and low-side PWM from the MCU, before gating |
| `MCU_EN` | The MCU's request to switch. Necessary but not sufficient |
| `HS_PWM`, `LS_PWM` | Gated PWM to the half-bridge driver: `MCU_PWMx` AND `STAGE_EN` |
| `STAGE_EN_FB` | Copy of the internal `STAGE_EN` for the MCU to read |
| `WD_IN` | Watchdog kick from the MCU. Too slow *or* too fast counts as a failure |
| `XRSn` | MCU reset, active low, open-drain. Driven by the supervisor and the JTAG debugger |

**Host and debug**

| Signal | Meaning |
|---|---|
| `SCI_TX`, `SCI_RX` | MCU UART, named from the MCU's side |
| `TCK`, `TMS`, `TDI`, `TDO` | JTAG |

---

Owners and status for each sheet are in the [README](../README.md). Schematic conventions (labels, net names, annotation, DNP) and the merge checklist are in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## 1 · Top sheet

**Responsible for:** showing how the board fits together, and nothing else.

**Contains:** the six sheet symbols wired together by their hierarchical pins, mounting holes, fiducials, and a notes block with the bring-up safety rules from the README.

**Does not contain:** circuit components.

**Owner duty:** when a sub-sheet owner adds or renames a hierarchical label, the top-sheet owner syncs the sheet pins and wires them.

---

## 2 · Input and supply — `input_supply.kicad_sch`

**Responsible for:** protecting the board from the 48 V input and generating the low-voltage rails.

**Contains**
- J1 48 V input connector
- Input fuse
- TVS diode, clamping below the 90 V switch-node limit (see [design/power_stage.md](design/power_stage.md))
- Reverse-polarity protection
- Input bulk capacitance (the low-ESR ceramic capacitors for the switching loop are on power_stage)
- Auxiliary step-down regulator, 48 V → `+5V_AUX`, rated for the full input range
- J6 external 5 V input header, with a fuse or PTC and reverse-polarity protection
- Two-input power multiplexer (TPS2121-class): `+5V_EXT` (priority) and `+5V_AUX` → `+5V`, with reverse-current blocking on both inputs
- SOURCE LED showing when the external input is active
- 3.3 V LDO from `+5V` → `+3V3`
- Analog supply filter (ferrite bead + capacitors) → `+3V3A`
- Power LED and test points on every rail

**Interface:** power nets only (`V_IN`, `+5V`, `+3V3`, `+3V3A`, `GND`). No hierarchical labels. `+5V_AUX` and `+5V_EXT` stay local to this sheet.

**Notes**
- Design guidance and decisions for this sheet are in [design/input_supply.md](design/input_supply.md).

---

## 3 · Power stage — `power_stage.kicad_sch`

**Responsible for:** the converter itself, from the 48 V bus to the 12 V output.

**Contains**
- Two Infineon IGC033S10S1 enhancement-mode GaN FETs, 100 V (high side and low side)
- TI LM5113-Q1 GaN half-bridge gate driver (90 V), with 5.2 V bootstrap clamp, powered from `+5V`
- Driver supply decoupling and bootstrap capacitor at the driver pins, plus the external bootstrap diode and 100 Ω series resistor its datasheet requires
- Gate resistors on the driver's split outputs (values in [design/power_stage.md](design/power_stage.md))
- RC input filters on `HS_PWM` / `LS_PWM` at the driver pins
- High-frequency input capacitors, placed tight against the FETs (the power loop)
- Output inductor
- Current-sense shunt in series with the output inductor, with Kelvin connections brought out as `I_SH_P` / `I_SH_N`, through a net tie at each shunt pad
- Output capacitors
- J301 12 V output connector
- RC snubber footprint across the switch node (DNP by default)
- Test points `TP_SW`, `TP_VOUT`, `TP_VIN`, with ground points `TP_GND1` / `TP_GND2` beside them for short scope grounding

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `HS_PWM`, `LS_PWM` | in | enable |
| `I_SH_P`, `I_SH_N` | out | sensing |

**Notes**
- The switch node (`SW_NODE`) and the gate nets (`HS_DRIVE`, `LS_DRIVE`) are local labels; they never cross a sheet boundary.
- Design decisions, values and layout rules for this sheet are in [design/power_stage.md](design/power_stage.md).

---

## 4 · Sensing — `sensing.kicad_sch`

**Responsible for:** turning power-stage quantities into clean, protected 0–3 V signals for the MCU.

**Contains**
- Current-sense amplifier across `I_SH_P` / `I_SH_N`, scaled so the overcurrent threshold sits well inside 0–3 V
- Output-voltage divider from `V_OUT`
- Input-voltage divider from `V_IN`
- Thermistor divider (the thermistor itself is placed beside the GaN stage in layout)
- Per channel: RC filter and clamp to `+3V3A` / `GNDA`
- Test points on each sense signal

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `I_SH_P`, `I_SH_N` | in | power_stage |
| `I_SENSE` | out | mcu |
| `VOUT_SENSE` | out | mcu |
| `VIN_SENSE` | out | mcu |
| `TEMP_SENSE` | out | mcu |

**Notes**
- Design guidance for this sheet is in [design/sensing.md](design/sensing.md).

---

## 5 · MCU — `mcu.kicad_sch`

**Responsible for:** the TMS320F280039C (U1, 64-pin LQFP) and everything it needs to run.

**Contains**
- U1 TMS320F280039C, 64-pin PM package
- Decoupling per TI's datasheet
- Internal core-regulator strapping and core-supply capacitance
- ADC reference and analog-supply capacitance
- **The single net tie joining `GNDA` to `GND`**, at the ADC reference
- Reset (`XRSn`) pull-up and capacitor
- External 20 MHz crystal **ECS-200-8-30B-CKM**, two **12 pF** load capacitors and an X2 series resistor; populated, using footprint `hexagan:ECS-200-8-30B-CKM`
- Boot-mode jumpers on the boot pins
- HEARTBEAT and FAULT LEDs

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | out | enable |
| `MCU_EN` | out | enable |
| `WD_IN` | out | enable |
| `STAGE_EN_FB` | in | enable |
| `XRSn` | bidir | enable, comms_debug |
| `I_SENSE`, `VOUT_SENSE`, `VIN_SENSE`, `TEMP_SENSE` | in | sensing |
| `SCI_TX` | out | comms_debug |
| `SCI_RX` | in | comms_debug |
| `TCK`, `TMS`, `TDI` | in | comms_debug |
| `TDO` | out | comms_debug |

**Notes**
- Every U1 pin assignment must match `pinmux.syscfg`. Design guidance is in [design/mcu.md](design/mcu.md).

---

## 6 · Enable — `enable.kicad_sch`

**Responsible for:** making sure the half-bridge can only switch when a person has enabled it, the watchdog is healthy, and the MCU is requesting it. Firmware can request switching but can never force it.

**How it works**
1. `STAGE_EN` = enable switch on AND `WD_OK` AND `RESET_OK` AND `MCU_EN`.
2. Each PWM signal is ANDed with `STAGE_EN` before it reaches the power stage. When `STAGE_EN` is low, both gates are held off.
3. During power-up and reset, `RESET_OK` is low, so the gates stay off until the MCU is running.

**Contains**
- Windowed watchdog supervisor (TPS3850-class): monitors `+3V3`, drives `XRSn` and the internal `RESET_OK` and `WD_OK`
- J5 enable switch input, with pull-down so an open switch means *off*
- AND logic producing `STAGE_EN`
- Two AND gates: `MCU_PWMx` AND `STAGE_EN` → `HS_PWM` / `LS_PWM`
- ENABLE LED, test points on `STAGE_EN` and `WD_OK`

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | in | mcu |
| `MCU_EN` | in | mcu |
| `WD_IN` | in | mcu |
| `XRSn` | bidir | mcu, comms_debug |
| `HS_PWM`, `LS_PWM` | out | power_stage |
| `STAGE_EN_FB` | out | mcu |

**Notes**
- Design guidance and the review walkthrough are in [design/enable.md](design/enable.md).

---

## 7 · Comms and debug — `comms_debug.kicad_sch`

**Responsible for:** connecting the MCU to a host laptop (serial over USB) and to a JTAG debugger.

**Contains**
- J3 USB-C receptacle, CC pull-down resistors, ESD protection on D+/D−
- USB-to-UART bridge (CP2102N or equivalent) with its decoupling
- J4 TI JTAG header

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `SCI_TX` | in | mcu |
| `SCI_RX` | out | mcu |
| `TCK`, `TMS`, `TDI` | out | mcu |
| `TDO` | in | mcu |
| `XRSn` | bidir | mcu, enable |

**Notes**
- Design guidance for this sheet is in [design/comms_debug.md](design/comms_debug.md).
