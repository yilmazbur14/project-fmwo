"""Effects for beast Bixby's transformation sequence, in the glow language of the entrance keys
(Liam/Entrance/bixby_transform_keys.png): spiky flame rims hugging the silhouette, thick radial light beams with
white cores, a glowing floor disc, rising ember specks and a white flash disc ringed with orange spikes.
Colours: beast fire ramp W L O o F Q r + crimson wing ramp P Q R S T. Alpha 0/255 only."""
import math
import lib
from lib import *
from pal import PALC, BLACK
from body import line_px
import fx2 as FX

FIRE = ['W', 'L', 'O', 'o', 'F', 'Q', 'r']


def rng(seed):
    return FX.rng(seed)


# ------------------------------------------------------------------ silhouette treatments
def top_edge(mask):
    """topmost pixel per column of a mask"""
    cols = {}
    for (x, y) in mask:
        if x not in cols or y < cols[x]:
            cols[x] = y
    return cols


def rim_glow(cv, mask, colour='O', outer='Q'):
    """1px bright outline hugging the silhouette, with a dimmer halo one step further out"""
    e1 = outer_edge(mask)
    for (x, y) in e1:
        cv.put(x, y, PALC[colour])
    for (x, y) in outer_edge(mask | e1):
        cv.put(x, y, PALC[outer])
    return e1


def rim_flames(cv, mask, t, height=7, seed=3, dense=2, colours=('O', 'o', 'F')):
    """flame spikes licking up off the silhouette's upper edge (entrance-key language)"""
    cols = top_edge(mask)
    R = rng(seed)
    xs = sorted(cols)
    for x in xs:
        if x % dense:
            continue
        h = height * (0.45 + 0.75 * R()) * (1.0 + 0.25 * math.sin(t * 1.7 + x * 0.4))
        if h < 1.5:
            continue
        y0 = cols[x]
        lean = math.sin(t * 0.9 + x * 0.25) * 1.2
        for k in range(int(h)):
            u = k / max(1.0, h)
            xx = int(round(x + lean * u * u))
            yy = int(round(y0 - 1 - k))
            c = colours[0] if u < 0.35 else (colours[1] if u < 0.7 else colours[2])
            if cv.get(xx, yy) is None:
                cv.put(xx, yy, PALC[c])
            if u < 0.3 and cv.get(xx + 1, yy) is None and R() < 0.35:
                cv.put(xx + 1, yy, PALC[colours[1]])


