# Simulations

Computer models of the converter, used to design the control loop before the hardware exists and to check what the bench measures against what we expected.

| Script | What it models | Status |
|---|---|---|
| [voltage_mode_sim.py](voltage_mode_sim.py) | Voltage-mode control (firmware stage 2): plant, Type III controller, digital delay, soft-start and load step | First version |

Planned next: average current mode (stage 3), and an LTspice switching simulation to check ripple and the current limit.

---

## Quick start

```
cd simulations
pip install -r requirements.txt
python voltage_mode_sim.py          # prints a summary, saves plots to output/
python voltage_mode_sim.py --show   # also opens the plot windows
python voltage_mode_sim.py --help   # options
```

It runs in a few seconds. All parameters are at the top of the script, each with its source. Values marked **ASSUMED** are not decided yet; update them as the design firms up.

---

## What the script models

```
            error               duty                      VOUT
 reference ──►(−)──► controller ──► power stage ──────────────┬──► output
 (12 V)        ▲     (Type III,      (FETs, inductor,         │
               │      in the ISR)     capacitors)             │
               │                                              │
               └──── ADC reading (12-bit) ◄── divider ◄───────┘
                     taken once per PWM cycle; the new duty
                     takes effect one cycle later
```

- **Averaged model.** The switch node is replaced by its average over each PWM cycle (duty × 48 V). This keeps everything the control loop sees and removes the switching ripple, which makes the simulation fast. Real ripple (≈ 27 mV p-p) comes on top of these results.
- **Digital controller, run the way firmware will run it.** Sampled once per cycle, rounded to 12 ADC bits, a one-cycle delay before the new duty applies, duty clamped, and duty rounded to the PWM's resolution (with or without HRPWM).
- **Load** is an electronic load in constant-current mode, the hardest case for stability because it adds no damping.

---

## Reading the plots

### 1. The plant: the power stage on its own

![Plant Bode plot](output/01_plant_bode.png)

A **Bode plot** shows how strongly the output responds (top) and how late it responds (bottom) when the duty cycle wiggles at each frequency.

- The peak at **2.7 kHz** is the **LC resonance**: the inductor and output capacitors behave like a mass on a spring. Above it the gain falls quickly and the phase drops by about 180°. This is what makes a buck hard to control.
- Around **13.5 kHz** the polymer capacitor's ESR (its internal resistance) gives some phase back.

### 2. The full loop

![Loop gain Bode plot](output/02_loop_bode.png)

The controller (orange) is shaped so that the **loop gain** (blue = controller × plant × delay) does two things:

- It is large at low frequencies, so the output sits exactly at 12 V.
- It **crosses 0 dB at 20 kHz**. This crossover frequency is how fast the loop reacts.

The bottom panel shows **phase margin**: at crossover, how far the phase is from −180°, the point where the loop would oscillate. The current design has **60°**, inside the usual 45–60° target. **Gain margin** (how much the gain could rise before oscillation) is **6.9 dB**, just above the usual 6 dB target.

The dashed purple line shows what happens if the control ISR ran every second PWM cycle instead of every cycle. The extra delay costs phase, and the phase margin drops to about 50°.

### 3. Soft-start and a load step

![Time response](output/03_time_response.png)

- **0–2 ms:** the firmware ramps the reference from 0 to 12 V (soft-start), and the output follows it closely. The inductor carries about 3 A even with no load, just to charge the 509 µF of output capacitance.
- **3 ms:** a light load (1.25 A) is connected.
- **5 ms:** the load jumps to 11.25 A (10 % → 90 % of full load). The output dips, the controller raises the duty cycle, and the inductor current climbs to catch up.
- **7 ms:** the load drops back, and the output briefly overshoots.

![Load step zoom](output/03b_load_step_zoom.png)

The zoom shows the dip in detail: **about 365 mV**, back inside ±60 mV within **about 50 µs**.

### 4. PWM resolution

![PWM resolution](output/04_pwm_resolution.png)

