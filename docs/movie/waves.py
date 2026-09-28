# The black hole pair below a parsec: stellar hardening, then gravitational-wave inspiral,
# merger and ringdown. SI units unless a name says otherwise.
#   Hardening: Quinlan (1996) da/dt = -G rho H a^2 / sigma, with the rates of Sesana & Khan (2015).
#   Inspiral: Peters (1964) at wide separations; TaylorT4 at 3.5PN for the last few hundred orbits.
#   Merger and ringdown: the Backwards One Body model (McWilliams 2019) matched to the inspiral,
#   with the l = m = 2 quasinormal mode of the remnant (Berti, Cardoso & Will 2006 fits).
#   Remnant: final spin and radiated energy for non-spinning holes (Hofmann, Barausse & Rezzolla
#   2016; Healy & Lousto 2017 scale), recoil from Gonzalez et al. (2007).
import numpy as np
from scipy.integrate import solve_ivp

G, C, MSUN, PC, AU = 6.674e-11, 2.998e8, 1.989e30, 3.0857e16, 1.496e11
YR, DAY, MYR = 3.156e7, 86400.0, 3.156e13

M1, M2 = 1.0e8, 5.0e7                   # the black holes of the two galaxies in galaxies.py
SIGMA = 170e3                            # M-sigma velocity dispersion for 1.5e8 Msun, m/s
RHO = 500 * MSUN / PC ** 3               # stellar density at the influence radius
H_HARD = 16.0                            # hardening rate (Sesana & Khan 2015)

M = M1 + M2
q, eta = M2 / M1, M1 * M2 / M ** 2
MC = M * eta ** 0.6
TM = G * M * MSUN / C ** 3               # GM/c^3: 739 s for 1.5e8 Msun
RG = G * M * MSUN / C ** 2               # GM/c^2: 1.48 AU

def remnant():
    af = eta * (2 * np.sqrt(3) - 3.5171 * eta + 2.5763 * eta ** 2)      # 0.62
    erad = 0.0484 * (4 * eta) ** 2                                      # 3.8% of M c^2
    mf = 1 - erad
    wr = (1.5251 - 1.1568 * (1 - af) ** 0.1292) / mf                     # l=m=2, n=0, in 1/M
    Q = 0.7000 + 1.4187 * (1 - af) ** -0.4990
    kick = 1.2e4 * eta ** 2 * np.sqrt(1 - 4 * eta) * (1 - 0.93 * eta)   # km/s
    return dict(af=af, erad=erad, mf=mf, w_qnm=wr, tau_qnm=2 * Q / wr, kick_kms=kick)

def radii():
    s = SIGMA
    r_infl = G * M * MSUN / s ** 2
    a_hard = G * (M1 * M2 / M) * MSUN / (4 * s ** 2)
    a_gw = (64 * G ** 2 * s * M * M1 * M2 * MSUN ** 3 / (5 * C ** 5 * H_HARD * RHO)) ** 0.2
    return dict(r_infl=r_infl, a_hard=a_hard, a_gw=a_gw)

def dadt(a):
    stars = G * RHO * H_HARD / SIGMA * a ** 2
    gw = 64 / 5 * G ** 3 * M1 * M2 * M * MSUN ** 3 / (C ** 5 * a ** 3)
    return -(stars + gw), stars, gw

def hardening(a0):
    # Separation against time from a0 down to 30 GM/c^2, stars and gravitational waves together.
    def rhs(t, y): return [dadt(np.exp(y[0]))[0] / np.exp(y[0])]
    stop = lambda t, y: y[0] - np.log(30 * RG)
    stop.terminal = True
    sol = solve_ivp(rhs, (0, 1e19), [np.log(a0)], events=stop, rtol=1e-9, atol=1e-12, dense_output=True, max_step=1e15)
    t = np.concatenate([sol.t[:-1], np.linspace(sol.t[-2], sol.t[-1], 50)])
    t = np.unique(t)
    a = np.exp(sol.sol(t)[0])
    return t, a

def f_gw(a):
    return np.sqrt(G * M * MSUN / a ** 3) / np.pi

def taylor_t4(x0, x1, n=400000):
    # dx/dt for quasi-circular non-spinning binaries, geometric units with M = 1.
    ge = 0.5772156649
    def dxdt(x):
        e = eta; pi = np.pi
        return 64 * e / 5 * x ** 5 * (1 - (743 / 336 + 11 * e / 4) * x + 4 * pi * x ** 1.5
            + (34103 / 18144 + 13661 * e / 2016 + 59 * e ** 2 / 18) * x ** 2
            - (4159 / 672 + 189 * e / 8) * pi * x ** 2.5
            + (16447322263 / 139708800 - 1712 * ge / 105 + 16 * pi ** 2 / 3 - 856 / 105 * np.log(16 * x)
               + (-56198689 / 217728 + 451 * pi ** 2 / 48) * e + 541 * e ** 2 / 896 - 5605 * e ** 3 / 2592) * x ** 3
            - (4415 / 4032 - 358675 * e / 6048 - 91495 * e ** 2 / 1512) * pi * x ** 3.5)
    xs = np.linspace(x0 ** -4, x1 ** -4, n) ** -0.25                  # dense where x changes slowly
    dt = np.diff(xs) / dxdt(0.5 * (xs[1:] + xs[:-1]))
    t = np.concatenate([[0], np.cumsum(dt)])
    om = xs ** 1.5
    phi = np.concatenate([[0], np.cumsum(0.5 * (om[1:] + om[:-1]) * np.diff(t))])
    return t, xs, om, phi, dxdt

