"""Shared setup for the Eric V2 UI art (Break gauge, 3-bar mash meter, tier stamps, yellow dodge tell).

It builds on the approved kit rather than copying it: the lettering recipe (MASH!, PARRY!) comes from
art_source/defense_hype/lettering.py and today's finisher meter from art_source/uppercut/qte_ui.py, so
the new pieces share their exact construction. Pure python, no PIL. DB32 only for the HUD pieces,
alpha 0/255; the yellow tell uses Carter's gold ramp, since it has to match his approved ring.

The kit's own modules put their folders at the front of sys.path, so every module here has a name
of its own (no export_all, previews, sheetview or zoom)."""
import os
import sys
import tempfile
sys.dont_write_bytecode = True

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
GODOT = 'C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe'
HERE = os.path.dirname(os.path.abspath(__file__)).replace(os.sep, '/')
for sub in ('defense_hype', 'uppercut'):
    p = PROJ + 'art_source/' + sub
    if p not in sys.path:
        sys.path.append(p)

from dh_common import (Canvas, from_png, strip, save_zoom, hex2rgb, DB32, C, grid, stamp, crop, cell,  # noqa: E402
                       flip_h, scale3, recolor, grid_sheet, bbox, to_rows)
import lettering as LT                                                                                   # noqa: E402

# scratch output never goes into the project: override with EV2_WORK
WORK = (os.environ.get('EV2_WORK') or os.path.join(tempfile.gettempdir(), 'fmwo_eric_v2_ui_work')).replace(os.sep, '/')
os.makedirs(WORK, exist_ok=True)


def work(name):
    return WORK.rstrip('/') + '/' + name


K = C['K']

# Carter's gold ramp (art_source/carter_demon_fx/fxlib.py RAMPS['gold']), for the yellow tell only.
GOLD = ['fffce0', 'ffe45c', 'ffc21e', 'd68a12', '8a5208', '4a2a04']


def put(c, x, y, ch, pal=C):
    c.set(int(x), int(y), pal[ch] if ch in pal else ch)


def solid(c):
    return {(x, y) for y in range(c.h) for x in range(c.w) if c.p[y][x]}


def halo(c, col, base=None, diag=False):
    """1 texel ring on empty pixels around `base` (default: everything drawn so far)"""
    src = solid(base if base is not None else c)
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ())
    for (x, y) in src:
        for dx, dy in nb:
            q = (x + dx, y + dy)
            if q not in src and c.inb(*q) and c.get(*q) is None:
                c.set(q[0], q[1], col)


def outline(c, pts, col=None, diag=True):
    """black (or `col`) outline around a set of points, on pixels not in the set"""
    col = col or K
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ())
    for (x, y) in pts:
        for dx, dy in nb:
            q = (x + dx, y + dy)
            if q not in pts and c.inb(*q):
                c.set(q[0], q[1], col)


def sparkle(c, x, y, size, core='W', tip='Y'):
    put(c, x, y, core)
    for k in range(1, size + 1):
        col = core if k < size else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            put(c, x + dx, y + dy, col)


def zoom(c, name, s=8, grid_wh=None, bg=(70, 70, 90)):
    save_zoom(c, work(name), s, bg=bg, grid=grid_wh)


def check_db32(c, name):
    bad = c.colours() - DB32
    assert not bad, (name, bad)
