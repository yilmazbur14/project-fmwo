"""PORTAL MONTE: Josh's own frames, built from his approved rig (art_source/josh_redesign, read-only) the
way his ride and ground sheets are: the approved head, hat, collar, torso, sleeves, gloves, boots and
duster, re-posed; nothing of his is redrawn.

  josh_monte_slash   128x80, feet (64,79): he bursts out of a small gate, dashes and slashes with a
                     sabre of his gold cards stacked edge to edge. 0-1 the dash, 2 CONTACT, 3 the
                     follow-through. The real Josh, the fakes and the punish all play it.
  josh_dive          80x80, feet (40,79): crouch, leap, dive, dive, vanish (folded into cards).
  josh_emerge        80x80, feet (40,79): the vanish undone: cards fold out into him, he drops out of the
                     gate, lands with a thud and a burst of cards, and comes up into his recover.
  josh_monte_scatter 96x96, pivot at the figure's centre: a fake coming apart into his cards.

All poses are written in his standard 80x80 frame's coordinates (feet on row 79, x = 40 the anchor) on an
unclipped canvas, then cut into each sheet's frame.
"""
import math
import random

import jh_lib as H
import jh_cards as C

JL = H.JL
gk = H.gk
josh3 = H.josh3
rig = H.rig
import anims_ride as R          # noqa: E402  (read-only: parts only; its __main__ is never run)
import anims_ground as AG       # noqa: E402

from lib import amap, fill, rim, poly                           # noqa: E402
from josh3 import capsule                                      # noqa: E402


# ------------------------------------------------------------------ an unclipped canvas

class Free:
    """lib.Canvas without the 80x80 clip: parts may run off any side while a pose is built."""

    def __init__(self):
        self.px = {}

    def stamp(self, part, outline=True):
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body:
                        self.px[q] = 'k'
        self.px.update(part)

    def under(self, part):
        for q, k in part.items():
            if q not in self.px:
                self.px[q] = k


def cut(px, fw, fh, ox, oy):
    """Shift a pose (80-frame coordinates) by (ox, oy) into a fw x fh frame; what falls outside is dropped."""
    return {(x + ox, y + oy): k for (x, y), k in px.items() if 0 <= x + ox < fw and 0 <= y + oy < fh}


def mv(px, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in px.items()}


# ------------------------------------------------------------------ the rider pose, on the free canvas

def rider(bob=0, torso=R.TORSO_AT, per=R.LEAN_PER, phase=0.0, front=R.ARM_FWD, back=R.ARM_TRAIL,
          tail=None, legs=None, boots=((51, R.RIDE_SOLE), (19, R.RIDE_SOLE)), face=None, hat=None,
          extras_back=(), extras_mid=(), extras_front=(), wind=None, back_over_head=True, boot_parts=(),
          front_under=False):
    """anims_ride.pose(), unclipped: skirt, legs, boots, collar, the sheared approved torso, the far
    ("front") arm, head and hat, the near ("back") arm, effects. extras_mid go between the far arm and
    the head (the sabre, held in the far hand, passes behind his head); hat: layers to use instead of
    the approved hat (moved with the head); back_over_head False puts the near arm under the head."""
    tdx, tdy = torso[0], torso[1] + bob
    hdx = tdx + R.lean_at(R.NECK_ROW, 59, per)
    hdy = tdy
    cv = Free()
    for part in extras_back:
        cv.under(part)
    if tail is not False:
        spec = dict(tail or {})
        spec.setdefault('phase', phase)
        for key, dflt in (('top_root', 51), ('bot_root', 63), ('top_tip', 47), ('bot_tip', 55)):
            spec[key] = spec.get(key, dflt) + bob
        cv.stamp(R.flag_tail(**spec))
    L = legs or {}
    cv.stamp(R.leg_shape(*L.get('front', ((45, 61 + bob), (55, 63 + bob), (55, 69)))))
    cv.stamp(R.leg_shape(*L.get('back', ((38, 62 + bob), (30, 66 + bob), (24, 69)))))
    for (bx, sole) in boots:
        cv.stamp(R.boot(bx, sole), outline=False)
    for part in boot_parts:
        cv.stamp(part, outline=False)
    if front and front_under:
        s, e, w, hand, at = front
        for p in R.sleeve(_b(s, bob), _b(e, bob), _b(w, bob), lit=False):
            cv.stamp(p)
        if hand:
            cv.stamp(amap(hand, at[0], at[1] + bob), outline=False)
        front = None
    for c in josh3.collar():
        cv.stamp(mv(c, hdx, hdy))
    cv.stamp(mv(R.hshear(R.torso_top(), 59, per), tdx, tdy), outline=False)
    near_layers = []
    if back:
        s, e, w, hand, at = back
        for p in R.sleeve(_b(s, bob), _b(e, bob), _b(w, bob), lit=True):
            near_layers.append((p, True))
        if hand:
            near_layers.append((amap(hand, at[0], at[1] + bob), False))
    if not back_over_head:
        for p, o in near_layers:
            cv.stamp(p, outline=o)
    if front:
        s, e, w, hand, at = front
        for p in R.sleeve(_b(s, bob), _b(e, bob), _b(w, bob), lit=False):
            cv.stamp(p)
        for part, outline in extras_mid:
            cv.stamp(part, outline=outline)
        if hand:
            cv.stamp(amap(hand, at[0], at[1] + bob), outline=False)
    else:
        for part, outline in extras_mid:
            cv.stamp(part, outline=outline)
    if face is not False:
        cv.stamp(mv(face or josh3.head(), hdx, hdy))
    for part, o in (hat if hat is not None else josh3.hat()):
        cv.stamp(mv(part, hdx, hdy), outline=o)
    if back_over_head:
        for p, o in near_layers:
            cv.stamp(p, outline=o)
    for part, outline in extras_front:
        cv.stamp(part, outline=outline)
    if wind:
        clear_of(cv, R.speed_lines(wind))
    return cv


