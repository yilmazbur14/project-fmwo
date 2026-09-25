"""The VS card's geometry, copied from Scripts/VsCardArtLayout.gd so the mock-ups draw exactly what
the game draws. Screen numbers are in the 1920x1080 frame; band numbers are texels, before the 3x.

Nothing here is new except the OVERHANG block at the bottom, which is the proposal.
"""
PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
ASSETS = PROJ + "/Assets"
SHIPPED = ASSETS + "/UI/VsCard/"

ART_SCALE = 3
SW, SH = 1920, 1080

# ---- the band (VsCardArtLayout.BAND_AT / BAND_SIZE / SPLIT_*) -------------------------------
BAND_AT = (0, 366)                 # screen px, top-left of the 640x132 band at 3x
BAND_W, BAND_H = 640, 132          # texels
SPLIT_TOP, SPLIT_BOTTOM = 350, 290  # the seam's x on the band's top and bottom rows

# ---- the frame the code draws (LETTERBOX_*, DIM_COLOR) --------------------------------------
LETTERBOX_TOP = [(0, 0, 1920, 276), (0, 274, 1920, 2)]
LETTERBOX_BOTTOM = [(0, 852, 1920, 228), (0, 852, 1920, 2)]
LETTERBOX_COLOR = (21, 19, 31)          # Color(0.08235294, 0.07450981, 0.12156863)
LETTERBOX_RULE_COLOR = (63, 63, 116)    # Color(0.24705882, 0.24705882, 0.45490196)
DIM_COLOR = (34, 32, 52)                # #222034
DIM_ALPHA = 0.78

# ---- where every piece sits (VS_AT, FIGHT_AT, EPITHET_AT, NAME_TOP_RIGHT, ...) ----------------
VS_AT, VS_SIZE = (866, 487), (224, 154)
VS_CENTRE = (VS_AT[0] + VS_SIZE[0] // 2, VS_AT[1] + VS_SIZE[1] // 2)
FIGHT_AT = (54, 174)
EPITHET_AT = (54, 900)
NAME_TOP_RIGHT = (1785, 644)
WIN_TOP_RIGHT = (1716, 924)
BADGE_AT = (1746, 888)

# The VS in band texels, for keeping poses out from under it: x 288.7..363.3, y 40.3..91.7.
VS_TEXELS = ((VS_AT[0]) / 3.0, (VS_AT[1] - BAND_AT[1]) / 3.0,
             (VS_AT[0] + VS_SIZE[0]) / 3.0, (VS_AT[1] + VS_SIZE[1] - BAND_AT[1]) / 3.0)


def seam_x(y):
    """The seam's x at band row y (texels)."""
    return SPLIT_TOP + (SPLIT_BOTTOM - SPLIT_TOP) * (y / float(BAND_H))


# ---- THE RULE: contained, the way Platinum's VS portraits are -----------------------------------
# Each pose lives inside its own half: clipped to the half's polygon, cropped by the band's top and
# bottom rules, and the seam is drawn OVER it, like a panel border. Nothing breaks the band and
# nothing crosses into the other fighter's half - a sword that reaches the seam is cut by it.
# So the halves stay 640 x 132 at BAND_AT, and the game needs no change to show them.
OVERHANG = 0
HALF_W, HALF_H = BAND_W, BAND_H
HALF_AT = BAND_AT
# Where the faces sit, so the two fighters look at each other across the VS on one line.
EYE_LINE = 48               # band row of the eyes, +-4 per character
