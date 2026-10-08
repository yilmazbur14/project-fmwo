"""The player's three-hit combo: hits 2 and 3 as 32x32 text grids, in player_4dir_sheet.png's own style.

    player_combo_sheet.png   8 columns x 4 rows of 32x32 cells (256x128)
        rows      DOWN, UP, LEFT, RIGHT (PlayerScript.Facing order, as the 4-dir sheet)
        cols 0-3  hit 2, the other hand from hit 1: guard, chamber, travel, extension
        cols 4-7  hit 3, the body blow: guard (sinks), chamber (crouch, fist cocked at the hip),
                  drive (a one-frame smear), extension (the lunge)

Hit 1 stays the 4-dir sheet's columns 5-8. Both new hits keep hit 1's cadence (four frames at 0, 1/6,
2/6 and 3/6 s of animation time at speed_scale 2.0, ~83 ms each, full extension on the fourth) and
start from the guard hit 1 starts from, since the player is back in Idle between punches.

Which hand throws each hit:
  hit 1  (the 4-dir sheet) DOWN screen-right (his left, the lead), UP screen-left (his left),
         RIGHT the lead glove held out in front of the face (blue).
  hit 2  the other hand in every facing: DOWN screen-left, UP screen-right, RIGHT the rear glove held
         at the chest (the near arm, dark blue). A straight from the rear hand: the lead glove pulled
         back to guard and a little more shoulder turn than hit 1.
  hit 3  the same rear (power) hand again, to the body: dip on bent knees, twist, drive in low with a
         lunge. Hit 2 and hit 3 double up on that hand, as a cross followed by a cross to the body.

His own style, measured off player_4dir_sheet.png (NOT the bosses'): seven colours, no keyline (black
is only his hair and his shoes), two skin tones (S lit, s shade), light from the upper left.
Everything that already exists on his sheet is copied from it texel for texel: the head (moved as one
block in hit 3), the torso rows, the shorts and legs of the punch stance. Only the arms, the crouch's
shorts and legs, and the smear marks are drawn. The feet never move: every cell's shoes sit on exactly
the pixels of the 4-dir sheet's punch cells (columns 5-8), so the game can swap sheets mid-chain
without a jitter. LEFT is RIGHT mirrored (x' = 31 - x), exactly as the 4-dir sheet's LEFT row is.

Each grid is {row: 32-character string}; rows not listed are empty.
    K black (hair, shoes)   R red (headband)   S skin   s skin shade
    B blue   D dark blue   L light blue   . empty
Nothing in this module writes anything; combo_export.py and combo_previews.py write, into a folder
you name on their command line.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
PLAYER_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer')
BASE_SHEET = os.path.join(PLAYER_DIR, 'player_4dir_sheet.png')   # read only

# His seven colours, exactly as player_4dir_sheet.png holds them.
PAL = {
    'K': (0, 0, 0, 255), 'R': (172, 50, 50, 255), 'S': (215, 152, 100, 255), 's': (172, 113, 79, 255),
    'B': (36, 100, 189, 255), 'D': (22, 47, 187, 255), 'L': (56, 131, 201, 255),
}
KEYS = {v[:3]: k for k, v in PAL.items()}
W = H = 32
FACINGS = ('DOWN', 'UP', 'LEFT', 'RIGHT')          # the sheet's rows, PlayerScript.Facing order
COLUMNS = ('hit 2 guard', 'hit 2 chamber', 'hit 2 travel', 'hit 2 extension',
           'hit 3 guard', 'hit 3 chamber', 'hit 3 drive (smear)', 'hit 3 extension')
HIT1_COLS = (5, 6, 7, 8)                            # hit 1 in player_4dir_sheet.png
IDLE_COL = 0
EXTENSION = {2: 3, 3: 7}                            # the extension column of each new hit


# --------------------------------------------------------------------------------------------------
# DOWN, facing the camera. Hit 1 throws the screen-right glove (his left, the lead hand), so hits 2
# and 3 throw the screen-left one (his right, the rear hand).
DOWN = [
    # 0 hit 2 guard: his right glove (screen-left) drops to the chest, the forearm hanging under it; the
    #   lead glove stays at the cheek
    {
         4: '..............KKK...............',
         5: '.............KKKKK..............',
         6: '.............RKKKR..............',
         7: '.............RRKRR..............',
         8: '.............SSRSS..............',
         9: '.............SRSRSBB............',
        10: '..............SSS.BB............',
        11: '.............SsSsSsS............',
        12: '...........BBsSsSsSS............',
        13: '...........BBSSSSSSS............',
        14: '...........SsSSsSSS.............',
        15: '...........SSSSsSSS.............',
        16: '...........SSSSSSSS.............',
        17: '.............BLBLBL.............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 1 hit 2 chamber: the right glove cocked back up at the face; the left hip turns in (waist notch,
    #   band end lifted)
    {
         4: '..............KKK...............',
         5: '.............KKKKK..............',
         6: '.............RKKKR..............',
         7: '.............RRKRR..............',
         8: '...........BBSSRSS..............',
         9: '...........BBSRSRSBB............',
        10: '...........Ss.SSS.BB............',
        11: '...........SsSsSsSsS............',
        12: '...........SSsSsSsSS............',
        13: '............SSSSSSSS............',
        14: '.............SSsSSS.............',
        15: '..............SsSSS.............',
        16: '.............LSSSSS.............',
        17: '..............LBLBL.............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 2 hit 2 travel: the right fist comes at the camera over the chest, foreshortened, dark underside
    {
         4: '..............KKK...............',
         5: '.............KKKKK..............',
         6: '.............RKKKR..............',
         7: '.............RRKRR..............',
         8: '.............SSRSS..............',
         9: '.............SRSRSBB............',
        10: '..............SSS.BB............',
        11: '...........SsSsSsSsS............',
        12: '...........SssSsSsSS............',
        13: '...........SsSSSSSSS............',
        14: '...........BBBSsSSS.............',
        15: '...........BBDSsSSS.............',
        16: '...........DDDSSSSS.............',
        17: '.............BLBLBL.............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 3 hit 2 extension: the right arm drives down the centre to the fist between the knees; the lead
    #   shoulder turned away (a texel narrower, shaded edge)
    {
         4: '..............KKK...............',
         5: '.............KKKKK..............',
         6: '.............RKKKR..............',
         7: '.............RRKRR..............',
         8: '.............SSRSS..............',
         9: '.............SRSRSBB............',
        10: '..............SSS.BB............',
        11: '...........SsSsSsSs.............',
        12: '...........SSsSsSss.............',
        13: '............SSsSSSs.............',
        14: '............SSsSSSs.............',
        15: '.............SSsSSs.............',
        16: '.............SSsSSs.............',
        17: '.............BSsLBL.............',
        18: '.............BSsBBD.............',
        19: '............BBSsBBBD............',
        20: '...........BBBSsBBBBD...........',
        21: '...........BBBSsBBBBD...........',
        22: '...........BBBSs.BBBD...........',
        23: '...........BBBSs..BBD...........',
        24: '...........Ss.BBB..Ss...........',
        25: '...........Ss.BBB..Ss...........',
        26: '...........KK.BBB..Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 4 hit 3 guard: the whole body sinks one row, both gloves up
    {
         5: '..............KKK...............',
         6: '.............KKKKK..............',
         7: '.............RKKKR..............',
         8: '.............RRKRR..............',
         9: '...........BBSSRSS..............',
        10: '...........BBSRSRSBB............',
        11: '...........Ss.SSS.BB............',
        12: '...........SsSsSsSsS............',
        13: '...........SSsSsSsSS............',
        14: '............SSSSSSSS............',
        15: '............SSSsSSS.............',
        16: '.............SSsSSS.............',
        17: '.............SSSSSS.............',
        18: '.............BLBLBL.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 5 hit 3 chamber: deep crouch (head down 3, knees out), the right fist cocked back at the right hip,
    #   the lead glove tucked at the chin
    {
         7: '..............KKK...............',
         8: '.............KKKKK..............',
         9: '.............RKKKR..............',
        10: '.............RRKRR..............',
        11: '.............SSRSS..............',
        12: '.............SRSRSBB............',
        13: '..............SSS.BB............',
        14: '...........SsSsSsSsS............',
        15: '..........SSSsSsSsSS............',
        16: '..........SsSSSSSSSS............',
        17: '.........BBBSSSsSSS.............',
        18: '.........BBD.SSsSSS.............',
        19: '.............BLBLBL.............',
        20: '...........BBBBBBBBD............',
        21: '..........BBBBBBBBBBD...........',
        22: '..........BBBBB..BBBBD..........',
        23: '..........BBBB....BBBD..........',
        24: '..........Ss.......SSs..........',
        25: '..........Ss.......SSs..........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 6 hit 3 drive (smear): crouched 4 rows, the right fist swings in to the belly with a light streak
    #   trailing from the hip
    {
         8: '..............KKK...............',
         9: '.............KKKKK..............',
        10: '.............RKKKR..............',
        11: '.............RRKRR..............',
        12: '.............SSRSS..............',
        13: '.............SRSRSBB............',
        14: '..............SSS.BB............',
        15: '...........SsSsSsSsS............',
        16: '...........SLBBsSsSS............',
        17: '..........LLBBBSSSSS............',
        18: '............BDDsSSS.............',
        19: '.............SSsSSS.............',
        20: '.............BLBLBL.............',
        21: '...........BBBBBBBBD............',
        22: '..........BBBBB..BBBD...........',
        23: '..........BBBB....BBBD..........',
        24: '..........Ss.......SSs..........',
        25: '..........Ss.......SSs..........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 7 hit 3 extension: from the crouch the right arm drives down the centre into a big 4x3 fist at the
    #   feet; lead glove at the chin, lead shoulder turned away
    {
         8: '..............KKK...............',
         9: '.............KKKKK..............',
        10: '.............RKKKR..............',
        11: '.............RRKRR..............',
        12: '.............SSRSS..............',
        13: '.............SRSRSBB............',
        14: '..............SSS.BB............',
        15: '...........SsSsSsSs.............',
        16: '...........SSsSsSss.............',
        17: '............SSsSSSs.............',
        18: '............SSSsSSs.............',
        19: '.............SSsSS..............',
        20: '.............BSsLBL.............',
        21: '...........BBBSsBBBD............',
        22: '..........BBBBSs.BBBD...........',
        23: '..........BBBBSs..BBBD..........',
        24: '..........Ss..Ss...SSs..........',
        25: '..........Ss..Ss...SSs..........',
        26: '...........KK.LBBB.Ss...........',
        27: '...........KK.BBBB.KK...........',
        28: '..............BBDD.KKK..........',
    },
]

# --------------------------------------------------------------------------------------------------
# UP, the back view. Hit 1 throws the screen-left glove (his left), so hits 2 and 3 throw the
# screen-right one (his right).
UP = [
    # 0 hit 2 guard: his right glove (screen-right) drops to the shoulder blade
    {
         4: '..............KKK...............',
         5: '.............KKKKK..............',
         6: '...........R.RRRRR..............',
         7: '............RKKRKK..............',
         8: '.............KKKKK..............',
         9: '...........BBsKKKs..............',
        10: '...........BB.SsS...............',
        11: '...........SsSSsSSBB............',
        12: '...........SSsSsSsBB............',
        13: '............SSSsSSsS............',
        14: '............SSSsSSS.............',
        15: '.............SSsSSS.............',
        16: '.............SSSSSS.............',
        17: '.............BLBLBL.............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 1 hit 2 chamber: the right glove chambered low at the hip; the waistband twists
    {
         4: '..............KKK...............',
         5: '.............KKKKK..............',
         6: '...........R.RRRRR..............',
         7: '............RKKRKK..............',
         8: '.............KKKKK..............',
         9: '...........BBsKKKs..............',
        10: '...........BB.SsS...............',
        11: '...........SsSSsSSs.............',
        12: '...........SSsSsSsSS............',
        13: '............SSSsSSs.............',
        14: '............SSSsSSBB............',
        15: '.............SSsSSBB............',
        16: '.............SSSSSS.............',
        17: '.............BLBLB..............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 2 hit 2 travel: the right arm reaches up past the head, the glove above the hair
    {
         4: '..............KKK.BB............',
         5: '.............KKKKKBB............',
         6: '...........R.RRRRRsS............',
         7: '............RKKRKKsS............',
         8: '.............KKKKKsS............',
         9: '...........BBsKKKssS............',
        10: '...........BB.SsSSS.............',
        11: '...........SsSSsSSs.............',
        12: '...........SSsSsSsSS............',
        13: '............SSSsSSSS............',
        14: '............SSSsSSS.............',
        15: '.............SSsSSS.............',
        16: '.............SSSSSS.............',
        17: '.............BLBLBL.............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 3 hit 2 extension: the right arm fully up to the top of the cell (hit 1 mirrored); the left glove
    #   holds guard
    {
         0: '..................BB............',
         1: '..................BB............',
         2: '..................sS............',
         3: '..................sS............',
         4: '..............KKK.sS............',
         5: '.............KKKKKsS............',
         6: '...........R.RRRRRsS............',
         7: '............RKKRKKsS............',
         8: '.............KKKKKsS............',
         9: '...........BBsKKKssS............',
        10: '...........BB.SsSSS.............',
        11: '...........SsSSsSSs.............',
        12: '...........SSsSsSsSS............',
        13: '............SSSsSSSS............',
        14: '............SSSsSSS.............',
        15: '.............SSsSSS.............',
        16: '.............SSSSSS.............',
        17: '.............BLBLBL.............',
        18: '.............BBBBBD.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 4 hit 3 guard: the whole body sinks one row, both gloves up
    {
         5: '..............KKK...............',
         6: '.............KKKKK..............',
         7: '...........R.RRRRR..............',
         8: '............RKKRKK..............',
         9: '.............KKKKKBB............',
        10: '...........BBsKKKsBB............',
        11: '...........BB.SsS.sS............',
        12: '...........SsSSsSSsS............',
        13: '...........SSsSsSsSS............',
        14: '............SSSsSSSS............',
        15: '............SSSsSSS.............',
        16: '.............SSsSSS.............',
        17: '.............SSSSSS.............',
        18: '.............BLBLBL.............',
        19: '............BBBBBBBD............',
        20: '...........BBBBBBBBBD...........',
        21: '...........BBBBBBBBBD...........',
        22: '...........BBBB..BBBD...........',
        23: '...........BBB....BBD...........',
        24: '...........Ss......Ss...........',
        25: '...........Ss......Ss...........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 5 hit 3 chamber: deep crouch, the right fist cocked back at the right hip with the elbow out
    {
         7: '..............KKK...............',
         8: '.............KKKKK..............',
         9: '...........R.RRRRR..............',
        10: '............RKKRKK..............',
        11: '.............KKKKK..............',
        12: '...........BBsKKKs..............',
        13: '...........BB.SsS...............',
        14: '...........SsSSsSSssS...........',
        15: '...........SSsSsSsSSSS..........',
        16: '............SSSsSSSSSs..........',
        17: '............SSSsSSSBBB..........',
        18: '.............SSsSSSBBD..........',
        19: '.............BLBLBL.............',
        20: '...........BBBBBBBBD............',
        21: '..........BBBBBBBBBBD...........',
        22: '..........BBBBB..BBBBD..........',
        23: '..........BBBB....BBBD..........',
        24: '..........Ss.......SSs..........',
        25: '..........Ss.......SSs..........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 6 hit 3 drive (smear): crouched 4 rows, the right arm drives up past the head, a speed line on its
    #   outer side
    {
         6: '..................BBB...........',
         7: '..................BBB...........',
         8: '..............KKK.BBD...........',
         9: '.............KKKKKsS.L..........',
        10: '...........R.RRRRRsS.L..........',
        11: '............RKKRKKsS.L..........',
        12: '.............KKKKKsS............',
        13: '...........BBsKKKssS............',
        14: '...........BB.SsSssS............',
        15: '...........SsSSsSSsS............',
        16: '...........SSsSsSsSS............',
        17: '............SSSsSSSS............',
        18: '............SSSsSSS.............',
        19: '.............SSsSSS.............',
        20: '.............BLBLBL.............',
        21: '...........BBBBBBBBD............',
        22: '..........BBBBB..BBBD...........',
        23: '..........BBBB....BBBD..........',
        24: '..........Ss.......SSs..........',
        25: '..........Ss.......SSs..........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
    # 7 hit 3 extension: the right arm fully up from the crouch into a 3x3 fist, stopping two rows short
    #   of hit 1's reach
    {
         2: '..................LBB...........',
         3: '..................BBB...........',
         4: '..................BBD...........',
         5: '..................sS............',
         6: '..................sS............',
         7: '..................sS............',
         8: '..............KKK.sS............',
         9: '.............KKKKKsS............',
        10: '...........R.RRRRRsS............',
        11: '............RKKRKKsS............',
        12: '.............KKKKKsS............',
        13: '...........BBsKKKssS............',
        14: '...........BB.SsSssS............',
        15: '...........SsSSsSSsS............',
        16: '...........SSsSsSsSS............',
        17: '............SSSsSSSS............',
        18: '............SSSsSSS.............',
        19: '.............SSsSSS.............',
        20: '.............BLBLBL.............',
        21: '...........BBBBBBBBD............',
        22: '..........BBBBB..BBBD...........',
        23: '..........BBBB....BBBD..........',
        24: '..........Ss.......SSs..........',
        25: '..........Ss.......SSs..........',
        26: '...........KK......Ss...........',
        27: '...........KK......KK...........',
        28: '...................KKK..........',
    },
]

# --------------------------------------------------------------------------------------------------
# RIGHT, the side view; LEFT is its exact mirror (x' = 31 - x), as in the 4-dir sheet. Hit 1 throws
# the lead glove held out in front of the face (blue); hits 2 and 3 throw the rear glove held at the
# chest (the near arm, dark blue), which stays dark when it is out so it reads as the other hand.
RIGHT = [
    # 0 hit 2 guard: the lead glove tucks a texel back toward the chin; the rear (dark) glove at the chest
    {
         4: '............R..KKK..............',
         5: '.............RKKKKK.............',
         6: '............R.RRRRR.............',
         7: '..............KRRRR.............',
         8: '..............sSSSBB............',
         9: '..............sSSSBB............',
        10: '............sSDDDSss............',
        11: '...........sSSDDDSss............',
        12: '...........sSsSsSsss............',
        13: '...........sSSsSSss.............',
        14: '...........sSSSSSSs.............',
        15: '............sSSSSS..............',
        16: '.............sSSS...............',
        17: '............DLBLBL..............',
        18: '............DBBBBBB.............',
        19: '...........DBBBBBBBB............',
        20: '...........DBBBBBBBBB...........',
        21: '..........LBBBBDDBBBB...........',
        22: '..........LBBBD..BBBBB..........',
        23: '..........BLLD....BBBBB.........',
        24: '..........Ss.......sSS..........',
        25: '.........Ss........sSS..........',
        26: '.........Ss........sS...........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 1 hit 2 chamber: the lead glove up at the brow; the rear glove pulls back and down (the coil)
    {
         4: '............R..KKK..............',
         5: '.............RKKKKK.............',
         6: '............R.RRRRR.............',
         7: '..............KRRRBB............',
         8: '..............sSSSBB............',
         9: '..............sSSS..............',
        10: '............sSSSSsss............',
        11: '...........sSDDDSsSs............',
        12: '...........sSDDDSsss............',
        13: '...........sSSsSSss.............',
        14: '...........sSSSSSSs.............',
        15: '............sSSSSS..............',
        16: '.............sSSS...............',
        17: '............DLBLBL..............',
        18: '............DBBBBBB.............',
        19: '...........DBBBBBBBB............',
        20: '...........DBBBBBBBBB...........',
        21: '..........LBBBBDDBBBB...........',
        22: '..........LBBBD..BBBBB..........',
        23: '..........BLLD....BBBBB.........',
        24: '..........Ss.......sSS..........',
        25: '.........Ss........sSS..........',
        26: '.........Ss........sS...........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 2 hit 2 travel: the rear arm half out at shoulder height, the dark glove at x20-22
    {
         4: '............R..KKK..............',
         5: '.............RKKKKK.............',
         6: '............R.RRRRR.............',
         7: '..............KRRRBB............',
         8: '..............sSSSBB............',
         9: '..............sSSS..............',
        10: '............sSSSSSSSBDD.........',
        11: '...........sSSSSSsssDDD.........',
        12: '...........sSsSsSsss............',
        13: '...........sSSsSSss.............',
        14: '...........sSSSSSSs.............',
        15: '............sSSSSS..............',
        16: '.............sSSS...............',
        17: '............DLBLBL..............',
        18: '............DBBBBBB.............',
        19: '...........DBBBBBBBB............',
        20: '...........DBBBBBBBBB...........',
        21: '..........LBBBBDDBBBB...........',
        22: '..........LBBBD..BBBBB..........',
        23: '..........BLLD....BBBBB.........',
        24: '..........Ss.......sSS..........',
        25: '.........Ss........sSS..........',
        26: '.........Ss........sS...........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 3 hit 2 extension: the rear arm fully out at shoulder height (a row under hit 1's), fist at x24-26;
    #   the lead glove guards the brow
    {
         4: '............R..KKK..............',
         5: '.............RKKKKK.............',
         6: '............R.RRRRR.............',
         7: '..............KRRRBB............',
         8: '..............sSSSBB............',
         9: '..............sSSS..............',
        10: '............sSSSSSSSSSSSBDD.....',
        11: '...........sSSSSSsssssssDDD.....',
        12: '...........sSsSsSsss............',
        13: '...........sSSsSSss.............',
        14: '...........sSSSSSSs.............',
        15: '............sSSSSS..............',
        16: '.............sSSS...............',
        17: '............DLBLBL..............',
        18: '............DBBBBBB.............',
        19: '...........DBBBBBBBB............',
        20: '...........DBBBBBBBBB...........',
        21: '..........LBBBBDDBBBB...........',
        22: '..........LBBBD..BBBBB..........',
        23: '..........BLLD....BBBBB.........',
        24: '..........Ss.......sSS..........',
        25: '.........Ss........sSS..........',
        26: '.........Ss........sS...........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 4 hit 3 guard: the whole body sinks one row, gloves at guard
    {
         5: '............R..KKK..............',
         6: '.............RKKKKK.............',
         7: '............R.RRRRR.............',
         8: '..............KRRRR.............',
         9: '..............sSSSBB............',
        10: '..............sSSSBB............',
        11: '............sSDDDSss............',
        12: '...........sSSDDDSss............',
        13: '...........sSsSsSsss............',
        14: '...........sSSsSSss.............',
        15: '...........sSSSSSSs.............',
        16: '............sSSSSS..............',
        17: '.............sSSS...............',
        18: '............DLBLBL..............',
        19: '............DBBBBBB.............',
        20: '...........DBBBBBBBBB...........',
        21: '..........LBBBBDDBBBB...........',
        22: '..........LBBBD..BBBBB..........',
        23: '..........BLLD....BBBBB.........',
        24: '..........Ss.......sSS..........',
        25: '.........Ss........sSS..........',
        26: '.........Ss........sS...........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 5 hit 3 chamber: deep crouch (down 3), torso tipping forward, the rear fist cocked back at the rear
    #   hip, the lead glove at the chin
    {
         7: '............R..KKK..............',
         8: '.............RKKKKK.............',
         9: '............R.RRRRR.............',
        10: '..............KRRRR.............',
        11: '..............sSSSBB............',
        12: '..............sSSSBB............',
        13: '.............sSSSSsss...........',
        14: '...........sSSSSSsSs............',
        15: '...........sSsSsSsss............',
        16: '.........BDDSSsSSss.............',
        17: '.........DDDSSSSSSs.............',
        18: '............sSSSSS..............',
        19: '............DLBLBL..............',
        20: '...........DBBBBBBBB............',
        21: '..........LBBBBDDBBBBB..........',
        22: '..........LBBBD..BBBBBB.........',
        23: '.........BLLD.....BBBBB.........',
        24: '.........Ss........sSSS.........',
        25: '.........Ss........sSS..........',
        26: '.........Ss........sS...........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 6 hit 3 drive (smear): lunging (down 4, head 2 forward), the rear arm snapping out between speed
    #   lines
    {
         8: '..............R..KKK............',
         9: '...............RKKKKK...........',
        10: '..............R.RRRRR...........',
        11: '................KRRRRBB.........',
        12: '................sSSSSBB.........',
        13: '................sSSS............',
        14: '..............sSSSSsLLL.........',
        15: '.............sSSSSSSSSSBDD......',
        16: '............sSsSsssssssDDD......',
        17: '............sSSsSSss.LLL........',
        18: '............sSSSSSSs............',
        19: '.............sSSSSS.............',
        20: '.............DLBLBL.............',
        21: '............DBBBBBBBB...........',
        22: '...........LBBBBBDDBBBB.........',
        23: '..........LBBBD....BBBBB........',
        24: '.........BLLD.......BBBB........',
        25: '.........Ss.........sSS.........',
        26: '........Ss.........sSS..........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
    # 7 hit 3 extension: full lunge (head 4 forward and 4 down, back leg long, front knee over the toes),
    #   the rear arm level into a 3x3 fist at x25-27; the lead glove guards the brow
    {
         8: '................R..KKK..........',
         9: '.................RKKKKK.........',
        10: '................R.RRRRR.........',
        11: '..................KRRRRBB.......',
        12: '..................sSSSSBB.......',
        13: '..................sSSS..........',
        14: '................sSSSSsss.BBD....',
        15: '..............sSSSSSSSSSSBDD....',
        16: '..............sSsSsssssssDDD....',
        17: '.............sSSsSSss...........',
        18: '............sSSSSSSs............',
        19: '.............sSSSSS.............',
        20: '.............DLBLBL.............',
        21: '............DBBBBBBBB...........',
        22: '...........LBBBBBDDBBBB.........',
        23: '..........LBBBD....BBBBB........',
        24: '.........BLLD.......BBBB........',
        25: '.........Ss.........sSS.........',
        26: '........Ss.........sSS..........',
        27: '........KK.........KKK..........',
        28: '.......KKK.........KKKKK........',
    },
]

# One line per column, per drawn facing (LEFT reads as RIGHT, mirrored).
DESCRIPTIONS = {
    'DOWN': [
        'hit 2 guard: his right glove (screen-left) drops to the chest, the forearm hanging under it; the lead glove stays at the cheek',
        'hit 2 chamber: the right glove cocked back up at the face; the left hip turns in (waist notch, band end lifted)',
        'hit 2 travel: the right fist comes at the camera over the chest, foreshortened, dark underside',
        'hit 2 extension: the right arm drives down the centre to the fist between the knees; the lead shoulder turned away (a texel narrower, shaded edge)',
        'hit 3 guard: the whole body sinks one row, both gloves up',
        'hit 3 chamber: deep crouch (head down 3, knees out), the right fist cocked back at the right hip, the lead glove tucked at the chin',
        'hit 3 drive (smear): crouched 4 rows, the right fist swings in to the belly with a light streak trailing from the hip',
        'hit 3 extension: from the crouch the right arm drives down the centre into a big 4x3 fist at the feet; lead glove at the chin, lead shoulder turned away',
    ],
    'UP': [
        'hit 2 guard: his right glove (screen-right) drops to the shoulder blade',
        'hit 2 chamber: the right glove chambered low at the hip; the waistband twists',
        'hit 2 travel: the right arm reaches up past the head, the glove above the hair',
        'hit 2 extension: the right arm fully up to the top of the cell (hit 1 mirrored); the left glove holds guard',
        'hit 3 guard: the whole body sinks one row, both gloves up',
        'hit 3 chamber: deep crouch, the right fist cocked back at the right hip with the elbow out',
        'hit 3 drive (smear): crouched 4 rows, the right arm drives up past the head, a speed line on its outer side',
        "hit 3 extension: the right arm fully up from the crouch into a 3x3 fist, stopping two rows short of hit 1's reach",
    ],
    'RIGHT': [
        'hit 2 guard: the lead glove tucks a texel back toward the chin; the rear (dark) glove at the chest',
        'hit 2 chamber: the lead glove up at the brow; the rear glove pulls back and down (the coil)',
        'hit 2 travel: the rear arm half out at shoulder height, the dark glove at x20-22',
        "hit 2 extension: the rear arm fully out at shoulder height (a row under hit 1's), fist at x24-26; the lead glove guards the brow",
        'hit 3 guard: the whole body sinks one row, gloves at guard',
        'hit 3 chamber: deep crouch (down 3), torso tipping forward, the rear fist cocked back at the rear hip, the lead glove at the chin',
        'hit 3 drive (smear): lunging (down 4, head 2 forward), the rear arm snapping out between speed lines',
        'hit 3 extension: full lunge (head 4 forward and 4 down, back leg long, front knee over the toes), the rear arm level into a 3x3 fist at x25-27; the lead glove guards the brow',
    ],
}
DESCRIPTIONS['LEFT'] = DESCRIPTIONS['RIGHT']

LEFT = [{y: r[::-1] for y, r in g.items()} for g in RIGHT]
FRAMES = {'DOWN': DOWN, 'UP': UP, 'LEFT': LEFT, 'RIGHT': RIGHT}

# Where each column's head sits relative to the idle's (hit 3 moves it as one block): (dx, dy).
HEAD_OFFSET = {
    'DOWN': [(0, 0)] * 4 + [(0, 1), (0, 3), (0, 4), (0, 4)],
    'UP': [(0, 0)] * 4 + [(0, 1), (0, 3), (0, 4), (0, 4)],
    'RIGHT': [(0, 0)] * 4 + [(0, 1), (0, 3), (2, 4), (4, 4)],
}
HEAD_OFFSET['LEFT'] = [(-dx, dy) for dx, dy in HEAD_OFFSET['RIGHT']]
# The head in each facing's idle cell (hair, headband, face), inclusive boxes x0, y0, x1, y1. The gloves
# and the flying headband tails are outside them.
HEAD_BOX = {'DOWN': (13, 4, 17, 9), 'UP': (13, 4, 17, 9), 'RIGHT': (14, 4, 17, 9), 'LEFT': (14, 4, 17, 9)}


# ------------------------------------------------------------------ images
def px_of(grid):
    """{row: string} -> {(x, y): key}"""
    px = {}
    for y, row in grid.items():
        for x, ch in enumerate(row):
            if ch != '.':
                px[(x, y)] = ch
    return px


def cell_image(grid):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), k in px_of(grid).items():
        im.putpixel((x, y), PAL[k])
    return im


def sheet_image():
    """The whole 256x128 sheet, built from the grids."""
    sheet = Image.new('RGBA', (W * 8, H * 4), (0, 0, 0, 0))
    for r, facing in enumerate(FACINGS):
        for c, grid in enumerate(FRAMES[facing]):
            sheet.alpha_composite(cell_image(grid), (c * W, r * H))
    return sheet


def base_cell(row, col, path=BASE_SHEET):
    """One 32x32 cell of player_4dir_sheet.png (read only), as an RGBA image."""
    with Image.open(path) as im:
        return im.convert('RGBA').crop((col * W, row * H, col * W + W, row * H + H))


def image_px(im):
    """RGBA image of his colours -> {(x, y): key}"""
    px = {}
    for y in range(im.height):
        for x in range(im.width):
            c = im.getpixel((x, y))
            if c[3]:
                px[(x, y)] = KEYS[c[:3]]
    return px


# ------------------------------------------------------------------ checks
def components(px):
    """8-connected pieces."""
    seen, n = set(), 0
    for p in px:
        if p in seen:
            continue
        n += 1
        stack = [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in px and q not in seen:
                        seen.add(q)
                        stack.append(q)
    return n


def lone(px):
    return [p for p in px if not any((p[0] + dx, p[1] + dy) in px
                                     for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)]


def pinholes(px):
    """Empty texels with all four neighbours drawn."""
    xs = [x for x, y in px]
    ys = [y for x, y in px]
    return [(x, y) for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))]


def syntax_problems():
    out = []
    for facing in ('DOWN', 'UP', 'RIGHT'):
        frames = FRAMES[facing]
        if len(frames) != 8:
            out.append('%s: %d frames, not 8' % (facing, len(frames)))
        for c, grid in enumerate(frames):
            for y, row in grid.items():
                if not 0 <= y < H or len(row) != W or set(row) - set(PAL) - {'.'}:
                    out.append('%s col %d row %d: bad row %r' % (facing, c, y, row))
    return out


def cell_problems(facing, c, base_path=BASE_SHEET):
    """What a cell of his must not ship with, checked against his own sheet."""
    r = FACINGS.index(facing)
    px = px_of(FRAMES[facing][c])
    tag = '%s col %d (%s)' % (facing, c, COLUMNS[c])
    out = []
    if components(px) != 1:
        out.append('%s: %d pieces' % (tag, components(px)))
    if lone(px):
        out.append('%s: lone texels %s' % (tag, lone(px)))
    # The feet: exactly hit 1's shoes, so nothing slides when the game swaps sheets mid-chain.
    punch = image_px(base_cell(r, HIT1_COLS[0], base_path))
    shoes = {p for p, k in punch.items() if k == 'K' and p[1] >= 24}
    mine = {p for p, k in px.items() if k == 'K' and p[1] >= 24}
    if mine != shoes:
        out.append("%s: shoes differ from hit 1's: extra %s, missing %s"
                   % (tag, sorted(mine - shoes), sorted(shoes - mine)))
    if max(y for x, y in px) != 28:
        out.append('%s: lowest texel on row %d, not 28' % (tag, max(y for x, y in px)))
    # The head: the idle's own, texel for texel, at this column's offset.
    idle = image_px(base_cell(r, IDLE_COL, base_path))
    x0, y0, x1, y1 = HEAD_BOX[facing]
    dx, dy = HEAD_OFFSET[facing][c]
    bad = [(x, y) for (x, y), k in idle.items()
           if x0 <= x <= x1 and y0 <= y <= y1 and px.get((x + dx, y + dy)) != k]
    if bad:
        out.append('%s: head differs from his own at %s' % (tag, bad[:6]))
    # Pinholes: only the idle's own neck notches, carried along with the head.
    allowed = {(x + dx, y + dy) for (x, y) in pinholes(idle)}
    extra = [p for p in pinholes(px) if p not in allowed]
    if extra:
        out.append('%s: pinholes %s' % (tag, extra))
    return out


def tip_of(px, facing):
    """The leading texel of the punching glove: of all the blue texels (B, D, L), the ones furthest along
    the facing, and the middle one of that edge (an even edge gives the lower index).
    Returns ((x, y), (edge_first, edge_last)) - the edge span runs along x for DOWN/UP, along y otherwise."""
    blue = [p for p, k in px.items() if k in 'BDL']
    if facing in ('DOWN', 'UP'):
        y = (max if facing == 'DOWN' else min)(yy for xx, yy in blue)
        edge = sorted(xx for xx, yy in blue if yy == y)
        return (edge[(len(edge) - 1) // 2], y), (edge[0], edge[-1])
    x = (max if facing == 'RIGHT' else min)(xx for xx, yy in blue)
    edge = sorted(yy for xx, yy in blue if xx == x)
    return (x, edge[(len(edge) - 1) // 2]), (edge[0], edge[-1])


def fist_tip(facing, c):
    """tip_of for column c of the combo sheet (meaningful on the extension columns, 3 and 7)."""
    return tip_of(px_of(FRAMES[facing][c]), facing)
