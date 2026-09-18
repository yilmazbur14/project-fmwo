"""Danny's evolved form, REDESIGN pass: less Snorlax, more E. Honda.

Kept deliberately separate from danny_sumo.py so the approved form and its
eleven production sheets stay untouched until the user picks an option.

What changes from the approved form
  * athletic bulk instead of soft bulk -- pec separation, deltoid and bicep
    mass, a firm round gut rather than a sagging one, powerful thighs
  * a deep, low, wide-kneed sumo crouch: the knees become the widest point of
    the silhouette, which is most of what reads as "sumo" at 3x
  * the sleepiness moves entirely into the face (heavy lids, slack mouth,
    sleep bubble); the body is no longer the joke

Kept exactly as approved
  * the beanie pulled down over the whole skull, in his blue / light-blue knit
  * the torn red collar, the gold chain, the sleep bubble

Options this module can render
  bottom = 'shorts'   the approved very-ripped shorts, with a sumo rope over
  bottom = 'mawashi'  a blue-and-white striped mawashi + decorative apron
  paint  = 0 | 1      E. Honda kabuki stroke through each eye
  bun    = 0 | 1      a topknot bun bulging under the beanie, hair escaping
  pose   = 'idle' | 'ready'
"""
import os
from rig import (Rig, S, SM, stamp, to_pix, dump, check_symmetry, curve,
                 region_mask, visible_mask, PAL)

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 176, 144
AX = 87.5
MIR = 175
SKIN = set('SsdD')
CLOTH = set('RrDM')


def tr(pts, dx=0.0, dy=0.0, sx=1.0, sy=1.0, ox=AX, oy=0.0):
    return [(ox + (x - ox) * sx + dx, oy + (y - oy) * sy + dy) for (x, y) in pts]


# ---------------------------------------------------------------- GEOMETRY
# head and beanie are the APPROVED shapes, dropped 2px because he is crouched
HEAD_PTS = tr([
    (87.5, 6.0), (78.0, 6.3), (70.0, 7.4), (63.5, 9.6), (58.6, 12.8),
    (55.2, 17.2), (53.4, 22.6), (53.0, 28.6), (53.4, 35.0), (54.8, 41.6),
    (57.2, 47.4), (60.6, 52.4), (65.2, 56.4), (71.0, 59.4), (77.4, 61.2),
    (83.0, 61.9), (87.5, 62.0),
], dy=-4)
BEANIE_PTS = tr([
    (87.5, 1.6), (77.6, 1.9), (69.4, 3.2), (62.8, 5.8), (57.8, 9.6),
    (54.4, 14.8), (52.6, 20.6), (52.2, 26.4), (52.8, 32.0), (54.4, 37.6),
    (57.4, 40.6), (61.0, 39.8), (61.8, 34.0), (61.2, 30.0),
    (66.0, 29.2), (74.0, 28.6), (87.5, 28.5),
], dy=-4)
# the same knit stretched over a topknot bun: a bulge at the crown
BEANIE_BUN = tr([
    (87.5, -3.0), (80.0, -2.6), (74.0, -0.6), (70.4, 2.6), (69.6, 6.4),
    (66.0, 6.0), (61.0, 8.2), (57.2, 12.0), (54.4, 16.6), (52.6, 21.6),
    (52.2, 26.4), (52.8, 32.0), (54.4, 37.6), (57.4, 40.6), (61.0, 39.8),
    (61.8, 34.0), (61.2, 30.0), (66.0, 29.2), (74.0, 28.6), (87.5, 28.5),
], dy=-4)

# torso: a heavy frame carrying real muscle.  Widest across the ribs, and the
# gut is firm -- it does not hang past the hips.
BODY_PTS = [
    (87.5, 44.0), (74.0, 44.8), (62.0, 47.6), (51.6, 52.4), (43.0, 58.6),
    (36.0, 66.0), (31.4, 74.0), (28.6, 82.0), (27.8, 89.0), (29.2, 95.0),
    (33.0, 99.4), (40.0, 102.4), (51.0, 104.2), (65.0, 105.0),
    (87.5, 105.2),
]

# the crouch: thighs drive out and down, knees are the widest point
LEG_PTS = [
    (32.0, 84.0), (87.5, 84.0), (86.0, 96.0), (78.0, 106.0),
    (69.0, 113.0), (61.0, 121.0), (55.0, 129.0), (50.4, 136.0),
    (48.0, 143.0), (14.0, 143.0), (11.6, 136.0), (8.6, 128.0),
    (7.0, 118.0), (8.8, 106.0), (15.0, 94.0),
]
FOOT_PTS = [
    (12.0, 136.0), (50.0, 136.0), (51.6, 138.6), (51.8, 141.0),
    (50.6, 143.0), (7.0, 143.0), (3.0, 141.4), (3.2, 139.0),
    (5.6, 137.2), (8.6, 136.4),
]

# ---- option (a): the approved very-ripped shorts
SHORTS_PTS = [
    (87.5, 92.0), (72.0, 92.4), (58.0, 94.0), (46.0, 96.6),
    (36.0, 100.0), (27.6, 105.0), (26.6, 115.0), (28.8, 122.0),
    (33.0, 126.4), (39.0, 128.6), (47.0, 127.8), (52.0, 122.6),
    (57.0, 125.0), (64.0, 126.6), (73.0, 127.4), (87.5, 127.6),
]
# ---- option (b): a proper mawashi, wrapped low and tight over the hips
MAWASHI_PTS = [
    (87.5, 94.0), (72.0, 94.4), (58.0, 96.0), (46.0, 98.6),
    (36.0, 102.0), (28.2, 107.0), (27.2, 113.0), (30.4, 119.0),
    (37.0, 122.4), (47.0, 124.2), (62.0, 125.2), (87.5, 125.6),
]
# the kesho-mawashi apron hanging off the front of it
APRON_PTS = [
    (61.0, 108.0), (114.0, 108.0), (116.0, 118.0), (116.0, 136.0),
    (114.0, 140.0), (61.0, 140.0), (59.0, 136.0), (59.0, 118.0),
]
# the twisted rope belt, worn over EITHER bottom half
ROPE_PTS = [
    (87.5, 96.0), (72.0, 96.6), (57.0, 98.6), (44.0, 101.8),
    (34.0, 106.0), (30.6, 109.6), (30.4, 117.0), (37.0, 114.6),
    (47.0, 112.8), (59.0, 111.6), (72.0, 110.8), (87.5, 110.6),
]

