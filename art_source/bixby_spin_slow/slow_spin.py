"""The slow spin loop (bixby_spin_slow.png, 24 frames of 192x160): the same seamless third of a turn as
frames 2-5 of bixby_spin.png, in 5 degree steps, for a spin slowed to about 40 degrees a second.

Built from the approved redesign rig (art_source/bixby_redesign, imported read-only) and from the
current spin's own parts (rig_spin: the spin head, the maw, the necks, the whirl's profile and colour
bands), so frame 0 is the old loop's frame 2 in every part but the whirl's streak pattern.

    import slow_spin
    frames = slow_spin.frames()          # 24 PIL images, 192x160
    slow_spin.anchors(k)                 # [[azimuth, x, y, near], ...] for frame k, as MOUTH_ANCHORS

What changes from the fast loop, and why
  * Frame k has its heads at azimuths 5k, 5k+120, 5k+240, on the orbit the old MOUTH_ANCHORS were
    computed on (art_source/bixby_beast/quake_spin.mouth_anchors):
        x = 84 + 52 cos(a) - 2.4 sin(a),  y = 71.4 + 14.68 sin(a),  near = sin(a) >= 0
    It reproduces every row of the old table, so the old spin_up / spin_down frames sit on it too.
  * The body is no longer re-rolled noise every frame. At 0.1 s a frame and 30 degrees a step the
    noise read as a blur; at 5 degrees a step it would boil while the heads crawl. The whirl is now one
    streak texture wrapped round the column (a cylinder about x = 84) that turns with the heads, 5
    degrees a frame. The texture repeats every 120 degrees, so 24 frames bring it back to frame 0.
    Same profile, colour bands, streak lengths (4-13 px, facing us) and highlight rate as the old whirl.
  * The heads turn to face their azimuth instead of flipping between the two 3/4 views: within 20
    degrees of straight at the camera (a = 90) or straight away (a = 270) a head turns through the
    front view, 10 degrees of head turn per frame. Everywhere else it is the old loop's 3/4 head,
    pixel for pixel. The tongue changes sides on the front-view frame.
  * The motion arcs go round once per loop (15 degrees a frame, three times the heads, as before);
    the dust puffs rock every 2 frames instead of every frame.
  * A head passing a side of the column slides behind its edge over 6 frames (see DEPTH below)
    instead of half of it popping in or out between two frames.

Kept exactly: the three heads are the same head (the spin head never wears the headband), which is
what lets a third of a turn loop at all: the head arriving at 120 degrees is indistinguishable from
the one that left it. Wings stay clamped: none are drawn, their membrane colours are in the whirl.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
REDESIGN = os.path.join(ART, 'bixby_redesign')
if REDESIGN not in sys.path:
    sys.path.insert(0, REDESIGN)
if ART not in sys.path:
    sys.path.insert(1, ART)

from pal import BCanvas, amap  # noqa: E402
import heads  # noqa: E402
import rig_fx as FX  # noqa: E402
import rig_spin  # noqa: E402

N = 24                      # frames in the loop
STEP = 5.0                  # degrees of turn per frame
PERIOD = 120.0              # three alike heads: a third of a turn is the whole loop
AXIS_X = rig_spin.AXIS_X    # 84: the whirl turns about the spin centre's x
TURN = 20.0                 # a head turns through the front view within this many degrees of a = 90 / 270
FACE = 40.0                 # the loop's 3/4 view: phi = -40 faces left, its mirror faces right
LEAN = 14.0                 # ...leaning back against the turn at the 3/4 view, upright facing us
ARC_STEP = 2 * math.pi / N  # the motion arcs go round once per loop
WHIRL_SEED = 102            # frame 2's seed in the old sheet
STREAK = (4, 13)            # old whirl streak lengths, px, as seen facing us
HIGHLIGHT = 0.08


#ORBIT AND ANCHORS

def orbit(az):
    """The mouth point of a head at floor azimuth `az` (degrees), and whether it is near the camera."""
    r = math.radians(az)
    s, c = math.sin(r), math.cos(r)
    return 84.0 + 52.0 * c - 2.4 * s, 71.4 + 14.68 * s, s > -1e-9


def azimuths(k):
    return [(STEP * k + 120.0 * j) % 360.0 for j in range(3)]


def anchors(k):
    """[[azimuth, x, y, near], ...] for frame k: the numbers the maws are drawn from, to 0.1 texel."""
    out = []
    for az in azimuths(k):
        x, y, near = orbit(az)
        out.append([az, round(x, 1), round(y, 1), near])
    return out


def maw_pixel(x, y):
    """The texel the maw's core is drawn on for a (reported) mouth point, as rig_spin.placed_head does."""
    return int(round(x)), int(round(y))


