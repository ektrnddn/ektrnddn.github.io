# Films the merger from far away, in one take and without words, and encodes it for the web.
#   python3 render.py CACHE OUT [--stills 3,12.5,20] [--jobs 6] [--exposure] [--resume]
# CACHE holds galaxies.py's run in nbody/ (and gets the caches: exposure.json, frames).
# Ink on paper: the stars of the N-body run; the only colour is the rose of the accreting black
# holes (a dual AGN, then one unresolved point); grey rings leave the remnant at the merger.
import os, json, argparse, subprocess, time, re
import numpy as np
import numba
import skia
from scipy.spatial import cKDTree
from scipy.interpolate import PchipInterpolator
from scipy.spatial.transform import Rotation
from story import Story, smooth, F1, F2

W = H = 1080
FPS = 30
PAPER, INK, ROSE = (255, 255, 255), (0x19, 0x19, 0x19), (0xd9, 0x8a, 0xa0)
END, FADE, POSTER = 30.0, 0.8, 13.6
# Film time (s) against N-body time (Myr), pinned to the story: first and second pericentres (p1,
# p2), hand-off of the pair to the pairing model (h) and the black holes' merger (m). Between h and m
# the binary hardens for ~0.4 Gyr, which the film crosses in a few seconds while the remnant settles.
TIME_KEYS = [(0.0, '0'), (3.0, 'p1-110'), (6.0, 'p1+20'), (11.0, 'p2-20'), (15.0, 'h-10'), (17.5, 'h+30'),
             (23.0, 'm-8'), (24.0, 'm'), (30.0, 'm+55')]
FOV_KEYS = [(0.0, 130.0), (6.0, 112.0), (11.0, 104.0), (15.0, 48.0), (17.5, 36.0), (22.0, 34.0), (24.0, 38.0), (30.0, 70.0)]   # kpc
YAW_KEYS = [(0.0, 0.0), (17.5, 0.0), (30.0, 32.0)]                                                          # degrees
MERGE = 24.0                                    # when the burst leaves the remnant
# The burst: the last cycles come closer together (the chirp) and the strongest is at the merger.
RINGS = [(0.00, 0.35), (0.30, 0.55), (0.52, 0.8), (0.68, 1.0), (0.80, 0.55), (0.90, 0.25)]
SHUTTER = 4.0                                   # px: how far a typical star moves between sub-frames

# ---------------------------------------------------------------- drawing primitives

@numba.njit(fastmath=True)
def splat(img, x, y, s, w, lo, hi):
    Hh, Ww = img.shape
    for j in range(lo, hi):
        sj = s[j]; r = int(3 * sj + 1)
        cx, cy = x[j], y[j]
        ix, iy = int(cx), int(cy)
        inv = 0.5 / (sj * sj)
        tot = 0.0
        for yy in range(iy - r, iy + r + 1):
            dy = yy + 0.5 - cy
            for xx in range(ix - r, ix + r + 1):
                dx = xx + 0.5 - cx
                tot += np.exp(-(dx * dx + dy * dy) * inv)
        if tot <= 0: continue
        f = w[j] / tot
        for yy in range(max(iy - r, 0), min(iy + r + 1, Hh)):
            dy = yy + 0.5 - cy
            for xx in range(max(ix - r, 0), min(ix + r + 1, Ww)):
                dx = xx + 0.5 - cx
                img[yy, xx] += f * np.exp(-(dx * dx + dy * dy) * inv)

@numba.njit(parallel=True)
def splat_all(x, y, s, w, Hh, Ww, nchunk):
    out = np.zeros((nchunk, Hh, Ww))
    n = x.size
    for c in numba.prange(nchunk):
        splat(out[c], x, y, s, w, c * n // nchunk, (c + 1) * n // nchunk)
    return out.sum(axis=0)

def smoothing(xy, k=10, smin=0.7, smax=4.0):
    # Kernel size of each point (px) from the distance to its k-th neighbour.
    d, _ = cKDTree(xy).query(xy, k=min(k, len(xy) - 1) + 1, workers=-1)
    return np.clip(0.55 * d[:, -1], smin, smax)

def density(xy, w, s, scale):
    # Surface density (Msun per pc^2) of weighted points in pixel coordinates.
    if len(w) == 0: return np.zeros((H, W))
    return splat_all(xy[:, 0].copy(), xy[:, 1].copy(), s, w.astype(np.float64), H, W, 8) * scale ** 2

def col(c, a=1.0): return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, a)

