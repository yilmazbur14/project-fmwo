"""The spin sheet (bixby_spin.png, 8 frames of 192x160): the beast whirling on the floor, his body a
blur of its own colours, his three heads flung round on their necks, maws screaming the sonic beams.

  0  the crouch he winds up in, maws starting to glow
  1  the lead-in: the spin catching (his body half blurred), maws alight - the beams come out here
  2-5  the seamless loop, a third of a turn each time round
  6-7  the wobble he stops on, the body coming back together

Every head's mouth sits exactly on BixbyCombinedArtLayout.MOUTH_ANCHORS (read from the script), so the
sonic sweep keeps firing from the maws: [azimuth, x, y, near the camera] per frame, orbiting
SPIN_CENTRE (84.0, 71.4). A head on the right half of the circle faces right, and every head leans
into the turn so its burning ears trail behind.
"""
import math
import os
import random
import re

from pal import BCanvas, amap, fill
import heads
import rig
import rig_fx as FX
import rig_poses as RP
import rig_wings as RW
from shapes import capsule, edge, recolor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LAYOUT = os.path.join(ROOT, 'Scripts', 'BixbyCombinedArtLayout.gd')

S = 0.56             # the heads flung out on their necks
PHI = -40            # three-quarter view, facing left (mirrored to face right)
CENTRE = (84.0, 71.4)
AXIS_X = 84          # the whirl turns about the spin centre's x, not his standing axis


def anchors():
    src = open(LAYOUT, encoding='utf-8').read()
    body = re.search(r'MOUTH_ANCHORS := \{(.*?)\n\}', src, re.S).group(1)
    out = {}
    for m in re.finditer(r'(\d+): \[(.*?)\]\],', body + ',', re.S):
        rows = re.findall(r'\[([-\d.]+), ([\d.]+), ([\d.]+), (true|false)', m.group(2) + ']')
        out[int(m.group(1))] = [(float(a), float(x), float(y), n == 'true') for a, x, y, n in rows]
    return out


# the screaming maw, stamped on each head's mouth: dark rim, fangs, the scream glowing inside
MAW = [
    "..kkkkk..",
    ".kwqqqwk.",
    "kkwpPpwkk",
    "kqpPYPpqk",
    "kqpPYPpqk",
    "kkpPPPpkk",
    ".kxkpkxk.",
    "..kkkkk..",
]
MAW_C = (4, 4)       # the mouth point inside the map

_HEADS = {}


def head_canvas(lean):
    """A spin head facing left, leaning `lean` degrees, and where its mouth is (cached)."""
    if lean in _HEADS:
        return _HEADS[lean]
    cv = BCanvas(w=72, h=72)
    xf = heads.Xf(cx=36, cy=30, phi=PHI, s=S, theta=lean)
    heads.build(cv, xf, tongue_flip=True, features=True, with_collar=True)
    mx, my = xf.p(95.5, 64, 10)
    mouth = (int(round(mx)), int(round(my)))
    cv.stamp(amap(MAW, mouth[0] - MAW_C[0], mouth[1] - MAW_C[1]), outline=False)
    _HEADS[lean] = (cv.px, mouth)
    return _HEADS[lean]


def placed_head(az, x, y):
    """The head for this azimuth, moved so its mouth lands exactly on (x, y)."""
    right = math.cos(math.radians(az)) >= 0
    px, (mx, my) = head_canvas(-14)          # leaning back against the turn: ears stream behind
    if right:
        px = {(71 - hx, hy): k for (hx, hy), k in px.items()}
        mx = 71 - mx
    dx, dy = int(round(x)) - mx, int(round(y)) - my
    return {(hx + dx, hy + dy): k for (hx, hy), k in px.items()}


# the whirl's half-width by height, and the colours smeared through each band of it. Its top sits
# below every far head's maw (the highest is at y 64), so the beams leave visible mouths.
PROFILE = [(70, 28), (76, 38), (86, 45), (100, 50), (116, 51), (130, 48), (142, 42), (149, 36), (153, 30)]
BANDS = [(70, 86, 'ccbdtsBCk'), (86, 100, 'ctsxdbk'), (100, 126, 'xxwytsc'), (126, 142, 'xytcbk'),
         (142, 154, 'xykcy')]


def half_width(y):
    for (y0, w0), (y1, w1) in zip(PROFILE, PROFILE[1:]):
        if y0 <= y <= y1:
            return w0 + (w1 - w0) * (y - y0) / (y1 - y0)
    return 0


