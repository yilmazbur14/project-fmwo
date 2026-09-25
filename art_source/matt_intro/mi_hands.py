"""Matt's hands for the gestures, drawn pixel by pixel in the rig's skin ramp (1 light -> 6 dark),
lit from the upper left, every finger split from the next by a keyline like the approved fists.

Each hand is (rows, anchor): anchor is the (col, row) of the map pixel that sits on the arm's attach
point, 3 px past the wrist along the forearm, which is where the approved fists meet their cuffs.
'_L' hands belong to the screen-left arm (his right hand), '_R' to the screen-right arm (his left).
A right-hand twin is drawn separately wherever the light would otherwise flip.

    python mi_hands.py        # check widths, render every hand at 10x into the scratchpad
"""
import mi_base as B

# ------------------------------------------------------------------ the approved fists (from the rig)
FIST_L = (B.details.FIST_L, (7, 0))
FIST_R = (B.details.FIST_R, (6, 0))

# ------------------------------------------------------------------ open hand, fingers up (the wave)
# His right hand raised beside his head, palm to camera: four fingers up (middle longest, pinky
# shortest), the thumb out toward his head, a palm crease. Attach point: the wrist at the bottom.
OPEN_UP_L = ([
    # 0123456789012345
    ".......kk.......",   # 0  middle fingertip
    "....kkk12kkk....",   # 1  ring and index tips
    "...k12k12k22k...",   # 2
    ".kkk12k12k22k...",   # 3  pinky tip
    "k12k12k12k22k...",   # 4
    "k12k12k12k23kkk.",   # 5  thumb tip
    "k12k12k22k23k23k",   # 6
    "k11222222333k23k",   # 7  fingers meet the palm
    "k11222333333334k",   # 8  crease, thumb joins
    "k1222222233334k.",   # 9
    "k122222233334k..",   # 10
    ".k2222233344k...",   # 11
    "..kkkkkkkkkk....",   # 12 wrist
], (6, 12))

# His left hand the same way (the shrug uses both): the thumb toward his head, now screen-left,
# drawn as its own twin so the light stays upper left.
OPEN_UP_R = ([
    # 0123456789012345
    ".......kk.......",   # 0
    "....kkk12kkk....",   # 1
    "...k12k12k23k...",   # 2
    "...k12k12k23kkk.",   # 3  pinky tip
    "...k12k12k23k23k",   # 4
    ".kkk12k12k23k23k",   # 5  thumb tip
    "k12k12k22k23k34k",   # 6
    "k12k11222222233k",   # 7
    "k11222222233334k",   # 8
    ".k1222222233334k",   # 9
    "..k122222233334k",   # 10
    "...k2222233344k.",   # 11
    "....kkkkkkkkkk..",   # 12
], (9, 12))

# ------------------------------------------------------------------ open hands hanging, palms out
# The welcoming pose: arms loose and a little out, palms turned to the front, fingers down, the
# thumbs out to the sides. Attach point: the wrist at the top.
OPEN_DOWN_L = ([
    # 0123456789012345
    "....kkkkkkkkkk..",   # 0  wrist
    "...k1122222233k.",   # 1
    "..k112222222334k",   # 2
    ".k1222222223334k",   # 3
    "k12222222233334k",   # 4  thumb joins
    "k12k22222223334k",   # 5
    "k23k12k12k23k34k",   # 6  fingers
    ".kkk12k12k23k34k",   # 7  thumb tip
    "...k12k12k23k34k",   # 8
    "...k12k12k23kkk.",   # 9  pinky tip
    "...k12k12k23k...",   # 10
    "....kkk12kkk....",   # 11 index and ring tips
    ".......kk.......",   # 12 middle fingertip
], (9, 0))

OPEN_DOWN_R = ([
    # 0123456789012345
    "..kkkkkkkkkk....",   # 0  wrist
    ".k1122222233k...",   # 1
    "k112222222334k..",   # 2
    "k1222222223334k.",   # 3
    "k12222222233323k",   # 4  thumb joins
    "k12222222333k23k",   # 5
    "k12k12k12k23k34k",   # 6  fingers
    "k12k12k12k23kkk.",   # 7  thumb tip
    "k12k12k12k23k...",   # 8
    ".kkk12k12k23k...",   # 9  pinky tip
    "...k12k12k23k...",   # 10
    "....kkk12kkk....",   # 11
    ".......kk.......",   # 12
], (6, 0))

# ------------------------------------------------------------------ thumb to chest (proud)
# His right fist across his chest, the thumb out and pointing in at his own sternum; the curled
# fingers face the camera as three creases. The forearm arrives from the left.
THUMB_L = ([
    # 0123456789012345
    ".kkkkkkk.......",    # 0
    "k1122223kkkkkk.",    # 1
    "k1222223111222k",    # 2  thumb
    "k2222233222334k",    # 3
    "k1kkkkk3kkkkkk.",    # 4  first crease; under the thumb
    "k2222334k......",    # 5
    "k1kkkk44k......",    # 6
    "k2223345k......",    # 7
    "k2kkk445k......",    # 8
    ".k33445k.......",    # 9
    "..kkkkk........",    # 10
], (0, 5))

