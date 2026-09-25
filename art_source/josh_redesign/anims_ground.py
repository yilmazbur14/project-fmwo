"""Josh's non-riding-set animation sheets in the approved redesign (josh_cards.png): idle, intro,
throw, recovery, hit and defeat stand on the ground (soles on row 79); lay_card and show_card play
while he rides the glider, so they follow the ride contract (soles on row 75) and are built on
anims_ride's glide pose. Horizontal strips of 80x80 frames, facing right, x = 40 the anchor column.
Idle frame 0 is josh_cards frame 0 exactly.

    python anims_ground.py preview        # previews only, into the scratchpad
    python anims_ground.py ship           # write the sheets into Assets/Characters/Josh
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import josh3                                                       # noqa: E402
import lib                                                         # noqa: E402
import rig                                                         # noqa: E402
import ground_kit as gk                                            # noqa: E402
from lib import amap                                               # noqa: E402


#IDLE: breath, a flutter of the fan, a sway of the coat. Frame 0 is josh_cards frame 0 exactly.

IDLE_BODY = [0, 1, 1, 0]           # rows the chest rises
IDLE_LAG = [0, 0, 1, 1]            # the hat, the fan hand and the fan follow a frame late
IDLE_SPREAD = [None, None, (-1, 1), (-1, 0)]   # the back two cards drag behind the rising hand, then splay
IDLE_SWAY = [
    {},
    {},
    {66: (1, 1), 67: (1, 1), 68: (1, 1), 69: (1, 1), 70: (1, 1)},
    {69: (1, 1), 70: (1, 1)},
]
IDLE_LINING = [None, None, {68: 4, 69: 4, 70: 4}, None]


def idle(i):
    rows = gk.sway_rows(IDLE_SWAY[i], IDLE_LINING[i]) if IDLE_SWAY[i] else None
    torso = gk.torso_px(rows)
    b = IDLE_BODY[i]
    lag = IDLE_LAG[i]
    if b:
        torso = rig.stretch_rows(torso, 49, b)
    L = [(torso, False)]
    L += rig.mvl(gk.far_arm_std(), 0, -b)
    L.append((rig.mv(rig.head_px(), 0, -b), True))
    L += rig.mvl(rig.hat_layers(), 0, -lag)
    L += gk.near_arm_std((32, 43 - b), (27, 50 - b), (21.5, 46.5 - lag))
    fan = gk.fan_spread(*IDLE_SPREAD[i]) if IDLE_SPREAD[i] else rig.fan_px()
    L.append((rig.mv(fan, 0, -lag), False))
    L.append((rig.mv(rig.near_hand_px(), 0, -lag), False))
    return gk.seal(rig.compose(L).px)


#THROW: 0 wind-up (the parry tell, held 0.45 s), 1 release, 2 follow-through, 3 ready.
# A dart-style snap with the far arm: the card, glowing, is cocked back beside his head, then the arm
# whips out flat at the player with a lunge and a step. The card leaves the fingertips at HAND_THROW
# (72, 45) on frame 1.

def near_side(wrist=(21.5, 46.5), shoulder=(32, 43), elbow=(27, 50), fan=None, hand_dxy=(0, 0)):
    """The near arm with the fan: joints, and the fan and hand moved by hand_dxy."""
    L = gk.near_arm_std(shoulder, elbow, wrist)
    f = fan if fan is not None else rig.fan_px()
    L.append((rig.mv(f, *hand_dxy), False))
    L.append((rig.mv(rig.near_hand_px(), *hand_dxy), False))
    return L


OPEN_HAND = [
    # fingers flicked out to the right, palm down, thumb along the top; skin fingertips
    ".kkk.....",
    "kTRRkkkk.",
    "kRRRRdddk",
    "kRRRRcddk",
    "kVRRVkkkk",
    ".kVVk....",
    "..kk.....",
]
LIMP_HAND = [
    # the follow-through: fingers still open, drooping
    ".kkkk...",
    "kTRRRkk.",
    "kRRRRddk",
    "kVRRRcdk",
    ".kVVkkdk",
    "..kk..k.",
]
CARD_HAND = [
    # at the hip, knuckles out, the next card pinched between two fingers
    ".kkkk.",
    "kTRRRk",
    "kRRRRk",
    "kVRRdk",
    ".kVVkk",
    "..kk..",
]


def throw(i):
    lean = [gk.Lean(-1, 10), gk.Lean(1, 6), gk.Lean(1, 8), gk.Lean(0)][i]
    step = [(0, 0), (3, 0), (3, 0), (0, 0)][i]
    sway = [None, gk.sway_rows({y: (-1, 1) for y in range(64, 71)}, {y: 4 for y in range(66, 71)}),
            gk.sway_rows({y: (-1, 1) for y in range(67, 71)}), None][i]
    torso = lean.torso(gk.torso_px(sway, far_boot=step))
    L = [(torso, False)]
    hx = lean.dx(31)
    sh_far = lean.pt(51, 43)
    sh_near = lean.pt(32, 43)
    if i == 0:
        # cocked: far arm up and back, the card tipped back beside his head, glowing
        L.append((gk.head('focus', hx, 0), True))
        L += gk.hat(hx, 0)
        L += gk.arm(sh_far, (58, 45), (60, 37), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        # a card tipped back on a clean 1:2 slope, the way the approved fan's cards are set
        card = gk.keyline(josh3.card_poly([(56, 34), (62, 31), (58, 23), (52, 26)], josh3.MARK_DIAMOND,
                                          face='0', border='9'))
        glow = {}
        gk.glow_ring(glow, card)
        L.append((glow, False))
        L.append((card, False))
        L.append((amap(RAISED_HAND, 57, 32), False))
        L += near_side((21.5 + hx, 49.5), sh_near, (26 + hx, 51), hand_dxy=(hx, 3))
    elif i == 1:
        # release: lunging, the arm snapped out along the card's line, the card leaving the
        # fingertips at HAND_THROW
        L.append((gk.head('focus', hx, 1), True))
        L += gk.hat(hx - 1, 1, tilt=1)
        L += near_side((19.5 + hx, 52.5), sh_near, (26 + hx, 52), hand_dxy=(hx - 2, 6))
        sm = {}
        gk.crescent(sm, [(58, 21), (65, 22), (71, 27), (75, 35), (73, 42)],
                    [(58, 23), (64, 25), (68, 29), (71, 35), (70, 41)])
        L.append((sm, False))
        L += gk.arm(sh_far, (61, 44), (66, 44), near=False, lit_up=[(0, -1)], lit_fore=[(0, -1)])
        L.append((amap(OPEN_HAND, 64, 42), False))
    elif i == 2:
        # follow-through: the arm carries on down past the line, fingers opening, sparks
        L.append((gk.head('smirk', hx, 1), True))
        L += gk.hat(hx, 1)
        L += near_side((20.5 + hx, 51.5), sh_near, (26 + hx, 51), hand_dxy=(hx - 1, 5))
        L += gk.arm(sh_far, (61, 47), (66, 51), near=False, lit_up=[(0, -1)], lit_fore=[(0, -1)])
        L.append((amap(LIMP_HAND, 65, 48), False))
    else:
        # ready: back on his heels, gunslinger-low, the next card pinched at his hip
        L.append((gk.head('smirk', 0, 0), True))
        L += gk.hat(0, 0)
        card = gk.small_card(61, 56, 62, w=6, h=8, pip='diamond')
        L.append((gk.keyline(card), False))
        L += gk.arm((51, 43), (56, 50), (58, 55), near=False)
        L.append((amap(CARD_HAND, 56, 53), False))
        L += near_side()
    px = gk.seal(rig.compose(L).px)
    if i == 2:
        for (sx, sy, big) in ((76, 41, True), (78, 35, False), (72, 37, False)):
            gk.sparkle(px, sx, sy, big)
    return px


RAISED_HAND = [
    # a fist gripping the card's foot, knuckles to the viewer
    ".kkkk.",
    "kdkdkk",
    "kTRRRk",
    "kRRRVk",
    "kVRRVk",
    ".kkkk.",
]


#INTRO: he is standing there as the burst clears: the fan bursts open in his hand (ta-da), snaps
# shut, he tips his hat with a wink, cocks the gold card and flicks it down into the floor, where it
# stays.

GRIP_HAND = [
    # the far hand from the back, fingers wrapped over whatever it holds
    ".kkkk.",
    "kTRRRk",
    "kRRRRk",
    "kdkdkk",
    ".k.k..",
]
BRIM_HAND = [
    # pinching the brim from below: two fingertips over it, thumb under
    ".k.k..",
    "kdkdk.",
    "kRkRkk",
    "kTRRRk",
    "kRRRVk",
    ".kVVk.",
]
POINT_DOWN = [
    # after the flick: fingers splayed down at the floor
    ".kkkk.",
    "kTRRRk",
    "kRRRRk",
    "kRRRVk",
    "kdkdkk",
    "kdkdk.",
    ".k.k..",
]


OPEN_UP = [
    # ta-da: palm out, fingers spread up
    ".k.k.k.",
    "kdkdkdk",
    "kdkdkdk",
    "kRRRRRk",
    "kTRRRVk",
    "kRRRRVk",
    ".kVVVk.",
    "..kkk..",
]
FAN_GRIP = [
    # the near glove closed round the pivot of a big fan, thumb over the front
    ".kkkk.",
    "kTRRdk",
    "kRTRck",
    "kRRRRk",
    "kVRRVk",
    ".kVVk.",
    "..kk..",
]
FAN_KINDS = ['diamond', 'club', 'heart', 'spade', 'diamond', 'heart', 'spade']


def intro(i):
    L = []
    px_after = []
    if i == 0:
        # the fan bursts open in his near hand, the other arm flung up: ta-da
        sway = gk.sway_rows({y: (-1, 1) for y in range(63, 71)})
        L.append((gk.torso_px(sway), False))
        L.append((gk.head('shut'), True))
        L += rig.hat_layers()
        L += gk.arm((51, 43), (59, 38), (63, 31), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(OPEN_UP, 60, 24), False))
        L += gk.near_arm_std(wrist=(19.5, 44.5), elbow=(26, 49))
        L += gk.clean_fan((16, 44), ['l90', 'l21', 'l12', 'up', 'r12'], FAN_KINDS)
        L.append((amap(FAN_GRIP, 12, 42), False))
        px_after = [(6, 20, True), (27, 17, False), (69, 22, True), (2, 44, False)]
    elif i == 1:
        # it snaps shut with a whip of light; the far hand comes down toward the hat
        L.append((gk.torso_px(), False))
        L.append((gk.head('shut'), True))
        L += rig.hat_layers()
        L += gk.arm((51, 43), (59, 40), (61, 32), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(OPEN_UP, 58, 25), False))
        L += gk.near_arm_std(wrist=(20.5, 45.5), elbow=(26, 50))
        sm = {}
        gk.crescent(sm, [(3, 47), (2, 42), (4, 37), (8, 33)], [(4, 47), (3, 42), (5, 38), (8, 34)],
                    keys=('G', 'o', 'O'))
        L.append((sm, False))
        L += gk.clean_fan((17, 44), ['l11', 'l12', 'l12', 'up', 'up'], FAN_KINDS)
        L.append((amap(FAN_GRIP, 13, 42), False))
        px_after = [(9, 21, False), (20, 18, True)]
    elif i == 2:
        # the fan is his own again; the far hand on its way up to the brim
        L.append((gk.torso_px(), False))
        L.append((gk.head('smirk'), True))
        L += rig.hat_layers()
        L += gk.arm((51, 43), (59, 38), (59, 29), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(GRIP_HAND, 56, 25), False))
        L += near_side()
        px_after = [(11, 31, False)]
    elif i == 3:
        # the hat tip: the front brim pinched and tipped down, with the wink
        L.append((gk.torso_px(), False))
        L.append((gk.head('wink'), True))
        L += gk.hat(0, 0, deg=8, pivot=(42, 18))
        L += gk.arm((52, 42), (60, 34), (60, 25), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(BRIM_HAND, 57, 17), False))
        L += near_side()
        px_after = [(68, 16, False)]
    elif i == 4:
        # the gold card, cocked high
        L.append((gk.torso_px(), False))
        L.append((gk.head('focus'), True))
        L += rig.hat_layers()
        L += gk.arm((51, 43), (60, 41), (62.5, 31), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L += gk.gold_card_turned(-12, 3, -9)
        L.append((amap(RAISED_HAND, 59, 25), False))
        L += near_side()
        px_after = [(71, 11, True), (54, 13, False)]
    else:
        # flicked: the card is in the floor, still humming; his hand follows it down
        lean = gk.Lean(1, 10)
        L.append((lean.torso(gk.torso_px(gk.sway_rows({y: (-1, 0) for y in range(66, 71)}))), False))
        hx = lean.dx(31)
        L.append((gk.head('smirk', hx, 0), True))
        L += gk.hat(hx, 0)
        L += near_side((21.5 + hx, 47.5), lean.pt(32, 43), (26 + hx, 50), hand_dxy=(hx - 1, 1))
        sm = {}
        gk.crescent(sm, [(68, 30), (73, 42), (73, 55), (70, 67)], [(65, 32), (69, 43), (69, 55), (68, 66)],
                    keys=('G', 'o', 'O'))
        L.append((sm, False))
        L += gk.arm(lean.pt(51, 43), (59, 49), (64, 55), near=False, lit_up=[(-1, 0)], lit_fore=[(-1, 0)])
        L.append((amap(POINT_DOWN, 62, 54), False))
        for part, o in gk.gold_card_turned(12, 8, 48, ring=True):
            L.append(({q: k for q, k in part.items() if q[1] <= 78}, o))
        px_after = [(76, 64, True)]
    px = gk.seal(rig.compose(L).px)
    for (sx, sy, big) in px_after:
        gk.sparkle(px, sx, sy, big)
    if i == 5:
        # dust kicked up where it went in
        gk.put(px, amap([".00.", "0990", "9889"], 58, 76), only_empty=True)
        gk.put(px, amap([".0.", "090", "989"], 76, 76), only_empty=True)
    return px


# The card he deals from the glider (ride_lay): a little copy of the giant card's back.
CARD_BACK = [
    ".kkkkkkk.",
    "kooooooOk",
    "ko00000ok",
    "ko0RRR0ok",
    "ko0RkR0ok",
    "koRkkkRok",
    "ko0RkR0ok",
    "ko0RRR0ok",
    "ko00000ok",
    "kGoooooGk",
    ".kkkkkkk.",
]


#SQUAT: the body the recovery and the defeat's buckling knees are built on.

def squat(D, lean, spread=None, far_boot_x=None, near_boot_x=None, top=None):
    """A squat D rows deep: the approved upper torso lowered (and leant), over bent legs spread at
    the knee, the duster's panels hanging outside them to the floor."""
    W = 56 + D
    hem = min(74, 69 + D)
    k = spread if spread is not None else D // 2 + 3          # how far each knee swings out
    nk, fk = (37 - k, W + 5), (47 + k, W + 4)
    na, fa = (nk[0] + 1, 75), (fk[0] - 1, 75)
    nbx = near_boot_x if near_boot_x is not None else na[0] - 4
    fbx = far_boot_x if far_boot_x is not None else fa[0] - 4
    left = [(30, W - 3), (nk[0] - 5, hem), (nk[0] + 1, hem), (nk[0] - 1, W + 4), (37, W - 3)]
    right = [(47, W - 3), (54, W - 3), (fk[0] + 7, hem), (fk[0] + 1, hem), (fk[0] + 1, W + 3)]
    Lb = gk.lower_body(W, hem, left, right, knees=(nk, fk), ankles=(na, fa),
                       boots_at=((nbx, 72), (fbx, 72)), boot_cut=(2, 2), lining=2,
                       fold_left=[(nk[0] - 3, W + 3), (nk[0] - 4, hem - 1)],
                       fold_right=[(fk[0] + 4, W + 3), (fk[0] + 5, hem - 1)])
    t = top if top is not None else gk.upper_torso(gk.torso_px(), 58)
    t = rig.mv(t, 0, D)
    t = lean.torso(t) if lean.sign else t
    return Lb + [(t, False)]


