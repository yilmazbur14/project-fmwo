"""jordan_walk_away.png: 6 frames, looping. The angry stomp out of the arena through the top gate, seen
from BEHIND (he walks up the screen, straight away from the camera).

No sheet of his had a back view. The back of his head is the finale-chars artist's (art_source/
jordan_finale_chars/jfc_back.py, HAIR: the greasy clumps, the wet shine round the lit side, the
dandruff, the rat-tail hanging over his neck, the quiff's crest peeking over the crown), snapshotted
here so the two agree; without the headset his ears show. Their thin neck with the knob of his spine,
and their back of the fitted tee (the shoulder blades through the thin cloth, the collar trim, the
dandruff), carried down to his hips here in the fitted outline of jordan_fit: the back of the tee is
plain red (the Peach print and its pink are on the front only; the back is in no reference).

The stomp: hunched, the head sunk forward between his shoulders, both fists clenched; the chase box
hangs from his left hand (screen-left from behind: he took it with him off the floor in the get-up),
the right fist pumping with his stride; each foot comes down flat and hard with a puff of dust, the
lifted foot shows its white sole; the anger mark on the back of his head.

  0  right foot down (forward, a row higher), left heel lifting; dust at the right foot
  1  down on the right, body a row lower, the left foot coming up off the floor
  2  passing: the left foot swung through, lifted, body a row higher
  3  left foot down, right heel lifting; dust at the left foot
  4  down on the left, the right foot coming up
  5  passing: the right foot swung through, lifted

Build coordinates as the rest (a frame is x - 1), his centre line on build x 49.5.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402

NAME = 'jordan_walk_away'
TIMES = [0.1] * 6
LOOP = True
CX = 49.5


#THE BACK OF HIS HEAD (jfc_back.HAIR, as drawn by the finale-chars artist, 2026-09-28)

HAIR = [
    # x: 35-39 40-44 45-49 50-54 55-59 60-61      y (theirs; placed HAIR_DY lower here)
    "..... ..... ..... ..... kk... ..",   # 6
    "..... ..... ..... ....k ljk.. ..",   # 7
    "..... ..... ..... ...kA ijk.. ..",   # 8
    "..... ..... ..... .kkAY ihk.. ..",   # 9
    "..... ..... ...kk kAYli jhk.. ..",   # 10
    "..... ..... .kkjl AYlji hhk.. ..",   # 11
    "..... ...kk kjlAY ljhij hihk. ..",   # 12
    "..... .kkjl lAjhi jhijh ihhk. ..",   # 13
    "....k kjlAl hljhi jhihh ihhik ..",   # 14
    "...kj lAljh ljhij hijhh ihhhk ..",   # 15
    "..kjl Alhjl jhijh ijhhi hhihk ..",   # 16
    "..kjA ljhlj hijhl ihhij hhihh k.",   # 17
    ".kjlA jhljh ijhli hjhij hihhh k.",   # 18
    ".kjAY lhjlh ijlih jhijh ihhih k.",   # 19
    ".kjlA jhjlh ijlih jhWjh ihhih k.",   # 20
    ".kijl Ahjlh jilih jhijh hhhih k.",   # 21
    ".kijl jhAlh jilhh jhijh hhhih k.",   # 22
    ".kijj lhjAh jihjh ihijh hihhh k.",   # 23
    ".kiij lhjlh WihjA hhijh hihhh k.",   # 24
    ".khij jhjlh jihjl hhihh hihhh k.",   # 25
    ".khij jhilh jihjl hhihh hhhhh k.",   # 26
    ".khii jhilh jhhjl hhihh Whhhh k.",   # 27
    ".khii jhijh jhhil hhihh hhhhh k.",   # 28
    ".khii jhijh jhhil hhihh hhhhh k.",   # 29
    ".khii ihijh ihhil hhihh hhhhh k.",   # 30
    ".khii ihiWh ihhij hhihh hhhhh k.",   # 31
    ".khhi ihihh ihhij hhhhh hhhhh k.",   # 32
    "..khi ihihh ihhij hhhhh hhhhk ..",   # 33
    "..khi ihihh ihhij hhhhh hhhhk ..",   # 34
    "...kh ihihh ihhih hhhhh hhhk. ..",   # 35
    "...kh iiihh ihhih hhhhh hhhk. ..",   # 36
    "....k hiihh ihhih hhhhh hhk.. ..",   # 37
    "..... khihk hihkh hhkhk kk... ..",   # 38
    "..... .kik. khk.k hk.k. ..... ..",   # 39
    "..... .kik. .k... k.... ..... ..",   # 40
    "..... ..kik ..... ..... ..... ..",   # 41
    "..... ..kik ..... ..... ..... ..",   # 42
    "..... ...k. ..... ..... ..... ..",   # 43
]
HAIR_X0, HAIR_Y0 = 35, 6
HAIR_DY = 3             # his head sunk forward between his hunched shoulders: three rows lower than seated

# his ears, which the seated headset covered: from behind, a thin rim of skin at each side of the head
EAR_L = [".k.", "kdk", "kck", "kck", "kbk", ".k."]      # the lit side
EAR_R = [".k.", "kbk", "kbk", "kak", "kak", ".k."]      # in shadow


def head(dy):
    rows = B.rows_of(HAIR)
    part = B.amap(rows, HAIR_X0, HAIR_Y0 + HAIR_DY + dy)
    for rows_e, x0 in ((EAR_L, 34), (EAR_R, 62)):
        for q, k in B.amap(rows_e, x0, 26 + HAIR_DY + dy).items():
            part.setdefault(q, k)
    return part


#NECK AND TEE (jfc_back's neck and back of the tee, carried down to the hem; SKINNY since 2026-09-28:
# the back follows the front's skinny outline, x 42-56 at the chest and 43-55 at the waist)

def neck(dy):
    n = B.fill(B.poly([(45.4, 36), (50.4, 36), (50.8, 45), (45.2, 45)]), 'b')
    B.rim(n, 'c', -1, 0)
    B.rim(n, 'a', 1, 0)
    for (x, y) in list(n):
        if y <= 41:
            n[(x, y)] = 'a' if (x + 1, y) not in n else 'b'
    n[(48, 44)] = 'd'                     # the knob of his spine at the base of the neck
    n[(48, 43)] = 'c'
    return B.shift(n, 0, HAIR_DY + dy)


TEE = [(43.4, 43.8), (55.6, 43.8), (57.2, 44.8), (57.8, 46.8), (56.5, 50.0), (56.4, 56.0), (56.4, 60.4),
       (55.4, 62.6), (55.4, 69.0), (54.2, 69.3), (52.4, 69.8), (50.6, 69.3), (46.0, 69.2), (43.8, 69.3),
       (42.6, 68.9), (42.6, 62.6), (41.6, 60.4), (41.6, 56.0), (41.5, 50.0), (40.6, 46.8), (41.8, 44.8)]
COLLAR = {44: 44, 45: 45, 46: 45, 47: 45, 48: 45, 49: 45, 50: 45, 51: 45, 52: 45, 53: 45, 54: 44}
DANDRUFF = {(42, 47): 'W', (46, 46): '9', (55, 47): 'W', (52, 48): 'W', (41, 51): '9'}


def tee(dy, sway):
    part = B.fill(B.poly([(x + sway, y + dy) for (x, y) in TEE]), 'R')
    col = {x + sway: y + dy for x, y in COLLAR.items()}
    for x, yc in col.items():
        for y in range(38 + dy, yc):
            part.pop((x, y), None)
    for (x, y) in list(part):
        lo, hi = B.V2B.span(part, y)
        t = (x - lo) / max(1, hi - lo)
        k = 'R'
        if t <= 0.07:
            k = 'T'
        elif t >= 0.93:
            k = 'v'
        elif t >= 0.72:
            k = 'V'
        elif 0.12 <= t <= 0.3 and y <= 50 + dy:
            k = 'T'
        part[(x, y)] = k
    for x, yc in col.items():
        if (x, yc) in part:
            part[(x, yc)] = '1'
    # the thin cloth close on him shows his shoulder blades (jfc_back's)
    for (x, y) in ((42, 49), (43, 50), (44, 51), (55, 49), (54, 50), (53, 51)):
        q = (x + sway, y + dy)
        if part.get(q) in ('R', 'T'):
            part[q] = 'V'
    # the cloth pulled into the armpits
    for (x, y) in ((40, 50), (40, 51), (41, 51), (40, 52), (58, 50), (57, 51), (58, 51), (58, 52), (57, 52)):
        q = (x + sway, y + dy)
        if part.get(q) in ('R', 'T'):
            part[q] = 'V'
        elif part.get(q) == 'V':
            part[q] = 'v'
    # a crease where the hem sits on his hips, pulled by the stride
    for (x, y) in ((44, 66), (45, 66), (46, 67), (53, 66), (54, 67)):
        q = (x + sway, y + dy)
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'V' if part[q] != 'V' else 'v'
    for q, k in DANDRUFF.items():
        q2 = (q[0] + sway, q[1] + dy)
        if part.get(q2) in ('R', 'T', 'V'):
            part[q2] = k
    return part


#ARMS FROM BEHIND

def sleeve_back(root, elbow, side, dy):
    """The back of a fitted short sleeve: a snug tube round the top of the arm, the trim at its hem."""
    dx_, dy_ = B.unit(elbow[0] - root[0], elbow[1] - root[1])
    nx, ny = -dy_, dx_
    half, length = 2.1, 4.6                    # skinny: tighter and shorter (the fitted tee's: 2.6, 5.4)
    rx, ry = root
    top_out = (rx - dx_ * 1.6 + nx * half * side * -1, ry - dy_ * 1.6 + ny * half * side * -1)
    pts = [(rx - dx_ * 2.2, ry - dy_ * 2.2 - 0.6),
           top_out,
           (rx + dx_ * length + nx * half * -side, ry + dy_ * length + ny * half * -side),
           (rx + dx_ * length + nx * half * side, ry + dy_ * length + ny * half * side),
           (rx + dx_ * 0.6 + nx * (half + 0.4) * side, ry + dy_ * 0.6 + ny * (half + 0.4) * side)]
    s = B.fill(B.poly(pts), 'R')
    B.rim(s, 'T' if side < 0 else 'R', -1, 0)
    B.rim(s, 'V', 1, 0)
    B.rim(s, 'v', 0, 1, only='RV')
    hem = [pts[2], pts[3]]
    B.stroke(s, [(int(round(x)), int(round(y))) for (x, y) in hem], '1')
    return s


# a fist from behind, knuckles down (the back of the hand toward us): the near side lit
FIST_BACK_L = [
    ".kkkk.",
    "kddcck",
    "kdcccb",
    "kdccbk",
    "kcbcbk",
    ".kkkk.",
]
FIST_BACK_R = [
    ".kkkk.",
    "kccbbk",
    "kcbbbk",
    "kcbbak",
    "kbabak",
    ".kkkk.",
]
# the hand hooked round the box's top edge, from behind
HOOK_L = [
    ".kkkk.",
    "kddcck",
    "kdccck",
]


def arm_back(side, dy, swing):
    """An arm from behind: side -1 his left (screen-left), +1 his right. `swing` moves the elbow and
    the fist (pixels, + = outward and up)."""
    sh = (CX + side * 9.4, 48.4 + dy)
    el = (CX + side * (12.2 + swing * 0.4), 57.6 + dy - swing * 0.5)
    wr = (CX + side * (12.0 + swing * 0.8), 65.4 + dy - swing)
    arm = B.arm([(sh, el, 1.5, 1.4), (el, wr, 1.4, 1.3)], knobs=((el[0], el[1], 1.8),), far=(side > 0))
    sl = sleeve_back(sh, el, side, dy)
    return arm, sl, wr


#LEGS FROM BEHIND

def jeans_back(dy, left, right):
    """The seat and the two legs from behind. `left`/`right`: (knee_dx, knee_dy, ankle_dx, ankle_dy)
    offsets for each leg's knee and ankle from the standing pose (positive dy = up)."""
    seat = B.poly([(42.6, 64 + dy), (55.4, 64 + dy), (55.2, 71 + dy), (53.4, 73.2 + dy), (49.5, 73.6 + dy),
                   (45.6, 73.2 + dy), (42.8, 71 + dy)])      # skinny: the waist's 43-55 (was 41-58)
    legs = {}
    for side, (kdx, kdy, adx, ady) in ((-1, left), (1, right)):
        hip = (CX + side * 4.2, 71.0 + dy)
        knee = (CX + side * 4.6 + kdx, 79.0 - kdy)
        ankle = (CX + side * 4.8 + adx, 87.4 - ady)
        leg = B.capsule(hip, knee, 2.8, 2.4) | B.capsule(knee, ankle, 2.4, 2.6)   # skinny: 0.5 thinner
        legs[side] = leg
    part = B.fill(seat | legs[-1] | legs[1], 'N')
    for (x, y) in list(part):
        lo, hi = B.V2B.span(part, y)
        own = legs[-1] if x < CX else legs[1]
        if (x, y) in own and y > 73 + dy:
            lo, hi = B.V2B.span(own, y)
        t = (x - lo) / max(1, hi - lo)
        k = 'N'
        if t <= 0.12:
            k = 'S' if x < CX else 's'
        elif t <= 0.3:
            k = 's'
        elif t >= 0.85:
            k = 'n'
        part[(x, y)] = k
    # the centre back seam and the back pockets' bottom stitching, just under the tee
    B.stroke(part, [(49, 69 + dy), (49, 73 + dy)], 'n')
    for (x0, x1) in ((43, 47), (52, 56)):
        B.stroke(part, [(x0, 70 + dy), ((x0 + x1) // 2, 71 + dy), (x1, 70 + dy)], 's', only='N')
    return part, legs


SHOE_BACK = [
    ".k1111k.",
    "k232211k",
    "k221111k",
    "k211111k",
    "k111111k",
    "k999999k",
    "k000009k",
    ".kkkkkk.",
]
SOLE_UP = [
    ".kkkkkk.",
    "k111111k",
    "k909909k",
    "k099999k",
    "k990099k",
    ".kkkkkk.",
]


#THE BOX FROM BEHIND (hanging from his left hand: we see its back)

BOX_BACK = [
    ".kkkkkkkkkkkkk.",
    "kGoooooooooooGk",
    "kRRRRRRRRRRRRVk",
    "kRRRROOORRRRRVk",
    "kRRRRRRRRRRRRVk",
    "kkkkkkkkkkkkkkk",
    "kOoooooooooooGk",
    "kOoGGGGGGGGGoGk",
    "kOoGgggggggGoGk",
    "kOoGgGGGGGgGoGk",
    "kOoGgGGGGGgGoGk",
    "kOoGgggggggGoGk",
    "kOoGGGGGGGGGoGk",
    "kOoooooooooooGk",
    "kOoooooooooooGk",
    "kOoooooooooooGk",
    "kOoooooooooooGk",
    "kgGGGGGGGGGGGgk",
    ".kkkkkkkkkkkkk.",
]


def dust(cx, cy):
    """A puff of dust off the mat where a foot slams down (effects: no keyline)."""
    out = {}
    for (x, y, k) in ((-5, 0, '9'), (-6, -1, '0'), (-4, -1, '9'), (-7, 0, '0'), (5, 0, '9'), (6, -1, '0'),
                      (4, -1, '9'), (7, 0, '0'), (-5, -2, '0'), (5, -2, '0')):
        out[(cx + x, cy + y)] = k
    return out


ANGER_BACK_AT = (54, 16)


#FRAMES

# Per frame: the body's bob (dy, + lower) and sway, each foot's height ('up': 0 planted on row 95,
# 1 the forward foot a row further off, 4 and 6 lifted with its white sole to us), the arms' swing,
# and which foot slams down with a puff of dust.
POSES = [
    dict(dy=0, sway=0, up=(0, 1), swing=(0, -1), dust=+1),      # 0 right foot down, forward
    dict(dy=1, sway=1, up=(4, 0), swing=(1, 1), dust=0),        # 1 down on the right, left foot up
    dict(dy=-1, sway=1, up=(6, 0), swing=(1, 2), dust=0),       # 2 passing
    dict(dy=0, sway=0, up=(1, 0), swing=(-1, 0), dust=-1),      # 3 left foot down, forward
    dict(dy=1, sway=-1, up=(0, 4), swing=(1, 1), dust=0),       # 4 down on the left, right foot up
    dict(dy=-1, sway=-1, up=(0, 6), swing=(2, 1), dust=0),      # 5 passing
]


def leg_raise(up):
    """(knee dx, knee raise, ankle dx, ankle raise) for a foot `up` rows off the floor: a lifted foot
    bends the knee (the calf swings back toward us and up)."""
    if up >= 4:
        return (0, up // 2 + 1, 0, up + 1)
    return (0, up, 0, up)


def build(i):
    p = POSES[i]
    dy, sway = p['dy'], p['sway']
    cv = B.Canvas(96, 96)
    fx = set()
    jeans, legs = jeans_back(dy, leg_raise(p['up'][0]), leg_raise(p['up'][1]))
    # feet first (the jeans' stacked hems fall over them)
    for side, up in ((-1, p['up'][0]), (1, p['up'][1])):
        ax = int(round(CX + side * 4.8)) - 4
        if up >= 4:
            cv.stamp(B.amap(B.rows_of(SOLE_UP), ax, 90 - up), outline=False)
        else:
            cv.stamp(B.amap(B.rows_of(SHOE_BACK), ax, 88 - up), outline=False)
    cv.stamp(jeans)
    # the box behind his left leg, hanging from his left hand
    armL, slL, wrL = arm_back(-1, dy, p['swing'][0])
    armR, slR, wrR = arm_back(1, dy, p['swing'][1])
    bx, by = int(round(wrL[0])) - 13, int(round(wrL[1])) + 1
    cv.stamp(B.amap(BOX_BACK, bx, by), outline=False)
    cv.stamp(tee(dy, sway))
    cv.stamp(neck(dy + 0))
    hd = head(dy)
    cv.stamp(hd, outline=False)
    for part, ol in ((armL, True), (slL, True), (armR, True), (slR, True)):
        cv.stamp(part, outline=ol)
    cv.stamp(B.amap(HOOK_L, int(round(wrL[0])) - 3, int(round(wrL[1])) - 1), outline=False)
    cv.stamp(B.amap(FIST_BACK_R, int(round(wrR[0])) - 2, int(round(wrR[1])) - 1), outline=False)
    B.overlay(cv, B.ANGER, ANGER_BACK_AT[0], ANGER_BACK_AT[1] + HAIR_DY + dy)
    # fuming: a puff of steam off one side of his head, then the other, with the stride
    x0, x1 = HAIR_X0 + 1, HAIR_X0 + 26
    y0 = HAIR_Y0 + HAIR_DY + dy
    puffs = ((B.STEAM, x0 - 7, y0 + 12), (B.STEAM_S, x1 + 3, y0 + 7)) if i % 3 != 2 else             ((B.STEAM_S, x0 - 5, y0 + 8), (B.STEAM, x1 + 2, y0 + 11))
    if i >= 3:
        puffs = tuple((r, int(2 * CX) - sx - len(B.rows_of(r)[0]) + 1, sy) for (r, sx, sy) in puffs)
    for rows, sx, sy in puffs:
        B.overlay(cv, rows, sx, sy, fx=fx, only_empty=True)
    if p['dust']:
        side = p['dust']
        for q, k in dust(int(round(CX + side * 4.8)), 95).items():
            if q not in cv.px and 0 <= q[1] < 96:
                cv.px[q] = k
                fx.add(q)
    return cv, fx


def builders():
    return [lambda i=i: build(i) for i in range(6)]


def frames():
    out = []
    for b in builders():
        cv, fx = b()
        out.append((B.fill_holes(B.finish(cv)), {(x + B.ANCHOR_SHIFT, y) for (x, y) in fx}))
    return out
