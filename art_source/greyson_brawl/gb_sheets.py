"""Greyson's brawl sheets, the PUNCHING half (this folder's): guard, hook_l, hook_r, straight,
rocked. Each frame is a front view in the light crouch, never flipped (his right fist on screen
left, the cannon gauntlet on screen right), built on the approved rig (gb_fig / gb_arms / gb_body).

SHEETS maps a sheet name to its frames [(label, builder, kwargs)]; each builder returns
(canvas, anchors). gb_export.py ships any module shaped like this one, so the other half's sheets
go through the same gate.

Anchors (cell texels; x right, y down; feet (56, 111)):
  crown     the top of his hair on the head's centre line
  chin      the jaw's keyline row + 2, on the head's centre line (the plan's convention: the
            approved standing jaw keyline is row 50, 61 above the soles, so the standing chin by
            this method is row 52, 59 above the soles, the plan's own figure)
  fist      his right fist's centre
  gauntlet  the cannon's striking end: the centre of its muzzle ring
  muzzle    the centre of the bore's face (where a glow sits); None where the bore is out of sight
  contact   on a strike: the texel the punch lands on
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gb_base as B  # noqa: E402
import gb_body as BD  # noqa: E402
import gb_fig as F  # noqa: E402
import gb_arms as A  # noqa: E402

K, G, P = B.K, B.G, B.P
gf_arms, gf_cannon, gr_face = G.gf_arms, G.gf_cannon, G.gr_face
Canvas, moved, mp = K.Canvas, BD.moved, P.mp

D = 4                          # the crouch: hips down 4 rows, head down 7 (the approved guard)
GUARD_GAUNTLET = (70.0, 63.0)


def guard_cannon(cv, d, gauntlet=GUARD_GAUNTLET, face=0.35, sh=6.0, el=-6.0):
    """His left arm held in the approved guard (the carry upper arm, mirrored; the cannon up to
    the cheek). Returns the cannon part."""
    arm = P.Arm(gf_arms.CARRY, gf_arms.CARRY_FORMS, P.I_SHOULDER, F.CARRY_ELBOW, sh=sh, el=el)
    cv.stamp(moved(K.despeckle(P.arm_layer(arm, gf_arms.CARRY_SPEC, 1,
                                           keep=('delt', 'upper', 'biceps'))), 0, d))
    e = mp(arm.upper(F.CARRY_ELBOW))
    cn = gf_cannon.cannon((e[0], e[1] + d), gauntlet, face=face)
    cv.stamp(cn)
    return cn


def frame(d=D, head=(0, 7), face='menace', extras=None, right=None, left=None, order='right_first',
          glow=False, lat=1.0, contact=None):
    """One brawl frame. right / left: None for the approved guard arm, or a dict for a punching
    arm: right = {'elbow', 'fist'} (+ 'fist_map'); left = {'elbow', 'gauntlet', 'face'}.
    order: which arm is stamped last (in front): 'right_first' puts the left (cannon) arm in
    front, 'left_first' the right."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=lat)
    hp, fpx = BD.head(face, head[0], head[1], extras)
    cv.stamp(hp, outline=False)

    def do_right():
        if right is None:
            _, fist = F.guard_arm_right(cv, d, 6.0, -6.0, 'idle')
            return fist, F.fist_centre(fist)
        parts, fc = A.fist_arm(d, right['elbow'], right['fist'], right.get('fist_map', 'idle'))
        for part, ol in parts[:-1]:
            cv.stamp(part, outline=ol)
        return parts[-1][0], fc

    def do_left():
        if left is None:
            cn = guard_cannon(cv, d)
            return cn, GUARD_GAUNTLET
        parts, cn = A.cannon_arm(d, left['elbow'], left['gauntlet'], left.get('face', 0.3))
        if glow:
            A.glow(cn)
        for part, ol in parts:
            cv.stamp(part, outline=ol)
        return cn, left['gauntlet']

    if order == 'right_first':
        fist, fc = do_right()
        cv.stamp(fist, outline=False)
        cn, g = do_left()
    else:
        cn, g = do_left()
        fist, fc = do_right()
        cv.stamp(fist, outline=False)
    P.finish(cv, fpx)
    anc = F.anchors(head[1], head[0], fc, g, cn, contact=contact)
    if glow:
        anc['muzzle'] = F.bore_centre({p: 'z' for p, k in cn.items() if k in ('W', 'o', 'O')
                                       and p in cn})
    return cv, anc


# ------------------------------------------------------------------------------------ the sheets
T = B.TARGET

