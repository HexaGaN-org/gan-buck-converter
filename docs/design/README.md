# Design Notes

One note per schematic sheet, recording why the sheet looks the way it does: decisions, calculations, part choices, values other sheets depend on, layout needs and verification.

| Sheet | Design note |
|---|---|
| Input and Supply | [input_supply.md](input_supply.md) |
| Power Stage | [power_stage.md](power_stage.md) |
| Sensing | [sensing.md](sensing.md) |
| MCU | [mcu.md](mcu.md) |
| Enable | [enable.md](enable.md) |
| Comms and Debug | [comms_debug.md](comms_debug.md) |

## How to use

- Each sheet's owner maintains its note.
- Update the note in the **same pull request** as the schematic change it explains.
- Link datasheets rather than committing PDFs.
- Never delete a decision: mark it *Superseded* and add the new one.
- For a new board or sheet, start from [_template.md](_template.md).
