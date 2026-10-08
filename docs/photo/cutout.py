# The portrait without its sky: the rooftops, the tower and the hair become the top edge and
# meet the page directly; the left and right edges fade into the paper, and the bottom stays a
# straight edge that docs/photo/meadow.py draws the sage on from. Black and white as
# before (darkest tone the ink colour, lightest the paper).
# Usage: python3 docs/photo/cutout.py _archive/photos/portrait-original.jpg public/photos
import sys, numpy as np
from PIL import Image, ImageFilter
from collections import deque
src, out = sys.argv[1], sys.argv[2]
INK = 25 / 255
im = Image.open(src).convert('RGB')
x0, y0, w = 330, 96, 1560; h = int(w * 2 / 3)
c = im.crop((x0, y0, x0 + w, y0 + h))
a = np.asarray(c, dtype=np.float32) / 255

# --- black and white, as before
L = 0.33 * a[..., 0] + 0.56 * a[..., 1] + 0.11 * a[..., 2]
lo, hi = np.percentile(L, 0.4), np.percentile(L, 99.9)
L = np.clip((L - lo) / (hi - lo), 0, 1) ** 1.12
L = np.clip(L - 0.06 * np.sin(2 * np.pi * L), 0, 1)
rng = np.random.default_rng(7)
g = rng.normal(0, 1, L.shape).astype(np.float32)
g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.55)), dtype=np.float32) / 255 - 0.5
L = np.clip(L + g * 0.045 * (1 - np.abs(2 * L - 1) ** 2), 0, 1)
bw = INK + (1 - INK) * L

# --- the sky: bright, cool, and connected to the top edge
mn = a.min(axis=2)                       # the darkest channel: high only for near-white
cool = a[..., 2] - a[..., 0]             # blue minus red: the sky is not warm like the stone
skyish = (mn > 0.80) & (cool > -0.02)
H, W = skyish.shape
seen = np.zeros_like(skyish)
q = deque((0, x) for x in range(W) if skyish[0, x])
for _, x in list(q): seen[0, x] = True
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and skyish[ny, nx]:
            seen[ny, nx] = True; q.append((ny, nx))
sky = Image.fromarray((seen * 255).astype(np.uint8))
# a soft edge: near the sky, opacity follows how far a pixel is from sky-white
near = np.asarray(sky.filter(ImageFilter.MaxFilter(9)), dtype=np.float32) / 255 > 0.5
soft = np.clip((0.90 - mn) / (0.90 - 0.70), 0, 1)          # 0 at near-white, 1 when clearly darker
soft = np.maximum(soft, np.clip(-cool / 0.08, 0, 1) * (mn < 0.93))  # warm (stone, hair) stays
alpha = np.where(seen, 0.0, np.where(near, soft, 1.0))
alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255
alpha[seen] = 0

# --- the sides fade into the paper
xs = np.linspace(0, 1, W)
ramp = np.clip(xs / 0.06, 0, 1) * np.clip((1 - xs) / 0.06, 0, 1)
ramp = ramp * ramp * (3 - 2 * ramp)
alpha = alpha * ramp[None, :]

outL = bw * alpha + 1.0 * (1 - alpha)
img = Image.fromarray((outL * 255).round().astype(np.uint8), 'L')
for width, name in ((1500, 'portrait.jpg'), (900, 'portrait-900.jpg')):
    r = img.resize((width, width * 2 // 3), Image.LANCZOS)
    r.save(f'{out}/{name}', quality=90, optimize=True, progressive=True, subsampling=0)
print('ok', img.size)
