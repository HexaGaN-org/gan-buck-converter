# PCB Stackup

The KiCad model uses JLCPCB **JLC04161H-1080**, the nominal **1.6 mm** four-layer FR-4 option. The **0.0764 mm** gap from the top copper to the first inner ground plane keeps the GaN switching return close to the outgoing current path and reduces loop inductance. [JLCPCB stackups](https://jlcpcb.com/impedance) · [Power Stage decision #19](power_stage.md#decision-log) · [EPC WP010](../datasheets/epc-wp010-optimizing-pcb-layout.pdf)

## Layer assignments

| Layer, top to bottom | Thickness | Layout intent |
|---|---:|---|
| Front solder mask | 0.010 mm | KiCad model |
| L1 `F.Cu` | 0.035 mm | Component side. Route the GaN half-bridge, local input ceramic and gate-drive loops, and the short `SW_NODE` connection to L301 here. Use broad copper for the main power paths and `GND` fill where it can connect to the ground planes. Keep the `GNDA` pour local to the ADC reference and filters. |
| L1–L2 prepreg | 0.0764 mm | 1080 glass style |
| L2 `In1.Cu` | 0.0152 mm | Primary `GND` plane and reference for top-side signals. Keep the low-side source to input-capacitor return continuous directly under Q301, Q302 and C301–C307. Keep signal routing and plane splits out of this area. |
| L2–L3 core | 1.265 mm | FR-4 core |
| L3 `In2.Cu` | 0.0152 mm | Secondary `GND` plane and reference for bottom-side signals. Keep it continuous beneath those routes and stitch it to L2 with `GND` vias. |
| L3–L4 prepreg | 0.0764 mm | 1080 glass style |
| L4 `B.Cu` | 0.035 mm | Supplemental routing and bounded `V_IN`, `+5V` and `+3V3` pours. Use broad outer copper where power routing needs to change layers. Keep sensitive traces over L3 ground and clear of the switching area. |
| Back solder mask | 0.010 mm | KiCad model |

Copper and dielectric total **1.5182 mm**. KiCad shows **1.5382 mm** including solder mask on both faces. Outer copper is approximately **1 oz** and inner copper approximately **0.5 oz**. [Board specifications](../specifications.md#mechanical-and-other)

## Plane and routing rules

- Size the outer-layer copper for the main DC power and return paths, including the 12.5 A output path. Use multiple vias where heavy current changes layers. Keep `SW_NODE` copper compact and reserve the inner layers for ground return and reference. [Power Stage layout notes](power_stage.md#layout-notes)
- When a ground-referenced signal changes between outer layers, place a nearby `GND` stitching via to connect its two reference planes. Check that the routed signal stays over continuous ground on the adjacent inner layer.
- Route signals primarily on `F.Cu` and `B.Cu`. A short crossover on L3 is acceptable in a quiet area if its clearance slot stays clear of bottom-side signal return paths. Keep both inner ground layers continuous around the GaN stage.
- Use local top-side power pours where they give regulators or banks of supply pins a shorter feed. In the crowded U501 area, feed the `+3V3` decouplers from nearby vias to `B.Cu` and keep the cap-to-pin and cap-to-ground connections short. Preserve the local `GNDA` return paths.
- Join local `GNDA` to board `GND` at NT501. Maintain copper clearance around the plated H101–H104 mounting holes on all layers to keep the hardware isolated from board `GND`. [MCU design notes](mcu.md) · [Input and Supply layout notes](input_supply.md#layout-notes)

## KiCad and fabrication checks

As of the latest 2026-11-26 checkpoint, the board has top-side `GND`, `GNDA` and local power pours, including `+3V3`, with power distribution on `B.Cu`. `In2.Cu` has a `GND` pour. Add the planned `In1.Cu` `GND` pour before reviewing the switching return. [Current PCB](../../hardware/gan-buck-converter/gan-buck-converter.kicad_pcb)

After adding the L2 zone, refill the zones and inspect each inner layer on its own. Check that via and pad clearances leave a continuous path from the low-side source to the input-capacitor grounds and that ground remains continuous beneath signals. Run DRC after inspecting the fills. If 2 oz outer copper is selected for fabrication, confirm the supplier's dielectric thicknesses and update the KiCad stackup and fabrication rules for that option. Confirm finished thickness tolerance at ordering. [KiCad Physical Stackup](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#physical-stackup)
