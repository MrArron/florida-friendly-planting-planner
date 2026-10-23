import math, json
from shapely.geometry import Point, box
import layout as Lo
import render as R
from render import px, f, text

ZONE_LABELS = [
    ((-4, -39.6), 'OAK HAMMOCK', 'zone'),
    ((46, -41.6), 'MYRTLEWOOD POLLINATOR MEADOW', 'zone'),
    ((40, -52.6), 'dashed rings = managed oak canopy (≈55 ft wide), pruned 10–15 ft off the pool fence', 'zonesub'),
    ((100, -49.6), 'BUTTERFLY GARDEN ↑', 'zone'),
    ((22, 74.0), 'NE GARDEN WALK', 'zone'),
    ((92, 120), 'DOG REST LAWN', 'zone'),
    ((92, 116.4), 'existing turf · bench, bag station & trash can', 'zonesub'),
    ((-26, 50), 'STREET', 'zone'),
    ((-26, 46.8), 'FRONTAGE', 'zone'),
    ((-26.5, 31.5), 'ENTRY', 'zone'),
]

def _plant_meta():
    import irrigation as IR, schedule as SC, prices as PR
    from shapely.geometry import Point
    wp_of = {v: k for k, v in SC.WP_ZONE.items()}
    first = {}
    for yr in SC.YEARS:
        for it in yr['items']:
            if it.get('kind') in ('structure', 'perennials'):
                first.setdefault((it['wp'], it['kind']), yr['year'])
    def zone_of(pt):
        p = Point(pt)
        for z, g in IR.Z.items():
            if g.buffer(0.6).contains(p): return z
        return min(IR.Z, key=lambda z: IR.Z[z].distance(p))
    STRUCT = ('3 gal', '7 gal', '15 gal')
    def year_for(code, z):
        grp = 'structure' if PR.PLANT[code][1] in STRUCT else 'perennials'
        return first.get((wp_of.get(z), grp), '')
    return zone_of, year_for

def drift_layer(mode):
    o = []
    if mode == 'plant':
        zone_of, year_for = _plant_meta()
    for d in Lo.DRIFTS:
        col = Lo.PAL[d['code']][6]
        if mode == 'irr':
            o.append(f'<path d="{R.path_d(d["geom"])}" fill="var(--sym-mute)" fill-opacity=".5" stroke="var(--line-faint)" stroke-width=".5"/>')
            continue
        rp = d['geom'].representative_point()
        z = zone_of((rp.x, rp.y))
        o.append(f'<g class="hit" data-k="p:{d["code"]}" data-n="{len(d["pts"])}" data-z="{z}" data-y="{year_for(d["code"], z)}">')
        o.append(f'<path d="{R.path_d(d["geom"])}" fill="{R.shade(col,.72)}" fill-opacity=".9" stroke="{R.shade(col,-.25)}" stroke-width=".8"/>')
        r = Lo.PAL[d['code']][4]*0.46
        if d['code'] == 'DO': r = 0.62
        o.append(''.join(R.plant_symbol(d['code'], x, y, r, col, mode) for x, y in d['pts']))
        o.append('</g>')
    for c, x, y in sorted(Lo.ind, key=lambda t: t[0] == 'MFT'):
        if mode == 'plant':
            z = zone_of((x, y))
            o.append(f'<g class="hit" data-k="p:{c}" data-n="1" data-z="{z}" data-y="{year_for(c, z)}">' + R.shrub_symbol(c, x, y, mode) + '</g>')
        else:
            o.append(R.shrub_symbol(c, x, y, mode))
    return o

def callouts():
    o = []
    for d in Lo.DRIFTS:
        g = d['geom']
        if g.area < 14 or d['code'] == 'DO' and d['zone'] == 'band': continue
        p = g.representative_point()
        cx, cy = px(p.x, p.y)
        o.append(f'<text x="{f(cx)}" y="{f(cy+2.5)}" class="tag" text-anchor="middle">{len(d["pts"])} {d["code"]}</text>')
    # twinflower ribbon note
    o.append(text(51, -4.4, 'DO · twinflower ribbon, 3 ft wide, all sides', 'tagnote', 'middle'))
    return o

