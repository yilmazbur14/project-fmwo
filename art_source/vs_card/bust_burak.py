"""Burak - VS-card bust. The one deliberate redraw in the set.

Every boss bust crops from that character's own sprite and scales it. Burak
cannot: his figure inside player_4dir_sheet.png is FIFTEEN BY TWENTY-FIVE
pixels. Filling a 116x120 bust from that needs about 5x, and 5x blocks are not
art. So he is drawn - and, by direction, drawn RICHER than his sheet.

His sheet is 7 colours at 13.9% black. That is faithful but he appears on all
eight cards and sets the tone every time, so being the plainest thing on each of
them is not acceptable. This bust extends each of his ramps within its own hue -
five skin steps where the sheet has two, five blues where it has three, three
reds where it has one, and three blacks so the hair is not one flat field - and
gives every shape a keyline with plate(), which is what lifts the black weight
to match the density of the bosses he is standing next to.

Identity is unchanged: red headband and tails, black hair, bare chest, blue
glove. The sheet has no white anywhere, so he still gets no sclera and no
catchlights - his eyes stay dark shapes cut into flat skin.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import *
import bustkit as K

W, H = 116, 120
BK = "#000000"
# --- ramps extended past the sheet, each inside its own hue ---------------
SK_HI, SK_LT, SK, SK_MD, SK_SH, SK_DK = "#F0BE8C", "#E2A874", "#D79864", "#BE8254", "#AC714F", "#7A4A33"
BL_HI, BL_LT, BL, BL_MD, BL_DK = "#6BA8E0", "#3883C9", "#2464BD", "#162FBB", "#0E1C72"
BA_HI, BA, BA_DK = "#D95763", "#AC3232", "#6E1F22"
HR_LT, HR, HR_DK = "#2E2E3A", "#1A1A22", "#000000"
PALETTE = [SK_HI, SK_LT, SK, SK_MD, SK_SH, SK_DK, BL_HI, BL_LT, BL, BL_MD, BL_DK,
           BA_HI, BA, BA_DK, HR_LT, HR, HR_DK]
GROUPS = [[SK_HI, SK_LT, SK, SK_MD, SK_SH, SK_DK], [BL_HI, BL_LT, BL, BL_MD, BL_DK],
          [BA_HI, BA, BA_DK], [HR_LT, HR]]


def build():
    im = canvas(W, H)

    # ---- headband tails, each its own keylined ribbon --------------------
    plate(im, [(44, 20), (28, 11), (12, 4), (8, 12), (24, 18), (40, 25)], BA, hi=BA_HI, sh=BA_DK)
    plate(im, [(44, 25), (30, 29), (16, 36), (18, 44), (32, 36), (46, 31)], BA, hi=BA_HI, sh=BA_DK)

    # Neck first: drawn after the chest its keyline reads as a black notch
    # sitting on his shoulder.
    plate(im, [(52, 44), (74, 44), (76, 66), (50, 66)], SK_MD, hi=SK, sh=SK_DK)
    poly(im, [(62, 46), (74, 46), (75, 64), (64, 64)], SK)

    # ---- chest -----------------------------------------------------------
    plate(im, [(70, 62), (84, 67), (95, 76), (101, 90), (103, 119), (13, 119), (15, 90),
               (21, 76), (32, 67), (46, 62)], SK, hi=SK_LT, sh=SK_SH)
    plate(im, [(46, 62), (32, 67), (21, 76), (15, 90), (13, 119), (34, 119), (33, 92), (40, 76)],
          SK_MD, hi=SK, sh=SK_DK)
    poly(im, [(36, 82), (56, 90), (58, 100), (38, 96)], SK_LT)
    poly(im, [(38, 96), (58, 100), (58, 104), (37, 100)], SK_MD)
    poly(im, [(80, 82), (60, 90), (58, 100), (78, 96)], SK)
    poly(im, [(78, 96), (58, 100), (58, 104), (79, 100)], SK_SH)
    poly(im, [(56, 100), (60, 100), (60, 119), (56, 119)], SK_MD)
    for y in (106, 113):
        poly(im, [(40, y), (52, y + 4), (52, y + 6), (39, y + 2)], SK_MD)
        poly(im, [(76, y), (64, y + 4), (64, y + 6), (77, y + 2)], SK_MD)

    # ---- head ------------------------------------------------------------
    plate(im, [(56, 6), (70, 6), (80, 12), (86, 22), (87, 32), (85, 42), (78, 51), (64, 55),
               (52, 51), (45, 41), (43, 26), (48, 13)], SK, hi=SK_LT, sh=SK_SH)
    poly(im, [(85, 28), (91, 33), (90, 39), (84, 41)], SK_LT)                        # nose
    poly(im, [(56, 6), (48, 13), (43, 26), (45, 41), (52, 51), (62, 55), (58, 40), (56, 20)], SK_MD)
    poly(im, [(60, 52), (76, 50), (78, 56), (58, 58)], SK_SH)                        # jaw shadow

    # ---- black hair, three tones so it is not one flat field -------------
    plate(im, [(54, 2), (68, 1), (80, 6), (87, 16), (88, 24), (84, 16), (74, 10), (60, 9),
               (50, 13), (45, 22), (44, 32), (41, 22), (43, 10)], HR, hi=HR_LT, sh=HR_DK)
    for a, b, c in (((46, 8), (50, 0), (56, 7)), ((58, 5), (63, -3), (69, 4)),
                    ((70, 5), (78, 0), (81, 9)), ((44, 16), (36, 12), (46, 10))):
        plate(im, [a, b, c], HR, hi=HR_LT, sh=HR_DK)
    plate(im, [(44, 30), (42, 42), (48, 50), (52, 44), (49, 34)], HR, hi=HR_LT, sh=HR_DK)

    # ---- headband --------------------------------------------------------
    plate(im, [(43, 18), (52, 12), (64, 10), (76, 13), (85, 19), (86, 27), (76, 20),
               (63, 17), (52, 21), (46, 27)], BA, hi=BA_HI, sh=BA_DK)
    plate(im, [(42, 16), (49, 14), (50, 28), (43, 29)], BA, hi=BA_HI, sh=BA_DK)

    # ---- face: dark shapes only. His sheet holds no white, so no sclera --
    poly(im, [(50, 22), (62, 19), (63, 24), (51, 27)], HR_DK)
    poly(im, [(68, 19), (81, 22), (80, 27), (67, 24)], HR_DK)
    # His 32x32 sprite gives its eyes one or two pixels, so there is nothing to
    # transcribe here. Keep them small and angled: big sockets read as a mask.
    poly(im, [(54, 28), (63, 26), (63, 29), (54, 31)], SK_SH)      # brow shadow
    poly(im, [(69, 27), (78, 28), (78, 31), (69, 30)], SK_SH)
    poly(im, [(56, 32), (62, 31), (63, 35), (57, 36)], HR_DK)      # eyes
    poly(im, [(70, 32), (76, 32), (76, 36), (70, 36)], HR_DK)
    poly(im, [(57, 35), (63, 34), (63, 36), (57, 37)], SK_MD)
    poly(im, [(70, 35), (76, 35), (76, 37), (70, 37)], SK_MD)
    poly(im, [(82, 31), (88, 36), (84, 41), (80, 38)], SK_SH)      # nose
    poly(im, [(81, 40), (86, 39), (86, 42), (81, 43)], SK_DK)
    poly(im, [(68, 45), (81, 43), (81, 47), (68, 49)], SK_DK)      # mouth
    poly(im, [(69, 48), (80, 46), (80, 50), (69, 52)], SK_LT)      # lit lower lip
    poly(im, [(48, 34), (55, 37), (53, 47), (47, 44)], SK_MD)      # far cheek plane

    # ---- blue glove: knuckle plates, thumb, wrist wrap -------------------
    plate(im, [(10, 90), (23, 84), (36, 88), (43, 99), (42, 112), (31, 119), (11, 119), (3, 106)],
          BL, hi=BL_LT, sh=BL_DK)
    poly(im, [(23, 84), (36, 88), (42, 98), (40, 106), (30, 98), (24, 90)], BL_LT)
    poly(im, [(8, 98), (18, 94), (22, 104), (14, 112), (6, 108)], BL)
    poly(im, [(7, 106), (4, 113), (12, 119), (26, 119), (17, 110)], BL_MD)
    plate(im, [(32, 112), (44, 107), (49, 117), (34, 119)], BL_DK, hi=BL_MD, sh=BL_DK)

    K.rim_all(im, GROUPS)
    return K.lock(im, PALETTE)


if __name__ == "__main__":
    im = build(); outline(im)
    sp = sys.argv[1] if len(sys.argv) > 1 else "."
    sheet = K.frame("MainPlayer/player_4dir_sheet.png", (0, 64, 32, 96))
    K.measure("burak", im, sheet)
    im.save(os.path.join(sp, "bust_burak.png"))
    save_zoom(im, os.path.join(sp, "bust_burak_5x.png"), 5, "#222034")
