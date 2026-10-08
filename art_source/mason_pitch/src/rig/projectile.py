"""The thrown nugget, in two stacked layers so the lit nugget never has to be rotated:

  nugget_fastball            4 x 32x32  the spin loop, nugget centred on (16, 16), lit upper left
  nugget_fastball_streaks   16 x 48x48  speed streaks behind it, centred on (24, 24):
                                        frame = dir * 2 + flicker, dir 0 = travelling E, then
                                        clockwise in 45 degree steps (1 SE, 2 S, 3 SW, 4 W, 5 NW,
                                        6 N, 7 NE). 8 directions keep every streak a clean line.
  nugget_changeup_trail     16 x 48x48  same layout: no streaks, a lazy wobble and shed crumbs,
                                        for the slower pitch (play the spin at half rate under it)

Both sprites are centred, so a centred Sprite2D for each stacks them with no offsets. Effects carry
no keyline (house rule); the nugget does.
"""
import math
import nugget as NUG

WHITE = '#FFFFFF'
CREAM_HI = '#FADCB8'     # Mason's own highlight cream: the streak tails
SPIN_DEG = [17.0, 17.0 - 90.0, 17.0 - 180.0, 17.0 - 270.0]


def blank(w, h):
    return [[None] * w for _ in range(h)]


def putter(g):
    def put(x, y, c):
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            g[y][x] = c
    return put


def spin_frames():
    out = []
    for deg in SPIN_DEG:
        g = blank(32, 32)
        NUG.paint(putter(g), 16.0, 16.0, math.radians(deg))
        out.append(g)
    return out


def _dir(d):
    a = math.radians(d * 45.0)
    return (round(math.cos(a), 6), round(math.sin(a), 6))


def _line(put, x0, y0, x1, y1, col_head, col_tail, tail_from):
    """Bresenham from the head (near the nugget) to the tail; pixels past `tail_from` of the
    length take the tail colour"""
    import rig
    pts = rig.bres(x0, y0, x1, y1)
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        put(x, y, col_tail if i >= tail_from * n else col_head)


def _lat(d):
    # whole-pixel lateral offsets per direction (perpendicular, so diagonals stay on the grid)
    dx, dy = _dir(d)
    return (-round(dy * 1.0), round(dx * 1.0)) if d % 2 == 0 else (-int(math.copysign(1, dy)), int(math.copysign(1, dx)))


# (lateral steps, start distance behind the centre, length, width) for the two flicker frames.
# Distances are euclidean px, the same on a diagonal as on a cardinal.
STREAKS = [
    [(0, 7, 16, 2), (3, 6, 10, 1), (-3, 6, 8, 1), (5, 5, 5, 1), (-5, 5, 6, 1)],
    [(0, 7, 13, 2), (3, 6, 8, 1), (-3, 6, 11, 1), (5, 5, 6, 1), (-5, 5, 4, 1)],
]
CRUMBS = [[(1, 12), (-3, 16)], [(-1, 14), (3, 18)]]
# lateral steps on a diagonal are 1.41 px long, so the spacing is scaled to stay about the same
DIAG_LAT = {3: 2, -3: -2, 5: 4, -5: -4, 1: 1, -1: -1}


def streak_frame(d, flick):
    g = blank(48, 48)
    put = putter(g)
    cx, cy = 24, 24
    dx, dy = _dir(d)
    bx, by = -dx, -dy
    lx, ly = _lat(d)
    diag = d % 2 == 1
    for (lat, start, length, width) in STREAKS[flick]:
        k = DIAG_LAT.get(lat, lat) if diag else lat
        ox, oy = k * lx, k * ly
        x0 = cx + ox + int(round(bx * start))
        y0 = cy + oy + int(round(by * start))
        x1 = cx + ox + int(round(bx * (start + length)))
        y1 = cy + oy + int(round(by * (start + length)))
        _line(put, x0, y0, x1, y1, WHITE, CREAM_HI, 0.75)
        if width == 2:
            # thicken: second line one px over (vertical/diagonal -> sideways, horizontal -> down)
            ax, ay = (0, 1) if d in (0, 4) else (1, 0)
            _line(put, x0 + ax, y0 + ay, x1 + ax, y1 + ay, WHITE, CREAM_HI, 0.75)
    for (lat, dist) in CRUMBS[flick]:
        lat = DIAG_LAT.get(lat, lat) if diag else lat
        x = cx + lat * lx + int(round(bx * dist))
        y = cy + lat * ly + int(round(by * dist))
        put(x, y, NUG.N_BASE)
        put(x + 1, y, NUG.N_DEEP)
    return g


def streak_frames():
    return [streak_frame(d, f) for d in range(8) for f in (0, 1)]


# changeup: no speed lines - two short wobble ticks either side and crumbs drifting off behind
WOBBLE = [[(5, 4, 2), (-5, 6, 2)], [(5, 6, 2), (-5, 4, 2)]]
LAZY_CRUMBS = [[(0, 9), (2, 13), (-2, 16)], [(1, 10), (-1, 14), (2, 17)]]


def changeup_frame(d, flick):
    g = blank(48, 48)
    put = putter(g)
    cx, cy = 24, 24
    dx, dy = _dir(d)
    bx, by = -dx, -dy
    lx, ly = _lat(d)
    diag = d % 2 == 1
    for (lat, start, length) in WOBBLE[flick]:
        latp = DIAG_LAT.get(lat, lat) if diag else lat
        s = start
        L = length
        x0 = cx + latp * lx + int(round(bx * s))
        y0 = cy + latp * ly + int(round(by * s))
        x1 = cx + latp * lx + int(round(bx * (s + L)))
        y1 = cy + latp * ly + int(round(by * (s + L)))
        _line(put, x0, y0, x1, y1, CREAM_HI, CREAM_HI, 1.0)
    for (lat, dist) in LAZY_CRUMBS[flick]:
        s = dist
        lat = DIAG_LAT.get(lat, lat) if diag else lat
        x = cx + lat * lx + int(round(bx * s))
        y = cy + lat * ly + int(round(by * s))
        put(x, y, NUG.N_BASE)
        put(x, y + 1, NUG.N_DEEP)
    return g


def changeup_frames():
    return [changeup_frame(d, f) for d in range(8) for f in (0, 1)]
