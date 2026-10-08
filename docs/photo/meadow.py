# The photo's sage carried on below its bottom edge in pen: each drawn stem starts where a real
# stem leaves the photo, keeps its lean and trails off on its own, at its own length, fading
# out; a few sprigs rise just outside the frame with looping flower heads, some in rose. Nothing
# meets at a point and there is no ground: the drawing dissolves into the page. On screen it is
# drawn stroke by stroke at a pen's pace (left side, then right; stems, then the sprigs and
# their flowers): each stroke carries its own delay and duration.
# Coordinates are the photo's (1500 x 1000), extended.
# Usage: python3 docs/photo/meadow.py src/components/PortraitMeadow.astro
import math, random, sys
out_path = sys.argv[1]
random.seed(11)
VB = (-150, 0, 1800, 1200)
strokes, defs = [], []                       # strokes in the order they are made; gradients
f = lambda v: f'{v:.1f}'

def smooth(pts):
    # a curve through the points (Catmull-Rom as cubic Beziers)
    d = f'M{f(pts[0][0])} {f(pts[0][1])}'
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(len(pts) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}'
    return d

def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])

def wobbly(p0, p1, p2, p3, n=9, jit=3.2, t0=0, t1=1):
    # points along a cubic with a hand's wobble across the line
    pts = []
    for i in range(n):
        t = t0 + (t1 - t0) * i / (n - 1)
        x, y = bez(p0, p1, p2, p3, t)
        xa, ya = bez(p0, p1, p2, p3, min(1, t + .01)); xb, yb = bez(p0, p1, p2, p3, max(0, t - .01))
        dx, dy = xa - xb, ya - yb; L = math.hypot(dx, dy) or 1
        j = random.uniform(-jit, jit) if 0 < i < n - 1 else 0
        pts.append((x - dy / L * j, y + dx / L * j))
    return pts

def stroke(pts, extra='', plant=None, kind='stem'):
    # plant: (side, group, x) of the plant the stroke belongs to; kind sets the pen's speed
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    strokes.append(dict(svg=f'<path pathLength="1" d="{smooth(pts)}"{extra}/>', plant=plant, kind=kind, length=length))

def fade(a, b, stops):
    # the ink along a line from a to b, as (offset, opacity) stops
    gid = f'pm{len(defs)}'
    s = ''.join(f'<stop offset="{o}" stop-color="currentColor" stop-opacity="{op}"/>' for o, op in stops)
    defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}">{s}</linearGradient>')
    return f' stroke="url(#{gid})"'

def coil(p0, p1, p2, p3, t0, t1, b0, loops, plant, color=None):
    # a looping scribble climbing the stem from t0 to t1, its loops shrinking towards the tip
    pts = []
    N = loops * 14
    for i in range(N + 1):
        s = i / N
        t = t0 + (t1 - t0) * s
        x, y = bez(p0, p1, p2, p3, t)
        xa, ya = bez(p0, p1, p2, p3, min(1, t + .01)); xb, yb = bez(p0, p1, p2, p3, max(0, t - .01))
        dx, dy = xa - xb, ya - yb; L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L                # along the stem
        px, py = -uy, ux                       # across it
        th = 2 * math.pi * loops * s
        b = b0 * (1 - .55 * s) * random.uniform(.85, 1.15)
        along = -b * .55 * math.sin(th)
        across = b * math.cos(th)
        pts.append((x + ux * along + px * across, y + uy * along + py * across))
    extra = ' stroke-width="1.1"' + (f' style="stroke:{color}"' if color else '')
    stroke(pts, extra, plant, 'coil')

# the stems, where the photo's stems leave its bottom edge: (x at the edge, how far the stem
# shifts sideways 40 px further up); each goes on down the way it was going
STEMS = [(54, 0), (112, 4), (184, 0),
         (973, -9), (1046, 0), (1136, 2), (1195, -12),
         (1241, 12), (1302, 8), (1356, -2), (1391, -3), (1427, -12), (1469, 0)]
