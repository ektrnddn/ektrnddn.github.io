# Writes scene.html: the ink drawing of the mountains. Hatching is computed from the skyline.
import math, sys, random
S = sys.argv[1]

# Main range skyline: an envelope (a broad massif with a second, lower knot), layered
# noise for irregularity, and a handful of sharp spires. Seeded so the drawing is stable.
rng = random.Random(7)
def skyline(x0, x1, base, massif, seed_phase, spires, step=11, jitter=1.6):
    r = random.Random(seed_phase)
    phases = [r.random() * 6.283 for _ in range(4)]
    pts = []
    x = x0
    while x <= x1:
        e = base
        for (cx, amp, wid) in massif: e -= amp * math.exp(-((x - cx) / wid) ** 2)
        n = 16 * math.sin(x / 95 + phases[0]) + 9 * math.sin(x / 47 + phases[1]) + 5 * math.sin(x / 23 + phases[2]) + 2.5 * math.sin(x / 11 + phases[3])
        sp = 0
        for (sx, h, w) in spires: sp = max(sp, h * max(0, 1 - abs(x - sx) / w))
        pts.append((x, e + n - sp + r.uniform(-jitter, jitter)))
        x += step + r.uniform(-2, 2)
    pts[-1] = (x1, pts[-1][1])
    return [(round(px), round(py, 1)) for px, py in pts]

spires = [(760, 40, 16), (812, 26, 12), (858, 56, 18), (884, 36, 13), (930, 24, 11), (1010, 40, 15), (1052, 20, 10), (1140, 32, 13), (1195, 16, 9), (1290, 26, 12), (1350, 14, 9), (640, 22, 12), (690, 16, 10), (560, 12, 9)]
range_pts = skyline(0, 1440, 378, [(860, 118, 250), (1130, 48, 130), (600, 30, 120), (200, 18, 160)], 3, spires)
farfar = skyline(0, 1440, 336, [(1150, 42, 160), (1330, 26, 90), (120, 22, 140)], 11, [(1120, 22, 12), (1230, 16, 10), (1330, 20, 11), (90, 12, 10)], step=14, jitter=1)

def poly(pts): return 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
def closed(pts, x0, x1, bottom=640): return poly(pts) + f' L{x1} {bottom} L{x0} {bottom} Z'

# Summits: local minima of y with some prominence
def summits_of(pts, min_prom):
    out = []
    for i in range(2, len(pts) - 2):
        x, y = pts[i]
        if y < pts[i-1][1] and y <= pts[i+1][1]:
            prom = min(max(pts[j][1] for j in range(max(0, i-6), i)), max(pts[j][1] for j in range(i+1, min(len(pts), i+7)))) - y
            if prom >= min_prom: out.append((i, prom))
    return out
rock, snow, hatch = [], [], []
for i, prom in summits_of(range_pts, 14):
    x, y = range_pts[i]
    # the steeper face gets a rock line curving down it
    lx, ly = range_pts[i-1]; rx, ry = range_pts[i+1]
    steep_left = (ly - y) / max(1, x - lx) > (ry - y) / max(1, rx - x)
    sgn = -1 if steep_left else 1
    L = min(60, 1.5 * prom + 14)
    rock.append(f'M{x + sgn*2} {y + 5} q{sgn*L*0.18:.0f} {L*0.45:.0f} {sgn*L*0.42:.0f} {L:.0f}')
    if prom > 30:
        rock.append(f'M{x - sgn*3} {y + 9} q{-sgn*L*0.1:.0f} {L*0.3:.0f} {-sgn*L*0.22:.0f} {L*0.62:.0f}')
    # snow hatches on the shaded (right) face just under the summit
    for k in range(3 if prom > 30 else 2):
        t = 9 + k * 8
        hatch.append(f'M{x + 4 + k*3} {y + t} l{7 + k*2} {3 + k}')
# Scalloped snow line following the skyline, some way below it
def snowline(pts, depth):
    out = []
    for i, (x, y) in enumerate(pts):
        if i % 2: continue
        d = depth + 10 * math.sin(x / 37) + rng.uniform(-3, 3)
        out.append((x, y + d))
    return out
