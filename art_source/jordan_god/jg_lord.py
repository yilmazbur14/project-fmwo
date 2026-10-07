"""Demon-god Jordan, the user's reference direction (2026-09-28): a tall, slender demon lord in
black obsidian armour, front-facing and symmetrical, huge jagged bat wings, a crown of flame-horns
(his quiff, burning), lava cracks, a white-hot core in the chest, long clawed hands, long thin legs
and a thick segmented tail curling below. Two variants: A1 shows Jordan's face; A2 is a full mask.

Frame 320x224 (the contract's 224x224, grown by three 32-texel steps for the wings). Mirror axis
between columns 159 and 160 (x' = 319 - x). His lowest texel sits on row 223; the anchor is
(160, 223). Built back to front on a keylined canvas; effects (core glow) carry no keyline.

build(variant, pose) draws him at a Pose (wing breath, crown flicker, crack and core pulse, tail
sway, the tail's lava seam, the open mouth, embers). The default Pose is the approved still,
pixel for pixel; jg_god drives the shipped hover, talk and aura frames through it.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402
import jg_body as Y  # noqa: E402
import jg_parts as P  # noqa: E402
from jg_lord_pal import LAVA, LEATHER, OBS, PAL_A1, PAL_A2  # noqa: E402

W, H = 320, 224
AX = 319            # mirror: x' = AX - x
ANCHOR = (160, 223)
CORE = (159.5, 124)

OBS_KEYS = set('12345')
LEATHER_KEYS = set('mnM')


class Pose:
    """Everything that moves. The defaults are the approved still (the approval pass)."""

    def __init__(self, wing_lift=0.0, wing_spread=0.0, flame=None, glow=1.0, core=1.0, tail_sway=0.0,
                 tail_seam=False, mouth_open=False, embers=()):
        self.wing_lift = wing_lift        # texels the wing's wrist rises (negative = up)
        self.wing_spread = wing_spread    # radians the finger fan opens (+) or folds (-)
        self.flame = flame                # crown flicker phase (None = the approved still)
        self.glow = glow                  # lava crack heat multiplier
        self.core = core                  # core star scale
        self.tail_sway = tail_sway        # texels the tail's lower loop swings sideways
        self.tail_seam = tail_seam        # a lava seam along the tail (reads in the void)
        self.mouth_open = mouth_open      # A2 talk: the furnace grin opens
        self.embers = embers              # [(x, y, key)] effect specks, drawn last


STILL = Pose()


def mir(part):
    return {(AX - x, y): k for (x, y), k in part.items()}


def mp(p):
    return (AX - p[0], p[1])


def obsidian(mask, radius=None, cuts=(0.24, 0.44, 0.64, 0.86), bias=0.0, light=B.LIGHT):
    return B.shade(set(mask), OBS, radius=radius, cuts=list(cuts), bias=bias, light=light)


def obs_tube(pts, radii, cuts=(0.22, 0.42, 0.64, 0.87), bias=0.0):
    return Y.limb(pts, radii, OBS, cuts=list(cuts), bias=bias)


def spike_mask(base, direction, length, width, bend=0.0):
    """A sharp tapering spike from `base` pointing along `direction` (radians), optionally hooked."""
    dx, dy = math.cos(direction), math.sin(direction)
    nx, ny = -dy, dx
    tip = (base[0] + dx * length + nx * bend, base[1] + dy * length + ny * bend)
    mid = (base[0] + dx * length * 0.5 + nx * bend * 0.35, base[1] + dy * length * 0.5 + ny * bend * 0.35)
    pts = [(base[0] + nx * width, base[1] + ny * width), (mid[0] + nx * width * 0.55, mid[1] + ny * width * 0.55),
           tip, (mid[0] - nx * width * 0.55, mid[1] - ny * width * 0.55), (base[0] - nx * width, base[1] - ny * width)]
    return B.poly(pts)


def spike(base, direction, length, width, bend=0.0, radius=2.2):
    return obsidian(spike_mask(base, direction, length, width, bend), radius=radius)


def both(C, part, relight=True, radius=None, outline=True):
    """Stamp a left-side part and its mirror. With relight, the mirrored copy is re-shaded so both
    sides take the light from the upper left (obsidian parts only)."""
    C.stamp(part, outline=outline)
    m = mir(part)
    if relight and all(k in OBS_KEYS for k in m.values()):
        m = obsidian(set(m), radius=radius)
    C.stamp(m, outline=outline)


def top_edge(part, key='5', only=OBS_KEYS, side_bias=None):
    """Recolour a plate's top-edge texels (the ones with nothing of the part above them) to `key`:
    the hard highlight that separates stacked armour plates."""
    out = dict(part)
    for (x, y), k in part.items():
        if k in only and (x, y - 1) not in part:
            if side_bias is None or (x < 159.5) == (side_bias < 0):
                out[(x, y)] = key
    return out


def crack_path(p0, p1, rnd, jag=1.4, step=3.0):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1.0
    n = max(1, int(ln / step))
    nx, ny = -dy / ln, dx / ln
    pts = [p0]
    for i in range(1, n):
        t = i / n
        j = rnd.uniform(-jag, jag)
        pts.append((p0[0] + dx * t + nx * j, p0[1] + dy * t + ny * j))
    pts.append(p1)
    return pts


GLOW = [1.0]      # the current pose's crack heat (set by build)


def draw_crack(C, pts, hot0=0.9, hot1=0.1, only=OBS_KEYS):
    """A glowing crack; heat runs from hot0 at its start to hot1 at its end."""
    path = B.polyline([(int(round(x)), int(round(y))) for x, y in pts])
    n = len(path)
    for i, q in enumerate(path):
        if q not in C.px or (only is not None and C.px[q] not in only):
            continue
        t = i / max(1, n - 1)
        heat = (hot0 + (hot1 - hot0) * t) * GLOW[0]
        C.px[q] = 'V' if heat < 0.22 else 'R' if heat < 0.45 else 'T' if heat < 0.7 else 'r' if heat < 0.9 else 'O'


# ------------------------------------------------------------------ wings

def wing_geom(pose=STILL):
    root = (150, 114)
    elbow = (117, 88)
    wrist = (92, 58)
    tips = [(57, 39), (17, 64), (9, 109), (27, 149), (67, 165)]
    inner = (112, 134)
    if pose.wing_lift or pose.wing_spread:
        lift = pose.wing_lift
        elbow = (elbow[0], elbow[1] + lift * 0.5)
        wrist = (wrist[0], wrist[1] + lift)
        angs = [math.atan2(t[1] - 58, t[0] - 92) for t in tips]
        mid = sum(angs[1:4]) / 3.0
        new = []
        for t, a in zip(tips, angs):
            r = math.hypot(t[0] - 92, t[1] - 58)
            a2 = mid + (a - mid) * (1.0 + pose.wing_spread)
            new.append((wrist[0] + math.cos(a2) * r, wrist[1] + math.sin(a2) * r))
        tips = new
        inner = (inner[0], inner[1] + lift * 0.3)
    return root, elbow, wrist, tips, inner


def _jagged(a, b, toward, pull, teeth, depth, rnd):
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    c = (mx + (toward[0] - mx) * pull, my + (toward[1] - my) * pull)
    curve = B.bezier(a, c, b, n=teeth * 2)
    out = [curve[0]]
    for i in range(1, len(curve) - 1):
        x, y = curve[i]
        if i % 2 == 1:
            vx, vy = toward[0] - x, toward[1] - y
            ln = math.hypot(vx, vy) or 1
            d = depth * rnd.uniform(0.75, 1.25)
            out.append((x + vx / ln * d, y + vy / ln * d))
        else:
            out.append((x, y))
    out.append(curve[-1])
    return out


def _wrap(d):
    while d > math.pi:
        d -= 2 * math.pi
    while d <= -math.pi:
        d += 2 * math.pi
    return d


def wing_left(pose=STILL):
    root, elbow, wrist, tips, inner = wing_geom(pose)
    rnd = random.Random(9)
    outline = [root, elbow, wrist, tips[0]]
    for a, b in zip(tips, tips[1:]):
        outline += _jagged(a, b, wrist, 0.24, 6, 7.0, rnd)[1:]
    outline += _jagged(tips[-1], inner, wrist, 0.14, 5, 5.5, rnd)[1:]
    outline += [(inner[0] + 6, inner[1] - 14), (root[0] - 10, root[1] + 2)]
    membrane = B.poly(outline)
    raw = [math.atan2(t[1] - wrist[1], t[0] - wrist[0]) for t in tips]
    raw.append(math.atan2(inner[1] - wrist[1], inner[0] - wrist[0]))
    bounds = [raw[0]]
    for r_ in raw[1:]:
        bounds.append(bounds[-1] + _wrap(r_ - bounds[-1]))
    part = {}
    for (x, y) in membrane:
        a = bounds[0] + _wrap(math.atan2(y - wrist[1], x - wrist[0]) - bounds[0])
        r = math.hypot(x - wrist[0], y - wrist[1])
        tone = 'm'
        for i in range(len(bounds) - 1):
            a0, a1 = bounds[i], bounds[i + 1]
            if min(a0, a1) <= a <= max(a0, a1):
                t = (a - a0) / (a1 - a0) if a1 != a0 else 0.0
                j = min(i, len(tips) - 1)
                reach = math.hypot(tips[j][0] - wrist[0], tips[j][1] - wrist[1])
                rr = r / max(1.0, reach)
                if t < 0.10 + 0.14 * (1 - rr) and rr < 0.92:
                    tone = 'M'
                elif t < 0.34 + 0.30 * (1 - rr) and rr < 0.88:
                    tone = 'n'
                elif rr < 0.97:
                    tone = 'm'
                else:
                    tone = 'k'
                break
        part[(x, y)] = tone
    # tears in the leather
    for (tx, ty, ln, wd) in ((31, 97, 9, 2.3), (49, 128, 8, 2.1), (77, 145, 6, 1.9)):
        if pose.wing_lift or pose.wing_spread:
            # the tears ride the leather: carried with the fan around the (moved) wrist
            a0_ = math.atan2(ty - 58, tx - 92)
            r0_ = math.hypot(tx - 92, ty - 58)
            angs0 = [math.atan2(t[1] - 58, t[0] - 92) for t in wing_geom()[3]]
            mid0 = sum(angs0[1:4]) / 3.0
            a1_ = mid0 + (a0_ - mid0) * (1.0 + pose.wing_spread)
            tx, ty = wrist[0] + math.cos(a1_) * r0_, wrist[1] + math.sin(a1_) * r0_
        ang = math.atan2(ty - wrist[1], tx - wrist[0])
        a = (tx - math.cos(ang) * ln / 2, ty - math.sin(ang) * ln / 2)
        b = (tx + math.cos(ang) * ln / 2, ty + math.sin(ang) * ln / 2)
        for q in B.capsule(a, b, wd, wd * 0.6):
            part.pop(q, None)
    # glowing veins: a thin ember line down each panel near its upper bone
    veins = []
    for i in range(len(bounds) - 1):
        a0, a1 = bounds[i], bounds[i + 1]
        am = a0 + (a1 - a0) * 0.33
        j = min(i, len(tips) - 1)
        reach = math.hypot(tips[j][0] - wrist[0], tips[j][1] - wrist[1])
        p0 = (wrist[0] + math.cos(am) * reach * 0.18, wrist[1] + math.sin(am) * reach * 0.18)
        p1 = (wrist[0] + math.cos(am + 0.05) * reach * 0.62, wrist[1] + math.sin(am + 0.05) * reach * 0.62)
        veins.append((p0, p1))
    return part, (root, elbow, wrist, tips, inner), veins


def wing_bones_left(geom):
    root, elbow, wrist, tips, inner = geom
    parts = [obs_tube([root, ((root[0] + elbow[0]) / 2.0, (root[1] + elbow[1]) / 2.0 - 1), elbow, wrist],
                      [4.6, 4.0, 3.4, 2.8])]
    for t, (r0, r1) in zip(tips, [(2.3, 0.8), (2.3, 0.8), (2.1, 0.7), (1.9, 0.7), (1.7, 0.7)]):
        mid = ((wrist[0] + t[0]) / 2.0, (wrist[1] + t[1]) / 2.0 - 2.0)
        parts.append(obs_tube([wrist, mid, t], [r0, (r0 + r1) / 2.0, r1], cuts=(0.14, 0.32, 0.56, 0.80)))
    claws = [spike((wrist[0] + 1, wrist[1] - 2), math.radians(-112), 15, 2.8, bend=-3.0),
             spike((elbow[0] - 1, elbow[1] - 2), math.radians(-140), 10, 2.3, bend=-2.0)]
    # a hooked talon on every finger tip, continuing the bone
    for t in tips:
        ang = math.atan2(t[1] - wrist[1], t[0] - wrist[0])
        claws.append(spike((t[0] - math.cos(ang) * 1.5, t[1] - math.sin(ang) * 1.5), ang, 6, 1.4, bend=1.5,
                           radius=1.5))
    return parts, claws


# ------------------------------------------------------------------ crown

def flame_horn(base, ctrl, radius, sway=0.0, heat=0.0):
    """A flame-like horn: a tapering curve from `base` through `ctrl` points; obsidian at the root,
    heating through the lava ramp to a gold tip. `heat` slides the colour bands up or down the horn
    (the flicker)."""
    pts = Y.smooth_curve([base] + ctrl, n=8)
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg) or 1.0
    acc = [0.0]
    for s in seg:
        acc.append(acc[-1] + s)
    rr = [radius * (1 - a / total) ** 0.9 + 0.35 + 0.45 * math.sin(a / 2.3 + sway) * (a / total) for a in acc]
    mask = B.ribbon(pts, rr) | B.ellipse(base[0], base[1], radius, radius)
    L = B._norm(B.LIGHT)
    out = {}
    for p in mask:
        i, t, s, (nx, ny) = B._closest_on_polyline(p, pts)
        u = (acc[i] + seg[i] * t) / total
        r = rr[i] + (rr[i + 1] - rr[i]) * t
        v = max(-1.0, min(1.0, s / (r + 0.35)))
        nz = math.sqrt(max(0.0, 1 - v * v))
        I = nx * v * L[0] + ny * v * L[1] + nz * L[2]
        if u < 0.34:
            k = OBS[max(0, min(4, int(I * 4.4 - 0.5)))]
        else:
            h = (u - 0.34) / 0.66 + (I - 0.6) * 0.35 + heat
            k = 'V' if h < 0.18 else 'R' if h < 0.38 else 'T' if h < 0.58 else 'r' if h < 0.8 else 'O'
        out[p] = k
    return out


CROWN = [
    # (base, control points, radius, mirrored?) ; the last is the quiff
    ((147, 86), [(140, 80), (134, 75), (131, 69)], 2.6, True),
    ((151, 83), [(147, 74), (143, 65), (142, 59)], 3.0, True),
    ((155, 82), [(153, 73), (151, 64), (151, 57)], 3.2, False),
    ((163, 81), [(164, 72), (166, 62), (170, 53), (176, 49)], 3.9, False),
]


def crown_horns(pose=STILL):
    """(back row, front row) of flame-horns rising out of his hair. The tallest sweeps up and
    flicks right, the way his quiff does. With a flame phase each horn's tip licks up to a texel
    sideways and its heat bands slide, each horn on its own beat."""
    def horn(i, side):
        base, ctrl, rad, _ = CROWN[i]
        if pose.flame is None:
            h = flame_horn(base, ctrl, rad)
            return mir(h) if side else h
        ph = pose.flame + i * 1.7 + side * 2.3
        lick = math.sin(ph)
        n = len(ctrl)
        c2 = [(x + lick * (j + 1) / n, y) for j, (x, y) in enumerate(ctrl)]
        b2 = base
        if side:
            b2 = mp(base)
            c2 = [mp(q) for q in c2]
        return flame_horn(b2, c2, rad, sway=ph * 0.5, heat=0.07 * math.sin(ph + 0.8))

    back = [horn(0, 0), horn(1, 0), horn(0, 1), horn(1, 1)]
    front = [horn(2, 0), horn(3, 0)]
    return back, front


def frontal_face():
    """Jordan's v2 shout head turned frontal: his near side mirrored about the nose."""
    head = P.head_1x(True)
    half = {p: k for p, k in head.items() if p[0] <= 53}
    face = dict(half)
    for (x, y), k in half.items():
        face[(107 - x, y)] = k
    return B.shift(face, 106, 69)


