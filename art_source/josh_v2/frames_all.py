"""Frame functions for Josh's 13-frame sheet (order fixed by the scene's AnimationLibrary_josh)."""
from jlib import *
import sheet_idle as SI


def f00():
    return SI.build_idle()


def f01():   # exhale: upper body settles 1px, feet locked
    return SI.build_idle(dy_upper=1)


def f02():   # flex pump: forearm + fist squeeze up 1px from the settled pose
    return SI.build_idle(dy_upper=1, pump=-1)


FRAMES = [f00, f01, f02]


# ------------------------------------------------------------------ telegraph (3-4): "most muscular" crab crouch
import sheet_pose as SP

FIST_L = [   # fist seen from the front, knuckles toward the centre
    ".######.",
    "#aassssd#"[:8],
    "#asdsdsf",
    "#sfsfsff",
    ".######.",
]


DUST_L = [
    "..lll...",
    ".lUuUll.",
    "lUuUUUUl",
    "lIiUiiIl",
    ".llIIll.",
]
DUST_R = [r[::-1] for r in DUST_L]


def telegraph(drop=3, effort=False):
    c = blank()
    D = drop
    SP.boots(c, dxn=-3, dxf=3)
    # bent legs, knees pushed out over the wide boots
    SP.limb(c, [(20, 46 + D), (30, 49 + D), (28, 53 + D), (25, 57), (11, 57), (10, 52), (14, 47 + D)], (24, 48 + D), (17, 57), 6.5, 5.0)
    SP.limb(c, [(36, 49 + D), (46, 46 + D), (51, 47 + D), (55, 52), (55, 57), (41, 57), (38, 53 + D)], (42, 48 + D), (49, 57), 6.5, 5.0)
    SP.torso(c, dy=D)
    SP.speedo(c, dy=D)
    # arms curl down and in: fists clenched together in front of the abs ("most muscular")
    SP.limb_bulge(c, [(10, 29 + D), (18, 30 + D), (19, 36 + D), (16, 42 + D), (11, 45 + D), (7, 42 + D), (7, 35 + D)],
                  (14, 32 + D), (11, 42 + D), 5.5, 4.2, (14, 32 + D, 5.5, 5.5, 6))
    SP.limb(c, [(8, 40 + D), (13, 38 + D), (20, 38 + D), (27, 37 + D), (28, 42 + D), (20, 44 + D), (13, 45 + D), (8, 44 + D)],
            (11, 42 + D), (26, 40 + D), 3.8, 3.2)
    SP.limb_bulge(c, [(46, 29 + D), (53, 29 + D), (57, 35 + D), (57, 42 + D), (53, 45 + D), (49, 42 + D), (47, 36 + D)],
                  (51, 32 + D), (54, 42 + D), 5.0, 4.0, (50, 31 + D, 5, 5.5, 5.5))
    SP.limb(c, [(52, 38 + D), (57, 40 + D), (55, 44 + D), (47, 44 + D), (38, 43 + D), (37, 38 + D), (45, 38 + D)],
            (54, 41 + D), (39, 40 + D), 3.6, 3.1)
    block(c, 25, 36 + D, FIST_L)
    block(c, 34, 36 + D, [r[::-1] for r in FIST_L])
    SP.head(c, 'CH', 'grit', dy=D + 1)
    c = SP.finish(c)
    if effort:
        # anime strain marks beside the head (2px bold) + dust kicked up at both boots
        for (x, y, rows) in [(13, 5, ["zZ..", ".zZ.", "..zZ"]), (47, 5, ["..Zz", ".Zz.", "Zz.."]),
                             (10, 12, ["zzZ"]), (51, 12, ["Zzz"])]:
            block(c, x, y, rows)
        block(c, 0, 58, DUST_L)
        block(c, 56, 58, DUST_R)
    return c


def f03():
    return telegraph(drop=3)


def f04():
    return telegraph(drop=4, effort=True)


FRAMES += [f03, f04]


# ------------------------------------------------------------------ charge (5-6): approved key pose + airborne shimmer
import charge as CH


