# HexaGaN 48 V → 12 V GaN Synchronous Buck

A GaN-based synchronous buck converter with an onboard C2000 microcontroller, digital control and layered protections. HexaGaN's first in-house power PCB, built as a learning platform for the team and a rehearsal for the universal control board's power-stage interface.

> **Status (November 2026): schematic capture.** The power stage schematic is complete and ERC-clean. The other five sheets are in progress. Layout has not started.

![Block diagram](docs/gan-buck-converter-block-diagram.png)

## At a glance

| | |
|---|---|
| Conversion | 48 V in → 12 V out, synchronous buck |
| Output | 12.5 A, 150 W design target; parts and copper rated for 200 W |
| Switching frequency | 400 kHz nominal, adjustable 300–500 kHz in firmware |
| Output ripple target | 50 mV p-p |
| GaN FETs | 2 × Infineon IGC033S10S1 (100 V, 3.3 mΩ max) |
| Gate driver | TI LM5113-Q1 half-bridge GaN driver (90 V, 5 V supply) |
| Output inductor | 6.8 µH, 31 A I<sub>sat</sub> (Sunltech SLB2212P6R8MTT) |
| Current sensing | 1 mΩ shunt in series with the inductor, for cycle-by-cycle limiting |
| Controller | TI TMS320F280039C, 64-pin LQFP (same device as the universal control board) |
| Control | Staged bring-up: open loop → voltage mode → average current mode |
| Protections | Cycle-by-cycle overcurrent (CMPSS), output overvoltage, input undervoltage lockout, overtemperature, and a hardware enable that firmware cannot override |
| Assembly | JLCPCB Economic PCBA, single-sided |

Full targets and every component decision are in [docs/specifications.md](docs/specifications.md).

## Schematic sheets and owners

| # | Sheet | Owner | Status |
|---|---|---|---|
| 1 | Top (root sheet) | Reza Rahimzadeh | Sheet symbols placed |
| 2 | input_supply | Reza Rahimzadeh | Not started |
| 3 | power_stage | Reza Rahimzadeh | Complete, ERC clean |
| 4 | sensing | Connor Jin | Not started |
| 5 | mcu | Yunxi He | Not started |
| 6 | enable | Connor Jin | Not started |
| 7 | comms_debug | Yunxi He | Not started |

Only a sheet's owner edits it. What each sheet contains and every signal that crosses between sheets are defined in [docs/schematic-hierarchy.md](docs/schematic-hierarchy.md).

## Repository layout

```
docs/
  specifications.md          Targets, protections, component decisions
  schematic-hierarchy.md     What each sheet holds, signal names, conventions, owners
  design/                    One design note per sheet: decisions, calculations, parts, layout, tests
  preferred-parts.md         JLCPCB passives to pick first, with measured DC-bias derating
  jlcpcb-assembly.md         Fab and assembly rules, ordering workflow, pre-order checklist
  firmware-requirements.md   Plain-language firmware guide for the firmware team
  edge-ai-dead-time-optimizer.md  Proposal: on-board neural network that picks the lowest-loss dead time and frequency
  gan-buck-converter-BOM.xlsx  Working BOM and cost, one tab per sheet
hardware/gan-buck-converter/
  gan-buck-converter.kicad_pro / .kicad_sch / .kicad_pcb   KiCad 10 project (root sheet and board)
  sheets/                    The six hierarchical sheets
  lib/                       hexagan library: hand-made symbols, footprints, 3D models
  JLCImport.*                Parts imported from LCSC by the JLCImport plugin
```

Firmware (C2000, SysConfig) will live in `firmware/` once that work starts.

## Tools

- **KiCad 10.0** for schematic and layout. Everyone uses the same major version.
- **JLCImport** plugin to bring LCSC parts into the project library, and **KiCad JLCPCB Tools** (Bouni) to generate the BOM and placement files.
- **TI SysConfig** for the MCU pin-mux, defined before layout.
- **Code Composer Studio + C2000Ware** for firmware.

## KiCad libraries

Both libraries are project-specific, with paths relative to `${KIPRJMOD}`, so the project opens identically on every machine:

- **`hexagan`** (`lib/`): parts drawn by hand, and the board's own power symbols. Place `V_IN` and `V_OUT` from here.
- **`JLCImport`** (project root): parts imported from LCSC. The plugin writes its "Project library" here. After importing, check the symbol's pin types (passives should be **Passive**) and set **Value** to the manufacturer part number.

Use KiCad's built-in `power` library for `GND`, `+5V`, `+3V3` and the other standard rails. Don't place parts from personal libraries. Fill in an `LCSC` field on every part when you place it.

## Workflow

1. **Close KiCad, then pull** before you start. Pull again before you push.
2. Work only on your own sheet. Annotate new parts with "first free number after sheet number × 100", so each sheet keeps its own range (power_stage uses 301, 302…).
3. Keep ERC clean as you go. A sheet is done when ERC shows zero errors and every warning is understood.
4. Update your sheet's design note in `docs/design/` and its BOM tab whenever a part or a decision changes.
5. Commit library changes separately from schematic work. Commit the schematic together with any library files it now needs, so it opens for everyone else.

## Safety

48 V is below the 60 V DC SELV limit, but a shorted output or a failed switch can still deliver large currents and burn hardware.

- Always bring up from a **current-limited bench supply**, starting at reduced input voltage with no load.
- Bring up the 5 V supply (through the external 5 V header) before applying 48 V.
- Check polarity before connecting any electronic load or source.
- The power stage stays disabled until the hardware enable is asserted. Firmware alone cannot enable it.

## Team

HexaGaN Power Circuits and Modules pod: Reza Rahimzadeh (lead), Connor Jin, Yunxi He.
