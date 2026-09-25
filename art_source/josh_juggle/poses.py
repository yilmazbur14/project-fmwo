"""Josh's juggle: 12 frames of 160x120, feet at (80, 119), the contract's order.

  0-1   HIT     the uppercut lands under his chin: head snapped back, eyes squeezed, jaw dropped; the
                hat pops straight off and the fan in his hand BURSTS into loose cards. 1 is him leaving
                the mat, the hat spinning away above.
  2-6   TUMBLE  2 the apex: limp and surprised, the duster billowing, the cards hanging in the air round
                him. 3-6 one full cartwheel, counter-clockwise as drawn (he faces right, so it is a flip
                back away from the player who hit him), a quarter turn a frame, the duster swinging out
                behind the turn and his cards wheeling round him.
  7-9   CRASH   back-first into the mat with arms and boots thrown up (7), a bounce (8), the settle (9);
                the hat drops out of the sky beside his head.
  10-11 DOWN    out cold: X eyes, tongue out, chest rising and falling; his cards lie scattered round
                him and the hat sits on the mat by his head.

Every part is his approved rig's (josh3 / rig / ground_kit / anims_ride, imported read-only), posed
in his own 80x80 frame and turned into the juggle frame. The quarter turns are exact, so his pixels are
the approved pixels; the lift and the apex are RotSprite with the face's features put back crisp. Each
turned frame is relit first (jkit.relight) so the light stays at the upper left.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jparts as P              # noqa: E402  (puts art_source/josh_redesign on the path)
import jkit as K                # noqa: E402
import lib                      # noqa: E402
import rig                      # noqa: E402
import ground_kit as gk         # noqa: E402
import anims_ground as ag       # noqa: E402
from lib import amap            # noqa: E402

W, H = 160, 120
FEET = (80, 119)
# The rig's 80x80 frame sits in a bigger local canvas so thrown limbs are never clipped.
OFF = (40, 40)
LW, LH = 160, 160
PIV = (P.PIVOT[0] + OFF[0], P.PIVOT[1] + OFF[1])          # the pivot on the local canvas
STAND_AT = (FEET[0] + P.PIVOT[0] - 40, FEET[1] + P.PIVOT[1] - 79)   # rig (40, 79) -> FEET
# Where the pivot sits in the frame while he is in the air: the tumble centre.
AIR_AT = (80, 62)
# Lying on his back, head to the left: the pivot, chosen so his near side rests on the mat line.
DOWN_AT = (80, 95)


# ------------------------------------------------------------------ FIGURE PIECES
def fig():
    return K.Fig(LW, LH, OFF)


def head_turned(face, deg, pivot=(42, 38)):
    """The approved head with an expression, hatless, tilted by deg about the neck (RotSprite, the
    features put back crisp). Stamp it with outline=True."""
    hp = P.head(face)
    if not deg:
        return hp
    turned = K.rotate_with_features(hp, deg, pivot, pivot, P.features(hp))
    return {q: k for q, k in turned.items() if k != 'k' or any(
        turned.get((q[0] + dx, q[1] + dy), 'k') != 'k' for dx in (-1, 0, 1) for dy in (-1, 0, 1))}


def hand(rows, wrist, anchor, turns=0):
    """A glove map placed so its `anchor` cell sits on the wrist, turned by quarter turns first."""
    px = amap(rows, 0, 0)
    ax, ay = anchor
    rel = K.turn_patch({(x - ax, y - ay): k for (x, y), k in px.items()}, turns)
    wx, wy = int(round(wrist[0])), int(round(wrist[1]))
    return {(wx + u, wy + v): k for (u, v), k in rel.items()}


SPLAY = ag.SPLAY_HAND            # fingers flung open, pointing up; the cuff at the bottom
SPLAY_AT = (3, 6)
LIMP = ag.LIMP_DOWN              # hanging open, fingers down; the cuff at the top
LIMP_AT = (2, 0)


def arm(f, shoulder, elbow, wrist, near, label, lit=None):
    lit_up, lit_fore = lit or (None, None)
    for part, o in gk.arm(shoulder, elbow, wrist, near=near, lit_up=lit_up, lit_fore=lit_fore):
        f.stamp(part, o, label)


def glove(f, rows, wrist, anchor, turns, label):
    f.stamp(hand(rows, wrist, anchor, turns), False, label)


def features_at(f, face_px):
    """The head's feature pixels as they sit on the figure (for a crisp RotSprite turn)."""
    out = []
    for feat, fill in P.features(face_px):
        out.append(({f.local(q): k for q, k in feat.items() if f.px.get(f.local(q)) == k}, fill))
    return out


