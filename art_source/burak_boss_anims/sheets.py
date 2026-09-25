"""Captain Burak's fight body sheets, as lists of (name, Pose, hold seconds). Built on akit (the
approved rig, posable) and aparts (arms, hands, cutlass, pistol). Every sheet is 96x96 frames, feet
on row 95, centre column 48, facing RIGHT (the code flips) unless it says otherwise.

The FX artist draws the barrels, muzzle flash and smoke, cannonballs and slash trails, so none of
those are baked in here. Anchors the coder needs (muzzle, release point, blade arcs, crown, mouth)
are recorded per frame in ANCHORS.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import akit as A  # noqa: E402
import aparts as AP  # noqa: E402
import burak as B  # noqa: E402

SHEETS = {}
ANCHORS = {}          # sheet -> list of dicts per frame


def sheet(name):
    def deco(fn):
        SHEETS[name] = fn
        return fn
    return deco


# ------------------------------------------------------------------ fire (3)
RECOIL = A.gun_arm(elbow=(70.5, 55.0), wrist=(75.5, 56.0), fist_at=(75, 51), exit_=(82, 55.5),
                   mouth=(88.5, 58.5), hammer_at=(80, 47))


@sheet('burak_fire')
def fire():
    """aim, FIRE (the approved shot frame without its smoke, flash and ball), recoil."""
    return [
        ('aim', A.Pose(expr='aim', arm_r='shot', tails=0.5), 0.10),
        ('fire', A.shot0(), 0.10),
        ('recoil', A.shot0(arm_r=RECOIL, head=(-3, 0), hat=-0.10, hat_off=(-1, 1), tails=1.6), 0.16),
    ]


FIRE_MUZZLE = [B.MUZZLE, B.MUZZLE, (88.5, 58.5)]


# ------------------------------------------------------------------ load (4 loop)
GUN_UP = dict(barrel_len=11.0, grip_len=4.5, bell_len=5.5, r_bar=2.3, r_bell=5.0, mouth_tip=0.62)


def hold_gun_up(wrist, breech, barrel=(0.38, -1.0), grip=(0.75, 0.8), elbow=(71.5, 61.5), ball=None,
                lines_=()):
    """His pistol arm bent up, the big flintlock held muzzle-up in his fist and tipped out past his
    head, so its grip, lock, barrel and bell all show. Drawn on top (the gun is in front of him).
    ball: a small ball being flicked into the bell."""
    def draw(F):
        AP.arm(F, AP.SH_R, elbow, wrist, lit=False)
        AP.pistol(F, breech, barrel, grip, **GUN_UP)
        ux, uy = AP.unit(*barrel)
        F.body(B.hammer(int(round(breech[0] - 2 - uy * 0)), int(round(breech[1] - 3))))
        F.body(AP.fist((wrist[0] + 0.5, wrist[1] - 1.0), (ux, uy), lit=False))
        if ball:
            F.body(B.cannonball(ball[0], ball[1], 2.2))
        for (x0, y0, x1, y1) in lines_:
            F.body({q: 'W' for q in A.line(x0, y0, x1, y1)}, outline=False)
    return draw


def gun_mouth(breech, barrel=(0.38, -1.0)):
    ux, uy = AP.unit(*barrel)
    L = GUN_UP['barrel_len'] + GUN_UP['bell_len']
    return (breech[0] + ux * L, breech[1] + uy * L)


LOAD_POSES = [
    # up: the pistol snapped muzzle-up beside his head, eyes on it
    dict(wrist=(69.0, 55.0), breech=(70.0, 51.0), elbow=(72.0, 62.0)),
    # drop: a ball flicked up, dropping into the bell
    dict(wrist=(69.0, 55.0), breech=(70.0, 51.0), elbow=(72.0, 62.0), ball=(77.5, 25.0)),
    # tamp: the butt slammed down to seat it, the gun jolted low
    dict(wrist=(70.0, 63.0), breech=(71.0, 59.0), elbow=(72.5, 65.0), lines_=((81, 42, 81, 47), (72, 44, 72, 49))),
    # click: back up, the thumb hauling the hammer back
    dict(wrist=(68.5, 54.0), breech=(69.5, 50.0), elbow=(71.5, 61.5)),
]


@sheet('burak_load')
def load():
    """One loop = one ball loaded: up, drop the ball in, tamp it, click the hammer back. The cutlass
    stays on his shoulder throughout, as on the idle and the shot."""
    faces = ['look_side', 'look_side', 'idle', 'wink']
    bobs = [(0, 0), (0, 0), (0, 1), (0, 0)]
    out = []
    for i, (spec, face, bob) in enumerate(zip(LOAD_POSES, faces, bobs)):
        out.append((['up', 'drop', 'tamp', 'click'][i],
                    A.Pose(expr=face, bob=bob, arm_r=None, extra=[hold_gun_up(**spec)], tails=0.3 * (i % 2)),
                    [0.14, 0.14, 0.12, 0.16][i]))
    return out


# ------------------------------------------------------------------ throw (4)
def throw_arm(elbow, wrist, hand, hand_dir):
    """His free left arm (screen right) heaving: the pistol tucked in his sash, an open hand the
    barrel (FX) sits in."""
    def draw(F):
        AP.pistol_sash(F)
        AP.arm(F, AP.SH_R, elbow, wrist, lit=False)
        F.body(AP.open_hand(hand, hand_dir, lit=False))
    draw.hand = hand
    return draw


THROW_POSES = [
    # wind-up: dropped into a crouch, the arm swung down and back to scoop the barrel up
    ('windup', dict(elbow=(72.0, 63.0), wrist=(76.0, 71.0), hand=(78.0, 75.0), hand_dir=(0.3, 1.0)),
     dict(bob=(0, 2), head=(1, 1), expr='strain', tails=0.4), 0.16),
    # heave: rising, the arm swung up over his shoulder, the barrel over his head
    ('heave', dict(elbow=(72.0, 44.0), wrist=(72.0, 34.0), hand=(72.0, 30.0), hand_dir=(0.0, -1.0)),
     dict(bob=(0, -1), head=(0, 0), expr='strain', tails=1.0), 0.12),
    # release: arm thrown out forward and up to the right, the barrel away
    ('release', dict(elbow=(75.0, 46.0), wrist=(82.0, 40.0), hand=(85.5, 37.5), hand_dir=(0.8, -0.6)),
     dict(bob=(0, 0), head=(2, 0), expr='shot', tails=1.4, flare=True), 0.10),
    # follow-through: the arm carried on down across him, the grin kept
    ('follow', dict(elbow=(73.0, 58.0), wrist=(79.0, 63.0), hand=(82.0, 66.0), hand_dir=(0.6, 0.8)),
     dict(bob=(0, 1), head=(2, 1), expr='idle', tails=0.8, flare=True), 0.18),
]


@sheet('burak_throw')
def throw():
    """wind-up, heave, release, follow-through. The barrel is FX: it sits in his open hand (HAND
    anchors) and leaves it on the release frame (2)."""
    out = []
    for name, arm, pose, hold in THROW_POSES:
        out.append((name, A.Pose(arm_r=throw_arm(**arm), **pose), hold))
    return out


# ------------------------------------------------------------------ taunt (4 loop): the punish window
def twirl_arm(gun_dir, grip_dir):
    """His arm flung out wide at shoulder height, the flintlock spinning round his trigger finger."""
    def draw(F):
        AP.arm(F, AP.SH_R, (72.0, 55.0), (78.5, 56.5), lit=False)
        finger = (82.0, 57.0)
        AP.pistol(F, finger, gun_dir, grip_dir, barrel_len=8.5, grip_len=4.0, bell_len=4.5, r_bar=2.0,
                  r_bell=4.3, mouth_tip=0.5)
        F.body(AP.open_hand((79.5, 56.5), (1.0, 0.1), lit=False, r=2.9))
    return draw


@sheet('burak_taunt')
def taunt():
    """The cocky punish beat, wide OPEN: blowing the smoke off his muzzle (the smoke is FX), then a
    showy twirl of the pistol round his finger with his arm flung wide. The cutlass lounges on his
    shoulder the whole time; his chest and face are wide open to a punch."""
    blow_a = hold_gun_up(wrist=(68.0, 57.0), breech=(68.5, 53.0), elbow=(72.5, 63.0), barrel=(-0.28, -1.0),
                         grip=(0.9, 0.5))
    blow_b = hold_gun_up(wrist=(68.0, 57.0), breech=(68.5, 53.0), elbow=(72.5, 63.0), barrel=(-0.24, -1.0),
                         grip=(0.9, 0.5))
    return [
        ('blow', A.Pose(expr='blow', head=(0, -1), hat=0.0, arm_r=None, extra=[blow_a], tails=0.4), 0.30),
        ('blow2', A.Pose(expr='blow', head=(1, 0), hat=0.05, arm_r=None, extra=[blow_b], tails=0.9), 0.30),
        ('twirl', A.Pose(expr='idle', head=(0, -1), arm_r=twirl_arm((0.3, -1.0), (0.6, 1.0)), tails=0.5), 0.12),
        ('twirl2', A.Pose(expr='idle', head=(0, -1), arm_r=twirl_arm((0.45, 0.9), (-0.9, -0.3)), tails=1.0), 0.12),
    ]


# ------------------------------------------------------------------ anchors, per sheet
def _r(p, P):
    """An approved-frame point through the pose's bob and frame offsets, as a whole texel."""
    return (int(round(p[0] + P.bob[0] + P.ox)), int(round(p[1] + P.bob[1] + P.oy)))