def _b(p, bob):
    return (p[0], p[1] + bob)


def clear_of(cv, part, gap=1):
    drawn = set(cv.px)
    for (x, y), k in part.items():
        if all((x + dx, y + dy) not in drawn for dx in range(-gap, gap + 1) for dy in range(-gap, gap + 1)):
            cv.px[(x, y)] = k


def head_at(bob=0, torso=R.TORSO_AT, per=R.LEAN_PER):
    """Where rider() puts the approved head (its offset from the standing frame)."""
    return torso[0] + R.lean_at(R.NECK_ROW, 59, per), torso[1] + bob


def trailing_boot(ankle, deg):
    """A side-on boot on a leg trailing behind him: the approved side boot mirrored (toe back) and
    turned by deg (clockwise) about its shaft, its shaft top on the ankle."""
    rows = [r[::-1] for r in R.BOOT_SIDE]
    w = len(rows[0])
    part = amap(rows, 0, 0)
    pivot = (w - 3, 1)
    turned = gk.rotate(part, deg, pivot) if deg else part
    return mv(turned, int(round(ankle[0] - pivot[0])), int(round(ankle[1] - pivot[1])))


# ------------------------------------------------------------------ the sabre of stacked gold cards

GOLD_ACROSS = ['Y', 'O', 'O', 'o', 'G']      # a card's bands across the blade, lit edge first


