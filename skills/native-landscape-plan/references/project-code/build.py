import math, json, html
from shapely.geometry import LineString
import layout as Lo, compose, irrigation as IR, details as D
import prices as PR, budget_section as BS, schedule as SCH

plant_svg = compose.plan_svg('plant')
irr_svg = compose.plan_svg('irr', IR.svg_overlay())
tokens = open('tokens.css').read().replace(':root{', '.sheet{').replace(':root{--main', '.sheet{--main')
dcss = open('details.css').read()

Q = dict(Lo.qty)
NOTES = {
 'QV':  'Future shade over the path, planted in year 1 in the right-of-way about 8 ft behind the curb and 38 ft from the pool fence, each in its own mulch bay. Watering bags for 8 months. An ISA-certified arborist keeps the canopy 10–15 ft off the fence.',
 'MFT': 'Shade for the NE lawn-overlook bench, about 28 ft from the fence and 20 ft from the neighbor line.',
 'MF':  'Evergreen privacy screen on the neighbor line. Clip at 7–9 ft. About 26 ft from the fence.',
 'VO':  'Loose clusters on the south-street side, about 30 ft from the fence. White spring flowers.',
 'HP':  'Hummingbird plant. Kept outside the path, 20 ft or more from the fence. May die back in a freeze, then regrows.',
 'AE':  'Evergreen understory under the oak.',
 'CA':  'Oak-hammock edge only, about 30 ft from the pool. Drops leaves in winter; berries feed birds.',
 'SR':  'Interior of the hammock, at least 5 ft from any walk (leaf stems have saw teeth).',
 'SB':  'Smooth-stemmed palmetto, safe beside walks. Shade tolerant.',
 'IVH': 'Low clipped edging on both sides of the concrete entry walk.',
 'IV':  'Male clone, so no berries. The workhorse shrub next to the pool.',
 'PN':  'Glossy shade shrub. Can be hurt by frost; plant in spring.',
 'TF':  'Tidy clumping grass. Cut back once in late winter.',
 'MC':  'Pink plumes in October and November.',
 'EE':  'Fine silver-blue grass, low debris.',
 'GP':  'Long bloom season, reseeds.', 'CL': 'State wildflower genus, self-seeds.',
 'MP':  'Pink bracts, very popular with bees.', 'SC': 'Hummingbird plant, reseeds.',
 'SJ':  'Buy the native low form only (not the upright nursery types).',
 'AT':  'Monarch host. Sap is toxic, so it is kept in the meadow, away from the pool.',
 'LS':  'Late-summer purple spikes.', 'RH': 'Short-lived; let it reseed.',
 'SS':  'Fall gold. Spreads, so it is kept in the SE garden.',
 'DO':  'Low ribbon along the rock band. Buckeye butterfly host.',
 'MS':  'Low strip at the street edge. Needs edging to keep it in bounds.',
 'TK':  'Shade fern. Relies on drip.',
}
GROUPS = [
 ('Trees & large shrubs', ['QV', 'MFT', 'VO']),
 ('Accent & understory shrubs', ['HP', 'AE', 'CA', 'SR', 'SB', 'PN']),
 ('Pool band shrubs & grasses', ['IV', 'IVH', 'TF', 'MC', 'EE']),
 ('Wildflower meadow', ['GP', 'CL', 'MP', 'SC', 'SJ', 'AT', 'LS', 'RH', 'SS']),
 ('Groundcovers & fern', ['DO', 'MS', 'TK']),
]
def sched_rows():
    out = []
    for g, codes in GROUPS:
        out.append(f'<tr class="grp"><th colspan="8">{g}</th></tr>')
        for c in codes:
            b, com, nat, cont, sp, size, col, kind = Lo.PAL[c]
            spc = '—' if not sp else (f'{sp:g} ft' if c not in ('IVH',) else f'{sp:g} ft in row')
            buy = max(1, round(Q.get(c, 0)*PR.SPREAD.get(c, 1)))
            out.append(f'<tr><td><span class="sw" style="--c:{col}"></span><b class="code">{c}</b></td>'
                       f'<td><i class="bot">{html.escape(b)}</i><span class="com">{html.escape(com)}</span></td>'
                       f'<td class="num">{Q.get(c, 0)}</td><td class="num">{buy}</td><td>{html.escape(PR.PLANT[c][1])} · ${PR.PLANT[c][0]:.2f}</td><td>{spc}</td><td>{html.escape(size)}</td>'
                       f'<td class="note">{html.escape(NOTES[c])}</td></tr>')
    return '\n'.join(out)

tot_plants = sum(Q.values())
by_cont = {}
for c, n in Q.items():
    k = Lo.PAL[c][3].split(',')[0]
    by_cont[k] = by_cont.get(k, 0) + n

zones = IR.zones
hdr_len = sum(LineString(h).length for hs in IR.HEAD.values() for h in hs)
zone_rows = '\n'.join(
    f'<tr><td><span class="zb" style="--c:{z["color"]}">{z["z"]}</span></td><td><b>{z["name"]}</b><span class="com">{z["plants"]}</span></td>'
    f'<td>{z["expo"]}</td><td class="num">{z["area"]:,}</td><td class="num">{int(z["tube"]):,}</td><td class="num">{z["gpm"]}</td>'
    f'<td class="num">{z["valve"]}</td><td class="num">{z["gal"]:,.0f}</td></tr>' for z in zones)
tube_tot = sum(z['tube'] for z in zones if z['tube'])

