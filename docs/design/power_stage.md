# Power Stage — Design Notes

Sheet: `sheets/power_stage.kicad_sch`

**Owner:** [Reza Rahimzadeh] · **Last updated:** [2026-11-03]

---

## Purpose and requirements

Convert the 48 V bus to the 12 V output with a synchronous buck: two discrete enhancement-mode GaN FETs, a GaN half-bridge gate driver, the output inductor and capacitors, and the current-sense shunt.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Power stage** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- 48 V in, 12 V out at up to 12.5 A (150 W), with parts and copper rated for 16.7 A (200 W).
- Switching frequency within 300–500 kHz.
- Meet the efficiency target in the specifications (about 95–96 % expected, roughly 6 W total loss at 150 W) with natural-convection cooling.
- Keep the GaN gate voltage within the FETs' limits under all conditions, including ringing.
- Support the shortest safe dead time, set in the MCU's ePWM.
- Meet the output ripple and load-transient targets in the specifications.
- Provide a Kelvin-connected current-sense shunt whose value lets sensing place the overcurrent threshold within 0–3 V.
- Hold both gates off when the driver is unpowered or `GATE_HI` / `GATE_LO` are undriven.
- Inputs: `GATE_HI`, `GATE_LO` from enable. Outputs: `ISH_P`, `ISH_N` to sensing.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-03 | Discrete GaN FETs with a separate GaN half-bridge gate driver | Integrated GaN half-bridge with built-in driver (LMG2100 family) | Team decision | Gate-loop layout and gate-voltage limits become this sheet's responsibility | Accepted |
| 2 | 2026-11-03 | GaN FETs: Infineon IGC033S10S1, same part in both positions | EPC2306 (0 stock at JLCPCB), EPC2302 (9 in stock, larger die), EPC2308 (150 V, 51 in stock, no EasyEDA footprint), Infineon IGB070S10S1 (5 mΩ, 80 in stock), Innoscience 100 V parts (WLCSP / LGA) | In stock at JLCPCB and Economic-assemblable; 3.3 mΩ max keeps total FET loss near 1.7 W at full load; packaged 3 × 5 mm; one part number for both positions | input_supply: TVS clamp must stay well below the 100 V rating. Enable/mcu: none | Accepted |
| 3 | 2026-11-03 | Gate driver: TI LM5113-Q1 (WSON-10) | LMG1205 (DSBGA, Standard-PCBA only), LMG1210 (needs 6–18 V supply; $12.72) | Keeps the order on Economic PCBA; 5.2 V bootstrap clamp is below the FET's 5.5 V recommended max; runs from `+5V`; split outputs; active part with JLCPCB stock | mcu: dead time must cover the 28 ns propagation delay and 1.5 ns matching. input_supply: about 10 mA more on `+5V` | Accepted |

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
| Switching overlap loss | Estimate | ≈ 0.3 W | Rough estimate; refine from driver current and $Q_{gd}$ (2.6 nC) |
| Total FET loss | Sum of the above | ≈ 1.7 W | Against a ~6 W total budget at 150 W |
| High-side turn-on time | $Q_g / I_{source}$ | $11\,nC / 1.2\,A \approx 9$ ns | $Q_g$ from FET datasheet; 1.2 A source from LM5113-Q1 page; turn-on resistor slows this further |
| Driver gate-charge current | $2 \cdot Q_g \cdot f_{sw}$ | $2 \cdot 11\,nC \cdot 400\,kHz \approx 8.8$ mA | Plus driver quiescent current; ≈ 10 mA total on `+5V` |

---

## Part selection

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| Q301, Q302 | 100 V enhancement-mode GaN FET | Infineon IGC033S10S1 | C41381300 | 100 V (120 V pulsed); 3.3 mΩ max; $Q_g$ 11 nC; $Q_{oss}$ 43 nC; gate 5 V typ, 5.5 V recommended max; PG-TSON-6, 3 × 5 mm | [Infineon](https://www.infineon.com/assets/row/public/documents/10/49/infineon-igc033s10s1q-datasheet-en.pdf) (automotive variant, same die) |
| U301 | GaN half-bridge gate driver | TI LM5113-Q1 (LM5113QDPRRQ1) | C2677036 | 100 V bootstrap; 4.5–5.5 V supply; 5.2 V bootstrap clamp; 1.2 A source / 5 A sink split outputs; 28 ns delay, 1.5 ns matching; WSON-10 4 × 4 mm | [TI](https://ti.com/product/LM5113-Q1) |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| GaN FET drain-source rating | 100 V (120 V pulsed) | input_supply | The input TVS must clamp well below this |
| Driver current on `+5V` | ≈ 10 mA at 400 kHz | input_supply | Rises with switching frequency |
| Driver propagation delay / matching | 28 ns typ / 1.5 ns typ | mcu, firmware | Include in the ePWM dead-time setting |
| FET reverse-conduction voltage | 2.4 V typ at 20 A | mcu, firmware | Every extra ns of dead time costs loss |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- The IGC033S10S1 has **no separate Kelvin source pin**. Return each gate loop to the source pad nearest that FET's gate pin, and route the power current away from that spot.
- Place the LM5113-Q1 right beside the FETs, with its bootstrap capacitor at its HB/HS pins and its VDD decoupling at its VDD pin.
- Gate margin is about 0.5 V (5 V drive, 5.5 V recommended max), so gate-loop inductance must be as small as possible.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | High- and low-side gate voltage | Scope with a low-inductance probe tip at the FET, at reduced then full input voltage | Peaks stay below 5.5 V; no turn-on during the other FET's switching | | |
| 2 | Switch-node overshoot | Scope at the switch node, full load | Peak well below 100 V | | |
| 3 | FET temperature at full load | Thermal camera after 30 min at 150 W | Within the thermal budget (TBD) | | |

---

## Open questions

- Confirm the hot $R_{DS(on)}$ factor (1.5× assumed) from the datasheet's normalized curve.
- Read the LM5113-Q1 datasheet's start-up section: TI lists improved start-up as a difference in the LMG1205, so check the bootstrap's behaviour at first switching.
- Refine the overlap-loss estimate once the gate resistors are chosen.
