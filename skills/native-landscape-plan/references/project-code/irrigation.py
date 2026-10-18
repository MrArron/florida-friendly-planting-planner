import math, json
from shapely.geometry import Point, LineString, box, Polygon
from shapely.ops import unary_union
import layout as Lo
import render as R
from render import px, f, text

band = Lo.band
rest = Lo.plantable.difference(Lo.band_outer)
lower = box(-60, -60, 130, 20.8); upper = box(-60, 20.8, 130, 160)

Z = {}
Z[1] = rest.intersection(box(-60, 7.5, -1, 160))
Z[2] = rest.intersection(box(-60, -60, 9, 7.5))
Z[7] = rest.intersection(box(-1, 52, 88, 160))
Z[5] = rest.intersection(box(9, -60, 88, 0))
Z[6] = rest.difference(unary_union([Z[1], Z[2], Z[7], Z[5]]))
Z[3] = band.intersection(lower)
Z[4] = band.intersection(upper)
from shapely.geometry import MultiPolygon
def polys(g):
    gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    out = []
    for x in gs:
        if x.geom_type == 'Polygon' and x.area > 1: out.append(x)
        elif x.geom_type == 'MultiPolygon': out += [y for y in x.geoms if y.area > 1]
    return MultiPolygon(out) if len(out) > 1 else out[0]
for k in Z: Z[k] = polys(Z[k])

INFO = {
 1: ('Entry walk & street frontage', 'Part shade → sun', 'Wild coffee, dwarf palmetto, yaupon edging, muhly, lovegrass, wildflowers', '#3d7ea6'),
 2: ('Oak hammock & mail kiosk', 'Shade (under live oak)', 'Wild coffee, shield fern, marlberry, beautyberry, saw palmetto', '#6b5ca5'),
 3: ('Pool band · SW half', 'Sun', 'Twinflower, dwarf yaupon, dwarf Fakahatchee, muhly, lovegrass', '#2f9c8f'),
 4: ('Pool band · NE half', 'Sun / afternoon shade', 'Twinflower, dwarf yaupon, dwarf Fakahatchee, muhly, lovegrass', '#7aa33a'),
 5: ('South-street pollinator meadow', 'Full sun', 'Wildflower meadow + viburnum clusters', '#d08a2a'),
 6: ('SE butterfly garden', 'Sun / part shade', 'Firebush, porterweed, sage, goldenrod, muhly', '#c4553b'),
 7: ('NE garden walk', 'Part shade', 'Dwarf Fakahatchee, muhly, lovegrass, sage, blanket flower', '#a14f8c'),
}
VALVES = {'A': (-1.5, 2.0), 'B': (-1.5, 36.0), 'C': (50.0, 43.15), 'D': (79.0, -1.5)}
ZV = {1: 'B', 2: 'A', 3: 'A', 4: 'C', 5: 'D', 6: 'D', 7: 'C'}
POC = (-1.5, 26.0)
from shapely.geometry import MultiLineString
MAIN_N = LineString([POC, (-1.5, 43.15), (50.0, 43.15)])          # POC -> valve B -> valve C
MAIN_S = LineString([POC, (-1.5, -1.5), (79.0, -1.5)])            # POC -> (bore under walk) -> valve A -> valve D
MAIN = MultiLineString([MAIN_N, MAIN_S])

HEAD = {
 1: [[VALVES['B'], (-10, 36), (-29, 36)], [(-10, 18), (-10, 54)], [(-29, 17), (-29, 63)]],
 2: [[VALVES['A'], (-4.5, 2.5), (-25, 2.5), (-28.5, -8.5)], [(-12, 2.5), (-7.5, -13.5)]],   # hand-dug, stays 10+ ft off the oak trunk
 3: [[VALVES['A'], (-4.5, -4.5), (86.5, -4.5), (86.5, 20.8)], [(-4.5, -4.5), (-4.5, 5.5)]],
 4: [[VALVES['C'], (50, 46.6), (-4.5, 46.6), (-4.5, 14.5)], [(50, 46.6), (86.6, 46.6), (86.6, 20.8)]],
 5: [[VALVES['D'], (79, -15), (12, -15)], [(50, -15), (50, -31.2)], [(14, -31.2), (90, -31.2)]],
 6: [[VALVES['D'], (89, -1.5), (89, -12), (106.5, -12), (106.5, 63)], [(106.5, -12), (106.5, -29)], [(89, -12), (89, 56)]],
 7: [[VALVES['C'], (50, 52), (50, 64.6)], [(-27, 64.6), (88, 64.6)]],
}
ROW = 1.5              # ft between drip rows
EMIT_GPH, EMIT_SP = 0.6, 1.0
PR = 231*EMIT_GPH/(EMIT_SP*12*ROW*12)     # in/hr

