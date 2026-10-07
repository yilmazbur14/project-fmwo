"""The summon rift: a tear in the void floor that a puppet is dragged up through on its strings,
and the despawn that swallows it again. An overlay that works for any puppet, one per puppet
(two side by side for a two-puppet summon).

Two sizes from the same drawing, each with its anchor on the texel a puppet's FEET point sits on:

  STD    144x96,  anchor (72, 72): a tear 96 texels wide, for a puppet up to about 90 wide
         (Greyson, Matt, Captain Burak, and the 64-96 frames of the rest)
  WIDE   224x112, anchor (112, 84): a tear 160 wide, for Danny's sumo (176 frame)

Three synced layers per frame:

  back   (normal, BEHIND the puppet): the black hole, its far wall lit by the fire below, the
         far rim burning, the cracks on the far side, smoke boiling up behind the puppet and
         the embers behind it.
  front  (normal, IN FRONT of the puppet): the near rim, the cracks on the near side, the
         SURFACE shimmer across the hole on the anchor row (it hides the puppet's clip edge),
         smoke curling round the two ends of the tear, and the embers in front.
  glow   (ADDITIVE, the aura's recipe and colours, over the puppet): a haze in rings round the
         tear, taller above its far rim, so the floor and the rising puppet's legs catch the
         fire from below.

While the puppet is in the rift it is CLIPPED at the anchor row: its texels below that row are
not drawn (a Sprite2D region that crops its bottom rows does it). Raise its feet from about one
puppet height below the anchor up to the anchor while the rift is open, then let it close.

Effect art: no keyline, no semi-alpha, the god's own palette (obsidian smoke, lava reds). Nothing
here writes a file.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import jp_rig as R  # noqa: E402,F401
import jg_base as B  # noqa: E402
import jg_god as G  # noqa: E402
from jg_base import JORDAN  # noqa: E402
from jg_lord_pal import LORD  # noqa: E402

PAL = {k: LORD[k] for k in ('k', '1', '2', '3', '4', '5', 'V', 'R', 'T', 'r', 'O', 'Y', 'w')}
PAL['v'] = JORDAN['v']      # 4C0D1A, the darkest blood red
GLOW_PAL = dict(G.AURA)     # x 3E0E0A, y 2A0907, z 160404 (added)

HEAT = ('v', 'V', 'R', 'T', 'r', 'O', 'Y')


def heat_key(h):
    cuts = (0.12, 0.28, 0.46, 0.64, 0.80, 0.93)
    k = 0
    while k < len(cuts) and h > cuts[k]:
        k += 1
    return HEAT[k]


# fixed jag tables so the tear keeps its shape from frame to frame
_rj = random.Random(11)
JAG_TOP = [_rj.uniform(0.0, 1.0) for _ in range(144)]
JAG_BOT = [_rj.uniform(0.0, 1.0) for _ in range(144)]
HOT = [_rj.uniform(-0.12, 0.12) for _ in range(144)]
_rw = random.Random(12)                  # the wide rift's extra columns
JAG_TOP += [_rw.uniform(0.0, 1.0) for _ in range(112)]
JAG_BOT += [_rw.uniform(0.0, 1.0) for _ in range(112)]
HOT += [_rw.uniform(-0.12, 0.12) for _ in range(112)]


def _smooth(tab, x):
    i = int(x) % len(tab)
    return (tab[i - 1] + 2 * tab[i] + tab[(i + 1) % len(tab)]) / 4.0


class Profile:
    """One rift size. The sequences' w and h are for STD; a profile scales them."""

    def __init__(self, name, w, h, anchor, ws, hs):
        self.name, self.W, self.H, self.ANCHOR = name, w, h, anchor
        self.CX, self.CY = anchor[0] - 0.5, anchor[1]
        self.ws, self.hs = ws, hs


STD = Profile('std', 144, 96, (72, 72), 1.0, 1.0)
WIDE = Profile('wide', 224, 112, (112, 84), 1.667, 1.35)
PROFILES = {'std': STD, 'wide': WIDE}


