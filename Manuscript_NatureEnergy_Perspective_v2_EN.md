# Waking the world's untapped mega-energy resources through the global token economy

*Perspective — draft v2, formatted for* Nature Energy. *Target: ≤3,000 words main text; unstructured ~150-word abstract with no references; ≤50 references; ≤6 display items (Fig. 1 concept schematic; Fig. 2–5; Box 1).*

> 中文备注（不属于稿件）：这是去"雅江中心化"后的 v2 英文稿，按 *Nature Energy* 体例。所有定量结果来自 `analysis/`（M1 组合/需求、M2 逐小时时间匹配、M3 芯片约束）输出的 `data/*_results.json`，并以区间陈述。关键对照论文为 Zhu et al., *Desert power for the AI era*, *Nexus* (2026)。⚠ 标记的引用投稿前须替换为一手文献。

**Authors:** [Author 1]¹, [Author 2]² · **Affiliations:** ¹…; ²… · **Correspondence:** …

---

## Abstract

The cleanest, cheapest electricity is increasingly built where almost no one can use it: remote mega-dams, desert wind and solar, and structurally curtailed renewable fleets that together strand or spill power on the scale of a major economy's entire consumption. The reflexive answer is to move the electrons over thousands of kilometres of lossy ultra-high-voltage line. Here we argue that for a large class of these resources the highest-value export is not the electron but the artificial-intelligence (AI) token — site inference at the resource and ship its output over optical fibre. A kilowatt-hour rendered as tokens can embed one to three orders of magnitude more exportable value than the same kilowatt-hour shipped as electrons or canned as aluminium. Quantifying a global portfolio of stranded resources against AI demand scenarios, and matching hourly clean supply to the always-on, planet-wide token load, we show the resource base is comparable to projected AI electricity demand and that a longitudinally distributed portfolio follows global demand with far less storage than any single site. The binding constraint is not energy but chips.

---

## Main

Across the world, the lowest-cost clean energy is being commissioned in places with no one to consume it. China's Yarlung Tsangpo project will generate on the order of 300 TWh a year — about three times the Three Gorges Dam — in a Himalayan gorge more than 2,000 km from demand¹,². But it is only the most dramatic instance of a global pattern. Grand Inga on the Congo, desert wind-and-solar export hubs from the Pilbara to Kazakhstan to Namibia, and the Gobi renewable mega-bases each marshal tens to hundreds of terawatt-hours far from load; meanwhile, *existing* wind and solar fleets in western China, west Texas, northern Chile, South Australia and Scotland already spill double-digit terawatt-hours a year as curtailment³,⁴. The conventional framing treats all of this as a transmission problem to be solved with more wire. That framing is not wrong, but it is increasingly the wrong default.

The same decade that produced these resources has produced an industrial demand for electricity that is unusually indifferent to *where* it is consumed, provided the result can move as information rather than as current. Global data-centre and AI electricity demand is rising steeply⁵, and the unit in which AI sells its output — the token — has become both enormous in aggregate and, for the first time, credibly measurable in its energy intensity⁶,⁷. A recent global optimization shows that off-grid desert wind-solar-storage systems could deliver firm, 24/7 power to co-located data centres at $39–46 MWh⁻¹, meeting the International Energy Agency's projected 2030 AI demand and far beyond⁸. That work establishes the supply-side feasibility. Here we ask the complementary, higher-level questions a Perspective should: *which* of the world's stranded resources are candidates, *how* they compare to plausible demand, why the token — not the electron — is the value-maximising export, how a global fleet matches a planet-wide and continuous demand, and what actually limits the build-out.

We make four quantitative claims, each anchored in an explicit calculation (Methods; `analysis/`): the token carries one to three orders of magnitude more exportable value per source kilowatt-hour than the electron or the metal (Fig. 2); the identified global portfolio of stranded clean energy is comparable to — not a multiple of — projected AI demand (Fig. 3, Box 1); because token demand exists everywhere and every hour, a longitudinally distributed portfolio can follow it with far less storage than any single site needs (Fig. 4); and the binding constraint on realising any of this is chips and capital, not watts (Fig. 5).

