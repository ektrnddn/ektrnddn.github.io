# Self-consistent N-body merger of two disc galaxies: dark halo, exponential disc, bulge and
# a central black hole each, Hernquist (1993) style initial conditions, tree gravity.
# Units: G = 1, kpc, 1e10 Msun, 207.4 km/s, 4.715 Myr.
#   python3 galaxies.py CACHE_DIR [scale] [json overrides]   scale < 1: quick low-resolution test
import sys, os, time, json
import numpy as np
from scipy import special
from pytreegrav import Accel

KMS, MYR = 207.4, 4.715

# The pair: a 1e12 Msun halo with a 1e8 Msun black hole meets one half its mass (5e7 Msun
# black hole). Black holes sit near the Kormendy & Ho (2013) bulge relation.
GALAXIES = [
    dict(Mh=100.0, ah=30.0, Md=5.0, Rd=3.0, z0=0.30, Mb=1.5, ab=0.60, Mbh=0.010, spin=(25, 0)),
    dict(Mh=50.0, ah=24.0, Md=2.5, Rd=2.4, z0=0.24, Mb=0.75, ab=0.48, Mbh=0.005, spin=(60, 90)),
]
ORBIT = dict(r0=60.0, rp=4.0, e=0.85)   # point-mass orbit; the haloes' extent makes the real first pericentre ~10 kpc
M_STAR, M_DM = 2.5e-5, 5e-4              # particle masses: 2.5e5 and 5e6 Msun
H_STAR, H_DM, H_BH = 0.22, 0.40, 0.22    # spline softening radii (Plummer-equivalent / 2.8)
T_END, DT, T_SNAP = 265.0, 0.05, 0.5     # 1.25 Gyr, 0.24 Myr steps, a snapshot every 2.4 Myr

def rho_hern(r, M, a): return M * a / (2 * np.pi * r * (r + a) ** 3)
def m_hern(r, M, a): return M * r ** 2 / (r + a) ** 2
def m_disc(r, Md, Rd): return Md * (1 - (1 + r / Rd) * np.exp(-r / Rd))

def sample_hern(n, a, rmax, rng):
    s = np.sqrt(rng.random(n) * (rmax / (rmax + a)) ** 2)
    r = a * s / (1 - s)
    u = rng.normal(size=(n, 3)); u /= np.linalg.norm(u, axis=1)[:, None]
    return r, r[:, None] * u

def spherical_potential(g, rmax_h):
    # Psi(r) = -Phi(r) of the spherically averaged galaxy (disc counted as a sphere), on a log grid.
    r = np.logspace(-4, np.log10(rmax_h * 4), 4000)
    M = m_hern(np.minimum(r, rmax_h), g['Mh'], g['ah']) + m_hern(r, g['Mb'], g['ab']) + m_disc(r, g['Md'], g['Rd']) + g['Mbh']
    gr = M / r ** 2
    # Phi(r) = -M_tot/r_last - int_r^rlast g dr
    seg = 0.5 * (gr[1:] + gr[:-1]) * np.diff(r)
    tail = np.concatenate([np.cumsum(seg[::-1])[::-1], [0.0]])
    psi = M[-1] / r[-1] + tail
    return r, M, psi

def eddington(r, psi, rho):
    # Isotropic distribution function of one component in the total potential.
    lr, lpsi = np.log(r), psi
    drho = np.gradient(rho, lr) / np.gradient(lpsi, lr)          # d rho / d Psi as a function of r
    order = np.argsort(psi)
    P, D = psi[order], drho[order]
    E = np.geomspace(1e-3, P[-1], 3000)
    u = np.linspace(0, 1, 400)
    # F(E) = int_0^E drho/dPsi / sqrt(E - Psi) dPsi, with Psi = E (1 - u^2)
    F = np.array([np.trapz(2 * np.sqrt(e) * np.interp(e * (1 - u ** 2), P, D), u) for e in E])
    f = np.gradient(F, E) / (np.sqrt(8) * np.pi ** 2)
    return E, np.maximum(f, 0)

