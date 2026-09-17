"""Eric redesign animation frames owned by designer A (indices 0-12, 21-31)."""
import math
import rig  # noqa
import variants as V
import approved_weapon as AW

FRAMES = {}


def frame(i):
    def deco(fn):
        FRAMES[i] = fn
        return fn
    return deco


def body(fr, upper=(0, 0), shoulders=(0, 0), headx=(0, 0), cape=None, torso=None, skip=(), extra=None, under_pauldrons=None):
    ex = dict(extra or {})
    if cape is not None:
        ex['cape'] = V.cape_layer(*cape)
    if torso is not None:
        ex['torso'] = V.torso_layer(*torso)
    hooks = {'paulL': under_pauldrons} if under_pauldrons else None
    rig.compose_body(fr, {'upper': upper, 'shoulders': shoulders, 'headx': headx}, skip=skip, extra=ex, hooks=hooks)


# ------------------------------------------------------------------ idle 21-24 (loop) + variants 25-26
@frame(21)
def idle0():
    fr = rig.Frame()
    body(fr)
    AW.draw(fr)
    return fr


@frame(22)
def idle1():
    fr = rig.Frame()
    body(fr, upper=(0, 1), cape=(0.6, 0, 0))
    AW.draw(fr, arm_dy=1)
    return fr


@frame(23)
def idle2():
    fr = rig.Frame()
    body(fr, upper=(0, 1), shoulders=(0, 1), cape=(1.2, 0.4, 0), torso=(1.0, 0.0))
    AW.draw(fr, arm_dy=1)
    return fr


@frame(24)
def idle3():
    fr = rig.Frame()
    body(fr, upper=(0, 1), cape=(0.6, 0, 0))
    AW.draw(fr, arm_dy=1)
    return fr


@frame(25)
def idle_shift():
    """weight shifts onto his sword side; he slides the grip up and lifts the blade a touch"""
    fr = rig.Frame()
    body(fr, upper=(-1, 1), headx=(0, 0), cape=(-1.2, 0, 0))
    AW.draw(fr, dx=0, dy=-2, arm_dx=-1, arm_dy=0)
    return fr


@frame(26)
def idle_regrip():
    """weight rolls back; the blade settles down into the re-set grip"""
    fr = rig.Frame()
    body(fr, upper=(1, 0), cape=(1.0, 0, 0))
    AW.draw(fr, dx=0, dy=1, arm_dx=0, arm_dy=1)
    return fr


# ================================================================== earthquake 0-10, transition 11-12
import fx


def head_put(fr, upper=(0, 0), shoulders=(0, 0), headx=(0, 0), kind=None):
    img = fx.head_variant(kind) if kind else rig.layers()['head']
    fr.put(img, upper[0] + shoulders[0] + headx[0], upper[1] + shoulders[1] + headx[1])


def arm_tube(fr, shoulder, elbow, wrist, chain_w=11, plate_w=11):
    rig.limb(fr, shoulder, elbow, chain_w, ramp='chain')
    rig.limb(fr, elbow, wrist, plate_w, ramp='plate')
    rig.cop(fr, elbow, 5.6, 5.4)


def upper_arm(fr, shoulder, elbow, w=11):
    rig.limb(fr, shoulder, elbow, w, ramp='chain')


def fore_arm(fr, elbow, wrist, w=11):
    rig.limb(fr, elbow, wrist, w, ramp='plate')
    rig.cop(fr, elbow, 5.6, 5.4)


@frame(0)
def eq_ready():
    """sets his feet, sinks a pixel, tightens the grip"""
    fr = rig.Frame()
    body(fr, upper=(0, 1), cape=(0.5, 0.5, 0))
    AW.draw(fr, dy=-1, arm_dy=1, fist_dy=-1)
    return fr


@frame(1)
def eq_dip():
    """big anticipation: sinks into the belly, cape flares, blade drawn back and down"""
    fr = rig.Frame()
    U, S = (0, 3), (0, 1)
    body(fr, upper=U, shoulders=S, cape=(0, 2.5, 0), torso=(1.5, 0.5), skip=('head', 'armL_back'),
         under_pauldrons=lambda fr: upper_arm(fr, (40, 86), (40, 104)))
    fore_arm(fr, (40, 104), (28, 106))
    rig.sword(fr, (26, 100), (12, 26))
    head_put(fr, U, S, kind='strain')
    rig.fist(fr, 28, 106)
    return fr


