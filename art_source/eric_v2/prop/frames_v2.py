"""Designer A frames for eric_sheet_v2 (256x192): 0-12 earthquake + post-slam, 21-26 idle, 27-31 downed.
Same beats as the approved v1 frames, re-fitted to the 75 px body and the 1.25x blade."""
import rig2 as R
import fx2 as FX
import scaled as SC

FRAMES = {}


def frame(i):
    def deco(fn):
        FRAMES[i] = fn
        return fn
    return deco


def body(fr, U=(0, 0), S=(0, 0), H=(0, 0), cape=None, torso=None, head=None, skip=(), hooks=None, off=None):
    extra = {}
    if cape is not None:
        extra['cape'] = R.cape_layer(*cape)
    if torso is not None:
        extra['torso'] = R.torso_layer(*torso)
    if head:
        extra['head'] = R.head_layer(head)
    o = {'upper': U, 'shoulders': S, 'headx': H}
    o.update(off or {})
    R.compose(fr, o, skip=skip, extra=extra, hooks=hooks)


def upper_arm(fr, a, b, w=9):
    R.limb(fr, a, b, w, ramp='chain')


def fore_arm(fr, elbow, wrist, w=9):
    R.limb(fr, elbow, wrist, w, ramp='plate')
    R.cop(fr, elbow, 4.6, 4.4)


def head_only(fr, U, S, H, kind=None):
    fr.put96(R.head_layer(kind), U[0] + S[0] + H[0], U[1] + S[1] + H[1])


# ================================================================== idle 21-24 + variants 25-26
@frame(21)
def idle0():
    return R.base_idle()


@frame(22)
def idle1():
    fr = R.Frame()
    body(fr, U=(0, 1), cape=(0.5, 0, 0))
    R.idle_weapon(fr, arm_dy=1)
    return fr


@frame(23)
def idle2():
    fr = R.Frame()
    body(fr, U=(0, 1), S=(0, 1), cape=(1.0, 0.3, 0), torso=(0.8, 0.0))
    R.idle_weapon(fr, arm_dy=1)
    return fr


@frame(24)
def idle3():
    fr = R.Frame()
    body(fr, U=(0, 1), cape=(0.5, 0, 0))
    R.idle_weapon(fr, arm_dy=1)
    return fr


@frame(25)
def idle_shift():
    fr = R.Frame()
    body(fr, U=(-1, 1), cape=(-1.0, 0, 0))
    R.idle_weapon(fr, dy=-2, arm_dx=-1, arm_dy=0)
    return fr


@frame(26)
def idle_regrip():
    fr = R.Frame()
    body(fr, U=(1, 0), cape=(0.8, 0, 0))
    R.idle_weapon(fr, dy=1, arm_dy=1)
    return fr


# ================================================================== earthquake 0-10, post-slam 11-12
@frame(0)
def eq_ready():
    fr = R.Frame()
    body(fr, U=(0, 1), cape=(0.5, 0.5, 0))
    R.idle_weapon(fr, dy=-1, arm_dy=1, fist_dy=-1)
    return fr


@frame(1)
def eq_dip():
    fr = R.Frame()
    U, S = (0, 2), (0, 1)
    body(fr, U=U, S=S, cape=(0, 2.0, 0), torso=(1.2, 0.4), skip=('head',),
         hooks={'paulL': lambda f: upper_arm(f, (109, 158), (108, 170))})
    fore_arm(fr, (108, 170), (98, 163))
    R.sword(fr, (96, 153), (-14, -74))
    head_only(fr, U, S, (0, 0), 'strain')
    R.fist(fr, 98, 162)
    return fr


@frame(2)
def eq_heave():
    fr = R.Frame()
    U, S = (0, -2), (0, -2)
    FX.smear_arc(fr, (98, 146), 104, 2, 9, 238, 266)

    def ua(f):
        upper_arm(f, (147, 150), (162, 152))
        upper_arm(f, (110, 152), (98, 158))
    body(fr, U=U, S=S, cape=(0, 1.2, 2.5), skip=('head', 'armR_front'), hooks={'paulL': ua})
    fore_arm(fr, (162, 152), (160, 141))
    fore_arm(fr, (98, 158), (98, 148))
    R.sword(fr, (98, 138), (-4, -61))
    head_only(fr, U, S, (0, 0), 'strain')
    R.fist(fr, 98, 144)
    R.fist(fr, 160, 138)
    return fr


