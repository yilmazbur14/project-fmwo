"""Danny's juggle: 12 frames of 304x208, feet at (152, 207), the contract's order.

The read is WEIGHT: the uppercut barely lifts him.

  0-1   HIT     the fist lands under his chins: head snapped back, eyes screwed shut, mouth wide in a
                howl, hands flung up; his feet have not left the mat (0). On 1 they have only just
                left it -- a few pixels -- and the mat's dust is still round his soles.
  2-6   TUMBLE  2 the stall at the top: tipped back, limp, arms hanging, legs dangling, eyes wide.
                3-6 he turns over like a dropped sack: tucked into the seated cannonball of his own
                defeat sheet, a quarter turn a frame, clockwise, the arms flopping about.
  7-9   CRASH   the belly flop: he lands flat on his back and the whole mass spreads -- belly puffed
                wide, dust thrown out flat both ways, the mat's cracks and shock lines under him (7);
                the belly bounces back up as the mass rebounds (8); he settles and a snot bubble starts
                to grow (9).
  10-11 DOWN    out cold, X eyes, tongue out, and the gag of his KO: the snot bubble swells on the
                breath out (10) and POPS on the breath in (11), over and over.

His rig renders every frame in his own 176x144 frame with the light turned against the frame's turn
(dparts.Render), so every turned frame is lit from the upper left by his own shading.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dparts as D              # noqa: E402  (puts danny_sumo_v2 on the path, loads jkit)
K = D.K
import sumo_lib as L            # noqa: E402

W, H = 304, 208
FEET = (152, 207)
OFF = (FEET[0] - 88, FEET[1] - 143)         # his own frame placed with its soles on FEET
PIVOT = (88, 78)                            # the middle of his mass, his own frame
AIR_AT = (152, 100)                         # where the pivot sits while he is in the air
DOWN_AT = (152, 132)                        # lying on his back

REC = {'body': {}, 'props': {}}


def recorded(fn):
    def wrapped(*a, **kw):
        REC['body'], REC['props'] = {}, {}
        return finish(fn(*a, **kw))
    wrapped.__name__ = fn.__name__
    return wrapped


def finish(g):
    g = K.clip(g, W, H)
    for _ in range(2):
        for q in K.pinholes(g):
            n = [g[(q[0] + dx, q[1] + dy)] for dx, dy in K.N4]
            g[q] = 'k' if n.count('k') >= 2 else max(set(n), key=n.count)
    return g


def over(dst, src, only_empty=False):
    for q, k in src.items():
        if 0 <= q[0] < W and 0 <= q[1] < H and (not only_empty or q not in dst):
            dst[q] = k
    return dst


def under(dst, src):
    return over(dst, src, only_empty=True)


def place(spec, deg, at, pivot=PIVOT, squash=(1.0, 1.0), crisp=True):
    """His rig, relit for a turn of deg, turned about `pivot` (his own frame) onto `at`, then
    squashed in the frame (sx across, sy down) the way a heavy body flattens on the mat. A squashed
    body gets its head laid back on unsquashed and turned by an exact quarter turn, on the point of
    the squashed body where it belongs, so his face and his beanie's knit stay pixel-crisp."""
    M = K.turn_squash(deg, *squash)
    turns = int(round(deg / 90.0))
    if squash == (1.0, 1.0):
        r = D.Render(spec, deg)
        px = D.relight_face(r)
        if deg % 90 == 0:
            out = K.rot90(px, turns, pivot, at)
        else:
            feats = r.features() if crisp else ()
            out = K.rekeyline(K.affine_with_features(px, M, pivot, at, feats, turns=turns))
    else:
        body = D.Render(spec, deg, part='body')
        out = K.rekeyline(K.affine(body.px, M, pivot, at))
        r = D.Render(spec, deg, part='head')
        hc = r.head_centre()
        hx, hy = K.affine_pt(hc, M, pivot, at)
        head = K.rot90(D.relight_face(r), turns, (int(round(hc[0])), int(round(hc[1]))),
                       (int(round(hx)), int(round(hy))))
        out.update(head)
    REC['body'].update(K.clip(out, W, H))
    r.M, r.at, r.pivot = M, at, pivot
    r.turns = turns
    return out, r


