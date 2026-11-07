# Indicator LEDs — Design Notes

Cross-sheet note: the plan for every indicator LED on the board. LEDs sit on four sheets (input_supply, power_stage, mcu, enable); each sheet's own note records its parts once they are in the schematic.

**Owner:** Reza Rahimzadeh · **Reviewer:** [NAME] · **Last updated:** 2026-11-06

**Status (2026-11-06):** implemented on all four sheets (PR #7, then commit `e85a5c7` for the 48V wiring and R211). input_supply was re-annotated in that commit; the references below are the current ones. One difference from the original plan: the 48V LED taps the fuse node instead of `V_IN` (decision #6).

---

## Principles

- **Discrete LEDs only.** Every indicator is a plain LED and resistor.
- **Hardware truth stays in hardware.** An LED that reports a voltage or the enable chain is wired to that net, so it stays correct when firmware hangs or the MCU is in reset. Only HEARTBEAT and FAULT are firmware-driven, because only firmware knows those states.
- **One meaning per color:**
  - **Red:** danger. Hands off, or something tripped.
  - **Yellow:** the stage may switch.
  - **Green:** healthy.
  - **White:** informational.
- **Even brightness:** about 1 mA in every LED.
- **No loading fees:** every LED is a fee-free 0805 part. JLCPCB has no fee-free green, blue or orange in 0603.

---

## Decision log

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-06 | Discrete LEDs, not addressable RGB | WS2812B / SK6812 for all LEDs; one SK6812 replacing HEARTBEAT and FAULT | An addressable LED shows only what firmware last sent, so it can't report hardware states (48 V present, ARMED) truthfully through a hang or reset. All SMD WS2812B parts at JLCPCB are Standard-assembly only. SK6812 parts would add a loading fee, a 5 V level shifter, an SPI + DMA driver to stay out of the 300-cycle control ISR, and pulsed tens-of-mA loads on `+5V`, which also drives the low-side GaN gate | none | Accepted |
| 2 | 2026-11-06 | Seven LEDs: 48V, EXT 5V, 12V at their connectors; POWER, HEARTBEAT, ARMED, FAULT in a status row | Fewer (no 12V); adding USB TX/RX activity LEDs on the CP2102N's GPIO.0 / GPIO.1 | 48V is the one safety indicator the board lacked. 12V kept so output state is visible at J301 without the e-load. USB activity left out: the serial terminal already shows traffic | comms_debug: GPIO.0 / GPIO.1 stay unconnected | Accepted |
| 3 | 2026-11-06 | Colors as in the table below; all 0805 fee-free parts: KENTO KT-0805G (green), KT-0805Y (yellow), KT-0805W (white), NationStar NCD0805R1 (red) | Keeping the 0603 green (C12624, Extended: a loading fee) and 0603 red | One package, four part numbers, no fees. Yellow for ARMED makes the one state you must always notice unique. White sits on a 5 V rail, so its 2.6–3.2 V forward voltage still leaves headroom | mcu, enable: LED part and resistor changes | Accepted |
| 4 | 2026-11-06 | 48V LED fed through **two 100 kΩ 1206 resistors in parallel** (50 kΩ) | One 47 kΩ 1206 (no fee-free part); one 100 kΩ 1206 (≈ 0.5 mA, half as bright as the rest); 0603 resistors (75 V rating, below the 82.4 V clamp) | Same part as R202, so no new part number; 200 V rating; ≈ 1 mA like the other LEDs | none | Accepted |
| 5 | 2026-11-06 | Green LEDs on 3.3 V nets get 330 Ω | Driving them from `+5V` through a transistor | A green's 2.6–3.1 V forward voltage leaves little headroom on 3.3 V, so their current spreads 0.3–2 mA with part tolerance. Accepted for a power and a heartbeat light: still clearly visible, no extra parts | input_supply (R209), mcu (R10) | Accepted |
| 6 | 2026-11-06 | 48V LED taps the **fuse node** (after F201 and D201, ahead of R201) rather than `V_IN` | `V_IN`, after R201 (the original plan) | Either works: the two nodes are 1 mΩ apart. At the fuse node the LED's ≈ 1 mA stays out of the input-current reading, as R202's gate-drive current does | input_supply: none | Accepted |

---

## The LEDs

| Ref (planned) | Sheet · owner | Silkscreen | Shows | Driven by | Color · part | Resistor | Current | Location |
|---|---|---|---|---|---|---|---|---|
| LED201 | input_supply · Reza | `48V` | Input live, including charge left on the input capacitors | fuse node → R203 ∥ R204 → LED → GND | red · NCD0805R1 (C84256) | 2 × 100 kΩ 1206 (C17900) in parallel | 0.76 mA at 40 V · 0.92 at 48 V · 1.6 at the 82.4 V clamp | Beside J201 |
| LED203 | input_supply · Reza | `EXT 5V` | J202 is live | `5V_EXT` → R211 → LED → GND | white · KT-0805W (C34499) | R211 2.2 kΩ (C4190) | ≈ 0.95 mA (0.8–1.1) | Beside J202 |
| LED301 | power_stage · Reza | `12V` | `V_OUT` live | `V_OUT` → R307 → LED → GND | green · KT-0805G (C2297) | R307 10 kΩ (C25804) | ≈ 0.9 mA | Beside J301 |
| LED202 | input_supply · Reza | `POWER` | Logic rails up (`+3V3` is the last rail in the chain) | `+3V3` → R209 → LED → GND | green · KT-0805G (C2297) | R209 330 Ω (C23138) | ≈ 1.4 mA (0.6–2.1) | Status row, position 1 |
| LED501 | mcu · Yunxi | `HEARTBEAT` | Firmware running; blink rate shows the mode | GPIO39 → R501 → LED → GND | green · KT-0805G (C2297) | R501 330 Ω (C23138) | ≈ 1 mA (0.3–1.8) | Status row, position 2 |
| LED601 | enable · Connor | `ARMED` | `STAGE_EN` high: the hardware enable chain allows switching | U5 → R601 → LED → GND | yellow · KT-0805Y (C2296) | R601 1 kΩ (C21190) | ≈ 1.1 mA (0.8–1.4) | Status row, position 3, at the SW1 end |
| LED502 | mcu · Yunxi | `FAULT` | Latched fault; blinks a code | GPIO40 → R502 → LED → GND | red · NCD0805R1 (C84256) | R502 1 kΩ (C21190) | ≈ 1.1 mA (0.6–1.6) | Status row, position 4 |

---

## Calculations

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| 48V current | $(V - V_F) / 50\,k\Omega$ | 0.76 mA at 40 V, 0.92 mA at 48 V, 0.98 mA at 51 V, 1.6 mA at 82.4 V | NCD0805R1 $V_F$ 1.6–2.6 V (≈ 2.1 V used); $V$ at the fuse node, ≈ `V_IN` |
| 48V resistor dissipation | $(V_{IN} - V_F)^2 / 100\,k\Omega$ each | 24 mW at 51 V; 64 mW at the 82.4 V clamp | 1206 rated 250 mW, 200 V |
| 48V effect on input-current sensing | — | none | Tapped at the fuse node, ahead of R201 (like R202), so the shunt doesn't see it |
| 12V current | $(12 - V_F) / 10\,k\Omega$ | ≈ 0.92 mA | KT-0805G $V_F$ 2.6–3.1 V |
| EXT 5V current | $(5.0 - V_F) / 2.2\,k\Omega$ | 0.82–1.09 mA | KT-0805W $V_F$ 2.6–3.2 V |
| POWER current | $(3.3 - V_F) / 330\,\Omega$ | 0.6–2.1 mA (≈ 1.4 typ) | |
| HEARTBEAT current | $(V_{OH} - V_F) / 330\,\Omega$ | 0.3–1.8 mA | $V_{OH}$ ≈ 3.2 V at this light load |
| ARMED current | $(V_{OH} - V_F) / (1\,k\Omega + R_{out})$ | 0.8–1.4 mA | KT-0805Y $V_F$ 1.8–2.4 V; LVC output ≈ 30 Ω |
| FAULT current | $(V_{OH} - V_F) / 1\,k\Omega$ | 0.6–1.6 mA | NCD0805R1 $V_F$ 1.6–2.6 V |

---

## Firmware behavior

Proposed; the firmware owner confirms these patterns. Both firmware-driven LEDs stay **off during boot** until firmware takes control (as mcu.md asks).

| LED | Pattern | Meaning |
|---|---|---|
| HEARTBEAT | 1 Hz blink | Running, stage idle (STANDBY) |
| HEARTBEAT | ≈ 4 Hz blink | Switching (RUN) |
| HEARTBEAT | Steady on or off | Firmware stuck. If it has also stopped kicking the watchdog, the supervisor resets it within ≈ 125 ms |
| FAULT | Off | No fault |
| FAULT | Steady | Latched fault with no code assigned |
| FAULT | *n* blinks, then a pause | Fault code: 1 overcurrent · 2 output overvoltage · 3 input overvoltage · 4 input undervoltage · 5 overtemperature · 6 unexpected reset |

The fault code is also reported over serial (firmware-requirements.md).

---

## Layout notes

- **Status row:** POWER, HEARTBEAT, ARMED and FAULT in one line on the board edge you face at the bench, in that order (the order things come up during bring-up). Put SW1 at the ARMED end, so you see ARMED respond when you flip the switch. Choose the edge during layout.
- **Connector LEDs:** each beside its own connector, on the board's outer side.
- **48V:** beside J201, but don't let it push D201 away from J201. D201's connection to J201 stays as short as possible.
- **Visibility:** keep every LED outboard of tall parts (L301 at 22 mm square, the C203 can, the screw terminals) so none is hidden from a side view.
- **Routing:** route LED traces away from the switch node and the gate loop. They carry milliamps of DC and need no special routing.
- **Silkscreen:** each LED gets a label next to it (column above).
- **Orientation:** point all cathode marks the same way, to make assembly inspection quick.

---

## Schematic changes

Each owner makes these on their own sheet and updates that sheet's design note in the same commit.

**input_supply (Reza)**
- [x] LED202 `POWER`: keep KT-0805G; **R209 2.2 kΩ → 330 Ω** (C23138).
- [x] LED203 `EXT 5V`: **replace the yellow with KT-0805W white (C34499)**, imported fresh from LCSC. **R211 2.2 kΩ** (C4190).
- [x] **Add** LED201 `48V`: NCD0805R1 (C84256), anode through **R203 and R204, 100 kΩ 1206 each (C17900), in parallel**, from the fuse node; cathode to GND.

**power_stage (Reza)**
- [x] **Add** LED301 `12V`: KT-0805G (C2297), anode through **R307 10 kΩ** (C25804) to `V_OUT`; cathode to GND.

**mcu (Yunxi)**
- [x] LED1 → LED501 `HEARTBEAT`: **0603 green C12624 → KT-0805G (C2297)**, which removes a loading fee. **R10 1 kΩ → R501 330 Ω** (C23138).
- [x] LED2 → LED502 `FAULT`: **0603 red KT-0603R (C2286) → NCD0805R1 (C84256)**. R11 → R502, still 1 kΩ.

**enable (Connor)**
- [x] LED3 → LED601 `ARMED`: **green KT-0805G → yellow KT-0805Y (C2296)**. **R24 100 Ω → R601 1 kΩ** (C21190).

**Library cleanup (after the swaps, in its own commit)**
- [ ] Remove the now-unused `0603_Green_509-620mcd` and `KT-0603R` symbols and footprints from `JLCImport`. Keep `17-21SUYC_TR8`: LED601 uses it, and its footprint is identical to KENTO's own 0805 with KT-0805Y's pad numbering.

---

## Verification

| # | Test | Method | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Even brightness | All LEDs lit, room light, viewed from the status-row edge | No LED clearly dimmer or brighter than the rest | | |
| 2 | 48V tracks the bus | Apply 48 V, then remove it with the stage off | Lights at once; dark within a few seconds of removal | | |
| 3 | ARMED follows `STAGE_EN` | Flip SW1 with the MCU requesting enable, then with the MCU held in reset | Lit only when `STAGE_EN` is high; dark in reset | | |
| 4 | Firmware patterns | Idle, run, and force each fault | Patterns match the table above | | |

---

## Open questions

- (Resolved 2026-11-06, commit `e85a5c7`: the 48V LED as first merged in #7 had one resistor feeding it, the other as a bleeder to `V_IN_RTN`, and its cathode on `V_IN_RTN`, which would have reverse-biased it at ≈ 48 V on a reversed input. Now R203 ∥ R204 feed it and the cathode is on GND.)
- Status-row edge: choose during layout.
