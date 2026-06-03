"""
Fetch a real diurnal human-activity kernel from Wikimedia pageviews (CC0)
=========================================================================
Replaces the hand-set Gaussian a(h) (peak 16:00 local, floor 0.45) used in
the global token-demand envelope with an EMPIRICAL local-hour activity shape
fitted to real, open, hourly Wikipedia pageview counts.

Why Wikimedia: the only open (CC0), no-auth, hourly, per-project web-activity
series available. Single-language projects whose readership clusters in one
timezone give a clean local-hour signal. We use the two purest single-timezone
projects, ja (JST=UTC+9) and de (CET=UTC+1, no DST in February), as the kernel
basis, and fetch hi/pt/en for cross-checking only.

Method: per project, bin hourly views by LOCAL hour (UTC + project tz), average
over the window, normalise to mean=1; average the kernel-basis projects; fit a
truncated Fourier series (K=3 harmonics) -> smooth analytic a(h). The fit, the
empirical kernel, and the per-project profiles are written to
data/diurnal_kernel.json for reproducibility and for Fig 2c.

CAVEAT: pageviews are a HUMAN WEB-ACTIVITY proxy, not measured AI-inference
demand; and language!=country (clean only for single-timezone projects). It is
strictly better grounded than the hand-set Gaussian, but remains a proxy.

Run: python analysis/fetch_diurnal_wikimedia.py   (needs internet; CC0 data)
"""
import json, os, time
import numpy as np
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
UA = "AI-perspective-research/1.0 (academic diurnal-shape study; contact 2674793917zhang@gmail.com)"
BASE = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/"
        "{proj}/all-access/user/hourly/{s}/{e}")

# February 2026: no European DST (de=CET=+1, matching the model's Europe tz),
# Japan/India/Brazil never observe DST. 4 full weeks, averaged over all days.
WEEKS = [("2026020100", "2026020723"), ("2026020800", "2026021423"),
         ("2026021500", "2026022123"), ("2026022200", "2026022823")]
# representative dominant timezone (offset hrs) of each project's readership
PROJ_TZ = {"ja.wikipedia": 9.0, "de.wikipedia": 1.0, "hi.wikipedia": 5.5,
           "pt.wikipedia": -3.0, "en.wikipedia": -5.0}
KERNEL_BASIS = ["ja.wikipedia", "de.wikipedia"]   # purest single-timezone signals
K_HARMONICS = 3


def fetch_project(proj):
    utc_hour, views = [], []
    for s, e in WEEKS:
        url = BASE.format(proj=proj, s=s, e=e)
        for attempt in range(4):
            try:
                r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
                r.raise_for_status()
                items = r.json()["items"]
                for it in items:
                    utc_hour.append(int(it["timestamp"][8:10]))
                    views.append(float(it["views"]))
                time.sleep(0.3)
                break
            except Exception as ex:
                print(f"  retry {proj} {s} ({attempt}): {ex}")
                time.sleep(2.0)
        else:
            raise RuntimeError(f"failed to fetch {proj} {s}")
    return np.array(utc_hour, int), np.array(views, float)


def local_hour_profile(proj):
    """24-value mean=1 profile of views vs LOCAL hour (integer-binned)."""
    tz = PROJ_TZ[proj]
    utc_hour, views = fetch_project(proj)
    local = (utc_hour + tz) % 24
    lh = np.floor(local).astype(int) % 24          # half-hour tz -> floor bin
    prof = np.array([views[lh == h].mean() if np.any(lh == h) else np.nan
                     for h in range(24)])
    prof = prof / prof.mean()                       # normalise to mean 1
    n = int(len(views))
    print(f"  {proj:16s} tz{tz:+.1f}  n={n}  peak@{int(np.argmax(prof)):02d}h "
          f"trough@{int(np.argmin(prof)):02d}h  trough/peak={prof.min()/prof.max():.2f}")
    return prof


def fourier_fit(y, K=3):
    """Least-squares truncated Fourier series on 24 hourly points. Returns
    coefficients [c0, a1,b1, a2,b2, ...] and the fitted 24-value curve."""
    h = np.arange(24)
    cols = [np.ones(24)]
    for k in range(1, K + 1):
        cols.append(np.cos(2 * np.pi * k * h / 24.0))
        cols.append(np.sin(2 * np.pi * k * h / 24.0))
    M = np.column_stack(cols)
    coef, *_ = np.linalg.lstsq(M, y, rcond=None)
    fit = M @ coef
    ss_res = float(np.sum((y - fit) ** 2)); ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    return coef, fit, r2


def main():
    os.makedirs(DATA, exist_ok=True)
    profiles = {}
    for proj in PROJ_TZ:
        try:
            profiles[proj] = local_hour_profile(proj).tolist()
        except Exception as ex:
            print(f"  SKIP {proj}: {ex}")

    basis = np.array([profiles[p] for p in KERNEL_BASIS if p in profiles])
    kernel = basis.mean(axis=0)                 # mean of single-TZ profiles
    kernel = kernel / kernel.mean()             # mean 1
    coef, fit, r2 = fourier_fit(kernel, K_HARMONICS)
    fit = fit / fit.mean()                       # keep mean 1

    peak_h = float(np.argmax(fit)); trough_h = float(np.argmin(fit))
    out = {
        "source": "Wikimedia pageviews REST API (aggregate, all-access, agent=user), CC0",
        "window_utc": [WEEKS[0][0], WEEKS[-1][1]],
        "kernel_basis": KERNEL_BASIS,
        "project_tz": PROJ_TZ,
        "K_harmonics": K_HARMONICS,
        "fourier_coef": coef.tolist(),     # [c0, a1,b1, a2,b2, a3,b3]
        "fit_r2": r2,
        "empirical_kernel_24": kernel.tolist(),
        "fitted_kernel_24": fit.tolist(),
        "per_project_profiles_24": profiles,
        "peak_local_hour": peak_h, "trough_local_hour": trough_h,
        "trough_over_peak": float(fit.min() / fit.max()),
        "diurnal_p2m": float(fit.max() / fit.mean()),
        "notes": ("Empirical local-hour human web-activity kernel (Wikimedia "
                  "pageviews) replacing the hand-set Gaussian. Human-activity "
                  "proxy, not measured AI inference. ja(+9)/de(+1) single-tz basis."),
    }
    with open(os.path.join(DATA, "diurnal_kernel.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("\n--- fitted diurnal kernel (Fourier K=%d) ---" % K_HARMONICS)
    print("R^2 = %.4f" % r2)
    print("Fourier coef [c0,a1,b1,a2,b2,a3,b3] =", [round(c, 4) for c in coef])
    print("peak @ %02d:00 local | trough @ %02d:00 local | trough/peak = %.2f | diurnal P2M = %.2f"
          % (int(peak_h), int(trough_h), out["trough_over_peak"], out["diurnal_p2m"]))
    print("(old hand-set Gaussian: peak 16:00, trough/peak 0.47, diurnal P2M ~2.1)")
    print("written:", os.path.join(DATA, "diurnal_kernel.json"))


if __name__ == "__main__":
    main()
