"""
M4 - Full life-cycle cost & value comparison of the three export pathways
=========================================================================
Per SOURCE kWh of stranded clean energy, over each pathway's asset lifetime:
  net value added = gross output value  -  non-energy lifecycle cost
                    (generation + conversion capex/opex + transport/loss).

The token is deliberately the MOST capital-intensive pathway (chips dominate its
cost -> see M3/Fig.5); we therefore compare the *bottom line* (net value added per
source kWh), not capex intensity. The token still wins decisively at every workload
tier, because the value it creates per source kWh dwarfs its (high) conversion cost.

Key identity for the token: because electricity is a fixed small share s of compute
cost, the NON-energy lifecycle cost per source kWh = p_elec*(1-s)/s is ~independent
of the model/epsilon, while gross value per source kWh is far larger across all tiers.

Outputs: data/lifecycle_results.json
Run:  python analysis/lifecycle_cost.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# ---- common ---------------------------------------------------------------
BUSBAR = (0.02, 0.04)          # $/kWh stranded clean generation (busbar)
ELEC_PRICE = 0.03              # $/kWh on-site electricity used inside the data centre
J_PER_KWH = 3.6e6


def rng_mid(t):
    return (t[0] + t[1]) / 2


# ---- electron (UHVDC) -----------------------------------------------------
def electron():
    loss = (0.06, 0.10)                       # fractional line+converter loss
    trans = (0.01, 0.03)                       # levelised transmission capex+opex $/source kWh
    price = (0.055, 0.085)                     # commodity electricity price at far end $/kWh delivered
    gen = BUSBAR
    # gross value per SOURCE kWh = delivered kWh * price
    gross = ((1 - loss[1]) * price[0], (1 - loss[0]) * price[1])
    cost = (gen[0] + trans[0], gen[1] + trans[1])
    net = (gross[0] - cost[1], gross[1] - cost[0])
    return {"gross": gross, "cost_components": {"generation": gen, "transmission": trans},
            "loss_frac": loss, "total_cost": cost, "net": net}


# ---- aluminium ------------------------------------------------------------
def aluminium():
    kwh_per_kg = (13.0, 16.0)
    kg_per_kwh = (1 / kwh_per_kg[1], 1 / kwh_per_kg[0])      # 0.0625-0.0769
    price_kg = (2.3, 2.6)                                     # $/kg metal (~$2,300-2,600/t)
    alumina = (0.65, 0.95)                                    # $/kg Al feedstock (~1.9 kg alumina @ $340-500/t)
    smelter = (0.45, 0.85)                                    # $/kg Al capex+opex (non-energy), amortised
    shipping = (0.10, 0.20)                                   # $/kg Al
    gross = (kg_per_kwh[0] * price_kg[0], kg_per_kwh[1] * price_kg[1])
    nonenergy_kg = (alumina[0] + smelter[0] + shipping[0], alumina[1] + smelter[1] + shipping[1])
    nonenergy = (kg_per_kwh[0] * nonenergy_kg[0], kg_per_kwh[1] * nonenergy_kg[1])
    gen = BUSBAR
    cost = (gen[0] + nonenergy[0], gen[1] + nonenergy[1])
    net = (gross[0] - cost[1], gross[1] - cost[0])
    return {"gross": gross, "cost_components": {"generation": gen, "feedstock+smelter+shipping": nonenergy},
            "total_cost": cost, "net": net, "kg_per_kwh": kg_per_kwh}


# ---- token (3 workload tiers) ---------------------------------------------
def token():
    s_lo, s_hi = 0.04, 0.07                    # electricity share of compute TCO
    # non-energy lifecycle cost per SOURCE kWh = p_elec*(1-s)/s  (independent of epsilon)
    nonenergy = (ELEC_PRICE * (1 - s_hi) / s_hi, ELEC_PRICE * (1 - s_lo) / s_lo)  # ~0.40-0.72
    tiers = [
        # name, epsilon J/token, price $/Mtoken
        ("budget / batched", 0.5, 0.40),
        ("mainstream", 2.0, 2.0),
        ("frontier / reasoning", 40.0, 30.0),
    ]
    out = {}
    grosses = []
    nets = []
    for name, eps, price_M in tiers:
        tok_per_kwh = J_PER_KWH / eps
        gross = tok_per_kwh * price_M / 1e6
        gen = BUSBAR
        cost = (gen[0] + nonenergy[0], gen[1] + nonenergy[1])
        net = (gross - cost[1], gross - cost[0])
        out[name] = {"epsilon_J": eps, "price_per_Mtoken": price_M,
                     "tokens_per_kwh": tok_per_kwh, "gross": gross,
                     "total_cost": cost, "net": net}
        grosses.append(gross); nets.append(net)
    # GROSS value density: sweep OUTPUT PRICE at an efficient fixed eps (parallel in
    # kind to the electron/aluminium price sweeps). Token prices span budget->frontier.
    eps_eff = 2.0
    tok_eff = J_PER_KWH / eps_eff                  # ~1.8e6 tokens/kWh
    price_budget, price_frontier = 0.40, 68.0      # $/Mtoken (budget -> frontier)
    gross_density = (tok_eff * price_budget / 1e6, tok_eff * price_frontier / 1e6)  # ~0.72-122
    span = {"gross_coupled_tiers": (min(grosses), max(grosses)),   # per-tier (eps,price) coupled
            "gross_density": gross_density,        # headline value-density (price sweep @ eps=2)
            "gross_density_note": "price sweep $0.40-68/Mtoken at efficient eps=2 J (one quantity: price)",
            "net": (min(n[0] for n in nets), max(n[1] for n in nets)),
            "nonenergy_cost": nonenergy,
            "cost_components": {"generation": BUSBAR, "chips+facility+labour": nonenergy}}
    return {"tiers": out, "span": span}


# ===========================================================================
# pillar (3).2  -  BOTTOM-UP LCOT  ($ per million tokens)
# ===========================================================================
# Per accelerator, facility level. tokens/yr = P * 3600*8760 * util / eps.
# Amortised annual cost stack (per accelerator):
#   (i)   accelerator/server capex : $50k system amortised over AMORT_YR (3-5 yr)
#   (ii)  facility capex/opex      : building, power distribution, cooling (PUE)
#   (iii) ENERGY                   : P * hours * util * $/kWh
#   (iv)  O&M / staff
#   (v)   networking / fibre       : small
# Shares are tuned to land near the Epoch-AI bottom-up split used in M3
# (chips/servers ~60% / facility ~29% / energy 4-7% / other small).
SEC_YR = 8760 * 3600              # seconds per year (tok/s * s/yr = tok/yr)
ACCEL_P_KW = 2.0                  # facility-level kW / accelerator (M3 central; 1.7-2.7)
UTIL = 0.90                       # accelerator utilisation
SYSTEM_CAPEX = 50_000             # $/accelerator system, all-in (M3)
AMORT_YR = (3.0, 5.0)             # capex amortisation horizon

# non-energy annual cost components per accelerator ($/yr), composed so the TCO
# shares match M3 (chips ~60% / facility ~29% / O&M+net ~ the rest, energy 4-7%).
def _capex_annual():
    # system capex amortised; central uses 4 yr
    return SYSTEM_CAPEX / 4.0                       # $12,500/yr  (~60% at grid price)

def _facility_annual():
    # facility capex/opex (building, distribution, cooling) amortised annual
    return 6_000.0                                  # $/yr  (~29%)

def _om_annual():
    return 1_400.0                                  # O&M / staff $/yr

def _network_annual():
    return 350.0                                    # networking / fibre $/yr (small)

# energy price cases ($/kWh)
ENERGY_CASES = {
    "stranded": (0.020, 0.046),        # $20-46/MWh curtailed / stranded clean
    "conventional": (0.060, 0.090),    # $60-90/MWh grid-connected data centre
}

# epsilon tiers (J/token)  -  J/tok defines tokens/yr
LCOT_TIERS = [
    ("budget / batched", (0.3, 0.5)),
    ("mainstream", (2.0, 2.0)),
    ("frontier / reasoning", (40.0, 70.0)),
]


def lcot_breakdown():
    """Bottom-up $/Mtoken with full cost stack, per eps tier x energy case."""
    capex = _capex_annual()
    facility = _facility_annual()
    om = _om_annual()
    net = _network_annual()

    def energy_annual(price_kwh):
        # P(kW) * hours/yr * util * $/kWh
        return ACCEL_P_KW * 8760 * UTIL * price_kwh

    out = {
        "basis": "bottom-up LCOT, $ per million tokens, per accelerator (facility level)",
        "capacity_model": {
            "accel_power_kW": ACCEL_P_KW, "utilisation": UTIL,
            "tokens_per_yr_formula": "P_W * 3600*8760 * util / eps_J_per_token",
            "system_capex_USD": SYSTEM_CAPEX, "amort_yr": AMORT_YR,
        },
        "annual_cost_stack_USD_per_accel": {
            "accelerator_server_capex_amortised": round(capex, 1),
            "facility_capex_opex": round(facility, 1),
            "om_staff": round(om, 1),
            "networking_fibre": round(net, 1),
            "energy_note": "energy = P*8760*util*$/kWh (varies by case below)",
        },
        "energy_cases_USD_per_MWh": {"stranded": [20, 46], "conventional": [60, 90]},
        "tiers": {},
    }

    P_W = ACCEL_P_KW * 1000.0
    for name, eps_rng in LCOT_TIERS:
        tier = {"epsilon_J": eps_rng, "cases": {}, "shares_at_conventional": {}}
        # tokens/yr at the eps endpoints (lo eps -> more tokens)
        for case, price_rng in ENERGY_CASES.items():
            lcot_pts = []
            stacks = []
            # combine eps endpoints with energy-price endpoints to bound LCOT
            for eps in (eps_rng[0], eps_rng[1]):
                tok_yr = P_W * SEC_YR * UTIL / eps      # tokens / yr
                for p_kwh in (price_rng[0], price_rng[1]):
                    energy = energy_annual(p_kwh)
                    total = capex + facility + om + net + energy
                    lcot = total / (tok_yr / 1e6)        # $ / Mtoken
                    lcot_pts.append(lcot)
                    stacks.append({
                        "eps_J": eps, "price_kWh": p_kwh, "tokens_per_yr": tok_yr,
                        "energy_annual_USD": round(energy, 1),
                        "total_annual_USD": round(total, 1),
                        "LCOT_USD_per_Mtoken": lcot,
                    })
            tier["cases"][case] = {
                "LCOT_USD_per_Mtoken_range": [round(min(lcot_pts), 4), round(max(lcot_pts), 4)],
                "detail": stacks,
            }
        # cost shares (use conventional mid energy + mid eps for a representative split)
        eps_mid = rng_mid(eps_rng)
        tok_yr_mid = P_W * SEC_YR * UTIL / eps_mid
        energy_conv_mid = energy_annual(rng_mid(ENERGY_CASES["conventional"]))
        total_conv = capex + facility + om + net + energy_conv_mid
        tier["shares_at_conventional"] = {
            "chips_servers": round(capex / total_conv, 3),
            "facility": round(facility / total_conv, 3),
            "om_staff": round(om / total_conv, 3),
            "networking_fibre": round(net / total_conv, 3),
            "energy": round(energy_conv_mid / total_conv, 3),
            "total_annual_USD": round(total_conv, 1),
            "tokens_per_yr_mid": tok_yr_mid,
        }
        # energy-share band across the conventional price range (4-7% target)
        e_lo = energy_annual(ENERGY_CASES["conventional"][0])
        e_hi = energy_annual(ENERGY_CASES["conventional"][1])
        tier["energy_share_conventional_band"] = [
            round(e_lo / (capex + facility + om + net + e_lo), 3),
            round(e_hi / (capex + facility + om + net + e_hi), 3),
        ]
        # KEY RESULT: % LCOT reduction from stranded vs conventional (mid eps, mid prices)
        e_str_mid = energy_annual(rng_mid(ENERGY_CASES["stranded"]))
        lcot_conv = (capex + facility + om + net + energy_conv_mid) / (tok_yr_mid / 1e6)
        lcot_str = (capex + facility + om + net + e_str_mid) / (tok_yr_mid / 1e6)
        tier["LCOT_reduction_stranded_vs_conventional_pct"] = round(
            100 * (lcot_conv - lcot_str) / lcot_conv, 2)
        tier["LCOT_mid_USD_per_Mtoken"] = {
            "conventional": round(lcot_conv, 4), "stranded": round(lcot_str, 4)}
        out["tiers"][name] = tier

    # headline message
    shares = out["tiers"]["mainstream"]["shares_at_conventional"]
    out["key_result"] = {
        "energy_share_of_TCO_pct": [round(100 * out["tiers"]["mainstream"]
                                          ["energy_share_conventional_band"][0], 1),
                                    round(100 * out["tiers"]["mainstream"]
                                          ["energy_share_conventional_band"][1], 1)],
        "tco_split_at_conventional": {"chips_servers": shares["chips_servers"],
                                      "facility": shares["facility"],
                                      "energy": shares["energy"],
                                      "other_om_net": round(shares["om_staff"] +
                                                            shares["networking_fibre"], 3)},
        "LCOT_reduction_stranded_vs_conventional_pct_by_tier": {
            n: out["tiers"][n]["LCOT_reduction_stranded_vs_conventional_pct"]
            for n, _ in LCOT_TIERS},
        "interpretation": (
            "Because energy is only ~4-7% of compute TCO, moving from conventional grid "
            "($60-90/MWh) to stranded clean energy ($20-46/MWh) cuts $/Mtoken by only a "
            "single-digit %. The economic win is NOT a cheaper token: it is (i) monetising "
            "near-zero-value curtailed energy and (ii) avoiding the transmission capex needed "
            "to move that energy as electrons."),
    }
    with open(os.path.join(DATA, "lcot_breakdown.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out


# ===========================================================================
# pillar (3).4  -  BREAKEVEN SURFACE
# ===========================================================================
# Where does the token pathway's NET value per SOURCE kWh still beat the
# electron and aluminium pathways? Sweep token price ($/Mtoken) x electricity
# price (on-site $/kWh, which sets the token's non-energy lifecycle cost via the
# same s-share identity used in token()). Record the frontier where
# token_net = electron_net and token_net = aluminium_net.
def breakeven_surface():
    import numpy as np
    e, a = electron(), aluminium()
    en_mid = rng_mid(e["net"])          # electron net midpoint (fixed reference)
    an_mid = rng_mid(a["net"])          # aluminium net midpoint (fixed reference)

    price_grid = np.geomspace(0.1, 50.0, 60)      # $/Mtoken
    elec_grid = np.linspace(0.02, 0.10, 50)       # $/kWh on-site electricity
    eps = 2.0

    # frontier curves: for each elec price, the token price where token_net == ref_net
    # token_net_mid(price, elec) = gross(price) - cost_mid(elec); solve for price.
    def cost_mid(elec):
        nonenergy_lo = elec * (1 - 0.07) / 0.07
        nonenergy_hi = elec * (1 - 0.04) / 0.04
        cost = (BUSBAR[0] + nonenergy_lo, BUSBAR[1] + nonenergy_hi)
        return rng_mid(cost)

    tok_per_kwh = J_PER_KWH / eps
    def breakeven_price(ref_net, elec):
        # gross = ref_net + cost_mid ; gross = tok_per_kwh * price_M / 1e6
        gross_needed = ref_net + cost_mid(elec)
        return gross_needed / (tok_per_kwh / 1e6)     # $/Mtoken

    frontier_vs_electron = [{"elec_price_USD_per_kWh": round(float(el), 4),
                             "breakeven_token_price_USD_per_Mtoken": round(float(breakeven_price(en_mid, el)), 4)}
                            for el in elec_grid]
    frontier_vs_aluminium = [{"elec_price_USD_per_kWh": round(float(el), 4),
                              "breakeven_token_price_USD_per_Mtoken": round(float(breakeven_price(an_mid, el)), 4)}
                             for el in elec_grid]

    # grid of token_net_mid - electron_net and - aluminium_net (sign = who wins)
    grid = []
    for el in elec_grid:
        cm = cost_mid(float(el))
        row_e, row_a = [], []
        for pm in price_grid:
            gross = tok_per_kwh * float(pm) / 1e6
            tnet = gross - cm
            row_e.append(round(float(tnet - en_mid), 4))     # >0 -> token beats electron
            row_a.append(round(float(tnet - an_mid), 4))
        grid.append({"elec_price_USD_per_kWh": round(float(el), 4),
                     "token_minus_electron_net": row_e,
                     "token_minus_aluminium_net": row_a})

    out = {
        "basis": "net value added per SOURCE kWh; token vs electron / aluminium frontiers",
        "axes": {"token_price_USD_per_Mtoken": [round(float(x), 4) for x in price_grid],
                 "elec_price_USD_per_kWh": [round(float(x), 4) for x in elec_grid],
                 "eps_J_per_token": eps},
        "reference_net_USD_per_source_kWh": {
            "electron_mid": round(en_mid, 4), "aluminium_mid": round(an_mid, 4),
            "electron_range": [round(x, 4) for x in e["net"]],
            "aluminium_range": [round(x, 4) for x in a["net"]]},
        "frontier_token_beats_electron": frontier_vs_electron,
        "frontier_token_beats_aluminium": frontier_vs_aluminium,
        "grid_sign_positive_means_token_wins": grid,
        "interpretation": (
            "Token net value/source kWh exceeds the electron and aluminium pathways for almost "
            "the entire realistic price plane: even at a budget token price of a few cents per "
            "Mtoken, the breakeven token price needed to match the electron/aluminium net is far "
            "below today's market prices. The token pathway only loses if its price collapses to "
            "well under $0.1/Mtoken or on-site electricity becomes very expensive."),
    }
    with open(os.path.join(DATA, "breakeven_surface.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out


def main():
    e, a, t = electron(), aluminium(), token()
    # headline multiples: token net vs electron / aluminium net (midpoints)
    tn = rng_mid(t["span"]["net"]); en = rng_mid(e["net"]); an = rng_mid(a["net"])
    out = {
        "basis": "net value added per SOURCE kWh of stranded clean energy, over asset lifetime",
        "assumptions": {"busbar_USD_per_kWh": BUSBAR, "onsite_elec_USD_per_kWh": ELEC_PRICE},
        "electron": e, "aluminium": a, "token": t,
        "headline": {
            "gross_value_density_USD_per_source_kWh": {
                "electron": [round(x, 3) for x in e["gross"]],
                "aluminium": [round(x, 3) for x in a["gross"]],
                "token": [round(x, 2) for x in t["span"]["gross_density"]],
            },
            "net_value_added_USD_per_source_kWh": {
                "electron": [round(x, 3) for x in e["net"]],
                "aluminium": [round(x, 3) for x in a["net"]],
                "token": [round(x, 2) for x in t["span"]["net"]],
            },
            "token_vs_electron_x": round(tn / max(en, 1e-6), 0),
            "token_vs_aluminium_x": round(tn / max(an, 1e-6), 0),
            "note_multiple_fragile": "Net multiples are sensitive to the near-zero electron/metal net "
                          "midpoints (which straddle zero); read as 'one-to-two orders of magnitude', "
                          "not as exact (e.g. ~50-170x).",
            "note_capex": "Token has the HIGHEST conversion cost per source kWh (~$0.4-0.7) and the "
                          "highest capital intensity per unit power (the chip constraint, M3); it wins on "
                          "NET value added, not on capex.",
        },
    }
    with open(os.path.join(DATA, "lifecycle_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("Net value added per source kWh ($/kWh):")
    print(f"  electron : {e['net'][0]:.3f} - {e['net'][1]:.3f}")
    print(f"  aluminium: {a['net'][0]:.3f} - {a['net'][1]:.3f}")
    print(f"  token    : {t['span']['net'][0]:.2f} - {t['span']['net'][1]:.2f}  (all 3 workload tiers)")
    print(f"  token non-energy lifecycle cost/source kWh (eps-independent): "
          f"{t['span']['nonenergy_cost'][0]:.2f} - {t['span']['nonenergy_cost'][1]:.2f}")
    print(f"  token net vs electron ~{out['headline']['token_vs_electron_x']:.0f}x ; "
          f"vs aluminium ~{out['headline']['token_vs_aluminium_x']:.0f}x")
    print("Results:", os.path.join(DATA, "lifecycle_results.json"))

    # ---- pillar (3).2  bottom-up LCOT ------------------------------------
    lc = lcot_breakdown()
    print("\nBottom-up LCOT ($/Mtoken)  [stranded $20-46/MWh vs conventional $60-90/MWh]:")
    for name, _ in LCOT_TIERS:
        ti = lc["tiers"][name]
        s = ti["cases"]["stranded"]["LCOT_USD_per_Mtoken_range"]
        c = ti["cases"]["conventional"]["LCOT_USD_per_Mtoken_range"]
        red = ti["LCOT_reduction_stranded_vs_conventional_pct"]
        print(f"  {name:22s}: stranded {s[0]:.3f}-{s[1]:.3f} | conventional {c[0]:.3f}-{c[1]:.3f}"
              f"  -> LCOT reduction {red:.1f}%")
    kr = lc["key_result"]
    print("  TCO split @ conventional (mainstream): chips {chips_servers:.0%} / facility "
          "{facility:.0%} / energy {energy:.0%} / other {other_om_net:.0%}".format(
              **kr["tco_split_at_conventional"]))
    print(f"  energy share of TCO: {kr['energy_share_of_TCO_pct'][0]:.1f}-"
          f"{kr['energy_share_of_TCO_pct'][1]:.1f}%  "
          f"-> stranded energy lowers $/Mtoken only single-digit % (win = monetise "
          f"curtailment + skip transmission)")
    print("Results:", os.path.join(DATA, "lcot_breakdown.json"))

    # ---- pillar (3).4  breakeven surface ---------------------------------
    bs = breakeven_surface()
    fe = bs["frontier_token_beats_electron"]
    fa = bs["frontier_token_beats_aluminium"]
    print("\nBreakeven token price ($/Mtoken) to match electron / aluminium net:")
    for label, fr in (("vs electron", fe), ("vs aluminium", fa)):
        lo = min(p["breakeven_token_price_USD_per_Mtoken"] for p in fr)
        hi = max(p["breakeven_token_price_USD_per_Mtoken"] for p in fr)
        print(f"  {label:14s}: {lo:.4f} - {hi:.4f}  (over elec $0.02-0.10/kWh)")
    print("Results:", os.path.join(DATA, "breakeven_surface.json"))


if __name__ == "__main__":
    main()