zones = []
BUB_GPM = 0.5
for z in sorted(Z):
    if False:
        n = 0
        zones.append(dict(z=z, name=INFO[z][0], expo=INFO[z][1], plants=INFO[z][2], color=INFO[z][3], valve=ZV[z],
                          area=round(Z[z].area), tube=None, emit=2*n, gpm=round(2*n*BUB_GPM, 1), gal=round(2*n*BUB_GPM*5), mins=5, trees=n))
        continue
    a = Z[z].area
    tube = a/ROW
    em = tube/EMIT_SP
    gpm = em*EMIT_GPH/60
    gal_half = a*0.623*0.5
    mins_half = 0.5/PR*60
    zones.append(dict(z=z, name=INFO[z][0], expo=INFO[z][1], plants=INFO[z][2], color=INFO[z][3], valve=ZV[z],
                      area=round(a), tube=round(tube, -1), emit=round(em, -1), gpm=round(gpm, 1),
                      gal=round(gal_half, -1), mins=round(mins_half)))

# sleeves where headers or mainline cross the nature path / concrete
crossings = []
hard = unary_union([Lo.path_poly, Lo.walk_full])
for z, hs in HEAD.items():
    for h in hs:
        ls = LineString(h)
        inter = ls.intersection(hard)
        if inter.is_empty: continue
        parts = list(inter.geoms) if hasattr(inter, 'geoms') else [inter]
        for p in parts:
            if p.length > 0.5: crossings.append((z, p))
crossings.append((3, LineString([(-1.5, 7.5), (-1.5, 12.5)])))   # mainline bore under the concrete walk
sleeve_len = sum(p.length + 4 for z, p in crossings)

def far_points(poly, src, n=2):
    pts = list(poly.exterior.coords) if poly.geom_type == 'Polygon' else [c for g in poly.geoms for c in g.exterior.coords]
    pts.sort(key=lambda p: -math.dist(p, src))
    out = []
    for p in pts:
        if all(math.dist(p, q) > 25 for q in out): out.append(p)
        if len(out) == n: break
    return out

