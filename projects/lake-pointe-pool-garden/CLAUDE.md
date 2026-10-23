# Lake Pointe Pool Garden

Florida-Friendly native planting plan for the Lake Pointe HOA pool garden (Melbourne, FL). Python builds one interactive HTML plan set (planting, irrigation, phasing/budget, details, notes). Published as a claude.ai artifact: https://claude.ai/artifact/QqpcZy8mpjA3H969hvnmDa

Read this file and README.md (module map) instead of opening the 220 KB built page.

## Rebuild and check
```bash
pip install --break-system-packages -q shapely numpy
cd projects/lake-pointe-pool-garden
python3 build.py     # writes lake-pointe-pool-garden.html and renders/<hash>.svg
python3 checks.py    # last line must be ALL PASS
```
`python3 fullshot.py 1280 full.png` and `shot.py` give screenshots for visual checks.

## Publishing
Publish `lake-pointe-pool-garden.html` as `index.html` plus `renders/*.svg` (same artifact URL). Drop stale renders (hashes no longer produced by the build) by passing null for them. Never publish before checks.py says ALL PASS.

## Which file controls what
| Topic | Where |
|---|---|
| Site features (parcel, pool, palms, oak, kiosk) | `site_corrections_ft.json`, `feat.json`; `layout.py` SC, CABBAGE, PALMS, REMOVE |
| Nature path and benches | `layout.py` path_way, N1-N3, NODE_R, _benches() |
| Pool fence strip and pool band | `layout.py` rock, PALM_ROCK, band_outer |
| Beds, drift zones, plant mix | `layout.py` zone_of(), WEIGHTS, HAMMOCK_OUTER, palm rings PALM_BED |
| Plant palette | `layout.py` PAL |
| Page notes and click info | `build.py` NOTES, PINFO (features), GROUPS |
| Prices | `prices.py` PLANT, SPREAD (coontie ZI is $0, donated; LS, OC, RF are estimates, verify) |
| Irrigation | `irrigation.py` |
| Phasing and budget | `phasing.py`, `schedule.py`, `budget_section.py` |
| Drawing | `render.py`; `compose.py` leaders and callouts; `phase_render.py` per-year renders |
| Construction details | `details.py`, `details.css` |
| Checks | `checks.py` |
| Styling and zoom | `tokens.css`, `zoom.css`, `zoom.js` |

## Standing rules
- No plant symbols overlap.
- checks.py must pass before publishing.
- All 6 cabbage palms stay; the fence strip bends around them.
- Coontie is toxic: keep at least 15 ft from the pool gate and 20 ft from the dog lawn.
- No salt exposure on this site.
- Layout uses seeded randomness (seed 7). Geometry edits can reshuffle drift species and counts, so recheck counts (and checks.py) after any edit.
- build.py page HTML is an f-string: double every `{` `}` in CSS and JS.

## Current plan
Path reroutes, one bench per node, no overlapping plants, oak hammock ferns, pinkscale blazing star (LS), all cabbage palms kept, donated coonties.