HAIR_KEYS = set('hijlmAYW')
HAIR_TO_OBS = {'h': '1', 'i': '2', 'j': '3', 'l': '4', 'm': '5', 'A': '5', 'Y': 'O', 'W': 'r', 'k': 'k'}
HAIRLINE = 91       # rows at or above this are hair; below it his brows, face and beard


def hair_crown():
    """His own greasy hair, clump for clump, turned to obsidian; its oily shine and the dandruff
    become embers (he is burning from the scalp up)."""
    out = {}
    for (x, y), k in frontal_face().items():
        if y <= HAIRLINE and (k in HAIR_KEYS or k == 'k'):
            out[(x, y)] = HAIR_TO_OBS.get(k, k)
    return out


SKIN_A1 = {'e': 'd', 'd': 'c', 'c': 'b', 'b': 'a', 'a': 'a'}


def face_a1():
    """Jordan's own face below the hairline, a step into shadow: eyes burning, the mouth a
    furnace, beard strands smouldering, pale obsidian fangs."""
    out = {}
    for (x, y), k in frontal_face().items():
        if y <= HAIRLINE and (k in HAIR_KEYS or k == 'k'):
            continue
        if k in SKIN_A1:
            k = SKIN_A1[k]
        elif k == 'p':
            k = 'V'
        elif k in ('j', 'l', 'm', 'A'):
            k = 'i' if (x * 3 + y) % 4 else 'V'
        elif k == 'W':
            k = '5'
        out[(x, y)] = k
    # the crown's shadow across the brow line
    for (x, y), k in list(out.items()):
        if y <= 92 and k in ('d', 'c'):
            out[(x, y)] = 'b' if k == 'c' else 'c'
    # burning eyes
    for x, k in ((151, 'R'), (152, 'O'), (153, 'Y'), (154, 'w'), (155, 'Y'), (156, 'O')):
        out[(x, 96)] = k
        out[(AX - x, 96)] = k
    for x in range(152, 157):
        out[(x, 97)] = 'R' if x in (152, 156) else 'T'
        out[(AX - x, 97)] = out[(x, 97)]
    # the maw glows
    for (x, y), k in list(out.items()):
        if y == 102 and 155 <= x <= 164 and k in ('a', 'V'):
            out[(x, y)] = 'r' if 157 <= x <= 162 else 'R'
    for q in ((156, 102), (163, 102)):
        out[q] = '5'
    return out


