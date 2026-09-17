from common import *

rig.layers()


def f32():
    f = Frame128()
    c = 1
    H = (22, 80 + c)
    S = sword_from_hand(H, -58, sa=0.92)
    Sh = (30, 84 + c)
    E = (12, 86 + c)

    def under_paul(f, c, lx):
        A.upper_arm(f.cv, Sh, E)

    def under_head(f, c, lx):
        S.draw_blade(f.cv)

    def front(f, c, lx):
        S.draw_grip(f.cv); S.draw_pommel(f.cv); S.draw_guard(f.cv)
        A.vambrace(f.cv, E, H); A.elbow(f.cv, E)
        A.hand(f.cv, 'H', H)
    front_body(f, crouch=c, lean=-1, paul_L=(0, -1), hooks={'under_paul': under_paul, 'under_head': under_head, 'front': front},
               keep_hip_arm=True)
    return f.rgba()


def f33(ang=-7, H=(20, 66), lean=-2):
    f = Frame128()
    c = 2
    H = (H[0], H[1] + c)
    S = sword_from_hand(H, ang, sa=1.0, sb=0.9)
    Sh = (30, 82 + c)
    E = (8, 78 + c)
    H2 = (86, 99 + c)
    E2 = (106, 97 + c)
    Sh2 = (96, 84 + c)

    def under_paul(f, c, lx):
        A.upper_arm(f.cv, Sh, E)
        A.upper_arm(f.cv, Sh2, E2)

    def over_paul(f, c, lx):
        S.draw_blade(f.cv)

    def front(f, c, lx):
        S.draw_grip(f.cv); S.draw_pommel(f.cv); S.draw_guard(f.cv)
        A.vambrace(f.cv, E, H); A.elbow(f.cv, E)
        A.hand(f.cv, 'H', H)
        A.vambrace(f.cv, E2, H2); A.elbow(f.cv, E2)
        A.hand(f.cv, 'side', H2)
    front_body(f, crouch=c, lean=lean, paul_L=(0, -2), hooks={'under_paul': under_paul, 'over_paul': over_paul, 'front': front})
    return f.rgba()


if __name__ == '__main__':
    frames = [approved_px(), f32(), f33()]
    sheet(frames, 3, '../p_windup_3x.png')
    rig.save_zoom(frames[2], '../p_f33_6x.png', 6)