The duty cycle can only move in steps. Without HRPWM, one step is 1/300 of a period, which moves the output by 160 mV. The loop can't land on exactly the right duty, so it keeps jumping between neighboring steps (red). HRPWM makes the steps about 50 times finer (blue). In this model the output filter smooths most of the jumping, so the difference is smaller than 160 mV suggests: about 8 mV p-p of wobble without HRPWM against 4 mV with it. The remaining wobble with HRPWM comes from the 12-bit ADC's resolution.

---

## What we've learned so far

These follow from the current parameters, including the assumed ones. They are worth checking as the design firms up.

1. **A 25 kHz crossover is too aggressive with our digital delay.** From ADC sample to new duty there are about 3.75 µs of delay. That limits the gain margin to about 5 dB at 25 kHz. At 20 kHz, the loop has 60° phase margin and 6.9 dB gain margin. `power_stage.md` assumes about 25 kHz.
2. **The load-step dip is set mostly by the output capacitors, not by the loop.** Right after a 10 A step, the current comes from the capacitors before the controller can respond. The polymer's 25 mΩ ESR alone accounts for about 250 mV (10 A × 25 mΩ). Changing the loop speed barely helps: a 10 kHz crossover gives a dip of about 394 mV and 30 kHz about 356 mV. A 10 mΩ polymer brings the dip to about 264 mV, though the controller then needs retuning (its phase margin falls to 38°). The estimate in `power_stage.md` (≈ 125 mV) leaves out the ESR. The load-transient target in `specifications.md` is still [TBD].
3. **The inductor current overshoots during a load step.** On the 10 A step the average inductor current peaks at about 16.8 A, about 18.5 A instantaneous once ripple is added. The cycle-by-cycle overcurrent threshold has to leave room for this, or it will trip on a normal load step.
4. **Run the control ISR every cycle if possible.** Running it every second cycle costs about 10° of phase margin at 20 kHz with the same controller.
5. **The inductor current goes negative (about −4 A) when the load is released.** This is the synchronous buck briefly returning energy to the input, as discussed for bidirectional operation. The bench supply must tolerate it, or the input bus rises.

---

## Things to try

Change a value at the top of the script (or use an option), rerun, and compare.

| Try | How | What to look for |
|---|---|---|
| Faster or slower loop | `--fc 10` or `--fc 30` (kHz) | Phase and gain margin change a lot; the load-step dip barely changes |
| Slower ISR | `--every 2` | Less phase margin, more ringing after the load step |
| No HRPWM | `--no-hrpwm` | The duty keeps jumping between steps (plot 4) |
| Lower-ESR polymer | `ESR_POLY = 10e-3` | Smaller dip, but less phase margin: the controller needs retuning |
| Move the controller zeros | `FZ1`, `FZ2` | Placing them lower adds phase margin but slows the low-frequency response |
| Resistive load | `LOAD_R = 0.96` (full load) | More damping at the resonance, so the peak in plot 1 shrinks |
| Longer soft-start | `SOFTSTART_TIME = 5e-3` | Lower capacitor-charging current at start-up |

---

## Assumptions and limits

| Item | Value used | Replace with |
|---|---|---|
| Ceramic bank ESR | 0.5 mΩ total | Datasheet ESR at ~100 kHz |
| PCB resistance | 1 mΩ | Estimate after layout |
| VOUT divider | 0.2 (16.5 V full scale) | Sensing sheet's divider |
| Sense-line RC filter | Not modeled | Sensing sheet's filter: it adds delay and costs phase |
| Hot R<sub>DS(on)</sub> | 1.5 × 3.3 mΩ | Datasheet curve at the expected temperature |

- **Averaged model:** no switching ripple, and no behavior within a cycle. That needs a switching simulation (LTspice or PLECS).
- **Input voltage is fixed at 48 V.** A real supply has its own impedance and ripple.
- **Voltage mode only.** Average current mode, with its inner current loop, is the next script.
- **Coefficients:** the summary prints the digital coefficients as u[n] = b0·e[n] + … − a1·u[n−1] − …. The C2000 Digital Control Library may use a different sign convention, so check it before copying them into firmware.

A simulation is only as good as its parameters. Once the board runs, measure the real loop with TI's SFRA, compare it with plot 2, and update the model until the two agree.
