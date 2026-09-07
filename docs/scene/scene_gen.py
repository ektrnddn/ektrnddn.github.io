# Writes scene.html: Mount Kazbek seen from Stepantsminda, traced from a photograph
# (kazbek-trace.json holds the per-column skyline, snow-cap bottom and foothill rows),
# with the Gergeti Trinity church on its hill, a meadow and a small walking figure.
import json, math, sys
import numpy as np
from scipy.ndimage import median_filter, gaussian_filter1d
S = sys.argv[1]
T = json.load(open(f"{S}/kazbek-trace.json"))
W, H = T["W"], T["H"]
VH, MEADOW = 660, 598
sc = 0.9 * 1440 / W                 # photo → frame, uniform, 90% of the width
xoff = (1440 - W * sc) / 2
sky0 = T["skyline"]
cx0 = min(range(150, 230), key=lambda i: sky0[i])
yoff = 315 - sky0[cx0] * sc         # the church hill top lands at y = 315
X = lambda x: x * sc + xoff
Y = lambda y: y * sc + yoff

def rdp(pts, eps):
    if len(pts) < 3: return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy) or 1
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x1 * y0 - y1 * x0) / L
        if d > dmax: dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

sky = np.array(T["skyline"], float)
skyline = rdp([(X(x), Y(sky[x])) for x in range(0, W, 2)], 1.1)
skyline = [(0, skyline[0][1] + 6)] + skyline + [(1440, skyline[-1][1] + 4)]
sky_d = 'M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in skyline)
sky_fill = sky_d + f' L1440 {VH} L0 {VH} Z'

# Snow cap: smoothed bottom of the contiguous snow, main cap only
sb = np.array(T["snowbot"], float)
cap = np.arange(W)[(sb > 0) & (np.arange(W) > 560) & (np.arange(W) < 1360)]
sbs = median_filter(np.interp(np.arange(W), cap, sb[cap]), size=61)
snow_pts = [(X(x), max(Y(sbs[x]), Y(sky[x]) + 6)) for x in range(int(cap.min()), int(cap.max()), 3)]
snow_pts = rdp(snow_pts, 1.5)
snow_d = 'M' + ' '.join((f'{x:.0f} {y:.0f}' if i == 0 else f'Q{x - 4:.0f} {y - 5:.0f} {x:.0f} {y:.0f}') for i, (x, y) in enumerate(snow_pts))

# Rock lines: couloirs fanning down from the summit region to the snow line
summit_x = int(np.argmin(sky))
rock = []
for dx in (-150, -95, -45, 35, 80, 130):
    xs = summit_x + dx
    if not (0 < xs < W): continue
    x0, y0 = X(xs), Y(sky[xs]) + 8
    x1, y1 = X(xs + dx * 0.55), Y(sbs[min(W - 1, max(0, int(xs + dx * 0.55)))]) - 4
    y1 = min(y1, y0 + 80)
    if y1 > y0 + 20: rock.append(f'M{x0:.0f} {y0:.0f} Q{(x0 + x1) / 2 + (6 if dx < 0 else -6):.0f} {(y0 + y1) / 2:.0f} {x1:.0f} {y1:.0f}')
# Snow hatches: short strokes just under the snow line
hatch = []
for i, (x, y) in enumerate(snow_pts):
    if i % 3 == 1: hatch.append(f'M{x:.0f} {y + 4:.0f} l7 4 M{x + 9:.0f} {y + 9:.0f} l6 4')

# Foothill: the forested hill in front. Heavily smoothed; left of the hill it follows the
# skyline so the church hill stays part of the range layer.
hill = np.array(T["hill"], float)
hs = gaussian_filter1d(median_filter(hill, size=61), 22)
xs = np.arange(W)
# blend from the skyline into the hill over 140 columns, and flatten the village bumps on the right
w = np.clip((xs - 560) / 140, 0, 1)
hs = (sky + 3) * (1 - w) + hs * w
hs = np.maximum(hs, sky + 3)
hs = np.where(xs > 1240, np.minimum(hs, np.interp(xs, [1240, W - 1], [hs[1240], hs[1240] + 40])), hs)
hs = np.minimum(hs, (MEADOW - yoff) / sc - 6)
hill_pts = rdp([(X(x), Y(hs[x])) for x in range(0, W, 2)], 1.4)
hill_d = 'M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in hill_pts)
hill_pts = hill_pts + [(1440, hill_pts[-1][1] + 2)]
hill_d = 'M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in hill_pts)
hill_fill = hill_d + f' L1440 {VH} L0 {VH} Z'
trees = ' '.join(f'M{x:.0f} {y:.0f} l3 -7 3 7' for x, y in hill_pts[::9] if 40 < x < 1400 and y < 470)

