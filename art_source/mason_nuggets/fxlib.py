"""Shared helpers + palette for the nugget meteor effects (pure Python, alpha 0/255 only)."""
import math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import write_png, read_png

def hx(h):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)

T = (0, 0, 0, 0)
K = hx('#000000')
WHITE = hx('#FFFFFF')
# nugget (Mason's nugget ramp: props.NUG + CREAM family, DB32 browns)
N_HI   = hx('#EEC39A')   # DB32 cream - breading highlight
N_BASE = hx('#D9A066')   # DB32 tan  - golden breading
N_MID  = hx('#AE8358')   # Mason CREAM_DEEP - breading shade
N_DEEP = hx('#8F563B')   # DB32 brown - crunchy pits / core shadow
N_DARK = hx('#663931')   # DB32 dark brown - deepest crevices
# fire (DB32 yellow/orange/red + the elbow flash's dark red-brown edge)
F_CORE = WHITE
F_YEL  = hx('#FBF236')   # DB32 yellow (Mason YEL)
F_ORG  = hx('#DF7126')   # DB32 orange
F_RED  = hx('#AC3232')   # DB32 red (Mason RED)
F_EDGE = hx('#6E1E0A')   # dark red-brown edge (elbow_impact flash edge)
# grease
G_HI   = WHITE
G_BODY = hx('#FBF236')
G_MID  = hx('#D4CC2E')   # Mason YEL_MID
G_EDGE = hx('#726E17')   # Mason YEL_DEEP
# smoke
S_LT   = hx('#847E87')   # DB32 grey
S_MID  = hx('#696A6A')   # DB32 grey
S_DK   = hx('#595652')   # DB32 dark grey
# sauce (ketchup)
SC_HI  = hx('#D95763')   # DB32 (Mason RED_HI)
SC     = hx('#AC3232')   # DB32 red
SC_DK  = hx('#7A2A30')   # deep red (bucket stripe shadow)
# dust (elbow_impact dust ramp)
D_P = hx('#FBF6E8'); D_Q = hx('#E6DCC2'); D_S = hx('#C4B494'); D_T = hx('#978769'); D_E = hx('#5A4A3A')
# ground shadow (opaque: what the old 80/120/160-alpha black looked like on the mat)
FLOOR = hx('#88B463')
SH_1 = (93, 123, 68, 255)
SH_2 = (72, 95, 52, 255)
SH_3 = (51, 67, 37, 255)

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def canvas(w, h):
    return [[T] * w for _ in range(h)]


def put(g, x, y, c):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = c


def get(g, x, y):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        return g[y][x]
    return T


def mask_from(fn, w, h):
    return {(x, y) for y in range(h) for x in range(w) if fn(x + 0.5, y + 0.5)}


def outline_of(mask, diag=False):
    """pixels outside the mask that touch it"""
    nb = N8 if diag else N4
    out = set()
    for (x, y) in mask:
        for dx, dy in nb:
            p = (x + dx, y + dy)
            if p not in mask:
                out.add(p)
    return out


def inner_edge(mask):
    return {(x, y) for (x, y) in mask if any((x + dx, y + dy) not in mask for dx, dy in N4)}


def paint_mask(g, mask, c):
    for (x, y) in mask:
        put(g, x, y, c)


def blit(dst, src, ox, oy):
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3]:
                put(dst, ox + x, oy + y, p)


def strip(frames):
    fh = len(frames[0]); fw = len(frames[0][0])
    out = canvas(fw * len(frames), fh)
    for i, fr in enumerate(frames):
        for y in range(fh):
            for x in range(fw):
                out[y][i * fw + x] = fr[y][x]
    return out


def save(path, g):
    write_png(path, len(g[0]), len(g), g)


def zoom(g, s, bg=FLOOR, grid_every=0):
    h, w = len(g), len(g[0])
    out = []
    for y in range(h * s):
        row = []
        for x in range(w * s):
            p = g[y // s][x // s]
            if p[3] == 0:
                p = bg
            if grid_every and (x % (grid_every * s) == 0 or y % (grid_every * s) == 0):
                p = tuple(max(0, v - 50) for v in p[:3]) + (255,)
            row.append(p)
        out.append(row)
    return out


def check_alpha(g, name):
    bad = {p[3] for row in g for p in row if p[3] not in (0, 255)}
    assert not bad, '%s has partial alpha %s' % (name, bad)


def edge_touch(g, fw, fh, name):
    n = len(g[0]) // fw
    hits = []
    for i in range(n):
        for y in range(fh):
            for x in range(fw):
                if g[y][i * fw + x][3] and (x in (0, fw - 1) or y in (0, fh - 1)):
                    hits.append((i, x, y))
    if hits:
        print('WARN %s touches frame edge: %d px, e.g. %s' % (name, len(hits), hits[:6]))
    return hits


def colours(g):
    return sorted({p for row in g for p in row if p[3]})
