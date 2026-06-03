"""
M2 - Global hourly temporal matching (SIGNATURE analysis)
=========================================================
Token demand exists everywhere, every hour. Desert Power firms EACH site to
24/7 with storage; here we show that a longitudinally distributed PORTFOLIO of
stranded sites follows the (near-continuous) GLOBAL token load with far less
storage than any single site needs - "follow-the-sun/wind compute".

Supply : real hourly capacity factors for representative sites across longitudes,
         from the Open-Meteo ERA5 archive (free, no token): shortwave radiation
         -> PV CF; 100 m wind speed -> turbine power curve -> wind CF. Hydro is
         modelled as a firm seasonal anchor. Year 2023. Cached to data/cache_openmeteo/.
Demand : a constructed GLOBAL token-demand envelope D(t) in UTC = sum over macro
         regions of (AI-usage weight) x (diurnal activity at local time). Aseasonal,
         with an overnight floor (agentic/batch). Assumptions documented here and
         in Supplementary_Methods.md.

Metrics: peak-to-mean of supply (single site vs portfolio) and of demand;
         storage (hours of mean load) to firm a flat load - single vs portfolio,
         split diurnal vs total; coincidence fraction for a routable batch load.

Outputs: data/temporal_matching_results.json, data/temporal_profiles.json
Run:  python analysis/temporal_matching.py   (needs internet on first run; then cached)
"""
import json, os, time, math
import numpy as np
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(DATA, "cache_openmeteo")
YEAR = 2023
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# representative portfolio sites spanning longitudes (subset of data/portfolio.csv)
# w_solar/w_wind = nameplate mix; hydro=firm anchor (no weather fetch)
SITES = [
    {"name": "West Texas",        "lat": 31.80, "lon": -102.40, "w_solar": 0.5, "w_wind": 0.5, "weight": 9},
    {"name": "Atacama (Chile)",   "lat": -23.60, "lon": -69.00, "w_solar": 0.7, "w_wind": 0.3, "weight": 7},
    {"name": "Noor (Morocco)",    "lat": 31.00, "lon": -6.86,  "w_solar": 0.8, "w_wind": 0.2, "weight": 28},
    {"name": "Hyphen (Namibia)",  "lat": -26.65, "lon": 15.16, "w_solar": 0.6, "w_wind": 0.4, "weight": 30},
    {"name": "Gobi/Qinghai (China)","lat": 37.00, "lon": 100.60,"w_solar": 0.6, "w_wind": 0.4, "weight": 60},
    {"name": "Pilbara (Australia)","lat": -21.00, "lon": 119.00,"w_solar": 0.6, "w_wind": 0.4, "weight": 85},
    {"name": "South Australia",   "lat": -33.50, "lon": 138.00, "w_solar": 0.4, "w_wind": 0.6, "weight": 5},
]
HYDRO = {"name": "Yarlung (hydro, firm anchor)", "lon": 95.0, "mean_cf": 0.55, "weight": 285}

# global token-demand envelope: macro region (tz offset hrs, AI-usage weight,
# representative centroid lon/lat for the demand map in Fig 2). Weights are
# DEMAND-side token-usage shares ESTIMATED from cited 2025 sources (no longer
# hand-set). They remain illustrative ORDER-OF-MAGNITUDE estimates - no public
# source gives a clean 6-macro-region token split - but each is now anchored:
#   * Anthropic Economic Index, Sep 2025 (Claude.ai country shares: US 21.6%,
#     India 7.2%, Brazil 3.7%; arXiv:2511.15080).
#   * Similarweb ChatGPT web traffic, Aug 2025 (US 15.1, India 9.3, Brazil 5.3,
#     UK 4.3, Indonesia 3.7, Japan 3.5, Germany 3.4, France 3.2, Philippines 3.0,
#     Canada 2.6; via Visual Capitalist / Similarweb blog).
#   * OpenAI / NBER w34255 "How People Use ChatGPT" (fastest growth in lower-
#     income countries; 18B msgs/wk, 700M users by Jul 2025).
#   * China National Data Bureau: ~30 trillion tokens/day mid-2025 (~1.1e16/yr;
#     ~140T/day by Mar 2026) served almost ENTIRELY by domestic models
#     (DeepSeek/Qwen/Doubao). ChatGPT/Claude are blocked in China, so the
#     consumer-platform sources above miss Chinese demand entirely.
# Two scenarios (both sum to 1; see Supplementary Methods S2):
#   "total"   (DEFAULT): all global token DEMAND incl. Chinese domestic models
#             (China ~30% of global -> East Asia is the largest region). The
#             honest basis for a GLOBAL token-demand map / follow-the-sun match.
#   "consumer": Western consumer platforms only (China ~ 0). Reported for
#             sensitivity. Toggle via env var AI_DEMAND_INCLUDE_CHINA=0.
INCLUDE_CHINA_DOMESTIC = os.environ.get("AI_DEMAND_INCLUDE_CHINA", "1") != "0"
_W_TOTAL = {"N. America": 0.18, "Europe+Africa": 0.19, "East Asia": 0.41,
            "South Asia": 0.12, "S. America": 0.07, "Oceania": 0.03}