SHEETS = {
    # the crouch bounce, from the approved f0: the whole body bobs down a row and two and back
    'greyson_brawl_guard': [
        ('rest', F.guard, {}),
        ('down 1', F.guard, dict(d=D + 1, head_dy=8, gauntlet=(70.0, 64.0), fist=(42, 62))),
        ('down 2', F.guard, dict(d=D + 2, head_dy=9, gauntlet=(70.0, 65.0), fist=(42, 63))),
        ('down 1', F.guard, dict(d=D + 1, head_dy=8, gauntlet=(70.0, 64.0), fist=(42, 62))),
    ],
    # the cannon hook, from screen right (his LEFT hand)
    'greyson_brawl_hook_l': [
        ('wind-up', frame, dict(head=(2, 7), left=dict(elbow=(96.0, 79.0), gauntlet=T['hook_l']['windup'], face=0.45))),
        ('strike', F.hook_l_strike, {}),
        ('follow', frame, dict(head=(-4, 7), face='flex', order='left_first',
                               left=dict(elbow=(63.0, 66.0), gauntlet=T['hook_l']['follow'], face=0.3))),
        ('whiff', frame, dict(head=(-6, 8), face='roar', order='left_first',
                              left=dict(elbow=(55.0, 64.0), gauntlet=T['hook_l']['whiff'], face=0.3))),
        ('recover', frame, dict(head=(0, 7), left=dict(elbow=(84.0, 74.0), gauntlet=(64.0, 58.0), face=0.4))),
    ],
    # the right hook, thrown with the fist from screen left (drawn, not mirrored)
    'greyson_brawl_hook_r': [
        ('wind-up', frame, dict(head=(-2, 7), order='left_first', right=dict(elbow=(16.0, 79.0), fist=T['hook_r']['windup']))),
        ('strike', frame, dict(head=(2, 7), face='flex', order='left_first',
                               right=dict(elbow=(28.0, 64.0), fist=T['hook_r']['strike']), contact=T['hook_r']['strike'])),
        ('follow', frame, dict(head=(4, 7), face='flex', order='left_first',
                               right=dict(elbow=(49.0, 66.0), fist=T['hook_r']['follow']))),
        ('whiff', frame, dict(head=(6, 8), face='roar', order='left_first',
                              right=dict(elbow=(57.0, 64.0), fist=T['hook_r']['whiff']))),
        ('recover', frame, dict(head=(0, 7), order='left_first', right=dict(elbow=(28.0, 74.0), fist=(48.0, 58.0)))),
    ],
    # the straight: the gauntlet down the centre line, at the player's parry
    'greyson_brawl_straight': [
        ('wind-up', frame, dict(head=(1, 7), glow=True, left=dict(elbow=(78.0, 75.0), gauntlet=T['straight']['windup'], face=0.9))),
        ('strike', frame, dict(head=(-1, 6), face='flex', left=dict(elbow=(67.0, 65.0), gauntlet=T['straight']['strike'], face=1.0),
                               contact=T['straight']['strike'])),
        ('parried', frame, dict(head=(1, 5), face='wince', left=dict(elbow=(86.0, 62.0), gauntlet=(91.0, 40.0), face=0.4))),
        ('parried 2', frame, dict(head=(2, 4), face='wince', left=dict(elbow=(89.0, 63.0), gauntlet=(97.0, 42.0), face=0.4))),
        ('recover', frame, dict(head=(0, 7), face='annoyed', left=dict(elbow=(84.0, 72.0), gauntlet=(74.0, 56.0), face=0.4))),
    ],
    # the read that dazes him: the head snapped, the guard thrown open, then sagging
    'greyson_brawl_rocked': [
        ('snapped', frame, dict(head=(3, 4), face='wince', order='left_first',
                                right=dict(elbow=(16.0, 70.0), fist=(10.0, 80.0)),
                                left=dict(elbow=(95.0, 70.0), gauntlet=(100.0, 86.0), face=0.5))),
        ('sagging', frame, dict(d=D + 2, head=(1, 10), face='dazed', order='left_first',
                                right=dict(elbow=(20.0, 78.0), fist=(22.0, 93.0)),
                                left=dict(elbow=(92.0, 78.0), gauntlet=(96.0, 98.0), face=0.6))),
    ],
}


def build_sheet(name):
    return [(label, *fn(**kw)) for label, fn, kw in SHEETS[name]]


if __name__ == '__main__':
    for name in SHEETS:
        print(name)
        for label, cv, anc in build_sheet(name):
            st = K.stats(cv.image())
            au = G.audit(cv.px)
            print('   %-10s black %.1f%% colours %2d bbox %s %s %s' % (
                label, 100 * st['black'], st['colours'], K.bbox(cv.px), anc,
                'clean' if not any(au.values()) else {k: len(v) for k, v in au.items() if v}))
