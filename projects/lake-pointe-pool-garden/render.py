"""Render the planting plan and irrigation plan as SVG strings."""
import math, random
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box, MultiPolygon
from shapely.ops import unary_union
import layout as Lo

random.seed(3)
S = 5.6                                   # px per foot
X0, X1, Y0, Y1 = -104, 168, -64, 153      # drawing extents (ft), label columns at both sides
W, H = (X1-X0)*S, (Y1-Y0)*S
def px(x, y): return ((x-X0)*S, (Y1-y)*S)
def f(v): return f'{v:.1f}'

def path_d(geom):
    out = []
    polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
    for p in polys:
        if p.is_empty or p.geom_type != 'Polygon': continue
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            out.append('M' + ' L'.join(f'{f(px(*c)[0])},{f(px(*c)[1])}' for c in cs) + 'Z')
    return ' '.join(out)
def line_d(ls):
    cs = list(ls.coords)
    return 'M' + ' L'.join(f'{f(px(*c)[0])},{f(px(*c)[1])}' for c in cs)

def shade(hexc, k):
    h = hexc.lstrip('#'); r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    if k < 0: r, g, b = (int(c*(1+k)) for c in (r, g, b))
    else: r, g, b = (int(c + (255-c)*k) for c in (r, g, b))
    return f'#{r:02x}{g:02x}{b:02x}'

GRASS = {'MC', 'EE', 'TF', 'SR', 'SB'}
def plant_symbol(code, x, y, r, col, mode):
    cx, cy = px(x, y); rp = r*S
    if mode == 'irr':
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="var(--sym-mute)" stroke="var(--line-faint)" stroke-width=".4"/>'
    if code in GRASS:
        spokes = 11 if code in ('SR', 'SB') else 9
        segs = []
        for i in range(spokes):
            a = 2*math.pi*i/spokes + random.uniform(-.15, .15)
            segs.append(f'M{f(cx)},{f(cy)} l{f(math.cos(a)*rp)},{f(math.sin(a)*rp)}')
        return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp*.92)}" fill="{shade(col,.55)}" fill-opacity=".85"/>'
                f'<path d="{" ".join(segs)}" stroke="{shade(col,-.35)}" stroke-width=".7" fill="none"/>')
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="{col}" fill-opacity=".78" stroke="{shade(col,-.4)}" stroke-width=".6"/>'
            f'<circle cx="{f(cx-rp*.25)}" cy="{f(cy-rp*.25)}" r="{f(rp*.28)}" fill="#fff" fill-opacity=".35"/>')

def shrub_symbol(code, x, y, mode):
    col = Lo.PAL[code][6]
    sp = Lo.PAL[code][4]
    r = {'MF': 2.6, 'VO': 3.4, 'HP': 2.6, 'AE': 2.8, 'CA': 2.6, 'SR': 2.8, 'SB': 2.7, 'IVH': 1.45, 'MFT': 6.5}[code]
    cx, cy = px(x, y); rp = r*S
    if mode == 'irr':
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="var(--sym-mute)" stroke="var(--line-faint)" stroke-width=".5"/>'
    if code in ('SR', 'SB'):
        return plant_symbol(code, x, y, r, col, mode)
    if code == 'MFT':
        n = 18; pts = []
        for i in range(n*2):
            a = math.pi*i/n; rr = rp*(1 if i % 2 == 0 else .86)
            pts.append(f'{f(cx+math.cos(a)*rr)},{f(cy+math.sin(a)*rr)}')
        return (f'<polygon points="{" ".join(pts)}" fill="{shade(col,.35)}" fill-opacity=".8" stroke="{shade(col,-.35)}" stroke-width=".9"/>'
                f'<circle cx="{f(cx)}" cy="{f(cy)}" r="2.2" fill="{shade(col,-.5)}"/>')
    # scalloped shrub
    n = 9; pts = []
    for i in range(n*3):
        a = 2*math.pi*i/(n*3); rr = rp*(1 - .09*abs(math.sin(i*math.pi/3)))
        pts.append(f'{f(cx+math.cos(a)*rr)},{f(cy+math.sin(a)*rr)}')
    return (f'<polygon points="{" ".join(pts)}" fill="{col}" fill-opacity=".82" stroke="{shade(col,-.42)}" stroke-width=".8"/>'
            f'<circle cx="{f(cx-rp*.3)}" cy="{f(cy-rp*.3)}" r="{f(rp*.3)}" fill="#fff" fill-opacity=".3"/>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="1.1" fill="{shade(col,-.55)}"/>')

