"""Evolved Danny: E. Honda x Snorlax sumo, 176x144 per frame.

Design frame: 176 wide x 144 tall, mirror axis x' = 175 - x (AX = 87.5),
feet planted on y = 143 (bottom row) so the sprite bottom-aligns like Carter.
The frame grew from 160 to 176 to make room for the heavier arms.

Identity:
  * the light-blue / blue knit beanie is pulled right down over the whole
    skull -- cuff and side flaps included, the same cut he wears in the
    training room.  It is the one thing carrying "this is Danny" across the
    transformation, so it is unmissable.
  * what is left of his dark-red kit is a pair of very ripped shorts: split
    up both side seams, hem chewed into rags, holes worn through, frayed
    threads hanging.
  * the torn red collar and the gold chain survive from the shirt.
  * heavy half-closed lids, a slack mouth and a sleep bubble keep the Snorlax.

Poses
  idle   sleepy, standing, could nod off where he stands
  awake  eyes open, roaring, hands up in the hundred-hand-slap guard
  land   the impact frame the moment the evolution flash ends

Every symmetric detail is authored as a LEFT half and mirrored by SM() or by
curve(mirror_axis=...); check_symmetry() re-verifies the silhouette.
"""
import os
from rig import (Rig, S, SM, stamp, to_pix, dump, check_symmetry, curve,
                 region_mask, visible_mask, PAL)

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 176, 144
AX = 87.5
MIR = 175            # x' = MIR - x
SKIN = set('SsdD')
CLOTH = set('RrDM')


# ------------------------------------------------------------------ SHAPES
# ---------------------------------------------------------------- GEOMETRY
def tr(pts, dx=0.0, dy=0.0, sx=1.0, sy=1.0, ox=AX, oy=0.0):
    """Translate / scale a point list about (ox, oy)."""
    return [(ox + (x - ox) * sx + dx, oy + (y - oy) * sy + dy) for (x, y) in pts]


HEAD_PTS = [
    (87.5, 6.0), (78.0, 6.3), (70.0, 7.4), (63.5, 9.6), (58.6, 12.8),
    (55.2, 17.2), (53.4, 22.6), (53.0, 28.6), (53.4, 35.0), (54.8, 41.6),
    (57.2, 47.4), (60.6, 52.4), (65.2, 56.4), (71.0, 59.4), (77.4, 61.2),
    (83.0, 61.9), (87.5, 62.0),
]
# the beanie is pulled down over the ENTIRE skull: cuff across the brow and
# knit flaps beside the temples, the same cut he wears in the training room
BEANIE_PTS = [
    (87.5, 1.6), (77.6, 1.9), (69.4, 3.2), (62.8, 5.8), (57.8, 9.6),
    (54.4, 14.8), (52.6, 20.6), (52.2, 26.4), (52.8, 32.0), (54.4, 37.6),
    (57.4, 40.6), (61.0, 39.8), (61.8, 34.0), (61.2, 30.0),
    (66.0, 29.2), (74.0, 28.6), (87.5, 28.5),
]
BODY_PTS = [
    (87.5, 50.0), (74.0, 51.0), (62.0, 54.0), (51.0, 58.4), (42.0, 64.4),
    (35.0, 72.0), (30.4, 80.0), (27.6, 88.0), (26.6, 96.0), (27.4, 103.0),
    (29.6, 104.0), (34.0, 108.0), (42.0, 111.0), (53.0, 113.0),
    (69.0, 114.0), (87.5, 114.2),
]
LEG_STAND = [
    (30.0, 104.0), (88.4, 104.0), (86.0, 116.0), (82.0, 124.0),
    (77.0, 131.0), (72.4, 136.6), (67.0, 140.2), (30.0, 140.2),
    (25.2, 135.0), (24.6, 126.0), (27.2, 115.0),
]
FOOT_STAND = [
    (28.0, 133.0), (67.0, 133.0), (68.6, 136.4), (68.8, 140.0),
    (67.6, 143.0), (21.0, 143.0), (17.4, 141.2), (17.6, 138.2),
    (20.2, 135.6), (24.4, 134.0),
]
# splayed, for the defeat -- he just sits down
LEG_SIT = [
    (26.0, 118.0), (88.4, 118.0), (86.0, 126.0), (79.0, 133.0),
    (68.0, 138.0), (50.0, 142.0), (28.0, 143.0), (14.0, 141.0),
    (7.4, 136.0), (8.0, 127.0), (15.0, 121.0),
]
FOOT_SIT = [
    (5.0, 131.0), (18.0, 129.0), (22.0, 133.0), (22.6, 139.0),
    (18.0, 143.0), (6.0, 143.0), (1.4, 141.0), (0.4, 136.0), (1.2, 133.0),
]
SHORTS_PTS = [
    (87.5, 95.0), (72.0, 95.4), (58.0, 97.0), (46.0, 99.8),
    (36.0, 103.4), (28.2, 108.4), (27.0, 119.0), (29.0, 127.0),
    (33.2, 129.4), (39.0, 132.0), (47.0, 131.2), (52.0, 125.6),
    (57.0, 128.0), (64.0, 129.6), (73.0, 130.4), (87.5, 130.6),
]

