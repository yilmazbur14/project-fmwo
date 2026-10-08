"""Every card-hand clip, cut to the build plan's art contract (scratchpad josh_hands/PLAN.md), from the
one hand of jh_hand. A frame is the hand's cards (moved, turned, flipped as the beat needs), effects
drawn with it (opaque glints, no keyline, like Josh's own card sparkles) and the additive glow.

THE PIVOT (hard): the centre of the flat hand's floor footprint on the impact contact frame; on the air
frames, the point that comes down onto it. Every pose is laid out with that point at the origin, and a
frame puts it on the frame's centre column (the mirror axis), at PIVOT = (64, PY) in frame texels
(corner coordinates, Josh's convention: sprite.offset = frame_size / 2 - pivot).

DRAWN AS THE RIGHT PORTAL'S HAND (the giant's left hand: thumb on its screen-left side, toward Josh);
the left portal's hand is the code's mirror of it.

Clips (frame times in CLIPS; the totals are the contract's):
  form     7  0.60  cards swirl in from nothing and knit into the hover pose (reads without a portal)
  hover    6  0.10 each, seamless loop: palm down, the fingers drumming in a wave, a one-texel bob
  windup   2  0.15  the lock: fingers splay stiff, the cards bristle, the glow goes hot
  drop     2  0.25  falling and flattening (streaks run BESIDE the hand, so it plays in reverse as the rise)
  impact   4  0.05 / 0.05 / 0.05 / hold: 0 the contact (the hit resolves on it; the flat hand fills the
              footprint ellipse), 1-2 the pin (the cards jolt out and settle), 3 held flat
  shatter  6  0.30  a parry: the hand bursts into its cards, which spin out, flip and wink out; ends empty
"""
import math
import random

import jh_hand as HD
from jh_hand import pose, build, xform, card_move

FW = FH = 128
PX, PY = 64, 70                 # the pivot, frame texels (corner coordinates): column 64 is the mirror axis
SQUASH = 0.55                   # how flat the floor is: the hand pressed onto it, seen from the camera
MIRROR = True                   # the delivered hand is the RIGHT portal's

CLIPS = {
    'form': [0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 0.1],
    'hover': [0.1] * 6,
    'windup': [0.07, 0.08],
    'drop': [0.12, 0.13],
    'impact': [0.05, 0.05, 0.05, 0.3],
    'shatter': [0.04, 0.05, 0.05, 0.05, 0.05, 0.06],
}
LOOPS = {'hover'}
ORDER = ['form', 'hover', 'windup', 'drop', 'impact', 'shatter']

CONTACT = dict(spread=0.3, curl=(-0.05,) * 4, thumb=24.0, thumb_curl=0.0)


def _h(s):
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


# ------------------------------------------------------------------ the pivot

def _pivot():
    """P: the centre of the contact pose's silhouette (unsquashed), in palm-centred coordinates."""
    F = build(pose(**CONTACT))
    px = HD.render(F, ox=0, oy=0, shadows=False)
    xs = [x for x, y in px]
    ys = [y for x, y in px]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)


P = _pivot()
HD.LIGHT_ORIGIN[0], HD.LIGHT_ORIGIN[1] = -P[0], -P[1]


def base(p):
    """A pose's cards with the pivot at the origin."""
    return HD.shift(build(p), -P[0], -P[1])


def hand_at(p, **x):
    return xform(base(p), **x)


# ------------------------------------------------------------------ poses

def hover_pose(i, n=6):
    ph = i / float(n)
    curl = tuple(0.24 + 0.2 * math.sin(2 * math.pi * ph - 0.95 * k) for k in range(4))
    return pose(curl=curl, thumb=52 + 5 * math.sin(2 * math.pi * ph + 1.3), thumb_curl=0.25)


HOVER_BOB = [0, -1, -1, -1, 0, 0]


def contact_cards(squash=SQUASH, scale=1.0):
    return hand_at(pose(**CONTACT), squash=squash, scale=scale)


def bristle(F, amount, seed=0, jitter=0.0):
    """Push every card out from the pivot (the cards stand off each other: charging)."""
    rnd = random.Random(seed)
    out = []
    for f in F:
        cx, cy = f.centre()
        L = math.hypot(cx, cy) or 1.0
        k = amount * (0.4 + 0.6 * min(1.0, L / 30.0))
        out.append(card_move(f, cx / L * k + rnd.uniform(-jitter, jitter), cy / L * k + rnd.uniform(-jitter, jitter)))
    return out


