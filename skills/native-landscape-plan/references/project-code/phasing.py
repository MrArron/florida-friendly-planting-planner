"""Phase assignment, cost model and phase renders."""
import math, json
from shapely.geometry import Point, box, LineString, Polygon
from shapely.ops import unary_union
import layout as Lo
import irrigation as IR

# ---------------------------------------------------------------- phase map
# zone -> phase (each phase finishes complete, irrigated areas)
ZONE_PHASE = {1: 1, 3: 2, 4: 3, 2: 4, 5: 5, 6: 6, 7: 7}
NPH = 7
PHASE_NAME = {
 1: 'Oaks, irrigation backbone & entry garden',
 2: 'Pool band, southwest half',
 3: 'Pool band, northeast half',
 4: 'Oak hammock, mail-kiosk spur & first bench node',
 5: 'South-street meadow, south path & street access',
 6: 'Butterfly garden & southeast path',
 7: 'NE garden walk & loop completion',
}

def zone_at(x, y):
    p = Point(x, y)
    for z in (3, 4, 1, 2, 5, 6, 7):
        if IR.Z[z].buffer(0.6).contains(p): return z
    # nearest
    return min(IR.Z, key=lambda z: IR.Z[z].distance(p))

# path pieces by phase
PATH_REG = {
 4: box(-60, -60, 9, 7.5),                                   # hammock segment, N1, kiosk spur
 5: box(9, -60, 88, 0).union(box(84, -60, 93, -24)),         # south leg + street access
 6: box(88, -60, 130, 56).difference(box(84, -60, 93, -24)), # SE leg + N2
 7: box(-60, 7.5, 130, 160).difference(box(88, -60, 130, 56)),  # NE leg, N3, return leg
}
def path_phase_geom(ph):
    return Lo.path_poly.intersection(PATH_REG[ph]) if ph in PATH_REG else None

# rock band by side (lower half with Z3, upper half with Z4)
ROCK = {2: Lo.rock.intersection(box(-60, -60, 130, 20.8)).intersection(Lo.parcel),
        3: Lo.rock.intersection(box(-60, 20.8, 130, 160)).intersection(Lo.parcel)}

# ---------------------------------------------------------------- per-phase contents
def drift_pts_by_phase():
    out = {p: {} for p in range(1, NPH+1)}
    geo = {p: [] for p in range(1, NPH+1)}
    for d in Lo.DRIFTS:
        for (x, y) in d['pts']:
            ph = ZONE_PHASE[zone_at(x, y)]
            out[ph][d['code']] = out[ph].get(d['code'], 0) + 1
    for d in Lo.DRIFTS:
        for z, zg in IR.Z.items():
            g = d['geom'].intersection(zg)
            if g.is_empty or g.area < 0.5: continue
            pts = [(x, y) for (x, y) in d['pts'] if zg.buffer(0.6).contains(Point(x, y))]
            geo[ZONE_PHASE[z]].append({'code': d['code'], 'geom': g, 'pts': pts})
    return out, geo

def ind_by_phase():
    out = {p: [] for p in range(1, NPH+1)}
    for c, x, y in Lo.ind:
        out[ZONE_PHASE[zone_at(x, y)]].append((c, x, y))
    for c, x, y, r in Lo.ROW_TREES:
        out[1].append((c, x, y))
    return out

CNT, GEO = drift_pts_by_phase()
IND = ind_by_phase()
for p in IND:
    for c, x, y in IND[p]:
        CNT[p][c] = CNT[p].get(c, 0) + 1

AREA = {p: sum(IR.Z[z].area for z, ph in ZONE_PHASE.items() if ph == p) for p in range(1, NPH+1)}
PATH_AREA = {p: (path_phase_geom(p).area if p in PATH_REG else 0) for p in range(1, NPH+1)}
PATH_EDGE = {p: (path_phase_geom(p).boundary.length*0.92 if p in PATH_REG else 0) for p in range(1, NPH+1)}
ROCK_AREA = {p: (ROCK[p].area if p in ROCK else 0) for p in range(1, NPH+1)}
TUBE = {p: sum((z['tube'] or 0) for z in IR.zones if ZONE_PHASE[z['z']] == p) for p in range(1, NPH+1)}
ZONES_IN = {p: [z for z, ph in ZONE_PHASE.items() if ph == p] for p in range(1, NPH+1)}

if __name__ == '__main__':
    for p in range(1, NPH+1):
        print(p, PHASE_NAME[p], 'beds', round(AREA[p]), 'path', round(PATH_AREA[p]), 'edge', round(PATH_EDGE[p]),
              'rock', round(ROCK_AREA[p]), 'tube', round(TUBE[p]), 'plants', sum(CNT[p].values()))
        print('   ', dict(sorted(CNT[p].items())))
