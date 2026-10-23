"""Geometry and budget checks for the field-survey revision (run: python3 checks.py)."""
import math
from shapely.geometry import Point
from shapely.ops import unary_union
import layout as Lo, irrigation as IR, schedule as SC

ok = True
def rep(name, cond, detail=''):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")

# (a) no plant point or drift in hardscape, trunk rings or service areas
hard = unary_union([Lo.deck, Lo.restroom, Lo.walk_full, Lo.path_poly, Lo.dog_poly, Lo.kiosk_walk, Lo.kiosk_pad, Lo.rock, Lo.stones])
access = unary_union([Lo.service, Lo.marker_rings])
bad_pts = bad_dr = 0; n_pts = 0
for d in Lo.DRIFTS:
    is_gc_access = d['zone'] == 'access'
    forbid = unary_union([hard, Lo.keepout] + ([] if is_gc_access else [access]))
    if d['zone'] == 'wing':
        forbid = unary_union([forbid, Lo.pump_corridor, Lo.pump_front])
    if d['geom'].intersection(forbid).area > 0.05: bad_dr += 1
    for x, y in d['pts']:
        n_pts += 1
        if forbid.contains(Point(x, y)): bad_pts += 1
forbid_all = unary_union([hard, Lo.keepout, access])
bad_ind = [(c, x, y) for c, x, y in Lo.ind if forbid_all.buffer(0.3).contains(Point(x, y))]
rep('(a) drift plant points clear', bad_pts == 0, f'{bad_pts} of {n_pts} points in a keep-out')
rep('(a) drift areas clear', bad_dr == 0, f'{bad_dr} of {len(Lo.DRIFTS)} drifts overlap a keep-out')
rep('(a) individual shrubs/trees clear', not bad_ind, f'{len(bad_ind)} of {len(Lo.ind)}')
shrub_in_access = [d['code'] for d in Lo.DRIFTS if d['geom'].intersection(access).area > 0.05 and d['zone'] != 'access']
rep('(a) service/marker areas low groundcover only', not shrub_in_access, f"codes there: {sorted(set(d['code'] for d in Lo.DRIFTS if d['zone']=='access'))}")

# (b) path clearances (distance from path EDGE to trunk / feature)
P = unary_union([Lo.path_poly, Lo.dog_poly])
d = lambda p: P.distance(Point(*p))
rep('(b) yucca: path clear of 15 ft spread (>=7.5 ft from trunk)', d(Lo.YUCCA) >= Lo.YUCCA_SPREAD, f'{d(Lo.YUCCA):.1f} ft')
rep('(b) queen palm >= 6 ft', d(Lo.QUEEN) >= 6, f'{d(Lo.QUEEN):.1f} ft')
for i, p in enumerate(Lo.PITTOS):
    rep(f'(b) pittosporum {i+1} >= 5 ft', d(p) >= 5, f'{d(p):.1f} ft')
rep('(b) oak >= 12 ft', d(Lo.OAK) >= 12, f'{d(Lo.OAK):.1f} ft')
rep('(b) no path base over dump-valve service area', P.distance(Lo.service) > 0, f'{P.distance(Lo.service):.1f} ft gap (valve {d(Lo.DUMP):.1f} ft from path)')
for i, m in enumerate(Lo.MARKERS):
    rep(f'(b) valve marker {i+1} >= 3 ft', d(m) >= 3, f'{d(m):.1f} ft')
rep('(b) path tees into walk (both legs touch it)', all(Lo.path_poly.buffer(0.05).intersection(Lo.walk_full).intersects(Lo.walk_full.exterior)
    for _ in [0]) and Lo.path_line.distance(Point(-10, Lo.WALK_Y[0])) < 1 and Lo.path_line.distance(Point(-16, Lo.WALK_Y[1])) < 1)
rep('(b) saw palmetto >= 5 ft from walks/path', all(unary_union([P, Lo.walk_full, Lo.kiosk_walk]).distance(Point(x, y)) >= 5 for c, x, y in Lo.ind if c == 'SR'))

# (b2) plant symbols never sit on each other (individuals, kept trees, drift plants)
import math as _m
_ind = [(c, x, y, Lo.SYM_R[c]) for c, x, y in Lo.ind]
_fix = [('yucca', *Lo.YUCCA, Lo.YUCCA_RING), ('queen', *Lo.QUEEN, 3.0), ('oak', *Lo.OAK, 3.0)] + \
       [('pitto', *p, Lo.PITTO_R*0.5) for p in Lo.PITTOS] + [('palm', *p, Lo.PALM_TRUNK) for p in Lo.PALMS]
