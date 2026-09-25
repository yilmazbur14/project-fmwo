"""The player's Glass Row poses: Assets/Characters/MainPlayer/player_glass_row.png.

18 columns x 4 rows of 32x32 in player_4dir_sheet.png's row order (DOWN, UP, LEFT, RIGHT). Only row 1
(UP, the back view) is drawn; the exporter copies it into rows 0, 2 and 3, because the player is
held facing up the whole time these poses play.

His own style, measured off player_4dir_sheet.png row 1 and player_guard_break.png, NOT Matt's:
seven colours (below), no keyline at all (black is only his hair and his shoes), flat blocks with the
darker skin ticking the spine, the shoulder blades and the shaded side of each limb, gloves as blue
blocks lit on the upper left, shorts lit along the waistband and shaded down the right. Soles on row
28, centred on column 16, as the 4-dir UP idle.

Each pose is a hand-drawn grid, one character per texel:
    k black (hair, shoes)   D dark blue   B blue   L light blue   R red (headband)
    s shaded skin           S skin        . empty
"""
import os

from PIL import Image

import mg_base as M
from mg_base import B

PAL = {
    'k': (0, 0, 0, 255), 'D': (22, 47, 187, 255), 'B': (36, 100, 189, 255), 'L': (56, 131, 201, 255),
    'R': (172, 50, 50, 255), 's': (172, 113, 79, 255), 'S': (215, 152, 100, 255),
}
SHEET_4DIR = os.path.join(M.PLAYER_DIR, 'player_4dir_sheet.png')
GUARD_BREAK = os.path.join(M.PLAYER_DIR, 'player_guard_break.png')
KEYS = {v[:3]: k for k, v in PAL.items()}


def grid(lines, y0=0):
    """Rows of 32 (spaces ignored) starting at row y0 -> {(x, y): key}."""
    px = {}
    for j, ln in enumerate(lines):
        ln = ln.replace(' ', '')
        assert len(ln) == 32, (y0 + j, len(ln), ln)
        for x, ch in enumerate(ln):
            if ch != '.':
                px[(x, y0 + j)] = ch
    return px


def image(px):
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < 32 and 0 <= y < 32:
            im.putpixel((x, y), PAL[k])
    return im


def from_sheet(path, col, row):
    im = Image.open(path).convert('RGBA').crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))
    px = {}
    for y in range(32):
        for x in range(32):
            c = im.getpixel((x, y))
            if c[3]:
                px[(x, y)] = KEYS[c[:3]]
    return px


def up_idle():
    return from_sheet(SHEET_4DIR, 0, 1)


# ------------------------------------------------------------------ building blocks
# Every pose is assembled from the shipped UP idle's own parts, moved, plus arms and gloves painted
# per pose in his style: a limb is two texels wide, lit on its left (S) and shaded on its right (s);
# a glove is a blue block lit top-left (L) and shaded bottom-right (D).
def region(px, x0, y0, x1, y1):
    return {(x, y): k for (x, y), k in px.items() if x0 <= x <= x1 and y0 <= y <= y1}


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


IDLE = None


def idle():
    global IDLE
    if IDLE is None:
        IDLE = up_idle()
    return IDLE


def head(dx=0, dy=0):
    """Hair, headband (with its knot and tails) and nape: idle rows 4-9, gloves left out."""
    h = region(idle(), 11, 4, 17, 9)
    return moved({p: k for p, k in h.items() if k not in 'BLD'}, dx, dy)


def back(dx=0, dy=0, arms_out=True):
    """Shoulders and back, idle rows 9-16; where the idle's guard gloves sat, bare shoulders."""
    b = region(idle(), 11, 9, 19, 16)
    b = {p: k for p, k in b.items() if k not in 'BLDk'}
    for (x, y) in ((11, 9), (12, 9), (11, 10), (12, 10)):
        b[(x, y)] = 'S' if x == 11 else 's'
    for (x, y) in ((18, 9), (19, 9), (18, 10), (19, 10)):
        b[(x, y)] = 's' if x == 19 else 'S'
    b[(13, 10)] = 'S'
    b[(17, 10)] = 's'
    return moved(b, dx, dy)


