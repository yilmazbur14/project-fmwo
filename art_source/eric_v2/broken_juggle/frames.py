"""Every frame of eric_broken / eric_broken_sword / eric_juggle / eric_winded (256x192, Eric's frame space,
feet on row 191, body centred on x = 128). Built on the approved key poses in keys.py.

The planted greatsword is NOT drawn into eric_broken or eric_juggle: it is its own sprite (eric_broken_sword),
drawn behind Eric in his frame space so it can stay on the mat while he is juggled. Nothing of Eric's
cape overlaps the sword's footprint on the broken frames, so sprite-behind-Eric composites exactly like the
approved keys. eric_winded keeps its sword baked in (he never leaves it there).
"""
import math
import os
from PIL import Image

import jr
import body
import faces
import keys as K
import rig2 as R
import fx2 as FX
from jr import Layer, Tf, FW, FH
from lib import PALC, BLACK

ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/'
TUMBLE_C = (128.0, 146.0)          # fixed centre of the cartwheel
PLANT_X, PLANT_GUARD_Y, MOUND_GROUND = K.PLANT_X, K.PLANT_GUARD_Y, K.MOUND_GROUND


def J(tf, x, y):
    return tf.pt(x, y)


def render(pose):
    fr, L = body.render(pose)
    return fr, L


def centred_hip(ang, centre=TUMBLE_C, local=(48.0, 58.0)):
    tf0 = Tf(body.PELVIS96, (0, 0), ang)
    c = tf0.pt(*local)
    return (centre[0] - c[0], centre[1] - c[1])


def lowest_row(lay):
    for y in range(FH - 1, -1, -1):
        if any(p is not None for p in lay.px[y]):
            return y
    return -1


# ======================================================================= eric_broken (8)
def pooled(lay, p, left=104.0, right=168.0):
    K.pooled_cape(lay, p, left=left, right=right)


def impact_lines(lay, c, r0, r1, angs, sq=0.85):
    for a in angs:
        t = math.radians(a)
        p0 = (c[0] + math.cos(t) * r0, c[1] + math.sin(t) * r0 * sq)
        p1 = (c[0] + math.cos(t) * r1, c[1] + math.sin(t) * r1 * sq)
        K.speed_lines(lay, [(p0, p1)])


