"""Year-by-year build schedule within a fixed annual budget (volunteer labor)."""
import math, hashlib
from shapely.geometry import LineString, Point
import layout as Lo, irrigation as IR, phasing as P, prices as PR

BUDGET = 2500.0
ESC = 0.03            # yearly price escalation
CONT = 0.08           # contingency on every purchase
ARBORIST = {2: 250, 4: 250, 6: 250, 10: 250}
PLANT_LABOR = {'4 in': 3.0, '6 in': 3.5, '1 gal': 4.0, '3 gal': 10.0, '7 gal': 25.0, '15 gal': 100.0}   # install allowance per plant
PATH_LABOR_SF = 2.50   # excavate, set edging, place & compact screenings   # young-oak structural pruning visits (by year)

M = dict(plastic_roll=86.89, drip_kit=140.0, tube_250=100.11, drip_small=45.0, pvc1_20=27.0, valve_box=65.56,
         wire_250=122.23, rain_sensor=49.34, root_barrier_10=25.0, sleeve=27.46, rock_ton=65.0, fabric_roll=159.0,
         fines_ton=60.0, poly1_ft=0.55, pet_station=200.0, base_ton=25.0, edging_lf=1.25, delivery=100.0, geocell_lot=490.0, water_bag=35.0, poc_fittings=60.0)

WP_NAME = {
 0: 'Live oaks & irrigation tie-in',
 1: 'Entry walk & street frontage',
 2: 'Pool band · southwest half',
 3: 'Pool band · northeast half',
 4: 'Oak hammock, kiosk spur & first bench node',
 5: 'South-street meadow, south path & street access',
 6: 'Butterfly garden & southeast path',
 7: 'NE garden walk & loop completion',
 8: 'Dog rest area on the east lawn',
}
WP_ZONE = {1: 1, 2: 3, 3: 4, 4: 2, 5: 5, 6: 6, 7: 7}
WP_PATH = {4: 4, 5: 5, 6: 6, 7: 7}      # phasing.PATH_REG keys
WP_ROCK = {2: 2, 3: 3}                  # phasing.ROCK keys
MAIN_SEG = {1: ('POC → valve box B', 10.0, 'B'), 2: ('POC → valve box A, bored under the entry walk', 27.5, 'A'),
            3: ('valve box B → valve box C', 58.6, 'C'), 5: ('valve box A → valve box D', 80.5, 'D')}

def header_len(z): return sum(LineString(h).length for h in IR.HEAD.get(z, []))

def plants_for(wp):
    """(code, design_qty, buy_qty, unit price, size) for a work package; structure first."""
    if wp == 8:
        return []
    if wp == 0:
        n = len(Lo.ROW_TREES)
        return [('QV', n, n, PR.PLANT['QV'][0], PR.PLANT['QV'][1])]
    ph = P.ZONE_PHASE[WP_ZONE[wp]]
    out = []
    for c, n in P.CNT[ph].items():
        if c == 'QV': continue
        q = max(1, round(n*PR.SPREAD.get(c, 1)))
        out.append((c, n, q, PR.PLANT[c][0], PR.PLANT[c][1]))
    out.sort(key=lambda r: (-r[3], r[0]))
    return out