def anchors(name, i, P):
    a = {}
    if name == 'burak_fire':
        a['muzzle'] = _r(FIRE_MUZZLE[i], P)
    elif name == 'burak_load':
        sp = LOAD_POSES[i]
        a['muzzle'] = _r(gun_mouth(sp['breech']), P)
        if sp.get('ball'):
            a['ball'] = _r(sp['ball'], P)
    elif name == 'burak_throw':
        a['hand'] = _r(THROW_POSES[i][1]['hand'], P)
        if i == 2:
            a['release'] = a['hand']
    elif name == 'burak_slash':
        hand, tip = SLASH[i][2], SLASH[i][3]
        a['blade'] = (_r(hand, P), _r(tip, P))
        if i % 3 == 1:
            # the strike's hit arc: the tip's path wind-up -> strike -> follow-through, round the fist
            frames = slash()
            a['arc'] = tuple(_r(SLASH[j][3], frames[j][1]) for j in (i - 1, i, i + 1))
    elif name == 'burak_run':
        hand, tip = RUN[i][2][0], RUN[i][2][1]
        a['blade'] = (_r(hand, P), _r(tip, P))
    elif name == 'burak_taunt' and i < 2:
        a['muzzle'] = _r(gun_mouth((68.5, 53.0), (-0.28, -1.0) if i == 0 else (-0.24, -1.0)), P)
    return a


