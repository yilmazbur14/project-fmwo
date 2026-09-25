"""The player's pose sheet for Danny's fight, in the player's pose-sheet format (PlayerPosed):

    player_sumo_push   the sumo tug-of-war against Danny at the top gate

8 columns x 4 rows of 32x32 cells, rows in player_4dir_sheet.png's order (DOWN, UP, LEFT, RIGHT), so
PlayerPosed's row is always the player's facing. The sumo is staged vertically: Danny blocks the TOP
gate facing the camera and the player clinches from below, facing UP, so only the back view is ever
seen. Row 1 (UP) is drawn and rows 0, 2 and 3 are copies of it, exactly as player_glass_row.png does,
so no facing can show a wrong row. (The worm root has no pose: it is the normal sprite plus the FX,
because a PlayerPosed pose would keep the guard down and the headbutt could not be parried.)

His own style, measured off player_4dir_sheet.png, player_guard_break.png and player_glass_row.png
(NOT the bosses' style): seven colours, no keyline at all (black is only his hair and his shoes), flat
blocks; arms two texels, lit on the outer side (S) and shaded on the inner (s); legs lit on the left;
gloves 2x3, lit on the outer top corner (L) and shaded along the bottom (D); the spine and shoulder
blades ticked in the darker skin. Soles on row 28, centred on column 16 (the idle's footprint).

Every body part that exists on his shipped sheets is copied from them texel for texel (the head from
the UP idle, checked by dp_export; the back; the shorts; the front torso and face for the frame that
ends on his back); only limbs are drawn per pose.

Each pose is a grid, one character per texel, up to 32 per row (trailing '.' may be left off), rows not
listed are empty:
    k black (hair, shoes)   D dark blue   B blue   L light blue   R red (headband)
    s shaded skin           S skin        . empty
Nothing in this module writes anything.
"""
import os
import sys

sys.dont_write_bytecode = True

from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
PLAYER_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer')
SHEET_4DIR = os.path.join(PLAYER_DIR, 'player_4dir_sheet.png')

PAL = {
    'k': (0, 0, 0, 255), 'D': (22, 47, 187, 255), 'B': (36, 100, 189, 255), 'L': (56, 131, 201, 255),
    'R': (172, 50, 50, 255), 's': (172, 113, 79, 255), 'S': (215, 152, 100, 255),
}
KEYS = {v[:3]: k for k, v in PAL.items()}
W = H = 32
DOWN, UP, LEFT, RIGHT = 0, 1, 2, 3


# ------------------------------------------------------------------ reading his shipped cells
def from_sheet(path, col, row):
    im = Image.open(path).convert('RGBA').crop((col * W, row * H, col * W + W, row * H + H))
    px = {}
    for y in range(H):
        for x in range(W):
            c = im.getpixel((x, y))
            if c[3]:
                px[(x, y)] = KEYS[c[:3]]
    return px


def as_rows(px, y0, y1):
    """Cells of a parsed cell as 32-wide strings, rows y0..y1."""
    return {y: ''.join(px.get((x, y), '.') for x in range(W)) for y in range(y0, y1 + 1)}


# ------------------------------------------------------------------ grids
def pad(r, y=None):
    """A grid row padded out to 32 with '.': trailing dots carry nothing, so rows may stop at their
    last texel. A row longer than 32 is an error."""
    assert len(r) <= W, (y, len(r), r)
    return r + '.' * (W - len(r))


def g(rows):
    """{row: string of up to 32} -> {(x, y): key}."""
    px = {}
    for y, r in rows.items():
        r = pad(r, y)
        for x, ch in enumerate(r):
            if ch != '.':
                assert ch in PAL, (y, x, ch)
                px[(x, y)] = ch
    return px


def image(px):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < W and 0 <= y < H:
            im.putpixel((x, y), PAL[k])
    return im


def with_rows(base, rows):
    """A copy of a {row: string} grid with some rows replaced or added."""
    out = dict(base)
    out.update(rows)
    return out