![Figure 1 | Three export pathways](figures/Fig1_three_pathways.png)

**Figure 1 | Three export pathways from one stranded-energy site.** A stranded watt can leave as an electron (UHV line: lossy, capital-heavy, regional reach, low value), a metal (aluminium: "canned electricity", shippable, modest value), or a token (fibre: near-zero transport loss, global reach, highest value density). Concept schematic.

### Why the token wins: full life-cycle value

Long-distance transmission is an engineering triumph, but as a way of *monetising a resource with no local market* it is a poor default: a ±800-kV UHVDC line loses 6–10% over 2,000–3,000 km⁹,¹⁰; its fixed capital makes the delivered cost scale inversely with utilisation³; the product is a bare commodity kilowatt-hour worth only ~$0.05–0.08 at the far end, and only if a buyer exists¹¹; and the line itself takes the better part of a decade to build, with interconnection queues now holding more than two terawatts of generation and storage¹² — whereas a data hall can be energised in months and scale incrementally with the resource. A century-old alternative is to export an energy-intensive *product*: primary aluminium, whose Hall–Héroult process consumes ~13–16 kWh kg⁻¹, so electricity is ~40% of the metal's cost and the ingot is, in effect, "canned electricity"¹³ — which is why smelters were deliberately sited at otherwise unmarketable hydropower from Norway to Iceland¹³,¹⁴. We propose the data centre as the modern smelter and the token as a far denser ingot, with an instructive inversion: electricity is ~40% of aluminium's cost but only ~4–7% of computation's⁶, so cheap power matters less to a token operation — but the operation is therefore *robust* rather than fragile to energy prices, and its decisive advantages are the two things a stranded resource uniquely supplies: a vast quantity of otherwise-curtailed clean energy, and freedom from the large-scale transmission build-out that exporting electrons would demand.

The token's advantage is clearest on a full life-cycle basis (Fig. 2). Per source kilowatt-hour, the *gross* value each pathway can embed differs by one to three orders of magnitude: ~$0.05–0.08 as delivered electrons⁹,¹¹, ~$0.14–0.20 as aluminium¹³, and ~$0.7 to ~$123 as tokens from budget to frontier pricing⁶,⁷ (Fig. 2a). The token's lifecycle *cost* per source kilowatt-hour is, honestly, the highest of the three — ~$0.4–0.7, because chips and facilities dominate compute cost while electricity is only ~4–7%⁶ (Fig. 2b); this capital intensity is the binding constraint we return to below, not a property of the watt. Yet because the value created is so much larger, the *net value added* per source kilowatt-hour — gross output value minus all non-energy lifecycle cost — still favours the token decisively: roughly $2–3 across budget, mainstream and frontier workloads, against near-zero to ~$0.11 for the electron or the metal — an advantage of one to two orders of magnitude (≈90–170×) that survives the token's high conversion cost (Fig. 2c). The token wins not by being cheap to produce, but by creating far more exportable value from each otherwise-stranded watt.

![Figure 2 | Life-cycle cost and value](figures/Fig2_lifecycle_value.png)

**Figure 2 | Full life-cycle cost and value per source kilowatt-hour.** (a) Gross export value density (log), each pathway swept over its output price: electron ~$0.05–0.08, aluminium ~$0.14–0.20, token ~$0.7–123 (budget-to-frontier pricing at efficient ε) — one to three orders of magnitude. (b) Life-cycle cost per source kWh: the token's conversion cost (~$0.5) is the highest of the three, because chips and facilities dominate while electricity is only ~4–7%. (c) Net value added per source kWh (gross minus non-energy lifecycle cost) across representative workload tiers: ~$2–3 for tokens versus near-zero to ~$0.11 for electrons or metal — an advantage of one to two orders of magnitude (≈90–170×).