#HEADS

def facing(az):
    """Head turn for a head at this azimuth: +40 the 3/4 view facing right, -40 facing left, 0 at us."""
    a = az % 360.0
    if a <= 180.0:
        phi = (90.0 - a) * FACE / TURN
    else:
        phi = (a - 270.0) * FACE / TURN
    return max(-FACE, min(FACE, phi))


_HEADS = {}

# heads.tongue's polygon, groove and shine (head space), moved 7 units right so it hangs down the
# middle of the jaw: the front-view head's tongue, between the two sides it hangs to either side of it
TONGUE = [(86, 62), (94, 62), (95, 70), (94, 78), (92, 86), (89, 93), (85, 94), (82, 90), (82, 81), (84, 72)]
TONGUE_GROOVE = [(89, 70), (88, 80), (87, 88)]
TONGUE_SHINE = [(85, 76), (85, 77), (86, 82)]
TONGUE_CENTRE_DX = 7


def centre_tongue(xf):
    from pal import fill
    from shapes import edge, recolor
    dx = TONGUE_CENTRE_DX
    t = fill(xf.poly([(x + dx, y) for x, y in TONGUE], 12), 'N')
    recolor(t, edge(t, -1, 0, 1), 'p')
    recolor(t, edge(t, 1, 0, 1), 'n')
    recolor(t, edge(t, 0, 1, 1), 'n')
    for p in xf.line([(x + dx, y) for x, y in TONGUE_GROOVE], 12):
        if p in t:
            t[p] = 'n'
    for x, y in TONGUE_SHINE:
        q = tuple(int(round(c)) for c in xf.p(x + dx, y, 12))
        if q in t:
            t[q] = 'P'
    return t


def build_head(cv, xf, tongue=None):
    """heads.build(cv, xf, tongue_flip=True, features=True, with_collar=True), stamp for stamp, with
    the tongue swappable (tongue=None is heads.tongue(xf, True))."""
    H = heads
    cv.stamp(H.ear(xf, 1))
    cv.stamp(H.ear(xf, -1))
    cv.stamp(H.crest(xf))
    band, spikes = H.collar(xf)
    for sp in spikes:
        cv.stamp(sp)
    cv.stamp(band)
    cv.stamp(H.ruff(xf))
    cv.stamp(H.mouth(xf))
    for s in H.both_sides(H.LOWER_FANG):
        cv.stamp(H.fang(xf, s, 10))
    cv.stamp(H.jaw(xf))
    cv.stamp(tongue if tongue is not None else H.tongue(xf, True))
    for s in H.both_sides(H.UPPER_FANG):
        cv.stamp(H.fang(xf, s, 12))
    cv.stamp(H.skull(xf))
    cv.stamp(H.nose(xf))
    for side in (1, -1):
        b, lit = H.brow(xf, side)
        cv.stamp(b, outline=False)
        cv.stamp(lit, outline=False)
    for side in (1, -1):
        cv.stamp(H.eye(xf, side))


def head(phi):
    """The spin head turned `phi` degrees on a 72x72 canvas, and where its mouth (maw core) is.

    phi <= 0 is built turned left (phi = -40 is rig_spin.head_canvas exactly); phi > 0 is the mirror of
    the head built at -phi, as the fast loop mirrors its right-facing heads."""
    phi = round(phi, 6)
    if phi in _HEADS:
        return _HEADS[phi]
    a = -abs(phi)
    cv = BCanvas(w=72, h=72)
    xf = heads.Xf(cx=36, cy=30, phi=a, s=rig_spin.S, theta=LEAN * a / FACE)
    if phi == 0:                             # facing us: the tongue hangs down the middle
        build_head(cv, xf, tongue=centre_tongue(xf))
    else:
        heads.build(cv, xf, tongue_flip=True, features=True, with_collar=True)
    mx, my = xf.p(95.5, 64, 10)
    mouth = (int(round(mx)), int(round(my)))
    cv.stamp(amap(rig_spin.MAW, mouth[0] - rig_spin.MAW_C[0], mouth[1] - rig_spin.MAW_C[1]), outline=False)
    px = dict(cv.px)
    if phi > 0:
        px = {(71 - x, y): k for (x, y), k in px.items()}
        mouth = (71 - mouth[0], mouth[1])
    _HEADS[phi] = (px, mouth)
    return _HEADS[phi]