# Gergeti Trinity on its hill: the traced bump between photo columns 150–230
cx = 150 + int(np.argmin(sky[150:230]))
church_x, church_y = X(cx), Y(sky[cx]) + 2

svg = f'''<svg viewBox="0 0 1440 660" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <g class="range">
    <path class="f" d="{sky_fill}"/>
    <path class="s" d="{sky_d}"/>
    <path class="h" d="{' '.join(rock)}"/>
    <path class="snowline" d="{snow_d}"/>
    <path class="snow" d="{' '.join(hatch)}"/>
    <g class="church" transform="translate({church_x:.0f} {church_y:.0f}) scale(1.35)">
      <path d="M-9 0 v-9 h18 v9 z M-4 -9 v-5 h8 v5 z M-4 -14 a4 4 0 0 1 8 0 z M-0.6 -18 v-5 h1.2 v5 z M-2.2 -21.5 h4.4 v1 h-4.4 z M10 0 v-14 h4 v14 z M10 -14 l2 -3 2 3 z"/>
    </g>
  </g>
  <g class="foothill">
    <path class="f" d="{hill_fill}"/>
    <path class="s" d="{hill_d}"/>
    <path class="trees" d="{trees}"/>
  </g>
  <g class="meadow">
    <path class="f" d="M0 598 C 240 590, 480 606, 720 596 S 1120 588, 1440 598 L1440 660 L0 660 Z"/>
    <path class="s" d="M0 598 C 240 590, 480 606, 720 596 S 1120 588, 1440 598"/>
    <path class="grass" d="M96 596 l-2 -11 M118 594 l3 -9 M300 600 l-1 -10 M330 601 l4 -8 M760 594 l-3 -11 M790 593 l2 -8 M902 590 l-2 -10 M930 589 l3 -9 M1180 592 l-2 -11 M1204 592 l3 -8 M1340 596 l-2 -10"/>
    <g class="flowers">
      <path class="stem" d="M212 594 v-15 M405 599 v-12 M700 594 v-16 M818 590 v-13 M1048 586 v-15 M1275 592 v-12"/>
      <circle cx="212" cy="577" r="2.5"/><circle cx="405" cy="585" r="2.1"/><circle cx="700" cy="576" r="2.7"/><circle cx="818" cy="575" r="2.2"/><circle cx="1048" cy="569" r="2.5"/><circle cx="1275" cy="578" r="2.1"/>
    </g>
    <g class="figure" transform="translate(600 597) scale(0.9)">
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
.range .s{stroke:#3a3a3a;stroke-width:1.3}.range .h{stroke:#8a8a8a}.snow{fill:none;stroke:#6a6a6a;stroke-width:.9;opacity:.85}.snowline{fill:none;stroke:#bdbdbd;stroke-width:.9;opacity:.9}
.foothill .s{stroke:#5a5a5a;stroke-width:1.1}.foothill .trees{fill:none;stroke:#5a5a5a;stroke-width:1;opacity:.8}
.meadow .s{stroke:#191919;stroke-width:1.4}.grass{fill:none;stroke:#191919;stroke-width:1;opacity:.7}.flowers .stem{fill:none;stroke:#191919;stroke-width:1;opacity:.6}.flowers circle{fill:#d98aa0}
.figure .ink{fill:#191919;stroke:#191919;stroke-width:1;stroke-linejoin:round}.figure .limb{fill:none;stroke:#191919;stroke-width:5;stroke-linecap:round}.figure .leg{fill:none;stroke:#191919;stroke-width:4.5;stroke-linecap:round}
.church{fill:#2a2a2a;stroke:none}
</style></head><body>''' + svg + '</body></html>'
open(f'{S}/scene.html', 'w').write(html)
# 48 skyline samples (fraction of box height, y from box top) for the star field
samples = [round(min(Y(sky[min(W - 1, max(0, int((i * 1440 / 47 - xoff) / sc)))]), MEADOW) / VH, 3) for i in range(48)]
json.dump(samples, open(f'{S}/skyline-samples.json', 'w'))
print('scene.html written;', len(skyline), 'skyline pts,', len(hill_pts), 'hill pts,', len(snow_pts), 'snow pts; church at', round(church_x), round(church_y))
