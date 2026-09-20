"""Role grids and palettes for the in-fight pause screen's final art.

Everything here is built with art_source/ui_kit's own framegen/kitlib, so the pause set is
assembled by the same code that assembled ui_button.png and ui_card_frame.png rather than by a
lookalike. That is the whole point: the screen has to read as this game's furniture, not as a new
one. Measured against the shipped kit, the targets are 11-12 colours and 25-33% pure black of the
opaque pixels (ui_button 12/29.8%, ui_dialogue_frame 11/25.7%, ui_card_frame 11/33.3%).

Every colour is DB32. Every 9-slice is 24x24 with margin 8, which is exactly the 72x72 / margin 24
the _3x companion needs, and PauseArtLayout already quotes 24 for all four of them.

build() -> {name: (rows, margin_or_None, palette)}, the same shape kit_assets.build() returns.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "art_source", "ui_kit"))

from framegen import frame_grid, chamfer, inner_round, stamp, to_rows  # noqa: E402

# ---------------------------------------------------------------- palette roles
# The kit's brass tube, lit from the upper left, straight out of kit_assets.BRASS.
BRASS = {
    "K": "000000",   # keyline
    "1": "fbf236",   # gold highlight
    "2": "eec39a",   # pale
    "3": "d9a066",   # tan
    "4": "8a6f30",   # dark gold
    "5": "524b24",   # deepest gold
    "a": "ffffff",   # stud sparkle
    "b": "fbf236",
    "c": "8f563b",   # stud core, lit
    "d": "45283c",   # stud core, shadow
}

# The kit's corner rivet, unchanged. It is the single most recognisable thing about this UI.
PLATE7 = [
    "KKKKKKK",
    "K11112K",
    "K1ab34K",
    "K1bcd4K",
    "K13dd4K",
    "K24445K",
    "KKKKKKK",
]

# ---------------------------------------------------------------- 9-slice profiles
# frame_grid takes `top`/`left` outer->inner and `bot`/`right` inner->outer. Anything past the end
# of a profile is the fill, so a 5-long profile on a margin-8 texture leaves three rings of flat
# fill inside it - which is what keeps the innermost margin ring equal to the centre, and the
# stretch bleed-safe.

# The panel: the kit's tube with a SECOND black ring inside it instead of the card frame's blue
# bottom/right hairline. Two things come out of that. The field is fenced off from the brass by a
# 6px black line at 3x, which is what lets the panel hold its edge over Eric's bright green mat
# and over Carter's near-black barrage with the same texture; and it pushes the black ratio up into
# the kit's band rather than below it.
PANEL_TOP = list("K1234KK")      # K gold pale tan dark K K
PANEL_BOT = list("KK2345K")      # reads outward: K K pale tan dark deepest K

# The rows are not buttons. Five crimson slabs in a column is a wall of red and gives the selected
# row nowhere to go, so a resting row is a recessed well - the same shape the boss nameplate uses -
# and only the selected one lights up.
ROW_TOP = list("K45Ks")          # K, dark gold, deepest gold, K, navy hairline
ROW_BOT = list("hK45K")          # reads outward: K, deepest gold, dark gold, K, blue bounce


def _frame(top, bot, fill, plate=None, n=24):
    g = frame_grid(n, top, bot, fill=fill)
    chamfer(g)
    # Round the OUTER of the two keyline rings. inner_round's second move writes K one pixel
    # further in, which lands on the inner ring and is what we want; aiming it at the inner ring
    # instead puts a black pixel in the innermost margin ring, and that ring has to stay equal to
    # the fill or the 9-slice bleeds a black speck into the stretched edge.
    inner_round(g, n, len(top) - 2)
    if plate:
        stamp(g, n, plate)
    return to_rows(g)


def build():
    A = {}

    # PANEL - navy field, the colour every card and dialogue box in the game is already filled with.
    A["pause_panel"] = (
        _frame(PANEL_TOP, PANEL_BOT, "P", PLATE7), 8,
        dict(BRASS, P="222034"),
    )

    # CONFIRM PANEL - the same frame, warmed to plum. It only ever appears on top of the navy panel
    # and it is asking whether to throw a fight away, so it wants to be a different object rather
    # than a second navy rectangle. The stud's shadow core moves off 45283c with it, or the rivets
    # would dissolve into the field.
    A["pause_confirm_panel"] = (
        _frame(PANEL_TOP, PANEL_BOT, "P", PLATE7), 8,
        dict(BRASS, P="45283c", d="663931"),
    )

    # ROW, resting - a well: hard keyline, a two-tone dark brass hairline, then the kit's own
    # portrait-well blue. Quiet enough that four of them stacked read as a list.
    A["pause_row"] = (
        _frame(ROW_TOP, ROW_BOT, "q"), 8,
        dict(BRASS, q="3f3f74", s="222034", h="5b6ee1"),
    )

    # ROW, selected - the panel's own frame recipe (full tube, double keyline, rivets) around the
    # menu button's bright crimson. It is deliberately NOT ui_button_hover: sharing the panel's
    # frame is what makes a selected row look like a piece of the pause screen that has lit up,
    # and a hard black fence keeps the crimson off the brass.
    A["pause_row_focus"] = (
        _frame(PANEL_TOP, PANEL_BOT, "F", PLATE7), 8,
        dict(BRASS, F="d95763"),
    )

    return A
