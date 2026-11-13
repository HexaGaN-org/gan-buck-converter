# Schematic Hierarchy — 48 V → 12 V GaN Synchronous Buck

This document is the contract between sheets: what each sheet is responsible for, what it contains, and every signal that crosses between sheets. How each sheet is designed inside (decisions, calculations, parts) lives in its design note in [design/](design/). For what the board is and does, see the [README](../README.md); for the design targets, see [specifications.md](specifications.md).

> **Status:** The physical MCU pin allocation is frozen for PCB routing in [firmware/pinmux-hardware.md](firmware/pinmux-hardware.md). A TI `pinmux.syscfg` and generated firmware are still pending. Update this document, the hardware pin table, and the schematic together if a sheet interface or physical pin changes.

**Current capture (2026-11-12):** All six sheets are captured and **the root sheet is wired**: every sheet pin connects to its counterpart, so all signals in the glossary below cross their sheet boundaries. The hierarchy has 219 annotated components. ERC reported zero violations under the project's configured checks on 2026-11-11, after imported-symbol pin typing was corrected; it has not been re-run since the power-stage capacitor banks were reduced on 2026-11-12, and the PCB has not yet been updated from the schematic. The physical MCU pin allocation is recorded in [firmware/pinmux-hardware.md](firmware/pinmux-hardware.md). Dynamic PWM overlap protection and power-rail handover margins remain open design decisions before layout freeze. The reset interface is named `XRSn`.

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
| J201 | input_supply | 48 V input, XT30PW-M30.G.Y male, C431092; JLC-imported symbol pin 2 positive, pin 1 `V_IN_RTN`; pins 3/4 mounting tabs, no-connect |
| J301 | power_stage | 12 V output, XT60PW-F female, C428722; JLC-imported symbol pin 3 `V_OUT`, pin 4 `GND`; pins 1/2 mounting tabs, no-connect |
| USBC701 | comms_debug | USB-C to a host laptop (data only; never powers the board) |
| H701 | comms_debug | JTAG debug header (2 × 10) |
| SW601 | enable | On-board hardware enable switch (MSK12C02 slide switch) |
| J202 | input_supply | External 5 V input from a bench supply, for low-voltage bring-up. Keyed JST XH 2-pin, so 48 V leads can't land on it |
| H101–H104 | top | Plated 3.2 mm M3 mounting holes, pads on no net (not connectors; listed here because they are the board's other mechanical interface) |

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

**Contains:** the six sheet symbols wired together by their hierarchical pins; four plated M3 mounting holes H101–H104 (`Mechanical:MountingHole_Pad` with a no-connect flag on each pin, footprint `MountingHole_3.2mm_M3_Pad`, excluded from the BOM and position files); a *Main Specifications* text block; a *Power Tree* diagram; and the project title. References on this sheet use the 100 range.

**Power tree (2026-11-10).** A drawing only (text boxes and arrow graphics, nothing on the board or in the BOM). Rails are solid boxes, converters dashed. It shows each rail's voltage and maximum current; the values come from the design notes, which remain the reference if the two ever differ:

| Rail | On the sheet | Set by |
|---|---|---|
| `V_IN` | 48 V, 3.95 A max | Full load at 40 V input ([design/input_supply.md](design/input_supply.md)) |
| `V_OUT` | 12 V, 12.5 A max | Output current limit ([specifications.md](specifications.md)) |
| `5V_AUX` | 5.0 V, 1 A max | LM5164 rating |
| `5V_EXT` | 5.0 V, 1.24 A max | TPS2121 current limit |
| `+5V` | 5.0 V, 1.24 A max | TPS2121 current limit when fed from J202; 1 A when fed from `5V_AUX` |
| `+3V3` | 3.3 V, 1.2 A max | LDL1117 rating |

Path: `V_IN` → power stage → `V_OUT`; `V_IN` → aux regulator (LM5164) → `5V_AUX`; `5V_AUX` or `5V_EXT` → power mux (TPS2121) → `+5V` → LDO (LDL1117) → `+3V3`. Expected load on the low-voltage rails is about 150 mA.

Fiducials are not placed: Economic PCBA does not need them ([guides/jlcpcb-assembly.md](guides/jlcpcb-assembly.md)).

**As wired (2026-11-10):** the enable sheet has two hierarchical labels each for `MCU_PWMH` and `MCU_PWML`, so its symbol carries two pins for each; both are wired to the MCU's single pin. `XRSn` joins mcu, enable and comms_debug on one net.

**Grounding note:** the holes are plated for a durable bearing surface under the screw heads, but their pads are on no net. Never tie them to `GND`; keep inner-plane clearance around each barrel and keep other copper clear of the washer and standoff footprint on both outer layers. Board `GND` is separated from J201− by Q201 ([design/input_supply.md](design/input_supply.md) decision #6). With normal lead polarity, an earthed supply negative plus earthed USB/JTAG/scope ground provides a parallel return path around Q201. That path can carry input current through external equipment; it does not by itself imply that a simple reversed-lead hookup energizes the board. Use a floating 48 V supply for the standalone prototype and review shared-ground installations separately.

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
- Two-input power multiplexer (TPS2121): `5V_EXT` and `5V_AUX` feed `+5V`, with reverse-current blocking, fast switchover and an overvoltage cutoff on `5V_EXT`. R212 = 26.1 kΩ lets healthy aux take over before J202 is removed in the nominal case; the actual source near two equal 5 V supplies is tolerance dependent.
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
- Test points `TP_SW`, `TP_VOUT`, `TP_VIN`, with ground points `TP_GND301` / `TP_GND302` beside them for short scope grounding

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
- TP402–TP407 on the six filtered sense outputs and TP401 on `GNDA`; place accessible pads near their measurement circuits

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

**Responsible for:** the TMS320F280039C (U501, 64-pin LQFP) and everything it needs to run.

**Contains**
- U501 TMS320F280039C, 64-pin PM package
- Decoupling per TI's datasheet
- Internal core-regulator strapping and core-supply capacitance
- ADC reference and analog-supply capacitance
- **The single net tie joining `GNDA` to `GND`**, at the ADC reference
- Reset (`XRSn`) pull-up and capacitor
- External 16 MHz crystal X501 (Monec **ESD16.0000F12M25F**), two **18 pF** load capacitors and a 0 Ω X2 series resistor (R503)
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
- Every U501 pin assignment must match [firmware/pinmux-hardware.md](firmware/pinmux-hardware.md). The future TI `pinmux.syscfg` must implement that allocation. Design guidance is in [design/mcu.md](design/mcu.md).

---

## 6 · Enable — `enable.kicad_sch`

**Responsible for:** making sure the half-bridge can only switch when a person has enabled it, the watchdog is healthy, and the MCU is requesting it. Firmware can request switching but can never force it.

**How it works**
1. `STAGE_EN` = enable switch on (`SW_EN`) AND `SUP_OK` AND `MCU_EN`. `SUP_OK` is the supervisor's one output: low while `+3V3` is low, for 25 ms after it recovers, and for 25 ms after any watchdog violation.
2. Each PWM signal is ANDed with `STAGE_EN` and with the **inverse of the other PWM** before it reaches the power stage:
   - `HS_PWM` = `MCU_PWMH` AND `STAGE_EN` AND NOT `MCU_PWML`
   - `LS_PWM` = `MCU_PWML` AND `STAGE_EN` AND NOT `MCU_PWMH`

   When `STAGE_EN` is low, both gates are held off. Sustained both-high PWM requests also make both outputs low. Simultaneous rising edges can pass briefly before the common inhibit path responds; this circuit has no proven dynamic break-before-make guarantee (enable.md finding #12). The LM5113-Q1 has independent inputs.
3. During power-up and reset, `SUP_OK` is low, so the gates stay off until the MCU is running.

   As drawn, the static both-high inhibit is a NAND of the two PWM requests (`PWM_ILK_OK`, U605), ANDed with `STAGE_EN` into `PWM_EN` (U604), which then gates each PWM (U603). This is Boolean-equivalent to the equations above only after propagation settles. enable.md decision #8 records an inverter + 3-input-AND form of the same logic.

**Contains**
- Supervisor with window watchdog, TI TPS3813K33 (U601): monitors `+3V3`, produces `SUP_OK`, and pulls `XRSn` low through D601 / R602
- SW601 on-board enable switch, with pull-down so *off* is the default
- AND logic producing `STAGE_EN` (U602)
- Static both-high inhibit and gating: SN74LVC1G00 NAND (U605) and SN74LVC2G08 AND gates (U603, U604) → `HS_PWM` / `LS_PWM`; the MCU ePWM dead-band provides dynamic non-overlap (enable decision #13), which still requires firmware and bench validation
- `ARMED` LED on `STAGE_EN` (see [design/indicator-leds.md](design/indicator-leds.md)), TP603 on `STAGE_EN`, TP601 on `SUP_OK`, and TP602 on GND

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
- USBC701 USB-C receptacle, CC pull-down resistors, USBLC6-2SC6 ESD protection on D+/D− (D701)
- CP2102N USB-to-UART bridge (U701) with its decoupling
- H701 TI JTAG header

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
