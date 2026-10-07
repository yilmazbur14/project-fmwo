"""The card hands: a giant hand built ENTIRELY of Josh's cards, like a paper-craft gauntlet.

Seen from above (the back of the hand, palm down), fingers pointing down-screen, the wrist up toward
its portal: the classic top-down "hand from the ceiling" read. The back of the hand is a FAN of four
cards pinned at the wrist (his signature fan, with a card's corner index showing on each), every
finger is three cards shingled along the bone, the thumb three more, and across the wrist a cuff card
in his hat's wine with his hat badge (the gold-rimmed spade) pinned on it.

build() lays out the giant's RIGHT hand (thumb on its screen-right). render(mirror=True) mirrors the
card layout and re-lights it from the same upper-left light: that is the giant's LEFT hand, thumb on
its screen-left, toward Josh - the RIGHT portal's hand, which is the one the sheets deliver (jh_anims
MIRROR); the left portal's is the code's flip of it.

A pose is a small dict of knobs (spread, curl, thumb, ...). build(pose) lays the cards out as Facets
(a quad each, in palm-centred texels); render() stamps them back to front, each with its own black
keyline, and drops a one-pixel shadow from every card onto the cards under it, which is what gives the
stack its depth. Everything that moves cards around - forming, the shatter on a parry, the re-form -
moves these same facets, so no card appears from nowhere.
"""
import math

import jh_lib as H
import jh_cards as C

FW = FH = 128                 # frame size, texels
AX, AY = 64, 60               # the anchor: the centre of the back of the hand = the slam's centre
S = 1.2                       # overall size of the hand (1.0 = the proportions the tables are in)

SUITS = ['spade', 'heart', 'club', 'diamond']


def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def add(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s)


class Facet:
    """One card of the hand: a quad (anchor-relative texels), how it is drawn, and its stack order.
    dot: a one-pixel corner index (u, v, suit); tip: round off the far end (a fingertip)."""
    __slots__ = ('z', 'cs', 'side', 'pip', 'pip_uv', 'bias', 'name', 'part', 'dot', 'tip')

    def __init__(self, z, cs, side='face', pip=None, pip_uv=None, bias=0.0, name='', part='', dot=None,
                 tip=False):
        self.z, self.cs, self.side, self.pip, self.pip_uv = z, cs, side, pip, pip_uv
        self.bias, self.name, self.part, self.dot, self.tip = bias, name, part, dot, tip

    def centre(self):
        return (sum(p[0] for p in self.cs) / 4.0, sum(p[1] for p in self.cs) / 4.0)

    def copy(self, **kw):
        f = Facet(self.z, list(self.cs), self.side, self.pip, self.pip_uv, self.bias, self.name, self.part,
                  self.dot, self.tip)
        for k, v in kw.items():
            setattr(f, k, v)
        return f


# ------------------------------------------------------------------ the skeleton

KNUCKLES = [(-15.5, 8.0), (-5.5, 11.0), (4.5, 12.0), (14.0, 9.5)]   # pinky, ring, middle, index
SPLAY = [-24, -9, 2, 13]                                          # degrees off straight down
LENGTHS = [(9, 7, 6), (11, 8, 7.5), (12, 9, 8), (11, 8, 7)]       # phalanx lengths
WRIST = (0.0, -17.0)
THUMB_BASE = (12.5, -8.0)
FINGER_W = [(9.5, 9.0), (9.0, 8.0), (8.0, 7.0)]                   # card widths along each phalanx
THUMB_W = [(10.0, 9.5), (9.5, 8.5), (8.5, 7.5)]

POSE_DEFAULTS = dict(spread=1.0, curl=(0.2, 0.2, 0.2, 0.2), thumb=52.0, thumb_curl=0.2, fan_open=1.0,
                     wrist_len=1.0)


def pose(**kw):
    p = dict(POSE_DEFAULTS)
    p.update(kw)
    return p


