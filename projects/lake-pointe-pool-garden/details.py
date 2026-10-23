"""Construction detail drawings (sections) as SVG strings. Units: px, ~12 px = 1 inch in sections."""
import math, random

def note(x, y, tx, ty, s, anchor='start'):
    return (f'<path d="M{x},{y} L{tx},{ty} L{tx + (14 if anchor == "start" else -14)},{ty}" class="dl"/>'
            f'<circle cx="{x}" cy="{y}" r="1.8" class="dd"/>'
            f'<text x="{tx + (17 if anchor == "start" else -17)}" y="{ty + 3}" class="dt" text-anchor="{anchor}">{s}</text>')

def soil(x0, x1, y0, y1):
    rnd = random.Random(int(x0+y0)); dots = ''.join(
        f'<circle cx="{rnd.uniform(x0, x1):.1f}" cy="{rnd.uniform(y0, y1):.1f}" r="{rnd.uniform(.5, 1.1):.1f}" class="dsoil"/>' for _ in range(int((x1-x0)*(y1-y0)/160)))
    return f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" class="dsoilbg"/>{dots}'

def gravel(x0, x1, y0, y1, big=False):
    rnd = random.Random(int(x1*3+y1)); n = int((x1-x0)*(y1-y0)/(26 if big else 14))
    g = ''.join(f'<ellipse cx="{rnd.uniform(x0+2, x1-2):.1f}" cy="{rnd.uniform(y0+2, y1-2):.1f}" rx="{rnd.uniform(1.6, 3.4) if big else rnd.uniform(1, 2):.1f}" ry="{rnd.uniform(1.1, 2.4) if big else rnd.uniform(.7, 1.4):.1f}" class="dgrav"/>' for _ in range(n))
    return f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" class="dgravbg"/>{g}'

def fines(x0, x1, y0, y1):
    rnd = random.Random(int(x0+y1)); n = int((x1-x0)*(y1-y0)/9)
    g = ''.join(f'<circle cx="{rnd.uniform(x0+1, x1-1):.1f}" cy="{rnd.uniform(y0+1, y1-1):.1f}" r=".7" class="dfine"/>' for _ in range(n))
    return f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" class="dfinebg"/>{g}'

def mulch(x0, x1, y0, y1):
    rnd = random.Random(int(x0*7+y0)); n = int((x1-x0)*(y1-y0)/12)
    g = ''.join(f'<path d="M{(x:=rnd.uniform(x0+2, x1-4)):.1f},{(y:=rnd.uniform(y0+1, y1-1)):.1f} l{rnd.uniform(2, 5):.1f},{rnd.uniform(-1, 1):.1f}" class="dmulch"/>' for _ in range(n))
    return f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" class="dmulchbg"/>{g}'

def plant(x, base, h, w, kind='shrub'):
    if kind == 'grass':
        blades = ''.join(f'<path d="M{x},{base} Q{x + (i-4)*w/14:.1f},{base - h*.6:.1f} {x + (i-4)*w/8:.1f},{base - h + abs(i-4)*3:.1f}" class="dplant"/>' for i in range(9))
        return blades + f'<ellipse cx="{x}" cy="{base + 10}" rx="{w*.22:.1f}" ry="9" class="droot"/>'
    return (f'<ellipse cx="{x}" cy="{base - h/2}" rx="{w/2}" ry="{h/2}" class="dshrub"/>'
            f'<line x1="{x}" y1="{base}" x2="{x}" y2="{base - h*.35}" class="dplant"/>'
            f'<ellipse cx="{x}" cy="{base + 12}" rx="{w*.28:.1f}" ry="12" class="droot"/>')

def frame(w, h, title, num, scale, body):
    return (f'<svg viewBox="0 0 {w} {h + 40}" class="detail" role="img" aria-label="{title}">'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h + 39}" class="dframe"/>{body}'
            f'<line x1="0" y1="{h}" x2="{w}" y2="{h}" class="dframe"/>'
            f'<circle cx="26" cy="{h + 20}" r="14" class="dnumc"/><text x="26" y="{h + 25}" class="dnum" text-anchor="middle">{num}</text>'
            f'<text x="50" y="{h + 18}" class="dtitle">{title}</text><text x="50" y="{h + 31}" class="dscale">{scale}</text></svg>')

