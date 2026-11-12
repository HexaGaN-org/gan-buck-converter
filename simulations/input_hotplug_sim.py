#!/usr/bin/env python3
"""
Input hot-plug and damping simulation for the HexaGaN 48 V -> 12 V GaN buck.

Plugging the board into a live 48 V supply connects the supply's lead
inductance to the power stage's and U201's low-loss input ceramics: an LC circuit that
rings, and can overshoot to almost twice the input voltage. The bulk
electrolytic on input_supply (C203) is there to damp that ring with its ESR.

What this script does, in order:

  1. HOT-PLUG   Steps the maximum input voltage onto the board through the
                bench-lead inductance and resistance, with and without C203,
                for a range of lead inductances. Prints the peak voltage, peak
                current and the I²t the fuse sees. A separate illustrative
                TVS sweep reports pulse current and energy.
  2. RIPPLE     Splits the converter's pulsed input current between the
                supply leads, the ceramics and C203, harmonic by harmonic, and
                prints the RMS ripple current C203 carries at full load.
  3. IMPEDANCE  Plots the output impedance of the input filter (leads +
                ceramics + C203) against the converter's negative input
                impedance, the Middlebrook check for input-filter stability.

This is a lumped screening model, not a surge qualification. D201 is upstream
of Q201, while C203 and the ceramics are downstream. Their trace/return
inductances and Q201's startup behavior are not modeled. The TVS piecewise
linear I-V approximation is anchored only to datasheet endpoints and cannot
predict an exact pulse or prove the TVS's 10/1000-us power rating for a short
hot-plug event. Measure the actual board before declaring margin.

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

# --- Bench leads (supply to J201) ---
L_LEAD = 1.0e-6        # H, ASSUMED: about 1 m of paired bench leads
L_LEAD_SWEEP = (0.5e-6, 1.0e-6, 2.0e-6)  # H, range checked
R_LEAD = 0.05          # ohm, ASSUMED round trip: leads, terminals, fuse, Q201.
                       # Low on purpose; more resistance only adds damping

# --- Input ceramics (power_stage.md #24, input_supply.md #26) ---
# Power stage: 3 x 10 uF X7S plus 4 x 100 nF X7R, estimated at 8.12 uF
# at 48 V and 6.14 uF at 60 V from recorded bias-curve readbacks. Interpolate
# each type to 51 V. Samsung's current exact-part library does not supply bias
# graphs for the 10 uF part, so this is an unverified typical estimate.
# U201: 5 x 2.2 uF X7R with 35.375% retained at 51 V from its recorded curve.
C_POWER_BULK_51 = 3 * (2.65 + (2.0 - 2.65) * (51 - 48) / (60 - 48)) * 1e-6
C_POWER_HF_51 = 4 * (0.042 + (0.035 - 0.042) * (51 - 48) / (60 - 48)) * 1e-6
C_POWER_51 = C_POWER_BULK_51 + C_POWER_HF_51
C_U201_51 = 5 * 2.2e-6 * (0.375 + (0.29 - 0.375) * (51 - 48) / (60 - 48))
C_CER = C_POWER_51 + C_U201_51  # F, 51 V screening estimate
C_CER_LOW = (C_POWER_BULK_51 * 0.9 * 0.78
             + (C_POWER_HF_51 + C_U201_51) * 0.9 * 0.85)
C_CER_HIGH = (C_POWER_BULK_51 * 1.1 * 1.22
              + (C_POWER_HF_51 + C_U201_51) * 1.1 * 1.15)
# Illustrative tolerance/temperature multipliers only: X7S permits +/-22% and
# X7R +/-15% without DC bias. Combined biased limits are not guaranteed here.
ESR_CER = 0.005        # ohm, ASSUMED for the whole bank
ESL_CER = 0.5e-9       # H, ASSUMED for the whole bank

# --- C203 bulk electrolytic (input_supply.md part selection) ---
C_BULK = 100e-6        # F, Ymin VKME1452A101MV (C487440), 100 µF 100 V
C_BULK_LOW = 80e-6     # F, -20% nameplate tolerance
C_BULK_HIGH = 120e-6   # F, +20% nameplate tolerance
ESR_BULK = 0.32        # ohm, ASSUMED scenario, NOT Ymin's specified ESR
                       # Ymin publishes no ESR/impedance for this exact part.
                       # Sweep below is illustrative, not a guaranteed corner.
# https://www.ymin.cn/chip-miniature-type-aluminum-electrolytic-capacitors-vkm-product/
ESL_BULK = 20e-9       # H, ASSUMED: can ESL plus the trace to the power stage
RIPPLE_RATING = 1.04   # A rms, Ymin VKME1452A101MV at 100 kHz/105 C

# --- Limits to compare against ---
# Hongjiacheng SMBJ51CA datasheet Rev 1.1, 25 C: breakdown 56.7-62.7 V
# at 1 mA, maximum clamp 82.4 V at 7.28 A for a 10/1000 us pulse.
# https://xonstorage.z8.web.core.windows.net/pdf/hongjiacheng_smbj170a__xonlink.pdf
# Endpoint slopes are *illustrative*, not a guaranteed I-V characteristic.
V_TVS_BR_MIN = 56.7    # V
V_TVS_BR_MAX = 62.7    # V
V_TVS_CLAMP = 82.4     # V at I_TVS_RATED
I_TVS_RATED = 7.28     # A, 10/1000 us waveform
TVS_CASES = (
    (V_TVS_BR_MIN, (V_TVS_CLAMP - V_TVS_BR_MIN) / I_TVS_RATED),
    (V_TVS_BR_MAX, (V_TVS_CLAMP - V_TVS_BR_MAX) / I_TVS_RATED),
)
V_HS_LIMIT = 90.0      # V, LM5113-Q1 HS recommended max (power_stage.md)
FUSE_I2T = 10.32       # A²s, Littelfuse 0451007.MRL melting I²t (LCSC listing)

T_END = 300e-6         # s, hot-plug simulation length
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# =============================================================================
# 1. HOT-PLUG
# =============================================================================


def hotplug(v_in, l_lead, with_bulk, c_cer=C_CER, c_bulk=C_BULK,
            esr_bulk=ESR_BULK, tvs=None):
    """Step the input onto a lumped node; return time, voltage, lead and TVS current.

    tvs is (breakdown_voltage, illustrative_dynamic_resistance), or None.
    """

    def node_voltage(i_lead, v_cer, v_bulk):
        # Solve ceramic, bulk and optional piecewise-linear TVS branch currents.
        if with_bulk:
            numerator = i_lead + v_cer / ESR_CER + v_bulk / esr_bulk
            conductance = 1 / ESR_CER + 1 / esr_bulk
        else:
            numerator = i_lead + v_cer / ESR_CER
            conductance = 1 / ESR_CER
        v_n = numerator / conductance
        if tvs is not None:
            v_br, r_dyn = tvs
            conducting_voltage = (numerator + v_br / r_dyn) / (conductance + 1 / r_dyn)
            v_n = np.where(v_n > v_br, conducting_voltage, v_n)
        return v_n

    def f(t, x):
        i_lead, v_cer, v_bulk = x
        v_n = node_voltage(i_lead, v_cer, v_bulk)
        i_cer = (v_n - v_cer) / ESR_CER
        i_bulk = (v_n - v_bulk) / esr_bulk if with_bulk else 0.0
        return [(v_in - R_LEAD * i_lead - v_n) / l_lead, i_cer / c_cer,
                i_bulk / c_bulk if with_bulk else 0.0]

    sol = solve_ivp(f, [0, T_END], [0.0, 0.0, 0.0], max_step=2e-8)
    if not sol.success:
        raise RuntimeError(f"Hot-plug integration failed: {sol.message}")
    i_lead, v_cer, v_bulk = sol.y
    v_n = node_voltage(i_lead, v_cer, v_bulk)
    i_tvs = np.maximum((v_n - tvs[0]) / tvs[1], 0) if tvs is not None else np.zeros_like(v_n)
    return sol.t, v_n, i_lead, i_tvs


def damping_check():
    z0 = np.sqrt(L_LEAD / C_CER)
    return dict(z0=z0, n=C_BULK / C_CER)

# =============================================================================
# 2. RIPPLE CURRENT IN C203
# =============================================================================


def branch_impedances(w, l_lead=L_LEAD):
    z_src = R_LEAD + 1j * w * l_lead
    z_cer = ESR_CER + 1j * w * ESL_CER + 1 / (1j * w * C_CER)
    z_bulk = ESR_BULK + 1j * w * ESL_BULK + 1 / (1j * w * C_BULK)
    return z_src, z_cer, z_bulk


def bulk_ripple_rms(v_in, fsw, n_harmonics=200):
    """RMS ripple current in C203. The buck draws a rectangular current pulse
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
    t, v, i, _ = results[(L_LEAD, False)]
    ax1.plot(t * 1e6, v, color="tab:red", lw=1.6, label="All input ceramics, no C203")
    ax2.plot(t * 1e6, i, color="tab:red", lw=1.6)
    t, v, i, _ = results[(L_LEAD, True)]
    ax1.plot(t * 1e6, v, color="tab:blue", lw=2.2, label="Full ceramic bank + C203, no TVS")
    ax2.plot(t * 1e6, i, color="tab:blue", lw=2.2)
    t, v, i, _ = results[(L_LEAD, "TVS minimum breakdown")]
    ax1.plot(t * 1e6, v, color="tab:green", lw=1.5, ls="--",
             label="Illustrative TVS: 56.7 V breakdown")
    ax2.plot(t * 1e6, i, color="tab:green", lw=1.5, ls="--")
    ax1.axhline(V_HS_LIMIT, color="k", lw=1, ls="--")
    ax1.text(T_END * 1e6 * 0.99, V_HS_LIMIT + 1.5, "90 V: gate driver HS limit",
             ha="right", fontsize=8)
    ax1.axhline(V_TVS_BR_MIN, color="tab:orange", lw=1, ls=":")
    ax1.text(T_END * 1e6 * 0.99, V_TVS_BR_MIN + 1.5,
             "56.7 V: TVS minimum breakdown at 1 mA", ha="right", fontsize=8,
             color="tab:orange")
    ax1.axhline(VIN_MAX, color="0.6", lw=0.8)
    ax1.set_ylabel("V_IN (V)")
    ax1.set_ylim(0, 100)
    ax1.legend(loc="lower right", fontsize=8)
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
    fig.suptitle("Lumped input filter output impedance vs converter input impedance")
    for with_bulk, color, label in ((False, "tab:red", "Ceramics only"),
                                    (True, "tab:blue", "With C203")):
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

    print("HOT-PLUG (lumped screening model; D201 and C203 are physically separated)")
    print(f"  {VIN_MAX:.0f} V step, lead resistance {R_LEAD*1e3:.0f} mΩ assumed")
    print(f"  ceramics {C_CER*1e6:.2f} µF (power stage + all five U201 parts),"
          f" C203 {C_BULK*1e6:.0f} µF / {ESR_BULK:.2f} Ω assumed ESR")
    results = {}
    for l_lead in L_LEAD_SWEEP:
        row = []
        for with_bulk in (False, True):
            t, v, i, i_tvs = hotplug(VIN_MAX, l_lead, with_bulk)
            results[(l_lead, with_bulk)] = (t, v, i, i_tvs)
            row.append((v.max(), i.max(), np.trapezoid(i ** 2, t)))
        (v0, i0, _), (v1, i1, i2t) = row
        print(f"  Leads {l_lead*1e6:3.1f} µH : ceramics only {v0:5.1f} V peak, {i0:4.0f} A"
              f"   |  with C203 {v1:5.1f} V peak, {i1:4.0f} A, I²t {i2t:.2f} A²s")
    worst_damped = max(results[(l, True)][1].max() for l in L_LEAD_SWEEP)
    worst_i2t = max(np.trapezoid(results[(l, True)][2] ** 2, results[(l, True)][0])
                    for l in L_LEAD_SWEEP)
    print(f"  Worst no-TVS C203 peak {worst_damped:.1f} V vs {V_TVS_BR_MIN:.1f} V minimum"
          " breakdown at 1 mA")
    print(f"  Fuse melting I²t reference {FUSE_I2T} A²s vs modeled {worst_i2t:.2f} A²s;"
          " this is not a fuse coordination check")

    print("\nILLUSTRATIVE TVS BRANCH (same-node endpoint approximation, not a rating pass)")
    for (v_br, r_dyn), label in zip(TVS_CASES, ("TVS minimum breakdown", "TVS maximum breakdown")):
        print(f"  {label}: Vbr={v_br:.1f} V, slope={r_dyn:.2f} Ω")
        for l_lead in L_LEAD_SWEEP:
            t, v, i, i_tvs = hotplug(VIN_MAX, l_lead, True, tvs=(v_br, r_dyn))
            results[(l_lead, label)] = (t, v, i, i_tvs)
            p_tvs = v * i_tvs
            print(f"    {l_lead*1e6:3.1f} µH: Vpk={v.max():.2f} V,"
                  f" I_TVS,pk={i_tvs.max():.3f} A, Ppk={p_tvs.max():.1f} W,"
                  f" E={np.trapezoid(p_tvs, t)*1e3:.3f} mJ")

    print("\nHOT-PLUG SENSITIVITY (assumed capacitance and ESR corners; no TVS / low-Vbr TVS)")
    largest_no_tvs = (0.0, "")
    largest_tvs_energy = (0.0, "")
    largest_tvs_current = (0.0, "")
    for c_cer in (C_CER_LOW, C_CER, C_CER_HIGH):
        for c_bulk in (C_BULK_LOW, C_BULK, C_BULK_HIGH):
            for esr_bulk in (ESR_BULK / 2, ESR_BULK, ESR_BULK * 2):
                for l_lead in L_LEAD_SWEEP:
                    case = (f"Ccer={c_cer*1e6:.2f} µF, C203={c_bulk*1e6:.0f} µF,"
                            f" ESR={esr_bulk:.2f} Ω, L={l_lead*1e6:.1f} µH")
                    t, v, _, _ = hotplug(VIN_MAX, l_lead, True, c_cer, c_bulk,
                                         esr_bulk)
                    largest_no_tvs = max(largest_no_tvs, (float(v.max()), case))
                    t, v, _, i_tvs = hotplug(VIN_MAX, l_lead, True, c_cer, c_bulk,
                                             esr_bulk, tvs=TVS_CASES[0])
                    largest_tvs_current = max(largest_tvs_current,
                                              (float(i_tvs.max()), case))
                    largest_tvs_energy = max(largest_tvs_energy,
                                             (float(np.trapezoid(v * i_tvs, t)), case))
    print(f"  Highest no-TVS node peak: {largest_no_tvs[0]:.2f} V ({largest_no_tvs[1]})")
    print(f"  Highest TVS peak current: {largest_tvs_current[0]:.3f} A"
          f" ({largest_tvs_current[1]})")
    print(f"  Highest TVS pulse energy: {largest_tvs_energy[0]*1e3:.3f} mJ"
          f" ({largest_tvs_energy[1]})")

    dc = damping_check()
    print("\nDAMPING RULES OF THUMB")
    print(f"  Characteristic impedance √(L/C)   : {dc['z0']:.2f} Ω  (C203 ESR {ESR_BULK} Ω)")
    print(f"  C203 / ceramics                   : {dc['n']:.1f}×   (aim for ≥ 4×)")

    print("\nRIPPLE CURRENT IN C203 (full load, harmonic split; 51 V capacitor estimate used throughout)")
    for fsw in (300e3, 400e3):
        cells = ", ".join(f"{bulk_ripple_rms(v, fsw):.2f} A at {v:.0f} V" for v in VIN_POINTS)
        print(f"  {fsw/1e3:.0f} kHz : {cells}")
    worst_ripple = max(bulk_ripple_rms(v, f) for v in VIN_POINTS for f in (300e3, 400e3))
    print(f"  Ymin rating {RIPPLE_RATING} A rms (100 kHz/105 C): "
          f"{'within rating' if worst_ripple <= RIPPLE_RATING else 'ABOVE rating, see input_supply.md'}")

    freqs = np.logspace(3, 7, 2000)
    print("\nINPUT-FILTER STABILITY (Middlebrook)")
    z_in = converter_input_impedance(min(VIN_POINTS))
    for with_bulk, name in ((False, "ceramics only"), (True, "with C203   ")):
        z = abs(filter_output_impedance(freqs, with_bulk))
        k = np.argmax(z)
        print(f"  Filter output impedance peak, {name}: {z[k]:.2f} Ω at {freqs[k]/1e3:.0f} kHz"
              f"   ({z_in / z[k]:.0f}× below the converter's {z_in:.1f} Ω)")

    plot_hotplug(plt, results)
    plot_impedance(plt, freqs)
    print(f"\nPlots saved in {OUT_DIR}")
    print("Remember: lead/trace parasitics and the TVS I-V between endpoints are ASSUMED."
          " D201 is upstream of Q201; this same-node model cannot establish part"
          " voltage or TVS safety. Measure real hot-plug waveforms and use the"
          " manufacturer pulse-width/temperature curves before approval.")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
