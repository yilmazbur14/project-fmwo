"""Every frame of Carter's core combat set, in the polish style. Frame orders, counts and the ideas in
each frame are the approved sheets' own (art_source/carter_akuma/build_combat.py and combat_poses.py);
timings live in Scripts/CarterArtLayout.gd and are untouched.

    SHEETS[name] = (frame function, frame count)     frame(i) -> Canvas

    carter_akuma.png        3  standing / arms crossed / his back with the 天
    carter_akuma_pose.png   1  arms crossed
    carter_idle.png         4  frame 0 IS his standing frame (the entrance cuts to it); breath + flicker
    carter_eye_flash.png    4  chin dips, head comes up, the slits burn out; 3 = the control-loss frame
    carter_hit.png          2  shunted back a few px, head rocked; annoyed, not hurt
    carter_rush.png         4  the lunge, travelling RIGHT (code flips it)
    carter_rush_pass.png    3  gone through the player: his back, the 天 in fragments
    carter_spent.png        4  the punish window: down on one knee, head hung, breathing
    carter_defeat.png       6  the aura blows out, then he goes down; holds on 5
    carter_aura.png         6  the ambient aura drawn under him (aura_overlay.py)
"""
import math
from lib import Canvas, LIGHTER
import frame0
import frame1
import back
import stand as ST
import faces as FC
import rig34 as RG
import poses34 as PZ
import fx34 as FX
import aura_overlay as AO


# ------------------------------------------------------------------ the approved sheet and pose

def akuma(i):
    return (frame0.build, frame1.build, back.build)[i]()


def akuma_pose(i):
    return frame1.build()


# ------------------------------------------------------------------ idle

BREATH = [0, 1, 1, 0]


def idle(i):
    if i == 0:
        return frame0.build()           # pixel-exact: the entrance's last frame hands over to this
    cv = ST.body()
    ST.breathe(cv, BREATH[i])
    return ST.aura(cv, 0.0, seed=i)


# ------------------------------------------------------------------ eye flash

FLASH = [
    dict(hdy=1, eye=0, jaw=0, glow=0, lv=0.00, heat=0.0, lance=0, pool=0.0, spokes=False),
    dict(hdy=-1, eye=1, jaw=0, glow=1, lv=0.30, heat=0.2, lance=0, pool=0.0, spokes=False),
    dict(hdy=-2, eye=2, jaw=1, glow=2, lv=0.66, heat=0.6, lance=9, pool=0.35, spokes=False),
    dict(hdy=-3, eye=3, jaw=2, glow=2, lv=1.00, heat=1.0, lance=18, pool=0.85, spokes=True),
]


def eye_flash(i):
    st = FLASH[i]
    cv = ST.body(eye=st['eye'], jaw=st['jaw'], hdy=st['hdy'])
    ST.face_glow(cv, st['glow'], 0, st['hdy'])
    if st['lance']:
        cv.stamp(FC.lances(FC.EYE_CENTRES, st['lance'], st['lv'], dy=st['hdy']), outline=False)
    ST.aura(cv, st['lv'], seed=4 + i, heat=st['heat'])
    if st['pool']:
        ST.pool(cv, st['pool'])
    if st['spokes']:
        ST.spokes(cv, 1.0, 0, st['hdy'])
    return cv


# ------------------------------------------------------------------ hit

def bloom(cv, cx, cy, r, steps=1, only='stuvwW'):
    """light landing on him: his skin within r steps lighter (cloth would jump to a bright blue that
    reads as a glitch, so by default only skin takes it)"""
    for (x, y), k in list(cv.px.items()):
        if k not in only:
            continue
        d = math.hypot(x - cx, y - cy)
        if d < r:
            for _ in range(steps if d < r * 0.5 else 1):
                k = LIGHTER.get(k, k)
            cv.px[(x, y)] = k
    return cv


