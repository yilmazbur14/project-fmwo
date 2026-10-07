"""Jordan's parts for the kaiju-fight sheets, all in the rig's BUILD coordinates (96x96 build space:
soles on row 95 standing, body centre x ~49, head offset (3, 2) as v2's idle).

Every part is the approved rig's own (the scratch copy in vendor/): v2's limb() / sleeves / tee / neck
/ jeans, the redesign rig's sneakers, box and fist maps, janim_heads' expressions, jr_ride's seated legs
and open box. What is NEW here is marked NEW: a few hand maps, face rows and hair maps, written the way
the rig writes its own (whole replacement rows over the approved head; maps in the rig's keys).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_ride as R    # noqa: E402

JB, JH, JBX = C.JB, C.JH, C.JBX
V = C.V
J = JB.jordan
RH = JB.rig_head
V2H = JB.jv2_head
amap, fill, poly, rim, stroke, ellipse = C.amap, C.fill, C.poly, C.rim, C.stroke, C.ellipse
shift = C.shift
rows_of = JB.rows_of
capsule = JB.capsule

HEAD_AT = (3, 2)                 # v2's idle head offset (the rider's)
NECK_PIVOT = (45, 33)            # head space: the top of the neck behind the jaw
NEAR_ROOT = V.NEAR_ROOT          # (40.6, 49.2) near shoulder joint
FAR_ROOT = V.FAR_ROOT            # (57.8, 48.5) far shoulder joint
SEAT_PT = (49, 70)               # the texel he sits on (the approved rider's JORDAN_SEAT)


#CANVAS

class Fig:
    """A build canvas plus the effect pixels and named anchor points of one frame."""

    def __init__(self):
        self.cv = C.Canvas(200, 200)
        self.fx = set()
        self.pts = {}

    def stamp(self, part, outline=True, name=None):
        self.cv.stamp(part, outline=outline)
        if name:
            self.pts[name] = part
        return part

    def stamp_all(self, parts):
        for part, ol in parts:
            self.cv.stamp(part, outline=ol)

    def fxput(self, part, under=False):
        """Effect pixels (no keyline). under=True only fills empty pixels (behind the figure)."""
        for q, k in part.items():
            if under and q in self.cv.px:
                continue
            self.cv.px[q] = k
            self.fx.add(q)

    @property
    def px(self):
        return self.cv.px


#HEADS

def face_rows(name):
    if name in FACES:
        return FACES[name]
    return JH.rows(name)


def hair_part(name, flopped=False):
    if name in HAIRS:
        return HAIRS[name]()
    if flopped:
        return JH._flopped_hair()
    return V2H.hair()


def head(face='idle', hair=None, dx=0, dy=0, tilt=0, pivot=NECK_PIVOT):
    """A head: face rows (row 22 down) under a hair map, as janim_heads.head builds it, tilted by
    `tilt` degrees (clockwise +) with the rig's tilt2 about the neck, then moved to (dx, dy)."""
    rows = face_rows(face)
    part = {q: k for q, k in amap(rows, RH.X0, RH.Y0).items() if q[1] >= 22}
    if hair is None:
        hair = 'flopped' if face in JH.FLOPPED else 'v2'
    part.update(hair_part(hair, flopped=(hair == 'flopped')))
    part.update(JH.ROW21.get(face, {}))
    part.update(ROW21.get(face, {}))
    if tilt:
        part = JB.tilt2(part, tilt, pivot, 'xy')
        JB.close_gaps(part)
    return shift(part, dx, dy)


def over(base, repl):
    return JH.over(base, repl)


# NEW faces (whole replacement rows in head space, x 37..59 from row 10; the approved face's own
# pixels everywhere else).
# YELP: knocked off, wide eyes (the DAZE eyes with the pupils back together), the laugh's dropped jaw
# for a yell, brows shot up.
YELP = over(JH.LAUGH, {
    21: ".kijj ihiii iiide djiii ik.",
    22: ".kijj idhhh hhhhd echhh hk.",
    23: ".kiji hcccc cccdd edccc ck.",
    24: ".kdci icccc cccdd edccc ck.",
    25: "kdbci ickkk kkkdd eckkk ck.",
    26: "kdaci jcWWW hWddd ecWhW ck.",
    27: "kdbci jcdcc ccddd ebccd ck.",
})
# DIZZY: the juggle's swirl eyes (its KO patch) over the DAZE face (jaw hanging, the flopped quiff).
_SWIRL_NEAR = [".kkk.", "kWWWk", "kWkWk", "kWWkk", ".kk.."]
_SWIRL_FAR = [".kk.", "kWWk", "kWkk", "kWWk", ".kk."]


