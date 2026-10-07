"""Liam's AVATAR-STATE float, two 96x96 frames in his OWN palette, built on his approved rig (the scratch copy
of art_source/liam_elements, proven pixel-identical to the live sheets). The puppet treatment comes after
(god_build.py). Body = the approved 64x64 figure at 1:1, raised so it floats: BODY_DY rows above where it
stands in his 96x96 cells, so the frame keeps his cell size and his centre column (48).

f0 FLOAT: arms spread out and down, palms open, legs hanging limp with the feet toe-down, a set mouth.
f1 SURGE: arms flung up in a V, palms open, the shout (its mouth will glow), legs the same.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'liam_rig'))
import numpy as np
import le_rig as R
import le_poses as P
import le_posedefs as D
import le_parts as X

FW = FH = 96
BODY_DY = -12            # the approved figure sits at (16, 32 + BODY_DY) = (16, 20)
BX, BY = P.BODY[0], P.BODY[1] + BODY_DY


def B(x, y):
    return (x + BX, y + BY)


# a set, grim mouth: the lips pressed in a line under the moustache (x 16..39, y 20..24 of the head)
SET = (16, 20, [
    "#hhHhhHHhkhHHhhkhHhhHhh#",
    "#hHhhHhkhHHhhkhHhhhHhhh#",
    "#hhHhh##########hhHhhH#.",
    ".#hhHh#hHhhHhhH#hHhhHh#.",
    ".#hHhhkhHhhHhhkhhhHhh#..",
])


# Below the seat (body rows 54..72): the two legs part and hang, the near one a texel lower, tapering to
# their hems, and the shoes hang toe-down under them (light from the upper left, as his rig lights him).
# Body-space (x0, row) per line; '#' keyline, p/q/Q/z his trouser ramp, o/O/x his shoe ramp.
HANG = {
    54: [(16, '#ppppqqqqqqQQQz#'), (31, '#qqpqqqqqqqQQQz#')],
    55: [(15, '#ppppqqqqqqQQzz#'), (32, '#qpqqqqqqqqQQQz#')],
    56: [(15, '#pppqqqqqqqQQQz#'), (32, '#qpqqqqqqqqQQQz#')],
    57: [(14, '#pppqqqqqqqQQQz#'), (33, '#qpqqqqqqqqQQQz#')],
    58: [(14, '#ppqqqqqqqQQQz#'), (33, '#qpqqqqqqqQQQz#')],
    59: [(14, '#ppqqqqqqqQQzz#'), (34, '#pqqqqqqqQQQz#')],
    60: [(14, '#pqqqqqqqQQQz#'), (34, '#pqqqqqqqQQQz#')],
    61: [(14, '#QQQQQQQQQzzz#'), (34, '#pqqqqqqqQQQz#')],
    62: [(14, '##############'), (34, '#QQQQQQQQQzzz#')],
    63: [(15, '#ooooOOOOOx#'), (34, '##############')],
    64: [(14, '#oooOOOOOOOx#'), (36, '#oooOOOOOOx#')],
    65: [(14, '#ooOOOOOOOxx#'), (35, '#ooOOOOOOOOx#')],
    66: [(13, '#ooOOOOOOOxx#'), (35, '#oOOOOOOOOxx#')],
    67: [(13, '#oOOOOOOOxxx#'), (36, '#oOOOOOOOxx#')],
    68: [(13, '#oOOOOOOxxx#'), (36, '#OOOOOOOxxx#')],
    69: [(13, '#OOOOOOxxx#'), (37, '#OOOOOOxxx#')],
    70: [(14, '#xxOOxxxx#'), (37, '#xOOOOxxx#')],
    71: [(15, '#xxxxxx#'), (38, '#xxxxxxx#')],
    72: [(16, '######'), (39, '#xxxxx#')],
    73: [(40, '#####')],
}


def legs_hanging():
    """His approved seat and trouser rows (legs_narrow 46..53) and the hanging legs and shoes (HANG)."""
    src = P.legs_narrow()
    full = R.blank(FW, FH)
    for y in range(46, 54):
        for x in range(64):
            if src[y, x] != '.':
                full[y + BY, x + BX] = src[y, x]
    for y, segs in HANG.items():
        for x0, row in segs:
            for i, ch in enumerate(row):
                if ch != '.':
                    full[y + BY, x0 + i + BX] = ch
    return full


def arms(kind):
    if kind == 'float':
        far = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 4, 39, 4.8, 4.0), fore=(4, 39, -2.5, 43.5, 3.6, 3.2), dy=BODY_DY)
        near = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 56, 39, 4.8, 4.0), fore=(56, 39, 62.5, 43.5, 3.6, 3.2), dy=BODY_DY)
        palms = [(B(-5.0, 47.0), 'far'), (B(65.0, 47.0), 'near')]
    else:
        far = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 5, 23, 4.6, 3.6), fore=(5, 23, 0.5, 15, 3.4, 3.1), dy=BODY_DY)
        near = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 23, 4.6, 3.8), fore=(56, 23, 60.5, 15, 3.6, 3.2), dy=BODY_DY)
        palms = [(B(-0.5, 10.5), 'far'), (B(61.5, 10.5), 'near')]
    return far, near, palms


def frame(kind):
    mouth = SET if kind == 'float' else 'shout'
    Hd = P.place(X.head(mouth, None), dy=BODY_DY)
    far, near, palms = arms(kind)
    cv = R.compose([D.tails(BODY_DY, 'up'), legs_hanging(), P.body('torso', dy=BODY_DY), far, near, Hd], FW, FH)
    for (cx, cy), side in palms:
        rows = X.OPEN_PALM if side == 'near' else [r[::-1] for r in X.OPEN_PALM]
        if side == 'far':   # mirrored palm: the light side swaps too (a <-> d/f stay as drawn: lit edge leads)
            rows = [r.replace('a', '\0').replace('d', 'a').replace('\0', 'd') for r in rows]
        X.hand(cv, rows, cx, cy)
    return cv


def frames():
    return [frame('float'), frame('surge')]


# texel points on the frames, for the treatment's hand-set hooks and the Avatar overlays
LENS_FAR = [B(x, y) for (x, y) in P.LENS_FAR]
LENS_NEAR = [B(x, y) for (x, y) in P.LENS_NEAR]

if __name__ == '__main__':
    sys.path.insert(0, HERE)
    import guard  # noqa
    from PIL import Image
    import le_build as LB
    im = LB.strip(frames())
    out = os.path.join(HERE, '..', 'look', 'liam_avatar_src.png')
    im.save(out)
    bg = Image.new('RGBA', im.size, (46, 49, 58, 255)); bg.alpha_composite(im)
    bg.resize((im.width * 6, im.height * 6), Image.NEAREST).save(os.path.join(HERE, '..', 'look', 'liam_avatar_src_6x.png'))
    print('ok', im.size)