def sample_speeds(psi_p, E, f, rng):
    x = np.linspace(0, 1, 96)
    vesc = np.sqrt(2 * psi_p)
    Ep = psi_p[:, None] * (1 - x[None, :] ** 2)
    p = x[None, :] ** 2 * np.interp(Ep, E, f)
    c = np.cumsum(p, axis=1); c /= c[:, -1:]
    u = rng.random(len(psi_p))
    i = np.clip((c < u[:, None]).sum(axis=1), 1, len(x) - 1)
    c0, c1 = c[np.arange(len(u)), i - 1], c[np.arange(len(u)), i]
    xs = x[i - 1] + (x[i] - x[i - 1]) * np.clip((u - c0) / np.maximum(c1 - c0, 1e-12), 0, 1)
    v = xs * vesc
    d = rng.normal(size=(len(v), 3)); d /= np.linalg.norm(d, axis=1)[:, None]
    return v[:, None] * d

def disc_vc2(R, g):
    y = R / (2 * g['Rd'])
    S0 = g['Md'] / (2 * np.pi * g['Rd'] ** 2)
    disc = 4 * np.pi * S0 * g['Rd'] * y ** 2 * (special.i0(y) * special.k0(y) - special.i1(y) * special.k1(y))
    return disc + (m_hern(R, g['Mh'], g['ah']) + m_hern(R, g['Mb'], g['ab']) + g['Mbh']) / R

def make_galaxy(g, rng, scale):
    rmax_h = 10 * g['ah']
    r, M, psi = spherical_potential(g, rmax_h)
    nh = int(m_hern(rmax_h, g['Mh'], g['ah']) / (M_DM / scale))
    nb = int(g['Mb'] / (M_STAR / scale)); nd = int(g['Md'] / (M_STAR / scale))
    parts = []
    for kind, n, Mc, ac, rmax in (('halo', nh, g['Mh'], g['ah'], rmax_h), ('bulge', nb, g['Mb'], g['ab'], 30 * g['ab'])):
        rp, x = sample_hern(n, ac, rmax, rng)
        rho = rho_hern(r, Mc, ac)
        E, f = eddington(r, psi, rho)
        v = sample_speeds(np.interp(rp, r, psi), E, f, rng)
        parts.append((kind, x, v, np.full(n, (m_hern(rmax, Mc, ac) if kind == 'halo' else Mc * (rmax / (rmax + ac)) ** 2) / n)))
    # Disc: exponential in R, sech^2 in z; velocities from the epicyclic approximation.
    R = -g['Rd'] * np.log(rng.random(nd) * rng.random(nd))
    R = np.where(R > 8 * g['Rd'], rng.random(nd) * 8 * g['Rd'], R)
    z = g['z0'] * np.arctanh(2 * rng.random(nd) - 1)
    ph = rng.random(nd) * 2 * np.pi
    Rg = np.geomspace(1e-3, 12 * g['Rd'], 4000)
    vc2 = disc_vc2(Rg, g); Om2 = vc2 / Rg ** 2
    kap2 = np.maximum(Rg * np.gradient(Om2, Rg) + 4 * Om2, 0.05 * Om2)
    Sig = lambda x: g['Md'] / (2 * np.pi * g['Rd'] ** 2) * np.exp(-x / g['Rd'])
    Rref = 2.43 * g['Rd']
    sR_ref = 1.5 * 3.36 * Sig(Rref) / np.sqrt(np.interp(Rref, Rg, kap2))
    sR2 = sR_ref ** 2 * np.exp(-(R - Rref) / g['Rd'])
    sz2 = np.pi * Sig(R) * g['z0']
    k2, O2, v2 = np.interp(R, Rg, kap2), np.interp(R, Rg, Om2), np.interp(R, Rg, vc2)
    sp2 = sR2 * k2 / (4 * O2)
    vphi_mean = np.sqrt(np.maximum(v2 + sR2 * (1 - k2 / (4 * O2) - 2 * R / g['Rd']), 0))
    vR = rng.normal(size=nd) * np.sqrt(sR2)
    vz = rng.normal(size=nd) * np.sqrt(sz2)
    vp = vphi_mean + rng.normal(size=nd) * np.sqrt(sp2)
    xd = np.stack([R * np.cos(ph), R * np.sin(ph), z], 1)
    vd = np.stack([vR * np.cos(ph) - vp * np.sin(ph), vR * np.sin(ph) + vp * np.cos(ph), vz], 1)
    # Tilt the disc so its spin points along (theta, phi) in the orbital frame.
    th, pp = np.radians(g['spin'])
    Ry = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
    Rz = np.array([[np.cos(pp), -np.sin(pp), 0], [np.sin(pp), np.cos(pp), 0], [0, 0, 1]])
    Rot = Rz @ Ry
    parts.append(('disc', xd @ Rot.T, vd @ Rot.T, np.full(nd, g['Md'] / nd)))
    parts.append(('bh', np.zeros((1, 3)), np.zeros((1, 3)), np.array([g['Mbh']])))
    return parts