# ------------------------------------------------------------------ the push frames
# Every frame is drawn in full, one character per texel. The head (hair, headband, knot, nape) is the
# UP idle's own, only moved (the exporter checks it texel for texel); where an arm crosses the
# headband's two flying tails, the tail is drawn over it. The torso rows are the idle's back (with its
# spine and shoulder-blade ticks) and the shorts are the idle's, cut shorter or wider for the crouch.

# 0 SET: the lock-up. His own guard (the UP idle's gloves either side of the head, the right one a
# row higher) dropped into the wide squat: the back bent over to five rows, the head sunk three rows
# between the shoulders, the knees out.
SET = {
    7:  '..............kkk...............',
    8:  '.............kkkkk..............',
    9:  '...........R.RRRRR.BL...........',
    10: '..........LBRkkRkk.BB...........',
    11: '..........BB.kkkkk.DD...........',
    12: '..........BD.skkks.SS...........',
    13: '..........SSS.SsS.sS............',
    14: '...........SsSSsSSsS............',
    15: '...........SSsSsSsSS............',
    16: '.............SSsSSS.............',
    17: '.............SSSSSS.............',
    18: '............BBLBLBL.............',
    19: '...........BBBBBBBBD............',
    20: '..........BBBBBBBBBBD...........',
    21: '..........BBBBBBBBBBD...........',
    22: '..........BBBBB..BBBBD..........',
    23: '..........BBBB....BBBD..........',
    24: '..........Ss.......SSs..........',
    25: '.........Ss.........Ss..........',
    26: '.........Ss.........SSs.........',
    27: '........kkk.........kkk.........',
    28: '.......kkkk.........kkkk........',
}

# 1-2 STRAIN: locked up. Both arms driven out up the ring and locked, bowed a texel under the weight,
# the gloves pressed on Danny's hands (rows 3-5); the head down between the hunched shoulders; the legs
# in a driving lunge, digging in turn. A: the left leg thrust back onto its toes, the right foot planted
# forward. B: the other way round. Everything above the waist is the same in A and B, so the gloves'
# contact never moves while the feet scrabble.
STRAIN_TOP = {
    3:  '...........LB.....BL............',
    4:  '...........BB.....BB............',
    5:  '...........BD.....DD............',
    6:  '...........Ss.....sS............',
    7:  '..........Ss..kkk..sS...........',
    8:  '..........Ss.kkkkk.sS...........',
    9:  '..........SR.RRRRR.sS...........',
    10: '..........SsRkkRkk.sS...........',
    11: '..........Ss.kkkkk.sS...........',
    12: '..........Ss.skkks.sS...........',
    13: '...........SS.SsS.sS............',
    14: '...........SsSSsSSsS............',
    15: '...........SSsSsSsSS............',
    16: '.............SSsSSS.............',
    17: '.............SSSSSS.............',
    18: '............BBLBLBL.............',
    19: '...........BBBBBBBBD............',
    20: '..........BBBBBBBBBBD...........',
    21: '..........BBBBBBBBBBD...........',
    22: '..........BBBBB..BBBBD..........',
}
STRAIN_A = with_rows(STRAIN_TOP, {
    23: '.........BBBB.....BBBD..........',
    24: '.........Ss.......SSs...........',
    25: '........Ss........kkk...........',
    26: '........Ss........kkkk..........',
    27: '.......kk.......................',
    28: '.......kk.......................',
})
STRAIN_B = with_rows(STRAIN_TOP, {
    23: '..........BBBB.....BBBD.........',
    24: '..........Ss........SSs.........',
    25: '.........kkk.........SSs........',
    26: '........kkkk..........Ss........',
    27: '......................kk........',
    28: '......................kk........',
})

