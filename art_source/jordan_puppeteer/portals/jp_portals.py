"""APPROVAL PASS (2026-09-28): Josh's portals for Jordan's attack 3 (Josh + Eric), cut to the attack-3
architect's contract. Two takes for the user to pick from; NOTHING here ships.

  Take A  Jordan's own rift language (the shipped summon rift's burning rim, lit far wall, blood-red
          surface and embers), redrawn on the contract's exact ellipses.
  Take B  Josh's own card-gate: a ring of his playing cards standing round a dark blue vortex, in
          Jordan's rune blue (the user's pick for his magic). Reads as "Josh's portal", never as
          the rift that summons the puppets.

Every sequence is a strip per layer (portal_<kind>_<sequence>_<layer>.png, the eventual ship names):
  back   on the Floor, behind whatever stands in the portal: the hole, its far rim, the far cards;
  front  on the Stage (1 px under the anchor): the near rim, the near cards, the sword's collar;
  glow   on the Stage, ADDED: the light round the rim and over the hole.
The anchor is the opening's centre (the top-left corner of the anchor texel). The opening is the exact
ellipse of the contract's size round it; on the floor no energy lands more than RIM texels outside
it (only straight up over that footprint). No semi-alpha anywhere.
  spike  48x24 (24,16), opening 36x14: open 5 (the telegraph; the whole opening reads from frame 1)
         / burst 2 / hold 2 (loop) / suck 2 / close 3
  body   112x40 (56,26), opening 88x24: open 4 / hold 2 (loop, the feint exit's tell) / close 3
  sword  64x40 (32,28), opening 44x14: open 5 / plunge 3 (the splash up the blade) / loop 4 / close 4;
         its front layer carries a collar of the portal's surface round the blade, at least COLLAR
         rows over the sword's base, so the blade reads halfway in
Also (take-neutral): portal_spike_smear (32x96, anchor (16,95), 3 frames: rise, full, retract; drawn
BEHIND the blade) and eric_sword_spike_up (eric_thrown_sword_v2 f6 without its white spin arcs, which
otherwise show beside the point over every spike).

Every size, count and time is in SPEC / SEQS and the *_specs tables: re-cut by editing and re-running.
A bare run writes nothing; `python jp_portals.py --write` writes into this folder only, behind a guard
that refuses any write outside it (and the temp folder) and any process but Aseprite.
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PUP = os.path.dirname(HERE)
sys.path.insert(0, PUP)
sys.path.insert(0, os.path.join(PUP, 'staging'))
import jp_rig as R  # noqa: E402,F401  (puts the approved god rig on the path)
import jp_rift as RF  # noqa: E402
import jp_strings as S  # noqa: E402
import jp_staging as ST  # noqa: E402
import jg_base as B  # noqa: E402
import jg_god as G  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_runes as RU  # noqa: E402
from PIL import Image, ImageChops, ImageDraw  # noqa: E402

ROOT = B.ROOT
ERIC_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'Eric')
THROWN = os.path.join(ERIC_DIR, 'eric_thrown_sword_v2.png')
PLANTED = os.path.join(ERIC_DIR, 'eric_bearhug_planted_sword_v2.png')
PARRY_TELL = os.path.join(ROOT, 'Assets', 'Effects', 'parry_tell.png')
CONCEPTS = os.path.join(ROOT, 'art_source', 'jordan_puppets', 'concepts')

# ------------------------------------------------------------------ the contract
# (the attack-3 architect, through the coordinator, 2026-09-28). Texels; times in seconds a frame.
SPEC = {
    'spike': dict(frame=(48, 24), anchor=(24, 16), opening=(36, 14), cards=6, card=(5, 7)),
    'body': dict(frame=(112, 40), anchor=(56, 26), opening=(88, 24), cards=12, card=(7, 10)),
    'sword': dict(frame=(64, 40), anchor=(32, 28), opening=(44, 14), cards=8, card=(6, 8)),
}
SEQS = {
    'spike': (('open', (0.06, 0.06, 0.08, 0.10, 0.10)), ('burst', (0.03, 0.03)), ('hold', (0.07, 0.07)),
              ('suck', (0.06, 0.06)), ('close', (0.04, 0.04, 0.04))),
    'body': (('open', (0.04, 0.04, 0.06, 0.06)), ('hold', (0.08, 0.08)), ('close', (0.05, 0.05, 0.05))),
    'sword': (('open', (0.05, 0.05, 0.06, 0.07, 0.07)), ('plunge', (0.05, 0.05, 0.05)), ('loop', (0.10,) * 4),
              ('close', (0.05, 0.05, 0.05, 0.05))),
}
LOOPS = {('spike', 'hold'), ('body', 'hold'), ('sword', 'loop')}
RIM = 2                  # portal energy reaches at most this far outside the opening on the floor
SPIKE_RISE = 70          # texels of blade over the floor line at full rise
BLADE_AT = {'burst': (40, 70), 'hold': (70, 70), 'suck': (44, 16)}   # the blade in the previews
COLLAR = 10              # rows of the planted blade the sword portal's front covers over its base, at least
BLADE_HALF = 13          # Eric's blade is 26 texels across, keyline included
SMEAR = dict(frame=(32, 96), anchor=(16, 95))
SPADE = [(0, -3), (-1, -2), (0, -2), (1, -2), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
         (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2), (-1, 3), (0, 3), (1, 3)]

# ------------------------------------------------------------------ palettes
PAL_A = dict(RF.PAL)
GLOW_A = dict(RF.GLOW_PAL)
GLOW_A['F'] = (205, 170, 130, 255)
GLOW_A['E'] = (120, 70, 40, 255)
PAL_B = {
    'k': B.hx('000000'),
    'd': B.hx('17385A'), 'e': B.hx('2B6C99'), 'f': B.hx('66C6EC'), 'g': B.hx('D2F6FF'), 'w': B.hx('FFFFFF'),
    'b': B.hx('9ADCF4'),                          # the strings' bright
    'n': B.hx('0B1A2E'), 'm': B.hx('050C17'),
    'c': B.hx('FBF7EE'), 'C': B.hx('EDE4D6'),     # Josh's card face (sampled from card_projectile.png)
    'r': B.hx('D95763'),                         # his pip red
}
GLOW_B = {'x': (18, 46, 76, 255), 'y': (9, 24, 40, 255), 'z': (4, 11, 20, 255), 'F': (120, 170, 210, 255),
          'E': (50, 90, 130, 255)}
STEEL = {'w': (255, 255, 255, 255), 'g': (212, 216, 220, 255), 's': (163, 168, 174, 255)}   # the blade's own
TAKES = {
    'A': dict(name="Jordan's rift", pal=PAL_A, glow=GLOW_A),
    'B': dict(name="Josh's card-gate", pal=PAL_B, glow=GLOW_B),
}


# ------------------------------------------------------------------ geometry

def geo(piece, sx=1.0, sy=None):
    """(anchor x, anchor y, rx, ry): the opening's half-sizes at scale sx (and sy, default sx)."""
    sp = SPEC[piece]
    ax, ay = sp['anchor']
    return ax, ay, sp['opening'][0] / 2.0 * sx, sp['opening'][1] / 2.0 * (sx if sy is None else sy)


def inside(ax, ay, rx, ry, p, pad=0.0):
    if rx + pad <= 0.0 or ry + pad <= 0.0:
        return False
    u = (p[0] + 0.5 - ax) / (rx + pad)
    v = (p[1] + 0.5 - ay) / (ry + pad)
    return u * u + v * v <= 1.0


def disc(piece, sx=1.0, sy=None, pad=0.0):
    """The texels of the opening (the exact ellipse round the anchor point) at a scale, or `pad`
    texels wider all round."""
    ax, ay, rx, ry = geo(piece, sx, sy)
    W_, H_ = SPEC[piece]['frame']
    return {(x, y) for y in range(H_) for x in range(W_) if inside(ax, ay, rx, ry, (x, y), pad)}


def outline(mask):
    return {p for p in mask if any(q not in mask for q in B.neighbours4(p))}


def by_angle(piece, pts):
    ax, ay, rx, ry = geo(piece)
    return sorted(pts, key=lambda p: math.atan2((p[1] + 0.5 - ay) / ry, (p[0] + 0.5 - ax) / rx))