def row_oak(code, x, y, rm, mode):
    cx, cy = px(x, y); rp = 4.5*S; col = Lo.PAL[code][6]
    ring = (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rm*S)}" fill="{col}" fill-opacity=".05" stroke="{col}" stroke-width="1.1" stroke-dasharray="6 4" pointer-events="none"/>')
    if mode == 'irr':
        return ring + f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="var(--sym-mute)" stroke="var(--line-faint)" stroke-width=".6"/>'
    n = 16; pts = []
    for i in range(n*2):
        a = math.pi*i/n; rr = rp*(1 if i % 2 == 0 else .84)
        pts.append(f'{f(cx+math.cos(a)*rr)},{f(cy+math.sin(a)*rr)}')
    return (ring + f'<polygon points="{" ".join(pts)}" fill="{R_shade(col,.25)}" fill-opacity=".85" stroke="{R_shade(col,-.35)}" stroke-width="1"/>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="2.4" fill="{R_shade(col,-.5)}"/>')
def R_shade(c, k): return shade(c, k)

def palm(x, y, r=7.5, mode='plant'):
    cx, cy = px(x, y); rp = r*S; segs = []
    for i in range(14):
        a = 2*math.pi*i/14
        ex, ey = cx+math.cos(a)*rp, cy+math.sin(a)*rp
        mx, my = cx+math.cos(a+.25)*rp*.6, cy+math.sin(a+.25)*rp*.6
        segs.append(f'M{f(cx)},{f(cy)} Q{f(mx)},{f(my)} {f(ex)},{f(ey)}')
    stroke = 'var(--line-faint)' if mode == 'irr' else 'var(--ink)'
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="none" stroke="{stroke}" stroke-width=".5" stroke-dasharray="2 2"/>'
            f'<path d="{" ".join(segs)}" fill="none" stroke="{stroke}" stroke-width=".8"/>'
            f'<circle cx="{f(cx)}" cy="{f(cy)}" r="2" fill="{stroke}"/>')

def yucca(x, y, mode='plant'):
    cx, cy = px(x, y); o = []
    stroke = 'var(--line-faint)' if mode == 'irr' else '#4f6b4a'
    o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(Lo.YUCCA_SPREAD*S)}" fill="#c9d8b8" fill-opacity=".25" stroke="{stroke}" stroke-width=".7" stroke-dasharray="3 2"/>')
    o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(Lo.YUCCA_RING*S)}" fill="none" stroke="var(--ink)" stroke-width=".6" stroke-dasharray="1.5 1.5"/>')
    for k, (dx, dy) in enumerate([(-1.2, .6), (1.1, .9), (.2, -1.2)]):
        hx, hy = px(x+dx*1.6, y+dy*1.6)
        segs = []
        for i in range(16):
            a = 2*math.pi*i/16 + k*.2; rr = 2.6*S
            segs.append(f'M{f(hx)},{f(hy)} l{f(math.cos(a)*rr)},{f(math.sin(a)*rr)}')
        o.append(f'<path d="{" ".join(segs)}" stroke="{stroke}" stroke-width=".8" fill="none"/><circle cx="{f(hx)}" cy="{f(hy)}" r="1.8" fill="{stroke}"/>')
    return ''.join(o)

DUMP_LBL = 5.6
def removal_mark(c, r, dashed=True):
    cx, cy = px(*c); k = r*S*.45
    return (f'<path d="M{f(cx-k)},{f(cy-k)} L{f(cx+k)},{f(cy+k)} M{f(cx-k)},{f(cy+k)} L{f(cx+k)},{f(cy-k)}" stroke="#b5462f" stroke-width="1.3"/>')

def removal(it, mode='plant'):
    cx, cy = px(*it['xy']); rp = it['r']*S
    col = 'var(--line-faint)' if mode == 'irr' else '#b5462f'
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rp)}" fill="#fff" fill-opacity=".35" stroke="{col}" stroke-width="1.1" stroke-dasharray="4 2.5"/>'
            + removal_mark(it['xy'], min(it['r'], 2.2)))

