# Schematic Hierarchy — 48 V → 12 V GaN Synchronous Buck

This document is the contract between sheets: what each sheet is responsible for, what it contains, and every signal that crosses between sheets. How each sheet is designed inside (decisions, calculations, parts) lives in its design note in [design/](design/). For what the board is and does, see the [README](../README.md); for the design targets, see [specifications.md](specifications.md).

> **Status:** Draft for schematic capture. Signal names are final once the MCU pin-mux is frozen in `firmware/pinmux.syscfg`. Update this document in the same commit as any change to a sheet boundary or interface signal.

**Current capture (2026-11-10):** All six sheets are captured and **the root sheet is wired**: every sheet pin connects to its counterpart, so all signals in the glossary below now cross their sheet boundaries. Next: annotation into per-sheet ranges and ERC across the hierarchy. The sense signals were renamed in #6 (`I_OUT_SENSE`, `V_IN_SENSE`, `V_OUT_SENSE`, `HS_TEMP_SENSE`, `LS_TEMP_SENSE`, with the new `I_IN_SENSE`); the names below follow the schematic. The reset interface is named `XRSn`.

---

## Sheet tree

```
gan-buck-converter.kicad_sch      1  Top sheet (sheet symbols, mounting holes, notes)
├── input_supply.kicad_sch        2  48 V input, protection, auxiliary rails
├── power_stage.kicad_sch         3  GaN FETs, gate driver, inductor, output
├── sensing.kicad_sch             4  Current, voltage and temperature sensing
├── mcu.kicad_sch                 5  Microcontroller and its support circuits
├── enable.kicad_sch              6  Hardware enable and watchdog
└── comms_debug.kicad_sch         7  USB serial and JTAG
```

The top sheet lives in the KiCad project folder, `hardware/gan-buck-converter/`. All sub-sheets live in its `sheets/` subfolder.

This document names each sheet by its file. The sheet symbols on the top sheet carry display names instead: Input Supply, Power Stage, Sensing, Microcontroller, Enable, and Comms and Debug. KiCad builds hierarchical paths from the display names (for example `/Enable/STAGE_EN`).

## How the sheets connect

**input_supply** protects the 48 V input and makes the low-voltage rails everything else runs on. **power_stage** is the converter itself: it takes the 48 V bus, switches it with a half-bridge of discrete GaN FETs and their gate driver, and delivers 12 V. **sensing** turns the power stage's current, the input and output voltages, and the board temperature into clean 0–3 V signals for the MCU. The **mcu** sheet runs the control loop and generates PWM, but its PWM never reaches the power stage directly: it passes through the **enable** sheet, which gates both PWM signals off unless the hardware enable switch is on, the watchdog is healthy, and the MCU is requesting switching. **comms_debug** connects the MCU to a laptop and a debugger.

---

## Connectors