# ------------------------------------------------------------------- ARMS
# Every arm shares the same upper-arm contour -- deltoid cap, bicep mass,
# elbow at roughly (11, 82) -- and differs only below the elbow, so any two
# of them cut together cleanly.
_UP_OUT = [(53.0, 41.0), (43.0, 41.6), (33.6, 44.6), (25.0, 50.0),
           (17.6, 57.6), (12.0, 66.6), (9.2, 76.0), (10.0, 85.0)]
_UP_IN = [(31.0, 85.0), (31.4, 73.0), (34.0, 64.0), (38.2, 55.4),
          (43.4, 48.0), (49.0, 43.4)]


def _arm(mid):
    return _UP_OUT + mid + _UP_IN


# idle: forearm down, hand resting on the hip, knee left clear below it
ARM_HANG = _arm([(13.0, 91.0), (17.6, 95.4), (16.0, 100.0), (17.0, 106.0),
                 (22.4, 110.4), (30.4, 111.2), (37.8, 107.6), (40.4, 100.6),
                 (38.6, 94.0), (34.0, 90.6)])
# guard: forearm up, open palm at chest height
ARM_GUARD = _arm([(13.4, 91.0), (19.6, 95.4), (27.0, 96.4), (33.6, 93.0),
                  (36.4, 86.0), (35.0, 78.0), (33.0, 88.0)])
# cocked: forearm swung up, fist held high beside the shoulder
ARM_COCK = _arm([(13.0, 90.0), (19.0, 93.6), (26.0, 93.0), (31.6, 88.6),
                 (33.4, 81.0), (32.0, 72.0), (31.6, 86.0)])
# extended low: the reaching arm of the sumo ready stance
ARM_LOW = _arm([(13.0, 92.0), (18.0, 99.0), (20.4, 107.0), (21.0, 115.0),
                (25.0, 121.4), (32.6, 122.4), (39.4, 118.6), (41.0, 111.0),
                (38.0, 103.0), (34.4, 95.0)])
# slapping: the forearm swings in and the palm is thrust at the camera
ARM_SLAP = _arm([(13.6, 92.0), (18.4, 98.0), (24.0, 101.0), (31.0, 100.0),
                 (36.4, 95.0), (37.6, 88.0), (34.6, 88.0)])

HAND_IDLE = [
    (19.0, 88.0), (27.0, 84.6), (36.0, 85.2), (42.6, 89.6),
    (45.4, 95.0), (47.2, 99.0), (45.6, 103.0), (42.6, 105.0),
    (40.0, 110.6), (32.0, 113.0), (23.0, 110.4), (17.6, 103.4),
    (17.0, 94.0),
]
HAND_GUARD = [
    (24.0, 60.0), (31.0, 55.4), (40.0, 55.0), (47.0, 59.0),
    (50.0, 66.0), (50.6, 76.0), (48.0, 84.0), (42.0, 89.0),
    (33.0, 90.0), (26.0, 86.0), (22.6, 78.0), (22.4, 67.0),
]
HAND_COCK = [
    (23.0, 48.0), (30.0, 43.6), (38.0, 43.8), (44.4, 48.0),
    (46.6, 55.0), (45.6, 63.0), (40.6, 68.4), (32.6, 69.6),
    (25.4, 66.4), (21.4, 59.4), (21.4, 52.0),
]
HAND_LOW = [
    (20.0, 112.0), (28.0, 108.6), (37.0, 109.2), (43.4, 113.6),
    (45.6, 119.0), (44.6, 126.0), (39.6, 131.0), (31.0, 132.2),
    (23.0, 129.4), (18.6, 123.0), (18.2, 116.0),
]
# the big foreshortened palm: the face the hitbox sits on
HAND_SLAP = [
    (30.0, 70.0), (40.0, 63.6), (54.0, 62.4), (65.0, 67.0),
    (71.0, 76.0), (71.6, 91.0), (67.6, 102.0), (59.0, 108.6),
    (46.0, 110.0), (35.6, 105.0), (29.0, 94.0), (28.4, 79.0),
]
HAND_SLAP_CENTRE = (50, 86)      # LEFT hand impact point (mirror: 125, 86)

ARMS = {
    'hang':    (ARM_HANG, HAND_IDLE),
    'guard':   (ARM_GUARD, HAND_GUARD),
    'cock':    (ARM_COCK, HAND_COCK),
    'low':     (ARM_LOW, HAND_LOW),
    'slap':    (ARM_SLAP, HAND_SLAP),
    'slap_hi': (tr(ARM_SLAP, dy=-6), tr(HAND_SLAP, dy=-7)),
    'slap_lo': (tr(ARM_SLAP, dy=4), tr(HAND_SLAP, dy=5)),
    'swingf':  (tr(ARM_HANG, dx=2.5, dy=-2), tr(HAND_IDLE, dx=3, dy=-3)),
    'swingb':  (tr(ARM_HANG, dx=-2.5, dy=2), tr(HAND_IDLE, dx=-3, dy=3)),
    'flail':   (tr(ARM_GUARD, dx=-3, dy=-5), tr(HAND_GUARD, dx=-5, dy=-9)),
    'limp':    (tr(ARM_HANG, dx=-2, dy=4), tr(HAND_IDLE, dx=-3, dy=5)),
}