def lower(dx=0, dy=0):
    """Shorts, legs and shoes: idle rows 17-28."""
    return moved(region(idle(), 0, 17, 31, 28), dx, dy)


def glove(x, y, right=False):
    """A 2x3 glove, lit top-left, shaded bottom-right."""
    rows = ['LB', 'BB', 'BD'] if not right else ['BL', 'BB', 'DD']
    return {(x + i, y + j): ch for j, r in enumerate(rows) for i, ch in enumerate(r)}


def limb(points, px):
    """A two-texel limb along the given texels: each texel and the one to its right, lit then shaded."""
    for (x, y) in points:
        px[(x, y)] = 'S'
        px[(x + 1, y)] = 's'


def compose(*parts):
    out = {}
    for p in parts:
        out.update(p)
    return out


# ------------------------------------------------------------------ poses (UP, the back view)
def slump():
    """The guard-break sheet's own back view (column 0 of its UP row): slumped, knees loose, arms
    hanging with the gloves at his hips. The dizzy loop is this body with the head lolling."""
    return from_sheet(GUARD_BREAK, 0, 1)


def ears(shake=0, sink=2):
    """Columns 7-9: EARS. Hunched (the head sunk two texels between raised shoulders), both gloves
    clamped over his ears, each arm a V from the shoulder out to a flared elbow and back up to the
    glove, knees braced. `shake` jitters everything above the waist by a texel."""
    s = shake
    # the shoulders ride up a texel; the waist stays on the shorts (the idle's waist row, so the
    # raised back never parts from the waistband)
    px = compose(lower(), moved(region(idle(), 11, 16, 19, 16), s, 0), back(s, -1), head(s, sink))
    # left arm: shoulder -> elbow (out and down) -> glove on the ear
    for (x, y, k) in ((10, 10, 'S'), (9, 11, 'S'), (8, 12, 's'), (9, 12, 's'), (8, 11, 'S'),
                      (10, 11, 's'), (9, 10, 's')):
        px[(x + s, y)] = k
    # right arm, mirrored in shape, lit on its left
    for (x, y, k) in ((20, 10, 's'), (21, 11, 's'), (22, 12, 's'), (21, 12, 'S'), (22, 11, 's'),
                      (20, 11, 'S'), (21, 10, 'S')):
        px[(x + s, y)] = k
    px.update(moved(glove(11, 6 + sink), s, 0))
    px.update(moved(glove(18, 6 + sink, right=True), s, 0))
    return px


def dizzy(k=0):
    """Columns 12-15: DIZZY. The slumped body, the head lolling round a small circle (k = 0..3:
    left, down, right, up) and the shoulders swaying after it."""
    base = slump()
    head_px = region(base, 0, 7, 31, 12)
    head_px = {p: q for p, q in head_px.items() if q in 'kR' or (11 <= p[0] <= 17 and p[1] <= 10)}
    body = {p: q for p, q in base.items() if p not in head_px}
    loll = [(-2, 0), (-1, 1), (2, 0), (1, -1)][k]
    sway = [-1, 0, 1, 0][k]
    upper = {p: q for p, q in body.items() if p[1] <= 16}
    lower_ = {p: q for p, q in body.items() if p[1] > 16}
    return compose(lower_, moved(upper, sway, 0), moved(head_px, loll[0] + sway, loll[1]))


# ------------------------------------------------------------------ hand-drawn grids
# Each grid row covers x 4..27 (24 texels) of the 32x32 cell; rows not listed are empty. Heads are
# the idle's own head, row for row, only moved; the neck notches either side of the nape (the
# idle's transparent texels at (13, 10) and (17, 10)) move with it.
def g24(rows):
    px = {}
    for y, r in rows.items():
        assert len(r) == 24, (y, len(r), r)
        for i, ch in enumerate(r):
            if ch != '.':
                assert ch in PAL, (y, ch)
                px[(4 + i, y)] = ch
    return px


def head_rows(dy):
    """The idle's head (rows 4-9) moved down dy rows, as grid rows (no gloves)."""
    rows = ['..........kkk...........', '.........kkkkk..........', '.......R.RRRRR..........',
            '........RkkRkk..........', '.........kkkkk..........', '.........skkks..........']
    return {4 + dy + j: r for j, r in enumerate(rows)}