def path_standard():
    W, H = 640, 300; g = 170  # grade line y
    b = []
    b.append(soil(0, W, g, H-4))
    # beds both sides
    b.append(mulch(30, 190, g-14, g)); b.append(mulch(450, 610, g-14, g))
    b.append(plant(100, g-14, 70, 70)); b.append(plant(530, g-14, 46, 60, 'grass'))
    # path: 48in wide = 384 px (8px/in)
    x0, x1 = 128+62, 128+62+384-128  # keep compact: draw at 5.33 px/in
    x0, x1 = 192, 448
    b.append(gravel(x0, x1, g, g+28))              # 4in base (scaled)
    b.append(fines(x0, x1, g-16, g+2))             # 3in stabilized fines (slight crown)
    b.append(f'<path d="M{x0},{g-14} Q{(x0+x1)/2},{g-20} {x1},{g-14}" class="dcrown"/>')
    for xe in (x0-4, x1):
        b.append(f'<rect x="{xe}" y="{g-16}" width="4" height="34" class="dedge"/><path d="M{xe+2},{g+18} l0,22" class="dstake"/>')
    b.append(f'<path d="M{x0},{g+30} H{x1}" class="dfab"/>')
    # dims
    b.append(f'<path d="M{x0-4},{g-40} H{x1+4} M{x0-4},{g-46} v12 M{x1+4},{g-46} v12" class="ddim"/><text x="{(x0+x1)/2}" y="{g-46}" class="ddimt" text-anchor="middle">4\'-0" path</text>')
    b.append(note(300, g-10, 300, 40, '3" crushed limestone screenings (¼" minus)'))
    b.append(f'<text x="317" y="56" class="dt">compacted in 2 lifts; 2% cross-slope; binder optional</text>')
    b.append(note(250, g+14, 210, 230, 'base rock only where the sand is soft (else none)'))
    b.append(note(x1+2, g, 625, 96, '3/16" x 4" aluminum edging, 16" stakes @ 30"', 'end'))
    b.append(note(380, g+31, 625, 250, 'non-woven geotextile (optional in clean sand)', 'end'))
    b.append(note(560, g+30, 560, 280, 'compacted native sand subgrade', 'end'))
    b.append(note(150, g-7, 20, 40, '3" shredded mulch in beds, 1" below path'))
    return frame(W, H, 'Nature path · typical section', 'A', 'Not to scale · in sun beds outside the oak root zone', ''.join(b))

def path_nodig():
    W, H = 640, 300; g = 190
    b = [soil(0, W, g, H-4)]
    # oak roots
    for i, (x, y, r) in enumerate([(80, g+40, 60), (300, g+55, 90), (520, g+35, 70)]):
        b.append(f'<path d="M{x-r},{y} C{x-r/2},{y-14} {x+r/2},{y+12} {x+r},{y-4}" class="droots"/>')
    b.append(mulch(30, 180, g-12, g)); b.append(mulch(460, 610, g-12, g))
    b.append(plant(100, g-12, 54, 56)); b.append(plant(540, g-12, 50, 50, 'grass'))
    x0, x1 = 196, 444
    b.append(f'<path d="M{x0-30},{g} L{x0},{g-34} L{x1},{g-34} L{x1+30},{g} Z" class="dfinebg"/>')
    b.append(fines(x0, x1, g-34, g-4))
    # geocell walls
    for x in range(x0+6, x1, 22):
        b.append(f'<path d="M{x},{g-30} l10,0 l0,26 l-10,0 Z" class="dcell"/>')
    b.append(f'<path d="M{x0-30},{g} H{x1+30}" class="dfab"/>')
    for xe in (x0-6, x1+2):
        b.append(f'<rect x="{xe}" y="{g-36}" width="4" height="34" class="dedge"/>')
    b.append(note(320, g-30, 330, 50, '2" screenings over 4" geocell filled with screenings'))
    b.append(f'<text x="347" y="66" class="dt">(total build-up ≈ 6", placed on top of existing grade)</text>')
    b.append(note(250, g+1, 200, 250, 'non-woven geotextile on existing grade · turf removed by hand only'))
    b.append(note(x1+3, g-20, 625, 112, 'edging pinned with 6" spikes only', 'end'))
    b.append(note(x0-20, g-6, 20, 112, 'taper shoulders with mulch, no soil fill'))
    b.append(note(300, g+50, 300, 285, 'oak roots undisturbed · no excavation, trenching or compaction', 'start'))
    b.append(f'<path d="M{x0-30},{g-60} H{x1+30}" class="ddim"/><text x="{(x0+x1)/2}" y="{g-66}" class="ddimt" text-anchor="middle">4\'-0" path + 1\'-0" tapered shoulders</text>')
    return frame(W, H, 'Nature path · no-dig section under the live oak', 'B', 'Not to scale · use inside the oak drip line and within 10 ft of existing palms', ''.join(b))

