"""
M1 - Stranded clean-energy portfolio inventory + AI demand-scenario comparison
==============================================================================
Builds a curated, *numeric* tiered portfolio of large stranded clean-energy
resources (replacing the single-Yarlung framing) and compares aggregate
strandable supply against future AI demand scenarios.

Tiers
-----
  Tier 1  - discrete stranded MEGA-PROJECTS (remote hydro mega-dams + planned
            desert export mega-hubs). Strandable = generation with no/weak local
            market or far from demand. Yarlung Tsangpo is ONE row (the extreme).
  Tier 2  - structurally CURTAILED existing renewable fleets (wind/solar already
            being spilled today). Strandable = energy actually curtailed now;
            small per site but zero-marginal-cost and growing -> the near-term
            pilot fuel.
  (theoretical=True rows are reported separately as an upper bound, never in the
   headline "realistic" sum.)

Numbers are curated from data/sites_master.csv (row index in `src`), with
strandable ranges read from the annualTWh / whyStranded fields. Demand scenarios
are anchored to IEA 'Energy and AI' (2025) and Zhu et al., 'Desert power for the
AI era', Nexus (2026) (1 / 10 / 100 PWh/yr).

Outputs
-------
  data/portfolio.csv                 - the curated portfolio
  data/portfolio_demand_results.json - aggregates + supply/demand metrics

Run:  python analysis/portfolio_demand.py
"""
import csv, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------------------
# Curated portfolio. strandable TWh/yr is the exportable / stranded / curtailed
# fraction (NOT necessarily total generation). Conservative ranges.
# fields: name, country, tier, etype, status, lat, lon,
#         lcoe_lo, lcoe_hi ($/MWh), str_lo, str_hi (TWh/yr), theoretical, src, note
# ---------------------------------------------------------------------------
P = [
    # ---- Tier 1 : discrete stranded mega-projects -------------------------
    ["Yarlung Tsangpo / Medog", "China", 1, "hydro", "under-constr", 29.77, 95.00, 30, 60, 270, 300, False, 37, "~300 TWh/yr, ~3x Three Gorges; Tibet uses ~12-13 TWh/yr; >2000 km to load; the extreme case"],
    ["Gobi Desert renewable mega-bases", "China", 1, "solar+wind", "under-constr", 40.50, 105.00, 15, 30, 450, 900, False, 33, "New coordinated desert mega-base build for UHV export; ~800-900+ TWh/yr at full build"],
    ["Grand Inga (Inga III -> Grand Inga)", "DR Congo", 1, "hydro", "planned", -5.52, 13.62, 30, 50, 40, 370, False, 38, "Inga III phase ~40 TWh -> full Grand Inga theoretical ~370 TWh/yr; world-class low-cost head"],
    ["Hyrasia One / Mangystau", "Kazakhstan", 1, "solar+wind", "planned", 43.20, 52.00, 25, 45, 60, 120, False, 35, "~120 TWh/yr planned green-energy export zone"],
    ["Australian Renewable Energy Hub (Pilbara)", "Australia", 1, "solar+wind", "planned", -21.00, 119.00, 20, 40, 80, 90, False, 32, "~80-90 TWh/yr potential at full build"],
    ["Hyphen / Tsau Khaeb H2 zone", "Namibia", 1, "solar+wind", "planned", -26.65, 15.16, 18, 35, 25, 35, False, 29, "World-class combined solar+wind; ~25-35 TWh/yr at full build"],
    ["Boegoebaai / Northern Cape H2 hub", "South Africa", 1, "solar+wind", "planned", -29.00, 17.00, 20, 40, 25, 30, False, 30, "~25-30 TWh/yr planned"],
    ["Xlinks Morocco (Guelmim-Oued Noun)", "Morocco", 1, "solar+wind", "planned", 28.60, -10.50, 25, 45, 26, 30, False, 24, "~26-30 TWh/yr planned export"],
    ["Siberian Angara-Yenisei cascade", "Russia", 1, "hydro", "operating", 57.00, 95.00, 10, 40, 20, 60, False, 41, "Bratsk+Krasnoyarsk+... ; large, much already feeds aluminium; surplus strandable"],
    ["Itaipu Paraguayan surplus", "Paraguay", 1, "hydro", "operating", -25.41, -54.59, 10, 40, 20, 40, False, 9, "Paraguay consumes a fraction of its half; chronic exportable surplus"],
    ["Churchill Falls (+ Gull Island)", "Canada", 1, "hydro", "operating", 53.53, -64.00, 20, 50, 25, 35, False, 8, "~35 TWh/yr; long locked to Hydro-Quebec; strandable on recontracting/expansion"],
    ["Rogun HPP (Vakhsh)", "Tajikistan", 1, "hydro", "under-constr", 38.68, 69.78, 40, 70, 10, 17, False, 49, "~17 TWh/yr at full build; weak local market"],
    ["Grand Ethiopian Renaissance Dam", "Ethiopia", 1, "hydro", "operating", 11.21, 35.09, 30, 60, 8, 16, False, 43, "~15.8 TWh/yr design; partly stranded pending regional evacuation"],
    ["Cahora Bassa (Zambezi)", "Mozambique", 1, "hydro", "operating", -15.58, 32.70, 25, 55, 5, 16, False, 45, "~14-16 TWh/yr; much exported to S.Africa already"],
    ["NEOM green-H2 / Oxagon", "Saudi Arabia", 1, "solar+wind", "under-constr", 28.00, 35.30, 10, 25, 8, 10, False, 25, "~8-10 TWh/yr (4 GW at high MENA capacity factors)"],
    ["HidroAysen (Baker & Pascua)", "Chile", 1, "hydro", "potential", -47.80, -72.90, 50, 80, 0, 20, True, 46, "~18-20 TWh/yr would-be; never built; extremely remote Patagonia"],
    ["Mongolian Gobi / Gobitec", "Mongolia", 1, "solar+wind", "potential", 43.50, 104.50, 15, 35, 0, 2600, True, 34, "~2,600 TWh/yr THEORETICAL; reported as upper-bound potential only"],
    ["US Southwest desert solar belt", "United States", 1, "solar", "potential", 35.00, -116.00, 35, 45, 0, 300, True, 36, "Tens-hundreds of TWh/yr additional buildable; theoretical"],
    # cold-climate hydro/geothermal with exportable surplus (operating, modest)
    ["Norway northern hydro surplus", "Norway", 1, "hydro", "operating", 67.30, 15.40, 30, 50, 10, 25, False, 4, "Large legacy reservoir hydro; northern surplus, weak local load"],
    ["Northern Sweden hydro surplus", "Sweden", 1, "hydro", "operating", 65.58, 22.15, 30, 55, 8, 20, False, 5, "SE1/SE2 chronic northern surplus"],
    ["British Columbia hydro surplus", "Canada", 1, "hydro", "operating", 56.02, -122.20, 30, 60, 5, 15, False, 6, "Peace/Columbia heritage hydro; exportable surplus"],
    ["Manitoba Nelson River surplus", "Canada", 1, "hydro", "operating", 56.30, -94.60, 25, 50, 5, 12, False, 7, "Nelson River; ~97% hydro; exportable surplus"],
    ["Iceland geothermal+hydro surplus", "Iceland", 1, "geothermal", "operating", 64.04, -21.40, 30, 60, 3, 6, False, 0, "Island, no EU cable; historically monetised via aluminium"],

    # ---- Tier 2 : structurally curtailed existing fleets (spilled today) ---
    ["Xinjiang renewable base", "China", 2, "solar+wind", "curtailed", 43.80, 87.60, 0, 30, 10, 18, False, 12, "Currently-curtailed strandable ~10-18 TWh/yr"],
    ["Inner Mongolia W&S bases", "China", 2, "solar+wind", "curtailed", 40.80, 109.80, 0, 30, 10, 15, False, 13, "Among China's largest; curtailed ~10-15 TWh/yr"],
    ["Gansu Hexi Corridor", "China", 2, "solar+wind", "curtailed", 39.70, 98.50, 0, 30, 5, 10, False, 14, "Curtailed ~5-10 TWh/yr"],
    ["Qinghai Talatan/Gonghe/Golmud", "China", 2, "mixed-renewable", "curtailed", 36.20, 100.60, 0, 25, 3, 8, False, 15, "Curtailed ~3-8 TWh/yr"],
    ["West Texas / ERCOT West", "United States", 2, "solar+wind", "curtailed", 31.80, -102.40, 0, 35, 6, 10, False, 16, "~8 TWh/yr curtailed ERCOT-wide (mostly west)"],
    ["Atacama / N. Chile", "Chile", 2, "solar+wind", "curtailed", -23.60, -69.00, 0, 30, 5, 8, False, 17, "~5.9 TWh curtailed in 2024; world-record-low solar LCOE"],
    ["South Australia W&S fleet", "Australia", 2, "solar+wind", "curtailed", -33.50, 138.00, 0, 40, 4, 6, False, 18, "~4.5 TWh large-scale W&S curtailed"],
    ["Scotland onshore+offshore wind", "United Kingdom", 2, "wind", "curtailed", 56.50, -3.00, 0, 60, 6, 9, False, 19, "~8.3 TWh wind curtailed (constraint payments)"],
    ["California Central Valley/Mojave", "United States", 2, "solar", "curtailed", 35.50, -119.00, 0, 40, 3, 4, False, 20, "~3.4 TWh utility solar curtailed (CAISO)"],
    ["Spain / Iberia W&S", "Spain", 2, "solar+wind", "curtailed", 39.00, -5.00, 0, 35, 2, 6, False, 21, "Curtailment ~2% 2024 and rising"],
    ["Northern Scandinavia surplus", "Sweden/Norway", 2, "mixed-renewable", "curtailed", 65.60, 19.50, 0, 40, 3, 8, False, 22, "Persistent SE1/SE2 surplus"],
    ["Nepal Himalayan wet-season surplus", "Nepal", 2, "hydro", "curtailed", 27.90, 85.90, 40, 70, 2, 5, False, 11, "Monsoon run-of-river surplus, limited export"],
]

