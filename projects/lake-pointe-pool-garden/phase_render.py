import math, random
import numpy as np
from shapely.geometry import Point, box, Polygon
from shapely.ops import unary_union
import layout as Lo, render as R, irrigation as IR, phasing as P
import schedule as SC, hashlib

XA, XB, YA, YB, SS = -58, 122, -55, 112, 4.3

def setup():
    R.S, R.X0, R.Y1 = SS, XA, YB
def px(x, y): return ((x-XA)*SS, (YB-y)*SS)
def f(v): return f'{v:.1f}'

def canopy_blob(c, r, seed, col, op=.92, shadow=True):
    g = R.blob(c, r, seed, .1)
    o = []
    if shadow:
        from shapely import affinity
        sh = affinity.translate(g, 1.6, -1.6)
        o.append(f'<path d="{R.path_d(sh)}" fill="#1d2a17" fill-opacity=".22"/>')
    o.append(f'<path d="{R.path_d(g)}" fill="{col}" fill-opacity="{op}" stroke="{R.shade(col,-.35)}" stroke-width=".8"/>')
    # leaf texture
    rnd = random.Random(seed)
    for _ in range(int(r*r*.35)):
        a = rnd.uniform(0, 6.283); d = r*math.sqrt(rnd.uniform(0, .85))
        x, y = c[0]+d*math.cos(a), c[1]+d*math.sin(a)
        cx, cy = px(x, y)
        o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rnd.uniform(1.2,2.6))}" fill="{R.shade(col, rnd.choice([.18,-.18,.3]))}" fill-opacity=".55"/>')
    return ''.join(o)

def growth(code, age):
    if code == 'QV': return None
    kind = Lo.PAL[code][7]
    if kind in ('mass', 'gc'):
        return min(1.0, .55 + .25*age)
    return min(1.0, .5 + .17*age)

def symbol(code, x, y, r, col):
    cx, cy = px(x, y); rp = r*SS
    return (f'<circle cx="{f(cx+.8)}" cy="{f(cy+.8)}" r="{f(rp)}" fill="#1d2a17" fill-opacity=".18"/>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="{col}" stroke="{R.shade(col,-.35)}" stroke-width=".5"/>'
            f'<circle cx="{f(cx-rp*.3)}" cy="{f(cy-rp*.3)}" r="{f(rp*.35)}" fill="#fff" fill-opacity=".28"/>')

STRUCT_SIZES = ('3 gal', '7 gal', '15 gal', '30 gal', '45 gal')
_Y = SC.YEARS      # schedule used by the state helpers below; year_svg(k, years) switches it

def wp_of_zone(z):
    return {v: k for k, v in SC.WP_ZONE.items()}[z]

def year_state(k):
    beds, rock, path, plants = set(), set(), set(), {}
    for yr in _Y[:k]:
        for it in yr['items']:
            wp = it.get('wp')
            if wp is None: continue
            if it['kind'] == 'infra':
                if 'drip zone kit' in it['desc']: beds.add(wp)
                if it['cat'] == 'Rock band': rock.add(wp)
                if it['cat'] == 'Path' and 'Path (' in it['desc']: path.add(wp)
            else:
                plants.setdefault((wp, it['kind']), []).append((yr['year'], it['frac']))
    return beds, rock, path, plants

def _h(s): return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

