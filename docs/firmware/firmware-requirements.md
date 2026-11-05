# Firmware Guide — 48 V → 12 V GaN Buck Converter

What the firmware for this board needs to do, explained for someone new to power electronics. Read this first; the hardware details live in [specifications.md](../specifications.md) and [schematic-hierarchy.md](../schematic-hierarchy.md) when you need them.

> **Status:** Draft. Numbers marked `[TBD]` are still being decided by the hardware team.

---

## 1. What the board does

The board takes **48 V** in and turns it into **12 V** out, delivering up to about 12.5 A (150 W).

It does this with two fast electronic switches (GaN transistors) that flip on and off **hundreds of thousands of times per second**. By controlling what fraction of each cycle the top switch is on, it sets the output voltage. A coil (inductor) and capacitors smooth the chopped result into a steady 12 V.

**The firmware is the brain.** It decides exactly when each switch turns on and off, watches the voltages and current, adjusts to keep the output at 12 V, and shuts everything down safely if something goes wrong.

---

## 2. Key ideas in plain language

| Term | What it means here |
|---|---|
| **PWM** (pulse-width modulation) | A signal that switches on and off at a fixed rate. The MCU generates it to drive the switches. |
| **Duty cycle** | The fraction of each cycle the top switch is on. To get 12 V from 48 V, it's about 12 ÷ 48 = **25 %**. |
| **Switching frequency** | How many on/off cycles per second: planned at about **400 kHz** (400,000 per second), adjustable from 300 to 500 kHz. |
| **Dead time** | A tiny gap (billionths of a second) when **both** switches are off, between one turning off and the other turning on. If both were ever on at once, they would short 48 V to ground and destroy themselves. |
| **Control loop** | Measure the output, compare it to 12 V, adjust the duty cycle, repeat, many thousands of times per second. |
| **ADC** | The MCU's analog-to-digital converter. It turns the measured voltages, current and temperature into numbers. |
| **Comparator trip** | A hardware circuit inside the MCU that shuts the PWM off instantly when a signal crosses a limit, faster than any code could react. You configure it; it then acts on its own. |
| **Hardware enable** | Circuitry outside the MCU that blocks the PWM unless a person has turned on the enable switch and the MCU is healthy. The firmware can *ask* to run but can never *force* it. |
| **Watchdog** | A separate chip that resets the MCU if the firmware stops "checking in" on schedule, for example because the code froze. |

---

## 3. Tools