# ------------------------------------------------------------------ slash (9): 128x96
def hand_on_hip(F):
    """His free arm (screen right): the pistol tucked in his sash, the fist planted on his hip.
    One-handed swordplay: too good to need the other hand."""
    AP.pistol_sash(F)
    AP.arm(F, AP.SH_R, (71.0, 60.0), (65.5, 66.0), lit=False)
    F.body(AP.fist((64.5, 67.0), (-0.6, 0.8), lit=False))


def sword_arm(elbow, hand, tip, bow=2.2, bow_side=1.0):
    """His sword arm (screen left) swinging the cutlass: shoulder -> elbow -> the fist round the grip,
    the blade out to the tip. The hilt and the knuckle-bow are drawn at the fist."""
    def draw(F):
        AP.arm(F, AP.SH_L, elbow, hand, lit=True)
        ux, uy = AP.unit(tip[0] - hand[0], tip[1] - hand[1])
        guard = (hand[0] + ux * 3.0, hand[1] + uy * 3.0)
        AP.cutlass(F, guard, tip, bow=bow)
        F.body(AP.fist(hand, (ux, uy), lit=True))
        AP.knuckle_bow(F, guard, tip, side=bow_side)
    draw.blade = (hand, tip)
    return draw


def planted_legs(a, b):
    """a: his right leg (screen left), b: his left leg (screen right), each (knee, ankle, toe) in the
    approved frame's terms; the hips ride the body's bob, the feet stay where they are put. The leg
    further back (smaller knee x) is drawn first."""
    def draw(F):
        bx, by = F.P.bob
        legs = [((44.0 + bx, 73.0 + by), a, True), ((52.0 + bx, 73.0 + by), b, False)]
        for hip, (knee, ankle, toe), lit in sorted(legs, key=lambda t: t[1][0][0]):
            AP.leg(F, hip, knee, ankle, toe, lit=lit, planted='abs')
    return draw


# The backhand's lunge: his left foot (screen right) stepped out toward the player, the right leg
# braced back, both knees bent, so the backhand can sweep at the player's height.
LUNGE_A = ((40.0, 85.0), (33.0, 89.5), (28.0, 92.0))       # braced back
LUNGE_B = ((67.0, 84.0), (72.0, 90.0), (77.5, 92.0))       # stepped out
LUNGE_B2 = ((65.0, 83.0), (72.0, 90.0), (77.5, 92.0))      # the same foot, the knee settling

# (name, elbow, hand, tip, pose kw, hold). Points in the approved 96-frame coordinates: the 128-wide
# frame adds 16 to x. The strike frames (1, 4, 7) carry the blade at the middle of its sweep.
SLASH = [
    # 1. side slash, forehand, left to right, at chest height
    ('side_windup', (24.0, 49.0), (21.0, 40.0), (5.0, 12.0), dict(bob=(-1, 0), head=(-1, 0), expr='fierce'), 0.16),
    ('side_strike', (40.0, 58.0), (54.0, 58.0), (88.0, 55.0), dict(bob=(1, 1), head=(2, 1), expr='fierce', flare=True, tails=1.2), 0.08),
    ('side_follow', (46.0, 63.0), (58.0, 67.0), (86.0, 85.0), dict(bob=(2, 1), head=(3, 1), expr='fierce', flare=True, tails=1.5), 0.12),
    # 2. backhand: cocked across his body over his left shoulder, then a lunge that sweeps the blade
    #    back across at the player's height (knee to thigh on him), carried through low to his right
    ('back_windup', (46.0, 56.0), (60.0, 52.0), (86.0, 32.0), dict(bob=(2, 2), head=(2, 1), expr='fierce', tails=1.0), 0.12),
    ('back_strike', (39.0, 62.0), (50.0, 71.0), (86.0, 82.0), dict(bob=(4, 5), head=(3, 2), expr='fierce', tails=1.2,
                                                                     flare=True, sweep=5.0,
                                                                     legs=planted_legs(LUNGE_A, LUNGE_B)), 0.08),
    ('back_follow', (25.0, 61.0), (17.0, 64.0), (-9.0, 74.0), dict(bob=(1, 4), head=(0, 2), expr='fierce', tails=0.5,
                                                                   sweep=3.0,
                                                                   legs=planted_legs(LUNGE_A, LUNGE_B2)), 0.12),
    # 3. overhead chop: raised high over his hat, brought down in front of him to the right
    ('over_windup', (38.0, 20.0), (45.0, 6.0), (14.0, -8.0), dict(bob=(0, -1), head=(0, 0), expr='fierce', tails=0.8), 0.18),
    ('over_strike', (46.0, 50.0), (60.0, 52.0), (88.0, 70.0), dict(bob=(1, 1), head=(2, 1), expr='fierce', flare=True, tails=1.4), 0.08),
    ('over_follow', (42.0, 60.0), (54.0, 68.0), (76.0, 91.0), dict(bob=(2, 2), head=(2, 2), expr='fierce', flare=True, tails=1.6), 0.14),
]


