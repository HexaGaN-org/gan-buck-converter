#!/usr/bin/env python3
"""
Input hot-plug and damping simulation for the HexaGaN 48 V -> 12 V GaN buck.

Plugging the board into a live 48 V supply connects the supply's lead
inductance to the power stage's low-loss input ceramics: an LC circuit that
rings, and can overshoot to almost twice the input voltage. The bulk
electrolytic on input_supply (C201) is there to damp that ring with its ESR.

What this script does, in order:

  1. HOT-PLUG   Steps the maximum input voltage onto the board through the
                bench-lead inductance and resistance, with and without C201,
                for a range of lead inductances. Prints the peak voltage, peak
                current and the I²t the fuse sees, and plots V_IN against time.
  2. RIPPLE     Splits the converter's pulsed input current between the
                supply leads, the ceramics and C201, harmonic by harmonic, and
                prints the RMS ripple current C201 carries at full load.
  3. IMPEDANCE  Plots the output impedance of the input filter (leads +
                ceramics + C201) against the converter's negative input
                impedance, the Middlebrook check for input-filter stability.

No TVS is modeled: the point is to show that, with C201 fitted, an ordinary
plug-in never reaches the TVS's breakdown voltage.

Run:   python input_hotplug_sim.py            (plots saved to ./output)
       python input_hotplug_sim.py --show     (also open plot windows)

Decisions and calculations that use these results are in
docs/design/input_supply.md.
"""

import argparse
import os

import numpy as np
import matplotlib
from scipy.integrate import solve_ivp

# =============================================================================
# PARAMETERS — change these and rerun. Sources are noted on every line.
# "ASSUMED" means the value is not measured or published; update it when it is.
# =============================================================================

# --- Operating point (docs/specifications.md) ---
VIN_MAX = 51.0         # V, maximum input voltage (worst case for overshoot)
VIN_POINTS = (40.0, 48.0, 51.0)  # V, min / typ / max, for the ripple check
VOUT = 12.0            # V
IOUT = 12.5            # A, full load (150 W)
P_IN = 150.0 / 0.95    # W, input power at full load, ~95 % efficiency

# --- Bench leads (supply to J1) ---
L_LEAD = 1.0e-6        # H, ASSUMED: about 1 m of paired bench leads
L_LEAD_SWEEP = (0.5e-6, 1.0e-6, 2.0e-6)  # H, range checked
R_LEAD = 0.05          # ohm, ASSUMED round trip: leads, terminals, fuse, Q201.
                       # Low on purpose; more resistance only adds damping

# --- Power-stage input ceramics (power_stage.md, decision #9) ---
C_CER = 10.4e-6        # F, effective at 48 V after DC-bias derating
ESR_CER = 0.005        # ohm, ASSUMED for the whole bank
ESL_CER = 0.5e-9       # H, ASSUMED for the whole bank

# --- C201 bulk electrolytic (input_supply.md part selection) ---
C_BULK = 100e-6        # F, JARSON FZ2A101M1313 (C5260780), 100 µF 100 V
ESR_BULK = 0.32        # ohm, LCSC listing for C5260780
ESL_BULK = 20e-9       # H, ASSUMED: can ESL plus the trace to the power stage
RIPPLE_RATING = 0.50   # A rms, LCSC listing for C5260780

# --- Limits to compare against ---
V_TVS_BR_MIN = 56.7    # V, SMBJ51CA minimum breakdown (datasheet)
V_HS_LIMIT = 90.0      # V, LM5113-Q1 HS recommended max (power_stage.md)
FUSE_I2T = 10.32       # A²s, Littelfuse 0451007.MRL melting I²t (LCSC listing)

T_END = 300e-6         # s, hot-plug simulation length
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# =============================================================================
# 1. HOT-PLUG
# =============================================================================


def hotplug(v_in, l_lead, with_bulk):
    """Step v_in onto the board at t = 0. Returns time, V_IN, lead current."""

    def node_voltage(i_lead, v_cer, v_bulk):
        # Node at V_IN: the lead current splits into the ceramic and bulk branches
        if with_bulk:
            return (i_lead + v_cer / ESR_CER + v_bulk / ESR_BULK) / (1 / ESR_CER + 1 / ESR_BULK)
        return i_lead * ESR_CER + v_cer

    def f(t, x):
        i_lead, v_cer, v_bulk = x
        v_n = node_voltage(i_lead, v_cer, v_bulk)
        i_cer = (v_n - v_cer) / ESR_CER
        i_bulk = (v_n - v_bulk) / ESR_BULK if with_bulk else 0.0
        return [(v_in - R_LEAD * i_lead - v_n) / l_lead, i_cer / C_CER,
                i_bulk / C_BULK if with_bulk else 0.0]

    sol = solve_ivp(f, [0, T_END], [0.0, 0.0, 0.0], max_step=2e-8)
    i_lead, v_cer, v_bulk = sol.y
    v_n = node_voltage(i_lead, v_cer, v_bulk)
    return sol.t, v_n, i_lead


