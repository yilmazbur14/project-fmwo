"""Jordan v2's body: skeletal and gangly, SKINNY, in a tee that clings to him.

  - stick arms and legs with bony elbows and knees, knock-kneed;
  - a slump: a thin neck craning forward, the head pushed forward and sunk down into narrow, sloped
    shoulders;
  - SKINNIER since 2026-09-28 (the user: "i want jordan even skinnier and his shirt even more
    fitted", approved the same day as "approve the skinnier one"; approval pass
    art_source/jordan_fit/skinny): arms about a pixel thinner (limb() takes ARM_THIN off every radius
    its callers pass, so no joint moved), the chest 15px and the waist 13px, thinner jeans (row spans,
    below), tighter and shorter sleeves;
  - the Peach tee (the approved print, cropped only at its two side OUTLINE columns, which on the
    15px chest would double the tee's keyline) tight on his thin chest, tapering in under the print
    to his narrow waist, the hem level on his hips at row 69 with one rumple; short sleeves hugging
    the top of each stick arm (a snug cuff ridden up the raised arm in the fist-pump); the stretched
    collar still gaping round the neck. The fitted tee before it (19px, 2026-09-28) and the sack
    before that are in git history; art_source/jordan_fit keeps both approval passes;
  - dark jeans on thin legs, bunched in stacks at the ankles over the (approved) sneakers.

Everything is placed in the rig's build coordinates, like art_source/jordan_redesign/jordan.py.
Parts are dicts {(x, y): key}; lists of (part, outline) pairs are stamped back to front.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jv2_base as B  # noqa: E402
from jv2_base import amap, capsule, ellipse, fill, poly, rim, span, stroke  # noqa: E402

J = B.jordan          # the approved rig: shoes, box, fist, pop cloud, star
T = B.rig_torso       # the approved rig: the Peach print


#LEGS

# Thin legs, SKINNY (2026-09-28): the jeans as ROW SPANS (build x, inclusive; the stamp's keyline goes
# round them), so every width is exact. 4px thighs, 5px bony knees still knocking together (their
# keylines touch, rows 76-78), 4px shins, a narrow thigh gap under the crotch; the stacks at the ankles
# narrower at the top and spreading onto the sneakers at their base as the fitted jeans' did (the
# shoes' top edges need that cover). The seat is the waist's width (x 43-55). The fitted legs were
# polygons 5-6px wide (git history).
HIP_ROWS = {y: (43, 55) for y in range(64, 72)}          # under the tee, and the crotch row 71
NEAR_ROWS = {71: (43, 46), 72: (43, 46), 73: (43, 46), 74: (43, 46), 75: (44, 47), 76: (44, 47),
             77: (44, 48), 78: (44, 47), 79: (44, 47), 80: (43, 46), 81: (43, 46), 82: (42, 45),
             83: (42, 45), 84: (40, 45), 85: (40, 45), 86: (40, 45), 87: (39, 46), 88: (39, 46)}
FAR_ROWS = {71: (52, 55), 72: (52, 55), 73: (52, 55), 74: (51, 54), 75: (51, 54), 76: (50, 54),
            77: (50, 54), 78: (50, 54), 79: (51, 54), 80: (51, 54), 81: (52, 55), 82: (52, 55),
            83: (53, 56), 84: (53, 57), 85: (53, 57), 86: (53, 57), 87: (53, 58), 88: (53, 58)}
LEG_SPLIT_Y = 72               # from this row down each leg is shaded across its own span
# the jeans' drawing: (kind, points, key, only): the fly, the bony kneecaps, the fold behind each knee,
# the slack drag down each thigh, the stacks at the ankles
LEG_DETAILS = (
    ('stroke', [(49, 66), (49, 71)], 'n', None),
    ('pix', [(46, 76), (46, 77), (47, 77)], 's', 'Nn'),
    ('pix', [(51, 76), (51, 77), (50, 77)], 's', 'Nn'),
    ('pix', [(45, 80), (45, 81)], 'n', 'N'),
    ('pix', [(53, 80), (53, 81)], 'n', 'N'),
    ('stroke', [(44, 73), (45, 74)], 'n', 'N'),
    ('stroke', [(53, 72), (53, 73)], 'n', 'N'),
    ('stroke', [(40, 85), (42, 86), (45, 85)], 'n', 'NsS'),
    ('stroke', [(40, 87), (43, 87), (45, 86)], 's', 'N'),
    ('stroke', [(53, 85), (55, 86), (57, 85)], 'n', 'Ns'),
    ('stroke', [(54, 87), (57, 87)], 's', 'N'),
)


def rows_px(rows):
    return {(x, y) for y, (a, b) in rows.items() for x in range(a, b + 1)}


def leg_pixels():
    """(near leg, far leg, seat) as pixel sets, the hems part of each leg."""
    return rows_px(NEAR_ROWS), rows_px(FAR_ROWS), rows_px(HIP_ROWS)


def detail(part, details):
    """Lay drawing over a part: ('stroke', polyline, key, only) or ('pix', pixels, key, only)."""
    for kind, pts, key, only in details:
        if kind == 'stroke':
            stroke(part, pts, key, only=only)
        else:
            for q in pts:
                if q in part and (only is None or part[q] in only):
                    part[q] = key
    return part


def legs():
    near, far, hips = leg_pixels()
    jeans = fill(near | far | hips, 'N')
    for (x, y) in list(jeans):
        if (x, y) in near and y >= LEG_SPLIT_Y:
            lo, hi = span(near, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x == hi else 'N'))
        elif (x, y) in far and y >= LEG_SPLIT_Y:
            lo, hi = span(far, y)
            k = 's' if x == lo + 1 else ('n' if x in (lo, hi) else 'N')
        else:
            lo, hi = span(jeans, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x >= hi - 1 else 'N'))
        jeans[(x, y)] = k
    return detail(jeans, LEG_DETAILS)


def shoes():
    """The approved sneakers, with one keyline pixel added: the near toe cap's lit edge touched the
    background at (47, 92) (a gap in the approved art too); (47, 91) closes it."""
    far, near = J.shoes()
    near = dict(near)
    near[(47, 91)] = 'k'
    return [far, near]


#NECK, CHEST AND SHIRT

def neck(dx):
    """A thin neck craning up and forward from the collar to under the jaw, and the skin the
    stretched collar shows round its base, as one part so no keyline cuts across the base of the
    neck. `dx` = the head's x offset: the neck leans with the head. The Adam's apple bumps out on its
    front edge."""
    o = dx - 3
    col = B.poly([(47.2 + o * 0.3, 46), (50.8 + o * 0.3, 46), (52.2 + o, 43), (54.2 + o, 40.5),
                  (54.6 + o, 37), (50.2 + o, 37), (50.2 + o, 40.5), (48.4 + o * 0.5, 43)])
    skin = B.poly([(43.4, 43), (56, 43), (55, 44.8), (51.6, 46.4), (48, 46.4), (44.4, 44.8)])
    n = fill(skin, 'c')
    column = fill(col, 'c')                            # the neck turns like a thin cylinder
    rim(column, 'd', -1, 0)
    rim(column, 'b', 1, 0)
    n.update(column)
    for (x, y) in list(n):
        if y <= 39:
            n[(x, y)] = 'b'                            # the jaw's shadow on the neck
        elif y == 40 and (x + 1, y) not in n:
            n[(x, y)] = 'b'
    ax = int(round(53.5 + o))                          # the Adam's apple
    n[(ax, 41)] = 'd'                                 # a 1px bump; the stamp keylines round it
    n[(ax, 42)] = 'b'
    # the neck's shadow falls on the chest to its right, down into the stretched collar
    for (x, y) in list(n):
        if (x, y) not in column and y >= 43 and (x - 1, y) in column:
            n[(x, y)] = 'b'
    return n


# where the collar trim runs (x -> y): stretched out, sagging off-centre, gaping
COLLAR = {43: 43, 44: 44, 45: 44, 46: 45, 47: 45, 48: 46, 49: 46, 50: 46, 51: 46, 52: 45, 53: 45,
          54: 44, 55: 44, 56: 43}

# the tee's body, SKINNY (2026-09-28): v2's narrow sloped shoulders (the collar and neck untouched),
# the sides close down his chest (pixel centres x 42..56: the print's own width, its two side outline
# columns cropped off so her hair meets a pixel of the tee's red inside the keyline), tapering in under
# the print to his narrow waist (x 43..55, the jeans' seat), a level hem on his hips with one small
# rumple left in it. The fitted tee was x 40..58 straight down (git history).
NEAR_X, FAR_X = 41.6, 56.4               # the chest's side seams
WAIST_NEAR, WAIST_FAR = 42.6, 55.4       # the waist's, below the print
HEM_Y = 69.3


def torso_outline(hem_y=HEM_Y):
    """The tee's outline with its hem at `hem_y` (the seated finale gathers it two rows higher)."""
    n, f, wn, wf = NEAR_X, FAR_X, WAIST_NEAR, WAIST_FAR
    return [(44.4, 43.4), (55.6, 43.4), (57.2, 44.4), (58.0, 46.4),                   # far shoulder
            (f + 0.1, 50.0), (f, 56.0), (f, 60.4), (wf, 62.6), (wf, hem_y - 0.3),      # far side
            (54.0, hem_y), (52.6, hem_y + 0.9), (51.4, hem_y + 0.9), (49.8, hem_y), (46.0, hem_y - 0.1),
            (wn + 1.2, hem_y + 0.1), (wn, hem_y - 0.4),                                 # near corner
            (wn, 62.6), (n, 60.4), (n, 56.0), (n - 0.1, 50.0),                          # near side
            (41.2, 46.4), (42.4, 44.6)]                                                 # near shoulder


