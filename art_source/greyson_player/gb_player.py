"""The player's poses for Greyson's FINAL PHASE, a Punch-Out-style brawl, in the player's pose-sheet
format (PlayerPosed):

    player_final_brawl   10 columns x 4 rows of 32x32 (320x128)

Walled in by debris right in front of Greyson (below him on screen), the player can't move: LEFT or
RIGHT slips a hook, the guard key parries a straight. He is seen from BEHIND, like Little Mac, so only
the back view is wanted: row 1 (UP) is drawn and rows 0, 2 and 3 are copies of it, as
player_glass_row.png and player_sumo_push.png do, so no facing can show a wrong row.

    0-1  GUARD         a high guard, gloves framing his head; 1 is the bounce (a row lower)
    2-3  SLIP LEFT     2 half way, 3 full; the return plays 2 again
    4-5  SLIP RIGHT    the same to the right, drawn (not mirrored), so his light stays upper left
    6-7  PARRY         6 the guard snapped shut over his head; 7 the straight's weight taken
    8-9  HIT           8 the punch lands (head snapped back, guard knocked open); 9 reeling

His own style (see art_source/danny_player/dp_player.py, whose palette, grid reader and audit this
imports read-only): seven colours, no keyline (black is only hair and shoes), arms two texels lit on
the outer side, legs lit on the left, gloves 2x3 lit on the outer top corner.

How the frames were built (the grids below are the result, frozen): every body part is his own,
copied texel for texel and only moved:
  - head: the UP idle's (player_4dir_sheet.png col 0 row 1, rows 4-9), or for the reel the bowed
    back-head of player_guard_break.png (col 1 row 1, rows 8-13); gb_export checks both;
  - back: the UP idle's rows 10-16, shoulders bare where its gloves sat (a crouch drops rows);
  - shorts and legs: the UP idle's, the knees a row softer; BOTH FEET SIT ON THE SAME TEXELS IN EVERY
    FRAME (he is walled in and can't step): left shoe x 11-12 rows 26-27, right x 18-21 rows 27-28;
  - the slips are guard A with everything above the waistband sheared over row by row (5 texels at
    the shoulders, 1 at the waist, dropped a row at full stretch), so the lean keeps his own shading.
Only the arms and gloves are drawn per pose. Draw order: back, arms, shorts, legs, head (from behind
the head is nearest the camera and the waistband sits over the torso's last row).

Grids: one character per texel, up to 32 per row (trailing '.' left off), rows not listed are empty:
    k black   D dark blue   B blue   L light blue   R red   s shaded skin   S skin   . empty
Nothing in this module writes anything.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
_DP = os.path.join(ART, 'danny_player')
if _DP not in sys.path:
    sys.path.insert(0, _DP)
import dp_player as DP  # noqa: E402  the player's palette, grid reader and audit (read-only)

if os.path.normcase(os.path.dirname(os.path.abspath(DP.__file__))) != os.path.normcase(_DP):
    raise ImportError('dp_player came from %s, not %s' % (DP.__file__, _DP))

PAL, g, image, from_sheet = DP.PAL, DP.g, DP.image, DP.from_sheet
audit, black, sole_row = DP.audit, DP.black, DP.sole_row
ROOT, PLAYER_DIR, SHEET_4DIR = DP.ROOT, DP.PLAYER_DIR, DP.SHEET_4DIR
GUARD_BREAK = os.path.join(PLAYER_DIR, 'player_guard_break.png')
DOWN, UP, LEFT, RIGHT = DP.DOWN, DP.UP, DP.LEFT, DP.RIGHT
W = H = 32

# 0 GUARD: his stance (the UP idle legs, knees a row softer) in a high guard: both gloves up
# framing the head (the rear right glove a row higher, as in his idle), forearms dropping to elbows
# tucked by the ribs.
GUARD_A = {
    5:  '..............kkk',
    6:  '.............kkkkk.BL',
    7:  '.........LBR.RRRRR.BB',
    8:  '.........BB.RkkRkk.DD',
    9:  '.........BD..kkkkk.sS',
    10: '.........Ss..skkks.sS',
    11: '.........SsSS.SsS.ssS',
    12: '..........SsSSSsSSsSsS',
    13: '...........SssSsSsSSs',
    14: '............SSSsSSSS',
    15: '............SSSsSSS',
    16: '.............SSsSSS',
    17: '.............SSSSSS',
    18: '............BBLBLBL',
    19: '...........BBBBBBBD',
    20: '...........BBBBBBBBD',
    21: '...........BBBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBB.BBBBD',
    24: '...........BBB...BBBD',
    25: '...........Ss.....SSs',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 1 GUARD, the bounce: everything above the knees a row lower, the feet where they were.
GUARD_B = {
    6:  '..............kkk',
    7:  '.............kkkkk.BL',
    8:  '.........LBR.RRRRR.BB',
    9:  '.........BB.RkkRkk.DD',
    10: '.........BD..kkkkk.sS',
    11: '.........Ss..skkks.sS',
    12: '.........SsSS.SsS.ssS',
    13: '..........SsSSSsSSsSsS',
    14: '...........SssSsSsSSs',
    15: '............SSSsSSSS',
    16: '............SSSsSSS',
    17: '.............SSsSSS',
    18: '.............SSSSSS',
    19: '............BBLBLBL',
    20: '...........BBBBBBBD',
    21: '...........BBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBBBBBBBD',
    24: '...........BBBB.BBBBD',
    25: '...........BBB...BBBD',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 2 SLIP LEFT, half way: guard A sheared left (3 at the head, 0 at the waist).
SLIP_L_MID = {
    5:  '...........kkk',
    6:  '..........kkkkk.BL',
    7:  '......LBR.RRRRR.BB',
    8:  '......BB.RkkRkk.DD',
    9:  '......BD..kkkkk.sS',
    10: '......Ss..skkks.sS',
    11: '......SsSS.SsS.ssS',
    12: '........SsSSSsSSsSsS',
    13: '.........SssSsSsSSs',
    14: '...........SSSsSSSS',
    15: '...........SSSsSSS',
    16: '.............SSsSSS',
    17: '.............SSSSSS',
    18: '............BBLBLBL',
    19: '...........BBBBBBBD',
    20: '...........BBBBBBBBD',
    21: '...........BBBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBB.BBBBD',
    24: '...........BBB...BBBD',
    25: '...........Ss.....SSs',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 3 SLIP LEFT, full: sheared 5 at the shoulders to 1 at the waist and dropped a row; the head
# ducks under the hook, the guard stays up.
SLIP_L_FULL = {
    6:  '.........kkk',
    7:  '........kkkkk.BL',
    8:  '....LBR.RRRRR.BB',
    9:  '....BB.RkkRkk.DD',
    10: '....BD..kkkkk.sS',
    11: '....Ss..skkks.sS',
    12: '....SsSS.SsS.ssS',
    13: '......SsSSSsSSsSsS',
    14: '.......SssSsSsSSs',
    15: '.........SSSsSSSS',
    16: '..........SSSsSSS',
    17: '............SSsSSS',
    18: '............BBLBLBL',
    19: '...........BBBBBBBD',
    20: '...........BBBBBBBBD',
    21: '...........BBBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBB.BBBBD',
    24: '...........BBB...BBBD',
    25: '...........Ss.....SSs',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 4 SLIP RIGHT, half way.
SLIP_R_MID = {
    5:  '.................kkk',
    6:  '................kkkkk.BL',
    7:  '............LBR.RRRRR.BB',
    8:  '............BB.RkkRkk.DD',
    9:  '............BD..kkkkk.sS',
    10: '............Ss..skkks.sS',
    11: '............SsSS.SsS.ssS',
    12: '............SsSSSsSSsSsS',
    13: '.............SssSsSsSSs',
    14: '.............SSSsSSSS',
    15: '.............SSSsSSS',
    16: '.............SSsSSS',
    17: '.............SSSSSS',
    18: '............BBLBLBL',
    19: '...........BBBBBBBD',
    20: '...........BBBBBBBBD',
    21: '...........BBBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBB.BBBBD',
    24: '...........BBB...BBBD',
    25: '...........Ss.....SSs',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 5 SLIP RIGHT, full. Sheared, not mirrored: his head, tails and light are unchanged.
SLIP_R_FULL = {
    6:  '...................kkk',
    7:  '..................kkkkk.BL',
    8:  '..............LBR.RRRRR.BB',
    9:  '..............BB.RkkRkk.DD',
    10: '..............BD..kkkkk.sS',
    11: '..............Ss..skkks.sS',
    12: '..............SsSS.SsS.ssS',
    13: '..............SsSSSsSSsSsS',
    14: '...............SssSsSsSSs',
    15: '...............SSSsSSSS',
    16: '..............SSSsSSS',
    17: '..............SSsSSS',
    18: '............BBLBLBLS',
    19: '...........BBBBBBBD',
    20: '...........BBBBBBBBD',
    21: '...........BBBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBB.BBBBD',
    24: '...........BBB...BBBD',
    25: '...........Ss.....SSs',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 6 PARRY: the guard snapped shut on the straight, both gloves thrust up together just over his
# head, forearms rising from elbows flared at the shoulders, knees soft (the bounce's legs).
PARRY_SNAP = {
    3:  '.............LB.BL',
    4:  '.............BB.BB',
    5:  '.............BD.DD',
    6:  '............SskkksS',
    7:  '...........SskkkkksS',
    8:  '...........RsRRRRRsS',
    9:  '...........SRkkRkksS',
    10: '...........SskkkkksS',
    11: '............SskkksS',
    12: '...........SS.SsS.sS',
    13: '...........SsSSsSSsS',
    14: '...........SSsSsSsSS',
    15: '............SSSsSSSS',
    16: '............SSSsSSS',
    17: '.............SSsSSS',
    18: '.............SSSSSS',
    19: '............BBLBLBL',
    20: '...........BBBBBBBD',
    21: '...........BBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBBBBBBBD',
    24: '...........BBBB.BBBBD',
    25: '...........BBB...BBBD',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 7 PARRY, the weight taken: the locked guard driven a row down onto his head, the body sunk a
# row with it (the back a row shorter), the elbows spread.
PARRY_ABSORB = {
    4:  '.............LB.BL',
    5:  '.............BB.BB',
    6:  '.............BD.DD',
    7:  '............SskkksS',
    8:  '...........SskkkkksS',
    9:  '...........RsRRRRRsS',
    10: '..........SsRkkRkksS',
    11: '..........SsSkkkkkSsS',
    12: '...........SSskkksSS',
    13: '...........SS.SsS.sS',
    14: '...........SsSSsSSsS',
    15: '...........SSsSsSsSS',
    16: '............SSSsSSSS',
    17: '.............SSsSSS',
    18: '.............SSSSSS',
    19: '............BBLBLBL',
    20: '...........BBBBBBBD',
    21: '...........BBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBBBBBBBD',
    24: '...........BBBB.BBBBD',
    25: '...........BBB...BBBD',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 8 HIT: the punch lands. Head snapped back into the shoulders and knocked a texel right, the
# headband tails whipping up, the guard knocked open: left glove flung high, right arm thrown out.
HIT_LAND = {
    3:  '.....LB',
    4:  '.....BB',
    5:  '.....BD',
    6:  '......Ss',
    7:  '.......Ss...R..kkk',
    8:  '........Ss...Rkkkkk',
    9:  '.........Ss...RRRRR......BL',
    10: '..........SsS.kkRkk.SSSSSBB',
    11: '...........SS.kkkkkSssss.DD',
    12: '...........SsSskkksS',
    13: '...........SSsSsSsSS',
    14: '............SSSsSSSS',
    15: '............SSSsSSS',
    16: '.............SSsSSS',
    17: '.............SSSSSS',
    18: '............BBLBLBL',
    19: '...........BBBBBBBD',
    20: '...........BBBBBBBBD',
    21: '...........BBBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBB.BBBBD',
    24: '...........BBB...BBBD',
    25: '...........Ss.....SSs',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

# 9 HIT, reeling: hunched, the guard break's bowed head, knees buckled, gloves dragged back up
# beside the head.
HIT_REEL = {
    10: '..............kkk',
    11: '.............kkkkk..BL',
    12: '.........LB..kkkkk..BB',
    13: '.........BBSSRRRRRSSDD',
    14: '.........BDSskkkRksSsS',
    15: '..........SsSskkkRSSsS',
    16: '............SSSsSSSS',
    17: '.............SSsSSS',
    18: '.............SSSSSS',
    19: '............BBLBLBL',
    20: '...........BBBBBBBD',
    21: '...........BBBBBBBBD',
    22: '...........BBBBBBBBBD',
    23: '...........BBBBBBBBBD',
    24: '...........BBBB.BBBBD',
    25: '...........BBB...BBBD',
    26: '...........kk.....SSs',
    27: '...........kk.....kkk',
    28: '..................kkkk',
}

FRAMES = [
    ('guard', GUARD_A), ('guard', GUARD_B),
    ('slip_left', SLIP_L_MID), ('slip_left', SLIP_L_FULL),
    ('slip_right', SLIP_R_MID), ('slip_right', SLIP_R_FULL),
    ('parry', PARRY_SNAP), ('parry', PARRY_ABSORB),
    ('hit', HIT_LAND), ('hit', HIT_REEL),
]

# Where each column's head came from, for the likeness check: (sheet, col, row, source box
# x0, y0, x1, y1, dx, dy). The UP idle's head core is x 13-17 rows 4-9 (its flying tail texels at x
# 11-12 are left out: they whip about). The reel's is the guard break's bowed head, x 13-17 rows 8-13.
_UP = (SHEET_4DIR, 0, UP, 13, 4, 17, 9)
_BOWED = (GUARD_BREAK, 1, UP, 13, 8, 17, 13)
HEADS = [_UP + (0, 1), _UP + (0, 2), _UP + (-3, 1), _UP + (-5, 2), _UP + (3, 1), _UP + (5, 2),
         _UP + (0, 2), _UP + (0, 3), _UP + (1, 3), _BOWED + (0, 2)]
