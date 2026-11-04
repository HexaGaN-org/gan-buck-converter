#!/usr/bin/env python3
"""
Voltage-mode control simulation for the HexaGaN 48 V -> 12 V GaN buck.

What this script does, in order:

  1. PLANT      Builds an averaged model of the power stage (inductor, output
                capacitors, losses) and plots how the output voltage responds
                to duty-cycle changes at every frequency (a Bode plot).
  2. CONTROLLER Designs a Type III compensator, converts it to the digital
                form the C2000 will run, and plots the full loop gain with
                crossover frequency and phase margin marked. It includes the
                MCU's sampling and computation delay.
  3. TIME SIM   Runs a time simulation of soft-start and a 10 % -> 90 % load
                step, with the controller running once per PWM cycle exactly
                as firmware would: sampled ADC readings (rounded to 12 bits),
                one-cycle delay, duty clamped, and PWM resolution with and
                without HRPWM.

  4. WORST CASE Re-checks the same controller with every part at the edge of its
                tolerance (capacitor ESR, inductance, capacitance, input voltage).

It is an *averaged* model: switching ripple is not shown, only the average
behavior the control loop sees. See README.md for what each plot means and
what to try.

Run:   python voltage_mode_sim.py            (plots saved to ./output)
       python voltage_mode_sim.py --show     (also open plot windows)
       python voltage_mode_sim.py --help     (all options)
"""

import argparse
import os
from contextlib import contextmanager

import numpy as np
import matplotlib
from scipy.linalg import expm
from scipy.signal import cont2discrete

# =============================================================================
# PARAMETERS — change these and rerun. Sources are noted on every line.
# "ASSUMED" means the value is not decided yet; update it when it is.
# =============================================================================

# --- Operating point (docs/specifications.md) ---
VIN = 48.0             # V, input voltage for this run
VIN_NOMINAL = 48.0     # V, the input voltage the feedforward normalizes to
VIN_MIN, VIN_MAX = 36.0, 54.0   # V, input range — ASSUMED (specifications.md is [TBD])
VOUT_TARGET = 12.0     # V, output voltage
FSW = 400e3            # Hz, switching frequency (power_stage.md decision #4)

# --- Inductor: Sunltech SLB2212P6R8MTT datasheet (Rev.01) ---
L = 6.8e-6             # H, nominal (tested at 100 kHz / 0.1 V, zero current)
L_TOL = 0.20           # +/-20 % tolerance (datasheet "M")
L_SAG_FULL_LOAD = 0.12 # fraction lost at 12.5 A. Iron-powder core, Isat = 31 A for a 30 % drop;
                       # no L-vs-I curve is published, so a straight line from 0 A is ASSUMED
R_DCR = 2.1e-3         # ohm, typical (2.31 mOhm max)

# --- Other resistances in the current path ---
R_SHUNT = 1e-3         # ohm, current-sense shunt R301
R_FET = 4.8e-3         # ohm, hot R_DS(on): 3.3 mOhm max x 1.45 at ~80 degC
                       # (IGC033S10S1 datasheet Rev 1.1, Diagram 11)
R_PCB = 1e-3           # ohm, copper traces — ASSUMED

# --- Output capacitors (power_stage.md decision #10) ---
C_CER = 39e-6          # F, 8 x 22 uF ceramics after DC-bias derating (effective)
ESR_CER = 0.5e-3       # ohm, whole ceramic bank — ASSUMED (~4 mOhm each, 8 in parallel)
C_POLY = 470e-6        # F, polymer bulk capacitor C319
C_POLY_TOL = 0.20      # +/-20 % (datasheet)
ESR_POLY = 25e-3       # ohm, C319's LCSC listing (jieerrui MA25V470M8x10, 25 mOhm @ 100 kHz)
# ESR range for the worst-case check. Datasheets give only a maximum:
#   Honorcap HV1E477M0810PZ (the 470 uF / 25 V / 8x10.5 datasheet supplied): 30 mOhm max at
#   100 kHz, 20 degC; impedance at 105 degC up to 1.25x; end of life up to 1.5x.
ESR_POLY_MIN = 15e-3   # ohm — ASSUMED (a good part, warm); no minimum is published
ESR_POLY_MAX = 37.5e-3 # ohm, 30 mOhm x 1.25 (new part, hot)
ESR_POLY_EOL = 45e-3   # ohm, 30 mOhm x 1.5 (end of life)

# --- Load ---
# None = electronic load in constant-current mode (the least damping, so the
# worst case for stability). Set a number in ohms for a resistive load.
LOAD_R = None

# --- Digital controller timing (docs/firmware/firmware-requirements.md) ---
LOOP_EVERY_N_CYCLES = 1     # control ISR runs every N PWM periods
COMPUTE_DELAY_CYCLES = 1.0  # PWM periods from ADC sample to new duty taking effect
F_TBCLK = 120e6             # Hz, ePWM time-base clock (300 counts per period at 400 kHz)
USE_HRPWM = True            # high-resolution PWM (required by the firmware guide)
USE_VIN_FEEDFORWARD = True  # duty = controller output x VIN_NOMINAL / measured VIN, so the
                            # loop gain doesn't change with input voltage (VIN_SENSE is
                            # already planned for feedforward in schematic-hierarchy.md)
HRPWM_STEP = 150e-12        # s, HRPWM fine step (~150 ps, power_stage.md)
D_MIN, D_MAX = 0.0, 0.60    # duty-cycle clamp

# --- Output-voltage measurement (sensing sheet — not designed yet) ---
ADC_BITS = 12
ADC_VREF = 3.3              # V
VOUT_DIVIDER = 0.2          # VOUT_SENSE = 0.2 x VOUT -> 16.5 V full scale — ASSUMED

# --- Controller design targets ---
F_CROSSOVER = 10e3          # Hz, target loop speed with nominal parts. Chosen so the loop
                            # stays stable at the worst part-tolerance corner (see the
                            # WORST CASE section of the summary): a high-ESR polymer and a
                            # low inductance roughly double the crossover. 20 kHz looks fine
                            # with nominal parts but drops to ~7 deg phase margin there.
# Type III placement. None = choose automatically from the plant:
#   both zeros below the LC resonance (0.4 x f_LC), first pole above crossover
#   (1.6 x F_CROSSOVER), second pole at 0.45 x the control rate.
FZ1 = None
FZ2 = None
FP1 = None
FP2 = None

# --- Time simulation scenario ---
SOFTSTART_TIME = 2e-3       # s, reference ramps 0 -> 12 V over this time
T_LOAD_ON = 3e-3            # s, light load applied
T_STEP_UP = 5e-3            # s, step to heavy load
T_STEP_DOWN = 7e-3          # s, step back to light load
T_END = 9e-3                # s
I_LIGHT = 1.25              # A, 10 % of 12.5 A
I_HEAVY = 11.25             # A, 90 % of 12.5 A
SETTLE_BAND = 0.005         # settled when within +/-0.5 % of 12 V (60 mV)
SUBSTEPS = 10               # simulation steps per PWM period

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# =============================================================================
# 1. PLANT — averaged state-space model of the power stage
# =============================================================================
#
# States  x = [inductor current, ceramic cap voltage, polymer cap voltage]
# Inputs  u = [average switch-node voltage (= duty x VIN), load current]
# Output  y = output voltage
#
# "Averaged" means the switch node is replaced by its average over one PWM
# period, duty x VIN. That removes the switching ripple but keeps everything
# the control loop cares about.