TORSO = torso_outline()
PRINT_AT = (42, 47)            # the approved print's top-left (it sat at (43, 45) on the old tee)
BAND_Y = PRINT_AT[1] + 15      # the princess's dress pink runs from here to the hem
PRINT_X0, PRINT_X1 = PRINT_AT[0], PRINT_AT[0] + 14       # 42..56, the print's own width
PRINT_CROP_COLS = (0, 14)      # the print map's side outline columns, left off (the approved map is untouched)


def print_part():
    """The approved Peach print (rig_torso.PRINT) at PRINT_AT, without its side outline columns."""
    rows = B.rows_of(T.PRINT)
    return {(x, y): k for (x, y), k in amap(rows, *PRINT_AT).items() if x - PRINT_AT[0] not in PRINT_CROP_COLS}


def shirt(frame=0):
    part = fill(poly(TORSO), 'R')
    for x, yc in COLLAR.items():                       # the neck opening above the trim
        for y in range(40, yc):
            part.pop((x, y), None)
    red = {'lit': 'T', 'base': 'R', 'shade': 'V', 'deep': 'v'}
    pink = {'lit': 'Q', 'base': 'P', 'shade': 'q', 'deep': 'q'}
    for (x, y) in list(part):                          # turned like a cylinder, lit upper left
        lo, hi = span(part, y)
        t = (x - lo) / max(1, hi - lo)
        ramp = pink if y >= BAND_Y else red
        k = ramp['base']
        if t <= 0.06:
            k = ramp['lit']
        elif t >= 0.95:
            k = ramp['deep']
        elif t >= 0.76:
            k = ramp['shade']
        elif y < BAND_Y and 0.1 <= t <= 0.24 and 46 <= y <= 52:
            k = ramp['lit']
        part[(x, y)] = k
    for x, yc in COLLAR.items():                       # the collar trim, stretched out
        if (x, yc) in part:
            part[(x, yc)] = '1'
    for (x, y) in list(part):                          # the seam where the red meets the pink
        if y == BAND_Y and (x < PRINT_X0 or x > PRINT_X1):
            part[(x, y)] = 'k'
    for q, k in print_part().items():                 # the print, its side outline columns cropped
        if q in part:
            part[q] = k

    def fold(pts, key='q', only='PQ'):
        for q in pts:                                   # (some fall outside the narrow waist now)
            if q in part and part[q] in only:
                part[q] = key
    if frame == 0:
        # his hand pinches the tee at the hip: the cloth, close on him, pulls toward the grip in two
        # short tension lines, each lit along its upper edge
        fold(((42, 64), (43, 64), (44, 64), (45, 65), (46, 65)))
        fold(((42, 63), (43, 63), (45, 64)), 'Q', 'P')
        fold(((42, 66), (43, 66), (44, 67), (45, 67)))
        fold(((44, 66),), 'Q', 'P')
    else:
        # hanging close on him: a soft crease where the hem sits on the belt line
        fold(((43, 66), (44, 66), (45, 67), (46, 67)))
        fold(((44, 65), (45, 66)), 'Q', 'P')
    fold(((52, 68), (51, 67)))                         # a crease from the rumple at the hem
    # scruff: the drip off the collar, the smudge on the pink
    for q in ((55, 46), (56, 46), (56, 47)):
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'b'
    for q in ((54, 66), (55, 66), (55, 67)):
        if q in part:
            part[q] = 'c'
    return part


