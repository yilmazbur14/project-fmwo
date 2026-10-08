"""Josh's two new sheets for the card-hands, cut to the plan's art contract: 80x80 frames, soles on
row 79, x = 40 the axis, drawn facing RIGHT (the fight mirrors them like every other sheet of his).
Built from his approved rig (art_source/josh_redesign: josh3 / rig / ground_kit / anims_ground,
imported read-only), so his head, hat, torso, fan and gloves are his own pixels.

josh_summon  (4):  0 GATHER   the deck drawn in to his chest in both hands, glowing       0.15
                   1 SWEEP    arms sweeping up and out, a gold arc of cards following      0.15
                   2 FLICK    arms up and out, cards leaving both hands for the two gates   0.10  loop
                   3 FLICK    the next beat of the stream                                   0.10  loop
josh_command (4):  0 DRAW     the far hand drawn back by his hat brim, fingers pinched      0.20
                   1 POINT    the arm thrust out at the player, a snap of gold off it       0.15
                   2 HOLD     pointing, the fingertip glinting                              0.16  loop
                   3 HOLD     the same, a breath and the glint's next beat                  0.16  loop
"""
import jh_lib as H
from jh_lib import gk, rig, JL
import anims_ground as AG

amap = JL.amap

SUMMON_TIMES = [0.15, 0.15, 0.1, 0.1]
COMMAND_TIMES = [0.2, 0.15, 0.16, 0.16]

# the far glove, fingers pinched for the snap (thumb and middle finger), knuckles to the viewer
SNAP_HAND = [
    "..k.k..",
    ".kdkdk.",
    "kTRkRRk",
    "kRRRRVk",
    "kVRRRVk",
    ".kVVVk.",
    "..kkk..",
]
# the far glove pointing right along the arm: index finger out (skin tip), the rest curled
POINT_HAND = [
    ".kkkk.....",
    "kTRRRkkkk.",
    "kRRRRdddck",
    "kRRRRkkkk.",
    "kVRRVk....",
    ".kVVk.....",
    "..kk......",
]
# the far glove cupped over the deck (the gather), fingers curled toward the viewer
CUP_HAND = [
    ".kkkkk.",
    "kTRRRRk",
    "kRRRRVk",
    "kdkdkdk",
    ".k.k.k.",
]
OPEN_UP = AG.OPEN_UP
FAN_GRIP = AG.FAN_GRIP
FAN_KINDS = AG.FAN_KINDS

# Where the cards leave his hands on the flick frames (texels on the 80x80 frame, facing right): the
# fan in his near (screen-left) hand and the open far (screen-right) hand. Filled in by summon().
CARD_ORIGINS = {}


def loose(px, kind, cx, cy, deg):
    for q, k in gk.loose_card(kind, cx, cy, deg).items():
        if q not in px and 1 <= q[0] < 79 and 1 <= q[1] < 80:
            px[q] = k