def blob(c, r, seed, wob=.12, n=60):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    return Polygon([(c[0]+r*(1+wob*math.sin(3*a+ph[0])+wob*.6*math.sin(5*a+ph[1])+wob*.4*math.sin(7*a+ph[2]))*math.cos(a),
                     c[1]+r*(1+wob*math.sin(3*a+ph[0])+wob*.6*math.sin(5*a+ph[1])+wob*.4*math.sin(7*a+ph[2]))*math.sin(a))
                    for a in np.linspace(0, 2*math.pi, n, endpoint=False)])

from shapely import affinity as _aff
# existing live oak canopy, ~55-60 ft wide (photo estimate), centred near the trunk
OAK_CANOPY = _aff.scale(Polygon([(-47,-14),(-41,-33),(-26,-45),(-6,-44),(11,-38),(19,-28),(14,-18),(3,-9),(-2,1),(-7,11),(-13,19),(-23,23),(-35,21),(-46,11),(-49,-1)]).buffer(3).buffer(-1.5), .86, .86, origin=Lo.OAK)
def canopy(geom, label_xy=None, cls='canopy'):
    cx, cy = px(*geom.centroid.coords[0])
    return (f'<path d="{path_d(geom)}" fill="url(#hatch)" stroke="var(--ink)" stroke-width=".9" stroke-dasharray="7 3 1.5 3" class="{cls}"/>')

def text(x, y, s, cls='lbl', anchor='start', extra=''):
    cx, cy = px(x, y)
    return f'<text x="{f(cx)}" y="{f(cy)}" class="{cls}" text-anchor="{anchor}" {extra}>{s}</text>'

