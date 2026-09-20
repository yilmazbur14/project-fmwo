"""Carter's victory look-back: back still turned, head cranked round over his
right shoulder to stare at the player he has just put down.

This follows the victory pose.  The emblem has burned alone in the black for
two seconds; then the spotlight comes back up on him and the player sees his
whole body for the first time since the fight ended - and he looks back at
them.  Pure Akuma, and pure deadpan: no snarl, no gloat, one red slit and a
flat stare over the shoulder.  He isn't even angry.

    f0      back view, head forward - the spotlight has just found him
    f1      the head starts round: the ear slides in, the jaw appears
    f2      edge-on: the brow, the nose and the beard break the silhouette
    f3      ARRIVED.  Cranked past profile, one slit looking straight back
    f4..f5  held with f3: the body is stone, only the eye, the mark and the
            aura are alive

The body is poses.draw_back_body - the approved back view, byte for byte - and
it does not move at all.  Only the head and the neck under it turn.

The problem this has to solve is the one that beat the entrance's profile
frame: a lit bald head at 90 degrees goes to a blank dome with the beard as a
lump on it.  The entrance got round it by back-lighting the pivot into a
silhouette; here he is lit, so the head is built to read on its own:
  - the silhouette carries the face - brow ridge, eye socket, nose and chin are
    real notches in the outline, so the direction of the look reads from the
    shape alone before any detail
  - the beard is a SHAPE with an edge, riding the jaw from the sideburn to the
    chin, with the moustache and the mouth cut into it - not a patch
  - one eye, and it is the hottest thing on the head: the approved slit, heavy
    black lid, red glow, facing the camera
  - the ear and the cross earring sit on the near side toward the back of the
    skull, where a head turned this far puts them, so the one accessory that
    says Carter is still front and centre
  - the neck shows the crank: a cord running down from behind the ear and a
    crease at the nape

Head geometry is authored in design space (the 96-frame, standing head centred
on x = 47.5) and goes through the same scale transform as everything else; the
face is hand-placed in PIXELS at the shipping scale, because at 0.84 an eye is
five pixels wide and has to be put there deliberately.
"""
import math
import lib
from lib import (Canvas, union, inter, sub, grow, erode, poly, ell, empty,
                 PALC, BLACK, W, H, TH_HARD, TH_HARD2)
import parts as P
import poses as PO
import face as F
import intro_lib as IL
import intro_frames as IF
import combat_lib as CL
from render import cylm, sphm, seg, dot
from intro_lib import compose, sigil_paint, sigil_bloom, aura_heat

# the head lifts a touch as the neck cranks - it also keeps the chin clear of
# the top-right of the emblem, which sits right under a jaw turned this way
LIFT = 1.5


def _up(pts, dy):
    return [(x, y - dy) for x, y in pts]


# ---------------------------------------------------------------- keys
# Each key is a head pose.  phi is how far the head has turned from facing
# straight away (0) round to his right; 90 is edge-on, 115 is the look-back.
# Silhouettes run clockwise from the crown.

# f1, ~40 degrees: still mostly the back of the skull; the cheekbone begins to
# bulge the right-hand outline and the ear has slid in toward the middle
HEAD_1 = [
    (47.8, 11.2), (53.0, 11.8), (57.6, 14.0), (60.6, 17.8), (62.0, 22.4),
    (62.2, 27.4), (61.4, 32.0), (59.4, 36.0), (56.0, 39.0), (51.6, 40.8),
    (47.0, 41.0), (42.6, 39.8), (38.6, 37.0), (35.6, 33.0), (34.0, 28.0),
    (33.8, 22.4), (35.0, 17.6), (37.8, 14.0), (42.2, 11.8),
]

