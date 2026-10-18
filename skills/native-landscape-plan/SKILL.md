---
name: "native-landscape-plan"
description: "Design a Florida-Friendly, Florida-native landscape with a nature path and drip irrigation, and deliver it as a presentation-quality interactive HTML plan set (planting plan, schedule, irrigation, details)."
---

# Native landscape plan set

Use this skill for landscape design requests such as a planting design around a pool, common area, yard or HOA property. It is especially suited to native or Florida-Friendly plantings with paths and irrigation, delivered as something a client, community or committee can review. Measure the site first with the `parcel-site-measurement` skill, and build budgets and phasing with the `phased-landscape-budget` skill.

## Example client context: Sample Community HOA (fictional reference project)
The bundled reference build uses a fictional community pool garden. Treat the following as an example brief, not as facts about your client.
- **Site:** community pool parcel at Example Rd and Example Dr, Anytown FL, county parcel ID XXXXXXX. It has a fenced pool deck (about 82 × 42 ft) and restroom building, a large live oak behind the mail kiosk, existing sabal palms around the pool, and an east lawn extension behind the backyards.
- **Example preferences:**
  - Permeable nature paths, not paved.
  - Low-litter plantings near the pool, and nothing planted inside the deck.
  - No hedges screening the neighbors; they want neighbors to see the garden.
  - 5 ft plant-free maintenance strips along zero-lot-line houses.
  - Soft, curving bed edges that may extend into the right-of-way while keeping at least 4 ft of lawn at the curb.
  - Live oaks planted in the right-of-way for future path shade, with an arborist keeping the canopy 10–15 ft off the pool fence.
  - A dog rest area on the east lawn.
  - Irrigation is handled by a contracted vendor, so leave it out of budgets.
- Ask the client for their own preferences; do not reuse these for a different site.

## Research the plant palette (use a subagent in the background)
Ask for 30–40 plants, mostly native, grouped as: accent trees, screening shrubs, low tidy plants near water or walks, pollinator meadow, shade understory, and groundcovers. For each plant get: botanical and common name, native yes/no, height × width, sun, salt and drought tolerance, debris near pools, toxicity and thorns, bloom, container size and spacing.

Sources: UF/IFAS Florida-Friendly Landscaping Guide (2022), FNPS plant pages (`fnps.org/plant/genus-species`), the FISC invasive list, and the USDA hardiness zone for the site ZIP code (look it up, e.g. via phzmapi.org).

Rules that held up in the Sample Community project:
- **Near pools:** use evergreen plants that don't fruit. Male dwarf yaupon 'Schillings', dwarf Fakahatchee, muhly, Elliott's lovegrass and twinflower work well.
- **Coontie:** leave it out where kids or dogs are around; the seeds are very toxic.
- **Thorns and spines:** keep saw palmetto at least 5 ft from walks, and skip wild lime, yucca and needle palm.
- **Native forms only:** buy native blue porterweed (*Stachytarpheta jamaicensis*), not the upright nursery types. Use only the red native firebush.
- **Bees and toxic plants:** keep bee-heavy and toxic plants (horsemint, milkweed) away from gates and the dog area.
- **Wildflower distance:** start wildflowers 8–14 ft from the pool fence. Keep fruiting shrubs (firebush, beautyberry, viburnum) 20–30 ft out, and no new trees within 20 ft.
- **Climb-free strip:** put a 3 ft crushed-stone strip at the pool fence. Stone doesn't float into the pool like mulch, and the strip keeps shrubs from becoming footholds.

## Layout engine (Python + shapely)
Work in the deck-aligned frame from `feat.json`. Install the tools with `pip install --break-system-packages shapely numpy`.
1. **Hardscape:**
   - Deck, walks and the kiosk walk as polygons.
   - Nature path as a Catmull-Rom spline through waypoints, buffered to 4 ft, with 12–13 ft round bench nodes.
   - Spurs drawn without clipping to the parcel so they reach walks in the right-of-way.
   - Keep paths at least 10–12 ft from big tree trunks and at least 6 ft from palms.
2. **Plantable area:** start with the parcel plus soft street-edge extensions, then subtract:
   - hardscape
   - deck buffered 3 ft
   - every spur or pad, so no path runs through plants
   - maintenance strips
   - lawn areas
   - tree and palm trunk rings
