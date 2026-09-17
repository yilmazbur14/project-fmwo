"""Face variants for the beast Bixby combat animations.
Same local coordinate systems as faces.py:
  middle head: lx = col - (ox - 30), ly = row - oy   (stamps authored for the LEFT half / left eye, mirrored)
  side head:   authored facing left; col = ox + lx (side +1) or ox + 41 - lx (side -1)
Pose keys read from P:
  eyes_mid / eyes_side_L / eyes_side_R : 'angry' (approved) | 'tired' | 'shut' | 'roar' | 'dizzy'
  mouth_mid / mouth_side_L / mouth_side_R : 'fire' (approved) | 'pant' | 'yelp' | 'roar' | 'shut'
  tongue_L / tongue_R : lolling tongue length for the side heads (0 = none)
'.' keeps the pixel underneath, '_' clears it."""
from pal import PALC
import faces as FC
from faces import put_grid, mid_tx, side_tx, sym_half, drop_rows

EXTRA = {'p': (0xFF, 0xB3, 0xC0, 255)}      # bixby.png tongue highlight


def _col(ch):
    return EXTRA[ch] if ch in EXTRA else PALC[ch]


def put2(cv, grid, lx0, ly0, tx):
    rows = grid.strip('\n').split('\n')
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            c, r = tx(lx0 + dx, ly0 + dy)
            if ch == '_':
                cv.put(c, r, None)
            else:
                cv.put(c, r, _col(ch))


# ================================================================== middle head eyes (12x9 at lx 16, ly 17)
MID_EYE = {
    'angry': FC.MID_EYE_L,
    # heavy upper lid, brow relaxed and sagging to the outside, thin dim glow
    'tired': """
............
............
..........kk
.......kkk45
kkkkkkk4555.
45555555kkk.
.kkkkkkkkk5.
.4kFoooFFk..
..44kkkkk...
""",
    # squeezed shut ">" with a crease above and below
    'shut': """
............
kk..........
44kk........
.444kkk.....
....44kkkk..
..kkkk4.....
kk444.......
44..........
............
""",
    # roar: wide open, blazing (bright core), brows slammed down
    'roar': """
kkk.........
455kkkk.....
.45555kkkk..
.kkkk45555kk
.kLWOkkk455k
.kOLWLOkk45k
.4kOLLLOokkk
..4kFoooFk..
...4kkkkk...
""",
    # dizzy swirl (defeat)
    'dizzy': """
............
..kkkkkk....
.k444444k...
k4kkkk44k...
k4k44k4k4k..
k4k4kk4k4k..
k44kkk44k...
.k44444k....
..kkkkk.....
""",
}

# ================================================================== middle head mouths (half grids at lx 16, ly 36)
# rows 0..3 are the muzzle underside (kept from the approved grid), row 4 is the upper lip line
MUZZLE_TOP = FC.MID_MOUTH_HALF.strip('\n').split('\n')[:4]