def duster(f, flare=2, sway=0, hem=72, knees=((37, 64), (47, 64)), ankles=((35, 72), (49, 72)),
           boots=((31, 73), (45, 73)), boot_cut=(2, 2)):
    """The approved coat top over a duster flaring out like a bell (ground_kit.lower_body, the squat's
    and the kneel's own lower body): `flare` px wider at each side of the hem, the hem swung `sway` px
    sideways, the legs bent inside it with the approved boots showing under the hem."""
    wr = 56
    left = [(30, wr - 3), (24 - flare + sway, hem - 2), (27 - flare // 2 + sway, hem),
            (32 + sway, hem + 1), (37, wr + 4), (37, wr - 3)]
    right = [(47, wr - 3), (54, wr - 3), (60 + flare + sway, hem - 2), (57 + flare // 2 + sway, hem),
             (52 + sway, hem + 1), (47, wr + 4)]
    back = [(37, wr + 2), (47, wr + 2), (52 + sway, hem), (32 + sway, hem)]
    for part, o in gk.lower_body(wr, hem, left, right, knees, ankles, boots, lining=3, back=back,
                                 boot_cut=boot_cut,
                                 fold_left=[(31 + sway // 2, wr + 4), (28 + sway, hem - 1)],
                                 fold_right=[(55 + sway // 2, wr + 4), (57 + sway, hem - 1)]):
        f.stamp(part, o, 'torso')
    f.stamp(gk.upper_torso(gk.torso_px(), 58), False, 'torso')


def air_figure(face, far, near, **lower):
    """A body in the air: the duster, the far arm, the head, the near arm. far / near are
    (elbow, wrist, glove rows, glove anchor, glove turns) from the approved shoulders."""
    f = fig()
    duster(f, **lower)
    e, w, rows, anc, turns = far
    arm(f, (51, 43), e, w, False, 'far_arm')
    glove(f, rows, w, anc, turns, 'far_hand')
    hp = P.head(face)
    f.stamp(hp, True, 'head')
    e, w, rows, anc, turns = near
    arm(f, (32, 43), e, w, True, 'near_arm')
    glove(f, rows, w, anc, turns, 'near_hand')
    return f, hp


# ------------------------------------------------------------------ TURNING INTO THE FRAME
SEAL_KEYS = set(gk.SEAL_KEYS) | {'v'}

# What the last frame built drew as HIM (his body, turned and placed) and as keylined props (the hat,
# his cards, the dust), for the lint and the layout numbers: measurements of where he is must not be
# thrown off by an effect, and a keyline check must not flag a glint that has no keyline on purpose.
REC = {'body': {}, 'props': {}}


def recorded(fn):
    def wrapped(*a, **kw):
        REC['body'], REC['props'] = {}, {}
        return finish(fn(*a, **kw))
    wrapped.__name__ = fn.__name__
    return wrapped


def place(f, deg, at, feats=()):
    """Relight the figure for a turn of deg, turn it about the pivot and put the pivot on `at` in
    the juggle frame."""
    # The rig's own pass (ground_kit.seal), with one key more: a moved part never leaves an open edge,
    # and the approved sprite's one open pixel (the coat's dark inside between his boots, which the
    # rig's seal skips) is closed too, so the audit is clean.
    K.seal(f.px, SEAL_KEYS)
    lit = K.relight(f, deg, P.FAMILIES, SLOPES, gain=GAIN)
    if deg % 90 == 0:
        out = K.rot90(lit, deg // 90, PIV, at)
    else:
        out = K.rekeyline(K.rotate_with_features(lit, deg, PIV, at, feats))
    REC['body'].update(K.clip(out, W, H))
    return out


def finish(g):
    """The last pass on a finished frame: every pinhole a turn or a stacked part left is closed,
    with keyline where it is walled in by keyline (so the approved collar slits close too; the audit
    is clean), and everything outside the frame goes."""
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


def prop(layers, deg, at, pivot, label='prop'):
    """A separate prop (the hat) through its own figure: relit and turned about its own pivot."""
    f = K.Fig(LW, LH, OFF)
    for part, o in layers:
        f.stamp(part, o, label)
    lit = K.relight(f, deg, P.FAMILIES, SLOPES, gain=GAIN)
    pv = f.local(pivot)
    if deg % 90 == 0:
        out = K.rot90(lit, deg // 90, pv, at)
    else:
        out = K.rekeyline(K.rotsprite(lit, deg, pv, at))
    REC['props'].update(K.clip(out, W, H))
    return out


def hat_prop(deg, at):
    """His hat, flying free: the approved hat, relit and turned about its own centre."""
    return prop(rig.hat_layers(), deg, at, gk.HAT_CENTRE, 'hat')


def loose(kind, cx, cy, deg):
    c = gk.loose_card(kind, cx, cy, deg)
    REC['props'].update(K.clip(c, W, H))
    return c


def cards(g, specs, behind=False):
    for kind, cx, cy, d in specs:
        (under if behind else over)(g, loose(kind, cx, cy, d))


def dust(g, specs):
    for (x, y, r) in specs:
        pf = P.puff(x, y, r)
        REC['props'].update({q: k for q, k in K.clip(pf, W, H).items() if q not in g})
        under(g, pf)


# ------------------------------------------------------------------ THE SLOPES (measured once)
def _measure_slopes():
    f = fig()
    labels = ['torso', 'far_up', 'far_fore', 'far_hand', 'head', 'hat', 'hat', 'hat', 'hat',
              'near_up', 'near_fore', 'fan', 'near_hand']
    for (part, o), lab in zip(rig.approved_frame0_layers(), labels):
        f.stamp(part, o, lab, flat=(lab == 'fan'))
    return K.fit_slopes(f.px, K.fig_normals(f), P.FAMILIES)


SLOPES = _measure_slopes()
GAIN = 1.3


# ------------------------------------------------------------------ 0-1 THE HIT
@recorded
def launch():
    """The uppercut lands under his chin. Thrown back from the fist, the head snapped over, eyes
    squeezed and the jaw hanging; the hat pops off and the fan bursts in his hand. His feet are
    still on the mat."""
    f = fig()
    lean = gk.Lean(-1, 5)
    sway = gk.sway_rows({y: (1, 2) for y in range(62, 71)}, {y: 4 for y in range(64, 71)})
    f.stamp(lean.torso(gk.torso_px(sway)), False, 'torso')
    hx = lean.dx(31)
    sn, sf = lean.pt(32, 43), lean.pt(51, 43)
    arm(f, sf, (59, 39), (64, 32), False, 'far_arm', ([(0, -1)], [(-1, 0)]))
    glove(f, SPLAY, (64, 32), SPLAY_AT, 0, 'far_hand')
    f.stamp(rig.mv(head_turned('agape', -18), hx - 1, 0), True, 'head')
    arm(f, sn, (sn[0] - 7, 45), (16.5, 41.5), True, 'near_arm')
    # the fan, splayed wide as it bursts, and the glove still round its pivot
    f.stamp(rig.mv(gk.fan_spread(-3, -2), -5, -5), False, 'fan', flat=True)
    f.stamp(rig.mv(rig.near_hand_px(), -5, -5), False, 'near_hand')
    g = place(f, 0, STAND_AT)
    head = {(q[0] - PIV[0] + STAND_AT[0], q[1] - PIV[1] + STAND_AT[1]) for q in f.masks['head']}
    over(g, hat_prop(-24, (75, 44)))                  # knocked straight up, starting to turn
    cards(g, (('diamond', 46, 70, -70), ('spade', 51, 56, -25), ('heart', 40, 87, -120)))
    fx = {}
    gk.burst(fx, 84, 81, r=8)                         # the fist, under his chin: never over his face
    over(g, {q: k for q, k in fx.items() if q not in head})
    under(g, P.lines([((95, 70), (101, 64)), ((97, 78), (105, 76)), ((92, 86), (99, 91))]))
    dust(g, ((68, 116, 3), (94, 116, 3), (60, 117, 2), (101, 117, 2)))
    return g


@recorded
def launch_lift():
    """A beat later: off the mat and tipping back, knees dangling, arms still flung up, the coat
    hanging long below him; the last of the fan spraying away and the hat spinning off over his head."""
    f, hp = air_figure('agape',
                       far=((58, 36), (61, 28), SPLAY, SPLAY_AT, 0),
                       near=((25, 37), (21, 29), SPLAY, SPLAY_AT, 0),
                       flare=3, sway=-2, hem=74, knees=((37, 65), (47, 65)), ankles=((36, 73), (48, 74)),
                       boots=((32, 74), (44, 75)))
    g = place(f, -12, (AIR_AT[0], AIR_AT[1] + 14), features_at(f, hp))
    over(g, hat_prop(-38, (122, 40)))
    cards(g, (('heart', 46, 40, -150), ('diamond', 34, 58, -40), ('club', 40, 78, 20), ('spade', 124, 62, 75)))
    under(g, P.lines([((72, 106), (72, 114)), ((82, 109), (82, 117)), ((92, 105), (92, 112))], '9'))
    dust(g, ((64, 116, 3), (100, 116, 3), (56, 117, 2)))
    return g


# ------------------------------------------------------------------ 2-6 THE TUMBLE
@recorded
def hang():
    """The apex: the moment he stops rising. Limp and surprised -- weightless for a beat, the arms
    drift loose, the knees dangle, the duster billows out round him and the cards hang in the air."""
    f, hp = air_figure('surprised',
                       far=((59, 38), (62, 46), LIMP, LIMP_AT, 0),
                       near=((24, 38), (21, 46), LIMP, LIMP_AT, 0),
                       flare=6, sway=3, hem=73, knees=((38, 63), (46, 64)), ankles=((36, 70), (49, 71)),
                       boots=((32, 71), (45, 72)))
    g = place(f, -35, AIR_AT, features_at(f, hp))
    cards(g, (('heart', 36, 36, -20), ('diamond', 126, 44, 30), ('club', 30, 86, 60),
              ('spade', 122, 92, -45), ('heart', 104, 32, 80)))
    return g


# One cartwheel, a quarter turn a frame, counter-clockwise. Everything loose lags the turn: in his
# own frame the hem swings left, the far arm is swept down behind him and the near arm up, and they
# change from frame to frame so the turn never reads as one sprite spun.
SPIN = [
    dict(deg=-90, face='yell', flare=5, sway=-4,
         far=((59, 49), (66, 53), SPLAY, SPLAY_AT, 1), near=((25, 38), (19, 33), SPLAY, SPLAY_AT, 3),
         knees=((36, 64), (48, 63)), ankles=((32, 71), (53, 70)), boots=((28, 72), (49, 71)),
         cards=(('diamond', 40, 22, 10), ('spade', 130, 70, 100), ('heart', 66, 106, -30))),
    dict(deg=-180, face='agape', flare=6, sway=-6,
         far=((60, 45), (66, 40), SPLAY, SPLAY_AT, 1), near=((24, 45), (17, 49), SPLAY, SPLAY_AT, 3),
         knees=((37, 64), (47, 64)), ankles=((34, 71), (50, 71)), boots=((30, 72), (46, 72)),
         cards=(('diamond', 124, 26, 100), ('spade', 104, 106, 190), ('heart', 28, 72, 60))),
    dict(deg=-270, face='yell', flare=5, sway=-3,
         far=((58, 49), (61, 57), LIMP, LIMP_AT, 0), near=((25, 40), (20, 34), SPLAY, SPLAY_AT, 0),
         knees=((38, 63), (46, 64)), ankles=((34, 69), (49, 72)), boots=((30, 70), (45, 73)),
         cards=(('diamond', 124, 96, 190), ('spade', 34, 98, 280), ('heart', 90, 14, 150))),
    dict(deg=-330, face='agape', flare=6, sway=-5,
         far=((59, 40), (65, 34), SPLAY, SPLAY_AT, 1), near=((25, 49), (20, 55), LIMP, LIMP_AT, 0),
         knees=((37, 63), (49, 64)), ankles=((33, 70), (53, 71)), boots=((29, 71), (49, 72)),
         cards=(('diamond', 34, 96, 280), ('spade', 40, 24, 10), ('heart', 126, 58, 240))),
]


@recorded
def tumble(i):
    s = SPIN[i]
    f, hp = air_figure(s['face'], s['far'], s['near'], flare=s['flare'], sway=s['sway'],
                       knees=s['knees'], ankles=s['ankles'], boots=s['boots'])
    g = place(f, s['deg'], AIR_AT, features_at(f, hp))
    wheel(g, s['deg'])
    trail(g, s['deg'])
    return g


def head_angle(deg):
    """The screen bearing of his head from the tumble centre (0 right, 90 down)."""
    return -90 + deg


def trail(g, deg, reach=55):
    """The arcs he is sweeping: behind the head and behind the feet (the turn is counter-clockwise,
    so behind is the clockwise side)."""
    h = head_angle(deg)
    under(g, P.arc(AIR_AT[0], AIR_AT[1], 48, h + 18, h + 18 + reach, 36))
    under(g, P.arc(AIR_AT[0], AIR_AT[1], 42, h + 198, h + 198 + reach * 0.8, 31))


WHEEL = ('diamond', 'spade', 'heart')


def wheel(g, deg, r=(54, 50, 52)):
    """The fan's cards wheeling round him, turning with him: three, a third of a turn apart. A card
    that would land on him slides round the wheel (never up out of it) until it is clear."""
    import math
    h = head_angle(deg)
    body = set(REC['body'])

    def card_at(kind, a, rr):
        cx = int(round(AIR_AT[0] + rr * math.cos(math.radians(a))))
        cy = int(round(AIR_AT[1] + rr * 0.62 * math.sin(math.radians(a))))
        return cx, cy, gk.loose_card(kind, cx, cy, a + 90)

    for j, kind in enumerate(WHEEL):
        base = h + 60 + 120 * j
        pick = None
        for rr in (r[j], r[j] + 4, r[j] + 8):
            for da in (0, 15, -15, 30, -30, 45, -45):
                cx, cy, c = card_at(kind, base + da, rr)
                near = {(x + dx, y + dy) for (x, y) in c for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)}
                if not (near & body) and min(y for x, y in c) >= 24:
                    pick = (cx, cy, base + da)
                    break
            if pick:
                break
        if pick:
            over(g, loose(kind, pick[0], pick[1], pick[2] + 90))


# ------------------------------------------------------------------ 7-11 DOWN
# His arms on the mat, in his own frame (turned, local right is up the screen and local down is to
# his feet): (elbow, wrist, glove rows, anchor, turns) for the far and near arm.
ARMS_FLUNG = (((58, 38), (63, 31), SPLAY, SPLAY_AT, 0), ((25, 38), (20, 31), SPLAY, SPLAY_AT, 0))
ARMS_FLOP = (((59, 42), (62, 49), LIMP, LIMP_AT, 0), ((24, 42), (20, 36), SPLAY, SPLAY_AT, 0))
ARMS_REST = (((56, 51), (57, 59), LIMP, LIMP_AT, 0), ((27, 51), (25, 59), LIMP, LIMP_AT, 0))


# The breath, lying on his back: the far half of his chest (turned, the top of him on screen) swells
# one pixel while his back stays on the mat. In his own frame that is a sideways widening of the
# torso's right half over the chest rows, so the column at the seam repeats to close the gap.
BREATH_SEAM = 45
BREATH_ROWS = range(36, 59)


def widen(px, seam=BREATH_SEAM, rows=BREATH_ROWS, dx=1):
    out = {}
    for (x, y), k in px.items():
        out[(x + dx, y) if (x > seam and y in rows) else (x, y)] = k
    for (x, y), k in px.items():
        if x == seam and y in rows:
            for i in range(1, dx + 1):
                out[(x + i, y)] = k
    return out


def lying(face, arms, boots_up=0, flare=3, breath=0):
    """The approved torso with its duster spread flat round him, about to be laid on his back."""
    f = fig()
    sway = gk.sway_rows({y: (-flare, flare) for y in range(58, 71)}, {y: 4 for y in range(63, 71)})
    torso = gk.torso_px(sway, far_boot=(boots_up, 0), near_boot=(-boots_up // 2, 0))
    if breath:
        torso = widen(torso, dx=breath)
    f.stamp(torso, False, 'torso')
    (fe, fw, frows, fanc, fturn), (ne, nw, nrows, nanc, nturn) = arms
    b = breath
    arm(f, (51 + b, 43), (fe[0] + b, fe[1]), (fw[0] + b, fw[1]), False, 'far_arm')
    glove(f, frows, (fw[0] + b, fw[1]), fanc, fturn, 'far_hand')
    f.stamp(P.head(face), True, 'head')
    arm(f, (32, 43), ne, nw, True, 'near_arm')
    glove(f, nrows, nw, nanc, nturn, 'near_hand')
    return f


HAT_REST = (24, 81)
# his cards, lying where they came down: in front of him, behind him, one by his boots
FLOOR_CARDS = ((40, 111, 'heart'), (122, 111, 'diamond'), (118, 65, 'spade'), (10, 97, 'club'),
               (68, 65, 'heart'))


@recorded
def crash():
    """Back-first into the mat: slammed two pixels into it, arms thrown up, a knee kicked up by the
    impact, the duster's far panel flapping; dust thrown out flat along the canvas both ways and the
    cards he was carrying bouncing off it. The hat is still falling."""
    f = fig()
    duster(f, flare=5, sway=0, hem=72, knees=((37, 64), (53, 61)), ankles=((34, 72), (60, 64)),
           boots=((30, 73), (57, 65)), boot_cut=(2, 0))
    (fe, fw, frows, fanc, fturn), (ne, nw, nrows, nanc, nturn) = ARMS_FLUNG
    arm(f, (51, 43), fe, fw, False, 'far_arm')
    glove(f, frows, fw, fanc, fturn, 'far_hand')
    f.stamp(P.head('agape'), True, 'head')
    arm(f, (32, 43), ne, nw, True, 'near_arm')
    glove(f, nrows, nw, nanc, nturn, 'near_hand')
    g = place(f, -90, (DOWN_AT[0], DOWN_AT[1] - 1))      # the coat's near panel spread to the mat line
    over(g, hat_prop(-150, (34, 20)))
    dust(g, ((22, 113, 5), (36, 116, 3), (10, 115, 3), (136, 112, 5), (150, 115, 3), (122, 116, 3)))
    under(g, P.lines([((28, 104), (14, 96)), ((132, 104), (146, 96)), ((44, 110), (30, 108)),
                      ((116, 110), (130, 108)), ((60, 64), (56, 56)), ((104, 64), (108, 56)),
                      ((82, 60), (82, 52))]))
    cards(g, (('heart', 62, 58, 40), ('diamond', 124, 70, -60), ('spade', 100, 52, 150)))
    return g


@recorded
def bounce():
    g = place(lying('wince', ARMS_FLOP, boots_up=1, flare=3), -90, (DOWN_AT[0], DOWN_AT[1] - 4))
    over(g, hat_prop(-230, (30, 50)))
    dust(g, ((12, 110, 5), (28, 114, 4), (140, 110, 5), (152, 114, 3)))
    cards(g, (('heart', 56, 72, 120), ('diamond', 120, 70, -150)))
    return g


@recorded
def settle():
    g = place(lying('ko', ARMS_REST, flare=3), -90, DOWN_AT)
    over(g, hat_prop(-12, (HAT_REST[0], HAT_REST[1] - 2)))
    dust(g, ((12, 114, 3), (148, 114, 3)))
    for (x, y, kind) in FLOOR_CARDS[:3]:
        under(g, P.floor_card(x, y, kind))
    return g


@recorded
def down(breath=0):
    g = place(lying('ko', ARMS_REST, flare=3, breath=breath), -90, DOWN_AT)
    over(g, hat_prop(0, HAT_REST))
    for (x, y, kind) in FLOOR_CARDS:
        under(g, P.floor_card(x, y, kind))
    return g


FRAMES = [
    ('launch_contact', launch, 0.06),
    ('launch_lift', launch_lift, 0.08),
    ('hang', hang, 0.20),
    ('tumble_a', lambda: tumble(0), 0.07),
    ('tumble_b', lambda: tumble(1), 0.06),
    ('tumble_c', lambda: tumble(2), 0.06),
    ('tumble_d', lambda: tumble(3), 0.07),
    ('crash_impact', crash, 0.06),
    ('crash_bounce', bounce, 0.08),
    ('crash_settle', settle, 0.12),
    ('down_rest', lambda: down(0), 0.40),
    ('down_breathe', lambda: down(1), 0.40),
]