def broken_0():
    """reel a: the Break lands. A jolt: body flinches, eyes screwed shut, the sword hand springs open"""
    pose = dict(
        hip=(127.0, 177.0), ang=-3.0, expr='pain', head=(-8.0, 0.0, -1.0), torso=(0.8, 0.4),
        arms={
            'L': dict(elbow=(101.0, 151.0), wrist=(92.0, 142.0), hand='open', hand_ang=150.0, spread=1.7),
            'R': dict(elbow=(158.0, 158.0), wrist=(169.0, 151.0), hand='open', hand_ang=235.0, spread=1.6,
                      mirror=True),
        },
        legs={
            'L': dict(knee=(114.0, 183.0), ankle=(112.0, 186.0), foot_ang=0.0, fw=19.0),
            'R': dict(knee=(142.0, 183.0), ankle=(144.0, 186.0), foot_ang=0.0, fw=19.0),
        },
        cape=lambda lay, p: jr.cape_idle(lay, jr.about(body.torso_tf(p), (48, 44), -3.0)),
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def front(lay, p):
        impact_lines(lay, (128, 146), 58, 72, [-165, -140, -115, -65, -40, -15, 10, 170])
        FX.sweat(lay, 160, 116)
        FX.sweat(lay, 98, 120)
    pose['extra'] = {'front': front}
    return pose


def broken_1():
    """reel b: the approved reel key without the sword (the sword sprite is mid-flight)"""
    pose = K.reel_pose()
    ex = dict(pose['extra'])
    ex.pop('sword', None)
    pose['extra'] = ex
    return pose


def broken_2():
    """reel c: legs buckle, he pitches toward the sword as it hits the mat"""
    pose = dict(
        hip=(123.0, 181.0), ang=-9.0, expr='groggy', head=(-6.0, 0.0, 2.0), torso=(0.8, 0.4), shoulders=(0, 1),
        arms={
            'L': dict(elbow=(103.0, 166.0), wrist=(96.0, 174.0), hand='open', hand_ang=28.0, spread=1.2),
            'R': dict(elbow=(151.0, 172.0), wrist=(154.0, 181.0), hand='open', hand_ang=-12.0, spread=1.1,
                      mirror=True),
        },
        legs={
            'L': dict(knee=(113.0, 185.0), ankle=(109.0, 187.2), foot_ang=12.0, fw=17.0),
            'R': dict(knee=(140.0, 184.0), ankle=(144.0, 186.0), foot_ang=0.0, fw=19.0),
        },
        cape=K.idle_cape_on,
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def front(lay, p):
        FX.sweat(lay, 150, 120)
        FX.sweat(lay, 104, 126)
    pose['extra'] = {'front': front}
    return pose


def broken_3():
    """kneel a: drops onto one knee, reaching for the grip"""
    pose = dict(
        hip=(127.0, 182.0), ang=-5.0, expr='groggy', head=(-4.0, 0.0, 2.0), torso=(0.8, 0.4), shoulders=(0, 1),
        flare=5.0,
        arms={
            'L': dict(elbow=(101.0, 163.0), wrist=(95.0, 153.0), hand='open', hand_ang=148.0, spread=1.2),
            'R': dict(elbow=(157.0, 171.0), wrist=(150.0, 177.0), hand='fist'),
        },
        legs={
            'L': dict(kneel=True, knee=(113.0, 187.0), toe=(103.0, 189.0)),
            'R': dict(knee=(145.0, 177.0), ankle=(147.0, 186.0), foot_ang=0.0, fw=19.0),
        },
        cape=lambda lay, p: pooled(lay, p, right=166.0),
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'paulL', 'paulR', 'armR', 'head', 'front'],
    )

    def front(lay, p):
        FX.sweat(lay, 147, 126)
        FX.sweat(lay, 108, 132)
    pose['extra'] = {'front': front}
    return pose


def broken_4():
    """kneel b: both knees down, hanging on to the planted sword's grip (the approved kneel key)"""
    pose = K.kneel_pose()
    pose['cape'] = lambda lay, p: pooled(lay, p, right=166.0)
    pose['extra'] = {'front': pose['extra']['front']}
    pose['order'] = [n for n in pose['order'] if n != 'sword']
    return pose


def slumped(hip, ang, head, torso, shoulders, drop):
    pose = dict(
        hip=hip, ang=ang, expr='dazed', head=head, torso=torso, shoulders=shoulders, flare=9.0,
        arms={
            'L': dict(elbow=(108.0, 179.0 + shoulders[1] - 2), wrist=(104.0, 185.0), hand='open', hand_ang=18.0,
                      spread=1.2, curl=-1.0),
            'R': dict(elbow=(152.0, 180.0 + shoulders[1] - 2), wrist=(156.0, 185.0), hand='open', hand_ang=-18.0,
                      spread=1.2, curl=-1.0, mirror=True),
        },
        legs={
            'L': dict(kneel=True, knee=(114.0, 188.0), toe=(102.0, 189.0)),
            'R': dict(kneel=True, knee=(144.0, 188.0), toe=(156.0, 189.0)),
        },
        cape=lambda lay, p: pooled(lay, p, right=170.0),
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'paulL', 'paulR', 'armL', 'armR', 'head', 'front'],
    )

    def front(lay, p):
        FX.sweat(lay, *drop)
    pose['extra'] = {'front': front}
    return pose


def broken_5():
    return slumped((129.0, 186.0), 5.0, (13.0, 1.0, 3.0), (1.2, 0.8), (0, 2), (150, 132))


def broken_6():
    return slumped((129.0, 187.0), 7.0, (17.0, 2.0, 4.0), (1.4, 1.0), (0, 3), (151, 137))


def broken_7():
    return slumped((128.0, 186.0), 3.0, (8.0, 0.0, 3.0), (1.2, 0.8), (0, 2), (152, 143))