# The film fades into the paper at its borders, so it sits on the page without a frame.
_u = np.minimum(np.arange(W) + 0.5, W - np.arange(W) - 0.5) / (0.09 * W)
EDGE = np.outer(np.clip(_u, 0, 1) ** 1.5, np.clip(_u, 0, 1) ** 1.5)
EDGE = EDGE * EDGE * (3 - 2 * EDGE)

# ---------------------------------------------------------------- the film

class Film:
    def __init__(self, cache):
        self.st = st = Story(cache)
        ev = dict(p1=st.p1, p2=st.p2, h=st.th, m=st.t_merge)
        keys = np.array([(T, float(eval(e, {}, ev))) for T, e in TIME_KEYS])
        self.tN = PchipInterpolator(keys[:, 0], keys[:, 1])
        f = np.array(FOV_KEYS)
        self.lfov = PchipInterpolator(f[:, 0], np.log(f[:, 1]))
        self.exposure = None
        if os.path.exists(f'{cache}/exposure.json'): self.exposure = json.load(open(f'{cache}/exposure.json'))
        if keys[-1, 1] > st.nb.t[-1]:
            print(f'note: the N-body run ends at {st.nb.t[-1]:.0f} Myr; the film asks for {keys[-1, 1]:.0f}', flush=True)

    def t(self, T): return float(self.tN(np.clip(T, 0, END)))
    def fov(self, T): return float(np.exp(self.lfov(np.clip(T, 0, END)))) * 1e3               # pc
    def rotation(self, T):
        yaw = np.interp(T, *zip(*YAW_KEYS))
        return Rotation.from_euler('y', yaw, degrees=True) * self.st.view()

    def to_px(self, T, P):
        # World (kpc) -> pixels.
        q = (np.atleast_2d(P) - self.st.centre(self.t(T))) * 1e3 @ self.rotation(T).as_matrix().T
        s = W / self.fov(T)
        return np.stack([W / 2 + q[:, 0] * s, H / 2 - q[:, 1] * s], 1), q[:, 2], s

    def sigma(self, T):
        # Stellar surface density of the N-body stars (Msun/pc^2), exposed over a tent in time in as
        # many sub-frames as the stars' motion needs: a frame each side, up to two where a frame
        # spans more Myr than the run's snapshots are apart. The stars then blur along their orbits
        # instead of flickering from frame to frame.
        st = self.st
        pos = lambda T: self.to_px(T, st.nb.stars(min(self.t(T), st.nb.t[-1])))
        xy, _, scale = pos(T)
        m = (xy[:, 0] > -120) & (xy[:, 0] < W + 120) & (xy[:, 1] > -120) & (xy[:, 1] < H + 120)
        w = st.nb.m[st.nb.star][m]
        fov = self.fov(T)
        s = smoothing(xy[m], k=int(np.interp(np.log10(fov), [4.3, 5.0], [24, 10])), smax=float(np.interp(np.log10(fov), [4.3, 5.0], [6, 4])))
        span = float(np.clip(2.5 * (self.t(T + 1 / FPS) - self.t(T - 1 / FPS)) / 2 / (st.nb.t[1] - st.nb.t[0]), 1, 2))
        move = np.median(np.linalg.norm(pos(T + span / FPS)[0][m] - pos(T - span / FPS)[0][m], axis=1))
        n = int(np.clip(np.ceil(move / SHUTTER), 1, 24))
        if n == 1: return density(xy[m], w, s, scale)
        off = ((np.arange(n) + 0.5) / n * 2 - 1) * span                         # frames
        tent = (1 - np.abs(off) / span) / (1 - np.abs(off) / span).sum()
        out = np.zeros((H, W))
        for o, q in zip(off, tent):
            xo, _, so = pos(T + o / FPS)
            out += q * density(xo[m], w, s, so)
        return out

    def exposure_at(self, T, sig):
        # (peak, floor): the 99.6th percentile of the stars and the frame's diffuse level, smoothed in time.
        if self.exposure:
            e = self.exposure
            return float(np.exp(np.interp(T, e['T'], e['log']))), float(np.exp(np.interp(T, e['T'], e['floor'])))
        v = sig[sig > 0]
        return (float(np.percentile(v, 99.6)) if v.size else 1.0), float(np.percentile(sig, 40))

    def frame(self, T):
        sig = self.sigma(T)
        ref, floor = self.exposure_at(T, sig)
        D = float(np.clip(np.log10(ref / floor) + 0.2, 1.2, 3.3)) if floor > ref * 1e-4 else 3.3
        lo = ref * 10 ** -D
        sig = np.maximum(sig - 0.9 * floor, 0)
        v = np.clip(np.log(1 + sig / lo) / np.log(1 + (ref - 0.9 * floor) / lo), 0, 1)
        dark = 0.9 * v ** 1.25 * EDGE
        img = np.empty((H, W, 4), np.uint8)
        for j, (p, q) in enumerate(zip(PAPER, INK)):
            img[:, :, j] = np.clip(p + (q - p) * dark, 0, 255).astype(np.uint8)
        img[:, :, 3] = 255
        c = skia.Surface(img, colorType=skia.kRGBA_8888_ColorType).getCanvas()
        self.draw_burst(c, T)
        self.draw_holes(c, T)
        fade = float(min(smooth(T / FADE), smooth((END - T) / FADE)))
        if fade < 1: c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=col(PAPER, 1 - fade)))
        return img[:, :, :3]

    def draw_holes(self, c, T):
        # Accreting holes as points of rose light: two in the dual AGN, one once they are too close to
        # tell apart, none as the gravitational waves take over, one again after the merger.
        st = self.st
        t = self.t(T)
        a = st.agn(t)
        if a <= 0.01: return
        xy = self.to_px(T, st.holes(min(t, st.t_merge)))[0]
        paint = skia.Paint(AntiAlias=True, Color4f=col(ROSE))
        if t >= st.t_merge:
            p = xy[0] * F2 + xy[1] * F1
            c.drawCircle(float(p[0]), float(p[1]), 9.5 * np.sqrt(a), paint)
            return
        for p, r in zip(xy, (11.0, 9.5)):
            c.drawCircle(float(p[0]), float(p[1]), r * np.sqrt(a), paint)

    def draw_burst(self, c, T):
        # Gravitational waves leaving the remnant: a few wavefronts, drawn far larger than their real
        # wavelength (tens of AU for this pair) so they can be seen at the scale of the galaxy.
        if T < MERGE: return
        o = self.to_px(T, self.st.centre(self.t(T)))[0][0]
        for dt, amp in RINGS:
            age = T - MERGE - dt * 0.5
            if age <= 0: continue
            r = 240 * age
            alpha = 0.6 * amp * smooth(age / 0.15) * (1 - smooth((r - 160) / 460))
            if alpha > 0.01:
                c.drawCircle(float(o[0]), float(o[1]), float(r), skia.Paint(AntiAlias=True, StrokeWidth=1.5, Style=skia.Paint.kStroke_Style, Color4f=col(INK, alpha)))