def gold_card_quad(corners, pip=False):
    """A gold card (his signature card's colours) as any quad: bands across its width from the edge
    nearer the light (upper left) in 'Y' to the far one in 'G', black keyline, an optional black spade."""
    body = JL.poly([(float(x), float(y)) for x, y in corners])
    if not body:
        return {}
    a, b, c, d = corners
    ax, ay = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    dx_, dy_ = (d[0] + c[0]) / 2.0, (d[1] + c[1]) / 2.0
    vx, vy = dx_ - ax, dy_ - ay
    L2 = vx * vx + vy * vy or 1.0
    lit_from_a = (vx + vy) > 0            # edge a-b lies toward the upper left
    part = {}
    for (x, y) in body:
        t = ((x - ax) * vx + (y - ay) * vy) / L2
        t = max(0.0, min(0.999, t if lit_from_a else 1.0 - t))
        part[(x, y)] = GOLD_ACROSS[int(t * len(GOLD_ACROSS))]
    if pip:
        mx = sum(p[0] for p in corners) / 4.0
        my = sum(p[1] for p in corners) / 4.0
        for r, row in enumerate(C.PIPS3['spade']):
            for cc, ch in enumerate(row):
                q = (int(math.floor(mx - 1 + 0.5)) + cc, int(math.floor(my - 1 + 0.5)) + r)
                if ch != '.' and q in part:
                    if all((q[0] + ex, q[1] + ey) in body for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        part[q] = 'k'
    return H.keyline(part)


def blade_line(hilt, deg, length, bend):
    """The sabre's spine: from the hilt along `deg` (0 = right, 90 = down), bending by `bend` texels at
    the tip toward the spine's left-hand normal (a sabre's curve). Returns f(t) -> (point, tangent)."""
    a = math.radians(deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = uy, -ux                       # left of the direction of travel (up, for a blade pointing right)

    def f(t):
        s = t * length
        off = bend * t * t
        p = (hilt[0] + ux * s + nx * off, hilt[1] + uy * s + ny * off)
        dt = 2 * bend * t / max(1e-6, length)
        tx, ty = ux + nx * dt, uy + ny * dt
        tl = math.hypot(tx, ty)
        return p, (tx / tl, ty / tl)
    return f


def sabre(hilt, deg, length=38.0, bend=3.0, n=5, w=6.0, overlap=2.0, pips=True, guard=True):
    """His gold cards laid end to end into one sabre, from the fist at `hilt` along `deg` (0 = right,
    90 = down), bending `bend` texels at the tip: one blade silhouette, keylined once, its cards told
    apart by dark-gold seams and a black spade on each; the last card tapers to the point; a cross-guard
    of one of his cream cards at the hilt. Lit from the upper left. Returns [(part, outline)]."""
    f = blade_line(hilt, deg, length, bend)
    seglen = (length + overlap * (n - 1)) / n
    owner = {}
    seams = set()
    pip_at = []
    for i in range(n):
        s0 = i * (seglen - overlap)
        s1 = s0 + seglen
        (p0, _), (p1, _) = f(s0 / length), f(min(1.0, s1 / length))
        cs = C.seg(p0, p1, w, w if i < n - 1 else 1.2)
        part = JL.poly(cs)
        a, b, c, d = cs
        fx, fy = (a[0] + d[0]) / 2.0, (a[1] + d[1]) / 2.0
        ux, uy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        for q in part:
            owner[q] = i
            if i > 0:
                along = (q[0] - fx) * ux + (q[1] - fy) * uy
                if -0.5 <= along < 0.7:
                    seams.add(q)
        if i < n - 1:
            pip_at.append(f((s0 + seglen * 0.55) / length)[0])
    body = set(owner)
    px = {}
    for q in body:
        n4 = [(q[0] + 1, q[1]) in body, (q[0] - 1, q[1]) in body, (q[0], q[1] + 1) in body, (q[0], q[1] - 1) in body]
        if not all(n4):
            px[q] = 'Y' if (not n4[3] or not n4[1]) else 'G'
        else:
            px[q] = 'O'
    for q in list(px):
        if px[q] == 'O' and px.get((q[0], q[1] - 1)) == 'Y':
            px[q] = 'Y' if (q[0] + q[1]) % 3 else 'O'
    for q in seams:
        if px.get(q) in ('O', 'Y'):
            px[q] = 'G'
    if pips:
        for (mx, my) in pip_at:
            ox, oy = int(math.floor(mx - 1 + 0.5)), int(math.floor(my - 1 + 0.5))
            for r, row in enumerate(C.PIPS3['spade']):
                for cc, ch in enumerate(row):
                    q = (ox + cc, oy + r)
                    if ch != '.' and q in px and all((q[0] + ex, q[1] + ey) in body
                                                      for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        px[q] = 'k'
    layers = []
    if guard:
        (gx, gy), (tx, ty) = f(0.0)
        nx, ny = -ty, tx
        cs = C.seg((gx - nx * 5.5 + tx * 0.5, gy - ny * 5.5 + ty * 0.5), (gx + nx * 5.5 + tx * 0.5, gy + ny * 5.5 + ty * 0.5),
                   3.6, 3.6)
        layers.append((C.quad(cs, 0, 'face', None), False))
    layers.append((H.keyline(px), False))
    return layers


def sabre_tip(hilt, deg, length=38.0, bend=4.0):
    return blade_line(hilt, deg, length, bend)(1.0)[0]


# ------------------------------------------------------------------ THE SLASH (128x80, feet (64,79))

SLASH_FW, SLASH_FH = 128, 80
SLASH_FEET = (64, 79)
SLASH_OX = SLASH_FEET[0] - 40            # 80-frame x to slash-frame x
SLASH_TIMES = [0.08, 0.10, 0.10, 0.16]   # 0-1 the dash (0.18, HARD), 2 CONTACT, 3 follow-through
GROUND = 79
# The contact frame's sabre (frame 2): its hilt, heading and length, in the 80-frame's coordinates.
CONTACT_HILT, CONTACT_DEG, CONTACT_LEN = (68, 61), -12.0, 34.0


def _contact_point(along=0.6):
    """The sabre's sweet spot on the contact frame, from his feet, in texels (x toward the blade)."""
    (x, y), _ = blade_line(CONTACT_HILT, CONTACT_DEG, CONTACT_LEN, 2.5)(along)
    return (round(x - 40, 1), round(y - 79, 1))


GRIP = [
    # the far glove closed round the sabre's grip, knuckles to the viewer
    ".kkkk.",
    "kTRRRk",
    "kRTRRk",
    "kRRRVk",
    ".kVVk.",
]


def trail_cards(pts):
    """A few of his cards peeling off behind him, spinning: [(part, outline)]."""
    out = []
    for (kind, cx, cy, deg) in pts:
        out.append((gk.loose_card(kind, cx, cy, deg), False))
    return out


def slash_pose(i):
    """The four slash frames' pixels, in 80-frame coordinates."""
    focus = gk.head('focus')
    if i == 0:
        # out of the gate: low and launching off the back foot, the sabre trailing low behind him,
        # both arms swept back, his cards still peeling off behind as he comes through
        bob = 8
        torso = (-4, 3)
        legs = {'front': ((45, 68), (55, 70), (58, 73)), 'back': ((38, 69), (27, 72), (17, 74))}
        boots = ((56, GROUND), (14, GROUND))
        tail = dict(x_root=37, x_tip=-5, top_tip=35, bot_tip=45, amp=1.6, lam=15.0, phase=0.4)
        front = ((55, 47), (50, 54), (44, 57), None, None)
        back = ((38, 47), (30, 46), (23, 43), R.HAND_BACK, (16, 39))
        hilt = (42, 65)
        blade = sabre(hilt, 172.0, length=36.0, bend=-2.5)
        grip = [(amap(AG.GRIP_HAND, int(hilt[0]) - 3, int(hilt[1]) - 3), False)]
        cards = trail_cards([('heart', 6, 40, -40), ('spade', 14, 30, 25), ('diamond', 2, 26, 70)])
        cv = rider(bob=bob, torso=torso, per=2, legs=legs, boots=boots, tail=tail, front=front, back=back,
                   face=focus, extras_back=[p for p, _ in cards], extras_mid=blade + grip,
                   wind=[(0, 50, 8), (4, 62, 10), (1, 56, 6)])
        return cv.px
    if i == 1:
        # the draw: dashing in, the sabre held back flat at his near hip like a blade in its sheath
        bob = 5
        legs = {'front': ((46, 65), (57, 66), (60, 73)), 'back': ((39, 66), (29, 70), (20, 74))}
        boots = ((58, GROUND), (17, GROUND))
        tail = dict(x_root=38, x_tip=-2, top_tip=40, bot_tip=50, amp=1.8, lam=14.0, phase=1.3)
        front = ((56, 47), (50, 52), (43, 55), None, None)
        back = ((39, 47), (31, 43), (24, 38), R.HAND_BACK, (17, 34))
        hilt = (41, 61)
        blade = sabre(hilt, 181.0, length=38.0, bend=2.0)
        grip = [(amap(AG.GRIP_HAND, int(hilt[0]) - 3, int(hilt[1]) - 3), False)]
        cv = rider(bob=bob, per=2, legs=legs, boots=boots, tail=tail, front=front, back=back, face=focus,
                   extras_mid=blade + grip, wind=[(0, 44, 9), (2, 70, 12), (0, 30, 7)])
        return cv.px
    if i == 2:
        # CONTACT: the lunge, the sabre drawn from his hip in one rising cut across the player's middle;
        # the smear sweeps up from the floor in front of him to the blade
        bob = 8
        torso = (-1, 3)
        legs = {'front': ((49, 68), (61, 69), (65, 73)), 'back': ((41, 69), (29, 73), (16, 74))}
        boots = ((63, GROUND), (13, GROUND))
        tail = dict(x_root=40, x_tip=1, top_tip=39, bot_tip=50, amp=1.4, lam=16.0, phase=2.2)
        front = ((58, 47), (62, 51), (66, 54), R.FIST, (64, 51))
        back = ((41, 47), (32, 43), (24, 39), R.HAND_BACK, (17, 35))
        hilt = CONTACT_HILT
        blade = sabre(hilt, CONTACT_DEG, length=CONTACT_LEN, bend=2.5)
        sm = {}
        gk.crescent(sm, [(52, 78), (70, 77), (87, 72), (98, 63), (102, 53)],
                    [(54, 76), (71, 73), (86, 67), (94, 60), (97, 55)], keys=('G', 'o', 'O', 'Y'))
        cv = rider(bob=bob, torso=torso, per=2, legs=legs, boots=boots, tail=tail, front=front, back=back,
                   face=focus, extras_back=[sm], extras_mid=blade)
        px = cv.px
        gk.sparkle(px, 100, 47, True)
        return px
    # follow-through: the cut carried on up and away, rising out of the lunge, the smear thinning
    bob = 5
    torso = (0, 3)
    legs = {'front': ((50, 66), (60, 67), (63, 73)), 'back': ((42, 67), (31, 71), (20, 74))}
    boots = ((61, GROUND), (17, GROUND))
    tail = dict(x_root=41, x_tip=5, top_tip=44, bot_tip=55, amp=1.2, lam=16.0, phase=3.0)
    front = ((57, 46), (63, 44), (68, 40), R.FIST, (66, 37))
    back = ((38, 46), (31, 47), (24, 48), R.HAND_BACK, (17, 44))
    hilt = (70, 44)
    blade = sabre(hilt, -40.0, length=34.0, bend=2.5)
    sm = {}
    tip = blade_line(hilt, -40.0, 34.0, 2.5)(1.0)[0]
    tip = (int(math.floor(tip[0] + 0.5)), int(math.floor(tip[1] + 0.5)))
    gk.crescent(sm, [(70, 67), (86, 64), (96, 54), (tip[0] + 2, 40), (tip[0] + 1, tip[1] + 4)],
                [(70, 69), (88, 67), (100, 56), (tip[0] + 6, 40), (tip[0] + 4, tip[1] + 5)], keys=('G', 'o', 'O'))
    cv = rider(bob=bob, torso=torso, per=3, legs=legs, boots=boots, tail=tail, front=front, back=back,
               face=gk.head('smirk'), extras_back=[sm], extras_mid=blade)
    px = cv.px
    for (sx, sy, big) in ((tip[0] + 5, tip[1] - 4, True), (tip[0] - 6, tip[1] - 2, False), (tip[0] + 7, tip[1] + 12, False)):
        gk.sparkle(px, sx, sy, big)
    return px


SLASH_CONTACT = None          # set below, once blade_line exists


def slash_frame(i):
    px = gk.fill_pinholes(slash_pose(i))
    return cut(px, SLASH_FW, SLASH_FH, SLASH_OX, 0)


# ------------------------------------------------------------------ THE DIVE (80x80, feet (40,79))
# The airborne frames are built upright on the juggle's posing kit (art_source/josh_juggle, read-only):
# an upright figure, relit for its turn and turned with RotSprite, the face's features put back crisp.

import os as _os                                                   # noqa: E402
import sys as _sys                                                 # noqa: E402
_JUGGLE = _os.path.join(H.ART, 'josh_juggle')
if _JUGGLE not in _sys.path:
    _sys.path.insert(0, _JUGGLE)
import poses as JP              # noqa: E402  (read-only: its own sheet is never built from here)
import jparts as JPP            # noqa: E402
import jkit as K                # noqa: E402

DIVE_FW = DIVE_FH = 80
DIVE_TIMES = [0.12, 0.10, 0.10, 0.10, 0.08]      # crouch, leap, dive, dive, vanish: 0.50 (HARD)
DIVE_ANGLE = 45.0                                # the dive's heading, degrees above the horizontal (up-right)
DIVE_CENTRE = (42, 41)                           # where the airborne body's middle sits in the cell (frames 1-3)
VANISH_AT = (50, 33)                             # the vanish's twist of cards, up the dive's heading
PINCH_UP = AG.PINCH_UP
PINCH_AT = (2, 5)


def figure(face, far, near, lower, hat=True, fan=None, far_over_hat=False, card=None):
    """An upright figure on the juggle kit, with the hat ON: duster, far arm, head, hat, near arm.
    far / near: (elbow, wrist, glove rows, glove anchor, glove quarter turns) from the approved
    shoulders; far_over_hat raises the far arm in front of the hat (a reach past the brim); card: a
    card (part) pinched in the far hand, stamped with it. Returns (fig, head px)."""
    f = JP.fig()
    JP.duster(f, **lower)

    def far_arm():
        e, w, rows, anc, turns = far
        JP.arm(f, (51, 43), e, w, False, 'far_arm')
        if card:
            f.stamp(card, False, 'card', flat=True)
        if rows:
            JP.glove(f, rows, w, anc, turns, 'far_hand')
    if not far_over_hat:
        far_arm()
    hp = JPP.head(face, hatless=not hat)
    f.stamp(hp, True, 'head')
    if hat:
        for part, o in rig.hat_layers():
            f.stamp(part, o, 'hat')
    if far_over_hat:
        far_arm()
    e, w, rows, anc, turns = near
    JP.arm(f, (32, 43), e, w, True, 'near_arm')
    if rows:
        JP.glove(f, rows, w, anc, turns, 'near_hand')
    if fan:
        for part, o in fan:
            f.stamp(part, o, 'fan', flat=True)
    return f, hp


def turned(f, hp, deg, at):
    """The figure relit for a turn of deg (clockwise), turned about his waistcoat and put there."""
    return JP.place(f, deg, at, JP.features_at(f, hp))


def card_ring(cx, cy, n, r, phase, kinds=('spade', 'heart', 'diamond', 'club'), ry=None, spin=0.0):
    """Cards circling a point (for the dive's swirl and the vanish): [(part, outline)]."""
    out = []
    ry = r if ry is None else ry
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * ry
        deg = math.degrees(a) + 90 + spin
        out.append((gk.loose_card(kinds[i % len(kinds)], int(math.floor(x + 0.5)), int(math.floor(y + 0.5)), deg), False))
    return out


def fold_into_cards(g, axis_deg, centre, cut, kinds=('spade', 'heart', 'diamond', 'club', 'heart', 'spade'),
                    n=6, spacing=6.0, spread=5.0, seed=3):
    """His leading part folding away into cards: every pixel of g further than `cut` texels along the
    heading from `centre` goes, and a stream of his cards takes its place, spinning, spread either side
    of the heading line."""
    a = math.radians(-axis_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    out = {q: k for q, k in g.items() if (q[0] - centre[0]) * ux + (q[1] - centre[1]) * uy <= cut}
    out = K.rekeyline(out)
    rnd = random.Random(seed)
    cards = []
    for i in range(n):
        along = cut + 3 + spacing * i
        side = spread * (1 if i % 2 else -1) * (0.6 + 0.4 * rnd.random())
        x = centre[0] + ux * along + nx * side
        y = centre[1] + uy * along + ny * side
        cards.append(gk.loose_card(kinds[i % len(kinds)], int(math.floor(x + 0.5)), int(math.floor(y + 0.5)),
                                   axis_deg + rnd.uniform(-60, 60)))
    for c in cards:
        JP.over(out, c)
    return out


def card_stream(start, heading, n, spacing, spread, seed=3,
                kinds=('spade', 'heart', 'diamond', 'club', 'heart', 'spade', 'diamond')):
    """His cards streaming away from `start` along `heading` (degrees above the horizontal), spinning,
    spread either side of the line: [(part, outline)], nearest first."""
    a = math.radians(-heading)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        along = spacing * i
        side = spread * (1 if i % 2 else -1) * (0.5 + 0.5 * rnd.random()) * min(1.0, 0.4 + i * 0.25)
        x = start[0] + ux * along + nx * side
        y = start[1] + uy * along + ny * side
        out.append((gk.loose_card(kinds[i % len(kinds)], int(math.floor(x + 0.5)), int(math.floor(y + 0.5)),
                                  -heading + 90 + rnd.uniform(-70, 70)), False))
    return out


def dive_pose(i):
    """The five dive frames' pixels, in the 80-frame's coordinates."""
    if i == 0:
        # CROUCH: sunk low on bent knees to spring, arms swept back, the fan snapped shut in the near
        # hand; eyes up on the gate ahead
        bob = 10
        legs = {'front': ((46, 71), (56, 68), (55, 73)), 'back': ((38, 72), (31, 71), (25, 74))}
        boots = ((52, GROUND), (22, GROUND))
        tail = dict(x_root=38, x_tip=10, top_tip=48, bot_tip=58, amp=1.0, lam=16.0, phase=0.5, sweep=5)
        front = ((56, 47), (49, 55), (39, 59), R.HAND_BACK, (32, 55))
        back = ((39, 47), (31, 51), (24, 54), R.HAND_BACK, (17, 50))
        face = rig.mv(gk.head_rot('focus', -9), 0, -1)
        hat = gk.hat(0, -1, deg=-12, pivot=(42, 38))
        cv = rider(bob=bob, per=3, legs=legs, boots=boots, tail=tail, front=front, back=back, face=face,
                   hat=hat, front_under=True)
        return gk.seal(cv.px, w=10 ** 6, h=10 ** 6)
    if i == 1:
        # LEAP: springing up and forward off the back foot, the far arm reaching up at the gate with a
        # card pinched in it, the deck flung on ahead of him
        bob = -3
        legs = {'front': ((45, 58), (54, 60), (54, 67)), 'back': ((38, 59), (33, 67), (28, 74))}
        boots = ((51, 73),)
        tail = dict(x_root=38, x_tip=8, top_tip=52, bot_tip=64, amp=1.4, lam=16.0, phase=0.9, sweep=5)
        front = ((56, 47), (62, 39), (66, 31), PINCH_UP, (64, 26))
        back = ((39, 47), (32, 50), (25, 52), R.HAND_BACK, (18, 48))
        card = [(gk.card_up('spade', 67, 25 + bob), False)]
        cv = rider(bob=bob, per=3, legs=legs, boots=boots, tail=tail, front=front, back=back,
                   face=gk.head('focus'), extras_mid=card,
                   boot_parts=[trailing_boot((29, 72), 60)])
        px = cv.px
        for (k, x, y, d) in (('spade', 70, 13, 40), ('heart', 61, 8, 10), ('diamond', 71, 24, 70)):
            JP.over(px, gk.loose_card(k, x, y, d))
        return gk.seal(px, w=10 ** 6, h=10 ** 6)
    if i in (2, 3):
        # DIVE: flung out flat toward the gate, leaning hard into it: the far arm thrust ahead with the
        # card leading him in, the near arm swept back, legs trailing, the duster streaming behind; his
        # cards swirl round him. 3: he starts to fold away into them, the card, hand and hat first.
        bob = -2
        legs = {'front': ((44, 58), (35, 63), (26, 66)), 'back': ((38, 59), (28, 66), (18, 71))}
        tail = dict(x_root=38, x_tip=2, top_tip=50, bot_tip=62, amp=1.6, lam=14.0, phase=2.0 + i, sweep=6)
        front = ((58, 47), (66, 42), (72, 37), PINCH_UP, (70, 32))
        back = ((41, 47), (36, 53), (29, 57), R.HAND_BACK, (22, 53))
        card = [(gk.card_up('spade', 73, 31 + bob), False)]
        if i == 2:
            cv = rider(bob=bob, torso=(-1, 3), per=2, legs=legs, boots=(), tail=tail, front=front, back=back,
                       face=gk.head('focus'), extras_mid=card,
                       boot_parts=[trailing_boot((25, 65), 35), trailing_boot((17, 70), 45)])
        else:
            # the card, the hand, the head and the hat are already cards, streaming on up into the gate
            cv = rider(bob=bob, torso=(-1, 3), per=2, legs=legs, boots=(), tail=tail, front=None, back=back,
                       face=False, hat=[], boot_parts=[trailing_boot((25, 65), 35), trailing_boot((17, 70), 45)])
            stream = card_stream((50, 38), 40.0, 6, 4.6, 4.5)
            for part, o in stream:
                cv.stamp(part, outline=o)
        g = gk.seal(cv.px, w=10 ** 6, h=10 ** 6)
        streaks = {}
        for (x0, y0, n) in ((3, 50, 8), (8, 76, 9), (2, 64, 6)):
            for t in range(n):
                streaks[(x0 + t, y0 - t // 2)] = '8' if t < n // 3 else ('9' if t < n - 2 else '0')
        clear = {q: k for q, k in streaks.items()
                 if all((q[0] + dx, q[1] + dy) not in g for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
        if i == 2:
            for part, o in card_ring(42, 44, 5, 28, 0.9, ry=21):
                JP.under(g, part)
        JP.under(g, clear)
        return g
    # VANISH: folded away into his cards: a tight twist of them and a last glint
    g = {}
    for part, o in card_ring(VANISH_AT[0], VANISH_AT[1], 5, 7, 2.4, ry=5, spin=30):
        JP.over(g, part)
    gk.sparkle(g, VANISH_AT[0] + 11, VANISH_AT[1] - 9, True)
    gk.sparkle(g, VANISH_AT[0] - 9, VANISH_AT[1] + 8, False)
    return g


def dive_frame(i):
    px = dive_pose(i)
    px = {q: k for q, k in px.items() if 0 <= q[0] < DIVE_FW and 0 <= q[1] < DIVE_FH}
    return gk.fill_pinholes(px)


# ------------------------------------------------------------------ THE EMERGE (80x80, feet (40,79))
# After the last round with no parry: he drops out of the gate onto the floor under it, lands with a
# thud in a burst of his cards, and comes up into his recover (winded, hands on knees): its last frame
# is josh_recovery frame 0 with the landing's cards settling round him.

EMERGE_TIMES = [0.08, 0.12, 0.14, 0.16]          # 0.50 (the plan's monte_emerge_time)
BRIM_HAND = AG.BRIM_HAND


def emerge_pose(i):
    if i == 0:
        # the gate spits his cards out and they fold back into him, legs first, falling
        g = {}
        for part, o in card_stream((40, 14), -90.0, 6, 5.0, 6.0, seed=5):
            JP.over(g, part)
        for part, o in card_ring(40, 20, 5, 13, 0.3, ry=9, spin=20):
            JP.under(g, part)
        gk.sparkle(g, 26, 10, True)
        gk.sparkle(g, 56, 16, False)
        gk.sparkle(g, 50, 40, False)
        return g
    if i == 1:
        # dropping out feet first, winded: a hand clamping the hat on, the other flung up, the duster
        # billowing up round him
        f, hp = figure('winded',
                       far=((60, 34), (57, 24), BRIM_HAND, (2, 4), 0),
                       near=((24, 38), (20, 30), JP.SPLAY, JP.SPLAY_AT, 0),
                       lower=dict(flare=6, sway=2, hem=70, knees=((38, 62), (46, 62)),
                                  ankles=((35, 67), (49, 67)), boots=((31, 68), (45, 68)), boot_cut=(1, 1)),
                       far_over_hat=True)
        g = turned(f, hp, -6.0, (40, 49))
        for (k, x, y, d) in (('heart', 12, 14, -30), ('spade', 70, 22, 50), ('diamond', 62, 9, 10)):
            JP.under(g, gk.loose_card(k, x, y, d))
        return g
    if i == 2:
        # THUD: down hard in a deep squat, arms thrown out for balance, his cards bursting out round
        # his boots and dust kicked up
        D = 10
        lean = gk.Lean(1, 8, 56 + D)
        L = AG.squat(D, lean, spread=6)
        hx = lean.dx(31 + D)
        sn, sf = lean.pt(32, 43 + D), lean.pt(51, 43 + D)
        L += gk.arm(sf, (61, 51 + D // 2), (67, 55), near=False, lit_up=[(0, -1)], lit_fore=[(0, -1)])
        L.append((amap(AG.SPLAY_HAND, 64, 49), False))
        L.append((rig.mv(gk.head_rot('wince', 6), hx + 1, D + 2), True))
        L += gk.hat(hx + 2, D + 2, deg=12, pivot=(42, 38))
        L += gk.arm(sn, (22, 51 + D // 2), (14, 56), near=True, lit_up=[(-1, 0)], lit_fore=[(0, -1)])
        L.append((amap(AG.SPLAY_HAND, 10, 50), False))
        cv = Free()
        for part, o in L:
            cv.stamp(part, outline=o)
        px = gk.seal(cv.px, w=10 ** 6, h=10 ** 6)
        for (k, x, y, d) in (('heart', 8, 68, -70), ('spade', 71, 66, 60), ('diamond', 15, 58, -30),
                             ('club', 65, 57, 35), ('heart', 72, 73, 95)):
            JP.under(px, gk.loose_card(k, x, y, d))
        gk.put(px, amap([".00.", "0990", "9889"], 20, 76), only_empty=True)
        gk.put(px, amap([".00.", "0990", "9889"], 58, 76), only_empty=True)
        gk.put(px, amap([".0.", "090", "989"], 4, 76), only_empty=True)
        gk.put(px, amap([".0.", "090", "989"], 72, 76), only_empty=True)
        return px
    # up into his recover: josh_recovery frame 0, his cards settling on the floor round him
    px = AG.recovery(0)
    for (k, x, y, d) in (('spade', 71, 72, 100), ('diamond', 8, 70, -95)):
        JP.under(px, gk.loose_card(k, x, y, d))
    return px


def emerge_frame(i):
    px = emerge_pose(i)
    px = {q: k for q, k in px.items() if 0 <= q[0] < DIVE_FW and 0 <= q[1] < DIVE_FH}
    return gk.fill_pinholes(px)


# ------------------------------------------------------------------ THE SCATTER (96x96, pivot centre)
# A fake at its contact instant: the figure comes apart into his cards, flung out from its middle.

SCATTER_FW = SCATTER_FH = 96
SCATTER_PIVOT = (48, 48)
SCATTER_TIMES = [0.05] * 6
_SCATTER_KINDS = ['heart', 'spade', 'diamond', 'club']


def _scatter_cards(seed=11, n=20):
    """The cards of one figure: where each starts (packed in a man-sized oval), which way it flies
    (straight out from the middle, all round), how far it gets, its spin, face or back."""
    rnd = random.Random(seed)
    order = list(range(n))
    random.Random(seed + 1).shuffle(order)
    cards = []
    for i in range(n):
        a = 2 * math.pi * (i + rnd.uniform(-0.3, 0.3)) / n
        r0 = rnd.uniform(0.25, 0.95)
        x0, y0 = math.cos(a) * 11.0 * r0, math.sin(a) * 24.0 * r0
        reach = rnd.uniform(24.0, 32.0)
        ux, uy = math.cos(a), math.sin(a) * 0.55
        cards.append(dict(x0=x0, y0=y0, ux=ux, uy=uy, reach=reach, life=(order[i] + 0.5) / n,
                          deg0=rnd.uniform(0, 360), spin=rnd.choice((-1, 1)) * rnd.uniform(40, 110),
                          kind=_SCATTER_KINDS[i % 4], back=(i % 3 == 2)))
    return cards


def _back_card(cx, cy, deg):
    """One of his cards face down (wine back, gold lattice), spinning free."""
    rows = [
        "kkkkkkkk",
        "kGooooGk",
        "koyzyzok",
        "kozyzyok",
        "koyzyzok",
        "kozyzyok",
        "koyzyzok",
        "kozyzyok",
        "kGooooGk",
        "kkkkkkkk",
    ]
    part = amap(rows, int(cx) - 4, int(cy) - 5)
    return gk.rotate(part, deg, (cx, cy))


def scatter_pose(i):
    g = {}
    cx, cy = SCATTER_PIVOT[0] - 0.5, SCATTER_PIVOT[1] - 0.5
    cards = _scatter_cards()
    # how far out each card has flown (a share of its reach, easing out), how far it has dropped
    out_k = [0.0, 0.34, 0.6, 0.78, 0.9, 1.0][i]
    drop = [0, 0, 1, 2, 4, 6][i]
    keep = [1.0, 1.0, 0.9, 0.75, 0.55, 0.3][i]
    for c in sorted([c for c in cards if c['life'] < keep], key=lambda c: c['y0']):
        x = cx + c['x0'] + c['ux'] * c['reach'] * out_k
        y = cy + c['y0'] + c['uy'] * c['reach'] * out_k + drop
        deg = c['deg0'] + c['spin'] * out_k * 3
        part = _back_card(x, y, deg) if c['back'] else gk.loose_card(c['kind'], int(math.floor(x + 0.5)),
                                                                     int(math.floor(y + 0.5)), deg)
        JP.over(g, part)
    if i == 0:
        # the pop: a white and gold ring flashed round the pack, in his shape
        body = set(g)
        ring = {}
        for (x, y) in body:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q not in body:
                        ring[q] = 'W'
        ring2 = {}
        for (x, y) in list(ring):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and q not in ring:
                    ring2[q] = 'Y'
        g.update(ring2)
        g.update(ring)
    else:
        for (sx, sy, big) in ((cx - 22, cy - 26, i < 3), (cx + 25, cy - 10, False), (cx - 8, cy + 31, i < 4),
                              (cx + 16, cy + 22, False)):
            gk.sparkle(g, int(sx), int(sy), big)
    return g


def scatter_frame(i):
    px = scatter_pose(i)
    return {q: k for q, k in px.items() if 0 <= q[0] < SCATTER_FW and 0 <= q[1] < SCATTER_FH}


SLASH_CONTACT = _contact_point()
# The figure's middle on the contact frame, from its feet (texels): where the scatter's pivot goes when a
# fake comes apart.
SLASH_CENTRE = (4, -32)
