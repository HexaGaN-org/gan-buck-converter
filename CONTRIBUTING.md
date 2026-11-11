# Contributing

How we work on this board. Read it once before your first commit; the checklist at the end is what every sheet must pass before it merges.

## Setup

- **KiCad 10.0** for schematic and layout. Everyone uses the same major version.
- **JLCImport** plugin, to bring LCSC parts into the project library.
- **KiCad JLCPCB Tools** (Bouni), to generate the BOM and placement files. Install it from the Plugin and Content Manager; [guides/jlcpcb-assembly.md](docs/guides/jlcpcb-assembly.md) has the repository URL.
- **TI SysConfig** for the MCU pin-mux, and **Code Composer Studio + C2000Ware** for firmware.

## Everyday workflow

1. **Close KiCad, then pull** before you start. Pull again before you push.
2. Work only on your own sheet. Owners are listed in the [README](README.md).
3. Keep ERC clean as you go. A sheet is done when ERC shows zero errors and every warning is understood.
4. Commit library changes separately from schematic work. Commit a schematic together with any library files it now needs, so it opens for everyone else.

## Sheet ownership

- One owner per sheet. Only the owner edits it; changes from anyone else go through the owner.
- Every sheet has a reviewer, who is never its owner.
- When a sub-sheet adds or renames a hierarchical label, the top-sheet owner syncs the sheet pins and wires them.

## Schematic conventions

**Connections between sheets**
- Power nets use power symbols, which are global (see *Libraries and parts* below).
- Every other signal crosses sheets through **hierarchical labels** only. No global labels.
- Label direction is written from the sheet's own point of view: a signal leaving the sheet is an *output*.
- Signals that stay on one sheet (for example `SW_NODE`) use local labels.

**Net names**
- UPPER_SNAKE_CASE. Active-low signals end in `_N`.
- A net has the same name on every sheet it appears on, exactly as listed in the signal glossary in [docs/schematic-hierarchy.md](docs/schematic-hierarchy.md).

**Reference designators**
- Annotate with *"Use first free number after sheet number × 100"*, so each sheet owns a range (top sheet: H101…, input_supply: R201…, power_stage: R301…). Two people annotating in parallel never collide.
- Every reference ends in a number: `TP_SW1` works, while a bare `TP_SW` is flagged as unannotated.
- Connectors use the designators in the Connectors table of the hierarchy doc. The MCU is U1.
- Annotate only new parts on your own sheet. Never re-annotate the whole schematic.

**Other**
- Mark do-not-populate parts with the DNP attribute, not by deleting them, and also untick *in BOM* and *in position files*.
- Test points and other footprint-only parts are excluded from the BOM and position files.
- Every sheet's title block carries the board revision, sheet title, owner and date.

## Libraries and parts

Both project libraries use paths relative to `${KIPRJMOD}`, so the project opens identically on every machine:

- **`hexagan`** (`lib/`): parts drawn by hand, and the board's own power symbols. Place `V_IN` and `V_OUT` from here.
- **`JLCImport`** (project root): parts imported from LCSC. The plugin writes its project library here. After importing a part, check its pin types (passives, FETs, diodes, inductors and connectors are **Passive**) and set **Value** to the manufacturer part number.
- KiCad's standard `power` and `Device` libraries for `GND`, `+5V`, `+3V3` and the other standard rails, and for generic symbols.

Never rename a power symbol's value to make a new net: a typo silently creates a separate net. Don't place parts from personal libraries; teammates won't have them.

Fill in an `LCSC` field on every assembled part when you place it. Choose parts with [guides/preferred-parts.md](docs/guides/preferred-parts.md), and check them against [guides/jlcpcb-assembly.md](docs/guides/jlcpcb-assembly.md).

## Keeping the docs in step

- **The KiCad symbol fields are the record of what is on the board**: MPN, LCSC number and footprint. Every other document points at them rather than repeating them.
- Update your sheet's design note in `docs/design/` in the same commit as the schematic change it explains.
- If you change a sheet boundary or a signal that crosses sheets, update [docs/schematic-hierarchy.md](docs/schematic-hierarchy.md) in the same commit.
- The BOM workbook (`docs/gan-buck-converter-BOM.xlsx`) adds cost and notes. Refresh your sheet's tab from a KiCad BOM export whenever its parts change.

## Before merging a sheet

- [ ] ERC passes with zero errors, and every warning is understood
- [ ] Every hierarchical label matches the hierarchy doc, in name and direction
- [ ] Every U1 pin used matches `pinmux.syscfg`
- [ ] Every part comes from a project library or KiCad's standard libraries, with a footprint and an `LCSC` field
- [ ] DNP and footprint-only parts are excluded from the BOM and position files
- [ ] Title block updated (revision, owner, date)
- [ ] Design note and BOM tab updated
- [ ] Reviewed by the sheet's reviewer