def over(*grids):
    """Stack grid dicts: a later grid's texels win, its '.' keep what is below."""
    out = {}
    for g in grids:
        for y, r in g.items():
            base = out.get(y, '.' * 24)
            out[y] = ''.join(b if c == '.' else c for b, c in zip(base, r))
    return out


# the idle's shorts one row shorter (a knee bend), legs and shoes as the idle
LOWER_BENT = {
    18: '........BBLBLBL.........',
    19: '.......BBBBBBBBD........',
    20: '.......BBBBBBBBBD.......',
    21: '.......BBBBBBBBBD.......',
    22: '.......BBBB.BBBBD.......',
    23: '.......BBB...BBBD.......',
    24: '.......Ss.....SSs.......',
    25: '.......Ss.....SSs.......',
    26: '.......kk.....SSs.......',
    27: '.......kk.....kkk.......',
    28: '..............kkkk......',
}
# the lunge: left foot forward up the ring (sole on row 26), right leg driving back (sole on 28)
LOWER_LUNGE = {
    18: '........BBLBLBL.........',
    19: '.......BBBBBBBBD........',
    20: '.......BBBBBBBBBD.......',
    21: '......BBBBBBBBBBD.......',
    22: '......BBBBB.BBBBBD......',
    23: '......BBBB...BBBBD......',
    24: '......Ss.......SSs......',
    25: '.....kkk.......SSs......',
    26: '....kkkk........SSs.....',
    27: '................kkk.....',
    28: '................kkkk....',
}
# a wide squat, both soles planted on row 28
LOWER_WIDE = {
    18: '........BBLBLBL.........',
    19: '.......BBBBBBBBD........',
    20: '......BBBBBBBBBBD.......',
    21: '......BBBBBBBBBBD.......',
    22: '......BBBBB..BBBBD......',
    23: '......BBBB....BBBD......',
    24: '......Ss.......SSs......',
    25: '.....Ss.........Ss......',
    26: '.....Ss.........SSs.....',
    27: '....kkk.........kkk.....',
    28: '...kkkk.........kkkk....',
}
# the idle's back (rows 10-16) with the shoulders bare, placed from row `top`, kept to n rows by
# dropping the idle's middle rows (a crouch shortens the back)
BACK = ['.......SS.SsS.sS........', '.......SsSSsSSsS........', '.......SSsSsSsSS........',
        '........SSSsSSSS........', '........SSSsSSS.........', '.........SSsSSS.........',
        '.........SSSSSS.........']


KEEP = {7: (0, 1, 2, 3, 4, 5, 6), 6: (0, 1, 2, 3, 5, 6), 5: (0, 1, 2, 5, 6), 4: (0, 1, 5, 6)}


def back_rows(top, n=7):
    return {top + j: BACK[i] for j, i in enumerate(KEEP[n])}


# 0-1 ROOTED: the lunge, crouched two texels, gloves up; B heaves a texel on up the ring (the back
# stretching, the gloves pushed on) against the root
ROOTED_A = over(LOWER_LUNGE, back_rows(12, 6), head_rows(2), {
    10: '..............BB........',
    11: '.......BB.....BB........',
    12: '.......BB...............',
})
ROOTED_B = over(LOWER_LUNGE, back_rows(11, 7), head_rows(1), {
    8:  '..............BB........',
    9:  '.......BB.....BB........',
    10: '.......BB.....SS........',
})

# 2 BRACE: the wide squat, the head tucked three texels down, both gloves up high beside it, the
# elbows flared under them
BRACE = over(LOWER_WIDE, back_rows(13, 5), head_rows(3), {
    8:  '.......LB.....BL........',
    9:  '.......BB.....BB........',
    10: '.......BD.....DD........',
    11: '.......Ss.....sS........',
    12: '......SSs.....sSS.......',
    13: '......SsSSSsSSSsS.......',
})

