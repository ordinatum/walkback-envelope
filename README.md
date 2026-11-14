# WALKBACK ENVELOPE

**Can the astronaut still walk home?**

A decision-support tool for Mars surface EVA. One question, answered
continuously: from the astronaut's current position, are there enough
consumables left to reach shelter — and which consumable runs out first.

Built for the [NASA Space Apps Challenge 2026](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/),
challenge *"Interplanetary Survival Guide: Martian Map"*.

## Run it

Open `dist/walkback.html` in any browser. No build, no server, no network —
one self-contained file that works offline.

For development:

```bash
python build.py          # rebuild dist/walkback.html from index.html + physics.mjs
node test-physics.mjs    # regression check on the consumption formulas
```

## Why this, and not another layered map

The challenge asks for a map a Mars astronaut could actually use, and states
that **crew safety is NASA's first priority**. Most layered-map projects show
*where things are*. This one answers the question that decides whether the
crew comes back: **the walk-back limit**.

The return envelope is not a circle. Climbing costs more than descending, so
the set of places you can still return from is an irregular shape that
shrinks as consumables drain. The moment the astronaut leaves it is the
**Point of No Return**.

## What it actually computes

**One reverse Dijkstra from the habitat.** Edges are reversed, so each cell
carries the directed cost of walking *from that cell back to shelter*. The
verdict, the Point of No Return and the drawn envelope all read from this
single field — they cannot disagree with each other.

**Four consumable channels, in physical units.** The headline finding of the
model: *oxygen is not the limiting resource.* At realistic metabolic rates an
O₂ supply lasts far longer than an EVA. What actually ends a Mars walk is
cooling water, CO₂ scrubber capacity and battery. The verdict always names
the specific limiting consumable rather than showing an abstract percentage.

**Cost anisotropy.** Traversing an edge downhill is not the same price as
traversing it uphill. A long descent away from base is cheap going out and
expensive coming back — which is exactly how crews get stranded.

**An irreducible 25 % reserve**, applied identically to the verdict and to
the envelope, per the mission requirement that at every point
`remaining ≥ return_cost + reserve`.

## Physical model

Metabolic cost uses the Pandolf equation adapted to Mars gravity (0.38 g).
The adaptation matters: gravity-dependent terms (load support, work against
grade) scale with g, while the level-walking term does not — a naive
multiplication of the whole equation by 0.38 badly underestimates the cost.

A heuristic Mars-gravity adaptation of Pandolf, regression-tested and compared
in **scale** with Apollo lunar-EVA averages (780–1200 BTU/h). The Apollo figure
is an overall range across lunar EVAs, not matched per-activity measurements, and
the model is **not validated for suited walking on Mars**:

| Activity | Model | BTU/h |
|---|---|---|
| Standing | 165 W | 563 |
| Walking 1.4 km/h, level | 206 W | 704 |
| Walking, +8 % grade | 282 W | 961 |
| Walking, +15 % grade | 348 W | 1186 |
| 2.5 km/h with 25 kg load | 414 W | 1413 |

Radiation uses the MSL RAD surface measurement at Gale crater:
**0.64 mSv/day = 0.0267 mSv/h**. Dose is an independent abort channel — a
solar particle event can force an abort while tanks are still full.

Heat rejection assumes a membrane evaporator, not a sublimator: Mars surface
pressure sits at or above water's triple point (6.1 mbar), so a sublimator
would not function.

## Data: real vs modelled

Stated plainly, because judges will ask.

**Real NASA data and published measurements**
- **Terrain — MOLA + HRSC Blended DEM, 200 m/px** (USGS/NASA/DLR). Four real
  sites are cut from the global 11 GB mosaic with GDAL `/vsicurl/`, 25 km
  across each, resampled to the 84x84 working grid (298 m per cell). There is
  no synthetic terrain in the application.
- MOLA context basemap — live tiles from NASA Trek
- Surface dose rate 0.0267 mSv/h — MSL RAD, Gale crater
- Metabolic range 780–1200 BTU/h — Apollo lunar surface EVAs (scale reference, not per-activity calibration)
- Physical constants (latent heat, caloric equivalent of O₂)

**Modelled, and labelled as such in the interface**
- Suit consumable capacities — design estimates
- Diurnal temperature and dust opacity profiles

MOLA alone (463 m/px) would give only 54 pixels across a 25 km site, so the
blended MOLA+HRSC product at 200 m/px is used instead — 125 pixels, enough to
resolve a crater rim and a canyon wall.

### Four real sites

| Site | Relief | Why it is here |
|---|---|---|
| **Jezero Crater** | 1211 m | Perseverance landing site. Rim and delta — strongly anisotropic return cost |
| **Gale Crater** | 2480 m | Curiosity landing site. Central mound: a sustained climb in every direction |
| **Melas Chasma** | 3261 m | Valles Marineris. 11 % of cells exceed 25 deg — walls are impassable and the envelope is forced along the valley |
| **Elysium Planitia** | 61 m | InSight landing site. The control case: on a flat plain the envelope is nearly circular |

