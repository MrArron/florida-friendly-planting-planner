"""Sample Community pool garden - layout engine.
Deck-aligned plan frame (feet): X runs NW->SE along the deck's long axis,
Y runs SW->NE.  Origin = west corner of the fenced deck.
"""
import json, math, random
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, MultiPoint, MultiPolygon, GeometryCollection
from shapely.ops import unary_union, voronoi_diagram
from shapely import affinity

random.seed(7); np.random.seed(7)
F = json.load(open('feat.json'))

# ---------------------------------------------------------------- site
parcel = Polygon(F['ring']).buffer(0)
DECK_L, DECK_W = 82.13, 41.65
deck = box(0, 0, DECK_L, DECK_W)
pool = Polygon(F['pool'])
restroom = box(0, 12, 20, 30)
walk_full = box(-48, 7.5, 0, 12.5)          # existing concrete walk to the west street
walk = walk_full.intersection(parcel)
rock = deck.buffer(3, join_style=2).difference(deck).difference(walk_full)

OAK = (-18.5, -17.5)       # trunk ~5 ft behind the mail kiosk's back wall (confirmed on site)
PALMS = [(-15.5, -20.0), (17.5, -3.0), (75.7, -8.2), (62.7, 49.7), (75.6, 55.3), (84.2, 34.0)]
EXIST_TREES = [((92.6, -17.0), 14), ((104.7, 10.8), 13)]   # south trees (verify)
NBR_TREE = ((77.3, 143.1), 20)
UTIL = tuple(F['util'])
EXIST_SHRUBS = [(35.0, -6.1), (39.0, -9.6)]
SMALL_TREE = ((-7.0, 18.0), 8)     # existing small tree at restroom street wall (seen in site video)

# mail kiosk + quarter-circle walk (approximate - mostly hidden by canopy)
CC = (-6.5, -9.3)          # centre of the property-corner curve (R = 25)
def arcpts(c, r, a0, a1, n=40):
    return [(c[0] + r*math.cos(math.radians(a)), c[1] + r*math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n)]
CK = (-43.0, -42.0)        # quarter-circle walk is centred on the street corner (2025 aerial + video)
kiosk_walk_line = LineString([(-47.6, -22.0)] + arcpts(CK, 20, 90, 0) + [(-23.0, -46.6)])
kiosk_walk = kiosk_walk_line.buffer(2.25, cap_style=2)
KIOSK = (CK[0] + 26.5*math.cos(math.radians(45)), CK[1] + 26.5*math.sin(math.radians(45)))
kiosk_box = affinity.rotate(box(KIOSK[0]-8, KIOSK[1]-3.25, KIOSK[0]+8, KIOSK[1]+3.25), -45, origin=KIOSK)   # covered shelter roof, ~16 x 6.5 ft
kiosk_pad = affinity.rotate(box(KIOSK[0]-8.5, KIOSK[1]-5.6, KIOSK[0]+8.5, KIOSK[1]+3.6), -45, origin=KIOSK)