# ---------------------------------------------------------------- driver

def work(args):
    cache, Ts, out = args
    numba.set_num_threads(2)
    f = Film(cache)
    from PIL import Image
    for T in Ts:
        Image.fromarray(f.frame(T)).save(f'{out}/{int(round(T * FPS)):05d}.png', compress_level=1)
    return len(Ts)

def exposure_work(args):
    cache, Ts = args
    numba.set_num_threads(2)
    f = Film(cache)
    out = []
    for T in Ts:
        sig = f.sigma(T)
        v = sig[sig > 0]
        out.append((float(T), float(np.log(np.percentile(v, 99.6))) if v.size else np.nan, float(np.log(max(np.percentile(sig, 40), 1e-9)))))
    return out

def exposures(cache, jobs):
    # First pass: the density scale of every third frame, smoothed in time so the exposure glides.
    import multiprocessing as mp
    Film(cache)                                         # builds the cached nucleus track once
    Tk = np.arange(0, END, 3 / FPS)
    with mp.get_context('spawn').Pool(jobs) as pool:
        res = sorted(sum(pool.map(exposure_work, [(cache, list(Tk[i::jobs])) for i in range(jobs)]), []))
    T = np.array([r[0] for r in res]); L = np.array([r[1] for r in res]); F = np.array([r[2] for r in res])
    k = np.exp(-0.5 * (np.arange(-8, 9) / 3.0) ** 2); k /= k.sum()
    sm = lambda a: np.convolve(np.pad(a, 8, mode='edge'), k, 'valid')
    json.dump(dict(T=T.tolist(), log=sm(L).tolist(), floor=sm(F).tolist()), open(f'{cache}/exposure.json', 'w'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cache'); ap.add_argument('out')
    ap.add_argument('--stills', default='')
    ap.add_argument('--jobs', type=int, default=5)
    ap.add_argument('--exposure', action='store_true')
    ap.add_argument('--resume', action='store_true', help='keep frames already rendered')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.exposure:
        exposures(a.cache, a.jobs); return
    if a.stills:
        f = Film(a.cache)
        for T in map(float, a.stills.split(',')):
            t0 = time.time()
            img = f.frame(T)
            skia.Image.fromarray(np.dstack([img, np.full(img.shape[:2], 255, np.uint8)])).save(f'{a.out}/still_{T:05.2f}.png', skia.kPNG)
            print(f'T = {T:5.2f}  t = {f.t(T):6.0f} Myr  fov = {f.fov(T) / 1e3:5.1f} kpc  agn = {f.st.agn(f.t(T)):.2f}  ({time.time() - t0:.1f} s)', flush=True)
        return
    Film(a.cache)
    Ts = np.arange(0, END, 1 / FPS)
    tmp = f'{a.cache}/frames-far'
    if not a.resume and os.path.isdir(tmp):
        import shutil; shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)
    todo = [T for T in Ts if not os.path.exists(f'{tmp}/{int(round(T * FPS)):05d}.png')]
    if todo:
        import multiprocessing as mp
        with mp.get_context('spawn').Pool(a.jobs) as pool:
            for n in pool.imap_unordered(work, [(a.cache, todo[i::a.jobs], tmp) for i in range(a.jobs)]): print('chunk done', n, flush=True)
    encode(tmp, len(Ts), a.out)

def encode(tmp, n, out):
    # The film as H.264 and VP9, a poster, and one clip per chapter (src/data/movie.yaml).
    import imageio_ffmpeg, yaml
    from PIL import Image
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = ['-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    def run(cmd, frames):
        p = subprocess.Popen([ff, '-y', '-loglevel', 'error', *raw, *cmd], stdin=subprocess.PIPE)
        for i in frames:
            p.stdin.write(np.asarray(Image.open(f'{tmp}/{i:05d}.png').convert('RGB')).tobytes())
        p.stdin.close(); p.wait()
        print('wrote', cmd[-1], f'{os.path.getsize(cmd[-1]) / 1e6:.1f} MB', flush=True)
    run(['-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{out}/merger.mp4'], range(n))
    run(['-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '37', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-pix_fmt', 'yuv420p', f'{out}/merger.webm'], range(n))
    Image.open(f'{tmp}/{int(round(POSTER * FPS)):05d}.png').convert('RGB').save(f'{out}/poster.jpg', quality=86, optimize=True)
    here = os.path.dirname(os.path.abspath(__file__))
    chapters = yaml.safe_load(open(os.path.join(here, '..', '..', 'src', 'data', 'movie.yaml')))['chapters']
    starts = [ch['at'] for ch in chapters] + [n / FPS]
    os.makedirs(f'{out}/clips', exist_ok=True)
    for i, ch in enumerate(chapters):
        slug = re.sub(r'[^a-z0-9]+', '-', ch['name'].lower()).strip('-')
        run(['-vf', 'scale=720:720:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{out}/clips/{slug}.mp4'],
            range(int(round(starts[i] * FPS)), min(n, int(round(starts[i + 1] * FPS)))))

if __name__ == '__main__':
    main()