# f2, ~85 degrees: edge-on facing right.  The face is the right-hand outline.
HEAD_2 = [
    (48.2, 11.0), (53.4, 11.8), (57.8, 14.4), (60.8, 18.2), (62.4, 22.2),
    (63.4, 24.6), (62.2, 26.6), (62.8, 28.6), (64.8, 31.4), (65.2, 32.6),
    (63.4, 33.6), (62.6, 34.6), (63.2, 36.4), (62.6, 38.6), (60.2, 40.4),
    (55.6, 41.2), (51.0, 40.0), (46.8, 38.0), (42.6, 36.8), (38.8, 36.2),
    (35.8, 33.4), (34.2, 28.4), (34.0, 22.6), (35.4, 17.6), (38.4, 13.8),
    (42.8, 11.6),
]

# f3, ~115 degrees: cranked past profile.  The nose protrudes a little less
# than edge-on because the face has come round toward the camera, and the
# whole face has slid a pixel or two back toward the middle of the head.
HEAD_3 = [
    (48.6, 11.2), (53.8, 12.0), (58.2, 14.6), (61.0, 18.4), (62.2, 22.4),
    (62.8, 24.8), (61.6, 26.6), (62.0, 28.4), (63.6, 30.8), (64.0, 32.2),
    (62.4, 33.4), (61.6, 34.4), (62.2, 36.2), (61.8, 38.2), (59.8, 40.0),
    (55.4, 40.8), (51.0, 39.6), (47.2, 37.6), (43.0, 36.4), (39.2, 36.2),
    (36.0, 33.4), (34.4, 28.6), (34.2, 22.8), (35.6, 17.8), (38.6, 14.0),
    (43.0, 11.8),
]

# beards, riding the jaw from the sideburn in front of the ear to the chin
BEARD_1 = [
    (57.6, 25.6), (60.2, 28.4), (61.6, 32.2), (59.8, 36.4), (56.4, 39.6),
    (51.8, 41.8), (48.4, 40.2), (52.6, 37.6), (55.8, 34.0), (57.2, 29.6),
]
BEARD_2 = [
    (48.0, 27.4), (51.0, 29.6), (55.0, 31.0), (59.2, 31.6), (62.2, 32.6),
    (64.0, 34.2), (64.2, 36.6), (63.6, 39.0), (61.0, 41.4), (56.0, 42.2),
    (51.0, 40.8), (47.0, 38.2), (45.6, 33.8), (46.0, 29.8),
]
BEARD_3 = [
    (47.2, 27.6), (50.2, 29.6), (54.2, 31.0), (58.4, 31.6), (61.2, 32.4),
    (63.0, 34.0), (63.2, 36.4), (62.6, 38.8), (60.2, 41.0), (55.6, 41.8),
    (51.0, 40.4), (47.0, 37.8), (45.4, 33.6), (45.6, 29.6),
]

MOUSTACHE_2 = [(58.4, 32.0), (63.6, 33.0), (64.2, 35.2), (60.6, 35.8),
               (57.6, 34.6)]
MOUSTACHE_3 = [(57.6, 32.0), (62.6, 32.8), (63.2, 35.0), (59.8, 35.6),
               (56.8, 34.4)]

# ear centre and radii, and where the cross hangs from its lobe
EAR = {1: ((56.0, 27.2), 3.0, 4.6), 2: ((47.4, 26.8), 3.2, 4.6),
       3: ((45.6, 26.6), 3.2, 4.6)}

KEYS = {
    1: dict(head=HEAD_1, beard=BEARD_1, stache=None, sphere=(48.0, 24.0)),
    2: dict(head=HEAD_2, beard=BEARD_2, stache=MOUSTACHE_2, sphere=(49.0, 24.0)),
    3: dict(head=HEAD_3, beard=BEARD_3, stache=MOUSTACHE_3, sphere=(49.0, 24.0)),
}


# ---------------------------------------------------------------- neck

