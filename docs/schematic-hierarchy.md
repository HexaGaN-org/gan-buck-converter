# Schematic Hierarchy — 48 V → 12 V GaN Synchronous Buck

This document defines how the KiCad schematic is divided into hierarchical sheets: what each sheet is responsible for, what it contains, and every signal that crosses between sheets. For what the board is and does, see the [README](../README.md); for the design targets, see [specifications.md](specifications.md).

> **Status:** Draft for schematic capture. Signal names are final once the MCU pin-mux is frozen in `firmware/pinmux.syscfg`. Update this document in the same commit as any change to a sheet boundary or interface signal.

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

Place `V_IN` and `V_OUT` with the `hexagan:V_IN` and `hexagan:V_OUT` power symbols, and the rest from KiCad's standard `power` library. Never rename another power symbol's value to make a net: a typo silently creates a separate net.

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
| `AGND` | MCU analog ground; joins `GND` at exactly one point |

**Power stage to sensing**

| Signal | Meaning |
|---|---|
| `I_SH_P`, `I_SH_N` | Kelvin connections across the current-sense shunt |

**Sensing to MCU**

| Signal | Meaning |
|---|---|
| `ISENSE` | Inductor (output) current, scaled to 0–3 V. Feeds a CMPSS comparator for cycle-by-cycle overcurrent |
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
| `WDI` | Watchdog kick from the MCU. Too slow *or* too fast counts as a failure |
| `XRSN` | MCU reset, active low, open-drain. Driven by the supervisor and the JTAG debugger |

**Host and debug**

| Signal | Meaning |
|---|---|
| `SCI_TX`, `SCI_RX` | MCU UART, named from the MCU's side |
| `TCK`, `TMS`, `TDI`, `TDO` | JTAG |

---

## Owners

| # | Sheet | Owner | Reviewer |
|---|---|---|---|
| 1 | Top | [NAME] | [NAME] |
| 2 | input_supply | [NAME] | [NAME] |
| 3 | power_stage | [NAME] | [NAME] |
| 4 | sensing | [NAME] | [NAME] |
| 5 | mcu | [NAME] | [NAME] |
| 6 | enable | [NAME] | [NAME] |
| 7 | comms_debug | [NAME] | [NAME] |

One owner per sheet. Only the owner edits it; changes from anyone else go through the owner. The reviewer is never the owner.

## Conventions

**Connections between sheets**
- Power nets use KiCad power symbols, which are global.
- Every other signal crosses sheets through **hierarchical labels** only. No global labels.
- Label direction is written from the sheet's own point of view: a signal leaving the sheet is an *output*.

**Net names**
- UPPER_SNAKE_CASE. Active-low signals end in `_N`.
- A net has the same name on every sheet it appears on, exactly as listed in the glossary.

**Reference designators**
- Annotate with *"Use first free number after sheet number × 100"*, so each sheet owns a range (input_supply: R201…, power_stage: R301…). Two people annotating in parallel never collide.
- Connectors keep the fixed designators in this document. The MCU is U1.
- Annotate only new parts on your own sheet. Never re-annotate the whole schematic.

**Other**
- Mark do-not-populate parts with the DNP attribute, not by deleting them.
- Every sheet's title block carries the board revision, sheet title, owner and date.
- Each sheet passes ERC with zero errors before its owner opens a merge.

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
- TVS diode, clamping below the GaN stage's voltage rating
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
- **Why a power mux and not a diode-OR:** the mux selects a source automatically with only milliohms of drop, and blocks reverse current, so the external supply can never back-feed through the aux regulator into the 48 V bus. A Schottky OR drops 0.3–0.5 V, which can push the GaN driver's bias out of its allowed range.
- **Priority:** the external input wins whenever it is present. Plugging in a bench supply is a deliberate act, so it overrides the aux regulator; unplugging it hands the rail back to the aux regulator automatically. Set the priority threshold so a sagging or disconnected bench supply is detected cleanly.
- **Switchover:** size the `+5V` output capacitance so the rail rides through the mux's switchover without browning out the MCU. If the MCU does reset during a switchover, the enable sheet holds both gates off, so the failure is safe.
- **Bring-up order:** bring up the MCU, firmware, sensing and enable logic from a current-limited 5 V bench supply on J6, with no 48 V connected. Only once that works, apply 48 V, then unplug J6 to confirm the hand-over to the aux regulator.
- Rate J6 for at least 0.5 A. Put a test point on each mux input and on `+5V`.
- Size the aux regulator for about 150 mA on `+5V` (GaN driver bias, MCU through the LDO, USB bridge, LEDs), with a part rated for at least 300 mA.
- The TVS clamp voltage, the fuse rating and the GaN stage's maximum voltage must be chosen together. The clamp has to stop a transient before it exceeds the GaN rating, since GaN has essentially no avalanche capability.

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
- This sheet decides most of the board's layout. Mark the power-loop capacitors in the schematic (a field or a note) so the layout owner places them first and closest.
- **Two loops to keep small:** the power loop (input capacitors → high-side FET → low-side FET → back) and each gate loop (driver output → gate resistor → gate → source → driver return). Place the driver right beside the FETs and return each gate loop to its FET's source (Kelvin source where the package offers one), never through the power path.
- **Never exceed the gate limit.** Enhancement-mode GaN gates are driven at about 5 V with an absolute maximum only slightly above it. Check the driver's output level and the bootstrap clamp against the chosen FET's datasheet, and keep gate ringing below the limit.
- **Dead time** is set in the ePWM. Size it from the driver's propagation delay and matching plus the FETs' switching times; GaN's reverse conduction during dead time drops 2 V or more, so too much dead time costs efficiency.
- Prefer FETs in a packaged form (QFN-style) over bare-die chip-scale parts for the first board: they are far easier to assemble and rework by hand.