# ------------------------------------------------------------------- ARMS
ARM_HANG = [
    (49.0, 57.0), (39.0, 58.6), (29.6, 63.0), (21.6, 70.0),
    (15.4, 79.0), (11.8, 88.0), (10.8, 97.0), (12.0, 105.0),
    (14.6, 111.0), (15.6, 115.0),
    (12.4, 119.0), (11.6, 125.0), (14.6, 130.0), (20.6, 131.6),
    (26.8, 129.6), (30.0, 124.6), (29.6, 118.0), (26.6, 114.6),
    (25.8, 111.0), (26.4, 105.0), (27.0, 97.0), (28.6, 88.0),
    (32.0, 79.0), (36.8, 71.0), (42.4, 64.0), (47.6, 58.6),
]
ARM_GUARD = [
    (49.0, 55.0), (38.0, 56.4), (28.0, 60.6), (19.6, 67.4),
    (13.4, 76.0), (10.2, 85.0), (10.0, 94.0), (13.4, 102.0),
    (19.6, 107.4), (28.0, 109.4), (36.0, 107.6), (41.4, 102.4),
    (42.6, 95.0), (40.0, 87.0), (37.6, 79.0), (38.4, 72.0),
    (42.0, 65.0), (47.0, 58.6),
]
HAND_GUARD = [
    (34.0, 56.0), (40.0, 51.6), (47.0, 51.0), (53.0, 54.0),
    (57.0, 60.0), (57.8, 69.0), (56.0, 78.0), (51.0, 84.0),
    (43.0, 85.6), (36.4, 82.0), (32.6, 75.0), (32.2, 64.0),
]
# the slapping arm: the elbow drops, the forearm swings in and the palm is
# thrust flat at the camera
ARM_SLAP = [
    (50.0, 56.6), (40.0, 58.2), (31.0, 62.6), (23.4, 69.6),
    (17.6, 78.6), (14.4, 88.0), (15.8, 96.0), (20.4, 102.0),
    (28.0, 105.0), (35.6, 103.0), (40.6, 97.0), (41.4, 89.0),
    (40.0, 82.0), (39.2, 75.0), (41.4, 68.0), (46.4, 62.0),
    (53.0, 57.6),
]
# big foreshortened palm thrust at the camera -- the face the hitbox sits on
HAND_SLAP = [
    (33.0, 80.0), (42.0, 73.0), (55.0, 71.6), (66.0, 76.0),
    (72.0, 85.0), (72.6, 100.0), (68.6, 111.0), (60.0, 117.6),
    (47.0, 119.0), (37.0, 114.0), (31.0, 103.0), (30.4, 88.0),
]
HAND_SLAP_CENTRE = (51, 95)      # impact pixel, LEFT hand (mirror: 124, 95)

ARMS = {
    'hang':   (ARM_HANG, None),
    'guard':  (ARM_GUARD, HAND_GUARD),
    'slap':   (ARM_SLAP, HAND_SLAP),
    # the flurry alternates a high slap and a low one so four frames read as
    # a blur of hands rather than the same frame twice
    'slap_hi': (tr(ARM_SLAP, dy=-5), tr(HAND_SLAP, dy=-7)),
    'slap_lo': (tr(ARM_SLAP, dy=3), tr(HAND_SLAP, dy=4)),
    # the other hand, pulled back small and high out of the way
    'cock':   (tr(ARM_GUARD, dy=-2),
               tr(HAND_GUARD, dx=-3, dy=-9, sx=0.86, sy=0.86, ox=44.5, oy=68)),
    'swingf': (tr(ARM_HANG, dx=2.5, dy=-2), None),
    'swingb': (tr(ARM_HANG, dx=-2.5, dy=2), None),
    'flail':  (tr(ARM_GUARD, dx=-3, dy=-5), tr(HAND_GUARD, dx=-5, dy=-9)),
    'limp':   (tr(ARM_HANG, dx=-2, dy=3), None),
}

DEFAULT = dict(arm='hang', arm_l=None, arm_r=None, head_dy=0, all_dy=0,
               dx=0, belly_s=1.0, leg='stand', eye='sleepy', mouth='slack',
               bubble=2, knuck=True)


def spec_for(pose):
    """The three originally-approved poses, expressed as specs."""
    if pose == 'awake':
        return dict(DEFAULT, arm='guard', eye='awake', mouth='roar',
                    bubble=0, knuck=False)
    if pose == 'land':
        return dict(DEFAULT, arm='hang', eye='awake', mouth='roar', bubble=0)
    return dict(DEFAULT)