def lens(P, w, h):
    """{x: (top_row, bottom_row)} of the tear for half-width w, half-height h (rows are the rim
    rows; the hole is strictly between them). With h < 0.5 the tear is a crack: top == bottom."""
    out = {}
    for x in range(int(math.floor(P.CX - w)), int(math.ceil(P.CX + w)) + 1):
        dx = (x - P.CX) / w
        if abs(dx) >= 1.0:
            continue
        f = (1.0 - dx * dx) ** 0.75
        if h < 0.5:
            j = _smooth(JAG_TOP, x)
            y = P.CY + (1 if j > 0.72 else -1 if j < 0.28 else 0)
            out[x] = (int(y), int(y))
            continue
        jt = (_smooth(JAG_TOP, x) - 0.3) * 1.6 * min(1.0, h / 6.0)
        jb = (_smooth(JAG_BOT, x) - 0.3) * 1.3 * min(1.0, h / 6.0)
        top = P.CY - h * f - jt
        bot = P.CY + h * f * 0.92 + jb
        yt, yb = int(math.floor(top + 0.5)), int(math.floor(bot + 0.5))
        if yb - yt < 2:
            yt, yb = P.CY - 1, P.CY + 1
        out[x] = (yt, yb)
    return out


# ------------------------------------------------------------------ cracks radiating on the floor

def _crack_set(seed, n, reach, side):
    """n jagged cracks leaving the tear's rim on `side` (-1 far/up, +1 near/down)."""
    rnd = random.Random(seed)
    cracks_ = []
    for i in range(n):
        u = (i + 0.5) / n * 2 - 1
        u += rnd.uniform(-0.12, 0.12)
        ang = math.atan2(side * (0.35 + 0.4 * rnd.random()), u * 1.6 + rnd.uniform(-0.3, 0.3))
        ln = reach * (0.55 + 0.45 * rnd.random()) * (1.3 if abs(u) > 0.7 else 1.0)
        jag = [rnd.uniform(-1.2, 1.2) for _ in range(12)]
        cracks_.append((u, ang, ln, jag))
    return cracks_


FAR_CRACKS = _crack_set(3, 6, 16, -1)
NEAR_CRACKS = _crack_set(4, 5, 12, 1)
END_CRACKS = [(-1.0, math.pi + 0.10, 16, [0.6, -0.8, 0.9, -0.4, 0.7, -0.9, 0.3, 0.5, -0.6, 0.8, -0.3, 0.4]),
              (1.0, -0.12, 17, [-0.5, 0.8, -0.7, 0.4, -0.9, 0.6, -0.2, -0.5, 0.7, -0.4, 0.6, -0.8])]


def _crack_pixels(start, ang, ln, jag, grow, heat):
    """[(pixel, key)] of one crack grown to `grow` (0..1) of its length, hot at the tear."""
    L_ = ln * grow
    if L_ < 1.0:
        return []
    n = max(2, int(L_ / 2.5))
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    pts = [start]
    for i in range(1, n + 1):
        t = i / n
        j = jag[i % len(jag)] * (0.4 if i == n else 1.0)
        pts.append((start[0] + dx * L_ * t + nx * j, start[1] + dy * L_ * t * 0.55 + ny * j * 0.55))
    path = B.polyline([(int(round(x)), int(round(y))) for x, y in pts])
    out = []
    for i, q in enumerate(path):
        t = i / max(1, len(path) - 1)
        out.append((q, heat_key(heat * (0.78 - 0.7 * t))))
    return out