# 3-5 KNOCKED BACK: the boom lands (head snapped back, gloves flung wide, heels skidding); carried
# back (leaning back, one glove up, one thrown out low, feet dragging); caught (dropped low, gloves
# hauled back up, knees soaking it up)
KNOCK_HIT = over(LOWER_BENT, back_rows(12, 6), head_rows(2), {
    6:  '....LB............BL....',
    7:  '....BB............BB....',
    8:  '....BD............DD....',
    9:  '......Ss.........sS.....',
    10: '.......Ss.......sS......',
    11: '.......Ss......sS.......',
    26: '......kkk.....SSs.......',
    27: '.....kkkk.....kkk.......',
})
KNOCK_SLIDE = over({
    18: '........BBLBLBL.....BL..',
    19: '.......BBBBBBBBD....BB..',
    20: '......BBBBBBBBBD....DD..',
    21: '......BBBBBBBBBBD.......',
    22: '......BBBBB.BBBBD.......',
    23: '......BBBB...BBBD.......',
    24: '......Ss......SSs.......',
    25: '.....Ss.......SSs.......',
    26: '.....Ss.......SSs.......',
    27: '....kkk.......kkk.......',
    28: '....kkkk......kkkk......',
}, head_rows(3), {
    7:  '...LB...................',
    8:  '...BB...................',
    9:  '...BD...................',
    10: '....Ss..................',
    11: '.....Ss.................',
    12: '......SS................',
    13: '.......SS.SsS.sSS.......',
    14: '.......SsSSsSSsSSs......',
    15: '........SSSsSSSS.sS.....',
    16: '........SSSsSSS...sS....',
    17: '.........SSSSSS....sS...',
})
KNOCK_CATCH = over(LOWER_WIDE, head_rows(4), {
    11: '..............BB........',
    12: '.......BB.....BB........',
    13: '.......BB.....SS........',
    14: '.......SsSsSsSsS........',
    15: '.......SSSSsSSSS........',
    16: '........SSSsSSS.........',
    17: '.........SSSSSS.........',
})

# 6 EARS IN: the yell hits; the shoulders jump, the head drops a texel and both gloves fly up to
# the ears, still a texel out and two above where they clamp, elbows flying out
EARS_IN = over(LOWER_BENT, back_rows(11, 7), head_rows(1), {
    5:  '......LB.......BL.......',
    6:  '......BB.......BB.......',
    7:  '......BD.......DD.......',
    8:  '.....Ss.........sS......',
    9:  '....Ss...........sS.....',
    10: '....SsS.........SsS.....',
    11: '.....sSSS.....SSSs......',
})

# 10-11 RESISTED: shrugging the yell off (chest up, arms flung down and out, fists clenched), then
# the hold: a double-biceps flex from behind
RESIST_BREAK = over(LOWER_WIDE, head_rows(-1), {
    8:  '.......SS.....SS........',
    9:  '......SsSSSsSSSsS.......',
    10: '.....SsSSSsSsSSSsS......',
    11: '....Ss.SSSSsSSSS.sS.....',
    12: '...Ss...SSSsSSSS..sS....',
    13: '..Ss....SSSsSSS....sS...',
    14: '.LB.....SSSsSSS.....BL..',
    15: '.BB......SSsSSS.....BB..',
    16: '.BD......SSSSSS.....DD..',
    17: '.........SSSSSS.........',
})
RESIST_FLEX = over(LOWER_WIDE, head_rows(-1), {
    3:  '.LB.................BL..',
    4:  '.BB.................BB..',
    5:  '.BD.................DD..',
    6:  '.Ss.................sS..',
    7:  '.Ss.................sS..',
    8:  '.SsSSSSSS.....SSSSSSsS..',
    9:  '..sSSSSSSSSsSSSSSSSSs...',
    10: '.......SSSSsSSSSS.......',
    11: '.......SSsSsSsSSS.......',
    12: '........SSSsSSSS........',
    13: '........SSSsSSSS........',
    14: '........SSSsSSS.........',
    15: '.........SSsSSS.........',
    16: '.........SSSSSS.........',
    17: '.........SSSSSS.........',
})