def damping_check():
    z0 = np.sqrt(L_LEAD / C_CER)
    return dict(z0=z0, n=C_BULK / C_CER)

# =============================================================================
# 2. RIPPLE CURRENT IN C201
# =============================================================================


def branch_impedances(w, l_lead=L_LEAD):
    z_src = R_LEAD + 1j * w * l_lead
    z_cer = ESR_CER + 1j * w * ESL_CER + 1 / (1j * w * C_CER)
    z_bulk = ESR_BULK + 1j * w * ESL_BULK + 1 / (1j * w * C_BULK)
    return z_src, z_cer, z_bulk


def bulk_ripple_rms(v_in, fsw, n_harmonics=200):
    """RMS ripple current in C201. The buck draws a rectangular current pulse
    (IOUT for D of each period); each harmonic splits between the branches in
    proportion to their admittances."""
    d = VOUT / v_in
    total = 0.0
    for n in range(1, n_harmonics + 1):
        amp = 2 * IOUT / (n * np.pi) * abs(np.sin(n * np.pi * d))   # peak amplitude
        z_src, z_cer, z_bulk = branch_impedances(2 * np.pi * n * fsw)
        y = 1 / z_src + 1 / z_cer + 1 / z_bulk
        i_bulk = amp * (1 / z_bulk) / y
        total += abs(i_bulk) ** 2 / 2
    return np.sqrt(total)

# =============================================================================
# 3. INPUT-FILTER OUTPUT IMPEDANCE
# =============================================================================


def filter_output_impedance(freqs, with_bulk):
    w = 2 * np.pi * freqs
    z_src, z_cer, z_bulk = branch_impedances(w)
    y = 1 / z_src + 1 / z_cer
    if with_bulk:
        y = y + 1 / z_bulk
    return 1 / y


def converter_input_impedance(v_in):
    """Magnitude of a regulated converter's (negative) input impedance."""
    return v_in ** 2 / P_IN

# =============================================================================
# PLOTS AND SUMMARY
# =============================================================================

BOX = dict(boxstyle="round,pad=0.35", fc="white", ec="0.75", alpha=0.95)


def plot_hotplug(plt, results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(f"Hot-plug: {VIN_MAX:.0f} V stepped onto the board through "
                 f"{L_LEAD*1e6:.1f} µH of bench leads")
    t, v, i = results[(L_LEAD, False)]
    ax1.plot(t * 1e6, v, color="tab:red", lw=1.6, label="Power-stage ceramics only")
    ax2.plot(t * 1e6, i, color="tab:red", lw=1.6)
    t, v, i = results[(L_LEAD, True)]
    ax1.plot(t * 1e6, v, color="tab:blue", lw=2.2, label="With C201 (100 µF, 0.32 Ω ESR)")
    ax2.plot(t * 1e6, i, color="tab:blue", lw=2.2)
    ax1.axhline(V_HS_LIMIT, color="k", lw=1, ls="--")
    ax1.text(T_END * 1e6 * 0.99, V_HS_LIMIT + 1.5, "90 V: gate driver HS limit",
             ha="right", fontsize=8)
    ax1.axhline(V_TVS_BR_MIN, color="tab:orange", lw=1, ls=":")
    ax1.text(T_END * 1e6 * 0.99, V_TVS_BR_MIN + 1.5,
             "56.7 V: TVS starts to conduct (minimum breakdown)", ha="right", fontsize=8,
             color="tab:orange")
    ax1.axhline(VIN_MAX, color="0.6", lw=0.8)
    ax1.set_ylabel("V_IN (V)")
    ax1.set_ylim(0, 100)
    ax1.legend(loc="lower right")
    ax2.set_ylabel("Lead current (A)")
    ax2.set_xlabel("Time after plug-in (µs)")
    ax2.axhline(0, color="k", lw=0.8)
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "input_01_hotplug.png"), dpi=150)
    return fig