_W_CONSUMER = {"N. America": 0.25, "Europe+Africa": 0.28, "East Asia": 0.16,
               "South Asia": 0.17, "S. America": 0.10, "Oceania": 0.04}
_W = _W_TOTAL if INCLUDE_CHINA_DOMESTIC else _W_CONSUMER
DEMAND_SCENARIO = "total_incl_china_domestic" if INCLUDE_CHINA_DOMESTIC else "consumer_western"
REGIONS = [
    {"name": "N. America",    "tz": -6.0, "w": _W["N. America"],    "lon": -100.0, "lat": 40.0},
    {"name": "Europe+Africa", "tz": 1.0,  "w": _W["Europe+Africa"], "lon": 15.0,   "lat": 30.0},
    {"name": "East Asia",     "tz": 8.0,  "w": _W["East Asia"],     "lon": 115.0,  "lat": 34.0},
    {"name": "South Asia",    "tz": 5.5,  "w": _W["South Asia"],    "lon": 78.0,   "lat": 22.0},
    {"name": "S. America",    "tz": -3.0, "w": _W["S. America"],    "lon": -58.0,  "lat": -15.0},
    {"name": "Oceania",       "tz": 10.0, "w": _W["Oceania"],       "lon": 140.0,  "lat": -28.0},
]
# 2025 global token throughput (central, tokens/yr) for absolute regional totals
THROUGHPUT_2025_CENTRAL = 1.75e16


def cf_wind(v):
    vin, vr, vout = 3.0, 12.0, 25.0
    v = np.asarray(v, float)
    out = np.zeros_like(v)
    ramp = (v >= vin) & (v < vr)
    out[ramp] = (v[ramp] ** 3 - vin ** 3) / (vr ** 3 - vin ** 3)
    out[(v >= vr) & (v < vout)] = 1.0
    return out


def cf_solar(ghi, pr=0.85):
    return np.clip(np.asarray(ghi, float) / 1000.0, 0, 1) * pr


def fetch_site(site):
    os.makedirs(CACHE, exist_ok=True)
    safe = site["name"].split("(")[0].strip()
    for ch in " /\\,:":
        safe = safe.replace(ch, "_")
    fn = os.path.join(CACHE, f"{safe}_{YEAR}.json")
    if os.path.exists(fn):
        with open(fn, encoding="utf-8") as f:
            return json.load(f)["hourly"]
    params = dict(latitude=site["lat"], longitude=site["lon"],
                  start_date=f"{YEAR}-01-01", end_date=f"{YEAR}-12-31",
                  hourly="shortwave_radiation,wind_speed_100m", timezone="UTC")
    for attempt in range(4):
        try:
            r = requests.get(ARCHIVE, params=params, timeout=60)
            r.raise_for_status()
            j = r.json()
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(j, f)
            time.sleep(1.0)
            return j["hourly"]
        except Exception as e:
            print(f"  retry {site['name']} ({attempt}): {e}")
            time.sleep(3.0)
    raise RuntimeError(f"failed to fetch {site['name']}")


def site_cf(site):
    h = fetch_site(site)
    ghi = np.array(h["shortwave_radiation"], float)
    wind = np.array(h["wind_speed_100m"], float)
    n = min(len(ghi), 8760)
    cf = site["w_solar"] * cf_solar(ghi[:n]) + site["w_wind"] * cf_wind(wind[:n])
    return cf[:8760] if n >= 8760 else np.pad(cf, (0, 8760 - n), mode="wrap")


def hydro_firm(mean_cf=0.55, n=8760):
    # firm seasonal anchor: high in NH summer monsoon, lower in winter; small ripple
    t = np.arange(n)
    seasonal = 1.0 + 0.18 * np.sin(2 * math.pi * (t - 120 * 24) / n)  # peak ~ May+
    cf = mean_cf * seasonal
    return np.clip(cf, 0, 1)