def build_plant():
    r_path = R_DCR + R_SHUNT + R_FET + R_PCB
    g_cer, g_poly = 1.0 / ESR_CER, 1.0 / ESR_POLY
    g_load = 0.0 if LOAD_R is None else 1.0 / LOAD_R
    g_sum = g_cer + g_poly + g_load

    # Output node (KCL): vout = (iL - i_load + g_cer*v_cer + g_poly*v_poly) / g_sum
    c_out = np.array([1.0, g_cer, g_poly]) / g_sum
    d_out = np.array([0.0, -1.0]) / g_sum

    a = np.zeros((3, 3))
    b = np.zeros((3, 2))
    # Inductor: L diL/dt = v_sw - r_path*iL - vout
    a[0] = (-np.array([r_path, 0.0, 0.0]) - c_out) / L
    b[0] = (np.array([1.0, 0.0]) - d_out) / L
    # Each capacitor: C dv/dt = (vout - v) / ESR
    a[1] = g_cer * (c_out - np.array([0.0, 1.0, 0.0])) / C_CER
    b[1] = g_cer * d_out / C_CER
    a[2] = g_poly * (c_out - np.array([0.0, 0.0, 1.0])) / C_POLY
    b[2] = g_poly * d_out / C_POLY
    return a, b, c_out, d_out


def plant_duty_to_vout(freqs, a, b, c_out, d_out):
    """G_vd(jw): output-voltage change per unit duty-cycle change."""
    s = 2j * np.pi * np.asarray(freqs)[:, None, None]
    m = s * np.eye(a.shape[0])[None] - a[None]
    rhs = np.broadcast_to(b[:, 0], (len(freqs), a.shape[0]))[..., None]
    x = np.linalg.solve(m, rhs)[..., 0]
    return VIN * (x @ c_out + d_out[0])


def plant_seen_by_controller(freqs):
    """What the controller drives. With input-voltage feedforward the duty is scaled by
    VIN_NOMINAL / VIN, which cancels the plant's dependence on the input voltage."""
    g = plant_duty_to_vout(freqs, *build_plant())
    return g * VIN_NOMINAL / VIN if USE_VIN_FEEDFORWARD else g


def plant_landmarks():
    f_lc = 1.0 / (2 * np.pi * np.sqrt(L * (C_CER + C_POLY)))
    f_esr = 1.0 / (2 * np.pi * ESR_POLY * C_POLY)
    return f_lc, f_esr


# =============================================================================
# 2. CONTROLLER — Type III compensator, digital loop gain, margins
# =============================================================================
#
# Type III = an integrator (removes steady-state error) + two zeros (add the
# phase the LC "spring" takes away) + two poles (cut high-frequency noise).
#
#            K   (1 + s/wz1)(1 + s/wz2)
#   Gc(s) = --- -------------------------
#            s   (1 + s/wp1)(1 + s/wp2)
#
# It is designed in continuous time, then converted to a digital filter with
# the Tustin (bilinear) method, which is what runs in the ISR.

def compensator_placement(n_cycles):
    f_lc, _ = plant_landmarks()
    f_ctrl = FSW / n_cycles
    fz1 = FZ1 if FZ1 is not None else 0.4 * f_lc
    fz2 = FZ2 if FZ2 is not None else 0.4 * f_lc
    fp1 = FP1 if FP1 is not None else 1.6 * F_CROSSOVER
    fp2 = FP2 if FP2 is not None else 0.45 * f_ctrl
    return fz1, fz2, fp1, fp2


def compensator_continuous(fz1, fz2, fp1, fp2, gain=1.0):
    wz1, wz2, wp1, wp2 = (2 * np.pi * f for f in (fz1, fz2, fp1, fp2))
    num = gain * np.polymul([1 / wz1, 1], [1 / wz2, 1])
    den = np.polymul([1, 0], np.polymul([1 / wp1, 1], [1 / wp2, 1]))
    return num, den


def discretize(num, den, ts):
    numd, dend, _ = cont2discrete((num, den), ts, method="bilinear")
    numd = np.atleast_1d(np.squeeze(numd))
    dend = np.atleast_1d(np.squeeze(dend))
    return numd / dend[0], dend / dend[0]


def digital_loop_gain(freqs, g_vd, b_z, a_z, n_cycles):
    """Loop gain T = controller x plant x delay x zero-order hold."""
    ts = n_cycles / FSW
    w = 2 * np.pi * freqs
    z = np.exp(1j * w * ts)
    g_c = np.polyval(b_z, z) / np.polyval(a_z, z)
    delay = np.exp(-1j * w * COMPUTE_DELAY_CYCLES / FSW)
    zoh = (1 - np.exp(-1j * w * ts)) / (1j * w * ts)
    return g_c * g_vd * delay * zoh, g_c


def design_controller(freqs, g_vd, n_cycles):
    """Place the poles and zeros, then set the gain so the loop crosses 0 dB at F_CROSSOVER."""
    fz1, fz2, fp1, fp2 = compensator_placement(n_cycles)
    ts = n_cycles / FSW
    num, den = compensator_continuous(fz1, fz2, fp1, fp2, 1.0)
    b_z, a_z = discretize(num, den, ts)
    f_probe = np.array([F_CROSSOVER])
    g_vd_probe = plant_seen_by_controller(f_probe)
    t_probe, _ = digital_loop_gain(f_probe, g_vd_probe, b_z, a_z, n_cycles)
    gain = 1.0 / abs(t_probe[0])
    num, den = compensator_continuous(fz1, fz2, fp1, fp2, gain)
    b_z, a_z = discretize(num, den, ts)
    return dict(fz1=fz1, fz2=fz2, fp1=fp1, fp2=fp2, gain=gain,
                num=num, den=den, b_z=b_z, a_z=a_z, n_cycles=n_cycles)


def margins(freqs, loop):
    """Crossover frequency, phase margin and gain margin from a loop-gain curve."""
    mag = np.abs(loop)
    phase = np.degrees(np.unwrap(np.angle(loop)))
    # Unwrap starts from the integrator (-90 deg); keep it in the usual range.
    phase -= 360.0 * np.round((phase[0] + 90.0) / 360.0)

    above = mag >= 1.0
    idx = np.where(above[:-1] & ~above[1:])[0]
    if len(idx) == 0:
        return None
    i = idx[-1]
    # Interpolate on a log scale for a precise crossover.
    f0, f1 = np.log10(freqs[i]), np.log10(freqs[i + 1])
    m0, m1 = np.log10(mag[i]), np.log10(mag[i + 1])
    frac = m0 / (m0 - m1)
    fc = 10 ** (f0 + frac * (f1 - f0))
    ph_c = phase[i] + frac * (phase[i + 1] - phase[i])
    pm = 180.0 + ph_c

    gm, f_gm = None, None
    j = np.where((phase[i:-1] > -180.0) & (phase[i + 1:] <= -180.0))[0]
    if len(j):
        k = i + j[0]
        f_gm = freqs[k]
        gm = -20 * np.log10(mag[k])
    return dict(fc=fc, pm=pm, gm=gm, f_gm=f_gm, phase=phase, mag=mag)