def hoist(tremble=(0, 0), glint_x=None, drops=(), marks=False, sag=0):
    fr = R.Frame()
    U, S, H = (0, -1), (0, -2), (0, 2)
    tx, ty = tremble

    def ua(f):
        upper_arm(f, (110, 148), (97, 138))
        upper_arm(f, (146, 148), (161, 139))
    body(fr, U=U, S=S, cape=(0, 1.2, 1.6), skip=('head', 'armR_front'), hooks={'paulL': ua})
    fore_arm(fr, (97, 138), (98 + tx, 124 + ty + sag))
    fore_arm(fr, (161, 139), (157 + tx, 134 + ty + sag))
    R.sword(fr, (106 + tx, 117 + ty + sag), (1.0, 0.0))
    if glint_x is not None:
        FX.glint(fr, glint_x + tx, 110 + ty + sag)
    head_only(fr, U, S, H, 'strain')
    R.fist(fr, 98 + tx, 118 + ty + sag, horizontal=True)
    R.fist(fr, 157 + tx, 131 + ty + sag)
    if marks:
        FX.strain_marks(fr, 90 + tx, 113 + ty, flip=True)
        FX.strain_marks(fr, 165 + tx, 127 + ty)
    for x, y in drops:
        FX.sweat(fr, x, y)
    return fr


@frame(3)
def eq_hold0():
    return hoist(glint_x=126)


@frame(4)
def eq_hold1():
    return hoist(tremble=(1, 0), glint_x=160, drops=[(146, 124)], marks=True)


@frame(5)
def eq_hold2():
    return hoist(tremble=(0, 1), glint_x=196, drops=[(149, 129), (108, 121)], marks=True)


@frame(6)
def eq_slam():
    fr = R.Frame()
    U, S = (-2, 2), (0, 1)
    FX.smear_arc(fr, (126, 147), 100, 3, 20, -40, -206)
    body(fr, U=U, S=S, cape=(2.0, 0.8, 0), torso=(0.8, 0.4), skip=('head',),
         hooks={'paulL': lambda f: upper_arm(f, (109, 158), (102, 168))})
    fore_arm(fr, (102, 168), (109, 162))
    head_only(fr, U, S, (0, 0), 'strain')
    R.sword(fr, (106, 166), (-0.88, 0.47), blade_len=46, grip_len=12)
    R.fist(fr, 112, 163)
    return fr


PLANT_X, PLANT_GUARD_Y = 93, 140          # planted blade: guard high so half the slab shows


def planted_body(fr, U=(-1, 2), S=(0, 1), kind=None, torso=(0.8, 0.4), cape=(0.8, 0, 0)):
    body(fr, U=U, S=S, cape=cape, torso=torso, skip=('head',),
         hooks={'paulL': lambda f: upper_arm(f, (109, 157 + U[1]), (101, 151 + U[1]))})
    head_only(fr, U, S, (0, 0), kind)


def planted_sword(fr, dy=0):
    R.sword(fr, (PLANT_X, PLANT_GUARD_Y), (0, 1), blade_len=191 - PLANT_GUARD_Y - 5)
    fore_arm(fr, (104, 150 + dy), (96, 134 + dy))          # reaches over the guard to the grip
    R.fist(fr, PLANT_X, 130 + dy)


def ground_cracks(fr, big=False):
    FX.crack(fr, [(93, 191), (83, 187), (74, 189), (64, 186)] + ([(52, 189)] if big else []))
    FX.crack(fr, [(94, 191), (105, 188), (113, 190), (122, 187)] + ([(134, 189)] if big else []))


@frame(7)
def eq_driven():
    fr = R.Frame()
    planted_body(fr, kind='strain')
    planted_sword(fr, dy=2)
    ground_cracks(fr)
    FX.rock(fr, 72, 180)
    FX.rock(fr, 114, 182)
    return fr


@frame(8)
def eq_burst():
    fr = R.Frame()
    planted_body(fr, U=(-1, 3), kind='strain', torso=(1.2, 0.8))
    planted_sword(fr, dy=3)
    FX.ellipse_fill(fr, 93, 189, 30, 8, 'A')
    FX.ellipse_fill(fr, 93, 189, 22, 6, 'W')
    import math
    for ang, ln, w in [(-90, 50, 3.4), (-62, 42, 3.0), (-118, 42, 3.0), (-38, 34, 2.4), (-142, 32, 2.4),
                       (-15, 28, 2.0), (-165, 26, 2.0)]:
        a = math.radians(ang)
        FX.ray(fr, (93, 188), (93 + math.cos(a) * ln, 188 + math.sin(a) * ln), w)
    for x, y in [(66, 150), (122, 156), (130, 176), (58, 172), (112, 138)]:
        FX.sparkle(fr, x, y, 2)
    R.fist(fr, PLANT_X, 133, shadow=False)
    return fr


