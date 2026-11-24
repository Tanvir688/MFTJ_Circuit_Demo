# MFTJ bitline discharge in Cadence Spectre

This four-cell read circuit demonstrates an equation-based Verilog-A compact model of a multiferroic tunnel junction (MFTJ). The model calculates the spin-dependent tunneling current at the instantaneous junction voltage. The example uses an Fe₃GeTe₂ / CuInP₂S₆ / Fe₅GeTe₂ junction at 120 K.

![Simulated bitline discharge for four MFTJ states. A zoomed inset shows the parallel and antiparallel ON states crossing 100 mV about 1.71 ns apart.](figures/mftj_bitline_discharge_5ms.png)

The main traces come from a 5 ms Spectre transient. The inset comes from a second, 120 ns transient with tighter time stepping. [Download the vector figure](figures/mftj_bitline_discharge_5ms.svg).

## Circuit

Each cell has a 1 pF bitline capacitor, a 100 Ω precharge switch connected to a 200 mV supply, and a junction with an assumed area of 1.99 µm². The junction model includes its geometric capacitance. Spectre first solves the DC operating point with the switches closed. At 1 ns the switches open, and each bitline discharges through its junction. The module's positive terminal is grounded, so a positive bitline voltage applies a negative junction read bias.

The four instances hold their polarization and magnetic alignment fixed during readout. The parameter `initial_sign` selects ON (+1) or OFF (−1). The parameter `alignment` selects parallel (+1) or antiparallel (−1). The read delay is the elapsed time from switch release to the first falling 100 mV bitline crossing.

## Run the example

Use a Linux shell with a licensed Cadence Spectre installation and its Verilog-A compiler available. Run both commands from the repository root. Both decks load the same local [Verilog-A model](mftj_equations.va).

```bash
spectre rc_discharge_5ms.scs -format psfascii -raw rc_5ms_results +log rc_5ms.log
spectre rc_discharge_tight.scs -format psfascii -raw rc_tight_results +log rc_tight.log
cat rc_discharge_5ms.measure rc_discharge_tight.measure
```

The [5 ms deck](rc_discharge_5ms.scs) measures all four 100 mV crossings and the OFF states' 1 mV settling times. The [120 ns deck](rc_discharge_tight.scs) uses a 200 ps maximum time step and a relative tolerance of 10⁻⁶ to resolve the closest pair. Both use 8 energy nodes per subinterval, 12 transverse nodes, 32 barrier slices and 32 slices per electrode tail.

## Reference results

The following are nominal simulation results from Spectre 25.1.0.470.isr13 with the supplied parameters.

| State | Delay to 100 mV, 5 ms run | Delay to 100 mV, tight run |
|---|---:|---:|
| ON/P | 84.052 ns | 85.066 ns |
| ON/AP | 85.812 ns | 86.778 ns |
| OFF/P | 230.985 µs | — |
| OFF/AP | 288.634 µs | — |

The P–AP separation is **1.712 ns** in the ON state (tight run) and **57.65 µs** in the OFF state (5 ms run). The OFF/P and OFF/AP bitlines reach 1 mV after 2.294 ms and 2.913 ms, respectively. These delays describe the simulated circuit at nominal conditions.

## Regenerate the figure

After both runs, use Python 3 with NumPy and Matplotlib installed. The script reads the two PSF ASCII waveforms and their Spectre measurements and writes the PNG and SVG to `figures/`.

```bash
python3 plot_discharge.py
```

Experimental device data used for calibration are reported by Xie et al., Fig. 3. [Nature Nanotechnology, DOI 10.1038/s41565-025-02065-1](https://doi.org/10.1038/s41565-025-02065-1).