def whirl(seed, streak=(4, 13), highlight=0.08):
    """The body as a spinning column: every row a run of streaks from its band's colours."""
    rnd = random.Random(seed)
    out = {}
    for y in range(PROFILE[0][0], PROFILE[-1][0] + 1):
        hw = half_width(y)
        if hw <= 0:
            continue
        x0, x1 = int(round(AXIS_X - hw)), int(round(AXIS_X + hw))
        cols = next(c for (a, b, c) in BANDS if a <= y < b or (y == b and b == 154))
        x = x0
        while x <= x1:
            run = rnd.randint(*streak)
            k = 'w' if rnd.random() < highlight else rnd.choice(cols)
            for xx in range(x, min(x1, x + run - 1) + 1):
                out[(xx, y)] = k
            x += run
    return out


def partial_whirl(src_px, seed, rows=0.55, streak=(3, 8)):
    """The lead-in and the wobble: his body, some rows of it dragged into streaks."""
    rnd = random.Random(seed)
    out = dict(src_px)
    ys = sorted({y for (_, y) in src_px})
    for y in ys:
        if rnd.random() > rows:
            continue
        xs = sorted(x for (x, yy) in src_px if yy == y)
        cols = [src_px[(x, y)] for x in xs if src_px[(x, y)] != 'k']
        if not cols:
            continue
        x, x1 = xs[0] + 1, xs[-1] - 1
        while x <= x1:
            run = rnd.randint(*streak)
            k = rnd.choice(cols)
            for xx in range(x, min(x1, x + run - 1) + 1):
                if (xx, y) in out and out[(xx, y)] != 'k':
                    out[(xx, y)] = k
            x += run
    return out


def neck(hx, hy):
    """A neck whipped out from the top of the whirl to a head: a charcoal streak."""
    n = fill(capsule((AXIS_X, 70), (hx, hy), 4.0, 3.0), 'c')
    recolor(n, edge(n, 0, -1, 1), 'd')
    recolor(n, edge(n, 0, 1, 1), 'b')
    return n


def crouched_body():
    """The crouch without its heads, standing on the spin's axis."""
    P = RP.grounded(10, RW.FOLD, front_x=124, hind_x=156)
    P['hide'] = ('mid', 'side', 'tails', 'tail')          # the tail is lost in the whirl
    shift = AXIS_X - 96
    return {(x + shift, y): k for (x, y), k in rig.build(P).px.items()}


def spin_frame(i, A):
    cv = BCanvas()
    hs = A.get(i, [])
    partial = i in (1, 7)                       # the spin catching / settling: body half blurred
    for az, x, y, near in hs:                   # necks all start behind the body
        cv.stamp(neck(x, y + 8))
    if not partial:
        for az, x, y, near in hs:               # far heads behind the whirl, maws above its top
            if not near:
                cv.px.update(placed_head(az, x, y))
    if partial:
        cv.px.update(partial_whirl(crouched_body(), 40 + i, rows={1: 0.55, 7: 0.35}[i]))
    else:
        if i == 6:                              # slowing: the wings start to swing back out
            import rig_wings
            from pal import mir
            wing_cv = BCanvas()
            rig_wings.build(wing_cv, rig_wings.moved(rig_wings.DOWN, dx=-12), mir)
            cv.px.update(wing_cv.px)
        cv.stamp(whirl(100 + i, streak=(3, 8) if i == 6 else (4, 13)))
    for az, x, y, near in hs:                   # near heads over it (all of them, while half blurred)
        if near or partial:
            cv.px.update(placed_head(az, x, y))
    if i in (2, 3, 4, 5):
        a0 = 0.5 + (i - 2) * 1.5708
        FX.motion_arc(AXIS_X, 112, 60, 14, a0, a0 + 2.4)(cv, None)
        FX.motion_arc(AXIS_X, 134, 56, 11, a0 + 3.1, a0 + 5.0)(cv, None)
        for dx, s in ((-52, 2), (-28, 1), (26, 2), (50, 1)):
            FX.dust(int(AXIS_X + dx + (i % 2) * 3), s, drift=1 if dx > 0 else -1)(cv, None)
    return cv


def frames():
    A = anchors()
    P0 = RP.grounded(10, RW.FOLD, front_x=124, hind_x=156, head_dy=12, side_dy=12,
                     mid=dict(mouth='inhale', low_dy=5), side=dict(mouth='roar', low_dy=3),
                     fx=[FX.dust(40, 2, drift=-1), FX.dust(150, 2)])
    out = [rig.build(P0).image()]
    for i in range(1, 8):
        out.append(spin_frame(i, A).image())
    return out


def mouths_check():
    """Each placed head's maw centre, against its anchor (should be exact to the texel)."""
    A = anchors()
    for i in range(1, 8):
        for az, x, y, near in A[i]:
            px = placed_head(az, x, y)
            # the maw's glowing core is at the mouth point
            print(i, az, (round(x), round(y)), px.get((int(round(x)), int(round(y)))))
