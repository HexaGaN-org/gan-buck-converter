# HexaGaN 48 V → 12 V GaN Synchronous Buck

A GaN-based synchronous buck converter with an onboard C2000 microcontroller, digital control and layered protections. HexaGaN's first in-house power PCB, built as a learning platform for the team and a rehearsal for the universal control board's power-stage interface.

> **Status:** Specification in progress. See [docs/specifications.md](docs/specifications.md).

## Overview

- **Conversion:** 48 V input → 12 V output, synchronous buck
- **Power stage:** GaN half-bridge with integrated gate driver
- **Controller:** TI TMS320F280039C, 64-pin LQFP (same device as the universal control board)
- **Control:** staged bring-up from open loop, to voltage mode, to average current mode
- **Protections:** cycle-by-cycle overcurrent (CMPSS), output overvoltage, input undervoltage lockout, overtemperature, and a hardware enable firmware cannot override

## Repository layout

```
docs/        Specifications, bring-up procedure, test results, design notes
hardware/    KiCad project (schematic and PCB) and project-local libraries
firmware/    C2000 firmware and SysConfig pin-mux (.syscfg)
```

## Tools

- KiCad 10.0 (schematic and layout). Everyone uses the same major version.
- TI SysConfig (pin-mux, defined before layout)
- Code Composer Studio + C2000Ware (firmware)

## KiCad libraries

All symbols, footprints and 3D models live in the KiCad project's own `lib/` folder and are registered as project-specific libraries with paths relative to `${KIPRJMOD}`, so the project opens identically on every machine. Place parts only from the project library; copy or import stock and vendor parts into it first.

## Safety

48 V is below the 60 V DC SELV limit, but a shorted output or a failed switch can still deliver large currents and burn hardware.

- Always bring up from a **current-limited bench supply**, starting at reduced input voltage with no load.
- Never connect an electronic load or source without checking polarity.
- The power stage stays disabled until the hardware enable is asserted. Firmware alone cannot enable it.

## Contributing

- Close KiCad before `git pull`, and pull before opening it.
- One owner per schematic sheet. Annotate only your own sheet.
- Commit library changes separately from schematic or layout work.
- Every change goes through a pull request with ERC (and later DRC) clean.

## Team

HexaGaN Power Circuits and Modules pod. Contact: [NAME / EMAIL]
