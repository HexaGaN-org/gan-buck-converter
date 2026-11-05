# Edge AI Dead-Time Optimizer — Proposal

**Owner:** Reza Rahimzadeh · **Status:** Proposal (after firmware step 8) · **Last updated:** 2026-11-04

A small neural network running on the F280039C that predicts the converter's power loss at any operating point, then picks the dead times (and, in STANDBY, the switching frequency) that the model says will lose the least. It is trained on our own bench measurements, runs entirely on the board with no laptop in the loop, and is benchmarked against a fixed dead time and a classical model-free optimizer.

Nothing here changes the schematic. It extends the step 10 frequency sweep in [firmware-requirements.md](firmware-requirements.md) and adds firmware after voltage-mode control works.

---

## 1. The problem the model solves

The IGC033S10S1 has no body diode. During dead time the low-side FET conducts in reverse at $V_{SD} \approx 2.4$ V typ, about three times a Si body diode. [design/power_stage.md](../design/power_stage.md) budgets 0.24 W for this at 10 ns per edge, out of about 2.3 W total FET loss.

The best dead time depends on the operating point, and the two edges behave differently:

| Edge | What happens during dead time | Too short | Too long | Optimum |
|---|---|---|---|---|
| High-side off → low-side on | Inductor current swings the switch node from $V_{in}$ to 0 (low side turns on at zero voltage) | Low side turns on before the node has fallen: partial hard switching | Extra reverse conduction at 2.4 V | ≈ time for the node to finish falling, which grows as load drops |
| Low-side off → high-side on (CCM, current positive) | Node sits at $-V_{SD}$; nothing useful happens | Shoot-through | Extra reverse conduction | Shortest safe value |
| Low-side off → high-side on (light load, valley current negative) | Negative current charges the node toward $V_{in}$ | High side hard-switches | Node rings back down; reverse conduction | ≈ time for the node to reach $V_{in}$: high side gets zero-voltage turn-on |

### First-order physics

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| Valley current goes negative below | $I_{out} < \Delta I_L / 2$ | 3.3 A / 2 ≈ 1.65 A at 400 kHz (2.2 A at 300 kHz, 1.3 A at 500 kHz) | $\Delta I_L$ from power_stage.md. Below this, high-side ZVS is possible with the right dead time |
| Charge to swing the switch node | $Q_{node} \approx 2 Q_{oss}$ | ≈ 86 nC | $Q_{oss}$ 43 nC typ at 50 V (datasheet), one FET charging and one discharging |
| Node fall time, high-side off → low-side on | $t \approx Q_{node} / I_{peak}$, $I_{peak} = I_{out} + \Delta I_L/2$ | 14.2 A: ≈ 6 ns · 5 A: ≈ 13 ns · 2 A: ≈ 23 ns | Upper-bound estimate (ignores channel current during turn-off). Add the ≈ 6.5 ns input-filter mismatch from power_stage.md decision #5 |
| Dead-time loss at fixed 10 ns per edge | $V_{SD} I_{out} \cdot 2 t_{dt} \cdot f_{sw}$ | ≈ 0.24 W at 12.5 A, 400 kHz | From power_stage.md |

The optimum moves by a factor of four across the load range, and real behavior (C_oss nonlinearity, driver delays, layout parasitics, temperature) is hard to capture analytically. That makes it a good fit for a model learned from measurements.

---

## 2. Model design

### Approach: learned loss surrogate + on-device search

Rather than training the network to output dead times directly, it learns the **loss surface**, and the firmware searches it.

$$\hat{P}_{loss} = f_\theta(I_{out}, V_{in}, T, f_{sw}, t_{dt,r}, t_{dt,f})$$

Every sweep point is a training sample, labeled with its measured loss. A direct "optimal dead time" regression would get only one label per operating point. The surrogate also gives a predicted loss to show on the dashboard, and the same model chooses $f_{sw}$ by comparing predicted loss across frequencies.

### Inputs and features

| Feature | Source | Why |
|---|---|---|
| $I_{out}$ | `ISENSE` | Sets the node transition time; strongest input |
| $V_{in}$ | `VIN_SENSE` | Sets $Q_{oss}$ swing and ripple |
| $T$ | `TEMP_SENSE` | $R_{DS(on)}$ and $V_{SD}$ shift with temperature |
| $f_{sw}$ | Firmware setting | Scales all switching losses |
| $t_{dt,r}$, $t_{dt,f}$ | Candidate dead times | What is being optimized |
| $Q_{node} / I_{peak}$ | Computed | Physics-informed: estimated node transition time |
| $V_{SD} I_{out} (t_{dt,r} + t_{dt,f}) f_{sw}$ | Computed | Physics-informed: analytic dead-time loss |
| $I_{out} - \Delta I_L/2$ | Computed | Physics-informed: sign of valley current, flags the ZVS region |

The physics-informed features let a very small network fit well with only a few hundred measured points. All inputs are normalized with constants exported alongside the weights.

### Network

- MLP, 9 inputs → 16 → 16 → 1, ReLU, float32. About 450 weights (under 2 KB).
- Inference: about 450 multiply-accumulates per evaluation.
- Search: evaluate a 5 × 5 grid of dead-time candidates around the present setting, about 10 400 MACs. On the 120 MHz C28x with FPU32 this is expected to be well under 1 ms, run at about 10 Hz in the background loop.
- Pick the candidate with the lowest predicted loss, then apply the safety rules in section 4.