def f05():
    return CH.build(0)


def f06():
    return CH.build(1)


FRAMES += [f05, f06]


# ------------------------------------------------------------------ recover (7-9): hands on knees, hunched, panting
import idle as I
SK = I.SKIN

SWEAT = [
    ".#.",
    "#z#",
    "#c#",
    ".#.",
]
HAND_KNEE_L = [   # hand gripping the knee, fingers wrapping round the front
    ".#####.",
    "#aasss#",
    "#asdsd#",
    "#sfsff#",
    ".#####.",
]


def recover(breath=0, mouth='pant', sweat=((12, 14), (50, 20))):
    """breath: +1 = shoulders/head sink (exhale), -1 = heave up (inhale). Feet locked."""
    c = blank()
    b = breath
    SP.boots(c, dxn=-1, dxf=1)
    # knees slightly bent, apart
    SP.limb(c, [(19, 47), (31, 50), (30, 54), (28, 57), (15, 57), (14, 52), (16, 48)], (24, 50), (21, 57), 6.5, 5.5)
    SP.limb(c, [(35, 50), (46, 47), (50, 48), (52, 52), (51, 57), (38, 57), (36, 54)], (41, 50), (45, 57), 6.5, 5.5)
    # torso bent toward the viewer: foreshortened vertically about the waist
    K, PY = 0.78, 47.0
    base = I.G['body']
    poly = [(x, PY - (PY - y) * K + 3 + b) for (x, y) in base]
    SP.torso(c, poly=poly, hfn=lambda px, py: I.torso_h(px, PY - (PY - (py - 3 - b)) / K))
    SP.speedo(c, dy=1)
    # arms: hand-traced, delt -> elbow (bowed out) -> wrist planted on the knee
    def arm(poly, delt, elbow, wrist):
        dx_, dy_ = delt
        I.hf_shade(c, poly_mask(poly), lambda px, py: max(I.hcap(px, py, dx_, dy_, elbow[0], elbow[1], 5.0, 4.2),
                                                          I.hcap(px, py, elbow[0], elbow[1], wrist[0], wrist[1], 4.0, 3.3),
                                                          I.hdome(px, py, dx_, dy_ - 1, 5.5, 5.0, 6.0)), SK, SP.TH_LIMB)
    arm([(8, 35 + b), (10, 32 + b), (14, 30 + b), (18, 31 + b), (20, 35 + b), (19, 39 + b), (17, 43), (20, 47), (23, 50), (17, 52), (13, 48), (9, 44), (8, 39 + b)],
        (14, 35 + b), (12, 43), (19, 50))
    arm([(57, 35 + b), (55, 32 + b), (51, 30 + b), (47, 31 + b), (45, 35 + b), (46, 39 + b), (48, 43), (45, 47), (42, 50), (48, 52), (52, 48), (56, 44), (57, 39 + b)],
        (51, 35 + b), (53, 43), (46, 50))
    block(c, 16, 48, HAND_KNEE_L)
    block(c, 42, 48, [r[::-1] for r in HAND_KNEE_L])
    SP.head(c, 'TIRED', mouth, dy=8 + b)
    c = SP.finish(c)
    for (x, y) in sweat:
        block(c, x, y, SWEAT)
    return c


def f07():
    return recover(breath=0, mouth='pant', sweat=((13, 13), (50, 18)))


def f08():   # exhale: sink, mouth half-closed
    return recover(breath=1, mouth='pant_small', sweat=((13, 15), (51, 21)))


def f09():   # heave in: shoulders up, mouth wide, sweat flicks off
    return recover(breath=-1, mouth='pant', sweat=((11, 10), (52, 24)))


FRAMES += [f07, f08, f09]


