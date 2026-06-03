# -*- coding: utf-8 -*-
"""Search Wikimedia Commons for CC/PD ground photos of representative stranded-energy
sites and (optionally) download the chosen file. Records license + attribution for the
figure caption / SI. Run with `--download` to actually fetch the picked files."""
import os, re, sys, json, ssl, urllib.request, urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
ctx = ssl.create_default_context()
API = "https://commons.wikimedia.org/w/api.php"
UA = "research-fig/1.0 (academic Perspective figure; non-commercial research)"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "figures", "site_photos")


def api(params):
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=40, context=ctx))


def strip(html):
    return re.sub("<[^>]+>", "", html or "").strip()


# representative sites (key, label, search query) -- spread by longitude & energy type
SITES = [
    ("gobi",       "Gobi mega-base (solar+wind)", "Tengger Desert Solar Park"),
    ("yarlung",    "Yarlung Tsangpo (hydro)",     "Yarlung Tsangpo"),
    ("grand_inga", "Grand Inga (hydro)",          "Inga Dam"),
    ("are_hub",    "Australian REH (solar+wind)", "Pilbara wind farm"),
    ("morocco",    "Noor / desert solar",         "Noor Ouarzazate"),
    ("geothermal", "Iceland geothermal",          "Hellisheidi Power Station"),
    ("itaipu",     "Itaipu (hydro)",              "Itaipu Dam"),
    ("churchill",  "Churchill Falls (hydro)",     "Churchill Falls Generating Station"),
    ("rogun",      "Rogun / Nurek (hydro)",       "Nurek Dam"),
    ("siberia",    "Angara-Yenisei (hydro)",      "Sayano-Shushenskaya Dam"),
    ("kazakhstan", "Hyrasia / Kazakhstan (wind)", "wind farm Kazakhstan"),
]

CC_OK = ("cc0", "public domain", "cc by", "cc-by", "attribution")


def search(query, n=8):
    d = api({"action": "query", "generator": "search", "gsrsearch": query,
             "gsrnamespace": "6", "gsrlimit": str(n),
             "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size",
             "iiurlwidth": "320"})
    out = []
    for p in (d.get("query", {}) or {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {}) or {}
        out.append({
            "title": p["title"], "mime": ii.get("mime", ""),
            "license": em.get("LicenseShortName", {}).get("value", "?"),
            "artist": strip(em.get("Artist", {}).get("value", "?"))[:60],
            "credit": strip(em.get("Credit", {}).get("value", ""))[:60],
            "thumb": ii.get("thumburl", ""), "url": ii.get("url", ""),
            "w": ii.get("width", 0), "h": ii.get("height", 0),
            "index": p.get("index", 99),
        })
    out.sort(key=lambda r: r["index"])
    return out


# chosen file per site: (search query, substring that identifies the exact file)
PICKS = {
    "gobi":       ("wind farm Xinjiang",        "Wind power plants in Xinjiang"),
    "yarlung":    ("Yarlung Tsangpo",           "Yarlung Tsangpo - Tibet - 02"),
    "grand_inga": ("Inga Dam",                  "Inga04"),
    "are_hub":    ("Collgar Wind Farm",         "Collgar Wind Farm 2011"),
    "morocco":    ("Noor Ouarzazate",           "Noor 1 and 2"),
    "geothermal": ("Hellisheidi Power Station", "HellisheidiPowerStation01"),
    "itaipu":     ("Itaipu Dam",                "Itaipu Dam, aerial photograph"),
    "churchill":  ("Churchill Falls Labrador",  "Churchill fallslabrador"),
    "rogun":      ("Nurek Dam",                 "Nurek Dam and the Vakhsh River"),
    "siberia":    ("Sayano-Shushenskaya Dam",   "Shushenskaya Dam1"),
    "kazakhstan": ("wind farm Kazakhstan",      "Korday wind farm in the south"),
}
LABELS = {k: lab for k, lab, _ in SITES}


def imageinfo(title, width=640):
    d = api({"action": "query", "titles": title, "prop": "imageinfo",
             "iiprop": "url|extmetadata|mime|size", "iiurlwidth": str(width)})
    p = next(iter((d.get("query", {}) or {}).get("pages", {}).values()))
    ii = (p.get("imageinfo") or [{}])[0]
    em = ii.get("extmetadata", {}) or {}
    return {"title": p["title"], "thumb": ii.get("thumburl", ii.get("url", "")),
            "page": ii.get("descriptionurl", ""), "mime": ii.get("mime", ""),
            "license": em.get("LicenseShortName", {}).get("value", "?"),
            "artist": strip(em.get("Artist", {}).get("value", "?"))}


def fetch_bytes(url, tries=6):
    import time
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(min(5 * (i + 1), 30))   # back off on 429 / timeout
    raise last


def download():
    os.makedirs(OUT, exist_ok=True)
    attrib_path = os.path.join(OUT, "attributions.json")
    attrib = {}
    if os.path.exists(attrib_path):
        attrib = json.load(open(attrib_path, encoding="utf-8"))
    for key, (query, sub) in PICKS.items():
        dst = os.path.join(OUT, f"{key}.jpg")
        if os.path.exists(dst) and key in attrib:
            print(f"  -- {key:11s} already present, skip"); continue
        try:
            hit = next((r for r in search(query, 12) if sub.lower() in r["title"].lower()), None)
            if hit is None:
                print(f"  !! {key}: no file matching '{sub}'"); continue
            info = imageinfo(hit["title"], 640)
            with open(dst, "wb") as f:
                f.write(fetch_bytes(info["thumb"]))
            attrib[key] = {"label": LABELS.get(key, key), **info, "file": f"{key}.jpg"}
            print(f"  OK {key:11s} <- {info['title'][:48]}  [{info['license']}]")
        except Exception as e:
            print(f"  XX {key:11s} failed: {repr(e)[:80]}")
        with open(attrib_path, "w", encoding="utf-8") as f:
            json.dump(attrib, f, ensure_ascii=False, indent=2)
    print("attributions ->", attrib_path)


if __name__ == "__main__":
    if "--download" in sys.argv:
        download()
    else:
        for key, label, query in SITES:
            print(f"\n============== {key}  |  {label}  |  q='{query}'")
            try:
                for r in search(query):
                    ok = any(t in r["license"].lower() for t in CC_OK) and r["mime"].startswith("image")
                    flag = "OK " if ok else "  -"
                    print(f"  {flag}[{r['mime'].split('/')[-1]:4s}] {r['license']:20s} {r['w']}x{r['h']}  {r['title'][:50]}")
                    print(f"        by {r['artist']}")
            except Exception as e:
                print("  ERR", repr(e))
