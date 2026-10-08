"""Presentation images for the approval pass: the 1920x1080 mock screenshots and the comparison
sheet. Everything is composed at the game's native 640x360 texels and scaled 3x with nearest
neighbour, so every layer shares one pixel grid exactly as the game draws it (canvas_items
stretch, every sprite at scale 3).

Placement follows the finale contract: the god's anchor texel (his lowest texel, on his centre
line) sits at screen (960, 600). The rune circle is centred on his chest core; the fire column's
pivot sits on his anchor. The player is the first 32x32 cell of his sheet at scale 3."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402
import jg_void as V  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCALE = 3
SCREEN = (1920, 1080)
NATIVE = (640, 360)
ANCHOR_SCREEN = (960, 600)
PLAYER_POS = (1200, 900)          # lower middle, stepped right so he is not standing in the fire


def player_cell():
    sheet = Image.open(B.PLAYER_PNG).convert('RGBA')
    return sheet.crop((0, 0, 32, 32))


def place(god_size, anchor, screen_pt=ANCHOR_SCREEN):
    """Native top-left of a layer whose texel `anchor` must land on `screen_pt`."""
    return (int(round(screen_pt[0] / SCALE - anchor[0])), int(round(screen_pt[1] / SCALE - anchor[1])))


def compose(god, god_anchor, runes=None, runes_centre=None, column=None, column_pivot=None,
            backdrop=None, player=True, player_pos=PLAYER_POS):
    """The native 640x360 frame. runes_centre: the god texel the rune circle centres on."""
    native = (backdrop or V.backdrop()).copy()
    gx, gy = place(god.size, god_anchor)
    if runes is not None:
        cx = gx + runes_centre[0]
        cy = gy + runes_centre[1]
        native.alpha_composite(runes, (int(round(cx - (runes.width - 1) / 2.0)), int(round(cy - (runes.height - 1) / 2.0))))
    if column is not None:
        native.alpha_composite(column, (gx + god_anchor[0] - column_pivot[0], gy + god_anchor[1] - column_pivot[1]))
    native.alpha_composite(god, (gx, gy))
    if player:
        pc = player_cell()
        native.alpha_composite(pc, (int(round(player_pos[0] / SCALE - 16)), int(round(player_pos[1] / SCALE - 16))))
    return native


def mock(*a, **kw):
    return compose(*a, **kw).resize(SCREEN, Image.NEAREST)


def screen_box(god, god_anchor):
    """Where the god's opaque texels land on the 1920x1080 screen: (x0, y0, x1, y1), exclusive."""
    bb = god.getbbox()
    gx, gy = place(god.size, god_anchor)
    return ((gx + bb[0]) * SCALE, (gy + bb[1]) * SCALE, (gx + bb[2]) * SCALE, (gy + bb[3]) * SCALE)
