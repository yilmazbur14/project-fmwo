"""The player's back-view uppercut for Greyson's brawl, at 2x (PLAN_BRAWL.md sections 6-7): the approval
pass for player_final_brawl_uppercut.png and its _super recolour.

    10 frames of 64x128 in one row (640x128), Sprite2D offset (0,-16): the origin is the frame's
    (32, 80), the ground line (soles' bottom edge) is y 93, the centre line is x 32.

The frame roles are player_uppercut.png's, so the finisher's timings and planned apex hold:
    f0 ready, f1-f2 charge, f3 launch, f4-f6 rise, f7 apex, f8 fall, f9 land.
The glove heights are the plan's: f5 is CONTACT, the glove's top 50 texels above the ground on the
centre line (Greyson's dazed chin); the apex glove 70 up with the feet 8 off the mat.

It is Little Mac's uppercut from behind: a crouch with the right fist cocked at the hip while the energy
gathers on it, then the legs drive up and the fist comes up close past the right side of the head and
turns in over it; he is still on his toes at contact and leaves the mat after it, stretched out at the
apex, flailing on the way down, and lands back in his crouched guard. The body is gb_native2x's own
(head, back, shorts, boots), centred on x 32 so a flip is harmless; a crouch removes rows (legs first,
then shorts, then back) with the feet planted.

The energy is baked in, opaque, in exactly player_uppercut.png's six effect colours, so the _super
sheet is the same recolour player_uppercut_super.png uses:
    e (91,110,225) deep blue   -> (215,123,186)      b (99,155,255) blue    -> (223,113,38)
    c (95,205,228) cyan        -> (251,242,54)       p (203,219,252) pale   -> (251,242,54)
    w (255,255,255) white and g (155,173,183) dust grey stay.

Nothing in this module writes anything.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gb_player as G  # noqa: E402
import gb_native2x as N  # noqa: E402

W, H = 64, 128
ORIGIN = (32, 80)
GROUND = 93
FX = {'e': (91, 110, 225, 255), 'c': (95, 205, 228, 255), 'b': (99, 155, 255, 255),
      'g': (155, 173, 183, 255), 'p': (203, 219, 252, 255), 'w': (255, 255, 255, 255)}
SUPER = {'e': (215, 123, 186, 255), 'b': (223, 113, 38, 255), 'c': (251, 242, 54, 255),
         'p': (251, 242, 54, 255), 'g': (155, 173, 183, 255), 'w': (255, 255, 255, 255)}
PAL = dict(G.PAL, **FX)
PAL_SUPER = dict(G.PAL, **SUPER)

# the bare upper back (shoulders without arms), brawl registration, gb_native2x's window
UPPER_BARE = {
    25: '.......SSS..SSssSS..SSS',
    26: '......SSSSS.SSssSS.SSSSS',
    27: '......SsSSSSSSSsSSSSSSsS',
    28: '......SSsSSSSSSsSSSSSsSS',
}
# the rows a crouch takes out, in order (brawl rows; the feet stay, everything above them drops)
CROUCH = [53, 54, 46, 45, 34, 33, 44, 32]


def compress(px, removed):
    return {(x, y + sum(1 for r in removed if r > y)): k for (x, y), k in px.items() if y not in removed}


def shoulder_row(h, c):
    """Where the bare upper back's first row lands, for a body h off the mat crouched c rows."""
    return 25 + 32 - h + c


def body(h, c, arms, legs=None):
    """The native body, feet h texels off the mat, crouched c rows, centred on x 32; arms drawn after
    the torso and before the head (from behind the head is nearest the camera)."""
    parts = {}
    parts.update(N.lower_back())
    parts.update(N.win_px(UPPER_BARE))
    parts.update(N.shorts())
    parts.update(legs if legs is not None else N.legs())
    removed = set(CROUCH[:c])
    out = N.moved(compress(parts, removed), 1, 32 - h)
    for x, y, text in arms:
        for i, ch in enumerate(text):
            if ch != '.':
                out[(x + i, y)] = ch
    out.update(N.moved(N.head(), 1, 32 - h + len(removed)))       # every crouch row is below the head
    return out