# dandruff fallen on his shoulders: white flakes, a couple of greyer ones
# (the flake v2 had at (59, 49) sat on the sack's far side; on the fitted tee it is two pixels in)
DANDRUFF = {(41, 48): 'W', (44, 45): '9', (57, 46): 'W', (38, 51): '9', (57, 49): 'W', (42, 46): 'W'}


def dandruff(px):
    for q, k in DANDRUFF.items():
        if px.get(q) in ('R', 'T', 'V', 'v'):
            px[q] = k


#ARMS

# SKINNY (2026-09-28): callers pass the fitted build's radii (1.25-1.6, knobs 1.7-1.9); limb() takes
# ARM_THIN off every segment's radius (about a pixel off the arm's width) and KNOB_THIN off every
# knob's (so the elbows still bulge), never below MIN_R / MIN_KNOB. The joints never move.
ARM_THIN, KNOB_THIN = 0.5, 0.35
MIN_R, MIN_KNOB = 0.75, 1.2


def limb(segments, knobs=(), base='d', lit='e', shade='c'):
    """A thin arm: capsules unioned into one shape, bony knobs at the joints, lit from the upper
    left, a shadow line along its underside."""
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= capsule(p0, p1, max(MIN_R, r0 - ARM_THIN), max(MIN_R, r1 - ARM_THIN))
    for (cx, cy, r) in knobs:
        r = max(MIN_KNOB, r - KNOB_THIN)
        shape |= ellipse(cx, cy, r, r)
    part = fill(shape, base)
    rim(part, lit, -1, 0)
    rim(part, lit, 0, -1, only=base)
    rim(part, shade, 1, 0)
    rim(part, shade, 0, 1, only=base)
    return part