def nostril_at(r):
    """Where his nostril is in the frame. On a squashed frame his head was laid on unsquashed, so
    the nostril goes with the head: turned about the head's centre, carried to where it landed."""
    if getattr(r, 'part', 'all') == 'head':
        hc = r.head_centre()
        hx, hy = K.affine_pt(hc, r.M, r.pivot, r.at)
        return K.rot_pt(r.nostril(), 90 * r.turns, hc, (round(hx), round(hy)))
    return K.affine_pt(r.nostril(), r.M, r.pivot, r.at)


def cheek_dir(r):
    """Screen direction of his own +x (the approved bubble grows that way, over his right cheek)."""
    if getattr(r, 'part', 'all') == 'head':
        a = math.radians(90 * r.turns)
        return (math.cos(a), math.sin(a))
    a, b, c, d = r.M
    n = math.hypot(a, c) or 1.0
    return (a / n, c / n)


def snot(g, r, size):
    """The bubble on his nostril, upright, grown out over his right cheek as in the approved idle."""
    nx, ny = nostril_at(r)
    ux, uy = cheek_dir(r)
    rad = D.anim.BUBBLE_R[size]
    b = D.bubble(nx + ux * rad, ny + uy * rad, rad)
    kl = K.rekeyline({**{q: 'k' for q in b}, **b})
    REC['props'].update(K.clip(kl, W, H))
    over(g, kl)


# The pop: the rig's own ring of droplets (anim.POP), each drawn as a keylined 2x2 bead so it reads
# over his face at 3x, and a white flash where the bubble was.
POP_BEAD = {(0, 0): 'W', (1, 0): 'H', (0, 1): 'H', (1, 1): 'h'}


def pop(g, r, reach=1.5):
    nx, ny = nostril_at(r)
    ux, uy = cheek_dir(r)
    cx, cy = nx + ux * 6, ny + uy * 6
    splash = {}
    for (ox, oy), _ in D.POP:
        bx, by = int(round(cx + ox * reach)), int(round(cy + oy * reach))
        for (dx, dy), k in POP_BEAD.items():
            splash[(bx + dx, by + dy)] = k
    kl = {}
    for (x, y) in splash:
        for dx, dy in K.N4:
            q = (x + dx, y + dy)
            if q not in splash:
                kl[q] = 'k'
    kl.update(splash)
    flash = {(int(round(cx)) + dx, int(round(cy)) + dy): 'W' for dx, dy in ((0, 0),) + K.N4}
    for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        flash[(int(round(cx)) + dx, int(round(cy)) + dy)] = 'H'
    kl.update(flash)
    REC['props'].update(K.clip({q: k for q, k in kl.items() if k != 'k'}, W, H))
    over(g, kl)


# ------------------------------------------------------------------ EFFECTS
def puff(cx, cy, r):
    """A dust ball off the mat in his white/wrap tones with a black rim, lit top-left."""
    disc = {(cx + dx, cy + dy) for dx in range(-r - 1, r + 2) for dy in range(-r - 1, r + 2)
            if dx * dx + dy * dy <= r * r + r * 0.5}
    out = {}
    for (x, y) in disc:
        if any((x + dx, y + dy) not in disc for dx, dy in K.N4):
            out[(x, y)] = 'k'
        else:
            t = (x - cx) + (y - cy)
            out[(x, y)] = 'W' if t < -r * 0.4 else ('h' if t > r * 0.7 else 'H')
    return out


def dust(g, specs):
    for (x, y, r) in specs:
        pf = puff(x, min(y, H - 2 - r), r)          # the whole ball, rim and all, inside the frame
        REC['props'].update({q: k for q, k in K.clip(pf, W, H).items() if q not in g})
        under(g, pf)


def lines(g, segs, key='k'):
    for (x0, y0), (x1, y1) in segs:
        under(g, {q: key for q in K.line_px(int(x0), int(y0), int(x1), int(y1))})


def arc(g, cx, cy, r, a0, a1, ry=None, key='W'):
    under(g, {q: key for q in K.arc_px(cx, cy, r, a0, a1, ry)})


