"""The wave-1 poses, as bone rotations (degrees, clockwise) and shifts (design units) on the rig.

Feet that stay planted are solved with leg_ik onto their rest ankles; airborne legs are set by hand.
Every sheet's frames are listed with the render options they need.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kjr as R  # noqa: E402

PX = 1.0 / R.BASE_SC            # one frame pixel, in design units
N_ANKLE = R.BONES['n_foot'][1]
F_ANKLE = R.BONES['f_foot'][1]


def P(**kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, tuple):
            out[k] = (float(v[0]), float(v[1]), float(v[2]))
        else:
            out[k] = (float(v), 0.0, 0.0)
    return out


def planted(pose, n=True, f=True, n_foot=0.0, f_foot=0.0, n_at=None, f_at=None, tail=True):
    if n:
        R.leg_ik(pose, 'n', n_at or N_ANKLE, foot_world=n_foot)
    if f:
        R.leg_ik(pose, 'f', f_at or F_ANKLE, foot_world=f_foot)
    if tail:
        R.tail_ground(pose)
    return pose


def up(px_dy):
    """A shift of the pelvis by whole frame pixels (negative = up)."""
    return px_dy * PX


#IDLE: a slow breath, the upper body settling a pixel, the claws easing, the tail tip curling

def idle(i):
    if i == 0:
        return {}
    sink = [0, 0, 1, 1, 1, 0][i]
    claw = [0, -2, -4, -4, -2, 0][i]
    tip = [0, -3, -6, -7, -4, -1][i]
    pose = P(chest=(0, 0, sink * PX), n_fore=claw, f_fore=claw * 0.5, t6=tip, t5=tip * 0.4)
    return pose


#THE BREATH STANCE (the body under the head layer)

def charge(i):
    if i == 0:
        return {}
    return P(n_fore=-5, f_fore=-6, n_upper=-2)


#THE STOMP: rear, leap, drop, stomp

def rear(i):
    if i == 0:
        pose = P(pelvis=(-5, 0, up(-2)), chest=-9, head=-16, jaw=12, n_upper=-35, n_fore=-25,
                 f_upper=-30, f_fore=-15, t1=5, t2=3)
    elif i == 1:
        pose = P(pelvis=(-8, 0, up(-4)), chest=-15, head=-24, jaw=22, n_upper=-62, n_fore=-38,
                 f_upper=-52, f_fore=-28, t1=9, t2=5, t3=3)
    elif i == 2:
        pose = P(pelvis=(4, 0, up(7)), chest=10, head=6, jaw=6, n_upper=24, n_fore=18, f_upper=20,
                 f_fore=10, t1=-5, t2=-3)
    else:
        pose = P(pelvis=(8, 0, up(13)), chest=17, head=10, n_upper=40, n_fore=28, f_upper=34, f_fore=18,
                 t1=-11, t2=-6, t3=-4)
    return planted(pose)


def leap(i):
    if i == 0:      # push-off: legs driving straight, heels up, arms swept up
        pose = P(pelvis=(-4, 0, up(-12)), chest=-8, head=-10, n_upper=-72, n_fore=-30, f_upper=-62,
                 f_fore=-20, t1=6, t2=4)
        return planted(pose, n_foot=28, f_foot=24, n_at=(N_ANKLE[0] + 2, N_ANKLE[1] - 5),
                       f_at=(F_ANKLE[0] + 2, F_ANKLE[1] - 5), tail=False)
    if i == 1:      # airborne, stretched: legs trailing, toes pointed, tail streaming down
        pose = P(pelvis=(-8, 0, up(-16)), chest=-6, head=-8, n_upper=-84, n_fore=-20, f_upper=-74,
                 f_fore=-10, t1=14, t2=8, t3=4, t4=4)
        return planted(pose, n_foot=55, f_foot=48, n_at=(N_ANKLE[0] - 4, N_ANKLE[1] - 2),
                       f_at=(F_ANKLE[0] - 1, F_ANKLE[1] - 2), tail=False)
    pose = P(pelvis=(2, 0, up(-18)), chest=6, head=4, n_upper=8, n_fore=30, f_upper=4, f_fore=20,
             n_thigh=-46, n_shin=72, n_foot=10, f_thigh=-40, f_shin=66, f_foot=10, t1=14, t2=18, t3=10)
    return pose


def drop(i):
    if i == 0:      # falling into view, the stomping (far, screen-right) foot cocked, its sole to us
        return P(pelvis=(-7, 0, up(-12)), chest=-8, head=12, jaw=14, n_upper=-56, n_fore=-26,
                 f_upper=-50, f_fore=-22, f_thigh=-74, f_shin=86, f_foot=-30, n_thigh=14, n_shin=16,
                 n_foot=30, t1=-16, t2=-10, t3=-6)
    # driving down: the far leg straight and hard under it, the near leg tucked, leaning in
    return P(pelvis=(5, 0, up(-12)), chest=10, head=16, jaw=20, n_upper=24, n_fore=12, f_upper=26,
             f_fore=12, f_thigh=12, f_shin=-8, f_foot=-4, n_thigh=-62, n_shin=92, n_foot=20, t1=-12, t2=-8)


def stomp(i):
    if i == 0:      # impact squash
        pose = P(pelvis=(6, 0, up(11)), chest=14, head=12, jaw=20, n_upper=46, n_fore=22, f_upper=40,
                 f_fore=18, t1=8, t2=4)
    elif i == 1:    # rebound
        pose = P(pelvis=(3, 0, up(4)), chest=6, head=5, jaw=10, n_upper=16, n_fore=8, f_upper=14,
                 f_fore=6, t1=3)
    else:           # settled, glaring
        pose = P(pelvis=(0, 0, up(1)), chest=3, head=4, n_upper=4, f_upper=4)
    return planted(pose)


#THE PARRY: stumble, kneel, stand

def _kneel_legs(pose, drop_px, near_knee=(89.0, 166.0)):
    """The near knee down on the mat in front, the shin laid back along it, the toes curled under;
    the far foot planted with its knee up. Uses the pose's pelvis."""
    probe = R.Rig({k: v for k, v in pose.items() if k == 'pelvis'})
    import math
    H = probe.W('pelvis', R.BONES['n_thigh'][1])
    hip0, knee0 = R.BONES['n_thigh'][1], R.BONES['n_shin'][1]
    ank0 = R.BONES['n_foot'][1]
    th = math.degrees(math.atan2(near_knee[1] - H[1], near_knee[0] - H[0])
                      - math.atan2(knee0[1] - hip0[1], knee0[0] - hip0[0]))
    sh = math.degrees(math.atan2(4.0, -15.0) - math.atan2(ank0[1] - knee0[1], ank0[0] - knee0[0]))
    pel = probe.rot['pelvis']
    pose['n_thigh'] = (th - pel, 0.0, 0.0)
    pose['n_shin'] = (sh - th, 0.0, 0.0)
    pose['n_foot'] = (34.0 - sh, 0.0, 0.0)
    R.leg_ik(pose, 'f', F_ANKLE, foot_world=0.0)
    R.tail_ground(pose)
    return pose