@sheet('burak_slash')
def slash():
    """3 swings x (wind-up, strike, follow-through): side slash, backhand, overhead. 128x112 frames
    (reach to the right, and headroom over his tricorn for the overhead), feet on row 111, centre
    column 64. His free hand stays planted on his hip."""
    out = []
    for name, elbow, hand, tip, kw, hold in SLASH:
        out.append((name, A.Pose(fw=128, fh=112, arm_l=sword_arm(elbow, hand, tip), arm_r=hand_on_hip, **kw), hold))
    return out


# ------------------------------------------------------------------ run (6 loop): 128x96
HIP_L, HIP_R = (44.0, 73.0), (52.0, 73.0)


def run_legs(l, r):
    """l / r: (knee, ankle, toe) for his right leg (screen left) and left leg (screen right). The
    trailing leg is drawn first."""
    def draw(F):
        for (hip, spec, lit) in sorted(((HIP_L, l, True), (HIP_R, r, False)), key=lambda t: t[1][0][0]):
            AP.leg(F, hip, *spec, lit=lit, planted=True)
    return draw


def run_arms(sword_hand, sword_tip, sword_elbow, free_elbow, free_hand):
    """The cutlass drawn and carried forward, low and ready; the free arm pumping, its fist swinging."""
    def sword(F):
        AP.arm(F, AP.SH_L, sword_elbow, sword_hand, lit=True)
        ux, uy = AP.unit(sword_tip[0] - sword_hand[0], sword_tip[1] - sword_hand[1])
        guard = (sword_hand[0] + ux * 3.0, sword_hand[1] + uy * 3.0)
        AP.cutlass(F, guard, sword_tip, bow=2.0)
        F.body(AP.fist(sword_hand, (ux, uy), lit=True))
        AP.knuckle_bow(F, guard, sword_tip)

    def free(F):
        AP.pistol_sash(F)
        AP.arm(F, AP.SH_R, free_elbow, free_hand, lit=False)
        F.body(AP.fist(free_hand, (0.0, 1.0), lit=False))
    return sword, free


# (name, legs (l, r), sword (hand, tip, elbow), free arm (elbow, hand), bob). The leading leg strides
# out into the open right of the swept-back hem, so the whole boot shows; the trailing leg kicks back
# behind the coat, where it would be.
RUN = [
    ('contact_r', (((38.0, 81.0), (30.0, 86.0), (26.0, 81.0)), ((62.0, 80.0), (69.0, 88.5), (75.0, 92.0))),
     ((52.0, 64.0), (84.0, 66.0), (40.0, 64.0)), ((70.0, 60.0), (64.0, 66.0)), (2, 1)),
    ('down_r', (((44.0, 80.0), (40.0, 87.0), (44.0, 90.0)), ((60.0, 81.0), (61.0, 89.0), (67.0, 92.0))),
     ((52.0, 65.0), (84.0, 68.0), (40.0, 65.0)), ((71.0, 61.0), (68.0, 67.0)), (2, 2)),
    ('pass_r', (((62.0, 76.0), (64.0, 85.0), (70.0, 86.0)), ((52.0, 82.0), (45.0, 89.0), (39.0, 87.0))),
     ((52.0, 63.0), (84.0, 64.0), (40.0, 63.0)), ((72.0, 58.0), (76.0, 52.0)), (2, 0)),
    ('contact_l', (((62.0, 80.0), (69.0, 88.5), (75.0, 92.0)), ((40.0, 81.0), (32.0, 86.0), (28.0, 81.0))),
     ((52.0, 64.0), (84.0, 66.0), (40.0, 64.0)), ((72.0, 58.0), (77.0, 53.0)), (2, 1)),
    ('down_l', (((60.0, 81.0), (61.0, 89.0), (67.0, 92.0)), ((46.0, 80.0), (42.0, 87.0), (46.0, 90.0))),
     ((52.0, 65.0), (84.0, 68.0), (40.0, 65.0)), ((71.0, 60.0), (72.0, 55.0)), (2, 2)),
    ('pass_l', (((50.0, 82.0), (43.0, 89.0), (37.0, 87.0)), ((62.0, 76.0), (64.0, 85.0), (70.0, 86.0))),
     ((52.0, 63.0), (84.0, 64.0), (40.0, 63.0)), ((70.0, 60.0), (65.0, 65.0)), (2, 0)),
]


