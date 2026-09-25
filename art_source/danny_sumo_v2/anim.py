"""Danny's evolved form, every production sheet, from the redesign the user approved on 2026-09-23.

One pose builder, build_frame(spec), draws any frame from the approved parts. With every offset at
zero it reproduces the approved frames exactly (the idle's frame 0 and the slap wind-up), and
check_approved() proves it on every run.

Frame contract, the same as the sheets it replaces: horizontal strips of 176x144 frames, frame 0
leftmost, anchor (88, 144). The soles' keyline sits on row 143 in every sheet: that is the ground
the small form stands on inside the same frame (its 64x64 frame pasted at +56, +80 puts his feet on
row 63 + 80), so the two forms swap in place. The frame lists and timings are the old sheets'
(art_source/danny_sumo/sheets.py), beat for beat.

A spec is a dict over DEFAULT:
  legs     'stand' | 'sit'
  body     (dx, dy)  the upper body (belt and up) moves; the feet stay planted and the legs stretch
  foot_l, foot_r (dx, dy)  a foot's own move, e.g. lifted mid-step
  belly    breath, 0..2 (see torso.swell)
  arms     (left, right) of 'ready' | 'cock' | 'hold' | 'lo' | 'hi' | 'limp' | 'rest'
  eyes     'sleepy' | 'half' | 'awake' | 'wide'
  mouth    'frown' | 'slack' | 'shout' | 'ow'
  bubble   0..4 (2 is the approved one); pop  the burst left when it goes
  head_dy  the head's own nod on top of the body
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

from sumo_lib import Canvas, spoly, sculpt, amap, taper_line, mirror_pts, MIR, SKIN  # noqa: E402
import sumo_lib as L  # noqa: E402
import face as F  # noqa: E402
import gear as G  # noqa: E402
import hands as HN  # noqa: E402
import limbs as LB  # noqa: E402
import torso as T  # noqa: E402
import danny_v2 as D  # noqa: E402
import slap as SL  # noqa: E402
import lib as jl  # noqa: E402

FW, FH = 176, 144
SHADOW = D.SHADOW
SKINSET = set(SKIN)


# ------------------------------------------------------------------ HELPERS
def shift(part, dx, dy):
    if not dx and not dy:
        return part
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def translate(dx, dy):
    if not dx and not dy:
        return T.ident
    return lambda p: (p[0] + dx, p[1] + dy)


def leg_xf(body, foot):
    """A leg between a moved body and a planted (or lifted) foot: every point moves by a blend of
    the two, all body at the hip (row 100) and all foot at the sole (row 143)."""
    (bdx, bdy), (fdx, fdy) = body, foot
    if not (bdx or bdy or fdx or fdy):
        return None

    def f(p):
        w = min(1.0, max(0.0, (143.0 - p[1]) / 43.0))
        return (p[0] + fdx + (bdx - fdx) * w, p[1] + fdy + (bdy - fdy) * w)
    return f


def wrap_band(pts, side):
    """A wrist wrap as drawn in the approved frame: white, the turns on the diagonal, the far edge
    and (on the shaded side of the body) the lower edge in the cool shade."""
    body = spoly(pts, 1)
    part = {p: 'W' for p in body}
    for (x, y) in body:
        u = x if side > 0 else MIR - x
        if (u + y) % 4 == 0:
            part[(x, y)] = 'H'
    jl.rim(part, 'h', 1, 0, depth=1)
    jl.rim(part, 'H' if side > 0 else 'h', 0, 1, depth=1)
    return part


# ------------------------------------------------------------------ FACE PARTS
# Written for the viewer's-left eye; the right is the mirror, one tone down (face.DOWN).
EYE_HALF_L = [
    # x: 0-4   5-9   10-13
    "..333 33333 3...",    # 0 crease
    ".3566 67776 63..",    # 1 the heavy lid
    "k6666 66666 6kk.",    # 2
    "kkkkk kkkkk kkkk",    # 3 lash
    ".kWWW WUUWk kk4.",    # 4 a sliver of eye under the lid, the pupil centred
    "..4kk kkkkk k4..",    # 5 lower lid
    "...44 45554 4...",    # 6 bag
]
EYE_WIDE_L = [
    "..kkk kkkkk k...",    # 0 the lid thrown up
    ".kWWW WWWWW Wk..",    # 1
    "kWWWW WUUWW WWk.",    # 2 a small pupil in a lot of white
    "kWWWW WUUWW WWk.",    # 3
    ".kWWW WWWWW Wk..",    # 4
    "..kkk kkkkk k...",    # 5
    "..333 44444 3...",    # 6
]
for _rows, _n in ((EYE_HALF_L, 'EYE_HALF_L'), (EYE_WIDE_L, 'EYE_WIDE_L')):
    F._check(_rows, _n)


def _mirror_eye(rows):
    return [''.join(F.DOWN.get(c, c) for c in r.replace(' ', '')[::-1]) for r in rows]


# (left map, right map, top row)
EYES = {
    'sleepy': (F.EYE_L, F.EYE_R, 28),
    'half': (EYE_HALF_L, _mirror_eye(EYE_HALF_L), 28),
    'awake': (SL.EYE_AWAKE_L, SL.EYE_AWAKE_R, 27),
    'wide': (EYE_WIDE_L, _mirror_eye(EYE_WIDE_L), 27),
}

MOUTH_SLACK = [
    # x: 78-82 83-87 88-92 93-97
    "..... 33333 333.. .....",    # 0 under the nose
    "..... .kkkk kkkk. .....",    # 1 upper lip
    "..... k1111 1111k .....",    # 2 hanging open
    "..... k11rr rr11k .....",    # 3 the tongue
    "..... .k111 111k. .....",    # 4
    "..... .4kkk kkk4. .....",    # 5 lower lip
    "..... ..444 444.. .....",    # 6
]
MOUTH_OW = [
    # x: 78-82 83-87 88-92 93-97
    "..... 33333 333.. .....",    # 0
    "...kk kkkkk kkkkk kk...",    # 1
    "..kWW kWWWk kWWWk WWk..",    # 2 teeth clenched
    "..khh khhhk khhhk hhk..",    # 3
    "...kk kkkkk kkkkk kk...",    # 4
    "..... 44444 44444 .....",    # 5
]
for _rows, _n in ((MOUTH_SLACK, 'MOUTH_SLACK'), (MOUTH_OW, 'MOUTH_OW')):
    F._check(_rows, _n)
MOUTHS = {'frown': F.MOUTH, 'slack': MOUTH_SLACK, 'shout': SL.MOUTH_SHOUT, 'ow': MOUTH_OW}

# the sleep bubble grows off the same nostril: its left edge stays on the nostril
BUBBLE_R = {1: 3.2, 2: 4.4, 3: 5.6, 4: 7.0}
# where the bubble was, when it goes: droplets thrown off in a ring
POP = [((0, -6), 'W'), ((4, -5), 'W'), ((5, -4), 'H'), ((7, 0), 'W'), ((6, 4), 'H'), ((2, 6), 'W'),
       ((-2, 5), 'H'), ((-5, -3), 'H'), ((1, -8), 'H'), ((9, -2), 'H')]


# ------------------------------------------------------------------ ARM PARTS
# The flurry's strikes. 'hold' is the approved wind-up's forward palm; 'lo' drives it further at
# the viewer; 'hi' strikes at chest height beside the chin. Written for the viewer's right.
S_UPPER_HI = [(137, 58), (145, 57), (152, 59), (157, 63.5), (158.5, 69.5), (156, 75), (150, 78), (143, 77),
              (138, 72), (135, 65)]
S_BICEPS_HI = [(140, 60.5), (147, 60), (152, 63.5), (153, 69), (148, 73.5), (142, 71), (139, 65.5)]
S_FORE_HI = [(151, 65), (155, 69.5), (153.5, 75), (147, 78.5), (139, 79), (132, 76.5), (130, 71.5), (134, 67),
             (142, 64.5)]
S_BRACHIO_HI = [(147, 66.5), (153, 69.5), (151.5, 74.5), (145.5, 76.5), (140.5, 74.5), (142, 69.5)]
S_WRAP_HI = [(127, 65), (134, 64), (136.5, 68.5), (136, 74.5), (130, 77), (126, 72.5)]

STRIKES = {
    'hold': dict(upper=SL.S_UPPER, biceps=SL.S_BICEPS, fore=SL.S_FORE, brachio=SL.S_BRACHIO, wrap=SL.S_WRAP,
                 palm=SL.PALM_AT, scale=SL.PALM_SCALE),
    'lo': dict(upper=SL.S_UPPER, biceps=SL.S_BICEPS, fore=SL.S_FORE, brachio=SL.S_BRACHIO, wrap=SL.S_WRAP,
               palm=(116.5, 81.5), scale=1.45),
    'hi': dict(upper=S_UPPER_HI, biceps=S_BICEPS_HI, fore=S_FORE_HI, brachio=S_BRACHIO_HI, wrap=S_WRAP_HI,
               palm=(125.0, 66.0), scale=1.4),
}


# ------------------------------------------------------------------ STAGES
DEFAULT = dict(legs='stand', body=(0, 0), foot_l=(0, 0), foot_r=(0, 0), belly=0, arms=('ready', 'ready'),
               eyes='sleepy', mouth='frown', bubble=2, pop=False, head_dy=0)


def legs_stand(cv, s):
    xfs = {1: leg_xf(s['body'], s['foot_l']), -1: leg_xf(s['body'], s['foot_r'])}
    for side in (1, -1):
        cv.stamp(LB.calf(side, xfs[side]))
    for side in (1, -1):
        cv.stamp(LB.thigh(side, xfs[side]), shadow=SHADOW)
        LB.leg_lines(cv.px, side, xf=xfs[side])
    for side in (1, -1):
        cv.stamp(LB.foot(side, xfs[side]), shadow=SHADOW)
        LB.toes(cv.px, side, xf=xfs[side])
        if D.ANKLE_WRAPS:
            cv.stamp(LB.ankle_wrap(side, xfs[side]))


def legs_sit(cv, s):
    """The seated legs rest on the canvas whatever the body does: a deeper slump sinks the body
    into the lap, not the thighs through the floor."""
    for side in (1, -1):
        cv.stamp(LB.thigh_sit(side), shadow=SHADOW)
    for side in (1, -1):
        cv.stamp(LB.foot_sit(side), shadow=SHADOW)
        LB.toes_sit(cv.px, side)


def belt(cv, s):
    dx, dy = s['body']
    cv.stamp(shift(D.knit_part(spoly(D.sym(D.BELT)), 40.0, sigma=5), dx, dy), shadow=SHADOW)
    cv.stamp(shift(G.apron(), dx, dy), shadow=SHADOW)
    # the fringe ends on the floor when he sits: strands stop a row above it, keyline on it
    cv.stamp({q: k for q, k in shift(G.fringe(), dx, dy).items() if q[1] <= FH - 2})
    cv.stamp(shift(G.rope(), dx, dy), shadow=SHADOW)


def torso(cv, s):
    xf = translate(*s['body'])
    m, part = T.build(xf=xf, a_pec=0.32, a_belly=0.45, belly=s['belly'])
    cv.stamp(part, shadow=SHADOW, under=1)
    T.lines(cv.px, xf=xf, belly=s['belly'])


def arms_ready(cv, s):
    dx, dy = s['body']
    for side in (1, -1):
        cv.stamp(shift(LB.upper_arm(side), dx, dy), shadow=SHADOW)
        cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=SHADOW, under=1)
        cv.stamp(shift(LB.forearm(side), dx, dy), shadow=SHADOW)
        LB.arm_lines(cv.px, side, dx, dy)
        cv.stamp(shift(HN.wrap(side), dx, dy), shadow=SHADOW)
        cv.stamp(shift(HN.fist(side), dx, dy), outline=False, shadow=SHADOW)


def neck(cv, s):
    dx, dy = s['body']
    cv.stamp(shift(G.gold_chain(), dx, dy))
    cv.stamp(shift(G.collar(), dx, dy), shadow=SHADOW)


def arm_cock(cv, side, s):
    """The approved wind-up's cocked arm (viewer's left), or its mirror."""
    dx, dy = s['body']
    m = (lambda pts: pts) if side > 0 else mirror_pts
    cv.stamp(shift(sculpt(spoly(m(SL.C_UPPER)), [(spoly(m(SL.C_BICEPS)), 2.2, 0.35)], sigma=4.5, exposure=0.05),
                   dx, dy), shadow=SHADOW)
    cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=SHADOW, under=1)
    cv.stamp(shift(sculpt(spoly(m(SL.C_FORE)), [(spoly(m(SL.C_BRACHIO)), 2.0, 0.3)], sigma=4.0, exposure=0.06),
                   dx, dy), shadow=SHADOW)
    cv.stamp(shift(wrap_band(m(SL.C_WRAP), side), dx, dy))
    cx = 15.0 if side > 0 else MIR - 15.0
    for layer, outline in SL.palm(cx, 20.5, 1.05, thumb=-side, fan=1.2, thumb_reach=10.5):
        cv.stamp(shift(layer, dx, dy), outline=outline)


def arm_strike(cv, side, kind, s):
    """A palm driven at the viewer; STRIKES geometry is for the viewer's right and mirrored."""
    g = STRIKES[kind]
    dx, dy = s['body']
    m = (lambda pts: pts) if side < 0 else mirror_pts
    cv.stamp(shift(sculpt(spoly(m(g['upper'])), [(spoly(m(g['biceps'])), 2.2, 0.32)], sigma=4.5, exposure=0.03),
                   dx, dy), shadow=SHADOW)
    cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=SHADOW, under=1)
    cv.stamp(shift(sculpt(spoly(m(g['fore'])), [(spoly(m(g['brachio'])), 2.0, 0.3)], sigma=4.0, exposure=0.04),
                   dx, dy), shadow=SHADOW)
    cv.stamp(shift(wrap_band(m(g['wrap']), side), dx, dy))
    px_, py_ = g['palm']
    cx = px_ if side < 0 else MIR - px_
    for layer, outline in SL.palm(cx, py_, s=g['scale'], thumb=side, exposure=0.03):
        cv.stamp(shift(layer, dx, dy), outline=outline, shadow=SHADOW)


