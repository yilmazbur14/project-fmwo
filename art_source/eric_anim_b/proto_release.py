from common import *
import bfx as fx
from proto_windup import f32, f33

rig.layers()


def f34c(ang=-12, cxy=(66, 17), sa=0.9):
    f = Frame128()
    c = -1
    Sh = (30, 82 + c); H = (22, 54 + c)
    E = A.solve_elbow(Sh, H, 18, 17, bend=1)
    Sh2 = (96, 84 + c); H2 = (104, 104 + c)
    E2 = A.solve_elbow(Sh2, H2, 18, 16, bend=-1)
    a = math.radians(ang)
    # sword centred on cxy (centre of the whole sword ~ a = 32)
    S = sword_from_hand(cxy, ang, sa=sa, sb=0.8, grip_a=32)

    def under_paul(f, c, lx):
        A.upper_arm(f.cv, Sh, E); A.upper_arm(f.cv, Sh2, E2)

    def front(f, c, lx):
        # spin smear: ellipse ring around the sword centre, trailing both ends
        fx.crescent(f.cv, cxy[0], cxy[1] + 2, 60, 17, 10, 150, 0.5, 6, rot=ang, dash_tail=0.3)
        fx.crescent(f.cv, cxy[0], cxy[1] + 2, 60, 17, 190, 330, 0.5, 6, rot=ang, dash_tail=0.3)
        S.draw(f.cv)
        A.vambrace(f.cv, E2, H2); A.elbow(f.cv, E2); A.hand(f.cv, 'side', H2)
        A.vambrace(f.cv, E, H); A.elbow(f.cv, E); A.hand(f.cv, 'open_up', H)
    front_body(f, crouch=c, lean=-1, head_dy=-1, paul_L=(0, -2), hooks={'under_paul': under_paul, 'front': front})
    return f.rgba()


def f35():
    f = Frame128()
    c = 3
    Sh = (30, 84 + c); H = (48, 106 + c)
    E = A.solve_elbow(Sh, H, 18, 17, bend=-1)
    Sh2 = (96, 84 + c); H2 = (112, 70 + c)
    E2 = A.solve_elbow(Sh2, H2, 18, 16, bend=1)

    def under_paul(f, c, lx):
        A.upper_arm(f.cv, Sh, E); A.upper_arm(f.cv, Sh2, E2)

    def front(f, c, lx):
        fx.crescent(f.cv, 40, 70, 40, 60, 200, 300, 0.3, 3, dash_tail=0.6)
        A.vambrace(f.cv, E2, H2); A.elbow(f.cv, E2); A.hand(f.cv, 'side', H2)
        A.vambrace(f.cv, E, H); A.elbow(f.cv, E); A.hand(f.cv, 'open_fwd', H)
    front_body(f, crouch=c, lean=2, head_dy=1, hooks={'under_paul': under_paul, 'front': front})
    return f.rgba()


if __name__ == '__main__':
    frames = [f32(), f33(), f34c(), f35()]
    sheet(frames, 3, '../p_release_3x.png')