# 3 SHOVE: he wins. A big step up the ring (the right foot planted well forward, its sole on row 24),
# the left leg driving straight back onto its toes, the whole body risen two rows and thrown forward,
# the arms locked out full length with the gloves at the top of the cell.
SHOVE = {
    0:  '...........LB.....BL............',
    1:  '...........BB.....BB............',
    2:  '...........BD.....DD............',
    3:  '...........Ss.....sS............',
    4:  '...........Ss.....sS............',
    5:  '..........Ss..kkk..sS...........',
    6:  '..........Ss.kkkkk.sS...........',
    7:  '..........SR.RRRRR.sS...........',
    8:  '..........SsRkkRkk.sS...........',
    9:  '..........Ss.kkkkk.sS...........',
    10: '..........Ss.skkks.sS...........',
    11: '...........SS.SsS.sS............',
    12: '...........SsSSsSSsS............',
    13: '...........SSsSsSsSS............',
    14: '.............SSsSSS.............',
    15: '.............SSSSSS.............',
    16: '............BBLBLBL.............',
    17: '...........BBBBBBBBD............',
    18: '..........BBBBBBBBBBD...........',
    19: '..........BBBBBBBBBBD...........',
    20: '..........BBBBB..BBBBD..........',
    21: '.........BBBB.....BBBD..........',
    22: '.........Ss.......SSs...........',
    23: '.........Ss.......kkk...........',
    24: '........Ss........kkkk..........',
    25: '........Ss......................',
    26: '.......Ss.......................',
    27: '.......kk.......................',
    28: '.......kk.......................',
}

# 4-5 SKID: he loses ground. Still locked on, but the arms buckle (the gloves driven a row back down,
# the elbows bowing out), the head tucked a row further down; both feet shoved back behind him and
# scraping. B: the right heel skips a row off the canvas. The top is the same in A and B.
SKID_TOP = {
    4:  '...........LB.....BL............',
    5:  '...........BB.....BB............',
    6:  '...........BD.....DD............',
    7:  '...........Ss.....sS............',
    8:  '..........Ss..kkk..sS...........',
    9:  '.........Ss..kkkkk..sS..........',
    10: '.........SsR.RRRRR..sS..........',
    11: '.........Ss.RkkRkk..sS..........',
    12: '.........Ss..kkkkk..sS..........',
    13: '..........Ss.skkks.sS...........',
    14: '...........SS.SsS.sS............',
    15: '...........SsSSsSSsS............',
    16: '.............SSsSSS.............',
    17: '.............SSSSSS.............',
    18: '............BBLBLBL.............',
    19: '...........BBBBBBBBD............',
    20: '..........BBBBBBBBBBD...........',
    21: '..........BBBBBBBBBBD...........',
    22: '..........BBBBB..BBBBD..........',
    23: '..........BBBB....BBBD..........',
    24: '..........Ss.......SSs..........',
    25: '.........Ss.........SSs.........',
}
SKID_A = with_rows(SKID_TOP, {
    26: '........Ss...........Ss.........',
    27: '.......kkk...........kkk........',
    28: '......kkkk...........kkkk.......',
})
SKID_B = with_rows(SKID_TOP, {
    26: '........Ss...........kkk........',
    27: '.......kkk...........kkkk.......',
    28: '......kkkk......................',
})

# 6 LAUNCHED: Danny's shove lands. Off his feet and tipping back toward us, thrown off square: the back
# foreshortened, the head snapped back into the shoulders with the headband's tails whipping up off
# it, the left arm flung high, the right thrown out wide, the legs kicked up unevenly (soles on 25-26).
LAUNCHED = {
    3:  '.....LB.........................',
    4:  '.....BB.........................',
    5:  '.....BD.........................',
    6:  '......Ss........................',
    7:  '......Ss..................BL....',
    8:  '.......Ss.................BB....',
    9:  '.......Ss..R..kkk.........DD....',
    10: '........Ss..Rkkkkk.......sS.....',
    11: '........Ss...RRRRR......sS......',
    12: '.........Ss..kkRkk.....sS.......',
    13: '.........Ss..kkkkk....sS........',
    14: '..........Ss.skkks..SsS.........',
    15: '...........SS.SsS.sS............',
    16: '...........SsSSsSSsS............',
    17: '.............SSsSSS.............',
    18: '.............SSSSSS.............',
    19: '............BBLBLBL.............',
    20: '...........BBBBBBBBD............',
    21: '..........BBBBBBBBBBD...........',
    22: '..........BBBB...BBBD...........',
    23: '.........Ss.......SSs...........',
    24: '........kkk.......SSs...........',
    25: '........kk........kkk...........',
    26: '..................kkkk..........',
}