@frame(2)
def eq_heave():
    """heaves the slab up past his shoulder; body stretches, cape lifts"""
    fr = rig.Frame()
    U, S = (0, -2), (0, -2)
    # upward smear on the lit side of the rising blade
    fx.smear_arc(fr, (60, 96), 58, 2, 9, 205, 262)
    def ua(fr):
        upper_arm(fr, (88, 78), (106, 80))
        upper_arm(fr, (42, 80), (27, 88))
    body(fr, upper=U, shoulders=S, cape=(0, 1.5, 3), skip=('head', 'armR_front', 'armR_back', 'armL_back'), under_pauldrons=ua)
    # left arm (viewer right) coming up to take the blade
    fore_arm(fr, (106, 80), (104, 66))
    fore_arm(fr, (27, 88), (26, 74))
    rig.sword(fr, (26, 64), (22, 3))
    head_put(fr, U, S, kind='strain')
    rig.fist(fr, 26, 70)
    rig.fist(fr, 104, 62)
    return fr


def hoist(tremble=(0, 0), glint_x=None, drops=(), marks=False, sag=0):
    fr = rig.Frame()
    U, S, Hx = (0, -1), (0, -3), (0, 2)
    tx, ty = tremble
    # both arms raised; right hand on the grip, left hand shoving up under the flat of the blade
    def ua(fr):
        upper_arm(fr, (42, 74), (25, 60))
        upper_arm(fr, (86, 74), (105, 62))
    body(fr, upper=U, shoulders=S, cape=(0, 1.5, 2), skip=('head', 'armR_front', 'armR_back', 'armL_back'), under_pauldrons=ua)
    fore_arm(fr, (25, 60), (26 + tx, 42 + ty + sag))
    fore_arm(fr, (105, 62), (100 + tx, 54 + ty + sag))
    rig.sword(fr, (37 + tx, 35 + ty + sag), (123 + tx, 35 + ty + sag))
    if glint_x is not None:
        fx.glint(fr, glint_x + tx, 29 + ty + sag)
    head_put(fr, U, S, Hx, kind='strain')
    rig.fist(fr, 27 + tx, 36 + ty + sag, vertical=False)
    rig.fist(fr, 100 + tx, 51 + ty + sag)
    if marks:
        fx.strain_marks(fr, 18 + tx, 30 + ty, flip=True)
        fx.strain_marks(fr, 109 + tx, 47 + ty)
    for x, y in drops:
        fx.sweat(fr, x, y)
    return fr


@frame(3)
def eq_hold0():
    return hoist(glint_x=58)


@frame(4)
def eq_hold1():
    return hoist(tremble=(1, 0), glint_x=84, drops=[(86, 44)], marks=True)


@frame(5)
def eq_hold2():
    return hoist(tremble=(0, 1), glint_x=110, drops=[(90, 50), (40, 40)], marks=True)


def planted_body(fr, U=(-1, 3), S=(0, 1), kind=None, cape=(1.0, 0, 0), torso=(1.0, 0.5), dy=0):
    body(fr, upper=U, shoulders=S, cape=cape, torso=torso, skip=('head', 'armL_back'),
         under_pauldrons=lambda fr: upper_arm(fr, (40, 86 + dy), (38, 96 + dy)))
    head_put(fr, U, S, kind=kind)


def planted_sword(fr, dy=0):
    fore_arm(fr, (38, 96 + dy), (27, 82 + dy))
    rig.sword(fr, (24, 88), (24, 127))
    rig.fist(fr, 24, 76 + dy)


@frame(6)
def eq_slam():
    """the slam: slab whips over and down in front, huge white smear"""
    fr = rig.Frame()
    U, S = (-2, 3), (0, 1)
    fx.smear_arc(fr, (62, 72), 60, 3, 17, -40, -228)
    body(fr, upper=U, shoulders=S, cape=(2.5, 1.0, 0), torso=(1.0, 0.5), skip=('head', 'armL_back'),
         under_pauldrons=lambda fr: upper_arm(fr, (40, 86), (31, 99)))
    fore_arm(fr, (31, 99), (40, 90))
    head_put(fr, U, S, kind='strain')
    rig.sword(fr, (38, 94), (10, 116), grip_len=11)
    rig.fist(fr, 42, 90)
    return fr


