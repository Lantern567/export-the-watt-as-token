"""
Validate the diurnal kernel a(h) against a REAL AI-inference token trace
========================================================================
The kernel a(h) in fetch_diurnal_wikimedia.py is fitted to human web-activity
(Wikipedia pageviews) as a PROXY for AI token demand. Here we cross-check that
real LLM inference exhibits a diurnal cycle of comparable shape/amplitude, using
BurstGPT (HPMLL/BurstGPT, CC-BY-4.0): real LLM-serving request logs with per-
request timestamps and token counts (~2 months). We build the TOKEN-WEIGHTED
hour-of-day curve (the closest analog to token demand) and compare it to the
fitted kernel.

LIMITATION: BurstGPT is a single aggregated service with NO geographic field and
an undisclosed timezone, so it validates the SHAPE/AMPLITUDE of the per-region
diurnal cycle, NOT the per-region weights or absolute timezone alignment. The
comparison is therefore phase-aligned (best circular shift) and shape-based.

Outputs: data/diurnal_ai_validation.json
Run: python analysis/validate_diurnal_ai_traces.py   (downloads ~52 MB once, cached)
"""
import json, os
import numpy as np
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(DATA, "cache_traces")
URL = "https://github.com/HPMLL/BurstGPT/releases/download/v1.1/BurstGPT_1.csv"
FN = os.path.join(CACHE, "BurstGPT_1.csv")


def download():
    os.makedirs(CACHE, exist_ok=True)
    if os.path.exists(FN) and os.path.getsize(FN) > 1_000_000:
        print("cached:", FN, round(os.path.getsize(FN) / 1e6, 1), "MB")
        return
    print("downloading BurstGPT_1.csv ...")
    with requests.get(URL, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(FN, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    print("saved:", round(os.path.getsize(FN) / 1e6, 1), "MB")


def build():
    tok = np.zeros(24); req = np.zeros(24)               # all rows
    tok_c = np.zeros(24); req_c = np.zeros(24)           # conversation-log rows
    maxts = 0; logtypes = {}; n = 0
    with open(FN, encoding="utf-8") as f:
        header = [h.strip() for h in f.readline().rstrip("\n").split(",")]
        ti = header.index("Timestamp")
        tti = header.index("Total tokens")
        li = header.index("Log Type") if "Log Type" in header else None
        for line in f:
            p = line.rstrip("\n").split(",")
            if len(p) <= max(ti, tti):
                continue
            try:
                ts = int(float(p[ti])); tt = float(p[tti])
            except ValueError:
                continue
            h = (ts // 3600) % 24
            tok[h] += tt; req[h] += 1; n += 1
            if ts > maxts:
                maxts = ts
            lt = p[li].strip() if (li is not None and len(p) > li) else "?"
            logtypes[lt] = logtypes.get(lt, 0) + 1
            if lt.lower().startswith("conversation"):
                tok_c[h] += tt; req_c[h] += 1
    return tok, req, tok_c, req_c, maxts / 86400.0, logtypes, n


def stats(curve):
    c = np.asarray(curve, float)
    c = c / c.mean()
    return {"curve_24": c.tolist(), "peak_hour": int(np.argmax(c)),
            "trough_hour": int(np.argmin(c)),
            "trough_over_peak": float(c.min() / c.max()),
            "diurnal_p2m": float(c.max() / c.mean())}


def best_align(a, b):
    """max circular cross-correlation (Pearson) of a vs shifted b; returns (corr, shift)."""
    a = (np.asarray(a) - np.mean(a)); b = np.asarray(b)
    best = (-2.0, 0)
    for s in range(24):
        bs = np.roll(b, s) - np.mean(b)
        denom = np.sqrt(np.sum(a * a) * np.sum(bs * bs))
        c = float(np.sum(a * bs) / denom) if denom > 0 else 0.0
        if c > best[0]:
            best = (c, s)
    return best


def main():
    download()
    tok, req, tok_c, req_c, days, logtypes, n = build()
    print(f"rows={n}  span={days:.1f} days  log types={logtypes}")

    kernel = json.load(open(os.path.join(DATA, "diurnal_kernel.json"), encoding="utf-8"))
    ak = np.array(kernel["fitted_kernel_24"], float); ak = ak / ak.mean()

    s_tok = stats(tok); s_req = stats(req)
    s_tok_c = stats(tok_c) if tok_c.sum() > 0 else None
    s_kernel = stats(ak)

    corr_tok, shift_tok = best_align(ak, np.array(s_tok["curve_24"]))
    corr_req, shift_req = best_align(ak, np.array(s_req["curve_24"]))

    out = {
        "source": "BurstGPT_1.csv (HPMLL/BurstGPT, CC-BY-4.0), real LLM-serving log; token-weighted hour-of-day",
        "url": URL, "rows": n, "span_days": days, "log_types": logtypes,
        "kernel_fit": {"peak_hour": s_kernel["peak_hour"], "trough_over_peak": s_kernel["trough_over_peak"],
                       "diurnal_p2m": s_kernel["diurnal_p2m"], "curve_24": ak.tolist()},
        "burstgpt_token_weighted": s_tok,
        "burstgpt_request_count": s_req,
        "burstgpt_token_weighted_conversation_only": s_tok_c,
        "shape_match_token_vs_kernel": {"max_pearson": corr_tok, "phase_shift_hours": shift_tok},
        "shape_match_request_vs_kernel": {"max_pearson": corr_req, "phase_shift_hours": shift_req},
        "notes": ("Real AI-inference token demand (BurstGPT) shows a diurnal cycle. We compare SHAPE/"
                  "AMPLITUDE to the Wikimedia-fitted kernel via best circular alignment (BurstGPT has no "
                  "geo / undisclosed timezone, so absolute phase is not comparable). High Pearson after "
                  "alignment + similar trough/peak and P2M => the human-activity proxy is a reasonable "
                  "stand-in for the AI-token diurnal shape."),
    }
    with open(os.path.join(DATA, "diurnal_ai_validation.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("\n--- diurnal shape comparison (normalised, mean=1) ---")
    print("kernel (Wikimedia fit) : peak %02dh  trough/peak %.2f  P2M %.2f"
          % (s_kernel["peak_hour"], s_kernel["trough_over_peak"], s_kernel["diurnal_p2m"]))
    print("BurstGPT token-weighted: peak %02dh  trough/peak %.2f  P2M %.2f"
          % (s_tok["peak_hour"], s_tok["trough_over_peak"], s_tok["diurnal_p2m"]))
    print("BurstGPT request-count : peak %02dh  trough/peak %.2f  P2M %.2f"
          % (s_req["peak_hour"], s_req["trough_over_peak"], s_req["diurnal_p2m"]))
    if s_tok_c:
        print("BurstGPT token (conv.) : peak %02dh  trough/peak %.2f  P2M %.2f"
              % (s_tok_c["peak_hour"], s_tok_c["trough_over_peak"], s_tok_c["diurnal_p2m"]))
    print("shape match (token vs kernel) : Pearson %.3f at phase shift %dh" % (corr_tok, shift_tok))
    print("shape match (req   vs kernel) : Pearson %.3f at phase shift %dh" % (corr_req, shift_req))
    print("written:", os.path.join(DATA, "diurnal_ai_validation.json"))


if __name__ == "__main__":
    main()
