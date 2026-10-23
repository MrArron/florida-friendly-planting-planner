"""Lake Pointe pool garden - layout engine.
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
# Corrected existing geometry (field survey 18 Oct 2026: BCPAO building sketch 2602286 dated
# 05/12/2026, user tape measurements and photo resection). Converted to this frame in
# site_corrections_ft.json (x_ft = px/5.6 - 104, y_ft = 153 - py/5.6).
SC = json.load(open('site_corrections_ft.json'))
parcel = Polygon(F['ring']).buffer(0)
DECK_RING = [tuple(p) for p in SC['deck_ring']]     # 77 x ~40 ft fenced deck with an 18 x ~27 ft SW notch
deck = Polygon(DECK_RING)
pool = Polygon(F['pool'])
(_bx0, _by1), (_bx1, _by0) = SC['building']
restroom = box(_bx0, _by0, _bx1, _by1)              # 21 x 13 ft building
PATIO_X = tuple(SC['covered_patio_x'])
patio = box(PATIO_X[0], _by0, PATIO_X[1], _by1)     # east 4 ft: covered patio facing the deck
WALK_Y = (SC['restroom_walk'][1][1], SC['restroom_walk'][0][1])   # (10.79, 14.45)
CURB_X = SC['entry_walk'][0][0]                     # entry walk ends at the Cypress Pt curb
restroom_walk = box(0.0, WALK_Y[0], _bx1, WALK_Y[1])
entry_walk = box(CURB_X, WALK_Y[0], 0.0, WALK_Y[1])
walk_full = unary_union([restroom_walk, entry_walk])   # existing 44 in concrete walk, curb to pool gate
walk = walk_full.intersection(parcel)
GATE = ((_bx1, SC['gate'][1][1]), (_bx1, SC['gate'][0][1]))   # pool gate, x 21.8, y 10.61-14.45
FENCE_CORNER = tuple(SC['fence_corner_post'])
# fence lines exposed to the garden (not the building walls, not across the walk / gate)
FENCE_LINE = LineString([(_bx1, WALK_Y[0]), FENCE_CORNER, (DECK_RING[2][0], DECK_RING[2][1]),
                         DECK_RING[1], DECK_RING[0], DECK_RING[5]])
# climb-free 3 ft crushed-stone strip outside the exposed fence
rock = FENCE_LINE.buffer(3, cap_style=2, join_style=2).difference(deck).difference(restroom).difference(walk_full)
# keep the restroom's street-facing wall (door, vents) clear: 3 ft mulch-only strip
bldg_clear = box(_bx0-3.0, WALK_Y[1], _bx0, _by1)

OAK = tuple(SC['oak'])     # trunk ~5 ft behind the mail kiosk's back wall (confirmed by HOA)
YUCCA = tuple(SC['yucca'])                          # giant (spineless) yucca, keep
YUCCA_RING = 3.0
YUCCA_SPREAD = 7.5                                  # multi-trunk, ~20 ft tall, ~15 ft spread
PITTOS = [tuple(p) for p in SC['pittosporum']]      # two Japanese pittosporum, keep
PITTO_R = 7.5                                       # ~15 ft tall and wide
SMALL_TREE = (PITTOS[0], PITTO_R)                   # (kept for older references)
QUEEN = tuple(SC['queen_palm'])                     # keep until it dies, then remove (FISC Cat. II)
_pp = SC['cabbage_pair_south']
CABBAGE = [('palmgate', tuple(SC['cabbage_gate'])),
           ('palmpair', (_pp[0]-1.5, _pp[1])), ('palmpair', (_pp[0]+1.5, _pp[1])),
           ('palmne', tuple(SC['cabbage_ne'])),
           # plant expert, 23 Oct 2026: these two are native cabbage palms too, not Chinese fan palms
           ('palme', tuple(SC['fan_palm_remove'][0])), ('palmn', tuple(SC['fan_palm_remove'][1]))]
PALMS = [p for k, p in CABBAGE]                     # existing cabbage palms to remain (all of them)
PALM_TRUNK = 1.5                                    # trunk + boots: mulch only, no plant symbol inside
PALM_ROCK = 3.0                                     # the fence strip bends this far around a trunk
PALM_BED = 4.5                                      # underplanting ring around every cabbage palm
# the climb-free fence strip bends around palms that stand in or next to it: rock stays PALM_ROCK
# off each trunk, so the strip narrows to pass the east-fence palm and stops at the gate palm's
# ring (that trunk is only 2 ft off the fence); the ring itself gets low underplanting only
_rock_palms = [p for p in PALMS if FENCE_LINE.distance(Point(*p)) < 3 + PALM_ROCK]
rock = rock.difference(unary_union([Point(*p).buffer(PALM_ROCK) for p in _rock_palms]))
NBR_TREE = ((77.3, 143.1), 20)                      # neighbor's tree, off-parcel beyond the east extension
UTIL = tuple(SC['pump'])                            # community irrigation pump (green box)
UTIL_ALT = (UTIL[0] + 8.0, UTIL[1])                 # possible true position, ~8 ft east
DUMP = tuple(SC['dump_valve'])                      # pool dump valve riser + box (+/- 8 ft)
DUMP_R = 4.0                                        # ~8 ft flexible service area
service = Point(*DUMP).buffer(DUMP_R)
MARKERS = [tuple(p) for p in SC['valve_markers']]   # white PVC stubs over buried control valves
MARKER_R = 2.0                                      # ring edge stays >= 2 ft from the path edge
marker_rings = unary_union([Point(*m).buffer(MARKER_R) for m in MARKERS])
NOTICE = tuple(SC['notice_board'])
NOPARK = tuple(SC['no_parking_sign'])
SAIL = Polygon([(5.0, 39.4), (27.0, 39.4), (19.0, 29.0)])    # shade sail over the NW deck (approx.)
# remove-later items: removed when construction reaches that area (allowances incl. disposal)
_sr = SC['shrubs_remove']
REMOVE = [
 dict(id='bop1', kind='clump', xy=tuple(SC['bop_remove'][0]), r=2.5, cost=120, name='Bird-of-paradise clump',
      note='Sits on the old nature-path line. Dig out the clump and rhizomes when this area is built.'),
 dict(id='bop2', kind='clump', xy=tuple(SC['bop_remove'][1]), r=2.5, cost=120, name='Bird-of-paradise clump',
      note='Second clump near the queen palm. Dig out when the entry beds are built.'),
 dict(id='shnw', kind='shrub', xy=tuple(_sr['nw_fence']), r=3.5, cost=150, name='Large clipped shrub, NW fence corner',
      note='Remove when the pool band on this side is built.'),
 dict(id='shrr1', kind='shrub', xy=tuple(_sr['rr_walk'][0]), r=2.2, cost=90, name='Clipped shrub south of the restroom walk',
      note='Remove when the new strip south of the walk is built. Field-locate the pool dump valve as these come out.'),
 dict(id='shrr2', kind='shrub', xy=tuple(_sr['rr_walk'][1]), r=2.2, cost=90, name='Clipped shrub south of the restroom walk',
      note='Remove when the new strip south of the walk is built. Field-locate the pool dump valve as these come out.'),
 dict(id='shrr3', kind='shrub', xy=tuple(_sr['rr_walk'][2]), r=2.2, cost=90, name='Clipped shrub south of the restroom walk',
      note='Remove when the new strip south of the walk is built. Keep clear of the cabbage palm at the gate.'),
 dict(id='shsl', kind='shrub', xy=tuple(_sr['south_lawn']), r=2.8, cost=100, name='Loose rounded shrub, south lawn', wp=4,
      note='It stands on the new path line next to the first bench node, so it comes out with that path segment (same work package).'),
 dict(id='hedge', kind='hedge', xy=tuple(_sr['kiosk_hedge']), r=3.0, cost=120, name='Low hedge at the kiosk oak',
      note='Remove by hand when the oak hammock is built: cut at grade and pull small roots only, no grinding inside the oak root zone.'),
]

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

# Path rules (field survey 18 Oct 2026): west leg tees into the corrected walk (south approach at
# its south edge, north leg at its north edge); path edge >= 6 ft from the queen palm, >= 5 ft from
# the yucca and pittosporums, >= 12 ft from the oak trunk, clear of the dump-valve service area and
# >= 3 ft from the irrigation valve markers.
N1 = (14.0, -13.0); N2 = (96.0, -21.0); N3 = (101.0, 66.0)   # N2 pulled in from x 104 so its benches sit >= 10 ft from the neighbor's wall
path_way = [(-10.0, WALK_Y[0] + 0.6), (-10.0, 7.0), (-10.2, 1.0), (-9.0, -5.2), (-5.0, -10.0), (1.0, -12.4), (7.5, -13.2), N1,
            (22, -20.5), (30, -24.0), (40, -22.5), (55, -25.5),
            (70, -23.5), (78, -25.5), (87, -25.0), N2, (98.5, -10.0), (96.5, 2), (96.5, 16),
            (97.5, 30), (98.0, 44), (98.6, 55), N3, (93.0, 66.0), (85, 64.6), (75, 62.6), (62, 60.0), (48, 58.0),
            (33, 59.5), (18, 57.5), (4, 58.5), (-6, 55.5), (-13, 48), (-16.5, 38), (-17, 28), (-16, 20.5),
            (-16.0, WALK_Y[1] - 0.6)]
PATH_W = 4.0
path_line = LineString(catmull(path_way))
# kiosk spur: the oak (12 ft rule) and the yucca's 15 ft spread leave no room between them,
# so the spur leaves the N1 node southward and passes south of the yucca in the right-of-way lawn
SPUR_START = (N1[0] - 1.0, N1[1] - 5.0)
spur_line = LineString(catmull([SPUR_START, (13.0, -24.5), (10.5, -31.5), (4.0, -36.6), (-4.0, -37.6), (-13.0, -37.4), (-22.0, -35.8), (-26.0, -35.1)]))   # last point runs into the kiosk walk (clipped off below) so the joint is flush
# street access to the Myrtlewood curb: starts on the path centerline so the joint leaves no bump on the far side
_sx = 80.0
_sy = path_line.intersection(LineString([(_sx, -60.0), (_sx, 0.0)])).centroid.y
street_line = LineString([(_sx, _sy), (_sx, -46.0)])
NODE_R = {'N1': 6.5, 'N2': 6.5, 'N3': 6.0}
nodes = [Point(*N1).buffer(NODE_R['N1']), Point(*N2).buffer(NODE_R['N2']), Point(*N3).buffer(NODE_R['N3'])]
path_poly = unary_union([unary_union([path_line.buffer(PATH_W/2, cap_style=2)] + nodes).intersection(parcel),
                         spur_line.buffer(PATH_W/2, cap_style=2).difference(kiosk_walk),
                         street_line.buffer(PATH_W/2, cap_style=2)]).difference(walk_full)
LOOP_LEN = path_line.length
SPUR_LEN = spur_line.difference(kiosk_walk).length
STREET_LEN = street_line.intersection(parcel).length
path_len = round(LOOP_LEN) + round(SPUR_LEN) + round(STREET_LEN)      # so the parts always add up as printed
# dog rest area on the east lawn: short spur from the N3 bench node to a small pad
DOG_PAD_C = (97.0, 84.0)
dog_spur = LineString([(100.2, 70.0), (98.8, 77.0), DOG_PAD_C]).buffer(PATH_W/2, cap_style=2)
dog_pad = Point(*DOG_PAD_C).buffer(6.0)
dog_poly = dog_spur.union(dog_pad).difference(Point(*N3).buffer(NODE_R['N3'] - 0.1))
DOG_BENCH = (DOG_PAD_C[0] + 2.0, DOG_PAD_C[1] + 3.6)
DOG_STATION = (DOG_PAD_C[0] - 4.4, DOG_PAD_C[1] + 2.0)   # bag dispenser + trash can

# benches at the rest nodes (also drawn by render.py / phase_render.py)
def _benches():
    """One bench per node, in the part of the node circle farthest from every path connection
    (loop legs, kiosk spur, street access, dog spur). Long axis runs along the circle, facing the center."""
    out = []
    bench0 = Polygon([(-2.5, -.8), (2.5, -.8), (2.5, .8), (-2.5, .8)])
    conns = [path_line, spur_line, street_line, LineString([(100.2, 70.0), (98.8, 77.0), DOG_PAD_C])]
    for n, rad in ((N1, NODE_R['N1']), (N2, NODE_R['N2']), (N3, NODE_R['N3'])):
        ring = Point(*n).buffer(rad).exterior
        angs = []
        for ln in conns:
            ix = ln.intersection(ring)
            for g in getattr(ix, 'geoms', [ix]):
                if not g.is_empty and g.geom_type == 'Point':
                    angs.append(math.atan2(g.y - n[1], g.x - n[0]))
        best = max((math.radians(t) for t in range(0, 360, 2)),
                   key=lambda t: min(abs((t - a + math.pi) % (2*math.pi) - math.pi) for a in angs))
        r = rad - 1.7
        cx, cy = n[0] + r*math.cos(best), n[1] + r*math.sin(best)
        out.append(affinity.translate(affinity.rotate(bench0, math.degrees(best) + 90, origin=(0, 0)), cx, cy))
    out.append(affinity.translate(bench0, *DOG_BENCH))
    return out
BENCHES = _benches()
# dump-valve access: stepping stones from the nearest path edge to the service area
_near = path_line.interpolate(path_line.project(Point(*DUMP)))
_v = np.array([DUMP[0]-_near.x, DUMP[1]-_near.y]); _dd = float(np.linalg.norm(_v)); _v = _v/_dd
STONES = [(_near.x + _v[0]*t, _near.y + _v[1]*t) for t in np.arange(PATH_W/2 + 1.1, _dd - DUMP_R + 1.4, 1.9)]
stone_geoms = [affinity.rotate(box(x-0.8, y-0.6, x+0.8, y+0.6), math.degrees(math.atan2(_v[1], _v[0]))+90, origin=(x, y)) for x, y in STONES]
stones = unary_union(stone_geoms) if stone_geoms else Polygon()

# ---------------------------------------------------------------- zones
wing = parcel.intersection(box(70, 71.4, 120, 160))      # east extension (backyards) - keep as lawn
# pump grass ring: open side faces the dog pad / path, so the vendor walks straight in on lawn
_pa = math.atan2(DOG_PAD_C[1]-UTIL[1], DOG_PAD_C[0]-UTIL[0])
PUMP_OPEN = math.degrees(_pa)
_wedge = Polygon([UTIL] + [(UTIL[0]+12*math.cos(_pa+t), UTIL[1]+12*math.sin(_pa+t)) for t in np.radians(np.linspace(-55, 55, 12))])
util_bed = Point(*UTIL).buffer(6.5).difference(Point(*UTIL).buffer(3.4)).difference(_wedge)
# walkable lawn corridor (4 ft) from the dog pad to the pump, plus 3 ft clear in front of its doors
pump_corridor = LineString([DOG_PAD_C, UTIL]).buffer(2.0, cap_style=2).difference(dog_pad).difference(Point(*UTIL).buffer(2.8))
pump_front = Point(*UTIL).buffer(5.8).intersection(_wedge).difference(Point(*UTIL).buffer(2.8))
deck_block = unary_union([deck, restroom, restroom_walk])       # what the pool band wraps
hard = unary_union([deck, rock, restroom, walk_full, path_poly, kiosk_walk, kiosk_pad, dog_poly.buffer(0.5), stones.buffer(0.2)])
# --- soft street edge: beds drift 2-6 ft into the right-of-way and swell around the new oaks
ROW_OAK_XY = [(32.0, -38.3), (60.0, -38.3), (107.0, -38.3), (-38.5, 38.0), (-38.5, 63.0)]
def _d(t, per, ph, oaks, peak):
    d = 3.2 + 2.0*math.sin(2*math.pi*t/per + ph) + 0.8*math.sin(2*math.pi*t/(per*0.43) + ph*2)
    for o in oaks:
        d = max(d, peak - 0.36*abs(t - o))
    return d
def taper(t, a, b, w=10):
    return max(0.0, min(1.0, (t-a)/w, (b-t)/w))
my_x = np.arange(2.0, 113.6, 1.0)
my_edge = [(x, -33.2 - _d(x, 34, .6, [32, 60, 107], 8.8)*taper(x, 2, 113.6, 9)) for x in my_x]
myrtle_ext = Polygon([(2.0, -32.0)] + my_edge + [(113.6, -32.0)]).buffer(0)
cy_y = np.arange(-5.0, 70.5, 1.0)
cy_edge = [(-31.9 - _d(y, 31, 2.1, [38, 63], 11.0)*taper(y, -5, 70.5, 8), y) for y in cy_y]
cypress_ext = Polygon([(-30.5, -5.0)] + cy_edge + [(-30.5, 70.5)]).buffer(0)
street_edge_lines = [LineString(my_edge), LineString(cy_edge)]
site = parcel.union(myrtle_ext).union(cypress_ext)

# --- 5 ft maintenance strips on the zero-lot-line neighbor sides (lawn, no plants, no emitters)
ne_line = LineString([(-32.52, 70.67), (-11.36, 70.9), (72.47, 71.8)])
se_line = LineString([(113.74, -32.75), (113.44, -7.24), (112.47, 72.24)])
maint = unary_union([ne_line.buffer(5, cap_style=2), se_line.buffer(5, cap_style=2)]).intersection(parcel).difference(wing)

plantable = site.difference(hard).difference(wing).difference(maint)
# keep-out rings: no new plants
TRUNK_RINGS = ([(OAK, 4.0), (YUCCA, YUCCA_RING), (QUEEN, 2.5)] + [(p, 3.0) for p in PITTOS] +
               [(p, PALM_TRUNK) for p in PALMS])
keepout = unary_union([Point(*p).buffer(r) for p, r in TRUNK_RINGS] + [bldg_clear])
access_gc = unary_union([service, marker_rings]).difference(hard).intersection(site)   # low-groundcover access rings
plantable = plantable.difference(keepout).difference(access_gc)
mulch_only = keepout.intersection(site).difference(hard).difference(wing)    # drawn as mulch, unplanted

# sight triangle at the Myrtlewood / Cypress Point corner (keep plants < 30 in)
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
band_outer = wavy_offset(deck_block, 11.0, 2.2, 31, 1.0, 11)   # follows the real fence ring, building and restroom walk
band = band_outer.intersection(plantable)
inner_band = deck_block.buffer(6.0, join_style=2).intersection(band)
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
 'GP':  ("Gaillardia pulchella", "Blanket flower", 'N', '1 gal', 2, '1-2 x 2', '#e0763f', 'mass'),
 'CL':  ("Coreopsis leavenworthii", "Leavenworth's tickseed", 'Y', '1 gal', 1.5, '1.5-3 x 1', '#f0c437', 'mass'),
 'MP':  ("Monarda punctata", "Dotted horsemint", 'Y', '1 gal', 2, '2-3 x 2', '#d79ab0', 'mass'),
 'SC':  ("Salvia coccinea", "Scarlet sage", 'Y', '1 gal', 1.5, '1-3 x 1.5', '#d4433f', 'mass'),
 'SJ':  ("Stachytarpheta jamaicensis", "Blue porterweed (native low form)", 'Y', '1 gal', 2.5, '1 x 3-4', '#6f73c4', 'mass'),
 'AT':  ("Asclepias tuberosa", "Butterfly milkweed", 'Y', '1 gal', 1.5, '1-2 x 1', '#f19a3e', 'mass'),
 'LS':  ("Liatris gracilis", "Pinkscale blazing star", 'Y', '1 gal', 1.5, '1.5-3 x 1', '#b0609f', 'mass'),
 'RH':  ("Rudbeckia hirta", "Black-eyed Susan", 'Y', '1 gal', 1.5, '2-3 x 1-2', '#e9b323', 'mass'),
 'SS':  ("Solidago sempervirens", "Seaside goldenrod", 'Y', '1 gal', 2.5, '3-5 x 2', '#d6c13a', 'mass'),
 # groundcovers
 'DO':  ("Dyschoriste oblongifolia", "Twinflower", 'Y', '1 gal', 1.5, '0.5-1 x 1.5', '#a99bd6', 'gc'),
 'MS':  ("Mimosa strigillosa", "Sunshine mimosa", 'Y', '1 gal', 2, '0.3-0.5 x spreading', '#e7a3c4', 'gc'),
 'TK':  ("Thelypteris kunthii", "Southern shield fern", 'Y', '1 gal', 2, '2-3 x 2', '#6c9a5a', 'gc'),
 'OC':  ("Osmunda cinnamomea", "Cinnamon fern", 'Y', '1 gal', 2.5, '2-3 x 3', '#4e8a52', 'gc'),
 'RF':  ("Osmunda regalis var. spectabilis", "Royal fern", 'Y', '1 gal', 3, '3-5 x 3-4', '#2f6b4a', 'gc'),
 'ZI':  ("Zamia integrifolia", "Coontie (donated, local)", 'Y', '1 gal', 3, '1-3 x 3-4', '#2e5e3a', 'mass'),
}

# ---------------------------------------------------------------- individuals
ind = []   # (code, x, y)
def addrow(code, p0, p1, sp):
    L = math.dist(p0, p1); n = int(L//sp) + 1
    for i in range(n):
        t = i/(n-1) if n > 1 else 0
        ind.append((code, p0[0]+(p1[0]-p0[0])*t, p0[1]+(p1[1]-p0[1])*t))
# Walter's viburnum screen along the SE property line + street-side clusters on Myrtlewood
for cx in (30, 50, 69):                      # pairs 7.2 ft apart (symbol radius 3.4); the last pair stays 4 ft off the Myrtlewood connector
    for dx in (-3.6, 3.6):
        ind.append(('VO', cx+dx, -30.6))
# firebush - sunny SE butterfly garden, >= 18 ft from the fence
for p in [(104.2, 26.0), (105.2, 31.5), (104.2, 37.0), (105.2, 42.5), (104.2, 48.0)]:
    ind.append(('HP', *p))
# oak hammock shrubs
for p in [(-19.5, -3.5), (-14.5, 0.5), (-24.0, -9.5)]:
    ind.append(('AE', *p))
for p in [(-27.5, 2.0), (-28.5, -4.0)]:
    ind.append(('SR', *p))
for p in [(0.5, -31.0), (12.0, -32.8), (20.5, -32.8)]:
    ind.append(('CA', *p))
for p in [(-13.5, -8.5), (5.5, -2.5), (-23.0, 26.0), (-28.0, 27.5)]:
    ind.append(('SB', *p))
# dwarf yaupon edging both sides of the concrete entry walk
# (gaps where the two path legs tee in; the filter below drops any that land in a keep-out ring)
_ys, _yn = WALK_Y[0] - 1.5, WALK_Y[1] + 1.5
addrow('IVH', (-30.5, _ys), (-13.4, _ys), 3.0)
addrow('IVH', (-6.5, _ys), (-3.5, _ys), 3.0)
addrow('IVH', (-30.5, _yn), (-19.4, _yn), 3.0)
addrow('IVH', (-12.6, _yn), (-3.5, _yn), 3.0)
# shade tree at the NE lawn overlook
# (in the lawn just NW of the overlook node; trunk 6.6 ft and canopy clear of the path edge,
#  15 ft from the neighbor line, so it shades the bench's lawn side rather than the path)
ind.append(('MFT', 88.0, 74.0))

# future shade oaks in the right-of-way lawn (street side of the path)
ROW_TREES = [('QV', 32.0, -38.3, 28), ('QV', 60.0, -38.3, 28), ('QV', 107.0, -38.3, 28),
             ('QV', -38.5, 38.0, 28), ('QV', -38.5, 63.0, 28)]      # code, x, y, managed canopy radius (arborist keeps 10-15 ft off the pool fence)
# symbol radius drawn for each individual (render.shrub_symbol uses the same table)
SYM_R = {'MF': 2.6, 'VO': 3.4, 'HP': 2.6, 'AE': 2.8, 'CA': 2.6, 'SR': 2.8, 'SB': 2.7, 'IVH': 1.45, 'MFT': 6.5}
IND_PATH_MIN = 4.0          # trunk >= 4 ft from any path edge, and the symbol may not touch path or benches
path_all = unary_union([path_poly, dog_poly] + BENCHES)
def _ok(c, x, y):
    p = Point(x, y)
    return (path_all.distance(p) >= max(IND_PATH_MIN, SYM_R[c] + 0.1) and plantable.buffer(-0.35).contains(p))
def _settle(c, x, y):
    if _ok(c, x, y): return (c, x, y)
    q = path_all.exterior.interpolate(0) if False else None
    from shapely.ops import nearest_points
    a = nearest_points(path_all, Point(x, y))[0]
    v = np.array([x-a.x, y-a.y]); n = np.linalg.norm(v); v = v/n if n > 1e-6 else np.array([0.0, 1.0])
    for t in np.arange(0.25, 6.01, 0.25):        # push straight away from the nearest path edge
        if _ok(c, x+v[0]*t, y+v[1]*t): return (c, x+v[0]*t, y+v[1]*t)
    return None
if 'MFT' in [c for c, x, y in ind]:
    pass
ind = [r for r in ((c, x, y) if c == 'IVH' and _ok(c, x, y) else None if c == 'IVH' else _settle(c, x, y) if c != 'MFT' else ((c, x, y) if path_all.distance(Point(x, y)) >= max(IND_PATH_MIN, SYM_R[c]) else None)
                   for (c, x, y) in ind) if r is not None]
_kept = [(YUCCA[0], YUCCA[1], YUCCA_RING), (QUEEN[0], QUEEN[1], 3.0), (OAK[0], OAK[1], 3.0)] + [(p[0], p[1], PITTO_R*0.5) for p in PITTOS] + [(p[0], p[1], PALM_TRUNK) for p in PALMS]
ind = [(c, x, y) for c, x, y in ind if all(math.dist((x, y), (kx, ky)) >= 0.8*(kr + SYM_R[c]) for kx, ky, kr in _kept)]   # no shrub under a kept tree
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

GATE_C = (GATE[0][0], (GATE[0][1] + GATE[1][1])/2)
def zone_of(x, y):
    # shade only where the kept live oak really casts it (canopy ~55-60 ft wide); the two
    # "south trees" of the old plan don't exist / are off-parcel, so everything else is sun
    if sight.contains(Point(x, y)): return 'corner'
    if math.dist((x, y), GATE_C) < 20: return 'gate'          # low-litter, not bee-heavy, at the pool gate
    if math.dist((x, y), OAK) < 25 and y < WALK_Y[0]: return 'hammock'
    if x < -3 and 12.5 <= y < 30: return 'entryshade'
    if x < -3 and y >= 30: return 'frontage'
    if y >= 52 and x <= 72: return 'ne'
    if x >= 88: return 'se'
    if y < 0: return 'meadow'
    return 'se'

WEIGHTS = {
 'corner':     {'TK': 3, 'DO': 2, 'TF': 1},
 'gate':       {'TF': 3, 'EE': 2, 'MC': 2, 'DO': 1},
 'hammock':    {'PN': 3, 'TK': 4, 'OC': 2, 'RF': 2, 'DO': 1, 'TF': 1},
 'entryshade': {'ZI': 6, 'PN': 3, 'TK': 2, 'TF': 2},
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
# 0) underplanting ring at every kept cabbage palm: free coonties (evergreen, low, takes the frond
#    and boot litter). Coontie is toxic if eaten, so the gate palm (>= 15 ft rule) and the NE palm
#    (>= 20 ft from the dog lawn) get dwarf Fakahatchee instead
palm_beds = unary_union([Point(*p).buffer(PALM_BED) for p in PALMS]).intersection(plantable).difference(ind_fp)
_dogz = unary_union([dog_poly, wing])
for k, p in CABBAGE:
    g = Point(*p).buffer(PALM_BED).intersection(palm_beds)
    near_kids_or_dogs = math.dist(p, GATE_C) < 15 + PALM_BED or _dogz.distance(Point(*p)) < 20 + PALM_BED
    drifts.append(('TF' if near_kids_or_dogs else 'ZI', g, 'palm'))
inner_band = inner_band.difference(palm_beds); outer_band = outer_band.difference(palm_beds)
field = field.difference(palm_beds)
# 1) twinflower edging strip next to the rock band (all the way round)
drifts.append(('DO', inner_band.difference(ind_fp), 'band'))
# 2) outer pool band: alternating low, tidy masses
mid = deck_block.buffer(9.0, join_style=1).exterior
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
HAMMOCK_OUTER = ['TK', 'OC', 'ZI', 'RF', 'PN', 'TK', 'ZI', 'OC', 'RF']; _hk = [0]
for s, g in sorted(cells, key=lambda c: (c[0][0], c[0][1])):
    z = zone_of(*s)
    w = dict(WEIGHTS[z])
    # neighbours shouldn't repeat
    nb = [c for (c, gg, zz) in drifts[-6:] if gg.distance(g) < 0.5]
    code = pick(w, avoid=nb)
    # free coonties: the dry shade under the oak (inside 18 ft of the trunk) is all coontie; the
    # moisture-loving ferns keep to the outer hammock. Under the pittosporums coontie replaces grass and fern.
    if z == 'hammock':
        if math.dist(s, OAK) < 18: code = 'ZI'
        else:                          # outer hammock: fixed rotation so all three ferns always appear
            code = HAMMOCK_OUTER[_hk[0] % len(HAMMOCK_OUTER)]; _hk[0] += 1
    if z == 'entryshade' and code in ('TF', 'TK'): code = 'ZI'
    # sidewalk edge of the meadow gets sunshine mimosa
    drifts.append((code, g, z))
# 4) utility structure: dwarf Fakahatchee ring, open on the access side
drifts.append(('TF', util_bed, 'wing'))
# 5) dump-valve service area and valve-marker rings: low twinflower groundcover only (no shrubs)
drifts.append(('DO', access_gc.intersection(site).difference(wing).difference(maint), 'access'))

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
# discs already drawn: individual shrubs/trees and the kept trees. A drift plant may not sit under one,
# and drift plants from neighboring drifts may not sit on each other.
_discs = [(x, y, SYM_R[c]) for c, x, y in ind] + [(YUCCA[0], YUCCA[1], YUCCA_RING)] + \
         [(p[0], p[1], PITTO_R*0.5) for p in PITTOS] + [(QUEEN[0], QUEEN[1], 3.0), (OAK[0], OAK[1], 3.0)] + \
         [(p[0], p[1], PALM_TRUNK) for p in PALMS]
_drift_kept = []
ring_pts = [(UTIL[0]+4.9*math.cos(a), UTIL[1]+4.9*math.sin(a)) for a in np.radians(np.arange(PUMP_OPEN+70, PUMP_OPEN+291, 36))]
for code, g, z in DR:
    pts = hexpts(g, PAL[code][4])
    if z == 'wing': pts = ring_pts
    if z == 'palm':                 # one ring of plants just outside each trunk's mulch circle
        _rr = PALM_TRUNK + PAL[code][4]*0.46 + 0.1
        pts = [(px_ + _rr*math.cos(a), py_ + _rr*math.sin(a)) for px_, py_ in PALMS
               for a in np.linspace(0, 2*math.pi, int(2*math.pi*_rr/PAL[code][4]), endpoint=False)]
        pts += hexpts(g.difference(unary_union([Point(*q).buffer(_rr + PAL[code][4]*0.6) for q in PALMS])), PAL[code][4]) \
            if not g.difference(unary_union([Point(*q).buffer(_rr + PAL[code][4]*0.6) for q in PALMS])).is_empty else []
        pts = [q for q in pts if g.contains(Point(q))]
        _keep = []
        for q in pts:                # the pair's two rings cross: keep one plant where they meet
            if all(math.dist(q, k_) >= PAL[code][4]*0.92 for k_ in _keep): _keep.append(q)
        pts = _keep
    # drop any point whose drawn symbol would touch the path, dog pad or a bench
    _sr = 0.62 if code == 'DO' else PAL[code][4]*0.46
    pts = [p for p in pts if path_all.distance(Point(p)) >= _sr + 0.05]
    if z != 'wing':
        pts = [p for p in pts if all(math.dist(p, (dx_, dy_)) >= dr_ + _sr for dx_, dy_, dr_ in _discs)
               and all(math.dist(p, (kx, ky)) >= 0.85*(kr + _sr) for kx, ky, kr in _drift_kept)]
    _drift_kept += [(p[0], p[1], _sr) for p in pts]
    if not pts: continue            # sliver beside the path: leave as mulch
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