3. **Pool band:** deck buffered about 11 ft with a wavy edge (two sine terms). Use a 3 ft groundcover ribbon next to the fence strip, then alternating low drifts.
4. **Drifts:**
   - Seed the field with Poisson-disk points about 8 ft apart.
   - Build `voronoi_diagram` cells, and assign species by zone rules (hammock, frontage, meadow and so on) with weights, so neighbors don't repeat.
   - Merge same-species cells, then shrink and round them (buffer −0.45, then +0.25).
5. **Plant counts:** place points on a hex grid at each species' spacing inside each drift. Counts come straight from the points. Add individual shrubs and trees as explicit points.
6. **Street safety:** keep a corner sight triangle with plants under 30 in.

## Irrigation design (retrofit drip)
- Split zones by hydrozone and exposure, such as pool band halves, shade hammock, meadow and frontage.
- Use inline drip at 0.6 gph every 12 in, rows 18 in apart (about 0.64 in/hr). Compute area → tubing ft → gpm, and keep each zone at or under 12 gpm.
- Put valve boxes and the branched mainline in the fence strip, with a bore under concrete walks. Use poly headers.
- Place sleeves wherever a header crosses the path: intersect the header lines with the path polygon.
- Florida rules to cite:
  - **Water management district watering rules (example: SJRWMD):** micro-irrigation may run any time. Spray zones are limited to set days, ¾ in and 1 hour per zone, and nothing between 10 a.m. and 4 p.m. New plantings get 60 days of establishment watering.
  - **Water shortage:** check your water management district for current restrictions.
  - **Rain shutoff:** F.S. 373.62 requires one on automatic systems.
  - **HOA rules:** F.S. 373.185 says an HOA can't prohibit Florida-Friendly Landscaping.
  - **Fertilizer:** check your county/city fertilizer ordinance; many Florida counties ban N and P June 1–Sept 30.

## Drawing style (SVG)
Take cues from professional plans:
- Light paper background, existing canopies drawn hatched with an X at the trunk, and palms as frond strokes.
- Drifts as tinted fills with plant-symbol circles, and grasses as starbursts.
- Code-and-count tags on each drift. Italic botanical names in label columns on both sides, with leaders whose label heights follow the anchor heights.
- Zone names in spaced capitals, a scale bar, a north arrow rotated to the frame, and a legend.

The irrigation plan reuses the base drawing with plants muted, plus zone-colored drip hatching, dashed headers, the mainline, sleeves, valve boxes, flush valves and zone badges.

Construction details are hand-coded SVG sections:
- path (typical and no-dig under the oak)
- pool edge band
- drip valve assembly
- inline drip grid
- sleeve

Keep callout text inside the frame (right-anchor notes near the edge) and render them once to check.

## Interactive plan
Wrap every drift, shrub, tree and feature in `<g class="hit" data-k="p:CODE|f:id" data-n data-z data-y>`. Set `pointer-events:none` on labels, leaders, canopy hatching and the big future-canopy rings, and give tree trunks a small invisible hit circle.

Embed a JSON lookup with plants (names, size and price, spacing, mature size, totals, notes) and features (title and description). On click:
- Show a card (absolute on desktop, static below the map on phones).
- Add `focus` to the SVG and `same` to every group with that key, so other species dim to about 0.28 opacity.
- Highlight the selection with a drop-shadow filter.
- Clear on Esc, the × button, or a click on empty space.

## Deliver as an HTML artifact
Run the Artifact quickstart, then build one self-contained HTML page arranged as a drawing set:
- title block and sheet navigation chips
- key-number stats and concept cards
- L-1 planting plan (zoom Fit / 2× / 3×)
- L-2 plant schedule (drawn and buy quantities, size and price, notes)
- L-3 path
- I-1 irrigation plan and I-2 zones and schedule
- B-1 phased buildout
- D-1 details
- N-1 notes, field-verify list and sources

Keep the drawings on fixed light "paper" in both themes, and theme the page chrome with tokens. Use Newsreader for display text and Archivo for body text.

Before every publish, render with Playwright (Chromium is preinstalled). Check scroll width at 400 px, crop and inspect regions, and script a few clicks. Republish to the same file path to keep the URL. Each time the client points something out (a path through plants, a misplaced kiosk), fix the geometry at its source and re-verify it in code; don't just patch the drawing.
## Reference code (start here, don't rebuild)
`references/project-code/` holds the complete working build from the Sample Community project: layout engine, renderer, irrigation, details, interactive page builder, phasing, scheduler and year renders. Read `references/project-code/README.md` first for the module map, run commands, how to adapt it to a new site, and gotchas. Copy the folder into the working directory, replace the site data and palette, run `python3 build.py`, then check with `fullshot.py` and `shot.py` before publishing.