# ---------------------------------------------------------------------------
# Diurnal activity kernel a(h): the local-hour human-activity shape each region's
# demand follows. v3.1 replaced the hand-set Gaussian (peak 16:00, floor 0.45)
# with an EMPIRICAL kernel fitted to real Wikimedia hourly pageviews (CC0; the
# ja/de single-timezone projects), via analysis/fetch_diurnal_wikimedia.py ->
# data/diurnal_kernel.json. Truncated Fourier series (K=3); peak ~21:00 local,
# trough ~03:00, trough/peak ~0.11. It is a HUMAN WEB-ACTIVITY proxy, not measured
# AI inference. Coefficients are hardcoded as a self-contained fallback; the JSON,
# if present, takes precedence so a re-fetch/re-fit propagates automatically.
_KERNEL_FOURIER = [1.0, -0.1188, -0.5185, 0.0896, -0.3192, -0.0319, -0.1]  # [c0,a1,b1,a2,b2,a3,b3]
try:
    with open(os.path.join(DATA, "diurnal_kernel.json"), encoding="utf-8") as _kf:
        _KERNEL_FOURIER = json.load(_kf)["fourier_coef"]
except Exception:
    pass


def _diurnal_activity(local_h):
    """Empirical local-hour activity kernel a(h) (Fourier series, mean ~ 1)."""
    h = np.asarray(local_h, float)
    c = _KERNEL_FOURIER
    out = np.full(h.shape, c[0], dtype=float)
    for k in range(1, (len(c) - 1) // 2 + 1):
        out = out + c[2 * k - 1] * np.cos(2 * np.pi * k * h / 24.0) \
                  + c[2 * k] * np.sin(2 * np.pi * k * h / 24.0)
    return np.clip(out, 0.0, None)


def demand_envelope(n=8760):
    hours_utc = np.arange(n) % 24
    activity = _diurnal_activity

    D = np.zeros(n)
    for rg in REGIONS:
        local = (hours_utc + rg["tz"]) % 24
        D += rg["w"] * activity(local)
    return D / D.mean()  # normalize to mean 1


def storage_hours(supply, demand):
    """Hours of mean-load storage to firm `supply` (mean-normalized) to `demand`
    (mean-normalized, same mean). Lossless reservoir: span of cumulative (supply-demand)."""
    s = supply / supply.mean()
    d = demand / demand.mean()
    cum = np.cumsum(s - d)
    return float(cum.max() - cum.min())


def diurnal_storage_hours(supply):
    """storage to firm the AVERAGE day only (isolates diurnal component)."""
    s = supply / supply.mean()
    avg_day = s.reshape(-1, 24).mean(axis=0)
    avg_day = avg_day / avg_day.mean()
    cum = np.cumsum(avg_day - 1.0)
    return float(cum.max() - cum.min())


def p2m(x):
    return float(np.max(x) / np.mean(x))


def diurnal_p2m(x):
    ad = (x / x.mean()).reshape(-1, 24).mean(axis=0)
    return float(ad.max() / ad.mean())


# ---------------------------------------------------------------------------
# v3 additions (pillar @.2): seasonal granularity, heuristic relay allocation,
# LP benchmark. All ADD-ONLY: existing functions/keys above are untouched.
# ---------------------------------------------------------------------------

def daily_mean_series(x):
    """365 daily means of an 8760-vector, mean-normalised to 1 (as a list)."""
    d = x[:8760].reshape(365, 24).mean(axis=1)
    return (d / d.mean()).tolist()


# longitude bands grouping the 7 VRE sites for the "baton-pass" stacked plot.
# Each band advances ~6-8h earlier in UTC than the next, so they hand off the
# load through the UTC day (Asia/Oceania -> Africa/Europe -> Americas).
LON_BANDS = [
    {"name": "Asia-Pacific (60E-150E)",  "lo": 60.0,  "hi": 150.0},
    {"name": "Africa-Europe (-30W-60E)", "lo": -30.0, "hi": 60.0},
    {"name": "Americas (-150W--30W)",    "lo": -150.0, "hi": -30.0},
]


def band_of(lon):
    for b in LON_BANDS:
        if b["lo"] <= lon < b["hi"]:
            return b["name"]
    return LON_BANDS[-1]["name"]  # fallback (none expected)


def regional_demands(n=8760):
    """Per-region demand D_r(t) = w_r * activity(local), UTC-indexed, in the SAME
    arbitrary units as demand_envelope() before its mean-normalisation. Returns
    array (nregion, n) and the region names. Sum over regions == un-normalised D."""
    hours_utc = np.arange(n) % 24
    activity = _diurnal_activity

    Dr = np.zeros((len(REGIONS), n))
    for i, rg in enumerate(REGIONS):
        local = (hours_utc + rg["tz"]) % 24
        Dr[i] = rg["w"] * activity(local)
    return Dr, [rg["name"] for rg in REGIONS]


def heuristic_relay(cfs, names, port_eq, hydro_n, n=8760):
    """Transparent greedy/proportional relay allocation with ABSOLUTE scaling.

    Supply = balanced VRE portfolio (port_eq, mean=1) scaled so its annual mean
    equals the global-demand annual mean (supply just covers demand on average).
    Each hour the clean pool is served to the 6 regional demands proportionally
    (coincident demand first). Surplus -> batchable buffer / curtailment; deficit
    -> firm hydro anchor, then unmet. Also tracks each LONGITUDE BAND's share of
    the served load on the average UTC day (for the baton-pass stacked area).
    """
    Dr, region_names = regional_demands(n)
    D = Dr.sum(axis=0)                     # un-normalised global demand
    Dmean = D.mean()

    # ABSOLUTE scaling: clean VRE supply annual mean == global demand annual mean
    # (supply just covers demand on average). The firm HYDRO anchor is an extra,
    # realistically-sized firm capacity (strandable hydro share wf of demand mean)
    # that fills deficits AFTER coincident clean is exhausted. With this scaling
    # clean surplus exists (curtailment / batchable buffer), the firm anchor tops
    # up deficits, and a small residual stays unmet -> all three arms are visible,
    # and total served (clean+firm) matches the +hydro coincidence anchor (~0.94).
    wf = HYDRO["weight"] / (np.array([s["weight"] for s in SITES]).sum() + HYDRO["weight"])
    supply = port_eq / port_eq.mean() * Dmean              # clean VRE, mean == Dmean
    firm_cap = hydro_n / hydro_n.mean() * Dmean * wf       # firm anchor, mean=wf*Dmean

    # per-site clean contribution (each site mean-normalised, equal weight),
    # scaled to the same absolute pool as `supply` (sums to `supply`).
    site_norm = cfs / cfs.mean(axis=1, keepdims=True)   # (nsite, n), each mean 1
    site_supply = site_norm / len(names) / port_eq.mean() * Dmean

    served = np.zeros(n)        # coincident clean energy delivered to demand
    unmet = np.zeros(n)         # demand not met by clean+firm
    curtail = np.zeros(n)       # clean surplus not used by coincident demand
    firm_used = np.zeros(n)     # firm hydro dispatched into deficit
    # per-band served contribution on the AVERAGE UTC day (24 buckets)
    band_served_day = {b["name"]: np.zeros(24) for b in LON_BANDS}
    # map each site to its band index
    site_band = [band_of(s["lon"]) for s in SITES]

    for t in range(n):
        d_t = D[t]
        s_t = supply[t]
        if s_t >= d_t:
            served[t] = d_t            # all demand met by clean
            curtail[t] = s_t - d_t     # surplus -> batchable buffer / curtailment
        else:
            served[t] = s_t            # all clean used coincidently
            deficit = d_t - s_t
            f = min(firm_cap[t], deficit)
            firm_used[t] = f
            unmet[t] = deficit - f
        # attribute the COINCIDENT clean served energy to longitude bands by the
        # share each band contributes to clean output this hour (proportional).
        used_clean = min(s_t, d_t)
        if s_t > 1e-12 and used_clean > 0:
            hh = t % 24
            for j, bname in enumerate(site_band):
                contrib = site_supply[j, t] / s_t * used_clean
                band_served_day[bname][hh] += contrib

    # average over the 365 days
    for b in band_served_day:
        band_served_day[b] /= 365.0

    served_fraction = float(np.minimum(supply + firm_cap, D).sum() / D.sum())
    served_fraction_clean = float(served.sum() / D.sum())      # clean only
    served_fraction_with_firm = float((served.sum() + firm_used.sum()) / D.sum())

    return {
        "method": "greedy proportional relay, absolute scaling (clean VRE mean == demand mean)",
        "scaling": {"clean_supply_annual_mean": float(supply.mean()),
                    "demand_annual_mean": float(Dmean),
                    "firm_anchor_annual_mean": float(firm_cap.mean()),
                    "firm_share_wf": float(wf)},
        "served_fraction": served_fraction_with_firm,
        "served_fraction_clean_only": served_fraction_clean,
        "served_fraction_clean_plus_firm": served_fraction_with_firm,
        "annual_energy_units": {
            "demand": float(D.sum()),
            "clean_served": float(served.sum()),
            "firm_served": float(firm_used.sum()),
            "unmet": float(unmet.sum()),
            "curtailment": float(curtail.sum()),
        },
        "fractions": {
            "clean_served": float(served.sum() / D.sum()),
            "firm_served": float(firm_used.sum() / D.sum()),
            "unmet": float(unmet.sum() / D.sum()),
            "curtailment_of_clean": float(curtail.sum() / supply.sum()),
        },
        "residual_firm_mean_units": float(firm_used.mean()),
        "residual_firm_peak_units": float(firm_used.max()),
        # average-UTC-day hourly series (24) for the figure
        "avg_day": {
            "hours": list(range(24)),
            "demand": (D.reshape(365, 24).mean(axis=0)).tolist(),
            "clean_supply": (supply.reshape(365, 24).mean(axis=0)).tolist(),
            "clean_served": (served.reshape(365, 24).mean(axis=0)).tolist(),
            "firm_served": (firm_used.reshape(365, 24).mean(axis=0)).tolist(),
            "unmet": (unmet.reshape(365, 24).mean(axis=0)).tolist(),
            "curtailment": (curtail.reshape(365, 24).mean(axis=0)).tolist(),
        },
        # baton-pass: each longitude band's contribution to served load by UTC hour
        "baton_pass_avg_day": {
            "hours": list(range(24)),
            "bands": [b["name"] for b in LON_BANDS],
            "served_by_band": {b: band_served_day[b].tolist() for b in band_served_day},
        },
        "regions": region_names,
        "notes": "Coincident clean energy is served first; surplus is batchable "
                 "buffer/curtailment, deficit is firmed by the hydro anchor then "
                 "recorded as unmet. Energy in mean-1 'units' (1 unit = 1h of mean "
                 "global load); fractions are dimensionless and scale-free.",
    }


def lp_benchmark(cfs, port_eq, hydro_n):
    """Supplementary UPPER BOUND on served fraction via a small LP over the
    average UTC day (24 h) with a cyclic storage buffer. Decision variables per
    hour: u[t] (unmet), c[t] (curtailment), b[t] (storage state-of-charge),
    plus charge/discharge implied by the SoC dynamics. Minimise
        sum u + lam*sum b + mu*sum c
    s.t. clean_supply[t] - c[t] + discharge - charge == demand[t] - u[t],
    cyclic SoC, non-negativity. Solved with scipy.optimize.linprog (HiGHS).
    Falls back to a transparent no-storage bound if scipy is unavailable.
    """
    Dr, _ = regional_demands(8760)
    D = Dr.sum(axis=0)
    Dmean = D.mean()
    wf = HYDRO["weight"] / (np.array([s["weight"] for s in SITES]).sum()
                            + HYDRO["weight"])
    # average UTC day, absolute-scaled EXACTLY as the heuristic:
    # clean VRE mean == demand mean; firm anchor mean == wf * demand mean.
    dem = D.reshape(365, 24).mean(axis=0)
    sup = (port_eq / port_eq.mean() * Dmean).reshape(365, 24).mean(axis=0)
    firm = (hydro_n / hydro_n.mean() * Dmean * wf).reshape(365, 24).mean(axis=0)
    # firm is a firm (always-dispatchable up to its cap) anchor share
    avail = sup + firm
    T = 24
    lam, mu = 0.02, 0.01

    try:
        from scipy.optimize import linprog
        # variables: u[0..T-1], c[0..T-1], chg[0..T-1], dis[0..T-1], soc[0..T-1]
        # index helpers
        nU, nC, nCh, nDis, nS = 0, T, 2 * T, 3 * T, 4 * T
        N = 5 * T
        cobj = np.zeros(N)
        cobj[nU:nU + T] = 1.0            # minimise unmet
        cobj[nS:nS + T] = lam           # small penalty on stored energy
        cobj[nC:nC + T] = mu            # small penalty on curtailment
        A_eq, b_eq = [], []
        # energy balance per hour: avail - c + dis - chg = dem - u
        #   -> avail - c + dis - chg + u = dem
        for t in range(T):
            row = np.zeros(N)
            row[nU + t] = 1.0
            row[nC + t] = -1.0
            row[nDis + t] = 1.0
            row[nCh + t] = -1.0
            A_eq.append(row); b_eq.append(dem[t] - avail[t])
        # SoC dynamics (cyclic): soc[t] = soc[t-1] + chg[t] - dis[t]
        for t in range(T):
            row = np.zeros(N)
            row[nS + t] = 1.0
            row[nS + ((t - 1) % T)] = -1.0
            row[nCh + t] = -1.0
            row[nDis + t] = 1.0
            A_eq.append(row); b_eq.append(0.0)
        bounds = [(0, None)] * N
        r = linprog(cobj, A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                    bounds=bounds, method="highs")
        if r.success:
            x = r.x
            u = x[nU:nU + T]
            c = x[nC:nC + T]
            soc = x[nS:nS + T]
            served_fraction = float(1.0 - u.sum() / dem.sum())
            return {
                "method": "LP over average UTC day (24h) with cyclic storage, scipy.linprog/HiGHS",
                "objective_weights": {"lambda_storage": lam, "mu_curtail": mu},
                "served_fraction": served_fraction,
                "unmet_fraction": float(u.sum() / dem.sum()),
                "curtailment_fraction_of_clean": float(c.sum() / sup.sum()),
                "storage_peak_units": float(soc.max()),
                "storage_mean_units": float(soc.mean()),
                "notes": "Optimal served fraction is an UPPER BOUND on the heuristic "
                         "(perfect-foresight, frictionless storage over the average day).",
                "solver": "scipy.optimize.linprog HiGHS",
            }
    except Exception as e:
        pass
    # transparent fallback bound: with unlimited frictionless storage over the
    # average day, served fraction = min(1, mean(avail)/mean(dem)).
    sf = float(min(1.0, avail.mean() / dem.mean()))
    return {
        "method": "transparent fallback (no scipy): unlimited-storage average-day bound",
        "served_fraction": sf,
        "notes": "scipy unavailable; reporting min(1, mean(supply)/mean(demand)) "
                 "as the storage-unconstrained upper bound.",
        "solver": "fallback",
    }


def storage_vs_ratio(single_solar, port_sw, port_eq, port_firm, demand):
    """v3 ADDITION (Fig 3d time axis): diurnal storage (h of mean demand) needed to MEET
    the demand shape from a FIXED-shape supply scaled so its annual mean = r * demand mean,
    over a grid of r = supply/demand. Surplus is freely curtailed; the required buffer is
    the worst contiguous deficit on the average UTC day (cyclic Kadane). For r<1 the metric
    saturates (energy-short: no diurnal store can fix a mean shortfall) and is capped at
    `cap`. The figure maps year -> r = portfolio_PWh / demand_PWh(year), so as demand grows
    (r falls) the required storage rises -- the dispersed / firm portfolios rise latest."""
    d_avg = (demand / demand.mean()).reshape(-1, 24).mean(0)

    def stor(supply_norm, r, cap=24.0):
        s = (r * supply_norm / supply_norm.mean()).reshape(-1, 24).mean(0)  # avg day, mean=r
        g = d_avg - s                        # hourly deficit (demand - supply)
        g2 = np.concatenate([g, g])          # cyclic: worst deficit window may wrap midnight
        best = cur = 0.0
        for x in g2:
            cur = max(0.0, cur + x)
            best = max(best, cur)
        return float(min(best, cap))

    rs = [round(float(x), 4) for x in np.linspace(0.5, 4.0, 36)]
    configs = {"single_solar": single_solar, "biggest_only": port_sw,
               "balanced": port_eq, "plus_hydro": port_firm}
    return {
        "_doc": ("Diurnal storage (h of mean load) to MEET demand from a fixed-shape supply "
                 "at annual-mean ratio r=supply/demand. Surplus curtailed; buffer covers the "
                 "worst contiguous deficit (cyclic). r<1 saturates (energy-short), capped at "
                 "24 h. Figure maps year -> r = portfolio_PWh / demand_PWh(year)."),
        "ratio_grid": rs,
        "cap_h": 24.0,
        "storage_h": {k: [stor(v, r) for r in rs] for k, v in configs.items()},
    }


def main():
    os.makedirs(DATA, exist_ok=True)
    # supply
    cfs, weights, names = [], [], []
    for s in SITES:
        cf = site_cf(s)
        cfs.append(cf); weights.append(s["weight"]); names.append(s["name"])
        print(f"  {s['name']:24s} annual CF={cf.mean():.3f}  P2M={p2m(cf):.2f}")
    cfs = np.array(cfs)                       # (nsite, 8760)
    weights = np.array(weights, float)

    norm = cfs / cfs.mean(axis=1, keepdims=True)         # each site mean=1

    # (1) geographically BALANCED portfolio = equal weight  -> headline "distributed"
    port_eq = norm.mean(axis=0)                           # mean=1
    # (2) strandable-weighted = "follow only the biggest resources" (Eastern-skewed here)
    w = weights / weights.sum()
    port_sw = (w[:, None] * norm).sum(axis=0)             # mean=1

    # balanced portfolio + firm hydro anchor (Yarlung), strandable-weighted hydro share
    hydro = hydro_firm(HYDRO["mean_cf"])
    hydro_n = hydro / hydro.mean()
    wf = HYDRO["weight"] / (weights.sum() + HYDRO["weight"])
    port_firm = (1 - wf) * port_eq + wf * hydro_n         # mean ~1

    demand = demand_envelope()

    # reference single sites (mean-normalized): a typical SOLAR site, and best/worst
    p2m_each = [p2m(c) for c in cfs]
    solar_idx = int(np.argmax([s["w_solar"] for s in SITES]))   # most solar-dominated
    single_solar = norm[solar_idx]
    single_best = norm[int(np.argmin(p2m_each))]

    flat = np.ones(8760)

    def block(x):
        return {"p2m": p2m(x), "diurnal_p2m": diurnal_p2m(x),
                "diurnal_storage_h": diurnal_storage_hours(x),
                "seasonal_storage_h": storage_hours(x, flat),
                "routable_coincidence": float(np.minimum(x, demand).sum() / demand.sum())}

    res = {
        "year": YEAR,
        "demand_weight_scenario": DEMAND_SCENARIO,
        "sites": [{"name": n, "lon": s["lon"], "annual_cf": float(c.mean()),
                   "p2m": p2m(c), "diurnal_p2m": diurnal_p2m(c)}
                  for n, s, c in zip(names, SITES, cfs)],
        "single_solar_site": block(single_solar),
        "single_best_site": block(single_best),
        "balanced_portfolio_vre": block(port_eq),
        "strandable_weighted_vre": block(port_sw),
        "balanced_portfolio_plus_hydro": block(port_firm),
        "global_demand_envelope": {"p2m": p2m(demand), "diurnal_p2m": diurnal_p2m(demand)},
        "demand_regions": [
            {"name": r["name"], "tz": r["tz"], "weight": r["w"], "lon": r["lon"], "lat": r["lat"],
             "token_share": r["w"], "tokens_per_yr_central": r["w"] * THROUGHPUT_2025_CENTRAL}
            for r in REGIONS
        ],
        "demand_regions_note": (f"Demand-side AI-usage shares per macro region (sum=1), scenario "
                                f"'{DEMAND_SCENARIO}', ESTIMATED from cited 2025 sources (Anthropic "
                                "Economic Index Sep-2025; Similarweb ChatGPT traffic Aug-2025; OpenAI/"
                                "NBER w34255; China National Data Bureau) - illustrative order-of-"
                                "magnitude, not a measured split. token total = share x 2025 global "
                                f"throughput ({THROUGHPUT_2025_CENTRAL:.2e} tokens/yr, central). The "
                                f"longitudinal stagger still flattens the global envelope (diurnal "
                                f"P2M {diurnal_p2m(demand):.2f})."),
        "headline": {
            "diurnal_storage_single_solar_h": diurnal_storage_hours(single_solar),
            "diurnal_storage_balanced_h": diurnal_storage_hours(port_eq),
            "diurnal_storage_reduction_x": round(diurnal_storage_hours(single_solar)
                                                 / diurnal_storage_hours(port_eq), 1),
            "routable_coincidence_balanced": float(np.minimum(port_eq, demand).sum() / demand.sum()),
            "routable_coincidence_with_hydro": float(np.minimum(port_firm, demand).sum() / demand.sum()),
        },
        "notes": {
            "diurnal_vs_seasonal": "Diurnal storage (hours) is what batteries provide; the "
            "larger seasonal_storage_h is a multi-week residual handled by the firm hydro "
            "anchor and by letting batchable utilization flex seasonally - NOT by batteries "
            "(see supply-side risks).",
            "weighting": "balanced=equal weight (deliberate longitudinal spread); strandable="
            "weighted by curtailable/strandable TWh (Eastern-skewed in this subset), which "
            "smooths less - so geographic balance must be a design objective.",
        },
        "assumptions": {
            "supply": "Open-Meteo ERA5 archive 2023; PV PR=0.85; wind cut-in/rated/out=3/12/25 m/s",
            "demand": "aseasonal; diurnal kernel empirically fitted to Wikimedia hourly "
                      "pageviews (ja/de, CC0; Fourier K=3; peak ~21:00 local, trough/peak ~0.11; "
                      "see data/diurnal_kernel.json); region weights "
                      + ", ".join(f"{r['name']}={r['w']}" for r in REGIONS),
            "hydro": f"firm anchor mean CF={HYDRO['mean_cf']}, +-18% seasonal",
        },
    }

    # v3 ADDITION (Fig 3d time axis): storage-to-meet vs supply/demand ratio, 4 configs
    res["storage_vs_ratio"] = storage_vs_ratio(single_solar, port_sw, port_eq, port_firm, demand)

    # profiles for plotting: average UTC day + a winter & summer week
    def avg_day(x):
        return (x / x.mean()).reshape(-1, 24).mean(axis=0).tolist()
    port_vre = port_eq   # plotting uses the balanced portfolio
    prof = {
        "avg_day_utc": {
            "hours": list(range(24)),
            "sites": {n: avg_day(c) for n, c in zip(names, cfs)},
            "vre_portfolio": avg_day(port_eq),
            "portfolio_with_hydro": avg_day(port_firm),
            "demand": avg_day(demand),
        },
        # representative weeks (hour index ranges): mid-Jan and mid-Jul
        "winter_week": {
            "t": list(range(24 * 14, 24 * 21)),
            "vre_portfolio": (port_vre / port_vre.mean())[24 * 14:24 * 21].tolist(),
            "portfolio_with_hydro": (port_firm / port_firm.mean())[24 * 14:24 * 21].tolist(),
            "demand": (demand / demand.mean())[24 * 14:24 * 21].tolist(),
        },
        "summer_week": {
            "t": list(range(24 * 195, 24 * 202)),
            "vre_portfolio": (port_vre / port_vre.mean())[24 * 195:24 * 202].tolist(),
            "portfolio_with_hydro": (port_firm / port_firm.mean())[24 * 195:24 * 202].tolist(),
            "demand": (demand / demand.mean())[24 * 195:24 * 202].tolist(),
        },
    }

    # ---- v3 ADDITION 1: seasonal (365-day) daily-mean granularity ----------
    prof["seasonal_daily"] = {
        "days": list(range(365)),
        "vre_portfolio": daily_mean_series(port_eq),
        "portfolio_with_hydro": daily_mean_series(port_firm),
        "demand": daily_mean_series(demand),
        "notes": "365 daily means, mean-normalised. Demand is aseasonal (flat ~1); "
                 "the +hydro portfolio carries the seasonal anchor.",
    }

    # ---- v3 ADDITION 2: heuristic relay allocation (main-text) --------------
    alloc = heuristic_relay(cfs, names, port_eq, hydro_n)
    with open(os.path.join(DATA, "allocation_heuristic.json"), "w", encoding="utf-8") as f:
        json.dump(alloc, f, indent=2, ensure_ascii=False)

    # ---- v3 ADDITION 3: LP benchmark (supplementary upper bound) ------------
    lp = lp_benchmark(cfs, port_eq, hydro_n)
    lp["heuristic_served_fraction"] = alloc["served_fraction"]
    if lp.get("served_fraction", 0) > 0:
        lp["heuristic_pct_of_optimal"] = round(
            100.0 * alloc["served_fraction"] / lp["served_fraction"], 1)
    with open(os.path.join(DATA, "allocation_lp_benchmark.json"), "w", encoding="utf-8") as f:
        json.dump(lp, f, indent=2, ensure_ascii=False)

    with open(os.path.join(DATA, "temporal_matching_results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA, "temporal_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(prof, f)

    h = res["headline"]
    print("\n--- temporal matching (headline) ---")
    print("Diurnal P2M : single solar {:.2f} | balanced portfolio {:.2f} | +hydro {:.2f} | demand {:.2f}".format(
        res["single_solar_site"]["diurnal_p2m"], res["balanced_portfolio_vre"]["diurnal_p2m"],
        res["balanced_portfolio_plus_hydro"]["diurnal_p2m"], res["global_demand_envelope"]["diurnal_p2m"]))
    print("Diurnal storage (h of mean load): single solar {:.1f} -> balanced {:.1f}  ({:.1f}x less)".format(
        h["diurnal_storage_single_solar_h"], h["diurnal_storage_balanced_h"], h["diurnal_storage_reduction_x"]))
    print("Routable coincidence with global demand: balanced {:.2f} | +hydro {:.2f}".format(
        h["routable_coincidence_balanced"], h["routable_coincidence_with_hydro"]))
    print("Strandable-weighted (biggest-only) diurnal storage: {:.1f} h  (geographic balance matters)".format(
        res["strandable_weighted_vre"]["diurnal_storage_h"]))
    print("Seasonal residual (weeks, NOT batteries): balanced VRE {:.0f} h -> +hydro {:.0f} h".format(
        res["balanced_portfolio_vre"]["seasonal_storage_h"],
        res["balanced_portfolio_plus_hydro"]["seasonal_storage_h"]))
    print("Results:", os.path.join(DATA, "temporal_matching_results.json"))

    # --- v3 additions verification ---
    sd = prof["seasonal_daily"]
    vre_s = np.array(sd["vre_portfolio"]); fir_s = np.array(sd["portfolio_with_hydro"])
    dem_s = np.array(sd["demand"])
    print("\n--- v3 allocation additions ---")
    print("Seasonal daily range (min..max of mean-normalised series):")
    print("  balanced VRE   {:.3f}..{:.3f}".format(vre_s.min(), vre_s.max()))
    print("  +hydro         {:.3f}..{:.3f}".format(fir_s.min(), fir_s.max()))
    print("  demand         {:.3f}..{:.3f}  (aseasonal)".format(dem_s.min(), dem_s.max()))
    print("Heuristic served_fraction (clean+firm): {:.4f}  | clean-only {:.4f}".format(
        alloc["served_fraction"], alloc["served_fraction_clean_only"]))
    print("  unmet {:.3f} | curtailment-of-clean {:.3f} | residual firm mean {:.3f} units".format(
        alloc["fractions"]["unmet"], alloc["fractions"]["curtailment_of_clean"],
        alloc["residual_firm_mean_units"]))
    print("LP benchmark served_fraction (upper bound): {:.4f}  [{}]".format(
        lp["served_fraction"], lp.get("solver", "?")))
    if "heuristic_pct_of_optimal" in lp:
        print("  heuristic reaches {:.1f}% of LP optimal".format(lp["heuristic_pct_of_optimal"]))
    print("New files:", os.path.join(DATA, "allocation_heuristic.json"), "|",
          os.path.join(DATA, "allocation_lp_benchmark.json"))


if __name__ == "__main__":
    main()