def _patch(rows, spans):
    out = [list(r) for r in rows]
    for y, i0, keys in spans:
        for j, ch in enumerate(keys):
            if ch != '.':
                out[y - RH.Y0][i0 + j] = ch
    return [''.join(r) for r in out]


DIZZY = _patch(JH.DAZE, [(24 + r, 8, row) for r, row in enumerate(_SWIRL_NEAR)]
               + [(24 + r, 16, row) for r, row in enumerate(_SWIRL_FAR)])
# DIZZY_B: the same with the swirls wound the other way (mirrored), so a 2-step loop spins them.
DIZZY_B = _patch(JH.DAZE, [(24 + r, 8, row[::-1]) for r, row in enumerate(_SWIRL_NEAR)]
                 + [(24 + r, 16, row[::-1]) for r, row in enumerate(_SWIRL_FAR)])
# SMUG: the admire face looking ahead (the idle's eyes) with the curled mouth kept.
SMUG = over(JH.IDLE, {31: "...ki jjclj dbkkk kkbbj ik."})

FACES = {'yelp': YELP, 'dizzy': DIZZY, 'dizzy_b': DIZZY_B, 'smug': SMUG}
ROW21 = {'yelp': {(x, 21): 'i' for x in list(range(44, 50)) + list(range(54, 58))}}


#HAIR (NEW maps, the rig's keys; v2's back of the head and rat-tail kept, the quiff blown back)

def _hair_map(rows, x0, y0, tail=True):
    rows = rows_of(rows)
    part = amap(rows, x0, y0)
    if tail:
        part.update(V2H.TAIL_TIP)
    return part


# WHIP_A / WHIP_B: the leap's wind: the greasy quiff blown back over the crown into a clump streaming
# off the back of his head, two loose strands whipping behind it. Columns x 29..61, rows 6..21. Rows
# 15-21 (the face edge and the forelock) are v2's own; only the dome and the streaming clumps change.
WHIP_A = [
    # x: 29-33 34-38 39-43 44-48 49-53 54-58 59-61   y
    "..... ..... ..... ..... ..... ..... ...",   # 6
    "..... ..... ..... ..... ..... ..... ...",   # 7
    "..... ..... ..... ..... ..... ..... ...",   # 8
    "kk... ..... ..... ..... ..... ..... ...",   # 9
    ".jkk. ..... ..... ..kkk kkk.. ..... ...",   # 10  the stray strands lift off behind
    "..kjk kk... ..kkk kkAYA hjkkk ..... ...",   # 11  the quiff laid back flat along the crown,
    "...kl jjkkk kkjAY Alhjj ihlAk k.... ...",   # 12  its shine band dragged back with it
    "....k ljjli jlYAh jhiljh ijAk k... ...",    # 13
    "..... kjkij AYAhj ljhil jhihi k.... ...",   # 14
    "..... ..k.k kAmhi ljhil jhWlj hihhk ...",   # 15  v2's own from here down
    "..... ...kk kmjhi lWhim jhilj hihhk ...",   # 16
    "..... ..kjl ihjWi hjmih jlihj Whhk. ...",   # 17
    "..... .kihj ijiih iijii hiihh ihk.. ...",   # 18
    "..... kikii Wijhc ciidd kjmAj ihk.. ...",   # 19
    "..... kjkii ijhde eeied kjAik cbk.. ...",   # 20
    "..... kikij jihde eeehe dkkdd cbk.. ...",   # 21
]


def _check_rows(rows, width):
    rr = rows_of(rows)
    for i, r in enumerate(rr):
        if len(r) != width:
            raise ValueError('row %d is %d wide: %r' % (i, len(r), r))
    return rr


HAIRS = {}


import jr_hair  # noqa: E402
HAIRS.update({'whip_a': jr_hair.whip_a, 'whip_b': jr_hair.whip_b})


#ARMS

def ik(shoulder, wrist, l1, l2, bend=1):
    """The elbow for a two-bone arm from `shoulder` to `wrist` (upper l1, fore l2). bend=+1 puts the
    elbow on the clockwise side of shoulder->wrist (below it for an arm reaching right), -1 the other.
    A wrist out of reach straightens the arm toward it."""
    sx, sy = shoulder
    wx, wy = wrist
    dx, dy = wx - sx, wy - sy
    d = math.hypot(dx, dy) or 1e-6
    d2 = min(d, l1 + l2 - 1e-6)
    a = (l1 * l1 - l2 * l2 + d2 * d2) / (2 * d2)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    px_, py_ = sx + ux * a, sy + uy * a
    nx, ny = -uy, ux                      # clockwise normal on screen (y down)
    return (px_ + nx * h * bend, py_ + ny * h * bend)


UPPER_L, FORE_L = 11.0, 8.3              # v2's near arm: shoulder-elbow 11.4, elbow-wrist 8.3