MID_MOUTH = {
    'fire': FC.MID_MOUTH_HALF,
    # panting: open, dark throat with a dying ember, tongue flopped over the lower teeth and out past the chin
    'pant': '\n'.join(MUZZLE_TOP + """
.kkkkkkkkkkkkk
.kDknnnnnnnnnn
.kDkWWknnkWkWk
.kkMWWkMMkMkMk
..kMWwkMMMMMMM
..kMwvkMMMMSSS
..kMkvkMMSSrrr
..kMMkMMSrrFrr
..kMMkMMSrFooF
..kMkMMMkkkkkk
...kvkMkppmmmm
...kwknkpmmmmm
...kWknkmmmmnm
....kwkkmmmnnm
....kvkkmmmnnn
.....kkkmmnnnk
.......kmnnnkk
.......kknnnk.
........kkkk..
""".strip('\n').split('\n')),
    # yelp: mouth snapped open wide, tongue curled back, no fire
    'yelp': '\n'.join(MUZZLE_TOP + """
.kkkkkkkkkkkkk
.kDknnnnnnnnnn
.kDkWWknnkWkWk
.kkMWWkMMkvkvk
..kMWwkMMMMMMM
..kMwvkMMMMMMM
..kMkvkMMMMMMM
..kMMkMMMMMMMM
..kMMkMMMMnnnn
..kMkMMMnnmmmm
...kvkMnmmpppp
...kwknmmmmmmm
...kWknnmmmmmm
....kwknnnnnnn
....kvukkkkkkk
.....kuuuutttt
......kkkkkkkk
""".strip('\n').split('\n')),
    # roar: jaw wide, throat full of fire (used with a large mh_jaw)
    'roar': FC.MID_MOUTH_HALF,
    # clenched teeth grimace (hit recoil frame 2)
    'shut': '\n'.join(MUZZLE_TOP + """
.kkkkkkkkkkkkk
.kDkWWkWWkWWkW
.kkkWWkWWkWWkW
..kkkkkkkkkkkk
..kvkWWkWWkWWk
...kvkkkkkkkkk
....kvvuuuuttt
.....kkkkkkkkk
""".strip('\n').split('\n')),
}

MID_ROW = {
    'fire': FC.MID_FIRE_ROW,
    'roar': FC.MID_FIRE_ROW,
    'pant': "..kMMkMMMSSSSS",
    'yelp': "..kMMkMMMMMMMM",
    'shut': None,
}


def middle_face(cv, ox, oy, jd, P):
    L = mid_tx(ox, oy)
    R = mid_tx(ox, oy, mirror=True)
    ev = P.get('eyes_mid', 'angry')
    evR = P.get('eyes_mid_R', ev)
    if ev == 'angry' and evR == 'angry' and P.get('mouth_mid', 'fire') == 'fire' and not P.get('nose_mid'):
        FC.middle_face(cv, ox, oy, jd)          # approved path, pixel identical
        return
    put2(cv, MID_EYE[ev], 16, 17, L)
    put2(cv, MID_EYE[evR], 16, 17, R)
    put_grid(cv, FC.MID_NOSE, 23, 25, L)
    mv = P.get('mouth_mid', 'fire')
    half = MID_MOUTH[mv]
    row = MID_ROW.get(mv)
    if jd and row:
        half = drop_rows(half, 12, [row] * jd)
    put2(cv, sym_half(half), 16, 36, L)
    if mv == 'pant':
        # the tongue flops to the viewer's left: clear the mirrored copy's lower tongue on the right
        pass


# ================================================================== side heads
SIDE_EYE_FAR = {
    'angry': FC.SIDE_EYE_FAR,
    'tired': """
.......
kkkk...
3444kk.
.kkkkkk
.3kFoFk
..3kkk.
""",
    'shut': """
k......
3kk....
.33kk..
.kk33k.
k33....
.......
""",
    'roar': """
kk.....
3kkk...
3kLWkk.
.kOLOkk
.3kFoFk
..3kkk.
""",
    'dizzy': """
.kkkk..
k3333k.
k3kk3k.
k3k33k.
.k33k..
..kk...
""",
}

SIDE_EYE_NEAR = {
    'angry': FC.SIDE_EYE_NEAR,
    'tired': """
.........
.........
......kkk
kkkkkkk44
k4444444k
.kkkkkkkk
..kFooFk.
...kkkk..
""",
    'shut': """
.........
.......kk
.....kk4.
...kk44..
.kk44....
...kk44..
.....kk4.
.......kk
""",
    'roar': """
.......kk
....kkkk4
..kkk4454
kkkWLLkk4
kkOLWLOk4
.kFoOOok.
..kkFFk..
....kk...
""",
    'dizzy': """
.........
..kkkkk..
.k44444k.
k4kkkk44k
k4k44k4k.
k44kk44k.
.k4444k..
..kkkk...
""",
}