# 16-17 GLASS HIT: jolted onto his toes with the gloves thrown up (soles on row 27), then the hop:
# off the glass, the left knee tucked up, arms windmilling (soles on rows 21 and 25)
GLASS_JOLT = over({
    16: '........BBLBLBL.........',
    17: '.......BBBBBBBD.........',
    18: '.......BBBBBBBBD........',
    19: '.......BBBBBBBBBD.......',
    20: '.......BBBBBBBBBD.......',
    21: '.......BBBB.BBBBD.......',
    22: '.......BBB...BBBD.......',
    23: '........Ss....SSs.......',
    24: '........Ss....SSs.......',
    25: '........Ss....SSs.......',
    26: '........kk....kkk.......',
    27: '........kk....kkk.......',
}, back_rows(9, 7), head_rows(-1), {
    0:  '......LB.......BL.......',
    1:  '......BB.......BB.......',
    2:  '......BD.......DD.......',
    3:  '......Ss.......sS.......',
    4:  '......Ss.......sS.......',
    5:  '......Ss.......sS.......',
    6:  '.......Ss.....sS........',
    7:  '.......Ss.....sS........',
    8:  '.......SS.....SS........',
})
GLASS_HOP = over({
    14: '........BBLBLBL.........',
    15: '.......BBBBBBBD.........',
    16: '.......BBBBBBBBD........',
    17: '.......BBBBBBBBBD.......',
    18: '.......BBBBBBBBBD.......',
    19: '.....SsBBBB.BBBBD.......',
    20: '....kkkBBB...BBBD.......',
    21: '....kkkk......SSs.......',
    22: '..............SSs.......',
    23: '..............SSs.......',
    24: '..............kkk.......',
    25: '..............kkkk......',
}, back_rows(7, 7), head_rows(-3), {
    0:  '..LB....................',
    1:  '..BB....................',
    2:  '..BD....................',
    3:  '...Ss...................',
    4:  '....Ss..................',
    5:  '.....Ss.................',
    6:  '......Ss......sSS.......',
    7:  '..............sSSS......',
    8:  '.................sSS....',
    9:  '...................sBL..',
    10: '....................BB..',
    11: '....................DD..',
})


# ------------------------------------------------------------------ the sheet
def columns():
    """(column, name, pixels, timing) for row 1; the exporter copies row 1 into rows 0, 2 and 3."""
    return [
        (0, 'rooted', g24(ROOTED_A), '0.20 loop'), (1, 'rooted', g24(ROOTED_B), '0.20 loop'),
        (2, 'brace', g24(BRACE), '0.12'),
        (3, 'knocked', g24(KNOCK_HIT), '0.06'), (4, 'knocked', g24(KNOCK_SLIDE), '0.08'),
        (5, 'knocked', g24(KNOCK_CATCH), '0.08'),
        (6, 'ears_in', g24(EARS_IN), '0.08'),
        (7, 'ears', ears(0), '0.07 loop'), (8, 'ears', ears(1), '0.07 loop'),
        (9, 'ears', ears(-1), '0.07 loop'),
        (10, 'resisted', g24(RESIST_BREAK), '0.12'), (11, 'resisted', g24(RESIST_FLEX), 'hold'),
        (12, 'dizzy', dizzy(0), '0.14 loop'), (13, 'dizzy', dizzy(1), '0.14 loop'),
        (14, 'dizzy', dizzy(2), '0.14 loop'), (15, 'dizzy', dizzy(3), '0.14 loop'),
        (16, 'glass', g24(GLASS_JOLT), '0.10'), (17, 'glass', g24(GLASS_HOP), '0.20'),
    ]


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
    """What a player frame must not ship with: more than one piece (a body split by a transparent
    row), pinholes other than the idle's own neck notches, lone texels, colours outside his seven."""
    lone = [p for p in px if not any((p[0] + dx, p[1] + dy) in px
                                     for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)]
    holes = [h for h in pinholes(px) if h not in notches(px)]
    keys = sorted(set(px.values()) - set(PAL))
    return {'pieces': components(px) - 1, 'holes': holes, 'lone': lone, 'keys': keys}


def black(px):
    return sum(1 for k in px.values() if k == 'k') / len(px)


if __name__ == '__main__':
    import mi_view as V
    ims = []
    for c, name, px, t in columns():
        bad = {k: v for k, v in audit(px).items() if v}
        ims.append(V.label(V.up(image(px), 8), '%d %s %.1f%%%s' % (c, name, 100 * black(px), ' BAD' if bad else '')))
        if bad:
            print(c, name, bad)
    print(V.save(V.col([V.row(ims[:9], gap=6), V.row(ims[9:], gap=6)], gap=6), 'player_cols_8x.png',
                 sub='../matt_glass_art'))
