"""The ground this rig stands on.

Carter's back-view and turn sheets (carter_intro, carter_look_back, carter_victory), redrawn on the
approved polish body. Two rigs meet here and neither is edited:

  carter_polish   the body, imported read-only (its README: frame0/frame1 are the approved front,
                  back.body() is carter_akuma frame 2, the back view the 天 is registered to).
                  Its lib - the key-per-pixel canvas and the approved palette - is THE lib here.
  carter_akuma    the 天 and everything it does: intro_sigil owns the shape; intro_lib the burn
                  (sigil_paint), the glow on the cloth (sigil_bloom), the bounce on his edge
                  (rim_light), the floor (ground_glow), the squeezes of the turn (hsq_canvas) and the
                  materialise field; intro_profile the back-lit pivot. It runs in its own process
                  (akuma_worker.py) because both rigs have a module called lib and the polish README
                  says never to load both in one interpreter.

Every frame repaints the mark through that rig at the level the shipped frame used, read from the
rig's own constants (intro_frames.MAT / FLARE_LV / TURN, combat_victory.TURN / BURN_LV,
combat_look.MARK_LV), so placement and burn timing are the approved ones by construction.

    fx.*       the mark rig's operations on a key canvas ({(x, y): key})
    K          the rig's constants (levels, timings, the squeeze factors)
    MARK       the 天's 227 pixels, x 32..62, y 53..67
"""
import atexit
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
POLISH = os.path.join(ART, 'carter_polish')
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Carter')

for p in (HERE, POLISH):
    if p in sys.path:
        sys.path.remove(p)
sys.path.insert(0, HERE)
sys.path.insert(1, POLISH)
sys.path.insert(2, ART)

import lib as L                                                               # noqa: E402

assert os.path.dirname(os.path.abspath(L.__file__)) == POLISH, 'lib resolved to the wrong rig'

W = H = 96
PAL = L.PAL
HEX = {k: '%02x%02x%02x' % v[:3] for k, v in PAL.items()}
HEX2KEY = {h: k for k, h in HEX.items()}


# ------------------------------------------------------------------ the akuma rig, in its own process

class _Worker:
    def __init__(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        self.p = subprocess.Popen([sys.executable, '-u', os.path.join(HERE, 'akuma_worker.py')],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
                                  cwd=HERE, bufsize=1)
        atexit.register(self.close)

    def call(self, op, **kw):
        kw['op'] = op
        self.p.stdin.write(json.dumps(kw) + '\n')
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError('the akuma worker died on %s' % op)
        out = json.loads(line)
        if not out.pop('ok'):
            raise RuntimeError('akuma worker, %s: %s\n%s' % (op, out['error'], out.get('trace', '')))
        return out

    def close(self):
        if self.p.poll() is None:
            self.p.stdin.close()
            self.p.wait(timeout=10)


_W = _Worker()


def enc(px):
    return [[x, y, HEX[k]] for (x, y), k in px.items() if 0 <= x < W and 0 <= y < H]


def dec(lst):
    out = {}
    for x, y, h in lst:
        k = HEX2KEY.get(h)
        if k is None:
            raise ValueError('colour #%s at (%d,%d) is not in the polish palette' % (h, x, y))
        out[(x, y)] = k
    return out


def encm(mask):
    return [[x, y] for (x, y) in mask]


def decm(lst):
    return {(x, y) for x, y in lst}


class _K:
    pass


K = _K()
for _k, _v in _W.call('init', pal=HEX).items():
    setattr(K, _k, _v)
MARK = decm(K.mark)
assert len(MARK) == 227 and (min(x for x, _ in MARK), min(y for _, y in MARK),
                             max(x for x, _ in MARK), max(y for _, y in MARK)) == (32, 53, 62, 67), \
    'the 天 moved'


def sq(phi):
    return K.sq[str(float(phi))]


class fx:
    """The mark rig's operations. Each takes and returns a key dict."""

    @staticmethod
    def burn(px, paint, bloom=None, host=None, rim=None, reach=None):
        """sigil_bloom (lit only on `host`) -> rim_light -> sigil_paint, the shipped order: bloom
        first and the emblem last, or the flare swallows the shape at its peak."""
        if rim is not None and reach is None:
            reach = 34.0 + 12.0 * rim
        return dec(_W.call('burn', px=enc(px), paint=paint, bloom=bloom,
                           host=encm(host) if host is not None else None, rim=rim,
                           reach=reach)['px'])

    @staticmethod
    def paint_mask(px, mask, level):
        return dec(_W.call('paint_mask', px=enc(px), mask=encm(mask), level=level)['px'])

    @staticmethod
    def bloom_mask(px, mask, level, host=None):
        return dec(_W.call('bloom_mask', px=enc(px), mask=encm(mask), level=level,
                           host=encm(host) if host is not None else None)['px'])

    @staticmethod
    def squeeze(px, s, keep_head=True, dx=0, reoutline=True):
        return dec(_W.call('squeeze', px=enc(px), s=s, keep_head=keep_head, dx=dx,
                           reoutline=reoutline)['px'])

    @staticmethod
    def sq_mask(mask, s, keep_head=True, dx=0):
        return decm(_W.call('sq_mask', mask=encm(mask), s=s, keep_head=keep_head, dx=dx)['mask'])

    @staticmethod
    def pivot(px):
        return dec(_W.call('pivot', px=enc(px))['px'])

    @staticmethod
    def ground(px, level):
        return dec(_W.call('ground', px=enc(px), level=level)['px'])

    @staticmethod
    def rim_edge(px, side, col='X', amt=0.6):
        return dec(_W.call('rim_edge', px=enc(px), side=side, col=col, amt=amt)['px'])

    @staticmethod
    def edge_shade(px, side, amt=0.55):
        return dec(_W.call('edge_shade', px=enc(px), side=side, amt=amt)['px'])

    @staticmethod
    def reveal(px, k):
        out = _W.call('reveal', px=enc(px), k=k)
        return dec(out['px']), decm(out['mark']), {n: decm(v) for n, v in out['bands'].items()}

    @staticmethod
    def seed(px, k, level):
        return dec(_W.call('seed', px=enc(px), k=k, level=level)['px'])

    @staticmethod
    def gather(t, k):
        out = _W.call('gather', t=t, k=k)
        return ([([tuple(p) for p in c], w0, w1) for c, w0, w1 in out['specs']],
                [tuple(p) for p in out['sparks']])


# ------------------------------------------------------------------ canvases

def canvas(px):
    c = L.Canvas()
    c.px = dict(px)
    return c


def image(px):
    return canvas(px).image()