# ---- arms (uppercut texels; the right arm is screen right, lit on its outer side)
def glove_up(x, y):
    return [(x + 1, y, 'BL'), (x, y + 1, 'BBLL'), (x, y + 2, 'BBBL'), (x, y + 3, 'BBBB'), (x, y + 4, 'DBBD')]


def glove_low(x, y):
    return [(x + 1, y, 'LB'), (x, y + 1, 'LBBB'), (x, y + 2, 'BBBB'), (x, y + 3, 'BBBD'), (x + 1, y + 4, 'DD')]


def right_arm_up(h, c, top):
    """Up past the right of the head (x 37-40) and turned in over it: the glove on the centre line
    (x 30-33), its top on row `top`."""
    t = shoulder_row(h, c)
    items = glove_up(30, top) + [(31, top + 5, 'DD'), (33, top + 5, 'Ss'), (34, top + 6, 'sSS'),
                                 (35, top + 7, 'sSSS'), (36, top + 8, 'sSSS')]
    return items + [(37, y, 'sSSS') for y in range(top + 9, t + 1)]


def right_arm_rising(h, c, top):
    """The fist driving up close beside the head (x 37-40), elbow still bent under it."""
    t = shoulder_row(h, c)
    items = [(38, top, 'BL'), (37, top + 1, 'BBLL'), (37, top + 2, 'BBBL'), (37, top + 3, 'BBBB'),
             (37, top + 4, 'DBBD'), (37, top + 5, 'sDDS')]
    return items + [(37, y, 'sSSS') for y in range(top + 6, t + 1)]


def right_arm_cocked(h, c, drop=0):
    """The fist drawn back low beside the hip, elbow bent back: the wind-up."""
    t = shoulder_row(h, c)
    items = [(37, t + 1, 'sSSS'), (38, t + 2, 'sSSS'), (38, t + 3, 'sSSS'), (39, t + 4, 'sSS'),
             (39, t + 5, 'sSS'), (39, t + 6, 'sSS')]
    g = t + 7 + drop
    return items + [(38, g, 'BL'), (37, g + 1, 'BBLL'), (37, g + 2, 'BBBL'), (37, g + 3, 'BBBB'), (38, g + 4, 'DD')]


def left_arm_down(h, c):
    """Hanging from its shoulder, the glove at the hip: the counter pull."""
    t = shoulder_row(h, c)
    items = [(22, t + 1, 'SSs'), (21, t + 2, 'SSs'), (21, t + 3, 'SSs'), (20, t + 4, 'SSs'),
             (20, t + 5, 'SSs'), (20, t + 6, 'SSs')]
    return items + glove_low(19, t + 7)


def left_arm_out(h, c):
    """Flung out and up for balance (the fall)."""
    t = shoulder_row(h, c)
    items = [(21, t + 1, 'SSSs'), (19, t, 'SSSs'), (17, t - 1, 'SSs'), (16, t - 2, 'SSs'), (15, t - 3, 'SSs')]
    return items + [(15, t - 8, 'LB'), (14, t - 7, 'LLBB'), (14, t - 6, 'LBBB'), (14, t - 5, 'BBBB'), (14, t - 4, 'BBBD')]


def _guard_arm(select, h, c):
    return [(x + 1, y + 32 - h + c, k) for (x, y), k in N.guard_px().items() if select(x, y)]


def left_arm_guard(h, c):
    """The native guard's own left glove, forearm and tucked elbow."""
    return _guard_arm(lambda x, y: (15 <= y <= 24 and x <= 21) or (25 <= y <= 28 and x <= 22), h, c)


def right_arm_guard(h, c):
    """The native guard's own right glove, forearm and elbow."""
    return _guard_arm(lambda x, y: (15 <= y <= 24 and x >= 37) or (25 <= y <= 26 and x >= 38)
                      or (27 <= y <= 28 and x >= 40), h, c)