def infra_items(wp):
    it = []
    def add(cat, desc, cost):
        if cat == 'Irrigation':      # covered by the HOA's contracted irrigation vendor
            it.append((cat, desc + ' (irrigation vendor, under contract)', 0.0))
        else:
            it.append((cat, desc, round(cost*(1+CONT), 2)))
    if wp == 0:
        add('Trees', f'Root barrier, 24 in, curb side of {len(Lo.ROW_TREES)} oaks', len(Lo.ROW_TREES)*M['root_barrier_10'])
        add('Trees', f'Slow-release tree watering bags ({len(Lo.ROW_TREES)})', len(Lo.ROW_TREES)*M['water_bag'])
        add('Irrigation', 'Tie into existing supply: tee, ball valve, fittings', M['poc_fittings'])
        add('Irrigation', 'Rain sensor (skip if the controller already has one)', M['rain_sensor'])
        add('Irrigation', 'Valve wire, 18-ga multi-strand, 250 ft', M['wire_250'])
        return it
    if wp == 8:
        a = Lo.dog_poly.area; e = Lo.dog_poly.boundary.length; t = a*0.25/27*1.4
        add('Path', f'Dog-area spur + pad ({a:.0f} sq ft): {t:.1f} t limestone screenings, {e:.0f} lf edging, + install labor ${a*PATH_LABOR_SF:,.0f}', t*M['fines_ton'] + e*M['edging_lf'] + 50 + a*PATH_LABOR_SF)
        add('Site', 'Pet-waste station: post-mount bag dispenser, sign and lidded can (est.)', M['pet_station'])
        return it
    z = WP_ZONE[wp]; zone = [x for x in IR.zones if x['z'] == z][0]
    beds = IR.Z[z].area
    # turf removal: sheet-mulch with donated cardboard + free county mulch (no purchase)
    if wp in MAIN_SEG:
        d, L, vb = MAIN_SEG[wp]
        add('Irrigation', f'Mainline {d} ({L:.0f} ft) + jumbo valve box {vb}', math.ceil(L*1.1/20)*M['pvc1_20']*1.35 + M['valve_box'])
    ft = zone['tube']*1.1
    add('Irrigation', f'Zone {z}: drip zone kit, {ft:,.0f} ft inline tubing, flush valves & staples',
        M['drip_kit'] + math.ceil(ft/250)*M['tube_250'] + M['drip_small'])
    hl = header_len(z)
    add('Irrigation', f'Zone {z} header, 1 in poly pipe ({hl:.0f} ft) + fittings', hl*1.1*M['poly1_ft']*1.2)
    nsl = sum(1 for zz, g in IR.crossings if zz == z)
    if nsl: add('Irrigation', f'Sleeves under future path ({nsl})', nsl*M['sleeve'])
    if wp == 5:
        add('Irrigation', 'Valve wire, second 250 ft roll', M['wire_250'])
    if wp in WP_ROCK:
        a = P.ROCK_AREA[WP_ROCK[wp]]; t = a*(2.5/12)/27*1.35
        add('Rock band', f'#57 crushed limestone, 2½ in deep, {t:.1f} t + fabric ({a:.0f} sq ft)', t*M['rock_ton'] + M['fabric_roll'])
    if wp in WP_PATH:
        k = WP_PATH[wp]; a = P.PATH_AREA[k]; e = P.PATH_EDGE[k]
        ft_ = a*0.25/27*1.4
        add('Path', f'Path ({a:.0f} sq ft): {ft_:.1f} t limestone screenings, 3 in compacted on sand, {e:.0f} lf edging, delivery, + install labor ${a*PATH_LABOR_SF:,.0f}',
            ft_*M['fines_ton'] + e*M['edging_lf'] + M['delivery'] + a*PATH_LABOR_SF)
        if wp == 4:
            add('Path', 'Geocell + geotextile for the no-dig section under the oak', M['geocell_lot'])
    return it

