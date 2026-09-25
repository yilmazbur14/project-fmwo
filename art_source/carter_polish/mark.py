"""Carter's back mark - Akuma's 天 - drawn by the MARK ARTIST'S OWN RIG, never redrawn here.

    ten_back()                -> {(x, y): key}: the 天 exactly where the approved back view has it
                                 (x 32..62, y 53..67), painted by intro_sigil.paint_rest - flat
                                 vermilion ff4a3c with its c01830 edge on the side away from the light.
                                 carter_mark_glow.png is registered to exactly these pixels
                                 (CarterArtLayout.FINAL_MARK_GLOW offset (16, 32)), so nothing moves it.
    ten_fitted(panel, cloth)  -> the same mark fitted onto a pitched back (the rush pass): scaled into
                                 the panel's box by combat_rush.mark_m, clipped to combat_rush.mark_cloth
                                 of the cloth, painted by paint_rest. `panel` and `cloth` are pixel sets.

Why a subprocess: that rig (art_source/carter_akuma) has its own lib.py, the same module name as this
folder's, so both cannot live in one interpreter. The child imports intro_sigil and combat_rush
read-only with the rig's own scale applied (carter_scale.apply()), writes nothing (bytecode off), and
prints the painted pixels as JSON.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.normpath(os.path.join(HERE, '..', 'carter_akuma'))

_CHILD = r'''
import sys, os, json
sys.dont_write_bytecode = True
RIG = sys.argv[1]
sys.path.insert(0, RIG)
import carter_scale
carter_scale.apply()
import lib as rl
import intro_sigil
req = json.loads(sys.stdin.read())

def to_mask(pixels):
    m = rl.empty()
    for x, y in pixels:
        if 0 <= x < rl.W and 0 <= y < rl.H:
            m[y][x] = True
    return m

if req['what'] == 'back':
    sg = intro_sigil.sigil_ten()
else:
    import combat_rush as CR
    panel = to_mask(req['panel'])
    cloth = to_mask(req['cloth'])
    p = {'chest': (47.5, 55.0, 12.0), 'pelvis': (47.5, 70.0, 10.0)}   # unused when a panel is given
    sg = rl.inter(CR.mark_m(p, panel), CR.mark_cloth(cloth))
cv = rl.Canvas()
intro_sigil.paint_rest(cv, sg)
out = []
for y in range(rl.H):
    for x in range(rl.W):
        c = cv.px[y][x]
        if c is not None and sg[y][x]:
            out.append([x, y, '%02x%02x%02x' % tuple(c[:3])])
print(json.dumps(out))
'''

# the two colours paint_rest uses, as this rig's palette keys
_KEY = {'ff4a3c': 'y', 'c01830': 'Y'}

_cache = {}


def _run(req):
    key = json.dumps(req, sort_keys=True)
    if key in _cache:
        return _cache[key]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    r = subprocess.run([sys.executable, '-c', _CHILD, RIG], input=key, capture_output=True,
                       text=True, env=env, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError('mark rig failed:\n' + r.stderr)
    px = {}
    for x, y, hexc in json.loads(r.stdout):
        if hexc not in _KEY:
            raise ValueError('paint_rest used an unexpected colour #%s' % hexc)
        px[(x, y)] = _KEY[hexc]
    _cache[key] = px
    return px


def ten_back():
    return dict(_run({'what': 'back'}))


def ten_fitted(panel, cloth):
    return dict(_run({'what': 'fit', 'panel': sorted(panel), 'cloth': sorted(cloth)}))