BROKEN = [broken_0, broken_1, broken_2, broken_3, broken_4, broken_5, broken_6, broken_7]


# ======================================================================= eric_broken_sword (7)
_THROWN = None


def thrown(i, flip=False):
    global _THROWN
    if _THROWN is None:
        _THROWN = Image.open(ASSETS + 'eric_thrown_sword_v2.png').convert('RGBA')
    f = _THROWN.crop((i * 160, 0, i * 160 + 160, 160))
    return f.transpose(Image.FLIP_LEFT_RIGHT) if flip else f


def paste_img(lay, img, x0, y0):
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if p[3]:
                X, Y = x0 + x, y0 + y
                if 0 <= X < FW and 0 <= Y < FH:
                    lay.px[Y][X] = p


def blade_axis_x(img):
    """centre column of the widest run of blade pixels in a vertical thrown-sword frame"""
    w, h = img.size
    px = img.load()
    best = None
    for y in range(h):
        xs = [x for x in range(w) if px[x, y][3] and px[x, y][:3] != (0, 0, 0)]
        if xs and (best is None or len(xs) > best[0]):
            best = (len(xs), (min(xs) + max(xs)) / 2.0)
    return best[1]


def planted(lay, lean=0.0, cracks=True):
    """the planted greatsword, blade entering the mat at (PLANT_X, MOUND_GROUND); lean tilts the hilt
    right (degrees) about that entry point"""
    a = math.radians(lean)
    d = (-math.sin(a), math.cos(a))           # blade direction, pointing into the mat
    depth = MOUND_GROUND - PLANT_GUARD_Y
    guard = (PLANT_X - d[0] * depth, MOUND_GROUND - d[1] * depth)
    tmp = Layer()
    if abs(lean) < 1e-9:
        R.sword(tmp, (PLANT_X, PLANT_GUARD_Y), (0, 1))
    else:
        R.sword(tmp, guard, d)
    for y in range(min(FH, MOUND_GROUND + 1)):
        for x in range(FW):
            if tmp.px[y][x] is not None:
                lay.px[y][x] = tmp.px[y][x]
    w = len(K.MOUND[0])
    x0 = PLANT_X - w // 2
    for r, row in enumerate(K.MOUND):
        for c, ch in enumerate(row):
            if ch not in '. ':
                lay.set(x0 + c, MOUND_GROUND - 1 + r, ch)
    if cracks:
        g = MOUND_GROUND
        FX.crack(lay, [(x0 - 1, g + 2), (x0 - 5, g + 1), (x0 - 8, g + 3), (x0 - 11, g + 2)])
        FX.crack(lay, [(x0 + w, g + 2), (x0 + w + 4, g + 4), (x0 + w + 7, g + 3)])
        FX.crack(lay, [(PLANT_X - 4, g + 4), (PLANT_X - 7, g + 5)])
        FX.crack(lay, [(PLANT_X + 6, g + 4), (PLANT_X + 9, g + 5)])


def sword_0():
    """knocked out of his grip: flung up, hilt still at his opening hand"""
    lay = Layer()
    R.sword(lay, (86.0, 112.0), (-0.34, -0.94))
    K.speed_lines(lay, [((104, 150), (100, 162)), ((96, 154), (92, 166)), ((112, 146), (109, 156))])
    return lay


def sword_1():
    """flipping over above his head (the approved spin frame, mirrored so it turns counter-clockwise)"""
    lay = Layer()
    paste_img(lay, thrown(0, flip=True), 80 - 80, 60 - 80)
    return lay


def sword_2():
    """dropping tip-first beside him"""
    lay = Layer()
    img = thrown(2, flip=True)
    ax = blade_axis_x(img)
    x0 = int(round(PLANT_X + 0.5 - ax - 0.5))
    # tip just above the mat
    h = img.size[1]
    px = img.load()
    tip = max(y for y in range(h) for x in range(img.size[0]) if px[x, y][3] and px[x, y][:3] != (255, 255, 255)
              and abs(x - ax) < 14)
    paste_img(lay, img, x0, 176 - tip)
    K.speed_lines(lay, [((78, 6), (78, 20)), ((98, 4), (98, 18)), ((88, 0), (88, 10))])
    return lay


