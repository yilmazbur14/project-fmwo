"""jordan_defeat.png: 6 frames, played once, the last one held. He does not vanish. In v2's look.

  0  stagger: the blow rocks him back on his heels, dazed, wall-eyed; the box slips in his fingers
  1  the box drops: his hand falls open and the box tumbles; he sways forward, head lolling
  2  his bony knees give (knocking together), the box hits the floor on its side
  3  down on both knees, stick arms hanging, head dropping
  4  sunk back toward his heels, shoulders slumped, head hung, the far arm fallen out onto the box
  5  settled, held: the head sunk a pixel lower, spent

Built back to front like v2's frames. The kneeling jeans are new polygons for his thin legs, shaded by
v2's own jeans rules (reimplemented here as jeans()).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_box as BX  # noqa: E402
import janim_heads as HD  # noqa: E402

J = B.jordan
V = B.V2B
NAME = 'jordan_defeat'
TIMES = [0.14, 0.12, 0.1, 0.14, 0.2, 1.0]
LOOP = False
HOLD_FRAME = 5

NECK_PIVOT = (45, 33)
GRIP_UV = (1, 19)
GRIP_XY = (64, 46)                  # the box's grip point in v2's idle
HEAD_AT = B.V2F.HEAD_AT[0]          # v2's idle head offset, (3, 2)


#JEANS

def jeans(near, far, hips, split_y, details=()):
    """Polygons -> one jeans part, shaded by v2's rules (jv2_body.legs): the near leg lit down its left
    edge, the far leg lit one pixel in from its left edge and dark at both, the hips shaded across the
    whole width. `details` are (kind, points, key, only) strokes laid over it."""
    near_px, far_px, hips_px = B.poly(near), B.poly(far), B.poly(hips)
    part = B.fill(near_px | far_px | hips_px, 'N')
    span = B.jv2_base.span
    for (x, y) in list(part):
        if (x, y) in near_px and y >= split_y:
            lo, hi = span(near_px, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x == hi else 'N'))
        elif (x, y) in far_px and y >= split_y:
            lo, hi = span(far_px, y)
            k = 's' if x == lo + 1 else ('n' if x in (lo, hi) else 'N')
        else:
            lo, hi = span(part, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x >= hi - 1 else 'N'))
        part[(x, y)] = k
    for kind, pts, key, only in details:
        if kind == 'stroke':
            B.stroke(part, pts, key, only=only)
        else:
            for q in pts:
                if q in part and (only is None or part[q] in only):
                    part[q] = key
    return part


# Down on both knees, thin thighs upright in loose denim, the bony knees on the floor (the hips 12 rows
# lower than standing).
KNEEL = dict(
    near=[(41, 78), (46.5, 78), (46.8, 83), (47.4, 88), (47.2, 91.5), (45.8, 94), (42.2, 94), (40.8, 91.5),
          (40.6, 87), (41, 83)],
    far=[(51.6, 78), (57, 78), (56.8, 83), (56.8, 88), (56.4, 91), (55, 93), (52.6, 93), (51.4, 91),
         (51, 87), (51.2, 83)],
    hips=[(40.6, 76), (57.4, 76), (57.2, 81), (53, 82.4), (50, 83.5), (47, 82.4), (41.2, 81)],
    split_y=82,
    details=(('stroke', [(50, 78), (50, 83)], 'n', None),                      # the fly
             ('pix', [(43, 90), (44, 90), (43, 91), (44, 91)], 's', 'N'),        # near kneecap
             ('pix', [(53, 89), (54, 89), (53, 90)], 's', 'N'),                  # far kneecap
             ('stroke', [(42, 85), (45, 86)], 'n', 'N'),                         # slack at the hip joint
             ('stroke', [(52, 84), (55, 85)], 'n', 'N')),
)

# Still on his knees but sunk back toward his heels: the hips 15 rows down, the thighs shorter.
KNEEL_LOW = dict(
    near=[(41, 81), (46.5, 81), (46.8, 85), (47.4, 89), (47.2, 91.5), (45.8, 94), (42.2, 94), (40.8, 91.5),
          (40.6, 88), (41, 85)],
    far=[(51.6, 81), (57, 81), (56.8, 85), (56.8, 89), (56.4, 91), (55, 93), (52.6, 93), (51.4, 91),
         (51, 88), (51.2, 85)],
    hips=[(40.6, 79), (57.4, 79), (57.2, 84), (53, 85.4), (50, 86.5), (47, 85.4), (41.2, 84)],
    split_y=85,
    details=(('stroke', [(50, 81), (50, 86)], 'n', None),
             ('pix', [(43, 91), (44, 91), (43, 92)], 's', 'N'),
             ('pix', [(53, 90), (54, 90)], 's', 'N'),
             ('stroke', [(42, 88), (45, 89)], 'n', 'N'),
             ('stroke', [(52, 87), (55, 88)], 'n', 'N')),
)


def kneel_jeans(spec):
    return jeans(spec['near'], spec['far'], spec['hips'], spec['split_y'], spec['details'])


def lean_jeans(back):
    """v2's jeans rocked back on the heels: rows slide left more the higher they are, the ankles
    fixed, so the thin legs lean back from planted feet."""
    return {(x - int(round(back * max(0, 88 - y) / 24.0)), y): k for (x, y), k in V.legs().items()}


def buckle_jeans(drop=(69, 71, 73, 75, 77, 80, 83), knees_in=2):
    """Knees giving way: rows out of the thighs and shins (hips sink, soles fixed) and the bony knees
    knocking together."""
    out = {}
    for (x, y), k in V.legs().items():
        if y in drop:
            continue
        out[(x, y + sum(1 for r in drop if r > y))] = k
    res = {}
    for (x, y), k in out.items():
        dx = 0
        if 74 <= y <= 86:
            w = 1.0 - abs(y - 80) / 7.0
            dx = int(round(knees_in * w)) * (1 if x <= 49 else -1)
        res[(x + dx, y)] = k
    return res


def near_shin(knee=(43.5, 91.5), ankle=(33, 90)):
    """His near shin lying back along the floor from the knee (it runs away from us, to the left),
    thin in loose denim lit along its top, the slack hem bunched at the ankle."""
    part = B.fill(B.capsule(knee, ankle, 2.0, 2.4), 'N')
    B.rim(part, 's', 0, -1)
    B.rim(part, 'n', 0, 1)
    ax = int(round(ankle[0]))
    for (x, y) in list(part):
        if x <= ax + 1:
            part[(x, y)] = 'n' if (x + y) % 2 else 's'
    return part


# His near sneaker at the end of the shin, kneeling on tucked toes: heel up, the white sole facing
# back (left) down to the toe on the floor, the charcoal upper toward us, lit on top.
TUCKED = B.rows_of([
    # x: 0-7
    ".kkkk...",
    "k0922k..",
    "k02111k.",
    "k02111k.",
    "k01111k.",
    "k01121k.",
    "k00111k.",
    "k00911k.",
    ".kkkkk..",
])


def tucked_shoe(x=27, y=86):
    return B.amap(TUCKED, x, y)


#ARMS AND HANDS

# a hand hanging limp off a thin wrist, fingers down (near side, lit on its left)
HAND_HANG = B.rows_of([
    ".kdk..",
    "kddck.",
    "kdddck",
    "kddcbk",
    ".kcbk.",
    "..kk..",
])
# the far hand hanging, just let go of the box (in shadow)
HAND_HANG_FAR = B.rows_of([
    "..kdk.",
    ".kcddk",
    "kcdddk",
    "kbccdk",
    ".kbcbk",
    "..kkk.",
])
# the far hand fallen onto the fallen box, fingers over its edge
HAND_ON_BOX = B.rows_of([
    "..kdk..",
    ".kdddk.",
    "kkcddck",
    "kbccbbk",
    ".kkkkk.",
])


def near_sleeve(ox, oy):
    """The near sleeve drooping off his narrow shoulder almost to the elbow of an arm hanging down."""
    return V.sleeve([(44.2 + ox, 43.4 + oy), (41.4 + ox, 44.6 + oy), (38.8 + ox, 47 + oy), (37 + ox, 50.6 + oy),
                     (34.8 + ox, 53.6 + oy), (39.6 + ox, 57.4 + oy), (42 + ox, 54 + oy), (43 + ox, 50.6 + oy),
                     (43.6 + ox, 47 + oy)],
                    [(int(round(35 + ox)), int(round(54 + oy))), (int(round(39 + ox)), int(round(57 + oy)))])


def limp_near(ox, oy):
    """His near arm hanging dead out of the drooping sleeve, the bony elbow kinked, the hand limp."""
    arm = V.limb([((40.6 + ox, 49.2 + oy), (36.4 + ox, 57.2 + oy), 1.55, 1.45),
                  ((36.4 + ox, 57.2 + oy), (35.6 + ox, 63.4 + oy), 1.45, 1.3)],
                 knobs=((36.4 + ox, 57.4 + oy, 1.9),))
    hand = B.amap(HAND_HANG, int(round(34 + ox)), int(round(63 + oy)))
    return [(arm, True), (near_sleeve(ox, oy), True), (hand, False)]


def limp_far(ox, oy):
    """His far arm hanging out of its drooping sleeve (v2's far arm as it carries the box low), the
    hand let go and hanging."""
    parts = [(B.shift(p, ox, oy), ol) for p, ol in V.far_arm_box_low()]
    hand = B.amap(HAND_HANG_FAR, int(round(61 + ox)), int(round(63 + oy)))
    return parts + [(hand, False)]


def reach_far(oy):
    """The far arm fallen out onto the fallen box: the stick arm slanting down out of its sleeve to
    the hand lying on the box's top edge."""
    arm = V.limb([((57.8, 48.5 + oy), (63.4, 56 + oy), 1.5, 1.4), ((63.4, 56 + oy), (68.4, 62 + oy), 1.4, 1.3)],
                 knobs=((63.4, 56.2 + oy, 1.8),), base='c', lit='d', shade='b')
    sl = V.sleeve([(55.6, 43.4 + oy), (58.4, 44.8 + oy), (60.8, 47.6 + oy), (62.6, 50.8 + oy), (63.6, 53.2 + oy),
                   (59, 55.2 + oy), (57.4, 51 + oy), (57, 47 + oy)],
                  [(59, 55 + oy), (63, 53 + oy)], lit=False)
    hand = B.amap(HAND_ON_BOX, 66, 62 + oy)
    return [(arm, True), (sl, True), (hand, False)]


#FRAMES

def head_part(name, tilt, dx, dy):
    hd = HD.head(name)
    if tilt:
        hd = B.tilt2(hd, tilt, NECK_PIVOT, 'xy')
        B.close_gaps(hd)
    return B.shift(hd, dx, dy)


def arms(cv, parts, name):
    """Stamp an arm's parts, recording its hand (the last part)."""
    B.rec(name, parts[-1][0])
    B.stamp_all(cv, parts)


def torso(cv, ox, oy, lean):
    """v2's thin neck (leaning `lean` the way v2 leans it with the head), the hanging tee and the
    dandruff, moved by (ox, oy)."""
    cv.stamp(B.shift(V.neck(lean), ox, oy))
    cv.stamp(B.shift(V.shirt(1), ox, oy))
    B.dandruff(cv.px, ox, oy)


def frame0():
    """Stagger: legs leaning back from planted feet, everything above the belt rocked back 3."""
    dx = -3
    cv = B.Canvas(96, 96)
    cv.stamp(lean_jeans(3))
    for s in V.shoes():
        cv.stamp(s, outline=False)
    back = lambda part: B.shift(part, dx, 0)  # noqa: E731
    for part, ol in V.far_arm_box():
        cv.stamp(back(part), outline=ol)
    torso(cv, dx, 0, HEAD_AT[0] - 1)
    cv.stamp(B.rec('head', head_part('daze', -9, HEAD_AT[0] + dx - 1, HEAD_AT[1])), outline=False)
    import janim_hit
    arms(cv, janim_hit.near_arm_flung(dx), 'hand_near')
    box = BX.box_at(24, GRIP_UV, (GRIP_XY[0] + dx + 1, GRIP_XY[1] + 3))   # slipping out of his grip
    B.close_gaps(box)
    cv.stamp(B.rec('box', box), outline=False)
    cv.stamp(B.rec('hand_far', back(B.amap(V.FAR_HAND_BOX, *B.V2F.FAR_HAND_AT))), outline=False)
    return cv, set()


def frame1():
    """The box drops; he sways forward over bending knees, arms falling limp."""
    ox, oy = 1, 2
    cv = B.Canvas(96, 96)
    cv.stamp(buckle_jeans(drop=(73, 80), knees_in=0))
    for s in V.shoes():
        cv.stamp(s, outline=False)
    arms(cv, limp_far(ox, oy), 'hand_far')
    torso(cv, ox, oy, HEAD_AT[0])
    cv.stamp(B.rec('head', head_part('daze', 8, HEAD_AT[0] + ox, HEAD_AT[1] + oy)), outline=False)
    arms(cv, limp_near(ox, oy), 'hand_near')
    cv.stamp(B.rec('box', BX.box_at(55, (7, 10), (73, 60))), outline=False)          # tumbling
    return cv, set()


def frame2():
    """Knees giving way; the box hits the floor on its side."""
    oy = 7
    cv = B.Canvas(96, 96)
    cv.stamp(buckle_jeans())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    arms(cv, limp_far(0, oy), 'hand_far')
    torso(cv, 0, oy, HEAD_AT[0])
    cv.stamp(B.rec('head', head_part('droop', 12, HEAD_AT[0], HEAD_AT[1] + oy)), outline=False)
    arms(cv, limp_near(0, oy), 'hand_near')
    box_on_floor(cv, lift=2)                                                # landing, bounced up
    return cv, set()


# Where the box comes to rest (its centre, build coordinates): it lands here in frame 2 (bouncing two
# pixels up) and stays put for the rest of the sheet.
BOX_REST = (75, 88)


def box_on_floor(cv, lift=0):
    box = BX.box_at(90, (7, 10), (BOX_REST[0], BOX_REST[1] - lift))
    cv.stamp(B.rec('box', box), outline=False)


def lower_kneel(cv, spec):
    cv.stamp(near_shin())
    cv.stamp(tucked_shoe(), outline=False)
    cv.stamp(kneel_jeans(spec))


def frame3():
    """Down on both knees, arms hanging, the head dropping."""
    oy = 12
    cv = B.Canvas(96, 96)
    lower_kneel(cv, KNEEL)
    arms(cv, limp_far(0, oy), 'hand_far')
    torso(cv, 0, oy, HEAD_AT[0])
    cv.stamp(B.rec('head', head_part('droop', 14, HEAD_AT[0], HEAD_AT[1] + 1 + oy)), outline=False)
    arms(cv, limp_near(0, oy), 'hand_near')
    box_on_floor(cv)
    return cv, set()


def frame_sit(head_drop):
    """Sunk back toward his heels, shoulders slumped, head hung; the near arm hangs dead and the far
    arm has fallen out onto the fallen box, still reaching for it. `head_drop` sinks the head that
    many more pixels (the held last frame settles it one lower)."""
    oy = 15
    cv = B.Canvas(96, 96)
    lower_kneel(cv, KNEEL_LOW)
    box_on_floor(cv)
    arms(cv, reach_far(oy), 'hand_far')
    torso(cv, 0, oy + 1, HEAD_AT[0] + 1)
    cv.stamp(B.rec('head', head_part('droop', 20, HEAD_AT[0] + 1, HEAD_AT[1] + 3 + oy + head_drop)), outline=False)
    arms(cv, limp_near(0, oy), 'hand_near')
    return cv, set()


def fill_holes(px):
    """A single transparent pixel boxed in by two parts' keylines is a gap in the ink: close it."""
    for q in B.audit(px)['holes']:
        px[q] = 'k'
    return px


def builders():
    return [frame0, frame1, frame2, frame3, lambda: frame_sit(0), lambda: frame_sit(1)]


def frames_info():
    return B.make_frames(builders(), post=fill_holes)


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.to_image(px))
        a = B.audit(px, fx)
        print(i, st, 'gaps', a['gaps'], 'lone', a['lone'], 'holes', a['holes'], 'keys', a['keys'])