def sleeve(pts, hem, lit=True):
    """A T-shirt sleeve on any outline: red, lit on the side toward the light, the dark red of its
    underside, the trim along its hem."""
    s = fill(poly(pts), 'R')
    rim(s, 'T' if lit else 'R', -1, 0)
    rim(s, 'V', 1, 0)
    rim(s, 'v', 0, 1, only='RV')
    stroke(s, [(int(round(x)), int(round(y))) for (x, y) in hem], '1')
    return s


#FITTED SLEEVES (2026-09-28), TIGHTER AND SHORTER ON THE SKINNY BUILD (the same day)

def _unit(dx, dy):
    ln = (dx * dx + dy * dy) ** 0.5 or 1.0
    return dx / ln, dy / ln


SLEEVE_LEN, SLEEVE_HALF = 0.85, 2.0


def sleeve_outline(root, elbow, collar, shoulder, outward, length=5.2, half=2.5):
    """A short fitted sleeve round the top of an upper arm that runs root -> elbow, as outline points:
    from the collar end of the shoulder, along the shoulder line (`shoulder`: points on or just outside
    the tee's own), down the outer side of the arm a pixel clear of it, across the hem `length` down
    the arm, back up the inner side to the armpit, and up the seam to the collar. `outward` (+1 or -1)
    picks which of the arm's normals points away from his body. Returns (outline, hem end points).
    `length` and `half` are the fitted tee's measures (what callers pass); the skinny tee's sleeve is
    SLEEVE_LEN of that length and SLEEVE_HALF wide either side of the arm (0.5 tighter)."""
    length = length * SLEEVE_LEN
    half = SLEEVE_HALF + (half - 2.5)
    dx, dy = _unit(elbow[0] - root[0], elbow[1] - root[1])
    ox, oy = -dy * outward, dx * outward                # away from the torso
    ix, iy = -ox, -oy                                   # toward it
    rx, ry = root

    def at(s_, w, sx, sy):
        return (rx + dx * s_ + sx * w, ry + dy * s_ + sy * w)
    top = at(0.0, half, ox, oy)                         # the round of the shoulder, over the arm's root
    out_mid = at(length * 0.5, half, ox, oy)
    out_hem = at(length, half, ox, oy)
    in_hem = at(length, half, ix, iy)
    pit = at(length * 0.3, half + 0.2, ix, iy)          # the armpit
    seam = ((pit[0] + collar[0]) / 2.0 + ix * 0.6, (pit[1] + collar[1]) / 2.0 + iy * 0.6)
    pts = [collar] + list(shoulder) + [top, out_mid, out_hem, in_hem, pit, seam]
    return pts, (out_hem, in_hem)


