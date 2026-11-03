# JLCPCB Design Rules and Assembly Workflow

How HexaGaN boards are designed, prepared and ordered for fabrication and assembly at JLCPCB. Applies to every board in this repo. JLCPCB's limits and prices change, so re-check the linked capability pages before each order and update this file if anything moved.

> Figures checked November 2026. **JLC limit** is the most JLCPCB can do. **House rule** is what we design to, with margin, so boards are cheap, reliable and reworkable by hand.

---

## 1. Choose the assembly service first

JLCPCB offers two assembly services. The choice limits which parts and layouts you can use, so make it before layout starts.

| | Economic PCBA | Standard PCBA |
|---|---|---|
| Assembly sides | One side only | One or both sides |
| Layers / thickness | 2, 4, 6 layers; 0.8–1.6 mm, standard stackups | 1–32 layers, any thickness and stackup |
| Smallest passive | 0402 | 01005 |
| Finest IC lead pitch | 0.4 mm | 0.35 mm |
| Finest BGA pitch | 0.5 mm | 0.3 mm |
| Edge rails and fiducials | Not needed | Required; boards under 70 × 70 mm must be panelized or railed |
| Quantity | 2–50 boards | 2–80,000 boards |
| Build time | 1–3 days | 4+ days |
| Setup fee | $8.18 | $25.56 (one side), $51.12 (two sides) |
| Loading fee per unique part | Basic and Preferred Extended free; other Extended $3.07 each | $1.53 each, Basic or Extended |

**House rule: design for Economic PCBA** — single-sided SMT, 0402 or larger, 2 or 4 layers, 1.6 mm, standard stackup. Move to Standard only when a part forces it, and record why in `specifications.md`.

**Open decision for the buck converter:** the LMG1205 gate driver is a 12-ball DSBGA. Check its ball pitch in the datasheet. If it is under 0.5 mm, Economic cannot place it, so either choose Standard PCBA (with rails, fiducials and the higher setup fee) or choose a GaN gate driver in a leaded or QFN package.

---

## 2. Board fabrication rules

Load the house rules into KiCad (**Board Setup → Design Rules → Constraints**, and the pre-defined track and via sizes) before routing, so DRC enforces them.

| Rule | JLC limit | House rule |
|---|---|---|
| Trace width / spacing, 2 layers | 0.127 mm / 0.127 mm | 0.15 mm / 0.15 mm |
| Trace width / spacing, 4–6 layers | 0.09 mm / 0.09 mm | 0.127 mm / 0.127 mm |
| Via drill / pad, 2 layers | 0.3 mm / 0.5 mm | 0.3 mm / 0.6 mm |
| Via drill / pad, 4+ layers | 0.2 mm / 0.45 mm | 0.3 mm / 0.6 mm |
| Annular ring, 1 oz copper | 0.13 mm | 0.15 mm |
| Annular ring, 2 oz copper | 0.2 mm | 0.2 mm |
| Copper to board edge | 0.2 mm | 0.3 mm |
| Hole to hole, different nets | 0.5 mm | 0.5 mm |
| Solder mask bridge | 0.2 mm (green), 0.254 mm (other colours) | Green mask; 0.2 mm |
| Silkscreen line width / text height | 0.153 mm / 1.0 mm | 0.15 mm / 1.0 mm |

**Copper weight.** Outer layers can be 1 oz or 2 oz. Inner layers are **0.5 oz** unless you choose JLCPCB's specific 4-layer 2 oz stackup, so never count on inner layers to carry high current. On a power board, carry current on the outer layers and use the inner layers for ground and signal. 2 oz outer copper helps current capacity but raises the minimum annular ring and makes fine-pitch pads harder to etch, so check it against the smallest-pitch part first.

**Surface finish.** Use **ENIG**. It gives flat pads, which matters for QFN, LGA and BGA parts such as GaN FETs and chip-scale drivers. HASL is cheaper but less flat.

**Stackup.** Use one of JLCPCB's standard stackups and record its name in `specifications.md`. If a trace needs controlled impedance, use JLCPCB's impedance calculator with that stackup.

---

## 3. Part selection rules

