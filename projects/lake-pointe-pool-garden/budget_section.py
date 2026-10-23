import html, re, os, hashlib
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
            elif it['cat'] == 'Removal':
                rm = {r['id']: r for r in Lo.REMOVE}
                names = {}
                for x in its:
                    if x['cat'] == 'Removal':
                        nm = rm[x['rm']]['name']
                        names[nm] = names.get(nm, 0) + 1
                lst = '; '.join(f'{n} × {nm}' if n > 1 else nm for nm, n in names.items())
                acts.append(f'Remove the existing {"plants" if sum(names.values()) > 1 else "plant"} marked to be removed: {lst}')
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
        if seen: out.append((SC.WP_NAME[wp], seen))
    return out

def year_table(yr):
    rows = []
    for it in yr['items']:
        if it.get('kind') in ('structure', 'perennials') and not it.get('rows'): continue
        extra = ''
        if it.get('kind') in ('structure', 'perennials') and (it.get('frac') or 1) < 0.97:
            extra = f' · {it["frac"]*100:.0f}% of this group'
        if it.get('kind') in ('structure', 'perennials'):
            lst = ', '.join(f'{max(1, round(r[2]*(it.get("frac") or 1)))} {r[0]}' for r in it['rows'])
            lab = it.get('lab', 0)
            labtxt = f' · includes ${lab:,.0f} {"arborist planting" if it.get("wp") == 0 else "planting labor"}' if lab >= 0.5 else ''
            wpn = f' ({SC.WP_NAME[it["wp"]]})' if it.get('wp') is not None else ''
            desc = f'{it["desc"]}{wpn}{extra}{labtxt}: <span class="muted">{esc(lst)}</span>'
        else:
            desc = esc(it['desc'])
        cost = 'vendor' if it['cat'] == 'Irrigation' else f'${it["cost"]:,.0f}'
        rows.append(f'<tr><td>{esc(it["cat"])}</td><td>{desc}</td><td class="num">{cost}</td></tr>')
    rows.append(f'<tr class="tot"><td></td><td>Year total (budget ${yr["budget"]:,.0f})</td><td class="num">${yr["spent"]:,.0f}</td></tr>')
    return '<div class="tablewrap"><table class="ytab"><thead><tr><th>Category</th><th>Item</th><th style="text-align:right">Cost</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'

# ---- year renders: one SVG file per distinct picture, shared between scenarios when identical
RENDERS = {}
def render_img(k, cal, years):
    svg = PRD.year_svg(k, years)
    h = hashlib.md5(svg.encode()).hexdigest()[:12]
    RENDERS[h] = svg
    return (f'<img src="renders/{h}.svg" width="{(PRD.XB-PRD.XA)*PRD.SS:.1f}" height="{(PRD.YB-PRD.YA)*PRD.SS:.1f}" loading="lazy" '
            f'alt="Top-down render of the garden at the end of year {k} ({cal})">')

def write_renders(folder):
    """Write every distinct year render to folder/<hash>.svg and drop stale ones."""
    os.makedirs(folder, exist_ok=True)
    for f_ in os.listdir(folder):
        if f_.endswith('.svg') and f_[:-4] not in RENDERS: os.remove(os.path.join(folder, f_))
    for h, svg in RENDERS.items():
        open(os.path.join(folder, h + '.svg'), 'w').write(svg)

def scenario_html(budget, vol):
    years = SC.SCEN[(budget, vol)]
    st = SC.scen_stats(years)
    total_budget = sum(y['budget'] for y in years)
    glance = ''.join(
        f'<tr><td>Year {y["year"]} · {y["cal"]}</td><td>{esc(" · ".join(n for n, a in scope_lines(y) if n != "Live oaks") or "Arborist visit")}</td>'
        f'<td class="num">${y["budget"]:,.0f}</td><td class="num">${y["spent"]:,.0f}</td></tr>' for y in years)
    cards = []
    run = 0
    for y in years:
        run += y['spent']
        k = y['year']
        sc_html = ''.join(f'<li><b>{esc(n)}:</b> {esc("; ".join(a))}</li>' for n, a in scope_lines(y))
        cards.append(f'''<article class="ycard">
  <figure class="yrender">{render_img(k, y["cal"], years)}<figcaption>End of year {k} · {y["cal"]}</figcaption></figure>
  <div class="ybody">
    <div class="yhead"><span class="yno">Year {k} <small>· {y["cal"]}</small></span><span class="ycost">${y["spent"]:,.0f}</span><span class="yrun">of ${y["budget"]:,.0f} budget · running total ${run:,.0f}</span></div>
    <ul class="tight">{sc_html}</ul>
    <details><summary>Line items</summary>{year_table(y)}</details>
  </div>
</article>''')
    return f'''<template id="sc-{budget}-{vol}"><div class="scbody" data-years="{st['years']}" data-finish="{st['finish']}" data-total="{st['total']:.0f}" data-labor="{st['labor']:.0f}">
  <h3>At a glance</h3>
  <div class="tablewrap"><table style="min-width:640px"><thead><tr><th>Year</th><th>Main work</th><th style="text-align:right">Budget</th><th style="text-align:right">Spend</th></tr></thead><tbody>{glance}
  <tr class="tot"><td></td><td>Total</td><td class="num">${total_budget:,.0f}</td><td class="num">${st['total']:,.0f}</td></tr></tbody></table></div>

  <h3>Year by year</h3>
  <p class="muted" style="margin-top:0">Each render shows the garden at the end of that year. Plants bought in earlier years are drawn larger as they fill in, and the new oaks' canopies widen each year.</p>
  <div class="years">{''.join(cards)}</div>
</div></template>'''