A = Lo.area
stats = [
  (f'{A["parcel"]:,.0f}', 'sq ft parcel', f'{A["parcel"]/43560:.2f} acre'),
  (f'{A["beds"]:,.0f}', 'sq ft new beds', 'turf converted to natives'),
  (f'{A["path_len"]:.0f}', 'ft nature path', '4 ft wide, permeable, 3 rest nodes'),
  (f'{tot_plants:,}', 'plants', '24 species, all Florida natives'),
  (f'{len(SCH.YEARS)} yrs', 'phased buildout', f'≤ ${SCH.BUDGET:,.0f}/year · ≈${sum(y["spent"] for y in SCH.YEARS):,.0f} total'),
]
stat_html = ''.join(f'<div class="stat"><b>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in stats)
det_html = ''.join(f'<figure class="det">{fn()}</figure>' for fn in D.ALL)

# ---- data for the clickable planting plan
import json
drift_count = {}
for d in Lo.DRIFTS: drift_count[d['code']] = drift_count.get(d['code'], 0) + 1
for c, x, y in Lo.ind: drift_count[c] = drift_count.get(c, 0) + 1
for c, x, y, r in Lo.ROW_TREES: drift_count[c] = drift_count.get(c, 0) + 1
PINFO = {'plants': {}, 'features': {}, 'zones': {str(z['z']): z['name'] for z in IR.zones}}
for c, v in Lo.PAL.items():
    if c not in Q: continue
    PINFO['plants'][c] = dict(bot=v[0], com=v[1], native=v[2] == 'Y', size=PR.PLANT[c][1], price=PR.PLANT[c][0],
                              sp=v[4], mature=v[5], color=v[6], total=Q[c], buy=max(1, round(Q[c]*PR.SPREAD.get(c, 1))),
                              groups=drift_count.get(c, 0), note=NOTES[c])
PINFO['features'] = {
 'bed': ('Mulched bed', 'Free county mulch, 3 in deep, over drip irrigation. Tap a plant drift for details.'),
 'doglawn': ('Dog rest lawn', 'Existing turf stays. The bench, pet-waste station and trash can are at the pad by the path. Kept back from the neighbors’ backyards.'),
 'maint': ('Neighbor maintenance strip', '5 ft of lawn along the zero-lot-line houses, with no plants and no emitters, so neighbors can set ladders and paint.'),
 'rock': ('Crushed-limestone strip', '3 ft wide along the pool fence: #57 limestone, 2½ in deep on fabric. Nothing climbable next to the fence, and it won’t float into the pool like mulch.'),
 'deck': ('Pool deck', 'Existing fenced deck, about 82 × 42 ft. No planting inside the fence.'),
 'pool': ('Pool', 'Existing pool. The plants nearest the fence are evergreen and set no fruit, to keep litter out of the water.'),
 'restroom': ('Restroom building', 'Existing. Keep the equipment-room door and vents on the street-facing wall clear.'),
 'walk': ('Existing concrete entry walk', 'Main entry from the west street. It stays as is, edged with clipped dwarf yaupon.'),
 'kioskwalk': ('Mail kiosk walk', 'Existing quarter-circle concrete walk from curb to curb. The nature path spur ties into it.'),
 'kiosk': ('Covered mail kiosk', 'Existing. The live oak trunk is about 5 ft behind it.'),
 'path': ('Nature path', f'4 ft wide, permeable: compacted limestone screenings with edging. About {Lo.path_line.length:.0f} ft loop plus the kiosk spur and street access. Built in stages; see sheet B-1.'),
 'bench': ('Bench', '6 ft recycled-plastic bench, about $600. A good candidate for sponsorship.'),
 'dogpad': ('Dog rest area pad', 'Limestone-screenings pad with a bench, reached by a short spur from the lawn-overlook node.'),
 'dogstation': ('Pet-waste station', 'Bag dispenser, sign and lidded trash can. Bagged waste keeps nutrients out of local waterways.'),
 'util': ('Existing utility structure', 'Ringed with dwarf Fakahatchee grass. The access side stays open.'),
 'oak': ('Existing live oak', 'Stays. Planting under it uses small containers, and the path there is built on top of grade with no digging (detail B).'),
 'southtree': ('Existing tree', 'Stays (verify whether it is on HOA land). Plants are kept 3 ft off the trunk.'),
 'smalltree': ('Existing small tree', 'Stays, at the restroom’s street-facing wall beside the entry walk.'),
 'palm': ('Existing sabal palm', 'Stays. Cut flower stalks in early summer before they fruit, to keep litter out of the pool.'),
}
pinfo_json = json.dumps(PINFO).replace('</', '<\\/')

page = f'''<title>Sample Community Pool Garden</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400;1,6..72,500&display=swap">
<style>
/* Layout: a landscape drawing set — title block, numbered sheets on light "paper", schedules beneath each sheet. */
:root{{
  --bg:#f3f3ee; --surface:#fffefa; --ink:#22281f; --muted:#5d6556; --line:#d6d9cc;
  --accent:#2f5d46; --accent2:#b9532f; --chip:#e7ebe0;
  --f-display:"Newsreader", Georgia, "Times New Roman", serif;
  --f-body:"Archivo", "Helvetica Neue", Arial, sans-serif;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141915;--surface:#1c221d;--ink:#e6eae0;--muted:#a2ab9a;--line:#2e372f;--accent:#93c7a6;--accent2:#e88c66;--chip:#253026;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141915;--surface:#1c221d;--ink:#e6eae0;--muted:#a2ab9a;--line:#2e372f;--accent:#93c7a6;--accent2:#e88c66;--chip:#253026;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:15px/1.55 var(--f-body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 64px}}
.wrap{{max-width:1240px;margin:0 auto}}
header.tb{{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:end;padding:40px 0 22px;border-bottom:2px solid var(--ink)}}
.eyebrow{{font:600 12px var(--f-body);letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}}
h1{{font:400 clamp(38px,6vw,64px)/1.02 var(--f-display);margin:.18em 0 .12em;text-wrap:balance;letter-spacing:-.01em}}
h1 i{{color:var(--accent)}}
.sub{{color:var(--muted);max-width:62ch;margin:0}}
.meta{{display:grid;grid-template-columns:auto auto;gap:4px 18px;font-size:12.5px;border:1px solid var(--line);padding:12px 16px;background:var(--surface);min-width:0}}
.meta dt{{color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-size:10.5px;padding-top:2px}} .meta dd{{margin:0;font-weight:600}}
nav.toc{{display:flex;flex-wrap:wrap;gap:8px;padding:16px 0 4px}}
nav.toc a{{font-size:12.5px;font-weight:600;letter-spacing:.05em;text-decoration:none;color:var(--ink);background:var(--chip);padding:6px 11px;border-radius:3px}}
nav.toc a:hover,nav.toc a:focus-visible{{background:var(--accent);color:var(--surface);outline:none}}
nav.toc a b{{color:var(--accent2);margin-right:6px}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0;margin:26px 0 8px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
.stat{{padding:14px 14px 14px 0;display:flex;flex-direction:column;gap:2px;min-width:0}}
.stat+.stat{{padding-left:14px;border-left:1px solid var(--line)}}
.stat b{{font:400 32px/1 var(--f-display);font-variant-numeric:tabular-nums}} .stat span{{font-weight:600;font-size:13px}} .stat small{{color:var(--muted);font-size:12px}}
section{{padding-top:44px}}
.sh{{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:16px;flex-wrap:wrap}}
.sh .no{{font:600 13px var(--f-body);letter-spacing:.12em;color:var(--surface);background:var(--ink);padding:3px 8px;border-radius:2px}}
h2{{font:400 30px/1.15 var(--f-display);margin:0;text-wrap:balance}}
h3{{font:600 13px var(--f-body);letter-spacing:.12em;text-transform:uppercase;margin:26px 0 10px;color:var(--accent)}}
p{{max-width:70ch}} .muted{{color:var(--muted)}}
.moves{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px 28px;margin-top:10px}}
.moves div{{min-width:0}} .moves h4{{font:500 19px/1.25 var(--f-display);margin:0 0 4px}} .moves p{{margin:0;color:var(--muted);font-size:14px}}
.sheet{{background:#fbfaf6;border:1px solid #c9cbbf;box-shadow:0 1px 0 rgba(0,0,0,.04);margin:0}}
.sheet-bar{{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #d9dacf;color:#2b2f2a;font-size:12px;flex-wrap:wrap;background:#f4f2ea}}
.sheet-bar b{{letter-spacing:.1em}}
.zoom{{display:flex;gap:4px}} .zoom button{{font:600 12px var(--f-body);border:1px solid #b9bcae;background:#fff;color:#2b2f2a;padding:4px 10px;border-radius:3px;cursor:pointer}}
.zoom button[aria-pressed="true"]{{background:#2b2f2a;color:#fff;border-color:#2b2f2a}}
.zoom button:focus-visible{{outline:2px solid #b9532f;outline-offset:1px}}
.scroll{{overflow:auto;-webkit-overflow-scrolling:touch;max-height:none}}
.scroll svg.plan{{display:block;width:100%;height:auto}}
.planwrap{{position:relative}}
svg.interactive .hit{{cursor:pointer}}
svg.interactive text, svg.interactive .leader, svg.interactive .canopy{{pointer-events:none}}
svg.interactive.focus .hit[data-k^="p:"]:not(.same){{opacity:.28}}
svg.interactive .hit.same{{filter:drop-shadow(0 0 1.5px #d9480f)}}
svg.interactive .hit.sel{{filter:drop-shadow(0 0 2px #d9480f) drop-shadow(0 0 4px #d9480f)}}
.pinfo{{position:absolute;top:12px;right:12px;width:min(300px,calc(100% - 24px));background:#fffef9;color:#22281f;border:1px solid #c9cbbf;border-radius:6px;box-shadow:0 6px 24px rgba(30,40,25,.18);padding:12px 14px;font-size:13px;line-height:1.45}}
.pinfo-hint{{margin:0;color:#5d6556}}
.pinfo h4{{margin:0;font:500 19px/1.2 var(--f-display);color:#22281f;display:flex;gap:8px;align-items:center}}
.pinfo .pi-bot{{font-family:var(--f-display);font-style:italic;color:#4b5244;margin:2px 0 8px}}
.pinfo .pi-sw{{width:14px;height:14px;border-radius:50%;flex:none;box-shadow:inset 0 0 0 1px rgba(0,0,0,.25)}}
.pinfo dl{{display:grid;grid-template-columns:max-content 1fr;gap:3px 10px;margin:6px 0}}
.pinfo dt{{color:#6a7262;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;padding-top:2px}} .pinfo dd{{margin:0;font-variant-numeric:tabular-nums}}
.pinfo .pi-note{{margin:6px 0 0;color:#3d4437}}
.pinfo .pi-close{{position:absolute;top:6px;right:8px;border:0;background:none;font-size:18px;line-height:1;color:#5d6556;cursor:pointer;padding:4px}}
.pinfo .pi-close:focus-visible{{outline:2px solid #b9532f}}
.pinfo .pi-chip{{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.04em;background:#e7ebe0;color:#2f5d46;border-radius:3px;padding:1px 6px;margin-right:4px}}
@media (max-width:720px){{.pinfo{{position:static;width:auto;margin:0;border-radius:0;border-width:1px 0 0;box-shadow:none}}}}
{tokens}
{dcss}
.legend{{display:flex;flex-wrap:wrap;gap:8px 22px;padding:10px 12px;border-top:1px solid #d9dacf;font-size:12px;color:#2b2f2a;background:#f4f2ea}}
.legend span{{display:inline-flex;align-items:center;gap:7px}}
.lg{{width:26px;height:12px;display:inline-block;border:1px solid #6b6f66;flex:none}}
.tablewrap{{overflow-x:auto;border:1px solid var(--line);background:var(--surface)}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;min-width:820px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
thead th{{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600;background:var(--surface);position:sticky;top:0}}
tr.grp th{{font:500 16px var(--f-display);color:var(--accent);padding-top:16px;background:var(--surface)}}
td.num{{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}}
td.note{{color:var(--muted);font-size:12.5px;max-width:34ch}}
.bot{{font-family:var(--f-display);font-size:15px;display:block}} .com{{display:block;color:var(--muted);font-size:12.5px}}
.sw{{display:inline-block;width:12px;height:12px;border-radius:50%;background:var(--c);margin-right:7px;vertical-align:-1px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.25)}}
.code{{font-size:12px;letter-spacing:.06em}}
.zb{{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--c);color:#fff;font-weight:700;font-size:12px}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px 34px}}
.cols>div{{min-width:0}}
ul.tight{{padding-left:18px;margin:6px 0}} ul.tight li{{margin:4px 0}}
.callout{{border-left:3px solid var(--accent2);background:var(--surface);padding:12px 16px;margin:16px 0}}
.callout p{{margin:4px 0}}
.dets{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:18px}}
figure.det{{margin:0;background:#fff;min-width:0}} figure.det svg{{display:block;width:100%;height:auto}}
.kv{{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;font-size:14px}} .kv dt{{color:var(--muted)}} .kv dd{{margin:0}}
.src a{{color:var(--accent);word-break:break-word}}
footer{{margin-top:48px;padding-top:14px;border-top:2px solid var(--ink);font-size:12.5px;color:var(--muted);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}}
@media (max-width:860px){{header.tb{{grid-template-columns:1fr}} .stats{{grid-template-columns:repeat(2,minmax(0,1fr))}} .stat+.stat{{border-left:0;padding-left:0}} .stat{{border-bottom:1px solid var(--line)}}}}

.years{{display:grid;gap:22px}}
.ycard{{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:20px;align-items:start;border-top:1px solid var(--line);padding-top:18px}}
.yrender{{margin:0;background:#fbfaf6;border:1px solid #c9cbbf}}
.yrender svg{{display:block;width:100%;height:auto}}
.yrender figcaption{{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#4b4f47;padding:6px 10px;background:#f4f2ea;border-top:1px solid #d9dacf}}
.ybody{{min-width:0}}
.yhead{{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:6px}}
.yno{{font:400 26px var(--f-display)}} .ycost{{font:600 18px var(--f-body);color:var(--accent);font-variant-numeric:tabular-nums}} .yrun{{color:var(--muted);font-size:13px}}
details{{margin-top:8px}} details summary{{cursor:pointer;font-weight:600;font-size:13px;color:var(--accent)}}
details summary:focus-visible{{outline:2px solid var(--accent2);outline-offset:2px}}
table.ytab{{min-width:0;font-size:12.5px}} tr.tot td{{font-weight:700;border-top:2px solid var(--ink)}}
@media (max-width:860px){{.ycard{{grid-template-columns:1fr}}}}
@media (prefers-reduced-motion:no-preference){{html{{scroll-behavior:smooth}}}}
</style>

<div class="wrap">
<header class="tb">
  <div>
    <div class="eyebrow">Sample Community HOA · Community pool grounds</div>
    <h1>Sample Community <i>Pool Garden</i></h1>
    <p class="sub">A native and Florida-Friendly landscape around the community pool. It adds a permeable nature walk that loops the pool enclosure, keeps low-litter planting at the fence, and puts every new bed on drip irrigation.</p>
  </div>
  <dl class="meta">
    <dt>Location</dt><dd>Example Rd &amp; Example Dr, Anytown FL</dd>
    <dt>Parcel</dt><dd>Parcel ID: XXXXXXX</dd>
    <dt>Climate</dt><dd>USDA zone 10a · sandy soil</dd>
    <dt>Phase</dt><dd>Concept design for client review</dd>
    <dt>Date</dt><dd>October 2026</dd>
  </dl>
</header>
<nav class="toc" aria-label="Sheets">
  <a href="#concept"><b>00</b>Concept</a><a href="#plan"><b>L-1</b>Planting plan</a><a href="#schedule"><b>L-2</b>Plant schedule</a>
  <a href="#path"><b>L-3</b>Nature path</a><a href="#irrigation"><b>I-1</b>Irrigation plan</a><a href="#irrsched"><b>I-2</b>Zones &amp; scheduling</a><a href="#budget"><b>B-1</b>Phased buildout</a>
  <a href="#details"><b>D-1</b>Details</a><a href="#notes"><b>N-1</b>Notes</a>
</nav>
<div class="stats">{stat_html}</div>

<section id="concept">
  <div class="sh"><span class="no">00</span><h2>Concept</h2></div>
  <div class="moves">
    <div><h4>Low litter at the fence</h4><p>No new trees within 20 ft of the deck. Next to the fence there is a 3 ft crushed-stone strip with nothing climbable, then a band of evergreen, non-fruiting natives (male dwarf yaupon, dwarf Fakahatchee, muhly, twinflower) that drop very little into the pool.</p></div>
    <div><h4>Taller and showier farther out</h4><p>Wildflowers start about 8–14 ft from the fence, and berry or flower shrubs (firebush, beautyberry, viburnum) sit 20–30 ft out. The existing palms stay, and their flower stalks get cut before they fruit.</p></div>
    <div><h4>A walk through the garden</h4><p>A compacted limestone-screenings loop of about 375 ft branches off the existing concrete walk, which stays the main entry. It circles the enclosure, links to the mail kiosk and to the south street, and passes three bench nodes: under the oak, in the butterfly garden, and at the lawn overlook.</p></div>
    <div><h4>A soft street edge</h4><p>Along both streets the beds leave the straight property line and drift 2–6 ft into the right-of-way lawn in loose curves. They swell out around each new oak, so every tree sits in its own mulch bay. At least 4 ft of lawn stays at the curb.</p></div>
    <div><h4>Work with the oak</h4><p>The northwest corner becomes a shade hammock of wild coffee, ferns, marlberry and palmettos. Under the canopy the path is built on top of grade with no excavation (detail B), and plants go in as small containers.</p></div>
    <div><h4>Open to the neighbors</h4><p>No screening hedges, so the houses next door look out onto low grasses and wildflowers. Their walls sit on the zero-lot line, so a 5 ft strip of lawn with no plants and no emitters runs along both neighbor sides. That leaves room for ladders and painting. The east extension behind the backyards stays lawn, with a low grass ring around the utility structure.</p></div>
    <div><h4>A dog rest lawn</h4><p>A short spur from the lawn-overlook bench leads to a small pad on the east lawn with a bench, a pet-waste station and a trash can. The lawn itself stays as existing turf. Bagged pet waste keeps nutrients out of local waterways. Butterfly milkweed, which is toxic to dogs, is kept in the meadow far from this end.</p></div>
    <div><h4>Shade for the future</h4><p>Five Southern live oaks go in the right-of-way lawn on the street side of the path, three on the south street and two on the west street. In 15–20 years they'll shade the walk. An arborist prunes them to keep the canopy 10–15 ft off the pool fence.</p></div>
    <div><h4>Drip, not spray</h4><p>Seven new drip zones tap the existing supply. The new oaks get slow-release watering bags while they establish. Drip keeps water off the deck, the path and the street, and under SJRWMD rules it can run on any day.</p></div>
  </div>
</section>

<section id="plan">
  <div class="sh"><span class="no">L-1</span><h2>Planting plan</h2><span class="muted">Drawn square to the pool deck. True north points to the upper left. Tap anything on the plan to see what it is.</span></div>
  <figure class="sheet" data-zoom>
    <div class="sheet-bar"><b>SHEET L-1 · PLANTING PLAN</b><span>Measured from county GIS · ±2 ft · field-verify before construction</span>
      <div class="zoom" role="group" aria-label="Zoom"><button type="button" data-z="1" aria-pressed="true">Fit</button><button type="button" data-z="2" aria-pressed="false">2×</button><button type="button" data-z="3" aria-pressed="false">3×</button></div></div>
    <div class="planwrap">
      <div class="scroll">{plant_svg}</div>
      <aside class="pinfo" id="pinfo" aria-live="polite">
        <p class="pinfo-hint">Tap any plant, tree or feature on the plan to see what it is. Every drift of the same plant lights up.</p>
      </aside>
    </div>
    <div class="legend">
      <span><i class="lg" style="background:#e8d6b0"></i>Nature path · limestone screenings</span>
      <span><i class="lg" style="background:#e6e4de"></i>Crushed-limestone strip (3 ft, climb-free)</span>
      <span><i class="lg" style="background:repeating-linear-gradient(45deg,#fff 0 3px,#9aa39a 3px 4px)"></i>Existing canopy to remain</span>
      <span><i class="lg" style="background:#e3ecd2"></i>Existing lawn to remain (incl. 5 ft neighbor maintenance strips)</span>
      <span><i class="lg" style="background:#efe5d3"></i>Mulched bed</span>
      <span><i class="lg" style="border:2px dashed #a2553a;background:none"></i>Parcel line</span>
      <span><i class="lg" style="border:1px dashed #b5462f;background:none"></i>Corner sight triangle</span>
    </div>
  </figure>
</section>

<section id="schedule">
  <div class="sh"><span class="no">L-2</span><h2>Plant schedule</h2><span class="muted">{tot_plants:,} plants. All 24 species are Florida natives, and none is on the FISC invasive list.</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>Code</th><th>Plant</th><th style="text-align:right">Drawn</th><th style="text-align:right">Buy</th><th>Size · price</th><th>Spacing (on center)</th><th>Mature H × W (ft)</th><th>Placement notes</th></tr></thead>
    <tbody>{sched_rows()}</tbody></table></div>
  <div class="cols" style="margin-top:20px">
    <div><h3>Order summary</h3><dl class="kv">{''.join(f'<dt>{k}</dt><dd>{v:,} plants</dd>' for k, v in sorted(by_cont.items(), key=lambda kv: -int(kv[0].split()[0])))}
      <dt>Mulch</dt><dd>≈{A["beds"]*0.25/27:.0f} cu yd, 3 in deep. Free shredded mulch from your county landfill or solid waste program (confirm eligibility), not nuggets, which float.</dd>
      <dt>Fence strip</dt><dd>≈{A["rock"]:.0f} sq ft of #57 crushed limestone, 2½ in deep, on fabric</dd></dl></div>
    <div><h3>Why these near the pool</h3><ul class="tight">
      <li><b>Male dwarf yaupon</b> and <b>dwarf Fakahatchee</b> are evergreen, set no fruit, and drop almost nothing.</li>
      <li><b>Coontie was left out</b> on purpose. Its seeds are highly toxic to children and dogs.</li>
      <li>Thorny or spiny natives (wild lime, yucca, needle palm) are not used. <b>Saw palmetto</b> sits 5 ft or more back from walks.</li>
      <li>Bee-heavy bloomers (horsemint, sunshine mimosa, milkweed) are 15 ft or more from the gate and off the barefoot route.</li>
      <li>Keep the existing sabal palms, and cut their flower stalks in early summer before they set black fruit.</li></ul></div>
  </div>
</section>

<section id="path">
  <div class="sh"><span class="no">L-3</span><h2>Nature path</h2><span class="muted">Permeable, firm, and kind to bare feet.</span></div>
  <div class="cols">
    <div><dl class="kv">
      <dt>Length</dt><dd>{Lo.path_line.length:.0f} ft loop, a {Lo.spur_line.length:.0f} ft spur to the mail-kiosk walk, and a street access to the south-street curb near the south corner</dd>
      <dt>Width</dt><dd>4 ft, with 12–13 ft round rest nodes and 2 benches at each</dd>
      <dt>Surface</dt><dd>Crushed limestone screenings, 3 in compacted on sand, ≈{A["path"]:,.0f} sq ft. It drains and packs firm enough for strollers. An organic stabilizer binder can be added later to make it firmer still.</dd>
      <dt>Edging</dt><dd>≈{Lo.path_poly.boundary.length:,.0f} lf of 3/16 × 4 in aluminum</dd>
      <dt>Connections</dt><dd>Leaves the concrete walk 10 ft and 22 ft from the gate, so loose grit is scuffed off on concrete before it reaches the deck. The south-street access crosses the right-of-way lawn, so check with the county about work in the right-of-way, and finish it with a short concrete landing at the curb.</dd>
    </dl></div>
    <div><h3>Why not shell or mulch?</h3><p class="muted" style="margin-top:0">Crushed shell is the classic Florida path, but it is sharp on bare feet and tracks into a pool. A mulch trail is cheaper but floats, washes out, and needs topping up every year. Stabilized fines cost more up front and need the least care. Pine-straw "mulch paths" would also work as a lower-cost first phase.</p>
    <p class="muted">Inside the oak's drip line, and within 10 ft of the existing palms, the path uses the no-dig build-up in detail B instead of the typical section in detail A.</p></div>
  </div>
</section>

<section id="irrigation">
  <div class="sh"><span class="no">I-1</span><h2>Irrigation plan</h2><span class="muted">A retrofit off the existing supply. New lines run in the rock band, and the headers cross the path inside sleeves.</span></div>
  <figure class="sheet" data-zoom>
    <div class="sheet-bar"><b>SHEET I-1 · IRRIGATION PLAN</b><span>Schematic routing · locate the existing main and controller before trenching</span>
      <div class="zoom" role="group" aria-label="Zoom"><button type="button" data-z="1" aria-pressed="true">Fit</button><button type="button" data-z="2" aria-pressed="false">2×</button><button type="button" data-z="3" aria-pressed="false">3×</button></div></div>
    <div class="scroll">{irr_svg}</div>
    <div class="legend">
      <span><i class="lg" style="height:4px;background:#1f4e79;border:0"></i>New 1" Sch 40 PVC mainline (in the fence strip)</span>
      <span><i class="lg" style="height:0;border:0;border-top:3px dashed #d08a2a"></i>Zone header, 1" poly pipe (zone color)</span>
      <span><i class="lg" style="background:repeating-linear-gradient(0deg,rgba(47,156,143,.15) 0 4px,#2f9c8f 4px 5px)"></i>Inline drip grid, 18 in rows</span>
      <span><i class="lg" style="background:#fff;border:3px solid #2b2f2a"></i>2" sleeve under path</span>
      <span><i class="lg" style="background:#fff;border-radius:2px"></i>Valve box (A–D)</span>
      <span><b style="font-size:11px">F</b>&nbsp;Flush valve</span><span><b style="font-size:11px">C</b>&nbsp;Controller</span><span><b style="font-size:11px">R</b>&nbsp;Rain / soil sensor</span>
    </div>
  </figure>
</section>

<section id="irrsched">
  <div class="sh"><span class="no">I-2</span><h2>Zones &amp; scheduling</h2><span class="muted">0.6 gph emitters every 12 in, rows 18 in apart. That applies ≈{IR.PR:.2f} in/hr, so ½ in takes about {zones[0]["mins"]} minutes.</span></div>
  <div class="tablewrap"><table>
    <thead><tr><th>Zone</th><th>Area &amp; plants</th><th>Exposure</th><th style="text-align:right">Sq ft</th><th style="text-align:right">Drip tubing (ft)</th><th style="text-align:right">GPM</th><th style="text-align:right">Valve box</th><th style="text-align:right">Gal per ½ in</th></tr></thead>
    <tbody>{zone_rows}</tbody></table></div>
  <div class="cols" style="margin-top:18px">
    <div><h3>Run schedule</h3>
      <div class="tablewrap"><table style="min-width:0">
        <thead><tr><th>Period</th><th>Zones 1, 3, 4, 6, 7</th><th>Zone 2 (shade)</th><th>Zone 5 (meadow)</th></tr></thead>
        <tbody>
          <tr><td>Weeks 1–2</td><td>Daily, 20 min</td><td>Daily, 15 min</td><td>Daily, 20 min</td></tr>
          <tr><td>Weeks 3–8</td><td>Every other day, 25 min</td><td>Every other day, 20 min</td><td>Every other day, 25 min</td></tr>
          <tr><td>Months 3–6</td><td>2× per week, 30 min</td><td>1× per week, 25 min</td><td>1× per week, 30 min</td></tr>
          <tr><td>Established</td><td>1× per week, 35–45 min in dry spells only (spring, fall)</td><td>Dry season only, 25 min</td><td>Off. Drought rescue only</td></tr>
        </tbody></table></div>
      <p class="muted" style="font-size:13px"><b>New oaks:</b> fill a 20 gal slow-release watering bag on each tree twice a week for the first 3 months, then weekly until about month 8. UF/IFAS puts establishment at roughly 3 months per inch of trunk caliper in our zone. After that, rainfall carries them.</p>
      <p class="muted" style="font-size:13px">Run between 4 a.m. and 8 a.m. In the summer rainy season the rain sensor should keep most zones off. These are starting points for 1–3 gal plants in sand; adjust to weather.</p>
    </div>
    <div><h3>Rules &amp; equipment</h3><ul class="tight">
      <li><b>Water management district watering rules (example: SJRWMD):</b> drip and micro-irrigation may run any time. Spray zones are limited to set days, ¾ in and 1 hour per zone, and nothing between 10 a.m. and 4 p.m. New plantings get a 60-day establishment allowance.</li>
      <li><b>Water shortage:</b> check your water management district for current restrictions before programming.</li>
      <li><b>Rain shutoff:</b> Florida law (F.S. 373.62) requires a working rain sensor or soil-moisture shutoff on automatic systems.</li>
      <li><b>Controller:</b> add 7 stations to the existing controller, or an expansion module. A WaterSense smart controller with a flow sensor is a worthwhile upgrade.</li>
      <li><b>Existing heads:</b> cap every spray or rotor head inside new beds. Re-aim the lawn heads in the east extension so they stay off the beds and path.</li>
      <li><b>Take-off for the irrigation vendor:</b> 7 drip kits (valve, filter, regulator) · 4 jumbo valve boxes · ≈{IR.MAIN.length:.0f} lf mainline (one bore under the entry walk) · ≈{hdr_len:.0f} lf poly headers · ≈{tube_tot*1.1:,.0f} ft inline tubing (+10%) · 14 flush valves · 7 air-relief valves · {len(IR.crossings)} sleeves (≈{IR.sleeve_len:.0f} lf) · 18-ga multi-strand valve wire.</li>
    </ul></div>
  </div>
</section>

{BS.section()}
<section id="details">
  <div class="sh"><span class="no">D-1</span><h2>Construction details</h2></div>
  <div class="dets">{det_html}</div>
</section>

<section id="notes">
  <div class="sh"><span class="no">N-1</span><h2>Notes, phasing &amp; care</h2></div>
  <div class="cols">
    <div><h3>Field-verify before bidding</h3><ul class="tight">
      <li>Exact palm count and positions (5 are shown), plus the live oak's trunk location and diameter</li>
      <li>Mail kiosk footprint and curved walk (placed from the site video; hidden under the canopy in the aerial)</li>
      <li>Keep the equipment-room door and vents on the restroom's street-facing wall clear. The rock band leaves 3 ft open there.</li>
      <li>Existing shrubs at the restroom and the two tall shrubs on the SW side: keep healthy ones that fit the band, replace the rest</li>
      <li>Existing irrigation main, zones, controller stations and water source</li>
      <li>What the east-lawn utility structure is, and its access needs</li>
      <li>Whether the two trees on the south side are on HOA land</li>
      <li>Call Sunshine 811 before any digging. The right-of-way strips usually carry buried utilities (water, cable, power), so keep the oaks 10 ft from any pedestal or box.</li>
      <li>The right-of-way oaks, the bed edges that extend into the right-of-way, and the south-street access path need a county right-of-way permit. Keep the oaks out of the corner sight triangle.</li></ul></div>
    <div><h3>Phasing</h3><ul class="tight">
      <li><b>Each year:</b> smother turf under cardboard and mulch, and lay drip in Nov–Feb. Plant in Mar–Apr. Frost-tender firebush and wild coffee go in last. Sheet B-1 has the year-by-year plan.</li>
      <li><b>Mar–Apr:</b> frost-tender plants (firebush, wild coffee), wildflowers, groundcovers and ferns. Start drip establishment.</li>
      <li><b>Budget option:</b> build the SW and NW sides and the entry first, then finish the NE and SE legs of the loop in year 2.</li></ul></div>
    <div><h3>Care calendar</h3><ul class="tight">
      <li><b>Monthly:</b> rake the path and nodes, hand-weed, check that drip lines haven't been kicked loose</li>
      <li><b>Late Feb:</b> cut back grasses and the meadow to 8–12 in. Seed heads are left through winter for birds.</li>
      <li><b>May–Jul:</b> cut palm flower stalks before they fruit · light-prune firebush and viburnum after bloom</li>
      <li><b>Quarterly:</b> flush drip lines and clean the filters</li>
      <li><b>Live oaks:</b> an ISA-certified arborist does structural pruning every 1–2 years for the first 5 years, then crown reduction and clearance pruning every 3–5 years to ANSI A300 standards. Keep the canopy 10–15 ft off the pool fence and 14 ft above the street. Install a 24 in root barrier on the curb side at planting.</li>
      <li><b>Fertilizer:</b> natives rarely need it. Check your county/city fertilizer ordinance; many Florida counties ban nitrogen and phosphorus June 1 to Sept 30.</li></ul></div>
  </div>
  <div class="callout"><p><b>For the client:</b> under Florida Statute 373.185, deed restrictions and HOA rules may not prohibit Florida-Friendly Landscaping. This plan follows the UF/IFAS Florida-Friendly principles: right plant, right place; group plants by water need; mulch; and use efficient irrigation.</p></div>
  <h3>Basis &amp; sources</h3>
  <p class="muted" style="font-size:13px">Parcel lines come from the county property appraiser GIS (State Plane FL East, US ft). The deck, pool, walk, palms and canopy were measured from the 2026 aerial, so expect ±2 ft. This is a concept design for review, not sealed construction documents.</p>
  <ul class="tight src" style="font-size:13px">
    <li>Your county property appraiser GIS viewer, such as <a href="https://www.bcpao.us/">BCPAO (Brevard)</a>, <a href="https://www.ocpafl.org/">OCPA (Orange)</a> or <a href="https://www.hcpafl.org/">HCPA (Hillsborough)</a></li>
    <li><a href="https://www.swfwmd.state.fl.us/sites/default/files/store_products/FFL%20Plant%20Guide%202022%20UF%20WEB-A.pdf">UF/IFAS Florida-Friendly Landscaping Guide to Plant Selection (2022)</a></li>
    <li><a href="https://www.fnps.org/plants">Florida Native Plant Society plant database</a></li>
    <li><a href="https://www.ffgc.org/resources/Documents/2024%20Documents/24-03-07%20Invasive%20Plants%20FIPS%202023%20by%20Common%20Name%203-7-2024.pdf">FISC 2023 invasive plant list</a></li>
    <li><a href="https://phzmapi.org/">USDA plant hardiness zone lookup by ZIP code</a></li>
    <li><a href="https://www.sjrwmd.com/wateringrestrictions/">SJRWMD watering restrictions</a> · <a href="https://www.sjrwmd.com/2026/06/drought-conditions-persist-despite-recent-rainfall/">2026 drought update</a></li>
    <li><a href="https://flsenate.gov/Laws/Statutes/2005/373.62">F.S. 373.62 (rain shutoff devices)</a> · <a href="https://ask.ifas.ufl.edu/publication/EP513">UF/IFAS on F.S. 373.185 and HOAs</a></li>
    <li>Your county/city fertilizer ordinance · <a href="https://www.fnai.org/PDFs/FieldGuides/Lantana_depressa_var_floridana.pdf">FNAI pineland lantana</a></li>
  </ul>
</section>
<footer><span>Sample Community Pool Garden · Concept design · October 2026</span><span>Prepared for: Sample Community HOA</span></footer>
</div>
<script>
document.querySelectorAll('[data-zoom]').forEach(function(fig){{
  var svg = fig.querySelector('svg.plan'), btns = fig.querySelectorAll('.zoom button');
  btns.forEach(function(b){{ b.addEventListener('click', function(){{
    var z = +b.dataset.z; svg.style.width = (z*100) + '%';
    btns.forEach(function(x){{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }});
  }}); }});
}});
(function(){{
  var INFO = {pinfo_json};
  var svg = document.querySelector('svg.plan.interactive'), box = document.getElementById('pinfo');
  if (!svg || !box) return;
  var hint = box.innerHTML;
  function esc(s){{ return String(s).replace(/[&<>"]/g, function(c){{ return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]; }}); }}
  function clear(){{
    svg.classList.remove('focus');
    svg.querySelectorAll('.hit.same, .hit.sel').forEach(function(g){{ g.classList.remove('same','sel'); }});
  }}
  function reset(){{ clear(); box.innerHTML = hint; }}
  function closeBtn(){{ return '<button type="button" class="pi-close" aria-label="Close">×</button>'; }}
  svg.addEventListener('click', function(e){{
    var g = e.target.closest('.hit');
    if (!g) {{ reset(); return; }}
    clear();
    var k = g.getAttribute('data-k'), html = '';
    if (k.indexOf('p:') === 0) {{
      var c = k.slice(2), p = INFO.plants[c]; if (!p) return;
      svg.classList.add('focus');
      svg.querySelectorAll('.hit[data-k="' + k + '"]').forEach(function(x){{ x.classList.add('same'); }});
      g.classList.add('sel');
      var n = +g.getAttribute('data-n') || 1, z = g.getAttribute('data-z'), y = g.getAttribute('data-y');
      var zone = z === 'row' ? 'Right-of-way · watering bags' : (INFO.zones[z] ? 'Zone ' + z + ' · ' + INFO.zones[z] : '—');
      html = closeBtn() + '<h4><span class="pi-sw" style="background:' + p.color + '"></span>' + esc(p.com) + '</h4>' +
        '<div class="pi-bot">' + esc(p.bot) + '</div>' +
        (p.native ? '<span class="pi-chip">Florida native</span>' : '') + '<span class="pi-chip">' + esc(p.size) + ' · $' + p.price.toFixed(2) + '</span>' +
        '<dl>' +
        '<dt>' + (n > 1 ? 'This drift' : 'This spot') + '</dt><dd>' + n + ' plant' + (n > 1 ? 's' : '') + '</dd>' +
        '<dt>Whole design</dt><dd>' + p.total + ' drawn · buy ' + p.buy + (p.groups > 1 ? ' · ' + p.groups + ' spots lit up' : '') + '</dd>' +
        (p.sp ? '<dt>Spacing</dt><dd>' + p.sp + ' ft on center</dd>' : '') +
        '<dt>Mature size</dt><dd>' + esc(p.mature.replace(/^([\\d.\\- x]+?)(\\s*\\(|$)/, '$1 ft$2')) + '</dd>' +
        '<dt>Irrigation</dt><dd>' + esc(zone) + '</dd>' +
        (y ? '<dt>Planted</dt><dd>Year ' + esc(y) + ' of the phased plan</dd>' : '') +
        '</dl><p class="pi-note">' + esc(p.note) + '</p>';
    }} else {{
      var f = INFO.features[k.slice(2)]; if (!f) return;
      g.classList.add('sel');
      html = closeBtn() + '<h4>' + esc(f[0]) + '</h4><p class="pi-note">' + esc(f[1]) + '</p>';
    }}
    box.innerHTML = html;
    var cb = box.querySelector('.pi-close'); if (cb) cb.addEventListener('click', reset);
  }});
  document.addEventListener('keydown', function(e){{ if (e.key === 'Escape') reset(); }});
}})();
</script>
'''
open('example-pool-garden.html', 'w').write(page)
print(len(page)//1024, 'KB')