@frame(7)
def eq_driven():
    """blade driven into the ground; body crunches down onto it"""
    fr = rig.Frame()
    planted_body(fr, kind='strain')
    planted_sword(fr)
    fx.crack(fr, [(24, 127), (16, 124), (10, 125), (4, 122)])
    fx.crack(fr, [(25, 127), (33, 125), (38, 126)])
    fx.rock(fr, 8, 116, small=True)
    fx.rock(fr, 38, 118, small=True)
    return fr


@frame(8)
def eq_burst():
    """big white impact burst at the blade"""
    fr = rig.Frame()
    planted_body(fr, U=(-1, 4), S=(0, 1), kind='strain', torso=(1.5, 1.0), dy=1)
    planted_sword(fr, dy=1)
    fx.ellipse_fill(fr, 24, 125, 22, 7, 'A')
    fx.ellipse_fill(fr, 24, 125, 16, 5, 'W')
    for ang, ln, w in [(-90, 38, 3.0), (-62, 32, 2.6), (-118, 32, 2.6), (-38, 26, 2.2), (-142, 24, 2.2),
                       (-15, 22, 1.8), (-165, 20, 1.8)]:
        a = math.radians(ang)
        fx.ray(fr, (24, 124), (24 + math.cos(a) * ln, 124 + math.sin(a) * ln), w)
    for x, y in [(6, 92), (46, 96), (52, 112), (2, 108), (40, 80)]:
        fx.sparkle(fr, x, y, 2)
    rig.fist(fr, 24, 77, shadow=False)
    return fr


@frame(9)
def eq_shock():
    """shock lines race along the ground, rocks kicked up"""
    fr = rig.Frame()
    planted_body(fr, U=(-1, 3), kind='strain')
    planted_sword(fr)
    # shock arcs racing outward along the ground from the blade
    for cx, r0, reach, lift in [(24, 18, 104, 9), (24, 34, 110, 14), (24, 52, 120, 18)]:
        for x in range(0, 128):
            d = abs(x - cx)
            if r0 <= d <= reach:
                t = (d - r0) / max(1, reach - r0)
                y = 126 - int(round(lift * (1 - t) * t * 2.2))
                fr.set(x, y, 'W')
                if t < 0.55:
                    fr.set(x, y + 1, 'A')
    fx.crack(fr, [(24, 127), (14, 123), (6, 125), (0, 121)])
    fx.crack(fr, [(25, 127), (36, 124), (46, 126), (54, 123)])
    for x, y, s in [(6, 104, False), (44, 100, False), (60, 108, True), (16, 94, True), (100, 110, True), (30, 110, True)]:
        fx.rock(fr, x, y, small=s)
    for x, y in [(70, 100), (116, 104), (2, 112)]:
        fx.sparkle(fr, x, y, 1)
    return fr


@frame(10)
def eq_settle():
    """dust rolls out and sparks drift down"""
    fr = rig.Frame()
    planted_body(fr, U=(-1, 2))
    planted_sword(fr)
    fx.crack(fr, [(24, 127), (14, 123), (6, 125), (0, 121)])
    fx.crack(fr, [(25, 127), (36, 124), (46, 126), (54, 123)])
    fx.puff(fr, 0, 114)
    fx.puff(fr, 8, 118)
    fx.puff(fr, 30, 116)
    fx.puff(fr, 38, 120)
    fx.puff(fr, 12, 106, small=True)
    fx.puff(fr, 44, 108, small=True)
    fx.puff(fr, 58, 120, small=True)
    for x, y in [(8, 96), (40, 92), (52, 104), (18, 86)]:
        fr.set(x, y, 'g')
        fr.set(x, y - 1, 'G')
    fx.rock(fr, 60, 122, small=True)
    return fr


@frame(11)
def eq_grip():
    """grips the planted hilt and straightens"""
    fr = rig.Frame()
    planted_body(fr, U=(-1, 1), torso=(0.5, 0))
    planted_sword(fr)
    fx.crack(fr, [(24, 127), (14, 123), (6, 125)])
    fx.crack(fr, [(25, 127), (36, 124), (46, 126)])
    fx.puff(fr, 34, 120, small=True)
    return fr


