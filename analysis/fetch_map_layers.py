"""
Fetch lightweight map-overlay layers for Fig. 3 (the supply & matching world map).
Idempotent: skips a layer if its cache already exists. Caches to data/.

Layers (all light, free):
  - Submarine fibre cables   -> data/cables.geojson           (TeleGeography, CC BY-NC-SA -> attribute)
  - Cable landing points     -> data/landing_points.geojson   (TeleGeography)
  - PeeringDB facilities     -> data/peeringdb_fac.json       (lat/lon of data-centre facilities)

Run:  python analysis/fetch_map_layers.py
Heavy/uncertain layers (CF raster, GRIP roads, seismic) are deliberately NOT fetched here;
Fig. 3 v1 ships with cables + sites only (see DESIGN_v3 §map / build order).
"""
import json, os, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "academic-figure-fetch/1.0 (Perspective on stranded-energy AI compute)"}

SOURCES = {
    "cables.geojson": "https://www.submarinecablemap.com/api/v3/cable/cable-geo.json",
    "landing_points.geojson": "https://www.submarinecablemap.com/api/v3/landing-point/landing-point-geo.json",
    "peeringdb_fac.json": "https://www.peeringdb.com/api/fac?limit=6000",
}


def fetch(name, url):
    out = os.path.join(DATA, name)
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print(f"  cached  {name} ({os.path.getsize(out)//1024} KB)")
        return True
    for attempt in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            r.raise_for_status()
            data = r.json()
            with open(out, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"  fetched {name} ({os.path.getsize(out)//1024} KB)")
            time.sleep(1.0)
            return True
        except Exception as e:
            print(f"  retry {name} ({attempt}): {e}")
            time.sleep(2.0)
    print(f"  FAILED  {name} -- Fig.3 will fall back to sites-only")
    return False


def main():
    os.makedirs(DATA, exist_ok=True)
    ok = {}
    for name, url in SOURCES.items():
        ok[name] = fetch(name, url)
    print("done:", {k: ("ok" if v else "fail") for k, v in ok.items()})


if __name__ == "__main__":
    main()