# ------------------------------------------------------------------ hit (10): recoil flinch
def _rot_fns(deg, pivot, off=(0, 0)):
    th = math.radians(deg); co, si = math.cos(th), math.sin(th)

    def rp(pts):
        return [((x - pivot[0]) * co - (y - pivot[1]) * si + pivot[0] + off[0],
                 (x - pivot[0]) * si + (y - pivot[1]) * co + pivot[1] + off[1]) for (x, y) in pts]

    def un(px, py):
        dx, dy = px - pivot[0] - off[0], py - pivot[1] - off[1]
        return (dx * co + dy * si + pivot[0], -dx * si + dy * co + pivot[1])
    return rp, un


OPEN_HAND_UP = [   # splayed hand, fingers up
    "#.#.#..",
    "#s#s#.#",
    "#s#s#s#",
    "#ssssd#",
    "#assdd#",
    ".#####.",
]
PAIN_L = [".z..", "zZ..", "..zZ", "...z"]


def f10():
    c = blank()
    # feet planted exactly like the idle
    SP.limb(c, I.G['n_leg'], (25, 48), (23, 57), 6.5, 5.5)
    SP.limb(c, I.G['f_leg'], (41, 48), (44, 57), 6.0, 5.2)
    SP.boots(c)
    rp, un = _rot_fns(-12, (33, 46))
    SP.torso(c, poly=rp(I.G['body']), hfn=lambda px, py: I.torso_h(*un(px, py)))
    SP.speedo(c)
    # far (right) shoulder is up: arm flung up and out, hand splayed
    I.hf_shade(c, poly_mask([(40, 26), (46, 21), (51, 16), (54, 12), (60, 12), (61, 17), (57, 23), (51, 29), (46, 33)]),
               lambda px, py: max(I.hcap(px, py, 46, 27, 57, 15, 6.0, 4.2), I.hdome(px, py, 46, 27, 6, 6, 6.5),
                                  I.hdome(px, py, 50, 21, 4.5, 3.5, 4.5)), SK, SP.TH_LIMB)
    block(c, 54, 7, OPEN_HAND_UP)
    # near (left) shoulder dropped: arm flung down and out
    I.hf_shade(c, poly_mask([(6, 31), (15, 30), (17, 37), (12, 44), (8, 50), (1, 50), (0, 45), (3, 36)]),
               lambda px, py: max(I.hcap(px, py, 12, 35, 4, 47, 6.0, 4.5), I.hdome(px, py, 12, 34, 6, 6, 6.5)), SK, SP.TH_LIMB)
    block(c, 0, 48, [r[::-1] for r in OPEN_HAND_UP[::-1]])
    SP.head(c, 'HURT', 'grit', dx=-5, dy=1)
    c = SP.finish(c)
    block(c, 1, 16, PAIN_L)
    block(c, 49, 34, [r[::-1] for r in PAIN_L])
    block(c, 46, 3, ["z.z", ".z.", "z.z"])
    return c


FRAMES += [f10]


# ------------------------------------------------------------------ defeated (11-12)
import jlib as JL

STAR = [".o.", "oOo", ".o."]
HAND_LIMP = [
    ".####.",
    "#ssssd#"[:6],
    "#asdsd",
    "#dfdff",
    ".####.",
]