# the splayed seat for the defeat
LEG_SIT = [
    (26.0, 96.0), (87.5, 96.0), (86.0, 106.0), (78.0, 116.0),
    (66.0, 124.0), (50.0, 132.0), (30.0, 137.0), (16.0, 139.0),
    (8.0, 135.0), (7.0, 124.0), (11.0, 110.0),
]
FOOT_SIT = [
    (5.0, 130.0), (18.0, 128.0), (22.0, 132.0), (22.6, 138.0),
    (18.0, 143.0), (7.0, 143.0), (3.0, 141.0), (2.6, 136.0), (3.4, 132.0),
]

DEFAULT = dict(arm='hang', arm_l=None, arm_r=None, head_dy=0, all_dy=0,
               dx=0, belly_s=1.0, leg='stand', eye='sleepy', mouth='slack',
               bubble=2, knuck=True, bottom='mawashi', paint=0, bun=0,
               rope=1, pose='idle')


def spec_for(pose):
    if pose == 'awake':
        return dict(DEFAULT, arm_l='low', arm_r='cock', eye='awake',
                    mouth='roar', bubble=0, knuck=False)
    if pose == 'land':
        return dict(DEFAULT, arm='hang', eye='awake', mouth='roar', bubble=0)
    return dict(DEFAULT)


def build_rig(pose='idle', spec=None):
    sp = dict(DEFAULT, **(spec if spec is not None else spec_for(pose)))
    R = Rig(W, H, AX, DX=0)
    dx, ady, hdy = sp['dx'], sp['all_dy'], sp['head_dy']

    HEAD = tr(R.mirror(HEAD_PTS), dx=dx, dy=ady + hdy)
    BEANIE = tr(R.mirror(BEANIE_BUN if sp['bun'] else BEANIE_PTS),
                dx=dx, dy=ady + hdy)
    BODY = tr(R.mirror(BODY_PTS), dx=dx, dy=ady,
              sx=sp['belly_s'], sy=sp['belly_s'], oy=105.2)
    sit = sp['leg'] == 'sit'
    LEG_SRC = LEG_SIT if sit else LEG_PTS
    FOOT_SRC = FOOT_SIT if sit else FOOT_PTS
    ldy = 0 if sit else ady
    LEG = tr(LEG_SRC, dx=dx, dy=ldy)
    FOOT = tr(FOOT_SRC, dx=dx, dy=ldy)
    LEG_R = tr(R.mx(LEG_SRC), dx=dx, dy=ldy)
    FOOT_R = tr(R.mx(FOOT_SRC), dx=dx, dy=ldy)

    def side(name):
        arm, hand = ARMS[name]
        return (tr(arm, dx=dx, dy=ady),
                tr(hand, dx=dx, dy=ady) if hand else None)

    sym = (sp['arm_l'] is None and sp['arm_r'] is None and dx == 0)
    if sym:
        ARM_L, HAND_L = side(sp['arm'])
        ARM_R = HAND_R = None
    else:
        ARM_L, HAND_L = side(sp['arm_l'] or sp['arm'])
        aR, hR = side(sp['arm_r'] or sp['arm'])
        ARM_R, HAND_R = R.mx(aR), (R.mx(hR) if hR else None)

    R.region('leg_l', LEG, 1, 'leg_l', 'skin')
    if dx == 0:
        R.region('leg_r', None, 1, 'leg_r', 'skin', mirror_of='leg_l')
    else:
        R.region('leg_r', LEG_R, 1, 'leg_r', 'skin')
    R.region('foot_l', FOOT, 2, 'foot_l', 'skin')
    if dx == 0:
        R.region('foot_r', None, 2, 'foot_r', 'skin', mirror_of='foot_l')
    else:
        R.region('foot_r', FOOT_R, 2, 'foot_r', 'skin')
    if sp['bottom'] == 'mawashi':
        R.region('shorts', tr(R.mirror(MAWASHI_PTS), dx=dx, dy=ady), 3,
                 'shorts', 'mawashi', sym=(dx == 0))
        R.region('apron', tr(APRON_PTS, dx=dx, dy=ady), 3.2, 'apron',
                 'mawashi', sym=(dx == 0))
    else:
        R.region('shorts', tr(R.mirror(SHORTS_PTS), dx=dx, dy=ady), 3,
                 'shorts', 'shorts', sym=(dx == 0))
    if sp['rope']:
        R.region('rope', tr(R.mirror(ROPE_PTS), dx=dx, dy=ady), 3.6, 'rope',
                 'rope', sym=(dx == 0))
    R.region('body', BODY, 4, 'body', 'belly', sym=(dx == 0))
    R.region('arm_l', ARM_L, 5, 'arm_l', 'skin')
    if sym:
        R.region('arm_r', None, 5, 'arm_r', 'skin', mirror_of='arm_l')
    else:
        R.region('arm_r', ARM_R, 5.2, 'arm_r', 'skin')
    if HAND_L:
        R.region('hand_l', HAND_L, 6, 'hand_l', 'skin')
        if sym:
            R.region('hand_r', None, 6, 'hand_r', 'skin', mirror_of='hand_l')
    if HAND_R:
        R.region('hand_r', HAND_R, 6.2, 'hand_r', 'skin')
    R.region('head', HEAD, 9, 'head', 'skin', sym=(dx == 0))
    R.region('beanie', BEANIE, 11, 'beanie', 'bw', sym=(dx == 0))
    R.sp = sp
    return R


