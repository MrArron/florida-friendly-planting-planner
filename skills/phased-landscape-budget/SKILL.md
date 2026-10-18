---
name: "phased-landscape-budget"
description: "Turn a Florida-Friendly landscape design into a priced, year-by-year phased buildout under an annual budget, with local nursery prices, labor allowances and a top-down render of each year."
---

# Phased landscape budget and renders

Use this skill after a plan exists (see `native-landscape-plan`) when the client gives an annual budget, such as "no more than $2,500/year", and wants a phased plan with renders.

## Gather prices (run two subagents in the background at the same time)
1. **Nursery plant prices.** Find a local native plant nursery with online prices and stock (the FANN directory or PlantRealFlorida.org can help locate one).
   - Search the nursery's online inventory by common and botanical names, and include out-of-stock items if the shop allows, noting that their prices may be older.
   - Illustrative example prices from Oct 2026, which must be re-priced locally: most native perennials come as 6 in pots ($7.99–9.99), with 4 in pots ($3.98–4.99) in spring. Shrubs are 3 gal ($17–30). Live oak is 15 gal $179 or 30 gal $356, with no 45 gal.
   - Record the source URL and stock status for each.
2. **Materials.** Ask for limestone screenings and #57 or #89 per ton, edging per lf, geocell, fabric, bulk mulch, rain sensor, valve boxes, drip tubing, benches, arborist rates, and right-of-way permit fees. Mark estimates as estimates.
   - Many Florida counties offer free mulch from the county landfill or solid waste program (confirm eligibility, including for HOAs).

## Cost levers that keep the look
- Plant spreading wildflowers and groundcovers at about half the drawn density. Show both "drawn" and "buy" quantities in the plant schedule.
- Smother turf under donated cardboard and free mulch.
- Use #57 limestone for the fence strip and compacted limestone screenings for paths (a binder can be added later).
- Use poly drip headers, and slow-release watering bags for new trees instead of bubbler zones.
- Buy 15 gal trees.
- Offer benches and trees as sponsorships.
- Exclude anything the client says is covered elsewhere. Sample Community has a contracted irrigation vendor, so keep vendor items in the schedule as zero-cost "vendor" lines and still show what to install when.

## Labor allowances
Use these when the person asks to include labor:
- **Planting:** $3.00 per 4 in pot, $3.50 per 6 in pot, $10 per 3 gal, $25 per 7 gal, $100 per 15 gal.
- **Path:** $2.50 per sq ft to excavate, set edging, and place and compact screenings.
- **Volunteer by default:** turf smothering, mulching and the fence strip.

Published per-plant labor guides vary wildly, so say these are allowances and suggest getting a local quote. Also show a table of who does the work (hire both, hire one, all volunteer) with years and totals. It's the biggest lever on the timeline.

## Scheduler (Python)
- **Work packages:** one per irrigation zone or area, in a sensible order:
  1. trees first, since they need the most time
  2. the entry
  3. the pool band
  4. shade garden, then meadow, then butterfly garden
  5. the loop closure
  6. extras such as a dog area
- **Items in each package:** infrastructure first (mainline segment, drip kit, header, sleeves, fence strip, path), then plants split into "structure" (3 gal and up) and "perennials".
- **Pricing:** apply an 8% contingency to every purchase and 3% escalation per year (`cost × 1.03^(year−1)`). Reserve arborist visits for young trees in years 2, 4 and 6.
- **Packing:** fill each year up to the budget.
  - Infrastructure items are atomic, except path work over about $1,100, which is pre-split into parts.
  - Plant groups can split across years. If a group is within about 12% of fitting, buy what fits and let spreaders cover the gap; never leave 2% slivers.
  - Look ahead within the same package (or a bed start in the next one) to fill leftover budget.
  - Never pull zero-cost vendor items years ahead of planting.
  - Guard against infinite loops when an item exceeds the budget.
- **Output:** a list of years, each with items `{wp, kind, cat, desc, cost, frac}`, plus `state_after(k)` for renders.

## Per-year top-down renders
- Use a separate SVG renderer with fixed colors and its own turf pattern; CSS variables are undefined outside the page.
- **Base:** road, curb, neighbor lots and simple roofs, deck and pool. Draw beds as brown mulch only once their package's bed prep or drip is done. Add the fence strip, path pieces and benches as each is built.
- **Plants:** order each package's points by a hash of the drift so whole drifts appear together. Reveal them by the cumulative fraction bought, tagged with purchase year.
- **Growth:** scale size with age, perennials `min(1, .55+.25·age)` and shrubs `min(1, .5+.17·age)`. New oak canopy radius is `4.5 + 1.5·age` ft, capped at the managed size.
- Draw existing big canopies semi-transparent (about 0.4 opacity) so gardens under them stay visible.

## Page section (B-1 Phased buildout)
- A header line with years, cap and total.
- Intro text plus a "What the numbers assume" list: labor, vendor-covered items, plant price source and date, free mulch, cheaper hardscape, allowances, and what's not included (benches, permit fees, tools).
- An at-a-glance table (year, main work, spend, total) and a who-does-the-work table.
- A card per year: render, year, cost, running total, plain-language scope per package, and a collapsible line-item table.
- "Ways to finish sooner": dividing plants, seeding the meadow, nursery discounts, sponsorships, grants, confirming the free mulch.
- Sources with links.

After the person changes assumptions (exclude irrigation, add labor), rerun the schedule. Report the new year count and total, and point out anything odd, such as a final year with only a few hundred dollars.
## Reference code
The scheduler, prices, phasing, year renderer and B-1 section builder are in `${CLAUDE_PLUGIN_ROOT}/skills/native-landscape-plan/references/project-code/`, in `schedule.py`, `prices.py`, `phasing.py`, `phase_render.py` and `budget_section.py`. Copy and adapt them. Re-price `prices.py` and the `M` material table in `schedule.py` for each project, and set `BUDGET`, `PLANT_LABOR`, `PATH_LABOR_SF` and `ARBORIST` to the person's assumptions.