def arm_limp(cv, side, s):
    dx, dy = s['body']
    cv.stamp(shift(LB.upper_arm(side), dx, dy), shadow=SHADOW)
    cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=SHADOW, under=1)
    cv.stamp(shift(LB.limp_forearm(side), dx, dy), shadow=SHADOW)
    LB.limp_lines(cv.px, side, dx, dy)
    m = (lambda pts: pts) if side > 0 else mirror_pts
    cv.stamp(shift(wrap_band(m(LB.LIMP_WRAP), side), dx, dy))
    cv.stamp(shift(LB.limp_hand(side), dx, dy), shadow=SHADOW)
    LB.limp_fingers(cv.px, side, dx, dy)


def arm_rest(cv, side, s):
    """Seated: the palm resting on top of the thigh, the forearm angled in to it."""
    dx, dy = s['body']
    cv.stamp(shift(LB.upper_arm(side), dx, dy), shadow=SHADOW)
    cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=SHADOW, under=1)
    cv.stamp(shift(LB.rest_forearm(side), dx, dy), shadow=SHADOW)
    m = (lambda pts: pts) if side > 0 else mirror_pts
    cv.stamp(shift(wrap_band(m(LB.REST_WRAP), side), dx, dy))
    cv.stamp(shift(LB.rest_hand(side), dx, dy), shadow=SHADOW)
    LB.rest_lines(cv.px, side, dx, dy)