def jolt(F, amount, lift=0.0):
    """On the floor: each finger's cards slide out along the finger (the tips most), the fan's cards
    lift a little off the pivot: the stack shaken by the blow."""
    out = []
    for f in F:
        cx, cy = f.centre()
        L = math.hypot(cx, cy) or 1.0
        if f.part.startswith('finger') or f.part == 'thumb':
            i = int(f.name[-1])
            k = amount * (0.35 + 0.4 * i)
            out.append(card_move(f, cx / L * k, cy / L * k * 0.6 - lift * (i == 2)))
        elif f.part == 'fan':
            out.append(card_move(f, cx / L * amount * 0.3, -lift * 0.5))
        else:
            out.append(f)
    return out


# ------------------------------------------------------------------ card flights

def _ring_slots(names_angles, radius, lift=0.0, squash=0.9):
    """Deal the cards round two rings in the order they sit round the pivot (an even spray, no clumps)."""
    names = sorted(names_angles, key=lambda n: names_angles[n])
    n = len(names)
    slots = {}
    if not n:
        return slots
    a0 = names_angles[names[0]]
    for i, nm in enumerate(names):
        a = a0 + 2 * math.pi * i / n
        r = radius * (1.0 if i % 2 == 0 else 0.68)
        slots[nm] = (math.cos(a) * r, math.sin(a) * r * squash - lift)
    return slots


def _angles(F):
    return {f.name: math.atan2(f.centre()[1], f.centre()[0]) for f in F if f.part != 'pin'}


def spin_of(f, seed=0):
    rnd = random.Random(_h(f.name) + seed * 7919)
    return rnd.choice((-1, 1)) * rnd.uniform(70, 160), rnd.random() < 0.5


def fly(F, slots, t, grow_to=1.0, seed=0, free_rate=2.2):
    """The cards of F at time t (0..1) of a flight to their slots: out (ease-out), turning, turning back
    into plain cards, the flippers showing their other side past half-way, shrinking toward grow_to."""
    out = []
    e = 1 - (1 - t) ** 2
    for f in F:
        cx, cy = f.centre()
        ex, ey = slots.get(f.name, (cx, cy - 20.0))
        dx, dy = (ex - cx) * e, (ey - cy) * e
        if f.part == 'pin':
            out.append(card_move(f, dx * 0.6, dy * 0.6))
            continue
        spin, flips = spin_of(f, seed)
        flip = math.cos(math.pi * min(1.0, t * 1.15)) if flips else 1.0
        g = 1.0 + (grow_to - 1.0) * t
        out.append(card_move(f, dx, dy, turn=spin * e, flip=flip, grow=g, free=min(1.0, t * free_rate)))
    return out


def swirl_in(F_home, slots, t, swirl=90.0, grow_from=0.45, seed=5):
    """The cards arriving home from their slots on a curl round the pivot: t = 0 at the slots (small,
    turned, some face-down), 1 home."""
    out = []
    e = t * t * (3 - 2 * t)
    for f in F_home:
        hx, hy = f.centre()
        gx, gy = slots.get(f.name, (hx, hy - 30.0))
        ha, hr = math.atan2(hy, hx), math.hypot(hx, hy)
        ga, gr = math.atan2(gy, gx), math.hypot(gx, gy)
        da = (ha - ga + math.pi) % (2 * math.pi) - math.pi
        a = ga + da * e + math.radians(swirl) * (1 - e) * e * 2
        r = gr + (hr - gr) * e
        x, y = r * math.cos(a), r * math.sin(a)
        if f.part == 'pin':
            out.append(card_move(f, x - hx, y - hy))
            continue
        spin, flips = spin_of(f, seed)
        flip = 1.0
        if flips and e < 0.5:
            flip = -math.cos(math.pi * e * 2) * 0.99 or 0.2
        g = grow_from + (1.0 - grow_from) * e
        out.append(card_move(f, x - hx, y - hy, turn=spin * (1 - e), flip=flip, grow=g,
                             free=max(0.0, 1.0 - e * 1.4)))
    return out


# ------------------------------------------------------------------ effects (opaque, no keyline)

def sparkle(fx, x, y, big=True):
    fx[(x, y)] = 'W'
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        fx[(x + dx, y + dy)] = 'Y'
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            fx[(x + dx, y + dy)] = 'O'


def streaks(fx, xs, y_top, y_bot, seed=0):
    """Vertical motion streaks at the given columns: pale in the middle, gold at both ends, so they read
    as speed whichever way the clip plays."""
    rnd = random.Random(seed)
    for x in xs:
        L = rnd.randint(int((y_bot - y_top) * 0.55), int(y_bot - y_top))
        y0 = int(y_top) + rnd.randint(0, int(y_bot - y_top) - L)
        for y in range(y0, y0 + L + 1):
            f = (y - y0) / float(max(1, L))
            fx[(x, y)] = 'Y' if 0.3 < f < 0.7 else ('O' if 0.12 < f < 0.88 else 'o')


# ------------------------------------------------------------------ frames

