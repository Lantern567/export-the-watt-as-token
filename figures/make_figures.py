# -*- coding: utf-8 -*-
"""
Publication figures (v3) for the Perspective
"Waking the world's untapped mega-energy resources through the global token economy".

4-pillar, demand-first display plan (<=6 main displays; Box 1 counts):
  Fig 1  three export pathways (concept)                                  [keep]
  Fig 2  DEMAND: multi-time-granularity + multi-scenario growth (P1)      [NEW; M1+M2]
  Fig 3  SUPPLY & MATCHING: world map + follow-the-sun + storage (P2)     [NEW; map + M2]
  Fig 4  ECONOMICS: value density + net value + TCO/LCOT (P3)             [reworked; M4]
  Fig 5  CONSTRAINT: tornado + phase diagram + scenarios (P4)             [reworked; M3]
  Box 1  candidate-project portfolio table                               [keep]
  Fig S1 follow-the-sun small-multiples world map (supplementary, P2)     [NEW; optional]

Maps use cartopy (frykit mandate relaxed by the user). Connectivity layers
(submarine cables, landing points) are fetched by analysis/fetch_map_layers.py.
English-only labels. PNG (300 dpi) + PDF.
"""
import os, re, csv, json, warnings
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from matplotlib.gridspec import GridSpec

warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CSV = os.path.join(DATA, "portfolio.csv")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
    "axes.labelsize": 9, "axes.linewidth": 0.8, "savefig.dpi": 300,
    "figure.dpi": 120, "axes.unicode_minus": False,
})
C = {"base": "#2563EB", "second": "#F59E0B", "hi": "#DC2626",
     "neutral": "#64748B", "pos": "#059669", "purple": "#7C3AED", "cyan": "#0EA5E9"}
ET_COLOR = {"hydro": C["base"], "solar": C["second"], "wind": C["cyan"],
            "solar+wind": C["pos"], "mixed-renewable": C["purple"], "geothermal": C["hi"]}
ET_LABEL = {"hydro": "Hydro", "solar": "Solar", "wind": "Wind", "solar+wind": "Solar+Wind",
            "mixed-renewable": "Mixed renewable", "geothermal": "Geothermal"}


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# ============================================================================ Fig 1
def fig1():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.set_xlim(0, 1.12); ax.set_ylim(0, 1); ax.axis("off")

    def box(x, y, w, h, text, fc, ec, tc="#111", fs=8.4, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                     boxstyle="round,pad=0.006,rounding_size=0.018",
                     linewidth=1.3, edgecolor=ec, facecolor=fc, zorder=2))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=fs, color=tc, weight=weight, zorder=3)

    box(0.012, 0.40, 0.195, 0.23,
        "Stranded\nclean-energy site\n(remote mega-hydro,\ndesert wind-solar,\nor curtailed fleet)",
        "#EAF2F8", C["base"], fs=8.2, weight="bold")

    rows = [
        (0.80, 0.60, C["neutral"], "Electrons - UHVDC",
         "+-800-1100 kV line\n2,000-3,000 km\n-6-10% loss",
         "Commodity electricity\n~$0.05-0.08 / source kWh\nreach: regional"),
        (0.50, 0.51, C["second"], "Aluminium - smelter",
         "Hall-Heroult\n14 kWh kg$^{-1}$\nship metal",
         "Aluminium (\"canned electricity\")\n~$0.14-0.20 / source kWh\nreach: global, shipped"),
        (0.20, 0.42, C["hi"], "AI tokens - inference",
         "Data centre ->\noptical fibre\n~0 loss - ms latency",
         "AI tokens\n~$0.7-123 / source kWh\nreach: global, instant"),
    ]
    for yc, ys, col, tag, mid, dest in rows:
        ax.annotate("", xy=(0.345, yc), xytext=(0.21, ys),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2), zorder=1)
        ax.text(0.46, yc + 0.105, tag, ha="center", fontsize=8.6, color=col, weight="bold")
        box(0.345, yc - 0.085, 0.225, 0.17, mid, "white", col, fs=7.9)
        ax.annotate("", xy=(0.655, yc), xytext=(0.572, yc),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2), zorder=1)
        box(0.655, yc - 0.095, 0.31, 0.19, dest, "white", col, fs=8.2)

    ax.annotate("", xy=(1.045, 0.83), xytext=(1.045, 0.16),
                arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.6))
    ax.text(1.08, 0.5, "value density  ~10-1000x", rotation=90,
            va="center", ha="center", fontsize=8.6, color="#444")
    save(fig, "Fig1_three_pathways")


