"""Wave-2 poses: roar, bow, hit, tail windup, tail spin, collapse, down. Same rig, same frame."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kjr as R  # noqa: E402
from kjr_poses import P, PX, planted, up, N_ANKLE, F_ANKLE  # noqa: E402


#ROAR: a breath in, rearing up, then the roar held and shaking

ROAR_FULL = dict(pelvis=(-8, 0, up(-3)), chest=-16, head=-30, jaw=27, n_upper=-76, n_fore=-46,
                 f_upper=-62, f_fore=-36, t2=4)


def roar(i):
    if i == 0:
        return planted(P(pelvis=(3, 0, up(3)), chest=8, head=12, n_upper=16, n_fore=8, f_upper=12, f_fore=6))
    if i == 1:
        return planted(P(pelvis=(-6, 0, up(-2)), chest=-11, head=-22, jaw=16, n_upper=-54, n_fore=-34,
                         f_upper=-44, f_fore=-24))
    shake = [(0, 0, 0), (1, -2, -1), (-1, 1, 1), (0, -1, 0)][i - 2]
    kw = dict(ROAR_FULL)
    kw['pelvis'] = (-8 + shake[2] * 0.5, shake[0] * PX, up(-3))
    kw['head'] = -30 + shake[1]
    kw['jaw'] = 27 + shake[1] * 0.5
    kw['n_fore'] = -46 + shake[1] * 3
    kw['f_fore'] = -36 - shake[1] * 3
    return planted(P(**kw))


#BOW: the head lowered to the mat so Jordan can climb back on

def bow(i):
    k = [0.3, 0.62, 0.95, 1.0][i]
    return planted(P(pelvis=(4 * k, 0, up(7 * k)), chest=21 * k, head=36 * k, jaw=4 * k, n_upper=20 * k,
                     n_fore=10 * k, f_upper=18 * k, f_fore=8 * k))


#HIT: a funko blast at its legs

def hit(i):
    if i == 0:
        pose = P(pelvis=(-4, 0, up(-3)), chest=-8, head=-14, jaw=16, n_upper=-36, n_fore=-24, f_upper=-30,
                 f_fore=-18)
        R.leg_ik(pose, 'n', (N_ANKLE[0] - 2, N_ANKLE[1] - 6), foot_world=12.0)
        R.leg_ik(pose, 'f', F_ANKLE, foot_world=0.0)
        return R.tail_ground(pose)
    return planted(P(pelvis=(2, 0, up(2)), chest=5, head=7, jaw=7, n_upper=10, f_upper=8))


#TAIL: the windup (coiling, the tail lifted and drawn back), the spin (a full turn, smeared)

def tail_windup(i):
    k = [0.4, 0.75, 1.0][i]
    return planted(P(pelvis=(3 * k, 0, up(8 * k)), chest=-6 + 18 * k, head=-4 + 10 * k, jaw=8 * k,
                     n_upper=10 * k, n_fore=20 * k, f_upper=-30 * k, f_fore=-20 * k,
                     t1=-34 * k, t2=-22 * k, t3=-16 * k, t4=-12 * k, t5=-10 * k, t6=-8 * k), tail=False)


# the spin: sx per frame (1 = facing right, -1 = facing left, between = mid-turn, squashed and smeared)
SPIN_SX = [1.0, 0.62, -0.62, -1.0, -0.62, 0.62, 1.0, 1.0]
SPIN_SMEAR = [0, 1, 1, 0, -1, -1, 0, 0]       # +1 smear trailing right, -1 left, 0 none


def tail_spin(i):
    """The tail swung out along the mat (its curl opened), the body leaning into the turn."""
    lean = [10, 14, 14, 10, 14, 14, 8, 4][i]
    open_ = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.7, 0.3][i]
    pose = P(pelvis=(2, 0, up(4)), chest=lean, head=lean * 0.6, jaw=10 if i < 6 else 4,
             n_upper=-30, n_fore=-14, f_upper=-38, f_fore=-14,
             t3=0.0, t4=10 * open_, t5=14 * open_, t6=30 * open_)
    return planted(pose)


#THE BREAK: collapse onto its rump, then down and dazed

def _sit(pose, n_at=(95.0, 166.5), f_at=(146.0, 166.0), toes=-28.0):
    R.leg_ik(pose, 'n', n_at, foot_world=toes)
    R.leg_ik(pose, 'f', f_at, foot_world=toes)
    return R.tail_ground(pose)


def collapse(i):
    if i == 0:      # the knees buckle
        return planted(P(pelvis=(4, 0, up(10)), chest=10, head=12, jaw=10, n_upper=-30, n_fore=-20,
                         f_upper=-26, f_fore=-16))
    if i == 1:      # going over backwards
        pose = P(pelvis=(-16, 0, up(20)), chest=-10, head=-20, jaw=18, n_upper=-60, n_fore=-30,
                 f_upper=-50, f_fore=-24)
        return _sit(pose, n_at=(84.0, 164.0), f_at=(136.0, 163.0), toes=-16.0)
    if i == 2:      # down hard on its rump, legs out in front
        pose = P(pelvis=(-12, 0, up(25)), chest=-4, head=8, jaw=10, n_upper=30, n_fore=18, f_upper=30,
                 f_fore=16)
        return _sit(pose)
    return down(0)


def down(i):
    pose = P(pelvis=(-10, 0, up(24)), chest=6 + 2 * i, head=18 + 6 * i, jaw=12 + 2 * i, n_upper=36, n_fore=22,
             f_upper=32, f_fore=18, t6=-4 * i)
    return _sit(pose)


def sheets():
    return {
        'kaiju_roar': [(roar(i), {'jaw_from_pose': True, 'roar': i >= 1}) for i in range(6)],
        'kaiju_bow': [(bow(i), {'jaw_from_pose': True}) for i in range(4)],
        'kaiju_hit': [(hit(i), {'jaw_from_pose': True, 'eye': 'squint'}) for i in range(2)],
        'kaiju_tail_windup': [(tail_windup(i), {'jaw_from_pose': True}) for i in range(3)],
        'kaiju_tail_spin': [(tail_spin(i), {'jaw_from_pose': True, 'sx': SPIN_SX[i], 'smear': SPIN_SMEAR[i]})
                            for i in range(8)],
        'kaiju_collapse': [(collapse(i), {'jaw_from_pose': True,
                                          'eye': ['squint', 'squint', 'squint', 'swirl'][i]}) for i in range(4)],
        'kaiju_down': [(down(i), {'jaw_from_pose': True, 'eye': ['swirl', 'swirl_b'][i]}) for i in range(2)],
    }
