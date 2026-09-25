"""The few pieces of Jordan's fight rig (art_source/jordan_anims, janim_*) the juggle uses, frozen here.

The juggle must not import the fight rig: a later change there would silently change the shipped
juggle. These are copied from it and depend only on the approved rigs (art_source/jordan_redesign via
art_source/jordan_v2). From the rig as the juggle used it on 2026-09-23:

  tilt2, close_gaps   janim_base's small-turn shear and keyline sealer
  write_sheet         janim_base's sheet writer (temp build, Aseprite round-trip, os.replace)
  heads               janim_heads' head space, over(), and the PAIN / LAUGH / DAZE face rows (only
                      rows 22 down are ever used: a hair map goes over every face)
  HAND_OPEN           janim_hit's splayed hand
  the box             janim_box's map and its two pieces of art (the star, the plumber); the juggle
                      only ever holds the box square to his body, so only the 0-degree placement

From its v2 set as SHIPPED on 2026-09-24 (jordan_hit, jordan_defeat, jordan_taunt; the rig was checked
to rebuild those three PNGs exactly before these were copied):

  FLOPPED_V2          janim_heads' quiff knocked flat in v2's greasy hair, worn by its hit and defeat
                      heads (FLOPPED: pain, wince, daze, droop)
  BOX_TOP_LEFT        janim_taunt's held-high box, (66, 3): 2 texels right of the 09-23 (64, 3)
  TAUNT_*             janim_taunt.far_arm_up's stick arm and far_raised_sleeve's bunched sleeve
"""
import math
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
_V2_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jordan_v2')
if _V2_DIR not in sys.path:
    sys.path.insert(0, _V2_DIR)

import jv2_base as V2B    # noqa: E402
import jv2_head as V2H    # noqa: E402
from PIL import Image     # noqa: E402

jordan = V2B.jordan
rig_head = V2B.rig_head
rig_torso = V2B.rig_torso
kit = V2B.kit
lib = V2B.lib
amap = V2B.amap
shift = V2B.shift
rows_of = V2B.rows_of
pixel_diff = V2B.pixel_diff
ANCHOR_SHIFT = V2B.ANCHOR_SHIFT
ASEPRITE = V2B.ASEPRITE
ALLOWED = V2B.ALLOWED


# ------------------------------------------------------------------------------ janim_base helpers
def tilt2(part, deg, pivot, order='xy'):
    """A small turn (clockwise positive) as one row-shear and one column-shear, so every row and
    every column of the part stays intact and features step instead of smearing. A pixel that
    neither shear covers (where a row step meets a column step) is filled from the source at the
    inverse-turned spot."""
    th = math.radians(deg)
    t = math.tan(th)
    px_, py_ = pivot

    def r(v):
        return int(math.floor(v + 0.5))

    out = {}
    for (x, y), k in part.items():
        if order == 'xy':
            x1 = x + r(-t * (y + 0.5 - py_))
            y1 = y + r(t * (x1 + 0.5 - px_))
        else:
            y1 = y + r(t * (x + 0.5 - px_))
            x1 = x + r(-t * (y1 + 0.5 - py_))
        out[(x1, y1)] = k
    c, s = math.cos(th), math.sin(th)
    xs = [q[0] for q in out]
    ys = [q[1] for q in out]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in out:
                continue
            if sum(n in out for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))) >= 3:
                dx, dy = x + 0.5 - px_, y + 0.5 - py_
                sx_, sy_ = c * dx + s * dy + px_, -s * dx + c * dy + py_
                k = part.get((int(math.floor(sx_)), int(math.floor(sy_))))
                if k:
                    out[(x, y)] = k
    return out


def close_gaps(part):
    """Keyline any transparent spot a coloured pixel of `part` touches (4-neighbours), in place."""
    add = set()
    for (x, y), k in part.items():
        if k == 'k':
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in part:
                add.add(q)
    for q in add:
        part[q] = 'k'
    return part