def pool_band():
    W, H = 640, 300; g = 180
    b = [soil(0, W, g, H-4)]
    # deck + fence
    b.append(f'<rect x="0" y="{g-8}" width="110" height="22" class="dconc"/>')
    b.append(f'<path d="M104,{g-8} V{g-110} M98,{g-108} H112 M98,{g-60} H112" class="dfence"/>')
    b.append(f'<text x="50" y="{g-20}" class="dt" text-anchor="middle">pool deck</text>')
    # rock band 3 ft
    b.append(gravel(112, 208, g-10, g+2, big=True))
    b.append(f'<path d="M112,{g+3} H208" class="dfab"/><rect x="208" y="{g-12}" width="4" height="30" class="dedge"/>')
    # band planting
    b.append(mulch(212, 600, g-10, g+1))
    b.append(plant(240, g-10, 18, 30)); b.append(plant(268, g-10, 18, 30))
    b.append(plant(330, g-10, 46, 54, 'grass')); b.append(plant(410, g-10, 52, 60)); b.append(plant(500, g-10, 60, 56, 'grass'))
    b.append(plant(590, g-10, 78, 70))
    for xd in range(222, 600, 24):
        b.append(f'<circle cx="{xd}" cy="{g-7}" r="2.4" class="ddrip"/>')
    # dims
    for (a, c, t) in [(112, 212, "3'-0\" climb-free"), (212, 300, '3\'-0"'), (300, 560, "6'–7' (band edge undulates 8'–14' from fence)")]:
        b.append(f'<path d="M{a},{g+40} H{c} M{a},{g+34} v12 M{c},{g+34} v12" class="ddim"/><text x="{(a+c)/2}" y="{g+56}" class="ddimt" text-anchor="middle">{t}</text>')
    b.append(note(160, g-6, 150, 50, '#57 crushed limestone, 2½" deep on fabric (won\'t float like mulch)'))
    b.append(note(250, g-24, 250, 80, 'twinflower ribbon, 12" tall'))
    b.append(note(410, g-58, 400, 104, "dwarf yaupon / dwarf Fakahatchee / muhly · 3 ft max"))
    b.append(note(590, g-84, 520, 30, 'meadow & shrubs beyond', 'end'))
    b.append(note(470, g-7, 450, 140, 'inline drip under shredded mulch (no nuggets)'))
    b.append(note(104, g-100, 160, 18, 'existing pool fence'))
    return frame(W, H, 'Pool edge band · section', 'C', 'Not to scale · applies on all four sides of the fenced deck', ''.join(b))

def valve_assembly():
    W, H = 640, 300; g = 110
    b = [soil(0, W, g, H-4), f'<rect x="0" y="{g-6}" width="{W}" height="6" class="dgravbg"/>']
    # valve box
    b.append(f'<path d="M150,{g-8} L170,{g+150} L470,{g+150} L490,{g-8} Z" class="dbox"/><rect x="140" y="{g-14}" width="360" height="8" class="dlid"/>')
    b.append(gravel(170, 470, g+150, g+176))
    # mainline
    y = g+128
    b.append(f'<path d="M20,{y} H190" class="dpipe"/><text x="24" y="{y-8}" class="dt">mainline (1" Sch 40 PVC, 18" cover)</text>')
    comps = [(200, 'tee'), (230, 'ball'), (290, 'valve'), (360, 'filter'), (420, 'prv')]
    b.append(f'<path d="M190,{y} H200 V{y-40} H450" class="dpipe"/>')
    b.append(f'<path d="M450,{y-40} H{W-20}" class="dpipe2"/>')
    b.append(f'<rect x="222" y="{y-48}" width="16" height="16" class="dcomp"/>')
    b.append(f'<rect x="270" y="{y-66}" width="40" height="34" rx="4" class="dcomp"/><rect x="282" y="{y-80}" width="16" height="14" class="dcomp"/>')
    b.append(f'<rect x="346" y="{y-62}" width="28" height="44" rx="6" class="dcomp"/>')
    b.append(f'<rect x="404" y="{y-56}" width="32" height="28" rx="12" class="dcomp"/>')
    b.append(note(230, y-48, 70, 40, 'brass ball valve (isolation)', 'start'))
    b.append(note(290, y-80, 250, 18, '1" remote-control valve, low-flow rated, wired to controller'))
    b.append(note(360, y-62, 420, 52, '1" disc filter, 150–200 mesh'))
    b.append(note(420, y-56, 625, 84, 'pressure regulator, 25–30 psi', 'end'))
    b.append(note(560, y-40, 560, 170, 'zone header to drip (1" poly pipe)', 'end'))
    b.append(note(320, g+160, 330, 250, '3" pea gravel sump · box on 4 bricks', 'start'))
    b.append(note(150, g-10, 40, 76, 'jumbo valve box, lid flush with rock band', 'start'))
    return frame(W, H, 'Drip zone valve assembly', 'D', 'Not to scale · one assembly per zone, two per box where noted on plan', ''.join(b))

