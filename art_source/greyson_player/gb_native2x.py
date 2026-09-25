"""The player's brawl poses redrawn NATIVELY at 2x (PLAN_BRAWL.md section 7): the approval pass.

Same contract as gb_player2x (cells of 64x96, the soles' bottom edge on y 61 with sole texels on rows
59-60, x centre at column 32, the back view), but drawn at 2x instead of doubled: one-texel
silhouettes and anatomy where the x2 has 2x2 blocks. It keeps the approved shapes (every pose
started from its exact x2) and his own style: his seven colours, no keyline (black is only hair and
shoes), arms lit on the outer side, legs lit on the left, gloves lit on the outer top corner.

What the extra resolution is spent on:
  - head: a domed crown with two tufts (his portrait's spiky hair), the headband's knot as a small bow
    at the back and its tails as a one-texel ribbon flying up and left, the ears and the neck under
    the hairline;
  - back: the spine as a one-texel groove, the shoulder blades as lines converging on it (his 1x
    back's own ticks), the lats narrowing to the waist;
  - gloves rounded, with the highlight on the outer top and a dark cuff;
  - shorts: a ribbed waistband (his 1x waistband's alternating highlight at full rate), the dark side
    panel, hemmed leg openings; the boots with a heel.

The approval pass is three cells: GUARD (column 0), the full SLIP LEFT (column 3, derived from the
guard exactly as the approved 1x slip is: the upper body sheared over row by row and dropped) and the
PARRY snap (column 6: the bounce body, gloves thrust up together over the head). The rest follow once
these are approved.

Grids are written in a 32-column window: the string's index + WIN is the cell x. Keys as gb_player.
Nothing in this module writes anything.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gb_player as G  # noqa: E402
import gb_player2x as G2  # noqa: E402

WIN = 16


def win_px(rows, win=WIN):
    px = {}
    for y, text in rows.items():
        assert len(text) <= 64 - win, (y, len(text), text)
        for i, ch in enumerate(text):
            if ch != '.':
                assert ch in G.PAL, (y, i, ch)
                px[(win + i, y)] = ch
    return px


def region(px, y0, y1, x0=0, x1=63):
    return {(x, y): k for (x, y), k in px.items() if y0 <= y <= y1 and x0 <= x <= x1}


def moved(px, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in px.items()}


#          x: 16      24      32      40    47
#             |       |       |       |      |
GUARD = {
    12: '.............k..k',
    13: '............kkkkkk',
    14: '...........kkkkkkkk',
    15: '..........kkkkkkkkkk...BL',
    16: '..........kkkkkkkkkk..BBLL',
    17: '...LB.R...RRRRRRRRRR..BBBL',
    18: '..LLBB.R..RRRRRRRRRR..BBBB',
    19: '..LBBB..RRkkkRRkkkkk..BBBB',
    20: '..BBBB...RkkRRRRkkkk..DBBD',
    21: '..BBBD....kkkkkkkkkk...DD',
    22: '...DD.....kkkkkkkkkk..SsS',
    23: '..SSs.....skkkkkkkks..sSS',
    24: '..SSs......sSkkkkSs..ssSS',
    25: '..SSsS.SSS..SSssSS..SSsSS',
    26: '..SSssSSSSS.SSssSS.SSSsSSS',
    27: '....SSsSSSSSSSSsSSSSSSSsSSS',
    28: '....SSSsSSSSSSSsSSSSSSsSSS',
    29: '......SSsSSSSSSsSSSSSSsS',
    30: '......SSSsSSSSSsSSSSSsSS',
    31: '........SSsSSSSsSSSSsSS',
    32: '........SSSSSSSsSSSSSSS',
    33: '........SSSSSSSsSSSSSS',
    34: '.........SSSSSSsSSSSSS',
    35: '..........SSSSSsSSSSSS',
    36: '..........SSSSSsSSSSSS',
    37: '..........SSSSSSSSSSSS',
    38: '..........SSSSSSSSSSSS',
    39: '........BLBLBLBLBLBLBL',
    40: '........BBBBBBBBBBBBBB',
    41: '.......BBBBBBBBBBBBBBDD',
    42: '......BBBBBBBBBBBBBBBDD',
    43: '......BBBBBBBBBBBBBBBBDD',
    44: '......BBBBBBBBBBBBBBBBDD',
    45: '......BBBBBBBBBBBBBBBBBDD',
    46: '......BBBBBBBBBBBBBBBBBBDD',
    47: '......BBBBBBBBBBBBBBBBBBDD',
    48: '......BBBBBBBBBBBBBBBBBBDD',
    49: '......BBBBBBBBB.BBBBBBBBDD',
    50: '......BBBBBBBB...BBBBBBBDD',
    51: '......BBBBBBB.....BBBBBBDD',
    52: '......LLBBBD......LLBBBBDD',
    53: '......SSSs..........SSSSs',
    54: '......SSss..........SSSSs',
    55: '......kkkk..........SSSSs',
    56: '.....kkkkk..........SSSss',
    57: '......kkkk..........kkkkkk',
    58: '......kkk...........kkkkkkk',
    59: '....................kkkkkkkk',
    60: '....................kkkkkkkk',
}


def guard_px():
    return win_px(GUARD)


# ---- the parts, as they sit in the guard (brawl registration: ground line on y 61)
def head():
    """Hair, headband with its knot and tails, ears and nape: rows 12-24, x 22-35."""
    return region(guard_px(), 12, 24, 22, 35)


def lower_back():
    """The back below the shoulders, spine and shoulder-blade ends, lats to the waist: rows 29-38."""
    return region(guard_px(), 29, 38, 22, 39)


def shorts():
    return region(guard_px(), 39, 52)


def legs():
    """Legs and boots, his stance: left foot forward (sole row 58), right foot back (rows 59-60)."""
    return region(guard_px(), 53, 60)


# ---- the full slip: the guard's upper body sheared over, 10 at the shoulders tapering to 2 at the
# waist, and dropped two rows (the approved 1x slip's 5 / 4 / 3 / 2 / 1 and 1, doubled and smoothed)
SLIP_DX = {26: 10, 27: 9, 28: 9, 29: 8, 30: 7, 31: 6, 32: 6, 33: 5, 34: 4, 35: 3, 36: 3, 37: 2, 38: 2}


def slip_px(side, waist=39, drop=2):
    g = guard_px()
    out = {}
    for (x, y), k in g.items():
        if y < waist:
            dx = SLIP_DX.get(y, 10 if y < 26 else 2)
            out[(x + side * dx, y + drop)] = k
    for (x, y), k in g.items():
        if y >= waist:
            out[(x, y)] = k
    return out


# ---- the parry snap: the bounce body (head, back and shorts two rows lower, the legs two rows
# shorter, the soles where they were), both gloves thrust up together just over the head, forearms
# rising from elbows flared at the shoulders. Gloves' top edge on row 9, centred on x 31.
PARRY_ARMS = {
    9:  '...........LB....BL',
    10: '..........LLBB..BBLL',
    11: '..........LBBB..BBBL',
    12: '..........BBBB..BBBB',
    13: '..........BBBD..DBBB',
    14: '...........DD....DD',
    15: '..........Ss......sS',
    16: '.........SSs......sSS',
    17: '........SSs........sSS',
    18: '........SSs........sSS',
    19: '.......SSs..........sSS',
    20: '.......SSs..........sSS',
    21: '.......SSs..........sSS',
    22: '.......SSs..........sSS',
    23: '.......SSs..........sSS',
    24: '.......SSSs........sSSS',
    25: '......SSSSs........sSSSS',
    26: '......SSSSS........SSSSS',
    27: '.....SSSSSs........sSSSSS',
    28: '.....SSSSS..........SSSSS',
}


def parry_px():
    g = guard_px()
    out = {}
    out.update(moved(region(g, 25, 52, 22, 41), 0, 2))     # back and shorts, without the guard's arms
    out.update(win_px(PARRY_ARMS))
    out.update(region(g, 55, 60))                           # the soles stay put; rows 53-54 go
    out.update(moved(head(), 0, 2))
    return out


# ---- the other seven columns, built exactly as their approved 1x frames were

def bounce_px():
    """1 GUARD BOUNCE: everything above the knees two rows lower, the legs two rows shorter, the
    soles where they were (the approved 1x bounce, doubled)."""
    g = guard_px()
    out = moved(region(g, 12, 52), 0, 2)
    out.update(region(g, 55, 60))
    return out


SLIP_HALF_DX = {26: 6, 27: 5, 28: 5, 29: 4, 30: 4, 31: 3, 32: 3, 33: 2, 34: 2, 35: 1, 36: 1, 37: 0, 38: 0}


def slip_half_px(side, waist=39):
    """2 / 4 SLIP HALF WAY: the guard's upper body sheared 6 at the shoulders to 0 at the waist, not
    dropped (the approved 1x half slip's 3 / 2 / 1 / 0, doubled and smoothed)."""
    g = guard_px()
    out = {}
    for (x, y), k in g.items():
        if y < waist:
            out[(x + side * SLIP_HALF_DX.get(y, 6 if y < 26 else 0), y)] = k
    for (x, y), k in g.items():
        if y >= waist:
            out[(x, y)] = k
    return out


# the bare upper back (shoulders without arms), brawl registration
UPPER_BARE = {
    25: '.......SSS..SSssSS..SSS',
    26: '......SSSSS.SSssSS.SSSSS',
    27: '......SsSSSSSSSsSSSSSSsS',
    28: '......SSsSSSSSSsSSSSSsSS',
}


def bare_body():
    """The guard's body without its arms: bare shoulders, back, shorts and legs."""
    g = guard_px()
    out = win_px(UPPER_BARE)
    out.update(region(g, 29, 38, 22, 39))
    out.update(region(g, 39, 60))
    return out


# 7 PARRY ABSORB: the snap's guard driven two rows down onto the head, the body sunk with it (the back
# two rows shorter, the knees soft), the elbows spread wide under the weight.
ABSORB_ARMS = {
    11: '...........LB....BL',
    12: '..........LLBB..BBLL',
    13: '..........LBBB..BBBL',
    14: '..........BBBB..BBBB',
    15: '..........BBBD..DBBB',
    16: '...........DD....DD',
    17: '.........SSs......sSS',
    18: '........SSs........sSS',
    19: '.......SSs..........sSS',
    20: '......SSs............sSS',
    21: '......SSs............sSS',
    22: '.....SSs..............sSS',
    23: '.....SSs..............sSS',
    24: '.....SSss.............sSS',
    25: '.....SSSss...........sSSS',
    26: '.....SSSSs..........sSSSS',
    27: '.....SSSSS..........SSSSS',
    28: '......SSSSs........sSSSS',
    29: '......SSSSS........SSSSS',
    30: '.......SSSS........SSSS',
}


def absorb_px():
    g = guard_px()
    back = region(g, 25, 38, 22, 41)
    back = {(x, y + (2 if y < 33 else 0)): k for (x, y), k in back.items() if y not in (33, 34)}
    out = moved(back, 0, 2)                     # the back sunk two rows and two rows shorter
    out.update(win_px(ABSORB_ARMS))
    out.update(moved(region(g, 39, 52), 0, 2))  # the shorts on the bounce
    out.update(region(g, 55, 60))
    out.update(moved(head(), 0, 4))
    return out


# 8 HIT LANDS: the head snapped back into the shoulders (four rows down, two right) with the tails
# whipping up off it, the guard knocked open: the left arm flung high, the right thrown out wide.
HIT_ARMS = {
    9:  '.....LB',
    10: '....LLBB',
    11: '....LBBB',
    12: '....BBBB',
    13: '....BBBD',
    14: '.....DDS',
    15: '......SSs',
    16: '.......SSs',
    17: '........SSs',
    18: '.........SSs',
    19: '..........SSs',
    20: '...........SSs',
    21: '............SSs.............................BL',
    22: '.............SSs...........................BBLL',
    23: '..............SSs.......SSSSSSSSSSSSSSSSSSSBBBL',
    24: '...............SSS......SSSSSSSSSSSSSSSSSSSBBBB',
    25: '...............SSS......sssssssssssssssssssDBBD',
    26: '................S.......sssss...............DD',
}
HIT_TAILS = {
    17: '.........R',
    18: '..........R',
    19: '...........RR',
    20: '.............R',
}


def hit_px():
    out = bare_body()
    out.update(win_px(HIT_ARMS, win=6))
    hd = {p: k for p, k in head().items() if not (p[0] <= 25 and k == 'R')}     # the tails come off
    out.update(moved(hd, 2, 4))
    out.update(win_px(HIT_TAILS, win=16))
    return out


# 9 HIT REEL: hunched over, the head bowed (the crown showing, the knot's tails hanging), the shoulders
# up round it, the knees buckled (the bounce), both gloves dragged back up either side of the head.
REEL_HEAD = {
    22: '.............k..k',
    23: '............kkkkkk',
    24: '...........kkkkkkkk',
    25: '..........kkkkkkkkkk',
    26: '..........kkkkkkkkkk',
    27: '..........kkkkkkkkkk',
    28: '..........kkkkkkkkkk',
    29: '..........RRRRRRRRRR',
    30: '..........RRRRRRRRRR',
    31: '..........kkkkkRRRkk',
    32: '...........kkkkRkRk',
    33: '............kkkk.RR',
    34: '...................R',
}
REEL_ARMS = {
    25: '.........................BL',
    26: '........................BBLL',
    27: '...LB...................BBBL',
    28: '..LLBB..................BBBB',
    29: '..LBBB.SS...........SS..DBBD',
    30: '..BBBB.SSS.........SSS..sDDS',
    31: '..BBBD.SSSs.......sSSSs.sSSS',
    32: '...DD..SSSs.......sSSSSssSSS',
    33: '....SsSSSSs........sSSSSSSS',
    34: '....SSSsSSSSs.....sSSSSsSS',
    35: '......SSSSSSsSSSSsSSSSSSSS',
    36: '........SSSSSSsSSSSSSSSS',
}


def reel_px():
    g = guard_px()
    back = region(g, 29, 38, 22, 39)
    out = moved({p: k for p, k in back.items() if p[1] not in (33, 34)}, 0, 2)   # a hunch: two rows shorter
    out = {(x, y + (2 if y < 35 else 0)): k for (x, y), k in out.items()}
    out.update(win_px(REEL_ARMS, win=16))
    out.update(moved(region(g, 39, 52), 0, 2))
    out.update(region(g, 55, 60))
    out.update(win_px(REEL_HEAD, win=16))
    return out


CELLS = [('guard', guard_px), ('guard', bounce_px),
         ('slip_left', lambda: slip_half_px(-1)), ('slip_left', lambda: slip_px(-1)),
         ('slip_right', lambda: slip_half_px(1)), ('slip_right', lambda: slip_px(1)),
         ('parry', parry_px), ('parry', absorb_px),
         ('hit', hit_px), ('hit', reel_px)]

# The head core's centre per column (the guard's is x 26-35 rows 13-24 -> (31, 19)), moved as each
# column's construction moves it; the reel's is its own bowed head (x 26-35, rows 23-34). These are
# the placeholder's own numbers: the native pass moved no head.
HEAD_CENTRES = [(31, 19), (31, 21), (25, 19), (21, 21), (37, 19), (41, 21), (31, 21), (31, 23), (33, 23), (31, 29)]
# The parry's gloves: top edge and centre line, where the straight meets them.
PARRY_CONTACTS = {6: (31, 9), 7: (31, 11)}

APPROVAL = [(0, 'guard', guard_px), (3, 'slip_left full', lambda: slip_px(-1)), (6, 'parry snap', parry_px)]


def audit2x(px):
    """gb_player's audit, with the 2x cell's bounds."""
    a = {k: v for k, v in G.audit(px).items() if k != 'outside'}
    xs = [x for x, y in px]
    ys = [y for x, y in px]
    if min(xs) < 0 or max(xs) >= G2.W2 or min(ys) < 0 or max(ys) >= G2.H2:
        a['outside'] = [(min(xs), min(ys), max(xs), max(ys))]
    return a