def neck_mask(k):
    """Twisted: it reaches up under the jaw on the right as the head turns,
    and the nape shows below the occiput on the left."""
    if k <= 0:
        return P.neck()
    # The bottom edge follows the approved neck's exactly (41.2,44 / 47.5,46 /
    # 53.8,44) and the right-hand side stays above the emblem's top bar.  A
    # first pass let it sag onto the bar and covered six more pixels of the
    # trident than the approved back view does; the mark is still burning in
    # this beat, so it gets exactly the same view of it as the shipped sheet.
    reach = {1: 2.0, 2: 5.0, 3: 6.0}[k]
    pts = [(37.6, 33.0), (44.0, 33.6), (52.0, 35.0 - LIFT),
           (56.0 + reach * 0.6, 37.0), (57.6 + reach * 0.3, 40.4),
           (53.8, 44.0), (47.5, 46.0), (41.2, 44.0), (36.8, 40.0)]
    return poly(pts)


# ---------------------------------------------------------------- face
# Hand-placed in PIXELS at the shipping scale.  At 0.84 the eye is five pixels
# wide; resampled from a design-space grid it loses its rim and stops being an
# eye, so each pixel is put where it has to go.  Anchors are the top-left
# pixel; '.' leaves the rendered head showing through.

# k=2, edge-on: the near eye is right behind the brow ridge, two pixels of glow
FACE_2 = (54, 34, """
..555...
.655555.
...kkkk.
...kVOk.
...k77v.
....ww.v
......w.
.....wk.
........
....333.
...kkkkk
....666.
""")

# k=3, the look-back.  Heavy brow, black lid pressed down on the slit - the
# approved deadpan eye, turned - then the nose's shadow, a nostril, the lit
# underside of the moustache, and a flat closed mouth.  No snarl.
FACE_3 = (51, 34, """
..55555...
.65555555.
..kkkkkk..
..kVOOVks.
..k7777kt.
...wwww.v.
.......tv.
.......wk.
..........
....3333..
...kkkkkk.
....6666..
""")

FACES = {2: FACE_2, 3: FACE_3}

# where the cross hangs from the lobe, top-left pixel of face.EARRING_S
EARRING_AT = {1: (53, 42), 2: (45, 41), 3: (44, 40)}


def stamp_px(cv, grid, x0, y0, over_only=True):
    """A stamp at exact pixel coordinates, bypassing the scale transform."""
    for dy, row in enumerate(grid.strip(chr(10)).split(chr(10))):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x, y = x0 + dx, y0 + dy
            if not (0 <= x < W and 0 <= y < H):
                continue
            if over_only and cv.px[y][x] is None:
                continue
            cv.px[y][x] = PALC[ch]


def outline_outside(cv, mask, solid):
    """Black edge on `mask` only where it borders something outside `solid`.

    Outlining the beard with the usual sub(beard, erode(head)) trick draws a
    line along the subtraction boundary, i.e. straight across the cheek - the
    same seam intro_profile had to paint out after the fact.  Testing each
    edge pixel's neighbours against the solid head+beard keeps the edge where
    the beard meets air or the neck below the jaw, and nowhere else."""
    kill = []
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < W and 0 <= yy < H) or not solid[yy][xx]:
                    kill.append((x, y))
                    break
    for x, y in kill:
        cv.px[y][x] = BLACK


def neck_crank(cv, k):
    """The cue that sells a neck turned this far: a cord pulled taut from
    behind the ear down to the collar, in shadow, and a crease at the nape.
    A lit edge along the cord as well read as a strap across his throat."""
    if k < 2:
        return
    lift = LIFT * (k / 3.0)
    seg(cv, [(43.0, 37.5 - lift), (49.0, 40.0), (55.0, 43.0)], 'w',
        mirror_too=False)
    seg(cv, [(37.8, 37.0 - lift), (41.4, 37.8 - lift)], 'w', mirror_too=False)


# ---------------------------------------------------------------- draw

MARK_LV = 0.60