def waveform(x0=0.02, x_match=0.13, dt=0.25, t_after=250.0):
    # h22 through inspiral, merger and ringdown, geometric units (M = 1, t = 0 at peak strain).
    rem = remnant()
    t, x, om, phi, dxdt = taylor_t4(x0, x_match)
    om0 = om[-1]
    domdt = 1.5 * x[-1] ** 0.5 * dxdt(x[-1])
    wq = rem['w_qnm'] / 2                                               # orbital-frequency analogue
    gam = 1 / rem['tau_qnm']
    # BOB: Om^4 = Om0^4 + k [tanh(g(t - tp)) - tanh(g(t0 - tp))]; pick tp so dOm/dt matches at t0.
    def slope(d):
        k = (wq ** 4 - om0 ** 4) / (1 - np.tanh(-gam * d))
        return k * gam / np.cosh(gam * d) ** 2 / (4 * om0 ** 3)
    ds = np.linspace(0.1, 200, 20000)
    d = ds[np.argmin(np.abs(slope(ds) - domdt))]
    k = (wq ** 4 - om0 ** 4) / (1 - np.tanh(-gam * d))
    t0 = t[-1]; tp = t0 + d
    tb = np.arange(t0, tp + t_after, dt)
    omb = (om0 ** 4 + k * (np.tanh(gam * (tb - tp)) - np.tanh(gam * (t0 - tp)))) ** 0.25
    phib = phi[-1] + np.concatenate([[0], np.cumsum(0.5 * (omb[1:] + omb[:-1]) * np.diff(tb))])
    # Amplitude: leading-order PN, a smooth rise to the numerical-relativity peak (|h22| r/M about
    # 1.575 eta, reached when M omega_22 is about 0.62 of the ringdown frequency), then the
    # quasinormal decay sech(g (t - t_peak)).
    amp_pn = 8 * np.sqrt(np.pi / 5) * eta * x
    ipk = np.searchsorted(omb, 0.62 * wq)
    tpk, apk = tb[ipk], 1.575 * eta
    s0 = dxdt(x[-1]) / x[-1]                                            # d ln A / dt at the match
    u = (tb - t0) / (tpk - t0)
    L0, L1, D = np.log(amp_pn[-1]), np.log(apk), tpk - t0
    rise = (2 * u ** 3 - 3 * u ** 2 + 1) * L0 + (u ** 3 - 2 * u ** 2 + u) * D * s0 + (-2 * u ** 3 + 3 * u ** 2) * L1
    ampb = np.where(tb < tpk, np.exp(rise), apk / np.cosh(gam * (tb - tpk)))
    tp = tpk
    T = np.concatenate([t[:-1], tb]) - tp
    OM = np.concatenate([om[:-1], omb])
    PHI = np.concatenate([phi[:-1], phib])
    AMP = np.concatenate([amp_pn[:-1], ampb])
    # Nonlinear memory grows with the radiated energy (Favata 2009), about 4% of the peak edge-on.
    hdot2 = np.gradient(AMP * np.cos(2 * PHI), T) ** 2 + np.gradient(AMP * np.sin(2 * PHI), T) ** 2
    E = np.concatenate([[0], np.cumsum(0.5 * (hdot2[1:] + hdot2[:-1]) * np.diff(T))])
    mem = E / E[-1] * 0.0405 * eta
    return dict(t=T, om=OM, phi=PHI, amp=AMP, mem=mem, remnant=rem, t_match=t0 - tp)

if __name__ == '__main__':
    rem, R = remnant(), radii()
    print(f'M = {M:.2e} Msun, q = {q}, eta = {eta:.4f}, chirp mass {MC:.3e}')
    print(f'GM/c^3 = {TM:.1f} s, GM/c^2 = {RG / AU:.2f} AU')
    print(f"influence radius {R['r_infl'] / PC:.1f} pc, hard binary {R['a_hard'] / PC:.2f} pc, GW takes over at {R['a_gw'] / PC:.4f} pc")
    print(f"remnant: spin {rem['af']:.3f}, radiated {rem['erad'] * 100:.1f}%, kick {rem['kick_kms']:.0f} km/s")
    print(f"ringdown f = {rem['w_qnm'] / (2 * np.pi) / TM * 1e6:.1f} uHz, tau = {rem['tau_qnm'] * TM / 3600:.2f} h")
    t, a = hardening(R['a_hard'])
    tl = t[-1] - t
    for ap in [1.0, 0.1, 0.03, 0.01, 0.003, 0.001]:
        i = np.argmin(np.abs(a - ap * PC))
        print(f'a = {ap:6.3f} pc: {tl[i] / MYR:9.3f} Myr to go, f_GW = {f_gw(a[i]) * 1e9:8.3f} nHz, stars/GW = {dadt(a[i])[1] / dadt(a[i])[2]:.3g}')
    w = waveform()
    i = np.argmax(w['amp'])
    print(f"peak |h22| r/M = {w['amp'][i]:.3f} at t = {w['t'][i]:.1f} M; match at {w['t_match']:.1f} M; last frequency {w['om'][-1]:.3f}")
    print(f"orbits from x=0.02: {(w['phi'][i] - w['phi'][0]) / 2 / np.pi:.1f}; duration {(w['t'][i] - w['t'][0]) * TM / DAY:.1f} days")