def head(cv, s):
    dx, dy = s['body'][0], s['body'][1] + s['head_dy']
    face = spoly([(x + dx, y + dy) for (x, y) in D.sym(D.FACE)])
    cv.stamp(F.face_base(face, dx, dy), shadow=SHADOW)
    el, er, ey = EYES[s['eyes']]
    for part in (amap(el, 66 + dx, ey + dy), amap(er, 96 + dx, ey + dy), amap(F.NOSE, 81 + dx, 31 + dy),
                 amap(MOUTHS[s['mouth']], 78 + dx, 43 + dy)):
        for q, k in part.items():
            cv.px[q] = k
    crown = spoly([(x + dx, y + dy) for (x, y) in D.sym(D.CROWN)])
    cv.stamp(D.knit_part_at(crown, 27.0, dx, sigma=9), shadow=SHADOW)
    cuff = spoly([(x + dx, y + dy) for (x, y) in D.sym(D.CUFF)], 1)
    cv.stamp(D.knit_part_at(cuff, 27.0, dx, sigma=4))
    if s['bubble']:
        r = BUBBLE_R[s['bubble']]
        cv.stamp(F.bubble(92.6 + r + dx, 41.5 + (r - 4.4) * 0.45 + dy, r=r))
    if s['pop']:
        cx, cy = 97 + dx, 41 + dy
        for (ox, oy), k in POP:
            cv.px[(cx + ox, cy + oy)] = k


