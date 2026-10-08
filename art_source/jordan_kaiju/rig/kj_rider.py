"""Jordan riding: his approved idle upper body, seated astride the kaiju's skull.

Built exactly like janim_idle.build(head='admire') (the approved v2 parts: far arm with the box, neck,
tee, dandruff, the near hand on his hip, the far hand on the box), with three changes:
  * the legs: seated astride, the near thigh coming forward and down, the shin and sneaker dangling
    down the side of the skull; the far thigh laid along the skull top, its shin over the far side;
  * the box: the chase-edition box OPEN, its window panel swung out on its hinge and the tray inside
    empty (a kaiju-shaped hollow in it: the figure that grew);
  * the face: 'admire' (the idle's own smug face: eye on the box, far brow cocked, mouth curled),
    or any janim_heads expression.
Everything is in Jordan's BUILD coordinates; the caller moves the finished part onto the kaiju.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402

JB, JH = K.JB, K.JH
V = JB.V2B
HEAD_AT = JB.V2F.HEAD_AT[0]
FAR_HAND_AT = JB.V2F.FAR_HAND_AT
BOX_XY = (63, 27)                 # the rig's box map, top-left, as v2's idle frame places it

# The open box, box-local (u across from BOX_XY[0], v down from BOX_XY[1]); 19 columns so the swung
# window panel fits. The header with its star, the gold sides and the base are the rig's own rows.
OPEN_BOX = [
    # u: 0-4   5-9   10-14 15-18      v
    ".kkkk kkkkk kkkk. ....",      # 0
    "kTRRR RRORR RRVvk ....",      # 1   the header, the rig's own
    "kTRRR ROOOR RRVvk ....",      # 2
    "kTRRO OOYOO ORVvk ....",      # 3
    "kTRRR OOOOO RRVvk ....",      # 4
    "kTRRR OOROO RRVvk ....",      # 5
    "kkkkk kkkkk kkkkk ....",      # 6
    "kYknn nnnnn nnkxk ....",      # 7   the header's shadow inside the open tray
    "kYkBD DDnnD DDkxx k...",      # 8   the panel swung out on its hinge (light plastic)
    "kYkBD Dnnnn DDkxw xk..",      # 9   the tray, empty: a hollow the shape of the figure
    "kYkBD nnnnD DDkxw wk..",      # 10
    "kYkBn nnnnD DDkxw wk..",      # 11
    "kokBD nnnnn DDkxw wk..",      # 12
    "kokBD nnnnD DDkxw wk..",      # 13
    "kokBn nDnnD DDkxw wk..",      # 14
    "kokBn DDnnn DDkxw wk..",      # 15
    "kokBD DDDDD DDkxw xk..",      # 16
    "kokBB BBBBB BDkxx k...",      # 17
    "kkkkk kkkkk kkkkk ....",      # 18
    "kOOoo ooooo oGGgk ....",      # 19  the base, the rig's own
    ".kkkk kkkkk kkkk. ....",      # 20
]


def open_box(dx=0, dy=0):
    rows = K.JB.rows_of(OPEN_BOX)
    assert all(len(r) == 19 for r in rows), [len(r) for r in rows]
    return K.amap(rows, BOX_XY[0] + dx, BOX_XY[1] + dy)


#SEATED LEGS (build coordinates; v2's jeans ramp: S lit edge, s, N base, n shadow)

def _jeans(shape, lit_side=True):
    part = K.fill(shape, 'N')
    K.rim(part, 'S' if lit_side else 's', -1, 0)
    K.rim(part, 'n', 1, 0)
    K.rim(part, 'n', 0, 1, only='N')
    return part


def seat():
    """The seat: v2's hips (x 43..55, rows 64..69) sat down, flattened into the saddle."""
    return _jeans(K.poly([(42.6, 63.5), (55.4, 63.5), (55.6, 69.4), (52.0, 70.4), (45.0, 70.4), (42.6, 69.4)]))


LEG_DX = 11      # the near shin hangs this far right of v2's standing near leg (the knee out in front)


def near_leg():
    """The near leg, seated: the thigh out in front of him (foreshortened, dropping a little toward
    us), a bony knee, the thin shin hanging straight down the skull's side, jeans bunched at the
    ankle."""
    thigh = K.JB.kit.capsule((46.4, 68.6), (53.6, 71.4), 2.6, 2.4)
    knee = K.ellipse(54.4, 72.0, 2.5, 2.3)
    shin = K.JB.kit.capsule((54.2, 73.2), (53.8, 81.0), 1.9, 1.9)
    stack = K.poly([(51.2, 80.0), (56.6, 80.0), (57.0, 83.6), (50.6, 83.6)])
    part = _jeans(thigh | knee | shin | stack)
    for (x, y) in list(part):                            # the top of the thigh, lit
        if part[(x, y)] == 'N' and (x, y - 1) not in part and x < 54:
            part[(x, y)] = 's'
    for q in ((53, 70), (54, 70), (55, 71)):            # the kneecap catches the light
        if q in part:
            part[q] = 'S'
    K.stroke(part, [(51, 81), (53, 82), (56, 81)], 'n', only='NsS')   # the stacks at the ankle
    K.stroke(part, [(52, 83), (55, 83)], 's', only='N')
    return part


def far_leg():
    """The far thigh beside the near one, out along the skull top, its knee up behind the near knee."""
    thigh = K.JB.kit.capsule((52.4, 66.6), (58.6, 68.2), 2.3, 2.2)
    knee = K.ellipse(59.4, 68.4, 2.4, 2.2)
    part = _jeans(thigh | knee, lit_side=False)
    for q in ((57, 66), (58, 66), (59, 66), (60, 66)):
        if q in part:
            part[q] = 's'
    return part


def near_shoe():
    """The approved near sneaker, dangling below the stacks (its top rows under the hem)."""
    rows = K.JB.rows_of(K.JB.jordan.SHOE_NEAR)
    part = K.amap(rows, 37 + LEG_DX, 86 - 4)
    part[(47 + LEG_DX, 85)] = 'k'                         # v2's toe-cap gap closer, moved with it
    return part


def build(head='admire', dx=0, dy=0, far_leg_on=True):
    """Jordan riding, as (canvas px in build coordinates + (dx, dy), fx pixels)."""
    cv = K.Canvas(400, 400)
    sh = lambda part: {(x + dx, y + dy): k for (x, y), k in part.items()}  # noqa: E731
    if far_leg_on:
        cv.stamp(sh(far_leg()))
    cv.stamp(sh(seat()))
    for part, ol in V.far_arm_box():
        cv.stamp(sh(part), outline=ol)
    cv.stamp(sh(V.neck(HEAD_AT[0])))
    cv.stamp(sh(V.shirt(0)))
    JB.dandruff(cv.px, dx, dy)
    cv.stamp(JH.head(head, HEAD_AT[0] + dx, HEAD_AT[1] + dy), outline=False)
    cv.stamp(sh(near_shoe()), outline=False)          # seated, the near leg comes forward over the hem
    cv.stamp(sh(near_leg()))
    for part, ol in V.near_arm_hip():
        cv.stamp(sh(part), outline=ol)
    cv.stamp(sh(open_box()), outline=False)
    cv.stamp(sh(K.amap(V.FAR_HAND_BOX, *FAR_HAND_AT)), outline=False)
    return cv.px


if __name__ == '__main__':
    px = build()
    px = {(x - 20, y): k for (x, y), k in px.items()}
    im = K.render(px, 80, 96)
    print(K.look(im, 'rider_v1_8x.png', 8))
    print(K.stats(im))
