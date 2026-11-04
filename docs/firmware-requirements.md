# Firmware Requirements — 48 V → 12 V GaN Synchronous Buck

What the converter's firmware must do, the hardware it runs on, and the order to build it in. Written for the firmware owner; read it alongside [specifications.md](specifications.md) (targets and thresholds), [schematic-hierarchy.md](schematic-hierarchy.md) (every signal the MCU touches) and [design/mcu.md](design/mcu.md).

> **Status:** Draft. Thresholds marked `[TBD]` come from `specifications.md` once the hardware team sets them. Change a requirement only by editing this file in a pull request.

**How to read the requirements.** Each has an ID, a priority and a verification method.
**Must** = required for the first working board. **Should** = wanted, but can follow later.
Verification: **T** = test on hardware, **I** = inspection or code review, **A** = analysis or measurement.

---

## 1. Platform

| Item | Choice |
|---|---|
| MCU | TI TMS320F280039C, 64-pin LQFP (C28x core with FPU, TMU and CLA coprocessor) |
| IDE / compiler | Code Composer Studio |
| Libraries | C2000Ware (driverlib) |
| Pin-mux and peripheral setup | TI SysConfig. `firmware/pinmux.syscfg` is the single source of truth for pin assignments, shared with the hardware team |
| Early development hardware | LAUNCHXL-F280039C LaunchPad, used until the boards arrive |
| Source location | `firmware/` in this repo |

---

## 2. Hardware interface

Every MCU signal, defined in [schematic-hierarchy.md](schematic-hierarchy.md). Names in firmware must match these.

| Signal | Direction | Peripheral | Purpose |
|---|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | out | One ePWM A/B pair, high-resolution | High- and low-side gate commands (pass through the hardware enable before reaching the FETs) |
| `MCU_EN` | out | GPIO | Firmware's request to switch. Necessary, never sufficient |
| `STAGE_EN_FB` | in | GPIO | Whether the hardware enable is actually active |
| `WDI` | out | GPIO | Kick for the external windowed watchdog |
| `XRSN` | in/out | Reset | Reset from the supervisor or debugger |
| `ISENSE` | in | ADC + CMPSS | Inductor current; hardware cycle-by-cycle overcurrent |
| `VOUT_SENSE` | in | ADC + CMPSS | Output voltage; hardware overvoltage |
| `VIN_SENSE` | in | ADC | Input voltage; undervoltage lockout, feedforward |
| `TEMP_SENSE` | in | ADC | Thermistor near the GaN FETs |
| `SCI_TX`, `SCI_RX` | out / in | SCI | Host link through the USB-UART bridge |
| HEARTBEAT, FAULT LEDs | out | GPIO | Status indication |

---

## 3. Functional requirements

### 3.1 Start-up and safe defaults

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-INIT-01 | From reset until firmware deliberately starts switching, both PWM outputs shall be held low and `MCU_EN` shall be low. | Must | T |
| FW-INIT-02 | All protections (section 3.3) shall be configured and armed before PWM is ever enabled. | Must | I |
| FW-INIT-03 | At start-up, firmware shall check that all sensed values are in a plausible range (no open or shorted sense channel) before allowing any transition out of STANDBY. | Must | T |
| FW-INIT-04 | The firmware version and build identifier shall be reported over SCI at start-up and on request. | Should | T |

### 3.2 Operating states

The converter shall run as an explicit state machine:

| State | Meaning | PWM | `MCU_EN` |
|---|---|---|---|
| INIT | Peripheral setup and self-checks after reset | Off | Low |
| STANDBY | Ready; waiting for a run command | Off | Low |
| SOFT_START | Output ramping up to its setpoint | On | High |
| RUN | Regulating the output | On | High |
| FAULT | A protection has tripped; latched until cleared | Off | Low |

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-SM-01 | Switching shall start only on an explicit run command from the host, and only from STANDBY. | Must | T |
| FW-SM-02 | On a run command, firmware shall assert `MCU_EN`, confirm through `STAGE_EN_FB` that the hardware enable is active, and only then start PWM. If `STAGE_EN_FB` stays low, it shall return to STANDBY and report why. | Must | T |
| FW-SM-03 | SOFT_START shall ramp the output setpoint from zero to its target over a configurable time, so inrush and overshoot stay within limits. | Must | T |
| FW-SM-04 | Any protection trip shall move the converter to FAULT, stop PWM and drop `MCU_EN`. | Must | T |
| FW-SM-05 | FAULT shall be latched: the converter shall not restart on its own when the fault condition clears. Leaving FAULT requires an explicit clear command, and returns to STANDBY, never directly to RUN. | Must | T |
| FW-SM-06 | If `STAGE_EN_FB` drops during SOFT_START or RUN (enable switch opened, watchdog fault), firmware shall stop PWM and enter FAULT with the cause recorded. | Must | T |

