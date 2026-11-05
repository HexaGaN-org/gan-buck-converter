# Input and Supply — Design Notes

Sheet: `sheets/input_supply.kicad_sch`

**Owner:** Reza Rahimzadeh · **Reviewer:** [NAME] · **Last updated:** 2026-11-05

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
- Rate J6 for at least 0.5 A. Overcurrent on the 5 V path is limited by the bench supply and the mux's current limit (decision #15).
- Provide `+3V3` for logic and a filtered `+3V3A` for the MCU's analog supply.
- Allow full low-voltage bring-up from J6 with no 48 V connected.

**Status (2026-11-05):** designed: the 48 V front end (J1, fuse, TVS, reverse-polarity FET, damping capacitor), the aux regulator, the power mux and the J6 path. Next: the 3.3 V LDO, the `+3V3A` filter, the power LED and the rail test points.

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
| 8 | 2026-11-04 | Damping capacitor C201: JARSON FZ2A101M1313, 100 µF 100 V aluminum electrolytic, 320 mΩ ESR (C5260780), from `V_IN` to GND downstream of Q201 | No bulk capacitor; a polymer capacitor (ESR too low to damp anything) | Bench leads (≈ 1 µH) and the power stage's 10.4 µF of ceramics ring to ≈ 90 V on a 51 V hot-plug. ESR ≈ √(L/C) ≈ 0.31 Ω and 9.6× the ceramic capacitance damp it to ≈ 54 V, below the TVS's breakdown. It also lowers the input filter's output-impedance peak from 1.8 Ω to 0.27 Ω, far below the converter's 10 Ω input impedance | none | Accepted; ripple current resolved by #9 |
| 9 | 2026-11-05 | Keep the single C201 (decision #8); judge its ripple current against its ambient-derated rating, not the 105 °C figure | Two 47 µF 100 V electrolytics in parallel (high-ESR parts are rated only 0.2 A each, which is worse); two low-ESR 47 µF parts (AISHI C3038651) plus a 0.20 Ω metal-strip damping resistor (Vishay WSL2512R2000FEA, C844905): works, 3 parts; a single larger-can 100 µF (Ymin VKME1452A101MV, C487440, 1.04 A) | An electrolytic's ripple rating is set at its maximum temperature (105 °C) to cap core temperature; at a 25–45 °C bench ambient the allowed ripple is typically 1.7–2× higher. The 0.75 A worst case is a sweep corner (40 V, 300 kHz, full load); at 48 V and 400 kHz it is 0.49 A, inside even the 105 °C rating. Moving C201 farther from the power stage barely helps (20 → 80 nH: 0.75 → 0.71 A), because ESR, not inductance, sets the split | none | Accepted; confirm with the datasheet's multiplier table and verification test 6. Fallback: Ymin C487440 |
| 10 | 2026-11-05 | Aux regulator U201: TI LM5164DDAR (C477928), 100 V 1 A synchronous buck, constant on-time | LM5163 (0.5 A, same family, $2.28; datasheet not checked); LM5017 / LM5018 (older 100 V parts); SCT2A10A (100 V, $2.89); SY8511 and other non-synchronous parts (need a catch diode); 60–80 V parts (below the 82.4 V clamp) | VIN absolute maximum 100 V, 17.6 V above the TVS clamp; 6–100 V operating, so it also starts during reduced-voltage bring-up; synchronous, internally compensated and with an internal VCC regulator, so few parts; 1 A against a ≈ 150 mA load | none | Accepted |
| 11 | 2026-11-05 | U201 configuration: ≈ 620 kHz (R202 20 kΩ), Type-3 ripple injection (R203 / C205 / C206), EN/UVLO tied to `V_IN`, PGOOD unused, output on local net `+5V_AUX` | 750 kHz with 16.9 kΩ (Extended part); Type-1 ripple (1 resistor, but ≈ 80 mV on the GaN driver's supply); an EN divider for a 38 V hardware UVLO (2 parts) | 620 kHz sits above the power stage's 300–500 kHz band and keeps 97 ns on-time at the 82.4 V clamp (50 ns minimum). Type 3 keeps output ripple ≈ 2 mV on the rail that drives the low-side GaN gate directly. Tying EN to `V_IN` costs nothing; input UVLO stays with firmware. `+5V_AUX` must be a local label, not the `+5V` power symbol, or the bench supply on J6 back-feeds the regulator and charges `V_IN` through its high-side body diode | firmware: owns input UVLO (open questions) | Accepted |
| 12 | 2026-11-05 | Power mux U202: TI TPS2121RUXR (C485916) | TPS2116DRLR (C3235557, $0.39, 1.6–5.5 V, no overvoltage cutoff) | `+5V` drives the GaN driver's VDD, which drives the low-side gate with no clamp (power_stage #5). The TPS2121 survives 22 V on its inputs, and OV1 cuts J6 off before `+5V` exceeds the gate's limit; a bench supply set to 12 V by mistake destroys a TPS2116 and passes through. 56 mΩ on-resistance: ≈ 10 mV at 150 mA | power_stage: `+5V` protected against J6 overvoltage | Accepted |
| 13 | 2026-11-05 | Mux configuration: XCOMP fast switchover (≈ 5 µs). IN1 = `+5V_EXT`, IN2 = `+5V_AUX`. PR1 and OV1 share one divider from IN1 (75 k / 8.2 k / 20 k); CP2 from IN2 (30 k / 10 k); OV2 and ST to GND; ILM 100 kΩ; SS 100 nF | Plain priority mode (≈ 100 µs switchover, needs ≈ 100 µF effective on `+5V`, about six 22 µF parts); separate OV1 and PR1 dividers (one more resistor); ST driving the SOURCE LED (needs a 6–20 kΩ pull-up) | Fast switchover holds the dip to ≈ 55 mV with one 22 µF on `+5V`. Ratiometric switch point: J6 hands over below 0.915 × `+5V_AUX` (≈ 4.54–4.68 V). OV1 cuts J6 at 5.47 V nominal (5.21–5.68 V), between a 5.0 V bench setting and the GaN gate limit. Current limit ≈ 1.24 A. SOURCE LED powered from `+5V_EXT` instead (lights whenever J6 is live) | power_stage, mcu: `+5V` minimum ≈ 4.48 V during a hand-over | Accepted |
| 14 | 2026-11-05 | J6: JST B2B-XH-A(LF)(SN) 2-pin keyed header (C158012), with a dedicated banana-to-XH bench cable | 5.08 mm screw terminal (C8465); 2.54 mm pin header; barrel jack | A keyed wire-to-board connector physically can't take the 48 V bench leads; a screw terminal accepts any wire, and 48 V on J6 exceeds the TPS2121's 24 V absolute maximum. Keying also makes reversed polarity unlikely. 3 A rating; genuine JST, 600k in stock, $0.04 | Bench: build one J6 cable (XH housing and crimps to banana plugs) | Accepted |
| 15 | 2026-11-05 | J6 reverse polarity: high-side P-FET Q202 AO3401A (C15127, Basic), drain to J6+, source to `+5V_EXT`, gate to GND. No PTC on J6 | PTC (e.g. 500 mA 1206); Schottky diode (0.3–0.4 V drop, too much for the driver's 4.5 V minimum); the TPS2121's GND-pin diode scheme (protects only the mux) | 60 mΩ at 4.5 V, ≈ 9 mV drop; gate rated ±12 V, so no zener at 5 V. Overcurrent is already limited by the bench supply, the TPS2121's ≈ 1.24 A current limit and the 3 A connector; between J6 and the mux there is only Q202 and a short trace. Changes the requirement that J6 have a fuse or PTC | none | Accepted |
| 16 | 2026-11-05 | USB-C (J3, comms_debug) stays data only; J6 remains the 5 V bring-up input | USB VBUS as mux IN1 in place of J6 | Keeps comms_debug.md's requirement that USB never powers the board or back-powers the MCU. VBUS can sag to ≈ 4.75 V, tight against the driver's 4.5 V minimum, and a board fault would load the laptop's port | none | Accepted |

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
| C201 ripple current | harmonic split of the pulsed input current (simulation) | 0.49 A rms at 48 V, 400 kHz; 0.75 A at 40 V, 300 kHz | Listed rating 0.5 A at 105 °C; typically 1.7–2× higher at bench ambient (decision #9). Assumes 20 nH of can ESL plus trace to the power stage |
| **Aux regulator (U201, LM5164)** | | | Equations from the LM5164 datasheet (SNVSAU4D) |
| Output voltage | $1.2\,V (1 + R_{204}/R_{205})$ | $1.2 (1 + 470/150) = 4.96$ V | Type-3 ripple adds about half the FB ripple as offset (≈ 12 mV at FB, ≈ 50 mV at the output), so ≈ 5.0 V expected; confirm on the bench |
| Switching frequency | $2500\,V_{OUT} / R_{RON}$ (kHz, V, kΩ) | $2500 \cdot 4.96 / 20 \approx 620$ kHz | Eq. 1. Above the power stage's 300–500 kHz band |
| On-time | $R_{RON} / (2.5\,V_{IN})$ (µs, kΩ, V) | 200 ns at 40 V · 167 ns at 48 V · 97 ns at the 82.4 V clamp | Eq. 11. Minimum 50 ns; below 300 ns the minimum off-time is 250 ns |
| Highest input before frequency fold-back | $V_{OUT} / (t_{ON,min} F_{SW})$ | $4.96 / (50\,ns \cdot 620\,kHz) \approx 160$ V | Eq. 17 |
| Inductor ripple | $\frac{V_{OUT}}{F_{SW} L}(1 - V_{OUT}/V_{IN})$ | 0.153 A p-p at 48 V (0.19 A with L at −20 %) | Eq. 18. 47 µH; continuous conduction above ≈ 76 mA load |
| Peak inductor current | $I_{OUT} + \Delta I_L / 2$ | 0.38 A at a 0.3 A design load | L201 saturates at 2 A, above the 1.5 A current limit as the datasheet asks |
| Output capacitance | $\Delta I_L / (8 F_{SW} \Delta V_{OUT})$ | 1.2 µF needed for 25 mV; C207 gives 13.6 µF effective, ≈ 2 mV ripple | Eq. 21. C12891 keeps 62 % at 5 V |
| Input capacitance | $I_{OUT} D(1-D) / (F_{SW} \Delta V_{IN})$ | 0.09 µF needed for 0.5 V; 2 × 2.2 µF fitted (1.65 µF effective at 48 V) | Eq. 23; datasheet recommends ≥ 2.2 µF |
| Type-3 CA | $C_A \ge 10 / (F_{SW} (R_{FB1} \parallel R_{FB2}))$ | ≥ 142 pF; 1 nF fitted | Eq. 24 |
| Type-3 RA·CA | $R_A C_A \le t_{ON}(V_{IN} - V_{OUT}) / 20\,mV$ | ≤ 3.6 × 10⁻⁴ s; 300 kΩ × 1 nF = 3.0 × 10⁻⁴ s | Eq. 25. FB ripple 24 mV at 48 V, 23 mV at 40 V, 16 mV at 12 V (≥ 12 mV minimum) |
| Type-3 CB | $C_B \ge t_{settle} / (3 R_{FB1})$ | ≥ 53 pF for 75 µs; 100 pF C0G fitted | Eq. 26 |
| R203 (RA) voltage | $V_{SW} - V_{OUT}$ | up to ≈ 77 V at the clamp | 0805 (150 V); 0603 (75 V) is too close |
| **Power mux (U202, TPS2121)** | | | Equations and limits from the TPS2121 datasheet (SLVSEA3F); $V_{REF}$ 1.06 V typ (1.01–1.10 V) |
| J6 overvoltage cutoff (OV1) | $V_{REF}(R_{206}+R_{207}+R_{208}) / R_{208}$ | 5.47 V nominal, 5.21–5.68 V | Keep the bench supply at 5.0 V |
| Hand-over point (XCOMP) | switch when $k_1 V_{EXT} < k_2 V_{AUX}$; $k_1 = 28.2/103.2$, $k_2 = 10/40$ | $V_{EXT} < 0.915\,V_{AUX}$: 4.54 V at 4.96 V aux, up to 4.68 V with the 40 mV comparator offset | Ratiometric, so $V_{REF}$ tolerance cancels |
| Fast-mode condition | $V_{CP2} \ge V_{REF}$ | $0.25 \cdot 4.96 = 1.24$ V vs 1.10 V max | Holds while `+5V_AUX` > 4.4 V |
| J6 margin over aux | $V_{PR1} - V_{CP2}$ at 5.0 V each | 1.37 V vs 1.25 V (≈ 9 %) | |
| J6 valid with no 48 V | $V_{REF} / k_1$ | 3.88 V (3.70–4.03 V) | Plain priority mode when CP2 = 0 |
| Hand-over dip | $t_{FSW} I_{OUT} / C_{OUT}$ | $5\,\mu s \cdot 0.15\,A / 13.6\,\mu F \approx 55$ mV, so `+5V` ≥ ≈ 4.48 V | Datasheet eq. 3–4 |
| Current limit | $65.2 / R_{ILM}^{0.861}$ (A, kΩ) | 1.24 A at 100 kΩ; fast trip ≈ 2.4 × that | Eq. 2; 100 kΩ is the largest allowed value |
| Soft-start | Table 9-1 | 780 V/s with 100 nF; ≈ 16 mA inrush into ≈ 20 µF | |
| Divider currents | $V / R$ | 48 µA (PR1/OV1 chain), 124 µA (CP2) | |
| Q202 drop | $I \cdot R_{DS(on)}$ | $0.15\,A \cdot 60\,m\Omega \approx 9$ mV | AO3401A at 4.5 V drive |
| SOURCE LED current | $(V_{EXT} - V_F) / R_{212}$ | $(5 - 2.0) / 3.3\,k\Omega \approx 0.9$ mA | |

---

## Part selection

Refs U201 through C207 match the schematic; U202 onward are suggested until the mux and J6 are drawn.

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| J1 (J201 in the schematic, see open questions) | 48 V input connector | Kefa KF635-6.35-2P | C475102 | 2-pin screw terminal, 32 A, 10–22 AWG, M3, 6.35 mm pitch; through-hole, same part as J301 | [LCSC](https://www.lcsc.com/product-detail/C475102.html) |
| F201 | Input fuse | Littelfuse 0451007.MRL | C99548 | 7 A fast-acting, 125 V DC, 50 A interrupting, melting I²t 10.3 A²s, 2410 | [LCSC](https://www.lcsc.com/product-detail/C99548.html) |
| D201 | Input TVS | hongjiacheng SMBJ51CA | C41376101 | Bidirectional 600 W; $V_{RWM}$ 51 V, $V_{BR}$ 56.7 V min, $V_C$ 82.4 V at 7.3 A; SMB; Preferred (no loading fee) | [LCSC](https://www.lcsc.com/product-detail/C41376101.html) |
| Q201 | Reverse-polarity FET | Infineon BSC070N10NS3G | C501502 | N-channel 100 V, 7 mΩ max at $V_{GS}$ = 10 V, 90 A, ±20 V gate, TDSON-8 5 × 6 mm. Pins 1–3 source, 4 gate, 5–8 and the exposed pad drain | [LCSC](https://www.lcsc.com/product-detail/C501502.html) |
| R201 | Q201 gate pull-up | UNI-ROYAL 1206W4F1003T5E | C17900 | 100 kΩ 1 %, 1206, 250 mW, 200 V; Basic. 1206 for voltage, not power | [LCSC](https://www.lcsc.com/product-detail/C17900.html) |
| D202 | Q201 gate clamp | hongjiacheng BZT52C12 | C19077410 | 12 V zener, 350 mW, SOD-123; Preferred | [LCSC](https://www.lcsc.com/product-detail/C19077410.html) |
| C201 | Hot-plug damping capacitor | JARSON FZ2A101M1313 | C5260780 | 100 µF ±20 % 100 V aluminum electrolytic, 320 mΩ ESR, 500 mA ripple, 5000 h at 105 °C, SMD 12.5 × 13.5 mm | [LCSC](https://www.lcsc.com/product-detail/C5260780.html) |
| U201 | Aux regulator | TI LM5164DDAR | C477928 | 100 V (abs max) 1 A synchronous buck, COT, internal compensation and VCC; SO-8 PowerPAD; EP to GND | [TI](https://www.ti.com/product/LM5164) |
| L201 | Aux inductor | cjiang FNR8040S470MT | C168137 | 47 µH ±20 %, 2 A $I_{sat}$, 1.7 A rated, 177 mΩ, shielded 8 × 8 mm | [LCSC](https://www.lcsc.com/product-detail/C168137.html) |
| C202, C203 | U201 input | Samsung CL31B225KCHSNNE | C170101 | 2.2 µF 100 V X7R 1206; same part as the power-stage input bank | |
| C204 | U201 bootstrap | FH 0603B222K500NT | C1604 | 2.2 nF 50 V X7R 0603, Basic. Must be 2.2 nF: a larger value can damage the LM5164 | |
| R202 | U201 RON (frequency) | UNI-ROYAL 0603WAF2002T5E | C4184 | 20 kΩ 1 %, Basic | |
| R203 | Type-3 RA, SW to the RA/CA node | UNI-ROYAL 0805W8F3003T5E | C17616 | 300 kΩ 1 % **0805** (150 V), Preferred | |
| C205 | Type-3 CA, RA/CA node to `+5V_AUX` | Samsung CL10B102KB8NNNC | C1588 | 1 nF 50 V X7R 0603, Basic | |
| C206 | Type-3 CB, RA/CA node to FB | Samsung CL10C101JB8NNNC | C14858 | 100 pF 50 V **C0G** 0603, Basic | |
| R204, R205 | U201 feedback divider | UNI-ROYAL 0603WAF4703T5E; 0603WAF1503T5E | C23178; C22807 | 470 kΩ / 150 kΩ 1 %, Basic | |
| C207 | U201 output | Samsung CL31A226KAHNNNE | C12891 | 22 µF 25 V X5R 1206, Basic; 62 % kept at 5 V | |
| U202 | Power mux | TI TPS2121RUXR | C485916 | 2.8–22 V (24 V abs max), 56 mΩ, OV per input, 5 µs fast switchover, VQFN-HR-12 2 × 2.5 mm | [TI](https://www.ti.com/product/TPS2121) |
| J6 | 5 V bring-up input | JST B2B-XH-A(LF)(SN) | C158012 | 2-pin keyed XH header, 2.5 mm pitch, 3 A, through-hole | [LCSC](https://www.lcsc.com/product-detail/C158012.html) |
| Q202 | J6 reverse-polarity FET | AOS AO3401A | C15127 | P-channel 30 V, 60 mΩ at 4.5 V, ±12 V gate, SOT-23; Basic | |
| C208 | U202 IN1 (`+5V_EXT`) | Samsung CL31A226KAHNNNE | C12891 | 22 µF 25 V 1206; large input capacitance for a long bench cable, per the TPS2121 datasheet | |
| C209 | U202 OUT (`+5V`) | Samsung CL31A226KAHNNNE | C12891 | 22 µF 25 V 1206; 13.6 µF effective for the hand-over dip | |
| C210 | U202 SS | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF 50 V X7R 0603, Basic | |
| R206, R207, R208 | PR1 / OV1 chain from IN1 | UNI-ROYAL 0603WAF7502T5E; 0603WAF8201T5E; 0603WAF2002T5E | C23242; C25981; C4184 | 75 kΩ → PR1 → 8.2 kΩ → OV1 → 20 kΩ → GND, 1 %, Basic | |
| R209, R210 | CP2 divider from IN2 | UNI-ROYAL 0603WAF3002T5E; 0603WAF1002T5E | C22984; C25804 | 30 kΩ → CP2 → 10 kΩ → GND, 1 %, Basic | |
| R211 | U202 ILM | UNI-ROYAL 0603WAF1003T5E | C25803 | 100 kΩ 1 %, Basic | |
| D203, R212 | SOURCE LED on `+5V_EXT` | KENTO KT-0805Y; UNI-ROYAL 0603WAF3301T5E | C2296; C22978 | Yellow 0805 LED, 3.3 kΩ (≈ 0.9 mA); Basic | |

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
| `+5V` steady state | ≈ 5.0 V from `+5V_AUX` (4.96 V set point); bench voltage minus ≈ 20 mV from J6 | power_stage, mcu, comms_debug | GaN driver VDD 4.5–5.5 V |
| `+5V` minimum during a J6 → aux hand-over | ≈ 4.48 V for ≈ 5 µs | power_stage, mcu | About 20 mV below the driver's 4.5 V recommended minimum, for ≈ 5 µs, and above its UVLO. Raising `+5V_AUX` slightly or the hand-over point (R207) buys margin if the bench shows a problem. The 3.3 V LDO must regulate from 4.4 V |
| `+5V` overvoltage protection | J6 is cut off above 5.21–5.68 V | power_stage | `+5V_AUX` is regulated, so it has no cutoff (OV2 grounded) |
| `+5V` current limit | ≈ 1.24 A (TPS2121 ILM) | all `+5V` loads | Fast trip at ≈ 3 A |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- Put a test point on each mux input and on `+5V`.
- **U201 (LM5164):** C202/C203 tight against VIN (2) and GND (1); a short SW (8) trace to L201; R204, R205 and C206 right at FB (5); route the Type-3 network and FB away from SW except R203's own end; tie the exposed pad to GND copper.
- **U202 (TPS2121):** bypass capacitors (C208, C209) as close to IN1 and OUT as possible; wide traces for IN1, IN2 and OUT. Keep the dividers short to PR1, OV1 and CP2.
- J6 can sit anywhere convenient: being keyed, it can't be confused with J1 or J301.
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
| 8 | Aux regulator | `+5V_AUX` with no load and at 300 mA, at 12, 40 and 51 V; scope SW and FB | 4.9–5.1 V; steady switching near 620 kHz with no bursting; FB ripple 15–30 mV | | |
| 9 | Hand-over dip | Scope `+5V` (single shot, 2 µs/div) while unplugging J6 with 48 V applied, at full `+5V` load | Minimum above 4.4 V; MCU does not reset (with test 2) | | |
| 10 | J6 overvoltage cutoff | Raise J6 slowly from 5.0 V with 48 V off, then with 48 V on | J6 drops out between 5.2 and 5.7 V; `+5V` never exceeds 5.7 V (switches to aux when 48 V is on) | | |
| 11 | J6 reverse polarity | Reverse the J6 cable with the bench supply limited to 0.2 A | Under 1 mA drawn; board works normally afterwards | | |

---

## Open questions

- **J1 designator.** The Connectors table in schematic-hierarchy.md assigns `J1` to the 48 V input (and `J6` to the 5 V input), but the schematic uses `J201`. The table itself mixes conventions: `J1`, `J3`–`J6`, and the sheet-numbered `J301` for power_stage. Pick one convention and make the table and schematic agree in the same commit.
- **C201 ripple current** (decision #9). Read the JARSON datasheet's ripple multiplier tables (ambient temperature and frequency) and record the derated rating; it should support 0.75 A at 45 °C. Verification test 6 confirms on the bench. Fallback: Ymin VKME1452A101MV (C487440).
- **Input UVLO and OVLO.** Proposed: UVLO on at 38 V, off at 36 V (hysteresis); input overvoltage lockout at 53 V, between the 51 V maximum and the TVS's 56.7 V breakdown. Decide with sensing (`VIN_SENSE`) and firmware, then fill in specifications.md. U201's EN is tied to `V_IN` (decision #11), so input UVLO is firmware's job; a 2-resistor EN divider could add a hardware UVLO later.
- **Fuse at 200 W, 40 V** runs at 76 % of its rating. Fine for 150 W; choose 8 A if sustained 200 W runs at low input are planned.
- **Bench rules** (also in the README's safety section): keep the 48 V supply floating (no earth strap), and set its OVP at about 55 V. A supply set above about 57 V drives the TVS into continuous conduction.
- **Lead inductance and resistance** in the hot-plug simulation are assumptions; verification test 3 replaces them with a measurement.
- **J6 designator** follows whatever convention settles the J1 question above (`J6` per the table, or `J202` if the sheet numbering is kept).
- **`+5V_AUX` set point.** Confirm it lands near 5.0 V (test 8). If it sits low, the hand-over margin (≈ 4.48 V minimum) shrinks; R205 can be trimmed.
- **J6 cable**: build one XH-to-banana lead and label it 5 V.
- Next on this sheet: the 3.3 V LDO (must regulate from a 4.4 V input), the `+3V3A` filter, the power LED and rail test points.