# ---- the bodies: (role, feet off the mat, crouch rows, the punching right arm, the left arm)
POSES = [
    ('ready', 0, 4, lambda: right_arm_cocked(0, 4), lambda: left_arm_guard(0, 4)),
    ('charge', 0, 6, lambda: right_arm_cocked(0, 6, 1), lambda: left_arm_guard(0, 6)),
    ('charge', 0, 6, lambda: right_arm_cocked(0, 6, 1), lambda: left_arm_guard(0, 6)),
    ('launch', 0, 5, lambda: right_arm_rising(0, 5, 55), lambda: left_arm_down(0, 5)),
    ('rise', 0, 4, lambda: right_arm_rising(0, 4, 49), lambda: left_arm_down(0, 4)),
    ('contact', 0, 4, lambda: right_arm_up(0, 4, 43), lambda: left_arm_down(0, 4)),
    ('rise', 4, 1, lambda: right_arm_up(4, 1, 33), lambda: left_arm_down(4, 1)),
    ('apex', 8, 0, lambda: right_arm_up(8, 0, 23), lambda: left_arm_down(8, 0)),
    ('fall', 4, 3, lambda: right_arm_rising(4, 3, 46), lambda: left_arm_out(4, 3)),
    ('land', 0, 6, lambda: right_arm_guard(0, 6), lambda: left_arm_guard(0, 6)),
]


def glove_box(i):
    """The punching glove of frame i: (x0, y0, x1, y1) of the right arm's glove texels, and its top
    centre (the striking point) in frame texels (continuous x)."""
    items = POSES[i][3]()
    pts = set()
    for x, y, text in items:
        for j, ch in enumerate(text):
            if ch in 'BLD':
                pts.add((x + j, y))
    x0, x1 = min(x for x, y in pts), max(x for x, y in pts)
    y0, y1 = min(y for x, y in pts), max(y for x, y in pts)
    return (x0, y0, x1, y1), ((x0 + x1 + 1) / 2.0, y0)


# ---- the energy
def stamp(px, x, y, rows, front):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != '.' and (front or (x + i, y + j) not in px):
                px[(x + i, y + j)] = ch
    return px


def dots(px, pts, key, front=False):
    for q in pts:
        if front or q not in px:
            px[q] = key
    return px


def ribbon(px, x0, y0, y1, drift=3, amp=1.6, period=12.0, phase=0.6):
    """A 3-wide energy ribbon from (x0, y0) down to row y1, drifting right and twisting: deep blue on
    the inside, a bright core, cyan outside, pale where it swings out. Behind the body."""
    n = max(1, y1 - y0)
    for j in range(n + 1):
        y = y0 + j
        t = j / n
        x = int(round(x0 + drift * t + amp * math.sin(2 * math.pi * j / period + phase)))
        swing = math.cos(2 * math.pi * j / period + phase)
        keys = ['e', 'b', 'c'] if swing >= 0 else ['c', 'b', 'e']
        for i in range(3 if 0.08 < t < 0.9 else 2):
            if (x - 1 + i, y) not in px:
                px[(x - 1 + i, y)] = keys[i]
        if abs(swing) > 0.85:
            q = (x + 2, y) if swing > 0 else (x - 2, y)
            if q not in px:
                px[q] = 'p'
    return px


SPARKLE = ['...p...', '...w...', '..cwc..', 'pwwwwwp', '..cwc..', '...w...', '...p...']
SPARKLE_S = ['..p..', '..w..', 'pwwwp', '..w..', '..p..']
BURST = [
    '........p........',
    '........w........',
    '...c....w....c...',
    '....c...w...c....',
    '.....c.pwp.c.....',
    '......cwwwc......',
    '.......www.......',
    'pwwwwpwwwwwpwwwwp',
    '.......www.......',
    '......cwwwc......',
    '.....c.pwp.c.....',
    '....c...w...c....',
    '...c....w....c...',
    '........w........',
    '........p........',
]
CHARGE_BURST = ['....p....', '.c..w..c.', '..cpwpc..', '.pwwwwwp.', 'pwwwwwwwp', '.pwwwwwp.', '..cpwpc..',
                '.c..w..c.', '....p....']
