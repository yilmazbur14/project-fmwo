import math
import lib
import brig as rig
import sword128
from brig import Frame128, FL
from sword import Sword
import arms as A
from pngio import write_png, read_png, scale, blank, paste, crop

APPROVED = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_sword.png'

SH_L = (33.0, 83.0)     # viewer-left shoulder joint (his right), hidden under the pauldron
SH_R = (95.0, 83.0)     # viewer-right shoulder joint (his left)
UPPER, FORE = 17.0, 15.0


def front_body(f, crouch=0, lean=0, head_dx=0, head_dy=0, hooks=None, keep_hip_arm=False,
               keep_sword_arm_back=False, paul_L=(0, 0), paul_R=(0, 0)):
    """composite the front body. crouch: px the upper body sinks. lean: px the upper body shifts in x
    (head shifts a bit more). hooks: dict stage -> callable(f, c, lx) at 'back', 'under_paul', 'over_paul',
    'under_head', 'front'."""
    hooks = hooks or {}
    c = crouch
    lo = int(round(c * 0.5))
    lx = lean
    llo = int(round(lean * 0.5))
    run = lambda k: hooks.get(k) and hooks[k](f, c, lx)
    run('back')
    f.put('cape', llo, lo if c > 2 else 0)
    f.put('legs')
    run('legs')
    f.put('flap', llo, lo)
    f.put('tassets', llo, lo)
    f.put('belt', lx, c)
    f.put('torso', lx, c)
    f.put('beltdet', lx, c)
    f.put('gorget', lx, c)
    run('under_paul')
    if keep_hip_arm:
        f.put('uarm_R', lx, c)
    if keep_sword_arm_back:
        f.put('uarm_L', lx, c)
    f.put('paul_L', lx + paul_L[0], c + paul_L[1])
    f.put('paul_R', lx + paul_R[0], c + paul_R[1])
    run('over_paul')
    if keep_hip_arm:
        f.put('farm_R', lx, c)
    run('under_head')
    f.put('head', lx + head_dx, c + head_dy)
    run('front')
    return f


def arm_chain(f, S, Hn, bend=1, hand=None, hand_flip=False, draw_upper=True, elbow_on_top=True, E=None):
    if E is None:
        E = A.solve_elbow(S, Hn, UPPER, FORE, bend)
    if draw_upper:
        A.upper_arm(f.cv, S, E, 5.0)
    A.vambrace(f.cv, E, Hn)
    if elbow_on_top:
        A.elbow(f.cv, E)
    if hand:
        A.hand(f.cv, hand, Hn, flip=hand_flip)
    return E


def sword_from_hand(hand_xy, ang, sa=1.0, sb=1.0, grip_a=-10.0):
    """Sword whose grip point a=grip_a sits at hand_xy."""
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    o = (hand_xy[0] - u[0] * grip_a * sa, hand_xy[1] - u[1] * grip_a * sa)
    return Sword(o, ang, sa, sb)


def to_px(f):
    return f.rgba()


def sheet(frames, s, path, pad=4, bg=(40, 40, 40, 255), cols=None):
    cols = cols or len(frames)
    rows = (len(frames) + cols - 1) // cols
    out = blank(pad + cols * (128 * s + pad), pad + rows * (128 * s + pad), bg)
    for i, px in enumerate(frames):
        paste(out, scale([[p if p[3] else FL for p in r] for r in px], s), pad + (i % cols) * (128 * s + pad),
              pad + (i // cols) * (128 * s + pad))
    write_png(path, len(out[0]), len(out), out)


def approved_px():
    return read_png(APPROVED)[2]