# =============================================================================
# 3. TIME SIMULATION — soft-start and load step, with a digital controller
# =============================================================================

class ThreePoleThreeZero:
    """The digital Type III filter, written the way it would be in C:

        u[n] = b0*e[n] + b1*e[n-1] + b2*e[n-2] + b3*e[n-3]
               - a1*u[n-1] - a2*u[n-2] - a3*u[n-3]

    The output is clamped to [D_MIN, D_MAX] and the *clamped* value is stored
    in the history. That stops the integrator winding up while the duty is
    saturated (anti-windup).
    """

    def __init__(self, b_z, a_z, u_min, u_max):
        self.b = np.pad(b_z, (0, 4 - len(b_z)))
        self.a = np.pad(a_z, (0, 4 - len(a_z)))
        self.e_hist = np.zeros(3)
        self.u_hist = np.zeros(3)
        self.u_min, self.u_max = u_min, u_max

    def step(self, err):
        u = (self.b[0] * err + self.b[1:] @ self.e_hist - self.a[1:] @ self.u_hist)
        u = min(max(u, self.u_min), self.u_max)
        self.e_hist = np.array([err, self.e_hist[0], self.e_hist[1]])
        self.u_hist = np.array([u, self.u_hist[0], self.u_hist[1]])
        return u


def duty_step(use_hrpwm):
    """Smallest duty-cycle change the PWM hardware can make."""
    if use_hrpwm:
        return HRPWM_STEP * FSW
    return FSW / F_TBCLK  # 1 / (counts per period)


def adc_read(vout):
    lsb = ADC_VREF / (2 ** ADC_BITS)
    code = np.clip(np.round(vout * VOUT_DIVIDER / lsb), 0, 2 ** ADC_BITS - 1)
    return code * lsb / VOUT_DIVIDER


def reference(t):
    return VOUT_TARGET * min(t / SOFTSTART_TIME, 1.0)


def load_current(t):
    if t < T_LOAD_ON:
        return 0.0
    if T_STEP_UP <= t < T_STEP_DOWN:
        return I_HEAVY
    return I_LIGHT


def simulate(ctrl, use_hrpwm=USE_HRPWM):
    a, b, c_out, d_out = build_plant()
    n_states = a.shape[0]
    dt = 1.0 / (FSW * SUBSTEPS)
    # Exact discretization of the plant for one substep (inputs held constant).
    m = np.zeros((n_states + 2, n_states + 2))
    m[:n_states, :n_states] = a * dt
    m[:n_states, n_states:] = b * dt
    em = expm(m)
    ad, bd = em[:n_states, :n_states], em[:n_states, n_states:]

    comp = ThreePoleThreeZero(ctrl["b_z"], ctrl["a_z"], D_MIN, D_MAX)
    q = duty_step(use_hrpwm)
    n_cycles = ctrl["n_cycles"]
    delay_cycles = int(round(COMPUTE_DELAY_CYCLES))

    n_periods = int(round(T_END * FSW))
    x = np.zeros(n_states)
    pending = [0.0] * (delay_cycles + 1)  # duty values waiting to take effect
    duty = 0.0

    rec = {k: np.empty(n_periods * SUBSTEPS) for k in ("t", "vout", "il", "iload", "duty", "ref")}
    vout = 0.0
    for k in range(n_periods):
        t0 = k / FSW
        # Control ISR: sample at the start of the period, result applies later.
        if k % n_cycles == 0:
            err = reference(t0) - adc_read(vout)
            u = comp.step(err)
            if USE_VIN_FEEDFORWARD:
                u = min(max(u * VIN_NOMINAL / VIN, D_MIN), D_MAX)
            pending.append(np.round(u / q) * q)
        else:
            pending.append(pending[-1])
        duty = pending.pop(0)

        i_load = load_current(t0)
        u_in = np.array([duty * VIN, i_load])
        for s in range(SUBSTEPS):
            x = ad @ x + bd @ u_in
            vout = c_out @ x + d_out @ u_in
            n = k * SUBSTEPS + s
            rec["t"][n] = t0 + (s + 1) * dt
            rec["vout"][n] = vout
            rec["il"][n] = x[0]
            rec["iload"][n] = i_load
            rec["duty"][n] = duty
            rec["ref"][n] = reference(t0)
    return rec


def step_metrics(rec):
    t, v = rec["t"], rec["vout"]
    band = SETTLE_BAND * VOUT_TARGET

    def window(t_start, length=1.5e-3):
        return (t >= t_start) & (t < min(t_start + length, T_END))

    def settle_time(t_start):
        w = window(t_start)
        outside = np.abs(v[w] - VOUT_TARGET) > band
        if not outside.any():
            return 0.0
        return t[w][np.where(outside)[0][-1]] - t_start

    up, down = window(T_STEP_UP), window(T_STEP_DOWN)
    quiet = (t >= T_STEP_UP - 1e-3) & (t < T_STEP_UP)
    ss = v[t >= SOFTSTART_TIME]
    tss = t[t >= SOFTSTART_TIME]
    return dict(
        softstart_overshoot=max(ss[tss < T_LOAD_ON].max() - VOUT_TARGET, 0.0),
        dip=VOUT_TARGET - v[up].min(),
        settle_up=settle_time(T_STEP_UP),
        overshoot=v[down].max() - VOUT_TARGET,
        settle_down=settle_time(T_STEP_DOWN),
        wobble_pp=v[quiet].max() - v[quiet].min(),
        il_peak=rec["il"][up].max(),
        il_min=rec["il"][down].min(),
    )


# =============================================================================
# PLOTS
# =============================================================================

from matplotlib.ticker import FuncFormatter, NullFormatter

F_PLOT_MAX = 160e3   # Hz, right edge of the frequency plots (just below the Nyquist limit)
BOX = dict(boxstyle="round,pad=0.35", fc="white", ec="0.75", alpha=0.95)
EVENT_STYLE = dict(color="0.55", ls=":", lw=1)


def setup_style(plt):
    plt.rcParams.update({
        "font.size": 9.5, "axes.labelsize": 10, "axes.titlesize": 10,
        "legend.fontsize": 8.5, "figure.titlesize": 11.5,
    })


def _hz(x, _pos=None):
    return f"{x/1e3:g} kHz" if x >= 1e3 else f"{x:g} Hz"