CLOD = """
.kk.
knok
.kk.
"""


@frame(12)
def eq_wrench():
    """wrenches the slab out and swings it back up onto his shoulder (leads into idle)"""
    fr = rig.Frame()
    fx.smear_arc(fr, (40, 112), 28, 1, 6, 210, 262)
    body(fr, upper=(0, 1), cape=(-1.0, 0.5, 0), skip=('head', 'armL_back'),
         under_pauldrons=lambda fr: upper_arm(fr, (40, 86), (40, 100)))
    head_put(fr, (0, 1))
    fore_arm(fr, (40, 100), (28, 98))
    rig.sword(fr, (26, 92), (12, 12))
    rig.fist(fr, 28, 98)
    for x, y in [(2, 44), (30, 56), (4, 70), (32, 34)]:
        fr.stamp(CLOD, x, y)
    return fr


# ================================================================== downed 27-31 (loop)
from legstamp import LEFT as LEG_LEFT


def split_layer(img, x_split, left=True):
    return [[(p if ((x < x_split) == left) else rig.T) for x, p in enumerate(row)] for row in img]


SOLE = """
..kkkkkkk
.kDDDEEEk
kCCDDDEEk
kkkkkkkkk
"""


def downed(U, S, H, drops=(), torso=(0.0, 0.0), knee_bob=0, breath=None):
    fr = rig.Frame()
    L = rig.layers()
    tl = split_layer(L['tassets'], 48, True)
    tr = split_layer(L['tassets'], 48, False)
    by = U[1]
    # back to front
    fr.put(V.cape_kneel(flare=5.0), U[0], 6)
    fr.stamp(SOLE, 101, 123)                                   # kneeling foot's sole behind him
    fr.put(L['flap'], 0, 4)
    fr.put(tr, U[0], by + 1)                                   # right tasset hangs to the ground
    rig.cop(fr, (81, 123), 8.5, 4.6)                           # right knee pressed into the ground
    def hook(fr):
        pass
    rig.compose_body(fr, {'upper': U, 'shoulders': S, 'headx': H},
                     skip=('cape', 'legs', 'flap', 'tassets', 'head', 'armR_back', 'armR_front', 'armL_back'),
                     extra={'torso': V.torso_layer(*torso)})
    # raised right knee (viewer left): tasset rides up on the thigh, knee cop out in front, shin to the foot
    fr.put(tl, U[0] - 2, by - 4)
    foot = chr(10).join(LEG_LEFT[4:])
    fr.stamp(foot, 25, 121)
    rig.limb(fr, (39, 112 + knee_bob), (39, 122), 13, ramp='plate')
    rig.cop(fr, (39, 111 + knee_bob), 8.2, 6.4)
    # free hand braced on the kneeling thigh
    rig.limb(fr, (100, 96 + by - 7), (96, 112), 11, ramp='plate')
    rig.cop(fr, (100, 97 + by - 7), 5.6, 5.4)
    rig.fist(fr, 94, 114)
    # leaning on the planted sword: arm out to the hilt
    fore_arm(fr, (36, 96 + by - 7), (27, 86 + by - 7))
    rig.sword(fr, (18, 98), (18, 127))
    head_put(fr, U, S, H, kind='tired')
    rig.fist(fr, 18, 83 + (by - 7))
    for x, y in drops:
        fx.sweat(fr, x, y)
    if breath:
        bx, by_ = breath
        fr.stamp(BREATH, bx, by_)
    return fr


BREATH = """
..BA.
.BAWA
BAWA.
.BA..
"""


@frame(27)
def down0():
    return downed((-1, 6), (0, 0), (0, 1), drops=[(88, 56)])


@frame(28)
def down1():
    return downed((-1, 7), (0, 1), (0, 2), drops=[(90, 62)], torso=(0.5, 0.0))


@frame(29)
def down2():
    return downed((-1, 8), (0, 1), (0, 3), drops=[(91, 69), (40, 60)], torso=(1.0, 0.5))


@frame(30)
def down3():
    return downed((-1, 7), (0, 1), (0, 2), drops=[(40, 66)], torso=(0.5, 0.0))


@frame(31)
def down4():
    return downed((-1, 6), (0, 0), (0, 1), drops=[(39, 73)])
