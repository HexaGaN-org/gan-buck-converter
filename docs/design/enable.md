# Enable — Design Notes

Sheet: `sheets/enable.kicad_sch`

**Owner:** Connor Jin · **Reviewer:** [NAME] · **Last updated:** 2026-11-05

---

## Purpose and requirements

Guarantee in hardware that the GaN half-bridge can switch only when the enable switch is on, the watchdog is healthy, reset is released, and the MCU requests switching. Firmware can request switching but never force it.

Targets are in [specifications.md](../specifications.md); boundaries and interface signals are in the **Enable** section of [schematic-hierarchy.md](../schematic-hierarchy.md).

**Requirements**

- Implement the gating logic in the **How it works** list of the Enable section of [schematic-hierarchy.md](../schematic-hierarchy.md): `STAGE_EN` from four conditions, then each PWM ANDed with `STAGE_EN` and with the inverse of the other PWM (the shoot-through interlock, decision #1).
- Both gates off in every undriven, floating, power-up and reset state.
- A windowed watchdog: kicks that are too slow or too fast both count as failures.
- Matched gating delay between the high-side and low-side paths, so gating does not eat into dead time: fast logic (74LVC-class).
- Pull-downs on `MCU_PWMH`, `MCU_PWML`, `MCU_EN`, `HS_PWM` and `LS_PWM`, and on the J5 input, so every undriven or floating state means *off*.
- Provide `STAGE_EN_FB` so firmware can read whether the stage is enabled.

---

## Decision log

One row per significant choice. Never delete a row: mark it *Superseded* and add the new decision below it.

| # | Date | Decision | Options considered | Rationale | Impact on other sheets | Status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-05 | **Hardware shoot-through interlock** in the PWM gating: `HS_PWM` = `MCU_PWMH` · `STAGE_EN` · NOT `MCU_PWML`, `LS_PWM` = `MCU_PWML` · `STAGE_EN` · NOT `MCU_PWMH`. One dual inverter (SN74LVC2G04, C10428) and two 3-input AND gates (74LVC1G11, C282348) | Dead time from the ePWM only (no interlock); 2-input interlock gates without `STAGE_EN` (drops the hardware enable); 2-input "AND with one inverted input" gates plus separate `STAGE_EN` gates (4 chips); a driver with a built-in interlock such as the LMG1210 (reopens the driver decision) | The LM5113-Q1 has independent inputs and no interlock. Correct dead time prevents timing shoot-through, but nothing in hardware stopped a firmware mistake (dead-band off, both pins driven as GPIO, a debugger halt) from turning both FETs on. At 48 V that destroys both GaN FETs in nanoseconds, long before the fuse acts. Several people will write ePWM code for the first time on this board, so a few cents of logic is cheap insurance. Each PWM goes straight into its own AND gate, so both paths have one matched gate delay; the inverters only act in the overlap case | power_stage: none (the same `HS_PWM` / `LS_PWM` labels). Firmware: the ePWM dead-band is still required; the interlock does not create dead time | Accepted |

---

## Calculations

One row per calculation. Note where each input came from (specification, datasheet, measurement) in Notes.

| Calculation | Formula | Result | Notes |
|---|---|---|---|
| Gate delay per path | one 74LVC1G11 at 3.3 V | ≈ 4–5 ns, the same on both paths | Datasheet propagation delay (≈ 3.5 ns at 5 V, 50 pF); the main PWM edge never passes through the inverter, so the dead time is not skewed |
| Inverter delay vs dead time | SN74LVC2G04 at 3.3 V | ≈ 4 ns, inside the ≥ 10 ns dead time | Only the overlap term passes through it |

---

## Part selection

| Ref des | Part | Manufacturer / MPN | LCSC # | Key parameters that justified it | Datasheet |
|---|---|---|---|---|---|
| U602 (suggested) | Interlock inverters (NOT `MCU_PWMH`, NOT `MCU_PWML`) | TI SN74LVC2G04DBVR | C10428 | Dual inverter, 1.65–5.5 V, SOT-23-6 | [TI](https://www.ti.com/product/SN74LVC2G04) |
| U603, U604 (suggested) | PWM gating and interlock, one per channel | Nexperia 74LVC1G11GW | C282348 | 3-input AND, Schmitt-trigger inputs, 1.65–5.5 V, SC-88 | [Nexperia](https://www.nexperia.com/product/74LVC1G11GW) |
| C6xx (suggested) | Decoupling, one per logic chip | YAGEO CC0603KRX7R9BB104 | C14663 | 100 nF X7R 0603, Basic | |

---

## Values published to other sheets

Numbers other sheets depend on. Update the dependent sheet's owner when one changes.

| Value | Result | Used by | Notes |
|---|---|---|---|
| | | | |

---

## Layout notes

What the layout owner must know: loops to keep small, parts to place first, keep-outs, thermal needs.

- Route `HS_PWM` and `LS_PWM` as a matched pair to the driver, away from the switch node; keep the two AND gates side by side so both paths are the same length.
- One 100 nF capacitor at each logic chip's VCC pin.

---

## Verification

How bring-up confirms this sheet works.

| # | Test | Method / equipment | Pass criterion | Result | Date |
|---|---|---|---|---|---|
| 1 | Gates off in every fault state | Walk through power-up, reset, watchdog timeout, enable switch off and a hung MCU; probe `HS_PWM` / `LS_PWM` | Both gates off in every case | | |
| 2 | Interlock | At low voltage (12 V input, supply limited to 0.5 A) or with the power stage unpowered, drive both `MCU_PWMH` and `MCU_PWML` high from firmware as GPIO | `HS_PWM` and `LS_PWM` both stay low | | |
| 3 | Gating delay match | Scope `MCU_PWMH`→`HS_PWM` and `MCU_PWML`→`LS_PWM` | Delays within about 1 ns of each other | | |

---

## Open questions

-
