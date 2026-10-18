# Project code: Sample Community Pool Garden (reference build)

Working code from a fictional Sample Community HOA pool-garden example project (Florida, Oct 2026). It turns measured site features into a full interactive HTML plan set. Copy the folder into the working directory, swap in the new site's data, and adapt it. Don't rewrite it from scratch.

## Run
```bash
pip install --break-system-packages shapely numpy   # playwright + chromium are preinstalled in the workspace
python3 build.py        # writes example-pool-garden.html (rename in build.py)
python3 fullshot.py 1280 full.png        # full-page screenshot for checking; add an arg for dark mode
python3 shot.py plant.svg plant.png 1523 # render a single SVG sheet
```

## Module map (dependency order)
| File | Role |
|---|---|
| `geo.py` | Converts GIS feature coordinates (local state-plane ft) into the deck-aligned design frame. Writes `feat.json`. **Replace its inputs per site.** |
| `feat.json` | Site features in the design frame: parcel ring, pool, palms, oak, kiosk, utility. Example data. |
| `layout.py` | Layout engine: hardscape, nature path spline, spurs, soft right-of-way bed edges, neighbor maintenance strips, pool band, Voronoi drifts, hex-grid plant counts, individual shrubs and trees, plant palette `PAL`, `qty`, `area`. **Most per-site edits go here.** |
| `render.py` | SVG drawing primitives and base layers: streets and curb, beds, deck, walks, path, canopies, palms, right-of-way oaks, patterns, north arrow, scale bar, leaders. Features are wrapped in `<g class="hit" data-k=...>` for the clickable plan. |
| `compose.py` | Assembles the planting and irrigation sheets: drift layer with click metadata (count, irrigation zone, planting year), callout tags, zone labels and leader columns. |
| `irrigation.py` | Drip zones (by hydrozone), valve boxes, branched mainline, headers, auto sleeves at path crossings, zone flow table, irrigation overlay SVG. |
| `details.py` + `details.css` | Hand-drawn construction detail sections: path typical and no-dig, pool band, drip valve assembly, drip grid, sleeve. |
| `prices.py` | Plant unit prices and sizes (illustrative example prices, Oct 2026) and the `SPREAD` reduced-density factors. **Re-price per project.** |
| `phasing.py` | Maps zones to phases, path pieces and rock pieces by region, and per-phase quantities and geometry. |
| `schedule.py` | Year-by-year scheduler under `BUDGET`: contingency, escalation, arborist visits, labor allowances, vendor-covered irrigation (zero cost), path splitting, look-ahead packing. |
| `phase_render.py` | Top-down render per year from the schedule state, with plant growth by age and widening oak canopies. |
| `budget_section.py` | B-1 phased-buildout HTML: assumptions, at-a-glance table, who-does-the-work table, year cards with renders and line items, ways to finish sooner. |
| `build.py` | Builds the whole page: tokens and CSS, title block, stats, concept, L-1 clickable plan (JSON info lookup and JS), L-2 schedule, L-3 path, I-1/I-2 irrigation, B-1, D-1 details, N-1 notes and sources. |
| `tokens.css` | Drawing-sheet colors and SVG text classes (scoped to `.sheet` in build). |

## Adapting to a new site
1. Measure the site (parcel-site-measurement skill) and update `geo.py`, then rebuild `feat.json`.
2. In `layout.py`:
   - Update deck and restroom sizes, path waypoints, nodes and spurs.
   - Update the kiosk and walks, existing trees and palms, wing and lawn regions, and the right-of-way oak positions.
   - Update `zone_of()` rules and `WEIGHTS`, and the palette `PAL` (code, botanical, common, native, container, spacing, size, color, kind).
3. In `irrigation.py`, update zone boxes, valves, mainline and headers. In `phasing.py` and `schedule.py`, update work packages, `WP_ZONE`, path regions, `MAIN_SEG` and `BUDGET`.
4. In `build.py` and `budget_section.py`, update text: title block, notes, sources, assumptions and feature descriptions in `PINFO`.
5. Render, inspect crops, fix the geometry at its source, then publish with the Artifact tool (same file path keeps the URL).

## Gotchas learned
- Subtract every hard element (spurs, pads, kiosk walk) from `plantable` so paths never run through plants.
- Don't clip spurs to the parcel when they must reach walks in the right-of-way.
- `build.py` page HTML is an f-string: double every `{` `}` in CSS and JS.
- Standalone renders can't use CSS variables, so use fixed colors there.
- An atomic item larger than the yearly budget will loop forever unless it's split.
- Zero-cost vendor items must not be pulled ahead by the look-ahead.