def build_frame(spec):
    s = dict(DEFAULT, **spec)
    cv = Canvas()
    (legs_sit if s['legs'] == 'sit' else legs_stand)(cv, s)
    belt(cv, s)
    torso(cv, s)
    al, ar = s['arms']
    if al == 'ready' and ar == 'ready':
        arms_ready(cv, s)
    neck(cv, s)
    for side, a in ((1, al), (-1, ar)):
        if a == 'cock':
            arm_cock(cv, side, s)
        elif a == 'limp':
            arm_limp(cv, side, s)
        elif a == 'rest':
            arm_rest(cv, side, s)
    head(cv, s)
    for side, a in ((1, al), (-1, ar)):
        if a in STRIKES:
            arm_strike(cv, side, a, s)
    L.clean_lone(cv.px)
    return cv


def small_flex_in():
    """Evolve frame 0: small Danny holding the flex (danny_flex.png frame 2, the approved small
    art, read not redrawn), pasted at (+56, +80) in the big frame."""
    flex = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'danny_flex.png')).convert('RGBA')
    out = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
    out.alpha_composite(flex.crop((128, 0, 192, 64)), (56, 80))
    return out


# ------------------------------------------------------------------ THE SHEETS
AWAKE = dict(eyes='awake', mouth='shout', bubble=0)
GUARD = dict(AWAKE, arms=('cock', 'hold'))          # the approved wind-up
COCK = dict(AWAKE, arms=('cock', 'cock'))
SLAP_LH = dict(AWAKE, arms=('hi', 'cock'))
SLAP_RL = dict(AWAKE, arms=('cock', 'lo'))
SLAP_LL = dict(AWAKE, arms=('lo', 'cock'))
SLAP_RH = dict(AWAKE, arms=('cock', 'hi'))
LAND = dict(AWAKE)                                   # the ready stance, roaring
SMALL = 'small'