# ---------------------------------------------------------------- base layers
def base(mode):
    o = []
    # street context (lawn runs to the curb; no public sidewalks)
    RC, RR = (-22.0, -21.0), 25.0          # curb return (measured on the 2025 aerial)
    quad = box(-90, -90, RC[0], RC[1])
    road = unary_union([box(-200, -200, 200, -46.0), box(-200, -200, -47.0, 200),
                        quad.difference(Point(*RC).buffer(RR, resolution=48))])
    gutter = unary_union([box(RC[0], -48.0, 200, -46.0), box(-49.0, RC[1], -47.0, 200),
                          quad.intersection(Point(*RC).buffer(RR+2, resolution=48)).difference(Point(*RC).buffer(RR, resolution=48))])
    road = road.difference(box(-48, 71.6, 72, 300)).difference(box(113.6, -48, 300, 300))
    clip = box(X0+44, Y0, X1, Y1)
    o.append(f'<path d="{path_d(road.intersection(clip))}" fill="var(--road)"/>')
    o.append(f'<path d="{path_d(gutter.intersection(clip))}" fill="var(--concrete)" stroke="var(--line-faint)" stroke-width=".5"/>')
    o.append(text(46, -44.6, 'right-of-way lawn to curb', 'zonesub', 'middle'))
    o.append(text(40, -56, 'MYRTLEWOOD ROAD', 'street', 'middle'))
    o.append(text(-55, 70, 'CYPRESS POINT DRIVE', 'street', 'middle', f'transform="rotate(-90 {f(px(-55,70)[0])} {f(px(-55,70)[1])})"'))
    # neighbor lots
    o.append(f'<path d="{path_d(box(-48,71.6,72,153).union(box(113.6,-48,168,153)).difference(Lo.parcel.buffer(.01)).intersection(box(X0+44,Y0,X1,Y1)))}" fill="var(--nbr)"/>')
    o.append(text(20, 84, 'ADJACENT RESIDENCE', 'nbr', 'middle'))
    o.append(text(145, 128, 'ADJACENT RESIDENCE', 'nbr', 'middle'))
    # beds (mulch) and lawn
    o.append('<g class="hit" data-k="f:bed">'); o.append(f'<path d="{path_d(Lo.plantable.union(Lo.mulch_only).union(Lo.access_gc))}" fill="var(--mulch)" stroke="var(--edge)" stroke-width="1.1"/>'); o.append('</g>')
    lawn = Lo.wing.difference(Lo.util_bed)
    o.append('<g class="hit" data-k="f:doglawn">'); o.append(f'<path d="{path_d(lawn)}" fill="url(#turf)" stroke="var(--edge)" stroke-width=".8"/>'); o.append('</g>')
    o.append('<g class="hit" data-k="f:maint">'); o.append(f'<path d="{path_d(Lo.maint)}" fill="url(#turf)" stroke="var(--edge)" stroke-width=".8" stroke-dasharray="4 2"/>'); o.append('</g>')
    if mode == 'plant':
        o.append(text(20, 68.4, '5 FT NEIGHBOR MAINTENANCE STRIP · lawn, no plants', 'mstrip', 'middle'))
        mx, my = px(110.7, 20)
        o.append(f'<text x="{f(mx)}" y="{f(my)}" class="mstrip" text-anchor="middle" transform="rotate(-90 {f(mx)} {f(my)})">5 FT NEIGHBOR MAINTENANCE STRIP · lawn, no plants</text>')
    # rock band
    o.append('<g class="hit" data-k="f:rock">'); o.append(f'<path d="{path_d(Lo.rock.intersection(Lo.parcel))}" fill="url(#pebble)" stroke="var(--edge)" stroke-width=".8"/>'); o.append('</g>')
    # deck, pool, restroom
    o.append('<g class="hit" data-k="f:deck">'); o.append(f'<path d="{path_d(Lo.deck)}" fill="url(#deckpat)" stroke="var(--ink)" stroke-width="1.6"/>'); o.append('</g>')
    o.append('<g class="hit" data-k="f:pool">'); o.append(f'<path d="{path_d(Lo.pool)}" fill="var(--water)" stroke="var(--ink)" stroke-width="1"/>'); o.append('</g>')
    o.append(f'<path d="{path_d(Lo.pool.buffer(-1.2))}" fill="none" stroke="var(--water-edge)" stroke-width=".8"/>')
    o.append('<g class="hit" data-k="f:restroom">'); o.append(f'<path d="{path_d(Lo.restroom.difference(Lo.patio))}" fill="url(#roof)" stroke="var(--ink)" stroke-width="1.2"/>'); o.append('</g>')
    o.append('<g class="hit" data-k="f:patio">'); o.append(f'<path d="{path_d(Lo.patio)}" fill="url(#roof2)" stroke="var(--ink)" stroke-width="1"/>'); o.append('</g>')
    rx = (Lo.restroom.bounds[0] + Lo.PATIO_X[0])/2
    o.append(text(rx, 22.0, 'RESTROOM', 'bldg', 'middle'))
    o.append(text(rx, 19.6, 'BUILDING', 'bldg', 'middle'))
    pcx, pcy = px((Lo.PATIO_X[0]+Lo.PATIO_X[1])/2, 20.9)
    o.append(f'<text x="{f(pcx)}" y="{f(pcy)}" class="decksub" text-anchor="middle" transform="rotate(-90 {f(pcx)} {f(pcy)})">COVERED PATIO</text>')
    o.append(text(52, 21.3, 'POOL', 'poolt', 'middle'))
    o.append(text(42, 36.0, 'POOL DECK  ·  NO PLANTING', 'decklbl', 'middle'))
    o.append(text(42, 33.6, '(fenced, 77 x 40 ft, from county building sketch)', 'decksub', 'middle'))
    # fence posts along the real fence line (not the building walls)
    ex = Lo.FENCE_LINE
    tick = []
    for s_ in np.arange(0, ex.length + .1, 6):
        p = ex.interpolate(s_); cx, cy = px(p.x, p.y)
        tick.append(f'<rect x="{f(cx-1.3)}" y="{f(cy-1.3)}" width="2.6" height="2.6" fill="var(--ink)"/>')
    o.append(''.join(tick))
    # gate post -> corner post: framed panel with black privacy screen
    a_, b_ = px(Lo.GATE[0][0], Lo.GATE[0][1]), px(*Lo.FENCE_CORNER)
    o.append(f'<line x1="{f(a_[0])}" y1="{f(a_[1])}" x2="{f(b_[0])}" y2="{f(b_[1])}" stroke="var(--ink)" stroke-width="3.2"/>')
    # concrete walks (entry walk to the curb + restroom walk to the pool gate)
    o.append('<g class="hit" data-k="f:walk">'); o.append(f'<path d="{path_d(Lo.walk_full)}" fill="var(--concrete)" stroke="var(--ink)" stroke-width="1"/>'); o.append('</g>')
    for xj in np.arange(Lo.CURB_X + 5, Lo.GATE[0][0] - 1, 5):
        a = px(xj, Lo.WALK_Y[0]); b = px(xj, Lo.WALK_Y[1])
        o.append(f'<line x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}" stroke="var(--line-faint)" stroke-width=".6"/>')
    # pool gate: opening + swing arc (swings out, onto the walk)
    (gx, gy0), (_, gy1) = Lo.GATE
    gl = gy1 - gy0
    A, B = px(gx, gy0), px(gx, gy1)
    C = px(gx - gl, gy0)
    o.append('<g class="hit" data-k="f:gate">'
             f'<line x1="{f(A[0])}" y1="{f(A[1])}" x2="{f(B[0])}" y2="{f(B[1])}" stroke="var(--paper)" stroke-width="3"/>'
             f'<line x1="{f(A[0])}" y1="{f(A[1])}" x2="{f(C[0])}" y2="{f(C[1])}" stroke="var(--ink)" stroke-width="1.4"/>'
             f'<path d="M{f(C[0])},{f(C[1])} A{f(gl*S)},{f(gl*S)} 0 0 1 {f(B[0])},{f(B[1])}" fill="none" stroke="var(--ink)" stroke-width=".7" stroke-dasharray="2 1.5"/>'
             f'<circle cx="{f(A[0])}" cy="{f(A[1])}" r="1.8" fill="var(--ink)"/><circle cx="{f(B[0])}" cy="{f(B[1])}" r="1.8" fill="var(--ink)"/></g>')
    o.append(text(gx + 1.4, gy1 - 0.9, 'POOL GATE', 'decksub'))
    o.append('<g class="hit" data-k="f:kioskwalk">'); o.append(f'<path d="{path_d(Lo.kiosk_walk)}" fill="var(--concrete)" stroke="var(--ink)" stroke-width=".9"/>'); o.append('</g>')
    o.append('<g class="hit" data-k="f:kiosk">'); o.append(f'<path d="{path_d(Lo.kiosk_pad)}" fill="var(--concrete)" stroke="var(--ink)" stroke-width=".8"/>'); o.append('</g>')
    o.append('<g class="hit" data-k="f:kiosk">'); o.append(f'<path d="{path_d(Lo.kiosk_box)}" fill="url(#roof)" stroke="var(--ink)" stroke-width="1"/>'); o.append('</g>')
    # nature path
    o.append('<g class="hit" data-k="f:path">'); o.append(f'<path d="{path_d(Lo.path_poly)}" fill="url(#dg)" stroke="var(--ink)" stroke-width="1"/>'); o.append('</g>')
    # benches at nodes
    for b in Lo.BENCHES[:-1]:
        o.append('<g class="hit" data-k="f:bench">'); o.append(f'<path d="{path_d(b)}" fill="var(--bench)" stroke="var(--ink)" stroke-width=".7"/>'); o.append('</g>')
    # dog rest area pad + spur
    o.append('<g class="hit" data-k="f:dogpad">'); o.append(f'<path d="{path_d(Lo.dog_poly)}" fill="url(#dg)" stroke="var(--ink)" stroke-width="1"/>'); o.append('</g>')
    from shapely import affinity as _af
    bb = _af.translate(Polygon([(-2.5, -.8), (2.5, -.8), (2.5, .8), (-2.5, .8)]), *Lo.DOG_BENCH)
    o.append('<g class="hit" data-k="f:bench">'); o.append(f'<path d="{path_d(bb)}" fill="var(--bench)" stroke="var(--ink)" stroke-width=".7"/>'); o.append('</g>')
    sx, sy = px(*Lo.DOG_STATION)
    o.append('<g class="hit" data-k="f:dogstation">')
    o.append(f'<rect x="{f(sx-4)}" y="{f(sy-4)}" width="8" height="8" rx="1.5" fill="#3d6b4a" stroke="var(--ink)" stroke-width=".7"/>'
             f'<circle cx="{f(sx+9)}" cy="{f(sy)}" r="3.6" fill="#555" stroke="var(--ink)" stroke-width=".7"/>')
    o.append('</g>')
    # community irrigation pump (green box); possible true position ~8 ft east shown dashed
    if mode == 'plant':
        o.append('<g class="hit" data-k="f:pumpway">'); o.append(f'<path d="{path_d(Lo.pump_corridor.union(Lo.pump_front))}" fill="none" stroke="#4d6b3a" stroke-width=".8" stroke-dasharray="3 2"/>'); o.append('</g>')
    u = box(Lo.UTIL[0]-2.0, Lo.UTIL[1]-1.4, Lo.UTIL[0]+2.0, Lo.UTIL[1]+1.4)
    ua = box(Lo.UTIL_ALT[0]-2.0, Lo.UTIL_ALT[1]-1.4, Lo.UTIL_ALT[0]+2.0, Lo.UTIL_ALT[1]+1.4)
    o.append(f'<path d="{path_d(ua)}" fill="none" stroke="#3d6b4a" stroke-width=".8" stroke-dasharray="2 2"/>')
    o.append('<g class="hit" data-k="f:util">'); o.append(f'<path d="{path_d(u)}" fill="#6f9a6a" stroke="var(--ink)" stroke-width=".9"/>'); o.append('</g>')
    if mode == 'plant':
        o.append(text(Lo.UTIL_ALT[0]+2.6, Lo.UTIL_ALT[1]-0.8, 'or ~8 ft E?', 'tiny'))
    # pool dump valve: flexible service area (low groundcover only, no path base), stepping stones
    o.append('<g class="hit" data-k="f:dump">')
    o.append(f'<path d="{path_d(Lo.service)}" fill="none" stroke="#2f6f9c" stroke-width="1.1" stroke-dasharray="5 2.5"/>')
    for g in Lo.stone_geoms:
        o.append(f'<path d="{path_d(g)}" fill="#d8d4ca" stroke="var(--ink)" stroke-width=".6"/>')
    dx, dy = px(*Lo.DUMP)
    o.append(f'<circle cx="{f(dx)}" cy="{f(dy)}" r="3.4" fill="#fff" stroke="#2f6f9c" stroke-width="1.3"/><rect x="{f(dx+4)}" y="{f(dy-2.5)}" width="7" height="5" fill="#fff" stroke="#2f6f9c" stroke-width=".9"/></g>')
    if mode == 'plant':
        o.append(text(Lo.DUMP[0], Lo.DUMP[1]-DUMP_LBL, 'DUMP VALVE', 'tiny', 'middle'))
    # irrigation valve markers (white PVC stubs over buried control valves)
    for m in Lo.MARKERS:
        mx_, my_ = px(*m)
        o.append('<g class="hit" data-k="f:marker">'
                 f'<path d="{path_d(Point(*m).buffer(Lo.MARKER_R))}" fill="none" stroke="#2f6f9c" stroke-width=".8" stroke-dasharray="3 2"/>'
                 f'<circle cx="{f(mx_)}" cy="{f(my_)}" r="3" fill="#fff" stroke="var(--ink)" stroke-width="1.1"/>'
                 f'<circle cx="{f(mx_)}" cy="{f(my_)}" r="1" fill="var(--ink)"/></g>')
    # HOA notice board (restroom south wall) and "No parking on grass" sign
    nx, ny = px(*Lo.NOTICE)
    o.append(f'<g class="hit" data-k="f:notice"><rect x="{f(nx-11)}" y="{f(ny-1)}" width="22" height="3.6" fill="#7a5b3a" stroke="var(--ink)" stroke-width=".6"/></g>')
    sx_, sy_ = px(*Lo.NOPARK)
    o.append(f'<g class="hit" data-k="f:nopark"><rect x="{f(sx_-3)}" y="{f(sy_-3)}" width="6" height="6" fill="#fff" stroke="#b5462f" stroke-width="1.2"/><circle cx="{f(sx_)}" cy="{f(sy_)}" r="7" fill="#fff" fill-opacity=".01"/></g>')
    # parcel line
    o.append(f'<path d="{path_d(Lo.parcel)}" fill="none" stroke="var(--pl)" stroke-width="1.6" stroke-dasharray="14 4 3 4"/>')
    return o

