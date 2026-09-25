"""Effects drawn into the perch frames. Each returns a callable fx(cv) for a pose's fx / fx_back list.

Fire is light, so it has no keyline, in the approved ramp the redesign's fire art uses (hottest first):
w (white-hot), Y, P, p, N, n, and r for dying edges. Smoke is solid, so it is keylined, in the
charcoal-violet ramp with a bone rim, like the rig's dust.
"""
import math

from common import pal, shapes
from pal import ellipse, fill
from shapes import edge, recolor, poly_line

HEAT = 'wYPpNnr'                     # hottest first


def hotter(a, b):
    """The hotter of two fire keys (a non-fire key always loses)."""
    ia = HEAT.index(a) if a in HEAT else 99
    ib = HEAT.index(b) if b in HEAT else 99
    return a if ia <= ib else b


def _put_fire(cv, pix, over_body=True):
    """Fire goes over whatever it is drawn on (it blasts out toward the camera). Merge several fires with
    hotter() first: the palette's 'w' is both bone white and white-hot, so the canvas can't tell them apart.
    A lone pixel cut off from the rest of the fire is dropped (it reads as noise, not a spark)."""
    pix = {q: k for q, k in pix.items()
           if any((q[0] + dx, q[1] + dy) in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for q, k in pix.items():
        if not (0 <= q[0] < cv.w and 0 <= q[1] < cv.h):
            continue
        if q not in cv.px or over_body:
            cv.px[q] = k


def _noise(i, seed):
    """A cheap repeatable wobble in -1..1."""
    return math.sin(i * 1.7 + seed * 3.1) * 0.6 + math.sin(i * 0.63 + seed * 1.3) * 0.4


#THROATS

def throat(cx, cy, r=4.5, keys='kqn', squash=1.1, dim=False):
    """Fire building in a maw: concentric heat over the dark mouth pixels only. dim: embers dying down."""
    ramp = 'pNNnn' if dim else 'wYPpN'
    cuts = (0.2, 0.4, 0.6, 0.8) if dim else (0.18, 0.4, 0.62, 0.82)

    def f(cv):
        for y in range(int(cy - r * 1.5) - 1, int(cy + r * 1.5) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, (y - cy) / squash)
                if d <= r and cv.px.get((x, y)) in keys:
                    t = d / r
                    k = ramp[-1]
                    for c, key in zip(cuts, ramp):
                        if t < c:
                            k = key
                            break
                    cv.px[(x, y)] = k
    return f


#MUZZLE FLASH (the volley: a fireball leaving the mouth, upward)

def flash(cx, cy, size=1.0, seed=0, up=True):
    """A burst of fire at a mouth: a white-hot ball with flame petals, the longest one trailing down
    into the mouth when it spits upward, and a few sparks flung off."""
    def f(cv):
        pix = {}
        R = 4.2 * size
        # the ball, just above the lips
        bx, by = cx, cy - (3.5 * size if up else 0)
        for y in range(int(by - R * 2), int(by + R * 2) + 1):
            for x in range(int(bx - R * 2), int(bx + R * 2) + 1):
                d = math.hypot(x - bx, y - by)
                a = math.atan2(y - by, x - bx)
                # petals: the rim swells in 7 lobes, one pointing down into the mouth longest
                lobe = 1.0 + 0.35 * math.cos(7 * a + seed) + (0.55 if up and math.sin(a) > 0.8 else 0)
                rr = R * lobe
                if d <= rr:
                    t = d / rr
                    pix[(x, y)] = 'w' if t < 0.3 else 'Y' if t < 0.5 else 'P' if t < 0.7 else \
                        'p' if t < 0.88 else 'N'
        # sparks flung up and out
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.55 + 0.2 * math.sin(seed + i)
            d = R * (1.9 + 0.3 * ((i + seed) % 3))
            sx, sy = int(round(bx + math.cos(a) * d)), int(round(by + math.sin(a) * d))
            pix[(sx, sy)] = 'Y'
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                pix.setdefault((sx + dx, sy + dy), 'P')
        _put_fire(cv, pix)
    return f


#INHALE (air and embers dragged into the maws)

def wisps(paths, phase=0.0, length=0.6):
    """Air and embers dragged into a maw: streaks along paths ending at the mouth (the last point), pale
    air at the tail warming to an ember head, 2px thick so they hold at game scale. phase 0..1 slides each
    streak along its path, so three frames make them flow."""
    def f(cv):
        pix = {}
        for j, path in enumerate(paths):
            pts = poly_line([(int(round(x)), int(round(y))) for (x, y) in path])
            n = len(pts)
            if n < 4:
                continue
            L = max(4, int(n * length))
            ph = (phase + 0.37 * j) % 1.0
            start = int(ph * (n - L))
            seg = pts[start:start + L]
            for i, (x, y) in enumerate(seg):
                t = i / max(1, len(seg) - 1)
                k = 'y' if t < 0.2 else 'x' if t < 0.45 else 'w' if t < 0.7 else 'P' if t < 0.88 else 'Y'
                pix[(x, y)] = k
                if 0.15 <= t:
                    # thicken on the side away from the mouth's axis
                    tx = path[-1][0]
                    side = 1 if x < tx else -1
                    pix.setdefault((x + side, y), 'y' if t < 0.45 else 'x' if t < 0.7 else 'p')
        for q, k in pix.items():
            if 0 <= q[0] < cv.w and 0 <= q[1] < cv.h:
                cv.px[q] = k
    return f


def embers(points, key='Y', halo='P'):
    """Single sparks with a plus-shaped halo (the approved inhale's sparks)."""
    def f(cv):
        for (x, y) in points:
            cv.px[(x, y)] = key
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in cv.px or cv.px[q] in 'kq':
                    cv.px[q] = halo
    return f


#SMOKE (spent)

def puff(cx, cy, r):
    """One keylined smoke ball: ash grey, lit on top, as the rig's dust is drawn."""
    p = fill(ellipse(cx, cy, r, r * 0.85), 'y')
    recolor(p, edge(p, 0, -1, 1), 'x')
    recolor(p, edge(p, -1, 0, 1), 'x', only='y')
    recolor(p, edge(p, 0, 1, 1), 'z')
    recolor(p, edge(p, 1, 0, 1), 'z', only='y')
    return p


def cloud(blobs):
    """One keylined curl of smoke from overlapping blobs [(x, y, r)], ash grey lit from above, as the rig
    draws its dust: the keyline goes round the whole curl, not each blob."""
    pts = set()
    for (x, y, r) in blobs:
        pts |= ellipse(x, y, r, r * 0.9)
    p = fill(pts, 'y')
    recolor(p, edge(p, 0, -1, 1), 'x')
    recolor(p, edge(p, -1, 0, 1), 'x', only='y')
    recolor(p, edge(p, 0, 1, 1), 'z')
    recolor(p, edge(p, 1, 0, 1), 'z', only='y')
    return p


def smoke(curls):
    """Curls of smoke [[(x, y, r), ...], ...], each one keylined cloud."""
    def f(cv):
        for c in curls:
            cv.stamp(cloud(c))
    return f


#BREATH (the blast: three streams merging into one cone)

def stream(mouth, angle, length, w0, w1, seed=0, tongues=5, open_end=False):
    """A gout of fire from a mouth. angle: degrees from straight down, positive toward +x. The stream
    widens from w0 to w1 (half-widths), its edges licking, and breaks into flame tongues at the end."""
    mx, my = mouth
    a = math.radians(angle)
    ux, uy = math.sin(a), math.cos(a)            # along the stream
    nx, ny = uy, -ux                              # across it
    pix = {}
    reach = length + w1 + 6
    for y in range(int(my - reach), int(my + reach) + 1):
        for x in range(int(mx - reach), int(mx + reach) + 1):
            dx, dy = x - mx, y - my
            t = dx * ux + dy * uy
            s = dx * nx + dy * ny
            if t < -1.5 or t > length + 8:
                continue
            tt = max(0.0, t) / length
            hw = w0 + (w1 - w0) * min(1.0, tt) + 1.2 * _noise(t * 0.8, seed + (1 if s > 0 else 7))
            if t > length and open_end:
                continue
            if t > length * 0.72 and not open_end:
                # tongues: the end splits into licks of fire
                ph = (s / max(1.0, hw)) * tongues * math.pi / 2 + seed
                lick = 0.5 + 0.5 * math.cos(ph)
                end = length * 0.72 + (length * 0.28 + 8) * lick
                if t > end:
                    continue
            if abs(s) > hw:
                continue
            r = abs(s) / max(0.8, hw)
            hot = 1.0 - min(1.0, tt)                   # hotter near the mouth
            k = 'w' if r < 0.22 + 0.25 * hot else 'Y' if r < 0.42 + 0.2 * hot else \
                'P' if r < 0.62 + 0.12 * hot else 'p' if r < 0.82 else 'N'
            if t > length * 0.85 and k in 'wY' and not open_end:
                k = 'P'
            pix[(x, y)] = k
    return pix


def breath(streams, sparks=()):
    def f(cv):
        merged = {}
        for st in streams:
            for q, k in stream(**st).items():
                merged[q] = hotter(k, merged[q]) if q in merged else k
        for (x, y) in sparks:
            merged[(x, y)] = hotter('Y', merged.get((x, y), 'r'))
        _put_fire(cv, merged)
    return f


def fan(apex, spread=65.0, reach=40.0, seed=0, lobes=9, core_len=0.55):
    """The start of the cone, from its apex: a fan of fire `spread` degrees either side of straight down,
    white-hot along the middle near the apex, cooling outward and toward its ragged far edge, which
    splits into tongues so the effects artist's cone can take over from it."""
    ax, ay = apex
    pix = {}
    R = reach + 10
    for y in range(int(ay) - 2, int(ay + R) + 1):
        for x in range(int(ax - R * 1.2), int(ax + R * 1.2) + 1):
            dx, dy = x - ax, y - ay
            d = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(dx, max(0.01, dy))) if d > 0 else 0.0
            if abs(ang) > spread:
                continue
            u = ang / spread                                  # -1..1 across the fan
            edge_r = reach * (1.0 - 0.18 * u * u)
            lick = 0.5 + 0.5 * math.cos(u * lobes * math.pi + seed)
            edge_r += 9 * lick - 3 + 1.5 * _noise(u * 9, seed)
            # the sides of the fan lick too
            side = 1.0 - abs(u)
            if side < 0.12 + 0.06 * _noise(d * 0.5, seed + 3):
                continue
            if d > edge_r:
                continue
            t = d / max(1.0, edge_r)                          # 0 at the apex, 1 at the far edge
            c = abs(u)                                        # 0 on the centre line
            heat = (1.0 - t) * 0.75 + (1.0 - c) * 0.45
            k = 'w' if heat > 1.02 and t < core_len else 'Y' if heat > 0.86 else 'P' if heat > 0.68 else                 'p' if heat > 0.48 else 'N' if heat > 0.3 else 'n'
            pix[(x, y)] = k
    return pix


def blast(streams, apex, spread=65.0, reach=40.0, seed=0, sparks=()):
    """The breath: streams from the mouths running into the apex, the fan opening from it."""
    def f(cv):
        merged = fan(apex, spread, reach, seed)
        for st in streams:
            for q, k in stream(**st).items():
                merged[q] = hotter(k, merged[q]) if q in merged else k
        for (x, y) in sparks:
            merged[(x, y)] = 'Y'
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                merged.setdefault((x + dx, y + dy), 'P')
        _put_fire(cv, merged)
    return f


def sheet(left, right, spread=65.0, reach=46.0, cores=(), seed=0, lobes=11):
    """One cone of fire from the three maws: its top is the line through the outer mouths `left` and
    `right`, its sides run down and out `spread` degrees from straight down, and its far edge (about
    `reach` px from the top) splits into tongues. `cores` are the maws (x, y, angle) whose white-hot
    streams run inside it. Returns (pixels, apex): the apex is where the two sides meet above the maws."""
    (lx, ly), (rx, ry) = left, right
    top = (ly + ry) / 2.0
    tn = math.tan(math.radians(spread))
    half = (rx - lx) / 2.0
    cx = (lx + rx) / 2.0
    apex = (cx, top - half / tn)
    pix = {}
    for y in range(int(top) - 1, int(top + reach + 14)):
        dy = y - top
        for x in range(int(lx - (reach + 14) * tn) - 2, int(rx + (reach + 14) * tn) + 3):
            # inside the two sides?
            if x < lx - dy * tn or x > rx + dy * tn:
                continue
            # the far edge, measured from the apex, licking
            d = math.hypot(x - apex[0], y - apex[1])
            ang = math.degrees(math.atan2(x - apex[0], y - apex[1]))
            u = ang / spread
            far = (top - apex[1]) + reach * (1.0 - 0.12 * u * u)
            lick = 0.5 + 0.5 * math.cos(u * lobes * math.pi + seed)
            far += 10 * lick - 4 + 1.5 * _noise(u * 7, seed)
            # the sides lick in too
            side = min(x - (lx - dy * tn), (rx + dy * tn) - x)
            if side < 1.5 + 2.5 * (0.5 + 0.5 * math.sin(y * 0.7 + seed * 2)) and dy > 3:
                continue
            if d > far:
                continue
            t = (d - (top - apex[1])) / max(1.0, far - (top - apex[1]))
            t = max(0.0, min(1.0, t))
            # heat: cools toward the far edge and the sides; the cores keep it white-hot
            core = 0.0
            for (mx, my, a) in cores:
                ar = math.radians(a)
                ux, uy = math.sin(ar), math.cos(ar)
                along = (x - mx) * ux + (y - my) * uy
                across = abs((x - mx) * uy - (y - my) * ux)
                if along > -1:
                    w = 2.5 + along * 0.22
                    core = max(core, max(0.0, 1.0 - across / w) * max(0.0, 1.0 - along / (reach * 0.95)))
            edge_c = min(1.0, side / 7.0)
            heat = (1.0 - t) * 0.62 + edge_c * 0.25 + core * 0.75
            k = 'w' if heat > 1.05 else 'Y' if heat > 0.82 else 'P' if heat > 0.62 else 'p' if heat > 0.44                 else 'N' if heat > 0.26 else 'n'
            pix[(x, y)] = k
    return pix, apex


def blast2(left, right, cores, spread=65.0, reach=46.0, seed=0, sparks=()):
    def f(cv):
        pix, _ = sheet(left, right, spread, reach, cores, seed)
        for (x, y) in sparks:
            pix[(x, y)] = 'Y'
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                pix.setdefault((x + dx, y + dy), 'P')
        _put_fire(cv, pix)
    return f


def cone(apex, spread=65.0, reach=50.0, seed=0.0, lobes=13, streaks=7, near=6.0, shrink=0.22):
    """The cone's start, from its apex at a maw: a fan `spread` degrees either side of straight down, hot
    radial streaks running out from the apex (so it reads as fire travelling outward), cooling toward the
    far edge, which splits into tongues pointing away from the apex. `near` px around the apex stay
    white-hot where the streams pour in."""
    ax, ay = apex
    pix = {}
    R = reach + 14
    tn = math.tan(math.radians(spread))
    for y in range(int(ay) - 1, int(ay + R) + 1):
        for x in range(int(ax - R * 1.05), int(ax + R * 1.05) + 1):
            dx, dy = x - ax, y - ay
            d = math.hypot(dx, dy)
            if d < 0.5:
                pix[(x, y)] = 'w'
                continue
            ang = math.degrees(math.atan2(dx, max(0.001, dy)))
            if dy < 0 or abs(ang) > spread:
                continue
            u = ang / spread
            far = reach * (1.0 - shrink * u * u)
            lick = 0.5 + 0.5 * math.cos(u * lobes * math.pi + seed)
            far += 11 * lick - 5 + 2.0 * _noise(u * 7, seed)
            # the two sides lick in toward the middle
            side_gap = spread - abs(ang)
            if side_gap < 3 + 4 * (0.5 + 0.5 * math.sin(d * 0.45 + seed * 2)) and d > near:
                continue
            if d > far:
                continue
            t = d / max(1.0, far)
            streak = max(0.0, math.cos(u * streaks * math.pi + seed * 0.7)) ** 3
            heat = (1.0 - t) * 0.8 + (1.0 - abs(u)) * 0.3 + streak * 0.28
            if d < near:
                heat += 0.6
            k = 'w' if heat > 1.12 else 'Y' if heat > 0.9 else 'P' if heat > 0.7 else 'p' if heat > 0.5                 else 'N' if heat > 0.32 else 'n'
            pix[(x, y)] = k
    return pix


def breath_cone(apex, jets, spread=65.0, reach=50.0, seed=0.0, sparks=(), shrink=0.22):
    """The cone from the apex plus each maw's jet pouring into it."""
    def f(cv):
        merged = cone(apex, spread, reach, seed, shrink=shrink)
        for st in jets:
            for q, k in stream(**st).items():
                merged[q] = hotter(k, merged[q]) if q in merged else k
        for (x, y) in sparks:
            merged[(x, y)] = 'Y'
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                merged.setdefault((x + dx, y + dy), 'P')
        _put_fire(cv, merged)
    return f