class Frame:
    """cards; fx (drawn where no card is) and over (drawn on top); glow None/'faint'/'mid'/'strong';
    dy the whole frame's bob; tone added to every card's tone (-1 = a flash)."""

    def __init__(self, cards, fx=None, glow='faint', dy=0, tone=0.0, over=None, rings=0):
        self.cards, self.fx, self.glow, self.dy, self.tone = cards, fx or {}, glow, dy, tone
        self.over = over or {}
        self.rings = rings          # opaque light rings round the hand, like his gold card's: 1 gold, 2 + orange


def clip_frames(name):
    if name == 'hover':
        return [Frame(hand_at(hover_pose(i)), dy=HOVER_BOB[i]) for i in range(6)]
    if name == 'windup':
        f0 = bristle(hand_at(pose(spread=1.2, curl=(0.02,) * 4, thumb=60, thumb_curl=0.1), scale=1.02), 1.0)
        p1 = pose(spread=1.36, curl=(-0.14,) * 4, thumb=68, thumb_curl=0.0)
        f1 = bristle(hand_at(p1, scale=1.05), 2.2, seed=3, jitter=0.4)
        fx0, fx1 = {}, {}
        for (x, y, b) in ((-38, -34, False), (40, 14, False)):
            sparkle(fx0, x, y, b)
        for (x, y, b) in ((-40, -30, True), (42, 16, True), (6, -44, False), (-42, 20, False)):
            sparkle(fx1, x, y, b)
        return [Frame(f0, fx0, glow='mid', dy=-1, rings=1), Frame(f1, fx1, glow='strong', dy=-2, tone=-1.0, rings=2)]
    if name == 'drop':
        f0 = hand_at(pose(spread=0.8, curl=(0.0,) * 4, thumb=45, thumb_curl=0.0), stretch=1.2, scale=1.02)
        fx0 = {}
        streaks(fx0, (-40, -35, 37, 43), -46, 30, seed=5)
        f1 = hand_at(pose(spread=0.5, curl=(-0.03,) * 4, thumb=32, thumb_curl=0.0), squash=0.78)
        fx1 = {}
        streaks(fx1, (-36, 36), -30, 18, seed=8)
        return [Frame(f0, fx0, glow='strong'), Frame(f1, fx1, glow='strong')]
    if name == 'impact':
        c = contact_cards()
        return [Frame(c, glow='strong', tone=-1.0),
                Frame(jolt(c, 2.0, lift=1.0), glow='mid'),
                Frame(jolt(c, 0.8), glow='faint'),
                Frame(c, glow=None)]
    if name == 'shatter':
        c = contact_cards()
        slots = _ring_slots(_angles(c), 50.0, lift=10.0)
        out = []
        steps = ((0.12, 1.0, 'strong', -0.8), (0.42, 1.0, 'strong', 0.0), (0.7, 0.95, 'mid', 0.0),
                 (0.9, 0.8, 'faint', 0.0), (1.0, 0.55, None, 0.0))
        for i, (t, g, glow, tone) in enumerate(steps):
            F = fly(c, slots, t, grow_to=g)
            fx = {}
            if i == 1:
                for (x, y, b) in ((-30, -34, True), (34, -30, True), (2, -46, False), (-44, 4, False)):
                    sparkle(fx, x, y, b)
            if i == 4:
                # the cards wink out: every other one is already a glint
                keep = []
                for k, f in enumerate(F):
                    if k % 2 and f.part != 'pin':
                        cx, cy = f.centre()
                        sparkle(fx, int(round(cx)), int(round(cy)), k % 4 == 1)
                    else:
                        keep.append(f)
                F = keep
            out.append(Frame(F, fx, glow=glow, tone=tone))
        out.append(Frame([], glow=None))                 # ends empty
        return out
    if name == 'form':
        home = hand_at(hover_pose(0))
        slots = _ring_slots(_angles(home), 52.0, lift=6.0)
        out = []
        # 0: glints where the cards will come from
        fx0 = {}
        for k, (x, y) in enumerate(list(slots.values())[::3]):
            sparkle(fx0, int(round(x)), int(round(y)), k % 2 == 0)
        out.append(Frame([], fx0, glow=None))
        # 1-4: the cards swirl in from the ring, growing out of the distance
        for t in (0.0, 0.3, 0.6, 0.85):
            out.append(Frame(swirl_in(home, slots, t), glow='mid' if t > 0.5 else 'faint'))
        # 5: whole, with a flash of gold
        fx5 = {}
        for (x, y, b) in ((-34, -30, True), (38, -24, False), (-28, 30, False), (32, 30, True)):
            sparkle(fx5, x, y, b)
        out.append(Frame(home, fx5, glow='strong', tone=-0.6))
        # 6: the hover pose, frame 0 exactly, so the loop takes over seamlessly
        out.append(Frame(home, glow='faint', dy=HOVER_BOB[0]))
        return out
    raise KeyError(name)