### The resource base, against demand

How large is the opportunity? We assemble a tiered portfolio of large stranded clean-energy resources (Box 1; `data/portfolio.csv`), screened on the criteria a co-located compute terminal actually needs — capacity factor, cooling climate, latency to fibre landing points, and proximity to infrastructure — following the desert-resource methodology of ref. 8. Tier 1 comprises discrete mega-projects: remote mega-hydro (Yarlung, Grand Inga, the Siberian cascade, Churchill Falls) and planned desert export hubs (Gobi mega-bases, Pilbara, Hyrasia, Hyphen). Tier 2 comprises *existing* renewable fleets whose output is already curtailed today, where the marginal value of the spilled energy is near zero.

The identified Tier 1 resource totals ~1,100–2,150 TWh yr⁻¹ of strandable energy, and Tier 2 adds ~60–110 TWh yr⁻¹ already being spilled (Fig. 3a) — together ~1.2–2.3 PWh yr⁻¹, with theoretical desert potential several times larger again⁸. The honest reading is deliberately undramatic: this is comparable to, not a vast multiple of, the IEA's ~1 PWh yr⁻¹ projection for 2030 AI electricity — about 1.2–2.3× it, and ~12–23% of an aggressive 10 PWh scenario⁸. Converted to tokens at central energy intensity, the same portfolio could embed ~100–230× the world's entire 2025 token throughput (Fig. 3b), but that multiple is set by the dominant uncertainty — ε, the energy per token, which spans ~0.15–120 J across measured workloads⁶,⁷ — and should always be stated as a range. The claim is not that one resource dwarfs the world; it is that the global stranded base is *the same order of magnitude* as the demand it could serve, so decisions about where the next gigawatts of compute are built are implicitly decisions about which stranded watts get monetised.

![Figure 3 | Portfolio supply vs demand](figures/Fig3_supply_vs_demand.png)

**Figure 3 | The stranded resource base, in energy and token terms, against AI demand scenarios.** (a) Strandable supply by tier (PWh yr⁻¹, log) against IEA-2030, 10× and 100× demand lines and the desert-WSS deliverable band⁸. (b) Token output of the realistic portfolio versus ε, with the 2025 global throughput band; right axis in multiples of current throughput.

### Token demand is global and continuous — so distribute the supply

A single site sees only its own sun and wind; the world's token demand sees neither. Inference is consumed across every time zone, around the clock, with an aggregate diurnal swing far gentler than any one region's because regional peaks are staggered by longitude (our constructed global demand envelope has a peak-to-mean ratio of only ~1.04; Methods). This is the mirror image of the supply problem, and it suggests a different solution from firming each site to 24/7 with storage⁸: distribute the supply across longitudes so that the *portfolio* — not any single site — follows the planet-wide load.

Using real hourly capacity factors for representative sites spanning −102° to +138° longitude (ERA5 reanalysis¹⁵; Methods), we find the effect is large (Fig. 4). A single solar-dominated site has a diurnal peak-to-mean ratio of ~2.6 and would need ~9 hours of mean-load storage to firm a flat load; a geographically balanced portfolio of the same sites falls to ~1.3 and ~1.5 hours — a ~6× reduction in the daily storage requirement — because one region's afternoon is another's night. For a *routable*, latency-tolerant workload that can follow the surplus, ~89% of the always-on global token demand can be met directly by coincident clean supply with no storage at all, rising to ~94% with a firm hydro anchor in the portfolio. Geographic balance is itself a design lever: a portfolio weighted only toward the largest resources (which happen to cluster in the Eastern Hemisphere) smooths less, needing ~2.9 rather than ~1.5 hours. A multi-week *seasonal* residual remains — the genuine limit — and is addressed not by batteries but by the firm hydro members of the portfolio and by letting batchable utilisation flex seasonally.

![Figure 4 | Global temporal matching](figures/Fig4_temporal_matching.png)