def freq_axes(ax):
    """Log frequency axis labelled in Hz / kHz instead of powers of ten."""
    ax.set_xscale("log")
    ax.set_xlim(10, F_PLOT_MAX)
    ax.xaxis.set_major_formatter(FuncFormatter(_hz))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", alpha=0.35)
    ax.grid(True, which="minor", alpha=0.12)


def times_axis(ax, ticks_db, label):
    """Right-hand axis that translates dB into 'times bigger'."""
    sec = ax.secondary_yaxis("right")
    sec.set_yticks(ticks_db)
    sec.set_yticklabels([f"×{10 ** (d / 20):g}" for d in ticks_db])
    sec.set_ylabel(label)
    return sec


def plot_plant(plt, freqs, g_vd):
    f_lc, f_esr = plant_landmarks()
    keep = freqs <= F_PLOT_MAX
    f, g = freqs[keep], g_vd[keep]
    swing_mv = np.abs(g)          # |G_vd| volts per unit duty = mV per 0.1 % duty
    phase = np.degrees(np.unwrap(np.angle(g)))
    i_pk = np.argmax(swing_mv)
    slow = swing_mv[0]
    fast_f = 50e3
    fast = np.interp(np.log10(fast_f), np.log10(f), swing_mv)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("1. The power stage on its own (no controller yet)\n"
                 "Wiggle the duty cycle up and down by ±0.1 % at different speeds: "
                 "how much does the output wiggle, and how late?")

    ax1.plot(f, swing_mv, color="tab:blue", lw=2)
    ax1.set_yscale("log")
    ax1.set_ylim(0.05, 2000)
    ax1.set_ylabel("How much the output wiggles\n(mV, for a ±0.1 % duty wiggle)")
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda y, _p: f"{y:g}"))
    ax_db = ax1.twinx()
    ax_db.set_yscale("log")
    ax_db.set_ylim(ax1.get_ylim())
    db_ticks = [-20, 0, 20, 40, 60]
    ax_db.set_yticks([10 ** (d / 20) for d in db_ticks])
    ax_db.set_yticklabels([f"{d} dB" for d in db_ticks])
    ax_db.yaxis.set_minor_formatter(NullFormatter())
    ax_db.tick_params(axis="y", which="minor", right=False)
    ax_db.set_ylabel("same thing in dB\n(engineering units)")

    ax1.annotate(f"Slow wiggles: the output simply follows.\n"
                 f"0.1 % of 48 V = {slow:.0f} mV", xy=(30, slow), xytext=(15, slow * 6),
                 bbox=BOX, arrowprops=dict(arrowstyle="->", lw=0.8))
    ax1.annotate(f"{f_lc/1e3:.1f} kHz: LC resonance (the 'spring').\n"
                 f"The output over-reacts: {swing_mv[i_pk]:.0f} mV, "
                 f"about {swing_mv[i_pk]/slow:.0f}× the slow value", xy=(f[i_pk], swing_mv[i_pk]),
                 xytext=(f_lc * 1.6, swing_mv[i_pk] * 3), bbox=BOX,
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    ax1.annotate(f"Fast wiggles: the inductor and capacitors\nsmooth them out "
                 f"({fast_f/1e3:.0f} kHz → {fast:.1f} mV)", xy=(fast_f, fast),
                 xytext=(1.2e3, 0.12), bbox=BOX, arrowprops=dict(arrowstyle="->", lw=0.8))

    ax2.plot(f, phase, color="tab:blue", lw=2)
    ax2.set_ylabel("How late the output is\n(degrees of one wiggle)")
    ax2.set_xlabel("How fast the duty cycle is wiggled up and down")
    ax2.set_ylim(-200, 20)
    for y, txt in ((0, "on time"), (-90, "¼ wiggle late"), (-180, "½ wiggle late")):
        ax2.axhline(y, color="0.5", lw=0.8, ls="--")
        ax2.text(F_PLOT_MAX * 0.97, y + 4, txt, ha="right", fontsize=8, color="0.35")
    ax2.text(15, -40, "Below the resonance the\noutput keeps up (≈ 0°)", bbox=BOX)
    ax2.text(f_lc * 1.55, -62, "Past the resonance it lags by\nalmost half a wiggle", bbox=BOX)

    for ax in (ax1, ax2):
        freq_axes(ax)
        ax.axvline(f_lc, color="tab:red", ls="--", lw=1)
        ax.axvline(f_esr, color="tab:green", ls="--", lw=1)
    ax2.text(f_esr * 1.08, -165, f"{f_esr/1e3:.1f} kHz: the polymer capacitor's\n"
             "resistance (ESR) gives some phase back", color="tab:green", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "01_plant_bode.png"), dpi=150)
    return fig


