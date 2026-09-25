"""Effects for the three-quarter sheets, all drawn BEHIND him (stamped with under=True) and all in the
aura's own palette: the flames edged in the dark violet, red-hot near him, violet at the tips.

    dash(cv, p, level, seed)      flames streaming back off his head and shoulders (the rush)
    tails(cv, p)                  torn gi tails whipping out behind his hips (the rush)
    gutter(cv, p, level, seed)    weak strands rising off his shoulders, dying (punish window, defeat)
    sweat(cv, pts)                drops coming off his hung head
"""
import math
from lib import grow, capsule, poly
import aura as AU
import rig34 as RG


def _body(cv):
    return grow(set(cv.px), 1)


def dash(cv, p, level=1.0, seed=0):
    """The aura torn backwards by the speed: long tongues off the back of his skull and his far
    shoulder, all pointing the way he came."""
    if level <= 0:
        return cv
    hdx, hdy = p['head']
    sx, sy = p['far'][0]
    (cx, cy), _, (nx, ny), _ = RG.torso_frame(p)
    cr = p['chest'][2]
    roots = [
        ((40.0 + hdx, 28.0 + hdy), 26.0, 7.0, -2.0),
        ((37.5 + hdx, 36.0 + hdy), 22.0, 6.0, 1.0),
        ((44.0 + hdx, 25.0 + hdy), 18.0, 5.6, -3.0),
        ((sx - 2.0, sy - 3.0), 18.0, 6.0, 1.5),
        ((cx - nx * cr * 0.9, cy - ny * cr * 0.9 + 4.0), 15.0, 5.0, 2.0),
    ]
    specs = []
    for j, ((rx, ry), ln, w, bend) in enumerate(roots):
        ln *= (0.55 + 0.45 * level)
        wob = math.sin(seed * 1.7 + j * 2.1) * 1.4
        c = [(rx, ry), (rx - ln * 0.35, ry + bend + wob), (rx - ln * 0.7, ry - bend * 0.6 - wob),
             (rx - ln, ry - 1.5 + bend * 0.3)]
        specs.append((c, w * (0.7 + 0.3 * level), 1.0))
    order = list(range(len(specs)))[::-1]
    cv.stamp(AU.flames(specs, _body(cv), order, heat=0.3 * level), outline=False, under=True)
    return cv


def tails(cv, p):
    """Three torn tails of the gi off the back of his hips, trailing along `tails` = (deg, length)."""
    if not p.get('tails'):
        return cv
    deg, ln = p['tails']
    (cx, cy), (ux, uy), (nx, ny), L = RG.torso_frame(p)
    px_, py_, pr = p['pelvis']
    rx, ry = px_ - nx * pr * 0.55, py_ - ny * pr * 0.55
    body = _body(cv)
    for i, (oy, da, f, w) in enumerate(((-4.0, -16.0, 1.00, 5.4), (0.0, 4.0, 0.84, 4.8), (3.5, 22.0, 0.66, 3.8))):
        a = math.radians(deg + da)
        ex, ey = rx + math.cos(a) * ln * f, ry + oy + math.sin(a) * ln * f
        strip = capsule((rx, ry + oy), (ex, ey), w / 2.0, 0.9)
        # torn: notches along the far end
        part = {}
        for (x, y) in strip:
            t = ((x - rx) * math.cos(a) + (y - ry - oy) * math.sin(a)) / (ln * f)
            if t > 0.7 and (x + y + i) % 3 == 0:
                continue
            part[(x, y)] = 'd' if t < 0.4 else ('e' if t < 0.8 else 'C')
        part = {q: k for q, k in part.items() if q not in body}
        cv.stamp(part, outline=True, under=True)
    return cv


def gutter(cv, p, level=0.5, seed=0):
    """What is left of the aura: short strands off the sides of his head and his shoulders that
    wilt - out, over and down - cooler the weaker he is. (Rooted on top of the skull they stood up
    like horns.)"""
    if level <= 0.02:
        return cv
    fx, fy = p['far'][0]
    nx_, ny_ = p['near'][0]
    hdx, hdy = p['head']
    roots = [(36.0 + hdx, 33.0 + hdy, -1), (59.0 + hdx, 33.0 + hdy, 1),
             (fx - 3.0, fy - 1.0, -1), (nx_ + 3.0, ny_ - 1.0, 1)]
    specs = []
    for j, (rx, ry, side) in enumerate(roots):
        ln = (5.0 + 8.0 * level) * (0.8 + 0.35 * abs(math.sin(seed * 1.3 + j)))
        wob = math.sin(seed * 2.3 + j * 1.9) * 1.0
        c = [(rx, ry), (rx + side * ln * 0.35, ry - ln * 0.30 + wob),
             (rx + side * ln * 0.72, ry - ln * 0.18 - wob), (rx + side * ln, ry + ln * 0.22)]
        specs.append((c, 3.0 + 2.4 * level, 1.0))
    cv.stamp(AU.flames(specs, _body(cv), None, heat=0.0), outline=False, under=True)
    return cv


def sweat(cv, pts):
    part = {}
    for x, y in pts:
        part[(x, y)] = '#'
        part[(x, y + 1)] = '%'
    cv.stamp(part, outline=False, under=True)
    return cv