def placed_head(az, x, y):
    """The head for this azimuth, moved so its maw core lands on the mouth point's texel."""
    px, (mx, my) = head(facing(az))
    X, Y = maw_pixel(x, y)
    dx, dy = X - mx, Y - my
    return {(hx + dx, hy + dy): k for (hx, hy), k in px.items()}


#THE WHIRL, WRAPPED ROUND A TURNING COLUMN

def _row_span(y):
    hw = rig_spin.half_width(y)
    if hw <= 0:
        return None
    return int(round(AXIS_X - hw)), int(round(AXIS_X + hw))


def _band(y):
    return next(c for (a, b, c) in rig_spin.BANDS if a <= y < b or (y == b and b == 154))


def texture(seed=WHIRL_SEED):
    """Per row: (x0, x1, runs), runs being [start, end, key] in degrees round the column over one
    period (120). A run is 4-13 px long where it faces us, like the old whirl's streaks."""
    rnd = random.Random(seed)
    rows = {}
    for y in range(rig_spin.PROFILE[0][0], rig_spin.PROFILE[-1][0] + 1):
        span = _row_span(y)
        if span is None:
            continue
        x0, x1 = span
        R = (x1 - x0 + 1) / 2.0
        cols = _band(y)
        runs = []
        a = 0.0
        while a < PERIOD - 1e-9:
            n = rnd.randint(*STREAK)
            k = 'w' if rnd.random() < HIGHLIGHT else rnd.choice(cols)
            length = math.degrees(n / R)
            runs.append([a, a + length, k])
            a += length
        runs[-1][1] = PERIOD
        # a sliver left at the seam goes to the run before it
        if len(runs) > 1 and runs[-1][1] - runs[-1][0] < math.degrees(STREAK[0] / R):
            runs.pop()
            runs[-1][1] = PERIOD
        # every row starts its runs at its own angle: rows that all broke at 0 drew a vertical seam
        phase = rnd.uniform(0.0, PERIOD)
        runs = [[(a + phase), (b + phase), k] for a, b, k in runs]
        runs = _wrap(runs)
        rows[y] = (x0, x1, runs)
    return rows


def _wrap(runs):
    """Runs moved past the period, folded back into [0, PERIOD) (a run over the end is split)."""
    out = []
    for a, b, k in runs:
        a0, b0 = a % PERIOD, a % PERIOD + (b - a)
        if b0 <= PERIOD:
            out.append([a0, b0, k])
        else:
            out.append([a0, PERIOD, k])
            out.append([0.0, b0 - PERIOD, k])
    return sorted(out)


def _dominant(runs, a0, a1):
    """The key covering most of the angular interval [a0, a1] (degrees, wrapped to the period)."""
    s = a0 % PERIOD
    e = s + (a1 - a0)
    pieces = [(s, min(e, PERIOD))]
    if e > PERIOD:
        pieces.append((0.0, e - PERIOD))
    acc = {}
    for r0, r1, key in runs:
        for p, q in pieces:
            o = min(r1, q) - max(r0, p)
            if o > 0:
                acc[key] = acc.get(key, 0.0) + o
    return max(acc, key=acc.get)


def whirl(k, tex):
    """The column on frame k: each texel shows the part of the texture turned in front of it."""
    shift = (STEP * k) % PERIOD
    out = {}
    for y, (x0, x1, runs) in tex.items():
        xc = (x0 + x1) / 2.0
        R = (x1 - x0 + 1) / 2.0
        for x in range(x0, x1 + 1):
            u0 = max(-1.0, min(1.0, (x - 0.5 - xc) / R))
            u1 = max(-1.0, min(1.0, (x + 0.5 - xc) / R))
            t0, t1 = math.degrees(math.asin(u0)), math.degrees(math.asin(u1))
            out[(x, y)] = _dominant(runs, t0 + shift, t1 + shift)
    return out


#FX