def face_mask(mouth_open=False):
    """A2: a full obsidian mask cut to the shape of his face, sculpted in planes: a widow's-peak
    groove down the forehead, his heavy brows as a brow plate slanting down in anger, burning
    almond eyes deep in black sockets, cheekbone ridges over hollow cheeks, a narrow nose ridge,
    a fanged furnace grin, and his patchy beard as glowing cracks along the jaw (moustache
    halves that never meet, gaps at the jaw corners, a fuller chin). Built on the left half and
    mirrored, then re-lit from the upper left."""
    f = frontal_face()
    region = {p for p, k in f.items() if not (p[1] <= HAIRLINE and (k in HAIR_KEYS or k == 'k'))}
    inner = {p for p in region if f[p] != 'k'}
    out = {p: 'k' for p in region}
    out.update(obsidian(inner, radius=6, cuts=(0.20, 0.40, 0.62, 0.86)))

    def put(x, y, k, both_sides=True, mirror_key=None):
        if (x, y) in out:
            out[(x, y)] = k
        if both_sides and (AX - x, y) in out:
            out[(AX - x, y)] = mirror_key or k

    # widow's-peak groove down the forehead
    for y in range(89, 93):
        put(159, y, 'k', both_sides=False)
    put(159, 92, '3', both_sides=False)
    # the brow plate: slanting down to the nose; lit top edge, black shelf beneath
    for x in range(146, 160):
        c = 159.5 - x
        y0 = 92 + (0 if c > 10 else 1 if c > 5 else 2)
        put(x, y0 - 1, '5' if x < 157 else '4', mirror_key='4')
        put(x, y0, '4', mirror_key='3')
        put(x, y0 + 1, 'k')
    # eye sockets and the burning almond eyes
    for x in range(148, 158):
        c = 159.5 - x
        ys = 95 + (0 if c > 8 else 1 if c > 4 else 2)
        put(x, ys, 'k')
        put(x, ys + 1, 'k')
    eye = {(149, 96): 'R', (150, 96): 'O', (151, 96): 'Y', (152, 96): 'Y', (153, 97): 'w', (154, 97): 'Y',
           (155, 97): 'O', (156, 98): 'R', (151, 97): 'R', (152, 97): 'T', (150, 97): 'k'}
    for (x, y), k in eye.items():
        put(x, y, k)
    # cheekbone ridges over hollow cheeks
    for x, y in ((147, 99), (148, 99), (149, 100), (150, 100), (151, 100)):
        put(x, y, '5', mirror_key='4')
    for x, y in ((148, 101), (149, 102), (150, 102), (151, 101)):
        put(x, y, 'k')
    # nose ridge, nostrils
    for y in range(96, 101):
        put(159, y, '5', mirror_key='3')
    put(158, 101, 'k')
    put(157, 101, 'k')
    # the grin: a wide furnace slit, fangs top and bottom
    for x in range(151, 160):
        put(x, 103, 'r' if x >= 155 else 'R')
        put(x, 104, 'O' if x >= 157 else 'r' if x >= 153 else 'R')
        put(x, 102, 'k' if x < 152 else '4', mirror_key='3')
    for x in (152, 155, 158):
        put(x, 103, '5', mirror_key='4')
    for x in (153, 156):
        put(x, 104, '5', mirror_key='4')
    put(151, 104, 'k')
    for x in range(151, 160):
        put(x, 105, 'k')
    if mouth_open:
        # the jaw drops two rows: the furnace behind the fangs flares white-hot
        for x in range(151, 160):
            put(x, 104, 'Y' if x >= 156 else 'O' if x >= 153 else 'r')
            put(x, 105, 'w' if x >= 157 else 'Y' if x >= 154 else 'O' if x >= 152 else 'R')
            put(x, 106, 'O' if x >= 155 else 'r' if x >= 153 else 'R')
            put(x, 107, 'k')
        for x in (152, 155, 158):
            put(x, 103, '5', mirror_key='4')
            put(x, 104, '5', mirror_key='4')
        for x in (153, 156, 159):
            put(x, 106, '5', mirror_key='4')
        put(151, 105, 'k')
        put(151, 106, 'k')
    # the beard, burning in the cracks of the jaw
    beard = [
        [(152, 101), (154, 101), (156, 102)],             # moustache half (never meets the other)
        [(146, 98), (147, 102), (149, 105), (152, 107)],  # the jaw line, a gap at the corner
        [(153, 106), (156, 107)],                          # chin patch
        [(158, 106), (159, 108)],                          # the fuller chin
    ]
    for path in beard:
        for q in B.polyline(path):
            if out.get(q, 'k') == 'k' or out.get((AX - q[0], q[1]), 'k') == 'k':
                continue
            k = 'T' if (q[0] + q[1]) % 3 else 'R'
            put(q[0], q[1], k)
    # an ear fin sweeping back from each side
    return out