- **Every assembled part gets an LCSC part number** in a symbol field named `LCSC`, added when the part goes into the schematic, not just before ordering.
- **Prefer parts in this order:** Basic → Preferred Extended → Extended → Global Sourcing. Basic and Preferred Extended parts are free to load on Economic; each other unique Extended part costs a loading fee.
- **Consolidate values.** Use the same part number for all decoupling capacitors, pull-ups and LED resistors where the value isn't critical. Leave calculated values (dividers, sense resistors, timing parts) alone.
- **Passive size:** 0603 by default for hand rework and probing; 0402 only where space demands it. Never below 0402 (Economic's limit).
- **Check stock before freezing the BOM.** A part out of stock at JLCPCB must be bought through Global Sourcing, which can impose large minimum order quantities and delays the build until parts arrive.
- **Avoid through-hole parts** except where a connector truly needs one. Through-hole parts are hand-soldered and charged per joint plus a labour fee per order.
- **Parts JLCPCB should not place** (DNP parts, parts we will hand-solder, test points) get *Exclude from BOM* and *Exclude from position files* set in their footprint attributes.

---

## 4. Layout rules for assembly

- **Use footprints from the project library** whose origin and pin 1 follow the standard (KiCad library / IPC-7351) convention. Placement errors almost always come from footprints with unusual origins or rotations.
- **Mark pin 1 and polarity** in silkscreen on every IC, diode, LED and polarized capacitor, and keep reference designators readable.
- **Keep parts at least 1 mm from the board edge** (house rule), more if the board will be panelized with mouse bites.
- **Keep all assembled parts on the top side**, unless the service decision in section 1 says otherwise.
- **Leave room around fine-pitch and bottom-terminated parts** (QFN, LGA, BGA) for rework with hot air: about 1–2 mm clear of tall neighbours.
- **Fiducials:** Economic does not need them, and JLCPCB adds its own. Standard PCBA requires them and edge rails; add them in JLCPCB's order options or in the layout.

---

## 5. Workflow

### Before layout
1. Make the assembly-service decision (section 1) and record it in `specifications.md`.
2. Load the house rules into KiCad's Board Setup (section 2) and choose the stackup.
3. Install the **KiCad JLCPCB Tools** plugin (Bouni): in the Plugin and Content Manager, add the repository `https://raw.githubusercontent.com/Bouni/bouni-kicad-repository/main/repository.json`, then install it. It supports KiCad 7 through 10.

### During schematic and layout
4. Assign LCSC numbers as parts are placed, using the plugin's part search or the LCSC website.
5. Keep ERC and DRC clean as you go, not just at the end.

### Before ordering
6. Run ERC and DRC: zero errors, and every warning understood.
7. Generate the production files with the plugin: a Gerber/drill zip, `BOM-<project>.csv` and `CPL-<project>.csv`.
8. Open the Gerbers in KiCad's Gerber viewer and check every layer, especially the board outline, drills and solder paste.
9. Complete the pre-order checklist (section 6), with a second person reviewing.

### Ordering
10. Upload the Gerber zip. Set layers, thickness, copper weight, **ENIG** finish and the board colour, matching section 2.
11. Enable PCB Assembly, choose Economic or Standard (section 1), select the top side, and choose how many boards to assemble. Assembling fewer than you order (for example 5 of 10) leaves bare boards for rework experiments.
12. Upload the BOM and CPL. Confirm every part matched, and check stock.
13. **Inspect the placement preview part by part.** Confirm pin 1, diode and capacitor polarity, and the orientation of every IC, connector and FET. Fix rotations in the plugin's rotation manager and regenerate rather than correcting them only on the website, so the fix is kept for next time.
14. Place the order and watch for JLCPCB's DFM and engineering questions. Answer them the same day, since the order waits until you do.

### After ordering
15. Tag the exact commit that was ordered (for example `buck-rev0.1-fab`) and create a GitHub Release with the Gerber zip, BOM, CPL and a schematic PDF attached. Record the JLCPCB order number in the release notes.
16. When boards arrive, inspect them before applying power: the orientation of every polarized part, solder bridges on fine-pitch parts, and shorts between each supply rail and ground. Then follow the bring-up procedure in the README.

---

## 6. Pre-order checklist

- [ ] Assembly service chosen and recorded; every part is within its limits (package size, pitch, BGA pitch)
- [ ] ERC and DRC clean against the house rules
- [ ] Every assembled part has an LCSC number and is in stock (or Global Sourcing accepted, with lead time noted)
- [ ] Non-assembled parts excluded from the BOM and position files
- [ ] Gerbers reviewed layer by layer, including the outline and drills
- [ ] Board options match the specification: layers, thickness, copper weight, ENIG, stackup
- [ ] Placement preview checked part by part for rotation and polarity
- [ ] Pin 1 and polarity marked in silkscreen
- [ ] Second person reviewed the order before submission
- [ ] Commit tagged and Release created with the production files

---

## References

- [JLCPCB PCB manufacturing capabilities](https://api.jlcpcb.com/capabilities/Capabilities)
- [JLCPCB PCB assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
- [What the JLCPCB assembly price includes](https://jlcpcb.com/help/article/40-pcb-assembly-price)
- [JLCPCB: reducing prototype assembly cost](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- [JLCPCB PCB assembly FAQs](https://jlcpcb.com/help/article/98-pcb-assembly-faqs)
- [KiCad JLCPCB Tools plugin](https://github.com/Bouni/kicad-jlcpcb-tools)