# ============================================================================ Fig 2  DEMAND
def fig2():
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    cov = load("coverage_surface.json")
    prof = load("temporal_profiles.json")
    tm = load("temporal_matching_results.json")
    dt = cov["demand_trajectory"]
    years = dt["years"]
    traj = dt["trajectories_PWh"]
    regions = tm["demand_regions"]

    import cartopy.io.shapereader as shpreader
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    fig = plt.figure(figsize=(10.4, 10.8))
    gs = GridSpec(3, 2, height_ratios=[1.86, 1.0, 1.0],
                  hspace=0.36, wspace=0.26, left=0.07, right=0.95, bottom=0.06, top=0.93)

    # (a) MAP: regional token demand as a CHOROPLETH (colour depth = share) ---
    m = fig.add_subplot(gs[0, :], projection=ccrs.PlateCarree())
    _basemap(m, ccrs, cfeature, extent=(-168, 182, -56, 84))
    rshare = {r["name"]: r["token_share"] for r in regions}

    def region_of(att):
        cont = att.get("CONTINENT", ""); sub = att.get("SUBREGION", "")
        if cont == "North America": return "N. America"
        if cont in ("Europe", "Africa"): return "Europe+Africa"
        if cont == "South America": return "S. America"
        if cont == "Oceania": return "Oceania"
        if cont == "Asia":
            if sub == "Eastern Asia": return "East Asia"
            if sub == "Southern Asia": return "South Asia"
        return None

    cmap = plt.cm.Blues; norm = Normalize(0, 0.40)
    shp = shpreader.natural_earth(resolution="110m", category="cultural", name="admin_0_countries")
    for rec in shpreader.Reader(shp).records():
        reg = region_of(rec.attributes)
        if reg is None:
            continue
        m.add_geometries([rec.geometry], ccrs.PlateCarree(), facecolor=cmap(norm(rshare[reg])),
                         edgecolor="white", linewidth=0.15, zorder=3)
    for r in regions:
        tz = r["tz"]; tzs = f"{tz:+.0f}" if float(tz).is_integer() else f"{tz:+.1f}"
        m.annotate(f"{r['name']} {r['token_share']*100:.0f}%\n(UTC{tzs})",
                   (r["lon"], r["lat"]), ha="center", va="center", fontsize=6.2,
                   color="#0F172A", zorder=7, transform=ccrs.PlateCarree(),
                   bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.6))
    sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    cax = m.inset_axes([0.015, 0.08, 0.016, 0.40])
    cb = fig.colorbar(sm, cax=cax); cb.set_label("AI-usage / token share", fontsize=6.2)
    cb.ax.tick_params(labelsize=5.5)
    m.set_title("(a) Where token demand sits: macro-regions shaded by AI-usage / token share (illustrative)",
                fontsize=8.6, loc="left")

    # (b) multi-year, multi-scenario growth ----------------------------------
    a = fig.add_subplot(gs[1, 0])
    def series(k): return [traj[k][str(y)] for y in years]
    lo = series("conservative"); hi = series("aggressive_10x_by_2035"); mid = series("iea_anchored")
    a.fill_between(years, lo, hi, color=C["base"], alpha=0.10, zorder=1)
    a.plot(years, hi, color=C["hi"], lw=2.0, label="Aggressive (10x by 2035)")
    a.plot(years, mid, color=C["base"], lw=2.4, label="IEA-anchored")
    a.plot(years, lo, color=C["pos"], lw=2.0, label="Conservative")
    a.scatter([2030], [1.0], color="#111", s=26, zorder=5)
    a.annotate("IEA 2030\n~1 PWh", (2030, 1.0), xytext=(2031, 3.4), fontsize=7.2,
               arrowprops=dict(arrowstyle="->", color="#111", lw=0.8))
    for k, col in [("aggressive_10x_by_2035", C["hi"]), ("iea_anchored", C["base"]), ("conservative", C["pos"])]:
        a.text(2050.2, dt["endpoints_2050_PWh"][k], f"{dt['endpoints_2050_PWh'][k]:.1f}",
               fontsize=7, color=col, va="center")
    a.set_xlim(2025, 2052); a.set_ylim(0, 23)
    a.set_xlabel("Year"); a.set_ylabel("AI electricity demand (PWh yr$^{-1}$)")
    a.set_title("(b) Token demand is large and growing (illustrative paths)", fontsize=8.8)
    a.legend(fontsize=7, frameon=False, loc="upper left")
    a.spines[["top", "right"]].set_visible(False)
    a.grid(color="#EEF1F4", lw=0.5)

    # (c) diurnal: flat global demand vs staggered single sites ---------------
    b = fig.add_subplot(gs[1, 1])
    ad = prof["avg_day_utc"]; H = ad["hours"]
    for y in ad["sites"].values():
        b.plot(H, y, color=C["neutral"], lw=0.8, alpha=0.40, zorder=2)
    b.plot(H, ad["demand"], color="#111", lw=2.4, ls="--", zorder=4, label="Global token demand")
    p2m_d = tm["global_demand_envelope"]["diurnal_p2m"]
    b.text(0.5, ad["demand"][0]*0.62, f"global demand\nP2M {p2m_d:.2f}", fontsize=7.4, color="#111")
    b.set_xlim(0, 23); b.set_xlabel("Hour (UTC)"); b.set_ylabel("Normalised (mean=1)")
    b.set_title("(c) Diurnal: demand far flatter than any site", fontsize=8.8)
    b.spines[["top", "right"]].set_visible(False); b.grid(color="#EEF1F4", lw=0.5)

    # (d) weekly --------------------------------------------------------------
    c = fig.add_subplot(gs[2, 0])
    ww = prof["winter_week"]; t = np.array(ww["t"]); t0 = (t - t[0]) / 24.0
    c.plot(t0, ww["vre_portfolio"], color=C["base"], lw=1.3, label="Balanced portfolio (supply)")
    c.plot(t0, ww["demand"], color="#111", lw=2.0, ls="--", label="Global token demand")
    c.set_xlim(0, t0[-1]); c.set_xlabel("Day (representative winter week)")
    c.set_ylabel("Normalised (mean=1)")
    c.set_title("(d) Weekly: demand stays flat; supply swings", fontsize=8.8)
    c.legend(fontsize=7, frameon=False, loc="upper right")
    c.spines[["top", "right"]].set_visible(False); c.grid(color="#EEF1F4", lw=0.5)

    # (e) seasonal ------------------------------------------------------------
    d = fig.add_subplot(gs[2, 1])
    sd = prof["seasonal_daily"]; days = sd["days"]
    d.plot(days, sd["vre_portfolio"], color=C["base"], lw=1.0, alpha=0.9, label="VRE portfolio")
    d.plot(days, sd["portfolio_with_hydro"], color=C["pos"], lw=1.4, label="+ hydro anchor")
    d.plot(days, sd["demand"], color="#111", lw=2.0, ls="--", label="Demand (aseasonal)")
    d.set_xlim(0, 364); d.set_xlabel("Day of year")
    d.set_ylabel("Normalised (mean=1)")
    d.set_title("(e) Seasonal: demand aseasonal; supply has a residual", fontsize=8.8)
    d.legend(fontsize=6.8, frameon=False, loc="lower center", ncol=3)
    d.spines[["top", "right"]].set_visible(False); d.grid(color="#EEF1F4", lw=0.5)

    save(fig, "Fig2_demand")


# ============================================================================ map helpers
def _iter_lines(geom):
    """Yield (lons, lats) arrays for a (Multi)LineString geometry, split at antimeridian."""
    t = geom["type"]; coords = geom["coordinates"]
    lines = coords if t == "MultiLineString" else [coords]
    for ln in lines:
        arr = np.asarray(ln, float)
        if arr.ndim != 2 or arr.shape[0] < 2:
            continue
        lon = arr[:, 0]; lat = arr[:, 1]
        brk = np.where(np.abs(np.diff(lon)) > 180)[0]
        seg = np.split(np.arange(len(lon)), brk + 1)
        for idx in seg:
            if len(idx) >= 2:
                yield lon[idx], lat[idx]


