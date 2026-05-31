# -*- coding: utf-8 -*-
"""
Publication figures for the Perspective "Export the watt as a token".
Fig 2: value-density ladder (log).  Fig 3: tokens-per-year sensitivity to energy/token (log-log).
Fig 4: AI compute cost structure + capex comparison.  Fig 5: global stranded-clean-energy site map.
English-only labels. Outputs PNG (300 dpi) + PDF into the same folder.
"""
import os, re, csv, warnings
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, FuncFormatter

warnings.simplefilter("always")  # surface all warnings on stderr for inspection
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "data", "sites_master.csv")

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
    "axes.labelsize": 9, "axes.linewidth": 0.8, "savefig.dpi": 300,
    "figure.dpi": 120, "axes.unicode_minus": False,
})
C = {"base": "#2563EB", "second": "#F59E0B", "hi": "#DC2626",
     "neutral": "#64748B", "pos": "#059669", "purple": "#7C3AED"}

def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)

# ----------------------------------------------------------------------------- Fig 1
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

    box(0.015, 0.40, 0.185, 0.22,
        "Stranded\nclean-energy site\n~60 GW · ~300 TWh yr$^{-1}$\n(Yarlung Tsangpo)",
        "#EAF2F8", C["base"], fs=8.4, weight="bold")

    rows = [
        (0.80, 0.60, C["neutral"], "Electrons — UHVDC",
         "±800–1100 kV line\n2,000–3,000 km\n−6–10% loss",
         "Commodity electricity\n~$0.05–0.08 / source kWh\nreach: regional"),
        (0.50, 0.51, C["second"], "Aluminium — smelter",
         "Hall–Héroult\n14 kWh kg$^{-1}$\nship metal",
         "Aluminium (\"canned electricity\")\n~$0.14–0.20 / source kWh\nreach: global, shipped"),
        (0.20, 0.42, C["hi"], "AI tokens — inference",
         "Data centre →\noptical fibre\n~0 loss · ms latency",
         "AI tokens\n~$0.7–123 / source kWh\nreach: global, instant"),
    ]
    for yc, ys, col, tag, mid, dest in rows:
        ax.annotate("", xy=(0.335, yc), xytext=(0.205, ys),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2), zorder=1)
        ax.text(0.45, yc + 0.105, tag, ha="center", fontsize=8.6, color=col, weight="bold")
        box(0.335, yc - 0.085, 0.225, 0.17, mid, "white", col, fs=7.9)
        ax.annotate("", xy=(0.645, yc), xytext=(0.562, yc),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2), zorder=1)
        box(0.645, yc - 0.095, 0.31, 0.19, dest, "white", col, fs=8.2)

    ax.annotate("", xy=(1.04, 0.83), xytext=(1.04, 0.16),
                arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.6))
    ax.text(1.075, 0.5, "value density  ~10–1000×", rotation=90,
            va="center", ha="center", fontsize=8.6, color="#444")
    ax.set_title("Fig. 1 | Three export pathways from one stranded-energy site",
                 fontsize=11, loc="left", pad=10)
    save(fig, "Fig1_three_pathways")

# ----------------------------------------------------------------------------- Fig 2
def fig2():
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    cats = ["Electrons\n(UHVDC)", "Aluminum\n(canned electricity)", "AI tokens\n(inference)"]
    x = [0, 1, 2]
    lows = [0.05, 0.14, 0.66]
    highs = [0.08, 0.20, 123.0]
    cols = [C["neutral"], C["second"], C["hi"]]
    for xi, lo, hi, col in zip(x, lows, highs, cols):
        ax.plot([xi, xi], [lo, hi], color=col, lw=9, solid_capstyle="round", alpha=0.85, zorder=2)
    # token sub-points
    ax.scatter([2, 2, 2], [0.66, 25, 123], color=C["hi"], s=34, zorder=3, edgecolor="white", linewidth=0.6)
    for y, lab in [(0.66, "budget $0.4/Mtok"), (25, "mid $15/Mtok"), (123, "frontier $75/Mtok")]:
        ax.annotate(lab, (2, y), xytext=(2.16, y), va="center", fontsize=7.5, color="#333")
    ax.scatter([0, 0], [0.05, 0.08], color=C["neutral"], s=22, zorder=3)
    ax.scatter([1, 1], [0.14, 0.20], color=C["second"], s=22, zorder=3)
    ax.annotate("", xy=(0.04, 60), xytext=(0.04, 0.07),
                arrowprops=dict(arrowstyle="<->", color="#444", lw=1.1))
    ax.text(0.10, 2.0, "~10–1000×\nvalue density", fontsize=8, color="#444")
    ax.set_yscale("log")
    ax.set_ylim(0.03, 400)
    ax.set_xlim(-0.4, 3.0)
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylabel("Gross export value per source kWh (USD/kWh, log scale)")
    ax.set_title("Fig. 2 | A token embeds energy at far higher value density than an electron or a metal")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"${v:g}"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", which="both", color="#E5E7EB", lw=0.5, zorder=0)
    save(fig, "Fig2_value_density_ladder")