def plot_loop(plt, freqs, g_vd, ctrl, m, alt_ctrl, alt_m):
    n = ctrl["n_cycles"]
    loop, g_c = digital_loop_gain(freqs, g_vd, ctrl["b_z"], ctrl["a_z"], n)
    keep = freqs <= F_PLOT_MAX
    f = freqs[keep]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.5), sharex=True)
    fig.suptitle("2. The whole control loop: controller × power stage × MCU delay\n"
                 "Check 1: where the loop gain crosses ×1 (loop speed).   "
                 "Check 2: how far the phase is from −180° (stability).")

    # Shaded zones either side of crossover.
    ax1.axvspan(10, m["fc"], color="tab:green", alpha=0.06)
    ax1.axvspan(m["fc"], F_PLOT_MAX, color="tab:red", alpha=0.05)
    ax1.text(14, 68, "Loop gain above ×1: disturbances this slow get corrected", color="tab:green")
    ax1.text(m["fc"] * 1.06, 75, "Below ×1: too fast\nfor the loop", color="tab:red", va="top")

    ax1.plot(f, 20 * np.log10(np.abs(g_vd[keep])), color="0.6", lw=1, label="Power stage alone (plot 1)")
    ax1.plot(f, 20 * np.log10(np.abs(g_c[keep])), color="tab:orange", lw=1, label="Controller alone")
    ax1.plot(f, 20 * np.log10(m["mag"][keep]), color="tab:blue", lw=2.2,
             label="Whole loop (controller × power stage × delay)")
    ax2.plot(f, m["phase"][keep], color="tab:blue", lw=2.2, label=f"Whole loop: phase margin {m['pm']:.0f}°")
    if alt_m is not None:
        na = alt_ctrl["n_cycles"]
        ka = freqs <= 0.8 * FSW / (2 * na)
        every = "every cycle" if na == 1 else f"every {na}{'nd' if na == 2 else 'th'} cycle"
        ax1.plot(freqs[ka], 20 * np.log10(alt_m["mag"][ka]), color="tab:purple", lw=1.2, ls="--",
                 label=f"Same controller if the ISR ran {every}")
        ax2.plot(freqs[ka], alt_m["phase"][ka], color="tab:purple", lw=1.2, ls="--",
                 label=f"ISR {every}: phase margin {alt_m['pm']:.0f}° (more delay, less margin)")

    ax1.axhline(0, color="k", lw=1)
    ax1.text(14, 2, "0 dB = ×1", fontsize=8)
    ax1.axvline(m["fc"], color="k", ls="--", lw=0.9)
    ax1.text(m["fc"] * 0.93, -50, f"Crossover\n{m['fc']/1e3:.0f} kHz\n(loop speed)", ha="right", bbox=BOX)
    ax1.set_ylabel("Loop gain (dB)")
    ax1.set_ylim(-60, 80)
    times_axis(ax1, [-40, -20, 0, 20, 40, 60], "correction strength\n(times)")
    ax1.legend(loc="lower left", bbox_to_anchor=(0.0, 0.13))

    ax2.axhline(-180, color="tab:red", lw=1.2, ls=":")
    ax2.text(14, -186, "−180°: the correction arrives half a cycle late and pushes the wrong way → oscillation",
             color="tab:red", fontsize=8, va="top")
    ax2.axvline(m["fc"], color="k", ls="--", lw=0.9)
    ph_c = m["pm"] - 180
    ax2.annotate("", xy=(m["fc"], -180), xytext=(m["fc"], ph_c),
                 arrowprops=dict(arrowstyle="<->", color="tab:green", lw=1.8))
    ax2.text(m["fc"] * 0.93, -157, f"Phase margin {m['pm']:.0f}°\n(distance from −180°\nat the crossover)",
             ha="right", va="center", color="tab:green", bbox=BOX)

    if m["gm"] is not None:
        mag_gm = 20 * np.log10(np.interp(np.log10(m["f_gm"]), np.log10(freqs), m["mag"]))
        for ax in (ax1, ax2):
            ax.axvline(m["f_gm"], color="tab:purple", ls=":", lw=0.9)
        ax2.plot([m["f_gm"]], [-180], "o", color="tab:red")
        ax2.text(m["f_gm"] * 1.07, -172, "−180° here", fontsize=8, color="tab:red")
        ax1.annotate("", xy=(m["f_gm"], 0), xytext=(m["f_gm"], mag_gm),
                     arrowprops=dict(arrowstyle="<->", color="tab:purple", lw=1.8))
        ax1.text(m["f_gm"] * 0.94, 32, f"Gain margin\n{m['gm']:.1f} dB (×{10 ** (m['gm'] / 20):.1f}\n"
                 "before oscillation)", color="tab:purple", ha="right", bbox=BOX)

    ax2.set_ylabel("Loop phase: how late\nthe correction is (degrees)")
    ax2.set_ylim(-270, 45)
    ax2.set_xlabel("Frequency of the disturbance")
    ax2.legend(loc="lower left")
    for ax in (ax1, ax2):
        freq_axes(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "02_loop_bode.png"), dpi=150)
    return fig


def mark_events(axes, label_ax=None):
    events = [(SOFTSTART_TIME, None), (T_LOAD_ON, None), (T_STEP_UP, None), (T_STEP_DOWN, None)]
    for ax in axes:
        for t_ev, _ in events:
            ax.axvline(t_ev * 1e3, **EVENT_STYLE)


def plot_time(plt, rec, met, margins_pm=None):
    t_ms = rec["t"] * 1e3
    soft_i = (C_CER + C_POLY) * VOUT_TARGET / SOFTSTART_TIME
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9.5), sharex=True)
    fig.suptitle("3. Time simulation: start-up, then a sudden load change and back\n"
                 "(like watching the board on an oscilloscope)")

    # --- Output voltage ---
    ax1.plot(t_ms, rec["ref"], color="0.55", lw=1.2, ls="--", label="Target set by firmware (reference)")
    ax1.plot(t_ms, rec["vout"], color="tab:blue", lw=1.6, label="Output voltage")
    ax1.set_title("Output voltage", loc="left", fontweight="bold")
    ax1.set_ylabel("Volts")
    ax1.set_ylim(-0.5, 14.5)
    ax1.text(0.08, 10.6, "Soft-start: the target ramps\n0 → 12 V over 2 ms", bbox=BOX)
    ax1.text(T_LOAD_ON * 1e3 + 0.08, 6.0, f"{I_LIGHT:g} A load\nconnected", bbox=BOX)
    ax1.text(T_STEP_UP * 1e3 + 0.08, 6.0, f"Load jumps to {I_HEAVY:g} A\noutput dips {met['dip']*1e3:.0f} mV\n"
             f"(too small to see at this scale:\nsee plot 3b)", bbox=BOX)
    ax1.text(T_STEP_DOWN * 1e3 + 0.08, 6.0, f"Load drops back\nto {I_LIGHT:g} A",
             bbox=BOX)
    ax1.legend(loc="lower right")

    # --- Currents ---
    ax2.plot(t_ms, rec["il"], color="tab:orange", lw=1.2, label="Inductor current (what the converter supplies)")
    ax2.plot(t_ms, rec["iload"], color="k", lw=1, ls="--", label="Load current (what the load takes)")
    ax2.set_title("Currents", loc="left", fontweight="bold")
    ax2.set_ylabel("Amps")
    ax2.set_ylim(-7, 21)
    ax2.annotate(f"≈ {soft_i:.1f} A just to charge the\noutput capacitors during soft-start",
                 xy=(1.0, soft_i), xytext=(0.15, 9), bbox=BOX, arrowprops=dict(arrowstyle="->", lw=0.8))
    k_pk = np.argmax(np.where(rec["t"] >= T_STEP_UP, rec["il"], -np.inf))
    ax2.annotate(f"Overshoots to {met['il_peak']:.1f} A\nto refill the capacitors",
                 xy=(t_ms[k_pk], rec["il"][k_pk]), xytext=(T_STEP_UP * 1e3 + 0.35, 17), bbox=BOX,
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    k_mn = np.argmin(np.where(rec["t"] >= T_STEP_DOWN, rec["il"], np.inf))
    ax2.annotate(f"Briefly {met['il_min']:.1f} A: current flows\nback toward the 48 V input",
                 xy=(t_ms[k_mn], rec["il"][k_mn]), xytext=(T_STEP_DOWN * 1e3 + 0.35, -5.8), bbox=BOX,
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    ax2.legend(loc="upper left")

    # --- Duty cycle ---
    ax3.plot(t_ms, rec["duty"] * 100, color="tab:green", lw=1)
    ax3.axhline(VOUT_TARGET / VIN * 100, color="0.5", lw=0.8, ls="--")
    ax3.text(T_END * 1e3 * 0.995, VOUT_TARGET / VIN * 100 + 1.5,
             f"12 V ÷ 48 V = {VOUT_TARGET/VIN*100:.0f} %", ha="right", fontsize=8, color="0.35")
    ax3.set_title("Duty cycle: the controller's output (fraction of each switching cycle the top FET is on)",
                  loc="left", fontweight="bold")
    ax3.set_ylabel("Percent")
    ax3.set_ylim(0, 55)
    ax3.text(0.08, 40, "Rises with the soft-start ramp", bbox=BOX)
    ax3.text(T_STEP_UP * 1e3 + 0.35, 40, "Spikes: the controller reacting to\nthe load change, then settling back",
             bbox=BOX)
    ax3.set_xlabel("Time (ms)")
    ax3.set_xlim(0, T_END * 1e3)
    for ax in (ax1, ax2, ax3):
        ax.grid(True, alpha=0.3)
    mark_events((ax1, ax2, ax3))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "03_time_response.png"), dpi=150)

    # --- Zoom on the load step ---
    fig2, ax = plt.subplots(figsize=(10, 4.8))
    w = (rec["t"] > T_STEP_UP - 0.1e-3) & (rec["t"] < T_STEP_UP + 0.5e-3)
    t_us = (rec["t"][w] - T_STEP_UP) * 1e6
    err_mv = (rec["vout"][w] - VOUT_TARGET) * 1e3
    band = SETTLE_BAND * VOUT_TARGET * 1e3
    ax.axhspan(-band, band, color="tab:green", alpha=0.15)
    ax.text(480, band - 12, f"settled = within ±{band:.0f} mV of 12 V", ha="right", color="tab:green")
    ax.plot(t_us, err_mv, color="tab:blue", lw=1.8)
    ax.axhline(0, color="0.5", lw=0.8)
    ax.axvline(0, color="k", lw=0.9, ls="--")
    ax.text(-95, -150, f"Load jumps\n{I_LIGHT:g} A → {I_HEAVY:g} A\nhere ►", bbox=BOX)
    i_min = np.argmin(err_mv)
    ax.plot([t_us[i_min]], [err_mv[i_min]], "o", color="tab:red")
    ax.annotate(f"Lowest point: {err_mv[i_min]:.0f} mV,\n{t_us[i_min]:.0f} µs after the jump",
                xy=(t_us[i_min], err_mv[i_min]), xytext=(60, -330), bbox=BOX,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    t_set = met["settle_up"] * 1e6
    ax.axvline(t_set, color="tab:green", lw=1, ls="--")
    ax.annotate(f"Back inside the band\nafter {t_set:.0f} µs", xy=(t_set, -band),
                xytext=(t_set + 60, -190), bbox=BOX, arrowprops=dict(arrowstyle="->", lw=0.8))
    if margins_pm is not None and margins_pm > 60:
        ring_note = (f"No ringing: with {margins_pm:.0f}° of phase margin the output climbs back smoothly.\n"
                     "Plot 5 shows a board with less margin: that one rings.")
    else:
        ring_note = ("The wiggles on the way back are ringing.\n"
                     "Less phase margin (plot 2) means more, bigger wiggles.")
    ax.text(200, -265, ring_note, bbox=BOX)
    ax.set_xlabel(f"Time after the load jumps (µs)")
    ax.set_ylabel("Output error (mV)\n= output − 12 V")
    ax.set_title("3b. Zoom on the load jump: how far the output dips and how fast it recovers",
                 loc="left", fontweight="bold")
    ax.set_xlim(-100, 500)
    ax.set_ylim(min(-400, err_mv.min() * 1.1), 90)
    ax.grid(True, alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUT_DIR, "03b_load_step_zoom.png"), dpi=150)
    return fig, fig2