def drip_layout():
    W, H = 640, 300
    b = [f'<rect x="40" y="30" width="560" height="230" rx="18" class="dmulchbg"/>']
    b.append(f'<path d="M60,40 V250" class="dpipe2"/>')
    rows = list(range(52, 250, 24))
    for y in rows:
        b.append(f'<path d="M60,{y} H560" class="dtube"/>')
        for x in range(76, 560, 16):
            b.append(f'<circle cx="{x}" cy="{y}" r="1.6" class="demit"/>')
        b.append(f'<circle cx="60" cy="{y}" r="3" class="dcomp"/>')
    b.append(f'<path d="M560,{rows[0]} V{rows[-1]}" class="dtube"/><rect x="566" y="{rows[-1]-6}" width="14" height="12" class="dcomp"/>')
    b.append(f'<rect x="566" y="{rows[0]-6}" width="14" height="12" class="dcomp"/>')
    # shrubs
    for x, y, r in [(180, 100, 24), (300, 150, 22), (430, 96, 26), (250, 220, 20), (470, 205, 22)]:
        b.append(f'<circle cx="{x}" cy="{y}" r="{r}" class="dshrubt"/>')
    b.append(f'<path d="M100,{rows[2]} V{rows[3]} M94,{rows[2]} h12 M94,{rows[3]} h12" class="ddim"/><text x="110" y="{rows[2]+15}" class="ddimt">18" rows</text>')
    b.append(f'<path d="M140,{rows[5]-10} H156 M140,{rows[5]-16} v12 M156,{rows[5]-16} v12" class="ddim"/><text x="160" y="{rows[5]-12}" class="ddimt">0.6 gph emitters @ 12"</text>')
    b.append(f'<text x="70" y="22" class="dt">1" poly header with ½" tubing adapters</text>')
    b.append(f'<text x="600" y="22" class="dt" text-anchor="end">flush valve each end · air-relief at high point</text>')
    b.append(f'<text x="320" y="282" class="dt" text-anchor="middle">tubing 4" in from bed edges & hardscape · staples every 3–4 ft · under mulch · large shrubs get a ring of 2 emitters</text>')
    return frame(W, H, 'Inline drip grid · typical bed', 'E', 'Not to scale · ≈0.64 in/hr precipitation rate', ''.join(b))

def sleeve():
    W, H = 640, 240; g = 90
    b = [soil(0, W, g, H-4)]
    b.append(fines(180, 460, g-16, g+2)); b.append(gravel(180, 460, g+2, g+26))
    b.append(mulch(20, 176, g-10, g)); b.append(mulch(464, 620, g-10, g))
    b.append(f'<rect x="100" y="{g+70}" width="440" height="24" rx="12" class="dsleeve"/>')
    b.append(f'<path d="M100,{g+82} H540" class="dpipe2"/>')
    b.append(f'<path d="M100,{g+120} H180 M100,{g+114} v12 M180,{g+114} v12 M460,{g+120} H540 M460,{g+114} v12 M540,{g+114} v12" class="ddim"/>')
    b.append(f'<text x="140" y="{g+138}" class="ddimt" text-anchor="middle">24" min</text><text x="500" y="{g+138}" class="ddimt" text-anchor="middle">24" min</text>')
    b.append(note(320, g+72, 330, 30, '2" Sch 40 PVC sleeve, 12" min cover, ends staked'))
    b.append(note(250, g+82, 200, 200, 'drip header or wire runs inside'))
    b.append(note(320, g-8, 470, 60, 'install before path base'))
    return frame(W, H, 'Sleeve under the nature path', 'F', 'Not to scale · at every crossing shown on the irrigation plan', ''.join(b))

ALL = [path_standard, path_nodig, pool_band, valve_assembly, drip_layout, sleeve]