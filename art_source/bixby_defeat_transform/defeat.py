"""bixby_beast_defeat.png: 10 frames of 192x160 on the beast's anchor (96, 151), timed by
BixbyBeastArtLayout.ANIMS.defeat. Frames 0-2 are the beast, redrawn in the approved Hades design; 3-9
(the smoke poof, normal Bixby dizzy, the cough, Liam shooting out, tumbling, LANDING ON FRAME 8, the
hold) have no beast in them and are carried over from the shipped sheet unchanged.

  0  the final blow     the uppercut rocks all three heads back, eyes screwed shut, wings flared
  1  collapse           slumped on the floor, wings fallen open, spiral eyes, stars
  2  the glow dies      the ear tips and the wings' torn edges go out and smoke; the eyes dim
  3  smoke              (kept) the poof that hides the change back
"""
import common as C
import fx
import pose as PS
import poses

FW, FH = C.BEAST_FW, C.BEAST_FH
SOURCE = C.os.path.join(C.HERE, 'src', 'bixby_beast_defeat_before.png')   # the shipped sheet, snapshotted
KEEP = [3, 4, 5, 6, 7, 8, 9]


# BixbyBeastArtLayout.BODY_DRAWN: everything drawn on a beast frame stays inside it (inclusive)
DRAWN = (2, 2, 189, 157)
CLIPPED = {}


def compose(back, beast_im, front, name=''):
    im = C.to_image(back, FW, FH)
    if beast_im is not None:
        im.alpha_composite(beast_im)
    im.alpha_composite(C.to_image(front, FW, FH))
    px = im.load()
    x0, y0, x1, y1 = DRAWN
    cut = 0
    for y in range(FH):
        for x in range(FW):
            if px[x, y][3] and not (x0 <= x <= x1 and y0 <= y <= y1):
                px[x, y] = C.CLEAR
                cut += 1
    CLIPPED[name] = cut
    return im


def frame0():
    back, front = {}, {}
    # shock lines thrown off the top of him, over the flared wings (none across the floor)
    fx.impact_lines(front, 96, 70, 26, 62, 76, seed=5, skip=[(0, 205), (335, 360)])
    # the blow lands under the middle head's chin: a white-hot burst, chips and sparks flying
    bx, by = 96, 100
    for (dx, dy, k) in ((0, 0, 'W'), (1, 0, 'Y'), (-1, 0, 'Y'), (0, 1, 'Y'), (0, -1, 'Y')):
        fx.put(front, bx + dx, by + dy, k)
    for a in range(8):
        ang = a * math.pi / 4 + math.pi / 8
        L = 7 if a % 2 == 0 else 4
        fx.streak(front, (bx + 2 * math.cos(ang), by + 2 * math.sin(ang)),
                  (bx + L * math.cos(ang), by + L * math.sin(ang)), ['Y', 'P', 'v'])
    for (x, y) in ((58, 30), (134, 26), (40, 70), (152, 66), (76, 12), (116, 10)):
        fx.hit_chip(front, x, y)
    fx.embers(front, (20, 10, 172, 120), 16, seed=11, hot_ratio=0.6, sizes=(1, 1, 2))
    return compose(back, PS.build(poses.blow()).image(), front, 'f0')


# the stars circle the middle head: (x, y, big) per frame
STARS = {
    1: [(72, 36, True), (97, 30, False), (122, 37, True)],
    2: [(80, 33, False), (106, 30, True), (128, 38, False)],
}


def frame1():
    back, front = {}, {}
    for (x, y, big) in STARS[1]:
        fx.star(front, x, y, big)
    for i, (x, y, r) in enumerate(((16, 149, 5), (52, 151, 4), (140, 151, 4), (176, 149, 5))):
        fx.dust(front, x, y, r, seed=21 + i)
    fx.embers(front, (24, 60, 168, 140), 10, seed=13, hot_ratio=0.5)
    return compose(back, PS.build(poses.collapse(1)).image(), front, 'f1')


def frame2():
    back, front = {}, {}
    P = poses.collapse(0)
    P['mid']['eye_glow'] = 0.5
    P['side']['eye_glow'] = 0.5
    for (x, y, big) in STARS[2]:
        fx.star(front, x, y, big)
    # the doused ear tips and wing edges smoke
    for i, (x, y, h) in enumerate(((64, 126, 12), (129, 126, 12), (30, 118, 9), (43, 120, 8), (148, 118, 8),
                                   (161, 120, 9), (8, 100, 8), (184, 100, 8))):
        fx.wisp(front, x, y, h, seed=31 + i, lean=1 if i % 2 else -1)
    fx.embers(front, (30, 50, 160, 120), 6, seed=17, hot_ratio=0.2, sizes=(1,))
    return compose(back, PS.build(P).image(), front, 'f2')


def frame3():
    back, front = {}, {}
    fx.puff_cloud(front, fx.big_cloud(96, 108, 184, 96, seed=7))
    fx.embers(front, (10, 24, 182, 150), 14, seed=19, hot_ratio=0.5, sizes=(1, 1, 2))
    for (x, y) in ((40, 40), (68, 24), (120, 20), (150, 32), (96, 10)):
        fx.twinkle(front, x, y)
    return compose(back, None, front)


import math  # noqa: E402  (used by frame0)


def frames():
    old = C.cells(C.load(SOURCE), FW, FH)
    new = [frame0(), frame1(), frame2()]
    return new + [old[i] for i in KEEP]
