#!/usr/bin/env python3
"""
Theoretical efficiency estimate for the HexaGaN 48 V -> 12 V GaN buck.

A component-level loss budget: every loss that the chosen parts' datasheets
let us calculate, summed at each operating point. Nothing here depends on the
PCB layout. Left out on purpose, because they need the board:

  * copper resistance of traces, planes and vias
  * connector contact resistance (J201, J301)
  * ringing and snubber losses from loop inductance
  * extra switching loss from common-source inductance
  * gate-loop parasitics

So the result is an upper bound on what the built board can reach. It is also
built from maximum or hot datasheet values where the design notes use them, so
the power stage figures are on the conservative side for an ideal layout.

Two efficiencies are reported:

  power stage   V_IN node -> J301, the converter alone
  whole board   J201 -> J301, adding the input protection path and the
                housekeeping supply (aux buck, LDO, MCU, sensing, LEDs)

Run:   python efficiency_estimate.py          (plots saved to ./output)
       python efficiency_estimate.py --show   (also open plot windows)

The loss formulas and most inputs come from docs/design/power_stage.md and
docs/design/input_supply.md; sources are noted on every parameter.
"""

import argparse
import os

import numpy as np
import matplotlib


# =============================================================================
# PARAMETERS — change these and rerun. Sources are noted on every line.
# "ASSUMED" means the value is not published for the exact part.
# =============================================================================

# --- Operating point (docs/specifications.md) ---
VOUT = 12.0              # V
IOUT_FULL = 12.5         # A, 150 W
IOUT_RATED = 16.7        # A, 200 W rating case
VIN_POINTS = (40.0, 48.0, 51.0)        # V, min / typ / max
FSW_POINTS = (300e3, 400e3, 500e3)     # Hz, firmware range (power_stage.md #4)
FSW_NOM = 400e3
VIN_NOM = 48.0

# --- GaN FETs: Infineon IGC033S10S1 (power_stage.md calculations) ---
R_DS_ON_HOT = 4.8e-3     # ohm, 3.3 mOhm max at 25 degC x 1.45 at ~80 degC (datasheet Diagram 11)
Q_OSS = 43e-9            # C, typ at 50 V; held constant over 40-51 V
V_SD = 2.4               # V, reverse conduction during dead time, typ
T_DEAD = 10e-9           # s per edge, ASSUMED ePWM setting (power_stage.md)
Q_SW = 3.3e-9            # C, switching charge, typ
I_GATE_ON = 0.52         # A, plateau current with the 2 ohm HOH resistor (power_stage.md)
T_OFF = 1.4e-9           # s, turn-off transition, upper bound (power_stage.md)
Q_G = 11e-9              # C, total gate charge per FET at 5 V (power_stage.md driver row)

# --- Output inductor: Sunltech SLB2212P6R8MTT ---
L_OUT = 6.8e-6           # H
DCR = 2.1e-3 * 1.2       # ohm, 2.1 mOhm typ x 1.2 for copper at ~70 degC — ASSUMED rise
# Iron-powder core. No core-loss data is published for this part, so the loss
# at the nominal point is ASSUMED and scaled with ripple amplitude and
# frequency using Steinmetz-style exponents typical of iron powder.
CORE_LOSS_NOM = 0.30     # W at 48 V, 400 kHz — ASSUMED (range checked below)
CORE_LOSS_RANGE = (0.15, 0.60)
STEINMETZ_ALPHA = 1.2    # frequency exponent — ASSUMED
STEINMETZ_BETA = 2.1     # flux-swing exponent — ASSUMED

# --- Shunts and capacitors ---
R_SHUNT_OUT = 1e-3       # ohm, R301
R_SHUNT_IN = 1e-3        # ohm, R201
ESR_CIN = 1e-3           # ohm, three 10 uF 1210 in parallel — ASSUMED (~3 mOhm each)
ESR_COUT = 5e-3          # ohm, C316 || C317 at the NCC PXJ catalog maximum

# --- Input protection path (input_supply.md) ---
R_FUSE = 9e-3            # ohm, Littelfuse 0451007.MRL nominal cold resistance
R_Q201_HOT = 10.5e-3     # ohm, BSC070N10NS3G 7 mOhm max x 1.5 hot (input_supply.md)

# --- Housekeeping (input_supply.md +5V and +3V3 budgets) ---
I_5V_BASE = 0.140        # A on +5V without the gate driver: LDO load (MCU, USB bridge,
                         # logic, LEDs) plus sensing amplifiers. input_supply.md budgets
                         # about 150 mA in total including the driver
I_DRIVER_Q = 1e-3        # A, LM5113-Q1 quiescent, ASSUMED
AUX_EFFICIENCY = 0.80    # LM5164 48 V -> 5 V at ~150 mA — ASSUMED. TI's curve for
                         # 48 V -> 12 V reads about 88 % at 150 mA (datasheet Figure 5-2);
                         # a 5 V output has the same switching losses on less power