def lord_hand(wrist, side):
    """A long, thin clawed hand hanging from `wrist` (side -1 = screen-left): a narrow palm,
    four fingers fanned down and out with a gap between each, hooked claws, a thumb turned in."""
    parts = []
    down = math.radians(90 - side * 14)
    px_, py_ = wrist[0] + math.cos(down) * 3.0, wrist[1] + math.sin(down) * 3.0
    parts.append(obsidian(B.ellipse(px_, py_, 3.0, 3.6), radius=3))
    claws = []
    for j, off in enumerate((-0.42, -0.14, 0.14, 0.42)):
        a = down + off * side * -1
        ln = 9.5 if j in (1, 2) else 8.0
        b0 = (px_ + math.cos(a) * 2.6, py_ + math.sin(a) * 2.6)
        k1 = (b0[0] + math.cos(a) * ln * 0.5, b0[1] + math.sin(a) * ln * 0.5)
        a2 = a + side * 0.18
        k2 = (k1[0] + math.cos(a2) * ln * 0.5, k1[1] + math.sin(a2) * ln * 0.5)
        parts.append(obs_tube([b0, k1, k2], [1.2, 1.0, 0.8]))
        a3 = a2 + side * 0.5
        tip = (k2[0] + math.cos(a3) * 5.0, k2[1] + math.sin(a3) * 5.0)
        claws.append(Y.limb([k2, tip], [1.0, 0.3], ('3', '4', '5'), cuts=[0.4, 0.78]))
    ta = down + side * 1.1
    t0 = (px_ + math.cos(ta) * 2.4, py_ + math.sin(ta) * 2.4)
    t1 = (t0[0] + math.cos(ta - side * 0.6) * 5, t0[1] + math.sin(ta - side * 0.6) * 5)
    parts.append(obs_tube([t0, t1], [1.2, 0.9]))
    t2 = (t1[0] + math.cos(ta - side * 1.2) * 3.5, t1[1] + math.sin(ta - side * 1.2) * 3.5)
    claws.append(Y.limb([t1, t2], [0.9, 0.3], ('3', '4', '5'), cuts=[0.4, 0.78]))
    return parts, claws