# -------------------------------------------------------- procedural cloth
def paint_beanie(g, R):
    mask = visible_mask(R, 'beanie')
    for y in range(H):
        for x in range(W):
            if mask[y][x] and g[y][x] != 'K':
                i = (87 - x) if x <= 87 else (x - 88)
                lit = 'n' if (i % 3 == 1) else 'C'
                t = (x - 60) * 0.62 + (y - 4) * 0.78
                g[y][x] = lit if t < 40 else ('m' if lit == 'n' else 'N')


def paint_rope(g, R):
    """The twisted rice-straw rope: chunky braided segments in warm grey, not
    a smooth bar, with a knot and two short tails over the centre front."""
    mask = visible_mask(R, 'rope')
    for x in range(W):
        ys = [y for y in range(H) if mask[y][x] and g[y][x] != 'K']
        if not ys:
            continue
        top, bot = ys[0], ys[-1]
        span = max(1, bot - top)
        for y in ys:
            v = (y - top) / float(span)
            lvl = 0 if v < 0.16 else 1 if v < 0.44 else 2 if v < 0.74 else 3
            # chunky diagonal strands with a hard groove between them: this
            # is what stops it reading as a chrome bar
            band = ((x * 3 + y * 2) // 9) % 2
            edge = ((x * 3 + y * 2) % 9) < 2
            lvl = min(3, lvl + (1 if band else 0) + (1 if edge else 0))
            g[y][x] = ['W', 'G', 'g', 'q'][lvl]
    # the knot and its two short tails, dead centre
    stamp(g, 80, 103, '\n'.join([
        "..KKKKKKKK..",
        ".KGGggggGGK.",
        "KGGgqqqqgGGK",
        "KGgqqKKqqgGK",
        ".KggqqqqggK.",
        "..KKgqqgKK..",
        "...KGggGK...",
        "...KggqgK...",
        "....KKKK....",
    ]))


def paint_mawashi(g, R):
    """Blue-and-white vertical stripes, the same knit palette as his beanie."""
    mask = visible_mask(R, 'shorts')
    for x in range(W):
        ys = [y for y in range(H) if mask[y][x] and g[y][x] != 'K']
        if not ys:
            continue
        top, bot = ys[0], ys[-1]
        span = max(1, bot - top)
        i = (87 - x) if x <= 87 else (x - 88)
        stripe = (i // 4) % 2 == 0
        for y in ys:
            v = (y - top) / float(span)
            if stripe:
                g[y][x] = 'C' if v < 0.34 else 'N' if v < 0.70 else 'n'
            else:
                g[y][x] = 'N' if v < 0.34 else 'n' if v < 0.70 else 'm'


def paint_apron(g, R):
    """Kesho-mawashi: Mount Fuji over waves, straight off the SF6 reference."""
    mask = visible_mask(R, 'apron')
    for x in range(W):
        ys = [y for y in range(H) if mask[y][x] and g[y][x] != 'K']
        if not ys:
            continue
        top, bot = ys[0], ys[-1]
        span = max(1, bot - top)
        for y in ys:
            v = (y - top) / float(span)
            g[y][x] = 'n' if v < 0.14 else 'm' if v < 0.86 else 'k'
    # gold trim along the top and bottom edges
    for x in range(W):
        ys = [y for y in range(H) if mask[y][x] and g[y][x] != 'K']
        if not ys:
            continue
        for k in (0, 1):
            if ys[0] + k <= ys[-1]:
                g[ys[0] + k][x] = 'Y' if k == 0 else 'y'
            if ys[-1] - k >= ys[0]:
                g[ys[-1] - k][x] = 'Y' if k == 0 else 'y'
    # Mount Fuji over waves, as in the SF6 reference
    stamp(g, 63, 113, '\n'.join([
        "...........EE...........",
        "..........EWWE..........",
        ".........EWWWWE.........",
        "........EWWEEWWE........",
        ".......EWWENNEWWE.......",
        "......EWNNNNNNNNWE......",
        ".....ENNNNNNNNNNNNE.....",
        "....ENNNNNNNNNNNNNNE....",
        "...ENNNNNNNNNNNNNNNNE...",
        "..ENNNNNNNNNNNNNNNNNNE..",
        "CCCCCCCCCCCCCCCCCCCCCCCC",
        "CCNNCCCCNNCCCCNNCCCCNNCC",
        "NNCCNNNNCCNNNNCCNNNNCCNN",
    ]))


# ======================================================== FACE (left halves)
# beanie cuff lands on y 26; brows 29; eye slit 36; nose 33..44;
# mouth 46..53; jowls 52..56.
FACE_DY = -4      # everything below was authored for the approved head

SLEEPY_EYE = SM(MIR, 32 + FACE_DY, [
    (60, "...KKKKKKKKKKKKKK"),
    (60, "..KssssssssssssssK"),
    (59, "..KKKKKKKKKKKKKKKKKK"),
    (59, ".KKKKKKKKKKKKKKKKKKK"),
    (59, "KKKKKKKKKKKKKKKKKKKK"),
    (59, "KKKKKKKKKKKKKKKKKKKK"),
    (59, "sKKKKKKKKKKKKKKKKKKs"),
    (59, "ssKKKKKKKKKKKKKKKKss"),
    (59, ".ssssssssssssssssss."),
    (60, "..dssssssssssssssd.."),
    (61, "...dddddddddddddd..."),
])
NOSE = SM(MIR, 37 + FACE_DY, [
    (83, "SSSSS"), (82, "sSSSSS"), (82, "sSSSSS"), (81, "ssSSSSS"),
    (81, "ssSSSSS"), (80, "sdSSSSSS"), (79, "sddSSSSSS"), (78, "sddSSSSSSS"),
    (78, "sddKKsSSSS"), (78, "sdKKKssSSS"), (78, "sdddddddds"),
])
SLEEPY_MOUTH = SM(MIR, 50 + FACE_DY, [
    (78, "..KKKKKKKKKK"), (77, ".KKMMMMMMMMMM"), (76, "KKMMMMMMMMMMMM"),
    (76, "KKMMMMMMMMMMMM"), (76, "KKddddddddddddd"), (77, ".KKdddddddddddd"),
    (78, "..KKKKKKKKKKKK"),
])
STUBBLE = SM(MIR, 57 + FACE_DY, [
    (72, ".d..d...d"), (71, "d...d..d"), (73, "..d..d"),
])
BRIM_SH = SM(MIR, 29 + FACE_DY, [
    (61, "sssssssssssssssssssssssss"),
    (62, "sssssssssssssssssssssssss"),
    (63, "dddddddddddddddddddddddd"),
])
BUBBLE = [S(94, 43 + FACE_DY, [
    "..KKKK..", ".KEEWWK.", "KEEWWWWK", "KEWWWWWK", "KWWWWWWK",
    ".KWWWWK.", "..KKKK..",
])]

# E. Honda's kabuki stroke: a bold bar straight THROUGH each eye, starting
# under the beanie cuff and running onto the cheek, so it cannot read as a
# wound at the temple.
PAINT = SM(MIR, 24, [
    (58, "KRRRRRRRRRRK"),   # 24 starts right under the beanie cuff
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),
    (58, "KRrrrrrrrrRK"),      # 27  (the eye slab covers 28-38)
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),      # 39 back out onto the cheek
    (60, "KRrrrrRK"),
    (60, "KRrrrrRK"),
    (59, ".KRrrrrrrRK"),
    (59, ".KRrrrrrrRK"),
    (60, "..KRrrrrRK"),
    (61, "..KRRRRK"),
    (62, "...KKKK"),
])

