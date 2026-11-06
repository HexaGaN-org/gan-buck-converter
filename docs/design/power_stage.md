# Power Stage — Design Notes

Sheet: `sheets/power_stage.kicad_sch`

**Owner:** Reza Rahimzadeh · **Reviewer:** [NAME] · **Last updated:** 2026-11-06

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
- Hold both gates off when the driver is unpowered or `HS_PWM` / `LS_PWM` are undriven. The LM5113-Q1's HI / LI must not float and have no documented internal pull-downs; on this board the 10 kΩ pull-downs R21 / R22 on the enable sheet's `HS_PWM` / `LS_PWM` outputs provide this (see open questions).

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-03 | Discrete GaN FETs with a separate GaN half-bridge gate driver | Integrated GaN half-bridge with built-in driver (LMG2100 family) | Team decision | Gate-loop layout and gate-voltage limits become this sheet's responsibility | Accepted |
| 2 | 2026-11-03 | GaN FETs: Infineon IGC033S10S1, same part in both positions | EPC2306 (0 stock at JLCPCB), EPC2302 (9 in stock, larger die), EPC2308 (150 V, 51 in stock, no EasyEDA footprint), Infineon IGB070S10S1 (5 mΩ, 80 in stock), Innoscience 100 V parts (WLCSP / LGA) | In stock at JLCPCB and Economic-assemblable; 3.3 mΩ max keeps total FET loss near 1.7 W at full load; packaged 3 × 5 mm; one part number for both positions | input_supply: TVS clamp must stay well below the 100 V rating. Enable/mcu: none | Accepted |
| 3 | 2026-11-03 | Gate driver: TI LM5113-Q1 (WSON-10) | LMG1205 (DSBGA, Standard-PCBA only), LMG1210 (needs 6–18 V supply; $12.72) | Keeps the order on Economic PCBA; 5.2 V bootstrap clamp is below the FET's 5.5 V recommended max; runs from `+5V`; split outputs; active part with JLCPCB stock | mcu: dead time must cover the 28 ns propagation delay and 1.5 ns matching. input_supply: about 10 mA more on `+5V` | Accepted |
| 4 | 2026-11-03 | Switching frequency 400 kHz nominal; hardware valid across 300–500 kHz | 300 kHz (1.15 W frequency-dependent loss, larger passives), 500 kHz (1.91 W, high-side FET ~50 °C rise, 240 CPU cycles per period), 1 MHz (3.8 W, needs a heatsink) | Middle of the spec range: 1.54 W frequency-dependent loss, high-side FET ~42 °C rise, 300 CPU cycles per period. One 6.8 µH inductor keeps ripple and peak current acceptable across 300–500 kHz, so frequency becomes a firmware setting and the bench can measure efficiency vs frequency | mcu/firmware: HRPWM required; control ISR budget 300 cycles. Input and output capacitors sized for the 300 kHz worst case | Accepted |
| 5 | 2026-11-03 | Gate-drive passives per the LM5113-Q1 datasheet and TI's reference circuit (Figure 18): 100 nF bootstrap, 1 µF + 100 nF on VDD, external BAT46W + 100 Ω bootstrap path, 2 Ω on HOH, HOL direct, LOH and LOL tied, 1 kΩ + 22 pF input filters | 0 Ω turn-on (≈ 0.3 W less loss, ≈ 17 V/ns edges); no input filters (TI's reference fits 0 Ω and leaves the capacitors off) | Datasheet section 7.3.2 requires the external diode and 100 Ω. 2 Ω roughly halves turn-on dv/dt and ringing on a first board and can be tuned 0–4.7 Ω on the bench. Turn-off paths stay stiff so Miller current can't lift the gates. Filters reject glitches on PWM traces that cross the board | mcu/firmware: input filters add ≈ 6.5 ns to every dead time. input_supply: `+5V` must stay ≤ 5.5 V, because VDD drives the low-side gate directly | Accepted |
| 6 | 2026-11-03 | 10 kΩ gate-to-source footprints at each FET, DNP | Fitted 10 kΩ; no footprint (TI's reference) | Not required by the datasheet: when unpowered, the driver's output structures clamp the gates into the bootstrap and VDD capacitors. The footprint guards against assembly faults (an open gate resistor or driver joint) and can be fitted if the bench shows gate movement on a cold 48 V start | none | Superseded by #13 |
| 7 | 2026-11-03 | Output ripple target 50 mV p-p | 100 mV p-p (fewer capacitors) | About 0.4 % of 12 V; achievable with Basic ceramics at 300 kHz worst case | specifications updated | Accepted |
| 8 | 2026-11-03 | Output inductor: Sunltech SLB2212P6R8MTT, 6.8 µH (C2842794) | COILMX MTF1810-6R8M (4.7 mΩ, 19 A thermal, $1.59, 18 mm); Sumida CY1770 6.8 µH (22.5 A $I_{sat}$, 6.55 mΩ) | 31 A $I_{sat}$ vs 18.9 A peak; 2.1 mΩ gives 0.33 W at 12.5 A (0.4 W less than the MTF1810); 28.5 A thermal rating covers 16.7 A with margin | Layout: 22.5 × 22 mm footprint | Accepted |
| 9 | 2026-11-03 | Input ceramics: 2× 100 nF 0805 (C28233) + 6× Samsung 2.2 µF 1206 (C170101) + 2× Samsung 10 µF 1210 (C22380050); 10.4 µF effective at 48 V | YAGEO 2.2 µF 1206 (C577211) and PSA 10 µF 1210 (C5156756): no published DC-bias curves | Every part has a published Samsung DC-bias curve; 33 % margin over the 7.8 µF requirement at 48 V, and still passes at 60 V | input_supply: bulk electrolytics stay on that sheet | Accepted |
| 10 | 2026-11-03 | Output capacitors: 8× Samsung 22 µF 25 V 1206 (C12891, Basic) + 1× 470 µF 25 V polymer (C46550466) | 6× C12891 (fails: only 26 % kept at 12 V); 5× 22 µF 1210 (C52306, 41 % kept, but an extra $3.07 loading fee) | 46 µF ceramic effective (≈ 39 µF at small ripple) vs 37 µF needed; polymer holds a 10 A step to ≈ 125 mV | sensing / firmware: loop crossover target ≈ 25 kHz assumed for the transient estimate | Accepted |
| 11 | 2026-11-03 | Current-sense shunt: 1 mΩ 3 W 2512 (C7420016), in series with the inductor between L301 and the output capacitors | Low-side source shunt (ground-referenced, but misses the high-side peak); input-side shunt | Sees the full inductor current, including the peak the cycle-by-cycle limit needs | sensing: amplifier must tolerate 12 V common mode (INA240-class); 12.5 mV at 12.5 A, 18.9 mV at peak | Accepted |
| 12 | 2026-11-03 | J301 output connector: Kefa KF635-6.35-2P screw terminal (C475102), plus switch-node RC snubber footprints (DNP) and test pads | XT60PW (needs adapter leads for the e-load); 5.08 mm terminals (24 A rating, 2.5 mm² wire) | 32 A, 10 AWG / 4 mm², M3 screws; connects straight to bench loads. Snubber values come from the measured ringing | input_supply: using the same terminal for J201 adds no loading fee | Accepted |
| 13 | 2026-11-03 | No gate-to-source pull-downs (supersedes #6) | DNP 10 kΩ footprints (#6) | Matches TI's reference design; the driver's output structures hold the gates when unpowered. Verification test 5 checks the cold start | none | Accepted |
| 14 | 2026-11-06 | Shunt Kelvin connections through net ties NT302 (L301 side → `I_SH_OUT_P`) and NT301 (`V_OUT` side → `I_SH_OUT_N`); hierarchical labels named `I_SH_OUT_P` / `I_SH_OUT_N` | Labels directly on R301's power wires | Same reasoning as input_supply #21: the ties make the sense pair two separate nets that meet the power copper only at R301's pads, and DRC enforces it. The `_OUT` names pair with the input shunt's `I_SH_IN_*` and match the sensing sheet | sensing: inputs already named `I_SH_OUT_P` / `I_SH_OUT_N`. schematic-hierarchy updated | Accepted |
| 15 | 2026-11-06 | `+5V` maximum stays 5.5 V in normal operation, with one accepted exception: a J202 bench supply mis-set above 5.5 V can reach the TPS2121's overvoltage cutoff (5.21–5.68 V), putting up to 5.68 V on the low-side gate | Requiring input_supply to guarantee ≤ 5.5 V (a cutoff that can trip on a correctly set 5.0 V supply) | See input_supply #23. The bench rule is 5.0 V on J202; the exceedance needs a mis-set supply and stays below the FET's ±6.5 V pulsed rating, though that rating isn't meant for continuous use | input_supply: none (cutoff unchanged) | Accepted |

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
| Miller-induced low-side gate bump | $C_{rss} \cdot dv/dt \cdot (R_{pulldown} + R_G)$ | $8\,pF \cdot 17\,V/ns \cdot 1.1\,\Omega \approx 0.15$ V | Worst case (0 Ω turn-on). Far below the 1.2 V minimum threshold, which is why the turn-off paths have no added resistance |
| Driver gate-charge current | $2 \cdot Q_g \cdot f_{sw}$ | $2 \cdot 11\,nC \cdot 400\,kHz \approx 8.8$ mA | Plus driver operating current; ≈ 10 mA total on `+5V` |
| Bootstrap capacitor | $C_{BST} \ge (Q_{gH} + I_{HB} t_{on} + Q_{rr}) / \Delta V$ | $(14 + 2.5\,mA \cdot 1.25\,\mu s + 4)\,nC / 100\,nF \approx 0.21$ V droop | Datasheet eq. 2. $Q_g$ 14 nC max; $I_{HB}$ 2.5 mA max at 500 kHz; $t_{on}$ budgeted at D = 0.5; $Q_{rr}$ 4 nC. 100 nF chosen; 220 nF if the bench shows sag |
| VDD bypass | $C_{VDD} \ge (Q_{gH} + Q_{gL} + Q_{rr}) / \Delta V$, and $\ge 10\,C_{BST}$ | 32 nC / 0.76 µF ≈ 42 mV droop | Datasheet eq. 1 and section 9 (100 nF at the pins + 220 nF–10 µF). C15849 keeps 66 % at 5 V (Samsung DC-bias data), so 0.66 µF + 0.1 µF effective. Well inside the 200 mV UVLO hysteresis |
| Input-filter delay, rising | $\tau \ln\big(V_{OH} / (V_{OH} - V_{IR})\big)$ | $22\,ns \cdot \ln(3.3 / 1.24) \approx 21.5$ ns | 1 kΩ × 22 pF; 3.3 V logic; 2.06 V rising threshold typ |
| Input-filter delay, falling | $\tau \ln(V_{OH} / V_{IF})$ | $22\,ns \cdot \ln(3.3 / 1.66) \approx 15$ ns | 1.66 V falling threshold typ. Turn-on lags turn-off by ≈ 6.5 ns, adding that to each dead time |
| Inductance | $L = (V_{in} - V_{out}) D / (f_{sw} \Delta I_L)$ | $36 \cdot 0.25 / (400\,kHz \cdot 3.75\,A) \approx 6.0$ µH → 6.8 µH | 30 % ripple target |
| Inductor ripple current | $\Delta I_L = (V_{in} - V_{out}) D / (L f_{sw})$ | 3.3 A at 400 kHz (4.4 A at 300 kHz, 2.6 A at 500 kHz) | 6.8 µH |
| Peak inductor current | $I_{out,max} + \Delta I_L / 2$ | $16.7 + 4.4/2 \approx 18.9$ A | 200 W rating, 300 kHz worst case. Inductor $I_{sat}$ ≥ 20 A; the current-limit trip must sit below $I_{sat}$ |
| Input capacitor RMS current | $I_{out} \sqrt{D(1-D)}$ | $12.5 \sqrt{0.1875} \approx 5.4$ A rms | Shared across the ceramic bank |
| Input capacitance | $C_{in} \ge I_{out} D(1-D) / (f_{sw} \Delta V_{in})$ | $2.34 / (300\,kHz \cdot 1\,V) \approx 7.8$ µF effective | 1 V p-p at the FETs, 300 kHz worst case. Effective value at 48 V after DC-bias derating |
| Input bank, effective | $\sum n \cdot C \cdot k_{DC}$ at 48 V | $2 \cdot 0.052 + 6 \cdot 0.83 + 2 \cdot 2.65 \approx 10.4$ µF | DC-bias retention from Samsung data: 100 nF 0805 52 %, 2.2 µF 1206 37.5 %, 10 µF 1210 26.5 %. At 60 V: ≈ 7.9 µF vs 6.7 µF needed (D = 0.2) |
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
| Q301, Q302 | 100 V enhancement-mode GaN FET | Infineon IGC033S10S1 | C41381300 | 100 V (120 V pulsed); 3.3 mΩ max; $Q_g$ 11 nC; $Q_{oss}$ 43 nC; gate 5 V typ, 5.5 V recommended max; PG-TSON-6, 3 × 5 mm | [Infineon](https://www.infineon.com/assets/row/public/documents/10/49/infineon-igc033s10s1q-datasheet-en.pdf) (automotive variant, same die) |
| U301 | GaN half-bridge gate driver | TI LM5113-Q1 (LM5113QDPRRQ1) | C2677036 | HS 90 V recommended / 93 V abs max (HB 100 V); 4.5–5.5 V supply; 5.2 V bootstrap clamp; 1.2 A source / 5 A sink split outputs; 28 ns delay, 1.5 ns matching; WSON-10 4 × 4 mm | [TI](https://ti.com/product/LM5113-Q1) |
| C323 | Bootstrap capacitor, HB–HS | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF 50 V X7R 0603, Basic; ≈ 0.21 V droop per cycle | |
| C321, C322 | VDD bypass | YAGEO CC0603KRX7R9BB104; Samsung CL10A105KB8NNNC | C14663; C15849 | 100 nF X7R at the pins + 1 µF 50 V X5R, Basic | |
| D301 | External bootstrap diode, VDD → HB | BAT46W (hongjiacheng) | C7420332 | 100 V Schottky, SOD-123, Preferred (no loading fee); the datasheet lists BAT46, BAT41 or LL4148 | |
| R303 | Bootstrap series resistor | UNI-ROYAL 0603WAF1000T5E | C22775 | 100 Ω, per datasheet section 7.3.2 | |
| R304 | High-side turn-on resistor (HOH) | UNI-ROYAL 0603WAF200KT5E | C22977 | 2 Ω, Basic; tune 0–4.7 Ω on the bench | |
| R305, R306 | HI / LI input-filter resistors | UNI-ROYAL 0603WAF1001T5E | C21190 | 1 kΩ, Basic; datasheet Figure 16 | |
| C324, C325 | HI / LI input-filter capacitors | Samsung CL10C220JB8NNNC | C1653 | 22 pF C0G, Basic; datasheet Figure 16 | |
| L301 | Output inductor | Sunltech SLB2212P6R8MTT | C2842794 | 6.8 µH ±20 %, 31 A $I_{sat}$, 28.5 A rated, 2.1 mΩ, 22.5 × 22 mm | [LCSC](https://www.lcsc.com/product-detail/C2842794.html) |
| C309, C310 | Input ceramics, closest to the FETs | Samsung CL21B104KCFNNNE | C28233 | 100 nF 100 V X7R 0805, Basic; 52 % kept at 48 V | [Samsung](https://product.samsungsem.com/mlcc/CL21B104KCFNNN.do) |
| C303–C308 | Input ceramics, main bank | Samsung CL31B225KCHSNNE | C170101 | 2.2 µF 100 V X7R 1206; 37.5 % kept at 48 V | [Samsung](https://product.samsungsem.com/mlcc/CL31B225KCHSNN.do) |
| C301, C302 | Input ceramics, main bank | Samsung CL32Y106KCV6PNE | C22380050 | 10 µF 100 V X7S 1210; 26.5 % kept at 48 V | [Samsung](https://product.samsungsem.com/mlcc/CL32Y106KCV6PN.do) |
| C311–C318 | Output ceramics | Samsung CL31A226KAHNNNE | C12891 | 22 µF 25 V X5R 1206, Basic; 26 % kept at 12 V | [Samsung](https://product.samsungsem.com/mlcc/CL31A226KAHNNN.do) |
| C319 | Output bulk | jieerrui MA25V470M8x10 | C46550466 | 470 µF 25 V polymer, 25 mΩ, 4.1 A ripple, SMD 8 × 10 mm | |
| R301 | Current-sense shunt | FOJAN FPM253WFR001TML | C7420016 | 1 mΩ 1 % 3 W 2512, ±50 ppm/°C | |
| NT301, NT302 | Shunt Kelvin net ties | KiCad `Device:NetTie_2` | — | Footprint only (copper), no part placed. NT302 on the L301 side (`I_SH_OUT_P`), NT301 on the `V_OUT` side (`I_SH_OUT_N`) | |
| J301 | 12 V output connector | Kefa KF635-6.35-2P | C475102 | 2-pin screw terminal, 32 A, 10–22 AWG, M3, 6.35 mm pitch; through-hole | [LCSC](https://www.lcsc.com/product-detail/C475102.html) |
| R302, C320 | Switch-node RC snubber (DNP) | — | — | 1206 resistor + 1206 100 V C0G footprints; values from the measured ringing | |
| TP_VIN1, TP_SW1, TP_VOUT1, TP_GND1, TP_GND2 | Test pads | — | — | Footprint only. In layout, put one ground pad right beside `TP_SW` (near Q302's source) and the other beside `TP_VOUT` | |

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
| Extra dead time from input filters | ≈ 6.5 ns per edge | mcu, firmware | Turn-on is delayed more than turn-off; measure the real dead time at the gates |
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
- **Power loop first:** C309/C310 (100 nF 0805) go directly across the high-side drain and low-side source, then C301–C308 just outside them. Mark them `Layout = power loop, place first`.
- Place R301 between L301 and the output capacitors, and route `I_SH_OUT_P` / `I_SH_OUT_N` as a tight pair from the shunt's inner pad edges (Kelvin), away from the switch node. Place NT302 and NT301 against the inner edge of their shunt pads; they keep layout from tapping the power copper anywhere else.
- Put the snubber (R302, C320) across the low-side FET, drain to source, inside the power loop.
- Keep the switch-node copper only as large as L301's pad needs; it radiates.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | High- and low-side gate voltage | Scope with a low-inductance probe tip at the FET, at reduced then full input voltage | Peaks stay below 5.5 V; no turn-on during the other FET's switching | | |
| 2 | Switch-node overshoot | Scope at the switch node, full load | Peak below 80 V (driver HS max 90 V) | | |
| 3 | FET temperature at full load | Thermal camera after 30 min at 150 W | Within the thermal budget (TBD) | | |
| 4 | Dead time at the gates | Scope both gates at the FETs | Both edges positive (no overlap) and close to the ePWM setting + ≈ 6.5 ns | | |
| 5 | Cold start with 48 V before `+5V` | Scope both gates while raising 48 V with the driver unpowered | Neither gate rises above 1 V; if one does, add gate-to-source pull-downs in the next revision | | |
| 6 | High-side turn-on resistor | Sweep R304 (0, 2, 4.7 Ω) at full load | Choose the lowest value that keeps switch-node and gate overshoot within limits | | |
| 7 | Efficiency vs frequency | Sweep 300 → 500 kHz at 20 %, 50 % and 100 % load | Curve recorded; confirm 400 kHz or choose a better point | | |
| 8 | Output ripple | Scope at J301 with a short ground spring, 20 MHz bandwidth limit, full load, 300 and 400 kHz | ≤ 50 mV p-p | | |
| 9 | Input ripple at the FETs | Scope across C309 at full load | ≤ 1 V p-p | | |
| 10 | Load step | 10 % → 90 % step on the e-load | Deviation and settling recorded against the spec | | |
| 11 | Inductor temperature | Thermal camera after 30 min at 150 W | Within the inductor's rating | | |

---

## Open questions

- Confirm the hot $R_{DS(on)}$ factor (1.5× assumed) from the datasheet's normalized curve.
- Check the SLB2212P6R8MTT datasheet for how $I_{sat}$ is defined and for core-loss data near 400 kHz.
- The load-transient target in the specifications is still [TBD]; the polymer sizing assumes ≈ 25 kHz crossover.
- Our board breaks the datasheet's "VDD first, then VIN" sequencing because `+5V` comes from the 48 V bus. Verification test 5 checks the effect; on the bench, bring up 5 V through J202 first.
- Gate hold-off with `HS_PWM` / `LS_PWM` undriven relies on the enable sheet's pull-downs (R21 / R22). For the universal control board, where PWM will arrive over a connector, consider 10 kΩ pull-downs at the driver's HI / LI on this sheet.