def plant_points(k):
    """[(code, x, y, r_base, purchase_year)] for everything planted by end of year k."""
    _, _, _, bought = year_state(k)
    out = []
    for wp in range(1, 8):
        ph = P.ZONE_PHASE[SC.WP_ZONE[wp]]
        for grp in ('structure', 'perennials'):
            buys = bought.get((wp, grp), [])
            if not buys: continue
            items = []   # (order key, code, x, y, r)
            for di, d in enumerate(P.GEO[ph]):
                is_struct = Lo.PAL[d['code']][3].split(',')[0] in STRUCT_SIZES or d['code'] in ('IV', 'PN', 'TF')
                if (grp == 'structure') != is_struct: continue
                r = 0.62 if d['code'] == 'DO' else Lo.PAL[d['code']][4]*0.5
                key = _h(f"{wp}{di}{d['code']}")
                for (x, y) in d['pts']:
                    items.append((key, d['code'], x, y, r, False))
            for (c, x, y) in P.IND[ph]:
                if c == 'QV': continue
                if grp != 'structure': continue
                items.append((_h(f'{c}{x}{y}'), c, x, y, None, True))
            items.sort(key=lambda t: t[0])
            n = len(items); start = 0; cum = 0.0
            for (yr, fr) in buys:
                cum += fr
                end = min(n, round(cum*n)) if cum < 0.999 else n
                for t in items[start:end]:
                    out.append((t[1], t[2], t[3], t[4], yr, t[5]))
                start = end
    return out

def removed_by(k):
    return {it.get('rm') for yr in _Y[:k] for it in yr['items'] if it.get('rm')} | \
           {r for yr in _Y[:k] for it in yr['items'] for r in it.get('rms', [])}

def DOGS_DONE(k):
    return {it.get('wp') for yr in _Y[:k] for it in yr['items'] if it.get('wp') == 8}

def phase_svg(k):
    return year_svg(k)

