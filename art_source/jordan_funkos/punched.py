"""Punched knockback tumble: 2 frames. The figure (tucked pose, dizzy eyes) rotated 90 CCW (head back/left)
then 90 CW (head forward/right) so a 2-frame loop reads as a fast spin; motion arcs + dizzy stars."""
from figures import *

#          x: -4 -3 -2 -1  0  1  2  3  4  5  6  7
TUCK = """
............
....####....
..KK####KK..
.KhK####KhK.
..KsSKffFK..
..KKKKKKKK..
............
"""

STAR_Y = hx('fbf236')
STAR_O = hx('ffb42a')
STAR_W = hx('ffffff')
ARC_L = hx('ffffff')
ARC_M = hx('cbdbfc')

# squint / dizzy eye overrides in HEAD-grid coords: (x, y, char)
DIZZY = {
    'plumber': [(5, 5, 't'), (4, 5, 'K'), (8, 5, 'K'), (9, 5, 'K')],
    'hedgehog': [(7, 4, 'l'), (8, 4, 'l'), (7, 5, 'K'), (8, 5, 'K'), (10, 4, 'l'), (10, 5, 'K'), (11, 4, 'K')],
    'mascot': [(5, 3, 'f'), (4, 3, 'W'), (9, 3, 'f'), (10, 3, 'W')],
    'gamer': [(7, 4, 'S'), (6, 4, 'K'), (9, 4, 'S'), (10, 4, 'K')],
}


def dizzy_head(fig):
    h = copy(fig.head)
    for (x, y, ch) in DIZZY[fig.name]:
        h[y][x] = BLACK if ch == 'K' else fig.color(ch)
    return h


def crop_bbox(px):
    b = bbox(px)
    x0, y0, x1, y1 = b
    return [r[x0:x1 + 1] for r in px[y0:y1 + 1]]


def star(cx, cy, big=False):
    pts = [(cx, cy, STAR_W), (cx - 1, cy, STAR_Y), (cx + 1, cy, STAR_Y), (cx, cy - 1, STAR_Y), (cx, cy + 1, STAR_Y)]
    if big:
        pts += [(cx - 2, cy, STAR_O), (cx + 2, cy, STAR_O), (cx, cy - 2, STAR_O), (cx, cy + 2, STAR_O)]
    return pts


def arc_pts(cx, cy, R, a0, a1, steps=24):
    """quarter-ish arc (angles in degrees, screen coords y down). brighter toward a1 (leading end)."""
    import math
    pts = {}
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        x = int(round(cx + R * math.cos(a)))
        y = int(round(cy + R * math.sin(a)))
        pts[(x, y)] = ARC_L if t > 0.35 else ARC_M
    return [(x, y, c) for (x, y), c in pts.items()]


def punched_frames(fig):
    base = fig.frame(TUCK, head_off=(0, 0), body_off=(0, 0), head=dizzy_head(fig))
    close_outline(base)
    fig_px = crop_bbox(base)
    out = []
    for i, rot in enumerate((rot90ccw, rot90cw)):
        r = rot(fig_px)
        w, h = size(r)
        f = blank(24, 24)
        ox = 12 - w // 2
        oy = 14 - h // 2
        paste(f, r, ox, oy)
        cx, cy = ox + w / 2.0 - 0.5, oy + h / 2.0 - 0.5
        R = max(w, h) / 2.0 + 1.6
        fx = []
        # CCW spin trails: top-left and bottom-right crescents
        fx += arc_pts(cx, cy, R, 165, 245)
        fx += arc_pts(cx, cy, R, -15, 65)
        if i == 0:
            fx += star(ox - 1, oy - 2, big=True) + star(ox + w + 1, oy + 2)
        else:
            fx += star(ox + w + 1, oy - 1, big=True) + star(ox - 2, oy + h - 1)
        for (x, y, c) in fx:
            if 0 <= x < 24 and 0 <= y < 24 and f[y][x][3] == 0:
                f[y][x] = c
        out.append(f)
    return out


if __name__ == '__main__':
    rows = []
    for fig in FIGURES:
        fr = punched_frames(fig)
        rows.append(hstack([zoom(f, 10, ARENA_GREEN, True) for f in fr], gap=10))
    save(vstack([hstack(rows[:2], gap=20), hstack(rows[2:], gap=20)], gap=20), WIP + 'punched_sheet.png')
    print('ok')
