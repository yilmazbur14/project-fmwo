"""jordan_ride_taunt: 4 frames, looping (0.13, 0.11, 0.13, 0.11). Taunting from the kaiju's head: his
fight taunt (jordan_taunt) sat astride: the open box hoisted over his head on a stick arm, head thrown
back laughing, the other hand on his hip, the dangling sneaker drumming on the kaiju's skull.

  0  head back, mouth wide on the laugh, the box held high, heel kicked back
  1  the laugh shakes him down a pixel; the box dips with him, the jaw half closes, heel kicked forward
  2  back up, the box pumped a pixel higher, a glint off it, heel back
  3  down again (as 1)

Built from janim_taunt's own parts (the raised far arm and fitted cuff, the tilted laugh heads, the
box held high by v2's far hand) on the rider's seated legs, with the rider's OPEN box in place of the
closed one.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_rider as RR  # noqa: E402
import jr_ride as R    # noqa: E402
import jr_sheet as S   # noqa: E402
import jr_s_ride_idle as RI  # noqa: E402
import janim_taunt as JT  # noqa: E402

NAME = 'jordan_ride_taunt'
TIMES = [0.13, 0.11, 0.13, 0.11]
LOOP = True
KIND = 'ride'
OFFSET = RI.OFFSET
NOTE = 'SEAT as jordan_ride_idle. Also works as the intro\'s seated cheer.'
V, JB = F.V, F.JB


def build(dip, box_dy, head, shin, glint=None):
    fig = F.Fig()
    up = lambda part: C.shift(part, 0, dip)  # noqa: E731
    bdy = dip + box_dy
    fig.stamp(R.far_leg())
    fig.stamp(R.seat())
    for part, ol in JT.far_arm_up(box_dy):
        fig.stamp(up(part), ol)
    fig.stamp(up(V.neck(JT.HEAD_AT[0])))
    fig.stamp(up(V.shirt(0)))
    JB.dandruff(fig.px, 0, dip)
    fig.stamp(JT.laugh_head(head, JT.HEAD_AT[0], JT.HEAD_AT[1] + dip), outline=False, name='head')
    fig.stamp(RR.near_shoe(*shin), outline=False)
    fig.stamp(RR.near_leg_swing(*shin))
    for part, ol in V.near_arm_hip():
        fig.stamp(up(part), ol)
    bx, by = JT.BOX_TOP_LEFT
    box = F.open_box(bx - R.BOX_XY[0], by - R.BOX_XY[1] + bdy)
    fig.stamp(box, outline=False, name='box')
    fig.stamp(F.amap(V.FAR_HAND_BOX, bx - 2, by + 17 + bdy), outline=False)
    if glint:
        fig.fxput(RI.sparkle(glint[0], glint[1] + bdy), under=True)
    return fig


def frames():
    specs = [(0, 0, 'laugh', (-2, 0), None, 'laughing, box high'),
             (1, 0, 'laugh_mid', (2, -1), None, 'shaking down a pixel'),
             (0, -1, 'laugh', (-2, 0), (87, 2), 'box pumped, a glint'),
             (1, 0, 'laugh_mid', (2, -1), None, 'shaking down again')]
    out = []
    for dip, bdy, head, shin, glint, note in specs:
        fig = build(dip, bdy, head, shin, glint)
        fr = RI.to_frame(fig, None, note)
        S.fill_holes(fr.px)
        out.append(fr)
    return out