def fx(cv, k):
    a0 = 0.5 + (k % N) * ARC_STEP              # frame 0 = the old frame 2's arcs
    FX.motion_arc(AXIS_X, 112, 60, 14, a0, a0 + 2.4)(cv, None)
    FX.motion_arc(AXIS_X, 134, 56, 11, a0 + 3.1, a0 + 5.0)(cv, None)
    rock = ((k // 2) % 2) * 3
    for dx, s in ((-52, 2), (-28, 1), (26, 2), (50, 1)):
        FX.dust(int(AXIS_X + dx + rock), s, drift=1 if dx > 0 else -1)(cv, None)


#DEPTH
# The fast loop drew near heads over the whirl and far heads under it, switching at the sides (a = 0,
# 180). A head at the side overlaps the column's edge by ~160 texels, so at 5 degrees a step that
# switch would pop half a head in or out in one frame. Instead each texel goes to whichever is nearer
# the camera: the column's front surface, sqrt(R^2 - dx^2) deep, or a head, 52 sin(a) + DEPTH_BIAS.
# With the bias at 30 every old loop frame (a = 0, 30, 60, 90) layers exactly as before - the heads
# at the sides fully over the whirl (needs > 29.1), the ones 30 degrees behind them fully under it
# (needs < 31.3) - and in between a head slides behind the column's edge over 6 frames.

DEPTH_BIAS = 30.0
MODE = 'depth'          # 'depth' (above), or 'switch' (the fast loop's near/far rule, for comparison)
EDGE_LINE = True        # a keyline where the column hides part of a head


def head_depth(az):
    return 52.0 * math.sin(math.radians(az)) + DEPTH_BIAS


def column_depth(tex, x, y):
    x0, x1, _ = tex[y]
    xc, R = (x0 + x1) / 2.0, (x1 - x0 + 1) / 2.0
    return math.sqrt(max(0.0, R * R - (x - xc) ** 2))


def _composite(cv, W, tex, placed):
    """Whirl (with its keyline ring) and heads into cv by depth. placed: [(depth, head px)] far first."""
    Z = {p: (column_depth(tex, *p), k, 'col') for p, k in W.items()}
    ring = {}
    for (x, y) in W:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in W and 0 <= q[0] < cv.w and 0 <= q[1] < cv.h:
                ring[q] = max(ring.get(q, 0.0), column_depth(tex, x, y))
    for q, d in ring.items():
        Z[q] = (d, 'k', 'ring')
    hidden = {}
    for j, (d, hp) in enumerate(placed):
        for p, k in hp.items():
            if not (0 <= p[0] < cv.w and 0 <= p[1] < cv.h):
                continue
            cur = Z.get(p)
            if cur is None or d > cur[0]:
                Z[p] = (d, k, j)
            elif cur[2] == 'col':
                hidden.setdefault(j, set()).add(p)
    for p, (d, k, owner) in Z.items():
        cv.px[p] = k
    if EDGE_LINE:
        # where the column hides part of a head, the column's texels along the cut are keyline
        for j, ps in hidden.items():
            for (x, y) in ps:
                if any(Z.get(q, (0, 0, None))[2] == j for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                    cv.px[(x, y)] = 'k'


#FRAMES

_TEX = {}


def frame(k, seed=WHIRL_SEED):
    """Frame k of the loop as a canvas (k = 24 is frame 0 again)."""
    if seed not in _TEX:
        _TEX[seed] = texture(seed)
    tex = _TEX[seed]
    cv = BCanvas()
    hs = anchors(k)
    by_depth = sorted(hs, key=lambda h: math.sin(math.radians(h[0])))
    for az, x, y, near in by_depth:            # necks all start behind the body; the nearest on top,
        cv.stamp(rig_spin.neck(x, y + 8))      # so where they meet does not depend on list order
    W = whirl(k, tex)
    if MODE == 'depth':
        _composite(cv, W, tex, [(head_depth(az), placed_head(az, x, y)) for az, x, y, near in by_depth])
    else:
        for az, x, y, near in by_depth:        # far heads behind the whirl, their maws above its top
            if not near:
                cv.px.update(placed_head(az, x, y))
        cv.stamp(W)
        for az, x, y, near in by_depth:        # near heads over it, the nearest last
            if near:
                cv.px.update(placed_head(az, x, y))
    fx(cv, k)
    return cv


def frames(seed=WHIRL_SEED):
    return [frame(k, seed).image() for k in range(N)]


def table():
    """The per-frame maw anchors as GDScript, in the form of BixbyCombinedArtLayout.MOUTH_ANCHORS."""
    lines = []
    for k in range(N):
        rows = ', '.join('[%.1f, %.1f, %.1f, %s]' % (az, x, y, 'true' if near else 'false')
                         for az, x, y, near in anchors(k))
        lines.append('\t%d: [%s],' % (k, rows))
    return '{\n' + '\n'.join(lines) + '\n}'