def matrix():
    rows = []
    for b in SC.BUDGETS:
        cells = []
        for v in (0, 1):
            st = SC.scen_stats(SC.SCEN[(b, v)])
            cells.append(f'<td><button type="button" class="mxb" data-b="{b}" data-v="{v}"><b>{st["years"]} yrs</b> · done {st["finish"]}<br><small>${st["total"]:,.0f}</small></button></td>')
        rows.append(f'<tr><th scope="row">${b:,}/yr</th>{"".join(cells)}</tr>')
    return ('<div class="tablewrap"><table class="mx" style="min-width:0"><thead><tr><th>Year-one budget</th><th>Hired planting</th><th>Volunteer planting</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table></div>')

SC_JS = r'''<script>
  (function(){
    var out=document.getElementById('sc-out'),v=document.getElementById('scv');
    function cur(){var r=document.querySelector('input[name=scb]:checked');return [r.value, v.checked?1:0];}
    function money(n){return '$'+Math.round(n).toLocaleString('en-US');}
    function show(){
      var c=cur(),t=document.getElementById('sc-'+c[0]+'-'+c[1]);
      out.replaceChildren(t.content.cloneNode(true));
      var d=out.firstElementChild.dataset;
      document.getElementById('ss-years').textContent=d.years;
      document.getElementById('ss-finish').textContent=d.finish;
      document.getElementById('ss-total').textContent=money(d.total);
      document.getElementById('ss-labor').textContent=money(d.labor);
      document.getElementById('sc-headline').textContent=d.years+' years starting at '+money(c[0])+' in 2027, rising with inflation · about '+money(d.total)+' in total';
      document.querySelectorAll('.mxb').forEach(function(b){b.setAttribute('aria-pressed', b.dataset.b===c[0] && +b.dataset.v===c[1]);});
      try{localStorage.setItem('lp-sc', c.join(':'));}catch(e){}
    }
    document.querySelectorAll('input[name=scb]').forEach(function(r){r.addEventListener('change',show);});
    v.addEventListener('change',show);
    document.querySelectorAll('.mxb').forEach(function(b){b.addEventListener('click',function(){
      document.querySelector('input[name=scb][value="'+b.dataset.b+'"]').checked=true; v.checked=b.dataset.v==='1'; show();
      document.querySelector('.scctl').scrollIntoView({block:'nearest'});
    });});
    try{var s=(localStorage.getItem('lp-sc')||'').split(':');
      if(s.length===2){var r=document.querySelector('input[name=scb][value="'+s[0]+'"]'); if(r){r.checked=true; v.checked=s[1]==='1';}}}catch(e){}
    show();
  })();
  </script>'''