# ----------------------------------------------------------------------------- Fig 3
def fig3():
    E_kwh = 300e9  # 300 TWh/yr in kWh
    eps = np.logspace(np.log10(0.5), np.log10(100), 300)  # J/token
    tok = E_kwh * 3.6e6 / eps
    G_lo, G_hi = 1.5e16, 2.0e16  # global throughput band 2025
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    ax.fill_between([0.5, 100], G_lo, G_hi, color=C["neutral"], alpha=0.18, zorder=0)
    ax.text(0.62, np.sqrt(G_lo*G_hi), "current global annual\ntoken throughput (~2025)",
            fontsize=7.5, color="#374151", va="center")
    ax.plot(eps, tok, color=C["base"], lw=2.2, zorder=2)
    pts = [(0.7, "best-case\nbatched"), (2.2, "Epoch central\n(GPT-4o)"), (4, "Joule median"),
           (40, "frontier /\nreasoning")]
    for e, lab in pts:
        t = E_kwh*3.6e6/e
        ax.scatter([e], [t], color=C["hi"], s=42, zorder=3, edgecolor="white", linewidth=0.7)
        ax.annotate(lab, (e, t), xytext=(e*1.15, t*1.7), fontsize=7.3, color="#333")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.5, 100); ax.set_ylim(5e15, 3e18)
    ax.set_xlabel("Datacenter energy per output token,  ε  (J/token, log scale)")
    ax.set_ylabel("Site annual token output (tokens yr$^{-1}$, log scale)")
    ax.set_title("Fig. 3 | One ~300 TWh/yr site spans ~0.5× to ~30× global token demand;\nε dominates the magnitude")
    # right axis: multiples of global throughput (midpoint)
    Gmid = np.sqrt(G_lo*G_hi)
    ax2 = ax.twinx()
    ax2.set_yscale("log"); ax2.set_ylim(5e15/Gmid, 3e18/Gmid)
    ax2.set_ylabel("× current global throughput")
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:g}×"))
    for a in (ax, ax2): a.spines[["top"]].set_visible(False)
    ax.grid(which="both", color="#EEF1F4", lw=0.5, zorder=0)
    save(fig, "Fig3_epsilon_sensitivity")

# ----------------------------------------------------------------------------- Fig 4
def fig4():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 4.2), gridspec_kw={"width_ratios": [1, 1.1]})
    fig.subplots_adjust(top=0.80, wspace=0.55, bottom=0.13, left=0.09, right=0.97)
    # (a) TCO stacked bar with labels to the RIGHT (leader lines), so no clipping
    parts = [("Servers / chips", 60, C["base"]), ("Facility / infrastructure", 29, C["neutral"]),
             ("Electricity", 7, C["hi"]), ("Other", 4, C["second"])]
    bottom = 0
    mids = []
    for lab, val, col in parts:
        a1.bar(0, val, bottom=bottom, width=0.45, color=col, edgecolor="white", linewidth=0.8)
        mids.append(bottom + val/2); bottom += val
    label_y = [30.0, 74.5, 90.0, 99.5]  # staggered to avoid overlap of the two thin top slices
    for (lab, val, col), m, ly in zip(parts, mids, label_y):
        a1.annotate(f"{lab}  ·  {val}%", xy=(0.23, m), xytext=(0.36, ly), va="center",
                    ha="left", fontsize=8, color="#111",
                    arrowprops=dict(arrowstyle="-", color=col, lw=1.0))
    a1.set_xlim(-0.5, 1.65); a1.set_ylim(0, 100); a1.set_xticks([])
    a1.set_ylabel("Share of AI compute total cost of ownership (%)")
    a1.set_title("(a) Electricity is only ~4–7% of cost", fontsize=9)
    a1.spines[["top", "right"]].set_visible(False)
    # (b) capex comparison
    labels = ["The dam\n(~60 GW hydro)", "Compute to fill\n60 GW (~40M GPUs)"]
    vals = [167, 2300]
    bars = a2.bar(labels, vals, width=0.55, color=[C["pos"], C["hi"]], edgecolor="white")
    for b, v in zip(bars, vals):
        a2.text(b.get_x()+b.get_width()/2, v+45, f"${v:,}B", ha="center", fontsize=8.5)
    a2.set_ylabel("Up-front capital (USD billions)")
    a2.set_ylim(0, 2700)
    a2.set_title("(b) Hardware capex ≈ 14× the dam", fontsize=9)
    a2.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Fig. 4 | Token export shifts the binding constraint from transmission/energy to chips and capital",
                 fontsize=10, y=0.96)
    save(fig, "Fig4_cost_structure")

