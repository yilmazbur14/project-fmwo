"""Small-form Danny keys for the transformation, 64x64.

This reuses Danny's ACTUAL training-room rig: the head / body / shorts / legs /
boots polygons and the face, beanie, chain, belly and shorts stamps are taken
straight from art_source/danny/danny.py, in its own coordinate space
(AX = 37, DX = 2).  Only the arms, the shirt and the expression change per key.
The finished grid is translated left by 7px so the figure is centred on
x = 31.5 in the 64-wide frame.

Keys: walk_a walk_b arrive grip tear shirt_off flex flex_hold
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DANNY = os.path.normpath(os.path.join(HERE, '..', 'danny'))
sys.path.insert(0, DANNY)
import danny as D                                     # noqa: E402  (his rig)
sys.path.remove(DANNY)

from rig import Rig, S, SM, stamp, to_pix, dump, curve, PAL   # noqa: E402

W = H = 64
AX = 37.0            # Danny's own mirror axis, in design coords
DX = -5              # Danny's DX(2) already shifted 7px left, so the
                     # figure is centred and both arms have room
MIR = 64             # x' = 64 - x
STAMP_DX = -7        # danny.py's stamps are in his old pixel frame
SKIN = set('SsdD')
SHIRT = set('RrDM')


def mxp(pts):
    return [(2 * AX - x, y) for (x, y) in reversed(pts)]


def mxc(caps):
    return [(2 * AX - c[2], c[3], 2 * AX - c[0], c[1], c[4]) for c in caps]


# ---------------------------------------------------------------- ARM POSES
# His left arm (screen right).  Sleeve polygon + forearm capsules + a fist.
SLEEVE_DOWN = [(47.5, 25.8), (51.8, 27.0), (54.8, 29.0), (56.4, 32.0),
               (56.8, 35.0), (56.2, 37.2), (50.6, 37.6), (49.2, 34.5),
               (48.2, 30.5)]
SLEEVE_UP = [(47.5, 25.2), (52.0, 26.2), (55.4, 28.0), (57.2, 30.6),
             (57.6, 33.4), (56.6, 35.4), (50.6, 35.8), (49.2, 33.0),
             (48.2, 29.5)]
SLEEVE_FLEX = [(47.5, 24.8), (52.6, 24.6), (56.6, 26.0), (58.8, 28.6),
               (58.6, 31.8), (56.2, 33.4), (50.6, 33.8), (49.0, 30.6),
               (48.0, 27.2)]

ARMPOSE = {
    # forearm capsule chain, sleeve polygon, fist centre
    'down':   ([(53.3, 36.5, 53.8, 42.6, 3.3)], SLEEVE_DOWN, (54.2, 46.2, 3.9)),
    'fwd':    ([(54.0, 35.4, 56.2, 41.0, 3.3)], SLEEVE_UP, (57.0, 44.0, 3.8)),
    'back':   ([(53.0, 36.8, 52.6, 43.0, 3.3)], SLEEVE_DOWN, (52.4, 46.6, 3.9)),
    # both hands up at the collar, about to pull
    'grip':   ([(53.8, 34.4, 47.6, 31.8, 3.2)], SLEEVE_UP, (44.4, 30.8, 3.7)),
    # flung out wide on the tear
    'out':    ([(55.4, 33.0, 61.0, 30.2, 3.2)], SLEEVE_UP, (64.4, 28.4, 3.7)),
    # double biceps: upper arm out to the side, forearm straight up
    'flex':   ([(56.6, 30.6, 57.8, 24.0, 3.3)], SLEEVE_FLEX, (58.2, 20.6, 4.0)),
    # hands on the way up to the collar
    'reach':  ([(53.6, 35.6, 50.0, 33.4, 3.2)], SLEEVE_UP, (47.0, 32.4, 3.7)),
    # arms flung wider still on the second tear frame
    'out_wide': ([(55.6, 32.0, 61.6, 28.6, 3.2)], SLEEVE_FLEX,
                 (65.0, 26.4, 3.7)),
    # elbows coming up before the flex lands
    'rise':   ([(56.0, 32.0, 56.4, 27.0, 3.3)], SLEEVE_UP, (56.6, 23.8, 3.8)),
}

# One name = both arms mirrored.  A pair = (screen-right, screen-left), for
# the walk, where one arm swings forward while the other goes back.
KEY_ARM = {
    'walk_a': ('fwd', 'back'), 'walk_pass': 'down',
    'walk_b': ('back', 'fwd'), 'walk_pass2': 'down',
    'arrive': 'down', 'reach': 'reach', 'grip': 'grip', 'strain': 'grip',
    'tear': 'out', 'tear_wide': 'out_wide', 'shirt_off': 'out',
    'flex_rise': 'rise', 'flex': 'flex', 'flex_hold': 'flex',
    'flex_in': 'flex', 'flex_out': 'flex',
}


def arm_names(key):
    a = KEY_ARM[key]
    return a if isinstance(a, tuple) else (a, a)


def build_rig(key):
    R = Rig(W, H, AX, DX=DX)
    rn, ln = arm_names(key)
    caps, sleeve, fist = ARMPOSE[rn]
    capsL, sleeveL, fistL = ARMPOSE[ln]
    fist_r = dict(caps=[(fist[0], fist[1], fist[0], fist[1], fist[2])])
    fist_l = dict(caps=[(2 * AX - fistL[0], fistL[1], 2 * AX - fistL[0],
                         fistL[1], fistL[2])])
    R.region('leg_l', D.LEG_L, 1, 'leg_l', 'skin')
    R.region('leg_r', D.LEG_R, 1, 'leg_r', 'skin')
    R.region('boot_l', D.BOOT_L, 2, 'boot_l', 'boot')
    R.region('boot_r', D.BOOT_R, 2, 'boot_r', 'boot')
    R.region('shorts', D.SHORTS, 3, 'shorts', 'shorts')
    R.region('belly', D.BODY, 3.5, 'belly', 'belly',
             clip=lambda xd, y: y + 0.5 >= D.hem_y(xd))
    R.region('body', D.BODY, 4, 'body', 'shirt',
             clip=lambda xd, y: y + 0.5 < D.hem_y(xd))
    R.region('arm_r', dict(caps=caps), 5, 'arm_r', 'skin')
    R.region('arm_l', dict(caps=mxc(capsL)), 5, 'arm_l', 'skin')
    R.region('fist_r', fist_r, 5.5, 'fist_r', 'skin')
    R.region('fist_l', fist_l, 5.5, 'fist_l', 'skin')
    R.region('sleeve_r', sleeve, 6, 'sleeve_r', 'shirt')
    R.region('sleeve_l', mxp(sleeveL), 6, 'sleeve_l', 'shirt')
    R.region('head', D.HEAD, 9, 'head', 'skin')
    return R


def paint_beanie(g, R):
    mask = next(r for r in R.regions if r['name'] == 'head')['mask']
    for y in range(H):
        for x in range(W):
            if mask[y][x] and g[y][x] != 'K' and D.beanie_is(x + 7, y):
                g[y][x] = 'n' if (abs(x - 32) % 3 == 1) else 'C'


def head_skin(x, y):
    return ('bw' if not D.stripe_is_grey(x, y) else 'bg') if D.beanie_is(x, y) \
        else 'face'


# ------------------------------------------------------------------- SHIRT
def rip_shirt(g, amount):
    """Tear the shirt open down the middle.  amount 0..1, about the pixel
    centreline x = 39 (Danny's own axis before the shift)."""
    if amount <= 0:
        return
    cx = 32.0
    for y in range(27, 44):
        t = (y - 26) / 17.0
        half = amount * (1.5 + 12.0 * t)
        if half < 1.2:
            continue
        x0, x1 = int(round(cx - half)), int(round(cx + half))
        for x in range(max(0, x0), min(W, x1 + 1)):
            if g[y][x] in SHIRT:
                d = abs(x - cx) / max(half, 1e-6)
                g[y][x] = 'S' if d < 0.40 else 's' if d < 0.76 else 'd'
        jag = 1 if (y % 3 == 0) else 0
        for x in (x0 - 1 - jag, x1 + 1 + jag):
            if 0 <= x < W and g[y][x] in SHIRT:
                g[y][x] = 'K'
        if jag:
            for x in (x0 - 1, x1 + 1):
                if 0 <= x < W and g[y][x] in SHIRT:
                    g[y][x] = 'd'
    # bare chest: collarbones, sternum groove, pec undersides
    curve(g, [(26, 30), (29, 31), (32, 31.5)], 'd', thick=1, over=SKIN,
          mirror_axis=MIR)
    if amount > 0.7:
        curve(g, [(32, 31), (32, 40)], 's', thick=1, over=set('S'))
        curve(g, [(26, 35), (29, 37), (32, 37.5)], 'd', thick=1, over=SKIN,
              mirror_axis=MIR)
        curve(g, [(25, 33), (28, 34)], 'S', thick=1, over=set('sd'),
              mirror_axis=MIR)


# torn cloth flying off on the tear frame
SHREDS = [S(10, 20, [
    ".r....................r.",
    "r.r..................r.r",
    ".r....................r.",
]), S(6, 33, [
    "r..............................r",
    "....r......................r....",
])]


# ------------------------------------------------------------------- FACES
# Danny's face box is x 27..50; eyes are rows 18-19, mouth rows 23-25.
EYES_SHUT = S(23, 18, [
    "KKKKKKssssKKKKKK",
    "sKKKKsssssKKKKs.",
])
EYES_WIDE = S(23, 17, [
    "KKKK......KKKK..",
    "KEEK......KEEK..",
    "KKKK......KKKK..",
])
MOUTH_EFFORT = S(27, 23, [
    ".KKKKK.",
    "KMMMMMK",
    "KEEEEEK",
    ".KKKKK.",
])
MOUTH_GRIN = S(27, 23, [
    ".KKKKK.",
    "KEEEEEK",
    "KMMMMMK",
    ".KKKKK.",
])
BROWS_UP = S(23, 15, [
    "..KKKK......KKKK",
    ".K....K..K....K.",
])
SPARKLE = [S(45, 20, [
    "..E..",
    ".EEE.",
    "EEEEE",
    ".EEE.",
    "..E..",
]), S(16, 13, [
    ".E.",
    "EEE",
    ".E.",
])]

FACES = {
    'reach': [],
    'grip': [MOUTH_EFFORT],
    'strain': [EYES_SHUT, MOUTH_EFFORT],
    'tear': [EYES_SHUT, MOUTH_EFFORT],
    'tear_wide': [EYES_SHUT, MOUTH_EFFORT],
    'shirt_off': [MOUTH_GRIN, BROWS_UP],
    'flex_rise': [MOUTH_GRIN, BROWS_UP],
    'flex': [MOUTH_GRIN, BROWS_UP],
    'flex_hold': [MOUTH_GRIN, BROWS_UP] + SPARKLE,
    'flex_in': [MOUTH_GRIN, BROWS_UP] + SPARKLE,
    'flex_out': [MOUTH_GRIN, BROWS_UP],
}

RIP = {'tear': 0.55, 'tear_wide': 0.85, 'shirt_off': 1.0, 'flex_rise': 1.0,
       'flex': 1.0, 'flex_hold': 1.0, 'flex_in': 1.0, 'flex_out': 1.0}
# (which boot lifts, by how many px) -- the pass frames get a half lift
STRIDE = {'walk_a': (1, 3), 'walk_pass': (-1, 1),
          'walk_b': (-1, 3), 'walk_pass2': (1, 1)}
BOB = {'walk_a': -1, 'walk_b': -1, 'strain': 1, 'flex_hold': -1,
       'flex_in': -1, 'tear_wide': -1}

BASE_STAMPS = [D.FOLD, D.FACE, D.CHAIN, D.SHIRT_VOL, D.BELLY, D.SHORTS_ST]


def stride(g, lift, amount=3):
    """Lift one boot by `amount` px, by translating its leg columns."""
    if lift == 0 or amount == 0:
        return
    cols = range(17, 32) if lift > 0 else range(32, 47)
    snap = [row[:] for row in g]
    for y in range(46, H):
        for x in cols:
            g[y][x] = ' '
    for y in range(46, H - amount):
        for x in cols:
            g[y][x] = snap[y + amount][x]


def shift(g, dx, dy=0):
    out = [[' '] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H:
                out[ny][nx] = g[y][x]
    return out


def build(key):
    R = build_rig(key)
    R.head_skin = head_skin
    g = R.build_letters()
    paint_beanie(g, R)
    for (x0, y0, block) in BASE_STAMPS:
        stamp(g, x0 + STAMP_DX, y0, block)
    rip_shirt(g, RIP.get(key, 0.0))
    if key in ('tear', 'tear_wide'):
        for (x0, y0, block) in SHREDS:
            stamp(g, x0 + (3 if key == 'tear_wide' else 0),
                  y0 - (3 if key == 'tear_wide' else 0), block)
    for (x0, y0, block) in FACES.get(key, []):
        stamp(g, x0, y0, block)
    fx, fy, fr = ARMPOSE[arm_names(key)[0]][2]
    fx += DX
    for dyk in (-1, 1):
        curve(g, [(fx - fr + 1.5, fy + dyk), (fx + fr - 1.5, fy + dyk)], 'd',
              thick=1, over=SKIN, mirror_axis=MIR)
    st = STRIDE.get(key)
    if st:
        stride(g, st[0], st[1])
    dy = BOB.get(key, 0)
    return shift(g, 0, dy) if dy else g


KEYS = ['walk_a', 'walk_pass', 'walk_b', 'walk_pass2', 'arrive',
        'reach', 'grip', 'strain', 'tear', 'tear_wide', 'shirt_off',
        'flex_rise', 'flex', 'flex_in', 'flex_out']


if __name__ == '__main__':
    import sys
    OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
    from pngio import write_png, upscale
    frames = []
    for k in KEYS:
        g = build(k)
        pix = to_pix(g)
        frames.append(pix)
        write_png(os.path.join(OUT, 'small_%s_1x.png' % k), W, H, pix)
    sheet = [[(0, 0, 0, 0)] * (W * len(frames)) for _ in range(H)]
    for i, p in enumerate(frames):
        for y in range(H):
            for x in range(W):
                sheet[y][i * W + x] = p[y][x]
    w2, h2, p2 = upscale(W * len(frames), H, sheet, 6, bg='checker')
    write_png(os.path.join(OUT, 'small_keys_6x.png'), w2, h2, p2)
    print('wrote', len(frames), 'small keys')