def plot_pwm_resolution(plt, rec_hr, rec_plain):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    w = (rec_hr["t"] > T_STEP_UP - 0.5e-3) & (rec_hr["t"] < T_STEP_UP)
    t_us = (rec_hr["t"][w] - (T_STEP_UP - 0.5e-3)) * 1e6
    q_plain, q_hr = duty_step(False), duty_step(True)
    lab_plain = f"Without HRPWM: duty moves in {q_plain*100:.2f} % steps (= {q_plain*VIN*1e3:.0f} mV of output)"
    lab_hr = f"With HRPWM: duty moves in {q_hr*100:.3f} % steps (= {q_hr*VIN*1e3:.1f} mV of output)"
    adc_lsb_mv = ADC_VREF / 2 ** ADC_BITS / VOUT_DIVIDER * 1e3

    ax1.plot(t_us, (rec_plain["vout"][w] - VOUT_TARGET) * 1e3, color="tab:red", lw=1.1, label=lab_plain)
    ax1.plot(t_us, (rec_hr["vout"][w] - VOUT_TARGET) * 1e3, color="tab:blue", lw=1.8, label=lab_hr)
    ax1.set_title("Output voltage", loc="left", fontweight="bold")
    ax1.set_ylabel("Output error (mV)\n= output − 12 V")
    span = max(7.0, 1.3 * 1e3 * max(np.abs(rec_plain["vout"][w] - VOUT_TARGET).max(),
                                     np.abs(rec_hr["vout"][w] - VOUT_TARGET).max()))
    ax1.set_ylim(-span, span * 1.25)
    ax1.legend(loc="upper left")
    ax1.text(495, -0.9 * span, f"Both wobble a little because the 12-bit ADC reads the output "
             f"in {adc_lsb_mv:.0f} mV steps", ha="right", fontsize=8, bbox=BOX)

    ax2.step(t_us, rec_plain["duty"][w] * 100, color="tab:red", lw=1.1, where="post")
    ax2.step(t_us, rec_hr["duty"][w] * 100, color="tab:blue", lw=1.8, where="post")
    ax2.set_title("Duty cycle the controller actually gets", loc="left", fontweight="bold")
    ax2.set_ylabel("Duty (%)")
    ax2.set_xlabel(f"Time (µs), half a millisecond of steady running at {I_LIGHT:g} A")
    fig.suptitle("4. PWM resolution: the duty cycle can only change in fixed steps\n"
                 "Coarse steps (red) can't land on the right value, so the controller keeps "
                 "jumping between neighbouring steps")
    for ax in (ax1, ax2):
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "04_pwm_resolution.png"), dpi=150)
    return fig


# =============================================================================
# 4. WORST CASE — the same controller with every part at the edge of its range
# =============================================================================
#
# Real parts are not exactly their nominal values. The controller is fixed in
# firmware, so it has to stay stable for every board you build, at every
# temperature, for the life of the product. This section re-checks the loop
# with every combination of: polymer ESR (low / nominal / hot max / end of
# life), inductance (low / nominal / high), polymer capacitance (-20 % / 0 /
# +20 %) and input voltage (min / max).

@contextmanager
def parts(**overrides):
    """Temporarily change module parameters, e.g. with parts(L=5e-6): ..."""
    g = globals()
    old = {k: g[k] for k in overrides}
    g.update(overrides)
    try:
        yield
    finally:
        g.update(old)


def corner_list():
    l_min = L * (1 - L_TOL) * (1 - L_SAG_FULL_LOAD)   # low tolerance and sagging at full load
    l_max = L * (1 + L_TOL)                           # high tolerance, light load
    corners = []
    for esr in (ESR_POLY_MIN, ESR_POLY, ESR_POLY_MAX, ESR_POLY_EOL):
        for ind in (l_min, L, l_max):
            for cap in (C_POLY * (1 - C_POLY_TOL), C_POLY, C_POLY * (1 + C_POLY_TOL)):
                for vin in (VIN_MIN, VIN_MAX):
                    corners.append(dict(ESR_POLY=esr, L=ind, C_POLY=cap, VIN=vin))
    return corners


