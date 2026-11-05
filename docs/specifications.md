# Specifications — 48 V → 12 V GaN Synchronous Buck

The one-page target for the design. Fill in every `[TBD]` before schematic capture starts, and change a value only by updating this file in a pull request.

## Electrical

| Parameter | Min | Typ | Max | Unit | Notes |
|---|---|---|---|---|---|
| Input voltage | 40 | 48 | 51 | V | Max is set by the input TVS: SMBJ51CA, 51 V standoff, 82.4 V clamp, below the 90 V gate-driver HS rating. Decision #2 in [design/input_supply.md](design/input_supply.md). Below 60 V (SELV) |
| Output voltage | | 12 | | V | |
| Output current | | | 12.5 | A | Size layout, connectors and parts for 16.7 A (200 W) |
| Output power | | | 150 | W | Design target; ratings sized for 200 W headroom |
| Input current | | 3.3 | 3.95 | A | At full load, ~95 % efficiency: typ at 48 V, max at 40 V. 5.3 A at 200 W and 40 V |
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

## Components

The headline parts per sheet. The exact part on the board (MPN, LCSC number, footprint) lives in the KiCad symbol fields; why each part was chosen lives in the sheet's design note.

| Sheet | Key parts | Status | Details |
|---|---|---|---|
| power_stage | 2 × Infineon IGC033S10S1 GaN FETs (100 V); TI LM5113-Q1 gate driver (90 V); 6.8 µH Sunltech SLB2212P6R8MTT inductor; 1 mΩ shunt in series with the inductor | Chosen | [design/power_stage.md](design/power_stage.md) |
| mcu | TI TMS320F280039C, 64-pin LQFP (PM) | Chosen. Confirm pin-mux and stock before schematic freeze | [design/mcu.md](design/mcu.md) |
| sensing | Current-sense amplifiers for the output and input shunts [TBD] | [TBD] | [design/sensing.md](design/sensing.md) |
| input_supply | SMBJ51CA bidirectional TVS; 7 A fuse; low-side reverse-polarity FET (Infineon BSC070N10NS3G); 100 µF damping electrolytic; TI LM5164 aux regulator (100 V, 1 A); TI TPS2121 power mux; JST XH J6; 1 mΩ input current-sense shunt | Chosen; 3.3 V LDO [TBD] | [design/input_supply.md](design/input_supply.md) |
| enable | Windowed watchdog, gating logic [TBD] | [TBD] | [design/enable.md](design/enable.md) |
| comms_debug | USB-UART bridge [TBD] | [TBD] | [design/comms_debug.md](design/comms_debug.md) |

## Mechanical and other

| Parameter | Value |
|---|---|
| Board size | [TBD] |
| Layer count | [TBD] |
| Input / output connectors | J1 and J301: Kefa KF635-6.35-2P 2-pin screw terminals (32 A, 10 AWG). Identical parts, so they go on opposite board edges with clear silkscreen |
| Cooling | Natural convection through copper pours (no heatsink planned at 150 W) |
| Debug and comms | JTAG header, USB-UART |

## Test equipment required

The power target must fit inside what the lab can test. Confirm these before committing to 150 W.

| Equipment | Requirement | Available? |
|---|---|---|
| Bench supply | ≥ 51 V at ≥ 4 A, with adjustable current limit and, ideally, overvoltage protection (set ≈ 55 V). Floating output (no earth strap) | [TBD] |
| Electronic load | ≥ 12.5 A at 12 V, 150 W continuous | [TBD] |
| Oscilloscope | Bandwidth and probes suitable for GaN switch-node edges | [TBD] |