def sword_3():
    """THUNK: buried to the guard, dust kicked up, a bright impact"""
    lay = Layer()
    planted(lay)
    K.speed_lines(lay, [((78, 96), (78, 110)), ((98, 94), (98, 108)), ((88, 88), (88, 100))])
    for x, y, s in [(56, 180, False), (104, 181, False), (46, 186, True), (118, 186, True)]:
        FX.puff(lay, x, y, small=s)
    for a in (-160, -130, -50, -20):
        t = math.radians(a)
        K.speed_lines(lay, [((PLANT_X + math.cos(t) * 26, MOUND_GROUND + math.sin(t) * 12),
                             (PLANT_X + math.cos(t) * 38, MOUND_GROUND + math.sin(t) * 18))])
    return lay


def sword_4():
    lay = Layer()
    planted(lay, lean=5.0)
    FX.puff(lay, 54, 183, small=True)
    FX.puff(lay, 112, 184, small=True)
    return lay


def sword_5():
    lay = Layer()
    planted(lay, lean=-3.0)
    return lay


def sword_6():
    lay = Layer()
    planted(lay)
    return lay


SWORD = [sword_0, sword_1, sword_2, sword_3, sword_4, sword_5, sword_6]


# ======================================================================= eric_juggle (10)
SPIN_ARCS = [(66, 100, 172, 2), (60, 282, 330, 2), (72, 196, 222, 1)]


def spin_fx(lay, rot, floor=186):
    """motion arcs trailing the clockwise spin (bright head leads clockwise); never below `floor`, so
    the body, not an effect, is what touches row 191"""
    tmp = Layer()
    jr.spin_arcs(tmp, TUMBLE_C, [(r, a0 + rot, a1 + rot, w) for r, a0, a1, w in SPIN_ARCS])
    for y in range(min(FH, floor + 1)):
        for x in range(FW):
            if tmp.px[y][x] is not None:
                lay.px[y][x] = tmp.px[y][x]


