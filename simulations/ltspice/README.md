# LTspice switching simulation: power stage

A switching-level model of `sheets/power_stage.kicad_sch`: both IGC033S10S1 FETs (Infineon's own SPICE model), the LM5113-Q1 gate drive, bootstrap, input and output capacitor banks, L301 and R301. It complements the averaged scripts one folder up: those design the control loop, this one shows what happens inside a cycle (edges, ringing, gate voltages, losses, ripple).

| File | What it is |
|---|---|
| `buck_power_stage.asc` | The LTspice schematic. Open this one |
| `buck_power_stage.cir` | The same circuit as a plain netlist (File > Open, then Run), kept as a fallback |
| `LM5113_BEHAV.asy`, `lm5113_behavioral.lib` | Symbol and behavioural model of the gate driver, written for this project from the TI datasheet. **Not a TI model** |
| `infineon_coolgan_100v_g3.lib` | Infineon's "CoolGaN Transistors 100 V G3 - Spice" library, version 1202 (2024-12-12). **Not in git:** see below |
| `output/ngspice_*.png` | Waveforms from the ngspice cross-check described under *Status* |

## Setup

1. Sign in at infineon.com, open the [IGC033S10S1 product page](https://www.infineon.com/part/IGC033S10S1), and download **CoolGaN Transistors 100 V G3 - Spice** (Design resources > Simulation models). The download needs a myInfineon account, which is why the file is git-ignored instead of committed.
2. Unzip it and save `CoolGaN Transistors 100 V G3 - Spice.lib` in this folder as `infineon_coolgan_100v_g3.lib`. Do not edit it.
3. Open `buck_power_stage.asc` in LTspice and run. Results of the `.meas` lines are in View > SPICE Error Log.

The FETs use the `IGC033S10S1_L1` subcircuit (drain, gate, source; junction temperature = the simulation temperature, set by `.temp 80`).

## What it simulates

48 V in, 12 V out, 12.5 A constant-current load, 400 kHz, open loop at a fixed duty cycle. There is no controller: V3 and V4 stand in for the MCU's ePWM outputs (3.3 V logic with a commanded dead time `tdt`).

The run starts in steady state from initial conditions (`uic`): output capacitors at 12 V, L301 at its valley current, bootstrap capacitor charged. It simulates `Ncyc` = 10 cycles and saves and measures the last `Nmeas` = 4.

`D` is trimmed (0.2567) so the average inductor current holds 12.5 A at the default settings. If you change the load, dead time, frequency or input voltage, check `IL_avg` in the log: if it has moved away from `Iout`, the output is drifting, so nudge `D` (about 0.001 per 50 mV) and rerun.

### Parameters (the `.param` lines on the schematic)

| Parameter | Default | Meaning |
|---|---|---|
| `Vin`, `Iout`, `fsw`, `D` | 48, 12.5, 400k, 0.2567 | Operating point |
| `tdt` | 10n | Dead time commanded at the MCU, each edge. The input filters and driver add about 8 ns on top |
| `Rgon` | 2 | R305, high-side turn-on resistor (verification test 6 sweeps 0, 2, 4.7) |
| `Lloop` | 1n | Power-loop inductance, HF capacitors to Q301 drain. **ASSUMED** until layout |
| `Lcs` | 0.15n | Common-source inductance at each FET (no Kelvin source pin). **ASSUMED** |
| `Lgate` | 2n | Gate-loop inductance, driver to gate. **ASSUMED** |
| `Lbus`, `Lsrc` | 0.6n, 1u | Bulk-to-HF-capacitor inductance; bench leads. **ASSUMED** |
| `Cbulk`, `Chf`, `Coc` | 2.65u, 42n, 5.7u | Effective capacitance per part after DC bias (10 uF at 48 V, 100 nF at 48 V, 22 uF at 12 V), from `power_stage.md` |

To sweep one, add a directive such as `.step param Rgon list 0 2 4.7`.

### Mapping to the schematic

Reference designators and net names match the KiCad sheet. Paralleled parts are lumped: C301 = C301 to C303, C304 = C304 to C307, C308 = C308 + C309, C316 = C316 + C317. C203 (input_supply sheet) is included because it shares `V_IN`. Parts named `L_...` and `R_5V` are parasitics or source impedances, not components. Left out: the DNP snubber R303/C310, LED301/R302, test points and net ties.

## Results at the defaults

From the ngspice cross-check (see *Status*); LTspice should land close to these.

| Quantity | Simulated | Design note (`power_stage.md`) |
|---|---|---|
| Q301 loss | 1.54 W | 1.46 W |
| Q302 loss | 0.83 W | 0.83 W |
| Loss from the HF capacitors to `V_OUT` (FETs, L301 DCR, R301) | 2.85 W | — |
| Efficiency of that section, including 58 mW gate drive | 98.1 % | 97.9 % for the stage, which also counts core and capacitor losses |
| Inductor ripple | 3.33 A p-p | 3.3 A |
| Output ripple | 26 mV p-p, including ESL spikes | about 19 mV |
| Ripple at the HF capacitors / at `V_IN` | 2.1 V / 1.05 V p-p | 1 V target at the FETs |
| Switch-node peak / Q302 Vds peak | 61 V / 63 V | 100 V rating |
| Switch-node dv/dt, rising / falling | 21 / 9 V/ns | about 10 V/ns estimated for turn-on |
| Q301 Vgs peak | 5.25 V | 5.5 V recommended limit |
| Q302 gate bump while held off | 1.4 V | 0.15 V estimate; 1.2 V minimum threshold at 25 C |
| Bootstrap voltage (HB to SW) | 5.1 to 5.2 V | — |
| Time the switch node spends below -1 V | 34 ns per cycle | 20 ns assumed |

Several of these depend directly on the assumed parasitics, so treat them as "what happens if the layout achieves these values", not as predictions: the switch-node peak and ring frequency (`Lloop`), the Q302 gate bump (`Lcs`, `Lgate`), and the ripple at the HF capacitors (`Lbus`). Replace the assumptions with extracted or measured values after layout, then with the bench results from verification tests 1, 2 and 12.

## Findings so far

### Switch-node ringing

At Q301 turn-on the switch node overshoots to about 61 V and rings at roughly 180 MHz (period about 5.5 ns). The loop inductance (1.3 nH in total with the defaults) resonates with Q302's output capacitance; the ring frequency implies about 600 pF at the switch node and a characteristic impedance near 1.5 ohm. The tank is excited because Q301's drain current must both take over the load current and charge Q302's output capacitance: it peaks near 30 A against a 10.8 A valley current.

The first peak is a fair estimate for the assumed inductance. The slow decay is not: the only damping in the model is a few milliohms of on-resistance and capacitor ESR, so a real board will settle in far fewer cycles.

Every stress stays inside its rating at the defaults:

| Stress | Simulated | Limit |
|---|---|---|
| Q302 drain-source peak | 63 V | 100 V (FET) |
| Switch-node peak at the driver's HS pin | 61 V | 93 V absolute maximum (LM5113 datasheet SNVS725I; check the -Q1 table) |
| Switch-node slew rate | 21 V/ns | 50 V/ns (driver) |
| Q301 gate peak | 5.25 V | 5.5 V recommended |
| Switch node below ground (dead time) | -4.0 V | -5 V absolute minimum on HS |
| Q302 gate bump while held off | 1.4 V | 1.2 V minimum threshold at 25 C (a screening line, not a guaranteed limit) |

The two with thin margin are the negative switch-node excursion and the low-side gate bump.

### Low-side gate bump: what moves it

One change at a time from the defaults. Three-cycle ngspice runs with the typical-threshold FET model, so read these as a ranking, not as predictions.

| Change | Q302 gate bump | Switch-node peak | Turn-on dv/dt | Q301 loss |
|---|---|---|---|---|
| Defaults (`Lloop` 1 nH, `Lcs` 0.15 nH, `Lgate` 2 nH, `Rgon` 2 ohm) | 1.40 V | 61 V | 21 V/ns | 1.54 W |
| `Lcs` 0.05 nH | 0.75 V | 78 V | 29 V/ns | 1.32 W |
| `Lcs` 0.3 nH | 2.54 V | 61 V | 15 V/ns | 1.75 W |
| `Rgon` 4.7 ohm | 1.26 V | 59 V | 17 V/ns | 1.70 W |
| `Rgon` 10 ohm | 0.95 V | 53 V | 14 V/ns | 2.04 W |
| `Lloop` 0.4 nH | 1.32 V | 54 V | 18 V/ns | 1.64 W |
| `Lgate` 1 nH | 1.91 V | 64 V | 20 V/ns | 1.55 W |
| `Lgate` 0.5 nH | 2.10 V | 65 V | 19 V/ns | 1.55 W |
| `Lloop` 0.4 nH, `Lcs` 0.05 nH, `Lgate` 1 nH | 0.94 V | 56 V | 27 V/ns | 1.51 W |
| Same, with `Rgon` 4.7 ohm | 0.70 V | 51 V | 20 V/ns | 1.70 W |

What this suggests for layout and bring-up:

1. **Common-source inductance dominates.** In this model each 0.1 nH of copper shared between the power path and the gate-drive return is worth nearly a volt of bump. Return U301's VSS to Q302's source pad beside the gate pin on its own trace or via, and do the same for the HS pin and Q301's source.
2. **A tight power loop** (decision #19) helps the bump only a little, but it is what holds the switch-node peak down once the common-source inductance is small and the edges get faster.
3. **R305 is a bench trim, not the cure.** 4.7 ohm buys about 0.15 V for 0.16 W; it takes 10 ohm to get under 1 V by resistor alone, at half a watt.
4. **Shortening the gate loop on its own made the bump larger here.** A stiffer gate connection pins the gate to the driver's ground while the source bounces on the shared inductance. Keep the gate loop short, but together with the dedicated source return.

The design note's 0.15 V estimate counts only Miller current through the pull-down resistance, which is why it is so much lower. Verification test 12 measures the real figure.

## Assumptions

Everything the model takes on trust, grouped by where it enters. Items marked **A** are assumptions with no datasheet or measurement behind them; the rest are datasheet typicals or values taken from the design notes.

### Operating point and method

| Item | Value | Basis |
|---|---|---|
| Control | Open loop, fixed duty | No controller, sensing or current limit modelled |
| Load | Ideal 12.5 A current sink | Matches the constant-current e-load convention of `voltage_mode_sim.py` |
| Duty cycle `D` | 0.2567 | Trimmed by hand so the average inductor current holds 12.5 A at the defaults |
| Start-up | `uic`: C308/C316 at 12 V, input capacitors at 48 V, C313 at 4.5 V, VDD capacitors at 5 V, L301 at valley current + 0.15 A, L_SRC at `Iout*12/Vin` | Chosen to start near steady state. The + 0.15 A offsets the current lost in the first tens of nanoseconds while the driver model initialises. **A** |
| Measurement window | Last 4 of 10 cycles | Enough for the switching waveforms; the 2.6 kHz output LC and the input LC are not settled to better than the initial conditions |
| Temperature | 80 C for every device (`.temp 80`) | About the hot-FET estimate in `power_stage.md`. Also applies to the diodes, which is not physical. **A** |
| Efficiency figure | Power into `V_OUT` over (power into the FET cell at `VIN_HF` + driver power) | Excludes input-capacitor ESR, inductor core loss, and everything upstream of the HF capacitors |

### FETs (Q301, Q302)

| Item | Value | Basis |
|---|---|---|
| Model | `IGC033S10S1_L1`, Infineon library version 1202, unmodified | Vendor model |
| Spread | `dVth=0`, `dRdson=0`: typical threshold and on-resistance | Library defaults. Worst-case threshold is **not** covered |
| Thermal | None: both FETs fixed at the simulation temperature | L1 model. No self-heating, no difference between high and low side |
| Package inductance | The library's own values (about 6 pH drain and source, 66 pH gate) | Vendor model; the external parasitics below are added on top |

### Layout parasitics

None of these is extracted from a layout. All **A**.

| Item | Value | What it represents |
|---|---|---|
| `Lloop` | 1 nH | HF capacitors (C304 to C307) through Q301 and Q302 and back, including the capacitors' own ESL. All lumped at Q301's drain |
| `Lcs` | 0.15 nH per FET | Source copper shared by the power current and the gate-drive return |
| `Lgate` | 2 nH per FET | Driver output to gate pin and back |
| `Lbus` | 0.6 nH | Between the bulk ceramics and the HF capacitors |
| `Lsrc` | 1 uH, 20 mohm | Bench leads and supply, as in `input_hotplug_sim.py` |
| Coupling | None | No mutual inductance between the power loop and the gate loops |
| Stray capacitance | None | No switch-node-to-ground copper capacitance, no heatsink capacitance |
| Resistance | None beyond the parts | No trace or via resistance, no skin effect, no dielectric loss: ringing is under-damped |
| Ground | Single ideal node | Q302's source inductance returns to it; driver VSS and all capacitor returns sit on it |

### Capacitors

All are fixed linear values with series R and L. No voltage, frequency or temperature dependence beyond the fixed derating.

| Part | Modelled as | Basis |
|---|---|---|
| C301 to C303 | One 7.95 uF, 1 mohm, 0.25 nH | 2.65 uF each at 48 V: typical bias readback in `power_stage.md`, not a guaranteed minimum. ESR and ESL **A** |
| C304 to C307 | One 168 nF, 5 mohm | 42 nF each at 48 V, same source. ESR **A**; ESL is inside `Lloop` |
| C203 | 100 uF, 0.32 ohm, no ESL | ESR is the assumed figure from `input_hotplug_sim.py`. **A** |
| C308, C309 | One 11.4 uF, 2.5 mohm, 0.3 nH | 5.7 uF each at 12 V (26 % retained, design note). ESR and ESL **A** |
| C316, C317 | One 540 uF, 5 mohm, 1.5 nH | Nominal capacitance; ESR at the catalog maximum of 10 mohm each; ESL of 3 nH each **A** |
| C313 | 100 nF | Nominal, no bias derating at 5 V. **A** |
| C311, C312 | 100 nF; 4 uF with 5 mohm | C312 at 40 % of 10 uF, the same assumption as the design note. ESR **A** |
| C314, C315 | 22 pF | Nominal (C0G) |

### Magnetics and sense resistor

| Part | Modelled as | Basis |
|---|---|---|
| L301 | 6.8 uH linear, 2.1 mohm | Nominal inductance and typical DCR. No saturation or inductance sag with current, no core loss, no winding capacitance |
| R301 | Ideal 1 mohm | No inductance, no Kelvin network, no sense amplifier load |

### Gate driver (U301)

A behavioural model written for this project from the LM5113 datasheet (SNVS725I), **not** the LM5113-Q1 datasheet and not a TI model. All values are 25 C typicals and do not change with temperature.

| Item | Value | Basis |
|---|---|---|
| Input thresholds | 2.06 V rising, 1.66 V falling | Datasheet |
| Input pull-down, capacitance | 200 kohm, 2 pF | Datasheet; capacitance **A** |
| Propagation delay | 28 ns turn-on, 26.5 ns turn-off, both channels identical | Datasheet. Channel mismatch `tmatch` = 0 (1.5 ns typical, 8 ns maximum) |
| Output resistance | 2.1 ohm pull-up, 0.6 ohm pull-down | Datasheet |
| Output current limit | 1.2 A source, 5 A sink, tanh-shaped saturation | Peak currents from the datasheet; the shape is **A** |
| Output transition | Pull-up and pull-down cross-fade with a 0.7 ns time constant; 20 pF on each output pin | **A**; chosen to give roughly the datasheet rise time into 1 nF |
| UVLO | 3.8 V on VDD, 3.2 V on HB to HS, 0.2 V hysteresis | Datasheet |
| Supply current | 1.6 mA on VDD, 1.2 mA on HB, constant | Datasheet 500 kHz figures scaled to 400 kHz. **A** |
| Internal bootstrap diode | Fitted to 0.45 V at 100 uA, 0.90 V at 100 mA, 1.85 ohm; no reverse recovery | Datasheet points |
| 5.2 V bootstrap clamp | The internal diode path stops charging once HB to HS reaches 5.2 V (linear over the last 50 mV) | The datasheet states the clamp level but not the mechanism. **A**. The 5.1 to 5.2 V bootstrap result depends on this |
| Not modelled | Minimum pulse width, level-shifter dv/dt immunity, behaviour with HS below ground, package inductance | |

### Bootstrap, supply and PWM

| Item | Value | Basis |
|---|---|---|
| D301 | Generic Schottky: `Is` 1.2 uA, `N` 1.1, `Rs` 1.8 ohm, `Cjo` 10 pF, no recovery charge | Rough fit to BAT46 figures, not a vendor model. **A** |
| R304, R305, R306, R307 | 100 ohm, 2 ohm, 1 kohm, 1 kohm, ideal | Schematic values |
| `+5V` | Ideal 5.0 V behind 50 mohm | **A**; the aux buck and its ripple are not modelled |
| PWM sources | Ideal 0 to 3.3 V, 2 ns edges, zero source impedance, no jitter | Stand in for the MCU and the enable sheet's gates, whose delay and output impedance are not modelled. **A** |
| Dead time `tdt` | 10 ns commanded, each edge | Chosen to land near the design note's dead-time assumption once the filter and driver delays are added. **A** |

### Left out entirely

The DNP snubber (R303, C310), LED301 and R302, test points and net ties, the sensing sheet's loads on `SW_NODE`, `V_OUT` and the shunt, and everything on the input_supply sheet except C203 (fuse, Q201, R201, TVS).

### Cross-check method

The results and plots come from ngspice 42, not LTspice. For that run only, two lines of a private copy of the Infineon library were changed for numerical reasons: the unused thermal power source `G_TH` was removed, and the 1 uohm resistor that ties the L1 model's temperature node was raised to 1 ohm. Neither changes the electrical behaviour of the L1 model (its temperature node is fixed by a voltage source). Capacitor and inductor series R and L were expanded into separate elements, since ngspice has no `Rser`/`Lser`. The library LTspice uses is Infineon's file, untouched.

## Limits

The short version of the assumptions above:

- **The driver is behavioural.** It reproduces the datasheet's typical thresholds, delays (28 ns on, 26.5 ns off), 2.1 / 0.6 ohm outputs with 1.2 / 5 A saturation, UVLO, and the internal bootstrap diode that stops charging at 5.2 V. It has no temperature dependence, no minimum pulse width, and nothing on dv/dt immunity. The model file lists what is ASSUMED.
- **D301 is a generic Schottky fit**, not a vendor model.
- **L301 is linear**, with DCR only: no saturation, core loss or winding capacitance.
- **Capacitors are fixed values** with series R and L. Their ESR and ESL are typical figures for the package sizes, ASSUMED.
- **No thermal feedback.** The FETs sit at 80 C throughout (`.temp 80`). Infineon's `_L3` subcircuits add a thermal network if self-heating is wanted.
- **Ringing is under-damped** compared with a real board, because skin effect and dielectric loss are not modelled.
- **Open loop only.** Load steps and the current limit need the controller added.

## Status

The Infineon library and the driver model both parse and run in ngspice 42 (PSpice/LTspice compatibility mode), and the results table and the plots in `output/` come from that run. The `.asc` was generated by script and its connectivity checked against the netlist that was simulated. **It has not yet been opened in LTspice itself:** the first run there is still to do. If LTspice reports a problem with the schematic, `buck_power_stage.cir` is the same circuit as text.

If LTspice stalls at a switching edge, try Tools > Control Panel > SPICE: solver *Alternate*, integration *Gear*.
