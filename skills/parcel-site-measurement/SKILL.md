---
name: "parcel-site-measurement"
description: "Measure a property for a Florida-Friendly landscape design project from a Florida county GIS map viewer (e.g. a Florida county property appraiser's GIS viewer): parcel lines, aerial features, scale, and cross-checks with site video."
---

# Parcel site measurement from county GIS

Use this skill when a design project (landscape, path, irrigation, structure) needs real dimensions and the person points you at a county property-appraiser map, such as your county property appraiser's GIS viewer (BCPAO in Brevard, OCPA in Orange, HCPA in Hillsborough, and so on), or any ArcGIS JS 3.x MapView. The goal is a set of feature coordinates in real feet that later design code can use, plus a plain list of what still needs field verification.

## 1. Open the map in the person's browser
- Open the link in the built-in browser (read that skill first), then tell the person what you see and let them navigate or turn on the measuring tool if they want to.
- Don't rely on the on-screen measure tool or the scale bar if the page exposes the map object. Reading the geometry directly is faster and more exact.

## 2. Pull the parcel geometry straight from the map object
ArcGIS JS 3.x viewers expose a global `map`. Run in the page:
```js
const g = map.graphics.graphics[0].geometry;   // highlighted parcel(s)
({sr: map.spatialReference.wkid, rings: g.rings.map(r => r.map(p => [+p[0].toFixed(2), +p[1].toFixed(2)]))})
```
- Many Florida counties (BCPAO is one example) use WKID 2881 (NAD83 HARN Florida East, **US survey feet**), so coordinates are already in feet. Always check the WKID for your county.
- A link may highlight several parcels as separate rings. Ask which one is the subject parcel (e.g. "the southeast one").
- Work in local coordinates by subtracting a round origin (e.g. E-758000, N-1418550).

## 3. Get clean aerial imagery with a measuring grid
The tiled map is awkward to measure on. Fetch the aerial MapServer `export` endpoint for any bounding box and draw it on a full-screen canvas with the parcel line and a labeled grid:
```js
// Example host and service name from one county (BCPAO); find your county's aerial MapServer in the viewer's network requests.
const u = `https://www.bcpao.us/arcgis/rest/services/Brevard_Aerials_${year}/MapServer/export?dpi=96&format=png24&bbox=${xmin},${ymin},${xmax},${ymax}&bboxSR=2881&imageSR=2881&size=${w},${h}&f=image`;
```
- Retry on 403s. The server rate-limits bursts, so wait about 700–900 ms between tries.
- Draw grid lines every 5 or 10 ft in local coordinates and the parcel ring in red. Zoom to about 7–12 screenshot px per ft for features.
- Brighten with a gamma curve (around 0.5–0.6) to see under tree shadows.
- **Try other aerial years.** Which years respond varies by county (in the BCPAO example only 2025 and 2026 did). A different sun angle or season can reveal curbs, walks and pads hidden under canopy in the newest image.
- Resize the browser viewport (for example to 1100×900) so screenshots map cleanly, and reset it to the desktop preset when done.

## 4. Measure features
- **Automatic shapes:** for strongly colored features (pool water, light concrete deck), pull the export image into a canvas, threshold the pixels, keep the largest connected component, and fit a minimum-area rotated rectangle. That gives length, width, angle and corners. In the Sample Community example the fenced deck came out 82.1 × 41.7 ft against an owner estimate of 80 × 45 ft.
- **Manual features** (palms, tree canopies, trunks, walks, utility boxes, curbs): read their positions off the gridded screenshot. Note which are uncertain.
- **Shadows:** work out the sun direction from building shadows so you don't confuse a palm's shadow with its crown.
- **Overlay check:** draw your fitted shapes back onto the live map with `map.graphics.add(new esri.Graphic(...))` and screenshot it. Ask the person to confirm, e.g. "is the purple outline the no-plant zone?"

## 5. Build a design frame
If the main structure (pool deck, building) is rotated, define a frame aligned to it: origin at one corner, X along the long side, Y along the short side.
```python
def T(p):  # local state-plane ft -> design frame
    d = (p[0]-C[0], p[1]-C[1]); return (d[0]*L[0]+d[1]*L[1], d[0]*S[0]+d[1]*S[1])
```
Check the frame is right-handed (cross product positive) so the drawing isn't mirrored. Compute true north in the frame for the north arrow. Save everything to `feat.json` with the parcel ring, deck, pool, trees, palms and utilities. Lot lines often turn out orthogonal to the structure, which simplifies layout.

## 6. Cross-check with site video and photos
People often share a phone video (Google Photos links embed a YouTube player).
- Open it in the browser. Click the video, press `0` to jump to the start, and press `k` to play or pause. Take zoomed screenshots every second or so.
- **Rewatch the first seconds on purpose.** Playback starts before your first capture, and the person often frames the key view there.
- Look for things the aerial can't show: whether sidewalks exist (often lawn runs to the curb), mail kiosks, gates, equipment-room vents and doors, small trees, fence type, existing irrigation heads, and how close neighbor walls sit to the line (zero-lot-line houses).
- Reconcile with the aerial: the aerial gives scale and position, the video gives identity and relative placement. Use known object sizes, such as a cluster mailbox unit about 30 in wide.
- Ask for one or two tape measurements for anything still uncertain, and update right away when the person gives ground truth (for example "oak trunk is 5 ft behind the kiosk").

## 7. Report accuracy honestly
Tell the person which features are firm and which are estimated:
- **Firm (±2 ft):** parcel lines from GIS, and anything measured straight off the aerial.
- **Estimated (±5 ft):** features hidden under canopy and placed from video.

List the items to field-verify before bids. Mention right-of-way permits and calling 811 whenever work extends past the property line.
## Reference files
- `references/gis-snippets.js` has ready-to-run browser snippets: read parcel geometry, show the aerial overlay with a grid (`showAerY`), auto-fit the pool or deck (`fitShape`), draw a confirmation overlay, and video controls.
- The design-frame transform and feature export live in `${CLAUDE_PLUGIN_ROOT}/skills/native-landscape-plan/references/project-code/geo.py` (with example output in `feat.json`).