def cracks(P, shape, w, grow, heat, side):
    """Floor cracks for one side of the tear (-1 far: back layer, +1 near: front layer)."""
    out = {}
    if grow <= 0 or not shape:
        return out
    xs = sorted(shape)
    table = FAR_CRACKS if side < 0 else NEAR_CRACKS
    for (u, ang, ln, jag) in table:
        x = int(round(P.CX + u * w * 0.9))
        x = min(max(x, xs[0]), xs[-1])
        yt, yb = shape[x]
        start = (x, yt - 1) if side < 0 else (x, yb + 1)
        for q, k in _crack_pixels(start, ang, ln * P.ws ** 0.5, jag, grow, heat):
            out[q] = k
    if side < 0:
        for (u, ang, ln, jag) in END_CRACKS:
            x = xs[0] if u < 0 else xs[-1]
            yt, yb = shape[x]
            for q, k in _crack_pixels((x + (-1 if u < 0 else 1), (yt + yb) // 2), ang, ln * P.ws ** 0.5, jag, grow,
                                      heat):
                out[q] = k
    return out


# ------------------------------------------------------------------ particles
# A clock is {emitter: [ages]}: every emitter can have a few particles in the air at once.

SMOKE_LIFE = 4
# (x offset in half-widths, outward drift per frame, rise per frame, start radius)
# The smoke stays low (about 20 texels over the far rim at most): in the fight the rifts open in
# front of his hips, and higher smoke would cloud his core.
SMOKE_EMITTERS = [(-0.78, -1.2, 4.0, 4.4), (0.05, 0.2, 4.5, 4.0), (0.80, 1.2, 4.0, 4.6),
                  (-0.95, -0.8, 4.5, 3.6), (0.62, 0.9, 4.2, 3.8), (-0.45, -1.0, 3.6, 3.4)]
EMBER_LIFE = ('Y', 'O', 'r', 'T', 'R')
# (x offset in half-widths, drift per frame, rise per frame, phase)
EMBER_EMITTERS = [(-0.60, -0.8, 8.0, 0), (-0.22, 0.5, 10.0, 1), (0.15, -0.4, 11.0, 2), (0.48, 0.6, 9.0, 3),
                  (0.82, 1.0, 7.0, 4), (-0.84, -1.1, 7.5, 5), (0.33, -0.6, 10.5, 6), (-0.40, 0.7, 9.0, 7),
                  (0.00, 0.2, 12.0, 8), (0.66, 0.3, 8.5, 9), (-0.05, -0.3, 9.5, 10), (-0.66, 0.4, 8.0, 11),
                  (-0.92, -0.5, 6.5, 12), (0.92, 0.6, 6.0, 13), (0.24, 0.9, 12.5, 14), (-0.30, -0.9, 11.5, 15),
                  (0.58, -0.2, 10.0, 16), (-0.52, 0.2, 9.5, 17)]


def loop_clock(j, n, period, life):
    """Frame j of a seamless `period`-frame loop: each emitter fires once a period, emitter e
    offset by e; particles live `life` frames, so up to ceil(life / period) per emitter."""
    out = {}
    for e in range(n):
        a0 = (j + e) % period
        ages = [a0 + period * m for m in range(life) if a0 + period * m < life]
        if ages:
            out[e] = ages
    return out


def aged(clock, extra, life):
    out = {}
    for e, ages in clock.items():
        keep = [a + extra for a in ages if a + extra < life]
        if keep:
            out[e] = keep
    return out


def puff(cx, cy, r, age, seed=0):
    """A billow of smoke: a lumpy dome of small discs, its top edge dithered soft, lit only on its
    upper-left cap, underlit by the fire while young; at its last age it is gone.
    Returns {pixel: key}."""
    rnd = random.Random(seed * 7 + 3)
    discs = [(cx, cy, r)]
    for i in range(4):
        a = math.pi + (i + 0.5) / 4.0 * math.pi                  # round the top half
        d = r * 0.6
        discs.append((cx + math.cos(a) * d * 1.3, cy + math.sin(a) * d * 0.75, r * rnd.uniform(0.42, 0.62)))
    discs.append((cx - r * 0.8, cy + r * 0.3, r * 0.55))
    discs.append((cx + r * 0.8, cy + r * 0.3, r * 0.55))
    mask = set()
    for (x0, y0, rr) in discs:
        mask |= B.ellipse(x0, y0, max(rr, 0.8), max(rr * 0.8, 0.8))
    edge = B.edge(mask)
    out = {}
    for (x, y) in mask:
        up = (y - cy) / max(r, 1.0)
        lx = (x - cx) / max(r, 1.0)
        chk = (x + y) % 2
        if age >= SMOKE_LIFE - 1:
            continue                                  # gone: no checkered ghost over whatever is behind
        if (x, y) in edge and chk and (age >= 1 or up < -0.2):
            continue                                  # a soft, dithered edge
        if (x, y + 1) not in mask and age <= 1:
            k = 'R' if age == 0 else 'V'              # the underside, lit by the fire
        elif age == 0 and up > 0.1:
            k = 'v'                                   # young smoke still glows red underneath
        elif up < -0.5 and lx < 0.15:
            k = '4'                                   # the lit cap
        elif up > 0.35 or lx > 0.55:
            k = '2'
        else:
            k = '3'
        out[(x, y)] = k
    return out


def smoke(P, clock, w, top_y, front=False):
    """Smoke for one frame. front=False: the billows rising behind the puppet; front=True: small
    curls at the two ends of the tear (they go in front, never over the middle)."""
    out = {}
    items = [(e, a) for e, ages in clock.items() for a in ages]
    items.sort(key=lambda ea: -ea[1])                 # the oldest (highest) first, the young over them
    for e, age in items:
        ex, drift, rise, r0 = SMOKE_EMITTERS[e]
        if front:
            if abs(ex) < 0.5 or age > 1:
                continue
            x = P.CX + math.copysign(w * 0.92, ex) + drift * age * 0.6
            y = P.CY - 1 - 2.0 * age
            r = (2.2 + 1.0 * age) * P.hs
        else:
            x = P.CX + ex * w * 0.8 + drift * age * (1.0 + abs(ex))
            y = top_y - 2 - rise * age * P.hs - 0.4 * rise * age * age / 3.0
            r = (r0 + 2.0 * age) * P.hs
        for q, k in puff(x, y, r, age, seed=e).items():
            if 0 <= q[0] < P.W and 0 <= q[1] < P.H:
                out[q] = k
    return out


def embers(P, clock, w, base_y, front):
    out = {}
    for e, ages in clock.items():
        ex, drift, rise, idx = EMBER_EMITTERS[e]
        if (idx % 2 == 0) != front:
            continue
        for age in ages:
            if age >= len(EMBER_LIFE):
                continue
            x = int(round(P.CX + ex * w * 0.9 + drift * age + math.sin(age * 1.7 + idx) * 1.2))
            y = int(round(base_y - 2 - rise * age * P.hs))
            if 0 <= x < P.W and 0 <= y < P.H:
                out[(x, y)] = EMBER_LIFE[age]
                if age <= 1 and 0 <= y + 1 < P.H:
                    out[(x, y + 1)] = 'R' if age == 0 else 'V'      # a short trail
    return out


# ------------------------------------------------------------------ glow (added)

def glow_rings(P, shape, g):
    """The aura's recipe round the tear: 2 texels of x, 2 of y, 2 of a z checker; above the far
    rim the haze climbs higher over the middle, so a rising puppet's legs catch it."""
    hole = set()
    for x, (yt, yb) in shape.items():
        for y in range(yt - 1, yb + 2):
            hole.add((x, y))
    if not hole or g <= 0:
        return {}
    out = {}
    seen = set(hole)
    frontier = set(hole)
    widths = [('x', max(1, int(round(2 * g)))), ('y', max(1, int(round(2 * g)))), ('z', 2)]
    for key, n in widths:
        for _ in range(n):
            nxt = set()
            for p in frontier:
                for q in B.neighbours8(p):
                    if q not in seen:
                        nxt.add(q)
            for q in nxt:
                if key == 'z' and (q[0] + q[1]) % 2:
                    continue
                out[q] = key
            seen |= nxt
            frontier = nxt
    xs = sorted(shape)
    w = (xs[-1] - xs[0]) / 2.0 or 1.0
    for x, (yt, yb) in shape.items():
        dxn = abs(x - P.CX) / w
        tall = (1.0 - dxn * dxn) * 10.0 * g * P.hs
        for dy in range(1, int(tall) + 1):
            q = (x, yt - 1 - dy)
            if q in hole:
                continue
            t = dy / max(1.0, tall)
            chk = (q[0] + q[1]) % 2 == 0
            # bands meet in a checker, so no flat stripe crosses a rising puppet
            if t < 0.25:
                k = 'x'
            elif t < 0.4:
                k = 'x' if chk else 'y'
            elif t < 0.6:
                k = 'y'
            elif t < 0.75:
                k = 'y' if chk else 'z'
            else:
                k = 'z' if chk else None
            if k and (q not in out or 'xyz'.index(k) < 'xyz'.index(out[q])):
                out[q] = k
    return {q: k for q, k in out.items() if 0 <= q[0] < P.W and 0 <= q[1] < P.H}


# ------------------------------------------------------------------ one frame

def frame(spec, P=STD):
    """spec: dict(w, h, heat, crack, glow, smoke clock, embers clock, surface, flash), sized for
    STD (the profile scales w and h). Returns (back, front, glow) as {pixel: key} dicts."""
    w, h, heat = spec['w'] * P.ws, spec['h'] * P.hs, spec['heat']
    shape = lens(P, w, h)
    back, front = {}, {}
    top_y = min((v[0] for v in shape.values()), default=P.CY)

    back.update(smoke(P, spec.get('smoke', {}), w, top_y))
    back.update(cracks(P, shape, w, spec['crack'], heat, -1))
    for x, (yt, yb) in shape.items():
        dx = (x - P.CX) / w
        rim_h = heat * (1.0 - 0.55 * dx * dx) + HOT[x % len(HOT)]
        if yt == yb:
            back[(x, yt)] = heat_key(min(1.0, rim_h + 0.08))      # a crack: one burning row
            continue
        depth = yb - yt - 1
        for y in range(yt + 1, yb):                                 # the far wall, lit from below
            t = (y - yt) / float(max(1, depth))
            back[(x, y)] = 'V' if t < 0.22 else 'v' if t < 0.40 else '1' if t < 0.55 else 'k'
        back[(x, yt)] = heat_key(rim_h)                             # the far rim, burning
        if back.get((x, yt - 1)) in (None, '2', '3', '4'):
            back[(x, yt - 1)] = heat_key(rim_h * 0.45)              # and its cooler outer lip
        front[(x, yb)] = heat_key(rim_h * 0.78)                     # the near rim, lit from inside
        front[(x, yb + 1)] = 'v' if rim_h > 0.3 else 'k'
    if spec.get('surface') and h >= 0.5:
        # the surface of the dark on the anchor row: dim blood red with a few live flecks
        for x, (yt, yb) in shape.items():
            if yb - yt < 2:
                continue
            j = _smooth(JAG_BOT[:144], x * 3)
            k = 'T' if j > 0.8 else 'R' if j > 0.5 else 'V'
            front[(x, P.CY)] = k
            if j > 0.66:
                front[(x, P.CY - 1)] = 'V'
    if spec.get('flash'):
        for x, (yt, yb) in shape.items():                          # the slam: a white-hot seam
            front[(x, P.CY)] = 'Y' if abs(x - P.CX) < w * 0.6 else 'O'
            front[(x, P.CY - 1)] = 'O' if abs(x - P.CX) < w * 0.35 else 'r'
    front.update(cracks(P, shape, w, spec['crack'], heat * 0.9, 1))
    front.update(smoke(P, spec.get('smoke', {}), w, top_y, front=True))
    ec = spec.get('embers', {})
    back.update(embers(P, ec, w, top_y, front=False))
    front.update(embers(P, ec, w, top_y, front=True))
    glow = glow_rings(P, shape, spec.get('glow', 0))
    clip = lambda d: {q: k for q, k in d.items() if 0 <= q[0] < P.W and 0 <= q[1] < P.H}  # noqa: E731
    return clip(back), clip(front), glow


# ------------------------------------------------------------------ the two sequences

NS, NE = len(SMOKE_EMITTERS), len(EMBER_EMITTERS)
BOIL = 3          # the open state loops over 3 frames


def summon_specs():
    """8 frames: crack, split, open, boil x3 (a seamless loop), close, seal."""
    boil = [loop_clock(j, NS, BOIL, SMOKE_LIFE) for j in range(BOIL)]
    boil_e = [loop_clock(j, NE, BOIL, len(EMBER_LIFE)) for j in range(BOIL)]
    specs = [
        dict(name='crack', w=30, h=0, heat=1.0, crack=0.0, glow=0.35, embers={0: [0], 3: [0]}),
        dict(name='split', w=42, h=3.5, heat=1.0, crack=0.45, glow=0.6, surface=True,
             embers={0: [1], 3: [1], 1: [0], 4: [0], 6: [0]}, smoke={1: [0]}),
        dict(name='open', w=48, h=11, heat=1.0, crack=1.0, glow=1.0, surface=True,
             embers={1: [1], 4: [1], 6: [1], 2: [0], 5: [0], 7: [0], 8: [0], 9: [0]}, smoke={1: [1], 0: [0], 2: [0]}),
    ]
    for j in range(BOIL):
        specs.append(dict(name='boil%d' % (j + 1), w=48, h=11, heat=0.95 + 0.05 * (j == 1), crack=1.0, glow=1.0,
                          surface=True, smoke=boil[j], embers=boil_e[j], loop=True))
    specs.append(dict(name='close', w=44, h=4, heat=1.0, crack=0.8, glow=0.6, surface=True,
                      smoke=aged(boil[-1], 1, SMOKE_LIFE), embers=aged(boil_e[-1], 1, len(EMBER_LIFE))))
    specs.append(dict(name='seal', w=36, h=0, heat=0.45, crack=0.35, glow=0.25,
                      smoke=aged(boil[-1], 2, SMOKE_LIFE), embers=aged(boil_e[-1], 2, len(EMBER_LIFE))))
    return specs


SUMMON_TIMES = [0.08, 0.08, 0.10, 0.10, 0.10, 0.10, 0.08, 0.12]
SUMMON_LOOP = (3, 5)          # frames 3-5 loop seamlessly while the puppet rises


def despawn_specs():
    """6 frames: crack under the feet, gape, swallow x2 (a seamless loop), slam shut, scar."""
    sw = [loop_clock(j, NS, 2, SMOKE_LIFE) for j in range(2)]
    sw_e = [loop_clock(j, NE, 2, len(EMBER_LIFE)) for j in range(2)]
    burst = {e: [1] for e in range(NS)}
    specs = [
        dict(name='crack', w=34, h=0, heat=1.0, crack=0.3, glow=0.4, embers={0: [0], 5: [0]}),
        dict(name='gape', w=48, h=11, heat=1.0, crack=1.0, glow=1.0, surface=True,
             embers={0: [1], 5: [1], 2: [0], 7: [0], 9: [0]}, smoke={1: [0], 3: [0]}),
    ]
    for j in range(2):
        specs.append(dict(name='swallow%d' % (j + 1), w=48, h=11, heat=0.95, crack=1.0, glow=1.0, surface=True,
                          smoke=sw[j], embers=sw_e[j], loop=True))
    specs.append(dict(name='slam', w=50, h=1.5, heat=1.0, crack=1.0, glow=0.9, flash=True,
                      embers={e: [0] for e in range(NE)}, smoke=burst))
    specs.append(dict(name='scar', w=38, h=0, heat=0.4, crack=0.5, glow=0.2,
                      embers={e: [2] for e in range(NE)}, smoke=aged(burst, 1, SMOKE_LIFE)))
    return specs


DESPAWN_TIMES = [0.06, 0.08, 0.12, 0.12, 0.08, 0.14]
DESPAWN_LOOP = (2, 3)
SEQS = {'summon': (summon_specs, SUMMON_TIMES, SUMMON_LOOP), 'despawn': (despawn_specs, DESPAWN_TIMES, DESPAWN_LOOP)}


def images(specs, P=STD):
    """(back strip, front strip, glow strip) as RGBA images, P.W x P.H per frame."""
    from PIL import Image
    n = len(specs)
    out = [Image.new('RGBA', (P.W * n, P.H), (0, 0, 0, 0)) for _ in range(3)]
    for i, spec in enumerate(specs):
        b, f, g = frame(spec, P)
        out[0].alpha_composite(B.image(b, P.W, P.H, PAL), (i * P.W, 0))
        out[1].alpha_composite(B.image(f, P.W, P.H, PAL), (i * P.W, 0))
        out[2].alpha_composite(B.image(g, P.W, P.H, GLOW_PAL), (i * P.W, 0))
    return out