def write_sheet(name, im, out_dir):
    """Write <out_dir>/<name>.png in one go (built in a temp folder, then os.replace), save the
    .aseprite beside it the same way, and check the .aseprite re-exports to exactly the PNG's pixels
    (imgdiff.pixel_diff: alpha everywhere and colour wherever a pixel shows). Returns the paths and
    the round-trip result of the files where they landed (None = identical)."""
    tmp = tempfile.mkdtemp(prefix='jj_')
    tmp_png = os.path.join(tmp, name + '.png')
    tmp_ase = os.path.join(tmp, name + '.aseprite')
    im.save(tmp_png)
    subprocess.run([ASEPRITE, '-b', tmp_png, '--save-as', tmp_ase], check=True, capture_output=True)
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([ASEPRITE, '-b', tmp_ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(tmp_png), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    os.replace(tmp_png, png)
    os.replace(tmp_ase, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    return png, ase, pixel_diff(Image.open(png), Image.open(back2))


# ------------------------------------------------------------------------------ janim_heads
X0, Y0 = rig_head.X0, rig_head.Y0
IDLE = rows_of(rig_head.HEAD)
SHOUT = IDLE[:22 - Y0] + rows_of(rig_head.SHOUT)


def _check(rows):
    for i, r in enumerate(rows):
        if len(r) != 23:
            raise ValueError('head row %d is %d wide: %r' % (Y0 + i, len(r), r))
    return rows


def over(base, repl):
    """base rows with {y: row} replacements (rows may run past the base's end)."""
    rows = list(base)
    for y, r in repl.items():
        i = y - Y0
        while len(rows) <= i:
            rows.append('.' * 23)
        rows[i] = r.replace(' ', '')
    return _check(rows)


# Laughing: brows up, eyes squeezed into arcs, the jaw dropped two rows on a wide open mouth.
LAUGH = over(SHOUT, {
    21: ".kijj ihiii iiide djiii ik.",
    22: ".kijj idhhh hhhhd echhh hk.",
    23: ".kiji hcccc cccdd edccc ck.",
    24: ".kdci icckk kkcdd edckc ck.",
    25: "kdbci ickde edkdd eckdk ck.",
    26: "kdaci jccdd ddcdd eccdc ck.",
    27: "kdbci jcdcc ccddd ebccd ck.",
    31: "...ki jjclj dkWWW WWWkj ik.",
    32: "...kh icjjc jkaaa aaakc ik.",
    33: "...kh icjjc jkapp ppakc ik.",
    34: "...kh icjjc jippd dppic ik.",
    35: "....k hijcj ijihi jljic ik.",
    36: ".....k hijj ljiij ljiih k..",
    37: "......k hhi ijjjj jiiih k..",
    38: ".......k hh iiiii iiihk ...",
    39: "........ kk kkkkk kkkk. ...",
})

# Hit, the moment it lands: eyes squeezed shut to > <, brows crushed down, teeth clenched.
PAIN = over(SHOUT, {
    24: ".kdci icccb bhhhh dhhbb ck.",
    25: "kdbci ickkc ccddd ecckk ck.",
    26: "kdaci jccck kkddd eckcc ck.",
    27: "kdbci jcckk ccddd ebckk ck.",
    31: "...ki jjclk kWWWW WWWkk ik.",
    32: "...kh icjjk kkkkk kkkkc ik.",
    33: "...kh icjjc jippd dppic ik.",
})

# Staggering: eyes wide and wall-eyed, the jaw hanging open on a gasp.
DAZE = over(IDLE, {
    26: "kdaci jcchW WWWdd ecWWh ck.",
    31: "...ki jjclj dbkkk kkbij ik.",
    32: "...kh icjjc jbkaa akbic ik.",
    33: "....k hijcj jijkk kjjic ik.",
})

HEADS = {'idle': IDLE, 'shout': SHOUT, 'laugh': LAUGH, 'pain': PAIN, 'daze': DAZE}


def head_rows(name):
    return HEADS[name]


# ------------------------------------------------------------------------------ janim_hit, janim_taunt
HAND_OPEN = rows_of([
    ".k.....",
    "kek.k..",
    ".kdkek.",
    "kedddkk",
    ".kcdddk",
    "kecdcck",
    ".kkkkk.",
])

# ------------------------------------------------------------------------------ the shipped v2 set
# The quiff knocked flat, in v2's greasy hair (janim_heads.FLOPPED_V2): the crest is gone, the top of
# the head sits low and round, the front of the quiff flopped forward over his forehead, a big oily
# lock hanging off the far side down to the brow; the back of the head, the tuft and the rat-tail are
# v2's own. Head space as v2's hair map: columns x = 35..61, rows from y = 7 ('.' is transparent).
FLOPPED_V2 = [
    "..... ..... ..... ..... ..... ..",       # 7
    "..... ..... ..... ..... ..... ..",       # 8
    "..... ..... ..... ..... ..... ..",       # 9
    "..... ..... ..... ..... ..... ..",       # 10
    "..... ..... ..... ..... ..... ..",       # 11
    "..... ..... .kkkk kkk.. ..... ..",       # 12
    "..... k...k kAYAh jAYkk ..... ..",       # 13
    "....k jkkkA YAhjl jhAYA kk... ..",       # 14
    "..... kAmhi ljhil jhWlA YAkk. ..",       # 15
    "....k kmjhi lWhim jhilj hlAk. ..",       # 16
    "...kj lihjW ihjmi hjlih jWlik ..",       # 17
    "..kih jijii hiiji ihijl mljih k.",       # 18
    ".kiki iWijh cciid kilmA mljih k.",       # 19
    ".kjki iijhd eeeie dkjAl jihih k.",       # 20
    ".kiki jjihd eeeeh edkji ljihk ..",       # 21
]
# the fight rig's heads that wear it
FLOPPED = {'pain', 'wince', 'daze', 'droop'}


def flopped_hair():
    """janim_heads._flopped_hair: the flopped map over v2's hair space, with the rat-tail's tip."""
    rows = rows_of(FLOPPED_V2)
    for i, r in enumerate(rows):
        if len(r) != 27:
            raise ValueError('flopped row %d is %d wide' % (V2H.HY0 + i, len(r)))
    part = amap(rows, V2H.HX0, V2H.HY0)
    part.update(V2H.TAIL_TIP)
    return part


# The box held high as the shipped v2 taunt holds it, before the frame's bob (build).
BOX_TOP_LEFT = (66, 3)
# janim_taunt.far_arm_up: the raised stick arm, shoulder to bony elbow to the wrist under the hand.
TAUNT_SHOULDER = (58.4, 47.5)
TAUNT_ELBOW = (63.6, 37.4)
TAUNT_RADII = ((1.55, 1.45), (1.45, 1.3))       # upper arm, forearm
TAUNT_KNOB = (63.6, 37.6, 1.8)
TAUNT_WRIST = (1.4, 22.8)                       # from BOX_TOP_LEFT: the wrist under the hand
# the raised arm catches the light on its inner side: its base tone lit at x <= 63, y <= 40
TAUNT_INNER_LIT = (63, 40)
# janim_taunt.far_raised_sleeve: v2's raised sleeve (jv2_body.raised_sleeve) mirrored onto his far
# shoulder (x -> 99 - x), fallen back and bunched round the top of the arm; its fold, and its opening
# rows round the arm (the trim on row 41, the dark inside on 42, the trim across on 43)
TAUNT_SLEEVE = [(99 - x, y) for (x, y) in
                [(34.6, 43.6), (44.6, 43.6), (45, 46.4), (43.4, 49.2), (40.2, 50.4), (36.6, 49.4), (34.8, 46.6)]]
TAUNT_SLEEVE_FOLD = [(62, 45), (59, 48), (58, 49)]
TAUNT_SLEEVE_OPENING = ((41, (56, 63), '1'), (42, (55, 64), 'v'))
TAUNT_SLEEVE_TRIM = (43, 55, 65)                # row, x from, x to (exclusive): x 55..64
TAUNT_THROUGH_ROWS = (41, 42)                   # the arm runs on through the opening on these rows


# ------------------------------------------------------------------------------ janim_box
BW, BH = 15, 21
MAP = rows_of(jordan.BOX)
assert len(MAP) == BH and all(len(r) == BW for r in MAP)

# The art on the box: the star (cols 4..10, rows 1..5) and the plumber (cols 3..11, rows 8..16),
# every non-fill pixel of those boxes.
STAR_BOX = (4, 1, 10, 5)
FIG_BOX = (3, 8, 11, 16)


def _art(box, fillkeys):
    c0, r0, c1, r1 = box
    return {(c, r): MAP[r][c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if MAP[r][c] not in fillkeys}


STAR_ART = _art(STAR_BOX, 'R')
FIG_ART = _art(FIG_BOX, 'wx')


def box_at(rows, top_left):
    """The box drawn from `rows` (MAP, or a re-lit copy of it) with its top-left on build point
    `top_left`: janim_box.box_at(0, (0, 0), top_left)."""
    x0, y0 = top_left
    return {(x0 + c, y0 + r): k for r, row in enumerate(rows) for c, k in enumerate(row) if k != '.'}


def _selftest():
    ok = box_at(MAP, (61, 25)) == jordan.box_part(0, 0)
    print('box at (61, 25) vs the rig box:', 'identical' if ok else 'DIFFERENT')
    head_ok = all(len(r) == 23 for rows in HEADS.values() for r in rows)
    print('head rows 23 wide:', head_ok)
    return ok and head_ok


if __name__ == '__main__':
    _selftest()