# ------------------------------------------------------------------ build

def build(variant='A1', pose=None, seat=True):
    """The god, drawn at `pose` (default: the approved still). Returns {pixel: key}. With seat,
    his lowest texel is put on the anchor row (the still is designed to need no shift)."""
    pose = pose or STILL
    GLOW[0] = pose.glow
    C = B.Canvas(W, H + 16)
    rnd = random.Random(5)

    # 1. wings
    lpart, geom, veins = wing_left(pose)
    C.stamp(mir(lpart))
    C.stamp(lpart)
    for (p0, p1) in veins:
        for pts in (crack_path(p0, p1, rnd, jag=1.0), crack_path(mp(p0), mp(p1), rnd, jag=1.0)):
            draw_crack(C, pts, hot0=0.35, hot1=0.05, only=LEATHER_KEYS)
    bones, claws = wing_bones_left(geom)
    for b in bones + claws:
        both(C, b, radius=2.6)

    # 2. tail: from behind the pelvis down the left, round under his feet, curling up the right
    tail_ctrl = [(162, 152), (163, 172), (170, 190), (185, 203), (193, 212), (182, 218), (160, 218.5),
                 (141, 215), (130, 207), (129, 198), (134, 193)]
    if pose.tail_sway:
        # the loop swings sideways, more toward the tip; it never drops
        tail_ctrl = [(x + pose.tail_sway * max(0.0, (i - 2) / 8.0) ** 1.2, y) for i, (x, y) in enumerate(tail_ctrl)]
    tail = Y.smooth_curve(tail_ctrl, n=10)
    radii = Y.taper(len(tail), 6.4, 1.2, power=1.0)
    tpart = obs_tube(tail, radii)
    # segment rings every few texels along its length
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(tail, tail[1:])]
    acc = 0.0
    rings = []
    for i, s in enumerate(seg):
        acc += s
        if acc >= 5.0:
            acc = 0.0
            (x0, y0), (x1, y1) = tail[i], tail[i + 1]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            r = radii[i]
            rings.append([(x1 + nx * r, y1 + ny * r), (x1 - nx * r, y1 - ny * r)])
    C.stamp(tpart)
    for a, b in rings:
        for q in B.line(a[0], a[1], b[0], b[1]):
            if q in tpart:
                C.px[q] = 'k'
    # dorsal spikes along the outside of the curl
    for i in range(12, len(tail) - 12, 9):
        (x0, y0), (x1, y1) = tail[i], tail[i + 1]
        ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
        base = (x1 + math.cos(ang) * radii[i] * 0.8, y1 + math.sin(ang) * radii[i] * 0.8)
        C.stamp(spike(base, ang, 4 + radii[i] * 0.6, 1.6, radius=1.8))
    if pose.tail_seam:
        # a lava seam down the tail, just inside its lower edge, cooling toward the tip: the tail
        # reads hanging in the dark void with no fire under it
        seam = []
        for i in range(18, len(tail) - 14):
            (x0, y0), (x1, y1) = tail[i], tail[i + 1]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            seam.append((x1 - nx * radii[i] * 0.35, y1 - ny * radii[i] * 0.35))
        n_ = len(seam)
        for j in range(0, n_ - 1, 1):
            a, b = seam[j], seam[j + 1]
            for q in B.line(a[0], a[1], b[0], b[1]):
                if C.px.get(q) in OBS_KEYS:
                    t = j / max(1, n_ - 1)
                    heat = (0.62 - 0.5 * t) * pose.glow
                    C.px[q] = 'V' if heat < 0.22 else 'R' if heat < 0.45 else 'T'


    # 3. legs: thigh under a hanging tasset, a spurred knee, a ridged greave, a taloned foot
    hip, knee, ankle, toe = (153, 160), (150, 186), (152, 204), (153, 214)
    thigh = obs_tube([hip, ((hip[0] + knee[0]) / 2.0 - 0.5, (hip[1] + knee[1]) / 2.0), knee], [5.2, 4.6, 3.4])
    shin = obs_tube([knee, ((knee[0] + ankle[0]) / 2.0 - 0.8, (knee[1] + ankle[1]) / 2.0), ankle],
                    [3.4, 3.4, 2.2])
    # the greave's ridge: a hard highlight down the lit side of the shin
    for y in range(189, 203):
        x = int(round(149.4 + (y - 189) * 0.1))
        if (x, y) in shin:
            shin[(x, y)] = '5' if y < 197 else '4'
    foot = obsidian(B.poly([(149, 203), (155, 203), (156, 209), (153.5, 216), (150, 209)]), radius=2.5)
    toes = [spike((150.5, 210), math.radians(118), 5, 1.2, bend=0.8, radius=1.5),
            spike((155.5, 210), math.radians(70), 4, 1.1, bend=-0.6, radius=1.5)]
    tasset = top_edge(obsidian(B.poly([(145, 157), (157, 159), (155, 172), (150, 175), (146, 170)]), radius=4,
                               cuts=(0.24, 0.44, 0.64, 0.86)), '4')
    knee_cop = obsidian(B.ellipse(150, 185.5, 3.4, 3.0), radius=3)
    knee_spur = spike((147.5, 186), math.radians(196), 6, 1.8, bend=-1.0, radius=1.8)
    both(C, thigh)
    both(C, shin)
    for t in toes:
        both(C, t)
    both(C, foot)
    both(C, tasset)
    both(C, knee_spur)
    both(C, knee_cop)
    for (a, b) in (((153, 175), (151.5, 181)),):
        pts = crack_path(a, b, rnd, jag=0.6)
        draw_crack(C, pts, 0.4, 0.1)
        draw_crack(C, [mp(p) for p in pts], 0.4, 0.1)

    # 4. torso: pelvis fauld, abdomen segments, chest plates
    fauld = B.poly([(147, 148), (159.5, 149), (159.5, 166), (153, 160), (146, 156)])
    both(C, obsidian(fauld, radius=4))
    hipspike = spike((147, 153), math.radians(160), 8, 2.2)
    both(C, hipspike)
    for i, (y0, y1, hw0, hw1) in enumerate(((133, 138, 13, 12), (138, 143, 12, 10.5), (143, 149, 10.5, 9))):
        seg_l = B.poly([(159.5 - hw0, y0), (159.5, y0 + 1), (159.5, y1 + 1), (159.5 - hw1, y1)])
        sl = top_edge(obsidian(seg_l, radius=4, cuts=(0.24, 0.44, 0.64, 0.86)), '4')
        C.stamp(sl)
        C.stamp(top_edge(obsidian(set(mir(sl)), radius=4, cuts=(0.24, 0.44, 0.64, 0.86)), '3'))
    for base, ang, ln in (((145, 136), 172, 7), ((147, 142), 165, 6)):
        both(C, spike(base, math.radians(ang), ln, 1.8, bend=1.5, radius=1.8))
    pec = B.poly([(159.5, 112), (153, 109), (146, 111), (142, 118), (144, 127), (150, 133), (159.5, 134)])
    pl = top_edge(obsidian(pec, radius=8, cuts=(0.26, 0.46, 0.66, 0.86)), '5')
    C.stamp(pl)
    C.stamp(top_edge(obsidian(set(mir(pl)), radius=8, cuts=(0.26, 0.46, 0.66, 0.86)), '4'))

    # 5. arms: upper arm, spiked elbow, bladed vambrace, clawed hand
    sh, el, wr = (143, 118), (132, 146), (127, 170)
    upper = obs_tube([sh, ((sh[0] + el[0]) / 2.0, (sh[1] + el[1]) / 2.0), el], [3.8, 3.2, 2.9])
    both(C, upper)
    elbow_spike = spike((131, 147), math.radians(165), 8, 2.3, bend=1.0)
    both(C, elbow_spike)
    vam = obsidian(B.poly([(131, 148), (135, 150), (131, 170), (126, 172), (125, 160)]), radius=3)
    both(C, vam)
    for j, yy in enumerate((153, 159, 165)):
        blade = spike((127.5 - j * 0.6, yy), math.radians(180 + 18), 6 - j, 1.6, bend=1.2, radius=1.6)
        both(C, blade)
    # the hands: long, thin, clawed
    hparts, hclaws = lord_hand((127, 171), -1)
    for hp in hparts + hclaws:
        both(C, hp)
    for a, b in (((129, 151), (128, 167)), ((140, 122), (135, 140))):
        pts = crack_path(a, b, rnd, jag=0.7)
        draw_crack(C, pts, 0.5, 0.1)
        draw_crack(C, [mp(p) for p in pts], 0.5, 0.1)

    # 6. pauldrons: layered plates and three spikes each
    pa = obsidian(B.poly([(131, 112), (138, 105), (148, 105), (152, 111), (149, 119), (140, 123), (132, 121)]),
                  radius=6, cuts=(0.26, 0.46, 0.66, 0.86))
    pb = obsidian(B.poly([(129, 118), (135, 116), (142, 122), (138, 128), (130, 126)]), radius=4)
    pb = top_edge(pb, '4')
    pa = top_edge(pa, '5')
    C.stamp(pb)
    C.stamp(top_edge(obsidian(set(mir(pb)), radius=4), '4'))
    C.stamp(pa)
    C.stamp(top_edge(obsidian(set(mir(pa)), radius=6, cuts=(0.26, 0.46, 0.66, 0.86)), '4'))
    for base, ang, ln, wd in (((136, 107), -118, 16, 3.0), ((131, 113), -150, 11, 2.6), ((144, 105), -97, 9, 2.2)):
        both(C, spike(base, math.radians(ang), ln, wd, bend=-1.5))

    # 7. collar spikes, neck, head
    both(C, spike((152, 108), math.radians(-105), 8, 2.0, bend=-0.8))
    neck = obs_tube([(159.5, 104), (159.5, 112)], [4.4, 4.8])
    C.stamp(neck)
    back, front = crown_horns(pose)
    for h in back:
        C.stamp(h)
    C.stamp(face_a1() if variant == 'A1' else face_mask(pose.mouth_open), outline=False)
    C.stamp(hair_crown(), outline=False)
    for h in front:
        C.stamp(h)

    # 8. cracks from the core across the chest, down the centre line
    for ang, ln in ((-150, 16), (-120, 12), (-35, 15), (-62, 11), (160, 13), (25, 13), (110, 20)):
        a = math.radians(ang)
        p0 = (CORE[0] + math.cos(a) * 4, CORE[1] + math.sin(a) * 4)
        p1 = (CORE[0] + math.cos(a) * ln, CORE[1] + math.sin(a) * ln)
        draw_crack(C, crack_path(p0, p1, rnd, jag=1.2, step=2.5), 0.95, 0.15)
    draw_crack(C, crack_path((159.5, 129), (159.5, 160), rnd, jag=0.6, step=3), 0.85, 0.2)

    # 9. the core (effect, no keyline)
    core = {}
    cx, cy = CORE
    s = pose.core
    for (x, y) in B.ellipse(cx, cy, 6.0 * max(1.0, s), 6.0 * max(1.0, s)):
        dxx, dyy = abs(x - cx), abs(y - cy)
        d = math.hypot(dxx, dyy)
        if d < 1.2:
            k = 'w'
        elif (dxx < 0.6 and dyy < 5.5 * s) or (dyy < 0.6 and dxx < 5.5 * s):
            k = 'Y' if d < 4 * s else 'O'
        elif abs(dxx - dyy) < 0.8 and d < 3.6 * s:
            k = 'O'
        elif d < 2.6 * s:
            k = 'Y'
        elif 3.6 * s <= d < 5.0 * s:
            k = 'P' if (x + y) % 2 else 'Q'
        else:
            continue
        core[(x, y)] = k
    C.stamp(core, outline=False)
    px = rim_light(C.px)
    # the deepest obsidian shadow is keyline black
    px = {p: ('k' if k == '1' else k) for p, k in px.items()}
    px = fill_pinholes(px)
    # effect specks last (no keyline): embers riding off him
    for (x, y, k) in pose.embers:
        if (x, y) not in px:
            px[(x, y)] = k
    if not seat:
        return px
    # seat his lowest texel on the anchor row
    low = max(y for (x, y) in px)
    dy = ANCHOR[1] - low
    if dy:
        print('note: seated %+d rows to put his lowest texel on row %d' % (dy, ANCHOR[1]))
    return {(x, y + dy): k for (x, y), k in px.items() if 0 <= y + dy < H}


