import html, re
import schedule as SC, prices as PR, layout as Lo
import phase_render as PRD

def esc(s): return html.escape(s)

def scope_lines(yr):
    """Plain-language scope for one year, grouped by work package."""
    by = {}
    for it in yr['items']:
        wp = it.get('wp')
        by.setdefault(wp, []).append(it)
    out = []
    for wp, its in by.items():
        if wp is None:
            out.append(('Live oaks', ['Arborist visit for structural pruning']))
            continue
        acts = []
        for it in its:
            d = it['desc']
            if it.get('kind') in ('structure', 'perennials'):
                fr = it.get('frac') or 1.0
                what = 'trees & shrubs' if it['kind'] == 'structure' else 'grasses, wildflowers & groundcovers'
                if wp == 0: what = f'{len(Lo.ROW_TREES)} live oaks (15 gal) in the right-of-way'
                acts.append(f'Plant {what}' + (f' (about {fr*100:.0f}% of them)' if fr < 0.97 else ''))
            elif 'drip zone kit' in d:
                acts.append('Smother turf with cardboard and free mulch; irrigation vendor lays the drip zone')
            elif d.startswith('Mainline'):
                acts.append('Vendor extends the mainline: ' + d.split('Mainline ')[1].split(' (')[0])
            elif 'header' in d:
                continue
            elif d.startswith('Sleeves'):
                acts.append('Vendor sets sleeves where the path will cross')
            elif it['cat'] == 'Rock band':
                acts.append('Lay the limestone strip at the fence')
            elif d.startswith('Path ('):
                acts.append('Build the path segment' + (' and bench node' if wp in (4, 6, 7) else ''))
            elif d.startswith('Dog-area'):
                acts.append('Build the dog-area spur and pad')
            elif d.startswith('Pet-waste'):
                acts.append('Install the pet-waste station and trash can')
            elif 'Geocell' in d:
                acts.append('No-dig path section under the oak')
            elif 'watering bags' in d:
                acts.append('Tree watering bags and root barrier')
            elif 'Root barrier' in d:
                continue
            elif d.startswith('Valve wire, second'):
                acts.append('Vendor runs more valve wire')
            elif 'Rain sensor' in d or 'Tie into' in d or 'Valve wire' in d:
                if 'Vendor ties into the existing supply and adds a rain sensor' not in acts:
                    acts.append('Vendor ties into the existing supply and adds a rain sensor')
        seen = []
        for a in acts:
            if a not in seen: seen.append(a)
        out.append((SC.WP_NAME[wp], seen))
    return out

def year_table(yr):
    rows = []
    for it in yr['items']:
        extra = ''
        if it.get('kind') in ('structure', 'perennials') and (it.get('frac') or 1) < 0.97:
            extra = f' · {it["frac"]*100:.0f}% of this group'
        if it.get('kind') in ('structure', 'perennials'):
            lst = ', '.join(f'{max(1, round(r[2]*(it.get("frac") or 1)))} {r[0]}' for r in it['rows'])
            lab = it.get('labor', 0)*(it.get('frac') or 1)*(it['cost']/max(1e-6, it['cost'])) if it.get('labor') else 0
            labtxt = f' · includes ${lab*(1+0.03)**(yr["year"]-1):,.0f} planting labor' if lab else ''
            desc = f'{it["desc"]} ({SC.WP_NAME[it["wp"]] if it["wp"] else ""}){extra}{labtxt}: <span class="muted">{esc(lst)}</span>'
        else:
            desc = esc(it['desc'])
        cost = 'vendor' if it['cat'] == 'Irrigation' else f'${it["cost"]:,.0f}'
        rows.append(f'<tr><td>{esc(it["cat"])}</td><td>{desc}</td><td class="num">{cost}</td></tr>')
    rows.append(f'<tr class="tot"><td></td><td>Year total</td><td class="num">${yr["spent"]:,.0f}</td></tr>')
    return '<div class="tablewrap"><table class="ytab"><thead><tr><th>Category</th><th>Item</th><th style="text-align:right">Cost</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'

def labor_options():
    keep = (dict(SC.PLANT_LABOR), SC.PATH_LABOR_SF)
    out = []
    for name, pl, pa in [('Hire planting and path labor (this plan)', 1, 1), ('Volunteers build the path; hire planting', 1, 0),
                         ('Volunteers plant; hire the path crew', 0, 1), ('All volunteer', 0, 0)]:
        SC.PLANT_LABOR = {k: (v if pl else 0) for k, v in keep[0].items()}
        SC.PATH_LABOR_SF = keep[1] if pa else 0
        Y = SC.build_schedule()
        out.append((name, len(Y), sum(y['spent'] for y in Y)))
    SC.PLANT_LABOR, SC.PATH_LABOR_SF = keep
    return out