**Figure 4 | Token demand exists every hour everywhere; a distributed portfolio follows it with far less storage than any single site.** (a) Average UTC day: longitudinally staggered sites (grey) sum to a near-flat portfolio (blue/green) tracking the always-on global demand (dashed). (b) Diurnal storage to firm a flat load. (c) Share of global demand met directly by coincident clean supply (routable "follow-the-sun" load).

### The binding constraint is chips, not watts

The same arithmetic that makes cheap power a minor cost advantage relocates the binding constraint. Because chips and servers are ~60% of compute cost of ownership and electricity only ~4–7%⁶ (Fig. 5a), cheap stranded power improves margins only modestly; what it removes is the *transmission* problem, not the *hardware* problem. At ~2 kW of facility-level power per high-end accelerator¹⁶, the ~1.2–2.3 PWh yr⁻¹ portfolio corresponds to ~130–260 GW of continuous compute — requiring of order 65–130 million accelerators. Against a global high-end accelerator output of order 4–5 million units a year (≈3.76 million data-centre GPUs in 2023), packaging-capacity-limited and growing¹⁷, even dedicating a fifth of world output to stranded sites deploys only ~2 GW of compute a year. A single 10-GW cluster then takes ~5 years; filling 60 GW takes ~30 years and ~30 million accelerators worth ~$1.5 trillion (~9× the dam itself); and the full resource base is a multi-decade horizon (Fig. 5b). First movers will accordingly be modest — a few gigawatts co-located with a curtailed resource, not a dam filled at once. The stranded watt is abundant; the chip to consume it is the scarce input.

![Figure 5 | The chip constraint](figures/Fig5_chip_constraint.png)

**Figure 5 | Cheap stranded power barely changes token cost; the binding constraint is chips, capital and ramp.** (a) Compute cost of ownership: chips ~60%, facility ~29%, electricity only ~4–7%⁶. (b) Cumulative compute deployable at 20% of global accelerator output against the strandable-resource band; a 10-GW cluster takes ~5 years, the full portfolio decades.

### What would have to be true, and what would not

The model fits a large and growing class of workloads under conditions several resources already meet. *Batchable, latency-tolerant* work — large-scale pre-training, batch and reasoning inference, synthetic-data generation, agentic background jobs — does not depend on being near the user, and reasoning-style workloads alone passed half of usage by late 2025⁶. Optical fibre adds negligible energy and only tens of milliseconds per 1,000 km, which such work tolerates easily; cold and high sites are unusually good for cooling¹⁸; and bitcoin mining has already proven that compute will migrate to flared gas, curtailed hydro and oversupplied wind as a buyer of last resort¹⁹. The scope limit is the natural rebuttal to "why not simply build near demand": latency-sensitive and data-resident workloads should and will stay near users — our claim is only that the *batchable* fraction has a strong, under-appreciated reason to migrate to stranded energy, and that premier resources should be planned with that option in view.

### Supply-side risks and limits

The decisive risks are on the *supply* side — whether the clean energy can actually, reliably feed a globally distributed fleet. First and most important is **temporal availability**: wind and solar are intermittent, and even a diversified portfolio has correlated low-output hours; our matching quantifies the residual firming, but it does not eliminate it. Second is **seasonality and multi-day extremes** — dry seasons, winter solar minima, multi-day wind-and-solar lulls, and climate-driven hydrological **drought** — which create sustained deficits that hourly storage cannot cover and that fall instead to firm hydro and to seasonal utilisation flex. Third is the **uncertainty of curtailment as a resource**: spilled energy is by definition variable, and the curtailed fraction shrinks as grids add storage and transmission, so compute sized to it must be interruptible and may face declining availability. Fourth are **physical and logistical** limits — seismic hazard, cooling-water scarcity, thin high-altitude air, extreme remoteness, and the supply-chain problem of moving millions of accelerators into such places; the Yarlung site, with design earthquakes near magnitude 8.5, near-roadless terrain, and a contested trans-boundary river, is the extreme instance of this category, not a template¹,². Fifth, **dependence on grid or fossil firming** would undercut the very "stranded" and "clean" premises on which both the economic and the carbon cases rest. Two further caveats are not supply risks but bound the climate claim: making tokens cheap may, by Jevons-style rebound, expand total energy and hardware use²⁰; and crediting the clean energy embedded in exported computation — analogous to embodied energy in traded aluminium — needs a carbon-accounting framework that does not yet exist²¹.

