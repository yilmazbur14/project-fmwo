"""A splayed open hand for the BOOMBURST: palm to camera, the four fingers fanned wide and the thumb
out toward his head, in the rig's skin ramp lit from the upper left, every finger keylined off the next
as the approved hands are. Built from finger segments on the rig's own Canvas (each part stamped with
its keyline), then printed as a map so it can be hand-tuned like mi_hands.

    python ea_hands.py       # build, print the map, render it at 12x into work/
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ea_base as E
from ea_base import B, H, sh, ellipse


def seg_px(p0, p1, r):
    (x0, y0), (x1, y1) = p0, p1
    out = set()
    for y in range(int(min(y0, y1) - r) - 1, int(max(y0, y1) + r) + 2):
        for x in range(int(min(x0, x1) - r) - 1, int(max(x0, x1) + r) + 2):
            vx, vy = x1 - x0, y1 - y0
            L2 = vx * vx + vy * vy or 1.0
            t = max(0.0, min(1.0, ((x - x0) * vx + (y - y0) * vy) / L2))
            if math.hypot(x - (x0 + vx * t), y - (y0 + vy * t)) <= r:
                out.add((x, y))
    return out


# (base, angle from straight up in degrees, length): pinky, ring, middle, index, thumb (screen-left hand)
FINGERS = [((6.6, 10.5), -42, 5.2), ((8.6, 9.2), -17, 6.6), ((10.8, 8.8), 3, 7.4), ((12.9, 9.4), 24, 6.4)]
THUMB = ((14.4, 13.2), 62, 4.6)
PALM = (10.6, 12.6, 4.9, 4.1)
W_, H_ = 22, 22


def build(side=0):
    """side 0: the screen-left hand (thumb to the right, toward his head); side 1 its twin, built
    from mirrored geometry and lit from the same upper left."""
    def m(p):
        return (W_ - 1 - p[0], p[1]) if side else p

    def ma(a):
        return -a if side else a
    cv = B.Canvas(W_, H_)
    pc = m((PALM[0], PALM[1]))
    palm = {p: '2' for p in ellipse(pc[0], pc[1], PALM[2], PALM[3])}
    sh.ellipsoid(palm, pc[0] - 0.5, pc[1] - 0.5, PALM[2] + 1, PALM[3] + 1, '12345', (0.75, 0.45, 0.1, -0.2))
    def digit(base, ang, ln):
        bx, by = m(base)
        a = math.radians(ma(ang))
        tip = (bx + math.sin(a) * ln, by - math.cos(a) * ln)
        part = {p: '2' for p in seg_px((bx, by), tip, 1.05)}
        sh.cylinder(part, (bx, by), tip, 1.3, '1234', (0.55, 0.2, -0.2))
        return part
    # the fingers keylined off each other, then the palm laid over their roots with no line (the
    # fingers grow out of it), then the thumb, keylined against the palm, then the outer keyline
    for f in FINGERS:
        cv.stamp(digit(*f))
    cv.stamp(palm, outline=False)
    cv.stamp(digit(*THUMB))
    return B.keyline_gaps(dict(cv.px))


def build_left():
    return build(0)


def hand(side):
    """(rows, anchor): anchor is the middle of the wrist's bottom keyline, where the forearm meets it."""
    rows, _ = to_rows(build(side))
    last = rows[-1]
    ks = [i for i, c in enumerate(last) if c == 'k']
    return rows, ((ks[0] + ks[-1]) // 2, len(rows) - 1)


def to_rows(px):
    xs = [x for x, y in px]
    ys = [y for x, y in px]
    x0, y0 = min(xs), min(ys)
    rows = []
    for y in range(y0, max(ys) + 1):
        rows.append(''.join(px.get((x, y), '.') for x in range(x0, max(xs) + 1)))
    return rows, (x0, y0)


if __name__ == '__main__':
    import env
    from ea_base import V
    px = build_left()
    rows, (x0, y0) = to_rows(px)
    for r in rows:
        print('    "%s",' % r)
    im = B.image(B.amap(rows, 1, 1), len(rows[0]) + 2, len(rows) + 2)
    ref = B.image(B.amap(H.OPEN_UP_L[0], 1, 1), 18, 15)
    V.row([V.up(im, 12), V.up(ref, 12)]).save(os.path.join(env.WORK, 'splay_12x.png'))
