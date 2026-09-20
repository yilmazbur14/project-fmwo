"""Approval-pass key frames for eric_broken / eric_juggle / eric_winded (256x192, feet anchor (128,191)).

    python keys.py <out_dir>      renders every key frame to <out_dir>/<name>.png (+ 4x previews)
"""
import os
import sys
import math
import jr
import body
import faces
import rig2 as R
import fx2 as FX
from jr import Layer, Tf, FW, FH
from lib import PALC, BLACK, _DARKER, _LIGHTER

GROUND = 191


def J(tf, x, y):
    return tf.pt(x, y)


def hem(p0, p1, teeth, amp, out):
    """zigzag hem from p0 to p1; `out` = unit-ish vector the points poke toward"""
    pts = []
    n = teeth * 2
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        k = (amp if (i // 2) % 2 == 0 else amp * 0.65) if i % 2 == 1 else 0.0
        pts.append((x + out[0] * k, y + out[1] * k))
    return pts


def boot_out(knee, ankle, centre, tilt=0.0):
    """side-view boot for a flailing leg: sole along the shin, toes turned away from `centre`"""
    dx, dy = ankle[0] - knee[0], ankle[1] - knee[1]
    L = math.hypot(dx, dy)
    dx, dy = dx / L, dy / L
    tx, ty = -dy, dx
    if (ankle[0] - centre[0]) * tx + (ankle[1] - centre[1]) * ty < 0:
        tx, ty = -tx, -ty
    a = math.radians(tilt)
    tx, ty = tx * math.cos(a) - ty * math.sin(a), tx * math.sin(a) + ty * math.cos(a)
    return ((tx, ty), (dx, dy))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ------------------------------------------------------------------ planted greatsword (bear-hug style: enters the mat)
PLANT_X = 88
PLANT_GUARD_Y = 150
MOUND_GROUND = 186
MOUND = [
    "..kk.k" + "k" * 22 + "k.kk..",
    ".knkkm" + "n" * 22 + "mkknk.",
    "kmnnmn" + "o" * 22 + "nmnnmk",
    ".kkoop" + "p" * 22 + "pookk.",
    "...kkk" + "k" * 22 + "kkk...",
]


def planted_sword(lay, x=PLANT_X, guard_y=PLANT_GUARD_Y, ground=MOUND_GROUND, cracks=True):
    tmp = Layer()
    R.sword(tmp, (x, guard_y), (0, 1))
    for y in range(min(FH, ground + 1)):
        for xx in range(FW):
            p = tmp.px[y][xx]
            if p is not None:
                lay.px[y][xx] = p
    w = len(MOUND[0])
    x0 = x - w // 2
    for r, row in enumerate(MOUND):
        for c, ch in enumerate(row):
            if ch not in '. ':
                lay.set(x0 + c, ground - 1 + r, ch)
    if cracks:
        g = ground
        FX.crack(lay, [(x0 - 1, g + 2), (x0 - 5, g + 1), (x0 - 8, g + 3), (x0 - 11, g + 2)])
        FX.crack(lay, [(x0 + w, g + 2), (x0 + w + 4, g + 4), (x0 + w + 7, g + 3)])
        FX.crack(lay, [(x - 4, g + 4), (x - 7, g + 5)])
        FX.crack(lay, [(x + 6, g + 4), (x + 9, g + 5)])


# ------------------------------------------------------------------ small fx
def speed_lines(lay, pts, ch='W', edge='A'):
    """short white motion streaks: pts = [((x0,y0),(x1,y1)), ...]"""
    for p0, p1 in pts:
        path = jr.polyline([p0, p1])
        for i, (x, y) in enumerate(path):
            if 0 <= x < FW and 0 <= y < FH:
                lay.px[y][x] = PALC[ch if i < len(path) * 0.6 else edge]


def dust_cloud(lay, cx, cy, spread, n=6, seed=0, small_every=2):
    import random
    rnd = random.Random(seed)
    for i in range(n):
        x = int(cx + rnd.uniform(-spread, spread))
        y = int(cy + rnd.uniform(-spread * 0.25, spread * 0.1))
        FX.puff(lay, x, y, small=(i % small_every == 1))


BIG_PUFF = """
....kkkkk.....
..kkWWWWAkk...
.kWWWWWWAABkk.
kWWWWWAAAABBBk
kWWAAAAABBBCCk
kAAABBBBBCCCDk
.kkBBCCCCCDkk.
...kkkkkkkk...
"""


def big_puff(lay, x, y):
    for dy, row in enumerate(BIG_PUFF.strip('\n').split('\n')):
        for dx, ch in enumerate(row):
            if ch != '.':
                lay.set(x + dx, y + dy, ch)


# ------------------------------------------------------------------ TUMBLE (juggle loop key pose)
def cape_flare(lay, pose, spread=1.0, length=1.0, lean=0.0, teeth=5, amp=5.0, folds=True):
    """the cape blown open behind a spinning body, authored in body-local 96-space so it turns with him:
    hung from the shoulders, flared wide past both sides, with a torn zigzag hem. lean skews the hem
    sideways (body-local x) to show which way the air drags it."""
    tf = body.torso_tf(pose)
    top = [(66, 39), (48, 40), (30, 39)]
    hw0, hw1 = 30.0, 52.0 * spread
    y1 = 40 + 58 * length
    left = [(48 - 34, 46), (48 - 42 * spread, 58), (48 - 48 * spread + lean * 0.4, 74)]
    right = [(48 + 48 * spread + lean * 0.4, 74), (48 + 42 * spread, 58), (48 + 34, 46)]
    h0 = (48 - hw1 + lean, y1 - 4)
    h1 = (48 + hw1 + lean, y1 - 4)
    hm = hem(h0, h1, teeth, amp, (0.0, 1.0))
    pts96 = top + left + hm + right
    pts = [tf.pt(x, y) for x, y in pts96]
    fl = []
    if folds:
        for fx in (-30, -14, 14, 30):
            a = tf.pt(48 + fx * 0.5, 52)
            b = tf.pt(48 + fx * spread + lean * 0.8, y1 - 8)
            fl.append([a, b])
    c = tf.pt(44, 56)
    jr.cape_poly(lay, pts, folds=fl, light=(c[0], c[1], 44 * max(spread, length)))


def tumble_pose(ang=140.0, head_da=24.0):
    tf0 = Tf(body.PELVIS96, (0, 0), ang)
    c = tf0.pt(48, 58)
    hip = (128 - c[0], 146 - c[1])
    tf = Tf(body.PELVIS96, hip, ang)
    pose = dict(
        hip=hip, ang=ang, expr='dazed', head=(head_da, 0.0, 0.0), flare=12.0,
        arms={
            'L': dict(elbow=J(tf, 12, 38), wrist=J(tf, 3, 25), hand='open', spread=1.4),
            'R': dict(elbow=J(tf, 86, 58), wrist=J(tf, 98, 67), hand='open', spread=1.3, mirror=True),
        },
        legs={
            'L': dict(knee=J(tf, 24, 92), ankle=J(tf, 14, 99), boot=boot_out(J(tf, 24, 92), J(tf, 14, 99), (128, 146))),
            'R': dict(knee=J(tf, 71, 93), ankle=J(tf, 80, 102), boot=boot_out(J(tf, 71, 93), J(tf, 80, 102), (128, 146))),
        },
        cape=lambda lay, p: cape_flare(lay, p, spread=1.15, length=1.05, lean=-16.0, teeth=5, amp=6.0),
        order=['cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def front(lay, p):
        jr.spin_arcs(lay, (128, 146), [(64, 150, 205, 2), (62, 320, 12, 2), (70, 240, 272, 1)])
        FX.sweat(lay, 188, 170)
        FX.sweat(lay, 176, 182)
    pose['extra'] = {'front': front}
    return pose


# ------------------------------------------------------------------ CRASH (juggle 6): the spin ends shoulders-first in the mat
def crash_cape(lay, pose):
    """the cape still trailing the fall: it billows up above his raised legs"""
    tf = body.torso_tf(pose)
    shL = J(tf, 25, 44)
    shR = J(tf, 71, 44)
    nk = J(tf, 48, 40)
    top = [(shR[0] - 20, 60.0), (shR[0] + 6, 40.0), (shL[0] - 14, 36.0), (shL[0] + 14, 50.0)]
    pts = [nk, shL, (shL[0] + 10, shL[1] - 22), (shL[0] + 8, shL[1] - 48)]
    pts += hem((shL[0] + 8, shL[1] - 48), (shR[0] - 22, shR[1] - 70), 5, 5.0, (0.2, -1.0))[1:-1]
    pts += [(shR[0] - 22, shR[1] - 70), (shR[0] - 20, shR[1] - 40), (shR[0] - 10, shR[1] - 14), shR]
    folds = [[(shL[0] + 2, shL[1] - 16), (shL[0] - 6, shL[1] - 48)],
             [(nk[0] - 2, nk[1] - 22), (nk[0] - 8, nk[1] - 62)],
             [(shR[0] - 8, shR[1] - 24), (shR[0] - 18, shR[1] - 60)]]
    c = J(tf, 48, 70)
    jr.cape_poly(lay, pts, folds=folds, light=(c[0] - 6, c[1] - 10, 46), flat=0.45)


def crash_pose():
    ang = 155.0
    hip = (107.0, 137.0)
    pose = dict(
        hip=hip, ang=ang, expr='pain', head=(-4.0, 0.0, 0.0), flare=14.0,
        arms={
            # arms flung out to the mat either side of his head
            'L': dict(elbow=(146.0, 158.0), wrist=(158.0, 168.0), hand='open', hand_ang=-52.0, spread=1.5),
            'R': dict(elbow=(89.0, 170.0), wrist=(78.0, 180.0), hand='open', hand_ang=40.0, spread=1.5,
                      mirror=True),
        },
        legs={
            # legs still up in the air, splayed
            'L': dict(knee=(123.0, 113.0), ankle=(131.0, 102.0), boot=((1.0, 0.25), (0.25, -1.0))),
            'R': dict(knee=(86.0, 124.0), ankle=(79.0, 112.0), boot=((-1.0, 0.35), (-0.35, -1.0))),
        },
        cape=crash_cape,
        order=['back', 'cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'armL',
               'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def back(lay, p):
        # impact lines bursting out from where he hits the mat
        c = (128, 188)
        for a in (-172, -150, -128, -52, -30, -8):
            t = math.radians(a)
            p0 = (c[0] + math.cos(t) * 60, c[1] + math.sin(t) * 40)
            p1 = (c[0] + math.cos(t) * 80, c[1] + math.sin(t) * 54)
            speed_lines(lay, [(p0, p1)])

    def front(lay, p):
        big_puff(lay, 86, 180)
        big_puff(lay, 150, 181)
        for x, y, s in [(70, 185, False), (170, 185, False), (104, 187, True), (138, 187, True), (54, 187, True),
                        (190, 187, True)]:
            FX.puff(lay, x, y, small=s)
        for x, y in [(60, 166), (190, 162), (74, 150), (180, 148), (100, 160)]:
            FX.rock(lay, x, y)
    pose['extra'] = {'back': back, 'front': front}
    return pose


# ------------------------------------------------------------------ LYING (juggle 9): flat out, KO'd
def lying_cape(lay, pose):
    """cape spread flat on the mat beneath him"""
    tf = body.torso_tf(pose)
    shL = J(tf, 25, 44)
    shR = J(tf, 71, 44)
    nk = J(tf, 48, 40)
    pts = [nk, shL, (shL[0] - 16, shL[1] - 6), (shL[0] - 42, shL[1] - 5), (shL[0] - 62, shL[1] - 1)]
    pts += hem((shL[0] - 62, shL[1] - 1), (shL[0] - 68, 189.0), 4, 4.0, (-1.0, 0.0))[1:-1]
    pts += [(shL[0] - 68, 189.0), (shL[0] - 40, 190.5), (shR[0] - 14, 190.5), shR]
    folds = [[(shL[0] - 20, shL[1] - 2), (shL[0] - 50, shL[1] + 10)], [(shL[0] - 30, shL[1] + 24), (shL[0] - 60, 180.0)],
             [(shR[0] - 22, shR[1] + 8), (shR[0] - 52, 188.0)]]
    jr.cape_poly(lay, pts, folds=folds, light=(shL[0] - 30, shL[1] + 6, 46))


def lying_pose():
    ang = 90.0
    hip = (102.0, 160.0)
    pose = dict(
        hip=hip, ang=ang, expr='dazed', head=(-5.0, 0.0, 0.0), flare=10.0,
        arms={
            # far arm flung back over his head, near arm flopped along his side
            'L': dict(elbow=(137.0, 131.0), wrist=(151.0, 124.0), hand='open', hand_ang=-128.0, spread=1.3),
            'R': dict(elbow=(110.0, 185.0), wrist=(97.0, 185.0), hand='open', hand_ang=80.0, spread=1.1,
                      mirror=True),
        },
        legs={
            'L': dict(knee=(86.0, 141.0), ankle=(74.0, 133.0), boot=((0.3, -1.0), (-1.0, -0.3))),
            'R': dict(knee=(85.0, 176.0), ankle=(71.0, 179.0), boot=((-0.15, -1.0), (-1.0, 0.15))),
        },
        cape=lying_cape,
        order=['cape', 'armL', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'paulL',
               'paulR', 'armR', 'head', 'front'],
    )

    def front(lay, p):
        FX.puff(lay, 44, 184, small=True)
        FX.puff(lay, 176, 186, small=True)
        FX.puff(lay, 52, 178, small=True)
    pose['extra'] = {'front': front}
    return pose


# ------------------------------------------------------------------ upright poses: shared bits
def pooled_cape(lay, pose, left=86.0, right=170.0, ground=190.0, teeth=6):
    """the cape hanging from his shoulders and pooling on the mat around a kneeling body"""
    tf = body.torso_tf(pose)
    shL = J(tf, 22, 46)
    shR = J(tf, 74, 46)
    nk = J(tf, 48, 40)
    pts = [nk, (shR[0] - 6, shR[1] - 6), shR, (shR[0] + 8, shR[1] + 14), (right, ground - 8), (right + 2, ground)]
    pts += hem((right + 2, ground), (left - 2, ground), teeth, 2.5, (0.0, 1.0))[1:-1]
    pts += [(left - 2, ground), (left, ground - 8), (shL[0] - 8, shL[1] + 14), shL, (shL[0] + 6, shL[1] - 6)]
    folds = [[(shL[0] - 2, shL[1] + 16), (left + 6, ground - 3)], [(shL[0] + 6, shL[1] + 22), (left + 16, ground - 2)],
             [(shR[0] + 2, shR[1] + 16), (right - 6, ground - 3)], [(shR[0] - 6, shR[1] + 22), (right - 16, ground - 2)]]
    c = J(tf, 44, 58)
    jr.cape_poly(lay, pts, folds=folds, light=(c[0], c[1], 46))


def idle_cape_on(lay, pose):
    jr.cape_idle(lay, body.torso_tf(pose))


def sword_in_fist(lay, fist, direction, blade_len=None):
    L = math.hypot(*direction)
    u = (direction[0] / L, direction[1] / L)
    guard = (fist[0] + u[0] * 10, fist[1] + u[1] * 10)
    if blade_len:
        R.sword(lay, guard, direction, blade_len=blade_len)
    else:
        R.sword(lay, guard, direction)


def surprise_lines(lay, c, r0, r1, angs):
    for a in angs:
        t = math.radians(a)
        p0 = (c[0] + math.cos(t) * r0, c[1] + math.sin(t) * r0)
        p1 = (c[0] + math.cos(t) * r1, c[1] + math.sin(t) * r1)
        for i, (x, y) in enumerate(jr.polyline([p0, p1])):
            if 0 <= x < FW and 0 <= y < FH:
                lay.px[y][x] = PALC['W' if i > 0 else 'A']


# ------------------------------------------------------------------ REEL (broken 1): the Break lands, he is flung off balance
def reel_pose():
    hip = (131.0, 172.0)
    ang = 10.0
    pose = dict(
        hip=hip, ang=ang, expr='shock', head=(10.0, 1.0, -1.0), torso=(0.4, 0.0),
        arms={
            # the sword hand springs open as the blade is knocked loose; the other arm flails for balance
            'L': dict(elbow=(101.0, 150.0), wrist=(91.0, 141.0), hand='open', hand_ang=150.0, spread=1.6),
            'R': dict(elbow=(161.0, 150.0), wrist=(171.0, 141.0), hand='open', hand_ang=212.0, spread=1.6,
                      mirror=True),
        },
        legs={
            'L': dict(knee=(118.0, 181.0), ankle=(115.0, 184.0), foot_ang=-16.0, fw=18.0),
            'R': dict(knee=(149.0, 181.0), ankle=(153.0, 186.0), foot_ang=0.0, fw=19.0),
        },
        cape=lambda lay, p: jr.cape_idle(lay, jr.about(body.torso_tf(p), (48, 44), 6.0)),
        order=['sword', 'cape', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'armR', 'paulL', 'paulR', 'head', 'front'],
    )

    def sword(lay, p):
        # knocked out of his grip: dropping tip-first beside him (it plunges into the mat on reel 2)
        R.sword(lay, (70.0, 73.0), (0.14, 1.0))
        speed_lines(lay, [((58, 22), (60, 34)), ((66, 16), (67, 30)), ((75, 20), (76, 32))])

    def front(lay, p):
        surprise_lines(lay, (134, 120), 23, 31, [-160, -128, -96, -64, -32])
        FX.sweat(lay, 164, 112)
        FX.sweat(lay, 104, 116)
        FX.sweat(lay, 170, 124)
    pose['extra'] = {'sword': sword, 'front': front}
    return pose


# ------------------------------------------------------------------ KNEEL (broken 4): down on both knees, hanging on to the sword
def kneel_pose():
    hip = (127.0, 184.0)
    ang = -4.0
    pose = dict(
        hip=hip, ang=ang, expr='groggy', head=(-3.0, 0.0, 3.0), torso=(0.8, 0.4), shoulders=(0, 1), flare=7.0,
        arms={
            'L': dict(elbow=(99.0, 165.0), wrist=(90.0, 151.0), hand='fist', hdy=-4),
            'R': dict(elbow=(155.0, 176.0), wrist=(149.0, 183.0), hand='fist', hdy=1),
        },
        legs={
            'L': dict(kneel=True, knee=(114.0, 187.0), toe=(103.0, 189.0)),
            'R': dict(kneel=True, knee=(141.0, 187.0), toe=(152.0, 189.0)),
        },
        cape=lambda lay, p: pooled_cape(lay, p, left=92.0, right=166.0),
        order=['cape', 'sword', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'paulL', 'paulR', 'armR', 'head', 'front'],
    )

    def sword(lay, p):
        planted_sword(lay)

    def front(lay, p):
        FX.sweat(lay, 146, 128)
        FX.sweat(lay, 110, 134)
    pose['extra'] = {'sword': sword, 'front': front}
    return pose


# ------------------------------------------------------------------ SLUMPED (broken 5): sat back on his heels, out on his feet
def slumped_pose():
    hip = (129.0, 186.0)
    ang = 5.0
    pose = dict(
        hip=hip, ang=ang, expr='dazed', head=(13.0, 1.0, 3.0), torso=(1.2, 0.8), shoulders=(0, 2), flare=9.0,
        arms={
            'L': dict(elbow=(108.0, 179.0), wrist=(104.0, 185.0), hand='open', hand_ang=18.0, spread=1.2, curl=-1.0),
            'R': dict(elbow=(152.0, 180.0), wrist=(156.0, 185.0), hand='open', hand_ang=-18.0, spread=1.2, curl=-1.0,
                      mirror=True),
        },
        legs={
            'L': dict(kneel=True, knee=(114.0, 188.0), toe=(102.0, 189.0)),
            'R': dict(kneel=True, knee=(144.0, 188.0), toe=(156.0, 189.0)),
        },
        cape=lambda lay, p: pooled_cape(lay, p, left=90.0, right=170.0),
        order=['cape', 'sword', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'paulL', 'paulR', 'armL', 'armR', 'head', 'front'],
    )

    def sword(lay, p):
        planted_sword(lay)

    def front(lay, p):
        FX.sweat(lay, 150, 132)
    pose['extra'] = {'sword': sword, 'front': front}
    return pose


# ------------------------------------------------------------------ WINDED (winded 0): leaning on the planted sword, panting
def winded_pose():
    hip = (131.0, 178.0)
    ang = -10.0
    pose = dict(
        hip=hip, ang=ang, expr='tired', head=(-6.0, -1.0, 4.0), torso=(0.6, 0.2), shoulders=(0, 1),
        arms={
            'L': dict(elbow=(101.0, 152.0), wrist=(93.0, 140.0), hand='fist', hdx=-4, hdy=-5),
            'R': dict(elbow=(157.0, 170.0), wrist=(150.0, 179.0), hand='fist', hdy=1),
        },
        legs={
            'L': dict(knee=(115.0, 182.0), ankle=(113.0, 186.0), foot_ang=0.0, fw=19.0),
            'R': dict(knee=(141.0, 182.0), ankle=(143.0, 186.0), foot_ang=0.0, fw=19.0),
        },
        cape=idle_cape_on,
        order=['cape', 'sword', 'legL', 'legR', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget',
               'armL', 'paulL', 'paulR', 'armR', 'head', 'front'],
    )

    def sword(lay, p):
        planted_sword(lay)

    def front(lay, p):
        FX.sweat(lay, 150, 124)
        FX.puff(lay, 146, 128, small=True)       # panting breaths drifting up off his face
        FX.puff(lay, 152, 121, small=True)
    pose['extra'] = {'sword': sword, 'front': front}
    return pose


KEYS = {
    'reel': reel_pose,
    'kneel': kneel_pose,
    'slumped': slumped_pose,
    'winded': winded_pose,
    'tumble': tumble_pose,
    'crash': crash_pose,
    'lying': lying_pose,
}


def render_key(name, layers=False):
    pose = KEYS[name]()
    fr, L = body.render(pose)
    return (fr, L, pose) if layers else fr


def to_image(lay):
    from PIL import Image
    im = Image.new('RGBA', (FW, FH))
    im.putdata([p for row in lay.rgba() for p in row])
    return im


def head_pixel(head_layer, above=6):
    """where the daze stars go: centred over the crown of the drawn head, `above` px over its top"""
    pts = [(x, y) for y in range(FH) for x in range(FW) if head_layer.px[y][x] is not None]
    top = min(y for x, y in pts)
    xs = [x for x, y in pts if y <= top + 2]
    return (round(sum(xs) / len(xs) + 0.5, 1) - 0.5, top - above)


def planted_sword_layer():
    lay = Layer()
    planted_sword(lay)
    return lay


if __name__ == '__main__':
    out = sys.argv[1]
    names = sys.argv[2:] or list(KEYS)
    os.makedirs(out, exist_ok=True)
    from PIL import Image
    for n in names:
        fr, L, pose = render_key(n, layers=True)
        im = to_image(fr)
        im.save(os.path.join(out, n + '.png'))
        bg = Image.new('RGBA', (FW, FH), (96, 110, 96, 255))
        bg.alpha_composite(im)
        bg.resize((FW * 4, FH * 4), Image.NEAREST).save(os.path.join(out, n + '_4x.png'))
        print('rendered', n, im.getbbox())
        if n in ('slumped', 'kneel', 'reel', 'winded'):
            hp = head_pixel(L['head'])
            print('   head pixel', hp)
            if n == 'slumped':
                open(os.path.join(out, 'broken_head_pixel.txt'), 'w').write('%s %s' % hp)
    to_image(planted_sword_layer()).save(os.path.join(out, 'planted_sword.png'))