def overlays(mode):
    o = []
    # existing canopies (hatched)
    o.append(canopy(OAK_CANOPY.intersection(box(-48, -48, 40, 40))))
    o.append(canopy(blob(Lo.NBR_TREE[0], Lo.NBR_TREE[1], 23, .1).intersection(box(X0+44, Y0, X1, Y1))))
    for i, p in enumerate(Lo.PITTOS):
        o.append(canopy(blob(p, Lo.PITTO_R, 24+i, .12)))
    # shade sail over the NW deck (light outline)
    o.append('<g class="hit" data-k="f:sail">' + f'<path d="{path_d(Lo.SAIL)}" fill="#fff" fill-opacity=".18" stroke="#6b7f8c" stroke-width=".9" stroke-dasharray="6 3"/>' + '</g>')
    if mode == 'plant':
        sc = Lo.SAIL.centroid; o.append(text(sc.x, sc.y + 2.2, 'shade sail', 'decksub', 'middle'))
    for c, key in [(Lo.OAK, 'f:oak')] + [(p, 'f:pitto') for p in Lo.PITTOS]:
        cx, cy = px(*c)
        o.append(f'<g class="hit" data-k="{key}"><circle cx="{f(cx)}" cy="{f(cy)}" r="11" fill="#fff" fill-opacity=".01"/>')
        o.append(f'<path d="M{f(cx-5)},{f(cy-5)} L{f(cx+5)},{f(cy+5)} M{f(cx-5)},{f(cy+5)} L{f(cx+5)},{f(cy-5)}" stroke="var(--ink)" stroke-width="1.2"/></g>')
    # giant yucca: multi-trunk, ~15 ft spread, 3 ft trunk ring with no new plants
    o.append('<g class="hit" data-k="f:yucca">' + yucca(*Lo.YUCCA, mode=mode) + '</g>')
    # existing cabbage palms to remain (pair at the south fence drawn as two trunks)
    for key, p in Lo.CABBAGE:
        r = {'palmpair': 8.5, 'palmgate': 7.0, 'palmne': 7.0, 'palme': 6.0, 'palmn': 6.0}[key]
        o.append(f'<g class="hit" data-k="f:{key}">' + palm(*p, r=r, mode=mode) + '</g>')
    # queen palm: keep until it dies, then remove
    o.append('<g class="hit" data-k="f:queen">' + palm(*Lo.QUEEN, r=7.5, mode=mode) + '</g>')
    # remove-later items (dashed outline + small x)
    for it in Lo.REMOVE:
        o.append(f'<g class="hit" data-k="f:rm_{it["id"]}">' + removal(it, mode) + '</g>')
    for c, x, y, rm in Lo.ROW_TREES:
        o.append(f'<g class="hit" data-k="p:{c}" data-n="1" data-z="row" data-y="1">' + row_oak(c, x, y, rm, mode) + '</g>')
    return o

