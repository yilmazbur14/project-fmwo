"""The standing Carter as a parametric body, for every front-facing combat sheet (idle, eye flash,
hit). With every argument at its default, body() + aura() is frame0.build() pixel for pixel - the
idle's frame 0 is his standing frame, and the entrance's last frame has to match it.

    body(eye=0, jaw=0, hdx=0, hdy=0)   -> Canvas: the standing body, head moved and in any state
    breathe(cv, lift)                  -> the chest lifts `lift` px (upper body up, legs planted)
    shunt(cv, dx)                      -> the whole figure moved sideways (knocked back)
    aura(cv, level=0, seed=0, heat=0)  -> flames behind him: level 0 the idle aura, 1 the full flare,
                                          seed a flicker variant (0 = the approved shapes)
    face_glow(cv, level, hdx, hdy)     -> the eyes' light on his own face (eye flash)
    spokes(cv, level, hdx, hdy)        -> light bursting off his eyes (eye flash peak)
    pool(cv, level)                    -> the floor lit red under him
    streaks(cv, rows, side, length)    -> speed marks off one side of him
"""
import math
from lib import Canvas, grow, DARKER, LIGHTER, AX
import head as HD
import chest as CH
import arms as AR
import jacket as JK
import lower as LO
import aura as AU
import faces as FC

SEAM = 64          # breathing: rows above this rise, the row at SEAM-1 stretches


def body(eye=0, jaw=0, hdx=0, hdy=0):
    cv = Canvas()
    cv.stamp(LO.shins())
    for f in LO.feet():
        cv.stamp(f, outline=False)
    cv.stamp(LO.trousers())
    cv.stamp(AR.arm_l(), outline=False)
    cv.stamp(AR.arm_r(), outline=False)
    for j in JK.jacket():
        cv.stamp(j)
    cv.stamp(CH.chest(), outline=False)
    if hdx or hdy < 0:
        cv.stamp(FC.neck_part(hdx, min(hdy, 0)), outline=False)
    for b in CH.beads():
        cv.stamp(b, outline=False)
    cv.stamp(LO.belt(), outline=False)
    cv.stamp(LO.knot(), outline=False)
    cv.stamp(LO.tails(), outline=False)
    cv.stamp(AR.fist_l(), outline=False)
    cv.stamp(AR.fist_r(), outline=False)
    cv.stamp(FC.head_part(eye, jaw, hdx, hdy), outline=False)
    cv.stamp(FC.earring_part(hdx, hdy), outline=False)
    return cv


def breathe(cv, lift):
    """Everything above SEAM rises `lift` px; the row just above the seam stretches to fill."""
    if not lift:
        return cv
    old = dict(cv.px)
    new = {q: k for q, k in old.items() if q[1] >= SEAM}
    for (x, y), k in old.items():
        if y < SEAM:
            new[(x, y - lift)] = k
    for d in range(1, lift + 1):
        y = SEAM - d
        for x in range(96):
            k = old.get((x, SEAM - 1))
            if k is not None:
                new[(x, y)] = k
            else:
                new.pop((x, y), None)
    cv.px = new
    return cv


def shunt(cv, dx):
    cv.px = {(x + dx, y): k for (x, y), k in cv.px.items()}
    return cv


# ------------------------------------------------------------------ aura

def _h(a, b):
    """a small deterministic hash in [-1, 1]"""
    v = math.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return (v - math.floor(v)) * 2.0 - 1.0


def jitter(specs, seed, amt=1.2):
    """The same tongues, licking: the tips wander, the roots stay put."""
    if not seed:
        return specs
    out = []
    for j, (ctrl, w0, w1) in enumerate(specs):
        c = list(ctrl)
        for n in (2, 3):
            x, y = c[n]
            f = amt * (0.6 if n == 2 else 1.0)
            c[n] = (x + _h(seed, j * 7 + n) * f, y + _h(seed + 3, j * 5 + n) * f)
        out.append((c, w0 * (1.0 + 0.06 * _h(seed, j)), w1))
    return out