@sheet('burak_run')
def run():
    """The chase: 6 frames looping, leaning into it, the cutlass drawn and carried forward, the coat
    and the bandana streaming back. 128x96 frames, feet on row 95, centre column 64."""
    out = []
    for name, (l, r), (sh, st, se), (fe, fh), bob in RUN:
        sword, free = run_arms(sh, st, se, fe, fh)
        out.append((name, A.Pose(fw=128, bob=bob, head=(1, 0), expr='fierce', hat=-0.04, tails=2.2,
                                 sweep=7.0, legs=run_legs(l, r), arm_l=sword, arm_r=free), 0.08))
    return out


# ------------------------------------------------------------------ idle (4 loop)
@sheet('burak_idle')
def idle():
    """f0 is the approved frame. A slow, smug breath: he settles a pixel, blinks, the bandana tails
    and the hat stir. His feet stay planted."""
    return [
        ('rest', A.Pose(), 0.30),
        ('breathe', A.Pose(bob=(0, 1), tails=0.5), 0.20),
        ('blink', A.Pose(bob=(0, 1), expr='blink', tails=1.0, hat=0.02), 0.12),
        ('settle', A.Pose(tails=0.5), 0.20),
    ]


# ------------------------------------------------------------------ broken (4 loop)
def drooped_sword(sway):
    """His sword arm gone limp at his side, the cutlass hanging, its tip dragging on the mat."""
    def draw(F):
        AP.arm(F, AP.SH_L, (28.5 + sway * 0.5, 63.0), (30.0 + sway, 72.0), lit=True)
        tip = (22.0 + sway * 2, 93.0 - F.P.bob[1])
        hand = (30.5 + sway, 74.0)
        ux, uy = AP.unit(tip[0] - hand[0], tip[1] - hand[1])
        guard = (hand[0] + ux * 3.0, hand[1] + uy * 3.0)
        AP.cutlass(F, guard, tip, bow=-1.5)
        F.body(AP.fist(hand, (ux, uy), lit=True))
        AP.knuckle_bow(F, guard, tip)
    return draw