def far(piece, p):
    return p[1] + 0.5 < SPEC[piece]['anchor'][1]


def allowed(piece):
    """Where energy may land: the opening and RIM texels round it on the floor, and straight up over
    that footprint (what stands or rises in a portal goes up; nothing spreads across the floor)."""
    def make():
        ax, ay, rx, ry = geo(piece)
        W_, H_ = SPEC[piece]['frame']
        return {(x, y) for y in range(H_) for x in range(W_)
                if inside(ax, ay, rx, ry, (x, y), RIM) or (y + 0.5 < ay and abs(x + 0.5 - ax) <= rx + RIM)}
    return ST.cached(('allowed', piece), make)


def clip(piece, layers):
    ok = allowed(piece)
    return tuple({q: k for q, k in d.items() if q in ok} for d in layers)


def opening_box(piece):
    ax, ay = SPEC[piece]['anchor']
    w, h = SPEC[piece]['opening']
    return (ax - w // 2, ay - h // 2, ax + w // 2 - 1, ay + h // 2 - 1)


# ------------------------------------------------------------------ shared pieces

def glow_ring(piece, sx=1.0, sy=None):
    """Added light round the rim: one texel of x, then a checker of y (the whole RIM)."""
    inner, one, two = disc(piece, sx, sy), disc(piece, sx, sy, 1.0), disc(piece, sx, sy, 2.0)
    out = {}
    for p in two - inner:
        if p in one:
            out[p] = 'x'
        elif (p[0] + p[1]) % 2 == 0:
            out[p] = 'y'
    return out


def haze(piece, sx=1.0, sy=None, level=0, height=1.4):
    """Light standing over the hole (added): level 0 a faint haze, 1 a glow, 2 a beam with an E core."""
    ax, ay, rx, ry = geo(piece, sx, sy)
    if rx < 2:
        return {}
    top = int(math.floor(ay - ry))
    h = int(round(ry * height * (1.0 + 0.6 * level)))
    out = {}
    for k in range(h):
        y = top - 1 - k
        t = k / float(max(1, h))
        half = rx * (0.75 - 0.35 * t)
        for x in range(int(math.floor(ax - half)), int(math.ceil(ax + half))):
            d = abs(x + 0.5 - ax) / max(1.0, half)
            chk = (x + y) % 2 == 0
            if level >= 2 and d < 0.3 and t < 0.35:
                key = 'E'                 # hot only low down: what rises through it is not washed out
            elif level >= 1 and d < 0.6 and t < 0.6:
                key = 'x'
            elif t < 0.35:
                key = 'x' if level else 'y'
            elif t < 0.7:
                key = 'y'
            else:
                key = 'z' if chk else None
            if key:
                out[(x, y)] = key
    return out


def sparks(piece, n, rnd, keys, sx=1.0, rise=1.5):
    ax, ay, rx, ry = geo(piece, max(sx, 0.5))
    out = {}
    for q in range(n):
        x = int(math.floor(ax + rnd.uniform(-0.9, 0.9) * rx))
        y = int(math.floor(ay - ry * rnd.uniform(0.3, 1.0) - rnd.uniform(0, ry * rise)))
        out[(x, y)] = keys[q % len(keys)]
    return out


def collar(piece, height, phase, keys, flare=0):
    """The portal's surface climbing the planted blade (front layer): a funnel round the blade's base
    from the floor line up `height` rows (a slow +-1 wave along its lip), widest at the bottom.
    Returns ({pixel: key}, {pixel: glow key})."""
    ax, ay, rx, ry = geo(piece)
    body, band, lit_side, shade, side, top, hot = keys
    half_b, half_t = BLADE_HALF + 3 + flare, BLADE_HALF + 1 + flare
    out, lit = {}, {}
    for x in range(int(math.floor(ax - half_b)), int(math.ceil(ax + half_b))):
        dx = x + 0.5 - ax
        lip = height - 1 + int(round(math.sin(dx * 0.55 + phase * 2 * math.pi)))
        for k in range(lip + 1):
            y = ay - 1 - k
            t = k / float(max(1, height - 1))
            half = half_b + (half_t - half_b) * t
            if abs(dx) > half:
                continue
            u = dx / half
            if k == lip:
                key = hot if abs(dx) < half * 0.45 else top
                lit[(x, y - 1)] = 'x'
                if (x + y) % 2 == 0:
                    lit[(x, y - 2)] = 'y'
            elif abs(dx) > half - 1.0:
                key = side
            elif math.sin(dx * 0.32 - k * 0.55 - phase * 2 * math.pi) > 0.72:
                key = band                     # broad bands spiralling up round it
            elif u < -0.45:
                key = lit_side                 # rounded: lit from the left like the blade
            elif u > 0.5:
                key = shade
            else:
                key = body
            out[(x, y)] = key
    return out, lit


def droplets(piece, stage, rnd, keys):
    """The plunge's splash: drops thrown up round the blade (0 the peak, 1 falling, 2 settling)."""
    ax, ay, rx, ry = geo(piece)
    out = {}
    lo, hi = ((COLLAR + 6, COLLAR + 18), (COLLAR + 3, COLLAR + 11), (COLLAR - 2, COLLAR + 3))[stage]
    for q in range((12, 8, 4)[stage]):
        side = -1 if q % 2 else 1
        x = int(math.floor(ax + side * rnd.uniform(BLADE_HALF - 2 + 2 * stage, BLADE_HALF + 5 + 2 * stage)))
        y = ay - 1 - rnd.randint(lo, hi)
        out[(x, y)] = keys[0] if q % 3 else keys[1]
        if stage < 2:
            out[(x, y + 1)] = keys[2]
    return out


# ------------------------------------------------------------------ take A: the rift's language

EMBERS_A = [(-0.62, -0.5, 1.0, 0), (-0.25, 0.3, 1.2, 1), (0.12, -0.3, 1.3, 2), (0.45, 0.4, 1.1, 3),
            (0.80, 0.5, 0.9, 4), (-0.85, -0.6, 0.9, 5), (0.30, -0.4, 1.25, 6), (-0.42, 0.4, 1.15, 7)]
NE_A = len(EMBERS_A)


def a_embers(piece, clock, sx=1.0, front=False, avoid=None):
    """Embers rising off the far rim (the rift's EMBER_LIFE keys); even emitters in front."""
    ax, ay, rx, ry = geo(piece, sx)
    top = ay - ry
    out = {}
    for e, ages in (clock or {}).items():
        ex, drift, rise, idx = EMBERS_A[e]
        if (idx % 2 == 0) != front:
            continue
        for age in ages:
            if age >= len(RF.EMBER_LIFE):
                continue
            x = int(math.floor(ax + ex * rx * 0.9 + drift * age))
            y = int(math.floor(top - 1 - rise * age * ry * 0.45))
            if avoid and abs(x + 0.5 - ax) <= avoid:
                continue                      # never across a blade: specks over it read as dirt on it
            out[(x, y)] = RF.EMBER_LIFE[age]
            if age <= 1:
                out[(x, y + 1)] = 'R' if age == 0 else 'V'
    return out


def a_frame(piece, sx=1.0, sy=None, heat=1.0, crack=False, mark=0, clock=None, flare=0, level=0, collar_h=0,
            splash=None, spin=0.0, gone=False, seed=0):
    """One rift frame on the exact ellipse: the far wall lit from below, the far rim burning with its
    cooler lip, the near rim, the blood-red surface on the floor line (in front, so it hides the cut
    of whatever stands in it), embers; crack: the first beat, a burning seam across the full width;
    gone: its dim scar. flare: the rim white-hot (a blade punching through, the plunge)."""
    sp = SPEC[piece]
    W_, H_ = sp['frame']
    AX, AY, RX, RY = geo(piece)
    sy = sx if sy is None else sy
    ax, ay, rx, ry = geo(piece, sx, sy)
    back, front, glow = {}, {}, {}
    rnd = random.Random(seed * 7919 + int(sx * 100) + int(sy * 1000) + flare * 31 + int(heat * 100))

    def put(layer, p, k):
        if 0 <= p[0] < W_ and 0 <= p[1] < H_:
            layer[p] = k

    if mark:
        # the whole opening marked on the floor from the first frame: the spike's only warning
        for i, p in enumerate(by_angle(piece, outline(disc(piece)))):
            if mark == 2 or (i // 2) % 2 == 0:
                put(back, p, 'r' if mark == 1 else ('V' if far(piece, p) else 'R'))
    if crack or gone:
        for x in range(int(math.ceil(ax - rx)), int(math.floor(ax + rx))):
            dx = (x + 0.5 - ax) / max(1.0, rx)
            j = RF._smooth(RF.JAG_TOP, x * 2)
            y = AY - 1 + (1 if j > 0.72 else -1 if j < 0.28 else 0)
            put(back, (x, y), 'v' if gone else RF.heat_key(heat * (1.0 - 0.6 * dx * dx) + 0.1))
            if not gone:
                put(glow, (x, y - 1), 'x')
                if (x + y) % 2 == 0:
                    put(glow, (x, y + 1), 'y')
    elif sx > 0.0:
        cols = {}
        for (x, y) in disc(piece, sx, sy):
            cols.setdefault(x, []).append(y)
        for x, ys in cols.items():
            yt, yb = min(ys), max(ys)
            dx = (x + 0.5 - ax) / rx
            rim_h = heat * (1.0 - 0.55 * dx * dx) + RF.HOT[x % len(RF.HOT)] + 0.25 * flare
            for y in range(yt + 1, yb):
                t = (y - yt) / float(max(1, yb - yt - 1))
                put(back, (x, y), 'V' if t < 0.22 else 'v' if t < 0.40 else '1' if t < 0.55 else 'k')
            put(back, (x, yt), 'w' if flare >= 2 and abs(dx) < 0.45 else RF.heat_key(rim_h))
            put(back, (x, yt - 1), RF.heat_key(rim_h * 0.45))
            put(front, (x, yb), 'Y' if flare >= 2 and abs(dx) < 0.45 else RF.heat_key(rim_h * 0.78))
            put(front, (x, yb + 1), 'v' if rim_h > 0.3 else 'k')
            if yb - yt >= 3:
                j = RF._smooth(RF.JAG_BOT[:144], x * 3)
                k = 'T' if j > 0.8 else 'R' if j > 0.5 else 'V'
                if flare:
                    k = 'Y' if abs(dx) < 0.6 else 'O'
                put(front, (x, AY), k)
        for p, k in glow_ring(piece, sx, sy).items():
            put(glow, p, ('E' if k == 'x' else 'x') if flare >= 2 else k)
        for p, k in haze(piece, sx, sy, level).items():
            glow.setdefault(p, k)
    if collar_h:
        c, lit = collar(piece, collar_h, spin, ('1', 'V', 'v', 'k', 'R', 'O', 'Y'), flare)
        for p, k in c.items():
            put(front, p, k)
        for p, k in lit.items():
            glow.setdefault(p, k)
    avoid = BLADE_HALF + 1 if piece in ('spike', 'sword') else None
    for p, k in a_embers(piece, clock, max(sx, 0.6), False).items():
        if 0 <= p[0] < W_ and 0 <= p[1] < H_:
            back.setdefault(p, k)
    for p, k in a_embers(piece, clock, max(sx, 0.6), True, avoid).items():
        put(front, p, k)
    if splash is not None:
        for p, k in droplets(piece, splash, rnd, ('Y', 'O', 'r')).items():
            put(front, p, k)
    return clip(piece, (back, front, glow))


def a_specs(piece):
    def c(j, period, life=3):
        return RF.loop_clock(j, NE_A, period, life)
    every = {e: [0] for e in range(NE_A)}
    if piece == 'spike':
        return {
            'open': [dict(crack=True, mark=1, heat=0.9), dict(sy=0.45, mark=2, heat=0.8, clock={0: [0], 3: [0]}),
                     dict(heat=0.85, clock={1: [0], 4: [0], 0: [1]}), dict(heat=1.0, clock=c(0, 2)),
                     dict(heat=1.15, level=1, clock=c(1, 2))],
            'burst': [dict(heat=1.2, flare=2, level=2, clock=every),
                      dict(heat=1.1, flare=1, level=1, clock=RF.aged(every, 1, 5))],
            'hold': [dict(heat=0.95, clock=c(0, 2)), dict(heat=1.0, clock=c(1, 2))],
            'suck': [dict(sx=0.9, heat=1.1, level=1, clock=c(0, 2)), dict(sx=0.78, heat=1.05, clock=c(1, 2))],
            'close': [dict(sx=0.5, sy=0.35, heat=0.9, clock=RF.aged(c(1, 2), 1, 5)),
                      dict(crack=True, sx=0.45, heat=0.6, clock=RF.aged(c(1, 2), 2, 5)),
                      dict(gone=True, sx=0.35, clock=RF.aged(c(1, 2), 3, 5))],
        }
    if piece == 'body':
        return {
            'open': [dict(crack=True, mark=1, heat=0.9), dict(sy=0.5, mark=2, heat=0.85, clock={1: [0], 5: [0]}),
                     dict(heat=0.95, clock=c(0, 2)), dict(heat=1.1, level=1, clock=c(1, 2))],
            # the feint exit's tell: a hot pulse, a pillar of heat and embers pouring up, over 2 frames
            'hold': [dict(heat=1.25, flare=1, level=2, clock=c(0, 2, 4)), dict(heat=1.0, level=1, clock=c(1, 2, 4))],
            'close': [dict(sx=0.6, sy=0.4, heat=0.9, clock=RF.aged(c(1, 2, 4), 1, 5)),
                      dict(crack=True, sx=0.5, heat=0.6, clock=RF.aged(c(1, 2, 4), 2, 5)),
                      dict(gone=True, sx=0.4, clock=RF.aged(c(1, 2, 4), 3, 5))],
        }
    return {
        'open': [dict(crack=True, mark=1, heat=0.9), dict(sy=0.4, mark=2, heat=0.8),
                 dict(sy=0.8, mark=2, heat=0.9, clock={2: [0]}), dict(heat=1.0, clock=c(0, 2)),
                 dict(heat=1.15, level=1, clock=c(1, 2))],
        'plunge': [dict(heat=1.25, flare=2, level=2, collar_h=17, splash=0, clock=every),
                   dict(heat=1.1, flare=1, level=1, collar_h=14, splash=1, clock=RF.aged(every, 1, 5)),
                   dict(heat=1.0, collar_h=12, splash=2, clock=RF.aged(every, 2, 5))],
        'loop': [dict(heat=0.95 + 0.05 * (j % 2), collar_h=COLLAR + 1, spin=j / 4.0, clock=c(j, 4, 4))
                 for j in range(4)],
        'close': [dict(sx=0.75, sy=0.6, heat=0.95), dict(sx=0.5, sy=0.35, heat=0.85),
                  dict(crack=True, sx=0.4, heat=0.6), dict(gone=True, sx=0.35)],
    }


# ------------------------------------------------------------------ take B: Josh's card-gate

def card(w, h, face=True):
    """A playing card standing up: black keyline, rune-blue inner frame (his gold, recoloured), a
    cream face with its red pip, or the blue back with a lattice; w squeezes to 1 edge-on."""
    out = {}
    if w <= 2:
        for y in range(h):
            for x in range(w):
                out[(x, y)] = 'f' if y not in (0, h - 1) else 'k'
        return out
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                k = 'k'
            elif face:
                k = 'c' if x < w - 2 else 'C'
            else:
                k = 'e' if (x + y) % 2 else 'd'
            out[(x, y)] = k
    if face and w >= 4 and h >= 6:
        out[((w - 1) // 2, h // 2)] = 'r'
        if h >= 8:
            out[((w - 1) // 2, h // 2 - 1)] = 'r'
    if w >= 5 and h >= 7:
        for x in range(1, w - 1):
            out[(x, 1)] = 'f'
            out[(x, h - 2)] = 'f'
    return out


def b_frame(piece, sx=1.0, spin=0.0, bright=0, cards_up=1.0, mark=0, flat_card=False, gone=False, lift=0,
            sparks_n=0, level=0, collar_h=0, flare=0, splash=None, seed=0):
    """One card-gate frame. sx: the gate's size (0..1); spin: where the ring of cards and the vortex are
    in their turn (0..1 a card slot, so an n-frame loop steps 1/n); bright: 0, 1 hot rim, 2 flare;
    cards_up: how far the cards have stood up; mark: the whole opening dotted (1) or ruled (2) on the
    floor while the gate grows into it; flat_card: the first beat, a card flicked onto the spot;
    gone: only its sparks."""
    sp = SPEC[piece]
    W_, H_ = sp['frame']
    AX, AY, RX, RY = geo(piece)
    ax, ay, rx, ry = geo(piece, sx)
    back, front, glow = {}, {}, {}
    rnd = random.Random(seed * 1009 + int(spin * 1000) + bright * 37 + int(sx * 100) + len(piece) * 11)

    def put(layer, p, k):
        if 0 <= p[0] < W_ and 0 <= p[1] < H_:
            layer[p] = k

    if mark:
        for i, p in enumerate(by_angle(piece, outline(disc(piece)))):
            if mark == 2 or (i // 2) % 2 == 0:
                put(back, p, 'f' if (mark == 1 or not far(piece, p)) else 'e')
        for p, k in glow_ring(piece).items():
            if k == 'x' and (mark == 2 or (p[0] + p[1]) % 2 == 0):
                put(glow, p, 'y')
    if flat_card:
        cw, ch = sp['card'][0] + 1, max(2, sp['card'][1] // 3)
        for y in range(-ch, ch):
            for x in range(-cw, cw):
                d = abs(x + 0.5) / cw + abs(y + 0.5) / ch
                if d <= 1.0:
                    put(back, (AX + x, AY + y), 'f' if d > 0.6 else 'e')
                elif d <= 1.5:
                    put(glow, (AX + x, AY + y), 'x' if d <= 1.25 else 'y')
    elif not gone and sx > 0.0:
        hole = disc(piece, sx)
        rim = outline(hole)
        wall = outline(hole - rim)
        for p in hole - rim:
            u, v = (p[0] + 0.5 - ax) / rx, (p[1] + 0.5 - ay) / ry
            r, a = math.hypot(u, v), math.atan2(v, u)
            sw = math.sin(3 * a + 7 * r - spin * 2 * math.pi)
            k = 'd' if sw > 0.6 and r > 0.25 else 'n' if (sw > -0.1 or r > 0.78) else 'm'
            if p in wall and far(piece, p):
                k = 'e' if bright == 0 else 'f'            # the far wall, lit
            put(back, p, k)
        if piece != 'spike' and sx > 0.6:
            for (dx, dy) in SPADE:
                put(back, (int(math.floor(ax + dx)), int(math.floor(ay - 0.5 + dy * 0.8))), 'e' if bright < 2 else 'f')
        for p in rim:
            if far(piece, p):
                put(back, p, 'g' if bright >= 2 else 'f')
            else:
                put(front, p, 'g' if bright >= 1 else 'f')
        if collar_h:
            c, lit = collar(piece, collar_h, spin, ('n', 'e', 'd', 'm', 'f', 'g', 'w'), flare)
            for p, k in c.items():
                put(front, p, k)
            for p, k in lit.items():
                glow.setdefault(p, k)
        # the ring of cards, faces out: faces on the near half (front), backs on the far half (back)
        n, (cw, ch) = sp['cards'], sp['card']
        h = int(round(ch * cards_up))
        rim_l = sorted(rim)
        items = []
        for i in range(n if rim_l else 0):
            a = 2 * math.pi * (i + 0.5 + spin) / n
            px_, py_ = ax + rx * math.cos(a), ay + ry * math.sin(a)
            base = min(rim_l, key=lambda q: (q[0] + 0.5 - px_) ** 2 + (q[1] + 0.5 - py_) ** 2)
            w = max(1, int(round(cw * abs(math.sin(a)))))
            items.append((base[1], base[0], w, math.sin(a) > 0))
        items.sort()
        for (by, bx, w, near) in items:
            layer = front if near else back
            if h < 2:
                put(layer, (bx, by - 1), 'g')
                continue
            c = card(w, h, face=near)
            x0, y0 = bx - (w - 1) // 2, by - h + 1 - lift
            for (x, y), k in c.items():
                put(layer, (x0 + x, y0 + y), k)
            for (x, y) in c:
                for q in ((x0 + x - 1, y0 + y), (x0 + x + 1, y0 + y), (x0 + x, y0 + y - 1)):
                    if q not in glow:
                        put(glow, q, 'x' if bright >= 2 else 'y')
        for p, k in glow_ring(piece, sx).items():
            put(glow, p, ('E' if k == 'x' else 'x') if bright >= 2 else k)
        for p, k in haze(piece, sx, level=level).items():
            glow.setdefault(p, k)
    if splash is not None:
        for p, k in droplets(piece, splash, rnd, ('g', 'f', 'e')).items():
            put(front, p, k)
    for p, k in sparks(piece, sparks_n, rnd, ('g', 'f', 'b'), 0.8 if (flat_card or gone) else sx).items():
        put(front, p, k)
    return clip(piece, (back, front, glow))


def b_specs(piece):
    if piece == 'spike':
        return {
            'open': [dict(flat_card=True, mark=1, sparks_n=2), dict(sx=0.45, mark=2, cards_up=0.4, sparks_n=2),
                     dict(sx=0.8, mark=2, cards_up=0.8), dict(sx=1.0), dict(sx=1.0, bright=1, sparks_n=3, level=1,
                                                                           spin=0.25)],
            'burst': [dict(bright=2, lift=2, sparks_n=8, level=2, spin=0.5),
                      dict(bright=1, lift=1, sparks_n=5, level=1, spin=0.75)],
            'hold': [dict(spin=0.0), dict(spin=0.5)],
            'suck': [dict(sx=0.9, bright=1, spin=0.25, sparks_n=3), dict(sx=0.78, bright=1, spin=0.5, cards_up=0.8)],
            'close': [dict(sx=0.5, cards_up=0.5, sparks_n=3), dict(sx=0.25, cards_up=0.0, sparks_n=4),
                      dict(gone=True, sparks_n=4)],
        }
    if piece == 'body':
        return {
            'open': [dict(flat_card=True, mark=1, sparks_n=3), dict(sx=0.5, mark=2, cards_up=0.5, sparks_n=3),
                     dict(sx=0.85, mark=2, cards_up=0.9), dict(sx=1.0, bright=1, level=1)],
            # the feint exit's tell: it strobes between a flare (hot rim, a beam, cards hopping, sparks
            # pouring up) and a glow, at 0.08 s: "something's coming"
            'hold': [dict(bright=2, spin=0.0, level=2, sparks_n=8, lift=1), dict(bright=1, spin=0.5, level=1,
                                                                               sparks_n=6)],
            'close': [dict(sx=0.6, cards_up=0.7, sparks_n=4), dict(sx=0.3, cards_up=0.2, sparks_n=4),
                      dict(gone=True, sparks_n=5)],
        }
    return {
        'open': [dict(flat_card=True, mark=1, sparks_n=2), dict(sx=0.4, mark=2, cards_up=0.4, sparks_n=2),
                 dict(sx=0.7, mark=2, cards_up=0.7), dict(sx=1.0), dict(sx=1.0, bright=1, level=1)],
        'plunge': [dict(bright=2, level=2, collar_h=17, flare=2, splash=0, sparks_n=4, lift=2),
                   dict(bright=1, level=1, collar_h=14, flare=1, splash=1, lift=1),
                   dict(collar_h=12, splash=2)],
        'loop': [dict(spin=j / 4.0, collar_h=COLLAR + 1) for j in range(4)],
        'close': [dict(sx=0.75, cards_up=0.8, sparks_n=3), dict(sx=0.5, cards_up=0.5, sparks_n=3),
                  dict(sx=0.25, cards_up=0.1, sparks_n=4), dict(gone=True, sparks_n=4)],
    }


# ------------------------------------------------------------------ strips

def frames(take, piece, name):
    """[(back, front, glow)] key dicts for one sequence."""
    specs = (a_specs if take == 'A' else b_specs)(piece)[name]
    fn = a_frame if take == 'A' else b_frame
    return [fn(piece, seed=j, **s) for j, s in enumerate(specs)]


def seq_images(take, piece, name):
    """{'back'|'front'|'glow': strip image} for one sequence."""
    def make():
        fr = frames(take, piece, name)
        W_, H_ = SPEC[piece]['frame']
        pal, gpal = TAKES[take]['pal'], TAKES[take]['glow']
        out = {}
        for li, layer in enumerate(('back', 'front', 'glow')):
            im = Image.new('RGBA', (W_ * len(fr), H_), (0, 0, 0, 0))
            for i, f in enumerate(fr):
                im.alpha_composite(B.image(f[li], W_, H_, gpal if layer == 'glow' else pal), (i * W_, 0))
            out[layer] = im
        return out
    return ST.cached(('seq', take, piece, name), make)


def times(piece, name):
    return dict(SEQS[piece])[name]


# ------------------------------------------------------------------ the blade, the planted sword, the smear

def spike_blade():
    """eric_thrown_sword_v2 f6 (point up) without its spin arcs: they are pure white and lie outside
    the sword's own span on every row (its glints lie inside). Returns (image, raw f6, x of the
    point's centre as an edge)."""
    def make():
        f6 = Image.open(THROWN).convert('RGBA').crop((6 * 160, 0, 7 * 160, 160))
        px = f6.load()
        out = Image.new('RGBA', f6.size, (0, 0, 0, 0))
        po = out.load()
        for y in range(f6.height):
            xs = [x for x in range(f6.width) if px[x, y][3] and px[x, y][:3] != (255, 255, 255)]
            if not xs:
                continue
            lo, hi = min(xs), max(xs)
            for x in range(f6.width):
                p = px[x, y]
                if p[3] and (p[:3] != (255, 255, 255) or lo < x < hi):
                    po[x, y] = p
        img = out.crop(out.getbbox())
        cols = [x for x in range(img.width) if img.getpixel((x, 0))[3]]
        return img, f6, (min(cols) + max(cols) + 1) / 2.0
    return ST.cached('spike_blade', make)


def planted():
    """eric_bearhug_planted_sword_v2 (read only) and its base: the blade's centre on the first row where
    it meets its dirt (from that row down is under the floor line), as edge coordinates."""
    def make():
        im = Image.open(PLANTED).convert('RGBA')
        px = im.load()
        span = {}
        for y in range(im.height):
            xs = [x for x in range(im.width) if px[x, y][3]]
            if xs:
                span[y] = (min(xs), max(xs))
        ys = sorted(span)
        guard = next(y for y in ys if span[y][1] - span[y][0] >= 30)
        blade = span[guard + 12]
        width = blade[1] - blade[0]
        base = next(y for y in ys if y > guard + 12 and span[y][1] - span[y][0] != width)
        return im, ((blade[0] + blade[1] + 1) / 2.0, base)
    return ST.cached('planted', make)


def smear_frames():
    """The spike's optional smear, take-neutral steel on the blade's own whites (drawn BEHIND the
    blade, so it only shows round it): 0 the rise (streaks up both sides, the air parting over the
    point), 1 full (a gleam off the point), 2 the retract (the blade's afterimage where it was)."""
    W_, H_ = SMEAR['frame']
    ax, ay = SMEAR['anchor']
    tip = ay - SPIKE_RISE
    f0, f1, f2 = {}, {}, {}

    def lane(d, x, y0, y1, on, off, keys, ph=0):
        for y in range(y0, y1):
            if (y - y0 + ph) % (on + off) < on:
                t = (y - y0) / float(max(1, y1 - y0))
                d[(x, y)] = keys[0] if t < 0.3 else keys[1] if t < 0.7 else keys[2]

    li, ri = ax - BLADE_HALF - 1, ax + BLADE_HALF          # the columns just outside the blade
    for x, ph in ((li, 0), (ri, 3)):
        lane(f0, x, tip + 3, ay, 10, 3, ('w', 'g', 's'), ph)
    for x, ph in ((li - 1, 5), (ri + 1, 1)):
        lane(f0, x, tip + 14, ay, 6, 5, ('g', 's', 's'), ph)
    for k in range(1, 5):
        f0[(ax - 1 - k, tip - 1 - k // 2)] = 'g'
        f0[(ax + k, tip - 1 - k // 2)] = 'g'
    cy = tip + 2
    for k in range(0, 6):
        key = 'w' if k <= 1 else 'g' if k <= 3 else 's'
        for x in (ax - 1, ax):
            f1[(x, cy - k)] = key
            f1[(x, cy + k)] = key
    for k in range(0, 8):
        key = 'w' if k <= 1 else 'g' if k <= 4 else 's'
        f1[(ax - 1 - k, cy)] = key
        f1[(ax + k, cy)] = key
    for x, ph in ((li, 2), (ri, 6)):
        lane(f1, x, tip + 8, tip + 22, 4, 3, ('s', 's', 's'), ph)
    for x, ph in ((ax - 10, 0), (ax - 5, 4), (ax + 4, 2), (ax + 9, 6)):
        lane(f2, x, tip + 2, tip + 44, 7, 4, ('g', 's', 's'), ph)
    for x, ph in ((li, 1), (ri, 5)):
        lane(f2, x, ay - 36, ay, 8, 4, ('g', 'g', 's'), ph)
    out = Image.new('RGBA', (W_ * 3, H_), (0, 0, 0, 0))
    for i, f in enumerate((f0, f1, f2)):
        f = {p: k for p, k in f.items() if 0 <= p[0] < W_ and 0 <= p[1] < ay}
        out.alpha_composite(B.image(f, W_, H_, STEEL), (i * W_, 0))
    return out


# ------------------------------------------------------------------ compositing helpers (previews)

def blit(canvas, img, xy):
    tmp = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    tmp.paste(img, (int(math.floor(xy[0])), int(math.floor(xy[1]))), img)
    canvas.alpha_composite(tmp)


def add(canvas, img, xy):
    layer = Image.new('RGB', canvas.size, (0, 0, 0))
    layer.paste(img.convert('RGB'), (int(math.floor(xy[0])), int(math.floor(xy[1]))), img)
    return ImageChops.add(canvas.convert('RGB'), layer).convert('RGBA')


def cut_at(img, feet, at, sink=0):
    """(image cut at the floor line, top-left) for `img` with its feet point `feet` (edge coords) on the
    floor point `at`, sunk `sink` texels; None when nothing is over the line."""
    tlx, tly = at[0] - feet[0], at[1] + sink - feet[1]
    rows = int(round(at[1] - tly))
    if rows <= 0:
        return None
    return img.crop((0, 0, img.width, min(img.height, rows))), (tlx, tly)


def blade_at(at, rise):
    img, raw, cx = spike_blade()
    return cut_at(img, (cx, rise), at) if rise > 0 else None


def sword_at(at, above=0):
    """The planted sword with its base `above` texels over the floor point (the plunge), cut at the line."""
    img, base = planted()
    img = img.crop((0, 0, img.width, int(base[1])))          # its dirt never shows, at any height
    return cut_at(img, base, at, -above)


def portal_on(canvas, take, piece, name, i, at, stand=(), behind=()):
    """Frame i of a sequence with its anchor on `at`: back, `behind` (the smear), what stands in it,
    glow added, front. Returns the new canvas."""
    L_ = seq_images(take, piece, name)
    W_, H_ = SPEC[piece]['frame']
    ax, ay = SPEC[piece]['anchor']
    tl = (at[0] - ax, at[1] - ay)

    def cut(im):
        return im.crop((i * W_, 0, (i + 1) * W_, H_))
    blit(canvas, cut(L_['back']), tl)
    for it in list(behind) + list(stand):
        if it:
            blit(canvas, it[0], it[1])
    canvas = add(canvas, cut(L_['glow']), tl)
    blit(canvas, cut(L_['front']), tl)
    return canvas


def void_crop(w, h, x0=300, y0=150):
    return ST.void(3).crop((x0, y0, x0 + w, y0 + h)).copy()


# ------------------------------------------------------------------ previews

def sheet_for(take):
    """Every frame of every sequence at the game's option-B scale (2 screen px a texel): the blade up
    the spike, the planted sword in the sword portal."""
    font_h = 14
    rows = []
    blade_img, _, _ = spike_blade()
    p_img, p_base = planted()
    for piece in SPEC:
        W_, H_ = SPEC[piece]['frame']
        ax, ay = SPEC[piece]['anchor']
        extra = {'spike': SPIKE_RISE + 4 - ay, 'sword': int(p_base[1] - p_img.getbbox()[1]) + 22 - ay}.get(piece, 0)
        extra = max(0, extra)
        tiles = []
        for name, tt in SEQS[piece]:
            for j, t in enumerate(tt):
                c = void_crop(W_ + 8, H_ + extra)
                at = (ax + 4, ay + extra)
                stand = []
                if piece == 'spike' and name in BLADE_AT:
                    stand = [blade_at(at, BLADE_AT[name][j])]
                if piece == 'sword' and name in ('plunge', 'loop'):
                    stand = [sword_at(at, (16, 6, 0)[j] if name == 'plunge' else 0)]
                c = portal_on(c, take, piece, name, j, at, stand)
                c2 = c.resize((c.width * 2, c.height * 2), Image.NEAREST)
                lab = Image.new('RGBA', (c2.width, c2.height + font_h), (10, 8, 16, 255))
                lab.paste(c2, (0, font_h))
                ImageDraw.Draw(lab).text((2, 1), '%s %s%d %.2fs%s' % (piece, name, j, t,
                                                                     ' loop' if (piece, name) in LOOPS else ''),
                                         fill=(230, 230, 240, 255))
                tiles.append(lab)
        row = Image.new('RGBA', (sum(t.width + 6 for t in tiles), max(t.height for t in tiles)), (10, 8, 16, 255))
        x = 0
        for t in tiles:
            row.paste(t, (x, row.height - t.height))
            x += t.width + 6
        rows.append(row)
    W = max(r.width for r in rows)
    out = Image.new('RGBA', (W, sum(r.height + 10 for r in rows) + 24), (10, 8, 16, 255))
    ImageDraw.Draw(out).text((6, 6), 'Take %s: %s. Every frame at the game\'s scale (2 screen px a texel): back, '
                                     'the blade or the planted sword cut at the floor line, glow added, front.' % (
                                         take, TAKES[take]['name']), fill=(230, 230, 240, 255))
    y = 24
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + 10
    return out


def gif_spike(take, scale=3):
    """Two spikes side by side, the plain blade and the blade with the smear: the telegraph, the
    blade punching up, held, sucked back, the portal gone."""
    W_, H_ = SPEC['spike']['frame']
    ax, ay = SPEC['spike']['anchor']
    extra = SPIKE_RISE + 8 - ay
    smear = smear_frames()
    sw, sh = SMEAR['frame']
    sax, say = SMEAR['anchor']
    beats = [('open', j, None, None, t) for j, t in enumerate(times('spike', 'open'))]
    beats += [('burst', 0, BLADE_AT['burst'][0], 0, times('spike', 'burst')[0]),
              ('burst', 1, BLADE_AT['burst'][1], 1, times('spike', 'burst')[1])]
    for rep in range(3):
        beats += [('hold', j, SPIKE_RISE, 1 if (rep, j) == (0, 0) else None, t)
                  for j, t in enumerate(times('spike', 'hold'))]
    beats += [('suck', j, BLADE_AT['suck'][j], 2, t) for j, t in enumerate(times('spike', 'suck'))]
    beats += [('close', j, None, None, t) for j, t in enumerate(times('spike', 'close'))]
    beats.append((None, 0, None, None, 0.3))
    out, durs = [], []
    for name, j, rise, sm, t in beats:
        c = void_crop(2 * W_ + 12, H_ + extra, 280, 130)
        for k, at in enumerate(((ax + 2, ay + extra), (W_ + 10 + ax, ay + extra))):
            if name is None:
                continue
            behind = []
            if k == 1 and sm is not None:
                behind = [(smear.crop((sm * sw, 0, (sm + 1) * sw, sh)), (at[0] - sax, at[1] - say))]
            c = portal_on(c, take, 'spike', name, j, at, [blade_at(at, rise)] if rise else [], behind)
        out.append(c.resize((c.width * scale, c.height * scale), Image.NEAREST))
        durs.append(t)
    return out, durs


def pose(boss, key):
    """A take-B concept pose cell from the puppets artist's strips (read only): (image, feet, back)."""
    with open(os.path.join(CONCEPTS, 'notes.json')) as f:
        notes = json.load(f)
    b = notes['bosses'][boss]
    cw, ch = b['strip']['cell']
    ci = [c['cell'] for c in b['strip']['cells'] if c['pose'] == key][0]
    p = [q for q in b['poses'] if q['key'] == key][0]
    strip = Image.open(os.path.join(CONCEPTS, b['strip']['file'])).convert('RGBA')
    return strip.crop((ci * cw, 0, (ci + 1) * cw, ch)), tuple(p['feet']), tuple(p['back'])


def parry_badge(i):
    im = Image.open(PARRY_TELL).convert('RGBA')
    return im.crop(((i % 6) * 32, 0, (i % 6 + 1) * 32, 24)), (16, 24)


def gif_body(take, scale=2):
    """Eric sinks into one portal (its open at 2x, the feint's entry), then the exit portal opens next
    to the player and holds as the tell (with the red parry badge over it) before he bursts out
    lunging, and it closes under him."""
    W_, H_ = SPEC['body']['frame']
    ax, ay = SPEC['body']['anchor']
    idle, ifeet, _ = pose('eric', 'idle')
    lunge, lfeet, _ = pose('eric', 'bearhug')
    ifeet = (ifeet[0], ifeet[1] + 1)
    lfeet = (lfeet[0], lfeet[1] + 1)
    tall = max(f[1] - im.getbbox()[1] for im, f in ((idle, ifeet), (lunge, lfeet)))
    top = tall + 30
    cw, chh = 2 * W_ + 70, top + (H_ - ay) + 4
    entry, exit_ = (ax + 2, top), (W_ + 66 + ax, top)
    player_at = (entry[0] + W_ // 2 + 30, top + 4)
    fig_i = ifeet[1] - idle.getbbox()[1]
    fig_l = lfeet[1] - lunge.getbbox()[1]
    t_open, t_hold, t_close = times('body', 'open'), times('body', 'hold'), times('body', 'close')
    # (entry: (seq, j) or None, eric-in sink fraction or None, exit: (seq, j) or None, eric-out rise or None, badge, secs)
    beats = [(None, 0.0, None, None, False, 0.3)]
    beats += [(('open', j), 0.0, None, None, False, t / 2) for j, t in enumerate(t_open)]
    for k, s_ in enumerate((0.35, 0.7, 1.0)):
        beats.append((('hold', k % 2), s_, None, None, False, t_hold[0] / 2))
    beats += [(('close', j), None, None, None, False, t / 2) for j, t in enumerate(t_close)]
    beats.append((None, None, None, None, False, 0.15))
    beats += [(None, None, ('open', j), None, False, t) for j, t in enumerate(t_open)]
    for rep in range(3):
        beats += [(None, None, ('hold', j), None, True, t) for j, t in enumerate(t_hold)]
    for k, r_ in enumerate((0.35, 0.8, 1.0)):
        beats.append((None, None, ('hold', k % 2), r_, True, 0.05))
    beats += [(None, None, ('close', j), 1.0, False, t) for j, t in enumerate(t_close)]
    beats.append((None, None, None, 1.0, False, 0.6))
    out, durs = [], []
    for n, (p1, s1, p2, r2, badge, secs) in enumerate(beats):
        c = void_crop(cw, chh, 150, 60)
        blit(c, ST.player_up(), (player_at[0] - 16, player_at[1] - 29))
        if p1 or s1 is not None:
            st = cut_at(idle, ifeet, entry, int(round((s1 or 0.0) * fig_i))) if s1 is not None else None
            c = portal_on(c, take, 'body', p1[0], p1[1], entry, [st]) if p1 else c
            if not p1 and st:
                blit(c, st[0], st[1])
        if p2 or r2 is not None:
            st = cut_at(lunge, lfeet, exit_, int(round((1.0 - r2) * fig_l))) if r2 is not None else None
            c = portal_on(c, take, 'body', p2[0], p2[1], exit_, [st]) if p2 else c
            if not p2 and st:
                blit(c, st[0], st[1])
        if badge:
            b, piv = parry_badge(n)
            blit(c, b, (exit_[0] - piv[0], exit_[1] - fig_l - 6 - piv[1]))
        out.append(c.resize((c.width * scale, c.height * scale), Image.NEAREST))
        durs.append(secs)
    return out, durs


def gif_sword(take, scale=3):
    """The sword portal opens, Eric's sword plunges in (the splash), the loop holds it, it is pulled
    out and the portal shuts."""
    W_, H_ = SPEC['sword']['frame']
    ax, ay = SPEC['sword']['anchor']
    p_img, p_base = planted()
    extra = int(p_base[1] - p_img.getbbox()[1]) + 30 - ay
    beats = [('open', j, None, t) for j, t in enumerate(times('sword', 'open'))]
    beats += [('plunge', j, a_, t) for j, (a_, t) in enumerate(zip((16, 6, 0), times('sword', 'plunge')))]
    for rep in range(2):
        beats += [('loop', j, 0, t) for j, t in enumerate(times('sword', 'loop'))]
    beats += [('loop', 0, 12, 0.05), ('loop', 1, 30, 0.05)]
    beats += [('close', j, None, t) for j, t in enumerate(times('sword', 'close'))]
    beats.append((None, 0, None, 0.35))
    out, durs = [], []
    for name, j, above, t in beats:
        c = void_crop(W_ + 8, H_ + extra, 280, 100)
        at = (ax + 4, ay + extra)
        if name:
            c = portal_on(c, take, 'sword', name, j, at, [sword_at(at, above)] if above is not None else [])
        out.append(c.resize((c.width * scale, c.height * scale), Image.NEAREST))
        durs.append(t)
    return out, durs


def save_gif(path, frames_, durs):
    pick = frames_[::max(1, len(frames_) // 12)][:12]
    w, h = pick[0].size
    mont = Image.new('RGB', (w, h * len(pick)))
    for i, f in enumerate(pick):
        mont.paste(f.convert('RGB'), (0, i * h))
    pal = mont.quantize(colors=255, method=Image.MEDIANCUT)
    q = [f.convert('RGB').quantize(palette=pal, dither=Image.NONE) for f in frames_]
    ms = [max(20, int(round(d * 100)) * 10) for d in durs]
    q[0].save(path, save_all=True, append_images=q[1:], duration=ms, loop=0, disposal=1)
    return len(q), sum(ms) / 1000.0


def blade_compare():
    """f6 as the contract names it next to the cleaned copy, both cut at a spike's floor line."""
    img, raw, cx = spike_blade()
    W_, H_ = SPEC['spike']['frame']
    ax, ay = SPEC['spike']['anchor']
    extra = SPIKE_RISE + 8 - ay
    c = void_crop(2 * W_ + 12, H_ + extra, 280, 130)
    left, right = (ax + 2, ay + extra), (W_ + 10 + ax, ay + extra)
    rx0 = [x for x in range(raw.width) if raw.getpixel((x, 5))[3] and raw.getpixel((x, 5))[:3] != (255, 255, 255)]
    raw_tip = ((min(rx0) + max(rx0) + 1) / 2.0, 5)
    raw_cut = cut_at(raw, (raw_tip[0], raw_tip[1] + SPIKE_RISE), left)
    c = portal_on(c, 'B', 'spike', 'hold', 0, left, [raw_cut])
    c = portal_on(c, 'B', 'spike', 'hold', 0, right, [blade_at(right, SPIKE_RISE)])
    c = c.resize((c.width * 4, c.height * 4), Image.NEAREST)
    lab = Image.new('RGBA', (c.width, c.height + 16), (10, 8, 16, 255))
    lab.paste(c, (0, 16))
    ImageDraw.Draw(lab).text((4, 2), 'f6 as named (spin arcs show)          cleaned f6 (eric_sword_spike_up)',
                             fill=(230, 230, 240, 255))
    return lab


# ------------------------------------------------------------------ the option-B mock

def to_screen(p):
    return ((p[0] + 480) / 1.5, (p[1] + 6) / 1.5)


# option-B world px. Josh, the sword portal, Eric's start and his first exit are the architect's
# staging facts; the player, the feint exit and the spikes are mine, for the mock.
MOCK = dict(josh=(560, 930), central=(960, 921), eric_start=(1154, 930), first_exit=(960, 1164),
            player=(1020, 1290), feint=(1268, 1269), eric_sink=8,
            spikes=[((810, 1352), 'hold', 0), ((878, 1157), 'burst', 0), ((1035, 1442), 'open', 1),
                    ((1170, 1434), 'suck', 1)])


def mock(take):
    """1920x1080 in option-B staging (2 screen px a texel): Jordan working; Josh on the left facing
    right, his sword portal between the two spots with Eric's sword plunged in it; Eric bursting out
    of a feint exit next to the player mid-grab, under the red parry badge; spikes round the player at
    different beats. Returns (image, info)."""
    s = 2
    cv = ST.Canvas(s)
    cv.blit(ST.void(2), 2, (0, 0))
    im, au, tips = ST.god_frame('control', 1)
    tl = ST.god_tl()
    core = (tl[0] + (L.CORE[0] + 0.5) * 2, tl[1] + (L.CORE[1] + 0.5) * 2)
    cv.blit(RU.frame_image(5), 2, (core[0] - 192, core[1] - 192))
    cv.blit(im, 2, tl)
    cv.add(au, 2, (tl[0] - G.AURA_PAD * 2, tl[1]))
    josh, jfeet, jback = pose('josh', 'wild_hold')
    eric, efeet, eback = pose('eric', 'bearhug')
    jfeet_e, efeet_e = (jfeet[0], jfeet[1] + 1), (efeet[0], efeet[1] + 1)
    J, C, P, Fx = (to_screen(MOCK[k]) for k in ('josh', 'central', 'player', 'feint'))
    sink = MOCK['eric_sink']
    info = {'screen': {'josh': J, 'central': C, 'player': P, 'feint': Fx},
            'world': {k: MOCK[k] for k in ('josh', 'central', 'eric_start', 'first_exit', 'player', 'feint')},
            'spikes': [{'world': w, 'screen': to_screen(w), 'frame': '%s%d' % (n, i)} for w, n, i in MOCK['spikes']]}

    def hook(feet_e, back, at, sink_=0):
        return (at[0] + (back[0] + 0.5 - feet_e[0]) * s, at[1] + (back[1] + 0.5 - feet_e[1] + sink_) * s)

    def pair_for(side, hk):
        # jp_scene.string_pair: the outer pair (ring, little) if the hook lies further from his centre
        # line than the hand's claws, else the inner pair (index, middle)
        mid = sum(p[0] for p in ST.tips_px(tips, side, (0, 1, 2, 3))) / 4.0
        return (2, 3) if abs(hk[0] - ST.GOD_POINT[0]) > abs(mid - ST.GOD_POINT[0]) else (0, 1)

    strings, knots = [], []
    for side, feet_e, back, at, sk, who in (('left', jfeet_e, jback, J, 0, 'josh'), ('right', efeet_e, eback, Fx, sink, 'eric')):
        hk = hook(feet_e, back, at, sk)
        pair = pair_for(side, hk)
        info[who + '_hook'] = [round(hk[0], 1), round(hk[1], 1)]
        info[who + '_pair'] = list(pair)
        for j, p0 in enumerate(ST.tips_px(tips, side, pair)):
            strings.append(S.curve(p0, (hk[0] + (j - 0.5) * 2 * s, hk[1]), 0.7))
            knots.append(p0)
    cv.strings(strings, knots, s)

    def screen_item(piece, name, i, at, stand):
        """A portal frame at screen point `at`, drawn at 2x onto the canvas: back, stand (images at
        texel offsets from the portal's anchor), glow added, front."""
        L_ = seq_images(take, piece, name)
        W_, H_ = SPEC[piece]['frame']
        ax, ay = SPEC[piece]['anchor']
        pos = (at[0] - ax * s, at[1] - ay * s)

        def cut(im_):
            return im_.crop((i * W_, 0, (i + 1) * W_, H_))
        cv.blit(cut(L_['back']), s, pos)
        for it in stand:
            if it:
                cv.blit(it[0], s, (at[0] + it[1][0] * s, at[1] + it[1][1] * s))
        cv.add(cut(L_['glow']), s, pos)
        cv.blit(cut(L_['front']), s, pos)

    items = []
    items.append((C[1], lambda: screen_item('sword', 'loop', 1, C, [sword_at((0, 0))])))
    for w, n, i in MOCK['spikes']:
        at = to_screen(w)
        rise = BLADE_AT[n][i] if n in BLADE_AT else 0
        items.append((at[1], (lambda at=at, n=n, i=i, rise=rise:
                              screen_item('spike', n, i, at, [blade_at((0, 0), rise)] if rise else []))))
    items.append((Fx[1], lambda: screen_item('body', 'hold', 0, Fx, [cut_at(eric, efeet_e, (0, 0), sink)])))
    items.append((J[1], lambda: cv.blit(josh, s, (J[0] - jfeet_e[0] * s, J[1] - jfeet_e[1] * s))))
    items.append((P[1], lambda: cv.blit(ST.player_up(), s, (P[0] - 16 * s, P[1] - 29 * s))))
    for y, fn in sorted(items, key=lambda it: it[0]):
        fn()
    # the red parry badge over Eric's head (Assets/Effects/parry_tell.png, frame 2, drawn at the
    # world's scale: its pivot is its bottom tip, a few texels over the head)
    b, piv = parry_badge(2)
    head_y = Fx[1] + (sink - (efeet_e[1] - eric.getbbox()[1])) * s
    cv.blit(b, s, (Fx[0] - piv[0] * s, head_y - 6 * s - piv[1] * s))
    return cv.im, info


# ------------------------------------------------------------------ checks

def audit(take):
    """Every strip: no semi-alpha; nothing outside the opening + RIM on the floor (or its column);
    and the drawn opening at full size is exactly the contract's."""
    out = {}
    for piece in SPEC:
        ok = allowed(piece)
        box = opening_box(piece)
        d = disc(piece)
        xs, ys = [p[0] for p in d], [p[1] for p in d]
        got = (min(xs), min(ys), max(xs), max(ys))
        assert got == box, (piece, got, box)
        for name, tt in SEQS[piece]:
            L_ = seq_images(take, piece, name)
            W_, H_ = SPEC[piece]['frame']
            for layer, im in L_.items():
                assert im.size == (W_ * len(tt), H_), (piece, name, layer, im.size)
                px = im.load()
                for y in range(im.height):
                    for x in range(im.width):
                        a = px[x, y][3]
                        if a not in (0, 255):
                            raise SystemExit('semi-alpha: %s %s %s (%d, %d)' % (piece, name, layer, x, y))
                        if a and (x % W_, y) not in ok:
                            raise SystemExit('outside the rim: %s %s %s (%d, %d)' % (piece, name, layer, x % W_, y))
        out[piece] = {'opening_box': box}
    return out


# ------------------------------------------------------------------ writing (guarded)

LUA = r'''
local src = app.params["src"]
local out = app.params["out"]
local n = tonumber(app.params["n"])
local fw = tonumber(app.params["fw"])
local durs = {}
for d in string.gmatch(app.params["durs"], "[^,]+") do table.insert(durs, tonumber(d)) end
local strip = Image{ fromFile = src }
local fh = strip.height
local spr = Sprite(fw, fh, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = app.params["layer"]
for i = 1, n do
  if i > 1 then spr:newEmptyFrame() end
  local img = Image(fw, fh, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0))
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = durs[((i - 1) % #durs) + 1]
end
local tag = spr:newTag(1, n)
tag.name = app.params["tag"]
spr:saveAs(out)
'''


def install_guard():
    here = os.path.normcase(os.path.realpath(HERE))
    tmp_root = os.path.normcase(os.path.realpath(tempfile.gettempdir()))
    ase = os.path.normcase(os.path.realpath(B.ASEPRITE))
    assets = os.path.normcase(os.path.realpath(os.path.join(ROOT, 'Assets')))

    def inside_(p, roots=(here, tmp_root)):
        rp = os.path.normcase(os.path.realpath(os.fspath(p)))
        return any(rp == r or rp.startswith(r + os.sep) for r in roots)

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not inside_(path):
                raise PermissionError('guard: portals writes only into %s (and a temp folder), not %s' % (HERE, path))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                       'shutil.copyfile', 'shutil.move', 'shutil.rmtree'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and not inside_(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event == 'subprocess.Popen':
            argv = args[1]
            line = argv if isinstance(argv, str) else subprocess.list2cmdline([os.fspath(a) for a in argv])
            first = line[1:line.index('"', 1)] if line.startswith('"') else line.split(' ')[0]
            if os.path.normcase(os.path.realpath(first)) != ase:
                raise PermissionError('guard: portals launches only Aseprite, not %s' % first)
            if assets in os.path.normcase(line):
                raise PermissionError('guard: an Aseprite argument under Assets')

    sys.addaudithook(hook)


def write_sprite(tmp, dest_dir, name, im, n, fw, durs, tag, layer):
    from imgdiff import pixel_diff
    tpng = os.path.join(tmp, name + '.png')
    tase = os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    lua = os.path.join(tmp, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LUA)
    subprocess.run([B.ASEPRITE, '-b', '--script-param', 'src=' + tpng, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % n, '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%.3f' % t for t in durs),
                    '--script-param', 'layer=' + layer, '--script-param', 'tag=' + tag, '--script', lua],
                   check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([B.ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    d = pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        with open(src, 'rb') as f:
            data = f.read()
        with open(os.path.join(dest_dir, name + ext), 'wb') as f:
            f.write(data)


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    sys.path.insert(0, os.path.dirname(PUP))          # art_source, for imgdiff
    install_guard()
    tmp = tempfile.mkdtemp(prefix='jpup_portals_')
    table = {'contract': {'spec': SPEC, 'seqs': {k: [[n, list(t)] for n, t in v] for k, v in SEQS.items()},
                          'loops': sorted('%s_%s' % lp for lp in LOOPS), 'rim': RIM, 'spike_rise': SPIKE_RISE,
                          'collar_rows_over_base': COLLAR, 'smear': SMEAR},
             'takes': {}}
    done = []
    for take in ('A', 'B'):
        dest = os.path.join(HERE, 'take' + take)
        if not os.path.isdir(dest):
            os.mkdir(dest)
        table['takes'][take] = {'name': TAKES[take]['name'], 'audit': audit(take), 'files': []}
        for piece in SPEC:
            for name, tt in SEQS[piece]:
                L_ = seq_images(take, piece, name)
                for layer in ('back', 'front', 'glow'):
                    fname = 'portal_%s_%s_%s' % (piece, name, layer)
                    write_sprite(tmp, dest, fname, L_[layer], len(tt), SPEC[piece]['frame'][0], tt,
                                 '%s_%s' % (piece, name), 'glow (additive)' if layer == 'glow' else layer)
                    table['takes'][take]['files'].append('take%s/%s.png' % (take, fname))
                    done.append('take%s/%s' % (take, fname))
        sheet_for(take).save(os.path.join(HERE, 'take%s_sheet.png' % take))
        done.append('take%s_sheet.png' % take)
        for gname, fn in (('spike', gif_spike), ('body', gif_body), ('sword', gif_sword)):
            fr_, durs = fn(take)
            n, secs = save_gif(os.path.join(HERE, 'take%s_%s.gif' % (take, gname)), fr_, durs)
            done.append('take%s_%s.gif (%d frames, %.2f s)' % (take, gname, n, secs))
        im, info = mock(take)
        im.save(os.path.join(HERE, 'take%s_mock.png' % take))
        table['takes'][take]['mock'] = info
        done.append('take%s_mock.png' % take)
    sm = smear_frames()
    write_sprite(tmp, HERE, 'portal_spike_smear', sm, 3, SMEAR['frame'][0], (0.03, 0.07, 0.06), 'spike_smear', 'smear')
    done.append('portal_spike_smear')
    img, raw, cx = spike_blade()
    write_sprite(tmp, HERE, 'eric_sword_spike_up', img, 1, img.width, (1.0,), 'sword_up', 'sword')
    done.append('eric_sword_spike_up')
    blade_compare().save(os.path.join(HERE, 'f6_arcs_compare.png'))
    done.append('f6_arcs_compare.png')
    p_img, p_base = planted()
    table['blade'] = {'file': 'eric_sword_spike_up.png', 'size': list(img.size), 'point_x_edge': cx,
                      'from': 'eric_thrown_sword_v2.png frame 6, its white spin arcs removed'}
    table['planted_sword'] = {'file': 'Assets/Characters/Eric/eric_bearhug_planted_sword_v2.png',
                              'base_edge': list(p_base), 'note': 'blade centre x; the first row of its dirt '
                                                                  '(rows from here down go under the floor line)'}
    with open(os.path.join(HERE, 'portals.json'), 'w') as f:
        json.dump(table, f, indent=1)
    done.append('portals.json')
    for d in done:
        print('wrote', d)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