COLS = ["name", "country", "tier", "etype", "status", "lat", "lon",
        "lcoe_lo", "lcoe_hi", "strandable_TWh_lo", "strandable_TWh_hi",
        "theoretical", "src_row", "note"]


def write_portfolio_csv():
    path = os.path.join(DATA, "portfolio.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in P:
            w.writerow(r)
    return path


def aggregate():
    def s(rows, k):
        return sum(r[k] for r in rows)
    # index helpers
    LO, HI, TH, TIER = 9, 10, 11, 2
    rows = [list(r) for r in P]
    t1 = [r for r in rows if r[TIER] == 1]
    t2 = [r for r in rows if r[TIER] == 2]
    t1_real = [r for r in t1 if not r[TH]]
    t1_theo = [r for r in t1 if r[TH]]

    agg = {
        "tier1_realistic_TWh": [s(t1_real, LO), s(t1_real, HI)],
        "tier1_theoretical_extra_TWh": [s(t1_theo, LO), s(t1_theo, HI)],
        "tier2_curtailed_TWh": [s(t2, LO), s(t2, HI)],
        "portfolio_realistic_TWh": [s(t1_real, LO) + s(t2, LO),
                                    s(t1_real, HI) + s(t2, HI)],
        "portfolio_with_theoretical_TWh": [s(t1, LO) + s(t2, LO),
                                           s(t1, HI) + s(t2, HI)],
        "n_tier1": len(t1), "n_tier2": len(t2),
    }
    # by resource type (realistic only)
    bytype = {}
    for r in t1_real + t2:
        bytype.setdefault(r[3], [0, 0])
        bytype[r[3]][0] += r[LO]
        bytype[r[3]][1] += r[HI]
    agg["by_type_TWh"] = bytype
    return agg


def demand_scenarios(agg):
    PWh_J = 3.6e18  # 1 PWh in joules
    # electricity demand scenarios (PWh/yr)
    elec = {"IEA_2030": 1.0, "mid_10x": 10.0, "extreme_100x": 100.0}
    # 2025 token throughput and epsilon (J/token)
    tok_2025 = {"lo": 1.5e16, "hi": 2.0e16, "central": 1.75e16}
    eps = {"best_batched": 0.3, "central": 2.0, "frontier": 70.0,
           "lo": 0.15, "hi": 120.0}

    # portfolio realistic supply in PWh
    sup_lo = agg["portfolio_realistic_TWh"][0] / 1000.0
    sup_hi = agg["portfolio_realistic_TWh"][1] / 1000.0

    def tokens_from_PWh(pwh, eps_j):
        return pwh * PWh_J / eps_j

    res = {
        "elec_scenarios_PWh": elec,
        "token_throughput_2025": tok_2025,
        "epsilon_J_per_token": eps,
        "portfolio_realistic_PWh": [round(sup_lo, 3), round(sup_hi, 3)],
        # how the realistic portfolio compares to each electricity scenario
        "portfolio_vs_elec_multiple": {
            k: [round(sup_lo / v, 3), round(sup_hi / v, 3)] for k, v in elec.items()
        },
        # tokens/yr the realistic portfolio could embed, across epsilon
        "portfolio_tokens_per_yr": {
            "central_eps": [tokens_from_PWh(sup_lo, eps["central"]),
                            tokens_from_PWh(sup_hi, eps["central"])],
            "best_eps": [tokens_from_PWh(sup_lo, eps["best_batched"]),
                         tokens_from_PWh(sup_hi, eps["best_batched"])],
            "frontier_eps": [tokens_from_PWh(sup_lo, eps["frontier"]),
                             tokens_from_PWh(sup_hi, eps["frontier"])],
        },
        # multiples of 2025 throughput (central eps)
        "portfolio_multiple_of_2025_throughput_centralEps": [
            tokens_from_PWh(sup_lo, eps["central"]) / tok_2025["central"],
            tokens_from_PWh(sup_hi, eps["central"]) / tok_2025["central"],
        ],
        # external benchmark: Desert Power desert-WSS deliverable
        "desert_WSS_benchmark": {
            "source": "Zhu et al., Desert power for the AI era, Nexus 2026",
            "deliverable_PWh": [1, 100],
            "lcoe_USD_per_MWh": {"1PWh": 39, "10PWh": 46, "100PWh_capex_mid": "<60"},
            "capacity_lt_68USD_GW": 10000,
        },
    }
    return res


# ---------------------------------------------------------------------------
# NEW (v3.1, design §2 + §3.1): coverage surface + demand magnitude trajectory.
# Written to a SEPARATE file data/coverage_surface.json. The legacy function
# demand_scenarios() and data/portfolio_demand_results.json are left untouched.
# ---------------------------------------------------------------------------
PWh_J = 3.6e18  # 1 PWh in joules (matches demand_scenarios())


def coverage_surface(agg):
    """Pillar ②.1 coverage of the realistic portfolio against AI demand.

    Two distinct objects, because the ε-dependence is subtle:

    (a) ENERGY coverage (ε-INDEPENDENT). Portfolio token output and a PWh
        demand BOTH scale as 1/ε, so their ratio is just PWh/PWh and ε cancels.
        We report portfolio_PWh / scenario_PWh for the IEA-2030 (1 PWh), mid
        (10 PWh) and extreme (100 PWh) electricity scenarios. (This is the same
        family of multiples as the legacy portfolio_vs_elec_multiple, but framed
        explicitly as the ε-independent coverage of the argument.)

    (b) TOKEN coverage SURFACE over ε (ε-DEPENDENT). Here the target is a FIXED
        TOKEN COUNT (not an energy), so the portfolio's token output
            portfolio_tokens(ε) = portfolio_PWh * 3.6e18 / ε
        falls as ε rises while the target stays fixed -> a real ε dependence.
        For each token target we find the FLIP POINT ε*: the per-token energy at
        which coverage crosses 1.0 (portfolio can no longer cover that demand).
        Solving portfolio_tokens(ε*) = target  =>  ε* = portfolio_PWh*3.6e18/target.
    """
    sup_lo = agg["portfolio_realistic_TWh"][0] / 1000.0  # PWh/yr
    sup_hi = agg["portfolio_realistic_TWh"][1] / 1000.0

    # ---- (a) energy coverage (epsilon-independent) ------------------------
    elec = {"IEA_2030": 1.0, "mid_10x": 10.0, "extreme_100x": 100.0}
    energy_cov = {
        k: [round(sup_lo / v, 4), round(sup_hi / v, 4)] for k, v in elec.items()
    }

    # ---- (b) token-coverage surface over epsilon --------------------------
    # epsilon log grid over [0.15, 120] J/token (design ②.1 range).
    eps_lo, eps_hi, n_eps = 0.15, 120.0, 73
    log_lo, log_hi = math.log10(eps_lo), math.log10(eps_hi)
    eps_grid = [10.0 ** (log_lo + (log_hi - log_lo) * i / (n_eps - 1))
                for i in range(n_eps)]

    # token-demand targets: 2025 central throughput and 10x / 100x / 1000x.
    tok_2025_central = 1.75e16
    targets = {
        "T_2025x1": 1.0 * tok_2025_central,
        "T_2025x10": 10.0 * tok_2025_central,
        "T_2025x100": 100.0 * tok_2025_central,
        "T_2025x1000": 1000.0 * tok_2025_central,
    }

    def tokens(pwh, eps_j):
        return pwh * PWh_J / eps_j

    # surface[target] = list over eps of [coverage_lo, coverage_hi]
    surface = {}
    flip = {}
    for tname, tval in targets.items():
        row = []
        for e in eps_grid:
            cov_lo = tokens(sup_lo, e) / tval
            cov_hi = tokens(sup_hi, e) / tval
            row.append([cov_lo, cov_hi])
        surface[tname] = row
        # flip point eps* (coverage == 1) for the lo and hi portfolio bounds.
        # eps* = portfolio_PWh * 3.6e18 / target ; larger portfolio -> larger eps*.
        eps_star_lo = sup_lo * PWh_J / tval
        eps_star_hi = sup_hi * PWh_J / tval

        def _status(es):
            # Is the flip inside the studied epsilon window?
            if es >= eps_hi:
                return "covered_across_grid"   # portfolio covers target for all studied eps
            if es <= eps_lo:
                return "uncovered_across_grid"  # portfolio cannot cover even at best eps
            return "flips_within_grid"

        flip[tname] = {
            "target_tokens_per_yr": tval,
            "eps_star_J_lo_portfolio": round(eps_star_lo, 4),
            "eps_star_J_hi_portfolio": round(eps_star_hi, 4),
            "status_lo_portfolio": _status(eps_star_lo),
            "status_hi_portfolio": _status(eps_star_hi),
        }

    return {
        "_doc": ("Pillar 2.1 coverage. (a) energy_coverage is epsilon-INDEPENDENT "
                 "(PWh/PWh, epsilon cancels). (b) token_coverage_surface is "
                 "epsilon-DEPENDENT (fixed token target). flip_points give eps* "
                 "where portfolio_tokens(eps)=target."),
        "portfolio_realistic_PWh": [round(sup_lo, 3), round(sup_hi, 3)],
        "energy_coverage": {
            "_note": "epsilon-independent: portfolio_PWh / scenario_PWh, [lo, hi]",
            "scenarios_PWh": elec,
            "coverage_ratio": energy_cov,
        },
        "token_coverage_surface": {
            "_note": ("epsilon-dependent. coverage = portfolio_tokens(eps)/target, "
                      "portfolio_tokens(eps)=portfolio_PWh*3.6e18/eps. value=[lo,hi]."),
            "epsilon_J_per_token_grid": [round(e, 5) for e in eps_grid],
            "epsilon_grid_range": [eps_lo, eps_hi],
            "targets_tokens_per_yr": targets,
            "surface": surface,
            "flip_points": flip,
        },
    }


def demand_trajectory():
    """Pillar ①.1 — illustrative AI-electricity-demand growth 2025->2050.

    A few clearly-labelled illustrative PWh/yr trajectories (NOT forecasts):
      - iea_anchored   : ~1 PWh by 2030 (IEA 'Energy and AI'), continued growth
      - aggressive_10x : 10x of the 2025 base by 2035, then continued growth
      - conservative   : slow, saturating growth
    Plus the 2025 token-throughput baseline so the demand panel can anchor
    "today" before extrapolating. All electricity figures are PWh/yr; tokens are
    derived at the central epsilon for an illustrative right-hand axis only.
    """
    years = list(range(2025, 2051))

    # 2025 anchor: AI electricity demand ~0.4 PWh/yr (data-centre/AI share),
    # token throughput 1.5-2.0e16 tokens/yr (central 1.75e16).
    base_2025_PWh = 0.4
    tok_2025_central = 1.75e16
    eps_central = 2.0  # J/token, matches legacy demand_scenarios()

    def logistic(y, y0, k, ymid, cap, floor):
        return floor + (cap - floor) / (1.0 + math.exp(-k * (y - ymid)))

    traj = {}

    # IEA-anchored: hit ~1 PWh by 2030, keep growing toward ~6 PWh by 2050.
    iea = {}
    for y in years:
        # piecewise-smooth: ~0.4 (2025) -> ~1.0 (2030) -> ~6 (2050)
        if y <= 2030:
            v = base_2025_PWh + (1.0 - base_2025_PWh) * (y - 2025) / 5.0
        else:
            v = logistic(y, 2030, 0.18, 2040, 6.0, 1.0)
        iea[y] = round(v, 4)
    traj["iea_anchored"] = iea

    # Aggressive: 10x the 2025 base (-> ~4 PWh) by 2035, then on toward ~30 PWh.
    aggr = {}
    target_2035 = 10.0 * base_2025_PWh  # 4 PWh
    for y in years:
        if y <= 2035:
            # geometric ramp from base_2025 to target_2035
            n = (y - 2025) / 10.0
            v = base_2025_PWh * (target_2035 / base_2025_PWh) ** n
        else:
            v = logistic(y, 2035, 0.16, 2045, 30.0, target_2035)
        aggr[y] = round(v, 4)
    traj["aggressive_10x_by_2035"] = aggr

    # Conservative: slow saturating growth toward ~2.5 PWh by 2050.
    cons = {}
    for y in years:
        v = logistic(y, 2025, 0.12, 2038, 2.5, base_2025_PWh)
        cons[y] = round(v, 4)
    traj["conservative"] = cons

    # illustrative token-equivalent (central eps) for the IEA-anchored path
    iea_tokens = {y: iea[y] * PWh_J / eps_central for y in years}

    return {
        "_doc": ("Pillar 1.1 illustrative AI-electricity demand 2025-2050 "
                 "(PWh/yr). NOT forecasts; bracketing growth narratives only."),
        "label": "ILLUSTRATIVE - bracketing growth paths, not forecasts",
        "years": years,
        "baseline_2025": {
            "ai_electricity_PWh": base_2025_PWh,
            "token_throughput_tokens_per_yr": {"lo": 1.5e16, "hi": 2.0e16,
                                               "central": tok_2025_central},
            "epsilon_central_J_per_token": eps_central,
        },
        "trajectories_PWh": traj,
        "iea_anchored_tokens_per_yr_centralEps": iea_tokens,
        "endpoints_2050_PWh": {k: v[2050] for k, v in traj.items()},
    }


def supply_trajectory():
    """v3.3 — strandable-SUPPLY growth 2025->2050 (PWh/yr), CEILING set by the
    literature's future-DEVELOPABLE clean-energy potential, not today's named projects.

    Strandable supply is NOT static: as infrastructure builds out the base grows --
    (i) structural curtailment rises with VRE penetration (Tier 2), (ii) the mega-
    project + desert-export-hub pipeline comes online (Tier 1), (iii) fibre reach
    extends to interior sites. Two paths from today's curated realistic base
    (1.16-2.25 PWh, 35 sites):
      fixed       : today's identified portfolio, FROZEN (pessimistic floor).
      developable : grows to the ECONOMIC-developable stranded potential, ~25 PWh/yr
                    by 2050. Anchored to (a) Zhu et al. 2026 desert wind-solar-storage
                    ~10,000 GW < $68/MWh ~ 22-31 PWh/yr deliverable, and (b) Angliviel
                    de La Beaumelle et al. 2023 (Annu. Rev. Environ. Resour.), whose
                    *economic* potential already exceeds current+near-future demand.
                    Growth rate follows fast learning-curve deployment (Way et al. 2022,
                    Joule; IEA Net-Zero-2050: solar+wind generation ~45-50 PWh/yr by 2050).
    technical_potential_PWh is the ABSOLUTE bound (solar PV / CSP / on- & off-shore wind
    each >100 PWh/yr technically; all renewables 164-27,200 PWh/yr -- Angliviel de La
    Beaumelle et al. 2023), shown only as an off-scale reference: energy is not the limit.
    Illustrative paths, not forecasts. Used by Fig 3d/3e."""
    years = list(range(2025, 2051))
    lo, hi = 1.162, 2.254
    mid = 0.5 * (lo + hi)
    DEV_CAP = 25.0          # economic-developable stranded ceiling (PWh/yr); Zhu + ARER
    TECH_POT = 150.0        # representative technical potential (PWh/yr); >100 each, ARER

    def logistic(y, k, ymid, cap, floor):
        return floor + (cap - floor) / (1.0 + math.exp(-k * (y - ymid)))

    fixed = {y: round(mid, 4) for y in years}
    # fast-deployment logistic toward the developable ceiling (~2.1 PWh in 2025 -> ~23 in 2050)
    developable = {y: round(logistic(y, 0.24, 2041, DEV_CAP, mid), 4) for y in years}

    def crossover(traj, dem):
        # first year supply dips below demand; linear-interpolate the crossing
        for i in range(1, len(years)):
            a = traj[years[i - 1]] - dem[years[i - 1]]
            b = traj[years[i]] - dem[years[i]]
            if a >= 0 > b:
                return round(years[i - 1] + a / (a - b), 1)
        return None  # no crossover within 2025-2050

    dem = demand_trajectory()["trajectories_PWh"]
    dem_iea = {int(k): v for k, v in dem["iea_anchored"].items()}
    dem_aggr = {int(k): v for k, v in dem["aggressive_10x_by_2035"].items()}
    return {
        "_doc": ("Strandable-supply growth (PWh/yr). CEILING = future economic-developable "
                 "clean-energy potential (~25 PWh, Zhu et al. 2026 desert WSS + Angliviel de "
                 "La Beaumelle et al. 2023 economic potential > demand), NOT today's named "
                 "projects. Growth rate from learning-curve deployment (Way et al. 2022; IEA "
                 "NZE-2050). technical_potential is the absolute bound (>100 PWh each). "
                 "fixed = today's identified portfolio, frozen. Illustrative, not forecasts."),
        "label": "Supply grows toward the developable potential; technical bound is far above",
        "years": years,
        "today_realistic_PWh": [lo, hi],
        "ceilings_PWh": {"developable": DEV_CAP},
        "technical_potential_PWh": TECH_POT,
        "trajectories_PWh": {"fixed": fixed, "developable": developable},
        "crossover_year_vs_iea_demand": {
            "fixed": crossover(fixed, dem_iea),
            "developable": crossover(developable, dem_iea),
        },
        "crossover_year_vs_aggressive_demand": {
            "fixed": crossover(fixed, dem_aggr),
            "developable": crossover(developable, dem_aggr),
        },
    }


def write_coverage_surface(agg):
    out = {
        "coverage": coverage_surface(agg),
        "demand_trajectory": demand_trajectory(),
        "supply_trajectory": supply_trajectory(),
    }
    path = os.path.join(DATA, "coverage_surface.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return path, out


def main():
    os.makedirs(DATA, exist_ok=True)
    path = write_portfolio_csv()
    agg = aggregate()
    dem = demand_scenarios(agg)
    out = {"aggregates": agg, "demand": dem}
    with open(os.path.join(DATA, "portfolio_demand_results.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # ---- NEW (v3.1): coverage surface + demand trajectory (separate file) --
    cov_path, cov = write_coverage_surface(agg)

    # human-readable summary
    print("Portfolio written:", path, f"({len(P)} sites)")
    print(f"  Tier 1 realistic : {agg['tier1_realistic_TWh'][0]:.0f}-{agg['tier1_realistic_TWh'][1]:.0f} TWh/yr")
    print(f"  Tier 1 theoretical extra: {agg['tier1_theoretical_extra_TWh'][0]:.0f}-{agg['tier1_theoretical_extra_TWh'][1]:.0f} TWh/yr")
    print(f"  Tier 2 curtailed : {agg['tier2_curtailed_TWh'][0]:.0f}-{agg['tier2_curtailed_TWh'][1]:.0f} TWh/yr")
    print(f"  Portfolio realistic: {dem['portfolio_realistic_PWh'][0]:.2f}-{dem['portfolio_realistic_PWh'][1]:.2f} PWh/yr")
    print("  vs IEA-2030 (1 PWh):", dem["portfolio_vs_elec_multiple"]["IEA_2030"], "x")
    print("  vs 10 PWh scenario :", dem["portfolio_vs_elec_multiple"]["mid_10x"], "x")
    m = dem["portfolio_multiple_of_2025_throughput_centralEps"]
    print(f"  tokens/yr @ central eps = {m[0]:.0f}-{m[1]:.0f}x 2025 throughput")
    print("Results:", os.path.join(DATA, "portfolio_demand_results.json"))

    # ---- NEW headline numbers ---------------------------------------------
    ec = cov["coverage"]["energy_coverage"]["coverage_ratio"]
    print("\n[NEW] Coverage surface (data/coverage_surface.json):")
    print("  Energy coverage (epsilon-INDEPENDENT), [lo,hi]:")
    for k in ("IEA_2030", "mid_10x", "extreme_100x"):
        print(f"    {k:13s}: {ec[k][0]:.3f} - {ec[k][1]:.3f} x")
    print("  Token-coverage flip points eps* (J/token; coverage crosses 1.0):")
    fp = cov["coverage"]["token_coverage_surface"]["flip_points"]
    for k, d in fp.items():
        print(f"    {k:12s}: eps*=[{d['eps_star_J_lo_portfolio']:.3f}, "
              f"{d['eps_star_J_hi_portfolio']:.3f}]  "
              f"({d['status_lo_portfolio']} / {d['status_hi_portfolio']})")
    dt = cov["demand_trajectory"]
    print("[NEW] Demand trajectory 2025->2050 (PWh/yr), endpoints @2050:")
    for k, v in dt["endpoints_2050_PWh"].items():
        print(f"    {k:24s}: {v:.2f} PWh/yr")
    print("Results:", cov_path)


if __name__ == "__main__":
    main()