def section():
    ex = SC.budget_of(SC.BUDGET, 5)
    radios = ''.join(f'\n      <label><input type="radio" name="scb" value="{b}"{" checked" if b == SC.BUDGET else ""}><span>${b:,}</span></label>' for b in SC.BUDGETS)
    templates = ''.join(scenario_html(b, v) for b in SC.BUDGETS for v in (0, 1))
    return f'''
<section id="budget">
  <div class="sh"><span class="no">B-1</span><h2>Phased buildout</h2><span class="muted" id="sc-headline"></span></div>
  <div class="scctl" role="group" aria-label="Buildout scenario">
    <fieldset class="seg"><legend>Year-one investment</legend>{radios}
    </fieldset>
    <label class="tog"><input type="checkbox" id="scv" role="switch"><span class="tr" aria-hidden="true"></span>
      <span class="tl"><b>Volunteers plant the beds</b><small>The arborist still plants the oaks; a contractor still builds the path</small></span></label>
    <div class="scsum" aria-live="polite">
      <div><b id="ss-years">–</b><span>years</span></div>
      <div><b id="ss-finish">–</b><span>finished</span></div>
      <div><b id="ss-total">–</b><span>total, with inflation</span></div>
      <div><b id="ss-labor">–</b><span>hired labor in total</span></div>
    </div>
  </div>
  <div class="cols">
    <div>
      <p>Each year buys one complete piece of the garden in a set order. The oaks go in first because they need the most time. Next comes the entry everyone walks through, then the pool band, the shade garden, the meadow and butterfly garden, then the NE leg that closes the loop, and last the dog rest area on the east lawn.</p>
      <p>Most years follow the same rhythm: smother the turf in fall, have the irrigation vendor lay drip over the winter, then plant in spring. When a purchase doesn't fit the remaining budget, the rest of that planting rolls into the next spring.</p>
      <h3>Compare every option</h3>
      {matrix()}
      <p class="muted" style="font-size:13px">Tap any cell to load that plan. Totals are in the dollars of each year they're spent.</p>
    </div>
    <div><h3 style="margin-top:0">What the numbers assume</h3><ul class="tight">
      <li><b>Inflation.</b> Prices were checked in October 2026 and year 1 is spring 2027. Plants and materials rise 4% a year, based on nursery price surveys and the BLS producer price index for crushed stone. Labor rises 4.5% a year, since landscape field wages are growing faster than general wages.</li>
      <li><b>The yearly budget rises with costs.</b> The amount you pick is the 2027 budget. It goes up 4.2% each year, about the blend of the two rates, so each year's money buys roughly the same amount of work. For $2,500 that's ${ex:,.0f} in {SC.START+4}.</li>
      <li><b>Labor allowances</b> for hired help, before inflation. Planting: $3.00 per 4 in pot, $3.50 per 6 in pot, $10 per 3 gal shrub. The arborist plants each 15 gal oak for $100. Path: $2.50 per sq ft to excavate, set edging, and place and compact the screenings. Turf smothering, mulching and the fence strip are volunteer work in every option.</li>
      <li><b>The volunteer toggle</b> removes the planting allowance for the beds only. The oaks stay with the arborist, and the path stays with a professional crew.</li>
      <li><b>Irrigation is not in these numbers.</b> The HOA's contracted irrigation vendor installs each drip zone, the mainline and the sleeves. Book the vendor before each area is planted. The schedule shows when each piece is needed.</li>
      <li><b>Plant prices</b> from the Rockledge Gardens online shop, checked October 17, 2026. Spreading wildflowers and groundcovers are bought at about half the drawn density and left to fill in.</li>
      <li><b>Free mulch</b> from Brevard County (Sarno Rd landfill, Melbourne). Turf is smothered under donated cardboard rather than sprayed or cut out.</li>
      <li><b>Cheaper hardscape</b> that doesn't change the look: crushed limestone (#57) at the fence, compacted limestone screenings for the path, and poly pipe for drip headers. Oaks get slow-release watering bags for their first 8 months.</li>
      <li><b>Allowances:</b> 8% contingency on every purchase, and arborist pruning visits for the oaks in years 2, 4, 6 and 10 when the build is still running. After that, plan on a visit every 3–5 years as upkeep.</li>
      <li><b>Removals:</b> existing plants marked "to be removed" come out when construction reaches their area, as allowances that include disposal: $60–150 per shrub or clump and $250–400 per palm (stump ground). The queen palm is left until it dies, so its removal is not scheduled.</li>
      <li><b>Not included:</b> benches (about $600 each; good candidates for sponsored or memorial benches), the county right-of-way permit fees (budgeted separately by the board), and tools.</li>
    </ul></div>
  </div>
  <div id="sc-out"></div>
  {templates}
  <h3>Ways to finish sooner</h3>
  <ul class="tight">
    <li><b>Buy early.</b> With costs rising about 4% a year, every year the build is shortened saves money. A bigger budget finishes for less in total.</li>
    <li><b>Divide and share:</b> muhly, dwarf Fakahatchee, twinflower and shield fern divide easily after a year or two. Volunteers can split year-2 plants to fill later areas, which could cut later plant buys by a quarter or more.</li>
    <li><b>Seed the meadow</b> with Florida-native wildflower seed instead of pots for blanket flower, tickseed and black-eyed Susan. This is slower to look full but costs a fraction.</li>
    <li><b>Ask Rockledge Gardens</b> about an HOA or volume discount, and watch for their native plant sales.</li>
    <li><b>Sponsorships:</b> offer benches and the five oaks as resident-sponsored dedications.</li>
    <li><b>Grants:</b> look for local garden-club, Indian River Lagoon or conservation grants for native and pollinator plantings.</li>
    <li><b>Confirm the free mulch:</b> it saves roughly $3,500–4,500 over the project. Check that HOAs qualify (Brevard Solid Waste, 321-633-2042).</li>
  </ul>
  {SC_JS}
</section>'''