def f11():
    """Knees buckle: slumped kneel, eyes rolled back, arms dangling, dizzy stars."""
    legs = blank()
    c = blank()
    D = 7
    SINK = 3
    # kneeling thighs/knees on the floor (boots hidden behind them)
    SP.limb(legs, [(16, 50), (31, 52), (31, 59), (28, 63), (15, 63), (12, 58)], (22, 54), (22, 61), 7.0, 6.2)
    SP.limb(legs, [(33, 52), (48, 50), (52, 58), (49, 63), (36, 63), (33, 59)], (42, 54), (42, 61), 7.0, 6.2)
    rp, un = _rot_fns(8, (33, 46), off=(1, D))
    SP.torso(c, poly=rp(I.G['body']), hfn=lambda px, py: I.torso_h(*un(px, py)))
    SP.speedo(c, dx=2, dy=D)
    # limp arms dangling, knuckles on the floor beside the knees
    I.hf_shade(c, poly_mask([(8, 35), (16, 34), (17, 41), (13, 50), (11, 57), (5, 57), (5, 48), (6, 40)]),
               lambda px, py: max(I.hcap(px, py, 12, 38, 8, 54, 5.5, 4.0), I.hdome(px, py, 12, 38, 5.5, 5.5, 6)), SK, SP.TH_LIMB)
    I.hf_shade(c, poly_mask([(48, 39), (56, 40), (59, 47), (59, 55), (58, 58), (52, 58), (51, 50), (48, 44)]),
               lambda px, py: max(I.hcap(px, py, 52, 42, 55, 55, 5.5, 4.0), I.hdome(px, py, 52, 42, 5.5, 5.5, 6)), SK, SP.TH_LIMB)
    block(c, 4, 56, HAND_LIMP)
    block(c, 52, 57, [r[::-1] for r in HAND_LIMP])
    SP.head(c, 'ROLL', 'ko', dx=2, dy=D + 1)
    up = shift_canvas(c, 0, SINK)
    for y in range(H):   # hands may not sink through the floor row
        for x in range(W):
            pass
    c = legs
    composite(c, up)
    # clip anything pushed below the pre-shift floor (row 62) back out
    for x in range(W):
        c[63][x] = '.'
    c = SP.finish(c)
    for (x, y) in ((15, 9), (29, 5), (45, 8)):
        block(c, x, y, STAR)
    return c


def f12():
    """Out cold: collapsed forward onto the floor, arms propped out, boots splayed, X_X, dizzy stars.
    Front view, matching Carter's final defeated frame."""
    c = blank()
    # splayed knees/thighs flat on the floor
    SP.limb(c, [(14, 53), (30, 54), (31, 59), (28, 63), (14, 63), (11, 58)], (21, 56), (22, 61), 6.0, 5.5)
    SP.limb(c, [(34, 54), (50, 53), (53, 58), (50, 63), (36, 63), (33, 59)], (43, 56), (42, 61), 6.0, 5.5)
    # boots splayed out at the bottom corners, soles out
    for poly in ([(0, 57), (12, 56), (15, 59), (15, 63), (0, 63)], [(49, 56), (61, 57), (63, 59), (63, 63), (48, 63)]):
        I.draw_boot(c, poly, shaft=(poly[0][0], poly[1][0]), toe=(poly[0][0] + 2, 62))
    # torso bent right over toward the viewer (heavily foreshortened, mostly hidden by the head)
    K, PY = 0.55, 47.0
    base = I.G['body']
    poly = [(x, PY - (PY - y) * K + 12) for (x, y) in base]
    SP.torso(c, poly=poly, hfn=lambda px, py: I.torso_h(px, PY - (PY - (py - 12)) / K))
    SP.speedo(c, dy=8)
    # arms propped straight out to the floor
    I.hf_shade(c, poly_mask([(10, 42), (17, 41), (18, 46), (13, 52), (10, 57), (4, 57), (5, 51), (7, 46)]),
               lambda px, py: max(I.hcap(px, py, 14, 44, 7, 55, 5.0, 3.8), I.hdome(px, py, 14, 43, 5.0, 5.0, 5.5)), SK, SP.TH_LIMB)
    I.hf_shade(c, poly_mask([(46, 41), (53, 42), (56, 46), (58, 51), (59, 57), (53, 57), (50, 52), (45, 46)]),
               lambda px, py: max(I.hcap(px, py, 50, 44, 56, 55, 5.0, 3.8), I.hdome(px, py, 50, 43, 5.0, 5.0, 5.5)), SK, SP.TH_LIMB)
    block(c, 3, 55, HAND_LIMP)
    block(c, 53, 55, [r[::-1] for r in HAND_LIMP])
    SP.head(c, 'KO', 'ko', dy=21)
    for x in range(W):   # keep the floor row clear for the 1px drop
        c[63][x] = '.'
    c = SP.finish(c)
    for (x, y) in ((14, 17), (31, 13), (47, 16)):
        block(c, x, y, STAR)
    return c


FRAMES += [f11, f12]