def hit_points():
    """(key, x, y, radius px) for every point feature; drawn as a top hit layer above drifts and beds."""
    pts = [('f:dump', *Lo.DUMP, 13), ('f:notice', *Lo.NOTICE, 11), ('f:nopark', *Lo.NOPARK, 11),
           ('f:util', *Lo.UTIL, 13), ('f:queen', *Lo.QUEEN, 14), ('f:yucca', *Lo.YUCCA, 14), ('f:oak', *Lo.OAK, 13)]
    pts += [('f:marker', *m, 12) for m in Lo.MARKERS]
    pts += [('f:pitto', *p, 13) for p in Lo.PITTOS]
    pp = [p for k, p in Lo.CABBAGE if k == 'palmpair']
    pts += [(f'f:{k}', *p, 14) for k, p in Lo.CABBAGE if k != 'palmpair']
    pts.append(('f:palmpair', (pp[0][0]+pp[1][0])/2, (pp[0][1]+pp[1][1])/2, 18))
    pts += [(f'f:rm_{it["id"]}', *it['xy'], max(10, it['r']*S*.75)) for it in Lo.REMOVE]
    return pts

def hit_layer():
    o = ['<g class="hitlayer">']
    for k, x, y, r in hit_points():
        cx, cy = px(x, y)
        o.append(f'<g class="hit" data-k="{k}"><circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="#000" fill-opacity="0" stroke="#d9480f" stroke-opacity="0" stroke-width="2"/></g>')
    o.append('</g>')
    return ''.join(o)