def build_rig(pose='idle', spec=None):
    sp = dict(DEFAULT, **(spec if spec is not None else spec_for(pose)))
    R = Rig(W, H, AX, DX=0)
    dx, ady, hdy = sp['dx'], sp['all_dy'], sp['head_dy']

    HEAD = R.mirror(tr(HEAD_PTS, dx=dx, dy=ady + hdy))
    BEANIE = R.mirror(tr(BEANIE_PTS, dx=dx, dy=ady + hdy))
    BODY = R.mirror(tr(BODY_PTS, dx=dx, dy=ady,
                       sx=sp['belly_s'], sy=sp['belly_s'], oy=114.2))
    sit = sp['leg'] == 'sit'
    LEG_L = tr(LEG_SIT if sit else LEG_STAND, dx=dx, dy=0 if sit else ady)
    FOOT_L = tr(FOOT_SIT if sit else FOOT_STAND, dx=dx, dy=0 if sit else ady)
    SHORTS = R.mirror(tr(SHORTS_PTS, dx=dx, dy=ady))

    def side(name):
        arm, hand = ARMS[name]
        return (tr(arm, dx=dx, dy=ady),
                tr(hand, dx=dx, dy=ady) if hand else None)

    sym = sp['arm_l'] is None and sp['arm_r'] is None
    if sym:
        ARM_L, HAND_L = side(sp['arm'])
        ARM_R = HAND_R = None
    else:
        ARM_L, HAND_L = side(sp['arm_l'] or sp['arm'])
        aR, hR = side(sp['arm_r'] or sp['arm'])
        ARM_R, HAND_R = R.mx(aR), (R.mx(hR) if hR else None)

    # ---------------------------------------------------------- z-order
    R.region('leg_l', LEG_L, 1, 'leg_l', 'skin')
    R.region('leg_r', None, 1, 'leg_r', 'skin', mirror_of='leg_l')
    R.region('foot_l', FOOT_L, 2, 'foot_l', 'skin')
    R.region('foot_r', None, 2, 'foot_r', 'skin', mirror_of='foot_l')
    R.region('shorts', SHORTS, 3, 'shorts', 'shorts', sym=(dx == 0))
    R.region('body', BODY, 4, 'body', 'belly', sym=(dx == 0))
    R.region('arm_l', ARM_L, 5, 'arm_l', 'skin')
    if sym:
        R.region('arm_r', None, 5, 'arm_r', 'skin', mirror_of='arm_l')
    else:
        R.region('arm_r', ARM_R, 5.2, 'arm_r', 'skin')
    if HAND_L:
        R.region('hand_l', HAND_L, 8, 'hand_l', 'skin')
        if sym:
            R.region('hand_r', None, 8, 'hand_r', 'skin', mirror_of='hand_l')
    if HAND_R:
        R.region('hand_r', HAND_R, 8.2, 'hand_r', 'skin')
    R.region('head', HEAD, 9, 'head', 'skin', sym=(dx == 0))
    R.region('beanie', BEANIE, 11, 'beanie', 'bw', sym=(dx == 0))
    R.sp = sp
    return R


# ------------------------------------------------- procedural cloth passes
def paint_beanie(g, R):
    """Flat 2-light / 1-blue knit, the exact pattern he wears in danny.png."""
    mask = visible_mask(R, 'beanie')
    for y in range(H):
        for x in range(W):
            if mask[y][x] and g[y][x] != 'K':
                i = (87 - x) if x <= 87 else (x - 88)
                lit = 'n' if (i % 3 == 1) else 'C'
                # light from the upper-left: shade the lower-right of the knit
                t = (x - 60) * 0.62 + (y - 4) * 0.78
                g[y][x] = lit if t < 44 else ('m' if lit == 'n' else 'N')


