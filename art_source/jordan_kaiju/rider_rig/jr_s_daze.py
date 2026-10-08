"""jordan_dismount_daze: 4 frames, looping (0.15). Knocked off the kaiju, he sits dazed on the mat: the
punch window. Butt on the mat, the near leg flopped out straight in front of him (heel down, toe up),
the far knee up, the near hand propped on the mat behind his hip, the box hugged loosely against his
far side, the quiff knocked flat, swirl eyes, his head lolling round in a slow circle under three
little gold stars that wheel round over it.

  0  head lolled back-left        stars at 12, 4 and 8 o'clock
  1  head rolling forward          stars a third of a turn on, swirls wound the other way
  2  head lolled forward-right     stars on again
  3  head rolling back             (and round)

NEW: the sitting pose (legs rebuilt from joints), the swirl eyes on the daze face (the juggle's KO
swirls in his fight rig's daze face), the wheeling stars.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_mat as M     # noqa: E402
import jr_sheet as S   # noqa: E402

NAME = 'jordan_dismount_daze'
TIMES = [0.15, 0.15, 0.15, 0.15]
LOOP = True
KIND = 'mat'
OFFSET = (-1, 0)            # the rig's own: build x - 1, soles / butt on row 95
NOTE = ('Sitting on the mat: SOLES = where his butt and heel meet the mat (the code sets this on the knock-off '
        'spot). BODY_BOX = the hurtbox (body, not the stars). CROWN = top of his head. STARS = the stars\' centre.')

UP = (0, 24)                 # the upper body sat down onto the mat (the tee's hem from row 69 to 93)
WOBBLE = [(-1, 0, -6), (0, 1, 2), (1, 1, 7), (0, 0, -1)]    # head (dx, dy, tilt) round the loll


def sit_body(fig, ux=0, uy=0, head=None, box=True, near_hand=True, lean=-2):
    """The sitting body (head given): far leg (knee up), far arm resting the box on that knee, the
    seat, the tee leaning back `lean`, the near leg flopped out along the mat, the near arm propped."""
    bx, by = UP[0] + ux + lean, UP[1] + uy
    # far leg: knee up, the sole flat on the mat
    fig.stamp(M.leg((53.0, 89.0), (62.5, 79.5), (67.0, 88.5), lit_side=False, hem=(67.0, 88.2)))
    fig.stamp(M.shoe('far', (67, 89)), outline=False)
    if box:
        fig.stamp_all(M.arm_to('far', bx, by, (63.4, 81.8), bend=-1))
    fig.stamp(M.hips(0, 24))
    M.torso(fig, bx, by, frame=1)
    # near leg: flopped out straight along the mat, heel down, toe up
    fig.stamp(M.leg((47.0, 90.0), (58.5, 90.0), (69.0, 90.8), hem=(68.6, 90.8)))
    fig.stamp(M.shoe('near', (71, 91), quarter=-1), outline=False)
    if near_hand:
        wr = (35.0, 89.5)
        fig.stamp_all(M.arm_to('near', bx, by, wr, bend=1))
        fig.stamp(F.map_at(F.HAND_FLAT, 29, 91), outline=False)
    if head is not None:
        fig.stamp(head, outline=False, name='head')
    if box:
        b = F.open_box(-1, 32)                   # the open box, still empty, resting on the knee
        fig.stamp(b, outline=False, name='box')
        fig.stamp(F.far_hand_box(-1, 32), outline=False)


def build(i):
    hx, hy, tilt = WOBBLE[i]
    fig = F.Fig()
    head = F.head('dizzy' if i % 2 == 0 else 'dizzy_b', hair='flopped', dx=F.HEAD_AT[0] + UP[0] - 2 + hx, dy=F.HEAD_AT[1] + UP[1] + hy,
                  tilt=tilt)
    sit_body(fig, head=head)
    cx, cy = F.HEAD_AT[0] + UP[0] + 48 + hx, F.HEAD_AT[1] + UP[1] + 4 + hy     # over his crown
    for k in range(3):
        a = math.radians(i * 30 + k * 120)
        sx, sy = cx + 10 * math.cos(a), cy + 3.2 * math.sin(a)
        fig.fxput(M.star(int(round(sx)), int(round(sy)), big=(k + i) % 2 == 0))
    return fig, (cx, cy)


def frames():
    out = []
    for i in range(4):
        fig, stars = build(i)
        a = {'SOLES': (49, 95), 'CROWN': S.crown(fig.px, fig.pts['head']), 'STARS': stars}
        fr = S.to_frame(fig, OFFSET, a, on_mat=True, note=['lolled back', 'rolling forward', 'lolled forward', 'rolling back'][i])
        S.fill_holes(fr.px)
        out.append(fr)
    return out
