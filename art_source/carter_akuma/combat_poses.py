"""Carter's combat poses: idle, eye flash, clone pass, punish window, hit,
defeat.

The front-facing sets (idle, eye flash, hit) are the approved standing body
with the head re-rendered at an offset, so frame 0 of the idle is the approved
sheet's frame 0 pixel for pixel and the entrance can cut straight into it.

The grounded sets (spent, defeat) and the clone pass reuse the three-quarter rig
from combat_rush - it is a general joint-driven body, not a rush-only one.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, erode,
                 poly, ell, PALC, BLACK, TH_HARD, TH_HARD2, bayer)
import parts as P
import aura as AU
import render as R
import intro_lib as IL
import combat_lib as CL
import combat_head as CH
import combat_rush as CR

FLOOR = 95


# ================================================================ front body

def front_body(**hk):
    """The approved standing body with a re-rendered head.  Draw order matches
    render.body exactly, including the juzu going on after the head."""
    cv = Canvas()
    R.legs_and_trousers(cv)
    R.torso_and_arms(cv)
    R.anatomy(cv)
    R.costume(cv)
    CH.draw_head(cv, **hk)
    R.beads_on(cv)
    IL.wrap_bands_both(cv, union(P.wraps_wrist(), P.wraps_fist()),
                       (22.0, 64.0), (19.8, 78.2))
    return cv


# ================================================================ idle
# 4 frames, ~180ms each.  He barely moves: the chest lifts one pixel, the aura
# licks, and that is deliberately all of it - anything more and he stops
# reading as someone who is not worried about you.

BREATH = [0, 1, 1, 0]


def idle(i):
    if i == 0:
        # pixel-exact handover from the last frame of the entrance
        cv = Canvas()
        bm = P.body_mask()
        AU.paint(cv, AU.IDLE, AU.IDLE_SPARKS, bm)
        AU.haze(cv, bm, 5, 0, 0)
        R.body(cv)
        return cv
    body = CL.breathe(front_body(), BREATH[i], seam=74)
    bm = body.mask_of()
    cv = Canvas()
    AU.paint(cv, IL.jitter(AU.IDLE, i, 1.1), AU.IDLE_SPARKS, bm)
    AU.haze(cv, bm, 5, 0, i)
    for y in range(H):
        for x in range(W):
            if body.px[y][x] is not None:
                cv.px[y][x] = body.px[y][x]
    return cv


# ================================================================ eye flash
# 4 frames.  The chin dips, the head comes up, the deadpan breaks and the slits
# burn out.  Frame 3 is the one the whole fight hangs on, so it gets everything:
# white sockets, light leaving his face sideways, a warm bounce all over him and
# the floor lit from above.

FLASH = [
    dict(dy=1, expr='deadpan', eye=0, drop=0, bloom=0.00, aura=0.00, lance=0),
    dict(dy=-1, expr='glare', eye=1, drop=0, bloom=0.18, aura=0.30, lance=0),
    dict(dy=-3, expr='glare', eye=2, drop=1, bloom=0.55, aura=0.66, lance=8),
    dict(dy=-4, expr='flash', eye=3, drop=1, bloom=1.00, aura=1.00, lance=20),
]


def eye_flash(i):
    st = FLASH[i]
    body = front_body(dy=st['dy'], expr=st['expr'], eye=st['eye'],
                      drop=st['drop'], bloom=st['bloom'])
    bm = body.mask_of()
    lv = st['aura']
    ex, ey = 47.5, 29.0 + st['dy'] + st['drop']
    if lv > 0.02:
        CL.point_light(body, bm, ex, ey, 0.30 + 0.62 * lv, reach=30.0 + 22.0 * lv)
    if st['lance']:
        CH.eye_lances(body, 0, st['dy'], st['drop'], st['lance'], lv)

    specs = IL.blend_specs(AU.IDLE, AU.FLARE, lv) if lv > 0.01 else AU.IDLE
    specs = IL.jitter(specs, 4 + i, 1.2)
    sparks = AU.IDLE_SPARKS if lv < 0.4 else AU.FLARE_SPARKS
    cv = IL.compose(body, specs, sparks, haze_in=5 + int(7 * lv),
                    haze_out=int(5 * lv), off=i)
    IL.aura_heat(cv, grow(bm, 1), 0.20 + 0.60 * lv)
    if lv > 0.5:
        CL.ground_pool(cv, (lv - 0.5) * 1.5, 47.5, 94, 34.0)
    if i == 3:
        # spokes of light bursting off the peak, kept clear of the silhouette
        for n in range(14):
            a = n * math.pi / 7 + 0.18
            for r in range(16, 44):
                x = int(round(ex + math.cos(a) * r * 1.05))
                y = int(round(ey + math.sin(a) * r * 0.95))
                if not (0 <= x < W and 0 <= y < H):
                    break
                if bm[y][x] or (r + n) % 3:
                    continue
                cv.px[y][x] = PALC['O'] if r < 24 else (
                    PALC['X'] if r < 34 else PALC['y'])
    return cv


# ================================================================ hit
# 2 frames.  He is annoyed, not hurt: the head rocks, the body shunts back a
# couple of pixels and the eyes brighten a step.  The deadpan survives.

def hit(i):
    dx = (-3, -1)[i]
    body = front_body(dx=dx - (1 - i), dy=(1, 0)[i],
                      expr=('glare', 'deadpan')[i], eye=(1, 0)[i])
    body = CL.shift_canvas(body, dx, 0)
    bm = body.mask_of()
    if i == 0:
        # white bloom on the struck side, so the flinch has a cause
        CL.point_light(body, bm, 70.0, 52.0, 0.85, reach=26.0, hot='M')
    cv = IL.compose(body, IL.jitter(AU.IDLE, 6 + i, 1.4), AU.IDLE_SPARKS,
                    haze_in=6, haze_out=int(2 * (1 - i)), off=i)
    if i == 0:
        CL.streaks(cv, bm, [44, 52, 60, 68], back=-1, ln=(5, 11), seed=3)
    return cv


# ================================================================ clone pass
# 3 frames.  He has gone through the player: back turned, the strike still out
# past them, the lunge unwinding.  The trident mark is the payoff - it is the
# last thing they see of each clone.

PASS = [
    dict(head=(10, 1), face=('glare', 2, 0), back=True, beads=False,
         chest=(56.0, 54.0, 12.0), pelvis=(41.0, 70.0, 9.6),
         near=((60.0, 55.0), (73.0, 58.0), (82.0, 60.0), (86.0, 61.0)),
         far=((51.0, 57.0), (41.0, 51.0), (33.0, 47.0), (29.4, 45.0)),
         lead=((45.0, 69.0), (55.0, 80.0), (61.0, 91.0), 4.0),
         rear=((37.0, 71.0), (26.0, 71.0), (16.0, 72.0), 178.0),
         tails=(176.0, 27.0), sway=-5.0, streak=(16, 30), k=0),
    dict(head=(7, 3), face=('glare', 1, 0), back=True, beads=False,
         chest=(53.0, 56.0, 12.4), pelvis=(41.0, 71.0, 9.8),
         near=((57.0, 57.0), (70.0, 61.0), (79.0, 65.0), (83.0, 67.0)),
         far=((49.0, 58.0), (40.0, 55.0), (33.0, 54.0), (29.4, 53.6)),
         lead=((45.0, 70.0), (54.0, 81.0), (59.0, 91.0), 2.0),
         rear=((37.0, 72.0), (28.0, 78.0), (20.0, 84.0), 158.0),
         tails=(172.0, 21.0), sway=-3.0, streak=(11, 22), k=1),
    dict(head=(4, 4), face=('glare', 1, 0), back=True, beads=False,
         chest=(50.0, 57.0, 12.6), pelvis=(42.0, 72.0, 10.0),
         near=((54.0, 58.0), (64.0, 64.0), (70.0, 71.0), (72.6, 74.6)),
         far=((46.0, 59.0), (38.0, 60.0), (32.0, 63.0), (28.6, 65.0)),
         lead=((46.0, 71.0), (54.0, 82.0), (58.0, 91.0), 2.0),
         rear=((38.0, 73.0), (31.0, 81.0), (26.0, 90.0), 140.0),
         tails=(166.0, 15.0), sway=-2.0, streak=(7, 15), k=2),
]


def rush_pass(i):
    p = PASS[i]
    body = CR.draw(p)
    bm = body.mask_of()
    lv = (1.00, 0.80, 0.58)[i]
    cv = CR.CL_compose(body, CR.dash_specs(p, p['k'], lv),
                       CR.dash_sparks(p, p['k']), bm, p['k'])
    rows = [18 + p['head'][1], 30 + p['head'][1], 44, 54, 62, 70, 80, 90]
    CL.streaks(cv, bm, rows, back=-1, ln=p['streak'], seed=p['k'])
    CR._lead_edge(cv, bm, 0.30 + 0.30 * lv)
    return cv


# ================================================================ punish window
# 4 frames, looping.  Down on one knee with a hand on the floor, head hung,
# shoulders heaving, the aura guttering out.  This has to read as VULNERABLE in
# a single glance and it must not be mistakable for the idle - so the whole
# silhouette changes: he loses a third of his height, the head drops below the
# shoulder line and the crown of aura collapses into low, sagging strands.

def _spent_pose(lift, head_dy, eye):
    """One knee planted on the floor, the other leg folded under him, the far
    hand flat on the ground taking his weight and the head hung between his
    shoulders.

    Two things had to be got right here.  The first version only dropped the
    head eight pixels and left the hips where the idle has them - it read as
    standing with short legs.  The second overcorrected: the hips came up to
    row 81 and the torso collapsed to fifteen rows, so a full-size skull sat on
    half a body and he read as a head with limbs.  The torso keeps its length;
    the HEIGHT is lost by folding the legs, which is where it should come from.
    """
    return dict(
        head=(0, 16 + head_dy), face=('strain', eye, -2), beads=True, tails=None,
        shade=1,
        chest=(53.0, 58.0 - lift, 12.6), pelvis=(45.0, 76.0, 9.8),
        near=((56.0, 59.0 - lift), (65.0, 70.0), (69.0, 80.0), (70.0, 85.0)),
        far=((44.0, 60.0 - lift), (36.0, 72.0), (31.0, 85.0), (29.6, 90.6)),
        lead=((53.0, 76.0), (67.0, 82.0), (63.0, 93.0), 2.0),
        rear=((43.0, 77.0), (33.0, 91.0), (21.0, 93.4), 184.0),
        sway=0.0, k=0,
    )


SPENT = [_spent_pose(0, 0, -1), _spent_pose(1, -1, -1),
         _spent_pose(1, -1, -1), _spent_pose(0, 0, -1)]
SPENT_LV = [0.52, 0.38, 0.42, 0.56]


def spent(i):
    p = dict(SPENT[i])
    p['k'] = i
    body = CR.draw(p)
    bm = body.mask_of()
    lv = SPENT_LV[i]
    specs = CL.guttering(i, lv, CL.roots_from(bm))
    cv = IL.compose(body, specs, [], haze_in=5, haze_out=1, off=i)
    IL.soften(cv, grow(bm, 1), near=9, far=24, seed=i)
    IL.aura_heat(cv, grow(bm, 1), 0.18 + 0.20 * lv)
    CL.ground_pool(cv, 0.22 + 0.10 * lv, 44.0, 94, 26.0, hot='z', cool='Z')
    # sweat coming off the hung head, and a couple of embers dying on the floor
    if i in (1, 2):
        CL.sweat(cv, [(36, 46 + i), (58, 44 + i)])
    CL.dust(cv, 40.0, 93, 0.30, 18.0, seed=i)
    return cv


# ================================================================ defeat
# 6 frames ending on a hold.  The aura blows out on frame 0, then he goes down:
# buckle, knees, hands, sit back, still.

DEFEAT = [
    # 0 - still on his feet, the aura detonating off him
    dict(head=(0, 2), face=('strain', -1, 0), beads=True, tails=None,
         chest=(48.0, 52.0, 13.0), pelvis=(46.0, 69.0, 10.4),
         near=((54.0, 52.0), (59.0, 62.0), (61.0, 72.0), (61.6, 76.0)),
         far=((42.0, 52.0), (36.0, 62.0), (33.0, 72.0), (32.4, 76.0)),
         lead=((51.0, 70.0), (56.0, 82.0), (57.0, 91.0), 2.0),
         rear=((41.0, 70.0), (36.0, 82.0), (35.0, 91.0), 178.0),
         sway=0.0, k=0),
    # 1 - the legs go: knees fold, the arms swing out, the head drops
    dict(head=(-1, 6), face=('strain', -1, 0), beads=True, tails=None,
         chest=(49.0, 55.0, 12.9), pelvis=(47.0, 72.0, 10.2),
         near=((55.0, 56.0), (62.0, 66.0), (65.0, 77.0), (65.6, 81.4)),
         far=((43.0, 56.0), (35.0, 66.0), (31.0, 77.0), (30.4, 81.4)),
         lead=((52.0, 73.0), (61.0, 84.0), (58.0, 94.0), 2.0),
         rear=((42.0, 73.0), (32.0, 85.0), (29.0, 94.0), 180.0),
         sway=0.0, k=1),
    # 2 - dropping, the rear knee a whisker off the floor
    dict(head=(-2, 11), face=('strain', -2, 0), beads=True, tails=None,
         chest=(50.0, 57.0, 12.7), pelvis=(48.0, 74.0, 10.0),
         near=((56.0, 58.0), (64.0, 68.0), (68.0, 78.0), (69.0, 82.6)),
         far=((44.0, 58.0), (35.0, 69.0), (30.0, 81.0), (28.6, 86.0)),
         lead=((53.0, 75.0), (67.0, 80.0), (64.0, 94.0), 2.0),
         rear=((43.0, 75.0), (32.0, 88.0), (21.0, 92.0), 182.0),
         sway=0.0, k=2),
    # 3 - the knee lands and the far hand catches him on the floor
    dict(head=(-2, 15), face=('beaten', -2, 0), beads=True, tails=None,
         chest=(51.0, 60.0, 12.5), pelvis=(49.0, 77.0, 9.9),
         near=((57.0, 61.0), (66.0, 71.0), (71.0, 81.0), (72.0, 85.6)),
         far=((45.0, 61.0), (36.0, 73.0), (31.0, 86.0), (29.6, 91.6)),
         lead=((54.0, 77.0), (68.0, 83.0), (65.0, 94.0), 2.0),
         rear=((44.0, 78.0), (33.0, 92.0), (21.0, 94.0), 184.0),
         sway=0.0, k=3),
    # 4 - sitting back onto his heels, the bracing arm going slack
    dict(head=(-1, 20), face=('beaten', -2, 0), beads=True, tails=None,
         chest=(48.0, 64.0, 12.3), pelvis=(47.0, 81.0, 9.7),
         near=((54.0, 65.0), (62.0, 74.0), (66.0, 84.0), (67.0, 89.0)),
         far=((42.0, 65.0), (34.0, 75.0), (29.0, 85.0), (27.6, 90.0)),
         lead=((51.0, 81.0), (64.0, 88.0), (70.0, 93.4), 6.0),
         rear=((43.0, 82.0), (32.0, 92.0), (20.0, 94.0), 184.0),
         sway=0.0, k=4),
    # 5 - the hold
    dict(head=(-1, 21), face=('beaten', -2, 0), beads=True, tails=None,
         chest=(48.0, 65.0, 12.3), pelvis=(47.0, 82.0, 9.7),
         near=((54.0, 66.0), (62.0, 75.0), (66.0, 85.0), (67.0, 90.0)),
         far=((42.0, 66.0), (34.0, 76.0), (29.0, 86.0), (27.6, 91.0)),
         lead=((51.0, 82.0), (64.0, 89.0), (70.0, 93.8), 6.0),
         rear=((43.0, 83.0), (32.0, 92.6), (20.0, 94.4), 184.0),
         sway=0.0, k=5),
]

DEFEAT_LV = [1.00, 0.72, 0.46, 0.26, 0.12, 0.06]


def defeat(i):
    p = DEFEAT[i]
    body = CR.draw(p)
    bm = body.mask_of()
    lv = DEFEAT_LV[i]
    if i == 0:
        # the blow-out: everything he has left leaving him at once
        specs = IL.scale_w(IL.jitter(AU.FLARE, 0, 1.6, grow_w=0.28), 1.25, 1.30)
        cv = IL.compose(body, specs, AU.FLARE_SPARKS, haze_in=12, haze_out=7,
                        off=0)
        IL.aura_heat(cv, grow(bm, 1), 0.95)
        CL.ground_pool(cv, 0.85, 47.0, 94, 40.0)
        CL.point_light(cv, bm, 47.5, 54.0, 0.55, reach=44.0)
        for n in range(16):
            a = n * math.pi / 8 + 0.1
            for r in range(18, 50):
                x = int(round(47.5 + math.cos(a) * r))
                y = int(round(54.0 + math.sin(a) * r * 0.9))
                if not (0 <= x < W and 0 <= y < H):
                    break
                if bm[y][x] or (r + n) % 3:
                    continue
                cv.px[y][x] = PALC['X'] if r < 30 else PALC['y']
    else:
        specs = CL.guttering(i, lv, CL.roots_from(bm, out=0.7 + 0.9 * lv),
                             scale=0.7 + 0.5 * lv)
        cv = IL.compose(body, specs, [], haze_in=4 + int(6 * lv), haze_out=int(3 * lv),
                        off=i)
        IL.soften(cv, grow(bm, 1), near=8, far=24, seed=i)
        IL.aura_heat(cv, grow(bm, 1), 0.45 * lv)
        CL.ground_pool(cv, 0.14 + 0.30 * lv, 44.0, 94, 24.0, hot='z', cool='Z')
        if i in (2, 3):
            CL.dust(cv, 40.0, 93, 0.85, 22.0, seed=i)
    return cv
