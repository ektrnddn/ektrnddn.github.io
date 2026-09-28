# The pair inside the merged nucleus, below what the N-body resolves: dynamical friction
# (Chandrasekhar 1943) on the secondary black hole and the stars still bound to it, tidally
# stripped, in the remnant's potential fitted to the N-body; from the hand-off separation (~1 kpc)
# to a bound binary. Physical units here: pc, Msun, km/s, Myr.
import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import erf
import waves

GPC = 4.30091e-3            # G in pc (km/s)^2 / Msun
KMS = 1.0227                # pc/Myr per km/s
M1, M2 = waves.M1, waves.M2

def fit_host(r, m):
    # Hernquist fit (mass, scale) to enclosed stellar mass around the pair, r in pc.
    order = np.argsort(r)
    rg = np.geomspace(150, 3000, 60)                  # the inner few kpc, where the pair sinks
    cm = np.interp(rg, r[order], np.cumsum(m[order]))
    a = np.geomspace(50, 6000, 300)[:, None, None]
    Mt = np.geomspace(5e9, 2e11, 400)[None, :, None]
    err = np.mean(np.log(Mt * rg ** 2 / (rg + a) ** 2 / cm) ** 2, axis=2)
    i, j = np.unravel_index(np.argmin(err), err.shape)
    return dict(M=float(Mt[0, j, 0]), a=float(a[i, 0, 0]))

class Host:
    def __init__(self, Ms, as_, Mh=1.5e12, ah=30e3):
        self.Ms, self.a, self.Mh, self.ah = Ms, as_, Mh, ah
    def mass(self, r):
        return self.Ms * r ** 2 / (r + self.a) ** 2 + self.Mh * r ** 2 / (r + self.ah) ** 2 + M1
    def rho(self, r):
        return self.Ms * self.a / (2 * np.pi * r * (r + self.a) ** 3) + self.Mh * self.ah / (2 * np.pi * r * (r + self.ah) ** 3)
    def sigma(self, r):
        # Isotropic Jeans dispersion of the stars in the total potential (numerical, cached grid).
        if not hasattr(self, '_sg'):
            rg = np.geomspace(1e-3, 1e6, 3000)
            rs = self.Ms * self.a / (2 * np.pi * rg * (rg + self.a) ** 3)
            integrand = rs * GPC * self.mass(rg) / rg ** 2
            I = np.concatenate([np.cumsum((0.5 * (integrand[1:] + integrand[:-1]) * np.diff(rg))[::-1])[::-1], [0]])
            self._sg = (rg, np.sqrt(I / rs))
        return np.interp(r, *self._sg)

def pairing(host, r0, v0, m_cusp=2e9, a_cusp=80.0, r_end=3.0):
    # Relative orbit of the secondary (black hole + stripped stellar cusp) around the primary.
    def sat_mass(r, prev):
        R = 50.0
        for _ in range(40):
            ms = M2 + m_cusp * R ** 2 / (R + a_cusp) ** 2
            R = r * (ms / (3 * host.mass(r))) ** (1 / 3)
        return min(prev, M2 + m_cusp * R ** 2 / (R + a_cusp) ** 2)
    state = dict(m=M2 + m_cusp)
    def rhs(t, y):
        x, v = y[:3], y[3:]
        r = np.linalg.norm(x); s = np.linalg.norm(v) + 1e-9
        ms = state['m']
        acc = -GPC * host.mass(r) / r ** 3 * x
        X = s / (np.sqrt(2) * host.sigma(r))
        lnL = max(1.0, np.log(r * s ** 2 / (GPC * ms) + 1))
        adf = -4 * np.pi * GPC ** 2 * ms * host.rho(r) * lnL * (erf(X) - 2 * X / np.sqrt(np.pi) * np.exp(-X * X)) / s ** 3 * v
        return np.concatenate([v * KMS, (acc + adf) * KMS])   # km/s and (km/s)^2/pc per Myr
    ts, ys, ms = [0.0], [np.concatenate([r0, v0])], [state['m']]
    t, y = 0.0, ys[0]
    while np.linalg.norm(y[:3]) > r_end and t < 3000:
        r = np.linalg.norm(y[:3])
        P = 2 * np.pi * r / max(np.linalg.norm(y[3:]), 1) / KMS
        sol = solve_ivp(rhs, (t, t + P / 8), y, rtol=1e-8, atol=1e-6, max_step=P / 40, dense_output=True)
        tt = np.linspace(t, sol.t[-1], 9)[1:]
        for ti in tt:
            ys.append(sol.sol(ti)); ts.append(ti)
            state['m'] = sat_mass(np.linalg.norm(ys[-1][:3]), state['m']); ms.append(state['m'])
        t, y = sol.t[-1], sol.y[:, -1]
    return np.array(ts), np.array(ys), np.array(ms)
