# HexaGaN 48 V → 12 V GaN Synchronous Buck

A GaN-based synchronous buck converter with an onboard C2000 microcontroller, digital control and layered protections. HexaGaN's first in-house power PCB, built as a learning platform for the team and a rehearsal for the universal control board's power-stage interface.

> **Status (November 2026): schematic capture.** MCU, input-supply, power-stage and sensing circuitry are captured. Full inter-sheet wiring, enable and comms/debug circuitry remain unfinished. Layout has not started.

![Block diagram](docs/gan-buck-converter-block-diagram.png)

## At a glance

| | |
|---|---|
| Conversion | 48 V in → 12 V out, synchronous buck |
| Output | 12.5 A, 150 W design target; parts and copper rated for 200 W |
| Switching frequency | 400 kHz nominal, adjustable 300–500 kHz in firmware |
| Power stage | 2 × Infineon IGC033S10S1 GaN FETs, TI LM5113-Q1 gate driver |
| Controller | TI TMS320F280039C, 64-pin LQFP (same device as the universal control board) |
| Control | Staged bring-up: open loop → voltage mode → average current mode |
| Protections | Cycle-by-cycle overcurrent (CMPSS), output overvoltage, input undervoltage lockout, overtemperature, and a hardware enable that firmware cannot override |
| Assembly | JLCPCB Economic PCBA, single-sided |

Targets are in [docs/specifications.md](docs/specifications.md); each sheet's decisions and parts are in its design note in [docs/design/](docs/design/).

## Schematic sheets and owners

| # | Sheet | Owner | Status |
|---|---|---|---|
| 1 | Top (root sheet) | Reza Rahimzadeh | Sheet symbols placed |
| 2 | input_supply | Reza Rahimzadeh | In progress: 48 V input protection, aux regulator and 5 V mux designed |
| 3 | power_stage | Reza Rahimzadeh | Captured; parent-sheet connections unfinished |
| 4 | sensing | Connor Jin | In progress: sensing circuitry captured; sheet interfaces unfinished |
| 5 | mcu | Yunxi He | Captured; source/destination interfaces unfinished |
| 6 | enable | Connor Jin | Not started |
| 7 | comms_debug | Yunxi He | Not started |

Only a sheet's owner edits it. What each sheet contains and every signal that crosses between sheets are defined in [docs/schematic-hierarchy.md](docs/schematic-hierarchy.md).

## Repository layout

```
CONTRIBUTING.md              How we work: workflow, conventions, libraries, merge checklist
docs/
  specifications.md          Targets, limits and headline parts
  schematic-hierarchy.md     The contract between sheets: contents, signals, connectors
  design/                    One design note per sheet: decisions, calculations, parts, layout, tests
  guides/
    preferred-parts.md       JLCPCB passives to pick first, with measured DC-bias derating
    jlcpcb-assembly.md       Fab and assembly rules, ordering workflow, pre-order checklist
  firmware/
    firmware-requirements.md         Plain-language firmware guide for the firmware team
    edge-ai-dead-time-optimizer.md   Proposal: on-board model that picks the lowest-loss dead time and frequency
  gan-buck-converter-BOM.xlsx  Cost and notes per sheet, refreshed from KiCad BOM exports
hardware/gan-buck-converter/
  gan-buck-converter.kicad_pro / .kicad_sch / .kicad_pcb   KiCad 10 project (root sheet and board)
  sheets/                    The six hierarchical sheets
  lib/                       hexagan library: hand-made symbols, footprints, 3D models
  JLCImport.*                Parts imported from LCSC by the JLCImport plugin
simulations/
  voltage_mode_sim.py        Python model of the voltage-mode control loop: Bode plots, load step
  input_hotplug_sim.py       Input hot-plug ringing and damping, bulk-capacitor ripple, input-filter stability
  README.md                  How to run it, how to read the plots, what we've learned
```

Firmware source (C2000, SysConfig) will live in `firmware/` once that work starts.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first commit: tool setup, the pull-and-push routine, schematic conventions, library rules and the checklist every sheet passes before it merges.

## Safety

48 V is below the 60 V DC SELV limit, but a shorted output or a failed switch can still deliver large currents and burn hardware.

- Always bring up from a **current-limited bench supply**, starting at reduced input voltage with no load.
- Bring up the 5 V supply (through J6, the keyed external 5 V input, set to 5.0 V) before applying 48 V. J6 cuts off above about 5.2–5.7 V.
- Check polarity before connecting any electronic load or source. J1 (48 V in) and J301 (12 V out) are identical screw terminals: 48 V on J301 destroys the output capacitors.
- Keep the 48 V supply's output floating (no earth strap), and set its overvoltage protection at about 55 V if it has one. Above about 57 V the input TVS conducts continuously.
- The power stage stays disabled until the hardware enable is asserted. Firmware alone cannot enable it.