### 3.3 Protections

Thresholds come from the protections table in [specifications.md](specifications.md).

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-PROT-01 | **Cycle-by-cycle overcurrent:** a CMPSS comparator on `ISENSE`, routed through the ePWM X-BAR to the trip zone, shall end the current PWM pulse in hardware when the current exceeds [TBD] A. No software is in this path. | Must | T |
| FW-PROT-02 | **Output overvoltage:** a CMPSS comparator on `VOUT_SENSE` shall trip both PWM outputs off in hardware (one-shot, latched) above [TBD] V. | Must | T |
| FW-PROT-03 | **Input undervoltage lockout:** firmware shall hold PWM off while `VIN` is below [TBD] V, and allow starting only above [TBD] V (hysteresis). Undervoltage during RUN shall cause FAULT. | Must | T |
| FW-PROT-04 | **Overtemperature:** firmware shall enter FAULT when `TEMP_SENSE` indicates more than [TBD] °C. | Must | T |
| FW-PROT-05 | A sustained cycle-by-cycle current-limit condition (current limit active for longer than a configurable time) shall be treated as a fault. | Must | T |
| FW-PROT-06 | Every fault shall record its cause as a fault code, reported over SCI and shown on the FAULT LED. | Must | T |
| FW-PROT-07 | Protection thresholds shall be defined in one configuration file, each with a comment giving its source in `specifications.md`. | Must | I |
| FW-PROT-08 | No host command shall be able to disable a protection or bypass the state machine. | Must | I, T |

### 3.4 Watchdog

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-WD-01 | Firmware shall kick the external windowed watchdog (`WDI`) within its valid window, both not too late and not too early. | Must | T |
| FW-WD-02 | The kick shall happen only when the control loop is confirmed to be running correctly (for example, the control interrupt has completed a recent cycle). It shall never come from a free-running timer that would keep kicking while the control loop is stuck. | Must | I |
| FW-WD-03 | A deliberate test mode (debug builds only) shall allow stopping the kicks, to verify that the hardware enable drops and the MCU resets. | Should | T |

### 3.5 Control

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-CTL-01 | PWM shall be a complementary high-side / low-side pair with dead time generated in the ePWM, configurable on both edges. | Must | T |
| FW-CTL-02 | Switching frequency shall be configurable from 300 kHz to 500 kHz. It may be changed only in STANDBY. | Must | T |
| FW-CTL-03 | Duty cycle shall use high-resolution PWM (HRPWM), so output-voltage steps are fine enough to avoid limit cycling. | Must | A |
| FW-CTL-04 | Duty cycle shall be clamped to configurable minimum and maximum limits at all times. | Must | I, T |
| FW-CTL-05 | Three control modes shall be supported, selectable in STANDBY: **open loop** (fixed duty, for bring-up), **voltage mode**, and **average current mode**. | Must (open loop, voltage mode); Should (current mode) | T |
| FW-CTL-06 | ADC sampling shall be triggered by the ePWM, timed so the current sample gives the average inductor current (for example, at the middle of the on-time or off-time). | Must | A, T |
| FW-CTL-07 | The control-loop interrupt shall run once per switching period, or once every N periods (N configurable), and shall finish with at least 30 % of its period to spare at 500 kHz. | Must | A |
| FW-CTL-08 | Integrators shall have anti-windup, so the loop recovers cleanly from current limiting and duty-cycle clamping. | Must | T |
| FW-CTL-09 | Controller gains shall be configurable parameters, not values buried in code. | Must | I |
| FW-CTL-10 | Input-voltage feedforward should be available in voltage mode. | Should | T |

### 3.6 Measurement

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-MEAS-01 | Firmware shall convert ADC readings to engineering units (V, A, °C), using scaling constants from the sensing design note. | Must | T |
| FW-MEAS-02 | Firmware shall support a per-channel offset and gain calibration, applied at run time. | Should | T |
| FW-MEAS-03 | Current offset shall be measured automatically at start-up with switching off. | Should | T |