def juggle_0():
    """hit a: struck from below - popped up off his knees, spine arched, head snapped back and to the side,
    arms thrown up and out, legs dangling"""
    pose = dict(
        hip=(128.0, 168.0), ang=6.0, expr='pain', head=(10.0, 1.0, -4.0), torso=(0.4, 0.0), shoulders=(0, -1),
        arms={
            'L': dict(elbow=(99.0, 147.0), wrist=(88.0, 139.0), hand='open', hand_ang=132.0, spread=1.7),
            'R': dict(elbow=(157.0, 139.0), wrist=(164.0, 125.0), hand='open', hand_ang=196.0, spread=1.7,
                      mirror=True),
        },
        legs={
            'L': dict(knee=(118.0, 178.0), ankle=(117.0, 185.0), foot_ang=8.0, fw=17.0),
            'R': dict(knee=(138.0, 179.0), ankle=(140.0, 186.0), foot_ang=-6.0, fw=17.0),
        },
        cape=lambda lay, p: K.cape_flare(lay, p, spread=1.05, length=0.9, lean=6.0, teeth=5, amp=4.0),
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def front(lay, p):
        # the launch: streaks rushing up past him from the blow below
        K.speed_lines(lay, [((104, 190), (104, 172)), ((150, 190), (150, 170)), ((92, 176), (92, 160)),
                            ((164, 178), (164, 160)), ((127, 191), (127, 184))])
        FX.sweat(lay, 170, 116)
        FX.sweat(lay, 90, 122)
        FX.sweat(lay, 150, 108)
    pose['extra'] = {'front': front}
    return pose


def reach(p0, p1, k):
    """p1 moved k px further along p0 -> p1"""
    if not k:
        return p1
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    return (p1[0] + dx / L * k, p1[1] + dy / L * k)


def tumble_pose(ang, arms, legs, head_da, expr='dazed', cape_len=1.05, lean=-16.0, spin_rot=0.0, drops=(),
                ext=None, spread=1.15):
    """ext: {'aL'|'aR'|'lL'|'lR': px} pushes that wrist / ankle further out along its limb (96-space units)"""
    ext = ext or {}
    hip = centred_hip(ang)
    tf = Tf(body.PELVIS96, hip, ang)
    (l_el, l_wr), (r_el, r_wr) = arms
    (l_kn, l_an), (r_kn, r_an) = legs
    l_wr = reach(l_el, l_wr, ext.get('aL', 0))
    r_wr = reach(r_el, r_wr, ext.get('aR', 0))
    l_an = reach(l_kn, l_an, ext.get('lL', 0))
    r_an = reach(r_kn, r_an, ext.get('lR', 0))
    pose = dict(
        hip=hip, ang=ang, expr=expr, head=(head_da, 0.0, 0.0), flare=12.0,
        arms={
            'L': dict(elbow=J(tf, *l_el), wrist=J(tf, *l_wr), hand='open', spread=1.4),
            'R': dict(elbow=J(tf, *r_el), wrist=J(tf, *r_wr), hand='open', spread=1.3, mirror=True),
        },
        legs={
            'L': dict(knee=J(tf, *l_kn), ankle=J(tf, *l_an), boot=K.boot_out(J(tf, *l_kn), J(tf, *l_an), TUMBLE_C)),
            'R': dict(knee=J(tf, *r_kn), ankle=J(tf, *r_an), boot=K.boot_out(J(tf, *r_kn), J(tf, *r_an), TUMBLE_C)),
        },
        cape=lambda lay, p: K.cape_flare(lay, p, spread=spread, length=cape_len, lean=lean, teeth=5, amp=6.0),
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def front(lay, p):
        spin_fx(lay, spin_rot)
        for x, y in drops:
            FX.sweat(lay, x, y)
    pose['extra'] = {'front': front}
    return pose


def juggle_1():
    """hit b: launched, the cartwheel starting (30 degrees), limbs trailing below him"""
    return tumble_pose(30.0, (((14, 42), (8, 28)), ((84, 44), (93, 31))),
                       (((30, 93), (25, 103)), ((64, 93), (70, 103))), 10.0, expr='pain', cape_len=0.95,
                       lean=-8.0, spin_rot=-110.0, drops=[(186, 104)], ext={'lR': -2})


# the four cartwheel poses (clockwise, 90 degrees apart). Limbs in body-local 96-space; `ext` pushes a
# wrist/ankle further along its limb (negative pulls it in) and `cape` is the flared cape's length. These
# were tuned with part_lows() so every loop frame's lowest body pixel is exactly row 191.
TUMBLE_SPEC = {
    2: dict(ang=50.0, aL=((13, 36), (5, 22)), aR=((86, 60), (97, 70)), lL=((25, 92), (15, 98)),
            lR=((70, 94), (79, 103)), head=20.0, rot=-90.0, cape=1.03, ext={'lR': -5, 'aR': -1}, drops=[(190, 150)]),
    3: dict(ang=140.0, aL=((12, 38), (3, 25)), aR=((91.3, 45.3), (103.6, 44.3)), lL=((24, 92), (14, 99)),
            lR=((71, 93), (80, 102)), head=24.0, rot=0.0, cape=1.05, ext={'aR': -1}, drops=[(188, 170), (176, 182)]),
    4: dict(ang=230.0, aL=((11, 44), (2, 34)), aR=((85, 52), (96, 58)), lL=((26, 93), (18, 102)),
            lR=((69, 92), (78, 99)), head=18.0, rot=90.0, cape=1.05, ext={'aL': -7}, drops=[(70, 150)]),
    5: dict(ang=320.0, aL=((14, 40), (4, 30)), aR=((84, 62), (94, 74)), lL=((27, 92), (19, 101)),
            lR=((68, 94), (75, 104)), head=22.0, rot=180.0, cape=0.88, spread=1.0, lean=-4.0, ext={'lL': -3},
            drops=[(66, 124)]),
}


def part_lows(i, **over):
    """true lowest row of every part of tumble frame i (rendered 8 px higher so nothing clips)"""
    p = shifted(juggle_tumble(i, **over), -8)
    ex = dict(p['extra'])
    ex.pop('front', None)
    p['extra'] = ex
    fr, L = body.render(p)
    return {n: lowest_row(l) + 8 for n, l in L.items() if lowest_row(l) >= 0}


def juggle_tumble(i, ext=None, cape=None, aR=None, spread=None, lean=None):
    sp = TUMBLE_SPEC[i]
    return tumble_pose(sp['ang'], (sp['aL'], aR or sp['aR']), (sp['lL'], sp['lR']), sp['head'],
                       cape_len=sp['cape'] if cape is None else cape, spin_rot=sp['rot'], drops=sp['drops'],
                       ext=sp['ext'] if ext is None else ext,
                       spread=sp.get('spread', 1.15) if spread is None else spread,
                       lean=sp.get('lean', -16.0) if lean is None else lean)


def body_lowest(pose, lift=0):
    """lowest opaque row of the body (effects excluded), rendered `lift` px higher so clipping shows"""
    p = dict(pose)
    ex = dict(p.get('extra', {}))
    for k in ('front', 'back'):
        ex.pop(k, None)
    p['extra'] = ex
    if lift:
        p = shifted(p, -lift)
    fr, L = body.render(p)
    return lowest_row(fr) + lift


def shifted(pose, dy):
    """the same pose moved dy px vertically (joints given in frame px move too)"""
    p = dict(pose)
    p['hip'] = (pose['hip'][0], pose['hip'][1] + dy)
    arms = {}
    for k, a in pose.get('arms', {}).items():
        a = dict(a)
        for key in ('elbow', 'wrist', 'shoulder'):
            if key in a:
                a[key] = (a[key][0], a[key][1] + dy)
        arms[k] = a
    p['arms'] = arms
    legs = pose.get('legs')
    if isinstance(legs, dict):
        lg = {}
        for k, g in legs.items():
            g = dict(g)
            for key in ('knee', 'ankle', 'toe'):
                if key in g:
                    g[key] = (g[key][0], g[key][1] + dy)
            lg[k] = g
        p['legs'] = lg
    return p


def juggle_6():
    """crash a: the approved crash key - shoulders-first into the mat, legs still up (raised 1 px so the
    crown sits on row 191 instead of running off the frame)"""
    return shifted(K.crash_pose(), -1)


def juggle_7():
    """crash b: the legs flop over to the left as the body tips back toward the mat"""
    ang = 122.0
    k6 = Tf(body.PELVIS96, (107.0, 137.0), 155.0)
    neck = k6.pt(*body.NECK96_BODY)
    t0 = Tf(body.PELVIS96, (0, 0), ang)
    n0 = t0.pt(*body.NECK96_BODY)
    hip = (neck[0] - n0[0] + 2.0, neck[1] - n0[1] + 1.0)
    tf = Tf(body.PELVIS96, hip, ang)
    hl = J(tf, *body.HIP96['L'])
    hr = J(tf, *body.HIP96['R'])
    pose = dict(
        hip=hip, ang=ang, expr='pain', head=(-8.0, 0.0, 0.0), flare=12.0,
        arms={
            'L': dict(elbow=(150.0, 160.0), wrist=(163.0, 170.0), hand='open', hand_ang=-58.0, spread=1.3),
            'R': dict(elbow=(96.0, 176.0), wrist=(84.0, 183.0), hand='open', hand_ang=52.0, spread=1.3, mirror=True),
        },
        legs={
            'L': dict(knee=(hl[0] - 12, hl[1] - 12), ankle=(hl[0] - 26, hl[1] - 16),
                      boot=((-0.35, -1.0), (-1.0, 0.35))),
            'R': dict(knee=(hr[0] - 15, hr[1] - 3), ankle=(hr[0] - 29, hr[1] - 5),
                      boot=((-0.1, -1.0), (-1.0, 0.1))),
        },
        cape=lambda lay, p: K.crash_cape(lay, p),
        order=['back', 'cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'armL',
               'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def front(lay, p):
        K.big_puff(lay, 70, 178)
        K.big_puff(lay, 166, 179)
        for x, y, s in [(52, 184, False), (186, 184, False), (100, 187, True), (146, 187, True), (36, 186, True),
                        (204, 186, True)]:
            FX.puff(lay, x, y, small=s)
        for x, y in [(44, 150), (204, 146), (60, 132), (190, 128)]:
            FX.rock(lay, x, y)
    pose['extra'] = {'front': front}
    return pose


def juggle_8():
    """bounce: flat on his back but popped a few px off the mat, limbs flopping"""
    ang = 97.0
    hip = (101.0, 154.0)
    tf = Tf(body.PELVIS96, hip, ang)
    hl = J(tf, *body.HIP96['L'])
    hr = J(tf, *body.HIP96['R'])
    pose = dict(
        hip=hip, ang=ang, expr='dazed', head=(-10.0, 0.0, 0.0), flare=12.0,
        arms={
            'L': dict(elbow=(138.0, 124.0), wrist=(150.0, 114.0), hand='open', hand_ang=-140.0, spread=1.4),
            'R': dict(elbow=(113.0, 176.0), wrist=(101.0, 172.0), hand='open', hand_ang=70.0, spread=1.3, mirror=True),
        },
        legs={
            'L': dict(knee=(hl[0] - 12, hl[1] - 12), ankle=(hl[0] - 25, hl[1] - 18),
                      boot=((0.2, -1.0), (-1.0, -0.2))),
            'R': dict(knee=(hr[0] - 14, hr[1] - 2), ankle=(hr[0] - 28, hr[1] - 6),
                      boot=((-0.1, -1.0), (-1.0, 0.1))),
        },
        cape=lambda lay, p: K.lying_cape(lay, p),
        order=['cape', 'armL', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'paulL',
               'paulR', 'armR', 'head', 'front'],
    )

    def front(lay, p):
        for x, y, s in [(46, 185, False), (180, 186, False), (64, 187, True), (160, 188, True), (30, 188, True),
                        (196, 188, True)]:
            FX.puff(lay, x, y, small=s)
    pose['extra'] = {'front': front}
    return pose


def juggle_9():
    return K.lying_pose()


def juggle_frame(i):
    if i == 0:
        return juggle_0()
    if i == 1:
        return juggle_1()
    if 2 <= i <= 5:
        return juggle_tumble(i)
    return {6: juggle_6, 7: juggle_7, 8: juggle_8, 9: juggle_9}[i]()


JUGGLE = [lambda i=i: juggle_frame(i) for i in range(10)]


# ======================================================================= eric_winded (4)
def winded(shoulders, head, torso, puffs, drop):
    pose = K.winded_pose()
    pose['shoulders'] = shoulders
    pose['head'] = head
    pose['torso'] = torso

    def front(lay, p):
        FX.sweat(lay, *drop)
        for x, y, s in puffs:
            FX.puff(lay, x, y, small=s)
    pose['extra'] = {'sword': pose['extra']['sword'], 'front': front}
    return pose


def winded_0():
    return winded((0, 1), (-6.0, -1.0, 4.0), (0.6, 0.2), [(146, 128, True), (152, 121, True)], (150, 124))


def winded_1():
    """in: chest swells, shoulders and head come up a pixel"""
    return winded((0, 0), (-5.0, -1.0, 3.0), (1.0, 0.1), [(150, 118, True)], (151, 129))


def winded_2():
    """out: shoulders sag, head drops, a big breath puffs out"""
    return winded((0, 2), (-7.0, -1.0, 5.0), (0.5, 0.4), [(144, 132, True), (149, 126, True), (156, 120, True)],
                  (152, 135))


def winded_3():
    return winded((0, 1), (-6.0, -1.0, 4.0), (0.7, 0.3), [(150, 124, True), (157, 116, True)], (153, 141))


WINDED = [winded_0, winded_1, winded_2, winded_3]


# ======================================================================= measurements
def head_crown(pose, above=6):
    fr, L = render(pose)
    return K.head_pixel(L['head'], above)