### Outlook

The cheapest clean energy is increasingly stranded where no one can use it, while the fastest-growing demand for it can be consumed anywhere and shipped as information. When those facts meet, the best export route for a stranded watt is increasingly the token, and premier stranded resources should be planned as compute terminals alongside — or instead of — transmission. Four steps follow. Agencies should publish a delivered-value-per-source-kilowatt-hour metric comparing electron, metal and token export site by site, and extend it into a carbon-accounting framework that credits embedded clean computation. Operators should pilot a gigawatt-scale, curtailment-financed inference cluster at an *existing* curtailed-renewable site — west Texas, northern Chile or Qinghai — as a near-term proof that needs no Himalayan dam. Because the constraint is silicon, chipmakers and policymakers should treat "compute at the resource" as a chip-allocation and export-control question. And the field should standardise transparent disclosure of energy per token, since that single parameter dominates every estimate here. Aluminium taught the twentieth century to can its stranded electricity and ship it; within this decade, the densest can we have is a token.

---

## Box 1 | A tiered portfolio of stranded clean-energy resources

![Box 1 | Portfolio table](figures/Box1_portfolio_table.png)

**Tier 1 — discrete mega-projects.** Remote mega-hydro (Yarlung Tsangpo ~270–300 TWh yr⁻¹; Grand Inga ~40–370; the Siberian Angara–Yenisei cascade; Churchill Falls) and planned desert export hubs (Gobi mega-bases ~450–900; Pilbara ~80–90; Hyrasia ~60–120; Hyphen ~25–35). Strandable total ~1,100–2,150 TWh yr⁻¹. Yarlung is the extreme member — maximal scale and a cold, high-head resource, but also maximal seismic, logistical and geopolitical difficulty — not the organising case.