# ----------------------------------------------------------------------------- Fig 5
def parse_twh(s):
    """extract a representative TWh/yr number from messy text; midpoint of first range."""
    if not s: return np.nan
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", s)
    if m: return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else np.nan

def fig5():
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    with open(CSV, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    et_color = {"hydro": C["base"], "solar": C["second"], "wind": "#0EA5E9",
                "solar+wind": C["pos"], "mixed-renewable": C["purple"], "geothermal": C["hi"],
                "flared-gas": C["neutral"]}
    et_label = {"hydro": "Hydro", "solar": "Solar", "wind": "Wind", "solar+wind": "Solar+Wind",
                "mixed-renewable": "Mixed renewable", "geothermal": "Geothermal", "flared-gas": "Flared gas"}
    lats = np.array([float(r["lat"]) for r in rows])
    lons = np.array([float(r["lon"]) for r in rows])
    twh = np.array([parse_twh(r["annualTWh"]) for r in rows])
    twh_f = np.where(np.isfinite(twh), twh, 5.0)
    sizes = 18 + 24 * np.sqrt(np.clip(twh_f, 1, 320))  # sqrt scaling, capped
    cols = [et_color.get(r["energyType"], C["neutral"]) for r in rows]

    fig = plt.figure(figsize=(9.2, 5.2))
    ax = fig.add_axes([0.02, 0.06, 0.66, 0.88], projection=ccrs.Robinson())
    ax.set_global()
    ax.add_feature(cfeature.LAND, facecolor="#F4F4F2")
    ax.add_feature(cfeature.OCEAN, facecolor="#EAF2F8")
    ax.add_feature(cfeature.COASTLINE, linewidth=0.4, edgecolor="#9AA3AD")
    ax.add_feature(cfeature.BORDERS, linewidth=0.25, edgecolor="#C2C8CF")
    ax.scatter(lons, lats, s=sizes, c=cols, alpha=0.82, edgecolor="white",
               linewidth=0.5, transform=ccrs.PlateCarree(), zorder=5)
    ax.set_title("Fig. 5 | A global map of stranded / curtailed clean-energy sites that could host AI compute",
                 fontsize=10, pad=8)

    # China inset
    axin = fig.add_axes([0.66, 0.30, 0.32, 0.46], projection=ccrs.PlateCarree())
    axin.set_extent([73, 124, 22, 50], crs=ccrs.PlateCarree())
    axin.add_feature(cfeature.LAND, facecolor="#F4F4F2")
    axin.add_feature(cfeature.OCEAN, facecolor="#EAF2F8")
    axin.add_feature(cfeature.COASTLINE, linewidth=0.4, edgecolor="#9AA3AD")
    axin.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="#C2C8CF")
    cn = [i for i, r in enumerate(rows) if r["country"] == "China"]
    axin.scatter(lons[cn], lats[cn], s=sizes[cn], c=[cols[i] for i in cn], alpha=0.85,
                 edgecolor="white", linewidth=0.5, transform=ccrs.PlateCarree(), zorder=5)
    # flag Yarlung
    yi = next(i for i, r in enumerate(rows) if "Yarlung" in r["name"])
    axin.annotate("Yarlung Tsangpo\n~60 GW / ~300 TWh", (lons[yi], lats[yi]),
                  xytext=(80, 24.5), fontsize=7, color="#111", ha="center",
                  arrowprops=dict(arrowstyle="->", color="#111", lw=0.8))
    axin.set_title("West China (东数西算 nodes)".replace("东数西算", "East-Data-West-Compute"),
                   fontsize=8)

    # legends
    type_handles = [Line2D([0],[0], marker="o", linestyle="", markerfacecolor=et_color[k],
                    markeredgecolor="white", markersize=8, label=et_label[k])
                    for k in ["hydro","solar","wind","solar+wind","mixed-renewable","geothermal"]]
    leg1 = ax.legend(handles=type_handles, title="Energy type", loc="lower left",
                     fontsize=7.5, title_fontsize=8, frameon=False, bbox_to_anchor=(0.0, -0.02))
    ax.add_artist(leg1)
    size_vals = [10, 50, 150, 300]
    size_handles = [Line2D([0],[0], marker="o", linestyle="", markerfacecolor="#9AA3AD",
                    markeredgecolor="white", markersize=np.sqrt(18+24*np.sqrt(v))*0.7,
                    label=f"{v} TWh/yr") for v in size_vals]
    ax.legend(handles=size_handles, title="Annual / strandable energy", loc="lower left",
              fontsize=7.5, title_fontsize=8, frameon=False, bbox_to_anchor=(0.30, -0.02),
              labelspacing=1.3, handletextpad=1.0, borderpad=0.8)
    save(fig, "Fig5_global_site_map")

if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4()
    try:
        fig5()
    except Exception as e:
        print("FIG5_ERROR:", repr(e))