def year_svg(k, years=None):
    """Top-down render at the end of year k of one scenario's schedule (the default scenario if years is None)."""
    global _Y
    _Y = years if years is not None else SC.YEARS
    setup()
    W, H = (XB-XA)*SS, (YB-YA)*SS
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(W)} {f(H)}" class="phase" role="img" aria-label="Top-down render of the garden">']
    rnd0 = random.Random(4)
    blades = ''.join(f'<path d="M{rnd0.uniform(1,15):.1f},{rnd0.uniform(3,15):.1f} l-1,-2.4 m1,2.4 l1,-2.6" stroke="#a9bf84" stroke-width=".6"/>' for _ in range(10))
    o.append(f'<defs><pattern id="pturf" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="#cfdcae"/>{blades}</pattern></defs>')
    clip = box(XA, YA, XB, YB)
    # ground: lawn everywhere, road, neighbor lots
    o.append(f'<rect width="{f(W)}" height="{f(H)}" fill="url(#pturf)"/>')
    RC, RR = (-22.0, -21.0), 25.0
    quad = box(-90, -90, RC[0], RC[1])
    road = unary_union([box(-200, -200, 200, -46.0), box(-200, -200, -47.0, 200), quad.difference(Point(*RC).buffer(RR, resolution=48))])
    road = road.difference(box(-48, 71.6, 72, 300)).difference(box(113.6, -48, 300, 300)).intersection(clip)
    o.append(f'<path d="{R.path_d(road)}" fill="#bdbcb6"/>')
    curb = unary_union([box(RC[0], -48.0, 200, -46.0), box(-49.0, RC[1], -47.0, 200),
                        quad.intersection(Point(*RC).buffer(RR+2, resolution=48)).difference(Point(*RC).buffer(RR, resolution=48))]).intersection(clip)
    o.append(f'<path d="{R.path_d(curb)}" fill="#e2e0d8"/>')
    nb = box(-48, 71.6, 72, 300).union(box(113.6, -48, 300, 300)).difference(Lo.parcel.buffer(.01)).intersection(clip)
    o.append(f'<path d="{R.path_d(nb)}" fill="#c7d4a6"/>')
    # neighbor houses (schematic roofs)
    for hb in [box(-20, 73, 58, 112), box(115.5, -20, 122, 60)]:
        o.append(f'<path d="{R.path_d(hb.intersection(clip))}" fill="#a9a59c" stroke="#7d796f" stroke-width=".8"/>')
    # built beds
    BEDS, ROCKS, PATHS, _b = year_state(k)
    built_z = [SC.WP_ZONE[wp] for wp in BEDS]
    beds = unary_union([IR.Z[z] for z in built_z]) if built_z else None
    if beds is not None and not beds.is_empty:
        o.append(f'<path d="{R.path_d(beds)}" fill="#9b7a55" stroke="#6e5538" stroke-width=".9"/>')
    # tree basins for oaks (phase 1)
    for c, x, y, r in Lo.ROW_TREES:
        o.append(f'<path d="{R.path_d(Point(x, y).buffer(3.5))}" fill="#9b7a55"/>')
    # rock band
    for ph, g in P.ROCK.items():
        if {2: 2, 3: 3}[ph] in ROCKS:
            o.append(f'<path d="{R.path_d(g)}" fill="#d9d5cb" stroke="#a9a397" stroke-width=".6"/>')
    # deck, pool, building, walks
    o.append(f'<path d="{R.path_d(Lo.deck)}" fill="#efe9dc" stroke="#5f5a50" stroke-width="1.2"/>')
    o.append(f'<path d="{R.path_d(Lo.pool)}" fill="#7fc3d6" stroke="#4a8fa3" stroke-width="1"/>')
    o.append(f'<path d="{R.path_d(Lo.pool.buffer(-1.5))}" fill="#9fd5e3"/>')
    o.append(f'<path d="{R.path_d(Lo.restroom.difference(Lo.patio))}" fill="#b9b2a5" stroke="#6f685c" stroke-width="1"/>')
    o.append(f'<path d="{R.path_d(Lo.patio)}" fill="#d6d1c6" stroke="#6f685c" stroke-width=".8"/>')
    o.append(f'<path d="{R.path_d(Lo.walk_full)}" fill="#e6e3da" stroke="#9c978b" stroke-width=".7"/>')
    o.append(f'<path d="{R.path_d(Lo.kiosk_walk)}" fill="#e6e3da" stroke="#9c978b" stroke-width=".7"/>')
    o.append(f'<path d="{R.path_d(Lo.kiosk_pad)}" fill="#e6e3da"/>')
    o.append(f'<path d="{R.path_d(Lo.kiosk_box)}" fill="#8f8a80" stroke="#5f5a50" stroke-width=".8"/>')
    u = box(Lo.UTIL[0]-2.0, Lo.UTIL[1]-1.4, Lo.UTIL[0]+2.0, Lo.UTIL[1]+1.4)
    o.append(f'<path d="{R.path_d(u)}" fill="#5f8a59" stroke="#3d5a39" stroke-width=".7"/>')
    # path pieces
    for ph in P.PATH_REG:
        if ph in PATHS:
            g = P.path_phase_geom(ph)
            o.append(f'<path d="{R.path_d(g)}" fill="#e3cf9f" stroke="#a88b55" stroke-width=".8"/>')
    # dog rest area
    _, _, _PATHS2, _ = year_state(k)
    if 8 in DOGS_DONE(k):
        o.append(f'<path d="{R.path_d(Lo.dog_poly)}" fill="#e3cf9f" stroke="#a88b55" stroke-width=".8"/>')
        sx, sy = px(*Lo.DOG_STATION)
        o.append(f'<rect x="{f(sx-3)}" y="{f(sy-3)}" width="6" height="6" rx="1" fill="#3d6b4a"/><circle cx="{f(sx+7)}" cy="{f(sy)}" r="2.6" fill="#555"/>')
        from shapely import affinity as _af
        bb = _af.translate(Polygon([(-2.5, -.8), (2.5, -.8), (2.5, .8), (-2.5, .8)]), *Lo.DOG_BENCH)
        o.append(f'<path d="{R.path_d(bb)}" fill="#6e5238"/>')
    # benches
    from shapely import affinity
    for b in Lo.BENCHES[:-1]:
        ph = {Lo.N1: 4, Lo.N2: 6, Lo.N3: 7}[min((Lo.N1, Lo.N2, Lo.N3), key=lambda n: b.centroid.distance(Point(*n)))]
        if ph not in PATHS: continue
        o.append(f'<path d="{R.path_d(b)}" fill="#6e5238"/>')
    # plants (cumulative, sized by age)
    for (c, x, y, r, yb, is_ind) in plant_points(k):
        age = k - yb
        col = Lo.PAL[c][6]
        if is_ind:
            base = {'MF': 2.6, 'VO': 3.6, 'HP': 2.6, 'AE': 2.8, 'CA': 2.6, 'SR': 2.8, 'SB': 2.7, 'IVH': 1.45, 'MFT': 6.5}[c]
            rr = base*growth(c, age)
            o.append(canopy_blob((x, y), max(3, rr), 77, col, .9) if c == 'MFT' else symbol(c, x, y, rr, col))
        else:
            o.append(symbol(c, x, y, r*growth(c, age), col))
    # existing trees (always)
    for i, p in enumerate(Lo.PITTOS):
        o.append(canopy_blob(p, Lo.PITTO_R, 24+i, '#4f7d47'))
    o.append(canopy_blob(Lo.NBR_TREE[0], Lo.NBR_TREE[1], 23, '#4a7442'))
    # giant yucca (kept): ~15 ft spread
    o.append(canopy_blob(Lo.YUCCA, Lo.YUCCA_SPREAD, 31, '#7f9a6c', .75))
    # remove-later items still standing at the end of year k
    gone = removed_by(k)
    for it in Lo.REMOVE:
        if it['id'] in gone: continue
        if it['kind'] == 'palm':
            o.append(palm_render(*it['xy'], r=5.5))
        else:
            o.append(symbol('IV', it['xy'][0], it['xy'][1], it['r'], '#7e8f5e'))
    oak = R.OAK_CANOPY.buffer(-4, resolution=24).buffer(6, resolution=24).intersection(box(-60, -60, 40, 40))
    from shapely import affinity
    o.append(f'<path d="{R.path_d(affinity.translate(oak, 2, -2))}" fill="#1d2a17" fill-opacity=".08"/>')
    o.append(f'<path d="{R.path_d(oak)}" fill="#40693b" fill-opacity=".42" stroke="#2c4a28" stroke-width="1"/>')
    rnd = random.Random(9)
    minx, miny, maxx, maxy = oak.bounds
    for _ in range(420):
        x, y = rnd.uniform(minx, maxx), rnd.uniform(miny, maxy)
        if oak.buffer(-1).contains(Point(x, y)):
            cx, cy = px(x, y)
            o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rnd.uniform(1.5,3.2))}" fill="{rnd.choice(["#567f4c","#35592f","#5f8a54"])}" fill-opacity=".3"/>')
    # new live oaks, canopy grows each year
    for c, x, y, r in Lo.ROW_TREES:
        age = k - 1
        rad = min(r, 4.5 + 1.5*age)
        o.append(canopy_blob((x, y), rad, int(x*3+y), '#4c7a43', .62))
    for p in Lo.PALMS:
        o.append(palm_render(*p))
    o.append(palm_render(*Lo.QUEEN))      # queen palm stays until it dies
    # parcel line (subtle)
    o.append(f'<path d="{R.path_d(Lo.parcel)}" fill="none" stroke="#7a3b26" stroke-width="1" stroke-dasharray="8 3 2 3" opacity=".55"/>')
    o.append('</svg>')
    return '\n'.join(o)

def palm_render(x, y, r=7):
    cx, cy = px(x, y); rp = r*SS; segs = []
    for i in range(12):
        a = 2*math.pi*i/12
        ex, ey = cx+math.cos(a)*rp, cy+math.sin(a)*rp
        segs.append(f'M{f(cx)},{f(cy)} Q{f(cx+math.cos(a+.3)*rp*.6)},{f(cy+math.sin(a+.3)*rp*.6)} {f(ex)},{f(ey)}')
    return (f'<circle cx="{f(cx+3)}" cy="{f(cy+3)}" r="{f(rp*.8)}" fill="#1d2a17" fill-opacity=".18"/>'
            f'<path d="{" ".join(segs)}" fill="none" stroke="#5d8a3e" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="{" ".join(segs)}" fill="none" stroke="#8cb062" stroke-width=".9"/>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="2.2" fill="#6d5a3a"/>')

if __name__ == '__main__':
    for k in range(1, len(SC.YEARS)+1):
        open(f'year{k}.svg', 'w').write(year_svg(k))
    print('ok')