def stumble(i):
    if i == 0:      # the parry lands: thrown back, roaring, the stomping foot bounced off the ground
        pose = P(pelvis=(-10, -3 * PX, up(-2)), chest=-14, head=-28, jaw=18, n_upper=-70, n_fore=-40,
                 f_upper=-60, f_fore=-30, t1=10, t2=4)
        R.leg_ik(pose, 'n', N_ANKLE, foot_world=0.0)
        R.leg_ik(pose, 'f', (F_ANKLE[0] - 2, F_ANKLE[1] - 9), foot_world=-14.0)
        return R.tail_ground(pose)
    if i == 1:      # staggering back (Jordan leaves the seat here)
        pose = P(pelvis=(-14, -6 * PX, up(-1)), chest=-9, head=-20, jaw=10, n_upper=-30, n_fore=-20,
                 f_upper=-82, f_fore=-36, t1=13, t2=6, t3=4)
        R.leg_ik(pose, 'n', (N_ANKLE[0] - 2, N_ANKLE[1]), foot_world=0.0)
        R.leg_ik(pose, 'f', (F_ANKLE[0] - 10, F_ANKLE[1] - 3), foot_world=-8.0)
        return R.tail_ground(pose)
    if i == 2:      # going down onto the near knee
        pose = P(pelvis=(6, 0, up(14)), chest=14, head=16, jaw=6, n_upper=22, n_fore=12, f_upper=26,
                 f_fore=12, t1=-4)
        return _kneel_legs(pose, 14, near_knee=(88.0, 162.0))
    if i == 3:      # the knee hits
        pose = P(pelvis=(8, 0, up(20)), chest=19, head=24, jaw=8, n_upper=34, n_fore=20, f_upper=34,
                 f_fore=16, t1=-2, t2=2)
        return _kneel_legs(pose, 20)
    return kneel(0)