snow_pts = [(x, y) for x, y in snowline(range_pts, 34) if 640 <= x <= 1120]
snow_d = 'M' + ' '.join((f'{x} {y:.0f}' if i == 0 else f'Q{x - 5} {y - 6:.0f} {x} {y:.0f}') for i, (x, y) in enumerate(snow_pts))

# Foothill in front of the range: rounded, forested
foothill = 'M300 470 C 420 452, 520 444, 640 452 S 860 474, 980 462 S 1200 430, 1320 438 S 1400 446, 1440 442'
trees_fh = ' '.join(f'M{x} {y} l3 -7 3 7' for x, y in [(360,458),(410,455),(560,447),(700,455),(760,462),(900,468),(1000,461),(1080,449),(1160,440),(1250,436),(1360,440)])

svg = f'''<svg viewBox="0 -20 1440 660" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <g class="farfar">
    <path class="f" d="{closed(farfar, 0, 1440)}"/>
    <path class="s" d="{poly(farfar)}"/>
  </g>
  <g class="range">
    <path class="f" d="{closed(range_pts, 0, 1440)}"/>
    <path class="s" d="{poly(range_pts)}"/>
    <path class="h" d="{' '.join(rock)}"/>
    <path class="snowline" d="{snow_d}"/>
    <path class="snow" d="{' '.join(hatch)}"/>
  </g>
  <g class="foothill">
    <path class="f" d="{foothill} L1440 640 L300 640 Z"/>
    <path class="s" d="{foothill}"/>
    <path class="trees" d="{trees_fh}"/>
  </g>
  <g class="near">
    <path class="f" d="M0 384 C 90 372, 160 392, 250 418 S 400 470, 520 522 S 600 548, 640 552 L640 640 L0 640 Z"/>
    <path class="s" d="M0 384 C 90 372, 160 392, 250 418 S 400 470, 520 522 S 600 548, 640 552"/>
    <path class="trees" d="M62 384 l3 -7 3 7 M110 386 l3 -8 3 8 M170 400 l3 -7 3 7 M330 452 l3 -7 3 7 M372 468 l3 -8 3 8 M430 494 l3 -7 3 7 M492 516 l3 -7 3 7"/>
  </g>
  <g class="near">
    <path class="f" d="M900 556 C 1000 540, 1080 500, 1180 468 S 1330 428, 1440 418 L1440 640 L900 640 Z"/>
    <path class="s" d="M900 556 C 1000 540, 1080 500, 1180 468 S 1330 428, 1440 418"/>
    <path class="trees" d="M1120 486 l3 -7 3 7 M1200 462 l3 -8 3 8 M1300 438 l3 -7 3 7 M1380 426 l3 -7 3 7"/>
  </g>
  <g class="meadow">
    <path class="f" d="M0 560 C 240 550, 480 568, 720 556 S 1120 546, 1440 560 L1440 640 L0 640 Z"/>
    <path class="s" d="M0 560 C 240 550, 480 568, 720 556 S 1120 546, 1440 560"/>
    <path class="grass" d="M96 558 l-2 -12 M118 556 l3 -10 M300 562 l-1 -11 M330 563 l4 -9 M760 556 l-3 -12 M790 555 l2 -9 M902 552 l-2 -11 M930 551 l3 -10 M1180 554 l-2 -12 M1204 554 l3 -9 M1340 558 l-2 -11"/>
    <g class="flowers">
      <path class="stem" d="M212 555 v-16 M405 561 v-13 M700 556 v-18 M818 552 v-14 M1048 548 v-16 M1275 554 v-13"/>
      <circle cx="212" cy="537" r="2.6"/><circle cx="405" cy="546" r="2.2"/><circle cx="700" cy="536" r="2.8"/><circle cx="818" cy="536" r="2.3"/><circle cx="1048" cy="530" r="2.6"/><circle cx="1275" cy="539" r="2.2"/>
    </g>
    <g class="figure" transform="translate(600 558)">
      <path class="ink" d="M 7 -96 C 4 -101, -3 -103, -8 -100 C -12 -104, -18 -101, -17 -96 C -22 -96, -24 -90, -20 -87 C -25 -85, -25 -79, -20 -77 C -24 -73, -21 -67, -16 -68 C -18 -63, -13 -60, -9 -63 C -8 -66, -7 -68, -6 -70 C -3 -72, 1 -74, 4 -78 C 8 -81, 10 -86, 9 -90 C 10 -93, 9 -95, 7 -96 Z"/>
      <path class="ink" d="M -10 -74 L 5 -74 C 10 -65, 10 -56, 8 -46 L -9 -46 C -12 -56, -12 -65, -10 -74 Z"/>
      <path class="ink" d="M -8 -46 L 7 -46 C 12 -34, 16 -18, 17 -6 L -18 -6 C -16 -18, -12 -34, -8 -46 Z"/>
      <path class="limb" d="M 4 -70 C 10 -62, 13 -54, 11 -44"/>
      <path class="limb" d="M -8 -70 C -13 -62, -14 -54, -11 -44"/>
      <path class="leg" d="M 5 -6 L 10 0 M -6 -6 L -12 0"/>
      <ellipse cx="12" cy="0.5" rx="5" ry="1.8" class="ink"/><ellipse cx="-14" cy="0.5" rx="5" ry="1.8" class="ink"/>
    </g>
  </g>
</svg>'''
html = '''<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#fff}svg{width:1440px;height:660px;display:block}
.f{fill:#fff;stroke:none}.s{fill:none;stroke-width:1.2}.h{fill:none;stroke-width:1;opacity:.8}
.farfar .s{stroke:#d6d6d6}.range .s{stroke:#4a4a4a;stroke-width:1.3}.range .h{stroke:#8a8a8a}.snow{fill:none;stroke:#6a6a6a;stroke-width:.9;opacity:.85}.snowline{fill:none;stroke:#c9c9c9;stroke-width:.9;opacity:.9}
.foothill .s{stroke:#8f8f8f;stroke-width:1.1}.foothill .trees{stroke:#8f8f8f}
.near .s{stroke:#2a2a2a}.trees{fill:none;stroke:#2a2a2a;stroke-width:1;opacity:.75}
.meadow .s{stroke:#191919;stroke-width:1.4}.grass{fill:none;stroke:#191919;stroke-width:1;opacity:.7}.flowers .stem{fill:none;stroke:#191919;stroke-width:1;opacity:.6}.flowers circle{fill:#d98aa0}
.figure .ink{fill:#191919;stroke:#191919;stroke-width:1;stroke-linejoin:round}.figure .limb{fill:none;stroke:#191919;stroke-width:5;stroke-linecap:round}.figure .leg{fill:none;stroke:#191919;stroke-width:4.5;stroke-linecap:round}
.church{fill:#2a2a2a;stroke:none}
</style></head><body>''' + svg + '</body></html>'
open(f'{S}/scene.html', 'w').write(html)
import json
import numpy as np
VW, VH, OY = 1440, 660, 20
xs = np.arange(VW + 1); top = np.full(VW + 1, 556.0)
for pts in (range_pts, farfar):
    px, py = zip(*pts); top[(xs >= px[0]) & (xs <= px[-1])] = np.minimum(top[(xs >= px[0]) & (xs <= px[-1])], np.interp(xs[(xs >= px[0]) & (xs <= px[-1])], px, py))
def bez(p, t):
    x0,y0,x1,y1,x2,y2,x3,y3 = p; u = 1 - t
    return (u**3*x0+3*u*u*t*x1+3*u*t*t*x2+t**3*x3, u**3*y0+3*u*u*t*y1+3*u*t*t*y2+t**3*y3)
for p in [(0,384,90,372,160,392,250,418),(250,418,340,444,430,496,520,522),(520,522,560,538,600,548,640,552),(900,556,1000,540,1080,500,1180,468),(1180,468,1280,436,1330,428,1440,418),(300,470,420,452,520,444,640,452),(640,452,760,460,860,474,980,462),(980,462,1100,450,1200,430,1320,438),(1320,438,1360,442,1400,446,1440,442)]:
    for t in np.linspace(0, 1, 300):
        x, y = bez(p, t); xi = int(round(x)); top[xi] = min(top[xi], y)
json.dump([round(float(top[int(i * VW / 47)] + OY) / VH, 3) for i in range(48)], open(f'{S}/skyline-samples.json', 'w'))
print('scene.html written;', len(range_pts), 'skyline points,', len(rock), 'rock lines,', len(hatch), 'hatches')