NEAR_ROOT, NEAR_COLLAR = (40.6, 49.2), (44.2, 43.2)
FAR_ROOT, FAR_COLLAR = (57.8, 48.5), (55.8, 43.4)
# the shoulder lines the sleeves start along: the near one just outside the tee's (it is stamped over
# the tee, so its keyline becomes his silhouette there); the far one just inside it (it hangs behind
# the tee, so only what passes the tee's far side shows, from the shoulder point down)
NEAR_SHOULDER = [(41.8, 44.4), (40.2, 46.2)]
FAR_SHOULDER = [(57.2, 44.6), (58.3, 46.0)]


def near_sleeve(root=NEAR_ROOT, elbow=(32.4, 57.2), **kw):
    """The fitted short sleeve on the near (right) upper arm running root -> elbow. The collar end and
    the shoulder line move with the shoulder (root - NEAR_ROOT), so a body moved by (dx, dy) gets its
    sleeve moved by (dx, dy)."""
    mx, my = root[0] - NEAR_ROOT[0], root[1] - NEAR_ROOT[1]
    pts, hem = sleeve_outline(root, elbow, (NEAR_COLLAR[0] + mx, NEAR_COLLAR[1] + my),
                              [(x + mx, y + my) for (x, y) in NEAR_SHOULDER], +1, **kw)
    return sleeve(pts, hem)


def far_sleeve(root=FAR_ROOT, elbow=(62.8, 56.6), **kw):
    """The fitted short sleeve on the far (left) upper arm, behind the tee, in shade."""
    kw.setdefault('length', 4.6)
    mx, my = root[0] - FAR_ROOT[0], root[1] - FAR_ROOT[1]
    pts, hem = sleeve_outline(root, elbow, (FAR_COLLAR[0] + mx, FAR_COLLAR[1] + my),
                              [(x + mx, y + my) for (x, y) in FAR_SHOULDER], -1, **kw)
    return sleeve(pts, hem, lit=False)


def near_arm_hip():
    """His right arm: a stick out of the fitted short sleeve, the elbow a sharp point, the hand on his
    hip."""
    arm = limb([((40.6, 49.2), (32.4, 57.2), 1.55, 1.45), ((32.4, 57.2), (38.2, 63.2), 1.45, 1.3)],
               knobs=((32.4, 57.4, 1.9),))
    sl = near_sleeve()
    hand = amap([
        # x: 36-42
        "..kkk..",     # 60
        ".kdedk.",     # 61  bony knuckles on the hip
        "kcdddck",     # 62
        "kbdccbk",     # 63
        ".kbcbk.",     # 64  fingers pinching the tee
        "..kbk..",     # 65
        "...k...",     # 66
    ], 36, 60)
    return [(arm, True), (sl, True), (hand, False)]


def far_arm_box():
    """His left arm holding the box up beside his face: the upper arm out of the fitted short sleeve
    behind his tee, a stick forearm rising in front of it to the box."""
    upper = limb([((57.8, 48.5), (62.8, 56.6), 1.5, 1.4)], knobs=((62.8, 56.6, 1.8),),
                 base='c', lit='d', shade='b')
    fore = limb([((62.8, 56.6), (64.4, 49.8), 1.4, 1.25)], knobs=((62.8, 56.8, 1.8),),
                base='c', lit='d', shade='b')
    sl = far_sleeve()
    # skinny: the tighter sleeve stops a pixel short of the thinner forearm at row 49, which would leave
    # a pinhole between their keylines at (62, 49); one more pixel of sleeve there keylines it shut
    sl[(61, 49)] = 'V'
    return [(upper, True), (sl, True), (fore, True)]