# 7 ON BACK: pushed out, he has gone over backward toward us and landed flat on his back, head toward
# the camera, so it is his FRONT that shows, upside down: the DOWN idle itself (player_4dir_sheet.png
# column 0, row 0) with its guard gloves taken off, flipped top to bottom and foreshortened to 18 rows
# for lying along the ring (leg, shorts and torso rows dropped), his legs splayed a texel apart; texel
# for texel otherwise (the head exactly, dp_export checks it). Only the arms are drawn, flung out wide
# overhead. The top of his head lands on row 28, where his soles were.
ON_BACK = {
    11: '...................kkkk',
    12: '..........kk.......kkk',
    13: '..........kk.......SSs',
    14: '..........Ss.......SSs',
    15: '...........BBB...BBBD',
    16: '...........BBBBBBBBBD',
    17: '...........BBBBBBBD',
    18: '............BBLBLBL',
    19: '.............SSSSSS',
    20: '............SSSSSSSS',
    21: '.........SsSsSsSsSsSsS',
    22: '.......Ss.....SSS.....sS',
    23: '...LBSs......SRSRS......sSBL',
    24: '...BB........SSRSS........BB',
    25: '...BD........RRkRR........DD',
    26: '.............RkkkR',
    27: '.............kkkkk',
    28: '..............kkk',
}
# which DOWN-idle row each ON_BACK row is (the flip); the rows between are dropped for the lie. Rows 24+
# of the idle (legs, shoes) are splayed a texel outward (left of column 15 left, the rest right).
ON_BACK_SOURCE_ROWS = {11: 28, 12: 27, 13: 26, 14: 24, 15: 23, 16: 21, 17: 18, 18: 17, 19: 16, 20: 13,
                       21: 11, 22: 10, 23: 9, 24: 8, 25: 7, 26: 6, 27: 5, 28: 4}

PUSH = [
    ('set', SET), ('strain', STRAIN_A), ('strain', STRAIN_B), ('shove', SHOVE),
    ('skid', SKID_A), ('skid', SKID_B), ('launched', LAUNCHED), ('on_back', ON_BACK),
]
# The head's top-left texel row per frame (where the UP idle's rows 4-9 moved to), for the likeness
# check; the tails may be over an arm or whipped elsewhere, so they are not part of it.
PUSH_HEAD_ROW = [7, 7, 7, 5, 8, 8, 9, None]


# ------------------------------------------------------------------ the audit
# What a cell of his must not ship with, as player_glass_row's exporter checks it: more than one piece
# (a body split by a transparent row), pinholes other than the idle's own neck notches, lone texels,
# colours outside his seven. Plus the numbers his sheets measure.
def components(px):
    seen, n = set(), 0
    for p in px:
        if p in seen:
            continue
        n += 1
        stack = [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in px and q not in seen:
                        seen.add(q)
                        stack.append(q)
    return n


def pinholes(px):
    xs = [x for x, y in px]
    ys = [y for x, y in px]
    out = []
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                out.append((x, y))
    return out


def notches(px):
    """The idle's own neck notches: the texels right under each end of the nape row (s k k k s)."""
    out = set()
    for (x, y), k in px.items():
        if k == 's' and [px.get((x + i, y)) for i in range(1, 5)] == ['k', 'k', 'k', 's']:
            out |= {(x, y + 1), (x + 4, y + 1)}
    return out


def audit(px):
    lone = [p for p in px if not any((p[0] + dx, p[1] + dy) in px
                                     for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)]
    holes = [h for h in pinholes(px) if h not in notches(px)]
    keys = sorted(set(px.values()) - set(PAL))
    out = {'pieces': components(px) - 1, 'holes': holes, 'lone': lone, 'keys': keys}
    xs = [x for x, y in px]
    ys = [y for x, y in px]
    if min(xs) < 0 or max(xs) >= W or min(ys) < 0 or max(ys) >= H:
        out['outside'] = [(min(xs), min(ys), max(xs), max(ys))]
    return out


def black(px):
    return sum(1 for k in px.values() if k == 'k') / len(px)


def sole_row(px):
    return max(y for x, y in px)
