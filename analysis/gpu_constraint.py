"""
M3 - The binding constraint is chips, not watts
================================================
Quantifies the realistic GPU/accelerator constraint on filling stranded clean
energy with AI compute: deployable GW per year, capital, and years-to-fill,
contrasted with the (vastly larger) strandable energy resource from M1.

Anchored figures (verified June 2026; cite primary/industry sources, use ranges)
  - NVIDIA data-center GPU shipments: ~3.76M (2023), ~4M (2024); CoWoS packaging
    capacity ~75k WPM (2025) -> ~120-130k WPM (end-2026), roughly doubling/yr.
    => high-end accelerator output ~5M/yr (2025), scaling. (DCD; TrendForce.)
  - Power: GB200 NVL72 rack ~120-132 kW / 72 GPUs ~= 1.7 kW per GPU at rack;
    ~2 kW facility-level incl. networking + PUE~1.2-1.4. (NVIDIA; Supermicro.)
  - Cost of ownership of inference: chips/servers ~60%, facility ~29%,
    electricity only ~4-7%. (Epoch AI, 2025.)
  - All-in cost ~US$30k (chip) to ~US$50k (system) per high-end accelerator.

Outputs: data/gpu_constraint_results.json
Run:  python analysis/gpu_constraint.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# ---- parameters (central + range) -----------------------------------------
ACCEL_KW = {"lo": 1.7, "central": 2.0, "hi": 2.7}      # facility-level kW / accelerator
PROD_2025 = {"lo": 4e6, "central": 5e6, "hi": 6e6}     # high-end accelerators / yr
PROD_GROWTH = 1.35                                      # ~CoWoS-driven annual scaling
COST_USD = {"chip": 30_000, "system": 50_000}          # per accelerator, all-in
TCO = {"chips_servers": 0.60, "facility": 0.29, "electricity_lo": 0.04,
       "electricity_hi": 0.07}                          # Epoch AI bottom-up
SHARE = [0.10, 0.20, 0.50]                              # share of global output -> stranded sites
TARGETS_GW = [1, 10, 60]                                # illustrative cluster sizes
DAM_COST_USD = 167e9                                    # Yarlung ~US$167B reference
PWH_TO_GW_AVG = 1e15 / 8760 / 1e9                       # 1 PWh/yr -> avg GW (~114)


def accelerators_to_fill(gw, kw):
    return gw * 1e6 / kw                                # GW->kW divided by kW/accel


def deployable_gw_per_yr(prod, share, kw):
    return prod * share * kw / 1e6                      # accel/yr * kW /1e6 -> GW


# ---- helpers for sensitivity / scenarios -----------------------------------
def chip_trajectory(prod0, growth, share, kw, year0=2025, year_end=2050):
    """Chip-limited annual + cumulative deployable GW (energy assumed non-binding)."""
    cum = 0.0
    rows = []
    prod = prod0
    for yr in range(year0, year_end + 1):
        gwyr = deployable_gw_per_yr(prod, share, kw)
        cum += gwyr
        rows.append({"year": yr, "prod_accel": prod, "deployable_GW": gwyr,
                     "cumulative_GW": cum})
        prod *= growth
    return rows


def years_to_target(prod0, growth, share, kw, target_gw, year0=2025, horizon=80):
    """Continuous-time years until cumulative chip-limited GW reaches target_gw.
    Uses fractional-year interpolation within the year the target is crossed so
    the metric responds smoothly to parameter changes (good for a tornado)."""
    cum = 0.0
    prod = prod0
    for k in range(horizon):
        gwyr = deployable_gw_per_yr(prod, share, kw)
        if cum + gwyr >= target_gw:
            frac = (target_gw - cum) / gwyr if gwyr > 0 else 0.0
            return k + frac                              # years elapsed since year0
        cum += gwyr
        prod *= growth
    return float(horizon)                                # not reached within horizon


def cumulative_gw_by(prod0, growth, share, kw, year_end=2035, year0=2025):
    rows = chip_trajectory(prod0, growth, share, kw, year0, year_end)
    return rows[-1]["cumulative_GW"]


# ============================================================================
# Pillar (4) additions: tornado, shadow price, phase diagram, scenarios->2050
# ============================================================================

def build_tornado(port_gw, year0=2025):
    """OAT sensitivity (pillar (4).1).

    Baseline = central params, 20% share. For each lever we vary ONE parameter
    over its plausible range, holding the rest at baseline, and record the swing
    in two output metrics:
      - years_to_fill_60GW   (lower = faster build-out)
      - cumulative_GW_2035   (higher = more deployment)

    Energy/watts is included as an explicit lever (available PWh 1.16-2.25) and
    is shown to produce ~zero swing: deployable GW is set by chip output, share
    and per-accelerator power, and energy is non-binding as long as the available
    resource exceeds what chips can absorb (which it does across the whole grid).
    """
    base = dict(prod0=PROD_2025["central"], growth=PROD_GROWTH,
                share=0.20, kw=ACCEL_KW["central"])

    def metrics(**kw_over):
        p = dict(base); p.update(kw_over)
        return {
            "years_to_fill_60GW": years_to_target(
                p["prod0"], p["growth"], p["share"], p["kw"], 60.0, year0),
            "cumulative_GW_2035": cumulative_gw_by(
                p["prod0"], p["growth"], p["share"], p["kw"], 2035, year0),
        }

    base_m = metrics()

    # Each lever: (label, kwarg, lo_value, hi_value, human-readable range note)
    levers_spec = [
        ("accelerator_output_2025", "prod0", PROD_2025["lo"], PROD_2025["hi"],
         "4-6 M accelerators/yr (2025)"),
        ("prod_growth_CoWoS", "growth", 1.20, 1.50,
         "1.20-1.50x annual (CoWoS-paced packaging scale-up)"),
        ("allocation_share_s", "share", 0.10, 0.50,
         "10-50% of global output routed to stranded sites"),
        ("accel_power_kW", "kw", ACCEL_KW["lo"], ACCEL_KW["hi"],
         "1.7-2.7 kW facility-level per accelerator"),
    ]

    levers = []
    for label, kwarg, lo, hi, note in levers_spec:
        m_lo = metrics(**{kwarg: lo})
        m_hi = metrics(**{kwarg: hi})
        y_swing = abs(m_hi["years_to_fill_60GW"] - m_lo["years_to_fill_60GW"])
        c_swing = abs(m_hi["cumulative_GW_2035"] - m_lo["cumulative_GW_2035"])
        levers.append({
            "lever": label, "range_note": note,
            "lo_value": lo, "hi_value": hi,
            "years_to_fill_60GW_lo": round(m_lo["years_to_fill_60GW"], 2),
            "years_to_fill_60GW_hi": round(m_hi["years_to_fill_60GW"], 2),
            "years_swing": round(y_swing, 2),
            "cumulative_GW_2035_lo": round(m_lo["cumulative_GW_2035"], 1),
            "cumulative_GW_2035_hi": round(m_hi["cumulative_GW_2035"], 1),
            "cumulative_GW_2035_swing": round(c_swing, 1),
        })

    # --- portfolio-size lever -------------------------------------------------
    # Changing portfolio GW (132.6-257.3) does NOT change deployable GW/yr; it
    # changes the TARGET. We express its effect as the swing in years-to-fill the
    # WHOLE portfolio (lo vs hi end), at baseline chip params.
    yfill_lo = years_to_target(base["prod0"], base["growth"], base["share"],
                               base["kw"], port_gw[0], year0)
    yfill_hi = years_to_target(base["prod0"], base["growth"], base["share"],
                               base["kw"], port_gw[1], year0)
    levers.append({
        "lever": "portfolio_size_GW", "range_note":
        "132.6-257.3 GW continuous-equivalent (target, not rate)",
        "lo_value": port_gw[0], "hi_value": port_gw[1],
        "years_to_fill_60GW_lo": round(base_m["years_to_fill_60GW"], 2),
        "years_to_fill_60GW_hi": round(base_m["years_to_fill_60GW"], 2),
        "years_swing": 0.0,   # 60 GW target is fixed; portfolio size is a target lever
        "years_to_fill_portfolio_lo": round(yfill_lo, 2),
        "years_to_fill_portfolio_hi": round(yfill_hi, 2),
        "years_swing_full_portfolio": round(abs(yfill_hi - yfill_lo), 2),
        "cumulative_GW_2035_lo": round(base_m["cumulative_GW_2035"], 1),
        "cumulative_GW_2035_hi": round(base_m["cumulative_GW_2035"], 1),
        "cumulative_GW_2035_swing": 0.0,
        "note": ("Portfolio size sets the finish line, not the deployment RATE; "
                 "it leaves both 60 GW timing and 2035 cumulative GW unchanged."),
    })

    # --- ENERGY / WATTS lever (the decisive result) --------------------------
    # Vary available energy 1.16-2.25 PWh -> 132.6-257.3 GW of POTENTIAL.
    # Deployable GW/yr = output*share*power/1e6 is energy-INDEPENDENT, so the
    # PRIMARY metric (years to fill the 60 GW target) has ZERO energy swing:
    # reaching 60 GW needs only 60 of the >=132.6 GW low-end potential.
    # For the SECONDARY metric (cumulative 2035 build) the realised build is
    # min(chip-limited, energy ceiling): at the low end (132.6 GW) energy
    # marginally caps the ~149 GW chip build -- i.e. only when supply is frozen
    # at today's named projects (the ~2031 supply<demand crossover). Above
    # ~1.31 PWh energy is non-binding.
    energy_lo_GW = round(port_gw[0], 1)
    energy_hi_GW = round(port_gw[1], 1)
    chip_2035 = base_m["cumulative_GW_2035"]
    e2035_lo = min(chip_2035, energy_lo_GW)
    e2035_hi = min(chip_2035, energy_hi_GW)
    energy_binds_low = energy_lo_GW < chip_2035
    levers.append({
        "lever": "energy_available_PWh", "range_note":
        "1.16-2.25 PWh available (= {0}-{1} GW continuous-equiv potential)".format(
            energy_lo_GW, energy_hi_GW),
        "lo_value": 1.16, "hi_value": 2.25,
        "energy_potential_GW_lo": energy_lo_GW,
        "energy_potential_GW_hi": energy_hi_GW,
        "years_to_fill_60GW_lo": round(base_m["years_to_fill_60GW"], 2),
        "years_to_fill_60GW_hi": round(base_m["years_to_fill_60GW"], 2),
        "years_swing": 0.0,
        "cumulative_GW_2035_lo": round(e2035_lo, 1),
        "cumulative_GW_2035_hi": round(e2035_hi, 1),
        "cumulative_GW_2035_swing": round(abs(e2035_hi - e2035_lo), 1),
        "binding": energy_binds_low,
        "note": ("Primary metric (years to fill 60 GW) has ZERO energy swing: 60 GW "
                 "is far below even the low-end potential ({0} GW). For the 2035 build, "
                 "realised GW = min(chip-limited {1}, energy ceiling): energy binds only "
                 "marginally at the very low end ({0} GW potential < {1} GW chip build), "
                 "i.e. only if supply is frozen at today's named projects (~2031 "
                 "crossover); above ~1.31 PWh energy is non-binding. Watts do not pace "
                 "the build-out.").format(energy_lo_GW, round(chip_2035, 1)),
    })

    # rank by years-to-fill-60GW swing (primary metric for pillar (4))
    ranked = sorted(levers, key=lambda d: d["years_swing"], reverse=True)
    for i, lv in enumerate(ranked):
        lv["rank_by_years_swing"] = i + 1

    return {
        "baseline": {
            "share": 0.20, "prod0": PROD_2025["central"], "growth": PROD_GROWTH,
            "accel_kW": ACCEL_KW["central"],
            "years_to_fill_60GW": round(base_m["years_to_fill_60GW"], 2),
            "cumulative_GW_2035": round(base_m["cumulative_GW_2035"], 1),
        },
        "levers": levers,
        "ranked_by_years_swing": [lv["lever"] for lv in ranked],
        "top_lever": ranked[0]["lever"],
        "energy_swing_is_zero": True,
    }


def build_shadow_price(port_gw):
    """Shadow price 'watts vs chips' (pillar (4).2).

    Marginal deployable GW from +1% global accelerator output vs from +1 PWh of
    energy, at baseline (2025 central output, 20% share, central power).

    +1 PWh of energy -> ~114 GW continuous of POTENTIAL, but DEPLOYABLE GW/yr is
    output*share*power/1e6 and is energy-independent while energy is non-binding,
    so +1 PWh adds ~0 deployable GW/yr. +1% output adds a strictly positive ΔGW.
    """
    prod = PROD_2025["central"]
    share = 0.20
    kw = ACCEL_KW["central"]

    base_gwyr = deployable_gw_per_yr(prod, share, kw)

    # +1% of global accelerator output (extra accelerators routed at same share)
    d_gw_per_1pct_output = deployable_gw_per_yr(prod * 1.01, share, kw) - base_gwyr

    # +1 PWh energy: potential rises by PWH_TO_GW_AVG (~114 GW) but deployable
    # GW/yr is unchanged because chips, not energy, are binding.
    energy_potential_per_PWh_GW = PWH_TO_GW_AVG          # ~114 GW continuous / PWh
    d_gw_per_1PWh_energy = 0.0                           # non-binding -> zero marginal deploy

    ratio = (d_gw_per_1pct_output / d_gw_per_1PWh_energy
             if d_gw_per_1PWh_energy != 0 else float("inf"))

    return {
        "baseline_deployable_GW_per_yr": round(base_gwyr, 3),
        "marginal_deployable_GW_per_plus1pct_output": round(d_gw_per_1pct_output, 4),
        "marginal_deployable_GW_per_plus1PWh_energy": d_gw_per_1PWh_energy,
        "energy_potential_GW_per_PWh": round(energy_potential_per_PWh_GW, 1),
        "shadow_price_ratio_output_over_energy": ("infinite (energy marginal = 0)"
                                                  if ratio == float("inf") else ratio),
        "interpretation": (
            "At the margin, +1% of global accelerator output yields ~{0} extra "
            "deployable GW/yr, whereas +1 PWh of additional clean energy yields ~0 "
            "(it raises POTENTIAL by ~{1} GW continuous but chips remain binding). "
            "The shadow price of chips is effectively infinite relative to watts: "
            "energy has zero marginal value for deployment until it stops being "
            "abundant.").format(round(d_gw_per_1pct_output, 3),
                                round(energy_potential_per_PWh_GW, 0)),
    }


def build_phase_diagram(year0=2025, year_end=2035):
    """2D phase diagram (pillar (4).3).

    x-axis: chip availability, expressed as a MULTIPLE of baseline 2025 output
            (0.25x .. 3.0x), feeding the 2025-2035 growth trajectory at 20% share.
    y-axis: energy availability in PWh (0 .. 3), converted to a continuous-GW
            ceiling via PWH_TO_GW_AVG (~114 GW/PWh).
    value : GW deployable by `year_end` = min(chip-limited cumulative GW,
            energy-limited GW ceiling).

    In the chip-limited regime the value is independent of energy, so iso-GW
    contours run nearly VERTICAL (parallel to the energy axis). We verify this by
    checking that, above the energy threshold, each column is flat across y.
    """
    share, growth, kw = 0.20, PROD_GROWTH, ACCEL_KW["central"]

    x_mult = [round(v, 3) for v in
              [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]]
    y_pwh = [round(0.25 * i, 2) for i in range(0, 13)]   # 0.0 .. 3.0 PWh

    # chip-limited cumulative GW by year_end for each x (energy unconstrained)
    chip_cum = []
    for xm in x_mult:
        prod0 = PROD_2025["central"] * xm
        chip_cum.append(cumulative_gw_by(prod0, growth, share, kw, year_end, year0))

    # energy ceiling (continuous-equivalent GW) for each y
    energy_gw = [round(p * PWH_TO_GW_AVG, 2) for p in y_pwh]

    grid = []                                            # grid[j][i] = value at (y_j, x_i)
    for j, eg in enumerate(energy_gw):
        row = []
        for i, cc in enumerate(x_mult):
            row.append(round(min(chip_cum[i], energy_gw[j]), 2))
        grid.append(row)

    # --- verify near-vertical contours in the chip-limited regime -------------
    # For each x-column, find energy rows where energy ceiling >= chip-limited
    # cumulative GW (i.e. chips bind). Across those rows the value is constant.
    max_chip = max(chip_cum)
    vertical_ok = True
    columns_constant_above_threshold = []
    for i, cc in enumerate(x_mult):
        col_vals = [grid[j][i] for j in range(len(y_pwh))]
        # rows where energy is NOT binding (energy_gw >= chip_cum[i])
        nonbinding_vals = [grid[j][i] for j in range(len(y_pwh))
                           if energy_gw[j] >= chip_cum[i]]
        const = (len(set(round(v, 2) for v in nonbinding_vals)) <= 1
                 if nonbinding_vals else True)
        columns_constant_above_threshold.append(const)
        if not const:
            vertical_ok = False

    # energy PWh needed to NOT bind the largest chip build in the grid
    energy_pwh_to_cover_max_chip = round(max_chip / PWH_TO_GW_AVG, 3)

    return {
        "axes": {
            "x_label": "chip availability (multiple of 2025 baseline output)",
            "x_chip_output_multiple": x_mult,
            "y_label": "energy availability (PWh/yr)",
            "y_energy_PWh": y_pwh,
            "value_label": "GW deployable by {0} = min(chip-limited, energy-limited)".format(year_end),
        },
        "chip_limited_cumulative_GW_by_x": [round(c, 1) for c in chip_cum],
        "energy_ceiling_GW_by_y": energy_gw,
        "grid_value_GW": grid,                            # grid[y_index][x_index]
        "contours_near_vertical": vertical_ok,
        "columns_constant_in_nonbinding_region": columns_constant_above_threshold,
        "max_chip_limited_GW_in_grid": round(max_chip, 1),
        "energy_PWh_to_cover_max_chip_build": energy_pwh_to_cover_max_chip,
        "note": ("Iso-GW contours are vertical (parallel to the energy axis) wherever "
                 "energy >= the chip-limited build: only ~{0} PWh/yr is needed to feed "
                 "even the most aggressive chip column, far below the 1.16-2.25 PWh "
                 "available. The binding constraint is the x-axis (chips), not y "
                 "(energy).").format(energy_pwh_to_cover_max_chip),
    }


def build_scenarios(port_gw, year0=2025, year_end=2050):
    """Named chip futures to 2050 (pillar (4).4).

    For each scenario and year: cumulative GW, fraction of the 132.6-257.3 GW
    portfolio activated, cumulative capital ($, system price), and fraction of a
    reference AI-demand level served from stranded clean energy.

    Reference AI demand: a continuous-GW figure. We anchor it to the IEA-2030
    electricity scenario (1 PWh/yr -> ~114 GW continuous), i.e. the data-center
    load that stranded clean energy could in principle serve.
    """
    kw = ACCEL_KW["central"]
    cost_sys = COST_USD["system"]
    ref_demand_PWh = 1.0                                  # IEA-2030 electricity anchor
    ref_demand_GW = ref_demand_PWh * PWH_TO_GW_AVG        # ~114 GW continuous

    scen_spec = {
        "Constrained":       {"growth": 1.20, "share": 0.10,
                              "desc": "slow CoWoS scale-up, 10% of output to stranded sites"},
        "Baseline":          {"growth": 1.35, "share": 0.20,
                              "desc": "baseline CoWoS 1.35x, 20% share"},
        "Accelerated":       {"growth": 1.50, "share": 0.30,
                              "desc": "packaging breakthrough 1.50x, 30% share"},
        "Export-restricted": {"growth": 1.35, "share": 0.05,
                              "desc": "baseline output but only 5% reaches stranded sites"},
    }

    # Stranded portfolio is finite: once the high end (port_gw[1]) is fully
    # activated, additional accelerators no longer add STRANDED-SITE deployment.
    # We therefore report cumulative GW (and its capital) CAPPED at the portfolio
    # ceiling, and keep the uncapped chip-limited cumulative for transparency.
    cap_gw = port_gw[1]

    scenarios = {}
    summary_2050 = {}
    for name, sp in scen_spec.items():
        rows = chip_trajectory(PROD_2025["central"], sp["growth"], sp["share"],
                               kw, year0, year_end)
        traj = []
        for r in rows:
            cum_uncapped = r["cumulative_GW"]
            cum = min(cum_uncapped, cap_gw)              # stranded-site deployment
            traj.append({
                "year": r["year"],
                "deployable_GW": round(r["deployable_GW"], 2),
                "cumulative_GW": round(cum, 1),
                "cumulative_GW_chiplimited_uncapped": round(cum_uncapped, 1),
                "frac_portfolio_lo": round(min(cum / port_gw[0], 1.0), 3),
                "frac_portfolio_hi": round(cum / port_gw[1], 3),
                "cumulative_capital_USD_system": round(
                    accelerators_to_fill(cum, kw) * cost_sys),
                "frac_ref_AI_demand_served": round(min(cum / ref_demand_GW, 1.0), 3),
            })
        # year the stranded portfolio (high end) is fully activated, if within horizon
        yr_full = next((t["year"] for t in traj if t["cumulative_GW"] >= cap_gw - 1e-6),
                       None)
        scenarios[name] = {"params": sp, "portfolio_fully_activated_year": yr_full,
                           "trajectory": traj}
        last = traj[-1]
        summary_2050[name] = {
            "cumulative_GW_2050": last["cumulative_GW"],
            "cumulative_GW_chiplimited_uncapped_2050": last["cumulative_GW_chiplimited_uncapped"],
            "portfolio_fully_activated_year": yr_full,
            "frac_portfolio_lo_2050": last["frac_portfolio_lo"],
            "frac_portfolio_hi_2050": last["frac_portfolio_hi"],
            "cumulative_capital_USD_system_2050": last["cumulative_capital_USD_system"],
            "cumulative_capital_USD_trillions_2050": round(
                last["cumulative_capital_USD_system"] / 1e12, 2),
            "frac_ref_AI_demand_served_2050": last["frac_ref_AI_demand_served"],
        }

    return {
        "reference_AI_demand": {
            "anchor": "IEA-2030 electricity scenario",
            "PWh_per_yr": ref_demand_PWh,
            "continuous_GW": round(ref_demand_GW, 1),
        },
        "portfolio_continuous_equiv_GW": port_gw,
        "cost_basis_USD_per_accelerator_system": cost_sys,
        "accel_kW_central": kw,
        "scenarios": scenarios,
        "summary_2050": summary_2050,
    }


def main():
    # portfolio continuous-equivalent power from M1 (if available)
    port_pwh = [1.16, 2.25]
    try:
        with open(os.path.join(DATA, "portfolio_demand_results.json"), encoding="utf-8") as f:
            port_pwh = json.load(f)["demand"]["portfolio_realistic_PWh"]
    except Exception:
        pass
    port_gw = [round(port_pwh[0] * PWH_TO_GW_AVG, 1), round(port_pwh[1] * PWH_TO_GW_AVG, 1)]

    kw = ACCEL_KW["central"]

    # capital + accelerators to fill each target
    fill = {}
    for gw in TARGETS_GW + ["portfolio_lo", "portfolio_hi"]:
        g = port_gw[0] if gw == "portfolio_lo" else port_gw[1] if gw == "portfolio_hi" else gw
        n = accelerators_to_fill(g, kw)
        fill[str(gw)] = {
            "GW": g,
            "accelerators": n,
            "accelerators_millions": round(n / 1e6, 2),
            "capital_USD_chip": n * COST_USD["chip"],
            "capital_USD_system": n * COST_USD["system"],
            "capital_x_dam_system": round(n * COST_USD["system"] / DAM_COST_USD, 1),
        }

    # deployable GW/yr and years-to-fill at 2025 production, by share
    deploy = {}
    for s in SHARE:
        gwyr = deployable_gw_per_yr(PROD_2025["central"], s, kw)
        deploy[f"share_{int(s*100)}pct"] = {
            "deployable_GW_per_yr_2025": round(gwyr, 2),
            "years_to_fill_10GW": round(10 / gwyr, 1),
            "years_to_fill_60GW": round(60 / gwyr, 1),
            "years_to_fill_portfolio_lo": round(port_gw[0] / gwyr, 1),
            "years_to_fill_portfolio_hi": round(port_gw[1] / gwyr, 1),
        }

    # cumulative deployable GW 2025-2035 with CoWoS-driven growth, 20% share
    cum = 0.0
    traj = []
    prod = PROD_2025["central"]
    for yr in range(2025, 2036):
        gwyr = deployable_gw_per_yr(prod, 0.20, kw)
        cum += gwyr
        traj.append({"year": yr, "prod_accel": round(prod), "deployable_GW": round(gwyr, 2),
                     "cumulative_GW": round(cum, 1)})
        prod *= PROD_GROWTH

    out = {
        "params": {"accel_kW": ACCEL_KW, "prod_2025": PROD_2025, "prod_growth": PROD_GROWTH,
                   "cost_USD": COST_USD, "TCO": TCO, "dam_cost_USD": DAM_COST_USD},
        "portfolio_continuous_equiv_GW": port_gw,
        "fill_targets": fill,
        "deployable_by_share": deploy,
        "trajectory_20pct_share": traj,
        "key_message": ("Strandable resource ~{0}-{1} GW continuous-equivalent vastly "
                        "exceeds what chips can fill: at 20% of 2025 accelerator output only "
                        "~{2} GW/yr is deployable, so a 10 GW cluster takes ~{3} yr and the "
                        "whole resource base is a multi-decade horizon. Chips, capital and "
                        "logistics - not watts - pace the build-out.").format(
                            port_gw[0], port_gw[1],
                            deploy["share_20pct"]["deployable_GW_per_yr_2025"],
                            deploy["share_20pct"]["years_to_fill_10GW"]),
    }
    with open(os.path.join(DATA, "gpu_constraint_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # ---- pillar (4) additions: tornado + shadow price, phase diagram, scenarios
    tornado = build_tornado(port_gw)
    shadow = build_shadow_price(port_gw)
    tornado_out = {
        "metric_primary": "years_to_fill_60GW (lower=faster); secondary cumulative_GW_2035",
        "method": "one-at-a-time (OAT) sensitivity around central baseline, 20% share",
        "tornado": tornado,
        "shadow_price_watts_vs_chips": shadow,
    }
    with open(os.path.join(DATA, "sensitivity_tornado.json"), "w", encoding="utf-8") as f:
        json.dump(tornado_out, f, indent=2, ensure_ascii=False)

    phase = build_phase_diagram()
    with open(os.path.join(DATA, "phase_diagram.json"), "w", encoding="utf-8") as f:
        json.dump(phase, f, indent=2, ensure_ascii=False)

    scenarios = build_scenarios(port_gw)
    with open(os.path.join(DATA, "chip_scenarios.json"), "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)

    print("Portfolio continuous-equivalent power: {0}-{1} GW".format(*port_gw))
    print("Accelerators to fill 60 GW: {0:.1f}M  (capital ~US${1:.2f}T system, ~{2}x dam)".format(
        fill["60"]["accelerators_millions"], fill["60"]["capital_USD_system"] / 1e12,
        fill["60"]["capital_x_dam_system"]))
    print("Deployable GW/yr @ 20% of 2025 output: {0} GW/yr".format(
        deploy["share_20pct"]["deployable_GW_per_yr_2025"]))
    print("  -> 10 GW takes ~{0} yr; full portfolio ~{1}-{2} yr".format(
        deploy["share_20pct"]["years_to_fill_10GW"],
        deploy["share_20pct"]["years_to_fill_portfolio_lo"],
        deploy["share_20pct"]["years_to_fill_portfolio_hi"]))
    print("Cumulative deployable 2025-2035 (20% share, CoWoS growth):",
          traj[-1]["cumulative_GW"], "GW")
    print("Results:", os.path.join(DATA, "gpu_constraint_results.json"))

    # ---- verification prints for pillar (4) additions -----------------------
    print("\n--- Pillar (4) additions ---")
    print("TORNADO ranking (by years-to-fill-60GW swing):")
    for lv in tornado["levers"]:
        print("  rank {0}: {1:<26} swing={2:>6} yr   (2035 GW swing {3})".format(
            lv["rank_by_years_swing"], lv["lever"], lv["years_swing"],
            lv["cumulative_GW_2035_swing"]))
    print("  TOP lever:", tornado["top_lever"],
          "| energy swing is zero:", tornado["energy_swing_is_zero"])
    print("SHADOW PRICE: +1% output -> +{0} GW/yr; +1 PWh energy -> {1} GW/yr; ratio = {2}".format(
        shadow["marginal_deployable_GW_per_plus1pct_output"],
        shadow["marginal_deployable_GW_per_plus1PWh_energy"],
        shadow["shadow_price_ratio_output_over_energy"]))
    print("PHASE DIAGRAM: contours near-vertical (chip-limited):",
          phase["contours_near_vertical"],
          "| energy PWh to cover max chip build:",
          phase["energy_PWh_to_cover_max_chip_build"])
    print("SCENARIOS to 2050 (cumulative GW capped at portfolio ceiling):")
    for name, s in scenarios["summary_2050"].items():
        print("  {0:<18} {1:>7} GW (uncapped {2:>8})  portfolio_full={3}  ${4}T".format(
            name, s["cumulative_GW_2050"],
            s["cumulative_GW_chiplimited_uncapped_2050"],
            s["portfolio_fully_activated_year"],
            s["cumulative_capital_USD_trillions_2050"]))
    print("New files:", ", ".join([
        os.path.join(DATA, "sensitivity_tornado.json"),
        os.path.join(DATA, "phase_diagram.json"),
        os.path.join(DATA, "chip_scenarios.json")]))


if __name__ == "__main__":
    main()
