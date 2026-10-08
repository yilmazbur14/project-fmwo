"""Shared parts for Liam's full pose sheets: extra mouths, hands, a far-foot lift, a squat, the dazed
legs, and RotSprite-style rotation (Scale2x x3, rotate, sample) for the tumbling frames.

Everything reuses his approved rig (liam_v2 layers via le_poses) so identity stays pixel-exact.
"""
import math

import numpy as np

import le_rig as R
import le_poses as P

FW = FH = P.FW


# ------------------------------------------------------------------ mouths (edits on his approved head)
def _mouth_from(rows_by_y):
    """A mouth as {y: (x0, 'chars')} edits, applied to a head copy."""
    def f(H):
        for y, (x0, s) in rows_by_y.items():
            for i, ch in enumerate(s):
                if ch not in '. ':
                    H[y, x0 + i] = ch
        return H
    return f


# relaxed talking: upper teeth, a dark mouth with the tongue, a sliver of lower teeth
TALK = _mouth_from({
    21: (16, "#hHh#WWWWWWWWWWWW#hhHhh#"),
    22: (16, "#hhHh#NNNNNNNNNN#hHhhH#"),
    23: (17, "#hhHh#NnnnnnnN#hHhhHh#"),
    24: (17, "#hHhhk#WWwWWW#khhHhh#"),
    25: (17, "#hhHrHh######HhkhHh#"),
})
# the smirk, opened a crack on the near side (smug talking)
SMIRK_TALK = _mouth_from({
    20: (16, "#hhHhhHHhkhHHhhk##hHhhh#"),
    21: (16, "#hHhhHhkhH#WWWWWW#hhHhh#"),
    22: (16, "#hhHhhkhHh#NNNNnN#hHhhH#"),
    23: (17, "#hhHhHhhkh#WWww#hHhhHh#"),
    24: (17, "#hHhhkhHhhH####hhHhh#"),
})
# cheeks puffed, lips pressed shut (the inhale)
PUFF = _mouth_from({
    19: (15, "..#hHhs#sdfdssdhHhhHhhhh#"),
    20: (15, ".#hhHhhHHhkhHHhhHhhHhhh#."),
    21: (15, "#hHhhHhhHhhhhhhhhHhhHhhhh#"[:25]),
    22: (15, "#hhHhhHhhh#####hHhhHhhh#."),
    23: (15, "#hHhhHhhhhhhhhhhhHhhHhh#."),
    24: (15, ".#hhHhhHhhhHhhhHhhHhhh#.."),
})
# a squeezed grimace (effort, a hit)
WINCE = _mouth_from({
    20: (16, "#hhHhhHHhkhHHhhk##hHhhh#"),
    21: (16, "#hHh#WWWWWWWWWWWW#hhHhh#"),
    22: (16, "#hhH#WwWwWwWwWwWw#hHhhH#"),
    23: (17, "#hhHh#WWWWWWWWWW#hHhhHh#"),
    24: (17, "#hHhhk##########khhHhh#"),
})


def head(mouth=None, lens=None):
    """The approved head with a mouth (a P.MOUTHS key, 'smirk', 'big', or a function here) and lenses."""
    if callable(mouth):
        Hd = P.head_variant(lens=lens)
        return mouth(Hd)
    return P.head_variant(mouth=mouth, lens=lens)


# ------------------------------------------------------------------ hands
FIST_UP = [  # liam_v2 frames.FIST_UP: a fist with the index finger up (13 x 14)
    ".........##..",
    "........#as#.",
    "........#ad#.",
    "........#sd#.",
    "........#sd#.",
    ".......#fsd#.",
    "....####ssf#.",
    "...#aasssdf#.",
    "..#asssdddf#.",
    "..#sfsfsff#..",
    "..#ssdsddf#..",
    "..#dddfff#...",
    "...#ffff#....",
    "....####.....",
]
FOUR = [  # four fingers up, palm to us, thumb folded (9 x 11)
    ".#.#.#.#.",
    "#a#s#s#d#",
    "#a#s#s#d#",
    "#a#s#s#d#",
    "#a#s#s#d#",
    "#asssssd#",
    "#assfssd#",
    "#sssssdf#",
    ".#ssddf#.",
    ".#dffff#.",
    "..#####..",
]
OPEN_PALM = [
    "..#.#.#..",
    ".#a#s#s#.",
    ".#a#s#s##",
    "#as#s#sd#",
    "#asssssd#",
    "#asssssd#",
    "#sssssdf#",
    ".#sssdf#.",
    ".#ddfff#.",
    "..#####..",
]
BACKHAND = [
    "...#####.",
    "..#aasss#",
    ".#assssd#",
    "#assssdd#",
    "#asssdf#.",
    "#sssdff#.",
    ".#dff##..",
    "..###....",
]


def hand(L, rows, cx, cy):
    """Paste a hand block centred on frame point (cx, cy)."""
    R.blk(L, int(round(cx - len(rows[0]) / 2)), int(round(cy - len(rows) / 2)), rows)
    return L