def main():
    global T_END
    out = sys.argv[1]; scale = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    if len(sys.argv) > 3:
        o = json.loads(sys.argv[3])
        ORBIT.update(o.get('orbit', {})); T_END = o.get('tend', T_END)
        for g, sp in zip(GALAXIES, o.get('spins', [])): g['spin'] = tuple(sp)
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(20260925)
    gals = [make_galaxy(g, rng, scale) for g in GALAXIES]
    Mt = [sum(p[3].sum() for p in parts) for parts in gals]
    # Keplerian orbit of two point masses, approaching, in the x-y plane.
    Mtot, r0, rp, e = Mt[0] + Mt[1], ORBIT['r0'], ORBIT['rp'], ORBIT['e']
    p = rp * (1 + e)
    nu = -np.arccos(np.clip((p / r0 - 1) / e, -1, 1))
    Rrel = r0 * np.array([np.cos(nu), np.sin(nu), 0])
    Vrel = np.sqrt(Mtot / p) * np.array([-np.sin(nu), e + np.cos(nu), 0])
    offs = [(-Mt[1] / Mtot * Rrel, -Mt[1] / Mtot * Vrel), (Mt[0] / Mtot * Rrel, Mt[0] / Mtot * Vrel)]
    X, V, M, H, tag = [], [], [], [], []
    code = {'halo': 0, 'bulge': 1, 'disc': 2, 'bh': 3}
    for gi, parts in enumerate(gals):
        for kind, x, v, m in parts:
            X.append(x + offs[gi][0]); V.append(v + offs[gi][1]); M.append(m)
            H.append(np.full(len(m), {'halo': H_DM, 'bh': H_BH}.get(kind, H_STAR)))
            tag.append(np.full(len(m), gi * 4 + code[kind], dtype=np.int8))
    X, V, M, H, tag = map(np.concatenate, (X, V, M, H, tag))
    order = np.argsort(tag % 4 == 0, kind='stable')           # stars and black holes first, halo last
    X, V, M, H, tag = X[order], V[order], M[order], H[order], tag[order]
    nsave = int((tag % 4 != 0).sum())
    ibh = np.where(tag % 4 == 3)[0]
    np.save(f'{out}/tag.npy', tag[:nsave]); np.save(f'{out}/mass.npy', M[:nsave])
    print(f'N = {len(M)} ({nsave} stars + black holes), masses {Mt[0]:.1f} + {Mt[1]:.1f}', flush=True)

    t, meta = 0.0, []
    acc = Accel(X, M, H, theta=0.7, parallel=True, method='tree')
    snaps = open(f'{out}/stars.f32', 'wb')
    def save():
        snaps.write(X[:nsave].astype(np.float32).tobytes())
        meta.append(dict(t=t, bh=X[ibh].tolist(), vbh=V[ibh].tolist()))
    save(); t0 = time.time()
    nsteps = int(round(T_END / DT)); every = int(round(T_SNAP / DT))
    for s in range(1, nsteps + 1):
        V += 0.5 * DT * acc
        X += DT * V
        acc = Accel(X, M, H, theta=0.7, parallel=True, method='tree')
        V += 0.5 * DT * acc
        t = s * DT
        if s % every == 0:
            save()
            if (s // every) % 20 == 0:
                d = np.linalg.norm(X[ibh[0]] - X[ibh[1]])
                print(f't = {t * MYR:7.0f} Myr  BH separation {d:7.2f} kpc  ({time.time() - t0:.0f} s)', flush=True)
                json.dump(dict(n=nsave, units=dict(kpc=1, Myr=MYR, kms=KMS, Msun=1e10), snaps=meta), open(f'{out}/meta.json', 'w'))
    snaps.close()
    json.dump(dict(n=nsave, units=dict(kpc=1, Myr=MYR, kms=KMS, Msun=1e10), snaps=meta), open(f'{out}/meta.json', 'w'))

if __name__ == '__main__':
    main()
