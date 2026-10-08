"""The swivel (jordan_seated frames 4-5) and the empty chair (frame 10).

  4  tapped: his head snaps round to screen-left in profile ("huh?"), headset still on, his near hand
     already up at the left cup; the chair has only begun to turn (yaw -20), so his body is still
     the idle's back view
  5  mid-swivel, the chair side-on (yaw -100): he sits in profile facing left, dragging the headset
     down round his neck with his near hand; speed lines trail the turn
  10 the empty chair, swivelled to face screen-left (yaw -135, the talk pairs' angle), same anchor

The profile head is new for this job (no approved view looks this way): it is drawn from the approved
head's own vocabulary, rows and ramps (the quiff's crest and its wet shine, the heavy straight brow,
the tired eye, the thin moustache that stops short of the patchy beard, the beard down the jaw, the
greasy back of the head with the rat-tail and dandruff), lit from the upper left like everything else.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfc_base as B  # noqa: E402
import jfc_chair as C  # noqa: E402
import jfc_back as K  # noqa: E402
import jfc_front as F  # noqa: E402

V = B.V2B


#THE PROFILE HEAD (96-space, placed like the mirrored approved head: jfc_front.head(.., 0, 0))

PX0, PY0 = 31, 8
PROFILE = [
    # x: 31-35 36-40 41-45 46-50 51-55 56-60      y
    "..... kk... ..... ..... ..... .....",   # 8
    "....k lmk.. ..... ..... ..... .....",   # 9   the crest, as the approved quiff's
    "....k jAmk. ..k.. ..... ..... .....",   # 10
    "....k ijYAk kkmk. ..... ..... .....",   # 11
    "....k ijlmY Aklkk kkk.. ..... .....",   # 12
    ".... .kijlA miYAm jlmkk k.... .....",   # 13
    ".... .kjlmj ilmjh AYAjl jkkk. .....",   # 14
    ".... .kilji lmjij ljhAY jlhik .....",   # 15
    ".... .kiiji lmWij lihjj hlijh k....",   # 16  dandruff
    ".... .kiiji lmjij mihWj hilhi hk...",   # 17
    ".... .kiiWl ijmlh imjhh Wihjh ik...",   # 18
    ".... ..kiji ijjii ijihh ihWhi hhk..",   # 19
    ".... ..kijl Amlkj iihij hihhi hhk..",   # 20  the greasy forelock over his brow
    ".... ..kcdk jAlkj hijhh ijhhi hik..",   # 21
    ".... .kdcde ekkij ihhij hjihh Whk..",   # 22
    ".... .kdjjj jlkij hihhi hihhi hk...",   # 23  the heavy brow
    ".... kdiiii ikdcj jihih hhihi hk...",   # 24
    ".... kcdkkk kdcdc bjjih ihhhi hk...",   # 25  lash line
    "...k dcdhWW cdcdj ikkkj ihhih k....",   # 26  the eye, looking left
    "..kd eddccc ddcji kddck hihih k....",   # 27  the sideburn and the ear
    ".kde dedcdc dccji kdbck hihhk .....",   # 28
    "kdee ddcdcc cdcji kdbck hihk. .....",   # 29  the nose's tip
    "kkdb dcddcc dcdcj kccbk jihk. .....",   # 30  nostril
    ".kkj ljdccd cdcbj jkkkj ihk.. .....",   # 31  the thin moustache, short of the beard
    "..kk kkjdcd cbjij ljjij hik.. .....",   # 32  mouth
    "..kp pijcdc jijli jijih ihk.. .....",   # 33  lower lip; the patchy beard down the jaw
    "..kj ijjcjl jijlj ihijh kik.. .....",   # 34
    "...k ijlji jlijl jihih kkik.. .....",   # 35  the rat-tail hangs off the back
    "...k hijji ijljj ihhik .kik.. .....",   # 36
    "....k hiij jiiji hhhk. ..k... .....",   # 37
    ".....k hhi iiihh hk... ...... .....",   # 38
    "......k kk kkkkk k.... ...... .....",   # 39
]


def profile_head(dx=0, dy=0):
    rows = B.rows_of(PROFILE)
    for i, r in enumerate(rows):
        if len(r) != 30:
            raise ValueError('profile row %d is %d wide' % (PY0 + i, len(r)))
    return B.shift(B.amap(rows, PX0, PY0), dx, dy)


# the headset on, seen from his left: the cup over his ear shows its outer face, the pink light ring
# round its dark middle; the band climbs from it over his crown
CUP_SIDE = [
    "..kkk..",
    ".k322k.",
    "k2QPPqk",
    "kQ211qk",
    "kP111qk",
    "kP111qk",
    "kq111qk",
    "k2qqq1k",
    ".k111k.",
    "..kkk..",
]


def headset_on(dx=0, dy=0):
    """(band, cup) for the profile head, in 96-space."""
    band = {}
    for y in range(12, 24):
        x = 48 if y > 15 else (47 if y > 13 else 46)
        band[(x, y)] = '3'
        band[(x + 1, y)] = '2'
    cup = B.amap(B.rows_of(CUP_SIDE), 45, 22)
    return B.shift(band, dx, dy), B.shift(cup, dx, dy)


#SPEED LINES (effects: no keyline)

def speed_lines(arcs):
    """[(x0, y, length, key)] short horizontal streaks, their tails tapering to grey."""
    out = {}
    for (x0, y, n, key) in arcs:
        for i in range(n):
            out[(x0 + i, y)] = key if i < n - 2 else '9'
    return out


#FRAME 4: TAPPED, HEAD ROUND IN PROFILE

def frame_tapped():
    cv = B.Canvas(B.FW, B.FH)
    yaw = -20
    parts = {}
    for n, p, d in C.solids(yaw):
        if n in ('back', 'seat', 'pad-1', 'pad+1', 'bolster-1', 'bolster+1'):
            C.pad(p)
        parts[n] = (p, d)
    for n in sorted(parts, key=lambda n: -parts[n][1]):
        if n != 'back':
            cv.stamp(parts[n][0])
    at = K._at
    # his right arm stays at the desk; his left comes up to the left cup
    cv.stamp(at(K.arm(1)))
    up = B.limb([((35.8, 52.4), (32.6, 41.8), 1.5, 1.4), ((32.6, 41.8), (45.4, 28.4), 1.4, 1.25)],
                knobs=((32.6, 41.8, 1.8),))
    cv.stamp(at(K.neck(0)))
    cv.stamp(at(K.tee()))
    cv.stamp(at(K.sleeve(1)))
    cv.stamp(at(up))
    sl = K.sleeve(-1)
    cv.stamp(at(sl))
    hd = profile_head(1, 0)
    cv.stamp(at(hd), outline=False)
    band, cup = headset_on(1, 0)
    cv.stamp(at(band))
    cv.stamp(at(B.shift(cup, -1, -2)), outline=False)      # one cup lifted off his ear to listen
    hand = B.close_gaps(B.amap(B.rows_of(HAND_UP), 44, 24))
    cv.stamp(at(hand), outline=False)
    back = parts['back'][0]
    cv.stamp(back)
    for q, k in C.decals(yaw).items():
        if q in back and cv.px.get(q) not in (None, 'k'):
            cv.px[q] = k
    # a startled tick over his head (an effect)
    fx = {}
    for (x, y) in ((42, 4), (42, 5), (42, 6), (42, 8)):
        fx[(x + B.OFF[0], y + B.OFF[1] + K.LIFT)] = 'W'
    for q, k in fx.items():
        cv.px[q] = k
    return cv, set(fx)


# his left hand come up to the cup, fingers over its rim (the lit side)
HAND_UP = [
    ".kkk..",
    "kdedk.",
    "kddeck",
    "kcddck",
    ".kcdk.",
    ".kcck.",
]


#FRAME 5: MID-SWIVEL, SIDE-ON

# his thin body side-on in the SKINNY build's tee (the user, 2026-09-28; the fitted tee before it, the
# same day): the chest to the left, the back to the right, the cloth close to him all the way down to
# the hem at his hips; a pixel thinner front to back than the fitted tee's (git history)
TORSO_SIDE = [(46.6, 39.0), (51.6, 37.8), (55.2, 39.4), (56.4, 44.6), (56.4, 51.0), (56.0, 57.0), (56.4, 62.6),
              (53.6, 63.4), (50.0, 63.0), (47.2, 63.2), (46.2, 62.2), (46.4, 57.0), (46.0, 50.0), (46.4, 44.0)]


def tee_side():
    part = B.fill(B.poly(TORSO_SIDE), 'R')
    for (x, y) in list(part):
        lo, hi = B.span(part, y)
        t = (x - lo) / max(1, hi - lo)
        pink = y >= 56
        if t <= 0.08:
            k = 'Q' if pink else 'T'
        elif t >= 0.9:
            k = 'q' if pink else 'v'
        elif t >= 0.66:
            k = 'q' if pink else 'V'
        else:
            k = 'P' if pink else 'R'
        part[(x, y)] = k
    for (x, y) in list(part):
        if y == 56 and (x <= 46 or x >= 56):
            part[(x, y)] = 'k'
    # the print's edge turning away round his chest: the princess's gold hair and the crown's tip
    for q, k in (((46, 42), 'O'), ((46, 43), 'Y'), ((46, 44), 'O'), ((46, 45), 'o'), ((46, 46), 'o'),
                 ((47, 43), 'O'), ((47, 44), 'o'), ((46, 47), 'G'), ((46, 48), 'G')):
        if q in part:
            part[q] = k
    for q in ((48, 60), (49, 61), (50, 61), (53, 60), (54, 61)):       # creases where he sits
        if part.get(q) == 'P':
            part[q] = 'q'
    for q, k in {(53, 41): 'W', (55, 44): '9'}.items():                   # dandruff on his shoulder
        if q in part:
            part[q] = k
    return part


def sleeve_side(root=(52.2, 41.4), elbow=(47.6, 51.6), length=4.6 * V.SLEEVE_LEN, half=V.SLEEVE_HALF):
    """The near sleeve side-on, fitted like the fight sheets' (a pixel of cloth either side of the arm,
    ending under half way down the upper arm; the skinny build's half 2.0 and 0.85 of the fitted
    length): a snug tube round the top of the arm, rendered as jfit_body.sleeve renders (lit rim, dark
    underside, trim)."""
    ux, uy = F._unit(elbow[0] - root[0], elbow[1] - root[1])
    a = (root[0] - ux * 1.4, root[1] - uy * 1.4)
    b = (root[0] + ux * length, root[1] + uy * length)
    s = B.fill(B.capsule(a, b, half + 0.2, half), 'R')
    B.rim(s, 'T', -1, 0)
    B.rim(s, 'V', 1, 0)
    B.rim(s, 'v', 0, 1, only='RV')
    for (x, y) in list(s):
        if (x + 0.5 - a[0]) * ux + (y + 0.5 - a[1]) * uy >= length + 1.4 - 0.9:
            s[(x, y)] = '1'
    return s


def legs_side():
    cv = B.Canvas(96, 96)
    # skinny (2026-09-28): the same joints, thinner as jfc_front.legs (thighs 0.6 off the radius, shins
    # 0.5, the knees and the bunched hems 0.4)
    far = F.jeans_limb([((51.0, 61.6), (38.0, 63.2), 2.2, 1.9), ((38.0, 63.2), (37.6, 84.0), 1.6, 1.5),
                        ((37.6, 84.0), (37.4, 86.4), 2.2, 2.5)], knobs=((37.8, 63.4, 1.9),))
    near = F.jeans_limb([((54.0, 62.8), (39.4, 65.4), 2.6, 2.2), ((39.4, 65.4), (39.2, 87.0), 1.7, 1.6),
                         ((39.2, 87.0), (39.0, 89.6), 2.3, 2.6)], knobs=((39.0, 65.6, 2.2),))
    cv.stamp(B.shift(far, -2, -1))
    cv.stamp(near)
    px = cv.px
    for q in ((38, 63), (39, 63), (40, 63)):
        if px.get(q) in ('N', 'n'):
            px[q] = 's'
    return px


def shoes_side():
    far, near = F.shoes()
    return [B.shift(far, -3, -2), B.shift(near, -3, -1)]


# his left hand dragging the cup down to his collarbone, knuckles to us (the lit side)
HAND_PULL = [
    "..kkkk.",
    ".kdedck",
    "kdeddck",
    "kddccbk",
    ".kcbbk.",
    "..kkk..",
]


def frame_swivel():
    cv = B.Canvas(B.FW, B.FH)
    yaw = -100
    parts = {}
    for n, p, d in C.solids(yaw):
        if n in ('back', 'seat', 'pad-1', 'pad+1', 'bolster-1', 'bolster+1'):
            C.pad(p)
        parts[n] = (p, d)
    for n in sorted(parts, key=lambda n: -parts[n][1]):
        cv.stamp(parts[n][0])
    for q, k in C.decals(yaw).items():
        if q in parts['back'][0] and cv.px.get(q) not in (None, 'k'):
            cv.px[q] = k
    at = lambda p: B.shift(p, *B.OFF)  # noqa: E731
    for s in shoes_side():
        cv.stamp(at(s), outline=False)
    cv.stamp(at(legs_side()), outline=False)
    neck = B.fill(B.poly([(46.6, 31.0), (51.4, 31.0), (51.8, 39.0), (46.2, 39.0)]), 'c')
    B.rim(neck, 'd', -1, 0)
    B.rim(neck, 'b', 1, 0)
    cv.stamp(at(neck))
    cv.stamp(at(tee_side()))
    hd = profile_head(4, -6)
    cv.stamp(at(hd), outline=False)
    # the band round the back of his neck, the near cup dragged onto his collarbone
    band = {(x, 33): '2' for x in range(49, 55)}
    band.update({(x, 32): '3' for x in range(49, 54)})
    cv.stamp(at(band))
    cup = B.amap(B.rows_of(F.CUP_NEAR), 43, 33)
    cv.stamp(at(cup), outline=False)
    arm = B.limb([((52.2, 41.4), (47.6, 51.6), 1.5, 1.4), ((47.6, 51.6), (44.6, 40.6), 1.4, 1.25)],
                 knobs=((47.6, 51.8, 1.8),))
    cv.stamp(at(arm))
    cv.stamp(at(sleeve_side()))
    cv.stamp(at(B.close_gaps(B.amap(B.rows_of(HAND_PULL), 41, 36))), outline=False)
    lines = speed_lines([(64, 24, 9, 'W'), (66, 30, 11, 'W'), (65, 48, 8, 'W'), (63, 62, 10, 'W'),
                         (62, 70, 7, 'W'), (20, 60, 6, '9'), (22, 76, 5, '9')])
    fx = set()
    for (x, y), k in lines.items():
        q = (x + B.OFF[0], y + B.OFF[1])
        if q not in cv.px:
            cv.px[q] = k
            fx.add(q)
    return cv, fx


#FRAME 10: THE EMPTY CHAIR

def frame_empty():
    cv = B.Canvas(B.FW, B.FH)
    F.chair_back(cv)
    return cv, set()


def builders():
    return [frame_tapped, frame_swivel]


def frames():
    return [(cv.px, fx) for cv, fx in (b() for b in builders())]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames() + [(frame_empty()[0].px, set())]):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: round(v, 4) if isinstance(v, float) else v for k, v in st.items()},
              {k: (len(v) if isinstance(v, list) else v) for k, v in a.items()})