def svg_overlay():
    o = []
    o.append('<defs>')
    for z in Z:
        c = INFO[z][3]
        o.append(f'<pattern id="drip{z}" width="{f(ROW*R.S)}" height="{f(ROW*R.S)}" patternUnits="userSpaceOnUse">'
                 f'<rect width="{f(ROW*R.S)}" height="{f(ROW*R.S)}" fill="{c}" fill-opacity=".13"/>'
                 f'<line x1="0" y1="{f(ROW*R.S/2)}" x2="{f(ROW*R.S)}" y2="{f(ROW*R.S/2)}" stroke="{c}" stroke-width=".7" stroke-opacity=".75"/></pattern>')
    o.append('</defs>')
    for z, g in Z.items():
        c = INFO[z][3]
        o.append(f'<path d="{R.path_d(g)}" fill="url(#drip{z})" stroke="{c}" stroke-width="1.4"/>')
    # headers
    for z, hs in HEAD.items():
        c = INFO[z][3]
        for h in hs:
            o.append(f'<path d="{R.line_d(LineString(h))}" fill="none" stroke="{c}" stroke-width="2.4" stroke-dasharray="9 3"/>')
    # mainline
    for ml in (MAIN_N, MAIN_S):
        o.append(f'<path d="{R.line_d(ml)}" fill="none" stroke="var(--main)" stroke-width="3.4"/>')
    # sleeves
    for z, p in crossings:
        a, b = p.coords[0], p.coords[-1]
        L = math.dist(a, b); ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        a2 = (a[0]-ux*2, a[1]-uy*2); b2 = (b[0]+ux*2, b[1]+uy*2)
        A, B = px(*a2), px(*b2)
        o.append(f'<line x1="{f(A[0])}" y1="{f(A[1])}" x2="{f(B[0])}" y2="{f(B[1])}" stroke="var(--ink)" stroke-width="7" stroke-linecap="butt"/>'
                 f'<line x1="{f(A[0])}" y1="{f(A[1])}" x2="{f(B[0])}" y2="{f(B[1])}" stroke="var(--paper)" stroke-width="4"/>')
    # flush + air relief
    for z, g in Z.items():
        src = VALVES[ZV[z]]
        for i, p in enumerate(far_points(g, src, 2)):
            q = Point(p)
            cx, cy = px(q.x, q.y)
            o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="3.6" fill="var(--paper)" stroke="{INFO[z][3]}" stroke-width="1.4"/>'
                     f'<text x="{f(cx)}" y="{f(cy+2.4)}" class="irrsym" text-anchor="middle" fill="{INFO[z][3]}">F</text>')
    # valves
    for k, (x, y) in VALVES.items():
        cx, cy = px(x, y)
        zs = [z for z, v in ZV.items() if v == k]
        o.append(f'<rect x="{f(cx-9)}" y="{f(cy-6)}" width="18" height="12" rx="2" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.2"/>'
                 f'<path d="M{f(cx-6)},{f(cy-3.5)} L{f(cx+6)},{f(cy+3.5)} L{f(cx+6)},{f(cy-3.5)} L{f(cx-6)},{f(cy+3.5)} Z" fill="var(--ink)"/>')
        lab = f'VALVE BOX {k} · Z{", Z".join(map(str, zs))}'
        dx, dy, anc = {'A': (-4, -3.5, 'end'), 'B': (-4, 3.2, 'end'), 'C': (0, 4.4, 'middle'), 'D': (4, -4.6, 'start')}[k]
        o.append(text(x+dx, y+dy, lab, 'irrlab', anc))
    # POC / controller / rain sensor
    cx, cy = px(*POC)
    o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="6" fill="var(--main)" stroke="var(--paper)" stroke-width="1.5"/>')
    o.append(text(POC[0]-4, POC[1]+0.5, 'POC · TAP EXISTING SUPPLY', 'irrlab', 'end'))
    o.append(text(POC[0]-4, POC[1]-2.2, 'master valve + flow sensor (field-locate)', 'irrsub', 'end'))
    cx, cy = px(3.5, 27)
    o.append(f'<rect x="{f(cx-7)}" y="{f(cy-7)}" width="14" height="14" fill="var(--ink)"/><text x="{f(cx)}" y="{f(cy+3.5)}" class="irrsymw" text-anchor="middle">C</text>')
    o.append(text(7.5, 26.2, 'EXISTING CONTROLLER (verify) · add Z1–Z7', 'irrlab'))
    cx, cy = px(18, 28.6)
    o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="5" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.2"/><text x="{f(cx)}" y="{f(cy+2.8)}" class="irrsym" text-anchor="middle">R</text>')
    o.append(text(10, 15.3, 'RAIN / SOIL-MOISTURE SENSOR', 'irrlab', 'middle'))
    o.append(text(10, 13.1, 'on restroom eave', 'irrsub', 'middle'))
    # zone number badges
    badge = {1: (-15, 63), 2: (-27, -2), 3: (40, -8.3), 4: (40, 50.2), 5: (30, -19.5), 6: (110, -18), 7: (8, 63)}
    for z, (x, y) in badge.items():
        cx, cy = px(x, y); c = INFO[z][3]
        o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="10" fill="{c}" stroke="var(--paper)" stroke-width="2"/>'
                 f'<text x="{f(cx)}" y="{f(cy+4)}" class="zbadge" text-anchor="middle">{z}</text>')
    # notes in lawn
    o.append(text(92, 116, 'EXISTING LAWN IRRIGATION', 'irrlab', 'middle'))
    o.append(text(92, 113, 'to remain · re-aim heads off new beds', 'irrsub', 'middle'))
    o.append(text(92, 90, 'utility ring: hand-water 60 days, then none', 'irrsub', 'middle'))
    return '\n'.join(o)

if __name__ == '__main__':
    for z in zones: print(z)
    print('sleeves', len(crossings), round(sleeve_len), 'PR', round(PR, 2))
    print('mainline ft', round(MAIN.length))
    print('total area', sum(z['area'] for z in zones), 'gpm max', max(z['gpm'] for z in zones))