def defs():
    pebbles = []
    rnd = random.Random(5)
    for _ in range(26):
        x, y = rnd.uniform(0, 14), rnd.uniform(0, 14); r = rnd.uniform(.8, 1.7)
        pebbles.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r*.75)}" fill="var(--pebble)" stroke="var(--line-faint)" stroke-width=".3"/>')
    dg = ''.join(f'<circle cx="{f(rnd.uniform(0,12))}" cy="{f(rnd.uniform(0,12))}" r="{f(rnd.uniform(.35,.8))}" fill="var(--dg-dot)"/>' for _ in range(22))
    turf = ''.join(f'<path d="M{f(x)},{f(y)} l-1,-2.4 M{f(x)},{f(y)} l1,-2.6" stroke="var(--turf-mark)" stroke-width=".6"/>'
                   for x, y in [(rnd.uniform(1, 15), rnd.uniform(3, 15)) for _ in range(9)])
    return f'''<defs>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="var(--canopy)"/><line x1="0" y1="0" x2="0" y2="7" stroke="var(--hatch)" stroke-width="1"/></pattern>
<pattern id="pebble" width="14" height="14" patternUnits="userSpaceOnUse"><rect width="14" height="14" fill="var(--rock)"/>{''.join(pebbles)}</pattern>
<pattern id="dg" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="var(--dg)"/>{dg}</pattern>
<pattern id="turf" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="var(--turf)"/>{turf}</pattern>
<pattern id="deckpat" width="11.2" height="11.2" patternUnits="userSpaceOnUse" patternTransform="rotate(0)"><rect width="11.2" height="11.2" fill="var(--deck)"/><path d="M0,0 H11.2 M0,0 V11.2" stroke="var(--deck-joint)" stroke-width=".5"/></pattern>
<pattern id="roof2" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#ecebe6"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--roof-line)" stroke-width=".5"/></pattern>
<pattern id="roof" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="6" height="6" fill="var(--roof)"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--roof-line)" stroke-width="1"/></pattern>
</defs>'''

