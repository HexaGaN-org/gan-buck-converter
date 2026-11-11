# Sensing — Design Notes

Sheet: `sheets/sensing.kicad_sch`

**Owner:** Connor Jin · **Reviewer:** [NAME] · **Last updated:** 2026-11-05

---

## Purpose and requirements

Turn the output current, the input current, the input and output voltages, and the GaN FET temperatures into filtered, clamped 0–3.3 V signals for the MCU's ADC and CMPSS comparators.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Sensing** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- `I_OUT_SENSE`: cover the full inductor current range, including negative current at light load, with the overcurrent threshold inside 0–3 V and enough bandwidth for cycle-by-cycle current limiting.
- `V_OUT_SENSE`: place the overvoltage threshold inside 0–3 V; this signal feeds a CMPSS comparator.
- `V_IN_SENSE`: cover the full input range, including the undervoltage-lockout thresholds.
- `HS_TEMP_SENSE`, `LS_TEMP_SENSE`: one temperature sensor beside each GaN FET, covering the overtemperature threshold (decision #5).
- `I_IN_SENSE`: amplify the input shunt (1 mΩ R201, Kelvin pair `I_SH_IN_P` / `I_SH_IN_N`, input_supply #17) with an amplifier whose common mode covers 40–51 V and **survives the 82.4 V clamped surge**. Telemetry and a firmware input-current limit only, so filter it heavily.
- Meet the measurement accuracy the control loop and protections need (target to be set in the specifications).
- Size every RC for the ADC's acquisition time, not only for noise, and keep every signal inside `+3V3` / `GNDA`: by a clamp on the channels driven from `+5V` (decision #11) (there is no separate `+3V3A` rail: input_supply #19).
- `I_OUT_SENSE` bandwidth sets how fast cycle-by-cycle current limiting can act: keep its filter light. Filter the temperature channels more heavily. `V_IN_SENSE` also feeds the fast input-overvoltage comparator (input_supply #24), which needs τ ≈ 1 µs (open questions).

**Status (2026-11-06):** circuit captured: six channels, labels matching the contract and the MCU sheet (decision #8), wired to mcu, power_stage and input_supply on the root sheet (2026-11-10). The amplifiers and RTD bias changed since rows 2–7 were written (decisions #9–#11); the calculations and published values below follow the sheet as drawn. Remaining before layout: test points and the open questions.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

Rows 2–7 were written on 2026-11-05 from the schematic as drawn. The rationale is what the calculations below support, not a record of the original discussion; the owner should confirm or correct each row and change its status to *Accepted*.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-05 | Proposed: one current-sense amplifier part for both channels (`I_OUT_SENSE` and `I_IN_SENSE`), gain ≈ 100, chosen so its common-mode rating covers the input side (operation to 51 V, survival to ≥ 82.4 V) | Gain 200 on the input channel (about 0.13–1.1 V over the load range; better light-load resolution, but a second amplifier part and loading fee) | One unique part for four placements (two shunts, two amplifiers). At gain 100 the input channel spans about 0.07–0.53 V: fine for telemetry and a limit; move it to gain 200 if bench readings at light load are too noisy | mcu: `I_IN_SENSE` on any ADC pin (no CMPSS needed) | Superseded by #2 |
| 2 | 2026-11-05 | Both current channels use **TI INA241A3 (gain 50 V/V)**, U402 on the output shunt and U407 on the input shunt, with REF1 on `+3V3` and REF2 on GND, so zero current sits at **1.65 V** (bidirectional). VS from `+5V` | Gain 100 (A4) with the same 1.65 V zero: 18.9 A peak would read 3.54 V, past the 3.3 V range; gain 100 with REF to GND (unidirectional): loses the negative valley current and puts zero current on the bottom rail; a different gain on the input channel (#1): a second part number | With a mid-scale zero, gain 50 is the highest INA241 gain that keeps the 18.9 A peak (2.60 V) and the inductor's 31 A $I_{sat}$ (3.20 V) inside the range, so the overcurrent trip can sit between them, and the −2.2 A light-load valley (1.54 V) is still readable. Common mode −5 to 110 V operating (−20 to 120 V survival) covers 12 V on the output shunt and 40–51 V plus the 82.4 V clamp on the input shunt. One part number serves both. The input channel spans only 1.68–1.92 V at 16 mA per count: adequate for telemetry and a firmware limit | mcu: `I_OUT_SENSE` (then `I_SENSE`) on a CMPSS-capable pin (then pin 9 as assigned); `I_IN_SENSE` on any ADC pin. Firmware: calibrate both zeros at start-up with PWM off (calculations) | As drawn — owner to confirm |
| 3 | 2026-11-05 | Voltage channels: resistive divider into an **OPA192 unity-gain buffer** (U401 for `V_OUT`, U408 for `V_IN`), then the per-channel RC and clamp (#6). `V_OUT`: 750 kΩ / 150 kΩ (÷ 6). `V_IN`: 750 kΩ / 20 kΩ (÷ 38.5). Both top resistors are the same **1206** part | Divider straight into the RC with no buffer (the divider's 125 kΩ / 19.5 kΩ would set the filter and the ADC's charge-sharing error); a lower-impedance divider (more current drawn from `V_IN`, larger resistors for the dissipation) | The buffer isolates the high-impedance dividers from the ADC sample capacitor and the CMPSS input. OPA192 bias current is a few pA, so the divider impedance adds no measurable error. `V_OUT` ÷ 6 puts 12 V at 2.00 V and leaves room to 19.8 V for the overvoltage trip. `V_IN` ÷ 38.5 keeps the 82.4 V clamp at 2.14 V, inside the range, so the clamp diodes never conduct during a surge and the reading stays valid; it costs resolution (31 mV per count), which is still ample for UVLO and feedforward. 1206 meets input_supply's rule for parts on `V_IN` (80 V across R411 at the clamp; 0603 is ≈ 75 V) | input_supply: 66 µA drawn from `V_IN`. mcu: `V_OUT_SENSE` on CMPSS2 (pin 23), `V_IN_SENSE` on pin 6 | Divider and buffer topology as drawn; op-amp part superseded by #9 |
| 4 | 2026-11-05 | Temperature sensors are **Vishay PTS1206 platinum RTDs (PT1000)**, U404 and U405, not thermistors. Each sits at the bottom of a 20 kΩ divider from `+5V`, amplified × 5.98 by an OPA192 non-inverting stage (U403, U406: 20 kΩ / 4.02 kΩ) | NTC thermistor (large signal, but non-linear and typically ±1–5 % tolerance); TI LMT8x-style analog sensor IC | Linear (IEC 60751, 3850 ppm/K) and tight-tolerance, so one equation and a room-temperature calibration cover the whole range. The gain stage turns the ≈ 0.9 mV/°C divider slope into ≈ 5.2 mV/°C (0.16 °C per ADC count). 25 °C reads 1.55 V, 100 °C 1.94 V, 150 °C 2.18 V. Measuring current 0.24 mA (Vishay: 0.1–0.25 mA), self-heating ≈ 0.04 K | mcu: needs an ADC pin per sensor. Layout: the RTDs sit on this sheet but are placed at the FETs | RTDs and gain as drawn; op-amp superseded by #9, bias by #10 |
| 5 | 2026-11-05 | Two temperature channels, one per FET: `HS_TEMP_SENSE` (U404, high-side Q301) and `LS_TEMP_SENSE` (U405, low-side Q302) | One sensor between the two FETs, as the contract's single `TEMP_SENSE` assumes | At D = 0.25 the low-side FET carries 75 % of the conduction loss (0.59 W vs 0.20 W) while the high side takes the switching loss (≈ 0.85 W overlap plus $Q_{oss}$), so the two can run at different temperatures; two sensors show which side to fix and which side to protect | schematic-hierarchy / mcu: a second temperature signal and ADC pin are needed (open questions) | As drawn — owner to confirm |
| 6 | 2026-11-05 | Every output gets **1 kΩ in series, a capacitor to `GNDA`, and a BAT54S series pair** clamping it to `GNDA` and `+3V3`. Capacitor per channel: **22 pF** on `I_OUT_SENSE`, **1 nF** on `V_OUT_SENSE`, **100 nF** on `V_IN_SENSE`, `I_IN_SENSE` and both temperature channels | One filter value for every channel; no clamps (relying on the MCU's internal ESD diodes) | Matches the requirements: `I_OUT_SENSE` stays fast for cycle-by-cycle limiting (22 ns, so the INA241's 145 ns dominates); `V_OUT_SENSE` gets 1 µs for a clean overvoltage comparator; the telemetry channels get 100 µs (1.6 kHz) and settle from a single ADC sample. 100 nF also makes ADC charge sharing negligible (0.2 mV). The amplifiers run from `+5V` and can drive past 3.3 V, so the Schottky clamps and 1 kΩ limit a fault to ≈ 1.3–1.9 mA, most of it through the Schottky rather than the MCU pin (±2 mA continuous allowed) | mcu: acquisition-window limits (values published below). input_supply: up to ≈ 2 mA per clamped channel flows into `+3V3` during a fault | Op-amp channel clamps superseded by #11 |
| 7 | 2026-11-05 | All six amplifiers run from `+5V`, each with a 100 nF supply bypass; each INA241's REF1 has its own 100 nF to GND | Amplifiers on `+3V3` | The OPA192 needs at least 4.5 V, so `+3V3` cannot run it. `+5V` gives the INA241 and OPA192 outputs room to reach the full 3.3 V range | input_supply: ≈ 9 mA added to `+5V`. The `+5V` hand-over dip (≈ 4.48 V for ≈ 5 µs) touches the OPA192's 4.5 V minimum (open questions) | Op-amp supply superseded by #9 |
| 8 | 2026-11-06 | Hierarchical labels renamed to the contract style: `I_OUT_SENSE`, `I_IN_SENSE`, `V_OUT_SENSE`, `V_IN_SENSE`, `HS_TEMP_SENSE`, `LS_TEMP_SENSE` (PR #6); the MCU sheet and the hierarchy doc use the same names | Keeping `I_OUT_SENSE`-style names | UPPER_SNAKE_CASE per CONTRIBUTING, and one name per signal across sheets | mcu, schematic-hierarchy: updated | Accepted |
| 9 | 2026-11-06 | The four op-amps (U401, U403, U406, U408) are **TI TLV9061** (C398358) on **`+3V3`**, replacing the OPA192s on `+5V`. Supersedes the op-amp part in #3 and #4, and #7 for the op-amps (the INA241s stay on `+5V`) | OPA192 on `+5V` (#3, #4, #7) | Recorded from the schematic. What the change gives, from the parts' data: an op-amp on `+3V3` can't drive its output past the ADC's range, so those channels need no clamp (#11); it rides through the `+5V` hand-over dip; it costs less. What it costs: 1.6 mV max offset against the OPA192's 25 µV (≈ 2 counts on the voltage channels, ≈ 1.5 °C on the temperature channels before calibration) | input_supply: `+5V` load down to ≈ 5 mA, ≈ 2.8 mA on `+3V3` | Recorded from the schematic — owner to confirm |
| 10 | 2026-11-06 | RTD bias **10 kΩ from `+3V3`** (R403, R404, C25804), replacing 20 kΩ from `+5V`. Supersedes the bias in #4; gain stays 5.98 | 20 kΩ from `+5V` (#4); 20 kΩ from `+3V3` (0.16 mA) | Recorded from the schematic. `+3V3` doesn't step when the 5 V source changes between J202 and `5V_AUX` (the open question this answers). Larger signal (≈ 6 mV/°C) than 20 kΩ would give; 0.30 mA measuring current, a little above Vishay's 0.1–0.25 mA (open questions) | none | Recorded from the schematic — owner to confirm |
| 11 | 2026-11-06 | BAT54S clamps only on the two INA241 outputs (D405 `I_OUT_SENSE`, D406 `I_IN_SENSE`). Supersedes #6's clamps on the four op-amp channels | Clamps on all six (#6) | Recorded from the schematic. The INA241s run from `+5V` and can drive past 3.3 V; the TLV9061s run from `+3V3` and can't. The 1 kΩ series resistors and filter capacitors are unchanged | none | Recorded from the schematic — owner to confirm |

---

## Calculations

One row per calculation. Note where each input came from (specification, datasheet, measurement) in Notes. ADC figures use the F280039C's internal reference in the 0–3.3 V range (mcu.md): one count is 0.806 mV.

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| **Output current (`I_OUT_SENSE`, U402)** | | | INA241A3: 50 V/V, ±10 µV offset, ±0.01 % gain error, 1.1 MHz, 8 V/µs (TI datasheet SBOSA30) |
| Transfer function | $V = (V_{REF1} + V_{REF2})/2 + G R_{sh} I_L$ | $V = 1.65\,V + 50\,mV/A \cdot I_L$ | REF1 on `+3V3`, REF2 on GND; 1 mΩ shunt R301 (power_stage #11) |
| Readings at key currents | same | −2.2 A → 1.54 V · 0 A → 1.65 V · 12.5 A → 2.28 V · 18.9 A → 2.60 V · 31 A → 3.20 V | −2.2 A: light-load valley at 300 kHz. 18.9 A: peak at 200 W, 300 kHz. 31 A: L301 $I_{sat}$ |
| Range and resolution | $(3.3 - 1.65) / 50\,mV/A$; $0.806\,mV / 50\,mV/A$ | ±33 A over 0–3.3 V; 16 mA per count | Above ≈ 39 A the pin passes VDDA + 0.3 V (clamp row) |
| Zero error before calibration | $\pm 3\,\% \cdot 1.65\,V$ | ±50 mV = **±1 A** | `+3V3` is ±3 % over temperature (input_supply #18) and the ADC uses its internal reference, so the REF midpoint is not ratiometric. The INA241's own offset is only 10 mA. Calibrate the zero at start-up with PWM off |
| Amplifier response at the switching frequency | $1/\sqrt{1 + (f_{sw}/1.1\,MHz)^2}$; $\tau = 1/(2\pi \cdot 1.1\,MHz)$ | Ripple amplitude reads 96 % (300 kHz), 94 % (400 kHz), 91 % (500 kHz); ≈ 145 ns lag | First-order estimate. A sample timed at the middle of the on-time reads the current from ≈ 145 ns earlier: ≈ 0.8 A low at 48 V. Delay the SOC by ≈ 150 ns, or sample mid off-time (≈ 0.25 A error) |
| Output RC (R417, C415) | $R C$ | 22 ns (7.2 MHz) | Isolation for the ADC and CMPSS; the amplifier sets the bandwidth |
| Cycle-by-cycle trip lag | $\tau_{INA} + R_{417}(C_{415} + C_p) + t_{CMPSS} + t_{driver} + t_{filter}$ | 145 + 29 + 60 + 28 + 15 ≈ 280 ns | CMPSS 60 ns max (F280039C datasheet §6.13.5.3); LM5113 28 ns and its input filter ≈ 15 ns (power_stage). ePWM trip-zone logic not included |
| Peak current above the trip setting | $\frac{di}{dt} \cdot t_{lag}$, $\frac{di}{dt} = (V_{in} - V_{out})/L$ | ≈ 1.5 A at 48 V; ≈ 2.0 A at 51 V with L at −20 % | Plus ±0.4 A from the CMPSS's ±20 mV offset. A trip at ≈ 22 A peaks near 24 A, still well below the 31 A $I_{sat}$ |
| **Input current (`I_IN_SENSE`, U407)** | | | Same amplifier and transfer function |
| Readings over the load range | $1.65\,V + 50\,mV/A \cdot I_{in}$ | 0.66 A (20 %) → 1.68 V · 3.29 A (48 V, 150 W) → 1.81 V · 3.95 A (40 V) → 1.85 V · 5.3 A (200 W) → 1.92 V | Input currents from input_supply. 16 mA per count: ≈ 0.5 % of the 48 V full-load reading |
| Filter (R418, C416) | $R C$ | 100 µs (1.6 kHz) | Telemetry and firmware limit only |
| Common-mode margin | INA241 range vs input_supply | 40–51 V operating and 82.4 V clamp vs 110 V operating, 120 V survival | No protection needed between R201 and U407 |
| **Output voltage (`V_OUT_SENSE`, U401)** | | | |
| Divider ratio | $R_{402} / (R_{401} + R_{402})$ | $150 / 900 = 1/6$ | |
| Readings | $V_{OUT} / 6$ | 12 V → 2.00 V · 13.2 V (+10 %) → 2.20 V · 18 V → 3.00 V · 19.8 V → 3.30 V | 4.8 mV of `V_OUT` per count |
| Ratio tolerance | 1 % resistors, worst case | ±1.7 % (±0.2 V at 12 V) | Calibrate the gain once against a meter (verification test 5) |
| Divider load and source impedance | $V/R$; $R_{401} \parallel R_{402}$ | 13 µA at 12 V; 125 kΩ | TLV9061 bias current (0.5 pA) adds no error |
| Filter (R413, C411) | $R C$ | 1 µs (159 kHz) | Fast enough for the overvoltage comparator; the 470 µF output bank limits how fast `V_OUT` can rise |
| **Input voltage (`V_IN_SENSE`, U408)** | | | |
| Divider ratio | $R_{412} / (R_{411} + R_{412})$ | $20 / 770 = 1/38.5$ | |
| Readings | $V_{IN} / 38.5$ | 36 V → 0.935 V · 38 V → 0.987 V · 40 V → 1.04 V · 48 V → 1.25 V · 51 V → 1.32 V · 53 V → 1.38 V · 82.4 V → 2.14 V | 36 / 38 / 53 V are input_supply's proposed UVLO and OVLO points. 31 mV of `V_IN` per count |
| Ratio tolerance | 1 % resistors, worst case | ±2.0 % (≈ ±1 V at 48 V) | Calibrate against a meter; matters for UVLO accuracy |
| R411 stress | $V_{IN}^2 / R$; $V_{IN} \cdot R_{411}/(R_{411}+R_{412})$ | 3.4 mW at 51 V, 8.8 mW and 80 V across it at the 82.4 V clamp | 1206: 250 mW, 200 V |
| Divider load | $V_{IN} / 770\,k\Omega$ | 66 µA at 51 V | |
| Filter (R407, C404) | $R C$ | 100 µs (1.6 kHz) | Too slow for the fast input-overvoltage comparator (input_supply #24): open questions |
| **Temperature (U404 / U405 with U403 / U406)** | | | PT1000: $R_T = 1000\,\Omega\,(1 + A T + B T^2)$, A = 3.9083 × 10⁻³, B = −5.775 × 10⁻⁷ (IEC 60751) |
| Amplifier gain | $1 + R_{405}/R_{406}$ | $1 + 20/4.02 = 5.98$ | Same for R409 / R408. ±1.7 % worst case from 1 % resistors |
| Transfer function | $V = 5.98 \cdot V_{3V3} \cdot R_T / (10\,k\Omega + R_T)$ | −40 °C → 1.53 V · 0 °C → 1.79 V · 25 °C → 1.95 V · 85 °C → 2.31 V · 100 °C → 2.40 V · 125 °C → 2.54 V · 150 °C → 2.68 V | At `+3V3` = 3.3 V (decision #10) |
| Sensitivity | $dV/dT$ | 6.2 mV/°C at 25 °C, 5.8 mV/°C at 100 °C; 0.13 °C per count | |
| Error from `+3V3` | $V \propto V_{3V3}$ | 1 % on `+3V3` = 3.1 °C at 25 °C, 4.2 °C at 100 °C | `+3V3` is ±2 % at 25 °C, ±3 % over temperature (input_supply #18) and doesn't move with the 5 V source; one-point calibration removes the initial error |
| Measuring current and self-heating | $V_{3V3}/(10\,k\Omega + R_T)$; $I^2 R_T \cdot 0.7\,K/mW$ | 0.30 mA at 25 °C; ≈ 0.07 K | Vishay PTS: 0.1–0.25 mA measuring current, 0.7 K/mW in still air (open questions) |
| Error from ground offset | $\Delta V_{GND} / (1.04\,mV/°C)$ | 1 mV between the RTD's return and the amplifier's ground ≈ 1 °C | Why the RTD return needs its own trace (layout notes) |
| Op-amp offset | $V_{OS} \cdot 5.98$ | ≤ 9.6 mV ≈ 1.5 °C (TLV9061, 1.6 mV max) | Removed by the one-point calibration (test 7) |
| Filter (R415 / C413, R416 / C414) | $R C$ | 100 µs (1.6 kHz) | |
| **ADC acquisition** | | | Input model, 3.3 V internal reference: $R_{on}$ 860 Ω, $C_h$ 7.5 pF; $C_p$ per pin from the 64-pin PM table, comparator enabled where CMPSS is used (F280039C datasheet §6.13.3.2.3) |
| Charge-sharing step, worst case | $3.3\,V \cdot C_h / (C_h + C_{ext} + C_p)$ | 686 mV (`iout`, 22 pF) · 24 mV (`vout`, 1 nF) · 0.2 mV (100 nF channels) | Worst case: the sample capacitor starts 3.3 V away from the signal |
| Time to settle to ½ count | two-node RC model (1 kΩ source) | **`iout`: ≈ 290 ns** (ACQPS ≥ 35 at 120 MHz) · **`vout`: ≈ 4.2 µs** · 100 nF channels: ≈ 65 ns (the 75 ns datasheet minimum covers it) | `vout` recovers through R413 into 1 nF (τ ≈ 1 µs). Avoided entirely if nothing else converts on the ADC that samples `V_OUT_SENSE` (values published below) |
| Loading by repeated sampling (100 nF channels) | $f_s R C_h \Delta V$ | 0.75 mV at 100 kHz, 3 mV at 400 kHz, with the previous channel 1 V away | ≤ 1 count below ≈ 100 kHz; telemetry channels don't need faster |
| **Clamps (D405, D406)** | | | BAT54S: $V_F$ ≤ 240 mV at 0.1 mA, ≤ 320 mV at 1 mA (Nexperia) |
| Clamp current, INA241 at its rail | $(V_{5V} - 3.3\,V - V_F) / 1\,k\Omega$ | 1.3 mA at 4.96 V; 1.9 mA at 5.5 V | Only `I_OUT_SENSE` and `I_IN_SENSE` (decision #11). MCU: ±2 mA continuous clamp current per pin, ±20 mA absolute maximum (datasheet §6.1) |
| Pin voltage while clamped | $V_{3V3} + V_F$ | ≈ 3.6 V | At the VDDA + 0.3 V limit, not below it. Above it the ADC disturbs other channels and the CMPSS isolates its input (datasheet §6.13.3.2, §6.13.5.3). Reached only past ≈ 39 A on `I_OUT_SENSE`, far beyond the trip; the op-amp channels stop at `+3V3` (decision #11) |
| Supply current added | sum | ≈ 5 mA on `+5V`: 2 × INA241 (≤ 2.5 mA). ≈ 2.8 mA on `+3V3`: 4 × TLV9061 (538 µA typ) + 2 × 0.30 mA RTDs | INA241 figure from the LCSC listing; confirm in the datasheet |

---

## Part selection

Refs match the schematic as of commit `808357c`.

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| U402 | Output current-sense amplifier (`I_SH_OUT_P` / `I_SH_OUT_N` → `I_OUT_SENSE`) | TI INA241A3IDDFR | C6051860 | 50 V/V; −5 to 110 V operating common mode (−20 to 120 V survival); ±10 µV offset; ±0.01 % gain error; 1.1 MHz, 8 V/µs, 1 µs settling to 1 %; REF1 / REF2 for a mid-scale zero; 2.7–20 V supply; SOT-23-8. Pins: 1 IN−, 2 GND, 3 REF2, 4 NC, 5 OUT, 6 VS, 7 REF1, 8 IN+ | [TI](https://www.ti.com/product/INA241A) |
| U407 | Input current-sense amplifier (`I_SH_IN_P` / `I_SH_IN_N` → `I_IN_SENSE`) | TI INA241A3IDDFR | C6051860 | Same part; 110 V operating common mode covers 40–51 V and the 82.4 V clamp | [TI](https://www.ti.com/product/INA241A) |
| U401, U408 | `V_OUT` and `V_IN` buffers (unity gain) | TI TLV9061IDBVR | C398358 | Rail-to-rail in and out; 1.8–5.5 V, run from `+3V3`; 1.6 mV max offset; 0.5 pA bias current; 10 MHz; SOT-23-5 (decision #9) | [TI](https://www.ti.com/product/TLV9061) |
| U403, U406 | HS and LS RTD amplifiers (gain 5.98) | TI TLV9061IDBVR | C398358 | Same part as the buffers; rail-to-rail input handles the 0.27–0.4 V divider signal with V− at GND | [TI](https://www.ti.com/product/TLV9061) |
| U404, U405 | HS and LS temperature sensors | Vishay PTS1206M2B1K00P100 | C17211685 | Platinum RTD, 1000 Ω at 0 °C, 3850 ppm/K (IEC 60751); 1206; −55 to +155 °C (Vishay datasheet; LCSC lists 175 °C). Tolerance class to confirm (open questions) | [DigiKey](https://www.digikey.ie/en/products/detail/vishay/PTS1206M2B1K00P100/8537261) |
| R401, R411 | Divider top resistors, `V_OUT` and `V_IN` | UNI-ROYAL 1206W4F7503T5E | C25835 | 750 kΩ 1 % **1206** (200 V, 250 mW); one part for both | |
| R402 | `V_OUT` divider bottom | UNI-ROYAL 0603WAF1503T5E | C22807 | 150 kΩ 1 %, Basic | |
| R412 | `V_IN` divider bottom | UNI-ROYAL 0603WAF2002T5E | C4184 | 20 kΩ 1 %, Basic | |
| R403, R404 | RTD bias resistors from `+3V3` | UNI-ROYAL 0603WAF1002T5E | C25804 | 10 kΩ 1 %, Basic (decision #10) | |
| R405, R409 | RTD amplifier feedback | UNI-ROYAL 0603WAF2002T5E | C4184 | 20 kΩ 1 %, Basic | |
| R406, R408 | RTD amplifier gain-set (to GND) | UNI-ROYAL 0603WAF4021T5E | C23040 | 4.02 kΩ 1 %, Basic | |
| R413, R407, R415, R416, R417, R418 | Output series resistors (`V_OUT`, `V_IN`, HS, LS, `I_OUT`, `I_IN`) | UNI-ROYAL 0603WAF1001T5E | C21190 | 1 kΩ 1 %, Basic; same part as power_stage R305 / R306 | |
| C415 | `I_OUT_SENSE` filter | Samsung CL10C220JB8NNNC | C1653 | 22 pF 50 V **C0G** 0603, Basic | |
| C411 | `V_OUT_SENSE` filter | Samsung CL10B102KB8NNNC | C1588 | 1 nF 50 V X7R 0603, Basic | |
| C404, C413, C414, C416 | `V_IN`, HS, LS and `I_IN` filters | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF 50 V X7R 0603, Basic | |
| D405, D406 | Clamps to `GNDA` / `+3V3` on `I_OUT_SENSE` and `I_IN_SENSE` | Nexperia BAT54S,215 | C47546 | Schottky series pair, 30 V, SOT-23: pin 1 (A) to `GNDA`, pin 2 (K) to `+3V3`, pin 3 to the signal (decision #11) | [LCSC](https://www.lcsc.com/product-detail/C47546.html) |
| C402, C407 | INA241 supply bypass on `+5V` | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF, one at each INA241's VS pin | |
| C401, C403, C406, C408 | TLV9061 supply bypass on `+3V3` | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF, one at each op-amp's V+ pin | |
| C409, C410 | INA241 REF1 bypass on `+3V3` | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF; C409 at U407, C410 at U402 | |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| `I_OUT_SENSE` | $V = 1.65\,V + 50\,mV/A \cdot I_L$; ±33 A full scale; 16 mA per count | mcu, firmware | CMPSS threshold in volts = 1.65 + 0.05 × (trip current in A). Zero varies ±50 mV board to board: calibrate at start-up with PWM off |
| `I_IN_SENSE` | Same transfer; 1.68–1.92 V over 20–200 % load; τ = 100 µs | mcu, firmware | Any ADC pin; no CMPSS |
| `V_OUT_SENSE` | $V_{OUT} / 6$; 2.00 V at 12 V; τ = 1 µs | mcu, firmware | CMPSS overvoltage comparator |
| `V_IN_SENSE` | $V_{IN} / 38.5$; 1.25 V at 48 V; 2.14 V at the 82.4 V clamp; τ = 100 µs | mcu, firmware | UVLO, OVLO and feedforward |
| `HS_TEMP_SENSE`, `LS_TEMP_SENSE` | 1.95 V at 25 °C, 2.40 V at 100 °C, ≈ 6 mV/°C; τ = 100 µs | mcu, firmware | Convert with $R_T = 10\,k\Omega \cdot v / (V_{3V3} - v)$, $v = V_{ADC} / 5.98$, then IEC 60751. Two pins (mcu.md: 23 and 13) |
| ADC acquisition window, `I_OUT_SENSE` | ≥ 290 ns (ACQPS ≥ 35 at 120 MHz) | firmware | Worst case from a 3.3 V difference on the sample capacitor |
| ADC acquisition, `V_OUT_SENSE` | Convert `V_OUT_SENSE` on an ADC that converts nothing else (ADCB channel 7, as suggested in mcu.md), or allow ≈ 4.2 µs | mcu, firmware | Otherwise up to 24 mV (≈ 145 mV of `V_OUT`) of error. Don't add the second temperature channel or `I_IN_SENSE` to ADCB |
| ADC acquisition, 100 nF channels | Datasheet minimum (75 ns) | firmware | |
| `iout` SOC timing | Delay the SOC ≈ 150 ns after the on-time (or off-time) midpoint | firmware | Compensates the INA241's lag when sampling average current |
| Cycle-by-cycle trip lag | ≈ 280 ns; peak overshoot ≈ 1.5–2 A above the trip | power_stage, firmware | Set the trip so trip + 2 A + 0.4 A (CMPSS offset) stays below 31 A $I_{sat}$ |
| Load on `+5V` | ≈ 5 mA | input_supply | The two INA241s |
| Load on `+3V3` | ≈ 2.8 mA | input_supply | Four TLV9061s and two RTD dividers |
| Load on `V_IN` / `V_OUT` | 66 µA / 13 µA | input_supply, power_stage | Divider currents |
| Clamp current into `+3V3` | Up to ≈ 2 mA per clamped channel (two) during a fault | input_supply | Far below `+3V3`'s load, so it can't pull the rail up |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- **RTDs at the FETs.** U404 and U405 are drawn here but belong beside Q301 (high side) and Q302 (low side). Q301's source is the switch node and its drain is `V_IN`, so put U404 on a GND island next to it, never on switch-node or `V_IN` copper. U405 can share Q302's source (GND) copper for thermal contact.
- **RTD returns.** 1 mV between an RTD's GND pin and its amplifier's ground is 1.2 °C. Run each RTD's pin 2 back to its amplifier's ground on its own trace, not through the power pour, and route the divider node beside it as a pair, away from the switch node.
- **Current-sense amplifiers near their shunts.** Put U402 next to R301 and U407 next to R201, so the millivolt Kelvin pairs stay short; send the amplified signal across the board instead. Bypass VS (C407, C402) and REF1 (C410, C409) at the pins.
- **Filters and clamps at the MCU.** The series resistors (R407, R413, R415–R418), filter capacitors (C404, C411, C413–C416) and clamps (D405, D406) go beside the MCU's ADC pins, on the `GNDA` side of the MCU sheet's net tie. Their ground pins are `GNDA`; the amplifiers' are `GND`.
- **`I_OUT_SENSE` is fast.** It feeds a CMPSS through only 22 pF: route it away from the switch node, the gate drive and the PWM traces, with ground beside it.
- **Divider nodes are high impedance** (125 kΩ and 19.5 kΩ). Keep R401 / R402 with U401 and R411 / R412 with U408, and the nodes short. Take R401's top from the output capacitors or J301, not from the shunt's copper, so the reading is the voltage the load sees.
- R411 has up to 80 V across it: keep the usual spacing from low-voltage copper around its `V_IN` end.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Current zeros | PWM off, 48 V applied; read `I_OUT_SENSE` and `I_IN_SENSE` codes at 25 °C and warm | Within 1.65 V ± 50 mV; record the zero calibration | | |
| 2 | Output-current gain | DC load at 0, 5, 10, 12.5 A; compare with a bench meter in series | Within ±1 % of reading above 5 A after zero calibration | | |
| 3 | `iout` dynamics | Current probe on L301 and scope on `I_OUT_SENSE` at 400 kHz, 50 % load | Ripple ≈ 94 % of the probe's; lag ≈ 150 ns; no ringing from the switch node | | |
| 4 | Cycle-by-cycle trip | Set the CMPSS threshold, then step the load past it | Peak inductor current within ≈ 2.5 A above the trip and below 31 A | | |
| 5 | Voltage gains | Sweep `V_IN` 36–53 V and `V_OUT` 0–13 V; compare with a DMM | Within ±2 % before calibration, ±0.3 % after | | |
| 6 | Overvoltage trip | Converter running at 12 V, no load: step the CMPSS threshold down toward 2.00 V. Don't back-drive J301 from a bench supply: the high-side GaN FET reverse-conducts and powers `V_IN` from the output | Trips as the threshold crosses the measured `V_OUT_SENSE` voltage, ± 20 mV | | |
| 7 | Temperature at ambient | Both channels against a thermocouple, board unpowered for an hour then switched on | Within ±2 °C after one-point calibration | | |
| 8 | Temperature under load | Thermal camera on Q301 / Q302 against both channels after 30 min at 150 W | Channels track the FET they sit beside | | |
| 9 | RTD ground offset | Step the load 0 → 12.5 A and read both temperatures within 1 s (before anything heats) | Step below 1 °C | | |
| 10 | Clamp and crosstalk | PWM off: drive `I_OUT_SENSE`'s amplifier output toward its `+5V` rail (inject a test current through R301, or lift R417's amplifier end to 5 V through 10 kΩ), and read every other channel | `I_OUT_SENSE` pin ≤ 3.6 V; other channels move less than 2 counts. The op-amp channels can't exceed `+3V3` (decision #11) | | |
| 11 | `V_OUT_SENSE` acquisition | Convert `V_OUT_SENSE` after a 0 V and after a 3.3 V conversion on the same ADC | Readings differ by less than 2 counts at the chosen ACQPS | | |
| 12 | `+5V` hand-over | Read all channels during input_supply test 9 (unplug J202 with 48 V applied) | No spurious overvoltage or overcurrent trip | | |

---

## Open questions

- **Schematic field fixes before layout** (checked against commit `808357c`):
  - (Fixed 2026-11-10: `LS_TEMP_SENSE` is now an output label, like `HS_TEMP_SENSE`.)
  - The contract lists test points on each sense signal; the sheet has none. Add one per output (after the RC) and a `GNDA` pad.
  - Gaps in the annotation: C405, C412, R410, R414 and D401–D404 are unused. Harmless; leave them rather than re-annotating.
  - (Resolved: labels renamed, #8; the hierarchy doc uses `I_SH_OUT_P` / `I_SH_OUT_N`; root-sheet pins added and wired (2026-11-10); the second temperature channel and `I_IN_SENSE` have MCU pins, mcu.md.)
- **`V_IN_SENSE` filter vs the fast input-overvoltage trip.** input_supply decision #24 puts `V_IN_SENSE` on a CMPSS comparator (CMPSS4, planned pin 18: mcu.md) and needs τ ≈ 1 µs on that path; R407 / C404 give 100 µs. Options: C404 → 1 nF like `V_OUT_SENSE` (feedforward and UVLO then oversample in firmware), or a second, lightly filtered tap for the comparator.
- **RTD measuring current.** 10 kΩ from `+3V3` gives 0.30 mA, a little above Vishay's 0.1–0.25 mA. Self-heating is only ≈ 0.07 K, so it is probably fine; 15 kΩ would bring it to 0.21 mA at ≈ 4.3 mV/°C.
- **Protection thresholds.** Set (specifications.md): overcurrent ≈ 22 A → 2.75 V; output overvoltage 13.2 V → 2.20 V; fast input overvoltage ≈ 55 V → 1.43 V. Still [TBD]: input UVLO (proposed 38 V on / 36 V off → 0.987 / 0.935 V), slow input OVLO (proposed 53 V → 1.38 V) and overtemperature.
- **INA241 REF on `+3V3`.** The zero tracks `+3V3`, not the ADC reference. Start-up calibration covers it; a reference voltage on REF1 would remove it if the zero drifts with temperature on the bench.
- **RTD part number.** "PTS1206M2B1K00P100" doesn't decode cleanly against Vishay's PTS datasheet. Confirm the tolerance class (F0.3 or F0.6) from the LCSC listing or Vishay.
- (Resolved by #9 and #10: RTD excitation no longer depends on `+5V`; the op-amps no longer see the `+5V` hand-over dip; the OPA192 cost question.)