def kneel(i):
    if i == 0:
        pose = P(pelvis=(7, 0, up(18)), chest=16, head=20, jaw=8, n_upper=28, n_fore=16, f_upper=28,
                 f_fore=14)
    else:
        pose = P(pelvis=(7, 0, up(18)), chest=14, head=26, jaw=10, n_upper=30, n_fore=18, f_upper=30,
                 f_fore=16, t6=-6, t5=-2)
    return _kneel_legs(pose, 18)


def stand(i):
    if i == 0:      # pushing up off the knee
        pose = P(pelvis=(4, 0, up(11)), chest=9, head=8, jaw=4, n_upper=10, n_fore=6, f_upper=14,
                 f_fore=8)
        return _kneel_legs(pose, 11, near_knee=(86.0, 158.0))
    if i == 1:
        pose = P(pelvis=(2, 0, up(5)), chest=3, head=1, n_upper=4, f_upper=6)
        return planted(pose, n_at=(N_ANKLE[0] + 3, N_ANKLE[1] - 3), n_foot=10)
    return planted(P(pelvis=(0, 0, up(1)), chest=0, head=-4))


#THE RETURN LANDING

def land(i):
    if i == 0:      # touch-down, legs long, arms out
        pose = P(pelvis=(-3, 0, up(-4)), chest=-5, head=-6, jaw=6, n_upper=-40, n_fore=-16, f_upper=-34,
                 f_fore=-12, t1=-10, t2=-6)
        return planted(pose)
    if i == 1:      # squash
        pose = P(pelvis=(6, 0, up(13)), chest=15, head=11, jaw=12, n_upper=36, n_fore=16, f_upper=30,
                 f_fore=14, t1=7, t3=4)
        return planted(pose)
    pose = P(pelvis=(2, 0, up(4)), chest=4, head=2, n_upper=10, f_upper=8, t1=2)
    return planted(pose)


#SHEETS: name -> [(pose, render options)]

def sheets():
    out = {
        'kaiju_idle': [(idle(i), {}) for i in range(6)],
        'kaiju_charge': [(charge(i), {'head': False}) for i in range(2)],
        'kaiju_rear': [(rear(i), {'jaw_from_pose': True}) for i in range(4)],
        'kaiju_leap': [(leap(i), {'floor': i == 0, 'jaw_from_pose': True}) for i in range(3)],
        'kaiju_drop': [(drop(i), {'floor': False, 'jaw_from_pose': True, 'star_sole': i == 0}) for i in range(2)],
        'kaiju_stomp': [(stomp(i), {'jaw_from_pose': True}) for i in range(3)],
        'kaiju_stumble': [(stumble(i), {'jaw_from_pose': True}) for i in range(5)],
        'kaiju_kneel': [(kneel(i), {'jaw_from_pose': True}) for i in range(2)],
        'kaiju_stand': [(stand(i), {'jaw_from_pose': True}) for i in range(3)],
        'kaiju_land': [(land(i), {'jaw_from_pose': True}) for i in range(3)],
    }
    return out


#THE TOY (drawn at 12%, so every move is pushed further)

def toy_crouch():
    return planted(P(pelvis=(6, 0, up(22)), chest=20, head=8, n_upper=34, f_upper=30))


def toy_hop():
    return leap(1)


def toy_land():
    return planted(P(pelvis=(5, 0, up(15)), chest=14, head=6, n_upper=20, f_upper=18))
