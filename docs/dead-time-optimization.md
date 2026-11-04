# Dead-Time and Frequency Optimization — Proposal

**Owner:** Reza Rahimzadeh · **Status:** Proposal (after firmware step 8) · **Last updated:** 2026-11-04

A firmware feature that sets the two dead times (and, in STANDBY, the switching frequency) from the operating point instead of using one fixed worst-case value. Three methods are compared on the bench: a fixed dead time, a schedule learned from sweep data (the "edge AI" part), and the learned schedule refined online by duty-cycle minimization.

Nothing here changes the schematic. It extends the step 10 frequency sweep in [firmware-requirements.md](firmware-requirements.md) and adds firmware after voltage-mode control works.

---

## Why it matters on this board

The IGC033S10S1 has no body diode. During dead time the low-side FET conducts in reverse at $V_{SD} \approx 2.4$ V typ, about three times a Si body diode. [design/power_stage.md](design/power_stage.md) already budgets 0.24 W for this at 10 ns per edge, out of about 2.3 W total FET loss.

The best dead time is not a constant. It depends on load current, and the two edges behave differently:

| Edge | What happens during dead time | Too short | Too long | Optimum |
|---|---|---|---|---|
| High-side off → low-side on | Inductor current swings the switch node from $V_{in}$ to 0 (low side turns on at zero voltage) | Low side turns on before the node has fallen: partial hard switching | Extra reverse conduction at 2.4 V | ≈ time for the node to finish falling, which grows as load drops |
| Low-side off → high-side on (CCM, current positive) | Node sits at $-V_{SD}$; nothing useful happens | Shoot-through | Extra reverse conduction | Shortest safe value |
| Low-side off → high-side on (light load, valley current negative) | Negative current charges the node toward $V_{in}$ | High side hard-switches | Node rings back down; reverse conduction | ≈ time for the node to reach $V_{in}$: high side gets zero-voltage turn-on |

### First-order numbers

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| Valley current goes negative below | $I_{out} < \Delta I_L / 2$ | 3.3 A / 2 ≈ 1.65 A at 400 kHz (2.2 A at 300 kHz, 1.3 A at 500 kHz) | $\Delta I_L$ from power_stage.md. Below this, high-side ZVS is possible with the right dead time |
| Charge to swing the switch node | $Q_{node} \approx 2 Q_{oss}$ | ≈ 86 nC | $Q_{oss}$ 43 nC typ at 50 V (datasheet), one FET charging and one discharging |
| Node fall time, high-side off → low-side on | $t \approx Q_{node} / I_{peak}$, $I_{peak} = I_{out} + \Delta I_L/2$ | 14.2 A: ≈ 6 ns · 5 A: ≈ 13 ns · 2 A: ≈ 23 ns | Ignores channel current during the high-side turn-off, so it is an upper-bound estimate. Add the ≈ 6.5 ns input-filter mismatch from power_stage.md decision #5 |
| Dead-time loss at fixed 10 ns per edge | $V_{SD} I_{out} \cdot 2 t_{dt} \cdot f_{sw}$ | ≈ 0.24 W at 12.5 A, 400 kHz | From power_stage.md. Halving the effective dead time saves ≈ 0.12 W at full load |

So the high-side-off edge wants about 6 ns at full load but about 20 ns or more at light load. A fixed value is wrong at one end or the other. Light-load efficiency is where the gain is largest, because there the fixed losses dominate.

---

## Methods to compare

| # | Method | How it works | Strength | Weakness |
|---|---|---|---|---|
| A | Fixed (baseline) | One dead time per edge, set from worst-case measurement plus margin | Simple, safe | Leaves efficiency on the table across the load range |
| B | Learned schedule | Small regression (start with a quadratic fit; try a small MLP, e.g. 3→8→3) trained offline on sweep data. Inputs: $I_{out}$, $V_{in}$, temperature. Outputs: $t_{dt,r}$, $t_{dt,f}$, recommended $f_{sw}$. Weights stored as a `const` array; evaluated in the background loop | Deterministic, no perturbation, runs in microseconds | Only as good as the training data; does not track part-to-part variation |
| C | Learned + online refinement | B gives the starting point. Duty-cycle minimization nudges each dead time within a small window: at fixed $V_{out}$ and $I_{out}$, lower loss needs less duty, so keep the step that reduces the averaged duty command | Tracks variation, temperature and aging | Slow to converge; needs heavy averaging because duty differences are tiny |

Method C follows Yousefzadeh and Maksimović, "Sensorless Optimization of Dead Times in DC–DC Converters With Synchronous Rectifiers," IEEE Trans. Power Electronics, 2006.

---

## Safety rules

These are firm requirements, in addition to section 6 of [firmware-requirements.md](firmware-requirements.md).

1. **Hard dead-time floor.** Measured at the gate pins (not the commanded value) during bring-up, plus margin, and stored in the configuration header. No method can command less.
2. **Hard ceiling and window.** Each method outputs inside [floor, ceiling]. Method C moves only within ± a small window around the method B value.
3. **Clamp and rate-limit.** One small step per update; no jumps.
4. **Switching frequency changes only in STANDBY**, as already required.
5. **Advisory mode first.** Methods B and C run and report their recommendation over SCI for a full test campaign before they are allowed to change the ePWM.
6. **Outside the control ISR.** All model evaluation and averaging run in the background loop. The ISR only applies an already-validated dead-band value.
7. **Never touches protections.** No method reads or writes CMPSS thresholds, trip-zone settings or the state machine.

---

## Data collection (extends firmware step 10)

Run in open loop or voltage mode, with a hardware team member present, from a current-limited supply.

| Variable | Points |
|---|---|
| Load current | 0.5, 1, 1.5, 2, 3, 5, 8, 12.5 A (dense below the 1.65 A ZVS boundary) |
| Input voltage | 36, 48, 54 V |
| Switching frequency | 300, 400, 500 kHz |
| Rising-edge dead time | floor to ceiling, about 5 steps |
| Falling-edge dead time | floor to ceiling, about 5 steps |

Record for every point: input and output voltage and current from bench instruments (the board has no input-current sense), board telemetry (duty command, `ISENSE`, `VOUT_SENSE`, `VIN_SENSE`, `TEMP_SENSE`), and a switch-node capture at selected points. Probe the switch node with a short ground spring, not a long ground lead.

The full grid is large. Start with a coarse grid at 48 V and 400 kHz, then refine around the optimum. Store the data in `test/dead-time-sweep/` as CSV with one row per operating point.

**Results to report:** efficiency vs load for methods A, B and C on one plot, and the optimal dead time vs load against the first-order estimate above.

---

## Firmware hooks needed

- High-resolution dead band in the ePWM/HRPWM. Confirm in SysConfig that the chosen ePWM channel supports it on the F280039C; 10 ns steps are too coarse.
- Configuration header entries: dead-time floor, ceiling, refinement window, step size, update rate, and the model coefficients.
- Status frame fields: applied dead times, recommended dead times, method in use, and averaged duty.
- Serial commands: `dt mode fixed|sched|refine`, `dt advise on|off`. Rejected unless allowed in the current state.

---

## Open questions

- $V_{SD}$ at the actual off-state gate voltage and temperature: confirm from the IGC033S10S1 datasheet curves.
- How well the duty proxy resolves: is the duty change from one dead-time step visible above ADC noise with reasonable averaging?
- Whether bench instruments are accurate enough to see a 0.1 W difference at 150 W (about 0.07 % efficiency). Light-load points will show the effect more clearly.
- Whether method C is worth its complexity over method B on this board.