# hair escaping from under the cuff when he wears the bun
HAIR_OUT = SM(MIR, 24 + FACE_DY, [
    (55, "jj"), (54, "jjj"), (54, "hjj"), (55, "hj"), (55, ".j"),
])

COLLAR = SM(MIR, 56, [
    (58, "..........KKrrrrrrrrrrrrrrrrrrrrrr"),
    (57, "........KKrRRRRRRRRRRRRRRRRRRRRRRR"),
    (56, ".......KrrRRrrrrrrrrrrrrrrrrrrrrrrr"),
    (56, "......KrrRrK..KrrrrrrrrrrrrrrrrrrrM"),
    (56, ".....KrrRrK....KrrrrrrrrrrrrrrrrMMM"),
    (57, ".....KrrK.......KrrrrrrrrrrrrrMMMMM"),
    (58, "......KK.........KKrrrrrrrrMMMMMMMM"),
    (61, "....................KKMMMMMMMMMMMMM"),
])
CHAIN = SM(MIR, 63, [
    (77, "yYssssssssss"), (77, ".yYsssssssss"), (78, ".yYssssssss"),
    (79, ".yYsssssss"), (80, ".yYssssss"), (81, ".yYsssss"),
    (82, ".yYssss"), (83, "..yYss"), (84, "..yYs"), (85, "..yY"),
])
NAVEL = SM(MIR, 84, [
    (82, "..dddd"), (81, ".dKKKK"), (81, ".dKKKK"), (82, "..dKKK"),
    (83, "...ddd"),
])
TOES = SM(MIR, 137, [
    (5, "..KSSSSSSKSSSSSKSSSSKSSSSK"),
    (4, ".KSSSSSSSKSSSSSKSSSSKSSSSK"),
    (4, ".KSssssSSKSssssKSsssKSsssK"),
    (4, ".KsssssssKsssssKssssKssssK"),
    (4, ".KdddddddKddddKdddKdddK"),
    (4, ".KKKKKKKKKKKKKKKKKKKKKKK"),
])