def plot_impedance(plt, freqs):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Input filter output impedance vs the converter's input impedance")
    for with_bulk, color, label in ((False, "tab:red", "Ceramics only"),
                                    (True, "tab:blue", "With C201")):
        z = filter_output_impedance(freqs, with_bulk)
        ax.loglog(freqs, abs(z), color=color, lw=2, label=label)
    z_in = converter_input_impedance(min(VIN_POINTS))
    ax.axhline(z_in, color="k", lw=1, ls="--")
    ax.text(freqs[0] * 1.2, z_in * 1.15,
            f"|Z_in| of the converter at {min(VIN_POINTS):.0f} V, full load: {z_in:.1f} Ω "
            "(keep the filter well below this)", fontsize=8)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("|Z| (Ω)")
    ax.set_ylim(3e-3, 40)
    ax.grid(alpha=0.3, which="both")
    ax.legend(loc="center right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "input_02_filter_impedance.png"), dpi=150)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", action="store_true", help="open plot windows as well as saving them")
    args = parser.parse_args()
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(OUT_DIR, exist_ok=True)

    print("HOT-PLUG (no TVS modeled)")
    print(f"  {VIN_MAX:.0f} V step, lead resistance {R_LEAD*1e3:.0f} mΩ")
    results = {}
    for l_lead in L_LEAD_SWEEP:
        row = []
        for with_bulk in (False, True):
            t, v, i = hotplug(VIN_MAX, l_lead, with_bulk)
            results[(l_lead, with_bulk)] = (t, v, i)
            row.append((v.max(), i.max(), np.trapezoid(i ** 2, t)))
        (v0, i0, _), (v1, i1, i2t) = row
        print(f"  Leads {l_lead*1e6:3.1f} µH : ceramics only {v0:5.1f} V peak, {i0:4.0f} A"
              f"   |  with C201 {v1:5.1f} V peak, {i1:4.0f} A, I²t {i2t:.2f} A²s")
    worst_damped = max(results[(l, True)][1].max() for l in L_LEAD_SWEEP)
    worst_i2t = max(np.trapezoid(results[(l, True)][2] ** 2, results[(l, True)][0])
                    for l in L_LEAD_SWEEP)
    print(f"  Worst damped peak {worst_damped:.1f} V vs TVS minimum breakdown "
          f"{V_TVS_BR_MIN} V: {'TVS stays off' if worst_damped < V_TVS_BR_MIN else 'TVS CONDUCTS'}")
    print(f"  Fuse melting I²t {FUSE_I2T} A²s is {FUSE_I2T / worst_i2t:.0f}× the worst hot-plug I²t")

    dc = damping_check()
    print("\nDAMPING RULES OF THUMB")
    print(f"  Characteristic impedance √(L/C)   : {dc['z0']:.2f} Ω  (C201 ESR {ESR_BULK} Ω: close match)")
    print(f"  C201 / ceramics                   : {dc['n']:.1f}×   (aim for ≥ 4×)")

    print("\nRIPPLE CURRENT IN C201 (full load, harmonic split)")
    for fsw in (300e3, 400e3):
        cells = ", ".join(f"{bulk_ripple_rms(v, fsw):.2f} A at {v:.0f} V" for v in VIN_POINTS)
        print(f"  {fsw/1e3:.0f} kHz : {cells}")
    worst_ripple = max(bulk_ripple_rms(v, f) for v in VIN_POINTS for f in (300e3, 400e3))
    print(f"  Rating {RIPPLE_RATING} A rms (LCSC listing): "
          f"{'within rating' if worst_ripple <= RIPPLE_RATING else 'ABOVE rating, see input_supply.md'}")

    freqs = np.logspace(3, 7, 2000)
    print("\nINPUT-FILTER STABILITY (Middlebrook)")
    z_in = converter_input_impedance(min(VIN_POINTS))
    for with_bulk, name in ((False, "ceramics only"), (True, "with C201   ")):
        z = abs(filter_output_impedance(freqs, with_bulk))
        k = np.argmax(z)
        print(f"  Filter output impedance peak, {name}: {z[k]:.2f} Ω at {freqs[k]/1e3:.0f} kHz"
              f"   ({z_in / z[k]:.0f}× below the converter's {z_in:.1f} Ω)")

    plot_hotplug(plt, results)
    plot_impedance(plt, freqs)
    print(f"\nPlots saved in {OUT_DIR}")
    print("Remember: the lead inductance and resistance are ASSUMED. Measure a real hot-plug "
          "on the bench (input_supply.md, verification).")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