def build_schedule():
    queue = []
    for wp in range(0, 9):
        for cat, desc, cost in infra_items(wp):
            n = max(1, math.ceil(cost/1100)) if cat == 'Path' else 1
            for k in range(n):
                dd = desc if n == 1 else f'{desc} — part {k+1} of {n}'
                queue.append(dict(wp=wp, kind='infra', cat=cat, desc=dd, cost=cost/n))
        pl = plants_for(wp)
        struct = [r for r in pl if r[4] not in ('6 in', '4 in', '1 gal')]
        peren = [r for r in pl if r[4] in ('6 in', '4 in', '1 gal')]
        for grp, rows in (('structure', struct), ('perennials', peren)):
            if not rows: continue
            n = sum(r[2] for r in rows)
            labor = sum(r[2]*PLANT_LABOR[r[4]] for r in rows)
            cost = (sum(r[2]*r[3] for r in rows) + labor)*(1+CONT)
            queue.append(dict(wp=wp, kind=grp, cat='Plants', rows=rows, n=n, cost=cost, labor=labor*(1+CONT),
                              desc=('Trees & shrubs' if grp == 'structure' else 'Grasses, wildflowers & groundcovers')))
    years = []
    y = 1
    cur = dict(year=y, items=[], spent=0.0)
    if y in ARBORIST:
        cur['items'].append(dict(wp=None, cat='Trees', desc='Arborist visit: young-oak structural pruning', cost=ARBORIST[y])); cur['spent'] += ARBORIST[y]
    def new_year():
        nonlocal cur, y
        years.append(cur); y += 1
        cur = dict(year=y, items=[], spent=0.0)
        if y in ARBORIST:
            c = ARBORIST[y]*(1+ESC)**(y-1)
            cur['items'].append(dict(wp=None, cat='Trees', desc='Arborist visit: young-oak structural pruning', cost=c)); cur['spent'] += c
    i = 0
    while i < len(queue):
        q = queue[i]
        esc = (1+ESC)**(y-1)
        c = q['cost']*esc
        room = BUDGET - cur['spent']
        if c <= room + 0.01:
            d = dict(q); d['cost'] = c; d['frac'] = 1.0 if q['kind'] in ('structure', 'perennials') else None
            if 'rest' in q: d['frac'] = q['rest']
            cur['items'].append(d); cur['spent'] += c; i += 1
            continue
        # look ahead: anything later in this or the next work package that still fits
        filled = False
        for j in range(i+1, len(queue)):
            qj = queue[j]
            if qj['wp'] > q['wp'] + 1: break
            if qj['cost'] == 0 and qj['wp'] != q['wp']: continue
            if qj['wp'] > q['wp'] and not (qj['kind'] == 'infra' and ('drip zone kit' in qj['desc'] or qj['desc'].startswith('Mainline'))): continue
            if qj['kind'] in ('structure', 'perennials') and qj['wp'] > q['wp']: continue
            cj = qj['cost']*esc
            if cj <= room + 0.01:
                d = dict(qj); d['cost'] = cj; d['frac'] = qj.get('rest', 1.0) if qj['kind'] != 'infra' else None
                cur['items'].append(d); cur['spent'] += cj; queue.pop(j); filled = True
                break
        if filled: continue
        if q['kind'] in ('structure', 'perennials') and room > 60:
            f = room/c
            if f >= 0.88:      # within ~12%: buy what fits and let spreaders cover the gap
                d = dict(q); d['cost'] = room; d['frac'] = q.get('rest', 1.0)*f
                cur['items'].append(d); cur['spent'] += room; i += 1
                new_year(); continue
            whole = q.get('rest', 1.0)
            part = dict(q); part['cost'] = room; part['frac'] = whole*f
            cur['items'].append(part); cur['spent'] += room
            q = dict(q); q['rest'] = whole*(1-f); q['cost'] = q['cost']*(1-f); queue[i] = q
            new_year(); continue
        new_year()
    years.append(cur)
    return years

YEARS = build_schedule()

def state_after(k):
    """What exists after year k: infra-done work packages, plant fraction bought per (wp, group) with years."""
    infra = {}; plant = {}
    for yr in YEARS[:k]:
        for it in yr['items']:
            if it.get('wp') is None: continue
            if it['kind'] == 'infra':
                infra.setdefault(it['wp'], []).append(yr['year'])
            else:
                plant.setdefault((it['wp'], it['kind']), []).append((yr['year'], it['frac']))
    return infra, plant

if __name__ == '__main__':
    tot = 0
    for yr in YEARS:
        print(f"Year {yr['year']}: ${yr['spent']:,.0f}")
        for it in yr['items']:
            extra = f" ({it['frac']*100:.0f}%)" if it.get('frac') not in (None, 1.0) else ''
            print(f"   WP{it.get('wp')} {it['cat']:10s} {it['desc'][:70]:70s} ${it['cost']:,.0f}{extra}")
        tot += yr['spent']
    print('TOTAL', round(tot), 'years', len(YEARS))