def burst(g, cx, cy, r=10, protect=()):
    """An impact flash: a white core and eight rays, yellow into gold (his chain's golds)."""
    pts = {}
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if abs(dx) + abs(dy) <= 1:
                pts[(cx + dx, cy + dy)] = 'W'
    for (ux, uy, n) in ((1, 0, r), (-1, 0, r), (0, 1, r - 1), (0, -1, r - 1),
                        (1, 1, r - 3), (-1, 1, r - 3), (1, -1, r - 3), (-1, -1, r - 3)):
        for t in range(2, n + 1):
            pts[(cx + ux * t, cy + uy * t)] = 'W' if t <= 3 else ('Y' if t <= n - 2 else 'o')
    over(g, {q: k for q, k in pts.items() if q not in protect})


# ------------------------------------------------------------------ 0-1 THE HIT
HIT = dict(eyes='squeeze', mouth='shout', bubble=0, arms=('cock', 'cock'))


@recorded
def launch():
    """Contact. The rig's own hit pose (hands flung up, knees giving) with the head snapped further
    back, eyes screwed shut and the mouth wide; his soles are still on the mat."""
    g, r = place(dict(HIT, body=(-1, 2), head_dy=-4), 0, (PIVOT[0] + OFF[0], PIVOT[1] + OFF[1]))
    face = {(q[0] + OFF[0], q[1] + OFF[1]) for q in r.face}
    burst(g, 164, 119, r=14, protect=face)
    lines(g, [((184, 104), (196, 94)), ((188, 120), (202, 121)), ((182, 134), (193, 143)),
              ((140, 138), (132, 148))])
    dust(g, ((104, 204, 4), (200, 204, 4), (92, 206, 3), (212, 206, 3)))
    return g


@recorded
def launch_lift():
    """He has barely left the mat: four pixels, tipping back a few degrees, the belly still
    wobbling from the blow and the dust from his soles hanging under him."""
    g, r = place(dict(HIT, eyes='squeeze', mouth='ow', body=(0, 1), head_dy=-3, belly=2), 6,
                 (PIVOT[0] + OFF[0], PIVOT[1] + OFF[1] - 11))
    dust(g, ((96, 203, 5), (208, 203, 5), (80, 206, 3), (224, 206, 3), (118, 206, 3), (186, 206, 3)))
    lines(g, [((128, 196), (128, 190)), ((152, 198), (152, 191)), ((176, 196), (176, 190))], 'H')
    # the belly still wobbling from the blow: a ripple either side of it
    for (cx, a0, a1) in ((106, 150, 210), (199, -30, 30)):
        arc(g, cx, 138, 9, a0, a1, 12, key='k')
        arc(g, cx + (-5 if cx < 152 else 5), 138, 9, a0, a1, 12, key='k')
    return g


# ------------------------------------------------------------------ 2-6 THE TUMBLE
@recorded
def hang():
    """The stall. A heavy body hangs at the top: tipped back, arms dropped, legs dangling, the belly
    sagging, eyes wide."""
    g, r = place(dict(eyes='wide', mouth='slack', bubble=0, arms=('limp', 'limp'), belly=1, head_dy=-1),
                 24, AIR_AT)
    arc(g, AIR_AT[0], AIR_AT[1], 104, -120, -84, 86)
    return g


TUCK = dict(legs='sit', body=(0, 10), bubble=0)
SPIN = [
    dict(deg=90, eyes='wide', mouth='shout', arms=('limp', 'cock'), head_dy=3),
    dict(deg=180, eyes='squeeze', mouth='ow', arms=('rest', 'rest'), head_dy=4),
    dict(deg=270, eyes='wide', mouth='slack', arms=('cock', 'limp'), head_dy=3),
    dict(deg=330, eyes='wide', mouth='shout', arms=('rest', 'limp'), head_dy=4),
]


def head_bearing(deg):
    return -90 + deg


