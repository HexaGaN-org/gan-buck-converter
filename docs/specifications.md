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
| Cycle-by-cycle overcurrent | ≈ 22 A | Truncate the PWM pulse, every cycle | CMPSS3 high comparator on `I_OUT_SENSE` → ePWM trip zone (cycle-by-cycle). Above the 18.9 A worst-case peak (200 W, 300 kHz); with ≈ 2.4 A of trip lag and offset, peaks stay near 24.4 A, below L301's 31 A $I_{sat}$ |
| Output overvoltage | 13.2 V (+10 %) | Disable PWM, latch off | CMPSS1 on `V_OUT_SENSE` → ePWM trip zone (one-shot) |
| Input undervoltage lockout | [TBD] V on / [TBD] V off | Hold PWM off | ADC, in firmware. Proposed 38 V on / 36 V off ([design/input_supply.md](design/input_supply.md)) |
| Input overvoltage, fast | ≈ 55 V | Trip PWM within ≈ 1 µs, latch off | CMPSS4 on `V_IN_SENSE` → ePWM trip zone (one-shot). Decision #24 in [design/input_supply.md](design/input_supply.md) |
| Overtemperature | [TBD] °C | Disable PWM | RTDs + ADC, in firmware |
| Hardware enable | — | No switching without it | Hardware logic, independent of firmware |

Each comparator threshold is a DAC code referenced to VDDA (`+3V3`); the pins, comparators and codes are in [firmware/firmware-requirements.md](firmware/firmware-requirements.md) §5.3 and [design/mcu.md](design/mcu.md). The pin plan behind them was set on 2026-11-06; the mcu schematic still has `V_IN_SENSE` and `I_IN_SENSE` on their old pins until it is updated.

## Components

The headline parts per sheet. The exact part on the board (MPN, LCSC number, footprint) lives in the KiCad symbol fields; why each part was chosen lives in the sheet's design note.

| Sheet | Key parts | Status | Details |
|---|---|---|---|
| power_stage | 2 × Infineon IGC033S10S1 GaN FETs (100 V); TI LM5113-Q1 gate driver (90 V); 6.8 µH Sunltech SLB2212P6R8MTT inductor; 1 mΩ shunt in series with the inductor | Chosen | [design/power_stage.md](design/power_stage.md) |
| mcu | TI TMS320F280039C, 64-pin LQFP (PM) | Chosen. Confirm pin-mux and stock before schematic freeze | [design/mcu.md](design/mcu.md) |
| sensing | TI INA241A3 current-sense amplifiers on the output and input shunts; TLV9061 buffers on the voltage and temperature channels; two 1 kΩ platinum RTDs beside the GaN FETs | Captured | [design/sensing.md](design/sensing.md) |
| input_supply | SMBJ51CA bidirectional TVS; 7 A fuse; low-side reverse-polarity FET (Infineon BSC070N10NS3G); 100 µF damping electrolytic; TI LM5164 aux regulator (100 V, 1 A); TI TPS2121 power mux; JST XH J202; 1 mΩ input current-sense shunt; ST LDL1117S33R 3.3 V LDO | Chosen; schematic complete | [design/input_supply.md](design/input_supply.md) |
| enable | TI TPS3813K33 supervisor with window watchdog; SN74LVC2G08 AND gates and an SN74LVC1G00 NAND forming `STAGE_EN` and the shoot-through interlock; SW1 enable switch | Captured | [design/enable.md](design/enable.md) |
| comms_debug | Silicon Labs CP2102N USB-UART bridge; USBLC6-2SC6 ESD protection; USB-C receptacle (data only); 2 × 10 JTAG header | Captured | [design/comms_debug.md](design/comms_debug.md) |

## Mechanical and other

| Parameter | Value |
|---|---|
| Board size | [TBD] |
| Mounting | 4 × M3 holes (H101–H104 on the top sheet), 3.2 mm plated with a via-stitched pad tied to `GND`. Positions: [TBD] with the board outline. Use nylon standoffs: board `GND` is not the 48 V supply's negative ([design/input_supply.md](design/input_supply.md) decision #6) |
| Layer count | 4, standard 1.6 mm stackup with the thinner L1–L2 prepreg (proposed, [design/power_stage.md](design/power_stage.md) decision #19). Stackup name: [TBD], record it here once chosen |
| Input / output connectors | J201 and J301: Kefa KF635-6.35-2P 2-pin screw terminals (32 A, 10 AWG). Identical parts, so they go on opposite board edges with clear silkscreen |
| Cooling | Natural convection through copper pours (no heatsink planned at 150 W). The layout reserves a top-side heatsink zone over the GaN FETs, fitted only if bench testing calls for it (proposed, [design/power_stage.md](design/power_stage.md) decision #20) |
| Debug and comms | JTAG header, USB-UART |

## Test equipment required

The power target must fit inside what the lab can test. Confirm these before committing to 150 W.

| Equipment | Requirement | Available? |
|---|---|---|
| Bench supply | ≥ 51 V at ≥ 4 A, with adjustable current limit and, ideally, overvoltage protection (set ≈ 55 V). Floating output (no earth strap) | [TBD] |
| Electronic load | ≥ 12.5 A at 12 V, 150 W continuous | [TBD] |
| Oscilloscope | ≥ 1 GHz scope and passive probes, with a short-loop tip (MMCX adapter or spring clip, loop < 10 mm); the switch node rings near 300 MHz on Infineon's reference board (UG122052). High-side gate measurements need an optically isolated probe (Tektronix IsoVu or PMK FireFly), or are skipped | [TBD] |