def north_arrow(x, y):
    cx, cy = px(x, y)
    return (f'<g transform="translate({f(cx)},{f(cy)}) rotate(-57)">'
            f'<circle r="22" fill="none" stroke="var(--ink)" stroke-width=".8"/>'
            f'<path d="M0,-30 L7,8 L0,3 L-7,8 Z" fill="var(--ink)"/>'
            f'<text y="-34" text-anchor="middle" class="na">N</text></g>'
            f'<text x="{f(cx)}" y="{f(cy+44)}" text-anchor="middle" class="tiny">TRUE NORTH</text>')

def scale_bar(x, y):
    cx, cy = px(x, y); o = [f'<g transform="translate({f(cx)},{f(cy)})">']
    for i, (a, b) in enumerate([(0, 5), (5, 10), (10, 20), (20, 40)]):
        o.append(f'<rect x="{f(a*S)}" y="0" width="{f((b-a)*S)}" height="6" fill="{"var(--ink)" if i % 2 == 0 else "var(--paper)"}" stroke="var(--ink)" stroke-width=".8"/>')
    for v in (0, 10, 20, 40):
        o.append(f'<text x="{f(v*S)}" y="18" text-anchor="middle" class="tiny">{v}</text>')
    o.append(f'<text x="{f(40*S+8)}" y="7" class="tiny">FEET</text></g>')
    return ''.join(o)

def leader(anchor, lab, side, ly, bot, common):
    ax, ay = px(*anchor)
    if side == 'L':
        lx = px(-62, 0)[0]; tx = px(-64, 0)[0]
        el = px(-58, 0)[0]
        s = (f'<path d="M{f(ax)},{f(ay)} L{f(el)},{f(px(0,ly)[1])} L{f(lx)},{f(px(0,ly)[1])}" class="leader"/>'
             f'<circle cx="{f(ax)}" cy="{f(ay)}" r="1.8" fill="var(--ink)" pointer-events="none"/>'
             f'<text x="{f(tx)}" y="{f(px(0,ly)[1]-1)}" text-anchor="end" class="bot">{bot}</text>'
             f'<text x="{f(tx)}" y="{f(px(0,ly)[1]+9)}" text-anchor="end" class="com">{common}</text>')
    else:
        lx = px(124, 0)[0]; tx = px(126, 0)[0]; el = px(119, 0)[0]
        s = (f'<path d="M{f(ax)},{f(ay)} L{f(el)},{f(px(0,ly)[1])} L{f(lx)},{f(px(0,ly)[1])}" class="leader"/>'
             f'<circle cx="{f(ax)}" cy="{f(ay)}" r="1.8" fill="var(--ink)" pointer-events="none"/>'
             f'<text x="{f(tx)}" y="{f(px(0,ly)[1]-1)}" class="bot">{bot}</text>'
             f'<text x="{f(tx)}" y="{f(px(0,ly)[1]+9)}" class="com">{common}</text>')
    return s