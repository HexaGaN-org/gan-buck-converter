# Specifications — 48 V → 12 V GaN Synchronous Buck

The one-page target for the design. Fill in every `[TBD]` before schematic capture starts, and change a value only by updating this file in a pull request.

## Electrical

| Parameter | Min | Typ | Max | Unit | Notes |
|---|---|---|---|---|---|
| Input voltage | [TBD] | 48 | [TBD] | V | Max must stay below 60 V (SELV). Transients at the switch node must stay below 90 V (gate driver HS rating) |
| Output voltage | | 12 | | V | |
| Output current | | | 12.5 | A | Size layout, connectors and parts for 16.7 A (200 W) |
| Output power | | | 150 | W | Design target; ratings sized for 200 W headroom |
| Input current | | 3.3 | | A | At 48 V, full load, ~95 % efficiency |
| Switching frequency | 300 | 400 | 500 | kHz | 400 kHz nominal. Hardware is sized to run anywhere in 300–500 kHz so firmware can sweep it. Decision #4 in [design/power_stage.md](design/power_stage.md) |
| Output voltage ripple | | | 50 | mV p-p | At 300 kHz worst case; ≈ 27 mV expected at 400 kHz |
| Load transient, 10 % → 90 % step | | | [TBD] | mV deviation | Settling time: [TBD] µs |
| Efficiency at full load | [TBD] | | | % | ~95–96 % expected (~6 W loss at 150 W) |
| Efficiency at 20 % load | [TBD] | | | % | |

## Protections

| Protection | Threshold | Response | Implemented by |
|---|---|---|---|
| Cycle-by-cycle overcurrent | [TBD] A | Truncate PWM pulse | CMPSS → ePWM trip zone |
| Output overvoltage | [TBD] V | Disable PWM, latch off | CMPSS / ADC |
| Input undervoltage lockout | [TBD] V on / [TBD] V off | Hold PWM off | ADC / comparator |
| Overtemperature | [TBD] °C | Disable PWM | Thermistor + ADC |
| Hardware enable | — | No switching without it | Hardware logic, independent of firmware |

## Components (decisions)

| Item | Choice | Status |
|---|---|---|
| MCU | TMS320F280039C, 64-pin LQFP (PM) | Chosen. Confirm pin-mux in SysConfig and stock before schematic freeze |
| GaN FETs (×2) | Infineon IGC033S10S1 (LCSC C41381300) — 100 V, 3.3 mΩ max, 3 × 5 mm | Chosen. See [design/power_stage.md](design/power_stage.md) |
| Gate driver | TI LM5113-Q1 (LCSC C2677036) — 90 V GaN half-bridge driver (HS pin 90 V recommended, 93 V absolute max), WSON-10 | Chosen. See [design/power_stage.md](design/power_stage.md) |
| Inductor | Sunltech SLB2212P6R8MTT (LCSC C2842794) — 6.8 µH, 31 A I<sub>sat</sub>, 2.1 mΩ | Chosen. See [design/power_stage.md](design/power_stage.md) |
| Current sensing | 1 mΩ shunt (LCSC C7420016) in series with the inductor; amplifier [TBD] on the sensing sheet | Shunt chosen |

**MCU rationale:** same device as the universal control board, so SysConfig setup, C2000Ware firmware, the LAUNCHXL-F280039C LaunchPad and the team's experience carry over directly. The 64-pin package keeps the schematic and layout simple while retaining what a buck needs: high-resolution PWM, CMPSS comparators for cycle-by-cycle current limiting, and a fast ADC. Early firmware bring-up can run on the LaunchPad before boards arrive.

## Mechanical and other

| Parameter | Value |
|---|---|
| Board size | [TBD] |
| Layer count | [TBD] |
| Input / output connectors | [TBD] |
| Cooling | Natural convection through copper pours (no heatsink planned at 150 W) |
| Debug and comms | JTAG header, USB-UART |

## Test equipment required

The power target must fit inside what the lab can test. Confirm these before committing to 150 W.

| Equipment | Requirement | Available? |
|---|---|---|
| Bench supply | ≥ 48 V at > 3.3 A, with adjustable current limit | [TBD] |
| Electronic load | ≥ 12.5 A at 12 V, 150 W continuous | [TBD] |
| Oscilloscope | Bandwidth and probes suitable for GaN switch-node edges | [TBD] |