The contrast between Melas and Elysium is the point: envelope shape comes from
real terrain, not from drawing.

## Known limits

- **Metabolism at 1.7 km/h gives 225.7 W against our 300–500 W design target.**
  If real expenditure is higher, the envelope is too wide and the
  resource-driven PNR too late. The regression suite reports this as a declared
  deviation rather than hiding it. Passing tests does not remove the uncertainty.
- **The 3 mSv abort threshold is an illustrative project value, not a NASA
  limit.** NASA states blood-forming-organ limits in mGy-Eq (500 mGy-Eq/year);
  equivalent and effective dose are not interchangeable. Only the MSL RAD
  background rate is a sourced quantity.
- **PNR is a hypothetical outbound deadline**, computed along uninterrupted
  outward walking, not a certified no-return point on the executed plan. It is
  possible to pass it and still walk home above reserve — the nominal run does.
- **Terrain shielding is weak at 200 m/px**: the deepest Melas point keeps
  96.2 % sky view, so dose falls about 3 % below the open plain. A real canyon
  would shield far more; we do not have data at that resolution.
- **Safe Havens are hypothetical**, not mapped infrastructure. Their caches and
  sky fractions are assumed values used to show the mechanism.
- **The cost field uses 16 directions** (8 neighbours + 8 knight moves).
  Directional distance error is about 2.7 %; true geodesic distance would need
  a continuous solver.

- Terrain is real but at 200 m/px; metre-scale hazards (boulders, fissures)
  need HiRISE or CTX DTM and are not resolved
- Metabolic model extrapolates lunar measurements to Mars gravity
- Suit capacities are estimates, not a specification of any real unit
- Thermal balance is simplified: no body orientation to the Sun, no soil
  thermal properties
- Dose uses mean GCR; local variation and secondary neutrons are not modelled
- Terrain data-resolution penalties and terrain-derived sky-view shielding
  were deliberately skipped — a synthetic coverage mask over a synthetic
  height field would be decoration, not evidence

## Structure

```
index.html          development entry point, imports physics.mjs
physics.mjs         physical core: metabolism, consumption, dose
build.py            inlines physics into the single-file deliverable
test-physics.mjs    regression barrier on the consumption formulas
dist/walkback.html  the deliverable — open this
```

The six values in `test-physics.mjs` are a regression barrier against our own
outputs, not an independent validation dataset. Its budget fixture
(water 3.2 kg / CO₂ 620 g / battery 760 Wh / O₂ 700 g) is a **separate legacy
suit configuration** — the application uses 5.6 kg / 640 g / 1100 Wh / 560 g,
so passing the suite does not certify the app's nominal endurance:
they change only deliberately.

## Live demo

**https://ordinatum.github.io/walkback-envelope/**

No login, no install. Pick a scenario, drag the EVA timeline, watch the
return envelope shrink and the Point of No Return approach.

Suggested 60-second tour:
1. `NOMINAL`, pace 1.7 km/h — watch the verdict go GO → CAUTION as the
   envelope contracts around the habitat.
2. Click anywhere on the map to move the science target — the route, the
   Point of No Return and the verdict recompute immediately.
3. Switch sites in the top bar: `MELAS CHASMA` shows the envelope pinned
   inside a canyon, `ELYSIUM PLANITIA` shows the near-circular control case.
4. Toggle `HAVENS ON` — the reachable return area grows by about half,
   because each haven is an additional zero-cost source in the same search.
5. Switch to `SCRUBBER FAILURE` — the limiting consumable changes from
   cooling water to the CO₂ scrubber, and the tool says so by name.
6. Switch to `SOLAR FLARE (SPE)` — dose aborts the EVA while every tank is
   still comfortably full.

## AI assistance

This project was built with AI assistance (Claude and OpenAI Codex) for code,
physics derivation, independent review and documentation. Terrain extraction,
the physics model, the verification harness and all defect fixes were produced
in that collaboration and verified in-browser against the running application.
NASA Space Apps requires AI usage to be disclosed; this is that disclosure.

## Data and tools

- **Terrain** — USGS/NASA/DLR, Mars MGS MOLA + MEX HRSC Blended DEM Global
  200 m/px, read with GDAL `/vsicurl/` from the global mosaic
- **Context basemap** — NASA Trek MOLA colour-shade tiles
- **Dose baseline** — MSL RAD, Gale crater surface measurements
- **Metabolic scale reference** — NASA Apollo lunar-EVA metabolic report
- **Tools** — GDAL, Python 3, Node.js, plain HTML/Canvas (no frameworks)