DUST_L = ['..pp.', '.pggp', 'ggggg', '.ggg.']
DUST_R = ['.pp..', 'pggp.', 'ggggg', '.ggg.']


def energy(i, px):
    px = dict(px)
    if i == 0:          # sparks gathering on the cocked fist
        dots(px, [(43, 66), (45, 70), (42, 74), (35, 76)], 'b')
        dots(px, [(44, 68), (36, 66)], 'c')
    elif i == 1:        # more, streaking in
        dots(px, [(44, 68), (45, 69), (46, 74), (47, 74), (43, 78), (35, 79), (34, 69)], 'b')
        dots(px, [(43, 70), (44, 76), (36, 68), (42, 67)], 'c')
        dots(px, [(45, 72), (46, 72)], 'p')
    elif i == 2:        # the burst on the fist
        stamp(px, 34, 68, CHARGE_BURST, True)
        dots(px, [(45, 67), (46, 66), (47, 78), (31, 78), (30, 70), (46, 73)], 'b')
        dots(px, [(44, 66), (32, 76), (47, 71)], 'c')
    elif i == 3:        # the swoosh up from the hip, a flash on the fist, dust off both feet
        for j, y in enumerate(range(59, 76)):
            x = int(round(41 + 3.2 * math.sin(math.pi * j / 16.0)))
            for k, key in enumerate('wpc'):
                if (x + k, y) not in px:
                    px[(x + k, y)] = key
        stamp(px, 36, 52, SPARKLE_S, True)
        stamp(px, 15, 89, DUST_L, False)
        stamp(px, 43, 89, DUST_R, False)
        dots(px, [(13, 90), (48, 90), (14, 87)], 'g')
    elif i in (4, 5, 6):  # the trail under the rising fist, a flash on it (the big one at contact)
        top = {4: 49, 5: 43, 6: 33}[i]
        start = {4: (43, 55), 5: (43, 50), 6: (43, 41)}[i]
        ribbon(px, start[0], start[1], {4: 82, 5: 84, 6: 86}[i])
        if i == 4:
            stamp(px, 35, top - 5, SPARKLE_S, True)
        else:
            stamp(px, 29, top - 5, SPARKLE if i == 5 else SPARKLE_S, True)
    elif i == 7:        # the starburst on the fist, sparks falling away down his side
        stamp(px, 23, 17, BURST, True)
        dots(px, [(22, 18), (41, 16), (20, 28), (43, 27)], 'p')
        dots(px, [(42, 40), (43, 46), (42, 52), (44, 58), (43, 64), (45, 70), (44, 76)], 'b')
        dots(px, [(43, 43), (44, 55), (46, 67)], 'e')
        dots(px, [(41, 49), (45, 61)], 'c')
    elif i == 8:        # sparks scattering
        dots(px, [(43, 42), (46, 50), (12, 44), (10, 52), (44, 60), (26, 38)], 'b')
        dots(px, [(45, 45), (40, 38), (13, 40), (47, 56)], 'c')
        dots(px, [(38, 36), (9, 47)], 'p')
    elif i == 9:        # dust at both feet
        stamp(px, 14, 89, DUST_L, False)
        stamp(px, 44, 89, DUST_R, False)
        dots(px, [(11, 91), (50, 91), (12, 88), (49, 88)], 'g')
        dots(px, [(10, 90), (51, 90)], 'p')
    return px


def bodies():
    return [(name, body(h, c, right() + left())) for name, h, c, right, left in POSES]


def frames():
    """[(role, pixels with the energy)] for f0..f9."""
    return [(name, energy(i, px)) for i, (name, px) in enumerate(bodies())]


def px_from_origin(x, y):
    return ((x - ORIGIN[0]) * 3, (y - ORIGIN[1]) * 3)


def image(px, pal=PAL):
    from PIL import Image
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < W and 0 <= y < H:
            im.putpixel((x, y), pal[k])
    return im
