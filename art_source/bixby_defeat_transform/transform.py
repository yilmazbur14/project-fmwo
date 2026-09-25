"""bixby_transform.png: 26 frames of 320x256 in a 13x2 grid (left to right, top row first), Bixby's feet
at texel (160, 251) in every frame, timed by LiamEntranceLayout.TRANSFORM_TIMES. Frames 0-9 are the
shipped dog frames on the redesign's ramps (early.py); 10-25 are the beast in the approved design
(late.py), ending on the approved hover frame 0 lifted HOVER_HEIGHT texels.
"""
import common as C
import early
import late

COLS, ROWS = 13, 2


def frames():
    return early.frames() + late.frames()


def sheet(fr=None):
    return C.grid_sheet(fr or frames(), COLS)
