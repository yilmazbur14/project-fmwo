"""in-sprite effects + face variants (128-space unless noted)"""
import math
import lib
import rig
from lib import PALC, hexc

# extra effect colours (sweat blues)
for k, v in {'d': 'd8f2ff', 'f': '7cc4f0', 'j': '3a78c0'}.items():
    lib.PAL[k] = v
    PALC[k] = hexc(v)

WHITE = PALC['W']


def smear_arc(fr, c, r_out, width0, width1, a0, a1, behind=False):
    """crescent motion smear following angle a0 -> a1 (degrees, screen coords, y down).
    width grows from width0 at a0 to width1 at a1. Outer rim white, inner soft grey."""
    cx, cy = c
    span = a1 - a0
    for y in range(rig.FH):
        for x in range(rig.FW):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r > r_out + 0.5 or r < r_out - max(width0, width1) - 1:
                continue
            a = math.degrees(math.atan2(dy, dx))
            t = (a - a0) / span if span else 0
            # unwrap
            for k in (-360, 0, 360):
                tt = (a + k - a0) / span
                if 0 <= tt <= 1:
                    t = tt
                    break
            else:
                continue
            w = width0 + (width1 - width0) * t
            inner = r_out - w
            if inner <= r <= r_out:
                if behind and fr.px[y][x] is not None:
                    continue
                q = (r - inner) / max(1e-6, w)
                if q > 0.7:
                    fr.setc(x, y, WHITE)
                elif q > 0.35:
                    fr.set(x, y, 'A')
                elif t > 0.35:
                    fr.set(x, y, 'B')


def ray(fr, p0, p1, w0, ch='W'):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    n = int(L * 2) + 1
    for i in range(n + 1):
        t = i / n
        w = w0 * (1 - t)
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for ox in range(int(-w - 1), int(w + 2)):
            for oy in range(int(-w - 1), int(w + 2)):
                if ox * ox + oy * oy <= w * w + 0.25:
                    fr.set(int(math.floor(cx + ox)), int(math.floor(cy + oy)), ch)


def sparkle(fr, x, y, size=2, ch='W'):
    fr.set(x, y, ch)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            fr.set(x + dx, y + dy, ch if k < size else 'B')


def glint(fr, x, y):
    """4-point star glint on metal"""
    fr.set(x, y, 'W')
    for k in (1, 2, 3):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            fr.set(x + dx, y + dy, 'W' if k < 3 else 'A')
    for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        fr.set(x + dx, y + dy, 'A')


def ellipse_fill(fr, cx, cy, rx, ry, ch, only_bottom_clip=True):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                fr.set(x, y, ch)


PUFF = """
...kkkk...
.kkWWWAkk.
kWWWWWAABk
kWWWAAABBk
kAAABBBCCk
.kkBCCCkk.
...kkkk...
"""
PUFF_S = """
.kkk.
kWWAk
kABCk
.kkk.
"""
ROCK = """
.kk.
kKLk
kLMk
.kk.
"""
ROCK_S = """
kk
kk
"""


def puff(fr, x, y, small=False):
    g = PUFF_S if small else PUFF
    fr.stamp(g, x, y)


def rock(fr, x, y, small=False):
    fr.stamp(ROCK_S if small else ROCK, x, y)


def crack(fr, pts, ch='k'):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            fr.set(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), ch)


DROP = """
.d.
dfd
fjf
.f.
"""


def sweat(fr, x, y):
    fr.stamp(DROP, x, y)


def strain_marks(fr, x, y, flip=False):
    """three short tension ticks radiating out"""
    s = -1 if flip else 1
    for dx, dy in ((0, -3), (s * 3, -2), (s * 4, 1)):
        fr.set(x + dx, y + dy, 'W')
        fr.set(x + dx + s * (1 if dx else 0), y + dy - (1 if dy < 0 else 0), 'W')


def speed_lines(fr, x, y0, y1, ch='W'):
    for y in range(y0, y1):
        fr.set(x, y, ch)


# ------------------------------------------------------------------ face variants (96-space stamps on head layer)
FACE_STRAIN = [
    # squeezed eyes: lid lines, brows pinched down
    (40, 22, "kkkkk"), (51, 22, "kkkkk"), (40, 23, "vtttt"), (51, 23, "ttttv"),
    # gritted teeth under the moustache
    (45, 31, "eeeeee"), (45, 32, "kkkkkk"),
]
FACE_TIRED = [
    # heavy half-closed lids
    (40, 21, "kkkkk"), (51, 21, "kkkkk"), (40, 22, "kkkbk"), (51, 22, "kbkkk"),
    # brows lifted at the inner ends (worn out)
    (41, 20, "ttttt"), (50, 20, "ttttt"), (43, 19, "55"), (51, 19, "55"),
    # mouth hanging open, panting
    (45, 31, "666666"), (45, 32, "k6666k"), (46, 33, "kkkk"),
]


def head_variant(kind):
    key = ('head', kind)
    if key in rig._CACHE:
        return rig._CACHE[key]
    base = rig.layers()['head']
    img = [row[:] for row in base]
    stamps = {'strain': FACE_STRAIN, 'tired': FACE_TIRED}[kind]
    for x0, y0, s in stamps:
        for i, ch in enumerate(s):
            if ch != '.' and img[y0][x0 + i][3]:
                img[y0][x0 + i] = PALC[ch]
    rig._CACHE[key] = img
    return img
