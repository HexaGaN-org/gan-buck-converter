# Enable — Design Notes

Sheet: `sheets/enable.kicad_sch`

**Owner:** Connor Jin · **Reviewer:** [NAME] · **Last updated:** 2026-11-12

---

## Purpose and requirements

Guarantee in hardware that the GaN half-bridge can switch only when the enable switch is on, the watchdog is healthy, reset is released, and the MCU requests switching. Firmware can request switching but never force it.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Enable** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- Implement the gating logic in the **How it works** list of the Enable section of [schematic-hierarchy.md](../schematic-hierarchy.md): `STAGE_EN` from three conditions (enable switch, supervisor, `MCU_EN`), then each PWM gated by the common `PWM_EN` mask. Dynamic overlap protection is still to be proven (pre-layout review finding #12).
- Both gates off in every undriven, floating, power-up and reset state.
- A windowed watchdog: kicks that are too slow or too fast both count as failures.
- Matched gating delay between the high-side and low-side paths, so gating does not eat into dead time: fast logic (74LVC-class).
- Pull-downs on `MCU_PWMH`, `MCU_PWML`, `MCU_EN`, `HS_PWM` and `LS_PWM`, and on the enable-switch input (SW1), so every undriven or floating state means *off*.
- Provide `STAGE_EN_FB` so firmware can read whether the stage is enabled.

**Status (2026-11-11):** captured: supervisor and watchdog, SW1 enable switch, `STAGE_EN` gating, static both-high inhibit as drawn (decision #9), and the `ARMED` LED (#11). Wired to mcu, power_stage and comms_debug on the root sheet (2026-11-10). Test pads for `STAGE_EN`, `SUP_OK`, and GND are in the schematic. Decision #13 assigns dynamic non-overlap to the MCU ePWM dead-band; the existing gates provide no guaranteed dynamic break-before-make. The power-stage input filters add delay but do not establish a positive dead-time margin at all corners.

**5 V rail decision (2026-11-11):** No dedicated `5V_VALID` comparator or hardware inhibit is fitted. Firmware must leave `MCU_EN` and both PWM requests low until `+5V` is stable. This startup rule does not protect against a `+5V` dip while PWM is already active; the LM5113-Q1's VDD operating minimum is 4.5 V. Measure U301 VDD and the driver inputs during both J202/aux transitions before enabling full-power switching. The 3.3 V supervisor does not monitor this rail.

**How the sheet implements it**

1. U7 (TPS3813K33) watches `+3V3` and the `WD_IN` kicks. Its one open-drain RESET output, net `SUP_OK`, covers both of the contract's `RESET_OK` and `WD_OK`: it is low while `+3V3` is below 2.93 V, for 25 ms after `+3V3` recovers, and for 25 ms after any watchdog violation.
2. U3 forms `STAGE_EN` = `SW_EN` AND `SUP_OK` AND `MCU_EN` in two cascaded gates (gate 1 makes `SW_SUP_OK`).
3. U8 (NAND) makes `PWM_ILK_OK`, low only when both PWM requests are high; U5's second gate makes `PWM_EN` = `STAGE_EN` AND `PWM_ILK_OK`; U4 ANDs `MCU_PWMH` and `MCU_PWML` with `PWM_EN` to make `HS_PWM` and `LS_PWM` (decision #9).
4. `SUP_OK` also pulls `XRSn` low through R15 and D1, so a watchdog fault or a sagging rail resets the MCU. The diode makes it one-way: an MCU or debugger reset does not pull `SUP_OK` low.
5. U5's first gate buffers `STAGE_EN` to the `ARMED` LED (LED601); R23 feeds it back to the MCU as `STAGE_EN_FB`.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

The row that stood here as #1 ("Gates off in every fault state") was a bring-up test in the decision table's columns, with no date or decision. It is now verification test 1, unchanged.

Rows 1–7 were written on 2026-11-05 from the schematic as drawn. The rationale is what the datasheets and calculations below support, not a record of the original discussion; the owner should confirm or correct each row and change its status to *Accepted*.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-05 | Supervisor and window watchdog: **TI TPS3813K33DBVR** (U7), monitoring `+3V3` | TPS3850G33 (the "TPS3850-class" part the contract names; its footprint and 3D model are still in `JLCImport`); separate voltage supervisor plus a watchdog timer | One SOT-23-6 does both jobs: 2.93 V threshold (2.87–3.00 V) for a 3.3 V rail, 25 ms reset delay, and a window watchdog set by one capacitor. Its single RESET output covers undervoltage and watchdog faults, so `RESET_OK` and `WD_OK` become one net. Leaded package, easy to inspect and rework | schematic-hierarchy: Enable section still says TPS3850-class, `RESET_OK` and `WD_OK` (open questions) | As drawn — owner to confirm |
| 2 | 2026-11-05 | Watchdog timing: **C5 = 220 pF C0G on WDT, WDR to GND**. Window: kicks must come **5.3–67.7 ms apart** worst case; 20 ms recommended | WDT to GND (fixed 0.25 s, 7.86 ms lower bound); WDT to VDD (fixed 2.5 s, 78 ms); WDR to VDD (window ratio 1:64.5, lower bound ≈ 1.5 ms) | ≈ 95 ms timeout (71–118 ms) limits how long a hung CPU can leave the ePWM switching open-loop to about a tenth of a second; the fixed 2.5 s setting would allow 25 times longer. The 1:25.8 ratio makes the lower bound (≈ 3.7 ms) large enough to catch a runaway loop that kicks too fast. C0G keeps the capacitor's 5 % from adding to the timer's own ±25 % | firmware: rising edge on `WD_IN` every ≈ 20 ms; first kick within 67 ms of reset release (values published below) | As drawn — owner to confirm |
| 3 | 2026-11-05 | Gating in **TI SN74LVC2G08** dual 2-input AND gates throughout (U4's PWM gating superseded by #8): U3 for `STAGE_EN`, U4 for both PWM paths (one package), U5 as the LED buffer | Separate single gates per PWM path (74LVC1G08); a 3-input AND for `STAGE_EN` (74LVC1G11, a second part number) | ≤ 4.7 ns per gate at 3.3 V. Both PWM paths share one die, so their delays track and the gating adds almost nothing to dead time. Ioff (partial power-down): outputs go high-impedance with VCC = 0, so the pull-downs hold the driver inputs low before `+3V3` is up. Inputs tolerate 5.5 V. One part number for three placements. U5's spare gate has its inputs grounded and its output marked no-connect | power_stage: ≤ 4.7 ns added to each PWM path, matched | As drawn — owner to confirm |
| 4 | 2026-11-05 | `SUP_OK` reaches `XRSn` through **D1 (BAT46W) and a 0 Ω link R15**: anode on `XRSn`, cathode toward `SUP_OK` | `SUP_OK` wired straight to `XRSn` (wire-OR); no link to `XRSn` (the supervisor gates the stage but never resets the MCU) | A watchdog fault or sagging rail resets the MCU, but the MCU's own internal-watchdog resets and a debugger reset can't pull `SUP_OK` low. Those cases are still safe: PWM pins go high-impedance and the pull-downs (#5) hold the PWM inputs and `MCU_EN` low. R15 can be lifted for JTAG debugging: a halted core stops kicking and would otherwise be reset every 68–124 ms; with R15 removed a watchdog fault still drops `STAGE_EN`. BAT46W is power_stage's D301 part (no loading fee). *The purpose of R15 is inferred from the circuit* | mcu: `XRSn` (R1 4.7 kΩ, C2 22 nF) is now driven from this sheet; mcu.md still calls the supervisor circuitry unfinished | As drawn — owner to confirm |
| 5 | 2026-11-05 | Default-off **10 kΩ pull-downs**: R19 / R20 on `MCU_PWMH` / `MCU_PWML`, R18 on `MCU_EN`, R21 / R22 on `HS_PWM` / `LS_PWM`, R17 on the J5 input, R13 on `WD_IN`. **R14 10 kΩ pull-up** on `SUP_OK` | Internal pull-downs (the F280039C has none: GPIO pull-ups are disabled through reset and boot, datasheet Table 5-9); pull-downs on the MCU sheet only | Every input is low while the MCU is in reset, booting or unprogrammed. R21 / R22 hold the driver inputs low while `+5V` (driver VDD) is up and `+3V3` (U4's supply) is not, which happens at every power-up because `+3V3` is made from `+5V`. R13 keeps WDI from floating (the TPS3813 requires it driven). R14 is required: TPS3813 RESET is **open-drain** | mcu: former duplicate R7–R9 were removed 2026-11-11; R18–R20 now provide the sole pull-downs on these request nets | As drawn; duplicate cleanup complete 2026-11-11 |
| 6 | 2026-11-05 | J5 enable switch: **JST B2B-XH-A 2-pin**, pin 2 = `+3V3` out, pin 1 back through **R16 1 kΩ**, with R17 10 kΩ to GND. Closed switch gives `SW_EN` = 3.0 V | Switch to GND with a pull-up (open switch would read *on*); screw terminal | An open switch, an unplugged cable or a broken wire all read *off*. R16 limits current and ESD from the off-board wire into U3. A short in the cable harness from `+3V3` to anything is limited by U202 (1.2 A) and, as `+3V3` falls, trips U7, so it fails off. Same part as input_supply's J202 (no loading fee) | input_supply: J5 and J202 are the same header (open questions) | Superseded by #10 |
| 7 | 2026-11-05 | `STAGE_EN_FB` through **R23 1 kΩ**; ENABLE LED (LED3, green) driven by U5 through **R24 100 Ω** | `STAGE_EN` straight to the MCU pin and to the LED | R23 limits current to 3.3 mA if GPIO4 is ever misconfigured as an output. Buffering the LED keeps its ≈ 4 mA off the `STAGE_EN` net. LED3 is the KT-0805G that input_supply uses for the power LED, here at a useful brightness (1.5–5.4 mA) | mcu: `STAGE_EN_FB` on GPIO4 (pin 48) | LED and R24 superseded by #11; R23 as drawn |
| 8 | 2026-11-05 | **Hardware shoot-through interlock** in the PWM gating, replacing U4: `HS_PWM` = `MCU_PWMH` · `STAGE_EN` · NOT `MCU_PWML`, `LS_PWM` = `MCU_PWML` · `STAGE_EN` · NOT `MCU_PWMH`. One dual inverter (TI SN74LVC2G04DBVR, C10428) and two 3-input AND gates (Nexperia 74LVC1G11GW, C282348), one per channel. Supersedes #3 for U4 | Dead time from the ePWM only (no interlock); 2-input interlock gates without `STAGE_EN` (drops the hardware enable); 2-input "AND with one inverted input" gates plus separate `STAGE_EN` gates (4 chips); a driver with a built-in interlock such as the LMG1210 (reopens the driver decision) | The LM5113-Q1 has independent inputs and no interlock. Correct dead time prevents timing shoot-through, but a firmware mistake (dead-band off, both pins driven as GPIO, a debugger halt) could command both FETs on. At 48 V, that can damage the FETs; no safe overlap duration is established. Several people will write ePWM code for the first time on this board. Each PWM goes straight into its own AND gate, so both paths keep one matched gate delay; the inverters only act in the overlap case | power_stage: same `HS_PWM` / `LS_PWM` labels, path delay ≤ ≈ 5 ns. Firmware: the ePWM dead-band is still required; the interlock does not create dead time | Logic accepted; parts superseded by #9; dynamic protection claim superseded by #12 |
| 9 | 2026-11-06 | Interlock **as drawn**: `PWM_ILK_OK` = NAND(`MCU_PWMH`, `MCU_PWML`) in one **TI SN74LVC1G00** (U8, C7826); U5's second gate makes `PWM_EN` = `STAGE_EN` AND `PWM_ILK_OK`; U4 keeps its two AND gates, `HS_PWM` = `MCU_PWMH` AND `PWM_EN`, `LS_PWM` = `MCU_PWML` AND `PWM_EN`. Supersedes #8's parts; the logic is the same | #8's dual inverter + two 3-input AND gates | Same equations as #8: both gates off when both PWM requests are high. Adds one part number (U8) instead of two, and uses U5's spare gate | schematic-hierarchy updated to describe it | Recorded from the schematic — owner to confirm |
| 10 | 2026-11-06 | Enable switch is **SW1, an on-board MSK12C02 slide switch** (C431540) in place of the J5 header: common (pin 2) → R16 1 kΩ → `SW_EN`, pin 1 to `+3V3`, pin 3 open, shell (pin 4) to GND; R17 10 kΩ pull-down unchanged. Supersedes #6's connector | #6's 2-pin XH header J5 for an off-board switch | On-board, so no cable can be plugged in wrong: this removes the J5 / J202 mix-up hazard (open questions). Switch toward pin 1 = run allowed | none | Recorded from the schematic — owner to confirm |
| 11 | 2026-11-06 | `ARMED` LED: **LED601, yellow KT-0805Y** (C2296) through **R601 1 kΩ** (C21190), driven by U5 as before. Supersedes #7's LED3 / R24 | #7's green KT-0805G through 100 Ω | Board LED plan ([indicator-leds.md](indicator-leds.md)): yellow marks the one state you must always notice, ≈ 1 mA like every other LED | none | Accepted |
| 12 | 2026-11-11 | Pre-layout timing review: U8 → U5 → U4 is a **static both-high inhibit**, not a proven dynamic shoot-through interlock. If both MCU PWM requests rise while `PWM_EN` is high, U4 can pass both requests before the common mask falls. The LM5113-Q1 has independent HI/LI inputs | Treat the steady-state Boolean equations in #9 as a timing guarantee | The shared inhibit path has more gates than the direct PWM path. A static both-high GPIO test cannot bound the transient overlap pulse over voltage, temperature, and part spread; the driver has no specified input interlock. ePWM dead-band remains necessary, and a reviewed hardware break-before-make solution is needed if hardware must tolerate simultaneous edges | power_stage, firmware, schematic-hierarchy: revise protection claims and test transient edges before freeze | Resolved by #13: MCU ePWM owns dynamic non-overlap |
| 13 | 2026-11-11 | Rely explicitly on the MCU ePWM dead-band for dynamic non-overlap; retain the current logic only as stage gating and a static both-high inhibit | Add a hardware break-before-make driver or circuit | Configure one complementary ePWM pair and its dead-band before asserting `MCU_EN`; keep PWM pins low through reset and faults; verify both driver inputs and FET gate voltages over operating corners. The static inhibit cannot make an invalid simultaneous-edge command safe | firmware, power_stage, schematic-hierarchy: remove hardware shoot-through guarantee | Decision recorded; firmware and bench validation pending |

---

## Calculations

One row per calculation. Note where each input came from (specification, datasheet, measurement) in Notes.

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| **Supervisor (U7, TPS3813K33)** | | | TI TPS3813 datasheet (SLVS331) |
| Undervoltage margin | $V_{3V3,min} - V_{IT,max}$ | $3.20 - 3.00 = 0.20$ V | `+3V3` is ±3 % over temperature (input_supply #18). The `+5V` hand-over dip doesn't reach `+3V3` (U202 regulates through it) |
| Reset delay after a fault | datasheet $t_d$ | 20 / 25 / 30 ms (min / typ / max) | After `+3V3` recovers and after a watchdog violation |
| Watchdog timeout (upper bound) | $t_{WD} = (C_{WDT}/15.55\,pF + 1) \cdot 6.25\,ms$, ×0.75 / ×1.25 for min / max | 94.7 ms typ; **67.7–123.9 ms** with C5 at ±5 % | Datasheet formula valid for 155 pF–63 nF |
| Lower bound, WDR = GND | $t_{WD,typ}/25.8$; $t_{WD,min}/28.7$; $t_{WD,max}/23.5$ | 3.67 ms typ; **2.36–5.27 ms** | Kicks closer together than this are a fault |
| Safe kick period | between the worst-case bounds | **5.3–67.7 ms**; 20 ms leaves ≈ 3.8× margin below and 3.4× above | A kick is a rising edge on WDI, ≥ 50 ns wide. The first window after reset release has no lower bound |
| First-kick deadline after reset | $t_{WD,min} - t_{XRSn} - t_{boot}$ | $67.7 - 0.1 - 1.2 \approx 66$ ms | XRSn release from the MCU sheet's 4.7 kΩ × 22 nF (96 µs to 2.0 V); boot ROM to flash 1.2 ms max (F280039C datasheet §6.12) |
| `XRSn` low level when U7 asserts | $V_{OL} + V_{F,D1}$ | ≈ 0.25 + 0.32 ≈ 0.57 V max | ≈ 0.59 mA from R1 plus 0.33 mA from R14 into RESET; VOL 0.2 V at 0.5 mA, 0.4 V at 2 mA (TPS3813); BAT46W ≤ 0.32 V near 0.6 mA (estimated from its 0.25 V / 0.1 mA and 0.45 V / 10 mA points). Against the MCU's 0.8 V VIL: 0.23 V margin |
| **Logic timing (SN74LVC2G08)** | | | TI SN74LVC2G08 datasheet (SCES198), 3.3 V ± 0.3 V, 30/50 pF, -40 to 125 °C |
| Gate delay | datasheet $t_{pd}$ | 1.0–5.3 ns | The 4.7 ns figure above applies only through 85 °C; use the full-temperature limit for timing checks |
| PWM path delay added | one gate (U4) | 1.0–5.3 ns per edge under datasheet load | Both paths share one die, but a 1 ns channel-skew guarantee is not specified here; measure the board |
| **Interlock as drawn (decision #9)** | | | U8 (SN74LVC1G00) and U5's second gate feed U4 |
| Static both-high inhibit reaction | U8, U5, then U4 | Up to 15.6 ns by summing published full-transition maxima | The direct rising path is only U4. This sum is not a maximum overlap guarantee; simultaneous rising requests can produce a pulse at both driver inputs |
| `SUP_OK` low → U4 outputs low | four gates (U3 ×2, U5, U4) | Up to 21.2 ns by summing maxima | Then the LM5113 input filter, driver, and FET gates add delay; this is not a measured fault response |
| `MCU_EN` or `SW_EN` low → U4 outputs low | three gates (U3 gate 2, U5, U4) or four (U3 gates 1–2, U5, U4) | Up to 15.9 ns / 21.2 ns by summing maxima | Not a measured fault response |
| Hung CPU, worst case | $t_{WD,max}$ | ePWM can keep switching open-loop for up to ≈ 124 ms | The ePWM runs without the CPU. The CMPSS overcurrent and overvoltage trips act in hardware throughout (sensing, mcu) |
| **Signal levels** | | | |
| `SW_EN`, switch closed | $3.3 \cdot R_{17} / (R_{16} + R_{17})$ | 3.0 V | LVC VIH 2.0 V at 3.0–3.6 V |
| Pull-down load on an MCU output | $3.3\,V / 10\,k\Omega$ | 0.33 mA per pin | One resistor on each net: R19 `MCU_PWMH`, R20 `MCU_PWML`, R18 `MCU_EN`; MCU-side R7–R9 were removed 2026-11-11 |
| `STAGE_EN_FB` fault current | $3.3\,V / R_{23}$ | 3.3 mA | If GPIO4 drove against `STAGE_EN` |
| `ARMED` LED current | $(V_{OH} - V_F) / (R_{601} + R_{out})$ | 0.8–1.4 mA (≈ 1.1 mA typ) | KT-0805Y $V_F$ 1.8–2.4 V; ≈ 30 Ω LVC output resistance estimated from its VOH table |
| `+3V3` load | sum | ≈ 1.5 mA, of which ≈ 1.1 mA is LED601 | TPS3813 ≤ 25 µA; three LVC2G08 and one LVC1G00 ≤ 10 µA each; SW1 0.3 mA when on |

---

## Part selection

Refs match the schematic as of commit `77f9e2e`.

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| U7 | Supervisor and window watchdog | TI TPS3813K33DBVR | C93238 | 2.93 V threshold (2.87–3.00 V), 40 mV hysteresis; 25 ms reset delay; window watchdog with capacitor-set timeout; **open-drain** active-low RESET, valid from VDD = 1.1 V; 9–25 µA; SOT-23-6. Pins: 1 WDI, 2 GND, 3 WDT, 4 VDD, 5 WDR, 6 RESET | [TI](https://www.ti.com/product/TPS3813K33) |
| C5 | Watchdog timing capacitor (WDT) | Samsung CL10C221JB8NNNC | C27675 | 220 pF 50 V **C0G** ±5 % 0603 | |
| U3, U4, U5 | Dual 2-input AND gates | TI SN74LVC2G08DCUR | C91875 | 1.65–5.5 V; $t_{pd}$ ≤ 4.7 ns at 3.3 V; Ioff partial power-down; 5.5 V tolerant inputs; ±24 mA outputs; VSSOP-8 | [TI](https://www.ti.com/product/SN74LVC2G08) |
| D1 | One-way link, `SUP_OK` → `XRSn` | hongjiacheng BAT46W | C7420332 | 100 V Schottky, SOD-123; same part as power_stage D301 | |
| R15 | Supervisor-to-`XRSn` link | UNI-ROYAL 0603WAJ0000T5E | C15402 | 0 Ω, Basic; lift for JTAG debugging (#4) | |
| SW1 | Hardware enable switch | MSK12C02 slide switch | C431540 | On-board SPDT slide switch; common (pin 2) to R16, pin 1 to `+3V3` (decision #10) | |
| R16 | SW1 series resistor | UNI-ROYAL 0603WAF1001T5E | C21190 | 1 kΩ 1 %, Basic | |
| R13, R17, R18, R19, R20, R21, R22 | Pull-downs: `WD_IN`, `SW_EN`, `MCU_EN`, `MCU_PWMH`, `MCU_PWML`, `HS_PWM`, `LS_PWM` | UNI-ROYAL 0603WAF1002T5E | C25804 | 10 kΩ 1 %, Basic | |
| R14 | `SUP_OK` pull-up (U7 RESET is open-drain) | UNI-ROYAL 0603WAF1002T5E | C25804 | 10 kΩ 1 %, Basic | |
| R23 | `STAGE_EN_FB` series resistor | UNI-ROYAL 0603WAF1001T5E | C21190 | 1 kΩ 1 %, Basic | |
| LED601, R601 | `ARMED` LED | KENTO KT-0805Y; UNI-ROYAL 0603WAF1001T5E | C2296; C21190 | Yellow 0805 ($V_F$ 1.8–2.4 V); 1 kΩ, Basic (decision #11). Symbol and footprint imported as Everlight 17-21SUYC, identical pads to the KENTO part | |
| U8 | Interlock NAND, `PWM_ILK_OK` | TI SN74LVC1G00DBVR | C7826 | Single 2-input NAND, 1.65–5.5 V, SOT-23-5 (decision #9) | [TI](https://www.ti.com/product/SN74LVC1G00) |
| C6–C9, C601 | Bypass on `+3V3` | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF, one each for U7 (C6), U3–U5 (C7–C9, drawn as a group) and U8 (C601) | |
| TP601–TP603 | `STAGE_EN`, `SUP_OK`, and GND test pads | Copper test pads | — | `TestPoint_Pad_D2.0mm`; footprint only, excluded from BOM and placement files | |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| Watchdog kick | Rising edge on `WD_IN`, ≥ 50 ns wide, **every 5.3–67.7 ms** (20 ms recommended) | firmware | Too fast is also a fault. Kick from the control loop's health, not a free-running timer, or the watchdog proves nothing |
| First kick after reset | Within ≈ 66 ms of `XRSn` releasing | firmware | Kick early in `main()`, before any slow initialisation |
| Watchdog fault response | `STAGE_EN` low within ≈ 14 ns; `XRSn` low for 20–30 ms, then the MCU reboots | firmware, mcu | Switching resumes only if firmware asserts `MCU_EN` again |
| Hung-CPU exposure | Up to ≈ 124 ms of open-loop switching before the watchdog acts | firmware, power_stage | CMPSS trips stay active in hardware |
| `+3V3` undervoltage reset | Below 2.87–3.00 V; released 20–30 ms after recovery | input_supply, mcu | 0.20 V below the `+3V3` minimum |
| `XRSn` drive | Pulled to ≈ 0.57 V max through D1 while U7 asserts | mcu | One-way: MCU and debugger resets don't reach `SUP_OK` |
| PWM path delay | U4 alone: 5.3 ns maximum at 3.3 V ± 0.3 V and -40 to 125 °C under the datasheet test load; board delay and channel skew remain to be measured | power_stage, firmware | This is the direct PWM-to-U4-output path with `PWM_EN` already asserted. It does not bound the fault-disable path or FET gate-off time. |
| `HS_PWM` / `LS_PWM` default | Low whenever `+3V3` is absent, the MCU is in reset, or any enable condition is false | power_stage | 10 kΩ pull-downs R21 / R22 |
| `STAGE_EN_FB` | Logic-level copy of `STAGE_EN` through 1 kΩ | mcu, firmware | GPIO4 input; lets firmware see that the switch or watchdog has the stage off |
| Load on `+3V3` | ≈ 1.5 mA | input_supply | Mostly LED601 |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- **Place U4 near the gate driver** (U301 on power_stage), so the gated `HS_PWM` / `LS_PWM` traces are short and the long runs from the MCU are the ungated ones. Keep U8 and U5 (which make `PWM_EN`) beside U4. Put R21 / R22 at U4's outputs. Route the two PWM paths side by side with matched length; they carry the dead time.
- **C5 hard against U7's WDT pin.** WDT is a high-impedance timing node: keep it short, away from switching and PWM traces, and clean of flux, since leakage shifts the timeout.
- Place each 100 nF at its IC's VCC pin: C6 at U7, one of C7–C9 at each of U3, U4 and U5, and C601 at U8. The schematic draws C7–C9 as a group, so check the mapping in layout.
- **R15 where it can be reached** with an iron (or replace it with a solder jumper): bring-up will lift it for JTAG work. Put D1 and R15 near the MCU's `XRSn` pin.
- SW1 at a board edge with `ENABLE` silkscreen, at the end of the status-LED row, with LED601 (`ARMED`) beside it so the switch and its effect are seen together ([indicator-leds.md](indicator-leds.md)).
- Keep `SW_EN` away from the PWM and `STAGE_EN` routing.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Default-off logic in every fault state | Walk through power-up, reset, watchdog timeout, enable switch off and a hung MCU; probe `HS_PWM` / `LS_PWM`, then verify Q301/Q302 gate-to-source voltages with suitable probes | Both driver inputs remain low and both FETs remain off in every case | | |
| 2 | Power-up | Scope `+5V`, `+3V3`, `SUP_OK`, `HS_PWM`, `LS_PWM` while powering from J202, then from 48 V | `HS_PWM` / `LS_PWM` stay low throughout; `SUP_OK` rises 20–30 ms after `+3V3` passes 3.0 V | | |
| 3 | Watchdog window | Firmware kicks at 2, 4, 6, 10, 20, 60, 80 and 130 ms periods | No resets from 6 to 60 ms; record where faults start on each side (expect ≈ 2.4–5.3 ms and 68–124 ms) | | |
| 4 | Watchdog fault while switching | Reduced input voltage, PWM running; stop the kicks; measure from `SUP_OK` to U4 outputs and separately to both FET gate-to-source voltages | `SUP_OK` falls within the watchdog's measured timeout; both U4 outputs go low and both FETs turn off. Record each delay; no 20 ns FET gate-off guarantee is established. MCU resets and stays off until `MCU_EN` is asserted again | | |
| 5 | Enable switch | Slide SW1 off while switching at reduced voltage; measure `SW_EN`, U4 outputs and FET gate-to-source voltages | Both U4 outputs go low and both FETs turn off; record each delay. LED601 off; `STAGE_EN_FB` reads low | | |
| 6 | `MCU_EN` | Firmware drops `MCU_EN` while switching | Gates off; LED601 off | | |
| 7 | MCU reset | Debugger or manual reset of the MCU while switching at reduced voltage | Gates off (PWM pins and `MCU_EN` fall to their pull-downs); `SUP_OK` stays high | | |
| 8 | `XRSn` drive | Measure `XRSn` while U7 asserts (stop the kicks) | ≤ 0.6 V | | |
| 9 | Path delay and skew | Scope `MCU_PWMH` → `HS_PWM` and `MCU_PWML` → `LS_PWM` at the U4 pins | Record both delays and skew versus supply and temperature; compare to 5.3 ns datasheet maximum under its stated load. No 1 ns board-skew limit has been established | | |
| 10 | `+3V3` undervoltage | Lower the J202 supply until U202 drops out | Reset asserts at 2.87–3.00 V on `+3V3`; gates off | | |
| 11 | JTAG with R15 lifted | Halt the core in the debugger for > 1 s | No MCU reset; `STAGE_EN` drops when the watchdog times out. Refit R15 afterwards | | |
| 12 | `ARMED` LED | Visual check in room light | Clearly visible | | |
| 13 | Static inhibit and overlap transient | With the power bus unpowered, test sustained both-high requests and simultaneous rising edges at the U4 and LM5113 input pins using a fast, low-capacitance scope setup over supply and temperature corners. Do not intentionally repeat both-high fault requests with the power bus energized during initial bring-up | Sustained both-high inputs produce low outputs. Any simultaneous-edge overlap pulse must be below a separately reviewed driver/FET-safe limit; no limit is yet established, so this test cannot approve the current circuit by itself | | |

---

## Open questions

- **Schematic field fixes before layout** (checked against commit `77f9e2e`):
  - (Fixed 2026-11-11: the enable-sheet C10 was changed to C601, removing its collision with comms_debug's C10.) Other enable references still continue the MCU sheet's numbering (C5–C9, D1, R13–R23, U3–U5, U7, U8) rather than the 600 range CONTRIBUTING asks for. U6 is unused.
  - (Verified 2026-11-11: the sheet title block names Connor Jin as owner.)
  - (Added 2026-11-11: TP601 on `STAGE_EN`, TP602 on `SUP_OK` (`WD_OK` in the contract), and TP603 on GND.) Place TP603 near the signal pads where probe access permits.
  - (Resolved 2026-11-10: the root sheet is wired to mcu, power_stage and comms_debug.) This sheet has two hierarchical labels each for `MCU_PWMH` and `MCU_PWML`, so its root-sheet symbol has two pins for each; both are wired. Remove the duplicate labels when the sheet is next edited.
  - `JLCImport` still holds the TPS3850G33DRCR footprint and 3D model, which nothing uses.
- (Resolved 2026-11-06: schematic-hierarchy.md now describes the TPS3813, the single `SUP_OK` and the interlock as drawn.)
- (Resolved: the interlock is drawn with U8 and U5's spare gate, decision #9. The `SN74LVC2G04` / `74LVC1G11` parts from #8 aren't used.)
- **Dynamic shoot-through protection:** decision #13 relies on the MCU ePWM dead-band. Keep the current NAND/AND chain described as a static fault inhibit and verify non-overlap at the driver inputs and FET gates before applying full bus power.
- **Restart after a fault.** Recovery is automatic: U7 releases after 20–30 ms, the MCU reboots, and firmware could re-enable straight away. Proposed firmware rule: after any reset other than power-on, stay off until a command over the UART, and log the cause.
- **JTAG and the watchdog.** A halted core stops kicking, so with R15 fitted the debugger loses the MCU every 68–124 ms. Write the R15 procedure into the bring-up guide, or replace R15 with a 2-pin jumper.
- (Resolved by decision #10: SW1 is an on-board switch, so there is no J5 header for the 5 V cable to land on.)
- **Duplicate pull-downs resolved 2026-11-11.** MCU-side R7–R9 and their branches were removed. R18–R20 remain here as the only pull-downs on the three MCU request nets; place them near the receiving logic.
- **mcu.md** still says the supervisor and debugger reset circuitry on `XRSn` is unfinished; the supervisor half now exists on this sheet.