def fill_pinholes(px, key='k'):
    """Close one-texel holes (transparent texels boxed in on all four sides) with keyline."""
    px = dict(px)
    while True:
        xs = [p[0] for p in px]
        ys = [p[1] for p in px]
        holes = [(x, y) for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)
                 if (x, y) not in px and all(q in px for q in B.neighbours4((x, y)))]
        if not holes:
            return px
        for q in holes:
            px[q] = key


def rim_light(px, cold_top='7', cold='6', warm='V', warm_below=120):
    """The rune circles behind him backlight his silhouette: obsidian / leather texels just inside
    the OUTER keyline take a cold rim on edges that face up or away from his centre line (the
    brighter cyan on top-facing edges); edges facing down over the fire take a warm rim. Edges
    facing his own centre line get none."""
    outer = {p for p, k in px.items() if k == 'k' and any(q not in px for q in B.neighbours4(p))}
    out = dict(px)
    for (x, y), k in px.items():
        if k not in OBS_KEYS and k not in LEATHER_KEYS:
            continue
        up_, dn = (x, y - 1) in outer, (x, y + 1) in outer
        away = (x - 1, y) in outer if x < 159.5 else (x + 1, y) in outer
        if k in LEATHER_KEYS:
            if up_:
                out[(x, y)] = cold
            continue
        if up_:
            out[(x, y)] = cold_top
        elif dn and y >= warm_below:
            out[(x, y)] = warm
        elif away:
            out[(x, y)] = cold
    return out


def image(variant='A1'):
    return B.image(build(variant), W, H, PAL_A1 if variant == 'A1' else PAL_A2)


if __name__ == '__main__':
    out = sys.argv[1]
    for v in ('A1',):
        im = image(v)
        B.up(im, 3, bg=(14, 10, 24, 255)).save(os.path.join(out, 'lord_%s_3x.png' % v))
        print(v, B.stats(im))
