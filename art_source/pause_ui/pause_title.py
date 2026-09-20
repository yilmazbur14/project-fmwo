"""The pause screen's drawn title: the idle badge, PAUSED, and the member-list line under it.

One image, because PauseMenuScene.tscn already has exactly one slot for it - TitleArt, the
TextureRect that replaces the placeholder Label the moment USE_FINAL_PAUSE_ART goes true. Baking
the Discord line into the title is what lets the whole garnish ship with no new nodes, no new
layout constant and no wiring.

The lettering is vs_card.textart, the same bake the VS cards and every boss nameplate use, so
PAUSED is the same font, the same hard 40-threshold and the same B-glyph repair as the rest of the
game's drawn text. Sizes are native (1x); build_pause_art writes the 3x companion by nearest
neighbour, so the 3x title is the 99px Godot label the layout sizes for.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # art_source/, so vs_card imports as a package

from PIL import Image  # noqa: E402
from vs_card import textart  # noqa: E402

# DB32. The title's shadow is black rather than PauseArtLayout's #141421, which is off-palette;
# on the panel's #222034 field a black shadow reads the same and keeps the set at 32 colours.
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
MUTED = (132, 126, 135, 255)     # #847e87, the tone the victory and defeat screens timestamp in
GOLD = (251, 242, 54, 255)       # #fbf236
PALE = (238, 195, 154, 255)      # #eec39a
DARK_GOLD = (138, 111, 48, 255)  # #8a6f30

# TITLE_FONT_SIZE is 99 and the art is drawn at 1x, so 33 is the same lettering the placeholder
# Label draws. The member line is 13: 11 is Pixelify's design size but its lowercase closes up
# there, 12 runs "newcomer" together, and 15 or more pushes the art past the 192px the rows allow,
# which would widen the whole panel to fit a garnish. The copy says "idle" rather than "is idle"
# because Pixelify's lowercase s bakes to an x below about 16 - "is idle" reads "ix idle" - and
# because a member list writes a status as a label, not as a sentence.
TITLE_SIZE = 33
STATUS_SIZE = 13
STATUS_TEXT = "newcomer idle in #arena-1"

# Pixelify Sans cannot draw an @ at this size. Measured: at 11 it bakes to a solid blob, and from
# 12 to 14 it comes out as a Q with a tail, so "@newcomer" reads as "Qnewcomer". It only resolves
# at about 16, which is too wide for the column. So the @ is drawn, the way textart already
# redraws the font's broken B and 5 - the difference is only that a rectangle patch cannot rescue
# this one.
AT_GLYPH = [
    ".#####.",
    "#.....#",
    "#.###.#",
    "#.#.#.#",
    "#.###..",
    "#......",
    ".#####.",
]
AT_GAP = 2          # between the drawn @ and the baked name

BADGE = 16          # the idle badge is a 16px square at 1x, 48 at 3x
BADGE_GAP = 6       # between the badge and the P
STATUS_GAP = 5      # between the title line and the member line

# The whole title has to fit the column the rows set, or it widens the panel on its own.
# ROW_MIN_SIZE.x is 576 at 3x = 192 at 1x.
MAX_WIDTH = 192


def idle_badge(size=BADGE):
    """Discord's idle status: a crescent, in the kit's gold ramp with a 1px black outline.

    Drawn from two circles rather than a glyph so it stays a clean pixel shape at 16px. The body
    is one flat block of gold with a 1px shaded rim along its lower right and a 1px pale rim along
    its upper left - lit from the upper left like every other piece of brass here. Shading it in
    wide bands across the crescent instead was tried and rejected: at 16px the bands cover most of
    the shape and it stops reading as a moon and starts reading as a banana.
    """
    r = size / 2.0
    disc = [[False] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            px, py = x + 0.5 - r, y + 0.5 - r
            near = (px * px + py * py) ** 0.5
            bx, by = x + 0.5 - r * 1.55, y + 0.5 - r * 0.50
            bite = (bx * bx + by * by) ** 0.5
            disc[y][x] = near <= r - 1.8 and bite > r - 2.8

    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    for y in range(size):
        for x in range(size):
            if not disc[y][x]:
                touching = any(
                    0 <= y + dy < size and 0 <= x + dx < size and disc[y + dy][x + dx]
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                )
                if touching:
                    px[x, y] = BLACK
                continue
            cx, cy = x + 0.5 - r, y + 0.5 - r
            edge = r - 1.8 - (cx * cx + cy * cy) ** 0.5     # how far inside the outer arc
            down = (cy + 0.45 * cx) / r                     # +1 at the lower right
            if edge < 1.2 and down > 0.0:
                px[x, y] = DARK_GOLD
            elif edge < 1.6 and down < -0.55:
                px[x, y] = PALE
            else:
                px[x, y] = GOLD
    return im


def _stamp(grid, colour):
    """A hand-drawn glyph: '#' is ink, '.' is clear."""
    w, h = len(grid[0]), len(grid)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, rowstr in enumerate(grid):
        for x, ch in enumerate(rowstr):
            if ch == "#":
                px[x, y] = colour
    return im


def title_word():
    """PAUSED in the game's drawn-text treatment: white, 1px black outline, hard black shadow."""
    return textart.bake("PAUSED", TITLE_SIZE, fill="#FFFFFF", outline="#000000",
                        ol_w=1, shadow=(0, 2), shadow_col="#000000")


def status_line(text=STATUS_TEXT):
    """The member-list line: a drawn @, then the name baked out of the font.

    No outline and no shadow, the same as a boss nameplate's lettering - at 7px of cap height an
    outline just fills the counters in.
    """
    name = textart.bake(text, STATUS_SIZE, fill="#847E87", ol_w=0, shadow=(0, 0))
    at = _stamp(AT_GLYPH, MUTED)
    im = Image.new("RGBA", (at.width + AT_GAP + name.width, max(at.height, name.height)),
                   (0, 0, 0, 0))
    # Bottom-aligned: the bake is trimmed to its ink, so its last row is the baseline.
    im.alpha_composite(at, (0, im.height - at.height))
    im.alpha_composite(name, (at.width + AT_GAP, im.height - name.height))
    return im


def build(text=STATUS_TEXT):
    """The finished 1x title. Returns a PIL RGBA image."""
    word = title_word()
    badge = idle_badge()
    line = status_line(text)

    head_w = badge.width + BADGE_GAP + word.width
    head_h = max(badge.height, word.height)
    w = max(head_w, line.width)
    h = head_h + STATUS_GAP + line.height
    assert w <= MAX_WIDTH, "title is %dpx wide, wider than the %dpx row column" % (w, MAX_WIDTH)

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hx = (w - head_w) // 2
    # The badge sits on the word's optical centre, not the block's: the bake carries its drop
    # shadow along the bottom, so centring on the full height drops the badge a pixel low.
    im.alpha_composite(badge, (hx, (head_h - 2 - badge.height) // 2))
    im.alpha_composite(word, (hx + badge.width + BADGE_GAP, (head_h - word.height) // 2))
    im.alpha_composite(line, ((w - line.width) // 2, head_h + STATUS_GAP))
    return im