def section():
    years = SC.YEARS
    total = sum(y['spent'] for y in years)
    cards = []
    run = 0
    for y in years:
        run += y['spent']
        k = y['year']
        svg = PRD.year_svg(k)
        sc = scope_lines(y)
        sc_html = ''.join(f'<li><b>{esc(n)}:</b> {esc("; ".join(a))}</li>' for n, a in sc)
        cards.append(f'''<article class="ycard" id="year{k}">
  <figure class="yrender">{svg}<figcaption>End of year {k}</figcaption></figure>
  <div class="ybody">
    <div class="yhead"><span class="yno">Year {k}</span><span class="ycost">${y["spent"]:,.0f}</span><span class="yrun">running total ${run:,.0f}</span></div>
    <ul class="tight">{sc_html}</ul>
    <details><summary>Line items</summary>{year_table(y)}</details>
  </div>
</article>''')
    timeline = ''.join(
        f'<tr><td>Year {y["year"]}</td><td>{esc(" · ".join(n for n, a in scope_lines(y) if n != "Live oaks") or "Arborist visit")}</td><td class="num">${y["spent"]:,.0f}</td></tr>' for y in years)
    return f'''
<section id="budget">
  <div class="sh"><span class="no">B-1</span><h2>Phased buildout</h2><span class="muted">{len(years)} years at no more than ${SC.BUDGET:,.0f} a year · about ${total:,.0f} in total</span></div>
  <div class="cols">
    <div>
      <p style="margin-top:0">Each year buys one complete piece of the garden in a set order. The oaks go in first because they need the most time. Next comes the entry everyone walks through, then the pool band, the shade garden, the meadow and butterfly garden, then the NE leg that closes the loop, and last the dog rest area on the east lawn.</p>
      <p>Most years follow the same rhythm: smother the turf in fall, have the irrigation vendor lay drip over the winter, then plant in spring. When a purchase doesn't fit the remaining budget, the rest of that planting rolls into the next spring.</p>
    </div>
    <div><h3 style="margin-top:0">What the numbers assume</h3><ul class="tight">
      <li><b>Labor allowances</b> for hired help with planting and path building. Planting: $3.00 per 4 in pot, $3.50 per 6 in pot, $10 per 3 gal shrub, $100 per 15 gal oak. Path: $2.50 per sq ft to excavate, set edging, and place and compact the screenings. Whatever volunteers do comes off these numbers. Turf smothering, mulching and the fence strip are assumed to be volunteer work.</li>
      <li><b>Irrigation is not in these numbers.</b> The HOA's contracted irrigation vendor installs each drip zone, the mainline and the sleeves. Book the vendor before each area is planted. The schedule shows when each piece is needed.</li>
      <li><b>Plant prices</b> are illustrative example prices from October 2026 and must be re-priced at a local native plant nursery. Spreading wildflowers and groundcovers are bought at about half the drawn density and left to fill in. Some 4 in pots are often sold out, so buy them in spring when they're back.</li>
      <li><b>Free mulch</b> from your county landfill or solid waste program (confirm eligibility). Turf is smothered under donated cardboard rather than sprayed or cut out.</li>
      <li><b>Cheaper hardscape</b> that doesn't change the look: crushed limestone (#57) for the strip at the fence, compacted limestone screenings for the path, and poly pipe for drip headers.</li>
      <li><b>Oaks</b> are watered with slow-release tree watering bags for their first 8 months instead of a bubbler zone.</li>
      <li><b>Allowances:</b> 8% contingency on every purchase, 3% price increase per year, and arborist pruning visits for the oaks in years 2, 4 and 6. After that, plan on a visit every 3–5 years as ongoing upkeep.</li>
      <li><b>Not included:</b> benches (about $600 each; good candidates for sponsored or memorial benches), the county right-of-way permit fee (not published), and tools.</li>
    </ul></div>
  </div>
  <h3>At a glance</h3>
  <div class="tablewrap"><table style="min-width:640px"><thead><tr><th>Year</th><th>Main work</th><th style="text-align:right">Spend</th></tr></thead><tbody>{timeline}
  <tr class="tot"><td></td><td>Total</td><td class="num">${total:,.0f}</td></tr></tbody></table></div>
  <h3>Year by year</h3>
  <p class="muted" style="margin-top:0">Each render shows the garden at the end of that year. Plants bought in earlier years are drawn larger as they fill in. The new oaks' canopies widen each year.</p>
  <div class="years">{''.join(cards)}</div>
  <h3>Who does the work</h3>
  <div class="tablewrap"><table style="min-width:520px"><thead><tr><th>Approach</th><th style="text-align:right">Years</th><th style="text-align:right">Total</th></tr></thead><tbody>
  {''.join(f'<tr><td>{esc(n)}</td><td class="num">{y}</td><td class="num">${t:,.0f}</td></tr>' for n, y, t in labor_options())}
  </tbody></table></div>
  <p class="muted" style="font-size:13px">Labor is the single biggest lever. A couple of volunteer planting days a year shortens the plan by several years.</p>
  <h3>Ways to finish sooner</h3>
  <ul class="tight">
    <li><b>Divide and share:</b> muhly, dwarf Fakahatchee, twinflower and shield fern divide easily after a year or two. Volunteers can split year-2 plants to fill later areas, which could cut later plant buys by a quarter or more.</li>
    <li><b>Seed the meadow</b> with Florida-native wildflower seed instead of pots for blanket flower, tickseed and black-eyed Susan. This is slower to look full but costs a fraction.</li>
    <li><b>Ask your native plant nursery</b> about an HOA or volume discount, and watch for their native plant sales.</li>
    <li><b>Sponsorships:</b> offer benches and the five oaks as resident-sponsored dedications.</li>
    <li><b>Grants:</b> look for local garden-club, watershed or conservation grants for native and pollinator plantings. Florida-Friendly projects that cut irrigation are often eligible.</li>
    <li><b>Confirm the free mulch:</b> it saves roughly $3,500–4,500 over the project. Check that HOAs qualify with your county solid waste office.</li>
  </ul>
</section>'''
