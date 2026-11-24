"""Regenerate the published figure from the loose 5 ms Spectre run."""
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import ConnectionPatch
from matplotlib.ticker import NullLocator
import numpy as np


ROOT = Path(__file__).resolve().parent
INK, GRAY, FRAME = "#172f3c", "#526571", "#8497a1"
STYLES = {
    "p": ("#155e85", "-", "o", "Parallel (P)"),
    "ap": ("#b44923", (0, (4, 2)), "s", "Antiparallel (AP)"),
}


def falling_crossing(time, voltage, threshold):
    matches = np.flatnonzero((voltage[:-1] > threshold) & (voltage[1:] <= threshold))
    if not len(matches):
        raise ValueError(f"Waveform never crosses {threshold:g} V on a falling edge.")
    i = matches[0]
    fraction = (threshold - voltage[i]) / (voltage[i + 1] - voltage[i])
    return time[i] + fraction * (time[i + 1] - time[i])


def read_run(result_dir, measures, states):
    waveform = ROOT / result_dir / "tran1.tran.tran"
    _, marker, samples = waveform.read_text().partition("\nVALUE\n")
    if not marker or not samples.rstrip().endswith("END"):
        raise ValueError(f"Expected a completed PSF ASCII transient in {waveform}.")
    columns = {}
    for signal, value in re.findall(r'^"(\w+)"\s+([-+.0-9Ee]+)$', samples, re.M):
        columns.setdefault(signal, []).append(float(value))
    time = np.asarray(columns["time"])
    release = falling_crossing(time, np.asarray(columns["pre"]), 0.5)
    measured = dict(re.findall(r"^\s*(delay_\w+)\s*=\s*(\S+)", (ROOT / measures).read_text(), re.M))
    volts_mv, delay_ns = {}, {}
    for state in states:
        voltage = np.asarray(columns[f"bl_{state}"])
        delay = falling_crossing(time, voltage, 0.100) - release
        if not np.isclose(delay, float(measured[f"delay_{state}"]), rtol=1e-5, atol=0):
            raise ValueError(f"Waveform crossing for {state} differs from {measures}.")
        volts_mv[state] = voltage * 1e3
        delay_ns[state] = delay * 1e9
    return (time - release) * 1e9, volts_mv, delay_ns


def style_axes(ax):
    ax.tick_params(colors=GRAY, direction="out", length=3.3, width=0.75)
    for spine in ax.spines.values():
        spine.set_color(FRAME)
        spine.set_linewidth(0.8)
    ax.grid(False, which="both")


def draw_figure():
    time, voltage, delay = read_run(
        "rc_loose_results", "rc_discharge_loose.measure", ("on_p", "on_ap", "off_p", "off_ap")
    )
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "svg.fonttype": "none",
                         "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(10.4, 5.05), facecolor="white")
    ax = fig.add_axes([0.10, 0.15, 0.866, 0.808])
    style_axes(ax)
    ax.set_xscale("log")
    ax.set(xlim=(0.9, 5e6), ylim=(-5, 226), yticks=[0, 50, 100, 150, 200],
           ylabel="Bitline voltage (mV)", xlabel="Time after switch release")
    ax.xaxis.labelpad = 7
    ax.set_xticks([1, 10, 100, 1e3, 1e4, 1e5, 1e6, 5e6])
    ax.set_xticklabels(["1 ns", "10 ns", "100 ns", "1 µs", "10 µs", "100 µs", "1 ms", "5 ms"])
    ax.xaxis.set_minor_locator(NullLocator())

    # Interpolate in physical time before transforming the horizontal axis.
    display_time = np.unique(np.r_[np.geomspace(0.9, time[-1], 2400), time[time >= 0.9]])
    for branch in ("on", "off"):
        for alignment, (color, line, marker, _) in STYLES.items():
            state = f"{branch}_{alignment}"
            ax.plot(display_time, np.interp(display_time, time, voltage[state]),
                    color=color, ls=line, lw=2.0, zorder=3)
            if branch == "off":
                ax.plot(delay[state], 100, marker=marker, mfc="white", mec=color,
                        mew=1.45, ms=5.6, zorder=5)
    handles = [Line2D([], [], color=c, ls=ls, lw=2, label=label)
               for c, ls, _, label in STYLES.values()]
    ax.legend(handles=handles, ncol=2, loc="upper left", bbox_to_anchor=(0.003, 1),
              borderaxespad=0.25, frameon=False, handlelength=2.8, columnspacing=1.8, fontsize=10)
    ax.text(12, 147, "ON", color=INK, fontsize=12, weight="bold")
    ax.text(1.5e4, 198, "OFF", color=INK, fontsize=12, weight="bold")
    off_center = np.sqrt(delay["off_p"] * delay["off_ap"])  # midpoint on the log axis
    off_gap_us = (delay["off_ap"] - delay["off_p"]) / 1e3
    ax.plot(off_center, 100, marker="o", ms=20, mfc="none", mec=INK, mew=1.15, ls="none", zorder=6)
    ax.annotate(f"Δt = {off_gap_us:.2f} µs", xy=(off_center, 100), xytext=(5.3e5, 128),
                ha="center", va="center", fontsize=10, color=INK, weight="bold", zorder=7,
                arrowprops=dict(arrowstyle="-", lw=1.0, color=INK, shrinkB=10.5))

    inset = ax.inset_axes([0.416, 0.14, 0.278, 0.34], zorder=9)
    style_axes(inset)
    for spine in inset.spines.values():
        spine.set_visible(True)
    inset.set(xlim=(83.5, 88.4), ylim=(97.7, 102.35), yticks=[98, 100, 102])
    inset.set_title("ON crossings at 100 mV", fontsize=9.5, fontweight="bold",
                    loc="left", pad=5, color=INK)
    for alignment, (color, line, marker, _) in STYLES.items():
        state = f"on_{alignment}"
        inset.plot(time, voltage[state], color=color, ls=line, lw=1.85)
        inset.plot(delay[state], 100, marker=marker, color=color,
                   mfc="white", ms=5.3, mew=1.35, zorder=4)
    p, ap = delay["on_p"], delay["on_ap"]
    inset.set_xticks([p, ap], labels=[f"{p:.2f} ns", f"{ap:.2f} ns"])
    inset.tick_params(labelsize=8.5, pad=2)
    # Truncate the displayed gap to hundredths of a nanosecond.
    inset.text(0.96, 0.86, f"Δt = {np.floor((ap - p) * 100) / 100:.2f} ns", ha="right",
               transform=inset.transAxes, color=INK, weight="bold", fontsize=9)
    on_center = (delay["on_p"] + delay["on_ap"]) / 2
    ax.plot(on_center, 100, "o", ms=12, mfc="none", mec=INK, mew=1.1, zorder=6)
    fig.add_artist(ConnectionPatch((on_center, 100), (0, 0.74),
                                   coordsA=ax.transData, coordsB=inset.transAxes,
                                   axesA=ax, axesB=inset, arrowstyle="-|>", mutation_scale=13,
                                   shrinkA=7, shrinkB=3, lw=1.15, color=INK, zorder=12))
    output = ROOT / "figures"
    output.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(output / f"mftj_bitline_discharge_5ms.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    draw_figure()
