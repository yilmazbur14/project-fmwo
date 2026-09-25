"""matt_teleport_fx.png: the burst where Matt teleports. 6 frames of 48x96 at 0.05 s, one strip.
THE PIVOT IS (24, 95): the bottom centre, on his feet (the column stands on the floor point he leaves or
lands on). The burst is self-contained (it rises, peaks and dies over the 6 frames), so it can play whole
where he vanishes and again where he lands; its peak (frame 2) lines up with the body sheet squeezing into
its streak.

His palette, from matt.png: a column of light in the shirt's lavender ramp, white-lavender at its core
(#F2F3FF, #DCDEFF) through #B3B6F2 and #8E91DA to a #6D6FBC rim, with gold from his hair tips and trim:
a gold flash where the column meets the floor and gold sparks rising beside it. On the floor, a small
speaker-ring pop: an ellipse in the approved roar-ring style (#F2F3FF core between #4F4D96 edges,
#C4C9FA flanks) that springs out from his feet and breaks up. No keyline, no partial alpha.

  f0  a thin white streak shoots up from his feet
  f1  the column swells, the gold flash at its base, the ring pops out
  f2  the column at full width and height, sparks rising, the ring spreading
  f3  the column splinters into streaks, the ring thinning
  f4  the last streaks and sparks rising, the ring in dashes
  f5  a few motes
"""
import math

import mfx_pal as pal

W, H = 48, 96
CX = 24.0              # the column's axis (a texel corner: texels 23 | 24)
FLOOR = 95             # his feet
FRAME_SIZE = (48, 96)
NOTE = '6 frames at 0.05 s; pivot (24, 95) on his feet'

# The column per frame: half-width, top row, rows at the top that break into rising streaks, whether the
# whole column has splintered into streaks, and whether it carries the gold rim.
COLUMN = [dict(hw=1.6, top=22, frayed=10, rim=False, bands=False),
          dict(hw=4.6, top=8, frayed=14, rim=True),
          dict(hw=7.2, top=2, frayed=16, rim=True),
          dict(hw=5.5, top=6, split=True),
          dict(hw=3.5, top=14, split=True, thin=True),
          None]
# Lavender across the column, core to rim, by |dx| / half-width.
ACROSS = [(0.3, 's'), (0.52, 'q'), (0.72, 'p'), (0.9, 'o'), (1.0, 'n')]
DIM = {'s': 'q', 'q': 'p', 'p': 'o', 'o': 'n', 'n': 'm', 'w': 'v', 'v': 'u'}


def width_at(spec, y, f):
    """The column's half-width at row y: jagged, flickering edges and a slight waist."""
    hw = spec['hw']
    w = hw * (1.0 + 0.11 * math.sin(0.9 * y + 2.1 * f) + 0.07 * math.sin(2.3 * y - 1.3 * f))
    w *= 1.0 - 0.1 * math.sin(math.pi * (y - spec['top']) / max(1, FLOOR - spec['top']))
    return w


def lane_on(x, y, f, density):
    """Streak lanes: every third column carries a broken vertical streak that rises frame to frame."""
    lane = int(math.floor(x + 0.5 - CX + 50)) % 3
    if lane != 0:
        return False
    return ((y + 7 * (x % 5) + 5 * f) % 11) >= density


def column(g, spec, f):
    top = spec['top']
    for y in range(top, FLOOR + 1):
        w = width_at(spec, y, f)
        for x in range(W):
            # the solid body starts lower in some lanes than others, so the top frays raggedly
            ragged = (0, 5, 2, 7, 3, 6, 1, 4)[int(math.floor(x + 0.5 - CX + 50)) % 8]
            frayed = not spec.get('split') and y < top + spec.get('frayed', 0) - ragged
            dx = abs(x + 0.5 - CX)
            if dx > w + (1.0 if spec.get('rim') else 0.0):
                continue
            if dx > w:
                k = 'w' if (y + x) % 7 else 'v'             # the gold rim, with a darker fleck now and then
            else:
                q = dx / w
                k = 'n'
                for edge, key in ACROSS:
                    if q <= edge:
                        k = key
                        break
                # bright sound bands rising through the column (every 9 rows, moving up each frame)
                if spec.get('bands', True) and not spec.get('split') and (y + 4 * f) % 9 == 0 and k in 'pon':
                    k = 'q'
            if spec.get('split') or frayed:
                if not lane_on(x, y, f, 5 if spec.get('thin') else (3 if spec.get('split') else 4)):
                    continue
                if spec.get('thin') or frayed:
                    k = DIM.get(k, k)
            g[y][x] = k