def build(p):
    """The cards for pose p, anchor-relative, before any global transform."""
    F = []
    s = S
    z = 0
    # the thumb, under the fan
    tb = (THUMB_BASE[0] * s, THUMB_BASE[1] * s)
    d = rot((0, 1), -p['thumb'])
    tc = p['thumb_curl']
    j1 = add(tb, d, 11 * s * (1 - 0.1 * tc))
    d2 = rot(d, -8 - 25 * tc)
    j2 = add(j1, d2, 9 * s * (1 - 0.35 * tc))
    d3 = rot(d2, -8 - 30 * tc)
    tip = add(j2, d3, 7 * s * (1 - 0.5 * tc))
    segs = [(tb, j1, THUMB_W[0], 3, 1.5), (j1, j2, THUMB_W[1], 2, 1.5), (j2, tip, THUMB_W[2], 2, 0)]
    for i in (2, 1, 0):
        a, b, (w0, w1), bk, fw = segs[i]
        F.append(Facet(z, C.seg(a, b, w0 * s, w1 * s, bk, fw), bias=0.45 + 0.3 * i + 0.5 * tc * (i == 2),
                       name='thumb%d' % i, part='thumb', dot=(0.25, 0.7, 'heart') if i == 0 else None,
                       tip=(i == 2)))
        z += 1
    # the fingers: tip first, so the card nearer the knuckle sits on top (shingled toward the tip)
    for fi in range(4):
        k = (KNUCKLES[fi][0] * s, KNUCKLES[fi][1] * s)
        c = p['curl'][fi]
        d = rot((0, 1), -SPLAY[fi] * p['spread'])
        L = [ln * s for ln in LENGTHS[fi]]
        j1 = add(k, d, L[0] * (1 - 0.12 * c))
        j2 = add(j1, d, L[1] * (1 - 0.42 * c))
        tip = add(j2, d, L[2] * (1 - 0.62 * c))
        segs = [(k, j1, FINGER_W[0], 3, 1.5), (j1, j2, FINGER_W[1], 2, 1.5), (j2, tip, FINGER_W[2], 2, 0)]
        for i in (2, 1, 0):
            a, b, (w0, w1), bk, fw = segs[i]
            dot = (0.25, 0.7, SUITS[(fi + i) % 4]) if i < 2 else None
            F.append(Facet(z, C.seg(a, b, w0 * s, w1 * s, bk, fw),
                           bias=0.3 * i + 0.75 * c * (i == 2) + 0.35 * c * (i == 1),
                           name='%s%d' % ('prmi'[fi], i), part='finger%d' % fi, dot=dot, tip=(i == 2)))
            z += 1
    # the fan on the back of the hand: four cards pinned at the wrist, left under right, each showing
    # its corner index on the strip left uncovered; the top (index-side) card shows its whole face
    W = (WRIST[0] * s, WRIST[1] * s * p['wrist_len'])
    for fi in range(4):
        k = (KNUCKLES[fi][0] * s, KNUCKLES[fi][1] * s)
        k = add(W, (k[0] - W[0], k[1] - W[1]), p['fan_open'])
        cs = C.seg(add(W, (k[0] * 0.18, 0)), k, 7 * s, 12.5 * s, 1, 3)
        uv = (0.5, 0.62) if fi == 3 else (0.24, 0.8)
        F.append(Facet(100 + fi, cs, pip=SUITS[fi], pip_uv=uv, bias=-0.25, name='fan%d' % fi, part='fan'))
    # the cuff: one wine card laid across the wrist over the fan's pivot, like his hat band, and on it
    # the fan's pin, his hat's gold-rimmed spade
    cw, ch = p.get('cuff', (19.0, 10.0))
    cy0 = W[1] - 1.0
    F.append(Facet(150, [(-cw / 2 + 1, cy0 - ch / 2), (cw / 2 - 1, cy0 - ch / 2), (cw / 2, cy0 + ch / 2),
                         (-cw / 2, cy0 + ch / 2)], side='back', bias=0.2, name='cuff', part='cuff'))
    px_, py_ = W[0], cy0
    F.append(Facet(200, [(px_ - 1, py_ - 1), (px_ + 1, py_ - 1), (px_ + 1, py_ + 1), (px_ - 1, py_ + 1)],
                   name='pin', part='pin'))
    # the wrist's trail: small cards streaming back toward the portal, fluttering with the phase
    ph = p.get('tail')
    if ph is not None:
        for i, (dy, w, h) in enumerate(((-9.0, 9.0, 7.0), (-16.5, 7.5, 6.0), (-22.5, 6.0, 5.0))):
            sway = math.sin(2 * math.pi * (ph - 0.18 * i)) * (1.0 + 0.8 * i)
            cx, cy = W[0] + sway, W[1] + dy
            ang = math.sin(2 * math.pi * (ph - 0.18 * i) + 0.9) * 22
            cs = [rot(v, ang) for v in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            cs = [(cx + x, cy + y) for x, y in cs]
            F.append(Facet(90 - i, cs, side='back', bias=0.6 + 0.2 * i, name='tail%d' % i, part='tail'))
    return F


# The pin: his hat badge (a black spade with a gold rim, josh3.CROWN rows 7-13), keylined, lit from
# the upper left, 9 x 9, centred on its facet.
BADGE = [
    "...o...",
    "..oko..",
    ".okkko.",
    "okkkkko",
    "okkkkko",
    ".okoko.",
    "..oko..",
]


def _pin(keyed):
    part = H.JL.amap(BADGE, 1, 1)
    for (x, y), k in list(part.items()):
        if k == 'o':
            if x + y <= 6:
                part[(x, y)] = 'O'
            elif x + y >= 10:
                part[(x, y)] = 'G'
    if keyed:
        part = H.keyline(part)
    rows = []
    for y in range(9):
        rows.append(''.join(part.get((x, y), '.') for x in range(9)))
    return rows


PIN = _pin(True)          # flying free: keylined
PIN_ON_CUFF = _pin(False)  # on the cuff it sits like the badge on his hat: gold rim straight on the wine


# ------------------------------------------------------------------ transforms

def xform(F, scale=1.0, squash=1.0, stretch=1.0, tilt=0.0, dx=0.0, dy=0.0):
    """The whole hand scaled, squashed flat (squash < 1: pressed onto the floor, seen from above),
    stretched (motion), turned by tilt degrees about the anchor, and moved."""
    out = []
    for f in F:
        cs = []
        for (x, y) in f.cs:
            x, y = x * scale / math.sqrt(stretch), y * scale * squash * stretch
            x, y = rot((x, y), tilt)
            cs.append((x + dx, y + dy))
        out.append(f.copy(cs=cs))
    return out


# A card's own shape once it leaves the hand (w, h): in the hand a card is a facet (a fan wedge, a
# tapering phalanx); flying free it is one of his ordinary cards again.
FREE_SIZE = {'fan': (10.0, 14.0), 'cuff': (12.0, 9.0), 'thumb': (9.0, 12.0), 'tail': (8.0, 11.0)}


def free_size(f):
    if f.part.startswith('finger'):
        return [(9.0, 12.0), (8.5, 11.5), (8.0, 11.0)][int(f.name[-1])]
    return FREE_SIZE.get(f.part, (9.0, 12.0))


def as_card(f, t):
    """The facet's quad blended toward his standard card of its size (t = 1: fully a card), keeping its
    centre and its long axis."""
    if t <= 0 or f.part == 'pin':
        return f
    t = min(1.0, t)
    cx, cy = f.centre()
    a, b, c, d = f.cs
    ux, uy = (b[0] + c[0] - a[0] - d[0]) / 2.0, (b[1] + c[1] - a[1] - d[1]) / 2.0
    ul = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ul, uy / ul
    nx, ny = -uy, ux
    w, h = free_size(f)
    if f.part == 'cuff':
        w, h = h, w
    rect = [(cx - ux * h / 2 + nx * w / 2, cy - uy * h / 2 + ny * w / 2),
            (cx + ux * h / 2 + nx * w / 2, cy + uy * h / 2 + ny * w / 2),
            (cx + ux * h / 2 - nx * w / 2, cy + uy * h / 2 - ny * w / 2),
            (cx - ux * h / 2 - nx * w / 2, cy - uy * h / 2 - ny * w / 2)]
    # match the facet's own corner order (its a->b side is the +n side for seg(), -n for the cuff)
    da = math.hypot(a[0] - rect[0][0], a[1] - rect[0][1]) + math.hypot(c[0] - rect[2][0], c[1] - rect[2][1])
    db = math.hypot(a[0] - rect[3][0], a[1] - rect[3][1]) + math.hypot(c[0] - rect[1][0], c[1] - rect[1][1])
    if db < da:
        rect = [rect[3], rect[2], rect[1], rect[0]]
    cs = [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(f.cs, rect)]
    return f.copy(cs=cs, pip_uv=(0.5, 0.5) if t > 0.6 and f.pip else f.pip_uv, dot=None if t > 0.5 else f.dot,
                  tip=False if t > 0.5 else f.tip)


def card_move(f, dx=0.0, dy=0.0, turn=0.0, flip=1.0, grow=1.0, free=0.0):
    """One card moved, turned about its own centre, flipped (flip = cos of the flip angle: 1 face up,
    0 edge-on, negative shows the back), grown, and (free > 0) turned back into a plain card of its
    size. Returns a new facet."""
    f = as_card(f, free)
    cx, cy = f.centre()
    a, b, c, d = f.cs
    # the card's long axis runs from its a/d end to its b/c end; a flip squeezes it across that axis
    ux, uy = (b[0] + c[0] - a[0] - d[0]) / 2.0, (b[1] + c[1] - a[1] - d[1]) / 2.0
    ul = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ul, uy / ul
    k = max(0.12, abs(flip))
    cs = []
    for (x, y) in f.cs:
        rx, ry = x - cx, y - cy
        along = rx * ux + ry * uy
        acx, acy = rx - along * ux, ry - along * uy
        rx, ry = along * ux + acx * k, along * uy + acy * k
        rx, ry = rot((rx * grow, ry * grow), turn)
        cs.append((cx + rx + dx, cy + ry + dy))
    side = f.side
    if flip < 0:
        side = 'back' if f.side == 'face' else 'face'
    pip = f.pip if abs(flip) > 0.55 else None
    return f.copy(cs=cs, side=side, pip=pip)


# ------------------------------------------------------------------ light and render

# Where the palm's centre sits in the coordinates the facets are in (jh_anims moves every pose so the
# pivot is the origin); the light is measured from the palm's centre.
LIGHT_ORIGIN = [0.0, 0.0]


def shift(F, dx, dy):
    return [f.copy(cs=[(x + dx, y + dy) for (x, y) in f.cs]) for f in F]


def tone_of(f, mirror=False, extra=0.0):
    """Light from the upper left over the dome of the hand; the facet's own bias darkens the far
    phalanges and the thumb. A mirrored hand is lit after mirroring, from the same side."""
    cx, cy = f.centre()
    cx, cy = cx - LIGHT_ORIGIN[0], cy - LIGHT_ORIGIN[1]
    if mirror:
        cx = -cx
    t = 0.55 + 0.045 * cx + 0.03 * cy + f.bias + extra
    return max(0, min(3, int(round(t))))


DARKER = {'0': '9', '9': '8', '8': '7', '7': '6', 'Y': 'O', 'O': 'o', 'o': 'G', 'G': 'g', 'g': 'g',
          'z': 'y', 'y': 'x', 'x': 'w', 'w': 'w', 'R': 'V', 'V': 'v', 'T': 'R', '6': '5', '5': '5'}


TAKE = {'backs': False}      # take B ("wine deck"): the hand shows his cards' wine backs, not faces


def render(F, mirror=False, ox=AX, oy=AY, gilt=True, shadows=True, tone_extra=0.0, only=None):
    """Stamp the facets back to front into a px dict. Each card is keylined; where a card lies over
    others, the cards under it take a one-pixel shadow along its keyline's lower-right side."""
    if TAKE['backs']:
        F = [f.copy(side='back' if f.side == 'face' else 'face') if f.part not in ('pin', 'cuff') else f
             for f in F]
    px = {}
    owner = {}
    cuff = [f for f in F if f.part == 'cuff']
    cuff_px = H.JL.poly([((-x if mirror else x) + ox, y + oy) for (x, y) in cuff[0].cs]) if cuff else set()
    for n, f in enumerate(sorted(F, key=lambda f: f.z)):
        if only and not only(f):
            continue
        cs = [((-x if mirror else x) + ox, y + oy) for (x, y) in f.cs]
        if mirror:
            cs = [cs[3], cs[2], cs[1], cs[0]]
        if f.part == 'pin':
            cx = sum(c[0] for c in cs) / 4.0
            cy = sum(c[1] for c in cs) / 4.0
            on_cuff = all((int(math.floor(cx + 0.5)) + dx, int(math.floor(cy + 0.5)) + dy) in cuff_px
                          for dx in (-3, 3) for dy in (-3, 3))
            base = PIN_ON_CUFF if on_cuff else PIN
            rows = [r[::-1] for r in base] if mirror else base
            if mirror:
                rows = [r.replace('O', '#').replace('G', 'O').replace('#', 'G') for r in rows]
            part = H.JL.amap(rows, int(math.floor(cx + 0.5)) - 4, int(math.floor(cy + 0.5)) - 4)
        else:
            uv = f.pip_uv
            if uv and mirror:
                uv = (1.0 - uv[0], uv[1])
            tone = tone_of(f, mirror, tone_extra)
            if f.side == 'back':
                tone = min(tone, 2)          # the wine back's darkest step would read as a hole
            part = C.quad_uv(cs, tone, f.side, f.pip, gilt=gilt, pip_uv=uv, keyed=False)
            if not part:
                continue
            inner = {q for q in part if all((q[0] + dx, q[1] + dy) in part
                                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
            if f.tip:
                # round the fingertip: drop the body pixel at each far corner
                for corner in (cs[1], cs[2]):
                    q = min(part, key=lambda q: (q[0] - corner[0]) ** 2 + (q[1] - corner[1]) ** 2)
                    part.pop(q, None)
            if f.dot and f.side == 'face':
                u, v, suit = f.dot
                if mirror:
                    u = 1.0 - u
                a, b, c, d = cs
                p0 = (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)
                p1 = (d[0] + (c[0] - d[0]) * v, d[1] + (c[1] - d[1]) * v)
                q = (int(math.floor(p0[0] + (p1[0] - p0[0]) * u + 0.5)), int(math.floor(p0[1] + (p1[1] - p0[1]) * u + 0.5)))
                if q in inner:
                    part[q] = C.RED[tone] if suit in ('heart', 'diamond') else 'k'
            part = H.keyline(part)
        if shadows:
            body = set(part)
            for (x, y), k in part.items():
                if k != 'k':
                    continue
                for q in ((x + 1, y + 1), (x, y + 1), (x + 1, y)):
                    if q not in body and q in px and px[q] != 'k' and owner.get(q) != -n - 1:
                        px[q] = DARKER.get(px[q], px[q])
                        owner[q] = -n - 1
        for q, k in part.items():
            px[q] = k
            owner[q] = n
    return px


def glow_of(px, strong=False, width=2):
    """The additive glow ring round a drawn silhouette: gold, hot when strong."""
    body = set(px)
    g = {}
    ring = set(body)
    keys = ('U', 'u') if strong else ('u', 'q')
    for r in range(width):
        nxt = set()
        for (x, y) in ring:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and q not in g:
                    nxt.add(q)
        for q in nxt:
            g[q] = keys[min(r, len(keys) - 1)]
        ring = nxt | ring
    return g