P_BLEED = 0.044 + 0.003  # W, 48V LED (0.92 mA at 48 V) and the V_IN divider, from V_IN
P_OUT_SIDE = 0.012       # W, 12V LED (about 1 mA from V_OUT) and the V_OUT divider

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# =============================================================================
# LOSS MODEL
# =============================================================================

def ripple(vin, fsw):
    d = VOUT / vin
    return (vin - VOUT) * d / (L_OUT * fsw)


def core_loss(vin, fsw, nominal=CORE_LOSS_NOM):
    """Scale the assumed nominal core loss with flux swing (∝ ripple) and frequency."""
    k_f = (fsw / FSW_NOM) ** STEINMETZ_ALPHA
    k_b = (ripple(vin, fsw) / ripple(VIN_NOM, FSW_NOM)) ** STEINMETZ_BETA
    return nominal * k_f * k_b


def losses(iout, vin, fsw, core_nominal=CORE_LOSS_NOM):
    """Return (dict of losses in W, input power, output power) at one operating point."""
    d = VOUT / vin
    di = ripple(vin, fsw)
    i_rms_sq = iout ** 2 + di ** 2 / 12
    i_valley = iout - di / 2
    i_peak = iout + di / 2

    loss = {}
    loss["High-side conduction"] = d * i_rms_sq * R_DS_ON_HOT
    loss["Low-side conduction"] = (1 - d) * i_rms_sq * R_DS_ON_HOT
    loss["Output charge (Qoss)"] = 0.5 * Q_OSS * vin * fsw
    loss["Dead time"] = V_SD * T_DEAD * fsw * (abs(i_valley) + abs(i_peak))
    t_on = Q_SW / I_GATE_ON
    loss["Turn-on overlap"] = 0.5 * vin * max(i_valley, 0.0) * t_on * fsw
    loss["Turn-off overlap"] = 0.5 * vin * i_peak * T_OFF * fsw
    loss["Inductor copper"] = i_rms_sq * DCR
    loss["Inductor core"] = core_loss(vin, fsw, core_nominal)
    loss["Output shunt"] = i_rms_sq * R_SHUNT_OUT
    i_cin_rms_sq = iout ** 2 * d * (1 - d) + d * di ** 2 / 12
    loss["Capacitor ESR"] = i_cin_rms_sq * ESR_CIN + (di ** 2 / 12) * ESR_COUT
    loss["Output-side bleed"] = P_OUT_SIDE

    p_out = VOUT * iout
    p_stage_in = p_out + sum(loss.values())

    # Housekeeping, fed from V_IN through the aux buck
    i_5v = I_5V_BASE + I_DRIVER_Q + 2 * Q_G * fsw
    p_aux_in = 5.0 * i_5v / AUX_EFFICIENCY
    loss["Housekeeping (MCU, logic, aux)"] = p_aux_in
    loss["Input-side bleed"] = P_BLEED

    # Input path: fuse, shunt and Q201 carry everything drawn from V_IN.
    # Solve I_in = (P_V_IN + I_in^2 R) / V_IN for I_in.
    r_path = R_FUSE + R_SHUNT_IN + R_Q201_HOT
    p_vin_node = p_stage_in + p_aux_in + P_BLEED
    i_in = (vin - np.sqrt(vin ** 2 - 4 * r_path * p_vin_node)) / (2 * r_path)
    loss["Input protection path"] = i_in ** 2 * r_path

    p_in = p_out + sum(loss.values())
    return loss, p_in, p_out, p_stage_in


STAGE_KEYS = ("High-side conduction", "Low-side conduction", "Output charge (Qoss)",
              "Dead time", "Turn-on overlap", "Turn-off overlap", "Inductor copper",
              "Inductor core", "Output shunt", "Capacitor ESR", "Output-side bleed")


def efficiencies(iout, vin, fsw, core_nominal=CORE_LOSS_NOM):
    loss, p_in, p_out, p_stage_in = losses(iout, vin, fsw, core_nominal)
    return p_out / p_stage_in, p_out / p_in, loss


# =============================================================================
# PLOTS
# =============================================================================