def _basemap(ax, ccrs, cfeature, extent=(-180, 180, -56, 80)):
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.set_facecolor("#EAF2F8")
    ax.add_feature(cfeature.LAND, facecolor="#F4F4F2", zorder=1)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.35, edgecolor="#AEB6BF", zorder=2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.22, edgecolor="#CBD2D9", zorder=2)


def _portfolio_sites():
    with open(CSV, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    lat = np.array([float(r["lat"]) for r in rows])
    lon = np.array([float(r["lon"]) for r in rows])
    twh = np.array([0.5*(float(r["strandable_TWh_lo"]) + float(r["strandable_TWh_hi"])) for r in rows])
    sizes = 16 + 26*np.sqrt(np.clip(twh, 1, 320))
    cols = [ET_COLOR.get(r["etype"], C["neutral"]) for r in rows]
    edge = ["#111" if r["tier"] == "1" else "white" for r in rows]
    elw = [0.8 if r["tier"] == "1" else 0.5 for r in rows]
    return rows, lat, lon, sizes, cols, edge, elw


def _circle_image(path, label="", px=320, ring_rgb=(0.15, 0.39, 0.92), ring_px=10, band_frac=0.36):
    """Center-crop a photo to a square, mask into a circle, add a coloured ring and a
    translucent white caption band (lower portion) carrying the site label. Returns a
    float RGBA array for matplotlib's OffsetImage."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGB")
    w, h = im.size; s = min(w, h)
    im = im.crop(((w - s)//2, (h - s)//2, (w - s)//2 + s, (h - s)//2 + s)).resize((px, px), Image.LANCZOS).convert("RGBA")
    dr = ImageDraw.Draw(im, "RGBA")
    band_top = int(px * (1 - band_frac))
    dr.rectangle([0, band_top, px, px], fill=(255, 255, 255, 95))       # translucent caption band
    if label:
        import matplotlib
        fp = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf", "DejaVuSans-Bold.ttf")
        R = px / 2.0
        ty_center = band_top + 0.30 * (px - band_top)      # text in the upper part of the band
        fs = int(px * 0.15); font = None; sw = 2; bb = (0, 0, 0, 0); th = 0
        while fs > 6:
            try:
                font = ImageFont.truetype(fp, fs)
            except Exception:
                font = ImageFont.load_default()
            sw = max(2, int(fs * 0.10))
            bb = dr.textbbox((0, 0), label, font=font, stroke_width=sw)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            dy = abs(ty_center + th / 2.0 - R)             # circle chord at the text's lower edge
            chord = 2.0 * np.sqrt(max(R * R - dy * dy, 1.0))
            if tw <= chord * 0.90:                         # fit within the circle, not just the square
                break
            fs -= 2
        tw = bb[2] - bb[0]
        dr.text(((px - tw)//2 - bb[0], int(ty_center - th / 2.0) - bb[1]),
                label, fill=(15, 15, 15, 255), font=font,
                stroke_width=sw, stroke_fill=(255, 255, 255, 235))
    arr = np.asarray(im, float) / 255.0
    yy, xx = np.mgrid[0:px, 0:px]
    R = px / 2.0; r = np.hypot(xx - (px - 1)/2.0, yy - (px - 1)/2.0)
    arr[..., 3] = arr[..., 3] * np.clip(R - r, 0, 1)                    # circular mask
    ring = (r <= R) & (r >= R - ring_px)
    for k in range(3):
        arr[..., k][ring] = ring_rgb[k]
    arr[..., 3][ring] = 1.0
    return arr


# ============================================================================ Fig 3  SUPPLY & MATCHING
def fig3():
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    al = load("allocation_heuristic.json")
    tm = load("temporal_matching_results.json")
    pdr = load("portfolio_demand_results.json")
    cov = load("coverage_surface.json")
    chp = load("chip_scenarios.json")

    fig = plt.figure(figsize=(10.4, 10.8))
    gs = GridSpec(3, 2, height_ratios=[1.86, 1.0, 1.0], hspace=0.36, wspace=0.26,
                  left=0.07, right=0.95, bottom=0.06, top=0.93)

    # (a) world map ----------------------------------------------------------
    ax = fig.add_subplot(gs[0, :], projection=ccrs.PlateCarree())
    _basemap(ax, ccrs, cfeature)
    # submarine cables
    try:
        cab = load("cables.geojson")
        for ft in cab["features"]:
            for lo, la in _iter_lines(ft["geometry"]):
                ax.plot(lo, la, color="#8B7EC8", lw=0.28, alpha=0.45,
                        transform=ccrs.PlateCarree(), zorder=3)
    except Exception as e:
        print("  cables skipped:", e)
    # landing points
    try:
        lp = load("landing_points.geojson")
        plon = [f["geometry"]["coordinates"][0] for f in lp["features"]]
        plat = [f["geometry"]["coordinates"][1] for f in lp["features"]]
        ax.scatter(plon, plat, s=1.6, c="#5B6B7B", alpha=0.35, linewidths=0,
                   transform=ccrs.PlateCarree(), zorder=4)
    except Exception as e:
        print("  landing pts skipped:", e)
    # portfolio sites
    rows, lat, lon, sizes, cols, edge, elw = _portfolio_sites()
    ax.scatter(lon, lat, s=sizes, c=cols, edgecolor=edge, linewidths=elw, alpha=0.92,
               transform=ccrs.PlateCarree(), zorder=6)
    handles = [Line2D([0], [0], marker="o", linestyle="", markerfacecolor=ET_COLOR[k],
               markeredgecolor="white", markersize=7, label=ET_LABEL[k])
               for k in ["hydro", "solar+wind", "solar", "wind", "mixed-renewable", "geothermal"]]
    handles += [Line2D([0], [0], color="#8B7EC8", lw=1.0, label="Submarine fibre"),
                Line2D([0], [0], marker="^", linestyle="", markerfacecolor="#5B6B7B",
                       markeredgecolor="#5B6B7B", markersize=5, label="Cable landing point")]
    ax.legend(handles=handles, loc="upper center", fontsize=6.4, ncol=4, frameon=False,
              bbox_to_anchor=(0.5, -0.015), columnspacing=1.4, handletextpad=0.4)

    # representative real site photos (CC, Wikimedia Commons) as circular insets ---
    try:
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        from matplotlib.colors import to_rgb
        pdir = os.path.join(HERE, "site_photos")
        # key, lon, lat, ring colour (energy type), inset position (axes fraction)
        # key, label, lon, lat, ring colour (energy type), inset position (axes fraction)
        PHOTOS = [
            ("itaipu",     "Itaipu",     -54.59, -25.41, C["base"],   (0.40, 0.12)),
            ("geothermal", "Iceland",    -21.40,  64.04, C["hi"],     (0.42, 0.79)),
            ("morocco",    "Noor",       -10.50,  28.60, C["pos"],    (0.40, 0.52)),
            ("grand_inga", "Grand Inga",  13.62,  -5.52, C["base"],   (0.48, 0.22)),
            ("kazakhstan", "Kazakhstan",  52.00,  43.20, C["pos"],    (0.62, 0.90)),
            ("rogun",      "Rogun",       69.78,  38.68, C["base"],   (0.66, 0.50)),
            ("yarlung",    "Yarlung",     95.00,  29.77, C["base"],   (0.74, 0.45)),
            ("siberia",    "Yenisei",     95.00,  57.00, C["base"],   (0.86, 0.90)),
            ("gobi",       "Gobi",       105.00,  40.50, C["pos"],    (0.92, 0.70)),
            ("are_hub",    "Pilbara",    119.00, -21.00, C["pos"],    (0.92, 0.30)),
        ]
        trans = ccrs.PlateCarree()._as_mpl_transform(ax)
        for key, label, plon, plat, col, xybox in PHOTOS:
            pth = os.path.join(pdir, f"{key}.jpg")
            if not os.path.exists(pth):
                continue
            img = _circle_image(pth, label=label, ring_rgb=to_rgb(col))
            ab = AnnotationBbox(OffsetImage(img, zoom=0.145), (plon, plat),
                                xybox=xybox, xycoords=trans, boxcoords="axes fraction",
                                frameon=False, pad=0.0,
                                arrowprops=dict(arrowstyle="-", color=col, lw=0.8, alpha=0.9),
                                zorder=11)
            ax.add_artist(ab)
    except Exception as _e:
        print("  site photos skipped:", _e)

    ax.set_title("(a) 35 stranded clean-energy sites on an already fibre-connected planet",
                 fontsize=9, loc="left")

    # (b) supply vs demand magnitude -----------------------------------------
    b = fig.add_subplot(gs[1, 0])
    agg = pdr["aggregates"]; dem = pdr["demand"]
    t1 = [v/1000 for v in agg["tier1_realistic_TWh"]]
    t2 = [v/1000 for v in agg["tier2_curtailed_TWh"]]
    port = dem["portfolio_realistic_PWh"]
    series = [("Tier 1", t1, C["base"]), ("Tier 2", t2, C["pos"]), ("Portfolio", port, C["hi"])]
    for xi, (lab, rng, col) in enumerate(series):
        b.plot([xi, xi], rng, color=col, lw=11, solid_capstyle="round", alpha=0.85, zorder=3)
    for v, lab, ls in [(1, "IEA 2030 (~1 PWh)", "-"), (10, "10x", "--"), (100, "100x", ":")]:
        b.axhline(v, color="#374151", lw=0.9, ls=ls, zorder=1)
        b.text(2.5, v, lab, fontsize=6.6, color="#374151", va="bottom", ha="right")
    b.set_yscale("log"); b.set_ylim(0.04, 200); b.set_xlim(-0.6, 2.6)
    b.set_xticks(range(3)); b.set_xticklabels([s[0] for s in series], fontsize=7.6)
    b.set_ylabel("PWh yr$^{-1}$ (log)")
    b.set_title("(b) Supply ~ same order as AI demand", fontsize=8.8)
    b.spines[["top", "right"]].set_visible(False)
    b.grid(axis="y", which="both", color="#EEF1F4", lw=0.5, zorder=0)

    # (c) baton-pass follow-the-sun ------------------------------------------
    c = fig.add_subplot(gs[1, 1])
    bp = al["baton_pass_avg_day"]; H = bp["hours"]; bands = bp["bands"]
    band_cols = [C["cyan"], C["second"], C["purple"]]
    ys = np.zeros(len(H))
    for bnd, col in zip(bands, band_cols):
        v = np.array(bp["served_by_band"][bnd])
        short = bnd.split(" (")[0]
        c.fill_between(H, ys, ys+v, color=col, alpha=0.80, label=short, linewidth=0)
        ys = ys + v
    # firm hydro anchor fills the residual gap between relayed VRE and demand
    firm = np.array(al["avg_day"]["firm_served"])
    c.fill_between(H, ys, ys+firm, facecolor=C["pos"], alpha=0.42, hatch="////",
                   edgecolor=C["pos"], linewidth=0.0, label="+ Hydro anchor")
    ys = ys + firm
    c.plot(H, [al["avg_day"]["demand"][h] for h in H], color="#111", lw=1.6, ls="--", label="Demand")
    c.set_xlim(0, 23); c.set_ylim(0, 1.62); c.set_xlabel("Hour (UTC)"); c.set_ylabel("Served load (mean=1)")
    c.set_title("(c) Follow-the-sun relay + hydro anchor meets demand", fontsize=8.8)
    c.legend(fontsize=6.2, frameon=False, loc="upper right", ncol=2,
             columnspacing=1.1, handletextpad=0.4, borderaxespad=0.3)
    c.spines[["top", "right"]].set_visible(False); c.grid(color="#EEF1F4", lw=0.5)

    # shared time axis + demand & supply trajectories (used by d & e) --------
    yrs = list(range(2025, 2051))
    demtraj = cov["demand_trajectory"]["trajectories_PWh"]["iea_anchored"]
    dem_y = np.array([demtraj[str(y)] for y in yrs])
    sup_lo, sup_hi = pdr["demand"]["portfolio_realistic_PWh"]
    sup_mid = 0.5 * (sup_lo + sup_hi)
    suptraj = cov["supply_trajectory"]
    sup_fix = np.array([suptraj["trajectories_PWh"]["fixed"][str(y)] for y in yrs])
    sup_dev = np.array([suptraj["trajectories_PWh"]["developable"][str(y)] for y in yrs])  # economic-developable
    tech_pot = suptraj["technical_potential_PWh"]                                          # >100 PWh each (ARER)
    xc = suptraj["crossover_year_vs_iea_demand"]   # fixed ~2031; developable None vs IEA

    # (d) storage to run 24/7: dispersion, not battery size, firms the supply
    d = fig.add_subplot(gs[2, 0])
    sr = tm["storage_vs_ratio"]; rg = sr["ratio_grid"]
    R_REF = 1.0                                  # clean supply sized to average demand: hardest 24/7 case
    cfg_meta = [("single_solar", "Single solar site", C["hi"]),
                ("biggest_only", "Biggest resources", C["second"]),
                ("balanced", "Dispersed portfolio", C["base"]),
                ("plus_hydro", "+ hydro anchor", C["pos"])]
    store = [(lab, float(np.interp(R_REF, rg, sr["storage_h"][key])), col)
             for key, lab, col in cfg_meta]
    n = len(store)
    for j, (lab, hrs, col) in enumerate(store):
        yp = n - 1 - j                           # single solar on top
        d.barh(yp, hrs, height=0.58, color=col, edgecolor="white", zorder=3)
        d.text(hrs + 0.15, yp, f"{hrs:.1f} h" if hrs >= 1 else "<1 h",
               va="center", ha="left", fontsize=7.2, color="#374151")
    d.set_yticks([n - 1 - j for j in range(n)])
    d.set_yticklabels([s[0] for s in store], fontsize=7.8)
    d.set_xlim(0, 9); d.set_ylim(-0.55, n - 0.35)
    d.set_xlabel("Battery to run 24/7 (h of mean load)")
    d.set_title("(d) A dispersed portfolio runs 24/7 on under 1 h of battery", fontsize=8.6)
    d.spines[["top", "right"]].set_visible(False); d.grid(axis="x", color="#EEF1F4", lw=0.5, zorder=0)

    # (e) developable supply dwarfs demand -- energy is not the limit --------
    e = fig.add_subplot(gs[2, 1])
    e.set_yscale("log")
    e.fill_between(yrs, sup_fix, sup_dev, color=C["pos"], alpha=0.10, zorder=0)
    e.plot(yrs, dem_y, color="#111", lw=2.2, label="AI demand (IEA)")
    e.plot(yrs, sup_fix, color=C["neutral"], lw=1.6, ls="--", label="Supply: today's projects (frozen)")
    e.plot(yrs, sup_dev, color=C["pos"], lw=2.2, label="Supply: developable (~25 PWh)")
    e.axhline(tech_pot, color=C["purple"], lw=1.3, ls=":")
    e.text(2037.5, tech_pot * 1.22, "Technical potential: solar & wind each > 100 PWh yr$^{-1}$",
           fontsize=6.5, color=C["purple"], ha="center", va="bottom")
    xcf = xc["fixed"]                            # only crossover: frozen projects fall below demand
    if xcf:
        yv = float(np.interp(xcf, yrs, dem_y))
        e.scatter([xcf], [yv], color=C["neutral"], s=40, zorder=6, edgecolor="white", lw=0.8)
        e.annotate(f"frozen projects\nfall short ~{round(xcf)}", xy=(xcf, yv), xytext=(2035, 0.85),
                   fontsize=6.5, color=C["neutral"], ha="center",
                   arrowprops=dict(arrowstyle="->", color="#9CA3AF", lw=0.8))
    e.set_xlim(2025, 2050); e.set_ylim(0.3, 320)
    e.set_xlabel("Year"); e.set_ylabel("Energy (PWh yr$^{-1}$, log)")
    e.set_title("(e) Developable supply dwarfs demand -- energy is not the limit", fontsize=8.6)
    e.legend(fontsize=6.4, frameon=False, loc="lower right")
    e.spines[["top", "right"]].set_visible(False)
    e.grid(color="#EEF1F4", lw=0.5, which="both")

    save(fig, "Fig3_supply_map")


# ============================================================================ Fig 4  ECONOMICS
def fig4():
    lc = load("lifecycle_results.json")
    lcot = load("lcot_breakdown.json")
    h = lc["headline"]
    cats = ["Electrons\n(UHVDC)", "Aluminium\n(smelter)", "AI tokens\n(inference)"]
    cols = [C["neutral"], C["second"], C["hi"]]
    x = [0, 1, 2]
    fig = plt.figure(figsize=(10.6, 3.9))
    gs = GridSpec(1, 3, wspace=0.42, left=0.07, right=0.97, bottom=0.17, top=0.80)

    # (a) gross value density
    a = fig.add_subplot(gs[0])
    gv = h["gross_value_density_USD_per_source_kWh"]
    lows = [gv["electron"][0], gv["aluminium"][0], gv["token"][0]]
    highs = [gv["electron"][1], gv["aluminium"][1], gv["token"][1]]
    for xi, lo, hi, col in zip(x, lows, highs, cols):
        a.plot([xi, xi], [lo, hi], color=col, lw=10, solid_capstyle="round", alpha=0.85, zorder=2)
    a.annotate("", xy=(0.04, 60), xytext=(0.04, 0.07), arrowprops=dict(arrowstyle="<->", color="#444", lw=1.0))
    a.text(0.10, 1.6, "~10-1000x", fontsize=7.6, color="#444")
    a.set_yscale("log"); a.set_ylim(0.03, 400); a.set_xlim(-0.4, 2.6)
    a.set_xticks(x); a.set_xticklabels(cats, fontsize=8)
    a.set_ylabel("Gross value per source kWh ($/kWh, log)")
    a.set_title("(a) Gross export value density", fontsize=9)
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"${v:g}"))
    a.spines[["top", "right"]].set_visible(False)
    a.grid(axis="y", which="both", color="#EEF1F4", lw=0.5, zorder=0)

    # (b) net value added
    b = fig.add_subplot(gs[1])
    nv = h["net_value_added_USD_per_source_kWh"]
    nets = [nv["electron"], nv["aluminium"], nv["token"]]
    for xi, (lo, hi), col in zip(x, nets, cols):
        b.plot([xi, xi], [max(lo, 0), hi], color=col, lw=11, solid_capstyle="round", alpha=0.85, zorder=2)
        b.text(xi, hi + 0.12, f"${hi:.2f}", ha="center", fontsize=7.4, color=col)
    b.annotate(f"~{h['token_vs_electron_x']:.0f}x electron\n~{h['token_vs_aluminium_x']:.0f}x aluminium",
               xy=(2, nets[2][1]*0.5), xytext=(0.4, nets[2][1]*0.6), fontsize=7.4, color=C["hi"],
               arrowprops=dict(arrowstyle="->", color=C["hi"], lw=1.0))
    b.set_ylim(0, nets[2][1]*1.25); b.set_xlim(-0.4, 2.6)
    b.set_xticks(x); b.set_xticklabels(cats, fontsize=8)
    b.set_ylabel("Net value added per source kWh ($/kWh)")
    b.set_title("(b) Net of all life-cycle cost, the token wins", fontsize=9)
    b.spines[["top", "right"]].set_visible(False)
    b.grid(axis="y", color="#EEF1F4", lw=0.5, zorder=0)

    # (c) token TCO split + LCOT
    c = fig.add_subplot(gs[2])
    sp = lcot["key_result"]["tco_split_at_conventional"]
    parts = [("Chips / servers", sp["chips_servers"], C["base"]),
             ("Facility", sp["facility"], C["neutral"]),
             ("Energy", sp["energy"], C["hi"]),
             ("O&M / network", sp["other_om_net"], C["second"])]
    bottom = 0
    for lab, frac, col in parts:
        c.bar(0, frac*100, bottom=bottom*100, width=0.5, color=col, edgecolor="white", linewidth=0.8)
        c.text(0.32, (bottom + frac/2)*100, f"{lab} {frac*100:.0f}%", va="center", fontsize=7.4, color="#111")
        bottom += frac
    c.set_xlim(-0.5, 2.0); c.set_ylim(0, 100); c.set_xticks([])
    c.set_ylabel("Token compute TCO (%)")
    c.set_title("(c) Energy is only ~6% of token cost", fontsize=9)
    c.spines[["top", "right"]].set_visible(False)

    save(fig, "Fig4_economics")


# ============================================================================ Fig 5  CONSTRAINT
def fig5():
    to = load("sensitivity_tornado.json")
    pd = load("phase_diagram.json")
    cs = load("chip_scenarios.json")
    fig = plt.figure(figsize=(11.0, 3.9))
    gs = GridSpec(1, 3, width_ratios=[1.0, 1.05, 1.05], wspace=0.40,
                  left=0.10, right=0.97, bottom=0.16, top=0.82)

    # (a) tornado
    a = fig.add_subplot(gs[0])
    pretty = {"allocation_share_s": "Allocation share", "prod_growth_CoWoS": "CoWoS / packaging growth",
              "accel_power_kW": "Accelerator power", "accelerator_output_2025": "Accelerator output",
              "portfolio_size_GW": "Portfolio size", "energy_available_PWh": "Energy / watts"}
    levers = sorted(to["tornado"]["levers"], key=lambda L: L["years_swing"])
    names = [pretty.get(L["lever"], L["lever"]) for L in levers]
    sw = [L["years_swing"] for L in levers]
    barcols = [C["hi"] if L["lever"] == "energy_available_PWh" else C["base"] for L in levers]
    a.barh(names, sw, color=barcols, edgecolor="white", height=0.66)
    for i, (L, s) in enumerate(zip(levers, sw)):
        a.text(s + 0.08, i, f"{s:.1f}", va="center", fontsize=7)
    a.text(0.05, 0.02, "energy swing = 0\n(watts don't bind)", transform=a.transAxes,
           fontsize=7, color=C["hi"])
    a.set_xlabel("Swing in years-to-fill 60 GW")
    a.set_title("(a) What paces the build-out", fontsize=8.8)
    a.spines[["top", "right"]].set_visible(False)

    # (b) phase diagram
    b = fig.add_subplot(gs[1])
    X = np.array(pd["axes"]["x_chip_output_multiple"])
    Y = np.array(pd["axes"]["y_energy_PWh"])
    Z = np.array(pd["grid_value_GW"])
    pm = b.pcolormesh(X, Y, Z, cmap="viridis", shading="auto")
    cont = b.contour(X, Y, Z, levels=[60, 120, 200, 300], colors="white", linewidths=0.8)
    b.clabel(cont, fmt="%d GW", fontsize=6, inline=True)
    b.axhspan(1.16, 2.25, color="white", alpha=0.10)
    b.text(0.30, 1.7, "energy in hand\n1.16-2.25 PWh", fontsize=6.6, color="white")
    b.set_xlabel("Chip availability (x 2025 output)")
    b.set_ylabel("Energy availability (PWh yr$^{-1}$)")
    b.set_title("(b) Iso-GW contours are vertical: chips bind", fontsize=8.8)
    cb = fig.colorbar(pm, ax=b, shrink=0.82, pad=0.02); cb.set_label("GW by 2035", fontsize=7.5)

    # (c) scenarios to 2050
    c = fig.add_subplot(gs[2])
    scol = {"Accelerated": C["pos"], "Baseline": C["base"], "Export-restricted": C["second"], "Constrained": C["hi"]}
    for name, col in scol.items():
        tr = cs["scenarios"][name]["trajectory"]
        yrs = [t["year"] for t in tr]; cum = [t["cumulative_GW"] for t in tr]
        c.plot(yrs, cum, color=col, lw=1.8, label=name)
        ya = cs["scenarios"][name]["portfolio_fully_activated_year"]
        c.scatter([ya], [cs["portfolio_continuous_equiv_GW"][1]], color=col, s=20, zorder=5)
        c.text(ya, cs["portfolio_continuous_equiv_GW"][1]+8, str(ya), fontsize=6.4, color=col, ha="center")
    c.axhspan(cs["portfolio_continuous_equiv_GW"][0], cs["portfolio_continuous_equiv_GW"][1],
              color=C["neutral"], alpha=0.10)
    c.text(2025.5, cs["portfolio_continuous_equiv_GW"][1]*0.62,
           "portfolio ceiling\n133-257 GW", fontsize=6.6, color="#374151")
    c.set_xlim(2025, 2051); c.set_ylim(0, 300)
    c.set_xlabel("Year"); c.set_ylabel("Cumulative compute (GW)")
    c.set_title("(c) Decades to fill; ~$6.4T capital", fontsize=8.8)
    c.legend(fontsize=6.6, frameon=False, loc="lower right")
    c.spines[["top", "right"]].set_visible(False); c.grid(color="#EEF1F4", lw=0.5)

    save(fig, "Fig5_constraint")


# ============================================================================ Box 1 table
def box1_table():
    with open(CSV, encoding="utf-8") as _fh:
        rows = list(csv.DictReader(_fh))
    t1 = [r for r in rows if r["tier"] == "1" and r["theoretical"] == "False"]
    t1.sort(key=lambda r: float(r["strandable_TWh_hi"]), reverse=True)
    top = t1[:12]
    t2 = [r for r in rows if r["tier"] == "2"]
    t2_lo = sum(float(r["strandable_TWh_lo"]) for r in t2)
    t2_hi = sum(float(r["strandable_TWh_hi"]) for r in t2)

    table = [["Project / cluster", "Country", "Type", "Strandable TWh yr-1", "LCOE $/MWh"]]
    for r in top:
        table.append([r["name"], r["country"], r["etype"],
                      f"{float(r['strandable_TWh_lo']):.0f}-{float(r['strandable_TWh_hi']):.0f}",
                      f"{r['lcoe_lo']}-{r['lcoe_hi']}"])
    table.append([f"Tier 2 - {len(t2)} curtailed fleets (today's spilled energy)", "global",
                  "wind/solar", f"{t2_lo:.0f}-{t2_hi:.0f}", "~0 marginal"])

    fig, ax = plt.subplots(figsize=(10.4, 5.0)); ax.axis("off")
    tbl = ax.table(cellText=table, cellLoc="left", loc="center",
                   colWidths=[0.40, 0.13, 0.13, 0.20, 0.14])
    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1, 1.5)
    ncol = len(table[0])
    for j in range(ncol):
        cc = tbl[0, j]; cc.set_facecolor(C["base"]); cc.set_text_props(color="white", weight="bold")
    yarlung_row = next((i for i, r in enumerate(table) if "Yarlung" in r[0]), None)
    for i in range(1, len(table)):
        for j in range(ncol):
            cell = tbl[i, j]
            if i == len(table)-1:
                cell.set_facecolor("#ECFDF5")
            elif yarlung_row and i == yarlung_row:
                cell.set_facecolor("#FEF2F2")
            elif i % 2 == 0:
                cell.set_facecolor("#F8FAFC")
    save(fig, "Box1_portfolio_table")


# ============================================================================ Fig S1  follow-the-sun map
def figS1_followsun():
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    prof = load("temporal_profiles.json")
    ad = prof["avg_day_utc"]
    # representative VRE sites (from temporal analysis) with coords
    SITE_LL = {"West Texas": (-102.4, 31.8), "Atacama (Chile)": (-69.0, -23.6),
               "Noor (Morocco)": (-6.86, 31.0), "Hyphen (Namibia)": (15.16, -26.65),
               "Gobi/Qinghai (China)": (100.6, 37.0), "Pilbara (Australia)": (119.0, -21.0),
               "South Australia": (138.0, -33.5)}
    snaps = [0, 4, 8, 12, 16, 20]
    fig = plt.figure(figsize=(10.4, 5.0))
    for i, hh in enumerate(snaps):
        ax = fig.add_subplot(2, 3, i+1, projection=ccrs.Robinson(central_longitude=150))
        ax.set_global()
        ax.add_feature(cfeature.LAND, facecolor="#F4F4F2")
        ax.add_feature(cfeature.OCEAN, facecolor="#EAF2F8")
        ax.add_feature(cfeature.COASTLINE, linewidth=0.25, edgecolor="#AEB6BF")
        lons = [SITE_LL[n][0] for n in SITE_LL]
        lats = [SITE_LL[n][1] for n in SITE_LL]
        share = np.array([ad["sites"][n][hh] for n in SITE_LL])
        sc = ax.scatter(lons, lats, c=share, s=80, cmap="YlOrRd", vmin=0, vmax=2.0,
                        edgecolor="#333", linewidth=0.5, transform=ccrs.PlateCarree(), zorder=5)
        ax.set_title(f"{hh:02d}:00 UTC", fontsize=8)
    cax = fig.add_axes([0.25, 0.06, 0.5, 0.022])
    fig.colorbar(sc, cax=cax, orientation="horizontal").set_label(
        "Instantaneous clean output (normalised, mean=1)", fontsize=8)
    fig.savefig(os.path.join(HERE, "FigS1_followsun.png"), bbox_inches="tight", dpi=300)
    fig.savefig(os.path.join(HERE, "FigS1_followsun.pdf"), bbox_inches="tight")
    plt.close(fig); print("saved FigS1_followsun")


def figS2_diurnal():
    """Methods figure for the diurnal kernel a(h): (a) real per-project profiles,
    (b) empirical kernel + Fourier fit, (c) longitudinal superposition -> global
    envelope, (d) validation against real AI-inference tokens (BurstGPT)."""
    k = load("diurnal_kernel.json")
    tm = load("temporal_matching_results.json")
    prof = load("temporal_profiles.json")
    v = load("diurnal_ai_validation.json")
    coef = k["fourier_coef"]
    H = np.arange(24)

    def kf(h):  # evaluate the fitted Fourier kernel at (continuous) local hour h
        h = np.asarray(h, float); out = np.full(h.shape, coef[0], float)
        for j in range(1, (len(coef) - 1) // 2 + 1):
            out = out + coef[2*j-1]*np.cos(2*np.pi*j*h/24) + coef[2*j]*np.sin(2*np.pi*j*h/24)
        return np.clip(out, 0, None)

    fig = plt.figure(figsize=(11.0, 7.8))
    gs = GridSpec(2, 2, hspace=0.36, wspace=0.23, left=0.065, right=0.975, bottom=0.07, top=0.90)

    # (a) real per-project local-hour profiles
    a = fig.add_subplot(gs[0, 0])
    pp = k["per_project_profiles_24"]; ptz = k["project_tz"]; basis = set(k["kernel_basis"])
    cols = {"ja.wikipedia": C["base"], "de.wikipedia": C["pos"], "hi.wikipedia": C["second"],
            "pt.wikipedia": C["purple"], "en.wikipedia": C["neutral"]}
    for p in ["ja.wikipedia", "de.wikipedia", "hi.wikipedia", "pt.wikipedia", "en.wikipedia"]:
        if p not in pp:
            continue
        lw = 2.6 if p in basis else 1.2; ls = "-" if p in basis else "--"
        a.plot(H, np.array(pp[p]), color=cols[p], lw=lw, ls=ls,
               label="%s (tz%+g%s)" % (p.split('.')[0], ptz[p], ", basis" if p in basis else ""))
    a.set_title("(a) Real per-project diurnal profiles (Wikimedia pageviews, CC0)", fontsize=8.6, loc="left")
    a.set_xlabel("Local hour"); a.set_ylabel("Pageviews (mean=1)"); a.set_xlim(0, 23)
    a.legend(fontsize=6.4, frameon=False, ncol=2, loc="upper left")
    a.grid(color="#EEF1F4", lw=0.5); a.spines[["top", "right"]].set_visible(False)

    # (b) empirical kernel + Fourier fit
    b = fig.add_subplot(gs[0, 1])
    b.plot(H, np.array(k["empirical_kernel_24"]), "o", color=C["neutral"], ms=4.5, label="empirical = mean(ja, de)")
    b.plot(H, np.array(k["fitted_kernel_24"]), color=C["hi"], lw=2.6, label="Fourier fit (K=3), R²=%.2f" % k["fit_r2"])
    b.set_title("(b) Kernel a(h): empirical + analytic fit", fontsize=8.6, loc="left")
    b.set_xlabel("Local hour"); b.set_ylabel("Activity (mean=1)"); b.set_xlim(0, 23)
    b.annotate("peak %02dh · trough/peak %.2f · P2M %.2f"
               % (int(k["peak_local_hour"]), k["trough_over_peak"], k["diurnal_p2m"]),
               xy=(0.03, 0.04), xycoords="axes fraction", va="bottom", fontsize=7, color="#374151")
    b.legend(fontsize=6.8, frameon=False, loc="upper left")
    b.grid(color="#EEF1F4", lw=0.5); b.spines[["top", "right"]].set_visible(False)

    # (c) superposition -> global envelope
    c = fig.add_subplot(gs[1, 0])
    for r in tm["demand_regions"]:
        c.plot(H, r["token_share"] * kf((H + r["tz"]) % 24), lw=1.0, alpha=0.85,
               label="%s w=%.2f" % (r["name"].split()[0], r["token_share"]))
    dem = np.array([prof["avg_day_utc"]["demand"][h] for h in range(24)])
    c.plot(H, dem, color="#111", lw=2.8, label="global D(t)")
    c.set_title("(c) Σ wᵣ·a((t+tzᵣ) mod 24) → global envelope, P2M %.2f"
                % tm["global_demand_envelope"]["diurnal_p2m"], fontsize=8.6, loc="left")
    c.set_xlabel("Hour (UTC)"); c.set_ylabel("Demand (mean=1)"); c.set_xlim(0, 23)
    c.legend(fontsize=5.9, frameon=False, ncol=2, loc="upper right")
    c.grid(color="#EEF1F4", lw=0.5); c.spines[["top", "right"]].set_visible(False)

    # (d) validation vs real AI tokens (centred on each curve's own peak)
    d = fig.add_subplot(gs[1, 1])
    ak = np.array(k["fitted_kernel_24"], float); ak = ak / ak.mean()
    cen = lambda cc: np.roll(np.asarray(cc, float), (12 - int(np.argmax(cc))) % 24)
    x = np.arange(-12, 12)
    d.axhline(1.0, color="#CBD5E1", lw=0.8, ls=":")
    d.plot(x, cen(ak), color=C["base"], lw=2.6, label="kernel a(h)  P2M %.2f" % k["diurnal_p2m"])
    d.plot(x, cen(v["burstgpt_token_weighted"]["curve_24"]), color=C["hi"], lw=1.8, ls="--",
           label="BurstGPT all  P2M %.2f" % v["burstgpt_token_weighted"]["diurnal_p2m"])
    d.plot(x, cen(v["burstgpt_token_weighted_conversation_only"]["curve_24"]), color=C["second"], lw=1.5, ls="-.",
           label="BurstGPT conv.  P2M %.2f" % v["burstgpt_token_weighted_conversation_only"]["diurnal_p2m"])
    d.set_title("(d) Validation: real AI tokens (BurstGPT, %.1fM req, %.0f d; r=%.2f)"
                % (v["rows"] / 1e6, v["span_days"], v["shape_match_token_vs_kernel"]["max_pearson"]),
                fontsize=8.6, loc="left")
    d.set_xlabel("Hours from local peak"); d.set_ylabel("Token rate (mean=1)")
    d.set_xlim(-12, 11); d.set_ylim(0, None)
    d.legend(fontsize=6.6, frameon=False, loc="upper left")
    d.grid(color="#EEF1F4", lw=0.5); d.spines[["top", "right"]].set_visible(False)

    save(fig, "FigS2_diurnal_validation")


if __name__ == "__main__":
    fig1(); fig2(); fig4(); fig5(); box1_table()
    for fn in (fig3, figS1_followsun):
        try:
            fn()
        except Exception as e:
            import traceback; print(f"{fn.__name__} skipped:", repr(e)); traceback.print_exc()