# ------------------------------------------------------------------ index fingers poking (nervous)
# Both fists in front of his belly, index fingers out and meeting in the middle. Forearms arrive
# from the outside; the attach point is the fist's outer edge.
POKE_L = ([
    # 012345678901
    ".kkkkkk.....",       # 0
    "k112223kkkk.",       # 1
    "k1222231112k",       # 2  index finger
    "k2222332233k",       # 3
    "k1kkk33kkkk.",       # 4
    "k222334k....",       # 5
    "k2kk344k....",       # 6
    "k233445k....",       # 7
    ".kkkkkk.....",       # 8
], (0, 4))

POKE_R = ([
    # 012345678901
    ".....kkkkkk.",       # 0
    ".kkkk112223k",       # 1
    "k1112122233k",       # 2
    "k2233222334k",       # 3
    ".kkkk2kk334k",       # 4
    "....k122334k",       # 5
    "....k2kk344k",       # 6
    "....k233445k",       # 7
    ".....kkkkkk.",       # 8
], (11, 4))

# ------------------------------------------------------------------ fists raised (ENOUGH)
# Both fists up beside his head: the approved fist turned over, so its three curled-finger ticks
# point up and the knuckle line sits above the back of the hand, re-lit from the upper left.
# Forearms arrive from below.
FIST_UP_L = ([
    # 01234567890123
    "..kkkkkkkkkk..",     # 0
    ".k12k12k22k3k.",     # 1  curled fingertips
    "k112k12k22k33k",     # 2
    "k122k12k23k34k",     # 3
    "k122k22k23k34k",     # 4
    "k122522523534k",     # 5  knuckles
    "k112222222334k",     # 6  back of the hand
    "k122222223344k",     # 7
    "k222223333444k",     # 8
    ".kkkkkkkkkkkk.",     # 9  wrist
], (7, 9))

FIST_UP_R = ([
    # 01234567890123
    "..kkkkkkkkkk..",     # 0
    ".k1k12k22k23k.",     # 1
    "k11k12k22k233k",     # 2
    "k12k12k23k334k",     # 3
    "k12k22k23k334k",     # 4
    "k125225235344k",     # 5
    "k112222222334k",     # 6
    "k122222223344k",     # 7
    "k222223333444k",     # 8
    ".kkkkkkkkkkkk.",     # 9
], (6, 9))

# ------------------------------------------------------------------ scratching his head (sheepish)
# His right hand on the side of his head, the back of the hand toward us and the fingers hooked
# into the hair. The forearm arrives from below-left.
SCRATCH_L = ([
    # 01234567890
    "....kkkkk..",        # 0
    "..kk1122kk.",        # 1  fingertips hooked over
    ".k11k22k23k",        # 2
    "k112k23k34k",        # 3
    "k122k23k34k",        # 4  knuckles
    "k12222223k.",        # 5  back of the hand
    "k1222223k..",        # 6
    ".k22234k...",        # 7
    "..kkkkk....",        # 8
], (3, 8))

HANDS = {n: v for n, v in globals().items() if n.isupper() and isinstance(v, tuple) and len(v) == 2
         and isinstance(v[0], list)}


def check():
    bad = []
    for n, (rows, (ac, ar)) in HANDS.items():
        rs = B.rows_of(rows)
        bad += B.check_map(rows, len(rs[0]), n)
        if not (0 <= ac < len(rs[0]) and 0 <= ar < len(rs)):
            bad.append('%s: anchor %s outside the map' % (n, (ac, ar)))
    return bad


def shear(hand, t, pivot_row=None):
    """A hand leaned by t px per row about pivot_row (default: its anchor row): the wave's rock.
    Rows shift whole, so fingers stay one keyline apart."""
    rows, (ac, ar) = hand
    rs = B.rows_of(rows)
    pr = ar if pivot_row is None else pivot_row
    shifts = [int(round((pr - r) * t)) for r in range(len(rs))]
    lo = min(shifts)
    hi = max(shifts)
    w = len(rs[0]) + (hi - lo)
    out = []
    for r, row in enumerate(rs):
        s = shifts[r] - lo
        out.append('.' * s + row + '.' * (w - s - len(row)))
    # where a row step opens the outline, close it with keyline (never over the hand itself)
    grid = [list(r) for r in out]
    h = len(grid)
    add = set()
    for y in range(h):
        for x in range(w):
            if grid[y][x] in '.k':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                qx, qy = x + dx, y + dy
                if 0 <= qx < w and 0 <= qy < h and grid[qy][qx] == '.':
                    add.add((qx, qy))
    for (x, y) in add:
        grid[y][x] = 'k'
    return [''.join(r) for r in grid], (ac + shifts[ar] - lo, ar)


if __name__ == '__main__':
    import mi_view as V
    for line in check():
        print(line)
    ims = []
    for n, (rows, anc) in sorted(HANDS.items()):
        part = B.amap(rows, 1, 1)
        w = len(B.rows_of(rows)[0]) + 2
        h = len(rows) + 2
        im = B.image(part, w, h)
        ims.append(V.label(V.up(im, 10), '%s %s' % (n, anc)))
    print(V.save(V.row(ims), 'hands_10x.png'))