def render_frame(fr, mirror=MIRROR, glow_on=True):
    """(px, glow_px) for a frame, in frame texels (FW x FH). The pivot corner (PX, PY) is the pixel-centre
    point (PX - 0.5, PY - 0.5)."""
    ox, oy = PX - 0.5, PY - 0.5 + fr.dy
    px = HD.render(fr.cards, mirror=mirror, ox=ox, oy=oy, tone_extra=fr.tone) if fr.cards else {}

    def place(d):
        # effects are whole-texel offsets from the pivot corner: offset 0 is the texel right-below it;
        # mirrored, column PX + x becomes PX - 1 - x
        return {((PX - 1 - x) if mirror else (PX + x), PY + fr.dy + y): k for (x, y), k in d.items()}

    if fr.rings and px:
        body = set(px)
        for k in ('O', 'r')[:fr.rings]:
            ring = {}
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                    q = (x + dx, y + dy)
                    if q not in body and (k == 'O' or (dx == 0 or dy == 0)):
                        ring[q] = k
            px.update(ring)
            body = set(px)
    glow = {}
    if glow_on and fr.glow and px:
        strong = fr.glow in ('strong', 'mid')
        width = {'strong': 3, 'mid': 2, 'faint': 1}[fr.glow]
        glow = HD.glow_of(px, strong=strong, width=width)
        if fr.glow == 'faint':
            glow = {q: 'q' for q in glow}
    for q, k in place(fr.fx).items():
        if q not in px:
            px[q] = k
    for q, k in place(fr.over).items():
        px[q] = k
    px = {q: k for q, k in px.items() if 0 <= q[0] < FW and 0 <= q[1] < FH}
    glow = {q: k for q, k in glow.items() if 0 <= q[0] < FW and 0 <= q[1] < FH and q not in px}
    return px, glow


# ------------------------------------------------------------------ the footprint (hard)

def contact_silhouette(mirror=MIRROR):
    px, _ = render_frame(clip_frames('impact')[0], mirror=mirror, glow_on=False)
    return set(px)


def in_ellipse(x, y, rx, ry, cx=PX - 0.5, cy=PY - 0.5):
    """A frame texel (x, y) is in the footprint when its centre is inside the ellipse on the pivot."""
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def ellipse_px(rx, ry, cx=PX - 0.5, cy=PY - 0.5):
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if in_ellipse(x, y, rx, ry, cx, cy):
                out.add((x, y))
    return out


def fit_stats(rx, ry, sil=None):
    """(fill, worst sideways overshoot, worst vertical overshoot): the share of the ellipse the flat hand
    covers, and how many texels of the drawn hand lie outside it, sideways and up/down."""
    sil = sil if sil is not None else contact_silhouette()
    E = ellipse_px(rx, ry)
    fill = len(E & sil) / float(len(E))
    worst_x = worst_y = 0.0
    for (x, y) in sil:
        if (x, y) in E:
            continue
        # sideways: distance to the ellipse along the row
        dy = (y - (PY - 0.5)) / ry
        if abs(dy) <= 1.0:
            half = rx * math.sqrt(1.0 - dy * dy)
            ox_ = abs(x - (PX - 0.5)) - half
        else:
            ox_ = abs(x - (PX - 0.5))
        worst_x = max(worst_x, ox_)
        dx = (x - (PX - 0.5)) / rx
        if abs(dx) <= 1.0:
            halfy = ry * math.sqrt(1.0 - dx * dx)
            oy_ = abs(y - (PY - 0.5)) - halfy
        else:
            oy_ = abs(y - (PY - 0.5))
        worst_y = max(worst_y, oy_)
    return fill, worst_x, worst_y


def extents(sil):
    """How far the drawn hand reaches from the pivot: left, right, up, down (texels, to pixel edges)."""
    cx, cy = PX - 0.5, PY - 0.5
    xs = [x for x, y in sil]
    ys = [y for x, y in sil]
    return (cx - min(xs) + 0.5, max(xs) - cx + 0.5, cy - min(ys) + 0.5, max(ys) - cy + 0.5)


def best_footprint():
    """The footprint radii (whole texels): the smallest ellipse on the pivot that the flat contact hand
    overhangs by no more than 4 texels on any side (the contract says sideways; up and down are held
    to the same rule here), which it must also fill to at least 80%. The hit area is then never bigger
    than what is drawn, and the drawn hand never more than 4 texels bigger than the hit area."""
    sil = contact_silhouette()
    l, r, u, d = extents(sil)
    rx = int(math.ceil(max(l, r) - 4.0))
    ry = int(math.ceil(max(u, d) - 4.0))
    fill = len(ellipse_px(rx, ry) & sil) / float(len(ellipse_px(rx, ry)))
    return dict(rx=rx, ry=ry, fill=fill, reach=(l, r, u, d))