prev = None
for i, (x, lean) in enumerate(STEMS):
    L = random.uniform(66, 122)
    while prev is not None and abs(L - prev) < 16:      # neighbours end at different heights
        L = random.uniform(66, 122)
    prev = L
    drift = -lean * L / 50 + random.uniform(-6, 6)
    p0 = (x, 1000)
    p1 = (x - lean * .6, 1000 + L * .33)
    p2 = (x + drift * .75 + random.uniform(-3, 3), 1000 + L * .68)
    p3 = (x + drift, 1000 + L)
    ink = fade(p0, p3, [(0, 1), (.5, 1), (1, 0)])       # the pen lifts off
    plant = ('L' if x < 750 else 'R', 0, x)
    stroke(wobbly(p0, p1, p2, p3, n=8, jit=3), ink, plant, 'stem')
    if random.random() < .5:                            # the pen goes over it again, partly
        stroke(wobbly(p0, p1, p2, p3, n=6, jit=4, t0=random.uniform(.1, .3), t1=random.uniform(.6, .9)), ink + ' stroke-opacity=".5" stroke-width="1"', plant, 'over')
    if random.random() < .45:                           # a leaf: a quick tick off the stem
        t = random.uniform(.15, .4)
        lx, ly = bez(p0, p1, p2, p3, t)
        side = random.choice([-1, 1])
        tip = (lx + side * random.uniform(10, 16), ly - random.uniform(8, 14))
        stroke([(lx, ly), ((lx + tip[0]) / 2 + side * 2, (ly + tip[1]) / 2 + 3), tip], ' stroke-width="1"', plant, 'leaf')

# sprigs rising just outside the frame, out of nothing, with looping flower heads
ROSE = 'var(--rose)'
for base, tip, bend, loops, b0, col in [
    ((1490, 1104), (1556, 840), 22, 6, 9, ROSE),
    ((1455, 1104), (1522, 930), -14, 4, 8, None),
    ((1520, 1106), (1600, 990), 10, 3, 7, ROSE),
    ((-10, 1100), (-66, 896), -18, 5, 8.5, ROSE),
    ((28, 1100), (-18, 970), 10, 3, 7, None),
]:
    p0 = base; p3 = tip
    p1 = (base[0] + bend * .4, base[1] - (base[1] - tip[1]) * .35)
    p2 = (tip[0] + bend, tip[1] + (base[1] - tip[1]) * .3)
    ink = fade(p0, bez(p0, p1, p2, p3, .45), [(0, 0), (1, 1)])
    plant = ('L' if base[0] < 750 else 'R', 1, base[0])
    stroke(wobbly(p0, p1, p2, p3, n=8, jit=2.6), ink, plant, 'sprig')
    coil(p0, p1, p2, p3, .5, 1.0, b0, loops, plant, col)

# The drawing order: the left side, then the right; on each, the stems from left to right,
# then the sprigs; within a plant, its strokes as they were made. A plant's first stroke starts
# when the one before is partly drawn, as a quick hand would; strokes take as long as their
# length at the pen's speed for that kind of stroke.
SPEED = {'stem': 420, 'over': 600, 'leaf': 260, 'sprig': 520, 'coil': 900}    # units a second
TOTAL = 4.6                                                                  # seconds, all told
order = sorted(range(len(strokes)), key=lambda i: ({'L': 0, 'R': 1}[strokes[i]['plant'][0]], strokes[i]['plant'][1], strokes[i]['plant'][2], i))
t_plant = 0.0; prev_plant = None; t = 0.0; last = None
for i in order:
    s = strokes[i]
    s['dur'] = min(1.3, max(.12, s['length'] / SPEED[s['kind']]))
    if s['plant'] != prev_plant:
        start = 0.0 if last is None else t_plant + strokes[last]['dur'] * .55
        t_plant = start; prev_plant = s['plant']
    else:
        start = t + strokes[last]['dur'] * .85
    s['start'] = start; t = start; last = i
end = max(strokes[i]['start'] + strokes[i]['dur'] for i in order)
k = TOTAL / end
body = '\n'.join(f'  <g style="--d:{strokes[i]["start"] * k:.2f}s;--t:{strokes[i]["dur"] * k:.2f}s">{strokes[i]["svg"]}</g>' for i in order)
svg = (f'<svg class="meadow" viewBox="{VB[0]} {VB[1]} {VB[2]} {VB[3]}" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">\n'
       f'  <defs>{"".join(defs)}</defs>\n{body}\n</svg>')
open(out_path, 'w').write("---\n// The photo's sage carried on below its bottom edge in pen, in the photo's own coordinates.\n"
                          "// Generated by docs/photo/meadow.py; do not edit by hand.\n---\n" + svg + "\n")
print('wrote', out_path, len(strokes), 'strokes, drawn in', TOTAL, 's (pace x', round(k, 2), ')')