# ---------------------------------------------------------------- nature path
def catmull(pts, n=14, closed=False):
    P = list(pts)
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P)-2):
        p0, p1, p2, p3 = map(np.array, (P[i-1], P[i], P[i+1], P[i+2]))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t*t, t*t*t
            out.append(tuple(0.5*((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t2 + (-p0+3*p1-3*p2+p3)*t3)))
    out.append(tuple(P[-2]))
    return out

N1 = (3.0, -15.0); N2 = (104.0, -21.0); N3 = (99.0, 63.0)
path_way = [(-10, 7.5), (-9, 2), (-5, -6), N1, (12, -21.5), (25, -24.5), (40, -22.5), (55, -25.5),
            (70, -23.5), (82, -26.5), (94, -28.0), N2, (101, -11), (96.5, 2), (96.5, 16),
            (97.5, 30), (98.0, 44), (98.5, 55), N3, (88, 59.5), (75, 61.8), (62, 59.5), (48, 57.5),
            (33, 59.5), (18, 57.0), (4, 58.5), (-8, 55), (-17, 46), (-21, 33), (-22, 21), (-22, 12.5)]
PATH_W = 4.0
path_line = LineString(catmull(path_way))
spur_line = LineString(catmull([(N1[0]-4.0, N1[1]-3.5), (-6, -25), (-13, -31), (-22.0, -35.8)]))
street_line = LineString([(88.5, -25.0), (88.5, -46.0)])     # street access to the south-street curb
nodes = [Point(*N1).buffer(6.5), Point(*N2).buffer(6.5), Point(*N3).buffer(6.0)]
path_poly = unary_union([unary_union([path_line.buffer(PATH_W/2, cap_style=2)] + nodes).intersection(parcel),
                         spur_line.buffer(PATH_W/2, cap_style=2).difference(kiosk_walk),
                         street_line.buffer(PATH_W/2, cap_style=2)])
path_len = path_line.length + spur_line.length + street_line.intersection(parcel).length
# dog rest area on the east lawn: short spur from the N3 bench node to a small pad
DOG_PAD_C = (97.0, 84.0)
dog_spur = LineString([(99.0, 68.0), (98.2, 76.0), DOG_PAD_C]).buffer(PATH_W/2, cap_style=2)
dog_pad = Point(*DOG_PAD_C).buffer(6.0)
dog_poly = dog_spur.union(dog_pad).difference(Point(*N3).buffer(5.9))
DOG_BENCH = (DOG_PAD_C[0] + 2.0, DOG_PAD_C[1] + 3.6)
DOG_STATION = (DOG_PAD_C[0] - 4.4, DOG_PAD_C[1] + 2.0)   # bag dispenser + trash can


# ---------------------------------------------------------------- zones
wing = parcel.intersection(box(70, 71.4, 120, 160))      # east extension (backyards) - keep as lawn
util_bed = Point(*UTIL).buffer(6.5).difference(Point(*UTIL).buffer(3.2)).difference(box(UTIL[0]-2.5, UTIL[1]-7, UTIL[0]+2.5, UTIL[1]))
hard = unary_union([deck.buffer(3, join_style=2), walk_full, path_poly, kiosk_walk, kiosk_pad, dog_poly.buffer(0.5)])
# --- soft street edge: beds drift 2-6 ft into the right-of-way and swell around the new oaks
ROW_OAK_XY = [(32.0, -38.3), (60.0, -38.3), (107.0, -38.3), (-38.5, 38.0), (-38.5, 63.0)]
def _d(t, per, ph, oaks, peak):
    d = 3.2 + 2.0*math.sin(2*math.pi*t/per + ph) + 0.8*math.sin(2*math.pi*t/(per*0.43) + ph*2)
    for o in oaks:
        d = max(d, peak - 0.36*abs(t - o))
    return d
def taper(t, a, b, w=10):
    return max(0.0, min(1.0, (t-a)/w, (b-t)/w))
south_x = np.arange(2.0, 113.6, 1.0)
south_edge = [(x, -33.2 - _d(x, 34, .6, [32, 60, 107], 8.8)*taper(x, 2, 113.6, 9)) for x in south_x]
south_ext = Polygon([(2.0, -32.0)] + south_edge + [(113.6, -32.0)]).buffer(0)
west_y = np.arange(-5.0, 70.5, 1.0)
west_edge = [(-31.9 - _d(y, 31, 2.1, [38, 63], 11.0)*taper(y, -5, 70.5, 8), y) for y in west_y]
west_ext = Polygon([(-30.5, -5.0)] + west_edge + [(-30.5, 70.5)]).buffer(0)
street_edge_lines = [LineString(south_edge), LineString(west_edge)]
site = parcel.union(south_ext).union(west_ext)

# --- 5 ft maintenance strips on the zero-lot-line neighbor sides (lawn, no plants, no emitters)
ne_line = LineString([(-32.52, 70.67), (-11.36, 70.9), (72.47, 71.8)])
se_line = LineString([(113.74, -32.75), (113.44, -7.24), (112.47, 72.24)])
maint = unary_union([ne_line.buffer(5, cap_style=2), se_line.buffer(5, cap_style=2)]).intersection(parcel).difference(wing)

plantable = site.difference(hard).difference(wing).difference(maint)
plantable = plantable.difference(Point(*OAK).buffer(4))           # keep mulch ring at oak trunk
for (p, r) in [(PALMS[i], 2.0) for i in range(len(PALMS))]:
    plantable = plantable.difference(Point(*p).buffer(r))
for (p, r) in EXIST_TREES + [SMALL_TREE]:
    plantable = plantable.difference(Point(*p).buffer(3))

# sight triangle at the south-street / west-street corner (keep plants < 30 in)
sight = Polygon([(-31.6, -34.1), (-4, -34.1), (-31.6, -6.5)])

# pool band: undulating outer edge 9-13 ft from fence
def wavy_offset(geom, base, amp1, per1, amp2, per2, step=1.0):
    ring = geom.buffer(base, join_style=1).exterior
    L = ring.length; pts = []
    for s in np.arange(0, L, step):
        p = ring.interpolate(s)
        q = geom.exterior.interpolate(geom.exterior.project(p))
        v = np.array([p.x-q.x, p.y-q.y]); d = np.linalg.norm(v); v = v/d
        r = base + amp1*math.sin(2*math.pi*s/per1) + amp2*math.sin(2*math.pi*s/per2+1.3)
        pts.append((q.x+v[0]*r, q.y+v[1]*r))
    return Polygon(pts).buffer(0)
band_outer = wavy_offset(deck, 11.0, 2.2, 31, 1.0, 11)
band = band_outer.intersection(plantable)
inner_band = deck.buffer(6.0, join_style=2).intersection(band)
outer_band = band.difference(inner_band)
field = plantable.difference(band_outer)

# ---------------------------------------------------------------- palette
# code: (botanical, common, native, container, spacing_ft, H x W, colour, kind, layer)
PAL = {
 # trees & large shrubs (individual symbols)
 'QV':  ("Quercus virginiana", "Southern live oak", 'Y', '45 gal, 2.5 in caliper, 12-14 ft', 0, '40-60 x 60-100 (canopy managed by arborist)', '#3e6b3f', 'tree'),
 'MFT': ("Myrcianthes fragrans", "Simpson's stopper (tree form)", 'Y', '30 gal, 8-10 ft ht', 0, '15-20 x 12-15', '#5f8f6e', 'tree'),
 'MF':  ("Myrcianthes fragrans", "Simpson's stopper (hedge)", 'Y', '7 gal, 4-5 ft ht', 4.5, '8-12 x 5-8 (keep 7-9 ft)', '#6f9c78', 'shrub'),
 'VO':  ("Viburnum obovatum", "Walter's viburnum", 'Y', '7 gal', 6, '10-15 x 10-15', '#86a86a', 'shrub'),
 'HP':  ("Hamelia patens var. patens", "Firebush (native red form)", 'Y', '3 gal', 4.5, '6-8 x 5-6 (kept)', '#d9653b', 'shrub'),
 'AE':  ("Ardisia escallonioides", "Marlberry", 'Y', '3 gal', 5, '8-12 x 5-8', '#7f8a5a', 'shrub'),
 'CA':  ("Callicarpa americana", "American beautyberry", 'Y', '3 gal', 5, '4-8 x 4-6', '#b26bb0', 'shrub'),
 'SR':  ("Serenoa repens (silver form)", "Saw palmetto", 'Y', '7 gal', 5, '4-6 x 4-8', '#9fb8b0', 'shrub'),
 'SB':  ("Sabal minor", "Dwarf palmetto", 'Y', '7 gal', 5, '4-6 x 4-6', '#4f7d5c', 'shrub'),
 'IVH': ("Ilex vomitoria 'Schillings'", "Dwarf yaupon (walk edging)", 'Y', '3 gal', 3, '2-3 x 3 (kept)', '#55734f', 'shrub'),
 # shrub & grass masses (drifts)
 'IV':  ("Ilex vomitoria 'Schillings'", "Dwarf yaupon holly (male, no berries)", 'Y', '3 gal', 3, '3-4 x 4-5', '#55734f', 'mass'),
 'PN':  ("Psychotria nervosa", "Wild coffee", 'Y', '3 gal', 3, '3-6 x 2-4', '#3f6b45', 'mass'),
 'TF':  ("Tripsacum floridanum", "Dwarf Fakahatchee grass", 'Y', '3 gal', 3, '2-3 x 3', '#8fae6b', 'mass'),
 'MC':  ("Muhlenbergia capillaris", "Muhly grass", 'Y', '1 gal', 3, '2-3 x 2-3', '#c98fb7', 'mass'),
 'EE':  ("Eragrostis elliottii", "Elliott's lovegrass", 'Y', '1 gal', 2, '1-3 x 1-2', '#a9bcc4', 'mass'),
 # wildflowers
 'GP':  ("Gaillardia pulchella", "Blanket flower", 'Y', '1 gal', 2, '1-2 x 2', '#e0763f', 'mass'),
 'CL':  ("Coreopsis leavenworthii", "Leavenworth's tickseed", 'Y', '1 gal', 1.5, '1.5-3 x 1', '#f0c437', 'mass'),
 'MP':  ("Monarda punctata", "Dotted horsemint", 'Y', '1 gal', 2, '2-3 x 2', '#d79ab0', 'mass'),
 'SC':  ("Salvia coccinea", "Scarlet sage", 'Y', '1 gal', 1.5, '1-3 x 1.5', '#d4433f', 'mass'),
 'SJ':  ("Stachytarpheta jamaicensis", "Blue porterweed (native low form)", 'Y', '1 gal', 2.5, '1 x 3-4', '#6f73c4', 'mass'),
 'AT':  ("Asclepias tuberosa", "Butterfly milkweed", 'Y', '1 gal', 1.5, '1-2 x 1', '#f19a3e', 'mass'),
 'LS':  ("Liatris spicata", "Blazing star", 'Y', '1 gal', 1.5, '2-4 x 1', '#9a5fb5', 'mass'),
 'RH':  ("Rudbeckia hirta", "Black-eyed Susan", 'Y', '1 gal', 1.5, '2-3 x 1-2', '#e9b323', 'mass'),
 'SS':  ("Solidago sempervirens", "Seaside goldenrod", 'Y', '1 gal', 2.5, '3-5 x 2', '#d6c13a', 'mass'),
 # groundcovers
 'DO':  ("Dyschoriste oblongifolia", "Twinflower", 'Y', '1 gal', 1.5, '0.5-1 x 1.5', '#a99bd6', 'gc'),
 'MS':  ("Mimosa strigillosa", "Sunshine mimosa", 'Y', '1 gal', 2, '0.3-0.5 x spreading', '#e7a3c4', 'gc'),
 'TK':  ("Thelypteris kunthii", "Southern shield fern", 'Y', '1 gal', 2, '2-3 x 2', '#6c9a5a', 'gc'),
}

# ---------------------------------------------------------------- individuals
ind = []   # (code, x, y)
def addrow(code, p0, p1, sp):
    L = math.dist(p0, p1); n = int(L//sp) + 1
    for i in range(n):
        t = i/(n-1) if n > 1 else 0
        ind.append((code, p0[0]+(p1[0]-p0[0])*t, p0[1]+(p1[1]-p0[1])*t))
# Walter's viburnum screen along the SE property line + street-side clusters on the south street
for cx in (26, 50, 73):
    for dx in (-3.3, 3.3):
        ind.append(('VO', cx+dx, -30.6))
# firebush - sunny SE butterfly garden, >= 18 ft from the fence
for p in [(104.2, 26.0), (105.2, 31.5), (104.2, 37.0), (105.2, 42.5), (104.2, 48.0)]:
    ind.append(('HP', *p))
# oak hammock shrubs
for p in [(-19.5, -3.5), (-14.5, 0.5), (-24.0, -9.5)]:
    ind.append(('AE', *p))
for p in [(-27.5, 2.0), (-28.5, -4.0)]:
    ind.append(('SR', *p))
for p in [(7.5, -31.5), (12.5, -31.0), (17.5, -31.8)]:
    ind.append(('CA', *p))
for p in [(-9.5, -11.0), (9.0, -6.5), (-21.0, 18.0), (-27.0, 23.0)]:
    ind.append(('SB', *p))
# dwarf yaupon edging both sides of the concrete entry walk
addrow('IVH', (-30.5, 5.5), (-5.0, 5.5), 3.0)
addrow('IVH', (-30.5, 14.5), (-24.5, 14.5), 3.0)
addrow('IVH', (-19.5, 14.5), (-5.0, 14.5), 3.0)
# shade tree at the NE lawn overlook
ind.append(('MFT', 91.0, 68.5))

# future shade oaks in the right-of-way lawn (street side of the path)
ROW_TREES = [('QV', 32.0, -38.3, 28), ('QV', 60.0, -38.3, 28), ('QV', 107.0, -38.3, 28),
             ('QV', -38.5, 38.0, 28), ('QV', -38.5, 63.0, 28)]      # code, x, y, managed canopy radius (arborist keeps 10-15 ft off the pool fence)
# drop any individual that landed on hardscape
ind = [(c, x, y) for (c, x, y) in ind if plantable.buffer(0.3).contains(Point(x, y))]
for c_, x_, y_, r_ in ROW_TREES:
    plantable = plantable.difference(Point(x_, y_).buffer(2.5))   # mulch ring at new oak trunks

ind_fp = unary_union([Point(x, y).buffer(max(PAL[c][4], 4)/2) for c, x, y in ind])
ind_fp = ind_fp.union(unary_union([Point(x, y).buffer(2.5) for c, x, y, r in ROW_TREES]))

# ---------------------------------------------------------------- drifts
def poisson(region, r, k=30):
    minx, miny, maxx, maxy = region.bounds
    pts = []
    tries = 0
    while tries < 6000:
        p = (random.uniform(minx, maxx), random.uniform(miny, maxy)); tries += 1
        if not region.contains(Point(p)): continue
        if all(math.dist(p, q) >= r for q in pts): pts.append(p)
    return pts

def zone_of(x, y):
    if sight.contains(Point(x, y)): return 'corner'
    if x <= 9 and y < 7.5: return 'hammock'
    if x < -3 and 12.5 <= y < 30: return 'entryshade'
    if x < -3 and y >= 30: return 'frontage'
    if y >= 52 and x <= 72: return 'ne'
    if x >= 88: return 'se'
    if y < 0: return 'meadow'
    return 'se'

WEIGHTS = {
 'corner':     {'TK': 3, 'DO': 2, 'TF': 1},
 'hammock':    {'PN': 4, 'TK': 4, 'DO': 1, 'TF': 1},
 'entryshade': {'PN': 3, 'TK': 2, 'TF': 2},
 'frontage':   {'MC': 3, 'EE': 2, 'GP': 2, 'SC': 2, 'DO': 1},
 'ne':         {'TF': 2, 'EE': 2, 'MC': 2, 'DO': 1, 'SC': 1, 'GP': 1},
 'meadow':     {'GP': 3, 'CL': 3, 'MP': 3, 'SC': 3, 'SJ': 2, 'AT': 2, 'LS': 2, 'RH': 2, 'MC': 3},
 'se':         {'SJ': 3, 'SC': 3, 'SS': 2, 'GP': 2, 'MC': 2, 'MP': 2, 'LS': 1},
}
def pick(w, avoid=()):
    keys = [k for k in w if k not in avoid] or list(w)
    tot = sum(w[k] for k in keys); r = random.uniform(0, tot)
    for k in keys:
        r -= w[k]
        if r <= 0: return k
    return keys[-1]

def voronoi_cells(region, seeds):
    vd = voronoi_diagram(MultiPoint(seeds), envelope=region.buffer(50))
    out = []
    for cell in vd.geoms:
        s = [p for p in seeds if cell.contains(Point(p))]
        if not s: continue
        g = cell.intersection(region)
        if not g.is_empty: out.append((s[0], g))
    return out

drifts = []   # (code, geom, zone)
# 1) twinflower edging strip next to the rock band (all the way round)
drifts.append(('DO', inner_band.difference(ind_fp), 'band'))
# 2) outer pool band: alternating low, tidy masses
mid = deck.buffer(9.0, join_style=1).exterior
seq = ['IV', 'MC', 'TF', 'EE', 'IV', 'TF', 'MC', 'IV', 'EE', 'TF']
seeds = [mid.interpolate(s).coords[0] for s in np.arange(4, mid.length, 10.5)]
cells = voronoi_cells(outer_band.difference(ind_fp), seeds)
for i, (s, g) in enumerate(cells):
    code = seq[i % len(seq)]
    if s[0] < 0 and 5 < s[1] < 36: code = 'IV'       # formal at the entry / restroom
    drifts.append((code, g, 'band'))
# 3) field drifts (seed spacing ~8.5 ft)
fieldr = field.difference(ind_fp)
ms_strip = fieldr.intersection(street_edge_lines[0].buffer(2.6)).intersection(box(12, -60, 104, -25))
drifts.append(('MS', ms_strip, 'meadow'))
fieldr = fieldr.difference(ms_strip)
seeds = poisson(fieldr, 8.0)
cells = voronoi_cells(fieldr, seeds)
prev = {}
for s, g in sorted(cells, key=lambda c: (c[0][0], c[0][1])):
    z = zone_of(*s)
    w = dict(WEIGHTS[z])
    # neighbours shouldn't repeat
    nb = [c for (c, gg, zz) in drifts[-6:] if gg.distance(g) < 0.5]
    code = pick(w, avoid=nb)
    # sidewalk edge of the meadow gets sunshine mimosa
    drifts.append((code, g, z))
# 4) utility structure: dwarf Fakahatchee ring, open on the access side
drifts.append(('TF', util_bed, 'wing'))

# clean geometry, merge same-code touching cells inside each zone
def clean(g):
    g = g.buffer(-0.45).buffer(0.25)
    return g
merged = {}
for code, g, z in drifts:
    merged.setdefault((code, z), []).append(g)
DR = []
for (code, z), gs in merged.items():
    u = unary_union(gs)
    parts = list(u.geoms) if hasattr(u, 'geoms') else [u]
    for p in parts:
        p = clean(p)
        if p.is_empty or p.area < 2: continue
        sub = list(p.geoms) if hasattr(p, 'geoms') else [p]
        for q in sub:
            if q.area >= 2: DR.append((code, q, z))

# plant points inside each drift (hex grid at the specified spacing)
def hexpts(g, sp):
    minx, miny, maxx, maxy = g.bounds
    pts = []; dy = sp*math.sqrt(3)/2; row = 0
    y = miny + dy/2
    inner = g.buffer(-sp*0.35)
    test = inner if not inner.is_empty else g
    while y <= maxy:
        x = minx + (sp/2 if row % 2 else 0) + sp/2*0.5
        while x <= maxx:
            if test.contains(Point(x, y)): pts.append((x, y))
            x += sp
        y += dy; row += 1
    if not pts:
        c = g.representative_point(); pts = [(c.x, c.y)]
    return pts

DRIFTS = []
ring_pts = [(UTIL[0]+4.9*math.cos(a), UTIL[1]+4.9*math.sin(a)) for a in np.radians(np.arange(110, 431, 40))]
for code, g, z in DR:
    pts = hexpts(g, PAL[code][4])
    if z == 'wing': pts = ring_pts
    DRIFTS.append({'code': code, 'zone': z, 'geom': g, 'pts': pts})

# ---------------------------------------------------------------- quantities
qty = {}
for d in DRIFTS: qty[d['code']] = qty.get(d['code'], 0) + len(d['pts'])
for c, x, y in ind: qty[c] = qty.get(c, 0) + 1
for c, x, y, r in ROW_TREES: qty[c] = qty.get(c, 0) + 1
# merge walk-edging yaupon into the main yaupon line for ordering
area = {
  'parcel': parcel.area, 'deck': deck.area, 'rock': rock.intersection(parcel).area,
  'path': path_poly.area, 'path_len': path_len, 'beds': plantable.area,
  'wing_lawn': wing.difference(util_bed).area, 'walk': walk.area,
}
if __name__ == '__main__':
    for k, v in area.items(): print(f'{k:10s} {v:9.0f}')
    tot = 0
    for c in PAL:
        if c in qty: print(c, PAL[c][1], qty[c]); tot += qty[c]
    print('total plants', tot, 'drifts', len(DRIFTS))
