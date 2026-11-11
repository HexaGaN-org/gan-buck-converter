# Power Stage — Design Notes

Sheet: `sheets/power_stage.kicad_sch`

**Owner:** Reza Rahimzadeh · **Reviewer:** [NAME] · **Last updated:** 2026-11-11

---

## Purpose and requirements

Convert the 48 V bus to the 12 V output with a synchronous buck: two discrete enhancement-mode GaN FETs, a GaN half-bridge gate driver, the output inductor and capacitors, and the current-sense shunt.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Power stage** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- 48 V in, 12 V out at up to 12.5 A (150 W), with parts and copper rated for 16.7 A (200 W).
- Switch at 400 kHz nominal, with every part sized to run anywhere in 300–500 kHz.
- Meet the efficiency target in the specifications (about 95–96 % expected, roughly 6 W total loss at 150 W) with natural-convection cooling.
- Keep the GaN gate voltage within the FETs' limits under all conditions, including ringing.
- Support the shortest safe dead time, set in the MCU's ePWM.
- Meet the output ripple and load-transient targets in the specifications.
- Provide a Kelvin-connected current-sense shunt whose value lets sensing place the overcurrent threshold within 0–3 V.
- Hold both gates off when the driver is unpowered or `HS_PWM` / `LS_PWM` are undriven. The LM5113-Q1's HI / LI must not float; its datasheet specifies 100–300 kΩ internal input pull-downs. On this board the 10 kΩ pull-downs R21 / R22 on the enable sheet's `HS_PWM` / `LS_PWM` outputs provide a stronger default-low bias before `+3V3` powers U4 (see open questions and the [input-filter analysis](../reviews/2026-11-11-pwm-overlap-and-input-filter.md)).

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-03 | Discrete GaN FETs with a separate GaN half-bridge gate driver | Integrated GaN half-bridge with built-in driver (LMG2100 family) | Team decision | Gate-loop layout and gate-voltage limits become this sheet's responsibility | Accepted |
| 2 | 2026-11-03 | GaN FETs: Infineon IGC033S10S1, same part in both positions | EPC2306 (0 stock at JLCPCB), EPC2302 (9 in stock, larger die), EPC2308 (150 V, 51 in stock, no EasyEDA footprint), Infineon IGB070S10S1 (5 mΩ, 80 in stock), Innoscience 100 V parts (WLCSP / LGA) | In stock at JLCPCB and Economic-assemblable; 3.3 mΩ max keeps total FET loss near 1.7 W at full load; packaged 3 × 5 mm; one part number for both positions | input_supply: TVS clamp must stay well below the 100 V rating. Enable/mcu: none | Accepted |
| 3 | 2026-11-03 | Gate driver: TI LM5113-Q1 (WSON-10) | LMG1205 (DSBGA, Standard-PCBA only), LMG1210 (originally assessed as needing a 6–18 V supply; TI also permits a regulated 5 V ±5 % supply with VIN tied to VDD; still requires a circuit and footprint redesign) | Keeps the order on Economic PCBA; the bootstrap clamp is 5.2 V typical and 5.456 V maximum, close to the FET's 5.5 V recommended limit, so high-side gate overshoot must be measured; runs from `+5V`; split outputs; active part with JLCPCB stock | mcu: dead time must cover propagation mismatch and switching transitions. input_supply: about 10 mA more on `+5V` | Accepted; supply alternative and clamp margin clarified 2026-11-11 |
| 4 | 2026-11-03 | Switching frequency 400 kHz nominal; hardware valid across 300–500 kHz | 300 kHz (1.15 W frequency-dependent loss, larger passives), 500 kHz (1.91 W, high-side FET ~50 °C rise, 240 CPU cycles per period), 1 MHz (3.8 W, needs a heatsink) | Middle of the spec range: 1.54 W frequency-dependent loss, high-side FET ~42 °C rise, 300 CPU cycles per period. One 6.8 µH inductor keeps ripple and peak current acceptable across 300–500 kHz, so frequency becomes a firmware setting and the bench can measure efficiency vs frequency | mcu/firmware: HRPWM required; control ISR budget 300 cycles. Input and output capacitors sized for the 300 kHz worst case | Accepted |
| 5 | 2026-11-03 | Gate-drive passives per the LM5113-Q1 datasheet and TI's reference circuit (Figure 18): 100 nF bootstrap, 1 µF + 100 nF on VDD, external BAT46W + 100 Ω bootstrap path, 2 Ω on HOH, HOL direct, LOH and LOL tied, 1 kΩ + 22 pF input filters | 0 Ω turn-on (≈ 0.3 W less loss, ≈ 17 V/ns edges); no input filters (TI's reference fits 0 Ω and leaves the capacitors off) | Datasheet section 7.3.2 requires the external diode and 100 Ω. 2 Ω roughly halves turn-on dv/dt and ringing on a first board and can be tuned 0–4.7 Ω on the bench. Turn-off paths stay stiff so Miller current can't lift the gates. Filters reject glitches on PWM traces that cross the board | mcu/firmware: input filters add ≈ 6.5 ns to every dead time. input_supply: `+5V` must stay ≤ 5.5 V, because VDD drives the low-side gate directly | Accepted; VDD bulk value superseded by #16. The stated positive deadtime margin is only nominal and is superseded by the 2026-11-11 [corner analysis](../reviews/2026-11-11-pwm-overlap-and-input-filter.md) |
| 6 | 2026-11-03 | 10 kΩ gate-to-source footprints at each FET, DNP | Fitted 10 kΩ; no footprint (TI's reference) | Not required by the datasheet: when unpowered, the driver's output structures clamp the gates into the bootstrap and VDD capacitors. The footprint guards against assembly faults (an open gate resistor or driver joint) and can be fitted if the bench shows gate movement on a cold 48 V start | none | Superseded by #13 |
| 7 | 2026-11-03 | Output ripple target 50 mV p-p | 100 mV p-p (fewer capacitors) | About 0.4 % of 12 V; achievable with Basic ceramics at 300 kHz worst case | specifications updated | Accepted |
| 8 | 2026-11-03 | Output inductor: Sunltech SLB2212P6R8MTT, 6.8 µH (C2842794) | COILMX MTF1810-6R8M (4.7 mΩ, 19 A thermal, $1.59, 18 mm); Sumida CY1770 6.8 µH (22.5 A $I_{sat}$, 6.55 mΩ) | 31 A $I_{sat}$ vs 18.9 A peak; 2.1 mΩ gives 0.33 W at 12.5 A (0.4 W less than the MTF1810); 28.5 A thermal rating covers 16.7 A with margin | Layout: 22.5 × 22 mm footprint | Accepted |
| 9 | 2026-11-03 | Input ceramics: 2× 100 nF 0805 (C28233) + 6× Samsung 2.2 µF 1206 (C170101) + 2× Samsung 10 µF 1210 (C22380050); 10.4 µF effective at 48 V | YAGEO 2.2 µF 1206 (C577211) and PSA 10 µF 1210 (C5156756): no published DC-bias curves | Every part has a published Samsung DC-bias curve; 33 % margin over the 7.8 µF requirement at 48 V, and still passes at 60 V | input_supply: bulk electrolytics stay on that sheet | Superseded by #22 for the high-frequency pair; main bank unchanged |
| 10 | 2026-11-03 | Output capacitors: 8× Samsung 22 µF 25 V 1206 (C12891, Basic) + 1× 470 µF 25 V polymer (C46550466) | 6× C12891 (fails: only 26 % kept at 12 V); 5× 22 µF 1210 (C52306, 41 % kept, but an extra $3.07 loading fee) | 46 µF ceramic effective (≈ 39 µF at small ripple) vs 37 µF needed; polymer holds a 10 A step to ≈ 125 mV | sensing / firmware: loop crossover target ≈ 25 kHz assumed for the transient estimate | Accepted |
| 11 | 2026-11-03 | Current-sense shunt: 1 mΩ 3 W 2512 (C7420016), in series with the inductor between L301 and the output capacitors | Low-side source shunt (ground-referenced, but misses the high-side peak); input-side shunt | Sees the full inductor current, including the peak the cycle-by-cycle limit needs | sensing: amplifier must tolerate 12 V common mode (INA240-class); 12.5 mV at 12.5 A, 18.9 mV at peak | Accepted |
| 12 | 2026-11-03 | J301 output connector: Kefa KF635-6.35-2P screw terminal (C475102), plus switch-node RC snubber footprints (DNP) and test pads | XT60PW (needs adapter leads for the e-load); 5.08 mm terminals (24 A rating, 2.5 mm² wire) | 32 A, 10 AWG / 4 mm², M3 screws; connects straight to bench loads. Snubber values come from the measured ringing | input_supply: using the same terminal for J201 adds no loading fee | Accepted |
| 13 | 2026-11-03 | No gate-to-source pull-downs (supersedes #6) | DNP 10 kΩ footprints (#6) | Matches TI's reference design; the driver's output structures hold the gates when unpowered. Verification test 5 checks the cold start | none | Accepted |
| 14 | 2026-11-06 | Shunt Kelvin connections through net ties NT302 (L301 side → `I_SH_OUT_P`) and NT301 (`V_OUT` side → `I_SH_OUT_N`); hierarchical labels named `I_SH_OUT_P` / `I_SH_OUT_N` | Labels directly on R301's power wires | Same reasoning as input_supply #21: the ties make the sense pair two separate nets that meet the power copper only at R301's pads, and DRC enforces it. The `_OUT` names pair with the input shunt's `I_SH_IN_*` and match the sensing sheet | sensing: inputs already named `I_SH_OUT_P` / `I_SH_OUT_N`. schematic-hierarchy updated | Accepted |
| 15 | 2026-11-06 | `+5V` maximum stays 5.5 V in normal operation, with one accepted exception: a J202 bench supply mis-set above 5.5 V can reach the TPS2121's overvoltage cutoff (5.21–5.68 V), putting up to 5.68 V on the low-side gate | Requiring input_supply to guarantee ≤ 5.5 V (a cutoff that can trip on a correctly set 5.0 V supply) | See input_supply #23. The bench rule is 5.0 V on J202; the exceedance needs a mis-set supply and stays below the FET's ±6.5 V pulsed rating, though that rating isn't meant for continuous use | input_supply: none (cutoff unchanged) | Accepted |
| 16 | 2026-11-06 | VDD bulk capacitor C322: 10 µF 25 V X5R 0603 (Samsung CL10A106MA8NRNC, C96446) in place of 1 µF (C15849); supersedes the VDD value in #5. C321 (100 nF at the pins) unchanged | 2.2 µF or 4.7 µF 0603 (a new part number) | The calculation row requires $C_{VDD} \ge 10\,C_{BST}$ ≈ 1 µF; the 1 µF part kept only 0.66 µF at 5 V, so the pair gave ≈ 0.76 µF. C96446 is already on the board (input_supply C209), so no new part or loading fee, and 10 µF is the top of the datasheet's 220 nF–10 µF range | none | Accepted |
| 17 | 2026-11-06 | Input ceramics C303–C308 on the standard `C_1206_3216Metric` footprint instead of the HandSolder variant | Keep HandSolder pads (longer, easier to rework) | These sit in the power loop, where the longer pads add loop inductance for no benefit: JLCPCB places them by machine. C311–C318 and R301 stay on HandSolder pads for now (outside the loop) | Layout: power-loop placement unchanged | Accepted |
| 18 | 2026-11-06 | `12V` output LED LED301 (KT-0805G green, C2297) on `V_OUT` through R307 10 kΩ (C25804), per [indicator-leds.md](indicator-leds.md) | No output LED (the e-load shows the output) | Output state visible at J301 without the e-load; ≈ 0.9 mA, 8 mW. Its current flows through R301, so it shows up as ≈ 1 mA of load in `I_OUT_SENSE`, inside the zero calibration | none | Accepted |
| 19 | 2026-11-07 | Lay out the power loop as EPC's "optimal power loop" ([epc-gan-pcb-layout.pdf](epc-gan-pcb-layout.pdf), EPC WP010) on a **4-layer** board: input ceramics on the top layer beside Q301's drain, inner layer 1 a solid `GND` return directly under the loop, and interleaved `SW_NODE` / `GND` via rows between the FETs aligned with Q302's alternating drain / source bars. Use the standard 1.6 mm stackup with the thinnest L1–L2 prepreg on offer | Lateral loop (inner layer 1 as a shield); vertical loop (input caps on the bottom side, under the FETs); 2 layers | A vertical loop is impossible here: Economic PCBA is single-sided, and WP010 shows vertical-loop inductance rising about 80 % when the board goes from 31 to 62 mil (we are at 63 mil). The optimal loop measured about 65 % lower inductance than the best conventional layout and does not depend on board thickness, only on the L1–L2 distance. Infineon's evaluation board for this exact FET ([infineon-FET-reference-design.pdf](infineon-FET-reference-design.pdf), UG122052) is 4 layers with solid inner pours. On 2 layers the nearest return plane is 1.6 mm away, the worst case. Lower loop inductance is what keeps switch-node overshoot inside verification test 2 | specifications: layer count 4; stackup name recorded there once chosen | Proposed |
| 20 | 2026-11-07 | Rev A ships without a heatsink, but the layout reserves room for an optional top-side heatsink over Q301 / Q302 and adds thermal vias under the FET pads. Fit a heatsink (or a fan) only if verification test 3 says so | Heatsink fitted on rev A; no provision at all | Estimated rise at 150 W, 400 kHz, still air: high-side ≈ 55 K, low-side ≈ 32 K (calculation rows below), so roughly 80 °C at a 25 °C bench, well below the 150 °C $T_{j,max}$. The 200 W / 500 kHz corner approaches 100 °C, and the loss estimate itself is uncertain, so a fallback costs little to keep. Infineon's reference-board temperature plots used a heatsink and 5 m/s airflow; the datasheet also supplies a 2s2p still-air $R_{th(j\text{-}a)}$, but our layout and neighboring heat sources still require bench verification | specifications: cooling row | Proposed |
| 21 | 2026-11-11 | Correct `JLCImport:IGC033S10S1_C41381300` copper, mask, and paste artwork against the exact-part datasheet Figure 2; retain six pad numbers and use 15 paste apertures for the 0.13 mm reference stencil | Keep imported full-pad paste and identical copper/mask shapes | The imported land geometry and stencil differed from the vendor drawing. The [footprint correction record](../reviews/2026-11-11-igc033s10s1-footprint-correction.md) gives dimensions, validation, and the under-dimensioned copper-overhang caveat | Layout: use the corrected library footprint for both FETs; fabricator/assembler signoff still needed | Implemented; manufacturing review open |
| 22 | 2026-11-11 | Use four 100 nF, 100 V Samsung CL10B104KC8NNNC 0603 capacitors (C309, C310, C326, C327) directly at the FET power loop; add 1 mm probe pads TP_LSG1 and TP_LSS1 for Q302 gate-to-source measurement | Keep two 0805 C28233; use an MMCX jack for the gate measurement | The smaller pads permit shorter, parallel high-frequency current paths. The exact-part Samsung bias graph suggests about 42 % capacitance at 48 V, so four parts retain about 0.17 µF versus about 0.10 µF for the former pair. This is typical curve data, not a guaranteed minimum. Two exposed pads permit a short ground spring without a tall connector inside the optional heatsink zone | Layout: place all four caps beside Q301/Q302 even though two symbols are drawn separately; put both probe pads beside Q302 pins 1 and 6, with less than 10 mm probe-loop length. C15725 is JLC Extended, Economic-compatible | Implemented in schematic; physical placement and probe access pending |

---

## Calculations

One row per calculation. Note where each input came from (specification, datasheet, measurement) in Notes.

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| Duty cycle | $D = V_{out} / V_{in}$ | $12 / 48 = 0.25$ | Ideal; real duty is slightly higher to cover losses |
| High-side conduction loss | $I_{out}^2 \cdot R_{DS(on),hot} \cdot D$ | $12.5^2 \cdot 5\,m\Omega \cdot 0.25 \approx 0.20$ W | $R_{DS(on)}$ 3.3 mΩ max at 25 °C (datasheet) × ~1.5 assumed when hot; confirm the factor from the datasheet curve |
| Low-side conduction loss | $I_{out}^2 \cdot R_{DS(on),hot} \cdot (1-D)$ | $12.5^2 \cdot 5\,m\Omega \cdot 0.75 \approx 0.59$ W | Same assumptions |
| Output-charge loss | $\tfrac{1}{2} Q_{oss} V_{in} f_{sw}$ | $0.5 \cdot 43\,nC \cdot 48 \cdot 400\,kHz \approx 0.41$ W | $Q_{oss}$ 43 nC typ at 50 V (datasheet); $f_{sw}$ = 400 kHz planned |
| Dead-time conduction loss | $V_{SD} \cdot I_{out} \cdot 2 t_{dt} \cdot f_{sw}$ | $2.4 \cdot 12.5 \cdot 20\,ns \cdot 400\,kHz \approx 0.24$ W | $V_{SD}$ 2.4 V typ (datasheet); 10 ns dead time per edge assumed |
| High-side turn-on gate current (plateau) | $(V_{DD} - V_{plateau}) / (R_{pullup} + R_{HOH} + R_{G})$ | $(5 - 2.6) / (2.1 + 2 + 0.5) \approx 0.52$ A | 2.1 Ω driver pull-up, 0.5 Ω FET internal $R_G$, 2.6 V plateau (datasheets); 2 Ω HOH (decision #5). Peak at 0 V gate: $5 / 4.6 \approx 1.1$ A, inside the driver's 1.2 A |
| Turn-on switching time | $Q_{sw} / I_{G}$ | $3.3\,nC / 0.52\,A \approx 6.3$ ns | $Q_{sw}$ 3.3 nC typ (datasheet). Common-source inductance (no Kelvin pin) slows this further |
| Turn-on dv/dt | $V_{in} / (Q_{gd} / I_{G})$ | $48 / (2.6\,nC / 0.52\,A) \approx 10$ V/ns | About 17 V/ns with 0 Ω. LM5113-Q1 HS slew limit is 50 V/ns |
| Turn-on overlap loss | $\tfrac{1}{2} V_{in} I_{valley} t_{sw} f_{sw}$ | $0.5 \cdot 48 \cdot 10.8 \cdot 6.3\,ns \cdot 400\,kHz \approx 0.66$ W | High-side hard turn-on; valley current $12.5 - 3.3/2$ A. About 0.37 W with 0 Ω |
| Turn-off overlap loss (upper bound) | $\tfrac{1}{2} V_{in} I_{peak} t_{off} f_{sw}$ | $0.5 \cdot 48 \cdot 14.2 \cdot 1.4\,ns \cdot 400\,kHz \approx 0.19$ W | $t_{off} = Q_{sw} / (2.6\,V / 1.1\,\Omega)$; the load current charges $C_{oss}$, so the real loss is lower |
| Total FET loss | Sum of the above | ≈ 2.3 W | 0.79 W conduction + 0.41 W $Q_{oss}$ + 0.24 W dead time + 0.85 W overlap. Against a ~6 W total budget at 150 W |
| Miller-induced low-side gate bump | $C_{rss} \cdot dv/dt \cdot (R_{pulldown} + R_G)$ | $8\,pF \cdot 17\,V/ns \cdot 1.1\,\Omega \approx 0.15$ V | Worst case (0 Ω turn-on). Far below the 1.2 V minimum threshold, which is why the turn-off paths have no added resistance. **Optimistic:** this counts only $C_{rss}$ current through the pull-down, not common-source or gate-loop inductance. Infineon's evaluation board, with an active Miller clamp, shows the low-side $V_{GS}$ reaching roughly +1.8 V during high-side turn-on (UG122052 Figure 25, 48 V → 12 V, 500 kHz, 20 A; read from the plot). Verification test 12 measures ours |
| FET loss split | High side: conduction + $Q_{oss}$ + overlap. Low side: conduction + dead time | High side $0.20 + 0.41 + 0.85 \approx 1.46$ W; low side $0.59 + 0.24 \approx 0.83$ W | 150 W, 400 kHz, from the rows above. In hard-switched turn-on, the $Q_{oss}$ energy of the low-side FET is dissipated in the high-side FET's channel |
| FET junction rise, still air | $P \cdot R_{th(j\text{-}a)}$ | High side $1.46 \cdot 38 \approx 55$ K; low side $0.83 \cdot 38 \approx 32$ K | $R_{th(j\text{-}a)}$ 38 K/W typ on a JEDEC 2s2p (4-layer) board, vertical, still air (exact IGC033S10S1 datasheet). Ignores heat from the neighbouring FET, L301 and R301, and that $R_{DS(on)}$ rises with temperature. Higher than the ≈ 42 °C in decision #4. At 200 W the high side reaches ≈ 1.9 W, ≈ 72 K |
| Loop inductance from ringing | $C_{par} = C_{add} / \big((f_1/f_2)^2 - 1\big)$, then $L_{loop} = 1 / \big((2\pi f_1)^2 C_{par}\big)$ | — (bench) | $f_1$: switch-node ring frequency as built. $f_2$: with a known C0G capacitor $C_{add}$ across Q302 at the snubber footprint (C320). Infineon's board rings at ≈ 300 MHz (period ≈ 3.3 ns), which implies well under 1 nH. Also sets the snubber starting values (R302 ≈ $\sqrt{L_{loop}/C_{par}}$) |
| Driver gate-charge current | $2 \cdot Q_g \cdot f_{sw}$ | $2 \cdot 11\,nC \cdot 400\,kHz \approx 8.8$ mA | Plus driver operating current; ≈ 10 mA total on `+5V` |
| Bootstrap capacitor | $C_{BST} \ge (Q_{gH} + I_{HB} t_{on} + Q_{rr}) / \Delta V$ | $(14 + 2.5\,mA \cdot 1.25\,\mu s + 4)\,nC / 100\,nF \approx 0.21$ V droop | Datasheet eq. 2. $Q_g$ 14 nC max; $I_{HB}$ 2.5 mA max at 500 kHz; $t_{on}$ budgeted at D = 0.5; $Q_{rr}$ 4 nC. 100 nF chosen; 220 nF if the bench shows sag |
| VDD bypass | $C_{VDD} \ge (Q_{gH} + Q_{gL} + Q_{rr}) / \Delta V$, and $\ge 10\,C_{BST}$ | 32 nC / ≈ 4.1 µF ≈ 8 mV droop; ≈ 4.1 µF vs 1 µF required | Datasheet eq. 1 and section 9 (100 nF at the pins + 220 nF–10 µF). C322 is C96446 (decision #16): ≥ 40 % kept at 5 V ASSUMED (no Samsung DC-bias figure recorded in preferred-parts.md yet), so ≥ 4 µF + 0.1 µF effective. The previous 1 µF part gave only 0.76 µF, below the 10 × C_BST rule |
| Input-filter delay, rising | $\tau \ln\big(V_{OH} / (V_{OH} - V_{IR})\big)$ | $22\,ns \cdot \ln(3.3 / 1.24) \approx 21.5$ ns | 1 kΩ × 22 pF; 3.3 V logic; 2.06 V rising threshold typ |
| Input-filter delay, falling | $\tau \ln(V_{OH} / V_{IF})$ | $22\,ns \cdot \ln(3.3 / 1.66) \approx 15$ ns | 1.66 V falling threshold typ. Turn-on lags turn-off by ≈ 6.5 ns **at nominal values only**; the [corner analysis](../reviews/2026-11-11-pwm-overlap-and-input-filter.md) shows no guaranteed positive deadtime margin |
| Inductance | $L = (V_{in} - V_{out}) D / (f_{sw} \Delta I_L)$ | $36 \cdot 0.25 / (400\,kHz \cdot 3.75\,A) \approx 6.0$ µH → 6.8 µH | 30 % ripple target |
| Inductor ripple current | $\Delta I_L = (V_{in} - V_{out}) D / (L f_{sw})$ | 3.3 A at 400 kHz (4.4 A at 300 kHz, 2.6 A at 500 kHz) | 6.8 µH |
| Peak inductor current | $I_{out,max} + \Delta I_L / 2$ | $16.7 + 4.4/2 \approx 18.9$ A | 200 W rating, 300 kHz worst case. Inductor $I_{sat}$ ≥ 20 A; the current-limit trip must sit below $I_{sat}$ |
| Input capacitor RMS current | $I_{out} \sqrt{D(1-D)}$ | $12.5 \sqrt{0.1875} \approx 5.4$ A rms | Shared across the ceramic bank |
| Input capacitance | $C_{in} \ge I_{out} D(1-D) / (f_{sw} \Delta V_{in})$ | $2.34 / (300\,kHz \cdot 1\,V) \approx 7.8$ µF effective | 1 V p-p at the FETs, 300 kHz worst case. Effective value at 48 V after DC-bias derating |
| Input bank, effective | $\sum n \cdot C \cdot k_{DC}$ at 48 V | $4 \cdot 0.042 + 6 \cdot 0.83 + 2 \cdot 2.65 \approx 10.45$ µF | Typical Samsung curve readback: 100 nF 0603 ≈ 42 % at 48 V, 2.2 µF 1206 37.5 %, 10 µF 1210 26.5 %. At 60 V: ≈ 8.0 µF vs 6.7 µF needed (D = 0.2). These curve values are not guaranteed minima |
| Output capacitance (ripple) | $C_{out} \ge \Delta I_L / (8 f_{sw} \Delta V_{out})$ | $4.4 / (8 \cdot 300\,kHz \cdot 50\,mV) \approx 37$ µF effective | 50 mV p-p target (decision #7), 300 kHz worst case. Effective value at 12 V |
| Output ceramics, effective | $n \cdot C \cdot k_{DC} \cdot k_{AC}$ | $8 \cdot 22 \cdot 0.26 \approx 46$ µF; ≈ 39 µF with $k_{AC} \approx 0.85$ | C12891 keeps 26 % at 12 V (Samsung DC-bias data, measured at 0.5 Vrms); about 15 % lower again at ~10 mV ripple |
| Output ripple | $\Delta I_L / (8 f_{sw} C_{eff})$ | ≈ 47 mV at 300 kHz, ≈ 27 mV at 400 kHz | Using 39 µF; polymer ESR (25 mΩ) is in parallel and does not dominate |
| Load-step deviation | $\Delta I / (2\pi f_c C_{out})$ | $10 / (2\pi \cdot 25\,kHz \cdot 510\,\mu F) \approx 125$ mV | 10 % → 90 % step; 470 µF polymer + ceramics; ≈ 25 kHz crossover assumed |
| Inductor DCR loss | $I_{out}^2 \cdot DCR$ | $12.5^2 \cdot 2.1\,m\Omega \approx 0.33$ W | 0.59 W at 16.7 A; core loss not included (no data at 400 kHz) |
| Shunt loss and signal | $I^2 R$; $I R$ | 0.16 W and 12.5 mV at 12.5 A; 18.9 mV at the 18.9 A peak | 1 mΩ, 3 W rated |
| Frequency-dependent loss | $Q_{oss}$ + dead time + overlap + gate drive | 1.15 W (300 kHz) · 1.54 W (400 kHz) · 1.91 W (500 kHz) | Same assumptions as the rows above; basis for decision #4 |
| PWM resolution without HRPWM | $V_{in} \cdot f_{sw} / f_{EPWM}$ | $48 \cdot 400\,kHz / 120\,MHz \approx 160$ mV per count | 300 counts per period in up-count mode (half that in up-down). HRPWM's ~150 ps step gives ≈ 3 mV |

---

## Part selection

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| Q301, Q302 | 100 V enhancement-mode GaN FET | Infineon IGC033S10S1 | C41381300 | 100 V (120 V pulsed); 3.3 mΩ max; $Q_g$ 11 nC; $Q_{oss}$ 43 nC; gate 5 V typ, 5.5 V recommended max; PG-TSON-6, 3 × 5 mm | [Infineon IGC033S10S1 industrial datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-igc033s10s1-datasheet-en.pdf) |
| U301 | GaN half-bridge gate driver | TI LM5113-Q1 (LM5113QDPRRQ1) | C2677036 | HS 90 V recommended / 93 V abs max (HB 100 V); 4.5–5.5 V supply; 5.2 V bootstrap clamp; 1.2 A source / 5 A sink split outputs; 28 ns delay, 1.5 ns matching; WSON-10 4 × 4 mm | [TI](https://ti.com/product/LM5113-Q1) |
| C323 | Bootstrap capacitor, HB–HS | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF 50 V X7R 0603, Basic; ≈ 0.21 V droop per cycle | |
| C321, C322 | VDD bypass | YAGEO CC0603KRX7R9BB104; Samsung CL10A106MA8NRNC | C14663; C96446 | 100 nF X7R at the pins + 10 µF 25 V X5R 0603, Basic (decision #16); C322 is the same part as input_supply C209 | |
| D301 | External bootstrap diode, VDD → HB | BAT46W (hongjiacheng) | C7420332 | 100 V Schottky, SOD-123, Preferred (no loading fee); the datasheet lists BAT46, BAT41 or LL4148 | |
| R303 | Bootstrap series resistor | UNI-ROYAL 0603WAF1000T5E | C22775 | 100 Ω, per datasheet section 7.3.2 | |
| R304 | High-side turn-on resistor (HOH) | UNI-ROYAL 0603WAF200KT5E | C22977 | 2 Ω, Basic; tune 0–4.7 Ω on the bench | |
| R305, R306 | HI / LI input-filter resistors | UNI-ROYAL 0603WAF1001T5E | C21190 | 1 kΩ, Basic; datasheet Figure 16 | |
| C324, C325 | HI / LI input-filter capacitors | Samsung CL10C220JB8NNNC | C1653 | 22 pF C0G, Basic; datasheet Figure 16 | |
| L301 | Output inductor | Sunltech SLB2212P6R8MTT | C2842794 | 6.8 µH ±20 %, 31 A $I_{sat}$, 28.5 A rated, 2.1 mΩ, 22.5 × 22 mm | [LCSC](https://www.lcsc.com/product-detail/C2842794.html) |
| C309, C310, C326, C327 | Input ceramics, closest to the FETs | Samsung CL10B104KC8NNNC | C15725 | Four 100 nF 100 V X7R 0603, Extended; about 42 % kept at 48 V on the typical DC-bias graph | [Samsung product](https://product.samsungsem.com/mlcc/CL10B104KC8NNN.do), [exact-part datasheet](https://datasheet.octopart.com/CL10B104KC8NNNC-Samsung-datasheet-42770383.pdf) |
| C303–C308 | Input ceramics, main bank | Samsung CL31B225KCHSNNE | C170101 | 2.2 µF 100 V X7R 1206; 37.5 % kept at 48 V | [Samsung](https://product.samsungsem.com/mlcc/CL31B225KCHSNN.do) |
| C301, C302 | Input ceramics, main bank | Samsung CL32Y106KCV6PNE | C22380050 | 10 µF 100 V X7S 1210; 26.5 % kept at 48 V | [Samsung](https://product.samsungsem.com/mlcc/CL32Y106KCV6PN.do) |
| C311–C318 | Output ceramics | Samsung CL31A226KAHNNNE | C12891 | 22 µF 25 V X5R 1206, Basic; 26 % kept at 12 V | [Samsung](https://product.samsungsem.com/mlcc/CL31A226KAHNNN.do) |
| C319 | Output bulk | jieerrui MA25V470M8x10 | C46550466 | 470 µF 25 V polymer, 25 mΩ, 4.1 A ripple, SMD 8 × 10 mm | |
| R301 | Current-sense shunt | FOJAN FPM253WFR001TML | C7420016 | 1 mΩ 1 % 3 W 2512, ±50 ppm/°C | |
| NT301, NT302 | Shunt Kelvin net ties | KiCad `Device:NetTie_2` | — | Footprint only (copper), no part placed. NT302 on the L301 side (`I_SH_OUT_P`), NT301 on the `V_OUT` side (`I_SH_OUT_N`) | |
| J301 | 12 V output connector | Kefa KF635-6.35-2P | C475102 | 2-pin screw terminal, 32 A, 10–22 AWG, M3, 6.35 mm pitch; through-hole | [LCSC](https://www.lcsc.com/product-detail/C475102.html) |
| R302, C320 | Switch-node RC snubber (DNP) | — | — | 1206 resistor + 1206 100 V C0G footprints; values from the measured ringing | |
| TP_VIN1, TP_SW1, TP_VOUT1, TP_GND1, TP_GND2, TP_LSG1, TP_LSS1 | Test pads | — | — | Footprint only. TP_LSG1 is on `LS_DRIVE` and TP_LSS1 is on `GND`; place the 1 mm pair close to Q302 gate pin 1 and source pin 6 for a short spring-ground measurement | |
| LED301, R307 | `12V` output LED | KENTO KT-0805G; UNI-ROYAL 0603WAF1002T5E | C2297; C25804 | Green 0805 LED ($V_F$ 2.6–3.1 V), 10 kΩ: ≈ 0.9 mA at 12 V; Basic. Place beside J301 | |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| Maximum switch-node voltage | 90 V (LM5113-Q1 HS recommended max; 93 V abs max) | input_supply | Tighter than the FETs' 100 V. TVS clamping voltage at surge current, plus ringing, must stay below this |
| GaN FET drain-source rating | 100 V (120 V pulsed) | input_supply | Not the limiting rating; see the row above |
| Switching frequency | 400 kHz nominal, 300–500 kHz range | mcu, firmware, sensing | HRPWM required |
| `+5V` maximum | 5.5 V in normal operation, including transients | input_supply | VDD drives the low-side gate directly, with no clamp. Accepted exception (#15): a mis-set J202 supply can reach the TPS2121 cutoff, up to 5.68 V |
| Driver current on `+5V` | ≈ 10 mA at 400 kHz | input_supply | Rises with switching frequency |
| Driver propagation delay / matching | 28 ns typ / 1.5 ns typ | mcu, firmware | Include in the ePWM dead-time setting |
| Input-filter effect on dead time | ≈ +6.7 ns per edge at nominal values, not a guaranteed positive margin | mcu, firmware | A high-rail/low-threshold corner can reverse the nominal rise/fall difference; measure the real dead time at the gates. See [input-filter analysis](../reviews/2026-11-11-pwm-overlap-and-input-filter.md) |
| Peak inductor current | ≈ 18.9 A at 200 W, 300 kHz | sensing | The overcurrent trip must sit below the inductor's 31 A $I_{sat}$ |
| Shunt | 1 mΩ, in series with the inductor; Kelvin pair `I_SH_OUT_P` / `I_SH_OUT_N` through NT302 / NT301 | sensing | 12 V common mode with switching ripple; 12.5 mV at 12.5 A |
| Output connector | KF635-6.35-2P screw terminal | input_supply | Reusing it for J201 avoids a second loading fee |
| FET reverse-conduction voltage | 2.4 V typ at 20 A | mcu, firmware | Every extra ns of dead time costs loss |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- The IGC033S10S1 has **no separate Kelvin source pin**. Return each gate loop to the source pad nearest that FET's gate pin, and route the power current away from that spot. On the PG-TSON-6 that is pin 6, the source pad directly beside the gate (pin 1).
- Place the LM5113-Q1 right beside the FETs, with its bootstrap capacitor at its HB/HS pins and its VDD decoupling at its VDD pin.
- Gate margin is about 0.5 V (5 V drive, 5.5 V recommended max), so gate-loop inductance must be as small as possible.
- Put C323 (bootstrap) and C321 (100 nF VDD) on the same side as the driver, right at its pins, with no vias between them and the pins.
- Keep the bootstrap charging loop (C321 → D301/R303 → C323 → low-side FET → back) short.
- Connect the driver's VSS to the low-side FET's source by a short, direct path. If a shunt ever sits in that source path, VSS goes on the FET side of it.
- TI's layout examples assume 0402 parts; 0402 for R304 and C323 would tighten the gate loop if space is short.
- **Power loop first:** C309, C310, C326 and C327 (100 nF 0603) go directly across the high-side drain and low-side source, then C301–C308 just outside them. Mark them `Layout = power loop, place first`.
- Place R301 between L301 and the output capacitors, and route `I_SH_OUT_P` / `I_SH_OUT_N` as a tight pair from the shunt's inner pad edges (Kelvin), away from the switch node. Place NT302 and NT301 against the inner edge of their shunt pads; they keep layout from tapping the power copper anywhere else.
- Put the snubber (R302, C320) across the low-side FET, drain to source, inside the power loop.
- Keep the switch-node copper only as large as L301's pad needs; it radiates.

**Power-loop layout (decision #19).** References: EPC WP010 ([epc-gan-pcb-layout.pdf](epc-gan-pcb-layout.pdf)) for the method, and Infineon UG122052 ([infineon-FET-reference-design.pdf](infineon-FET-reference-design.pdf), section 6.2) for a working 4-layer layout with this exact FET.

- **4 layers.** Inner layer 1 is the power loop's return path: a solid, unbroken `GND` pour directly under Q301, Q302, C301–C310, C326 and C327. No traces or splits cross it in that area; a single cut breaks the field cancellation the layout depends on.
- **Stackup.** Choose the standard 1.6 mm 4-layer stackup with the thinner L1–L2 prepreg (about 0.1 mm, versus about 0.2 mm for 7628 prepreg). In WP010, this distance, not board thickness, sets the loop inductance. Confirm the stackup name and dielectric on JLCPCB's stackup page at order time and record it in [specifications.md](../specifications.md).
- **Inner copper is 0.5 oz.** That is fine for the high-frequency return, which spreads across the plane, but no DC load current goes through the inner layers. Keep the 12.5 A path from the switch node to L301 on the outer layers (on EPC's board the switch node drops through inner layers; ours must not).
- **Interleaved vias.** Q302's pads 2–5 alternate drain / source / drain / source (three 0.45 × 3.30 mm inner bars and one 0.65 × 3.30 mm outer bar), the same interleaved structure as EPC's LGA parts. Place alternating `SW_NODE` and `GND` via rows aligned with those bars, between the two FETs. Avoid via-in-pad unless the vias are plugged and capped, which is a process option to check against the Economic PCBA rules first.
- **Input caps.** Put the positive terminals of C309, C310, C326 and C327 right at Q301's drain bars, as WP010 does. Split the four parts along the drain and return bars to shorten each current loop; their schematic spacing does not define PCB placement. Infineon's board uses a separate group of 5 × 220 nF 0603 caps at the half-bridge.
- **Low-side gate loop is the most sensitive loop on the board.** LOH / LOL to Q302's gate and the driver's VSS to Q302's pin 6 as short and as tightly paired as possible. Infineon's board shows a low-side gate bump near +1.8 V even with an active Miller clamp, and the LM5113-Q1 has none.
- **Probe points.** The switch node rings at a few hundred MHz, so probe loops must stay under 10 mm (UG122052 section 3.2). Place TP_LSG1 (`LS_DRIVE`) and TP_LSS1 (`GND`) as a 1 mm exposed-pad pair within a few millimetres of Q302 gate pin 1 and source pin 6. Keep the gate pad's branch short and off the driver-to-gate path; return the source pad directly to pin 6, not to a distant ground pour. Confirm the intended scope tip and ground spring can contact both pads without touching neighboring copper or an optional heatsink.
- **Q301 / Q302 footprint.** The library footprint now separates `F.Cu`, `F.Mask`, and `F.Paste` per Infineon's [IGC033S10S1 footprint drawing](https://www.infineon.com/assets/row/public/documents/24/49/infineon-igc033s10s1-datasheet-en.pdf) (Figure 2). See the [correction record](../reviews/2026-11-11-igc033s10s1-footprint-correction.md). Place from the updated library. Before ordering, confirm the inferred copper overhang, mask registration, and paste pattern for the assembler's stencil thickness. The symbol pin map remains gate 1, drain 2/4, source 3/5/6.

**Thermal provisions (decision #20).**

- Thermal vias under the FET drain and source pads into the inner and bottom pours are the main planned heat path without a heatsink. The exact IGC033S10S1 datasheet gives $R_{th(j\text{-}c)}$ of **0.5 K/W typ at the top** and **1.9 K/W typ at the bottom**; the former does not imply a low junction-to-ambient resistance without a fitted heatsink.
- Keep a heatsink zone over Q301 / Q302: no parts taller than the FETs inside it, and room for two mounting holes or push-pins clear of the power loop. Infineon clips its heatsink on with spring pins over an electrically isolating thermal pad (T-Global TG-A1780, 0.5 mm). The exposed top silicon is internally connected to source: Q301's top is at `SW_NODE` and Q302's at `GND`. Use an electrically insulating thermal interface that keeps these surfaces isolated from each other and the heatsink; the top is not an electrical connection pad.
- The bottom side stays free of parts (single-sided assembly), so a bottom-side heatsink over the thermal vias is a second option. The vias there sit at `V_IN`, `SW_NODE` and `GND` potential, so it also needs an isolating pad.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Low-side and high-side gate-to-source voltages | Low side: ≥ 1 GHz scope and passive probe on the low-side gate/source probe pair (MMCX or spring tip, loop < 10 mm), at reduced then full input voltage. High side: use a suitable isolated or high-common-mode differential measurement across gate and source; a ground-referenced passive probe on the high-side gate cannot verify its gate-to-source peak (UG122052 section 3.2). The LM5113-Q1 bootstrap clamp is 5.2 V typical but can reach 5.456 V before ringing, so it is not a substitute for measurement | Measured positive peaks remain below the FET's 5.5 V recommended gate limit over tested conditions | | |
| 2 | Switch-node overshoot and undershoot | ≥ 1 GHz scope and probe at `TP_SW1` with the ground pad beside it (loop < 10 mm), and check as close as practical to U301 HS; increase load at 48 V and 51 V | Proposed positive peak below 80 V for margin to the driver's 90 V recommended HS maximum; negative minimum above its -5 V recommended HS minimum. Record both edge waveforms. Reference: Infineon's board peaks near 52 V at 2 Ω and 66 V at 1 Ω (48 V, 20 A, UG122052 Figure 27, read from the plot) | | |
| 3 | FET temperature at full load | Thermal camera after 30 min at 150 W in still air, then at 200 W and at 500 kHz. Paint the FETs and nearby copper matte black or white first so emissivity is consistent (UG122052 section 3.3). Record the RTD readings alongside, since they read the board, not the die | Proposed: hottest FET ≤ 100 °C at a 25 °C bench. Above that, fit the heatsink or a fan (decision #20). The camera-to-RTD offset feeds the overtemperature threshold | | |
| 4 | Dead time | Measure both FET gate-to-source waveforms simultaneously with suitable low-inductance, high-common-mode probes (test 1). A low-side gate plus switch-node capture is only a preliminary screen | Confirm turn-on/turn-off transitions do not overlap under tested conditions and record the difference from the ePWM setting; ≈ +6.7 ns from the input filters is only a nominal estimate. Infineon suggests starting near 10 ns per edge | | |
| 5 | Cold start and gate hold-off | With J202 disconnected, apply only 48 V at J201 using slow and fast input ramps; record `V_IN`, `+5V`, both FET gate-to-source voltages (with a suitable high-side probe), `SW_NODE` and output voltage. Repeat with J202's 5 V applied before 48 V, then with 48 V present and J202 removed | Neither gate rises above 1 V before valid drive and there is no unintended output pulse under the tested ramps. Keep the full VGS waveforms within the FET's recommended limits. Compare single-bus and prebiased starts; if hold-off fails, revise the hardware before full-power operation | | |
| 6 | High-side turn-on resistor | Sweep R304 (0, 2, 4.7 Ω) at full load | Choose the lowest value that keeps switch-node and gate overshoot within limits. Infineon's 1–3 Ω sweep changed efficiency by only ≈ 0.15 % at 12.5 A (UG122052 Figure 28), so overshoot margin should decide, not efficiency | | |
| 7 | Efficiency vs frequency | Sweep 300 → 500 kHz at 20 %, 50 % and 100 % load | Curve recorded; confirm 400 kHz or choose a better point | | |
| 8 | Output ripple | Scope at J301 with a short ground spring, 20 MHz bandwidth limit, full load, 300 and 400 kHz | ≤ 50 mV p-p | | |
| 9 | Input ripple at the FETs | Scope across C309 at full load | ≤ 1 V p-p | | |
| 10 | Load step | 10 % → 90 % step on the e-load | Deviation and settling recorded against the spec | | |
| 11 | Inductor temperature | Thermal camera after 30 min at 150 W, surface painted matte as in test 3 | Within the inductor's rating | | |
| 12 | Low-side gate bump during high-side turn-on | Same probing as test 1, at full load, R304 at its chosen value | Record the gate bump, switch-node waveform and input current. A 1.2 V comparison is only a 25 °C screening reference: the specified minimum $V_{GS(th)}$ is measured at 8 mA and does not define a safe parasitic-turn-on limit over temperature. If the bump is material, tighten the gate loop or revisit the driver before full-power use | | |
| 13 | Power-loop inductance | Ring frequency at the switch node as built ($f_1$), then with a known C0G capacitor fitted at C320 ($f_2$); calculation row *Loop inductance from ringing* | Recorded; target ≲ 1 nH. Sets R302 / C320 starting values | | |

---

## Open questions

- Confirm the hot $R_{DS(on)}$ factor (1.5× assumed) from the datasheet's normalized curve.
- Check the SLB2212P6R8MTT datasheet for how $I_{sat}$ is defined and for core-loss data near 400 kHz.
- The load-transient target in the specifications is still [TBD]; the polymer sizing assumes ≈ 25 kHz crossover.
- **Startup sequence validation.** The [LM5113-Q1 datasheet](https://www.ti.com/lit/ds/symlink/lm5113-q1.pdf) §7.3.2 specifies VDD before the half-bridge VIN bus, while this board derives `+5V` from `V_IN` when J202 is absent. TI's [LM5113 evaluation board guide](https://www.ti.com/lit/ug/snva484b/snva484b.pdf) describes a single-VIN-supply startup, so the practical applicability of that sequence instruction to this topology needs confirmation. Test 5 now covers the normal single-bus cold start as well as J202-first operation; a J202-first-only bench procedure does not validate normal operation. R21 / R22 hold HI / LI low, and the driver's VDD UVLO pulls HOL / LOL low, but no fitted gate-to-source resistor independently holds either FET off if the driver is unpowered.
- Gate hold-off with `HS_PWM` / `LS_PWM` undriven relies on the enable sheet's pull-downs (R21 / R22). For the universal control board, where PWM will arrive over a connector, consider 10 kΩ pull-downs at the driver's HI / LI on this sheet.
- **High-frequency input caps:** decision #22 chooses four 0603 parts. Recheck C15725 stock and the exact-part bias curve before assembly release; the capacitance estimate is typical. Confirm all four can fit in the short power-loop placement without stretching the loop.
- **Low-side gate probe point:** TP_LSG1 / TP_LSS1 implement the schematic interface. Confirm the physical pad spacing and scope-probe clearance during placement, before routing the gate loop.
- **Stackup.** Confirm the exact name of JLCPCB's thin-prepreg 4-layer 1.6 mm stackup and its L1–L2 dielectric (about 0.1 mm expected) and record it in the specifications (decision #19).
- **Heatsink.** Decide after verification test 3 (decision #20). The exact-part datasheet resolves the top connection: source. Keep any heatsink electrically isolated from both FET tops and verify the insulation with the mechanical design.
- (Resolved 2026-11-11: the correct datasheet is the industrial IGC033S10S1, Rev. 1.1, 2025-04-22. It supersedes the earlier IGC033S101 and automotive IGC033S10S1Q references. Its $R_{th(j\text{-}c)}$ values are 0.5 K/W top and 1.9 K/W bottom; $R_{th(j\text{-}a)}$ is 38 K/W on a 2s2p board with vias.)
- **GaN footprint manufacturing review.** The Figure 2 copper/mask/paste library correction is complete. Obtain the fabricator's mask-registration and assembler's stencil review before releasing the board; Figure 2 does not dimension every copper edge.
- **Driver choice, if test 12 fails.** Infineon pairs this FET with two 1EDN7126G drivers: active Miller clamp, high-side bootstrap fed from the low-side driver so it cannot overcharge, and optional negative off-state bias. The LM5113-Q1's internal 5.2 V bootstrap clamp covers the overcharge risk, so this alone is no reason to reopen decision #3; a low-side gate bump near threshold would be.
