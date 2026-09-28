# The story in N-body time (Myr): the two galaxies from galaxies.py; the black holes' pairing
# below the N-body's resolution, by dynamical friction in the fitted remnant (nucleus.py); the
# binary's hardening and gravitational-wave inspiral to merger (waves.py); and when the holes
# shine as AGN. render.py films it.
import os
import numpy as np
from scipy.spatial.transform import Rotation
import waves, nucleus

KPC_MYR = 207.4 * 1.0227e-3                     # N-body velocity unit in kpc/Myr
PC_M = 3.0857e16
M1, M2 = waves.M1, waves.M2
F1, F2 = M2 / (M1 + M2), M1 / (M1 + M2)         # distance of each hole from the centre of mass, / separation
VIEW = dict(tilt=48.0, turn=-20.0)              # the camera: tilt from the orbital axis, turn about it (deg)

def smooth(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def glerp(a, b, u): return np.exp(lerp(np.log(a), np.log(b), u))

class NBody:
    def __init__(self, d):
        import json
        meta = json.load(open(f'{d}/meta.json'))
        self.n = meta['n']
        tag = np.load(f'{d}/tag.npy'); self.m = np.load(f'{d}/mass.npy') * 1e10
        raw = np.memmap(f'{d}/stars.f32', dtype=np.float32, mode='r')
        ns = min(raw.size // (self.n * 3), len(meta['snaps']))
        self.X = raw[:ns * self.n * 3].reshape(ns, self.n, 3)
        s = meta['snaps'][:ns]
        self.t = np.array([q['t'] for q in s]) * 4.715
        self.bh = np.array([q['bh'] for q in s])
        self.vbh = np.array([q['vbh'] for q in s]) * KPC_MYR
        self.star = np.where((tag % 4 == 1) | (tag % 4 == 2))[0]

    def stars(self, t):
        # Catmull-Rom through the four snapshots around t (kpc).
        i = int(np.clip(np.searchsorted(self.t, t) - 1, 0, len(self.t) - 2))
        u = float(np.clip((t - self.t[i]) / (self.t[i + 1] - self.t[i]), 0, 1))
        idx = [max(i - 1, 0), i, i + 1, min(i + 2, len(self.t) - 1)]
        P = [np.asarray(self.X[k][self.star], dtype=np.float64) for k in idx]
        if u < 1e-6: return P[1]
        c = [(-u ** 3 + 2 * u ** 2 - u) / 2, (3 * u ** 3 - 5 * u ** 2 + 2) / 2, (-3 * u ** 3 + 4 * u ** 2 + u) / 2, (u ** 3 - u ** 2) / 2]
        return c[0] * P[0] + c[1] * P[1] + c[2] * P[2] + c[3] * P[3]

    def holes(self, t):
        # Cubic Hermite with the saved velocities (kpc).
        i = int(np.clip(np.searchsorted(self.t, t) - 1, 0, len(self.t) - 2))
        h = self.t[i + 1] - self.t[i]; u = float(np.clip((t - self.t[i]) / h, 0, 1))
        p0, p1, v0, v1 = self.bh[i], self.bh[i + 1], self.vbh[i] * h, self.vbh[i + 1] * h
        return (2 * u ** 3 - 3 * u ** 2 + 1) * p0 + (u ** 3 - 2 * u ** 2 + u) * v0 + (-2 * u ** 3 + 3 * u ** 2) * p1 + (u ** 3 - u ** 2) * v1

def shrink_centre(X, c, r=3.0):
    # Centre of the densest stars by shrinking spheres (kpc).
    while r > 0.15:
        m = np.linalg.norm(X - c, axis=1) < r
        c = X[m].mean(0); r *= 0.85
    return c

class Story:
    def __init__(self, cache):
        self.nb = nb = NBody(f'{cache}/nbody')
        sep = np.linalg.norm(nb.bh[:, 0] - nb.bh[:, 1], axis=1)
        com = (M1 * nb.bh[:, 0] + M2 * nb.bh[:, 1]) / (M1 + M2)
        k = np.exp(-0.5 * (np.arange(-6, 7) / 2.5) ** 2); k /= k.sum()
        self.com = np.stack([np.convolve(np.pad(com[:, j], 6, mode='edge'), k, 'valid') for j in range(3)], 1)
        # Pericentres of the galaxies: local minima of the black-hole separation inside 25 kpc.
        ss = np.convolve(np.pad(sep, 3, mode='edge'), np.ones(7) / 7, 'valid')
        peri = [nb.t[i] for i in range(1, len(ss) - 1) if ss[i] < ss[i - 1] and ss[i] <= ss[i + 1] and ss[i] < 25]
        peri = [p for j, p in enumerate(peri) if j == 0 or p - peri[j - 1] > 60]
        self.p1, self.p2 = peri[0], peri[1]
        # Hand-off: the pair is inside 0.7 kpc and stays within 1.4 kpc for the next 25 Myr.
        ih = next(i for i in range(len(sep)) if sep[i] < 0.7 and np.searchsorted(nb.t, nb.t[i] + 25) < len(sep)
                  and sep[i:np.searchsorted(nb.t, nb.t[i] + 25)].max() < 1.4)
        self.ih, self.th = ih, nb.t[ih]
        # The pair's orbital plane from its angular momentum over the 40 Myr before hand-off.
        i0 = np.searchsorted(nb.t, self.th - 40)
        L = np.cross(nb.bh[i0:ih + 1, 1] - nb.bh[i0:ih + 1, 0], nb.vbh[i0:ih + 1, 1] - nb.vbh[i0:ih + 1, 0]).mean(0)
        e3 = L / np.linalg.norm(L)
        e1 = np.cross(e3, [0, 0, 1.0]) if abs(e3[2]) < 0.9 else np.cross(e3, [1.0, 0, 0]); e1 /= np.linalg.norm(e1)
        e2 = np.cross(e3, e1)
        # Pairing: dynamical friction on the secondary and its stripped cusp, in the remnant's
        # stellar profile fitted to the N-body, from the hand-off down to a few pc.
        Xs = np.asarray(nb.X[ih][nb.star], dtype=np.float64)
        fit = nucleus.fit_host(np.linalg.norm(Xs - self.com[ih], axis=1) * 1e3, nb.m[nb.star])
        host = nucleus.Host(fit['M'], fit['a'])
        rel = (nb.bh[ih, 1] - nb.bh[ih, 0]) * 1e3
        vrel = (nb.vbh[ih, 1] - nb.vbh[ih, 0]) / 1.0227e-3
        rel = np.dot(rel, e1) * e1 + np.dot(rel, e2) * e2
        vrel = np.dot(vrel, e1) * e1 + np.dot(vrel, e2) * e2
        a_hard = waves.radii()['a_hard'] / PC_M
        tp, yp, _ = nucleus.pairing(host, rel, vrel, r_end=a_hard)
        self.pair_t, self.pair_rel = tp, yp[:, :3] / 1e3                   # Myr since hand-off, kpc
        # Then the binary hardens in this remnant (stellar density at the influence radius from the
        # fit) and gravitational waves take over: the merger time.
        waves.RHO = host.rho(waves.radii()['r_infl'] / PC_M) * waves.MSUN / PC_M ** 3
        t_h, _ = waves.hardening(waves.radii()['a_hard'])
        self.t_merge = self.th + tp[-1] + t_h[-1] / waves.MYR
        # The merged nucleus keeps sloshing after hand-off: follow its stellar centre (cached).
        path = f'{cache}/nbody/centre.npy'
        cs = np.load(path) if os.path.exists(path) else None
        if cs is None or len(cs) != len(nb.t) - ih:
            cs = np.array([shrink_centre(np.asarray(nb.X[i][nb.star], dtype=np.float64), self.com[ih].copy()) for i in range(ih, len(nb.t))])
            np.save(path, cs)
        self.drift = (nb.t[ih:], cs - cs[0])

    def view(self):
        return Rotation.from_euler('zx', [VIEW['turn'], VIEW['tilt']], degrees=True).inv()

    def centre(self, t):
        # Before hand-off the pair's centre of mass; after, the pair rides with its nucleus (kpc).
        if t <= self.th:
            return np.array([np.interp(t, self.nb.t, self.com[:, j]) for j in range(3)])
        tt, d = self.drift
        return self.com[self.ih] + np.array([np.interp(t, tt, d[:, j]) for j in range(3)])

    def holes(self, t):
        # World positions of the two holes (kpc): the N-body's, then the pairing orbit, which ends a
        # few pc apart (a point, from this far away).
        if t <= self.th: return self.nb.holes(t)
        rel = np.array([np.interp(t - self.th, self.pair_t, self.pair_rel[:, j]) for j in range(3)])
        c = self.centre(t)
        pos = np.stack([c - F1 * rel, c + F2 * rel])
        u = smooth((t - self.th) / 5.0)                                   # blend in over 5 Myr
        return lerp(self.nb.holes(min(t, self.nb.t[-1])), pos, u) if u < 1 else pos

    def agn(self, t):
        # Both holes switch on from the second approach, as gas driven in by the merger reaches them
        # (the dual AGN), stay on through the binary, fade as gravitational waves take over (the gas
        # disc can no longer follow), and the remnant lights up again after the merger.
        on = smooth((t - self.p2 + 30) / 60)
        off = smooth((t - self.t_merge + 30) / 25)
        again = smooth((t - self.t_merge - 8) / 20)
        return float(max(on * (1 - off), 0.6 * again))