def near_arm(shoulder, elbow, wrist, r=(1.55, 1.45, 1.3), knob=1.9, sleeve=True):
    """His near (lit) stick arm: v2's limb() through shoulder, elbow, wrist; the fitted sleeve."""
    arm = V.limb([(shoulder, elbow, r[0], r[1]), (elbow, wrist, r[1], r[2])],
                 knobs=((elbow[0], elbow[1] + 0.2, knob),))
    parts = [(arm, True)]
    if sleeve:
        parts.append((V.near_sleeve(shoulder, elbow), True))
    return parts


def far_arm(shoulder, elbow, wrist, r=(1.5, 1.4, 1.25), knob=1.8, sleeve=True):
    """His far (shadow side) stick arm, v2's far-arm ramp, the far fitted sleeve."""
    arm = V.limb([(shoulder, elbow, r[0], r[1]), (elbow, wrist, r[1], r[2])],
                 knobs=((elbow[0], elbow[1] + 0.2, knob),), base='c', lit='d', shade='b')
    parts = [(arm, True)]
    if sleeve:
        sl = V.far_sleeve(shoulder, elbow)
        parts.append((sl, True))
    return parts


def far_arm_box(dx=0, dy=0):
    """v2's far arm holding the box up beside his face, moved by (dx, dy)."""
    return [(shift(p, dx, dy), ol) for p, ol in V.far_arm_box()]


def near_arm_hip(dx=0, dy=0):
    return [(shift(p, dx, dy), ol) for p, ol in V.near_arm_hip()]


def far_hand_box(dx=0, dy=0):
    """v2's far hand wrapped over the box's base corner, at the approved spot moved by (dx, dy)."""
    return amap(V.FAR_HAND_BOX, JB.V2F.FAR_HAND_AT[0] + dx, JB.V2F.FAR_HAND_AT[1] + dy)


def open_box(dx=0, dy=0):
    """The rider's open box (window panel swung out, tray empty), moved by (dx, dy) from the approved spot."""
    return R.open_box(dx, dy)


def map_at(rows, x, y):
    return amap(rows_of(rows), int(round(x)), int(round(y)))


#HANDS (rig maps, and NEW ones in the rig's skin keys)

FIST_UP = JB.rows_of(["..kkkk.", ".kebedk", "kdbdbck", "kddddck", "kkkkdck", "keedkbk", ".kdckk.", "..kdk.."])
BAND = ["kkkkkkk", "kQPPPqk", "kQPPqqk", "kkkkkkk"]
# the redesign rig's raised fist (palm out), the summon's FIST_UP with its wrist
FIST_UP_FULL = [".kkkkkkk.", "kebebdbdk", "kebdbdbck", "kdbdbdbck", "kddddddck", "kkkkkdcbk", "keeedkcbk",
                ".kddckbk.", "..kkkkk.."]
FIST_SIDE = [".kkkkk.", "kdeeedk", "kkkkkdk", "kdbdbck", "kdbdbck", "kcbcbbk", ".kkkkk."]
FIST_HANG = [".kkkkk.", "kdeeddk", "kdddddk", "kcdddck", "kbcbcbk", "kbkbkbk", ".kkkkk."]
HAND_HANG = [".kdk..", "kddck.", "kdddck", "kddcbk", ".kcbk.", "..kk.."]
HAND_HANG_FAR = ["..kdk.", ".kcddk", "kcdddk", "kbccdk", ".kbcbk", "..kkk."]
HAND_OPEN_BACK = [".k.....", "kek.k..", ".kdkek.", "kedddkk", ".kcdddk", "kecdcck", ".kkkkk."]
# NEW: reaching into the box: the wrist in from the left, knuckles up, fingers dipping into the tray
REACH = [
    ".kkkk...",
    "kdeedkk.",
    "kcdddedk",
    "kbcdddck",
    ".kkbcdck",
    "...kcck.",
    "...kbk..",
    "....k...",
]
# NEW: thrown open, palm forward: the wrist on the left, fingers splayed out to the right
PALM_FWD = [
    "...k.k..",
    "..kekek.",
    ".kdedekk",
    "kdddddek",
    "kcdddddk",
    "kbcddck.",
    ".kbcck..",
    "..kkk...",
]
# NEW: palm up, fingers curled round something held up (the toy goes on top of it)
PALM_UP = [
    "kkkkkkk.",
    "kedddekk",
    "kdeddddk",
    "kcdddcbk",
    ".kbccbk.",
    "..kddk..",
    "..kdck..",
]
# NEW: a hand flat on the mat, fingers forward (right), propping him up
HAND_FLAT = [
    ".kkkk...",
    "kdeedkkk",
    "kcdddddk",
    "kkkkkkkk",
]
