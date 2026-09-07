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
range_pts = skyline(380, 1440, 336, [(860, 118, 250), (1130, 48, 130), (600, 30, 120)], 3, spires)
farfar = skyline(940, 1440, 292, [(1150, 42, 160), (1330, 26, 90)], 11, [(1120, 22, 12), (1230, 16, 10), (1330, 20, 11)], step=14, jitter=1)

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
snow_pts = [(x, y) for x, y in snowline(range_pts, 34) if 620 <= x <= 1250]
snow_d = 'M' + ' '.join((f'{x} {y:.0f}' if i == 0 else f'Q{x - 5} {y - 6:.0f} {x} {y:.0f}') for i, (x, y) in enumerate(snow_pts))

# Foothill in front of the range: rounded, forested
foothill = 'M300 470 C 420 452, 520 444, 640 452 S 860 474, 980 462 S 1200 430, 1320 438 S 1400 446, 1440 442'
trees_fh = ' '.join(f'M{x} {y} l3 -7 3 7' for x, y in [(360,458),(410,455),(560,447),(700,455),(760,462),(900,468),(1000,461),(1080,449),(1160,440),(1250,436),(1360,440)])

svg = f'''<svg viewBox="0 -20 1440 660" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <g class="farfar">
    <path class="f" d="{closed(farfar, 980, 1440)}"/>
    <path class="s" d="{poly(farfar)}"/>
  </g>
  <g class="range">
    <path class="f" d="{closed(range_pts, 380, 1440)}"/>
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
    <g class="church" transform="translate(236 418)">
      <path d="M-9 0 v-9 h18 v9 z M-4 -9 v-5 h8 v5 z M-4 -14 a4 4 0 0 1 8 0 z M-0.6 -18 v-5 h1.2 v5 z M-2.2 -21.5 h4.4 v1 h-4.4 z M10 0 v-14 h4 v14 z M10 -14 l2 -3 2 3 z"/>
    </g>
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
    <g class="sketch-figure" transform="translate(568 452) scale(0.255)" fill="none" stroke="#191919" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M92 78 C 88 100, 90 128, 108 138 C 118 143, 124 143, 134 138 C 150 128, 152 100, 148 78" />
  <path d="M100 72 C 104 62, 138 62, 142 72" stroke-opacity=".5"/>
  <ellipse cx="108" cy="100" rx="8" ry="9.5"/><ellipse cx="134" cy="100" rx="8" ry="9.5"/>
  <circle cx="110" cy="102" r="4" fill="#191919"/><circle cx="136" cy="102" r="4" fill="#191919"/>
  <path d="M99 92 l-4 -4 M102 89 l-2 -5 M143 92 l4 -4 M140 89 l2 -5"/>
  <path d="M122 110 l-2 5 4 1"/>
  <path d="M110 122 Q121 132 134 122"/>
  <path d="M66.9 116.2 a7.4 6.3 0 1 1 14.7 0 a7.4 6.3 0 1 1 -14.7 0 M62.2 105.3 a7.5 6.4 0 1 1 15.0 0 a7.5 6.4 0 1 1 -15.0 0 M61.2 93.4 a6.2 5.2 0 1 1 12.3 0 a6.2 5.2 0 1 1 -12.3 0 M65.0 82.4 a8.1 6.9 0 1 1 16.2 0 a8.1 6.9 0 1 1 -16.2 0 M70.1 71.3 a6.6 5.6 0 1 1 13.2 0 a6.6 5.6 0 1 1 -13.2 0 M74.0 59.1 a7.2 6.1 0 1 1 14.4 0 a7.2 6.1 0 1 1 -14.4 0 M85.0 52.0 a7.2 6.1 0 1 1 14.4 0 a7.2 6.1 0 1 1 -14.4 0 M98.2 48.0 a6.4 5.4 0 1 1 12.8 0 a6.4 5.4 0 1 1 -12.8 0 M109.1 45.9 a8.2 6.9 0 1 1 16.3 0 a8.2 6.9 0 1 1 -16.3 0 M122.1 47.4 a7.9 6.7 0 1 1 15.7 0 a7.9 6.7 0 1 1 -15.7 0 M136.3 50.3 a6.2 5.2 0 1 1 12.3 0 a6.2 5.2 0 1 1 -12.3 0 M146.2 56.5 a7.5 6.4 0 1 1 15.0 0 a7.5 6.4 0 1 1 -15.0 0 M154.5 67.0 a6.1 5.2 0 1 1 12.2 0 a6.1 5.2 0 1 1 -12.2 0 M162.7 75.9 a7.2 6.1 0 1 1 14.4 0 a7.2 6.1 0 1 1 -14.4 0 M164.5 88.1 a8.2 7.0 0 1 1 16.4 0 a8.2 7.0 0 1 1 -16.4 0 M164.8 100.4 a8.3 7.1 0 1 1 16.6 0 a8.3 7.1 0 1 1 -16.6 0 M160.6 111.9 a8.0 6.8 0 1 1 16.0 0 a8.0 6.8 0 1 1 -16.0 0 M57.0 110.0 a8.4 7.1 0 1 1 16.7 0 a8.4 7.1 0 1 1 -16.7 0 M56.0 122.0 a6.7 5.7 0 1 1 13.4 0 a6.7 5.7 0 1 1 -13.4 0 M60.3 134.0 a6.9 5.9 0 1 1 13.9 0 a6.9 5.9 0 1 1 -13.9 0 M54.8 146.0 a7.4 6.3 0 1 1 14.7 0 a7.4 6.3 0 1 1 -14.7 0 M57.1 158.0 a7.1 6.0 0 1 1 14.2 0 a7.1 6.0 0 1 1 -14.2 0 M69.0 158.0 a7.0 6.0 0 1 1 14.0 0 a7.0 6.0 0 1 1 -14.0 0 M167.8 110.0 a7.3 6.2 0 1 1 14.5 0 a7.3 6.2 0 1 1 -14.5 0 M166.4 122.0 a7.7 6.5 0 1 1 15.3 0 a7.7 6.5 0 1 1 -15.3 0 M167.2 134.0 a8.3 7.1 0 1 1 16.6 0 a8.3 7.1 0 1 1 -16.6 0 M167.7 146.0 a8.4 7.1 0 1 1 16.7 0 a8.4 7.1 0 1 1 -16.7 0 M168.7 158.0 a8.5 7.2 0 1 1 17.0 0 a8.5 7.2 0 1 1 -17.0 0 M157.0 158.0 a7.0 6.0 0 1 1 14.0 0 a7.0 6.0 0 1 1 -14.0 0 M89.5 58.7 a6.5 5.5 0 1 1 13.0 0 a6.5 5.5 0 1 1 -13.0 0 M103.5 56.7 a6.5 5.5 0 1 1 13.0 0 a6.5 5.5 0 1 1 -13.0 0 M117.5 59.4 a6.5 5.5 0 1 1 13.0 0 a6.5 5.5 0 1 1 -13.0 0 M131.5 59.9 a6.5 5.5 0 1 1 13.0 0 a6.5 5.5 0 1 1 -13.0 0" stroke-width="1.5"/>
  <path d="M110 140 v10 M132 140 v10 M100 154 Q121 160 142 154"/>
  <path d="M90 158 L86 262 M152 158 L156 262"/>
  <path d="M98 162 v56 M144 162 v56" stroke-width="3.2"/>
  <path d="M98 218 H144 M98 232 H144 M104 218 v-40 M138 218 v-40"/>
  <path d="M116 158 C 114 175, 118 190, 114 210 M126 158 C 128 175, 124 190, 128 210"/>
  <circle cx="114" cy="211" r="2.2" fill="#191919"/><circle cx="128" cy="211" r="2.2" fill="#191919"/>
  <path d="M90 160 C 78 180, 76 220, 74 252 C 73 262, 82 264, 86 258 M152 160 C 164 180, 166 220, 168 252 C 169 262, 160 264, 156 258"/>
  <path d="M84 176 C 80 200, 80 230, 80 250" stroke-opacity=".45"/>
  <path d="M86 262 C 84 300, 88 340, 96 370 M156 262 C 158 300, 154 340, 146 370 M121 262 L118 370 M96 370 h20 M126 370 h20"/>
  <path d="M90 292 h18 v22 h-18 z M132 292 h18 v22 h-18 z" stroke-width="1.4"/>
  <path d="M96 370 v10 M116 370 v10 M126 370 v10 M146 370 v10 M98 375 h16 M128 375 h16"/>
  <path d="M94 380 C 88 384, 84 392, 90 398 C 100 402, 114 402, 118 396 C 120 390, 118 384, 116 380"/>
  <path d="M124 380 C 122 384, 120 392, 126 398 C 136 402, 150 402, 154 396 C 156 390, 152 384, 148 380"/>
  <path d="M96 386 h18 M98 391 h16 M128 386 h18 M130 391 h16" stroke-width="1.2"/>
  <circle cx="60" cy="262" r="11"/><circle cx="72" cy="272" r="10"/><circle cx="56" cy="282" r="9"/>
  <path d="M50 290 L 66 300 L 70 336 Z"/>
  <path d="M54 300 l12 8 M52 308 l14 10 M56 320 l10 8" stroke-width="1.2"/>
  <path d="M232 296 l-8 -22 14 8 M266 296 l8 -22 -14 8"/>
  <path d="M226 304 C 222 320, 232 334, 248 334 C 264 334, 274 320, 270 304 C 266 288, 232 288, 226 304 Z"/>
  <path d="M238 310 l8 2 M258 312 l8 -2 M244 322 l4 2 4 -2" />
  <path d="M236 318 l-18 -4 M236 322 l-20 2 M236 326 l-16 6 M260 318 l18 -4 M260 322 l20 2 M260 326 l16 6" stroke-width="1.2"/>
  <path d="M234 334 C 226 350, 226 372, 230 396 M262 334 C 270 350, 270 372, 266 396 M230 396 h10 M256 396 h10 M240 396 v-40 M256 396 v-40" />
  <path d="M270 340 C 296 330, 300 290, 290 270 C 286 262, 278 266, 282 274 C 286 282, 296 278, 292 268" />
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