---

## 4 · Sensing — `sensing.kicad_sch`

**Responsible for:** turning power-stage quantities into clean, protected 0–3 V signals for the MCU.

**Contains**
- Current-sense amplifier across `I_SH_P` / `I_SH_N`, scaled so the overcurrent threshold sits well inside 0–3 V
- Output-voltage divider from `V_OUT`
- Input-voltage divider from `V_IN`
- Thermistor divider (the thermistor itself is placed beside the GaN stage in layout)
- Per channel: RC filter and clamp to `+3V3A` / `AGND`
- Test points on each sense signal

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `I_SH_P`, `I_SH_N` | in | power_stage |
| `ISENSE` | out | mcu |
| `VOUT_SENSE` | out | mcu |
| `VIN_SENSE` | out | mcu |
| `TEMP_SENSE` | out | mcu |

**Notes**
- `ISENSE` bandwidth sets how fast cycle-by-cycle current limiting can act. Keep its filter light; filter `VIN_SENSE` and `TEMP_SENSE` more heavily.
- Size each RC for the ADC's sample-and-hold acquisition time, not only for noise.

---

## 5 · MCU — `mcu.kicad_sch`

**Responsible for:** the TMS320F280039C (U1, 64-pin LQFP) and everything it needs to run.

**Contains**
- U1 TMS320F280039C, 64-pin PM package
- Decoupling per TI's datasheet
- Internal core-regulator strapping and core-supply capacitance
- ADC reference and analog-supply capacitance
- **The single net tie joining `AGND` to `GND`**, at the ADC reference
- Reset (`XRSN`) pull-up and capacitor
- Crystal footprint (DNP; the internal oscillator is used)
- Boot-mode jumpers on the boot pins
- HEARTBEAT and FAULT LEDs

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | out | enable |
| `MCU_EN` | out | enable |
| `WDI` | out | enable |
| `STAGE_EN_FB` | in | enable |
| `XRSN` | bidir | enable, comms_debug |
| `ISENSE`, `VOUT_SENSE`, `VIN_SENSE`, `TEMP_SENSE` | in | sensing |
| `SCI_TX` | out | comms_debug |
| `SCI_RX` | in | comms_debug |
| `TCK`, `TMS`, `TDI` | in | comms_debug |
| `TDO` | out | comms_debug |

**Notes**
- Every U1 pin assignment must match `pinmux.syscfg`. Change the `.syscfg` first, then the schematic.
- `MCU_PWMH` / `MCU_PWML` are one ePWM A/B pair on high-resolution-capable pins, with dead time generated in the ePWM.
- `ISENSE` and `VOUT_SENSE` go on ADC pins that also reach CMPSS comparators, routed through the ePWM X-BAR to the trip zone, so overcurrent and overvoltage shut the PWM down in hardware.
- Keep the boot pins free of any function that could be driven during boot.

---

## 6 · Enable — `enable.kicad_sch`

**Responsible for:** making sure the half-bridge can only switch when a person has enabled it, the watchdog is healthy, and the MCU is requesting it. Firmware can request switching but can never force it.

**How it works**
1. `STAGE_EN` = enable switch on AND `WD_OK` AND `RESET_OK` AND `MCU_EN`.
2. Each PWM signal is ANDed with `STAGE_EN` before it reaches the power stage. When `STAGE_EN` is low, both gates are held off.
3. During power-up and reset, `RESET_OK` is low, so the gates stay off until the MCU is running.

**Contains**
- Windowed watchdog supervisor (TPS3850-class): monitors `+3V3`, drives `XRSN` and the internal `RESET_OK` and `WD_OK`
- J5 enable switch input, with pull-down so an open switch means *off*
- AND logic producing `STAGE_EN`
- Two AND gates: `MCU_PWMx` AND `STAGE_EN` → `HS_PWM` / `LS_PWM`
- ENABLE LED, test points on `STAGE_EN` and `WD_OK`

**Hierarchical labels**

| Signal | Dir | To / from |
|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | in | mcu |
| `MCU_EN` | in | mcu |
| `WDI` | in | mcu |
| `XRSN` | bidir | mcu, comms_debug |
| `HS_PWM`, `LS_PWM` | out | power_stage |
| `STAGE_EN_FB` | out | mcu |

**Notes**
- Pull-downs on `MCU_PWMH`, `MCU_PWML`, `MCU_EN`, `HS_PWM` and `LS_PWM`. Every undriven or floating state must mean *off*.
- Use fast logic gates (74LVC-class) and keep their delay matched between the two PWM paths, so the gating does not eat into the dead time.
- Review walkthrough: power-up, reset, watchdog timeout, enable switch off, MCU hung. Confirm both gates end up off in every case.

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
| `XRSN` | bidir | mcu, enable |

**Notes**
- USB power does not run the board. Power the bridge's I/O from `+3V3`, so a plugged-in laptop cannot back-power the MCU while the board is off.

---

## Before merging a sheet

- [ ] ERC passes with zero errors on that sheet
- [ ] Every hierarchical label matches this document, in name and direction
- [ ] Every U1 pin used matches `pinmux.syscfg`
- [ ] All parts come from the project library, with footprints assigned
- [ ] DNP parts are marked DNP
- [ ] Title block updated (revision, owner, date)
- [ ] Reviewed by the sheet's listed reviewer