@sheet('burak_broken')
def broken():
    """The Break state: stunned and dizzy, the juggle's @ @ eyes and wobbly mouth, knees buckled,
    swaying, the hat slipping, the cutlass drooping to drag on the mat and the pistol dangling. The
    code's daze stars go over the crown anchor."""
    out = []
    for i, (sx, hx, tilt) in enumerate(((-1, -2, -0.05), (0, -1, -0.02), (1, 1, 0.04), (0, 0, 0.01))):
        out.append(('sway%d' % i, A.Pose(bob=(sx, 2), head=(hx, 1), expr='dizzy', hat=tilt, hat_off=(hx // 2, 1),
                                         tails=0.3, arm_l=drooped_sword(sx)), 0.18))
    return out


# ------------------------------------------------------------------ hit (2)
@sheet('burak_hit')
def hit():
    """Punched: snapped back with the smirk knocked off, the hat knocked askew; then the gritted
    recoil."""
    return [
        ('snap', A.Pose(bob=(-2, 0), head=(-2, 0), expr='hit', hat=-0.06, hat_off=(-2, 1), tails=1.6), 0.10),
        ('recoil', A.Pose(bob=(-1, 1), head=(-1, 1), expr='pain', hat=-0.03, hat_off=(-1, 1), tails=0.8), 0.14),
    ]


# ------------------------------------------------------------------ laugh (4 loop): the cutscene
DROP = [".B.", "BBA", ".A."]


def tears(*pts):
    """Tears of laughter flying off his face: small keylined drops, in the head's coordinates."""
    def draw(F):
        for (x, y) in pts:
            F.headpart(A.amap(DROP, x - 1, y - 1))
    return draw


def point_arm(elbow, wrist, fist_at):
    """His free arm (screen right) flung out at the player, the finger pointing; the pistol in his sash."""
    def draw(F):
        AP.pistol_sash(F)
        AP.arm(F, AP.SH_R, elbow, wrist, lit=False)
        F.body(AP.point_hand_r(fist_at), outline='soft')
    draw.finger = fist_at
    return draw


def slap_arm(elbow, wrist, hand, d, ticks=()):
    """His free arm (screen right) come down to slap his knee with an open hand; small white slap ticks."""
    def draw(F):
        AP.pistol_sash(F)
        AP.arm(F, AP.SH_R, elbow, wrist, lit=False)
        F.body(AP.open_hand(hand, d, lit=False, r=3.4))
        for (x0, y0, x1, y1) in ticks:
            F.body({q: 'W' for q in A.line(x0, y0, x1, y1)}, outline=False)
    return draw


def squat_legs(F):
    """Knees bent and splayed under the coat, the boots planted where the approved stance has them:
    the laugh's doubled-over crouch. The hips ride the body's bob; the feet stay put."""
    bx, by = F.P.bob
    for hip, knee, ankle, toe, lit in (((44.0 + bx, 73.0 + by), (38.5, 83.5), (39.5, 89.0), (35.0, 92.0), True),
                                       ((52.0 + bx, 73.0 + by), (58.5, 83.5), (57.0, 89.0), (61.5, 92.0), False)):
        AP.leg(F, hip, knee, ankle, toe, lit=lit, planted='abs')


LAUGH_FRAME = dict(fw=96, fh=112, hair='tossed')


@sheet('burak_laugh')
def laugh():
    """The cutscene laugh, AT the player: rearing back to point at him with a HA!, then doubled over
    slapping his knee, twice round, the tricorn hopping off his head on every HA. 96x112 frames: the
    hat's hop needs headroom. Feet on row 111, centre column 48."""
    return [
        ('ha', A.Pose(bob=(-1, 1), head=(-1, -1), expr='laugh_big', hat=-0.07, hat_off=(-1, -5), tails=1.4,
                      arm_r=point_arm((72.5, 51.0), (79.0, 49.0), (82.5, 48.5)), **LAUGH_FRAME), 0.13),
        ('slap', A.Pose(bob=(1, 3), head=(2, 3), expr='laugh_big2', hat=0.05, hat_off=(0, 2), tails=0.4,
                        legs=squat_legs,
                        arm_r=slap_arm((68.0, 63.0), (62.5, 72.5), (60.0, 76.0), (-0.25, 1.0),
                                       ticks=((66, 72, 68, 70), (67, 76, 70, 76), (66, 80, 68, 82))),
                        **LAUGH_FRAME), 0.11),
        ('ha2', A.Pose(bob=(0, 1), head=(0, -1), expr='laugh_big', hat=0.06, hat_off=(1, -4), tails=1.8,
                       arm_r=point_arm((73.0, 52.0), (79.5, 50.5), (83.0, 50.0)), **LAUGH_FRAME), 0.13),
        ('slap2', A.Pose(bob=(1, 2), head=(2, 3), expr='laugh_big2', hat=-0.03, hat_off=(0, 1), tails=0.8,
                         legs=squat_legs,
                         arm_r=slap_arm((68.0, 62.5), (63.0, 71.0), (61.0, 74.0), (-0.25, 1.0)),
                         **LAUGH_FRAME), 0.11),
    ]


# ------------------------------------------------------------------ talk (pairs: mouth shut / open)
def belly_arm(F):
    """His free hand (screen right) on his belly for the chuckle; the pistol in his sash."""
    AP.pistol_sash(F)
    AP.arm(F, AP.SH_R, (70.0, 61.5), (63.5, 66.0), lit=False)
    F.body(AP.open_hand((60.0, 66.5), (-1.0, 0.15), lit=False, r=3.2))


def temple_arm(F):
    """His free hand (screen right) up at his temple, the finger to his head: "Think!". Drawn over
    the head, which it is in front of."""
    AP.arm(F, AP.SH_R, (73.5, 47.5), (67.0, 39.5), lit=False)
    F.headpart(AP.point_hand_u((65.0, 36.5)), outline='soft')


def shrug_arm(F):
    """His free hand (screen right) turned out palm-up at his side: "eh"."""
    AP.pistol_sash(F)
    AP.arm(F, AP.SH_R, (71.0, 62.0), (77.5, 59.5), lit=False)
    F.body(AP.open_hand((80.5, 58.0), (1.0, -0.3), lit=False, r=3.2))


TALK = [
    # (pair, shut face, open face, pose)
    ('smug', 'idle', 'smug_open', dict()),
    ('laugh', 'chuckle', 'chuckle_open', dict(head=(0, -1), hat=0.0, tails=0.6, arm_r=belly_arm)),
    ('point', 'think', 'think_open', dict(head=(1, 0), hat=0.04, tails=0.3, arm_r=AP.pistol_sash,
                                          extra=[temple_arm])),
    ('shrug', 'shrug', 'shrug_open', dict(head=(-1, 1), hat=-0.06, tails=0.5, arm_r=shrug_arm)),
]


@sheet('burak_talk')
def talk():
    """Mouth shut / open pairs for his lines, frame 2n shut and 2n+1 open: smug (the approved idle,
    frame 0 IS the approved frame), laugh (a chuckle, a hand on his belly), point ("Think!", a finger
    to his temple), shrug ("eh", one hand turned out, the cutlass kept on his shoulder)."""
    out = []
    for pair, shut, open_, kw in TALK:
        out.append((pair, A.Pose(expr=shut, **kw), 0.12))
        out.append((pair + '_open', A.Pose(expr=open_, **kw), 0.12))
    return out


# ------------------------------------------------------------------ walk (6 loop): the swagger
def swing_pistol(dx):
    """The approved pistol arm hanging at his side, swung dx whole pixels with the step (the hand and
    the big flintlock move as one; the upper arm follows by half)."""
    def draw(F):
        F.body(B.sleeve((64.5, 53), (68 + dx * 0.5, 62), 4.6, 3.9, lit_side=False))
        F.body(B.cuff((68.5 + dx * 0.5, 63.5), 3.8, 1.5, lit=False))
        F.body(B.limb([((69 + dx * 0.6, 65.5), (69.5 + dx, 68), 2.7, 2.5)], '4', '3', '5', '6'))
        for part in B.pistol_parts((71.5 + dx, 70.5), (0.66, 1.0), (-1.0, 0.3), barrel_len=12.5, grip_len=5.0,
                                   bell_len=6.5, r_bar=2.2, r_bell=5.2, mouth_tip=0.5):
            F.body(part)
        F.body(B.hammer(70 + dx, 66))
        F.body(B.hand_pistol(), outline=False, extra=(dx, 0))
    return draw


def walk_legs(a, b):
    """The walk's legs: planted_legs (the hips ride the bob, the feet stay put)."""
    return planted_legs(a, b)


# (name, a, b, bob, head, hat tilt, pistol swing, tails, flare). Contact, down, passing, for each leg
# in turn; the hips roll toward the supporting leg, the head counters it, the hat rocks, the pistol
# swings against the step and the striding leg kicks the coat's skirt out on the contacts.
WALK = [
    ('contact_b', ((40.0, 82.0), (35.0, 88.5), (30.0, 92.0)), ((59.5, 81.5), (65.0, 89.0), (70.5, 92.0)),
     (0, 0), (0, 0), 0.02, -2, 0.8, True),
    ('down_b', ((42.0, 81.5), (38.5, 87.5), (35.0, 90.0)), ((57.5, 82.0), (61.0, 89.0), (66.5, 92.0)),
     (1, 2), (-1, 0), 0.03, -1, 1.2, False),
    ('pass_b', ((48.0, 78.5), (47.0, 85.0), (52.0, 87.0)), ((54.5, 81.0), (56.0, 89.0), (61.0, 92.0)),
     (1, -1), (-1, 0), 0.0, 0, 1.0, False),
    ('contact_a', ((57.0, 81.5), (62.5, 89.0), (68.0, 92.0)), ((46.0, 82.0), (41.0, 88.5), (36.0, 92.0)),
     (0, 0), (0, 0), -0.02, 2, 0.8, True),
    ('down_a', ((55.5, 82.0), (58.5, 89.0), (64.0, 92.0)), ((47.0, 81.5), (43.5, 87.5), (40.0, 90.0)),
     (-1, 2), (1, 0), -0.03, 1, 1.2, False),
    ('pass_a', ((50.5, 81.0), (51.5, 89.0), (56.5, 92.0)), ((53.0, 78.5), (52.0, 85.0), (57.0, 87.0)),
     (-1, -1), (1, 0), 0.0, 0, 1.0, False),
]


@sheet('burak_walk')
def walk():
    """The swaggering intro walk: 6 frames looping, the cutlass lounging on his shoulder, the pistol
    swinging at his side, hips rolling, the hat rocking, the smirk never leaving his face."""
    out = []
    for name, a, b, bob, head, tilt, swing, tails, flare in WALK:
        out.append((name, A.Pose(bob=bob, head=head, hat=tilt, tails=tails, sweep=3.0, flare=flare,
                                 legs=walk_legs(a, b), arm_r=swing_pistol(swing)), 0.12))
    return out


# ------------------------------------------------------------------ defeat (6, holds the last)
class _Ground:
    """Draws props straight into the frame's own terms, ignoring the body's bob: things dropped on
    the mat stay where they fell."""

    def __init__(self, F):
        self.F = F
        self.P = F.P

    def body(self, part, outline=True, owner=None, extra=(0, 0)):
        self.F.put(part, extra[0], extra[1], outline, owner)


def ground_cutlass(guard, tip, bow=1.4):
    def draw(F):
        AP.cutlass(_Ground(F), guard, tip, bow=bow)
    return draw


def ground_pistol(breech, barrel, grip):
    def draw(F):
        AP.pistol(_Ground(F), breech, barrel, grip, barrel_len=8.5, grip_len=4.5, bell_len=4.5, r_bar=1.9,
                  r_bell=3.9, mouth_tip=0.5)
    return draw


def limp_l(F):
    """His sword arm (screen left) hanging limp, the hand open and empty."""
    AP.arm(F, AP.SH_L, (28.0, 63.0), (29.0, 71.5), lit=True)
    F.body(AP.open_hand((29.5, 75.0), (0.1, 1.0), lit=True))


def limp_r(F):
    """His pistol arm (screen right) hanging limp, the hand open and empty."""
    AP.arm(F, AP.SH_R, (68.0, 63.0), (67.0, 71.5), lit=False)
    F.body(AP.open_hand((66.5, 75.0), (-0.1, 1.0), lit=False))


def hands_on_knees_l(F):
    """His sword arm (screen left) slumped forward, the empty hand resting on his knee."""
    AP.arm(F, AP.SH_L, (28.5, 63.5), (37.0, 73.0), lit=True)
    F.body(AP.open_hand((39.5, 76.0), (0.45, 1.0), lit=True))


def hands_on_knees_r(F):
    """His pistol arm (screen right) slumped forward, the empty hand resting on his knee."""
    AP.arm(F, AP.SH_R, (67.5, 63.5), (59.0, 73.0), lit=False)
    F.body(AP.open_hand((56.5, 76.0), (-0.45, 1.0), lit=False))


def kneel_legs(F):
    """Down on both knees: the thighs dropped short under the coat, the knees on the mat in the parted
    skirt, each boot's turned-down cuff lying on the mat under its knee, the shins folded away behind."""
    bx, by = F.P.bob
    G = _Ground(F)
    for hip, knee, lit in (((44.0 + bx, 73.0 + by), (41.0 + bx, 87.5), True),
                           ((52.0 + bx, 73.0 + by), (55.0 + bx, 87.5), False)):
        th = A.fill(A.capsule(hip, knee, 3.4, 3.3), '9')
        A.cylinder(th, hip, knee, 3.4, '0987' if lit else '9877', (0.55, 0.15, -0.3))
        G.body(th)
        cuff = A.fill(A.ellipse(knee[0], knee[1] + 3.6, 4.7, 2.5), 't')
        for (x, y) in list(cuff):
            lo = min(xx for (xx, yy) in cuff if yy == y)
            hi = max(xx for (xx, yy) in cuff if yy == y)
            t = (x - lo) / max(1, hi - lo)
            cuff[(x, y)] = 'u' if (t < 0.25 and lit) else ('t' if t < 0.55 else ('r' if t < 0.85 else 'q'))
        top = min(y for (_, y) in cuff)
        for (x, y) in list(cuff):
            if y == top:
                cuff[(x, y)] = 'u' if cuff[(x, y)] in 'ut' else 't'      # the rolled rim catches the light
        G.body(cuff)
        cap = A.fill(A.ellipse(knee[0], knee[1] + 0.5, 3.0, 2.2), '9')    # the trouser knee over it
        A.rim(cap, '0', -1, 0)
        A.rim(cap, '0', 0, -1, only='9')
        A.rim(cap, '8', 1, 0)
        G.body(cap)


KNEEL = dict(bob=(0, 9), skirt_to=85, part_skirt=3.0, legs=kneel_legs, arm_l=limp_l, arm_r=limp_r,
             hat_clip=True, tails=0.0)
DROPPED = [ground_cutlass((25.0, 89.5), (4.0, 85.5)), ground_pistol((73.0, 87.5), (1.0, 0.12), (-0.75, 0.55))]
SLUMP = dict(KNEEL, arm_l=hands_on_knees_l, arm_r=hands_on_knees_r)


@sheet('burak_defeat')
def defeat():
    """Beaten: the last punch snaps him back, he reels dizzy, his knees buckle as the cutlass and the
    pistol slip from his hands, he drops to his knees, slumps, and the tricorn slides down over his
    eyes. Holds the last frame."""
    return [
        ('struck', A.Pose(bob=(-2, 0), head=(-2, 0), expr='hit', hat=-0.06, hat_off=(-2, 1), tails=1.6), 0.14),
        ('reel', A.Pose(bob=(1, 2), head=(1, 1), expr='dizzy', hat=0.05, hat_off=(1, 2), tails=0.4,
                        arm_l=drooped_sword(1)), 0.18),
        ('buckle', A.Pose(bob=(0, 5), head=(0, 1), expr='stunned', hat=0.07, hat_off=(0, 3), tails=0.2,
                          legs=squat_legs, arm_l=limp_l, arm_r=limp_r,
                          extra=[ground_cutlass((27.0, 84.0), (15.0, 92.0), bow=1.0),
                                 ground_pistol((74.0, 80.0), (0.55, 1.0), (-0.9, 0.2))]), 0.14),
        ('knees', A.Pose(head=(0, 1), expr='pain', hat=0.03, hat_off=(0, 5), extra=DROPPED, **KNEEL), 0.12),
        ('slump', A.Pose(head=(0, 3), expr='defeat', hat=0.02, hat_off=(0, 8), extra=DROPPED, **SLUMP), 0.18),
        ('defeated', A.Pose(head=(0, 4), expr='defeat2', hat=0.0, hat_off=(0, 10), extra=DROPPED, **SLUMP), 1.00),
    ]


# ------------------------------------------------------------------ the dialogue portrait (64x64)
@sheet('portrait')
def portrait():
    """His dialogue portrait, 64x64: his own pixels 1:1, the approved idle frame's head and shoulders
    (x 16-79, y 0-63): the tricorn with its bandana tails, the smirk, the gold chain and collar, the
    cutlass resting on his shoulder. Written as portrait.png beside the sheets."""
    return [('portrait', A.Pose(fw=64, fh=64, crop=(16, 0)), 1.0)]
