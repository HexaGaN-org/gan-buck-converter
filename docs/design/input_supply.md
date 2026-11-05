# Input and Supply — Design Notes

Sheet: `sheets/input_supply.kicad_sch`

**Owner:** Reza Rahimzadeh · **Reviewer:** [NAME] · **Last updated:** 2026-11-04

---

## Purpose and requirements

Protect the board from the 48 V input, and generate the low-voltage rails every other sheet runs on (`+5V`, `+3V3`, `+3V3A`), from either the 48 V bus or an external 5 V bench supply.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Input and supply** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- Accept the full input voltage range in the specifications: 40–51 V, 48 V nominal (decision #2).
- Carry the input current: 3.95 A at 150 W and 40 V, with parts sized for the 200 W headroom (5.3 A).
- Clamp input transients below the switch-node limit published by power_stage: **90 V** (the LM5113-Q1's HS rating), including ringing. Choose the TVS clamp voltage, the fuse rating and that limit together; GaN has essentially no avalanche capability, so the clamp must stop a transient before it gets there.
- Keep an ordinary hot-plug of the input below the TVS's breakdown voltage, so the TVS is reserved for real faults.
- Protect against reverse polarity on both J1 and J6.
- Supply about 150 mA on `+5V` (GaN driver bias, 3.3 V LDO, USB bridge, LEDs) from an aux regulator rated for at least 300 mA.
- Select between the external 5 V input (priority) and the aux regulator automatically, with reverse-current blocking, and ride through the switchover without resetting the MCU: size the `+5V` output capacitance for the mux's switchover time. If the MCU does reset, the enable sheet holds both gates off, so the failure is safe.
- Set the mux's priority threshold so a sagging or disconnected bench supply is detected cleanly.
- Rate J6 for at least 0.5 A, with a fuse or PTC.
- Provide `+3V3` for logic and a filtered `+3V3A` for the MCU's analog supply.
- Allow full low-voltage bring-up from J6 with no 48 V connected.

**Status (2026-11-04):** the 48 V front end (J1, fuse, TVS, reverse-polarity FET, damping capacitor) is designed. The aux regulator, power mux, J6 path, LDO and `+3V3A` filter are next.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-03 | 5 V source selection with a two-input power mux (TPS2121-class), external input J6 has priority | Schottky diode-OR; a jumper | The mux selects automatically with milliohms of drop and blocks reverse current, so the bench supply can never back-feed the 48 V bus. A Schottky OR drops 0.3–0.5 V, which can push the GaN driver's bias out of its 4.5–5.5 V range. Plugging in a bench supply is deliberate, so it wins; unplugging hands the rail back to the aux regulator | power_stage: `+5V` must stay within 4.5–5.5 V | Accepted |
| 2 | 2026-11-04 | Input voltage range **40 V min, 48 V typ, 51 V max** | 36–54 V (the simulation's assumption), which needs an SMBJ54A: 87.1 V clamp, 2.9 V below the 90 V limit; 40–54 V (same TVS problem) | 51 V is the highest maximum whose TVS (SMBJ51CA, 51 V standoff) clamps below 90 V on datasheet worst-case numbers alone: 82.4 V at rated $I_{PP}$, 7.6 V of margin. 40 V matches the common floor of 48 V systems; going lower raises the 200 W input current to 5.8 A for no benefit on a bench board. Below 40 V the board can still run at reduced load for bring-up, with the firmware UVLO overridden | specifications.md updated. Everything on `V_IN` must survive 82.4 V. power_stage input ceramics still pass at 40 V (calculation below). sensing: `VIN_SENSE` covers the range. Simulation updated, no change to the loop margins (feedforward) | Accepted |
| 3 | 2026-11-04 | J1: Kefa KF635-6.35-2P screw terminal (C475102), the same part as J301 | XT60 (polarized, but needs an adapter lead to the bench supply, the reason it was rejected for J301); 4 mm binding posts (two extra part numbers) | 32 A and 10 AWG against at most 5.3 A; bench leads land directly; no extra loading fee | Layout: J1 and J301 are identical terminals, and 48 V on J301 would destroy the 25 V output capacitors. Put them on opposite board edges with large `48 V IN` / `12 V OUT` silkscreen and the same polarity orientation | Accepted |
| 4 | 2026-11-04 | Front-end order: J1 → fuse F201 → TVS D201 across the input → reverse-polarity FET Q201 in the return → damping capacitor C201 → `V_IN` | TVS downstream of the reverse-polarity FET; fuse after the TVS | The fuse comes first so a TVS that fails short (their usual failure) opens it. The TVS sits at the point of entry so a surge is stopped before it reaches Q201 or the power stage; being bidirectional (#5), it ignores reversed leads | none | Accepted |
| 5 | 2026-11-04 | TVS: SMBJ51CA, **bidirectional**, 600 W (hongjiacheng, C41376101) | SMBJ51A unidirectional (Littelfuse C1973217); SMBJ54A (87.1 V clamp) | 51 V standoff = maximum input; 56.7 V minimum breakdown sits above the 54–56 V hot-plug peak; 82.4 V clamp at 7.3 A. Bidirectional so reversed leads (48 V < standoff) don't forward-bias it: a unidirectional part across J1 would conduct and cook behind a current-limited supply rather than blow the fuse. Preferred part, no loading fee | power_stage: worst-case `V_IN` transient 82.4 V | Accepted |
| 6 | 2026-11-04 | Reverse polarity: **low-side N-FET** Infineon BSC070N10NS3G (C501502) in the J1 return, drain to J1−, source to GND; gate from `V_IN` through R201 100 kΩ 1206, clamped to 12 V by zener D202 (BZT52C12) | High-side P-FET (best 100 V part at JLCPCB with a datasheet: Vishay SUM70101EL, 10.1 mΩ, D²PAK, $4.41); high-side N-FET with an ideal-diode controller (LM74700-Q1 / LM74800-Q1 are rated 65 V, below the 82.4 V clamp); series Schottky (≈ 2 W at 4 A) | Lowest loss (≈ 0.16 W at 3.95 A), $0.60, 5 × 6 mm, and its 100 V rating survives anything the TVS lets through, with no controller to protect. The cost is that board GND is no longer the supply's negative; acceptable because this is a standalone board on a floating bench supply. **Revisit for any design that shares ground with other boards** (signal grounds would carry return current in parallel with the FET) | Bench: keep the 48 V supply floating; measure at the board's `V_IN` / GND test points, not at J1 | Accepted |
| 7 | 2026-11-04 | Fuse F201: Littelfuse 0451007.MRL, 7 A, 125 V DC, fast-acting, 2410 (C99548) | 7 A 1206 fuses rated 32 V (below the clamp voltage); time-lag 2410 parts (I²t 100+ A²s, no need) | Voltage rating above the 82.4 V clamp. 56 % of rating at 150 W and 40 V. Melting I²t 10.3 A²s is 20× the hot-plug I²t, so plugging in won't age it. 50 A interrupting rating is fine behind a current-limited bench supply. It protects wiring and the supply from a hard short; it cannot save the GaN FETs, which fail in nanoseconds | none | Accepted |
| 8 | 2026-11-04 | Damping capacitor C201: JARSON FZ2A101M1313, 100 µF 100 V aluminum electrolytic, 320 mΩ ESR (C5260780), from `V_IN` to GND downstream of Q201 | No bulk capacitor; a polymer capacitor (ESR too low to damp anything) | Bench leads (≈ 1 µH) and the power stage's 10.4 µF of ceramics ring to ≈ 90 V on a 51 V hot-plug. ESR ≈ √(L/C) ≈ 0.31 Ω and 9.6× the ceramic capacitance damp it to ≈ 54 V, below the TVS's breakdown. It also lowers the input filter's output-impedance peak from 1.8 Ω to 0.27 Ω, far below the converter's 10 Ω input impedance | none | Accepted; ripple-current rating open (see open questions) |

---

## Calculations

One row per calculation. Note where each input came from (specification, datasheet, measurement) in Notes.

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| Input current, 150 W | $P_{out} / (\eta V_{in})$ | 3.95 A at 40 V · 3.29 A at 48 V · 3.10 A at 51 V | η ≈ 95 % (specifications) |
| Input current, 200 W | same | 5.26 A at 40 V · 4.39 A at 48 V | Rating case for F201, Q201, J1 and copper |
| TVS clamp margin | $V_{HS,max} - V_{C}$ | $90 - 82.4 = 7.6$ V | SMBJ51CA $V_C$ at $I_{PP}$ = 7.3 A (datasheet); LM5113-Q1 HS 90 V (power_stage). Trace inductance between D201 and the protected node spends this margin |
| TVS dynamic resistance (worst case) | $(V_C - V_{BR,max}) / I_{PP}$ | $(82.4 - 62.7) / 7.3 \approx 2.7\,\Omega$ | Clamp ≈ $V_{BR} + I R_{dyn}$: about 65 V at 1 A, 71 V at 3 A. A bench supply can't drive the rated current, so real clamps sit low on this slope |
| Input ceramics at 40 V (power_stage check) | $I_{out} D(1-D) / (f_{sw} \Delta V_{in})$ | $12.5 \cdot 0.21 / (300\,kHz \cdot 1\,V) \approx 8.7$ µF needed | D = 0.3. The bank is ≥ 10.4 µF effective at 40 V (less DC-bias loss than at 48 V), so power_stage decision #9 still holds |
| Q201 conduction loss | $I^2 R_{DS(on),hot}$ | $3.95^2 \cdot 10.5\,m\Omega \approx 0.16$ W (0.29 W at 5.3 A) | 7 mΩ max at 10 V (datasheet) × 1.5 assumed hot |
| Q201 gate-source voltage | zener clamp | ≈ 11–12 V from 15 V input up to the 82.4 V clamp | BZT52C12: 11.4–12.6 V at its 5 mA test current, a little lower at 0.3–0.4 mA. $R_{DS(on)}$ is specified at 10 V; FET limit ±20 V |
| Q201 turn-on time constant | $R_{201} C_{iss}$ | $100\,k\Omega \cdot 3\,nF \approx 0.3$ ms | The body diode carries the current meanwhile; the converter isn't switching yet (UVLO) |
| R201 voltage and power | $(V_{IN} - V_Z)$; $(V_{IN} - V_Z)^2 / R$ | 39 V, 15 mW at 51 V; 70 V, 50 mW at the 82.4 V clamp | 1206 rated 200 V / 250 mW. An 0603 (≈ 75 V working voltage) is too close |
| D202 current | $(V_{IN} - V_Z) / R_{201}$ | 0.28 mA at 40 V, 0.39 mA at 51 V | |
| Fuse loading | $I_{in} / I_{rated}$ | 56 % at 150 W, 40 V; 76 % at 200 W, 40 V | Littelfuse suggests ≤ 75 % continuous at 25 °C |
| Hot-plug characteristic impedance | $Z_0 = \sqrt{L_{lead} / C_{cer}}$ | $\sqrt{1\,\mu H / 10.4\,\mu F} \approx 0.31\,\Omega$ | Lead inductance ASSUMED. Damping target: C201 ESR ≈ $Z_0$ and $C_{201} \ge 4 C_{cer}$ |
| Hot-plug peak, 51 V | `simulations/input_hotplug_sim.py` | Ceramics only: 85 / 90 / 93 V. With C201: 56 / 54 / 54 V | Leads 0.5 / 1 / 2 µH, 50 mΩ round trip (ASSUMED, deliberately low). No TVS modeled |
| Hot-plug I²t | $\int i^2\,dt$ (simulation) | ≈ 0.5 A²s | Against 10.3 A²s melting I²t for F201: 20× margin |
| Input-filter stability (Middlebrook) | peak $\lvert Z_{out,filter} \rvert$ vs $V_{in}^2 / P_{in}$ | 0.27 Ω with C201 (1.8 Ω without) vs 10.1 Ω at 40 V, full load | Simulation |
| C201 ripple current | harmonic split of the pulsed input current (simulation) | 0.49 A rms at 48 V, 400 kHz; 0.75 A at 40 V, 300 kHz | Listed rating 0.5 A. Assumes 20 nH of can ESL plus trace to the power stage. See open questions |

---

## Part selection

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| J1 (J201 in the schematic, see open questions) | 48 V input connector | Kefa KF635-6.35-2P | C475102 | 2-pin screw terminal, 32 A, 10–22 AWG, M3, 6.35 mm pitch; through-hole, same part as J301 | [LCSC](https://www.lcsc.com/product-detail/C475102.html) |
| F201 | Input fuse | Littelfuse 0451007.MRL | C99548 | 7 A fast-acting, 125 V DC, 50 A interrupting, melting I²t 10.3 A²s, 2410 | [LCSC](https://www.lcsc.com/product-detail/C99548.html) |
| D201 | Input TVS | hongjiacheng SMBJ51CA | C41376101 | Bidirectional 600 W; $V_{RWM}$ 51 V, $V_{BR}$ 56.7 V min, $V_C$ 82.4 V at 7.3 A; SMB; Preferred (no loading fee) | [LCSC](https://www.lcsc.com/product-detail/C41376101.html) |
| Q201 | Reverse-polarity FET | Infineon BSC070N10NS3G | C501502 | N-channel 100 V, 7 mΩ max at $V_{GS}$ = 10 V, 90 A, ±20 V gate, TDSON-8 5 × 6 mm. Pins 1–3 source, 4 gate, 5–8 and the exposed pad drain | [LCSC](https://www.lcsc.com/product-detail/C501502.html) |
| R201 | Q201 gate pull-up | UNI-ROYAL 1206W4F1003T5E | C17900 | 100 kΩ 1 %, 1206, 250 mW, 200 V; Basic. 1206 for voltage, not power | [LCSC](https://www.lcsc.com/product-detail/C17900.html) |
| D202 | Q201 gate clamp | hongjiacheng BZT52C12 | C19077410 | 12 V zener, 350 mW, SOD-123; Preferred | [LCSC](https://www.lcsc.com/product-detail/C19077410.html) |
| C201 | Hot-plug damping capacitor | JARSON FZ2A101M1313 | C5260780 | 100 µF ±20 % 100 V aluminum electrolytic, 320 mΩ ESR, 500 mA ripple, 5000 h at 105 °C, SMD 12.5 × 13.5 mm | [LCSC](https://www.lcsc.com/product-detail/C5260780.html) |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| `V_IN` operating range | 40–51 V (48 V nominal) | all sheets, firmware | UVLO thresholds still to be set (open questions) |
| `V_IN` worst-case transient | 82.4 V (TVS clamp at rated surge) | power_stage, sensing, this sheet | Every part on `V_IN` must survive it: 100 V-class ICs and capacitors, and 1206 (200 V) resistors, not 0603 (≈ 75 V). Applies to the `VIN_SENSE` divider on sensing |
| `V_IN` hot-plug peak | ≈ 54–56 V | power_stage | Simulated with C201 fitted; below the TVS's 56.7 V minimum breakdown |
| Board GND vs J1 negative | GND sits I × 10 mΩ (≈ 40 mV) above J1−, which is net `VIN_RTN` | sensing, firmware, bench | Measure `V_IN` against board GND, never against J1−. Never connect `VIN_RTN` to GND anywhere but through Q201 |
| Input current, full load | 3.95 A at 40 V (150 W); 5.3 A at 200 W | power_stage, layout | Copper and connector sizing |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- Put a test point on each mux input and on `+5V`.
- **D201 right at J1**, with short, wide connections to both terminals. Every nanohenry between them adds L·di/dt on top of the 82.4 V clamp and spends the 7.6 V margin.
- **`VIN_RTN` is its own copper.** It runs from J1− to D201 and Q201's drain pads only; it reaches GND only through Q201. A stray via or pour that touches GND bypasses the reverse-polarity protection.
- Route D202's anode straight to Q201's source pad, not into the general ground pour, so the zener clamps the FET's actual gate-source voltage.
- Q201's drain pads and exposed pad carry the full input current: pour copper on them for current and heat.
- J1 and J301 are identical terminals. Put them on **opposite board edges**, with large `48 V IN  + / −` and `12 V OUT  + / −` silkscreen, and give both the same polarity orientation.
- Place C201 between Q201 and the power stage, not inside the power loop. The trace inductance between C201 and the power-stage ceramics keeps switching ripple out of C201 (the ripple estimate assumes about 20 nH).
- Size `V_IN`, `VIN_RTN` and GND copper for 5.3 A (200 W at 40 V).

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Low-voltage bring-up | Current-limited 5 V bench supply on J6, no 48 V connected | MCU, firmware, sensing and enable logic all work | | |
| 2 | 48 V hand-over | Apply 48 V with J6 connected, then unplug J6 | `+5V` stays in regulation; the MCU does not reset | | |
| 3 | Hot-plug | Scope `V_IN` at C201 (single shot, 1 µs/div) while plugging 51 V in through the usual bench leads | Peak below 56.7 V (TVS stays off); compare with `input_hotplug_sim.py` and update its lead parameters | | |
| 4 | Reverse polarity | Reverse J1 at 48 V with the supply limited to 0.5 A, then correct it | Under 1 mA drawn while reversed; board works normally afterwards | | |
| 5 | Q201 enhancement | Measure $V_{GS}$ of Q201 at 40 and 51 V; measure J1− to GND at full load | $V_{GS}$ 11–12.6 V; drop below 60 mV at 3.95 A | | |
| 6 | C201 ripple heating | Thermocouple on C201 after 30 min at full load, 300 kHz and 40 V | Rise below 5 °C above the board; otherwise act on the open question | | |
| 7 | TVS idle in normal operation | Thermal camera on D201 at 51 V, full load | No heating | | |

---

## Open questions

- **J1 designator.** The Connectors table in schematic-hierarchy.md assigns `J1` to the 48 V input (and `J6` to the 5 V input), but the schematic uses `J201`. The table itself mixes conventions: `J1`, `J3`–`J6`, and the sheet-numbered `J301` for power_stage. Pick one convention and make the table and schematic agree in the same commit.
- **C201 ripple current.** C201 carries about 0.49 A rms at 48 V and 400 kHz, but about 0.75 A at 40 V and 300 kHz, against its 0.5 A listed rating (frequency of the rating not stated). Options: two 47 µF 100 V electrolytics in parallel (twice the ripple rating; similar total ESR keeps the damping), a part with a higher ripple rating whose ESR is still ≈ 0.3 Ω, or confirm on the bench (verification test 6) and accept. Any replacement must keep ESR near 0.3 Ω, or the damping is lost.
- **Input UVLO and OVLO.** Proposed: UVLO on at 38 V, off at 36 V (hysteresis); input overvoltage lockout at 53 V, between the 51 V maximum and the TVS's 56.7 V breakdown. Decide with sensing (`VIN_SENSE`) and firmware, then fill in specifications.md. The aux regulator's EN divider can provide a hardware UVLO as well.
- **Fuse at 200 W, 40 V** runs at 76 % of its rating. Fine for 150 W; choose 8 A if sustained 200 W runs at low input are planned.
- **Bench rules** (also in the README's safety section): keep the 48 V supply floating (no earth strap), and set its OVP at about 55 V. A supply set above about 57 V drives the TVS into continuous conduction.
- **Lead inductance and resistance** in the hot-plug simulation are assumptions; verification test 3 replaces them with a measurement.
- Next on this sheet: the aux regulator must survive the 82.4 V clamp, which rules out most 60–65 V buck regulators (look at the 100 V class, such as LM5164 / LM5163), then the mux, J6 path, LDO and `+3V3A` filter.