def rip_shorts(g, R, under):
    """Chew the shorts up: split both side seams, tear the hem into rags, wear
    holes through and leave frayed threads hanging.

    `under` is the same figure rendered WITHOUT the shorts, so every tear shows
    the leg behind it (in shadow) rather than punching a hole in the sprite.
    Which pixels are cloth is tracked POSITIONALLY, never by letter: 'D' is
    both the shorts' shadow tone and the deep skin tone, and testing by letter
    made carved pixels read as cloth again.
    """
    vis = visible_mask(R, 'shorts')
    full = region_mask(R, 'shorts')
    DEEP = {'S': 'S', 's': 's', 'd': 'd', 'D': 'D', 'K': 'K'}

    # --- vertical tone ramp over what actually shows, so the garment reads
    cloth = [[False] * W for _ in range(H)]
    for x in range(W):
        ys = [y for y in range(H) if vis[y][x] and g[y][x] != 'K']
        if not ys:
            continue
        top, bot = ys[0], ys[-1]
        span = max(1, bot - top)
        for y in ys:
            v = (y - top) / float(span)
            g[y][x] = 'R' if v < 0.18 else 'r' if v < 0.62 else                       'D' if v < 0.88 else 'M'
            cloth[y][x] = True

    # --- vertical folds down the front of the cloth
    for fx in (48, 66, 78):
        for mx, side in ((fx, -1), (MIR - fx, +1)):
            for y in range(112, 134):
                if cloth[y][mx]:
                    g[y][mx] = {'R': 'r', 'r': 'D', 'D': 'M',
                                'M': 'M'}[g[y][mx]]
                lx = mx + side          # the lit side of each fold, mirrored
                if cloth[y][lx] and g[y][lx] in ('r', 'D'):
                    g[y][lx] = {'r': 'R', 'D': 'r'}[g[y][lx]]

    def carve(x, y):
        """Remove cloth, revealing whatever the shorts were covering."""
        if not (0 <= x < W and 0 <= y < H) or not cloth[y][x]:
            return
        cloth[y][x] = False
        u = under[y][x]
        g[y][x] = DEEP.get(u, u) if u != ' ' else ' '

    # --- waistband: a lit band along the top of what shows
    for x in range(W):
        ys = [y for y in range(H) if cloth[y][x]]
        if not ys:
            continue
        for k in range(4):
            if ys[0] + k <= ys[-1]:
                g[ys[0] + k][x] = 'R' if k < 2 else 'r'

    # --- two slashes torn up the front of each leg, widening toward the hem
    for k in range(20):
        y = 110 + k
        wdt = k // 5
        for sx in (46 - k // 6, 63 - k // 8):
            for mx in (sx, MIR - sx):
                for x in range(mx - wdt, mx + wdt + 1):
                    carve(x, y)

    # --- torn hem: broad tabs of cloth with V notches bitten between them
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
        if abs(x - 87.5) < 13:      # the inseam panel is the last to go
            bite = min(bite, 2)
        for j in range(bite):
            carve(x, ys[-1] - j)

    # --- holes worn through, mirrored
    for (hx, hy, hr) in ((58, 120, 4), (76, 130, 3)):
        for mx in (hx, MIR - hx):
            for y in range(hy - hr, hy + hr + 1):
                for x in range(mx - hr, mx + hr + 1):
                    if (x - mx) ** 2 + ((y - hy) * 1.3) ** 2 <= hr * hr:
                        carve(x, y)

    # --- the cloth throws a hard shadow onto whatever a tear reveals
    shade = {'S': 's', 's': 'd', 'd': 'D', 'D': 'D'}
    for y in range(H - 1):
        for x in range(W):
            if not cloth[y][x]:
                continue
            for k in (1, 2):
                if y + k < H and not cloth[y + k][x] and full[y + k][x]                         and g[y + k][x] in shade:
                    g[y + k][x] = shade[g[y + k][x]]

    # --- black outline round every torn edge
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
        cloth[y][x] = False

    # --- a few frayed threads off the lowest points of the hem
    for tx in (44, 62, 78):
        for mx in (tx, MIR - tx):
            col = [y for y in range(H) if g[y][mx] == 'K' and full[y][mx]]
            if not col:
                continue
            for k in range(1, 4):
                y = col[-1] + k
                if 0 <= y < H and (g[y][mx] == ' ' or g[y][mx] in SKIN):
                    g[y][mx] = 'M' if k == 3 else 'r'


def dither_terminators(g, pairs, phase=0):
    """Stipple a 1px checker along each light->dark boundary.  Big smooth
    masses read flat without it; this is what gives Mason his rendered look."""
    H_, W_ = len(g), len(g[0])
    snap = [row[:] for row in g]
    for y in range(1, H_ - 1):
        for x in range(1, W_ - 1):
            a = snap[y][x]
            nxt = pairs.get(a)
            if nxt is None or (x + y) % 2 != phase:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if snap[y + dy][x + dx] == nxt:
                    g[y][x] = nxt
                    break


def paint_gut_roll(g, R):
    """The gut hangs over the waistband and throws a hard shadow onto it."""
    body = visible_mask(R, 'body')
    dark = {'R': 'r', 'r': 'D', 'D': 'M', 'M': 'M',
            'S': 's', 's': 'd', 'd': 'D'}
    for x in range(W):
        ys = [y for y in range(H) if body[y][x]]
        if not ys:
            continue
        bot = ys[-1]
        for k, ch in ((0, 's'), (-1, 'S'), (-2, 'S')):
            y = bot + k
            if 0 <= y < H and g[y][x] in SKIN:
                g[y][x] = ch
        for k in (1, 2):
            y = bot + k
            if 0 <= y < H and g[y][x] in dark:
                g[y][x] = dark[g[y][x]]


# ======================================================== FACE (left halves)
# Head box: x 53..122, y 8..59.  Centre column pair 87 | 88.
# Beanie cuff lands on y 30; brows 33; eye slit 40; nose 38..48;
# mouth 51..57; jowls 56..60.

# the knit cuff, folded once -- the same black arc his small sprite has
BRIM_SH = SM(MIR, 29, [
    (61, "sssssssssssssssssssssssss"),
    (62, "sssssssssssssssssssssssss"),
    (63, "dddddddddddddddddddddddd"),
])

SLEEPY_EYE = SM(MIR, 32, [
    (60, "...KKKKKKKKKKKKKK"),      # 33 brow top
    (60, "..KssssssssssssssK"),     # 34 brow body
    (59, "..KKKKKKKKKKKKKKKKKK"),   # 35 brow underside
    (59, ".KKKKKKKKKKKKKKKKKKK"),   # 36 heavy lid slab
    (59, "KKKKKKKKKKKKKKKKKKKK"),   # 37
    (59, "KKKKKKKKKKKKKKKKKKKK"),   # 38
    (59, "sKKKKKKKKKKKKKKKKKKs"),   # 39
    (59, "ssKKKKKKKKKKKKKKKKss"),   # 40 the last slit of eye
    (59, ".ssssssssssssssssss."),   # 41 eye bag
    (60, "..dssssssssssssssd.."),   # 42 second fold
    (61, "...dddddddddddddd..."),   # 43
])

AWAKE_EYE = SM(MIR, 30, [
    (57, "KKKKKKKKKKKKKKKKKKKKKK"),  # 31 brows slammed down
    (57, ".KKKKKKKKKKKKKKKKKKKKK"),  # 32
    (58, ".KKKKKKKKKKKKKKKKKKKKK"),  # 33
    (59, ".KKKKKKKKKKKKKKKKKKKKK"),  # 34
    (59, "..KKKKKKKKKKKKKKKKKK"),    # 35
    (59, ".KEEEEEEEEEEEEEEEEEK"),    # 36 sclera
    (59, "KEEEEEEEEKKKKEEEEEEK"),    # 37 iris
    (59, "KEEEEEEEKKKKKKEEEEEK"),    # 38
    (59, "KEEEEEEEEKKKKEEEEEEK"),    # 39
    (59, ".KEEEEEEEEEEEEEEEEEK"),    # 40
    (59, "..KKKKKKKKKKKKKKKKKK"),    # 41
    (60, "...ddddddddddddddd.."),    # 42
])

NOSE = SM(MIR, 37, [
    (83, "SSSSS"),                   # 38 bridge
    (82, "sSSSSS"),                  # 39
    (82, "sSSSSS"),                  # 40
    (81, "ssSSSSS"),                 # 41
    (81, "ssSSSSS"),                 # 42
    (80, "sdSSSSSS"),                # 43
    (79, "sddSSSSSS"),               # 44
    (78, "sddSSSSSSS"),              # 45
    (78, "sddKKsSSSS"),              # 46 nostril
    (78, "sdKKKssSSS"),              # 47
    (78, "sdddddddds"),              # 48
])

SLEEPY_MOUTH = SM(MIR, 50, [
    (78, "..KKKKKKKKKK"),            # 51
    (77, ".KKMMMMMMMMMM"),           # 52
    (76, "KKMMMMMMMMMMMM"),          # 53 dark interior
    (76, "KKMMMMMMMMMMMM"),          # 54
    (76, "KKddddddddddddd"),         # 55 lower lip
    (77, ".KKdddddddddddd"),         # 56
    (78, "..KKKKKKKKKKKK"),          # 57
])

AWAKE_MOUTH = SM(MIR, 47, [
    (76, "...KKKKKKKKKKKK"),         # 48
    (74, "..KKEEEEEEEEEEEE"),        # 49 top teeth
    (73, ".KKMMMMMMMMMMMMM"),        # 50
    (72, "KKMMMMMMMMMMMMMM"),        # 51
    (72, "KKMMMMMMMMMMMMMM"),        # 52
    (72, "KKMMMMMMMMMMMMMM"),        # 53
    (73, ".KKMMMMMMMMMMMMM"),        # 54
    (74, "..KKEEEEEEEEEEEE"),        # 55 bottom teeth
    (75, "...KKdddddddddddd"),       # 56
    (76, "....KKKKKKKKKKKK"),        # 57
])

STUBBLE = SM(MIR, 57, [
    (72, ".d..d...d"),
    (71, "d...d..d"),
    (73, "..d..d"),
])

KABUKI = SM(MIR, 37, [
    (58, "Rrr"),
    (58, "Rrr"),
    (58, "Rrr"),
    (59, "Rrr"),
    (59, "Rrr"),
    (60, ".rr"),
])

# the Snorlax tell: a sleep bubble swelling at one nostril
BUBBLE = [S(94, 43, [
    "..KKKK..",
    ".KEEWWK.",
    "KEEWWWWK",
    "KEWWWWWK",
    "KWWWWWWK",
    ".KWWWWK.",
    "..KKKK..",
])]

# ---- the torn red collar, all that survived of the training-room shirt
COLLAR = SM(MIR, 61, [
    (58, "..........KKrrrrrrrrrrrrrrrrrrrrrr"),   # 55
    (57, "........KKrRRRRRRRRRRRRRRRRRRRRRRR"),   # 56
    (56, ".......KrrRRrrrrrrrrrrrrrrrrrrrrrrr"),  # 57
    (56, "......KrrRrK..KrrrrrrrrrrrrrrrrrrrM"),  # 58
    (56, ".....KrrRrK....KrrrrrrrrrrrrrrrrMMM"),  # 59
    (57, ".....KrrK.......KrrrrrrrrrrrrrMMMMM"),  # 60
    (58, "......KK.........KKrrrrrrrrMMMMMMMM"),  # 61
    (61, "....................KKMMMMMMMMMMMMM"),  # 62
])

CHAIN = SM(MIR, 68, [
    (77, "yYssssssssss"),            # 62
    (77, ".yYsssssssss"),            # 63
    (78, ".yYssssssss"),             # 64
    (79, ".yYsssssss"),              # 65
    (80, ".yYssssss"),               # 66
    (81, ".yYsssss"),                # 67
    (82, ".yYssss"),                 # 68
    (83, "..yYss"),                  # 69
    (84, "..yYs"),                   # 70
    (85, "..yY"),                    # 71
])

NAVEL = SM(MIR, 92, [
    (82, "..dddd"),
    (81, ".dKKKK"),
    (81, ".dKKKK"),
    (82, "..dKKK"),
    (83, "...ddd"),
])

KNUCK = SM(MIR, 120, [
    (13, ".s.s.s.s"),
    (13, "KsKsKsKs"),
    (13, "dsdsdsds"),
    (14, ".K.K.K.K"),
])

TOES = SM(MIR, 135, [
    (19, "..KSSSSSSKSSSSSKSSSSKSSSSK"),
    (18, ".KSSSSSSSKSSSSSKSSSSKSSSSK"),
    (18, ".KSssssSSKSssssKSsssKSsssK"),
    (18, ".KsssssssKsssssKssssKssssK"),
    (18, ".KdddddddKdddddKdddsKddddK"),
    (18, ".KKKKKKKKKKKKKKKKKKKKKKKKK"),
])


# ------------------------------------------------- extra animation faces
# lids cracking open: the moment he stops being a joke
HALF_EYE = SM(MIR, 31, [
    (60, "..KKKKKKKKKKKKKK"),     # 31 brow
    (59, ".KKKKKKKKKKKKKKKKK"),   # 32
    (59, "KKKKKKKKKKKKKKKKKK"),   # 33 heavy lid, still low
    (59, "KKKKKKKKKKKKKKKKKK"),   # 34
    (59, "KEEEEKKKKKKEEEEEEK"),   # 35 a sliver of eye under it
    (59, "KEEEKKKKKKKKEEEEEK"),   # 36
    (59, ".KEEEEEEEEEEEEEEK."),   # 37
    (59, "..KKKKKKKKKKKKKK.."),   # 38
    (60, "...dddddddddddd..."),   # 39
])

# hit react: eyes blown wide open
WIDE_EYE = SM(MIR, 29, [
    (57, "..KKKKKKKKKKKKKKKK"),   # 29
    (57, ".KKKKKKKKKKKKKKKKK"),   # 30
    (57, "KKEEEEEEEEEEEEEEKK"),   # 31
    (57, "KEEEEEEEEEEEEEEEEK"),   # 32
    (57, "KEEEEEEKKKKEEEEEEK"),   # 33
    (57, "KEEEEEKKKKKKEEEEEK"),   # 34
    (57, "KEEEEEKKKKKKEEEEEK"),   # 35
    (57, "KEEEEEEKKKKEEEEEEK"),   # 36
    (57, "KEEEEEEEEEEEEEEEEK"),   # 37
    (57, ".KKEEEEEEEEEEEEKK."),   # 38
    (57, "..KKKKKKKKKKKKKK.."),   # 39
    (58, "...dddddddddddd..."),   # 40
])

# out cold: a simple closed curve
SHUT_EYE = SM(MIR, 34, [
    (60, "...KKKKKKKKKKK"),       # 34
    (59, "..KsssssssssssK"),      # 35
    (59, ".KKKKKKKKKKKKKKK"),     # 36
    (59, "KKKKKKKKKKKKKKKK"),     # 37
    (60, ".sssssssssssss."),      # 38
    (61, "..dddddddddd.."),       # 39
])

# taking a hit: a gritted grimace
MOUTH_OW = SM(MIR, 49, [
    (76, "...KKKKKKKKKK"),        # 49
    (74, "..KKMMMMMMMMMM"),       # 50
    (73, ".KKEKEKEKEKEKE"),       # 51 gritted teeth
    (73, ".KKMMMMMMMMMMM"),       # 52
    (73, ".KKEKEKEKEKEKE"),       # 53
    (74, "..KKMMMMMMMMMM"),       # 54
    (75, "...KKdddddddddd"),      # 55
    (76, "....KKKKKKKKKK"),       # 56
])

# asleep sitting down: a small slack O
MOUTH_SNORE = SM(MIR, 51, [
    (80, "..KKKKKK"),             # 51
    (79, ".KMMMMMM"),             # 52
    (79, ".KMMMMMM"),             # 53
    (79, ".KMMMMMM"),             # 54
    (80, "..Kddddd"),             # 55
    (81, "...KKKKK"),             # 56
])

BUBBLE_S = [S(95, 45, [
    ".KKK.",
    "KEWWK",
    "KWWWK",
    ".KKK.",
])]
BUBBLE_M = [S(94, 43, [
    "..KKKK..",
    ".KEEWWK.",
    "KEEWWWWK",
    "KEWWWWWK",
    "KWWWWWWK",
    ".KWWWWK.",
    "..KKKK..",
])]
BUBBLE_L = [S(93, 41, [
    "...KKKKK...",
    "..KEEWWWK..",
    ".KEEWWWWWK.",
    "KEEWWWWWWWK",
    "KEWWWWWWWWK",
    "KWWWWWWWWWK",
    ".KWWWWWWWK.",
    "..KWWWWWK..",
    "...KKKKK...",
])]
BUBBLE_POP = [S(92, 40, [
    "..W.....W..",
    "...W...W...",
    ".W..K.K..W.",
    "....W.W....",
    "..W..K..W..",
    "...W...W...",
    "..W.....W..",
])]

EYES = {'sleepy': SLEEPY_EYE, 'awake': AWAKE_EYE, 'half': HALF_EYE,
        'wide': WIDE_EYE, 'shut': SHUT_EYE}
MOUTHS = {'slack': SLEEPY_MOUTH, 'roar': AWAKE_MOUTH, 'ow': MOUTH_OW,
          'snore': MOUTH_SNORE}
BUBBLES = {0: [], 1: BUBBLE_S, 2: BUBBLE_M, 3: BUBBLE_L, 4: BUBBLE_POP}


# --------------------------------------------------------------- CREASES
def paint_creases(g, sp):
    """Anatomy, all drawn as curves so every line follows the form.
    Offsets follow the spec so a nodding head or a crouch takes its shading
    with it."""
    dx, ady, hdy = sp['dx'], sp['all_dy'], sp['head_dy']

    def C(pts, ch, thick=1, over=SKIN, mirror=True, head=False):
        oy = ady + (hdy if head else 0)
        p = [(x + dx, y + oy) for (x, y) in pts]
        curve(g, p, ch, thick=thick, over=over,
              mirror_axis=(MIR + 2 * dx) if mirror else None)

    # trapezius sloping off the neck into the shoulders
    C([(60, 62), (70, 57), (80, 55)], 'S', 2, set('sdD'))
    C([(58, 66), (70, 61), (82, 59)], 'd', 1)
    # cast shadow of the head on the chest
    C([(58, 61), (70, 65), (87.5, 67)], 'd', 2)
    # deltoid cap and the crease that splits it from the pec
    if sp['arm'] in ('hang', 'swingf', 'swingb', 'limp') and not sp['arm_l']:
        C([(26, 72), (17, 81), (13, 91)], 'S', 3, set('sdD'))
    C([(44, 62), (38, 70), (36, 80)], 'd', 2)
    C([(46, 61), (40, 69), (38, 79)], 'D', 1)
    # pec domes: a lit crest and the deep crease beneath each
    C([(46, 68), (60, 69), (74, 73)], 'S', 3, set('sdD'))
    C([(38, 76), (50, 86), (65, 91), (80, 89)], 'd', 3)
    C([(39, 74), (52, 83), (66, 88), (80, 86)], 'D', 1)
    # sternum groove
    C([(87.5, 70), (87.5, 89)], 'd', 1, set('Ss'), mirror=False)
    # serratus / rib hints on the flanks
    for k, yy in enumerate((82, 88, 94)):
        C([(31 + k, yy), (39 + k, yy + 4)], 'd', 1)
    # the gut's own bulge
    C([(50, 92), (54, 100), (56, 108)], 'S', 4, set('sdD'), mirror=False)
    C([(60, 88), (64, 98), (66, 107)], 'S', 2, set('sdD'), mirror=False)
    # obliques dropping into the waistband
    C([(33, 96), (39, 104), (47, 110)], 'd', 2)

    # ---- hands.  Each side is detailed for the pose that side is holding,
    #      so a slapping palm never gets the guard hand's fingers on top.
    def hand_detail(name, mir):
        """mir: None = draw both sides mirrored, False = left only,
        True = right only."""
        def P(pts, ch, thick=1, over=SKIN, sx=1.0, sy=1.0, ox=44.5, oy=68.0,
              ddx=0.0, ddy=0.0):
            q = [(ox + (x - ox) * sx + ddx + dx,
                  oy + (y - oy) * sy + ddy + ady) for (x, y) in pts]
            if mir is None:
                curve(g, q, ch, thick=thick, over=over,
                      mirror_axis=MIR + 2 * dx)
            elif mir:
                curve(g, [(MIR - x + 2 * dx, y) for (x, y) in q], ch,
                      thick=thick, over=over)
            else:
                curve(g, q, ch, thick=thick, over=over)

        if name in ('guard', 'flail'):
            d = (-5.0, -9.0) if name == 'flail' else (0.0, 0.0)
            for fx, y0 in ((40, 55), (46, 53), (52, 54)):
                P([(fx, y0), (fx, y0 + 10)], 'K', 1, ddx=d[0], ddy=d[1])
                P([(fx - 1, y0), (fx - 1, y0 + 10)], 'S', 1, set('sdD'),
                  ddx=d[0], ddy=d[1])
            P([(36, 64), (45, 67), (55, 65)], 'd', 1, ddx=d[0], ddy=d[1])
            P([(36, 75), (45, 79), (54, 77)], 'd', 2, ddx=d[0], ddy=d[1])
        elif name == 'cock':
            for fx, y0 in ((40, 55), (46, 53), (52, 54)):
                P([(fx, y0), (fx, y0 + 10)], 'K', 1, sx=0.86, sy=0.86,
                  ddx=-3, ddy=-9)
            P([(36, 66), (45, 69), (55, 67)], 'd', 1, sx=0.86, sy=0.86,
              ddx=-3, ddy=-9)
        elif name in ('slap', 'slap_hi', 'slap_lo'):
            sdy = {'slap': 0, 'slap_hi': -7, 'slap_lo': 4}[name]
            for fx in (41, 52, 63):
                P([(fx, 76), (fx, 93)], 'K', 1, ddy=sdy)
                P([(fx - 1, 76), (fx - 1, 93)], 'S', 1, set('sdD'), ddy=sdy)
            P([(34, 97), (52, 102), (70, 98)], 'd', 2, ddy=sdy)
            P([(32, 88), (35, 101), (41, 112)], 'S', 2, set('sdD'), ddy=sdy)
            P([(78, 86), (79, 100), (73, 115)], 'd', 3, ddy=sdy)
            P([(81, 88), (82, 100), (76, 116)], 'D', 2, ddy=sdy)

    if sp['arm_l'] is None and sp['arm_r'] is None:
        hand_detail(sp['arm'], None)
    else:
        hand_detail(sp['arm_l'] or sp['arm'], False)
        hand_detail(sp['arm_r'] or sp['arm'], True)

    if sp['arm'] in ('guard', 'cock', 'flail') or sp['arm_l'] or sp['arm_r']:
        C([(13, 84), (20, 92), (30, 96)], 'd', 2)   # bicep under a raised arm
    else:
        C([(30, 72), (27, 88), (27, 104), (28, 118)], 'd', 2)
        C([(12, 100), (19, 104), (27, 102)], 'd', 1)
        C([(13, 110), (20, 113), (27, 111)], 'd', 1)
        C([(13, 117), (20, 119), (28, 117)], 'd', 1)
    # thighs
    if sp['leg'] != 'sit':
        C([(31, 118), (29, 128), (30, 136)], 'S', 4, set('sdD'))
        C([(65, 120), (69, 130), (68, 138)], 'd', 2)
        C([(38, 132), (50, 130), (62, 132)], 'S', 3, set('sdD'))
        C([(87.5, 130), (87.5, 143)], 'K', 1, SKIN, mirror=False)
    # head volume
    C([(59, 38), (57, 46), (60, 53)], 's', 2, set('S'), mirror=False, head=True)
    C([(116, 39), (118, 46), (114, 53)], 's', 2, set('S'), mirror=False,
      head=True)
    C([(74, 48), (70, 54), (71, 59)], 's', 1, head=True)
    C([(62, 55), (74, 61), (87.5, 63)], 'd', 2, head=True)


STAMPS_COMMON = TOES + NOSE + STUBBLE + BRIM_SH       # head/foot group
STAMPS_CHEST = COLLAR + CHAIN + NAVEL


def build(pose='idle', spec=None, verify=False):
    sp = dict(DEFAULT, **(spec if spec is not None else spec_for(pose)))

    # the same figure with no shorts at all: what every tear reveals
    U = build_rig(pose, sp)
    U.regions = [r for r in U.regions if r['name'] != 'shorts']
    under = U.build_letters()

    R = build_rig(pose, sp)
    g = R.build_letters()
    paint_beanie(g, R)
    paint_creases(g, sp)
    paint_gut_roll(g, R)
    rip_shorts(g, R, under)
    dither_terminators(g, {'S': 's', 's': 'd'}, phase=0)
    dither_terminators(g, {'C': 'N', 'n': 'm'}, phase=1)

    dx, ady, hdy = sp['dx'], sp['all_dy'], sp['head_dy']
    head_off = (dx, ady + hdy)
    foot_off = (dx, 0 if sp['leg'] == 'sit' else ady)

    def put(group, off):
        for (x0, y0, block) in group:
            stamp(g, x0 + off[0], y0 + off[1], block)

    put(NOSE + STUBBLE + BRIM_SH, head_off)
    put(EYES[sp['eye']], head_off)
    put(MOUTHS[sp['mouth']], head_off)
    put(BUBBLES[sp['bubble']], head_off)
    put(COLLAR, head_off)
    put(CHAIN + NAVEL, (dx, ady))
    put(TOES, foot_off)
    for name, mir in ((sp['arm_l'], False), (sp['arm_r'], True)):
        if name in ('slap', 'slap_hi', 'slap_lo'):
            dyy = {'slap': 0, 'slap_hi': -7, 'slap_lo': 4}[name]
            cx, cy = HAND_SLAP_CENTRE
            cy += dyy + ady
            cx += dx
            for k, yy in enumerate((-18, -6, 7)):
                x0 = cx - 40 - k * 4
                for x in range(x0, cx - 22):
                    for ry in (cy + yy, cy + yy + 1):
                        xx = (MIR - x) if mir else x
                        if 0 <= xx < W and 0 <= ry < H and g[ry][xx] == ' ':
                            g[ry][xx] = 'E'
    if sp['knuck'] and sp['arm'] in ('hang', 'swingf', 'swingb', 'limp') \
            and not sp['arm_l']:
        put(KNUCK, (dx, ady))
    if verify and dx == 0:
        check_symmetry(g, MIR, 'sumo_' + pose)
    return g


if __name__ == '__main__':
    import sys
    sys.path.insert(0, HERE)
    OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
    from pngio import write_png, upscale
    for pose in ('idle', 'awake', 'land'):
        g = build(pose, verify=(pose != 'idle'))
        pix = to_pix(g)
        write_png(os.path.join(OUT, 'sumo_%s_1x.png' % pose), W, H, pix)
        w2, h2, p2 = upscale(W, H, pix, 4, bg='checker')
        write_png(os.path.join(OUT, 'sumo_%s_4x.png' % pose), w2, h2, p2)
        print('wrote', pose)
