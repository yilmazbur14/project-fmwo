"""The beast's poses for the defeat and the transformation, as pose dicts for pose.build().

GROUND = 151 is the floor row under his feet (BixbyBeastArtLayout.ANCHOR). The approved hover pose
hangs its claws down to that row; standing on the floor, the paws plant with their claw stubs on it.
"""
import copy

import pose as PS

GROUND = 151

# Flared by the blow: spread high and wide, the fingers splayed.
WING_FLARE = dict(
    shoulder=(116, 80), elbow=(140, 42), wrist=(162, 8), thumb=(156, 3),
    tips=[(187, 4), (189, 26), (189, 52), (184, 80)],
    tears=[[(183, 9), (186, 13), (180, 15), (183, 19), (178, 21)],
           [(184, 31), (186, 37), (180, 39), (183, 44), (178, 47)],
           [(184, 57), (185, 63), (179, 64), (181, 70), (176, 73)],
           [(177, 85), (172, 83), (168, 90), (160, 88), (154, 96), (146, 94), (138, 103),
            (130, 104)]],
    holes=[[(170, 14), (174, 16), (172, 20), (168, 18)], [(178, 44), (182, 46), (179, 50)]],
    burn=[(178, 21), (178, 47), (176, 73), (168, 90), (154, 96)],
    knuckles=[(175, 6), (176, 17), (176, 30), (173, 44)],
    claw='up')

# Spent: the arm lies out along the floor, the membrane spills over it and pools on the ground.
WING_DRAPE = dict(
    shoulder=(118, 108), elbow=(146, 116), wrist=(172, 124), thumb=(179, 116),
    tips=[(189, 130), (189, 146), (180, 156), (158, 156)],
    tears=[[(186, 135), (188, 139), (184, 141)],
           [(186, 150), (184, 154), (182, 153)],
           [(175, 153), (172, 157), (167, 153), (163, 157)],
           [(151, 153), (145, 156), (139, 152), (132, 154), (125, 148), (121, 142)]],
    holes=[[(170, 136), (174, 138), (171, 142)], [(152, 140), (156, 142), (153, 146)]],
    burn=[(184, 141), (182, 153), (167, 153), (139, 152)],
    knuckles=[(181, 127), (180, 136), (176, 142), (166, 142)],
    claw='down')


# Both stay inside BixbyBeastArtLayout.BODY_DRAWN (x 2..189, y 2..157) with their claws and keylines.
WING_FLARE = PS.wing_moved(WING_FLARE, sx=0.96, sy=0.96)


def planted_front(x=123):
    c = PS.planted_centre(True, GROUND, x)
    return c


def planted_hind(x=153):
    return PS.planted_centre(False, GROUND, x)


def blow():
    """The final blow: eyes screwed shut, jaws wide, the side heads jolted up and out, the wings flared,
    the paws planted. (The middle head can't be thrown back: the approved crest already touches the top
    of BODY_DRAWN, so it recoils in place with its jaw dropped.)"""
    fp = planted_front()
    hp = planted_hind()
    return PS.make(
        wings=WING_FLARE,
        tails_wave=1,
        front=dict(wrist=(124, fp[1] - 6), paw=fp),
        planted_front=True,
        hind=dict(ankle=(152, hp[1] - 5), paw=hp),
        planted_hind=True,
        side=dict(dx=3, dy=-4, mouth='roar', eyes='shut', low_dy=3),
        mid=dict(dy=0, mouth='gape', eyes='shut', low_dy=3, brows=True),
    )


# Slumped: the wings fall half open behind him, the arm sagging, the fingers fanning down to the floor.
WING_SLUMP = dict(
    shoulder=(118, 110), elbow=(142, 90), wrist=(165, 82), thumb=(171, 73),
    tips=[(189, 92), (190, 116), (187, 140), (170, 152)],
    tears=[[(186, 98), (189, 103), (184, 105), (187, 110)],
           [(186, 122), (189, 127), (184, 130), (186, 135)],
           [(182, 144), (181, 150), (177, 147), (174, 153)],
           [(162, 150), (156, 154), (150, 149), (142, 152), (134, 146), (126, 142)]],
    holes=[[(174, 100), (178, 102), (175, 106)], [(160, 128), (164, 130), (161, 134)]],
    burn=[(184, 105), (184, 130), (177, 147), (150, 149)],
    knuckles=[(177, 87), (177, 99), (176, 111), (167, 117)],
    claw='up')

WING_SLUMP = PS.wing_moved(WING_SLUMP, sx=0.95, sy=1.0)

# The tail lies limp along the floor on the left, its white tip flopped over flat.
TAIL_LIMP = [(66, 136), (52, 147), (37, 151), (23, 152)]
TIP_LIMP = [(24, 148), (16, 147), (9, 149), (13, 151), (5, 152), (11, 154), (18, 155), (25, 155)]


def collapse(glow=1):
    """Down and out: the body sunk onto the floor, the wings slumped open behind him, the heads flopped
    on the floor with their jaws slack and their eyes spinning, the front paws out in front."""
    t = 16
    fp = PS.planted_centre(True, GROUND, 138)
    hp = PS.planted_centre(False, GROUND, 166)
    return PS.make(
        wings=WING_SLUMP, wing_glow=glow,
        tails_wave=1,
        tail=(TAIL_LIMP, (0, 0)), tail_tip_pts=TIP_LIMP,
        torso=(0, t),
        front=dict(shoulder=(119, 100 + t), sh_end=(126, 108 + t), arm_top=(125, 106 + t), elbow=(136, 128),
                   fore_top=(135, 130), wrist=(138, fp[1] - 5), paw=fp),
        planted_front=True,
        hind=dict(hip=(138, 112 + t), hock=(160, 134), ankle=(164, hp[1] - 4), paw=hp),
        planted_hind=True,
        neck=((118, 98 + t), (150, 110)),
        side=dict(dx=10, dy=40, mouth='roar', eyes='dizzy', low_dy=2, ears=glow, eye_glow=glow),
        mid=dict(dy=42, mouth='gape', eyes='dizzy', low_dy=4, brows=False, ears=glow, eye_glow=glow),
        paws_front=[(70, None), (121, None)],
    )