def describe(corner):
    return (f"ESR {corner['ESR_POLY']*1e3:.1f} mΩ, L {corner['L']*1e6:.2f} µH, "
            f"C_poly {corner['C_POLY']*1e6:.0f} µF, VIN {corner['VIN']:.0f} V")


def worst_case(freqs, ctrl):
    results = []
    for corner in corner_list():
        with parts(**corner):
            g = plant_seen_by_controller(freqs)
        loop, _ = digital_loop_gain(freqs, g, ctrl["b_z"], ctrl["a_z"], ctrl["n_cycles"])
        m = margins(freqs, loop)
        if m is None:
            continue
        m["corner"] = corner
        m["eol"] = corner["ESR_POLY"] == ESR_POLY_EOL
        results.append(m)
    new = [r for r in results if not r["eol"]]
    eol = [r for r in results if r["eol"]]

    def gm_or_inf(r):
        return r["gm"] if r["gm"] is not None else np.inf

    return dict(
        all=results,
        new_pm=min(new, key=lambda r: r["pm"]), new_gm=min(new, key=gm_or_inf),
        eol_pm=min(eol, key=lambda r: r["pm"]), eol_gm=min(eol, key=gm_or_inf),
        fc_range=(min(r["fc"] for r in new), max(r["fc"] for r in new)),
    )


def plot_worst_case(plt, freqs, m_nom, wc, rec_nom, rec_worst):
    keep = freqs <= F_PLOT_MAX
    f = freqs[keep]
    worst = wc["new_pm"]
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 11),
                                        gridspec_kw=dict(height_ratios=[1, 1, 0.9]))
    fig.suptitle("5. Worst case: the same controller with every part at the edge of its tolerance\n"
                 "Each thin grey line is one combination of capacitor ESR, inductance, capacitance "
                 "and input voltage")
    for r in wc["all"]:
        if r["eol"]:
            continue
        ax1.plot(f, 20 * np.log10(r["mag"][keep]), color="0.75", lw=0.6)
        ax2.plot(f, r["phase"][keep], color="0.75", lw=0.6)
    ax1.plot(f, 20 * np.log10(m_nom["mag"][keep]), color="tab:blue", lw=2.2, label="Nominal parts")
    ax2.plot(f, m_nom["phase"][keep], color="tab:blue", lw=2.2, label=f"Nominal: phase margin {m_nom['pm']:.0f}°")
    ax1.plot(f, 20 * np.log10(worst["mag"][keep]), color="tab:red", lw=2,
             label="Worst combination: " + describe(worst["corner"]))
    ax2.plot(f, worst["phase"][keep], color="tab:red", lw=2,
             label=f"Worst combination: phase margin {worst['pm']:.0f}°")
    ax1.axhline(0, color="k", lw=1)
    lo, hi = wc["fc_range"]
    ax1.axvspan(lo, hi, color="tab:orange", alpha=0.15)
    ax1.text(hi * 1.08, 30, f"Crossover moves\nbetween {lo/1e3:.0f} and {hi/1e3:.0f} kHz\n"
             "as the parts vary", bbox=BOX)
    ax1.set_ylabel("Loop gain (dB)")
    ax1.set_ylim(-60, 80)
    ax1.legend(loc="lower left")
    ax2.axhline(-180, color="tab:red", lw=1.2, ls=":")
    ax2.text(14, -186, "−180°: oscillation line", color="tab:red", fontsize=8, va="top")
    ax2.set_ylabel("Loop phase (degrees)")
    ax2.set_ylim(-270, 45)
    ax2.set_xlabel("Frequency of the disturbance")
    ax2.legend(loc="lower left")
    for ax in (ax1, ax2):
        freq_axes(ax)

    w = (rec_nom["t"] > T_STEP_UP - 0.05e-3) & (rec_nom["t"] < T_STEP_UP + 0.6e-3)
    t_us = (rec_nom["t"][w] - T_STEP_UP) * 1e6
    band = SETTLE_BAND * VOUT_TARGET * 1e3
    ax3.axhspan(-band, band, color="tab:green", alpha=0.15)
    ax3.plot(t_us, (rec_nom["vout"][w] - VOUT_TARGET) * 1e3, color="tab:blue", lw=1.8, label="Nominal parts")
    ax3.plot(t_us, (rec_worst["vout"][w] - VOUT_TARGET) * 1e3, color="tab:red", lw=1.5,
             label="Worst combination")
    ax3.axvline(0, color="k", lw=0.9, ls="--")
    ax3.set_title(f"The load jump ({I_LIGHT:g} A → {I_HEAVY:g} A) on both boards", loc="left", fontweight="bold")
    ax3.set_xlabel("Time after the load jumps (µs)")
    ax3.set_ylabel("Output error (mV)")
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "05_worst_case.png"), dpi=150)
    return fig


# =============================================================================
# SUMMARY
# =============================================================================

def verdict_pm(pm):
    if pm < 30:
        return "RISKY: expect ringing or oscillation"
    if pm < 45:
        return "marginal: works, but rings after load steps"
    if pm <= 70:
        return "good (aim for 45–60°)"
    return "very safe, possibly slower than it could be"


def verdict_gm(gm):
    if gm is None:
        return "phase never reaches −180° below the Nyquist limit"
    return "good (aim for > 6 dB)" if gm > 6 else "LOW: raise it before trusting the design"


