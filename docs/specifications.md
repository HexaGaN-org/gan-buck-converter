# Specifications — 48 V → 12 V GaN Synchronous Buck

The one-page target for the design. Fill in every `[TBD]` before schematic capture starts, and change a value only by updating this file in a pull request.

## Electrical

| Parameter | Min | Typ | Max | Unit | Notes |
|---|---|---|---|---|---|
| Input voltage | [TBD] | 48 | [TBD] | V | Max must stay below 60 V (SELV) |
| Output voltage | | 12 | | V | |
| Output current | | | [TBD] | A | |
| Output power | | | [TBD] | W | 100–200 W keeps thermals manageable |
| Switching frequency | | [TBD] | | kHz | |
| Output voltage ripple | | | [TBD] | mV p-p | |
| Load transient, 10 % → 90 % step | | | [TBD] | mV deviation | Settling time: [TBD] µs |
| Efficiency at full load | [TBD] | | | % | |
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
| MCU | [F280039C or F28002x] | [TBD] |
| GaN half-bridge | [part number] | [TBD] |
| Inductor | [part number, value, Isat] | [TBD] |
| Current sensing | [shunt + amplifier / other] | [TBD] |

## Mechanical and other

| Parameter | Value |
|---|---|
| Board size | [TBD] |
| Layer count | [TBD] |
| Input / output connectors | [TBD] |
| Cooling | [Natural convection / heatsink / fan] |
| Debug and comms | JTAG header, USB-UART |