### 3.7 Host communication

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-COM-01 | Firmware shall communicate with the host over SCI through the USB-UART bridge, at a fixed baud rate defined in the configuration file. | Must | T |
| FW-COM-02 | Commands shall cover at least: run, stop, clear fault, select control mode, set open-loop duty, set output setpoint, set switching frequency and dead time (STANDBY only), and read status. | Must | T |
| FW-COM-03 | Firmware shall stream telemetry at a configurable rate (default about 10–50 Hz): state, fault code, `VIN`, `VOUT`, output current, temperature, duty cycle and switching frequency. | Must | T |
| FW-COM-04 | Every command shall be validated (range-checked and allowed in the current state) and acknowledged, or rejected with a reason. | Must | T |
| FW-COM-05 | Communication shall never run inside, or delay, the control-loop interrupt. | Must | I, A |
| FW-COM-06 | The protocol shall be documented in `firmware/PROTOCOL.md`. Start with a simple human-readable text protocol so commands can be typed in a serial terminal. | Must | I |

### 3.8 Status and debug

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-DBG-01 | The HEARTBEAT LED shall blink at a steady rate whenever the main loop is running. | Must | T |
| FW-DBG-02 | The FAULT LED shall indicate a latched fault; blink codes for the fault cause are optional. | Must | T |
| FW-DBG-03 | Debug builds shall be able to toggle a spare GPIO at the start and end of the control interrupt, so its execution time can be measured on a scope. | Should | A |

---

## 4. Software quality

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| FW-SQ-01 | No dynamic memory allocation. | Must | I |
| FW-SQ-02 | Interrupt routines stay short: the control interrupt does only measurement, control and PWM update. Everything else runs in the main loop. | Must | I |
| FW-SQ-03 | All tunable values (thresholds, gains, timing, frequencies) live in one configuration header, with units in their names or comments. | Must | I |
| FW-SQ-04 | The `.syscfg` file and every source file needed to build are committed; a fresh clone builds in CCS with no manual steps beyond installing CCS and C2000Ware. Build instructions go in `firmware/README.md`. | Must | T |
| FW-SQ-05 | Every change goes through a pull request reviewed by someone else. Changes to protections or the state machine also need a hardware-team reviewer. | Must | I |
| FW-SQ-06 | Code follows TI driverlib conventions and uses the signal names in section 2. | Should | I |

---

## 5. Development plan

Build and prove each step before the next. Steps 1–5 run on the LaunchPad, so firmware work never waits for boards.

| Step | Milestone | Done when |
|---|---|---|
| 1 | Toolchain | CCS and C2000Ware installed; a LaunchPad LED-blink project builds, flashes and debugs |
| 2 | Pin-mux | `pinmux.syscfg` agreed with the hardware team for the 64-pin package and committed |
| 3 | PWM | Complementary PWM with dead time and HRPWM seen on a scope; frequency and dead time adjustable |
| 4 | Sensing and hardware trips | ADC triggered by PWM; CMPSS trips shut PWM off on the scope when a function generator crosses the threshold |
| 5 | Comms and state machine | Text commands and telemetry over SCI; state machine, fault latching and watchdog behave as specified |
| 6 | Board, low voltage | On the real board, powered from the external 5 V input with no 48 V: MCU runs, sensing reads correctly, the enable chain responds to `MCU_EN`, the switch and the watchdog |
| 7 | Board, open loop | Open-loop switching at reduced input voltage and light load, from a current-limited supply; gate and switch-node waveforms checked with the hardware team |
| 8 | Voltage mode | Regulates 12 V across the load range; load-step response measured |
| 9 | Current mode | Average current mode regulating, with the same tests |
| 10 | Frequency sweep | Efficiency measured from 300 to 500 kHz at several loads; results recorded |

---

## 6. Open items

- Protection thresholds (all `[TBD]` above): set in `specifications.md` by the hardware team.
- Switching frequency target: 400 kHz planned, final value from the step 10 sweep.
- Sensing scaling constants: from `design/sensing.md` once parts are chosen.
- Whether the control loop runs on the main CPU or the CLA coprocessor: decide after measuring loop time at step 8.
- Exact command set and telemetry format: defined in `firmware/PROTOCOL.md` at step 5.