def print_summary(ctrl, m, alt_ctrl, alt_m, met, met_plain, wc, met_worst):
    f_lc, f_esr = plant_landmarks()
    n = ctrl["n_cycles"]
    t_delay = (COMPUTE_DELAY_CYCLES + n / 2) / FSW
    print()
    print("=" * 72)
    print(" HexaGaN 48 V -> 12 V GaN buck: voltage-mode control simulation")
    print("=" * 72)
    print("\nPLANT (the power stage on its own)")
    print(f"  LC resonance, the 'spring' bounce : {f_lc/1e3:6.2f} kHz")
    print(f"  Polymer-capacitor ESR zero        : {f_esr/1e3:6.2f} kHz")
    print(f"\nCONTROLLER (Type III), ISR every {n} PWM cycle(s) = {FSW/n/1e3:.0f} kHz")
    print(f"  Zeros: {ctrl['fz1']/1e3:.2f} kHz, {ctrl['fz2']/1e3:.2f} kHz   "
          f"Poles: 0 Hz (integrator), {ctrl['fp1']/1e3:.1f} kHz, {ctrl['fp2']/1e3:.1f} kHz")
    print("  Digital coefficients, u[n] = b0 e[n] + b1 e[n-1] + b2 e[n-2] + b3 e[n-3]")
    print("                               - a1 u[n-1] - a2 u[n-2] - a3 u[n-3]")
    print("  (check the sign convention of the DCL structure you use in firmware)")
    for i, v in enumerate(ctrl["b_z"]):
        print(f"    b{i} = {v: .8e}")
    for i, v in enumerate(ctrl["a_z"][1:], start=1):
        print(f"    a{i} = {v: .8e}")
    print("\nLOOP")
    print(f"  Crossover (how fast it reacts)    : {m['fc']/1e3:6.1f} kHz   (target {F_CROSSOVER/1e3:.1f} kHz)")
    print(f"  Phase margin (stability safety)   : {m['pm']:6.1f} °     {verdict_pm(m['pm'])}")
    gm_txt = f"{m['gm']:6.1f} dB" if m["gm"] is not None else "   n/a  "
    print(f"  Gain margin                       : {gm_txt}    {verdict_gm(m['gm'])}")
    print(f"  Digital delay                     : {t_delay*1e6:6.2f} µs  -> costs "
          f"{360*m['fc']*t_delay:.0f}° of phase at crossover")
    if alt_m is not None:
        print(f"  If the ISR ran every {alt_ctrl['n_cycles']} cycles     : phase margin {alt_m['pm']:.0f}° "
              f"(same controller, different delay)")
    print("\nTIME SIMULATION")
    print(f"  Soft-start overshoot              : {met['softstart_overshoot']*1e3:6.0f} mV")
    print(f"  Load step {I_LIGHT:.2f} -> {I_HEAVY:.2f} A, dip    : {met['dip']*1e3:6.0f} mV, "
          f"back within ±{SETTLE_BAND*VOUT_TARGET*1e3:.0f} mV in {met['settle_up']*1e6:.0f} µs")
    print(f"  Load release, overshoot           : {met['overshoot']*1e3:6.0f} mV, "
          f"settles in {met['settle_down']*1e6:.0f} µs")
    ripple_half = (VIN - VOUT_TARGET) * (VOUT_TARGET / VIN) / (L * FSW) / 2
    print(f"  Inductor current during the step  : peaks at {met['il_peak']:.1f} A average "
          f"(+{ripple_half:.2f} A ripple = {met['il_peak'] + ripple_half:.1f} A instantaneous);")
    print(f"                                      dips to {met['il_min']:.1f} A on release")
    print(f"  Soft-start charging current       : {(C_CER + C_POLY) * VOUT_TARGET / SOFTSTART_TIME:.1f} A "
          f"just to charge the output capacitors")
    print(f"  Steady-state wobble, HRPWM on     : {met['wobble_pp']*1e3:6.1f} mV p-p")
    print(f"  Steady-state wobble, HRPWM off    : {met_plain['wobble_pp']*1e3:6.1f} mV p-p")
    print("\nWORST CASE (same controller, parts at the edges of their tolerances)")
    print(f"  Crossover moves between           : {wc['fc_range'][0]/1e3:.1f} and {wc['fc_range'][1]/1e3:.1f} kHz")
    for label, key_pm, key_gm in (("New parts", "new_pm", "new_gm"), ("End of life", "eol_pm", "eol_gm")):
        r_pm, r_gm = wc[key_pm], wc[key_gm]
        gm_txt = f"{r_gm['gm']:.1f} dB" if r_gm["gm"] is not None else "n/a"
        print(f"  {label:<12} worst phase margin : {r_pm['pm']:6.1f} °     {verdict_pm(r_pm['pm'])}")
        print(f"                 at                 {describe(r_pm['corner'])}")
        print(f"  {label:<12} worst gain margin  : {gm_txt:>8}    {verdict_gm(r_gm['gm'])}")
        print(f"                 at                 {describe(r_gm['corner'])}")
    print(f"  Load-step dip at the worst corner : {met_worst['dip']*1e3:6.0f} mV, "
          f"settles in {met_worst['settle_up']*1e6:.0f} µs")
    print(f"  Input-voltage feedforward         : {'on' if USE_VIN_FEEDFORWARD else 'OFF'}")
    print(f"\nPlots saved in {OUT_DIR}")
    print("Remember: this is an averaged model. Real switching ripple (~27 mV p-p at 400 kHz)")
    print("comes on top of these numbers, and every ASSUMED parameter should be updated.\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    global LOOP_EVERY_N_CYCLES, USE_HRPWM, F_CROSSOVER
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", action="store_true", help="open plot windows as well as saving them")
    parser.add_argument("--every", type=int, help="run the control ISR every N PWM cycles")
    parser.add_argument("--fc", type=float, help="target crossover frequency in kHz")
    parser.add_argument("--no-hrpwm", action="store_true", help="simulate the main run without HRPWM")
    args = parser.parse_args()
    if args.every:
        LOOP_EVERY_N_CYCLES = args.every
    if args.fc:
        F_CROSSOVER = args.fc * 1e3
    if args.no_hrpwm:
        USE_HRPWM = False

    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    setup_style(plt)

    os.makedirs(OUT_DIR, exist_ok=True)
    n = LOOP_EVERY_N_CYCLES
    freqs = np.logspace(1, np.log10(0.5 * FSW / n * 0.999), 3000)
    g_vd = plant_duty_to_vout(freqs, *build_plant())     # the power stage itself (plot 1)
    g_ctrl = plant_seen_by_controller(freqs)             # including feedforward

    ctrl = design_controller(freqs, g_ctrl, n)
    loop, _ = digital_loop_gain(freqs, g_ctrl, ctrl["b_z"], ctrl["a_z"], n)
    m = margins(freqs, loop)
    if m is None:
        raise SystemExit("The loop gain never crosses 0 dB: check the parameters.")

    # Comparison: the same continuous controller, run at a different loop rate.
    n_alt = 2 if n == 1 else 1
    alt_ctrl = dict(ctrl, n_cycles=n_alt)
    alt_ctrl["b_z"], alt_ctrl["a_z"] = discretize(ctrl["num"], ctrl["den"], n_alt / FSW)
    alt_loop, _ = digital_loop_gain(freqs, g_ctrl, alt_ctrl["b_z"], alt_ctrl["a_z"], n_alt)
    alt_m = margins(freqs, alt_loop)

    rec = simulate(ctrl, USE_HRPWM)
    met = step_metrics(rec)
    rec_plain = simulate(ctrl, use_hrpwm=False) if USE_HRPWM else rec
    rec_hr = rec if USE_HRPWM else simulate(ctrl, use_hrpwm=True)
    met_plain = step_metrics(rec_plain)

    wc = worst_case(freqs, ctrl)
    with parts(**wc["new_pm"]["corner"]):
        rec_worst = simulate(ctrl, USE_HRPWM)
    met_worst = step_metrics(rec_worst)

    plot_plant(plt, freqs, g_vd)
    plot_loop(plt, freqs, g_ctrl, ctrl, m, alt_ctrl, alt_m)
    plot_time(plt, rec, met, m["pm"])
    plot_pwm_resolution(plt, rec_hr, rec_plain)
    plot_worst_case(plt, freqs, m, wc, rec, rec_worst)
    print_summary(ctrl, m, alt_ctrl, alt_m, met, met_plain, wc, met_worst)
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