### Baselines it must beat

| # | Method | Role |
|---|---|---|
| A | Fixed dead time (worst case + margin) | Today's approach; the reference |
| B | Quadratic fit of the same surrogate | Proves the neural network earns its place over a simpler regression |
| C | Model-free duty-cycle minimization: at fixed $V_{out}$ and $I_{out}$, lower loss needs less duty, so step each dead time toward lower averaged duty (Yousefzadeh and Maksimović, "Sensorless Optimization of Dead Times in DC–DC Converters With Synchronous Rectifiers," IEEE Trans. Power Electronics, 2006) | Classical non-AI optimizer |
| **D** | **Edge AI optimizer (this proposal)** | **The feature** |
| E | D, then refined online by C within a small window | Online learning: corrects for part-to-part variation and aging |

---

## 3. Training and deployment pipeline

```
bench sweep ──► CSV dataset ──► train (PyTorch) ──► validate ──► export C header ──► firmware
   (step 10)     ml/dead-time/     ml/dead-time/      held-out       dt_model_weights.h
                  data/             train.py           operating
                                                       points
```

### Dataset (extends firmware step 10)

Run in open loop or voltage mode, with a hardware team member present, from a current-limited supply.

| Variable | Points |
|---|---|
| Load current | 0.5, 1, 1.5, 2, 3, 5, 8, 12.5 A (dense below the 1.65 A ZVS boundary) |
| Input voltage | 36, 48, 54 V |
| Switching frequency | 300, 400, 500 kHz |
| Rising-edge dead time | floor to ceiling, about 5 steps |
| Falling-edge dead time | floor to ceiling, about 5 steps |

Label each row with loss computed from bench instruments: $P_{loss} = V_{in} I_{in} - V_{out} I_{out}$ (the board's own input-current sense, `I_IN_SENSE`, is only about ±1–2 % accurate, far too coarse to resolve 0.1 W, so labels come from bench meters). Also log board telemetry (duty command, `ISENSE`, `VOUT_SENSE`, `VIN_SENSE`, `I_IN_SENSE`, `TEMP_SENSE`) so a later model could use on-board signals only. Probe the switch node with a short ground spring at selected points.

Start with a coarse grid at 48 V and 400 kHz, then refine around the optimum. Store data in `ml/dead-time/data/` as CSV, one row per operating point.

### Validation

Hold out whole operating points (an entire load current or input voltage), not random rows, so the test measures generalization to conditions the model never saw.

| Metric | What it measures | Target |
|---|---|---|
| Loss prediction MAE | How well the surrogate fits | [TBD] W |
| **Regret** | Measured loss at the model's chosen setting minus the measured best loss at that point | Lower than baselines A, B and C |
| Efficiency gain vs A | The headline result, plotted against load | Largest at light load |

### Deployment

- `train.py` exports weights, biases and normalization constants to `firmware/.../dt_model_weights.h` as `const float` arrays, with a header comment recording the dataset hash and training date.
- Inference is a plain C function, no libraries, no dynamic memory, matching section 7 of the firmware guide.
- **Out-of-distribution guard:** if any input is outside the range seen in training, the firmware ignores the model and uses the fixed dead time (method A), and sets an `OOD` flag in telemetry.

---

## 4. Safety rules

These are firm requirements, in addition to section 6 of [firmware-requirements.md](firmware-requirements.md). The model is an optimizer, never a protection.

1. **Hard dead-time floor.** Measured at the gate pins (not the commanded value) during bring-up, plus margin, and stored in the configuration header. No model output can go below it.
2. **Hard ceiling and window.** Candidates are only drawn from [floor, ceiling]. Online refinement (method E) moves only within ± a small window around the model's choice.
3. **Clamp and rate-limit.** One small step per update; no jumps.
4. **Switching frequency changes only in STANDBY**, as already required.
5. **Advisory mode first.** The model runs and reports its recommendation over SCI for a full test campaign before it is allowed to change the ePWM.
6. **Outside the control ISR.** Inference and search run in the background loop. The ISR only applies an already-validated dead-band value.
7. **Never touches protections.** The model cannot read or write CMPSS thresholds, trip-zone settings or the state machine.
8. **OOD fallback** to the fixed dead time, as above.

---

## 5. Firmware and dashboard hooks

- High-resolution dead band in the ePWM/HRPWM. Confirm in SysConfig that the chosen ePWM channel supports it on the F280039C; 10 ns steps are too coarse.
- Configuration header: dead-time floor, ceiling, refinement window, step size, update rate.
- Status frame fields: applied dead times, model-recommended dead times, **predicted loss**, **predicted loss with the fixed dead time**, `OOD` flag, active method.
- Serial commands: `dt mode fixed|ai|ai+refine`, `dt advise on|off`. Rejected unless allowed in the current state.
- Dashboard: live plot of predicted vs measured loss, and "watts saved by AI" against the fixed baseline.

---

## 6. Open questions

- $V_{SD}$ at the actual off-state gate voltage and temperature: confirm from the IGC033S10S1 datasheet curves.
- Whether bench instruments resolve a 0.1 W difference at 150 W (about 0.07 % efficiency). Light-load points will show the effect more clearly; this decides whether we need a power analyzer.
- Whether the MLP beats the quadratic baseline (B) by enough to justify it. If not, report that honestly; it is still a valid result.
- Whether a model trained on one board transfers to a second board, and how much online refinement (E) recovers.