def crack_lines(cv, mask, seeds, level=2, seed=11, length=16, branch=True):
    """glowing lava cracks spreading inside a silhouette / body"""
    R = rng(seed)
    hot = {1: ('r', 'F', 'F'), 2: ('F', 'o', 'O'), 3: ('o', 'O', 'L')}[level]
    for (sx, sy, ang0) in seeds:
        x, y = float(sx), float(sy)
        ang = ang0
        pts = [(x, y)]
        for i in range(int(length)):
            ang += (R() - 0.5) * 1.1
            x += math.cos(ang) * 2.2
            y += math.sin(ang) * 2.2
            if (int(x), int(y)) not in mask:
                break
            pts.append((x, y))
        px = line_px(pts)
        for k, q in enumerate(px):
            if q not in mask:
                continue
            u = k / max(1, len(px) - 1)
            c = hot[2] if u < 0.3 else (hot[1] if u < 0.7 else hot[0])
            cv.put(q[0], q[1], PALC[c])
        if branch and len(px) > 6 and R() < 0.8:
            bx, by = px[len(px) // 2]
            ba = ang + (1.1 if R() < 0.5 else -1.1)
            bp = [(bx, by)]
            for i in range(int(length * 0.45)):
                ba += (R() - 0.5) * 0.9
                bx += math.cos(ba) * 2.2
                by += math.sin(ba) * 2.2
                if (int(bx), int(by)) not in mask:
                    break
                bp.append((bx, by))
            for q in line_px(bp):
                if q in mask:
                    cv.put(q[0], q[1], PALC[hot[1] if R() < 0.5 else hot[0]])


CRIMSON = ['R', 'S', 'T']          # lit / body / shadow crimson for transformation silhouettes


def fill_silhouette(cv, mask, light=(-0.5, -0.8), body=CRIMSON, rim='Q'):
    """fill a mask as a dark crimson transformation silhouette with a lit upper-left edge"""
    if not mask:
        return
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w = max(1.0, (max(xs) - min(xs)) / 2)
    h = max(1.0, (max(ys) - min(ys)) / 2)
    inner = erode(mask, 1)
    for (x, y) in mask:
        if (x, y) not in inner:
            cv.put(x, y, PALC[rim])
            continue
        u = (x - cx) / w
        v = (y - cy) / h
        d = u * light[0] + v * light[1]
        cv.put(x, y, PALC[body[0] if d > 0.42 else (body[1] if d > -0.25 else body[2])])


# ------------------------------------------------------------------ ground + rings
def ground_disc(cv, cx, cy, rx, ry, level=1.0):
    """glowing floor disc under the transformation (entrance-key F0 language)"""
    m = ell(cx, cy, rx, ry)
    inner = ell(cx, cy, rx * 0.72, ry * 0.72)
    core = ell(cx, cy, rx * 0.4, ry * 0.42)
    for (x, y) in m:
        c = 'r' if level < 0.5 else 'Q'
        cv.put(x, y, PALC[c])
    for (x, y) in inner:
        cv.put(x, y, PALC['F' if level < 0.6 else 'o'])
    if level > 0.45:
        for (x, y) in core:
            cv.put(x, y, PALC['o' if level < 0.8 else 'O'])
    for (x, y) in edge(m):
        cv.put(x, y, PALC['r'])


def ring(cv, cx, cy, rx, ry, thick=2, colours=('W', 'O', 'o'), squash_rim='r'):
    """flat expanding ground ring (shockwave)"""
    outer = ell(cx, cy, rx, ry)
    innr = ell(cx, cy, max(0.5, rx - thick), max(0.4, ry - thick * ry / max(1e-3, rx)))
    band = outer - innr
    for (x, y) in band:
        d = abs(((x + 0.5 - cx) / max(1e-3, rx)) ** 2 + ((y + 0.5 - cy) / max(1e-3, ry)) ** 2)
        c = colours[0] if d > 0.86 else (colours[1] if d > 0.6 else colours[2])
        cv.put(x, y, PALC[c])
    for (x, y) in edge(band):
        if cv.get(x, y) is not None:
            cv.put(x, y, PALC[squash_rim])


def dome(cv, cx, cy, r, squash=0.55, colours=('L', 'O', 'o')):
    """half-dome shock (used when he lifts off)"""
    m = {(x, y) for (x, y) in ell(cx, cy, r, r * squash) if y <= cy + r * squash * 0.35}
    inner = erode(m, 2)
    for (x, y) in m:
        cv.put(x, y, PALC[colours[2] if (x, y) in inner else colours[1]])
    for (x, y) in edge(m):
        cv.put(x, y, PALC[colours[0]])


# ------------------------------------------------------------------ rays / flash
def rays(cv, cx, cy, n, r0, r1, phase=0.0, width=0.075, colours=('W', 'L', 'O'), seed=3, jitter=0.30, margin=4):
    """thick radial light beams with white cores, wedge shaped (entrance-key F1 language)"""
    R = FX.rng(seed)
    beams = []
    for k in range(n):
        a = phase + 2 * math.pi * k / n + (R() - 0.5) * 0.12
        length = r1 * (1.0 - jitter * R())
        # never let a beam reach the frame edge: cap it to the distance to the margin along its own direction
        dx, dy = math.cos(a), math.sin(a)
        cap = 1e9
        for lim, d in ((margin - cx, dx), (cv.w - 1 - margin - cx, dx), (margin - cy, dy), (cv.h - 1 - margin - cy, dy)):
            if d != 0:
                t = lim / d
                if t > 0:
                    cap = min(cap, t)
        beams.append((a, max(r0 + 6, min(length, cap)), width * (0.7 + 0.6 * R())))
    x0 = max(0, int(cx - r1 - 4)); x1 = min(cv.w - 1, int(cx + r1 + 4))
    y0 = max(0, int(cy - r1 - 4)); y1 = min(cv.h - 1, int(cy + r1 + 4))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r < r0 or r > r1 + 2:
                continue
            ang = math.atan2(dy, dx)
            for (a, L, w) in beams:
                if r > L:
                    continue
                d = abs((ang - a + math.pi) % (2 * math.pi) - math.pi)
                # wedge: narrow at the core, opening outward, with a soft taper at the tip
                ww = w * (0.55 + 0.45 * min(1.0, (r - r0) / max(1.0, L - r0))) * (1.0 - 0.92 * max(0.0, (r - L * 0.62) / max(1.0, L * 0.38)))
                if ww <= 0.004 or d > ww:
                    continue
                f = d / ww
                cv.put(x, y, PALC[colours[0] if f < 0.34 else (colours[1] if f < 0.68 else colours[2])])
                break


def flash_disc(cv, cx, cy, r, spikes=18, phase=0.0, core=0.55, ring_w=0.16, sq=0.90, margin=3):
    """white core disc, yellow ring, orange spikes and a thin white rim (entrance-key F2 language).
    Spikes are capped so they end inside the frame."""
    for k in range(spikes):
        a = phase + 2 * math.pi * k / spikes
        L = r * (1.12 + 0.26 * (((k * 5) % 3) / 2.0))
        dx, dy = math.cos(a), math.sin(a) * sq
        cap = 1e9
        for lim, d in ((margin - cx, dx), (cv.w - 1 - margin - cx, dx), (margin - cy, dy), (cv.h - 1 - margin - cy, dy)):
            if d != 0:
                t = lim / d
                if t > 0:
                    cap = min(cap, t)
        L = min(L, cap)
        w = r * 0.085
        px_, py_ = -math.sin(a), math.cos(a) * sq
        start = r * 0.8
        if L <= start + 2:
            continue
        for s_ in range(int(start), int(L)):
            u = (s_ - start) / max(1.0, L - start)
            ww = max(0.5, w * (1.0 - u))
            ax, ay = cx + dx * s_, cy + dy * s_
            for t in range(-int(ww), int(ww) + 1):
                cv.put(int(round(ax + px_ * t)), int(round(ay + py_ * t)), PALC['o' if u > 0.45 else 'O'])
    outer = ell(cx, cy, r, r * sq)
    mid = ell(cx, cy, r * (1 - ring_w), r * sq * (1 - ring_w))
    inner = ell(cx, cy, r * core, r * sq * core)
    for (x, y) in outer:
        cv.put(x, y, PALC['O'])
    for (x, y) in mid:
        cv.put(x, y, PALC['L'])
    for (x, y) in inner:
        cv.put(x, y, PALC['W'])
    for (x, y) in edge(outer):
        cv.put(x, y, PALC['W'])


def implode_streaks(cv, cx, cy, r0, r1, n=22, seed=5, colours=('L', 'O', 'o')):
    """embers and light sucked inward: tapered streaks pointing at the core"""
    R = rng(seed)
    for k in range(n):
        a = 2 * math.pi * k / n + R() * 0.3
        rr1 = r1 * (0.7 + 0.5 * R())
        rr0 = r0 * (0.8 + 0.4 * R())
        pts = [(cx + math.cos(a) * rr0, cy + math.sin(a) * rr0 * 0.92),
               (cx + math.cos(a) * rr1, cy + math.sin(a) * rr1 * 0.92)]
        px = line_px(pts)
        for i, q in enumerate(px):
            u = i / max(1, len(px) - 1)
            c = colours[0] if u < 0.25 else (colours[1] if u < 0.6 else colours[2])
            cv.put(q[0], q[1], PALC[c])


# ------------------------------------------------------------------ embers / smoke
def embers_rising(cv, box, t, n=18, seed=7, speed=6.0, sizes=(1, 1, 2)):
    """ember specks drifting upward; t advances them (loops over n columns)"""
    x0, y0, x1, y1 = box
    R = rng(seed)
    for k in range(n):
        bx = x0 + R() * (x1 - x0)
        span = (y1 - y0)
        by = y1 - ((R() * span + t * speed) % span)
        sway = math.sin(t * 0.8 + k) * 2.0
        s = sizes[int(R() * len(sizes)) % len(sizes)]
        FX.ember(cv, bx + sway, by, s, hot=R() < 0.5)


def ember_swirl(cv, cx, cy, t, n=20, rx=54, ry=30, seed=9, rise=1.0):
    """embers spiralling up around him"""
    R = rng(seed)
    for k in range(n):
        ph = R() * 6.28
        h = R()
        a = ph + t * 0.55 + h * 2.2
        r = rx * (0.45 + 0.55 * h)
        x = cx + math.cos(a) * r
        y = cy - h * ry * 2.0 * rise + math.sin(a) * ry * 0.22
        FX.ember(cv, x, y, 1 if R() < 0.7 else 2, hot=R() < 0.45)


def smoke_ring(cv, cx, cy, rx, ry, r=6.0, n=9, seed=13, holes=0.0):
    R = rng(seed)
    for k in range(n):
        a = 2 * math.pi * k / n + R() * 0.4
        x = cx + math.cos(a) * rx
        y = cy + math.sin(a) * ry
        FX.puff(cv, x, y, r * (0.7 + 0.5 * R()), seed=seed * 31 + k, holes=holes)