#RECOVERY: spent. Hands on his knees, elbows out, head hung, the hat slid down over his brow;
# the chest heaves on a four-frame breath, sweat flies, and he puffs on the out-breath.

KNEE_HAND_NEAR = [
    ".kkkk.",
    "kTRRRk",
    "kRTRRk",
    "kRRRVk",
    "kdkdkk",
    ".k.k..",
]
KNEE_HAND_FAR = [
    ".kkkk.",
    "kRTRRk",
    "kRRRVk",
    "kVRRVk",
    "kkdkdk",
    "..k.k.",
]
SWEAT = [".W.", "WWt", "WtS", ".S."]
SWEAT_SMALL = ["W.", "WS"]
PUFF = [".0000.", "099990", "0999.0", ".00..."]
PUFF_SMALL = [".00.", "0990", ".00."]
FLOOR_CARD = [
    # a card lying on the floor, foreshortened
    ".kkkkkk.",
    "k900R09k",
    "k990009k",
    ".kkkkkk.",
]
RECOVER_DEPTH = [7, 6, 5, 6]


def recovery(i, hat=True, floor=True):
    D = RECOVER_DEPTH[i]
    lean = gk.Lean(1, 7, 56 + D)
    L = squat(D, lean, spread=6)
    hx = lean.dx(31 + D)
    # the head hangs a little lower than the collar, forward of it and tipped over
    tilt = [8, 7, 6, 7][i]
    L.append((rig.mv(gk.head_rot('winded', tilt), hx + 2, D + 3), True))
    if hat:
        L += gk.hat(hx + 3, D + 4, deg=tilt + 9, pivot=(42, 38))
    sn, sf = lean.pt(32, 43 + D), lean.pt(51, 43 + D)
    L += gk.arm(sn, (22, 56 + D // 2), (29, 63), near=True, lit_up=[(-1, 0)], lit_fore=[(-1, 0)])
    L += gk.arm(sf, (62, 55 + D // 2), (56, 62), near=False, lit_up=[(0, -1)], lit_fore=[(1, 0)])
    L.append((amap(KNEE_HAND_NEAR, 26, 61), False))
    L.append((amap(KNEE_HAND_FAR, 52, 60), False))
    if floor:
        L.append((amap(FLOOR_CARD, 13, 76), False))
        L.append((amap(FLOOR_CARD, 19, 75), False))
    px = gk.seal(rig.compose(L).px)
    # sweat thrown off his brow, falling a little each frame
    drops = [((68, 38), (21, 30)), ((70, 40), (19, 32)), ((72, 43), (17, 35)), ((73, 47), (16, 39))][i]
    gk.put(px, amap(SWEAT, *drops[0]), only_empty=True)
    gk.put(px, amap(SWEAT_SMALL, *drops[1]), only_empty=True)
    # a puff of breath on the out-breath
    if i == 0:
        gk.put(px, amap(PUFF, 61, 47), only_empty=True)
    elif i == 1:
        gk.put(px, amap(PUFF_SMALL, 64, 44), only_empty=True)
    return px


#HIT: 0 the blow lands, 1 he reels. Thrown back from the right: head snapped over, hat jumping off,
# the fan spilling, a flash where it connected.

SPLAY_HAND = [
    # fingers flung open
    ".k.k.k.",
    "kdkdkdk",
    "kRRRRRk",
    "kTRRRVk",
    "kRRRRVk",
    ".kVVVk.",
    "..kkk..",
]


def hit(i):
    lean = [gk.Lean(-1, 5), gk.Lean(-1, 7)][i]
    sway = gk.sway_rows({y: (1, 2) for y in range(63, 71)}) if i == 0 else gk.sway_rows({y: (1, 1) for y in range(66, 71)})
    torso = lean.torso(gk.torso_px(sway))
    L = [(torso, False)]
    hx = lean.dx(31)
    tilt = [-14, -7][i]
    L.append((rig.mv(gk.head_rot('wince', tilt), hx - 1, 0), True))
    L += gk.hat(hx - 3, [-5, -2][i], deg=tilt - [10, 4][i], pivot=(42, 38))
    sn, sf = lean.pt(32, 43), lean.pt(51, 43)
    if i == 0:
        L += gk.near_arm_std(sn, (sn[0] - 6, 49), (16.5, 46.5))
        fan = gk.fan_spread(-1, 1)
        L.append((rig.mv(fan, -5, 0), False))
        L.append((rig.mv(rig.near_hand_px(), -5, 0), False))
        L += gk.arm(sf, (59, 49), (66, 47), near=False, lit_up=[(0, -1)], lit_fore=[(0, -1)])
        L.append((amap(SPLAY_HAND, 65, 42), False))
        L.append((gk.loose_card('diamond', 7, 55, -60), False))
        L.append((gk.loose_card('club', 15, 63, 30), False))
    else:
        L += gk.near_arm_std(sn, (sn[0] - 5, 50), (18.5, 46.5))
        L.append((rig.mv(rig.fan_px(), -3, 0), False))
        L.append((rig.mv(rig.near_hand_px(), -3, 0), False))
        L += gk.arm(sf, (58, 50), (61, 54), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(SPLAY_HAND, 59, 52), False))
        L.append((gk.loose_card('diamond', 7, 66, -100), False))
        L.append((gk.loose_card('club', 17, 70, 75), False))
    px = gk.seal(rig.compose(L).px)
    if i == 0:
        gk.burst(px, 58, 32, r=7)
    else:
        for (sx, sy, big) in ((60, 28, False), (66, 36, False)):
            gk.sparkle(px, sx, sy, big)
    return px


#KNEELING: sat back on his heels, the duster pooled round him on the floor, knees to the front,
# the soles of his boots showing behind.

SOLE = [
    # a boot seen from behind, lying on its toe: the sole and heel toward us
    ".kkkk.",
    "kjhhhk",
    "kljhhk",
    "kljhhk",
    "kkkkkk",
]


def kneel(D=10, lean=None, top=None):
    lean = lean or gk.Lean(0)
    W = 56 + D
    hem = 78
    left = [(30, W - 3), (13, hem), (37, hem), (38, W + 4), (37, W - 3)]
    right = [(47, W - 3), (54, W - 3), (67, hem), (52, hem), (50, W + 4)]
    L = []
    L.append((amap(SOLE, 19, 74), False))
    L.append((amap(SOLE, 25, 75), False))
    L += gk.lower_body(W, hem, left, right, knees=((42, 74), (51, 73)), ankles=((30, 76), (40, 76)),
                       boots_at=((90, 90), (90, 90)), lining=3, back=[(38, W + 2), (46, W + 2), (50, hem), (36, hem)],
                       hips=((39, 0), (45, 0)),
                       fold_left=[(29, W + 5), (24, hem - 1)], fold_right=[(57, W + 4), (60, hem - 1)])
    t = top if top is not None else gk.upper_torso(gk.torso_px(), 58)
    t = rig.mv(t, 0, D)
    t = lean.torso(t) if lean.sign else t
    L.append((t, False))
    return L


#DEFEAT: 0 the last blow, the fan exploding and the hat blown off; 1 staggering back, flailing;
# 2 the knees going; 3 down on his knees; 4 the hat comes down on his head; 5 folded, the hat over
# his eyes (held).

LIMP_DOWN = [
    # a glove hanging open, fingers down
    ".kkkk.",
    "kTRRRk",
    "kRRRVk",
    "kVRRVk",
    "kdkdkk",
    ".k.k..",
]


KNEE_REST = [
    # a glove resting on the thigh, fingers draped forward
    ".kkkk..",
    "kTRRRk.",
    "kRRRRdk",
    "kVRRkdk",
    ".kkk.k.",
]
DEFEAT_HAT = [((34, 12), -22), ((31, 10), -8), ((36, 11), 10), ((40, 19), 16)]


def defeat(i):
    px_fx = []
    if i == 0:
        lean = gk.Lean(-1, 4)
        sway = gk.sway_rows({y: (1, 2) for y in range(62, 71)}, {y: 4 for y in range(64, 71)})
        L = [(lean.torso(gk.torso_px(sway)), False)]
        hx = lean.dx(31)
        L.append((rig.mv(gk.head_rot('shock', -16), hx - 1, 1), True))
        sn, sf = lean.pt(32, 43), lean.pt(51, 43)
        L += gk.near_arm_std(sn, (sn[0] - 7, 42), (15.5, 37.5))
        L.append((amap(SPLAY_HAND, 11, 31), False))
        L += gk.arm(sf, (60, 40), (64, 33), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(SPLAY_HAND, 61, 27), False))
        for kind, cx, cy, d in (('heart', 7, 25, -30), ('diamond', 8, 46, -80), ('spade', 19, 63, 160)):
            L.append((gk.loose_card(kind, cx, cy, d), False))
        L += gk.hat_at(*DEFEAT_HAT[0])
        px_fx = [('burst', 56, 30)]
    elif i == 1:
        # staggering back, the knees starting to go
        D = 3
        lean = gk.Lean(-1, 6, 56 + D)
        L = squat(D, lean, spread=3)
        hx = lean.dx(31 + D)
        L.append((rig.mv(gk.head_rot('wince', -8, hatless_top=True), hx - 1, D + 1), True))
        sn, sf = lean.pt(32, 43 + D), lean.pt(51, 43 + D)
        L += gk.near_arm_std(sn, (sn[0] - 7, 44 + D), (17.5, 40.5))
        L.append((amap(SPLAY_HAND, 13, 34), False))
        L += gk.arm(sf, (61, 45), (65, 39), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(SPLAY_HAND, 62, 33), False))
        for kind, cx, cy, d in (('heart', 9, 30, -70), ('spade', 71, 18, 40), ('club', 72, 56, 100)):
            L.append((gk.loose_card(kind, cx, cy, d), False))
        L += gk.hat_at(*DEFEAT_HAT[1])
        px_fx = [('spark', 69, 32), ('spark', 9, 40)]
    elif i == 2:
        # the knees go; he folds forward, out on his feet
        D = 7
        lean = gk.Lean(1, 8, 56 + D)
        L = squat(D, lean, spread=5)
        hx = lean.dx(31 + D)
        L.append((rig.mv(gk.head_rot('ko', 10, hatless_top=True), hx + 1, D + 2), True))
        sn, sf = lean.pt(32, 43 + D), lean.pt(51, 43 + D)
        L += gk.near_arm_std(sn, (26, 57), (25.5, 64.5))
        L.append((amap(LIMP_DOWN, 22, 63), False))
        L += gk.arm(sf, (59, 57), (59, 64), near=False, lit_up=[(-1, 0)], lit_fore=[(-1, 0)])
        L.append((amap(LIMP_DOWN, 56, 63), False))
        for kind, cx, cy, d in (('heart', 7, 42, -110), ('club', 71, 70, 150)):
            L.append((gk.loose_card(kind, cx, cy, d), False))
        L += gk.hat_at(*DEFEAT_HAT[2])
    else:
        D = 12
        lean = gk.Lean(1, [9, 7, 7][i - 3], 56 + D)
        L = kneel(D, lean)
        hx = lean.dx(31 + D)
        tilt = [12, 14, 13][i - 3]
        L.append((rig.mv(gk.head_rot('ko', tilt, hatless_top=(i == 3)), hx + 1, D + 2), True))
        sn, sf = lean.pt(32, 43 + D), lean.pt(51, 43 + D)
        L += gk.near_arm_std(sn, (28, 64), (36.5, 69.5))
        L.append((amap(KNEE_REST, 35, 67), False))
        L += gk.arm(sf, (58, 63), (55, 70), near=False, lit_up=[(-1, 0)], lit_fore=[(-1, 0)])
        L.append((amap(KNEE_REST, 51, 67), False))
        if i == 3:
            L += gk.hat_at(*DEFEAT_HAT[3])
            L.append((gk.loose_card('heart', 70, 60, 160), False))
        else:
            # it lands on his head, crooked, down over his eyes
            L += gk.hat(hx + 2, D + [7, 8][i - 4], deg=tilt + [8, 4][i - 4], pivot=(42, 38))
            L.append((gk.loose_card('heart', 68, 74, 95), False))
    px = gk.seal(rig.compose(L).px)
    for fx in px_fx:
        if fx[0] == 'burst':
            gk.burst(px, fx[1], fx[2], r=8)
        else:
            gk.sparkle(px, fx[1], fx[2], True)
    return px


#ON THE GLIDER: lay_card and show_card play while he rides (JoshCardsLayCards), so they follow the
# ride contract: soles on row 75, the duster's tail within rows 43-66, and anims_ride's glide pose
# as the base, so lay -> glide and show -> glide hand over cleanly.

import math as _math                                               # noqa: E402
import anims_ride as R                                             # noqa: E402

RIDE_HEAD = (7, 3)            # where anims_ride.pose() puts the approved head at bob 0
# josh3.raised_arm's hand: two fingertips pinching the card's foot
PINCH_UP = ['.k.k. .', 'kdkdk .', 'kRkRk k', 'kTRRR k', 'kRRRV k', '.kVVk .']
RIDE_SHEETS = ('josh_lay_card', 'josh_show_card')


def ride_card_raise(bob, card_dy=0, bright=False):
    """The signature gold card held high beside his face, on the rider: arm, hand, card, glow."""
    hx, hy = RIDE_HEAD[0] - 1, RIDE_HEAD[1] + bob
    arm = gk.arm((56, 47 + bob), (63, 49 + bob), (65.5, 42 + bob + card_dy), near=False,
                 lit_up=[(0, -1)], lit_fore=[(-1, 0)], cuff_at=2.2)
    hand = rig.mv(amap(PINCH_UP, 57, 33), hx, hy + card_dy)
    card_px, glow, ring2 = (rig.mv(p, hx, hy + card_dy) for p in josh3.gold_card())
    rings = [ring2, glow]
    if bright:
        g = {q: 'Y' for q in glow}
        r2 = {q: 'O' for q in ring2}
        r3 = {}
        for (x, y) in list(r2):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in r2 and q not in g and q not in card_px:
                    r3[q] = 'r'
        rings = [r3, r2, g]
    return arm, hand, card_px, rings


def ride_show(i):
    bob = [0, 0, 1][i]
    phase = [1, 2, 3][i] * _math.pi / 2
    if i == 0:
        # the plain card whipped up from riding height, turning face-out; eyes shut, smug
        front = ((56, 47), (62, 46), (64.5, 40), None, None)
        cv = R.pose(bob=bob, phase=phase, front=front, face=gk.head('shut'), wind=R.GLIDE_WIND[1])
        turning = josh3.card(65, 36, 10, w=5, h=11, pip=None, face='O', border='o')
        lib.rim(turning, 'Y', -1, 0)
        cv.stamp(gk.keyline(turning), outline=False)
        cv.stamp(amap(RAISED_HAND, 62, 36), outline=False)
        R.under(cv, R.smear([(71, 56), (72, 50), (70, 44), (67, 40)], 1, keys='OoG'))
        gk.sparkle(cv.px, 71, 25, big=True)
        return gk.seal(cv.px)
    arm, hand, card_px, rings = ride_card_raise(bob, card_dy=[0, 0, -1][i], bright=(i == 2))
    extras = [(p, True) for p, _ in arm] + [(hand, False)]
    cv = R.pose(bob=bob, phase=phase, front=None, face=gk.head('wink'), extras_front=extras)
    gk.seal(cv.px)
    josh3.rim_light(cv.px, set(card_px), reach=9)
    for ring in rings:
        for q, k in ring.items():
            if q not in cv.px:
                cv.px[q] = k
    cv.stamp(card_px, outline=False)
    pts = [(60, 29, False), (75, 30, True), (73, 42, False)] if i == 1 else [(59, 26, False), (76, 27, True), (74, 44, False)]
    for (sx, sy, big) in pts:
        gk.sparkle(cv.px, sx, sy, big)
    return cv.px


def ride_lay(i):
    bob = [0, 1, 0][i]
    phase = [1, 2, 3][i] * _math.pi / 2
    if i == 0:
        # cocked: the card, face down, drawn back over his front shoulder
        front = ((56, 47), (60, 41), (60, 33), None, None)
        cv = R.pose(bob=bob, phase=phase, per=3, torso=(-2, 3), front=front, face=gk.head('focus'),
                    wind=R.GLIDE_WIND[1])
        cv.stamp(rig.mv(amap(CARD_BACK, 56, 20), 2, 0), outline=False)
        cv.stamp(amap(GRIP_HAND, 58, 29), outline=False)
        gk.seal(cv.px)
        gk.sparkle(cv.px, 70, 21, big=True)
        return cv.px
    if i == 1:
        # the deal: the arm whipped down past the front of the card, the card spinning away below
        front = ((56, 48), (63, 54), (68, 58), None, None)
        cv = R.pose(bob=bob, phase=phase, front=front, face=gk.head('focus'),
                    tail=dict(top_tip=45, bot_tip=53), wind=R.GLIDE_WIND[2])
        dealt = gk.rotate(amap(CARD_BACK, 67, 61), 55, (71, 66))
        cv.stamp(dealt, outline=False)
        cv.stamp(amap(R.HAND_SPREAD, 65, 55), outline=False)
        gk.seal(cv.px)
        sm = {}
        gk.crescent(sm, [(66, 20), (73, 27), (76, 38), (76, 50)], [(65, 23), (70, 29), (72, 39), (72, 50)],
                    keys=('G', 'o', 'O', 'Y'))
        R.under(cv, sm)
        return cv.px
    # the follow-through: the hand comes back up toward riding height; sparks trail after the card
    front = ((56, 47), (62, 52), (66, 53), R.HAND_FWD, (65, 50))
    cv = R.pose(bob=bob, phase=phase, front=front, wind=R.GLIDE_WIND[3])
    gk.seal(cv.px)
    for (sx, sy, big) in ((72, 62, True), (68, 69, False), (75, 70, False)):
        gk.sparkle(cv.px, sx, sy, big)
    return cv.px


SHEETS = {
    'josh_idle': (idle, 4, [0.15]),
    'josh_throw': (throw, 4, [0.45, 0.07, 0.11, 0.13]),
    'josh_show_card': (ride_show, 3, [0.13, 0.2, 0.2]),
    'josh_intro': (intro, 6, [0.11, 0.15, 0.11, 0.26, 0.16, 0.42]),
    'josh_lay_card': (ride_lay, 3, [0.14, 0.22, 0.3]),
    'josh_recovery': (recovery, 4, [0.19]),
    'josh_hit': (hit, 2, [0.07, 0.12]),
    'josh_defeat': (defeat, 6, [0.13, 0.11, 0.11, 0.13, 0.18, 1.0]),
}


def frame(name, i):
    """A finished frame: the pose, with any pinhole a re-posed part left in the keylines closed."""
    fn = SHEETS[name][0]
    return gk.fill_pinholes(fn(i))


def build(name):
    fn, n, times = SHEETS[name]
    frames = [frame(name, i) for i in range(n)]
    for f in frames:
        bad = [q for q in f if not (0 <= q[0] < 80 and 0 <= q[1] < 80)]
        for q in bad:
            del f[q]
    import sheet_tools as st
    return st.strip(frames), frames


# How each preview GIF plays: the fight's own timings (JoshArtLayout.FINAL_ANIMS). A one-shot holds
# its last frame a moment before the GIF starts over; loops play a few times.
GIF_SEQ = {
    'josh_idle': [(i, 0.15) for i in range(4)] * 3,
    'josh_throw': [(0, 0.45), (1, 0.07), (2, 0.11), (3, 0.13 + 0.4)],
    'josh_show_card': [(0, 0.13)] + [(1, 0.2), (2, 0.2)] * 3,
    'josh_intro': [(0, 0.11), (1, 0.15), (2, 0.11), (3, 0.26), (4, 0.16), (5, 0.42 + 0.4)],
    'josh_lay_card': [(0, 0.14), (1, 0.22), (2, 0.3 + 0.3)],
    'josh_recovery': [(i, 0.19) for i in range(4)] * 3,
    'josh_hit': [(0, 0.07), (1, 0.12 + 0.4)],
    'josh_defeat': [(0, 0.13), (1, 0.11), (2, 0.11), (3, 0.13), (4, 0.18), (5, 1.0 + 0.4)],
}


if __name__ == '__main__':
    import sheet_tools as st
    what = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    names = sys.argv[2:] or list(SHEETS)
    os.makedirs(st.SCRATCH, exist_ok=True)
    built = []
    for name in names:
        fn, n, times = SHEETS[name]
        im, frames = build(name)
        s = st.stats(im)
        lowest = [max(y for (x, y) in f) for f in frames]
        print('%-16s %d frames  opaque %5d  colours %2d  black %.1f%%  lowest rows %s'
              % (name, n, s['opaque'], s['colours'], 100 * s['black'], lowest))
        riding = name in RIDE_SHEETS
        if what == 'ship':
            png, ase, d = st.ship(name, im, n)
            print('   wrote %s and %s; .aseprite re-export vs .png: %s' % (png, ase, d or 'pixel-identical'))
            out_dir = st.SCRATCH
        else:
            out_dir = st.WIP
            st.inspect(frames, os.path.join(st.WIP, 'wip_%s.png' % name), s=6)
            st.plain(frames, os.path.join(st.WIP, 'wip_%s_4x.png' % name), s=4, riding=riding)
        st.gif(im, n, times, os.path.join(out_dir, ('%s.gif' if what == 'ship' else 'wip_%s.gif') % name),
               riding=riding, seq=GIF_SEQ[name])
        built.append((name, im))
    if len(built) > 1:
        path = os.path.join(st.SCRATCH if what == 'ship' else st.WIP,
                            'contact_4x.png' if what == 'ship' else 'wip_contact.png')
        st.contact(built, riding=RIDE_SHEETS, times={k: v[2] for k, v in SHEETS.items()}).save(path)