_pairs = [(a, b) for i, a in enumerate(_ind) for b in _ind[i+1:] + _fix if _m.dist(a[1:3], b[1:3]) < 0.8*(a[3] + b[3])]
rep('(b2) individual shrubs/trees do not overlap each other or kept trees', not _pairs, f'{len(_pairs)} overlaps {[(a[0], round(a[1],1), round(a[2],1), b[0]) for a, b in _pairs[:4]]}')
_dp = [(d['code'], x, y, 0.62 if d['code'] == 'DO' else Lo.PAL[d['code']][4]*0.46) for d in Lo.DRIFTS if d['zone'] != 'wing' for x, y in d['pts']]
_bad = [p for p in _dp if any(_m.dist(p[1:3], o[1:3]) < o[3] + p[3] - 0.05 for o in _ind + _fix)]
_bad2 = [(a[0], b[0]) for i, a in enumerate(_dp) for b in _dp[i+1:] if _m.dist(a[1:3], b[1:3]) < 0.8*(a[3] + b[3])]
rep('(b2) drift plants clear of individuals and kept trees', not _bad, f'{len(_bad)} under another symbol')
rep('(b2) drift plants clear of each other', not _bad2, f'{len(_bad2)} overlapping pairs {_bad2[:3]}')

# (c) pump corridor is clear lawn
beds_all = unary_union([Lo.plantable, Lo.util_bed] + [dd['geom'] for dd in Lo.DRIFTS])
cor = unary_union([Lo.pump_corridor, Lo.pump_front])
w = Lo.pump_corridor.minimum_rotated_rectangle
rep('(c) pump corridor + door zone clear of beds', cor.intersection(beds_all).area < 0.05,
    f'overlap {cor.intersection(beds_all).area:.2f} sq ft; corridor 4.0 ft wide, {cor.area:.0f} sq ft; touches dog pad {Lo.pump_corridor.distance(Lo.dog_pad) < 0.1}')

# (d) zone flows
for z in IR.zones:
    rep(f"(d) zone {z['z']} <= 12 gpm", z['gpm'] <= 12, f"{z['gpm']} gpm, {z['area']} sq ft, valve {z['valve']}")

# (e) yearly budget: every scenario, every year within that year's (inflated) budget
bad_e = [(k, y['year'], round(y['spent']), round(y['budget'])) for k, Y in SC.SCEN.items() for y in Y if y['spent'] > y['budget'] + 0.5]
rep('(e) every year <= its budget, all 6 scenarios', not bad_e and len(SC.SCEN) == 6,
    '; '.join(f"${b:,} {'vol' if v else 'hired'}: {len(Y)} yrs, ${sum(y['spent'] for y in Y):,.0f}" for (b, v), Y in SC.SCEN.items()) + (f' OVER: {bad_e}' if bad_e else ''))
rep('(e) year-one budget = pick, +4.25%/yr after', all(abs(Y[0]['budget'] - b) < 1e-6 and (len(Y) < 2 or abs(Y[1]['budget']/Y[0]['budget'] - 1.0425) < 1e-9) for (b, v), Y in SC.SCEN.items()))
rep('(e) arborist visits only in years 2, 4, 6, 10 while the build runs',
    all(sorted(y['year'] for y in Y if any(i['desc'].startswith('Arborist') for i in y['items'])) == [n for n in (2, 4, 6, 10) if n <= len(Y)] for Y in SC.SCEN.values()))
for (b, v), Y in SC.SCEN.items():
    rm = [it.get('rm') for y in Y for it in y['items'] if it.get('rm')]
    rep(f"(e) every remove-later item scheduled once (${b:,} {'vol' if v else 'hired'})", sorted(rm) == sorted(i['id'] for i in Lo.REMOVE), f'{len(rm)} removals')

# rules
gate = Lo.GATE_C
bee = [dd for dd in Lo.DRIFTS if dd['code'] in ('MP', 'MS', 'AT', 'SS', 'CL', 'LS', 'ZI') and dd['geom'].distance(Point(*gate)) < 15]
rep('rule: bee-heavy/toxic plants >= 15 ft from the gate', not bee, f"{[(b['code'], round(b['geom'].distance(Point(*gate)),1)) for b in bee]}")
dogz = unary_union([Lo.dog_poly, Lo.wing])
tox = [dd['code'] for dd in Lo.DRIFTS if dd['code'] in ('AT', 'ZI') and dd['geom'].distance(dogz) < 20]
rep('rule: milkweed and coontie >= 20 ft from dog area', not tox, f"closest coontie {min(dd['geom'].distance(dogz) for dd in Lo.DRIFTS if dd['code'] == 'ZI'):.1f} ft")
pr = [(k, round(Lo.rock.distance(Point(*p)), 2)) for k, p in Lo.CABBAGE if Lo.rock.distance(Point(*p)) < Lo.PALM_ROCK - 0.05]
rep('rule: every cabbage palm kept, fence strip >= 3 ft off each trunk', len(Lo.PALMS) == 6 and not pr and not [r for r in Lo.REMOVE if r['kind'] == 'palm'], f'{len(Lo.PALMS)} palms {pr}')
newtrees = [(c, x, y) for c, x, y in Lo.ind if c == 'MFT'] + [(c, x, y) for c, x, y, r in Lo.ROW_TREES]
rep('rule: no new tree within 20 ft of fence', all(Lo.deck.distance(Point(x, y)) >= 20 for c, x, y in newtrees),
    f"min {min(Lo.deck.distance(Point(x, y)) for c, x, y in newtrees):.1f} ft")
