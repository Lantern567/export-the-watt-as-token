# Export the watt as a token

A *Perspective*-style manuscript and its evidence base, arguing that **stranded clean
electricity** at remote mega-sites (flagship case: the ~60 GW / ~300 TWh-per-year Yarlung
Tsangpo hydropower project) is best exported **as AI inference — tokens — over optical fibre**,
rather than as electrons over lossy ultra-long-distance transmission. Per source kilowatt-hour, a
token can embed roughly **10–1,000×** the value density of an electron, or of the aluminium that
smelters have made from stranded hydropower for a century.

> ⚠️ **Working draft of an unpublished manuscript.** Numbers are presented as ranges with sources
> and several citations still need replacement with primary literature before any submission.

## Contents

| Path | What it is |
|------|------------|
| [`Manuscript_Nature_Perspective_v1_EN.md`](Manuscript_Nature_Perspective_v1_EN.md) | English Perspective draft (Nature format, ~3,250 words) |
| [`Manuscript_Perspective_v1_中文.md`](Manuscript_Perspective_v1_中文.md) | Chinese mirror of the manuscript |
| [`Perspective_选题拓展_中文版.md`](Perspective_选题拓展_中文版.md) | Concept/expansion document: quantitative framework, worked example, outline, sources |
| [`figures/`](figures/) | Publication figures (Fig. 1–5, PNG + PDF) and the reproducible `make_figures.py` |
| [`data/`](data/) | `sites_master.csv` (50 global stranded-energy sites with coordinates) and verified-number / research JSON |
| [`references/`](references/) | Reading list of Nature / Nature Energy Perspectives (`README.md`); the PDFs themselves are not redistributed |

## Key figures

- **Fig. 1** — three export pathways from one stranded-energy site (electrons / aluminium / tokens).
- **Fig. 2** — value-density ladder (log scale).
- **Fig. 3** — site token output vs energy-per-token ε (one site ≈ 0.5×–30× current global token demand).
- **Fig. 4** — compute cost structure (electricity ≈ 4–7%; the constraint becomes chips).
- **Fig. 5** — global map of stranded / curtailed clean-energy sites.

Figures are reproducible: `python figures/make_figures.py` (requires `matplotlib`, `numpy`, `pandas`, `cartopy`).

## Reproducing the figures

```bash
pip install matplotlib numpy pandas cartopy
python figures/make_figures.py
```

## License / use

The downloaded reference PDFs are third-party copyrighted works and are **excluded** from this
repository (see `.gitignore`); `references/README.md` lists them with links. The manuscript text,
figures and data in this repository are the authors' work in progress.