**Tier 2 — curtailed fleets (today's spilled energy).** Existing wind and solar in western China, west Texas, northern Chile, South Australia, Scotland and Iberia, already curtailing ~60–110 TWh yr⁻¹ at near-zero marginal value. Smaller in total than Tier 1, but already built, already paid for, and the cleanest near-term case for the argument. Full list and screening fields: `data/portfolio.csv`.

---

## References

*(Highlighted references carry a bold significance note, per Nature-portfolio style. ⚠ = trade/secondary, to be replaced with primary literature before submission.)*

1. China Breaks Ground for World's Largest Hydropower Station. *POWER Magazine* (2025). ⚠
2. Yarlung Tsangpo Hydropower Fuels the PRC's Energy–Computing Strategy. *Jamestown China Brief* (2025). ⚠
3. What's Driving China's Mega Medog Hydropower Project? *The Diplomat* (2026). ⚠
4. China renewable curtailment statistics, 2025 (provincial and Tibetan). [Ember China Energy Transition Review 2025; NEA H1-2025]. ⚠
5. International Energy Agency. *Energy and AI* (IEA, 2025).
**The first authoritative projection that data-centre and AI electricity demand will roughly double by 2030.**
6. You, J. How much energy does ChatGPT use? *Epoch AI, Gradient Updates* (2025).
**Bottom-up accounting (~2 J per token; electricity ~4–7% of compute cost) underpinning the value-density and chip-constraint cores.**
7. Energy use of AI inference: efficiency pathways and test-time scaling. *Joule* (2026).
**Establishes that reasoning and test-time scaling raise per-token energy by one to two orders of magnitude — the upper end of ε.**
8. Zhu, Z., Yu, R., Chen, W.-Q. & Zhang, D. Desert power for the AI era. *Nexus* 3, 100121 (2026).
**The complementary supply-side analysis: a global techno-economic optimization showing off-grid desert wind-solar-storage can deliver firm 24/7 power to co-located data centres and meet IEA-to-100 PWh AI demand; we adopt its screening method and contrast its per-site firming with our distributed-portfolio matching.**
9. DeSantis, D. et al. Cost of long-distance energy transmission by different carriers. *iScience* 24, 103495 (2021).
10. World Nuclear Association. *Electricity Transmission Grids* (2024). ⚠
11. International Renewable Energy Agency. *Renewable Power Generation Costs in 2023* (IRENA, 2024).
**Documents that Chinese large hydropower (~$40 MWh⁻¹) is among the lowest-cost electricity on Earth.**
12. Rand, J. et al. *Queued Up: Power Plants Seeking Transmission Interconnection* (LBNL, 2024).
**Quantifies that transmission, not generation, is now the binding step of the energy transition — the temporal asymmetry favouring fast-to-build compute.**
13. International Aluminium Institute. *Primary Aluminium Smelting Energy Intensity* (IAI, 2023).
14. Stranded hydropower and aluminium smelting — Iceland (Kárahnjúkar/Alcoa) and US Pacific Northwest (Bonneville) closures. [primary refs to be added]. ⚠
15. Hersbach, H. et al. The ERA5 global reanalysis. *Q. J. R. Meteorol. Soc.* 146, 1999–2049 (2020); hourly data via the Open-Meteo archive API.
**The reanalysis source for the hourly capacity-factor profiles in the temporal-matching analysis.**
16. NVIDIA GB200 NVL72 technical specifications (rack ~120–132 kW / 72 GPUs). ⚠
17. NVIDIA data-centre GPU shipments ~3.76M (2023); TSMC CoWoS packaging capacity 2024–2026. [DCD; TrendForce]. ⚠
**Establishes that high-end accelerator output, packaging-capacity-limited, is the true bottleneck on deploying compute at stranded sites.**
18. Google. *Efficiency — Data Centers* (PUE disclosures) (2024). ⚠
19. de Vries, A. Bitcoin's growing energy problem. *Joule* 2, 801–805 (2018). [+ flared-gas/curtailment mining ref].
20. Sorrell, S. Jevons' Paradox revisited. *Energy Policy* 37, 1456–1469 (2009).
21. Trans-boundary and embodied-energy accounting for traded computation. [framework refs to be added]. ⚠

*[List to be expanded to ~40–50 for submission: primary sources for token throughput, Chinese UHV utilisation, curtailment statistics, accelerator output and HBM/CoWoS capacity, Three Gorges comparison, and Hall–Héroult thermodynamics.]*

---

## Author notes (not part of the manuscript)

- **Reframing vs v1:** Yarlung demoted from organising case to one Tier-1 row / the "extreme" member (Box 1, §risks). New quantitative spine = portfolio-vs-demand (M1, Fig. 3), global temporal matching (M2, Fig. 4, signature), chip constraint (M3, Fig. 5). Risk section rewritten to supply-side. New title.
- **Numbers** are all generated by `analysis/` → `data/*_results.json`; cited as ranges. ε remains the dominant uncertainty.
- **Display items:** Fig. 1–2 retained; Fig. 3–5 + Box 1 new; old global map → `figures/FigS1_global_site_map` (Supplementary). 6 items, within limit.
- **Differentiation from ref. 8 (Desert Power):** they optimise per-site 24/7 firm supply; we add (i) value-density framing, (ii) demand-side global temporal matching with a distributed portfolio, (iii) the chip constraint. Must be stated explicitly in cover letter.
- **To do before submission:** replace ⚠ refs with primaries (`academic-paper/scripts/verify_citations.py`); confirm word count ≤3,000; optionally render Fig. 1 in-house.
