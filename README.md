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
node test-physics.mjs    # regression check against Apollo EVA measurements
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

Calibrated against Apollo lunar-surface EVA measurements (780–1200 BTU/h):

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
- MOLA context basemap — live tiles from NASA Trek
- Surface dose rate 0.0267 mSv/h — MSL RAD, Gale crater
- Metabolic range 780–1200 BTU/h — Apollo lunar surface EVAs
- Physical constants (latent heat, caloric equivalent of O₂)

**Modelled, and labelled as such in the interface**
- Local elevation and slope field — synthetic, deterministic
- Suit consumable capacities — design estimates
- Diurnal temperature and dust opacity profiles

The local relief is synthetic by necessity: a MOLA tile covers ~167 km at
463 m/px, while an EVA plays out over ~10 km. Stretching it would produce
one blurred pixel. MOLA is shown as a context inset with the working area
marked, which is the honest use of it.

## Known limits

- Elevation field is synthetic; real planning needs HiRISE or CTX DTM
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
test-physics.mjs    regression barrier against the Apollo figures
dist/walkback.html  the deliverable — open this
```

The six calibration values in `test-physics.mjs` are a regression barrier:
they change only deliberately.

## Live demo

**https://ordinatum.github.io/walkback-envelope/**

No login, no install. Pick a scenario, drag the EVA timeline, watch the
return envelope shrink and the Point of No Return approach.

Suggested 60-second tour:
1. `NOMINAL`, pace 1.7 km/h — watch the verdict go GO → CAUTION as the
   envelope contracts around the habitat.
2. Toggle `HAVENS ON` — the reachable return area grows by about half,
   because each haven is an additional zero-cost source in the same search.
3. Switch to `SCRUBBER FAILURE` — the limiting consumable changes from
   cooling water to the CO₂ scrubber, and the tool says so by name.
4. Switch to `SOLAR FLARE (SPE)` — dose aborts the EVA while every tank is
   still comfortably full.