@recorded
def tumble(i):
    s = SPIN[i]
    spec = dict(TUCK, eyes=s['eyes'], mouth=s['mouth'], arms=s['arms'], head_dy=s['head_dy'])
    g, r = place(spec, s['deg'], AIR_AT)
    h = head_bearing(s['deg'])
    # behind the head and behind the seat: the turn is clockwise, so behind is anticlockwise
    arc(g, AIR_AT[0], AIR_AT[1], 104, h - 18 - 50, h - 18, 88)
    arc(g, AIR_AT[0], AIR_AT[1], 98, h + 162 - 40, h + 162, 82)
    return g


# ------------------------------------------------------------------ 7-11 DOWN
# Lying on his back, head to the right (the clockwise turn put it there), front to the camera, and
# flattened into the mat the way Mason's lying frames are (a heavy body spreads): the impact flattest,
# the rebound least, the settled body between.
LIE = dict(legs='stand', bubble=0)
FLAT = {'impact': (1.10, 0.62), 'bounce': (1.02, 0.80), 'rest': (1.06, 0.70)}


def down_at(squash, lift=0):
    """The pivot for a lying frame: his near side (screen bottom) on row 203."""
    half = 88 * squash[1]                 # his stance, turned, reaches about 88 px either side
    return (DOWN_AT[0], int(round(203 - half - lift)))


@recorded
def crash():
    """The belly flop: flat on his back, the belly puffed out wide as the mass spreads, arms flung
    out, dust thrown flat both ways along the mat, shock lines round him."""
    sq = FLAT['impact']
    g, r = place(dict(LIE, eyes='squeeze', mouth='shout', arms=('cock', 'cock'), belly=6), 90,
                 down_at(sq), squash=sq)
    # the whole mat jumps: dust thrown out flat and far both ways, shock lines skimming the canvas,
    # grit kicked up over him
    dust(g, ((26, 192, 10), (52, 200, 8), (8, 200, 6), (78, 204, 5), (278, 192, 10), (252, 200, 8),
             (296, 200, 6), (226, 204, 5), (104, 206, 3), (200, 206, 3)))
    lines(g, [((44, 170), (14, 160)), ((260, 170), (290, 160)), ((66, 182), (36, 178)),
              ((238, 182), (268, 178)), ((90, 194), (68, 194)), ((214, 194), (236, 194)),
              ((98, 88), (88, 74)), ((206, 88), (216, 74)), ((152, 80), (152, 64))])
    for (x, y) in ((70, 150), (236, 146), (120, 70), (186, 66), (44, 140), (262, 136)):
        over(g, {(x, y): 'H', (x + 1, y): 'h', (x, y + 1): 'h'})
    return g


@recorded
def bounce():
    sq = FLAT['bounce']
    g, r = place(dict(LIE, eyes='wide', mouth='ow', arms=('limp', 'limp'), belly=3), 90,
                 down_at(sq, lift=4), squash=sq)
    dust(g, ((22, 192, 9), (46, 199, 7), (282, 192, 9), (258, 199, 7), (6, 200, 4), (298, 200, 4)))
    return g


@recorded
def settle():
    sq = FLAT['rest']
    g, r = place(dict(LIE, eyes='x', mouth='tongue', arms=('limp', 'limp'), belly=1), 90,
                 down_at(sq), squash=sq)
    snot(g, r, 1)
    dust(g, ((18, 200, 5), (286, 200, 5)))
    return g


@recorded
def down(breath_in):
    sq = FLAT['rest']
    spec = dict(LIE, eyes='x', mouth='tongue', arms=('limp', 'limp'), belly=2 if breath_in else 0)
    g, r = place(spec, 90, down_at(sq), squash=sq)
    if breath_in:
        pop(g, r)
    else:
        snot(g, r, 4)
    return g


FRAMES = [
    ('launch_contact', launch, 0.07),
    ('launch_lift', launch_lift, 0.10),
    ('hang', hang, 0.26),
    ('tumble_a', lambda: tumble(0), 0.09),
    ('tumble_b', lambda: tumble(1), 0.08),
    ('tumble_c', lambda: tumble(2), 0.08),
    ('tumble_d', lambda: tumble(3), 0.09),
    ('crash_impact', crash, 0.07),
    ('crash_bounce', bounce, 0.10),
    ('crash_settle', settle, 0.14),
    ('down_swell', lambda: down(False), 0.45),
    ('down_pop', lambda: down(True), 0.35),
]