def body_lit(level=MARK_LV):
    """The approved back view, with the mark burning rather than the dim
    painted ember - it is still lit when the spotlight comes back.

    No bloom is baked in.  In this beat the fight lays carter_mark_glow over
    the mark additively, and a bloom painted into the sheet as well washed the
    whole upper back salmon and turned the trident into a block.  The sheet
    paints the mark crisp - hot fill, dark contour - and the overlay supplies
    the glow."""
    cv = Canvas()
    PO.draw_back_body(cv)
    sigil_paint(cv, IF.sigil_mask(), level)
    return cv


def draw_head(cv, k):
    """k = 0 back of head (approved), 1..3 the turn."""
    if k == 0:
        PO.draw_back_head(cv)
        return
    key = KEYS[k]
    lift = LIFT * (k / 3.0)
    hd = poly(_up(key['head'], lift))
    bd = inter(poly(_up(key['beard'], lift)), grow(hd, 2))
    (ex, ey), erx, ery = EAR[k]
    er = ell(ex, ey - lift, erx, ery)

    nk = neck_mask(k)
    cv.part(nk, 'skin', cylm((38.0, 40.0), (58.0, 40.0), 9.0), TH_HARD, bias=1)
    cv.outline(nk)

    sx, sy = key['sphere']
    cv.part(hd, 'skin', sphm(sx - 3.0, sy - lift, 18.4, 18.4, 0.30), TH_HARD,
            bias=0)
    cv.outline(hd)
    cv.part(bd, 'hair', ('dist', 4.4), TH_HARD, bias=0)
    outline_outside(cv, bd, union(hd, bd))
    if key['stache']:
        ms = inter(poly(_up(key['stache'], lift)), grow(hd, 2))
        cv.part(ms, 'hair', ('dist', 2.4), TH_HARD, bias=-1)
    cv.part(er, 'skin', ('dist', 3.4), TH_HARD, bias=0)
    cv.outline(er)
    # ear inner
    seg(cv, [(ex - 0.6, ey - lift - 2.4), (ex - 1.2, ey - lift),
             (ex - 0.4, ey - lift + 2.6)], 'w', mirror_too=False)
    neck_crank(cv, k)
    if k in FACES:
        fx, fy, grid = FACES[k]
        stamp_px(cv, grid, fx, fy)
    ax, ay = EARRING_AT[k]
    stamp_px(cv, F.EARRING_S, ax, ay, over_only=False)
    return hd, bd, er


# ---------------------------------------------------------------- frames
# f0-f2 play once and hand to a hold that STARTS on the arrival frame, the
# same split as victory / victory_hold: look_back = [0, 1, 2], then
# look_back_hold = [3, 4, 5] on a loop.  Only the aura moves in the hold - he
# is stone, and that is the contempt.
#
# The painted mark is deliberately the same in every frame.  The fight lays the
# animated carter_mark_glow over it in this beat, which is where the burn's
# pulse comes from; a pulse painted into the sheet as well would fight it (and
# sigil_paint quantises to colour bands anyway, so a small level swing would
# not even show).

HEADS = [0, 1, 2, 3, 3, 3]
MARK = [MARK_LV] * 6
MS = [120, 110, 100, 200, 200, 200]

N = len(HEADS)                        # 6
ARRIVE_FRAME = 3
ARRIVE_MS = sum(MS[:ARRIVE_FRAME])    # 330
ONE_SHOT = [0, 1, 2]
HOLD = [3, 4, 5]


def frame(i):
    k = HEADS[i]
    body = body_lit(MARK[i])
    draw_head(body, k)
    bm = body.mask_of()
    # the entrance's aura, calm: it wraps him instead of spiking off his skull,
    # and the fight is over, so nothing flares
    specs = IL.entr_specs(40 + i, scale=0.84, reach=0.88)
    cv = compose(body, specs, IL.entr_sparks(40 + i), haze_in=6, haze_out=2,
                 off=i)
    aura_heat(cv, grow(bm, 1), 0.22)
    IL.soften(cv, grow(bm, 1), near=9, far=28, seed=40 + i)
    return cv