def leaders():
    picks = [  # (side, kind, code, target, botanical, common)
        ('L','feat','oak', Lo.OAK, 'Quercus virginiana', 'existing live oak · protect root zone'),
        ('L','ind','SR', (-28, 0), None, None), ('L','ind','AE', (-24, -9), None, None),
        ('L','drift','PN', (-30, -14), None, None), ('L','drift','TK', (-30, -20), None, None), ('L','drift','OC', (-10, -22), None, None), ('L','drift','RF', (-22, 0), None, None), ('L','drift','ZI', (-12, -20), None, None),
        ('L','feat','kiosk', Lo.KIOSK, 'Existing covered mail kiosk', 'quarter-circle walk to curb · to remain'),
        ('L','feat','pitto', Lo.PITTOS[0], 'Pittosporum tobira (2)', 'existing Japanese pittosporum · keep'),
        ('L','feat','queen', Lo.QUEEN, 'Syagrus romanzoffiana', 'existing queen palm · remove when it dies'),
        ('L','feat','yucca', Lo.YUCCA, 'Yucca gigantea (likely)', 'existing giant yucca · keep, 3 ft trunk ring'),
        ('L','feat','rm', Lo.REMOVE[0]['xy'], 'To be removed', 'when construction reaches the area'),
        ('L','ind','CA', (-3, -31), None, None), ('L','drift','DO', (-28, -28), None, None),
        ('L','ind','IVH', (-30, 14.5), None, None), ('L','ind','SB', (-27, 23), None, None),
        ('L','drift','MC', (-31, 40), None, None), ('L','drift','GP', (-31, 34), None, None),
        ('L','drift','EE', (-31, 60), None, None),
        ('L','feat','path', (-21.7, 30), 'Nature path', 'limestone screenings · 4 ft · permeable'),
        ('L','feat','walk', (-30, 12.6), 'Existing concrete walk', 'main entry · to remain'),
        ('L','feat','dump', Lo.DUMP, 'Pool dump valve', '8 ft service area · field-locate'),
        ('R','feat','util', Lo.UTIL, 'Community irrigation pump', 'TF ring open to the path · 4 ft lawn way'),
        ('R','feat','dog', Lo.DOG_STATION, 'Dog rest area', 'pad, bench, pet-waste station'),
        ('R','ind','MFT', (106, 67), None, None), ('R','drift','GP', (60, 66), None, None), ('R','feat','palm', Lo.PALMS[3], 'Sabal palmetto', 'existing cabbage palms to remain'),
        ('R','feat','marker', Lo.MARKERS[0], 'Irrigation valve marker', 'keep findable · drip tie-in'),
        ('R','feat','palme', Lo.CABBAGE[4][1], 'Sabal palmetto (east fence)', 'keep · fence strip bends around it'),
        ('R','feat','pair', Lo.CABBAGE[2][1], 'Sabal palmetto (pair)', 'keep · ID sword fern in boots first'),
        ('R','ind','VO', (78, -31), None, None), ('R','ind','HP', (105, 37), None, None),
        ('R','drift','SS', (112, 20), None, None), ('R','feat','rock', (84.6, 14), 'Limestone strip', '3 ft climb-free strip at fence'),
        ('R','drift','IV', (90, 22), None, None), ('R','drift','SC', (112, 5), None, None),
        ('R','drift','SJ', (112, -5), None, None), ('R','drift','MP', (112, -30), None, None),
        ('R','drift','LS', (100, -32), None, None), ('R','drift','AT', (85, -33), None, None),
        ('R','drift','CL', (75, -33), None, None), ('R','drift','RH', (60, -33), None, None),
        ('R','rowtree','QV', (60, -40), None, None), ('L','rowtree','QV', (-40, 38), None, None), ('R','drift','MS', (50, -33), None, None), ('R','feat','street', (88.5, -40), 'Street access', 'path to Myrtlewood curb · concrete landing'), ('R','drift','TF', (80, 55), None, None),
    ]
    items = {'L': [], 'R': []}
    for side, kind, code, tgt, bot, com in picks:
        if kind == 'feat':
            a = tgt
        elif kind == 'rowtree':
            a = min([(x, y) for cc, x, y, r in Lo.ROW_TREES if cc == code], key=lambda p: math.dist(p, tgt))
        elif kind == 'ind':
            cands = [(x, y) for c, x, y in Lo.ind if c == code]
            if not cands: continue
            a = min(cands, key=lambda p: math.dist(p, tgt))
        else:
            cands = [d for d in Lo.DRIFTS if d['code'] == code and d['geom'].area > 6]
            if not cands: continue
            d = min(cands, key=lambda d: d['geom'].distance(Point(tgt)))
            pt = d['geom'].representative_point(); a = (pt.x, pt.y)
        if bot is None:
            bot = Lo.PAL[code][0]; com = Lo.PAL[code][1].split(' (')[0]
        items[side].append((a, bot, com))
    o = []
    GAP, TOP, BOT = 7.2, 147, -44
    for side in ('L', 'R'):
        its = sorted(items[side], key=lambda it: -it[0][1])
        ys = [min(TOP, it[0][1]) for it in its]
        for i in range(1, len(ys)):           # push down to clear
            ys[i] = min(ys[i], ys[i-1]-GAP)
        if ys and ys[-1] < BOT:                # shift up if overflowing
            ys[-1] = BOT
            for i in range(len(ys)-2, -1, -1): ys[i] = max(ys[i], ys[i+1]+GAP)
        for (a, bot, com), ly in zip(its, ys):
            o.append(R.leader(a, bot, side, ly, bot, com))
    return o

def plan_svg(mode='plant', extra=''):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(R.W)} {f(R.H)}" class="plan{' interactive' if mode == 'plant' else ''}" role="img">', R.defs()]
    o += R.base(mode)
    o += drift_layer(mode)
    o += R.overlays(mode)
    if mode == 'plant':
        o += callouts()
        # sight triangle
        o.append(f'<path d="{R.path_d(Lo.sight.intersection(Lo.parcel))}" fill="none" stroke="var(--warn)" stroke-width="1" stroke-dasharray="3 3"/>')
        o.append(text(-30.5, -4.5, 'sight triangle · plants under 30 in', 'tiny warn'))
        for (x, y), s, cls in ZONE_LABELS:
            o.append(text(x, y, s, cls, 'middle'))
        o += leaders()
        o.append(R.hit_layer())      # point features stay clickable above drifts, beds and leader dots
    o.append(extra)
    o.append(R.north_arrow(150, -50) if mode == 'plant' else R.north_arrow(150, -50))
    o.append(R.scale_bar(-96, -58) if mode == 'plant' else R.scale_bar(-96, -58))
    o.append('</svg>')
    return '\n'.join(o)

if __name__ == '__main__':
    open('plant.svg', 'w').write(plan_svg('plant'))
    print('ok')