- **MCU:** TI TMS320F280039C, a microcontroller designed for power converters
- **IDE:** Code Composer Studio (CCS)
- **Library:** C2000Ware (TI's driver library for this MCU)
- **Pin setup:** TI SysConfig. The file `firmware/pinmux.syscfg` decides which pin does what, and is shared with the hardware team
- **Practice hardware:** the LAUNCHXL-F280039C LaunchPad, a TI development board with the same MCU. Use it until our boards arrive
- **Code goes in:** `firmware/` in this repo

---

## 4. What the firmware connects to

| Signal | Direction | What it is |
|---|---|---|
| `MCU_PWMH`, `MCU_PWML` | out | The two PWM signals: top switch and bottom switch |
| `MCU_EN` | out | "I'd like to run." Goes to the hardware enable |
| `STAGE_EN_FB` | in | "Running is actually allowed." Comes back from the hardware enable |
| `WD_IN` | out | The regular check-in pulse to the watchdog |
| `ISENSE` | in | Output current |
| `VOUT_SENSE` | in | Output voltage |
| `VIN_SENSE` | in | Input voltage |
| `TEMP_SENSE` | in | Temperature near the switches |
| `SCI_TX`, `SCI_RX` | out / in | Serial link to the laptop over USB |
| HEARTBEAT, FAULT LEDs | out | Status lights |

All measured signals arrive scaled to 0–3 V, so the ADC can read them directly.

---

## 5. What the firmware must do

### 5.1 Start safely
- After power-up or reset, keep both PWM outputs **off** and `MCU_EN` **low**.
- Set up all the protections (section 5.3) **before** PWM can ever turn on.
- Check that every measurement looks sensible (nothing reading zero or maxed out) before allowing a start.

### 5.2 Follow a simple set of states

```
INIT ──► STANDBY ──run──► SOFT_START ──► RUN
            ▲                  │          │
            │               any fault  any fault
            │                  ▼          ▼
            └────clear────── FAULT ◄──────┘
```

| State | What's happening |
|---|---|
| **INIT** | Setting up after reset |
| **STANDBY** | Ready and waiting. Switches off |
| **SOFT_START** | Ramping the output up gently from 0 to 12 V |
| **RUN** | Holding the output at 12 V |
| **FAULT** | Something went wrong. Switches off until someone clears it |

The rules:
- Only start when the laptop sends a **run** command, and only from STANDBY.
- When starting, raise `MCU_EN`, then check `STAGE_EN_FB`. If the hardware won't allow running (for example, the enable switch is off), go back to STANDBY and say why.
- **Soft start:** ramp the output up over a short, adjustable time instead of jumping straight to 12 V, to avoid current surges and overshoot.
- **Faults stay latched.** After a fault, the board must not restart by itself, even if the problem goes away. A person sends **clear**, which returns to STANDBY, never straight to RUN.
- If `STAGE_EN_FB` drops while running (someone flipped the enable switch off), stop and go to FAULT.

### 5.3 Protect the hardware

Two kinds of protection, both required:

**Instant hardware trips** (you configure them; the MCU's comparators then act on their own in nanoseconds):
- **Overcurrent:** if the current goes above [TBD] A, cut the current switching pulse short. This repeats every cycle while the current is too high.
- **Overvoltage:** if the output goes above [TBD] V, shut PWM off and keep it off.

**Software checks** (in your code, a little slower):
- **Undervoltage:** don't start, or stop, if the input is below [TBD] V. Use two thresholds (on above one, off below a lower one) so it doesn't flicker at the edge.
- **Overtemperature:** stop if the temperature goes above [TBD] °C.
- **Stuck in current limit:** if the overcurrent trip keeps firing for longer than a set time, treat it as a fault.

For every fault:
- Record **why** it happened (a fault code), report it over serial, and light the FAULT LED.
- Keep every threshold in **one configuration file**, with a comment saying where the number came from.

### 5.4 Keep the watchdog happy, but only when healthy
- Send the `WD_IN` check-in pulse regularly. This watchdog is "windowed": checking in **too early** counts as a failure, just like too late.
- Only check in after confirming the control loop really ran. **Never** check in from a simple timer, because a timer would keep checking in even if the rest of the code had frozen, which defeats the purpose.

### 5.5 Control the output

Build the control in three stages, each one proven before the next:

1. **Open loop:** you set the duty cycle directly. No feedback. Used to test the hardware.
2. **Voltage mode:** measure the output voltage and adjust the duty cycle to hold 12 V.
3. **Current mode:** a faster, more advanced loop that also controls the current. Comes later.

Requirements:
- The two PWM signals are a matched pair with **dead time** between them, generated by the MCU's PWM hardware. Dead time must be adjustable.
- Switching frequency **400 kHz by default**, adjustable from 300 to 500 kHz, changed only in STANDBY.
- Use the MCU's **high-resolution PWM** mode, so the duty cycle can be adjusted in very fine steps. This is required, not optional: at 400 kHz an ordinary PWM step changes the output by about 160 mV, far too coarse to hold 12 V steady.
- Always keep the duty cycle between a minimum and maximum limit.
- Trigger the ADC readings from the PWM itself, so measurements are taken at the same point in every cycle.
- The control code runs in an interrupt once per cycle (or once every few cycles) and must finish with time to spare. At 400 kHz, a whole cycle is only 2.5 µs.
- Put all controller tuning values (gains) in the configuration file, not scattered through the code.

### 5.6 Measure
- Convert raw ADC numbers into real units (volts, amps, °C). The conversion factors will come from the hardware team.
- At start-up, with switching off, measure the current sensor's zero reading and subtract it.

### 5.7 Talk to the laptop
- Use the serial link (SCI) through the USB connection.
- Start with simple **text commands** you can type in a serial terminal, for example `run`, `stop`, `clear`, `mode open`, `duty 20`, `vref 12.0`.
- Send regular status updates (around 10–50 per second): state, fault code, input and output voltage, current, temperature, duty cycle and frequency.
- Check every command: reject anything out of range or not allowed in the current state, and say why.
- Serial communication must **never** slow down the control interrupt.
- Write the command list in `firmware/PROTOCOL.md`.

### 5.8 Show status
- **HEARTBEAT LED:** blinks steadily while the code is running normally.
- **FAULT LED:** on when a fault is latched.
- In debug builds, toggle a spare pin at the start and end of the control interrupt, so its timing can be checked on an oscilloscope.

---

## 6. The golden rules

If you remember nothing else:

1. **Never let both switches be on at the same time.** Always keep dead time between them.
2. **Protections are armed before PWM ever starts,** and nothing can turn them off.
3. **No host command can bypass a protection or the state machine.**
4. **After a fault, never restart automatically.** A person must clear it.
5. **Only check in with the watchdog when the control loop is truly healthy.**
6. **Keep the control interrupt fast.** Anything slow (serial, LEDs, calculations that can wait) belongs in the main loop.

---

## 7. How to write the code

- No dynamic memory allocation (`malloc`).
- All adjustable numbers (thresholds, gains, timings, frequencies) in **one** configuration header, with units in the name or a comment.
- Use the signal names from section 4.
- Commit everything needed to build, including the `.syscfg` file. Someone should be able to clone the repo and build it. Put build instructions in `firmware/README.md`.
- Every change goes through a pull request reviewed by someone else. Changes to protections or the state machine also need a hardware-team reviewer.

---

## 8. Step-by-step plan

Each step is finished before starting the next. Steps 1–5 use only the LaunchPad, so you can start right away.

| Step | Goal | You're done when |
|---|---|---|
| 1 | Set up the tools | A LaunchPad LED-blink program builds, flashes and runs in the debugger |
| 2 | Pin setup | `pinmux.syscfg` agreed with the hardware team and committed |
| 3 | PWM | The two PWM signals with dead time show on an oscilloscope; frequency and dead time adjustable |
| 4 | Measurements and trips | ADC readings work; a comparator trip shuts PWM off when a test signal crosses the threshold |
| 5 | Commands and states | Serial commands and status updates work; states, faults and the watchdog behave as described |
| 6 | Real board, low voltage | On our board, powered by 5 V only (no 48 V): code runs, readings are correct, the enable chain responds |
| 7 | Real board, open loop | Switching at low input voltage and light load, with the hardware team watching the waveforms |
| 8 | Voltage control | Holds 12 V steady across different loads |
| 9 | Current control | The advanced loop works, with the same tests |
| 10 | Frequency sweep | Efficiency measured from 300 to 500 kHz, to choose the best frequency |

**Steps 6 onward are always done with a hardware team member present.** The board is powered from a current-limited supply, and the first power-ups happen at reduced voltage.

---

## 9. Still to be decided

- Protection thresholds (the `[TBD]`s above): set by the hardware team in `specifications.md`.
- Final switching frequency: chosen from the step 10 measurements.
- Conversion factors for the measurements: from the hardware team once the sensing parts are chosen.
- The exact command list: you define it in `firmware/PROTOCOL.md` during step 5.

If anything here is unclear, ask. In power electronics, a question asked early is far cheaper than a fried board.