# ------------------------------------------------------------------ legs
def legs_lift_far(up=5, out=3):
    """legs_narrow with the FAR foot kicked up off the stone (the mirror of legs_lift_near)."""
    L = P.legs_narrow()
    shoe = L[57:64, 11:32].copy()
    L[57 - up:64, 8:31] = '.'
    R.composite(L, shoe, 11 - out, 57 - up)
    for y in range(57, 63):
        L[y, 31] = '#'
    for y in range(57 - up, 57 - up + 6):
        if L[y, 30] == '.':
            L[y, 30] = '#'
    return L


def legs_squat(rows=5, wide=True):
    """His legs with `rows` of trouser removed under the hips: a squat (knees bent toward us).
    The torso and everything above must be lowered by the same `rows`."""
    src = P.B64['legs'] if wide else P.legs_narrow()
    L = R.blank(64, 64)
    L[46, :] = src[46, :]
    L[47 + rows:64, :] = src[47 + rows:64, :]
    L[47:47 + rows, :] = '.'
    # the hip line sits straight on the shortened legs
    out = R.blank(64, 64)
    out[46 + rows, :] = src[46, :]
    out[47 + rows:64, :] = src[47 + rows:64, :]
    return out


DAZED_SOLE = [
    "..######..",
    ".#OOOOOO#.",
    "#OxxxxxxO#",
    "#OxOxxOxO#",
    "#OxxxxxxO#",
    "#OxOxxOxO#",
    ".#OxxxxO#.",
    ".#OOOOOO#.",
    ".#OxxxxO#.",
    ".#OOOOOO#.",
    "..######..",
]


def legs_sit(hip_y=85, spread=19.5):
    """Sat down: legs out toward us in a V, soles up (frame coords; hip_y is the belt's bottom row)."""
    L = R.blank(FW, FH)
    X, Y = R.centres(FW, FH)
    for (a, b) in (((38.5, hip_y), (48 - spread - 9.5, hip_y + 4)), ((57.5, hip_y), (48 + spread + 9.5, hip_y + 4))):
        m = R.tcapsule_mask(a[0], a[1], b[0], b[1], 7.2, 6.0, FW, FH)
        v = R.lambert(R.tcapsule_normal(X, Y, a[0], a[1], b[0], b[1], 7.2, 6.0))
        R.paint_part(L, m, R.quant(v, 'zQqp', [0.28, 0.58, 0.88]))
    R.blk(L, int(48 - spread - 20.5), hip_y - 1, DAZED_SOLE)
    R.blk(L, int(48 + spread + 10.5), hip_y - 1, DAZED_SOLE)
    return L


# ------------------------------------------------------------------ RotSprite-style rotation
def scale2x(cv):
    """EPX / Scale2x on a char canvas."""
    h, w = cv.shape
    P_ = np.pad(cv, 1, mode='edge')
    A = P_[:-2, 1:-1]; B = P_[1:-1, 2:]; C = P_[1:-1, :-2]; D = P_[2:, 1:-1]; E = cv
    out = np.empty((h * 2, w * 2), dtype=cv.dtype)
    e0 = np.where((C == A) & (C != D) & (A != B), A, E)
    e1 = np.where((A == B) & (A != C) & (B != D), B, E)
    e2 = np.where((D == C) & (D != B) & (C != A), C, E)
    e3 = np.where((B == D) & (B != A) & (D != C), D, E)
    out[0::2, 0::2] = e0
    out[0::2, 1::2] = e1
    out[1::2, 0::2] = e2
    out[1::2, 1::2] = e3
    return out


def rotsprite(cv, deg, pivot=None, out_size=None, out_pivot=None):
    """Rotate a char canvas by deg (counter-clockwise on screen) about pivot, RotSprite style: 8x with
    Scale2x three times, nearest rotation, then sample every 8th texel. Returns a new canvas of out_size
    with the pivot landing on out_pivot."""
    h, w = cv.shape
    pivot = pivot or (w / 2.0, h / 2.0)
    out_size = out_size or (w, h)
    out_pivot = out_pivot or (out_size[0] / 2.0, out_size[1] / 2.0)
    big = scale2x(scale2x(scale2x(cv)))
    S = 8
    ow, oh = out_size
    out = R.blank(ow, oh)
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    ys, xs = np.mgrid[0:oh * S, 0:ow * S]
    # destination (big) -> source (big): inverse rotation about the pivots
    dx = (xs + 0.5) / S - out_pivot[0]
    dy = (ys + 0.5) / S - out_pivot[1]
    sx = ca * dx - sa * dy + pivot[0]
    sy = sa * dx + ca * dy + pivot[1]
    bx = np.floor(sx * S).astype(int)
    by = np.floor(sy * S).astype(int)
    ok = (bx >= 0) & (by >= 0) & (bx < w * S) & (by < h * S)
    res = np.full((oh * S, ow * S), '.', dtype=cv.dtype)
    res[ok] = big[by[ok], bx[ok]]
    # sample the centre of each 8x8 block
    out[:, :] = res[S // 2::S, S // 2::S]
    return out