def plot_efficiency(show):
    import matplotlib.pyplot as plt
    loads = np.linspace(0.05, 1.34, 200) * IOUT_FULL
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
    for fsw, color in zip(FSW_POINTS, ("tab:blue", "tab:orange", "tab:red")):
        board = [efficiencies(i, VIN_NOM, fsw)[1] * 100 for i in loads]
        stage = [efficiencies(i, VIN_NOM, fsw)[0] * 100 for i in loads]
        axes[0].plot(loads * VOUT, stage, color=color, label=f"{fsw/1e3:.0f} kHz")
        axes[1].plot(loads * VOUT, board, color=color, label=f"{fsw/1e3:.0f} kHz")
    lo = [efficiencies(i, VIN_NOM, FSW_NOM, CORE_LOSS_RANGE[1])[1] * 100 for i in loads]
    hi = [efficiencies(i, VIN_NOM, FSW_NOM, CORE_LOSS_RANGE[0])[1] * 100 for i in loads]
    axes[1].fill_between(loads * VOUT, lo, hi, color="tab:orange", alpha=0.15,
                         label="400 kHz, core loss 0.15–0.6 W")
    for ax, title in zip(axes, ("Power stage (V_IN → J301)",
                                "Whole board (J201 → J301), with housekeeping")):
        ax.axvline(150, color="grey", lw=0.8, ls="--")
        ax.text(152, 99.2, "150 W", color="grey", fontsize=9)
        ax.set_title(title)
        ax.set_xlabel("Output power (W)")
        ax.grid(alpha=0.3)
        ax.set_ylim(80, 100)
        ax.legend(loc="lower right")
    axes[0].set_ylabel("Efficiency (%)")
    fig.suptitle("Estimated efficiency at 48 V input, component losses only (no layout parasitics)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "eff_01_efficiency.png"), dpi=130)
    if not show:
        plt.close(fig)


def plot_breakdown(show):
    import matplotlib.pyplot as plt
    loss, p_in, p_out, _ = losses(IOUT_FULL, VIN_NOM, FSW_NOM)
    items = sorted(loss.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["tab:blue" if k in STAGE_KEYS else "tab:green" for k, _ in items]
    ax.barh([k for k, _ in items], [v for _, v in items], color=colors)
    for y, (_, v) in enumerate(items):
        ax.text(v + 0.01, y, f"{v:.2f} W", va="center", fontsize=9)
    ax.set_xlabel("Loss (W)")
    ax.set_title(f"Loss breakdown at 150 W, 48 V, 400 kHz: {p_in - p_out:.2f} W in total, "
                 f"{p_out / p_in * 100:.1f} % board efficiency\n"
                 "blue = power stage, green = input path and housekeeping")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "eff_02_loss_breakdown.png"), dpi=130)
    if not show:
        plt.close(fig)


# =============================================================================
# SUMMARY
# =============================================================================

def summary():
    print("=" * 72)
    print(" HexaGaN 48 V -> 12 V GaN buck: theoretical efficiency estimate")
    print(" Component losses only; layout parasitics are not included")
    print("=" * 72)

    loss, p_in, p_out, p_stage_in = losses(IOUT_FULL, VIN_NOM, FSW_NOM)
    print("\nLOSS BREAKDOWN at 150 W, 48 V, 400 kHz")
    for k, v in sorted(loss.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<30}: {v:5.2f} W")
    print(f"  {"Total":<30}: {p_in - p_out:5.2f} W")
    print(f"  Power stage efficiency        : {p_out / p_stage_in * 100:5.2f} %")
    print(f"  Whole-board efficiency        : {p_out / p_in * 100:5.2f} %")

    print("\nWHOLE-BOARD EFFICIENCY (%) vs load, 48 V")
    loads = (0.1, 0.2, 0.5, 0.75, 1.0, IOUT_RATED / IOUT_FULL)
    print("  load          " + "".join(f"{l*150:>8.0f} W" for l in loads))
    for fsw in FSW_POINTS:
        row = "".join(f"{efficiencies(l * IOUT_FULL, VIN_NOM, fsw)[1]*100:>10.1f}" for l in loads)
        print(f"  {fsw/1e3:.0f} kHz      {row}")
    print("\nPOWER-STAGE EFFICIENCY (%) vs load, 48 V")
    for fsw in FSW_POINTS:
        row = "".join(f"{efficiencies(l * IOUT_FULL, VIN_NOM, fsw)[0]*100:>10.1f}" for l in loads)
        print(f"  {fsw/1e3:.0f} kHz      {row}")

    print("\nINPUT VOLTAGE at 150 W, 400 kHz (whole board / power stage)")
    for vin in VIN_POINTS:
        st, bd, _ = efficiencies(IOUT_FULL, vin, FSW_NOM)
        print(f"  {vin:.0f} V : {bd*100:5.2f} % / {st*100:5.2f} %")

    print("\nCORE-LOSS SENSITIVITY at 150 W, 48 V, 400 kHz (whole board)")
    for c in (CORE_LOSS_RANGE[0], CORE_LOSS_NOM, CORE_LOSS_RANGE[1]):
        print(f"  {c:.2f} W assumed core loss : {efficiencies(IOUT_FULL, VIN_NOM, FSW_NOM, c)[1]*100:5.2f} %")

    _, p_in_r, p_out_r, _ = losses(IOUT_RATED, VIN_POINTS[0], FSW_POINTS[0])
    print(f"\n200 W at 40 V, 300 kHz: {p_in_r - p_out_r:.2f} W loss, "
          f"{p_out_r / p_in_r * 100:.2f} % whole board")
    print(f"\nPlots saved in {OUT_DIR}")
    print("Remember: the inductor core loss and the aux-buck efficiency are ASSUMED,"
          " and layout adds loss on top of these figures.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--show", action="store_true", help="open plot windows")
    args = parser.parse_args()
    if not args.show:
        matplotlib.use("Agg")
    os.makedirs(OUT_DIR, exist_ok=True)
    summary()
    plot_efficiency(args.show)
    plot_breakdown(args.show)
    if args.show:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
