"""jordan_ride_brace: 2 frames, looping (0.10). The kaiju rears and leaps: he hunches down over its head,
the near hand dropped back to grip the plate behind him, the box hugged in tight against his far
shoulder, teeth gritted, eyes screwed up, the greasy quiff blown back and whipping in the wind.

  0  hunched, the hair streaming back (WHIP_A), the sneaker clamped back against the skull
  1  jolted a pixel up, the hair's clump flicked the other way (WHIP_B), the sneaker kicking loose

NEW: the whipped hair maps (jr_hair), the gripping hand position (where the nearest plate sits
behind his hip on the approved mount); the plate itself is the kaiju's, not drawn here.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_rider as RR  # noqa: E402
import jr_sheet as S   # noqa: E402
import jr_s_ride_idle as RI  # noqa: E402
import jr_s_ride_throw as RT  # noqa: E402

NAME = 'jordan_ride_brace'
TIMES = [0.10, 0.10]
LOOP = True
KIND = 'ride'
OFFSET = RI.OFFSET
NOTE = 'GRIP is his near fist (where the nearest back plate is on the approved mount). SEAT as jordan_ride_idle.'

# WINCE eyes (screwed shut) over the grit's clenched teeth: the brace face
BRACE_FACE = F.over(F.JH.SHOUT, {
    24: ".kdci icccb bhhhh dhhbb ck.",
    25: "kdbci ickkc ccddd eckkk ck.",
    26: "kdaci jccck kkddd eckcc ck.",
    27: "kdbci jcckk ccddd ebccd ck.",
    31: "...ki jjclj dkWWW WWWkj ik.",
    32: "...kh icjjc jkkkk kkkkc ik.",
    33: "...kh icjjc jippd dppic ik.",
})
F.FACES['brace'] = BRACE_FACE


def wind(fig, dy):
    """Wind streaks rushing past behind him (free-floating effect pixels, no keyline)."""
    out = {}
    for (x0, y0, n, k) in ((20, 22 + dy, 5, 'W'), (18, 30 + dy, 4, 'Q'), (22, 40 + dy, 6, 'W'), (19, 50 + dy, 3, 'Q')):
        for i in range(n):
            out[(x0 + i, y0 - i // 2)] = k
    fig.fxput(out, under=True)


def build(j):
    up = (2, 3 - j)
    hair = 'whip_a' if j == 0 else 'whip_b'
    head = F.head('brace', hair=hair, dx=F.HEAD_AT[0] + up[0] + 1, dy=F.HEAD_AT[1] + up[1] + 1, tilt=4)
    sh = (F.NEAR_ROOT[0] + up[0], F.NEAR_ROOT[1] + up[1])
    fist_at = (31, 64 - j)
    wrist = (fist_at[0] + 3.5, fist_at[1] + 0.5)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, 1)
    near = F.near_arm(sh, el, wrist) + [(F.map_at(F.FIST_HANG, *fist_at), False)]
    bdx, bdy = -2 + up[0], up[1] + 2
    far = RT.far_box_arm(up, bdx, bdy)
    fig = RR.rider(up=up, head=head, far=far, near=near, box=F.open_box(bdx, bdy),
                   far_hand=F.far_hand_box(bdx, bdy), shin=(-2 + j, -1 + j))
    wind(fig, j)
    return fig, {'GRIP': (fist_at[0] + 3, fist_at[1] + 4)}, ['hunched, hair streaming', 'jolted up, hair flicked'][j]


def frames():
    out = []
    for j in range(2):
        fig, extra, note = build(j)
        fr = RI.to_frame(fig, extra, note)
        S.fill_holes(fr.px)
        out.append(fr)
    return out