def hit(i):
    dx = (-3, -1)[i]
    cv = ST.body(eye=(1, 0)[i], hdx=(-1, 0)[i], hdy=(1, 0)[i])
    ST.shunt(cv, dx)
    if i == 0:
        bloom(cv, 66 + dx, 58, 9.0, steps=2)
    ST.aura(cv, 0.0, seed=6 + i)
    if i == 0:
        ST.streaks(cv, [44, 52, 60, 68], side=-1, length=(5, 11), seed=3)
    return cv


# ------------------------------------------------------------------ the rush and the rush pass

RUSH_STREAK = [(8, 15), (12, 22), (15, 27), (10, 20)]
PASS_STREAK = [(13, 25), (9, 18), (6, 13)]
PASS_LV = [1.00, 0.80, 0.58]


def _streak_rows(p):
    hy = p['head'][1]
    return [30 + hy, 38 + hy, 50, 58, 64, 70, 78, 86]


def rush(i):
    p = PZ.RUSH[i]
    cv = RG.draw(p)
    FX.tails(cv, p)
    FX.dash(cv, p, 1.0, seed=i)
    ST.streaks(cv, _streak_rows(p), side=-1, length=RUSH_STREAK[i], keys='yYzU', seed=i)
    return cv


def rush_pass(i):
    p = PZ.PASS[i]
    cv = RG.draw(p)
    FX.tails(cv, p)
    FX.dash(cv, p, PASS_LV[i], seed=10 + i)
    ST.streaks(cv, _streak_rows(p), side=-1, length=PASS_STREAK[i], keys='yYzU', seed=10 + i)
    return cv


# ------------------------------------------------------------------ the punish window

SPENT_LIFT = [0, 1, 1, 0]
SPENT_LV = [0.52, 0.38, 0.42, 0.56]


def _lifted(p, lift):
    """the chest and shoulders rise `lift` px on the in-breath, the head with them"""
    if not lift:
        return p
    q = dict(p)
    cx, cy, cr = p['chest']
    q['chest'] = (cx, cy - lift, cr)
    for key in ('near', 'far'):
        sh, el, wr, fi = p[key]
        q[key] = ((sh[0], sh[1] - lift), el, wr, fi)
    hx, hy = p['head']
    q['head'] = (hx, hy - lift)
    return q


def spent(i):
    p = _lifted(PZ.SPENT, SPENT_LIFT[i])
    cv = RG.draw(p)
    lv = SPENT_LV[i]
    FX.gutter(cv, p, lv, seed=i)
    ST.pool(cv, 0.22 + 0.10 * lv)
    if i in (1, 2):
        hx, hy = p['head']
        FX.sweat(cv, [(35 + hx, 50 + hy + i), (60 + hx, 48 + hy + i)])
    return cv


# ------------------------------------------------------------------ the defeat

DEFEAT_LV = [1.00, 0.72, 0.46, 0.26, 0.12, 0.06]


def defeat(i):
    if i == 0:
        # still on his feet: the aura detonating off him, everything he has left leaving at once
        cv = ST.body(eye=-1, jaw=1, hdy=2)
        bloom(cv, 47.5, 58, 14.0, steps=1)
        ST.aura(cv, 1.0, seed=20, heat=1.0)
        ST.pool(cv, 0.85)
        ST.spokes(cv, 1.0, 0, 18)
        return cv
    p = PZ.DEFEAT[i]
    cv = RG.draw(p)
    lv = DEFEAT_LV[i]
    FX.gutter(cv, p, lv, seed=20 + i)
    ST.pool(cv, 0.14 + 0.30 * lv)
    return cv


# ------------------------------------------------------------------ the ambient aura

def aura(i):
    cv = Canvas()
    cv.px = AO.frame(i)
    return cv


SHEETS = {
    'carter_akuma.png': (akuma, 3),
    'carter_akuma_pose.png': (akuma_pose, 1),
    'carter_idle.png': (idle, 4),
    'carter_eye_flash.png': (eye_flash, 4),
    'carter_rush.png': (rush, 4),
    'carter_rush_pass.png': (rush_pass, 3),
    'carter_spent.png': (spent, 4),
    'carter_hit.png': (hit, 2),
    'carter_defeat.png': (defeat, 6),
    'carter_aura.png': (aura, 6),
}