# ---- animation faces, in this head's coordinate space (FACE_DY = -4)
HALF_EYE = SM(MIR, 27, [
    (60, "..KKKKKKKKKKKKKK"),
    (59, ".KKKKKKKKKKKKKKKKK"),
    (59, "KKKKKKKKKKKKKKKKKK"),
    (59, "KKKKKKKKKKKKKKKKKK"),
    (59, "KEEEEKKKKKKEEEEEEK"),
    (59, "KEEEKKKKKKKKEEEEEK"),
    (59, ".KEEEEEEEEEEEEEEK."),
    (59, "..KKKKKKKKKKKKKK.."),
    (60, "...dddddddddddd..."),
])
AWAKE_EYE = SM(MIR, 26, [
    (57, "KKKKKKKKKKKKKKKKKKKKKK"),
    (57, ".KKKKKKKKKKKKKKKKKKKKK"),
    (58, ".KKKKKKKKKKKKKKKKKKKKK"),
    (59, ".KKKKKKKKKKKKKKKKKKKKK"),
    (59, "..KKKKKKKKKKKKKKKKKK"),
    (59, ".KEEEEEEEEEEEEEEEEEK"),
    (59, "KEEEEEEEEKKKKEEEEEEK"),
    (59, "KEEEEEEEKKKKKKEEEEEK"),
    (59, "KEEEEEEEEKKKKEEEEEEK"),
    (59, ".KEEEEEEEEEEEEEEEEEK"),
    (59, "..KKKKKKKKKKKKKKKKKK"),
    (60, "...ddddddddddddddd.."),
])
WIDE_EYE = SM(MIR, 25, [
    (57, "..KKKKKKKKKKKKKKKK"),
    (57, ".KKKKKKKKKKKKKKKKK"),
    (57, "KKEEEEEEEEEEEEEEKK"),
    (57, "KEEEEEEEEEEEEEEEEK"),
    (57, "KEEEEEEKKKKEEEEEEK"),
    (57, "KEEEEEKKKKKKEEEEEK"),
    (57, "KEEEEEKKKKKKEEEEEK"),
    (57, "KEEEEEEKKKKEEEEEEK"),
    (57, "KEEEEEEEEEEEEEEEEK"),
    (57, ".KKEEEEEEEEEEEEKK."),
    (57, "..KKKKKKKKKKKKKK.."),
    (58, "...dddddddddddd..."),
])
SHUT_EYE = SM(MIR, 30, [
    (60, "...KKKKKKKKKKK"),
    (59, "..KsssssssssssK"),
    (59, ".KKKKKKKKKKKKKKK"),
    (59, "KKKKKKKKKKKKKKKK"),
    (60, ".sssssssssssss."),
    (61, "..dddddddddd.."),
])
MOUTH_ROAR = SM(MIR, 43, [
    (76, "...KKKKKKKKKKKK"),
    (74, "..KKEEEEEEEEEEEE"),
    (73, ".KKMMMMMMMMMMMMM"),
    (72, "KKMMMMMMMMMMMMMM"),
    (72, "KKMMMMMMMMMMMMMM"),
    (72, "KKMMMMMMMMMMMMMM"),
    (73, ".KKMMMMMMMMMMMMM"),
    (74, "..KKEEEEEEEEEEEE"),
    (75, "...KKdddddddddddd"),
    (76, "....KKKKKKKKKKKK"),
])
MOUTH_OW = SM(MIR, 45, [
    (76, "...KKKKKKKKKK"),
    (74, "..KKMMMMMMMMMM"),
    (73, ".KKEKEKEKEKEKE"),
    (73, ".KKMMMMMMMMMMM"),
    (73, ".KKEKEKEKEKEKE"),
    (74, "..KKMMMMMMMMMM"),
    (75, "...KKdddddddddd"),
    (76, "....KKKKKKKKKK"),
])
MOUTH_SNORE = SM(MIR, 47, [
    (80, "..KKKKKK"),
    (79, ".KMMMMMM"),
    (79, ".KMMMMMM"),
    (79, ".KMMMMMM"),
    (80, "..Kddddd"),
    (81, "...KKKKK"),
])
BUBBLE_S = [S(95, 45, [".KKK.", "KEWWK", "KWWWK", ".KKK."])]
BUBBLE_L = [S(93, 37, [
    "...KKKKK...", "..KEEWWWK..", ".KEEWWWWWK.", "KEEWWWWWWWK",
    "KEWWWWWWWWK", "KWWWWWWWWWK", ".KWWWWWWWK.", "..KWWWWWK..",
    "...KKKKK...",
])]
BUBBLE_POP = [S(92, 36, [
    "..W.....W..", "...W...W...", ".W..K.K..W.", "....W.W....",
    "..W..K..W..", "...W...W...", "..W.....W..",
])]

EYES = {'sleepy': SLEEPY_EYE, 'awake': AWAKE_EYE, 'half': HALF_EYE,
        'wide': WIDE_EYE, 'shut': SHUT_EYE}
MOUTHS = {'slack': SLEEPY_MOUTH, 'roar': MOUTH_ROAR, 'ow': MOUTH_OW,
          'snore': MOUTH_SNORE}
BUBBLES = {0: [], 1: BUBBLE_S, 2: BUBBLE, 3: BUBBLE_L, 4: BUBBLE_POP}


