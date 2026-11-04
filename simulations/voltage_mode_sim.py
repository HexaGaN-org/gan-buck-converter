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

It is an *averaged* model: switching ripple is not shown, only the average
behavior the control loop sees. See README.md for what each plot means and
what to try.

Run:   python voltage_mode_sim.py            (plots saved to ./output)
       python voltage_mode_sim.py --show     (also open plot windows)
       python voltage_mode_sim.py --help     (all options)
"""

import argparse
import os

import numpy as np
import matplotlib
from scipy.linalg import expm
from scipy.signal import cont2discrete

# =============================================================================
# PARAMETERS — change these and rerun. Sources are noted on every line.
# "ASSUMED" means the value is not decided yet; update it when it is.
# =============================================================================

# --- Operating point (docs/specifications.md) ---
VIN = 48.0             # V, input voltage
VOUT_TARGET = 12.0     # V, output voltage
FSW = 400e3            # Hz, switching frequency (power_stage.md decision #4)

# --- Inductor and resistances in the current path (docs/design/power_stage.md) ---
L = 6.8e-6             # H, SLB2212P6R8MTT
R_DCR = 2.1e-3         # ohm, inductor winding resistance (datasheet)
R_SHUNT = 1e-3         # ohm, current-sense shunt R301
R_FET = 5e-3           # ohm, hot R_DS(on) averaged over both FETs (3.3 mOhm x 1.5)
R_PCB = 1e-3           # ohm, copper traces — ASSUMED

# --- Output capacitors (power_stage.md decision #10) ---
C_CER = 39e-6          # F, 8 x 22 uF ceramics after DC-bias derating (effective)
ESR_CER = 0.5e-3       # ohm, whole ceramic bank — ASSUMED (~4 mOhm each, 8 in parallel)
C_POLY = 470e-6        # F, polymer bulk capacitor C319
ESR_POLY = 25e-3       # ohm, C319 datasheet

# --- Load ---
# None = electronic load in constant-current mode (the least damping, so the
# worst case for stability). Set a number in ohms for a resistive load.
LOAD_R = None

# --- Digital controller timing (docs/firmware/firmware-requirements.md) ---
LOOP_EVERY_N_CYCLES = 1     # control ISR runs every N PWM periods
COMPUTE_DELAY_CYCLES = 1.0  # PWM periods from ADC sample to new duty taking effect
F_TBCLK = 120e6             # Hz, ePWM time-base clock (300 counts per period at 400 kHz)
USE_HRPWM = True            # high-resolution PWM (required by the firmware guide)
HRPWM_STEP = 150e-12        # s, HRPWM fine step (~150 ps, power_stage.md)
D_MIN, D_MAX = 0.0, 0.60    # duty-cycle clamp

# --- Output-voltage measurement (sensing sheet — not designed yet) ---
ADC_BITS = 12
ADC_VREF = 3.3              # V
VOUT_DIVIDER = 0.2          # VOUT_SENSE = 0.2 x VOUT -> 16.5 V full scale — ASSUMED

# --- Controller design targets ---
F_CROSSOVER = 20e3          # Hz, target loop speed. power_stage.md assumes ~25 kHz, but with
                            # the 3.75 us digital delay 25 kHz leaves only ~5 dB gain margin;
                            # 20 kHz gives ~60 deg phase margin and ~7 dB gain margin.
# Type III placement. None = choose automatically from the plant:
#   both zeros a little below the LC resonance (0.6 x f_LC), first pole just
#   above crossover (1.25 x F_CROSSOVER, which also roughly cancels the polymer
#   ESR zero's effect), second pole at 0.45 x the control rate.
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
    resp = np.empty(len(freqs), dtype=complex)
    eye = np.eye(a.shape[0])
    for i, f in enumerate(freqs):
        s = 2j * np.pi * f
        resp[i] = c_out @ np.linalg.solve(s * eye - a, b[:, 0]) + d_out[0]
    return VIN * resp


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
    fz1 = FZ1 if FZ1 is not None else 0.6 * f_lc
    fz2 = FZ2 if FZ2 is not None else 0.6 * f_lc
    fp1 = FP1 if FP1 is not None else 1.25 * F_CROSSOVER
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
    g_vd_probe = plant_duty_to_vout(f_probe, *build_plant())
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

def style_axes(ax):
    ax.grid(True, which="both", alpha=0.3)
    ax.set_xscale("log")


def plot_plant(plt, freqs, g_vd):
    f_lc, f_esr = plant_landmarks()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    fig.suptitle("1. The plant: how the output voltage responds to duty-cycle changes\n"
                 "(no controller yet — this is the power stage on its own)", fontsize=11)
    ax1.plot(freqs, 20 * np.log10(np.abs(g_vd)), color="tab:blue")
    ax1.set_ylabel("Gain (dB)")
    ax2.plot(freqs, np.degrees(np.unwrap(np.angle(g_vd))), color="tab:blue")
    ax2.set_ylabel("Phase (degrees)")
    ax2.set_xlabel("Frequency of the duty-cycle wiggle (Hz)")
    for ax in (ax1, ax2):
        style_axes(ax)
        ax.axvline(f_lc, color="tab:red", ls="--", lw=1)
        ax.axvline(f_esr, color="tab:green", ls="--", lw=1)
    ax1.annotate(f"LC resonance ({f_lc/1e3:.1f} kHz)\nthe 'spring' bounce:\n"
                 "a peak, then the gain falls fast", xy=(f_lc, 20 * np.log10(np.abs(g_vd)).max()),
                 xytext=(f_lc * 11, 20 * np.log10(np.abs(g_vd)).max() - 8), fontsize=8,
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    ax2.text(f_lc * 1.1, -30, "phase drops ~180°\nat the resonance", fontsize=8, color="tab:red")
    ax2.text(f_esr * 1.1, -150, f"polymer ESR zero\n({f_esr/1e3:.1f} kHz)\ngives some phase back",
             fontsize=8, color="tab:green")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "01_plant_bode.png"), dpi=150)
    return fig


def plot_loop(plt, freqs, g_vd, ctrl, m, alt_ctrl, alt_m):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True)
    fig.suptitle("2. The full loop: controller × plant × digital delay\n"
                 "Crossover = how fast the loop reacts. Phase margin = how far it is from oscillating.",
                 fontsize=11)
    loop, g_c = digital_loop_gain(freqs, g_vd, ctrl["b_z"], ctrl["a_z"], ctrl["n_cycles"])
    n = ctrl["n_cycles"]
    ax1.plot(freqs, 20 * np.log10(np.abs(g_vd)), color="0.6", lw=1, label="Plant alone")
    ax1.plot(freqs, 20 * np.log10(np.abs(g_c)), color="tab:orange", lw=1, label="Controller alone")
    ax1.plot(freqs, 20 * np.log10(m["mag"]), color="tab:blue", lw=2,
             label=f"Loop gain (ISR every {n} cycle{'s' if n > 1 else ''})")
    ax2.plot(freqs, m["phase"], color="tab:blue", lw=2, label=f"Loop phase (every {n})")
    if alt_m is not None:
        na = alt_ctrl["n_cycles"]
        ax1.plot(freqs, 20 * np.log10(alt_m["mag"]), color="tab:purple", lw=1, ls="--",
                 label=f"What if the ISR ran every {na} cycles")
        ax2.plot(freqs, alt_m["phase"], color="tab:purple", lw=1, ls="--",
                 label=f"Every {na}: phase margin {alt_m['pm']:.0f}°")
    ax1.axhline(0, color="k", lw=0.8)
    ax2.axhline(-180, color="tab:red", lw=1, ls=":")
    ax2.text(freqs[1], -176, "−180°: the oscillation line", fontsize=8, color="tab:red")
    for ax in (ax1, ax2):
        style_axes(ax)
        ax.axvline(m["fc"], color="k", ls="--", lw=0.8)
    ax1.text(m["fc"] * 1.08, 30, f"crossover\n{m['fc']/1e3:.1f} kHz", fontsize=8)
    ph_c = m["pm"] - 180
    ax2.annotate("", xy=(m["fc"], -180), xytext=(m["fc"], ph_c),
                 arrowprops=dict(arrowstyle="<->", color="tab:green", lw=1.5))
    ax2.text(m["fc"] * 1.15, (ph_c - 180) / 2, f"phase margin\n{m['pm']:.0f}°",
             fontsize=9, color="tab:green")
    ax1.set_ylabel("Gain (dB)")
    ax1.set_ylim(-60, 80)
    ax2.set_ylabel("Phase (degrees)")
    ax2.set_ylim(-270, 0)
    ax2.set_xlabel("Frequency (Hz)")
    ax1.legend(fontsize=8, loc="lower left")
    ax2.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "02_loop_bode.png"), dpi=150)
    return fig


def plot_time(plt, rec, met):
    t_ms = rec["t"] * 1e3
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8.5), sharex=True)
    fig.suptitle("3. Time simulation: soft-start, then a 10 % → 90 % load step and back", fontsize=11)
    ax1.plot(t_ms, rec["ref"], color="0.6", lw=1, ls="--", label="Reference (what firmware asks for)")
    ax1.plot(t_ms, rec["vout"], color="tab:blue", lw=1.5, label="Output voltage")
    ax1.set_ylabel("Volts")
    ax1.legend(fontsize=8, loc="lower right")
    ax1.text(SOFTSTART_TIME * 1e3 * 0.35, VOUT_TARGET * 0.55, "soft-start ramp", fontsize=8)
    ax1.text(T_STEP_UP * 1e3 + 0.1, VOUT_TARGET - 1.5,
             f"load step: dips {met['dip']*1e3:.0f} mV\nsettles in {met['settle_up']*1e6:.0f} µs",
             fontsize=8)

    ax2.plot(t_ms, rec["il"], color="tab:orange", lw=1, label="Inductor current (average)")
    ax2.plot(t_ms, rec["iload"], color="k", lw=1, ls="--", label="Load current")
    ax2.set_ylabel("Amps")
    ax2.legend(fontsize=8, loc="upper left")

    ax3.plot(t_ms, rec["duty"] * 100, color="tab:green", lw=1)
    ax3.set_ylabel("Duty cycle (%)")
    ax3.set_xlabel("Time (ms)")
    ax3.text(0.1, 30, f"ideal steady-state duty = {VOUT_TARGET/VIN*100:.0f} %, "
             "a bit more under load to cover losses", fontsize=8)
    for ax in (ax1, ax2, ax3):
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "03_time_response.png"), dpi=150)

    # Zoom on the load step.
    fig2, ax = plt.subplots(figsize=(9, 4))
    w = (rec["t"] > T_STEP_UP - 0.1e-3) & (rec["t"] < T_STEP_UP + 0.5e-3)
    ax.plot((rec["t"][w] - T_STEP_UP) * 1e6, (rec["vout"][w] - VOUT_TARGET) * 1e3, color="tab:blue")
    band = SETTLE_BAND * VOUT_TARGET * 1e3
    ax.axhspan(-band, band, color="tab:green", alpha=0.15, label=f"±{band:.0f} mV settling band")
    ax.axvline(0, color="k", lw=0.8, ls="--")
    ax.set_xlabel("Time after the load steps from 1.25 A to 11.25 A (µs)")
    ax.set_ylabel("Output error (mV)")
    ax.set_title("3b. Zoom on the load step: how far the output dips and how fast it recovers", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUT_DIR, "03b_load_step_zoom.png"), dpi=150)
    return fig, fig2


def plot_pwm_resolution(plt, rec_hr, rec_plain):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
    w = (rec_hr["t"] > T_STEP_UP - 0.5e-3) & (rec_hr["t"] < T_STEP_UP)
    t_us = (rec_hr["t"][w] - (T_STEP_UP - 0.5e-3)) * 1e6
    lab_plain = f"Without HRPWM (one duty step = {duty_step(False)*VIN*1e3:.0f} mV of output)"
    lab_hr = f"With HRPWM (one duty step = {duty_step(True)*VIN*1e3:.1f} mV of output)"
    ax1.plot(t_us, (rec_plain["vout"][w] - VOUT_TARGET) * 1e3, color="tab:red", lw=1, label=lab_plain)
    ax1.plot(t_us, (rec_hr["vout"][w] - VOUT_TARGET) * 1e3, color="tab:blue", lw=1.5, label=lab_hr)
    ax1.set_ylabel("Output error (mV)")
    ax1.legend(fontsize=8, loc="upper right")
    ax2.step(t_us, rec_plain["duty"][w] * 100, color="tab:red", lw=1, where="post")
    ax2.step(t_us, rec_hr["duty"][w] * 100, color="tab:blue", lw=1.5, where="post")
    ax2.set_ylabel("Duty cycle (%)")
    ax2.set_xlabel("Time (µs), steady state at light load")
    fig.suptitle("4. PWM resolution: the duty cycle can only move in steps.\n"
                 "Without HRPWM the loop can't land on the right duty, so it keeps jumping between steps",
                 fontsize=11)
    for ax in (ax1, ax2):
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "04_pwm_resolution.png"), dpi=150)
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


def print_summary(ctrl, m, alt_ctrl, alt_m, met, met_plain):
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

    os.makedirs(OUT_DIR, exist_ok=True)
    n = LOOP_EVERY_N_CYCLES
    freqs = np.logspace(1, np.log10(0.5 * FSW / n * 0.999), 3000)
    g_vd = plant_duty_to_vout(freqs, *build_plant())

    ctrl = design_controller(freqs, g_vd, n)
    loop, _ = digital_loop_gain(freqs, g_vd, ctrl["b_z"], ctrl["a_z"], n)
    m = margins(freqs, loop)
    if m is None:
        raise SystemExit("The loop gain never crosses 0 dB: check the parameters.")

    # Comparison: the same continuous controller, run at a different loop rate.
    n_alt = 2 if n == 1 else 1
    alt_ctrl = dict(ctrl, n_cycles=n_alt)
    alt_ctrl["b_z"], alt_ctrl["a_z"] = discretize(ctrl["num"], ctrl["den"], n_alt / FSW)
    alt_loop, _ = digital_loop_gain(freqs, g_vd, alt_ctrl["b_z"], alt_ctrl["a_z"], n_alt)
    alt_m = margins(freqs, alt_loop)

    rec = simulate(ctrl, USE_HRPWM)
    met = step_metrics(rec)
    rec_plain = simulate(ctrl, use_hrpwm=False) if USE_HRPWM else rec
    rec_hr = rec if USE_HRPWM else simulate(ctrl, use_hrpwm=True)
    met_plain = step_metrics(rec_plain)

    plot_plant(plt, freqs, g_vd)
    plot_loop(plt, freqs, g_vd, ctrl, m, alt_ctrl, alt_m)
    plot_time(plt, rec, met)
    plot_pwm_resolution(plt, rec_hr, rec_plain)
    print_summary(ctrl, m, alt_ctrl, alt_m, met, met_plain)
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
