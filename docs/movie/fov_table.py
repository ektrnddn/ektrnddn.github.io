# The film's field of view (kpc across the frame) against film time, for the scale bar on the
# home page: the same interpolation as render.py's camera (PCHIP in log fov over FOV_KEYS).
#   python3 docs/movie/fov_table.py src/data/film-fov.json
import json, sys, re, ast
import numpy as np
from scipy.interpolate import PchipInterpolator
src = open(__file__.replace('fov_table.py', 'render.py')).read()
keys = np.array(ast.literal_eval(re.search(r'^FOV_KEYS = (\[.*?\])', src, re.M).group(1)))
f = PchipInterpolator(keys[:, 0], np.log(keys[:, 1]))
dt = 0.25
T = np.arange(0, 30 + dt / 2, dt)
json.dump({'dt': dt, 'kpc': [round(float(np.exp(f(t))), 2) for t in T]}, open(sys.argv[1], 'w'))
print('wrote', sys.argv[1], len(T), 'samples')