def summon(i):
    L = []
    if i == 0:
        # GATHER: the deck squared up in both hands at his chest, glowing, eyes shut, drawing it in
        sway = gk.sway_rows({y: (1, -1) for y in range(66, 71)})
        L.append((gk.torso_px(sway), False))
        L.append((gk.head('shut', 0, 1), True))
        L += rig.mvl(rig.hat_layers(), 0, 1)
        L += gk.arm((51, 43), (57, 51), (49.5, 53.5), near=False, lit_up=[(0, -1)], lit_fore=[(0, -1)])
        L += gk.near_arm_std(shoulder=(32, 43), elbow=(28, 52), wrist=(34.5, 53.5))
        px = gk.seal(rig.compose(L).px)
        # the deck: three cards squared up, standing on his hands, and its glow over the coat
        deck = {}
        for (dx, dy, kind) in ((2, -2, 'diamond'), (1, -1, 'heart'), (0, 0, 'spade')):
            card = gk.keyline(gk.small_card(42 + dx, 52 + dy, 0, w=7, h=9, pip=kind))
            deck.update(card)
        glow = {}
        gk.glow_ring(glow, list(deck), inner='O', outer='r', only_empty=False)
        for q, k in glow.items():
            if q not in deck:
                px[q] = k
        px.update(deck)
        # the two gloves holding it from either side
        px.update(amap([".kkk.", "kTRRk", "kRRVk", "kVRVk", ".kkk."], 33, 48))
        px.update(amap([".kkk.", "kRRRk", "kRRVk", "kVVVk", ".kkk."], 46, 48))
        gk.sparkle(px, 36, 40, False)
        gk.sparkle(px, 51, 43, True)
        return px
    if i == 1:
        # SWEEP: the arms on their way up and out, cards peeling off in a gold arc
        L.append((gk.torso_px(gk.sway_rows({y: (-1, 1) for y in range(64, 71)})), False))
        L.append((gk.head('focus', 0, 0), True))
        L += rig.hat_layers()
        L += gk.arm((51, 43), (59, 42), (65, 35), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(OPEN_UP, 62, 28), False))
        L += gk.near_arm_std(shoulder=(32, 43), elbow=(25, 44), wrist=(18.5, 38.5))
        L += gk.clean_fan((15, 37), ['l21', 'l12', 'up', 'r12'], FAN_KINDS[1:])
        L.append((amap(FAN_GRIP, 11, 35), False))
        px = gk.seal(rig.compose(L).px)
        # smears trailing the hands up and out (anime arcs, no keyline), then the first cards away
        sm = {}
        gk.crescent(sm, [(10, 47), (7, 41), (7, 34), (10, 29)], [(12, 46), (9, 41), (9, 35), (11, 30)],
                    keys=('G', 'o', 'O'))
        gk.crescent(sm, [(71, 45), (74, 39), (74, 32), (71, 27)], [(69, 44), (72, 39), (72, 33), (70, 28)],
                    keys=('G', 'o', 'O'))
        gk.put(px, sm, only_empty=True)
        loose(px, 'heart', 8, 22, -35)
        loose(px, 'diamond', 72, 20, 40)
        gk.sparkle(px, 4, 30, False)
        gk.sparkle(px, 77, 36, True)
        return px
    # FLICK (2, 3): arms up and out, cards streaming from both hands to the gates
    j = i - 2
    L.append((gk.torso_px(gk.sway_rows({y: (-1, 1) for y in range(62, 71)}) if j == 0 else
                          gk.sway_rows({y: (-1, 2) for y in range(64, 71)})), False))
    L.append((gk.head('focus', 0, 0), True))
    L += rig.hat_layers()
    wr = (66, 25) if j == 0 else (67, 24)
    L += gk.arm((51, 43), (60, 35), wr, near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
    L.append((amap(OPEN_UP, wr[0] - 3, wr[1] - 8), False))
    nw = (17.5, 29.5) if j == 0 else (17.0, 28.5)
    L += gk.near_arm_std(shoulder=(32, 43), elbow=(24, 38), wrist=nw)
    fan_pivot = (int(nw[0]) - 3, int(nw[1]) - 1)
    L += gk.clean_fan(fan_pivot, ['l90', 'l21', 'l12', 'up', 'r12'], FAN_KINDS)
    L.append((amap(FAN_GRIP, int(nw[0]) - 7, int(nw[1]) - 3), False))
    px = gk.seal(rig.compose(L).px)
    # the card origins: the top of the fan (left) and the open palm's fingertips (right)
    CARD_ORIGINS[i] = {'left': (fan_pivot[0], fan_pivot[1] - 11), 'right': (wr[0], wr[1] - 8)}
    cards = [('heart', 9, 12, -30), ('spade', 21, 8, 15), ('diamond', 7, 24, -60)] if j == 0 else \
            [('club', 8, 9, -45), ('heart', 19, 6, 30), ('spade', 8, 20, -20)]
    cards_r = [('diamond', 71, 13, 35), ('club', 60, 8, -20), ('heart', 73, 25, 70)] if j == 0 else \
              [('spade', 70, 9, 50), ('diamond', 59, 6, -35), ('club', 73, 20, 15)]
    for kind, cx, cy, deg in cards + cards_r:
        loose(px, kind, cx, cy, deg)
    for (sx, sy, big) in ((14, 32, True), (70, 34, False)) if j == 0 else ((12, 31, False), (72, 33, True)):
        gk.sparkle(px, sx, sy, big)
    return px


def command(i):
    if i == 0:
        # DRAW BACK: the far hand drawn up by the brim, fingers pinched for the snap, a sly look
        L = [(gk.torso_px(), False), (gk.head('smirk', 0, 0), True)]
        L += rig.hat_layers()
        L += gk.arm((51, 43), (60, 40), (61, 31), near=False, lit_up=[(0, -1)], lit_fore=[(-1, 0)])
        L.append((amap(SNAP_HAND, 58, 25), False))
        L += AG.near_side()
        px = gk.seal(rig.compose(L).px)
        gk.sparkle(px, 68, 22, False)
        return px
    lean = gk.Lean(1, 12)
    breath = 1 if i == 3 else 0
    torso = lean.torso(gk.torso_px(gk.sway_rows({y: (-1, 0) for y in range(66, 71)})))
    if breath:
        torso = rig.stretch_rows(torso, 49, 1)
    L = [(torso, False)]
    hx = lean.dx(31)
    L.append((gk.head('focus', hx, -breath), True))
    L += gk.hat(hx, -breath)
    L += AG.near_side((21.5 + hx, 47.5 - breath), lean.pt(32, 43 - breath), (26 + hx, 50 - breath),
                      hand_dxy=(hx, 1 - breath))
    L += gk.arm(lean.pt(51, 43 - breath), (60, 43 - breath), (67, 42 - breath), near=False,
                lit_up=[(0, -1)], lit_fore=[(0, -1)])
    L.append((amap(POINT_HAND, 65, 39 - breath), False))
    px = gk.seal(rig.compose(L).px)
    if i == 1:
        gk.burst(px, 77, 41, r=4, only_empty=True)
    elif i == 2:
        gk.sparkle(px, 77, 41, True)
    else:
        gk.sparkle(px, 77, 40, False)
        gk.sparkle(px, 74, 35, False)
    return px


def frame(sheet, i):
    fn = summon if sheet == 'summon' else command
    px = gk.fill_pinholes(fn(i))
    return {q: k for q, k in px.items() if 0 <= q[0] < 80 and 0 <= q[1] < 80}
