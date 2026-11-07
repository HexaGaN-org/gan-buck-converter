# HexaGaN 48 V → 12 V GaN Synchronous Buck

A GaN-based synchronous buck converter with an onboard C2000 microcontroller, digital control and layered protections. HexaGaN's first in-house power PCB, built as a learning platform for the team and a rehearsal for the universal control board's power-stage interface.

> **Status (November 2026): schematic capture.** Circuitry on all six sheets is captured, and every sheet symbol on the root sheet has its pins. Remaining before layout: wiring the root sheet (no wires are drawn yet), the indicator-LED changes (PR #7), annotating each sheet into its own range, ERC on every sheet, and each design note's open questions. Layout has not started.

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
| Protections | Cycle-by-cycle overcurrent (CMPSS), output overvoltage, input undervoltage lockout, overtemperature, a hardware enable that firmware cannot override, and a hardware shoot-through interlock on the PWM gating |
| Host interface | USB-C serial (CP2102N USB-UART bridge, ESD-protected) and a TI-compatible JTAG header |
| Assembly | JLCPCB Economic PCBA, single-sided |

Targets are in [docs/specifications.md](docs/specifications.md); each sheet's decisions and parts are in its design note in [docs/design/](docs/design/).

## Schematic sheets and owners

| # | Sheet | Owner | Status |
|---|---|---|---|
| 1 | Top (root sheet) | Reza Rahimzadeh | Sheet pins synced on all six sheet symbols; wiring pending |
| 2 | input_supply | Reza Rahimzadeh | Schematic complete: 48 V protection, input shunt, aux regulator, 5 V mux and 3.3 V LDO. Root-sheet pins added |
| 3 | power_stage | Reza Rahimzadeh | Captured; root-sheet pins added |
| 4 | sensing | Connor Jin | Circuitry captured (six channels); labels aligned with the MCU sheet; root-sheet pins added |
| 5 | mcu | Yunxi He | Captured, with 16 MHz external crystal; all interface labels on the root sheet |
| 6 | enable | Connor Jin | Captured: watchdog, enable switch, `STAGE_EN` gating and the shoot-through interlock. Root-sheet pins added |
| 7 | comms_debug | Yunxi He | Captured: USB-C with CP2102N bridge and USBLC6 ESD protection, JTAG header. Root-sheet pins added |

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
  datasheets/                Datasheets and reference images for key parts (MCU, crystal, JTAG pinout)
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
- Bring up the 5 V supply (through J202, the keyed external 5 V input, set to 5.0 V) before applying 48 V. J202 cuts off above about 5.2–5.7 V.
- Check polarity before connecting any electronic load or source. J201 (48 V in) and J301 (12 V out) are identical screw terminals: 48 V on J301 destroys the output capacitors.
- Keep the 48 V supply's output floating (no earth strap), and set its overvoltage protection at about 55 V if it has one. Above about 57 V the input TVS conducts continuously.
- The power stage stays disabled until the hardware enable is asserted. Firmware alone cannot enable it.