def blend(t):
    """The idle tongues growing toward the flare's (t 0..1); the flare's extra pairs (elbows, legs)
    come in once it is past a quarter."""
    specs, order = [], []
    for j, (ctrl, w0, w1) in enumerate(AU.FLARE):
        if j < len(AU.IDLE):
            ci, wi, _ = AU.IDLE[j]
            c = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(ci, ctrl)]
            specs.append((c, wi + (w0 - wi) * t, w1))
        else:
            specs.append((ctrl, w0 * max(0.0, (t - 0.25) / 0.75), w1))
    for j in AU.FLARE_ORDER:
        if j < len(AU.IDLE) or t > 0.3:
            order.append(j)
    return specs, order


def aura(cv, level=0.0, seed=0, heat=0.0, embers=None):
    body_px = set(cv.px)
    if level <= 0.0:
        specs, order = AU.IDLE, AU.IDLE_ORDER
    else:
        specs, order = blend(level)
    specs = jitter(specs, seed)
    cv.stamp(AU.flames(specs, grow(body_px, 1), order, heat=heat), outline=False, under=True)
    if embers is None:
        embers = AU.IDLE_EMBERS if level < 0.5 else AU.FLARE_EMBERS
    if embers:
        cv.stamp(AU.embers(_drift(embers, seed)), outline=False, under=True)
    return cv


def _drift(embers, seed):
    """embers rise a little every frame"""
    if not seed:
        return embers
    return [(x + int(round(_h(seed, x))), y - seed * 2, hot) for x, y, hot in embers if y - seed * 2 > 0]


# ------------------------------------------------------------------ light

SKIN = set('stuvwW')


def face_glow(cv, level, hdx=0, hdy=0):
    """The eyes lighting his own face: the skin just round them steps lighter, and at white heat the
    skin touching the slits takes the glow's red. Skin only - the beard and brows keep their colour."""
    if level <= 0:
        return cv
    r1 = 3.5 + 1.2 * level
    for (cx, cy) in FC.EYE_CENTRES:
        cx, cy = cx + hdx, cy + hdy
        for (x, y), k in list(cv.px.items()):
            if k not in SKIN:
                continue
            d = math.hypot((x - cx) * 0.75, y - cy)
            if d < r1:
                cv.px[(x, y)] = LIGHTER.get(k, k)
            if level >= 2 and d < 2.6:
                cv.px[(x, y)] = 'V'
    return cv


def spokes(cv, level, hdx=0, hdy=0):
    """Dotted shafts of light bursting off the eyes, kept clear of his silhouette."""
    body_px = set(cv.px)
    cx, cy = AX / 2.0 + hdx, 39.5 + hdy
    part = {}
    for n in range(14):
        a = n * math.pi / 7 + 0.18
        for r in range(14, int(20 + 20 * level)):
            x = int(round(cx + math.cos(a) * r * 1.05))
            y = int(round(cy + math.sin(a) * r * 0.95))
            if not (0 <= x < 96 and 0 <= y < 96):
                break
            if (x, y) in body_px or (r + n) % 3:
                continue
            part[(x, y)] = 'O' if r < 22 else ('V' if r < 30 else '7')
    cv.stamp(part, outline=False, under=True)
    return cv


def pool(cv, level):
    """His aura lighting the floor: a low ellipse under his feet, hottest at the middle."""
    part = {}
    rx = 16.0 + 16.0 * level
    for y in range(90, 96):
        for x in range(96):
            u = (x - AX / 2.0) / rx
            v = (y - 95.5) / 5.0
            d = u * u + v * v
            if d <= 1.0:
                part[(x, y)] = 'U' if d > 0.72 else ('z' if d > 0.35 else ('Y' if level < 0.8 or d > 0.15 else 'y'))
    cv.stamp(part, outline=False, under=True)
    return cv


def streaks(cv, rows, side=-1, length=(5, 11), keys='yYz', seed=0):
    """Speed marks leaving one side of his silhouette, broken into dashes."""
    body_px = set(cv.px)
    part = {}
    for i, y in enumerate(rows):
        xs = [x for (x, yy) in body_px if yy == y]
        if not xs:
            continue
        x0 = (min(xs) - 2) if side < 0 else (max(xs) + 2)
        n = length[0] + int(abs(_h(seed, i)) * (length[1] - length[0]))
        for s in range(n):
            if s % 4 == 3:
                continue
            x = x0 + side * s
            part[(x, y)] = keys[min(len(keys) - 1, s * len(keys) // max(1, n))]
    cv.stamp(part, outline=False, under=True)
    return cv