def paint_creases(g, sp):
    """Athletic anatomy: this is the pass that stops him reading as soft."""
    dx, ady, hdy = sp['dx'], sp['all_dy'], sp['head_dy']

    def C(pts, ch, thick=1, over=SKIN, mirror=True, head=False):
        oy = ady + (hdy if head else 0)
        q = [(x + dx, y + oy) for (x, y) in pts]
        curve(g, q, ch, thick=thick, over=over,
              mirror_axis=(MIR + 2 * dx) if mirror else None)

    # traps rolling off the neck onto the shoulders
    C([(60, 54), (70, 49), (80, 47)], 'S', 2, set('sdD'))
    C([(57, 58), (70, 53), (82, 51)], 'd', 1)
    C([(59, 61), (72, 57), (87.5, 55)], 'D', 1)
    # deltoid caps, then the crease splitting them from the pecs
    C([(24, 55), (17, 64), (14.6, 74)], 'S', 4, set('sdD'))
    C([(26, 52), (20, 60), (17, 70)], 'S', 2, set('sdD'))
    C([(44, 50), (37, 58), (34, 68)], 'd', 2)
    C([(46, 49), (39, 57), (36, 67)], 'D', 1)
    # pecs: two distinct slabs, lit on top, hard crease underneath
    C([(43, 58), (58, 58), (73, 61)], 'S', 4, set('sdD'))
    C([(39, 68), (52, 75), (67, 78), (80, 76)], 'd', 3)
    C([(40, 66), (54, 72), (68, 75), (80, 73)], 'D', 2)
    C([(87.5, 56), (87.5, 78)], 'd', 1, set('Ss'), mirror=False)
    C([(87.5, 57), (87.5, 77)], 'D', 1, set('sd'), mirror=False)
    # serratus
    for k, yy in enumerate((72, 79)):
        C([(33 + k * 2, yy), (41 + k * 2, yy + 4)], 'd', 2)
        C([(34 + k * 2, yy - 1), (42 + k * 2, yy + 3)], 'S', 1, set('sd'))
    # a firm gut: the upper abs read, the lower belly is taut
    C([(60, 80), (72, 82), (80, 81)], 'd', 2)
    C([(63, 87), (74, 89), (81, 88)], 'd', 2)
    C([(52, 84), (56, 93), (58, 102)], 'S', 4, set('sdD'), mirror=False)
    C([(62, 82), (66, 92), (68, 101)], 'S', 2, set('sdD'), mirror=False)
    # obliques driving into the belt
    C([(31, 86), (37, 94), (46, 100)], 'd', 2)
    C([(33, 85), (39, 93), (47, 99)], 'D', 1)
    # arms: bicep / tricep split and the elbow
    C([(15, 70), (22, 74), (29, 72)], 'd', 2)
    C([(13, 82), (20, 86), (28, 84)], 'd', 1)

    # ---- hands, detailed per side for whatever that side is holding
    def hand_detail(name, mir):
        def P(pts, ch, thick=1, over=SKIN, ddx=0.0, ddy=0.0):
            q = [(x + ddx + dx, y + ddy + ady) for (x, y) in pts]
            if mir is None:
                curve(g, q, ch, thick=thick, over=over,
                      mirror_axis=MIR + 2 * dx)
            elif mir:
                curve(g, [(MIR - x + 2 * dx, y) for (x, y) in q], ch,
                      thick=thick, over=over)
            else:
                curve(g, q, ch, thick=thick, over=over)

        if name in ('hang', 'swingf', 'swingb', 'limp'):
            d = {'swingf': (3, -3), 'swingb': (-3, 3),
                 'limp': (-3, 5)}.get(name, (0, 0))
            P([(22, 92), (30, 90), (39, 92)], 'S', 2, set('sdD'), *d)
            for fx in (24, 30, 36):
                P([(fx, 94), (fx + 1, 108)], 'K', 1, SKIN, *d)
                P([(fx - 1, 94), (fx, 108)], 'S', 1, set('sdD'), *d)
            P([(21, 95), (30, 98), (40, 96)], 'd', 2, SKIN, *d)
            P([(43, 95), (46, 99), (43, 103)], 'd', 2, SKIN, *d)
        elif name in ('guard', 'flail'):
            d = (-5.0, -9.0) if name == 'flail' else (0.0, 0.0)
            for fx, y0 in ((28, 59), (35, 57), (42, 58)):
                P([(fx, y0), (fx, y0 + 11)], 'K', 1, SKIN, *d)
                P([(fx - 1, y0), (fx - 1, y0 + 11)], 'S', 1, set('sdD'), *d)
            P([(25, 70), (34, 73), (46, 71)], 'd', 2, SKIN, *d)
            P([(25, 80), (34, 84), (45, 82)], 'd', 2, SKIN, *d)
        elif name == 'cock':
            for fx in (27, 33, 39):
                P([(fx, 48), (fx, 57)], 'K', 1)
                P([(fx - 1, 48), (fx - 1, 57)], 'S', 1, set('sdD'))
            P([(24, 60), (33, 63), (43, 61)], 'd', 2)
        elif name == 'low':
            P([(23, 115), (31, 113), (40, 115)], 'S', 2, set('sdD'))
            for fx in (25, 31, 37):
                P([(fx, 117), (fx + 1, 129)], 'K', 1)
                P([(fx - 1, 117), (fx, 129)], 'S', 1, set('sdD'))
            P([(22, 118), (31, 121), (41, 119)], 'd', 2)
        elif name in ('slap', 'slap_hi', 'slap_lo'):
            sdy = {'slap': 0, 'slap_hi': -7, 'slap_lo': 5}[name]
            for fx in (40, 50, 60):
                P([(fx, 70), (fx, 87)], 'K', 1, SKIN, 0, sdy)
                P([(fx - 1, 70), (fx - 1, 87)], 'S', 1, set('sdD'), 0, sdy)
            P([(32, 92), (50, 97), (68, 93)], 'd', 2, SKIN, 0, sdy)
            P([(30, 80), (33, 94), (39, 105)], 'S', 2, set('sdD'), 0, sdy)
            P([(76, 78), (77, 92), (71, 107)], 'd', 3, SKIN, 0, sdy)
            P([(79, 80), (80, 92), (74, 108)], 'D', 2, SKIN, 0, sdy)

    if sp['arm_l'] is None and sp['arm_r'] is None:
        hand_detail(sp['arm'], None)
    else:
        hand_detail(sp['arm_l'] or sp['arm'], False)
        hand_detail(sp['arm_r'] or sp['arm'], True)

    # thigh: the quad sweeps from the hip out to the knee
    if sp['leg'] != 'sit':
        C([(24, 98), (16, 106), (12, 114)], 'S', 5, set('sdD'))
        C([(34, 96), (26, 106), (22, 116)], 'S', 3, set('sdD'))
        C([(62, 98), (70, 108), (64, 118)], 'd', 3)
        C([(64, 97), (72, 107), (66, 117)], 'D', 1)
        # the knee: a lit cap, a crease above it and a hard shadow under it
        C([(12, 114), (24, 110), (40, 113)], 'd', 2)
        C([(11, 117), (24, 114), (40, 117)], 'S', 4, set('sdD'))
        C([(12, 123), (24, 121), (40, 124)], 'd', 2)
        C([(13, 125), (25, 123), (40, 126)], 'D', 1)
        # the shin tapers to the ankle, calf shaded on the inside
        C([(11, 128), (16, 134), (20, 141)], 'S', 3, set('sdD'))
        C([(42, 126), (46, 134), (44, 142)], 'd', 3)
        C([(44, 125), (48, 133), (46, 141)], 'D', 1)
        C([(16, 136), (28, 135), (40, 138)], 's', 1)
    # head volume
    C([(59, 34), (57, 42), (60, 49)], 's', 2, set('S'), mirror=False, head=True)
    C([(116, 35), (118, 42), (114, 49)], 's', 2, set('S'), mirror=False,
      head=True)
    C([(62, 51), (74, 57), (87.5, 59)], 'd', 2, head=True)