# name: [(spec, ms)], loop note -- frame lists and timings from art_source/danny_sumo/sheets.py
SHEETS = {
    'danny_sumo_idle': ([
        (dict(), 200),
        (dict(head_dy=1, belly=1), 180),
        (dict(head_dy=2, belly=2, bubble=3), 260),
        (dict(head_dy=1, belly=1), 180),
    ], 'loop 0-3: sleepy; the belly swells, the head nods, the bubble grows'),
    'danny_sumo_wake': ([
        (dict(eyes='half', mouth='slack', bubble=4, head_dy=1), 140),
        (dict(eyes='wide', mouth='slack', bubble=0, pop=True, head_dy=-1, arms=('cock', 'cock')), 90),
        (GUARD, 260),
    ], 'once; frame 2 is identical to danny_sumo_slap frame 0'),
    'danny_sumo_slap': ([
        (GUARD, 120),
        (COCK, 100),
        (SLAP_LH, 60),
        (dict(SLAP_RL, head_dy=1), 60),
        (dict(SLAP_LL, head_dy=1), 60),
        (SLAP_RH, 60),
        (dict(GUARD, head_dy=1), 140),
        (dict(GUARD, belly=1), 200),
    ], 'loop 2-5 for as long as the flurry runs, then 6-7 to recover'),
    'danny_sumo_step': ([
        (dict(body=(0, -1), foot_r=(0, -3)), 140),
        (dict(body=(2, -2), foot_r=(1, -4)), 90),
        (dict(body=(3, 2), belly=2), 110),
        (dict(body=(1, 0)), 160),
    ], 'loop 0-3 while he walks; the body sways over the feet, the right foot lifts and plants'),
    'danny_sumo_hit': ([
        (dict(eyes='wide', mouth='ow', bubble=0, arms=('cock', 'cock'), body=(-1, 2), head_dy=-3), 90),
        (dict(eyes='wide', mouth='ow', bubble=0, arms=('cock', 'cock'), body=(0, 1), head_dy=-1), 140),
    ], 'once, then back to idle: the knees give, the head snaps back'),
    'danny_sumo_defeat': ([
        (dict(eyes='half', mouth='ow', bubble=0, arms=('limp', 'limp'), head_dy=1, body=(2, 0)), 180),
        (dict(eyes='half', mouth='slack', bubble=0, arms=('limp', 'limp'), body=(0, 5), head_dy=2), 160),
        (dict(eyes='sleepy', mouth='slack', bubble=0, arms=('rest', 'rest'), body=(0, 10), head_dy=3,
              legs='sit'), 220),
        (dict(eyes='sleepy', mouth='slack', bubble=3, arms=('rest', 'rest'), body=(0, 11), head_dy=4,
              legs='sit'), 600),
    ], 'once, hold on frame 3: he sits down and goes to sleep, he does not topple'),
    'danny_sumo_evolve': ([
        (SMALL, 0),
        (GUARD, 0),
        (LAND, 0),
    ], 'driven by the transformation; frames 0 and 1 are the flash pair, 2 is the landing'),
}


def frame_image(spec):
    return small_flex_in() if spec == SMALL else build_frame(spec).image()


def build_sheet(name):
    frames = [frame_image(sp) for sp, _ in SHEETS[name][0]]
    sheet = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * FW, 0))
    return sheet


def check_approved():
    """The approved frames must come out of the pose builder unchanged."""
    sys.path.insert(0, os.path.dirname(HERE))
    from imgdiff import pixel_diff
    # the two frames the user approved (the approval-pass sheet, kept here so the check does not
    # depend on anything under Assets)
    ref = Image.open(os.path.join(HERE, 'approved_2026-09-23.png'))
    ref = ref.convert('RGBA')
    out = []
    for spec, box, name in ((dict(), (0, 0, FW, FH), 'idle f0'), (GUARD, (FW, 0, 2 * FW, FH), 'wind-up')):
        d = pixel_diff(build_frame(spec).image(), ref.crop(box))
        out.append((name, d))
    return out


if __name__ == '__main__':
    for name, d in check_approved():
        print('approved %-8s rebuilt: %s' % (name, 'pixel-identical' if d is None else d))