FAR_HAND_BOX = [
    # x: 61-66
    ".kkkk.",      # 44
    "kdeddk",      # 45  fingers wrapped over the base's front corner
    "kddddk",      # 46
    "kcddck",      # 47
    ".kccbk",      # 48
    "..kbk.",      # 49  a thin wrist
]


# the fist-pump's cuff round the thinner raised arm, a pixel of cloth either side of it (the fitted
# tee's was a pixel wider each side: git history)
RAISED_CUFF = [(36.4, 43.2), (41.8, 43.2), (43.0, 44.2), (43.6, 45.8), (42.6, 48.0), (40.9, 50.0),
               (39.9, 50.0), (37.9, 47.8), (36.5, 45.4)]


def raised_sleeve(arm):
    """The fitted sleeve on the fist-pump's raised arm: ridden up round the top of the arm, snug, a
    pixel of cloth either side of it, the trim across its opening where the arm goes in (raised_arm
    lays the arm's rows 41-42 back over it, so the arm runs on out of it); a tension fold pulled from
    the armpit up into it. Its outer side runs down into the tee's near side at the armpit, so it reads
    as the tee stretched up with the arm, not a block on his shoulder."""
    part = fill(poly(RAISED_CUFF), 'R')
    rim(part, 'T', -1, 0)
    rim(part, 'V', 1, 0)
    rim(part, 'v', 0, 1, only='RV')
    stroke(part, [(40, 47), (41, 49)], 'V', only='RT')
    top = min(y for (x, y) in part)
    for (x, y) in list(part):
        if y == top:
            part[(x, y)] = '1'                          # the trim round the opening
    return part


def far_raised_cuff(arm=None, dx=0, dy=0):
    """The same fitted cuff on the far shoulder, for his left arm raised (mirrored about x = 49.6, as
    the fight rig mirrors this sleeve), in his shadow: no lit rim, the dark red underneath, the trim
    across the opening. Moved by (dx, dy) with the body."""
    part = fill(poly([(99.2 - x + dx, y + dy) for (x, y) in RAISED_CUFF]), 'R')
    rim(part, 'V', 1, 0)
    rim(part, 'v', 0, 1, only='RV')
    stroke(part, [(59 + dx, 47 + dy), (58 + dx, 49 + dy)], 'V', only='R')
    top = min(y for (x, y) in part)
    for (x, y) in list(part):
        if y == top:
            part[(x, y)] = '1'
    return part


def raised_arm():
    """The fist-pump: a stick arm punched up out of the fitted cuff ridden up at the shoulder, a bony
    elbow, the pink wristband hanging loose on the thin wrist."""
    arm = limb([((40.8, 47.5), (35.4, 34.6), 1.6, 1.5), ((35.4, 34.6), (31.4, 22.5), 1.5, 1.3)],
               knobs=((35.4, 34.8, 1.9),))
    sl = raised_sleeve(arm)
    band = amap([
        # x: 28-34
        "kkkkkkk",     # 22
        "kQPPPqk",     # 23  loose on him now
        "kQPPqqk",     # 24
        "kkkkkkk",     # 25
    ], 28, 22)
    fist = J.raised_arm()[2][0]                    # the approved fist, straight from the rig
    # the arm runs on through the opening, between the dark of the sleeve's inside either side of it
    through = {q: k for q, k in arm.items() if q[1] in (41, 42)}
    return [(arm, True), (sl, True), (through, False), (band, False), (fist, False)]


def far_arm_box_low():
    """Frame 1: his left arm hanging out of the fitted short sleeve, swung a little clear of the tee so
    the stick of it shows, the box's weight on it."""
    arm = limb([((57.8, 48.5), (62.6, 56.4), 1.5, 1.4), ((62.6, 56.4), (63.8, 63), 1.4, 1.3)],
               knobs=((62.6, 56.6, 1.7),), base='c', lit='d', shade='b')
    sl = far_sleeve(elbow=(62.6, 56.4))
    return [(arm, True), (sl, True)]


# the approved hooked fingers, redrawn at the top so the thin wrist runs into the hand instead of
# stopping at a keyline across it
LOW_HAND = [
    # x: 61-66
    "..kdk.",      # 63  the wrist
    ".kcddk",      # 64
    "kcdddk",      # 65  fingers hooked over the box's top edge
    "kbccdk",      # 66
    ".kkkk.",      # 67
]