def rip_shorts(g, R, under):
    """The approved damage, unchanged: side slashes, torn hem, holes, fray."""
    vis = visible_mask(R, 'shorts')
    full = region_mask(R, 'shorts')
    DEEP = {'S': 'S', 's': 's', 'd': 'd', 'D': 'D', 'K': 'K'}
    cloth = [[False] * W for _ in range(H)]
    for x in range(W):
        ys = [y for y in range(H) if vis[y][x] and g[y][x] != 'K']
        if not ys:
            continue
        top, bot = ys[0], ys[-1]
        span = max(1, bot - top)
        for y in ys:
            v = (y - top) / float(span)
            g[y][x] = 'R' if v < 0.18 else 'r' if v < 0.62 else \
                      'D' if v < 0.88 else 'M'
            cloth[y][x] = True
    for fx in (48, 66, 78):
        for mx, side in ((fx, -1), (MIR - fx, +1)):
            for y in range(111, 128):
                if cloth[y][mx]:
                    g[y][mx] = {'R': 'r', 'r': 'D', 'D': 'M',
                                'M': 'M'}[g[y][mx]]
                lx = mx + side
                if cloth[y][lx] and g[y][lx] in ('r', 'D'):
                    g[y][lx] = {'r': 'R', 'D': 'r'}[g[y][lx]]

    def carve(x, y):
        if not (0 <= x < W and 0 <= y < H) or not cloth[y][x]:
            return
        cloth[y][x] = False
        u = under[y][x]
        g[y][x] = DEEP.get(u, u) if u != ' ' else ' '

    for k in range(16):
        y = 110 + k
        wdt = k // 5
        for sx in (46 - k // 6, 63 - k // 8):
            for mx in (sx, MIR - sx):
                for x in range(mx - wdt, mx + wdt + 1):
                    carve(x, y)
    TOOTH = (3, 6, 2, 8, 4, 7, 2, 5)
    TW = 12
    for x in range(W):
        ys = [y for y in range(H) if cloth[y][x]]
        if not ys:
            continue
        i = min(x, MIR - x)
        depth = TOOTH[(i // TW) % len(TOOTH)]
        k = i % TW
        f = abs(k - (TW - 1) / 2.0) / ((TW - 1) / 2.0)
        bite = int(round(depth * f * f))
        if abs(x - 87.5) < 13:
            bite = min(bite, 2)
        for j in range(bite):
            carve(x, ys[-1] - j)
    for (hx, hy, hr) in ((58, 117, 4), (76, 122, 3)):
        for mx in (hx, MIR - hx):
            for y in range(hy - hr, hy + hr + 1):
                for x in range(mx - hr, mx + hr + 1):
                    if (x - mx) ** 2 + ((y - hy) * 1.3) ** 2 <= hr * hr:
                        carve(x, y)
    shade = {'S': 's', 's': 'd', 'd': 'D', 'D': 'D'}
    for y in range(H - 1):
        for x in range(W):
            if not cloth[y][x]:
                continue
            for k in (1, 2):
                if y + k < H and not cloth[y + k][x] and full[y + k][x] \
                        and g[y + k][x] in shade:
                    g[y + k][x] = shade[g[y + k][x]]
    edge = []
    for y in range(H):
        for x in range(W):
            if not cloth[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or not cloth[ny][nx]:
                    edge.append((x, y))
                    break
    for (x, y) in edge:
        g[y][x] = 'K'


def dither_terminators(g, pairs, phase=0, only=None):
    snap = [row[:] for row in g]
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if only is not None and not only[y][x]:
                continue
            nxt = pairs.get(snap[y][x])
            if nxt is None or (x + y) % 2 != phase:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if snap[y + dy][x + dx] == nxt:
                    g[y][x] = nxt
                    break


def build(pose='idle', spec=None, verify=False):
    sp = dict(DEFAULT, **(spec if spec is not None else spec_for(pose)))
    U = build_rig(pose, sp)
    U.regions = [r for r in U.regions if r['name'] != 'shorts']
    under = U.build_letters()

    R = build_rig(pose, sp)
    g = R.build_letters()
    paint_beanie(g, R)
    paint_creases(g, sp)
    if sp['bottom'] == 'mawashi':
        paint_mawashi(g, R)
        paint_apron(g, R)
    else:
        rip_shorts(g, R, under)
    if sp['rope']:
        paint_rope(g, R)
    dither_terminators(g, {'S': 's', 's': 'd'}, phase=0)
    dither_terminators(g, {'C': 'N', 'n': 'm'}, phase=1,
                       only=visible_mask(R, 'beanie'))

    dx, ady, hdy = sp['dx'], sp['all_dy'], sp['head_dy']
    head_off = (dx, ady + hdy)

    def put(group, off):
        for (x0, y0, block) in group:
            stamp(g, x0 + off[0], y0 + off[1], block)

    put(COLLAR, head_off)
    put(CHAIN + NAVEL, (dx, ady))
    put(TOES, (dx, 0 if sp['leg'] == 'sit' else ady))
    put(BRIM_SH, head_off)
    if sp['paint']:
        put(PAINT, head_off)
    put(NOSE, head_off)
    put(STUBBLE, head_off)
    put(EYES[sp['eye']], head_off)
    put(MOUTHS[sp['mouth']], head_off)
    put(BUBBLES[sp['bubble']], head_off)
    if verify and dx == 0:
        check_symmetry(g, MIR, 'honda')
    return g


if __name__ == '__main__':
    import sys
    sys.path.insert(0, HERE)
    OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
    from pngio import write_png, upscale
    g = build('idle', verify=True)
    pix = to_pix(g)
    write_png(os.path.join(OUT, 'honda_1x.png'), W, H, pix)
    w2, h2, p2 = upscale(W, H, pix, 4, bg='checker')
    write_png(os.path.join(OUT, 'honda_4x.png'), w2, h2, p2)
    print('wrote honda draft')
