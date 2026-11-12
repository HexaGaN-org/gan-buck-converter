# MCU — Design Notes

Sheet: `sheets/mcu.kicad_sch`

**Owner:** Yunxi He · **Reviewer:** [NAME] · **Last updated:** 2026-11-11

## MCU section

Based on the MCU section of [schematic-hierarchy.md](../schematic-hierarchy.md).

## 5 · MCU — `mcu.kicad_sch`

**Responsible for:** the TMS320F280039C (U501, 64-pin LQFP) and everything it needs to run.

**Contains**
- U501 TMS320F280039C, 64-pin PM package
- Decoupling per TI's datasheet
- Internal core-regulator strapping and core-supply capacitance
- ADC reference and analog-supply capacitance
- **The single net tie joining `GNDA` to `GND`**, at the ADC reference
- Reset (`XRSn`, U501 pin 3) pull-up and capacitor
- Selected external 16 MHz crystal **ESD16.0000F12M25F**, two **18 pF** load capacitors and a **0 Ohm** X2 series resistor
- Boot-mode jumpers on the boot pins
- `HEARTBEAT` (LED502) and `FAULT` (LED501) LEDs; see [indicator-leds.md](indicator-leds.md)

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
- The physical U501 pin allocation is frozen for PCB routing in [pinmux-hardware.md](../firmware/pinmux-hardware.md). The future firmware `pinmux.syscfg` must implement that allocation; update the hardware table and schematic together if a pin moves.
- `MCU_PWMH` / `MCU_PWML` are one ePWM A/B pair on high-resolution-capable pins, with dead time generated in the ePWM.
- `I_OUT_SENSE`, `V_OUT_SENSE` and `V_IN_SENSE` go on ADC pins that also reach CMPSS comparators, routed through the ePWM X-BAR to the trip zone, so overcurrent, output overvoltage and the fast input overvoltage (input_supply decision #24) shut the PWM down in hardware.
- Keep the boot pins free of any function that could be driven during boot.

---

## Purpose and requirements

U501 controls the 48 V-to-12 V buck converter using the TMS320F280039C, 64-pin PM package.

- Generate a high-resolution PWM pair with dead time; measure current, input/output voltage and temperature. Use hardware comparator trips for overcurrent and overvoltage.
- Support open loop, voltage mode and average current mode; provide enable/watchdog control, serial communication, JTAG and status LEDs. Start with switching off and boot from flash.
- Provide power, decoupling, reference, reset and boot circuits. Match the final SysConfig pin assignment and the project's single `GNDA`-to-`GND` net tie.

See [specifications](../specifications.md) for converter targets.

Input-current telemetry (`I_IN_SENSE`) uses U501 physical pin 9 (ADCC C9) for input power and the firmware input-current limit.

---

Check page 57 for connections for Unused Pins

Pins with internal pullup and pulldown:
![alt text](../datasheets/pin-pullup-pulldown-table.png)

Connections for Unused Pins
![alt text](../datasheets/image.png)

- **Unused pins:** The current schematic marks physical pins 6, 7, 10-12, 18-20, 24, 25, 29-34, 47, 54-57 and 61-64 no-connect (25 pins total). Pins 8, 13, 14 and 15 are active sense inputs. No-connect markers do not enable internal pull-ups.
- **Firmware:** Configure unused GPIO5-13, GPIO16, GPIO17, GPIO22, GPIO23, GPIO33 and GPIO41 as GPIO inputs with internal pull-ups enabled. Keep unused analog/DAC functions disabled.

---

## Concrete connections for the selected MCU

Device: **F280039CSPMR**, LCSC **C20345419**, standard 64-pin PM LQFP. The `R` is reel packaging; the pinout matches F280039CSPM. Pin numbers below are physical package pin numbers.

### Pin functions and connections

Supply limits: [TI datasheet, Section 6.12.1.5.1, p. 80](../datasheets/tms320f280039c.pdf#page=80). Power-decoupling capacitor tolerance must be no greater than **20%**; check effective capacitance at operating voltage and temperature. Component values marked proposed still need exact MPNs.

#### `VDDIO`

- **Description:** 3.3 V supply for digital I/O and the internal core regulator.
- **Pins:** 28, 43, 60
- **Connection:** `+3V3`; local decoupling to `GND` at every pin.
- **Decoupling:** Minimum **0.1 µF (100 nF) per pin**; proposed **220 nF at each pin**. Additional regulator output/bulk capacitance depends on the regulator.
- **SR up:** **8-100 mV/µs**.
- **SR down:** **20-100 mV/µs**, falling-rate magnitude.
- **Brownout guardband:** **0.1 V typical** margin above the applicable brownout-reset threshold.
- **Supply arrangement:** Connect VDDIO and VDDA to the common `+3V3` source permitted by TI.
- **Sequence:** Power the supply rails first; external signal pins should only be driven after `XRSn` goes high.
- **Chosen parts:** `Cvddio501`, `Cvddio503`, `Cvddio502` - 220nF; **CL10B224KA8NNNC**; **LCSC C21120**.
- **Capacitor connections:** `Cvddio501.2`, `Cvddio503.2`, `Cvddio502.2 -> +3V3`; pin 1 of each -> GND. Place one capacitor close to each of U501.28, U501.43 and U501.60.

#### `VDDA`

- **Description:** 3.3 V supply for analog circuitry.
- **Pins:** 22
- **Connection:** `+3V3`; local capacitor return to the VSSA-side `GNDA`.
- **Decoupling:** Minimum **2.2 µF per pin**; proposed **4.7 µF** to `GNDA`.
- **Sequence:** Rise with or after VDDIO; enable analog modules only after VDDA reaches its operating voltage. No separate VDDA SR is specified in this table.
- **Chosen part:** `Cvdda501` - 4.7uF; **CL10B475KQ8NQNC**; **LCSC C107368**.
- **Capacitor connection:** `Cvdda501.1 -> +3V3/U501.22`, `Cvdda501.2 -> GNDA`; `U501.21/VSSA -> GNDA`.

#### `VDD`

- **Description:** Internally generated 1.2 V supply for processor logic.
- **Pins:** 4, 27, 44, 59
- **Connection:** Decouple to `GND`; never connect to 3.3 V or use to power other circuitry.
- **Decoupling:** **10-26.8 µF total across all VDD pins**, not per pin. Proposed **4.7 µF per pin = 18.8 µF nominal total**; verify effective capacitance.
- 0603 capacitors
- **SR:** This package uses the internal regulator. The table's external-VREG SR and ramp-delay rows do not apply; external VREG mode is unsupported.
- **Chosen parts:** `Cvdd504`, `Cvdd503`, `Cvdd502`, `Cvdd501` - 4.7uF; **CL10B475KQ8NQNC**; **LCSC C107368**.
- **Capacitor connections:** `U501.4 -> Cvdd504.1`, `U501.27 -> Cvdd503.1`, `U501.44 -> Cvdd502.1`, `U501.59 -> Cvdd501.1`; pin 2 of each capacitor -> GND.

#### `VSS`

- **Description:** Digital ground return.
- **Pins:** 5, 26, 45, 58
- **Connection:** `GND`

#### `VSSA`

- **Description:** Analog ground return.
- **Pins:** 21
- **Connection:** `GNDA`; join to `GND` through the project's single net tie
- **Chosen implementation:** NT501, `Device:NetTie_2`; `NT501.1 -> GND`, `NT501.2 -> GNDA`. Use a single join between these two named grounds.

#### `VREFHI` / `VREFLO`

- **Description:** ADC high and low voltage references.
- **Pins:** 16 / 17
- **Connection:** Reference capacitor between these pins; `VREFLO` to `GNDA`
- **Capacitor:** **2.2 µF ceramic** between pins 16 and 17, close to the MCU.
- **Proposed mode:** Internal reference, **0-3.3 V conversion range**; VREFHI is driven internally at approximately **1.65 V**. Do not tie it to 3.3 V or drive it externally.
- **Chosen part:** `C501` - 2.2uF; **GRM188R71A225KE15D**; **LCSC C86018**.
- **Capacitor connection:** `C501.2 -> U501.16/VREFHI`, `C501.1 -> U501.17/VREFLO -> GNDA`; `U501.21/VSSA -> GNDA`.

#### `XRSn` - physical pin 3

- **Description:** Active-low reset; the MCU can also pull this pin low.
- **Pins:** 3
- **Connection:** Pull up to `+3V3`; share with open-drain supervisor/debugger reset outputs
- **Pull-up:** TI range **2.2-10 kΩ**, used 4.7k.
- **Filter capacitor:** Proposed **10 nF to GND**; TI maximum **100 nF**. Check supervisor/debugger reset behavior, used 22 nF for now
- **Chosen part:** `R502` - 4.7k; **RCT034K7JLF**; **LCSC C177333**.
- **Pull-up connection:** `R502.2 -> +3V3`, `R502.1 -> U501.3/XRSn`; use a bidirectional `XRSn` hierarchical label.
- **Chosen part:** `C502` - 22nF; **CL10B223KB8NNNC**; **LCSC C21122**.
- **Filter connection:** `C502.1 -> U501.3/XRSn`, `C502.2 -> GND`; C502 branches from reset to ground while R502 pulls reset up to +3V3.

#### `TCK` / `TMS`

##### TCK - physical pin 36

- **Function:** JTAG clock input from the debugger; hierarchical label `TCK`, input on the MCU sheet, from `comms_debug`.
- **Connection:** `U501.36 -> TCK` -> top-sheet connection -> H701 pin 11 (TCK).

##### TMS - physical pin 38

- **Function:** JTAG mode-select input from the debugger; hierarchical label `TMS`, input on the MCU sheet, from `comms_debug`.
- **Intended connection:** `U501.38 -> TMS` -> top-sheet connection -> debug header TMS. Branch from the TMS signal through a **2.2 kOhm pull-up to +3V3**; TI recommended.
- **Chosen part for this pin:** `R501`, **2.2 kOhm**, +/-1%, 0603, 100 mW; **0603WAF2201T5E**, **LCSC C4190**. Intended endpoints: `R501.1 -> U501.38/TMS`, `R501.2 -> +3V3`.

#### `TDI` / `TDO`

##### GPIO35 / TDI - physical pin 39

- **Function:** Test Data In, debugger -> MCU; reserve GPIO35 for JTAG. Use an input hierarchical label `TDI` from `comms_debug`.
- **Connection:** `U501.39 -> TDI` -> top-sheet connection -> H701 pin 3 (TDI).
- **Chosen part for this pin:** `R506`, **10 kOhm**, **RCT0310KJLF**, **LCSC C177337**; pull-up, with `R506.1 -> U501.39/TDI` and `R506.2 -> +3V3`.

##### GPIO37 / TDO - physical pin 37

- **Function:** Test Data Out, MCU -> debugger; reserve GPIO37 for JTAG. Use an output hierarchical label `TDO` to `comms_debug`.
- **Connection:** `U501.37 -> TDO` -> top-sheet connection -> H701 pin 7 (TDO).
- **Chosen part for this pin:** `R507`, **10 kOhm**, **RCT0310KJLF**, **LCSC C177337**; pull-up, with `R507.1 -> U501.37/TDO` and `R507.2 -> +3V3`.

#### Boot select `GPIO24` / `GPIO32`

Both pins default high for the planned flash boot, assuming OTP boot settings are unchanged. Reserve them from functions driven during boot. R504 and R505 provide 10 kOhm pull-ups. JP501 and JP502 are normally-open solder jumpers to GND; closing one overrides its pull-up during reset. With JP501 closed and JP502 open, the default boot table selects SCI/Wait boot. Verify the OTP boot configuration before using the recovery mode.

##### GPIO24 - physical pin 35

- **Function:** Boot-mode select, used together with GPIO32.
- **Connection:** `U501.35 -> BOOT_GPIO24 -> R504.1` and `JP501.1`; `R504.2 -> +3V3`; `JP501.2 -> GND`.
- **Chosen parts for this pin:** `R504`, **10 kOhm**, **RCT0310KJLF**, **LCSC C177337**; `JP501`, normally-open copper solder jumper, `Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm`.

##### GPIO32 - physical pin 40

- **Function:** Boot-mode select, used together with GPIO24.
- **Connection:** `U501.40 -> BOOT_GPIO32 -> R505.1` and `JP502.1`; `R505.2 -> +3V3`; `JP502.2 -> GND`.
- **Chosen parts for this pin:** `R505`, **10 kOhm**, **RCT0310KJLF**, **LCSC C177337**; `JP502`, same normally-open copper solder jumper footprint. Both jumpers are excluded from BOM and placement files.

**Layout:** Put JP501 and JP502 on an accessible board face near the MCU, with `BOOT24` and `BOOT32` silkscreen. Keep their traces short and away from switching nodes; leave both open for normal Flash boot. Do not hide them under a heatsink or the debug header.

#### `GPIO18/X2` / `GPIO19/X1`

- **Shared selected crystal:** `X501`, **Monec ESD16.0000F12M25F**, **[JLCPCB C353726](https://jlcpcb.com/partdetail/ZHUHAI_MONECELEC-ESD160000F12M25F/C353726)**; 16 MHz, fundamental AT-cut, CL 12 pF, ESR <=40 Ohm, C0 <=5 pF, maximum drive 1 mW (50 uW nominal); +/-20 ppm initial tolerance and +/-50 ppm temperature stability, -40 to +85 degC.
- **Population/configuration:** Populate the crystal, both load capacitors and the X2 series resistor. Configure firmware for a **16 MHz** external crystal and recalculate the PLL settings for the planned 120 MHz CPU clock. Keep connections short.
- **Chosen load capacitors:** `C503 = C504 = 18 pF`, **Samsung CL10C180JB8NNNC**, **[JLCPCB C1647](https://jlcpcb.com/partdetail/1999-CL10C180JB8NNNC/C1647)** (Basic), C0G, +/-5%, 50 V, 0603. Initial calculation: `CL = C503*C504/(C503+C504) + Cstray = 9 pF + 3 pF = 12 pF`. The 3 pF stray term is an estimate; adjust the capacitor values using the actual layout/frequency result.
- **Chosen R503:** **0 Ohm**, **0603WAJ0000T5E / C15402**, as the initial selection. The crystal's 1 mW maximum drive rating meets TI's drive-rating screening. Board startup and frequency still require verification; any later damping resistance must preserve startup margin.
- **Package/connections:** Two-terminal HC-49SMB SMD crystal, 3.2 mm maximum height. `X501.1 -> U501.42/X1` and C504; `X501.2 -> R503.1` and C503; `R503.2 -> U501.41/X2`. C503/C504 return to GND. Neither crystal terminal connects directly to GND.

Sources: [Monec ESD16.0000F12M25F specifications, p. 2, and package drawing, p. 4](../datasheets/monec-esd16.0000f12m25f.pdf#page=2); [TI frequency limits, p. 88](https://www.ti.com/lit/ds/symlink/tms320f280039c.pdf#page=88); [TI crystal selection/testing and ESR table, pp. 94-95](https://www.ti.com/lit/ds/symlink/tms320f280039c.pdf#page=94).

##### GPIO18 / X2 - physical pin 41

- **Function:** Crystal oscillator output; reserve GPIO18 for the external crystal.
- **Intended connection:** `U501.41/X2 -> R503.2`; `R503.1 -> X501.2` and `C503.2`; `C503.1 -> GND`. The resistor is in series with the crystal branch, and C503 is on the crystal side of it.
- **Chosen parts for this pin:** `R503`, **0 Ohm**, **0603WAJ0000T5E**, **LCSC C15402**; `C503`, **18 pF**, **Samsung CL10C180JB8NNNC**, **JLCPCB/LCSC C1647**; shared crystal X501 as above.

##### GPIO19 / X1 - physical pin 42

- **Function:** Crystal oscillator input; reserve GPIO19 for the external crystal.
- **Connection:** `U501.42/X1 -> X501.1` and `C504.2`; `C504.1 -> GND`.
- **Chosen parts for this pin:** `C504`, **18 pF**, **Samsung CL10C180JB8NNNC**, **JLCPCB/LCSC C1647**; shared crystal X501 as above.

#### ADC inputs (`Ax`, `Bx`, `Cx`)

- **Description:** Analog-to-digital channels; 12-bit results range from 0 to 4095. The selected reference mode gives a 0-3.3 V measurement range.
- **Pins:** 6-15, 18-20, 23-25; names such as `A0`, `B2` and `C6` identify internal ADC channels.
- **Connection:** Scaled 0-3 V sensing signals; see the proposed channel assignments below.
- **Input RC/clamps:** Owned by sensing; values in [sensing.md](sensing.md). Meet acquisition time, input protection limits and comparator-trip bandwidth.

#### `DACA_OUT` / `DACB_OUT`

- **Description:** Digital-to-analog voltage outputs.
- **Pins:** 15 / 14, shared with ADC inputs.
- **Connection:** Connect to an analog-output circuit if needed; follow Table 5-10 when unused.

#### `GPIOx`

Digital inputs/outputs with peripheral functions selected in firmware. Each used pin below lists its own purpose, associated parts and known endpoints. Destination-sheet connector pin numbers and unselected parts stay TBD. Unassigned GPIOs have no new assignments or parts implied here.

The former duplicate pull-downs were removed from this sheet on 2026-11-11. Enable-sheet R608/R611/R604 are now the single 10 kOhm default-off pull-downs on `MCU_PWMH`, `MCU_PWML` and `MCU_EN`, to be placed near their receiving logic. Each draws about 0.33 mA from a high 3.3 V MCU output. Keep the status LEDs off during startup and verify their current and package polarity.

##### GPIO0 - physical pin 52 - `MCU_PWMH`

- **Function:** EPWM1_A output; high-side PWM in the high-resolution-capable A/B pair. Generate dead time in ePWM.
- **Connection:** `U501.52 -> MCU_PWMH` -> enable sheet MCU_PWMH input, held low when undriven by R608 on enable. Hardware enable gates this signal before the driver.
- **Chosen parts for this pin:** No local pull-down; R608 on enable is 10 kOhm.

##### GPIO1 - physical pin 51 - `MCU_PWML`

- **Function:** EPWM1_B output; low-side PWM paired with EPWM1_A, with dead time generated in ePWM.
- **Connection:** `U501.51 -> MCU_PWML` -> enable sheet MCU_PWML input, held low when undriven by R611 on enable. Hardware enable gates this signal before the driver.
- **Chosen parts for this pin:** No local pull-down; R611 on enable is 10 kOhm.

##### GPIO2 - physical pin 50 - `MCU_EN`

- **Function:** GPIO output requesting switching; the request is only one condition of hardware enable.
- **Connection:** `U501.50 -> MCU_EN` -> enable sheet MCU_EN input, held low when undriven by R604 on enable.
- **Chosen parts for this pin:** No local pull-down; R604 on enable is 10 kOhm.

##### GPIO3 - physical pin 49 - `WD_IN`

- **Function:** GPIO output providing the external windowed-watchdog check-in signal. Both too-fast and too-slow check-ins must count as failures.
- **Connection:** `U501.49 -> WD_IN` -> enable sheet U601 (TPS3813K33) pin 1. The watchdog timing is documented in [enable.md](enable.md); firmware must implement the kick schedule.
- **Chosen parts for this pin:** No local support part selected for this pin; the watchdog is owned by the enable sheet.

##### GPIO4 - physical pin 48 - `STAGE_EN_FB`

- **Function:** GPIO input reading the hardware-enable state.
- **Connection:** Enable sheet U602 pin 3 (`STAGE_EN`) through R605 to `STAGE_EN_FB -> U501.48`.
- **Chosen parts for this pin:** No local support part selected for this pin.

##### GPIO28 - physical pin 2 - `SCI_RX`

- **Function:** SCIA_RX input receiving serial data from the USB-UART bridge.
- **Connection:** CP2102N-A02-GQFN24R U701 pin 21 (TXD) -> comms_debug SCI_RX output -> `SCI_RX -> U501.2`.
- **Chosen parts for this pin:** No local support part selected for this pin; UART bridge is on comms_debug.

##### GPIO29 - physical pin 1 - `SCI_TX`

- **Function:** SCIA_TX output transmitting serial data to the USB-UART bridge.
- **Connection:** `U501.1 -> SCI_TX` -> comms_debug SCI_TX input -> bridge RX. CP2102N-A02-GQFN24R U701 pin 20 is RXD.
- **Chosen parts for this pin:** No local support part selected for this pin; UART bridge is on comms_debug.

##### GPIO39 - physical pin 46 - `HEARTBEAT`

- **Function:** GPIO output driving the local green heartbeat/status LED.
- **Connection:** `U501.46 -> R509`; `R509 -> LED502` anode; LED502 cathode `-> GND`. R509 is the series current-limiting resistor.
- **Chosen parts for this pin:** `R509`, **330 Ohm**, **0603WAF3300T5E**, **LCSC C23138**; `LED502`, green **KT-0805G**, **LCSC C2297** (≈ 1 mA; [indicator-leds.md](indicator-leds.md)). Replaces the 0603 green (C12624, an Extended part) and its 1 kOhm resistor.

##### GPIO40 - physical pin 53 - `FAULT`

- **Function:** GPIO output driving the local red fault LED.
- **Connection:** `U501.53 -> R508`; `R508 -> LED501` anode; LED501 cathode `-> GND`. R508 is the series current-limiting resistor.
- **Chosen parts for this pin:** `R508`, **1 kOhm**, **0603WAF1001T5E**, **LCSC C21190**; `LED501`, red **NationStar NCD0805R1**, **LCSC C84256** (≈ 1.1 mA; [indicator-leds.md](indicator-leds.md)). Replaces the 0603 red KT-0603R (C2286).

### Frozen hardware signal-to-pin assignment

This table is summarized in the [routing pin assignment](../firmware/pinmux-hardware.md), which records the saved schematic, TI package/function check, and the remaining SysConfig work. The hardware pin allocation is frozen; peripheral configuration and trip routing are not yet implemented.

| Net | Direction | Physical pin | MCU function | Destination / purpose |
|---|---|---|---|---|
| `MCU_PWMH` | out | 52 | GPIO0 / EPWM1_A | enable; high-side PWM |
| `MCU_PWML` | out | 51 | GPIO1 / EPWM1_B | enable; low-side PWM, paired dead time |
| `I_OUT_SENSE` | in | 8 | A3 on **ADCA, alone**; CMPSS3 high comparator (`CMP3_HP5`) | sensing; current feedback and cycle-by-cycle overcurrent trip |
| `V_OUT_SENSE` | in | 14 | B7 on **ADCB, alone**; CMPSS1 (`CMP1_HP4`) | sensing; output feedback and latched overvoltage trip |
| `V_IN_SENSE` | in | 15 (as wired) | C15 on ADCC; CMPSS3 low comparator (`CMP3_LP2`) | sensing; feedforward, UVLO and the fast input-overvoltage trip (input_supply #24) |
| `I_IN_SENSE` | in | 9 (as wired) | C605 on ADCC; ADC only | sensing; input current (telemetry, input power, firmware current limit) |
| `HS_TEMP_SENSE` | in | 23 | C14 on ADCC; ADC only | sensing; high-side FET temperature |
| `LS_TEMP_SENSE` | in | 13 | C502 on ADCC; ADC only | sensing; low-side FET temperature |
| `MCU_EN` | out | 50 | GPIO2 | enable; request switching |
| `WD_IN` | out | 49 | GPIO3 | enable; external watchdog check-in |
| `STAGE_EN_FB` | in | 48 | GPIO4 | enable; hardware enable feedback |
| `SCI_TX` | out | 1 | GPIO29 / SCIA_TX | comms_debug; MCU TX to bridge RX |
| `SCI_RX` | in | 2 | GPIO28 / SCIA_RX | comms_debug; MCU RX from bridge TX |
| HEARTBEAT LED | out | 46 | GPIO39 | LED502 via R509 (green) |
| FAULT LED | out | 53 | GPIO40 | LED501 via R508 (red) |

Reserve the fixed debug/boot pins above. Use hierarchical labels for signals between sheets; LEDs stay local.

**Protection and ADC plan (updated 2026-11-11).** CMPSS3 is shared: its high comparator reads `I_OUT_SENSE` on pin 8 for cycle-by-cycle overcurrent, and its low comparator reads `V_IN_SENSE` on pin 15 for latched input overvoltage. Set the low comparator's DAC to about 1.43 V and invert its output so a voltage **above** the limit trips. CMPSS1 high handles output overvoltage on `V_OUT_SENSE`; CMPSS2 is unused. The high and low comparators in CMPSS3 have separate threshold DACs and filters, but their ePWM X-BAR trip routes and fault responses must remain distinct. The DAC reference is VDDA (`+3V3`); VDAC is taken by `I_OUT_SENSE` on pin 8. Route overcurrent as cycle-by-cycle and both overvoltages as one-shot (latched). Thresholds, DAC codes and setup order are in [firmware-requirements.md](../firmware/firmware-requirements.md) §5.3. `I_OUT_SENSE` and `V_OUT_SENSE` each have an ADC to themselves; `V_IN_SENSE`, `I_IN_SENSE` and both temperature signals share ADCC.

**Pin mapping:** keep the schematic's existing `V_IN_SENSE` pin 15 and `I_IN_SENSE` pin 9. Pin 15 supports `CMP3_LP2`; pin 18 supports `CMP4_HP2` but is no longer needed for this trip ([TI F28003x datasheet](https://www.ti.com/lit/ds/symlink/tms320f280039c.pdf), analog pin table). Confirm the CMPSS3 input mux and separate trip routes in SysConfig when firmware is implemented.