SIDE_MOUTH = {
    'fire': FC.SIDE_MOUTH,
    # panting: open, dark, a dying ember deep in the throat; the tongue is added by side_tongue()
    'pant': """
kkkkkkkkkkkkkkkkkkkkkk.
kWWknnnnnnnWWknnnnnkkk.
kWWkMkWkWkMWWkMMMMMMkk.
.kWMMMMMMMMkvkMMMMMMMk.
.kvMMMMMSrrSkMMMMMMMk..
..kMMMMSrFrSSMMMMMMk...
..kkMMMSrrSnnkkkkkk....
...kWknnnnmmnkvW.......
...kvWkknnnnkkWk.......
""",
    'yelp': """
kkkkkkkkkkkkkkkkkkkkkk.
kWWknnnnnnnWWknnnnnkkk.
kWWkMkWkWkMWWkMMMMMMkk.
.kWMMMMMMMMkvkMMMMMMMk.
.kvMMMMMMMMMkMMMMMMMk..
..kMMMMnnnnnMMMMMMMk...
..kkMnnmmmmnnkkkkkk....
...kWknmmppmnkvW.......
...kvWkknnnnkkWk.......
""",
    'roar': FC.SIDE_MOUTH,
    'shut': """
kkkkkkkkkkkkkkkkkkkkkk.
kWWkWWkWWkWWkWWkWWkkk..
kkkkkkkkkkkkkkkkkkk....
.kvWWkWWkWWkWWkk.......
..kkkkkkkkkkkkk........
""",
}

SIDE_ROW = {'fire': FC.SIDE_FIRE_ROW, 'roar': FC.SIDE_FIRE_ROW,
            'pant': "..kMMMMSrrSSMMMMMMMMk..", 'yelp': "..kMMMMMMMMMMMMMMMMMk..", 'shut': None}

# lolling tongue hanging from the front of the mouth (authored facing left), grows downward with length n
TONGUE_TOP = """
..kppmmk.
.kpmmmmnk
.kpmmmnnk
"""
TONGUE_SEG = ".kmmmnnnk"
TONGUE_TIP = """
.kmmnmnnk
..kmmnnk.
...kkkk..
"""


def side_tongue(cv, ox, oy, side, jd, n, sway=0):
    T = side_tx(ox, oy, side)
    ly0 = 33 + jd
    rows = TONGUE_TOP.strip('\n').split('\n') + [TONGUE_SEG] * max(0, n) + TONGUE_TIP.strip('\n').split('\n')
    for i, row in enumerate(rows):
        off = 0
        if sway and i > 3:
            off = int(round(sway * (i - 3) / max(1, len(rows) - 3)))
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            c, r = T(3 + dx + off, ly0 + i)
            cv.put(c, r, _col(ch))


def side_face(cv, ox, oy, side, jd, P, which):
    ev = P.get('eyes_side_' + which, P.get('eyes_side', 'angry'))
    mv = P.get('mouth_side_' + which, P.get('mouth_side', 'fire'))
    tongue = P.get('tongue_' + which, 0)
    if ev == 'angry' and mv == 'fire' and not tongue:
        FC.side_face(cv, ox, oy, side, jd)       # approved path, pixel identical
        return
    T = side_tx(ox, oy, side)
    put2(cv, SIDE_EYE_FAR[ev], 13, 9, T)
    put2(cv, SIDE_EYE_NEAR[ev], 25, 7, T)
    put_grid(cv, FC.SIDE_NOSE, 0, 17, T)
    m = SIDE_MOUTH[mv]
    row = SIDE_ROW.get(mv)
    if jd and row:
        m = drop_rows(m, 5, [row] * jd)
    put2(cv, m, 3, 26, T)
    if tongue:
        side_tongue(cv, ox, oy, side, jd, tongue - 1, P.get('tongue_sway_' + which, 0))
