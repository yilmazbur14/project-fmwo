"""Small FX for the fastball, in Mason's own palette (his creams/yellows) plus the nugget's breading ramp.

  nugget_bonk   5 x 32x32, centre pivot on HEAD_HIT: the returned nugget bursts into breading crumbs on his
                forehead under a flash star, and two of his own cartoon dizzy stars pop out and wheel off.
                The flash and crumbs carry no keyline (sparks); the cartoon stars are his dizzy star exactly
                (props.star, black outline) so they match frame 13 of his sheet.
  nugget_puff   3 x 8x8, cream puffs with no keyline, emitted behind the changeup.
"""
import math
import sys
sys.dont_write_bytecode = True
import props
import nugget as NUG
from rig import WHITE, YEL, YEL_MID, CREAM_HI, CREAM, CREAM_MID


class _C:
    def __init__(self, w, h):
        self.g = [[None] * w for _ in range(h)]
        self.w, self.h = w, h
        self.head = (0, 0)
        self.bdx = self.bdy = 0

    def put(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = col

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else None


def flash(c, cx, cy, r, core_r=2.2):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            ax, ay = abs(dx), abs(dy)
            d = math.hypot(dx, dy)
            main = (ax == 0 and ay <= r) or (ay == 0 and ax <= r)
            thick = (ax <= 1 and ay <= r - 3) or (ay <= 1 and ax <= r - 3)
            diag = ax == ay and d <= r * 0.72
            if d <= core_r:
                c.put(cx + dx, cy + dy, YEL)
            elif main or thick or diag:
                c.put(cx + dx, cy + dy, WHITE)
    c.put(cx, cy, WHITE)


# eight crumb directions, a little uneven so the burst isn't a stamp
CRUMB_DIRS = [(-0.95, -0.30), (-0.55, -0.85), (0.05, -1.0), (0.60, -0.80), (0.98, -0.20),
              (0.85, 0.50), (-0.20, 0.98), (-0.80, 0.55)]


def crumbs(c, cx, cy, dist, drop, big=True, keep=None):
    for i, (ux, uy) in enumerate(CRUMB_DIRS):
        if keep is not None and i not in keep:
            continue
        x = int(round(cx + ux * dist))
        y = int(round(cy + uy * dist + drop))
        if big:
            c.put(x, y, NUG.N_BASE)
            c.put(x + 1, y, NUG.N_WARM)
            c.put(x, y + 1, NUG.N_WARM)
            c.put(x + 1, y + 1, NUG.N_DEEP)
        else:
            c.put(x, y, NUG.N_BASE if i % 2 else NUG.N_WARM)


def twinkle(c, x, y):
    for p in ((x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        c.put(p[0], p[1], YEL)
    c.put(x, y, WHITE)


def bonk_frames():
    out = []
    cx = cy = 16
    # 0: the hit - flash star, the nugget breaking into its first ring of crumbs
    c = _C(32, 32)
    flash(c, cx, cy, 10)
    crumbs(c, cx, cy, 5, 0)
    out.append(c.g)
    # 1: smaller flash, crumbs flying, the two cartoon stars pop out
    c = _C(32, 32)
    flash(c, cx, cy, 6, 1.6)
    crumbs(c, cx, cy, 8, 0)
    props.star(6, 8, local='abs')(c)
    props.star(26, 7, local='abs')(c)
    out.append(c.g)
    # 2: crumbs spreading and starting to fall, stars wheeling up and out
    c = _C(32, 32)
    crumbs(c, cx, cy, 11, 2)
    props.star(5, 5, local='abs')(c)
    props.star(27, 4, local='abs')(c)
    out.append(c.g)
    # 3: crumbs falling, smaller; stars higher
    c = _C(32, 32)
    crumbs(c, cx, cy, 13, 5, big=False)
    props.star(7, 3, local='abs')(c)
    props.star(25, 3, local='abs')(c)
    out.append(c.g)
    # 4: last crumbs at the edges, the stars down to twinkles
    c = _C(32, 32)
    crumbs(c, cx, cy, 14, 8, big=False, keep={0, 4, 5, 6, 7})
    twinkle(c, 6, 2)
    twinkle(c, 26, 2)
    out.append(c.g)
    return out


def puff_frames():
    out = []
    for (r, ring) in ((1.6, False), (2.7, False), (3.2, True)):
        c = _C(8, 8)
        for dy in range(-4, 4):
            for dx in range(-4, 4):
                d = math.hypot(dx + 0.5, dy + 0.5)
                if d > r or (ring and d < r - 1.2):
                    continue
                if ring and (dx + dy) % 3 == 0:
                    continue
                col = WHITE if (dx + dy) < -1 else (CREAM_HI if (dx + dy) < 2 else CREAM_MID)
                c.put(4 + dx, 4 + dy, col)
        out.append(c.g)
    return out