| Ref | Sheet | Function |
|---|---|---|
| J201 | input_supply | 48 V input |
| J301 | power_stage | 12 V output |
| USBC1 | comms_debug | USB-C to a host laptop (data only; never powers the board) |
| H1 | comms_debug | JTAG debug header (2 × 10) |
| SW1 | enable | On-board hardware enable switch (MSK12C02 slide switch) |
| J202 | input_supply | External 5 V input from a bench supply, for low-voltage bring-up. Keyed JST XH 2-pin, so 48 V leads can't land on it |
| H101–H104 | top | M3 mounting holes with plated pads tied to `GND` (not connectors; listed here because they are the board's other mechanical interface) |

---

## Signal glossary

Every signal that crosses a sheet boundary. Active-low signals end in `_N`.

**Power nets** (global, via power symbols)

Which library each power symbol comes from is in [CONTRIBUTING.md](../CONTRIBUTING.md).

| Net | Meaning |
|---|---|
| `V_IN` | Protected 48 V input bus |
| `V_OUT` | 12 V output |
| `5V_AUX` | Output of the onboard 48 V → 5 V auxiliary regulator (local to input_supply) |
| `5V_EXT` | 5 V from the external header J202, after its reverse-polarity FET (local to input_supply) |
| `+5V` | The selected 5 V rail (via the power mux): GaN driver bias and the 3.3 V LDO input |
| `+3V3` | 3.3 V supply for the MCU (VDDIO and VDDA) and logic |
| `GND` | Board ground (power and signal share one ground plane) |
| `GNDA` | MCU analog ground; joins `GND` at exactly one point |

**Input supply to sensing**

| Signal | Meaning |
|---|---|
| `I_SH_IN_P`, `I_SH_IN_N` | Kelvin connections across the input current-sense shunt R201 (`_P` on the fuse side, `_N` on the `V_IN` side) |

**Power stage to sensing**

| Signal | Meaning |
|---|---|
| `I_SH_OUT_P`, `I_SH_OUT_N` | Kelvin connections across the output current-sense shunt R301 (`_P` on the L301 side, `_N` on the `V_OUT` side) |

**Sensing to MCU**

| Signal | Meaning |
|---|---|
| `I_OUT_SENSE` | Inductor (output) current, scaled to 0–3 V. Feeds a CMPSS comparator for cycle-by-cycle overcurrent |
| `V_OUT_SENSE` | Output voltage, divided to 0–3 V. Feeds a CMPSS comparator for overvoltage |
| `V_IN_SENSE` | Input voltage, divided to 0–3 V. Feeds a CMPSS comparator for the fast input-overvoltage trip (≈ 55 V), and the ADC for undervoltage lockout and feedforward |
| `HS_TEMP_SENSE`, `LS_TEMP_SENSE` | RTD voltages beside the high-side and low-side GaN FETs |
| `I_IN_SENSE` | Input current, scaled to 0–3 V. Telemetry, input power and an input-current limit in firmware; not a hardware trip |

**PWM and enable**

| Signal | Meaning |
|---|---|
| `MCU_PWMH`, `MCU_PWML` | High-side and low-side PWM from the MCU, before gating |
| `MCU_EN` | The MCU's request to switch. Necessary but not sufficient |
| `HS_PWM`, `LS_PWM` | Gated PWM to the half-bridge driver: `MCU_PWMx` AND `STAGE_EN`, and both held off if the MCU requests both at once |
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

**Contains:** the six sheet symbols wired together by their hierarchical pins; four M3 mounting holes H101–H104 (`Mechanical:MountingHole_Pad`, footprint `MountingHole_3.2mm_M3_Pad_Via`, pads tied to `GND`, excluded from the BOM); a *Main Specifications* text block; and the project title. References on this sheet use the 100 range.

**Still to add:** a notes block with the bring-up safety rules from the README. Fiducials are not placed: Economic PCBA does not need them ([guides/jlcpcb-assembly.md](guides/jlcpcb-assembly.md)).

**As wired (2026-11-10):** the enable sheet has two hierarchical labels each for `MCU_PWMH` and `MCU_PWML`, so its symbol carries two pins for each; both are wired to the MCU's single pin. `XRSn` joins mcu, enable and comms_debug on one net.

**Grounding note:** the mounting-hole pads are on board `GND`, which sits above J201− by the drop across Q201 ([design/input_supply.md](design/input_supply.md) decision #6). An earthed standoff plus an earthed supply negative bypasses the reverse-polarity FET; use nylon standoffs or keep the supply floating.

**Does not contain:** circuit components (the mounting holes are footprint-only).

**Owner duty:** when a sub-sheet owner adds or renames a hierarchical label, the top-sheet owner syncs the sheet pins and wires them.

---

## 2 · Input and supply — `input_supply.kicad_sch`

**Responsible for:** protecting the board from the 48 V input and generating the low-voltage rails.

**Contains**
- J201 48 V input connector
- Input fuse
- TVS diode, clamping below the 90 V switch-node limit (see [design/power_stage.md](design/power_stage.md))
- Reverse-polarity protection
- Input bulk capacitance (the low-ESR ceramic capacitors for the switching loop are on power_stage)
- Input current-sense shunt (1 mΩ, high side), after the fuse, TVS and reverse-polarity protection and ahead of `V_IN`, with Kelvin connections brought out as `I_SH_IN_P` / `I_SH_IN_N` through a net tie at each shunt pad
- Auxiliary step-down regulator (LM5164), 48 V → `5V_AUX`, rated for the full input range and the 82.4 V TVS clamp
- J202 external 5 V input (keyed JST XH header), with reverse-polarity protection. Overcurrent is limited by the bench supply and the mux
- Two-input power multiplexer (TPS2121): `5V_EXT` (priority) and `5V_AUX` → `+5V`, with reverse-current blocking on both inputs, fast switchover and an overvoltage cutoff on `5V_EXT`
- `EXT 5V` LED (J202 live) and `48V` LED (`V_IN` live): see [design/indicator-leds.md](design/indicator-leds.md)
- 3.3 V LDO (ST LDL1117S33R) from `+5V` → `+3V3`. No separate analog rail: MCU VDDA runs from `+3V3`
- `POWER` LED on `+3V3` and test points on every low-voltage rail (`V_IN` uses power_stage's `TP_VIN`)

**Interface:** power nets (`V_IN`, `+5V`, `+3V3`, `GND`), plus the input-shunt Kelvin pair. `5V_AUX`, `5V_EXT` and `V_IN_RTN` (J201 negative, ahead of the reverse-polarity FET) stay local to this sheet.

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `I_SH_IN_P`, `I_SH_IN_N` | out | sensing |

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
- Current-sense shunt in series with the output inductor, with Kelvin connections brought out as `I_SH_OUT_P` / `I_SH_OUT_N`, through a net tie at each shunt pad
- Output capacitors
- J301 12 V output connector
- RC snubber footprint across the switch node (DNP by default)
- `12V` LED on `V_OUT` (see [design/indicator-leds.md](design/indicator-leds.md))
- Test points `TP_SW`, `TP_VOUT`, `TP_VIN`, with ground points `TP_GND1` / `TP_GND2` beside them for short scope grounding

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `HS_PWM`, `LS_PWM` | in | enable |
| `I_SH_OUT_P`, `I_SH_OUT_N` | out | sensing |

**Notes**
- The switch node (`SW_NODE`) and the gate nets (`HS_DRIVE`, `LS_DRIVE`) are local labels; they never cross a sheet boundary.
- Design decisions, values and layout rules for this sheet are in [design/power_stage.md](design/power_stage.md).

---

## 4 · Sensing — `sensing.kicad_sch`

**Responsible for:** turning power-stage quantities into clean, protected 0–3 V signals for the MCU.

**Contains**
- Current-sense amplifier across `I_SH_OUT_P` / `I_SH_OUT_N`, scaled so the overcurrent threshold sits well inside 0–3 V
- Input-current amplifier across `I_SH_IN_P` / `I_SH_IN_N` (common mode at `V_IN`)
- Output-voltage divider from `V_OUT`
- Input-voltage divider from `V_IN`
- Two RTD channels, one per GaN FET (each RTD is placed beside its FET in layout)
- Per channel: RC filter and clamp to `+3V3` / `GNDA`
- Test points on each sense signal

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `I_SH_OUT_P`, `I_SH_OUT_N` | in | power_stage |
| `I_SH_IN_P`, `I_SH_IN_N` | in | input_supply |
| `I_OUT_SENSE` | out | mcu |
| `I_IN_SENSE` | out | mcu |
| `V_OUT_SENSE` | out | mcu |
| `V_IN_SENSE` | out | mcu |
| `HS_TEMP_SENSE`, `LS_TEMP_SENSE` | out | mcu |

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
- External 16 MHz crystal X1 (Monec **ESD16.0000F12M25F**), two **18 pF** load capacitors and a 0 Ω X2 series resistor (R4)
- Boot-mode jumpers on the boot pins
- `HEARTBEAT` and `FAULT` LEDs (see [design/indicator-leds.md](design/indicator-leds.md))

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | out | enable |
| `MCU_EN` | out | enable |
| `WD_IN` | out | enable |
| `STAGE_EN_FB` | in | enable |
| `XRSn` | bidir | enable, comms_debug |
| `I_OUT_SENSE`, `I_IN_SENSE`, `V_OUT_SENSE`, `V_IN_SENSE`, `HS_TEMP_SENSE`, `LS_TEMP_SENSE` | in | sensing |
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
1. `STAGE_EN` = enable switch on (`SW_EN`) AND `SUP_OK` AND `MCU_EN`. `SUP_OK` is the supervisor's one output: low while `+3V3` is low, for 25 ms after it recovers, and for 25 ms after any watchdog violation.
2. Each PWM signal is ANDed with `STAGE_EN` and with the **inverse of the other PWM** before it reaches the power stage:
   - `HS_PWM` = `MCU_PWMH` AND `STAGE_EN` AND NOT `MCU_PWML`
   - `LS_PWM` = `MCU_PWML` AND `STAGE_EN` AND NOT `MCU_PWMH`

   When `STAGE_EN` is low, both gates are held off. If firmware ever drives both PWMs high, both gates are held off too (the shoot-through interlock: the LM5113-Q1 has independent inputs and no interlock of its own).
3. During power-up and reset, `SUP_OK` is low, so the gates stay off until the MCU is running.

   As drawn, the interlock is a NAND of the two PWM requests (`PWM_ILK_OK`, U8), ANDed with `STAGE_EN` into `PWM_EN` (U5), which then gates each PWM (U4). This is logically identical to the equations above. enable.md decision #8 records an inverter + 3-input-AND form of the same logic.

**Contains**
- Supervisor with window watchdog, TI TPS3813K33 (U7): monitors `+3V3`, produces `SUP_OK`, and pulls `XRSn` low through D1 / R15
- SW1 on-board enable switch, with pull-down so *off* is the default
- AND logic producing `STAGE_EN` (U3)
- Shoot-through interlock and gating: SN74LVC1G00 NAND (U8) and SN74LVC2G08 AND gates (U4, U5) → `HS_PWM` / `LS_PWM`
- `ARMED` LED on `STAGE_EN` (see [design/indicator-leds.md](design/indicator-leds.md)), test points on `STAGE_EN` and `SUP_OK`

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
- USBC1 USB-C receptacle, CC pull-down resistors, USBLC6-2SC6 ESD protection on D+/D− (D701)
- CP2102N USB-to-UART bridge (U703) with its decoupling
- H1 TI JTAG header

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