def base_flash(g, f):
    """Gold where the column meets the floor (frames 1-2)."""
    spans = {1: [(FLOOR, 7.5, 'w'), (FLOOR - 1, 5.5, 'x'), (FLOOR - 2, 3.0, 'x')],
             2: [(FLOOR, 9.5, 'v'), (FLOOR - 1, 7.0, 'w'), (FLOOR - 2, 4.0, 'x')]}.get(f, [])
    for y, half, k in spans:
        for x in range(W):
            if abs(x + 0.5 - CX) <= half:
                g[y][x] = k


def floor_ring(g, f):
    """The speaker-ring pop: an ellipse on the floor round his feet in the roar-ring style."""
    spec = {1: (7.0, 's', 0.55, 0.9, 1.6, None), 2: (13.0, 's', 0.6, 0.95, 1.7, None),
            3: (18.0, 'r', 0.5, 0.5, 1.3, None), 4: (21.5, 'm', 0.6, 0.6, 0.6, (14, 0.5))}.get(f)
    if not spec:
        return
    rx, core_k, core, flank, edge, dash = spec
    ry = rx * 0.34
    cy = FLOOR - 1.5
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - CX, (y + 0.5 - cy) / 0.34
            d = math.hypot(dx, dy)
            dd = abs(d - rx)
            # measure the band in screen texels: scale by the local stretch of the ellipse
            stretch = math.hypot(dx, dy * 0.34 * 0.34) / max(0.001, math.hypot(dx, dy * 0.34))
            dd *= max(0.34, min(1.0, stretch))
            if dd > edge:
                continue
            if dash:
                a = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                if (a * dash[0]) % 1.0 > dash[1]:
                    continue
            k = core_k if dd <= core else ('r' if dd <= flank else 'm')
            if g[y][x] in '.mn':
                g[y][x] = k


# Gold sparks rising beside the column: (x, y, key) per frame; mirrored with small differences.
SPARKS = {
    1: [(17, 80, 'x'), (31, 74, 'w'), (19, 62, 'w')],
    2: [(14, 70, 'x'), (33, 62, 'x'), (16, 48, 'w'), (31, 40, 'w'), (13, 30, 'v')],
    3: [(12, 56, 'w'), (35, 48, 'x'), (14, 34, 'w'), (33, 24, 'v'), (16, 14, 'v')],
    4: [(11, 40, 'v'), (36, 30, 'w'), (15, 16, 'v'), (32, 8, 'u')],
    5: [(12, 26, 'u'), (35, 16, 'v'), (22, 4, 'u')],
}
# Lavender motes left over at the end.
MOTES = {4: [(22, 6, 'o'), (26, 20, 'p')], 5: [(24, 12, 'n'), (21, 30, 'o'), (27, 44, 'n')]}


def specks(g, f):
    for table in (SPARKS, MOTES):
        for x, y, k in table.get(f, []):
            if g[y][x] == '.':
                g[y][x] = k
                if k in 'xw' and y + 1 < H and g[y + 1][x] == '.':
                    g[y + 1][x] = 'v'           # a short trail under a bright spark


def frame(f):
    g = pal.blank(W, H)
    floor_ring(g, f)
    if COLUMN[f]:
        column(g, COLUMN[f], f)
    base_flash(g, f)
    specks(g, f)
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(6)]