# ---- review items
# R1/R2: individual trees/shrubs vs path and benches
pathb = unary_union([Lo.path_poly, Lo.dog_poly] + Lo.BENCHES)
trunk = [(c, round(pathb.distance(Point(x, y)), 1)) for c, x, y in Lo.ind if pathb.distance(Point(x, y)) < 4.0]
rep('R1 every individual trunk >= 4 ft from path edge', not trunk, f"min {min(pathb.distance(Point(x, y)) for c, x, y in Lo.ind):.1f} ft {trunk}")
mft = [(x, y) for c, x, y in Lo.ind if c == 'MFT'][0]
rep("R1 Simpson's stopper canopy (6.5 ft) clears the path", pathb.distance(Point(*mft)) >= Lo.SYM_R['MFT'],
    f"trunk {pathb.distance(Point(*mft)):.1f} ft from path, {math.dist(mft, Lo.N3):.1f} ft from the N3 bench node")
over = [(c, round(x, 1), round(y, 1)) for c, x, y in Lo.ind if Point(x, y).buffer(Lo.SYM_R[c]).intersection(pathb).area > 0.01]
over += [(d['code'], round(px_, 1), round(py_, 1)) for d in Lo.DRIFTS for px_, py_ in d['pts']
         if Point(px_, py_).buffer(Lo.PAL[d['code']][4]*0.46 if d['code'] != 'DO' else 0.62).intersection(pathb).area > 0.05]
rep('R2 no plant symbol overlaps path, dog pad or benches', not over, f'{len(over)} overlaps {over[:4]}')
shsl = [r for r in Lo.REMOVE if r['id'] == 'shsl'][0]
wp_path = [[it['wp'] for y in Y for it in y['items'] if it.get('rm') == 'shsl'] for Y in SC.SCEN.values()]
rep('R2 south-lawn shrub on the path line is removed with that path segment (WP4)', all(w == [4] for w in wp_path) and 4 in SC.WP_PATH)
# R3: point-feature hit targets are in the top layer, above drifts and beds
import render as RR, compose as CO
svg = CO.plan_svg('plant')
top = svg.rindex('class="hitlayer"')
last_drift = svg.rfind('data-k="p:'); last_bed = svg.rfind('data-k="f:bed"'); last_kiosk = svg.rfind('data-k="f:kiosk"')
keys = {k for k, *_ in RR.hit_points()}
need = {'f:dump', 'f:marker', 'f:nopark', 'f:queen', 'f:palmne', 'f:palmpair', 'f:palmgate', 'f:palme', 'f:palmn', 'f:oak', 'f:util', 'f:notice', 'f:yucca', 'f:pitto'}
rep('R3 point features in a top hit layer (above drifts, beds, kiosk)', top > max(last_drift, last_bed, last_kiosk) and need <= keys,
    f"{len(RR.hit_points())} targets, min radius {min(r for *_, r in RR.hit_points()):.0f} px")
import inspect
rep('R3 leader dots ignore clicks', inspect.getsource(RR.leader).count('pointer-events="none"') == 2 and svg.count('pointer-events="none"/>') >= 2)
# R4: B-1 scope lists the actual removed items per year, no empty plant groups
import budget_section as BS
bad4 = []
for y in [y for Y in SC.SCEN.values() for y in Y]:
    ids = [it['rm'] for it in y['items'] if it.get('rm')]
    txt = ' '.join(a for n, acts in BS.scope_lines(y) for a in acts)
    for i in ids:
        nm = [r['name'] for r in Lo.REMOVE if r['id'] == i][0]
        if nm not in txt: bad4.append((y['year'], i))
    if 'fan palms, clipped shrubs' in txt: bad4.append((y['year'], 'boilerplate'))
    if '()' in BS.year_table(y): bad4.append((y['year'], 'empty group'))
rep('R4 B-1 removal lines name the real items; no empty groups', not bad4, str(bad4))
# R5: valve-marker ring edge >= 2 ft from path
mk = [round(pathb.distance(Point(*m)) - Lo.MARKER_R, 2) for m in Lo.MARKERS]
rep('R5 valve-marker ring edge >= 2 ft from path', min(mk) >= 2, f'{mk} ft')
# R6: zone badge contrast (white text)
cs = {z: round(IR.contrast_white(c), 2) for z, c in IR.BADGE.items()}
rep('R6 zone badges >= 4.5:1 with white text', min(cs.values()) >= 4.5, str(cs))
# R7: path length parts add up
rep('R7 path length parts add up', round(Lo.LOOP_LEN) + round(Lo.SPUR_LEN) + round(Lo.STREET_LEN) == Lo.path_len,
    f"{Lo.LOOP_LEN:.0f} + {Lo.SPUR_LEN:.0f} + {Lo.STREET_LEN:.0f} = {Lo.path_len:.0f} ft")
print('ALL PASS' if ok else 'SOME CHECKS FAILED')