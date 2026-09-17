"""FMWO UI kit asset definitions (role grids + DB32 palettes).
build(opts) -> dict name -> (rows, margin_or_None, palette)"""
from framegen import *

TUBE_TOP = list("K1234K")
TUBE_BOT = list("K2345K")          # inner -> outer

PLATE9 = [
    "KKKKKKKKK",
    "K1111112K",
    "K1333334K",
    "K13ab334K",
    "K13bcd34K",
    "K133dd34K",
    "K1333334K",
    "K2444445K",
    "KKKKKKKKK",
]
PLATE7 = [
    "KKKKKKK",
    "K11112K",
    "K1ab34K",
    "K1bcd4K",
    "K13dd4K",
    "K24445K",
    "KKKKKKK",
]

BRASS = {'K': '000000', '1': 'fbf236', '2': 'eec39a', '3': 'd9a066', '4': '8a6f30', '5': '524b24',
         'a': 'ffffff', 'b': 'fbf236', 'c': '8f563b', 'd': '45283c'}


def panel_frame(n, plate, inner_top, inner_bot):
    top = TUBE_TOP + inner_top
    bot = inner_bot + TUBE_BOT
    g = frame_grid(n, top, bot)
    chamfer(g)
    inner_round(g, n, 5)
    if plate:
        stamp(g, n, plate)
    return to_rows(g)


def button_frame(n, state, plate):
    """Crimson face inside the brass rim. All face detail sits at index 6
    (next to the rim); index 7 is plain face on every side (bleed-safe).
    normal/hover: face = rows 6..16 (highlight top/left, shadow right),
                  lip at bottom row 17.
    pressed:      face = rows 7..17 (sunk 1px): dark gap at top row 6,
                  bevel inverted (shadow left, highlight right/bottom)."""
    if state == 'pressed':
        top = TUBE_TOP + list("D")
        bot = list("H") + TUBE_BOT
        left = TUBE_TOP + list("s")
        right = list("H") + TUBE_BOT
    else:
        top = TUBE_TOP + list("H")
        bot = list("L") + TUBE_BOT
        left = TUBE_TOP + list("H")
        right = list("S") + TUBE_BOT
    g = frame_grid(n, top, bot, left, right, fill='F')
    chamfer(g)
    inner_round(g, n, 5)
    if plate:
        stamp(g, n, plate)
    return to_rows(g)


def arrow_rows():
    ARROW = [
        "KKKKKKKK",
        "K111112K",
        "K133334K",
        ".K1334K.",
        "..K34K..",
        "...KK...",
    ]
    f0 = ARROW + ["........"] * 2
    f1 = ["........"] + ARROW + ["........"]
    return [a + b for a, b in zip(f0, f1)]


def build(plates_on_buttons=True, portrait_style='deep'):
    A = {}
    A['ui_dialogue_frame'] = (panel_frame(32, PLATE9, ['p'], ['q']), 10,
                              dict(BRASS, P='222034', p='000000', q='3f3f74'))
    A['ui_card_frame'] = (panel_frame(24, PLATE7, ['p'], ['q']), 8,
                          dict(BRASS, P='222034', p='000000', q='3f3f74'))
    if portrait_style == 'deep':
        # recessed well: black+navy shadow top/left, navy bottom/right; the
        # last margin ring (index 7) is navy on all sides (bleed-safe)
        A['ui_portrait_frame'] = (panel_frame(24, PLATE7, ['p', 's'], ['s', 's']), 8,
                                  dict(BRASS, P='3f3f74', p='000000', s='222034'))
    else:
        A['ui_portrait_frame'] = (panel_frame(24, PLATE7, ['p'], ['q']), 8,
                                  dict(BRASS, P='3f3f74', p='000000', q='3f3f74'))
    bp = PLATE7 if plates_on_buttons else None
    A['ui_button'] = (button_frame(24, 'normal', bp), 8,
                      dict(BRASS, H='d95763', F='ac3232', S='663931', L='45283c'))
    A['ui_button_hover'] = (button_frame(24, 'hover', bp), 8,
                            dict(BRASS, H='eec39a', F='d95763', S='ac3232', L='663931'))
    A['ui_button_pressed'] = (button_frame(24, 'pressed', bp), 8,
                              dict(BRASS, D='45283c', s='663931', F='ac3232', H='d95763'))
    A['ui_dialogue_next'] = (arrow_rows(), None,
                             {'K': '000000', '1': 'ffffff', '2': 'fbf236', '3': 'fbf236', '4': 'd9a066'})
    return A