@frame(9)
def eq_shock():
    fr = R.Frame()
    planted_body(fr, U=(-1, 2), kind='strain')
    planted_sword(fr, dy=2)
    FX.shock_arcs(fr, 93, [(22, 150, 11), (42, 158, 17), (64, 165, 22)])
    ground_cracks(fr, big=True)
    for x, y in [(66, 160), (118, 156), (138, 170), (78, 148), (190, 172), (100, 172)]:
        FX.rock(fr, x, y)
    for x, y in [(150, 162), (214, 168), (36, 176)]:
        FX.sparkle(fr, x, y, 1)
    return fr


@frame(10)
def eq_settle():
    fr = R.Frame()
    planted_body(fr, U=(-1, 1))
    planted_sword(fr, dy=1)
    ground_cracks(fr, big=True)
    for x, y, s in [(58, 182, False), (68, 186, False), (98, 184, False), (108, 187, False),
                    (74, 174, True), (116, 176, True), (132, 186, True), (46, 186, True)]:
        FX.puff(fr, x, y, small=s)
    for x, y in [(70, 158), (114, 152), (128, 168), (82, 146)]:
        fr.set(x, y, 'g')
        fr.set(x, y - 1, 'G')
    return fr


@frame(11)
def eq_grip():
    fr = R.Frame()
    planted_body(fr, U=(-1, 1), torso=(0.4, 0.0))
    planted_sword(fr, dy=1)
    ground_cracks(fr)
    FX.puff(fr, 106, 186, small=True)
    return fr


@frame(12)
def eq_wrench():
    fr = R.Frame()
    FX.smear_arc(fr, (98, 176), 36, 1, 6, 212, 262)
    body(fr, U=(0, 1), cape=(-1.0, 0.5, 0), skip=('head',),
         hooks={'paulL': lambda f: upper_arm(f, (109, 158), (108, 168))})
    head_only(fr, (0, 1), (0, 0), (0, 0))
    fore_arm(fr, (108, 168), (98, 158))
    R.sword(fr, (95, 150), (-14, -80))
    R.fist(fr, 97, 158)
    for x, y in [(70, 110), (108, 124), (72, 138), (110, 98)]:
        FX.clod(fr, x, y)
    return fr


# ================================================================== downed 27-31 (loop)
SOLE = """
..kkkkkkk
.kDDDEEEk
kCCDDDEEk
kkkkkkkkk
"""


def downed(U, S, H, drops=(), torso=(0.0, 0.0), knee_bob=0):
    fr = R.Frame()
    L = R.layers()
    tl = R.split_layer(L['tassets'], 48, True)
    tr = R.split_layer(L['tassets'], 48, False)
    by = U[1]
    fr.put96(R.cape_kneel(flare=5.0), U[0], 5)
    fr.stamp(SOLE, 157, 188)
    fr.put96(L['flap'], 0, 3)
    fr.put96(tr, U[0], by + 1)
    R.cop(fr, (141, 188), 6.8, 3.7)
    R.compose(fr, {'upper': U, 'shoulders': S, 'headx': H},
              skip=('cape', 'legs', 'flap', 'tassets', 'head', 'armR_front'),
              extra={'torso': R.torso_layer(*torso)})
    fr.put96(tl, U[0] - 2, by - 3)
    fr.stamp('\n'.join(SC.LEG_L[2:]), 97, 186)
    R.limb(fr, (108, 179 + knee_bob), (108, 187), 10, ramp='plate')
    R.cop(fr, (108, 178 + knee_bob), 6.6, 5.1)
    k = by - 6
    R.limb(fr, (157, 166 + k), (153, 178), 9, ramp='plate')
    R.cop(fr, (157, 166 + k), 4.6, 4.4)
    R.fist(fr, 152, 180)
    R.sword(fr, (90, 152), (0, 1), blade_len=191 - 152 - 5)
    fore_arm(fr, (104, 162 + k), (93, 146 + k))
    fr.put96(R.head_layer('tired'), U[0] + S[0] + H[0], U[1] + S[1] + H[1])
    R.fist(fr, 90, 142 + k)
    for x, y in drops:
        FX.sweat(fr, x, y)
    return fr


@frame(27)
def down0():
    return downed((-1, 5), (0, 0), (0, 1), drops=[(147, 134)])


@frame(28)
def down1():
    return downed((-1, 6), (0, 1), (0, 2), drops=[(149, 139)], torso=(0.4, 0.0))


@frame(29)
def down2():
    return downed((-1, 7), (0, 1), (0, 3), drops=[(150, 145), (108, 138)], torso=(0.8, 0.4))


@frame(30)
def down3():
    return downed((-1, 6), (0, 1), (0, 2), drops=[(108, 143)], torso=(0.4, 0.0))


@frame(31)
def down4():
    return downed((-1, 5), (0, 0), (0, 1), drops=[(107, 148)])
