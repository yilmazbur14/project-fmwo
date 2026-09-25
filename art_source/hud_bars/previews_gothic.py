"""Gothic boss bar + daze meter previews at 1920x1080 over a real arena frame.

Renders, in one pass:
  _gothic_full / _60 / _20      the three fill states, bar and daze meter together
  _gothic_pair                  the two-bar Greyson + Computah case
  _gothic_mixed                 THE QUESTION: gothic top-centre, brass player HUD
                                bottom-left, so the user can see whether two
                                languages on one screen read as hierarchy or as
                                two kits that do not match.

Layout constants are previews.py's, unchanged, so the footprint comparison
against the brass version is like for like.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image
from barlib import up3
import gothic as G
import export_gothic as EG
import plates as PL
from vs_card import bosses

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
UI = PROJ + "/Assets/UI/"
SW, SH = 1920, 1080
# previews.py put the bar's rail top at y=60.  The gothic block is taller: the
# plate now sits ABOVE the crest instead of lapping the rail, so it needs
# CREST_OVER*3 = 21px of crest plus its own 48px above that line.  At y=60 the
# plate's top landed at -7 and was clipped off the screen.  y=84 is the smallest
# value that fits the whole block, and the footprint is printed by this script.
# 100, not 84: the PAIR carries the tall 26px plate (78 at 3x), and at 84 its
# plate top landed at -13.  100 is the smallest value that fits both cases.
BAR_AT = (720, 100)         # 3x screen px: the bar's TOP RAIL
ROW_PITCH = 60
TRAY_AT = (10, 954)
HEART_AT = [(34, 963), (112, 963), (190, 963)]
STAMINA_AT = (10, 1026)
GAUGE_GAP = 6               # 3x px between the bar's bottom rail and the daze rail


def arena():
    bg = Image.open(PROJ + "/Assets/Environment/arena_ringside.png").convert("RGBA")
    mat_p = PROJ + "/Assets/Environment/arena_mat.png"
    if os.path.exists(mat_p):
        mat = Image.open(mat_p).convert("RGBA")
        bg.alpha_composite(mat, ((640 - mat.width) // 2, 360 - mat.height - 10))
    return up3(bg)


def boss_block(img, key, ratio, y, low=False, daze=None, show_plate=True):
    """One boss: plate, bar, crest, and (when given) the daze rail beneath."""
    b = bosses.by_key(key)
    lines = PL.plate_lines(key)
    try:
        em = PL.emblem(key, G.EMBLEM)
    except Exception:
        em = None
    p3 = up3(G.plate_named(key, lines, em, low)) if show_plate else None
    # the boss's SHIPPED fill, not the reference crimson, so the preview is
    # what the coder gets when the flag flips
    fill = EG.gothic_fill(b["ramp"], b["mark"][1], as_is=b.get("fill_as_is", False),
                          trim=b.get("fill_trim"))
    bar = G.compose(ratio, low, fill=fill, with_crest=True)
    b3 = up3(bar)
    # the bar's own top rail sits CREST_OVER texels down inside `bar`
    bar_top = y - G.CREST_OVER * 3
    # The plate sits ABOVE the crest, not lapping the bar's rail.  Lapping the
    # rail put the plate's centre exactly where the crest's mask and horns rise,
    # and the crest ate the name.  Both are centred on the bar, so they cannot
    # share that column - the plate goes above and the crest's horns rise to
    # touch its underside, which reads as one ornament linking the two.
    if p3 is not None:
        img.alpha_composite(p3, (BAR_AT[0] + (480 - p3.width) // 2, bar_top - p3.height + 2))
    img.alpha_composite(b3, (BAR_AT[0], bar_top))
    # `bar` carries CREST_OVER texels of crest overhang above AND below the
    # frame, so the frame's real bottom rail is that much above the image edge.
    # Hanging the daze rail off b3.height put it a full overhang too low.
    rail_bottom = bar_top + b3.height - G.CREST_OVER * 3
    if daze is not None:
        g3 = up3(G.compose_gauge(daze, low))
        img.alpha_composite(g3, (BAR_AT[0] + (480 - g3.width) // 2,
                                 rail_bottom + GAUGE_GAP))
        rail_bottom += GAUGE_GAP + g3.height
    return rail_bottom


def player_hud(img):
    """The shipped BRASS player HUD, untouched - this is the half of the
    question that is not changing."""
    def load(n):
        p = UI + n + "_3x.png"
        return Image.open(p).convert("RGBA") if os.path.exists(p) else None
    tray = load("player_hp_tray")
    if tray:
        img.alpha_composite(tray, TRAY_AT)
    heart = load("player_hp_heart_full")
    if heart:
        for at in HEART_AT:
            img.alpha_composite(heart, at)
    for n in ("stamina_bar_frame", "stamina_bar_fill"):
        im = load(n)
        if im is None:
            continue
        off = (0, 0) if n.endswith("frame") else (21, 15)
        img.alpha_composite(im, (STAMINA_AT[0] + off[0], STAMINA_AT[1] + off[1]))


def shot(name, out, rows, with_player=False):
    img = arena()
    y = BAR_AT[1]
    for row in rows:
        key, ratio, low, daze = row[:4]
        show_plate = row[4] if len(row) > 4 else True
        bottom = boss_block(img, key, ratio, y, low, daze, show_plate)
        # The NEXT row's plate (when it has one) must clear this row's bar, so
        # the pitch is derived from the plate height rather than a flat 60.
        y = bottom + 8 + (G.CREST_OVER * 3 + up3(G.plate(False)).height - 2
                          if len(rows) > 1 and show_plate is False else 0)
        if len(rows) > 1:
            y = bottom + 8 + G.CREST_OVER * 3
    if with_player:
        player_hud(img)
    img.convert("RGB").save(os.path.join(out, name + ".png"))
    print("  %-26s 1920x1080" % name)
    return img


def footprint():
    """Print the block's real extent so the coder has the offsets, not a guess."""
    plate_h = up3(G.plate(True)).height
    top = BAR_AT[1] - G.CREST_OVER * 3 - plate_h + 2
    bar_bottom = BAR_AT[1] + G.FH * 3
    gauge_bottom = bar_bottom + GAUGE_GAP + G.GH * 3
    print("  footprint (single): plate top y=%d, bar rail y=%d..%d, daze y=%d..%d"
          % (BAR_AT[1] - G.CREST_OVER * 3 - up3(G.plate(False)).height + 2,
             BAR_AT[1], bar_bottom, bar_bottom + GAUGE_GAP, gauge_bottom))
    print("  footprint (pair)  : plate top y=%d, second bar adds %d, total to y=%d"
          % (top, ROW_PITCH + G.FH * 3, gauge_bottom + ROW_PITCH + G.FH * 3))


def run(out):
    os.makedirs(out, exist_ok=True)
    footprint()
    shot("_gothic_full", out, [("eric", 1.00, False, 0.20)])
    shot("_gothic_60", out, [("eric", 0.60, False, 0.55)])
    shot("_gothic_20", out, [("eric", 0.20, True, 0.95)])
    # One daze meter for the pair, under BOTH bars - it is the fight's gauge,
    # not a per-boss one, so hanging it off the first row put it in the middle.
    # ONE plate for the pair, not one per boss.  Greyson's plate_lines already
    # returns both names - that is what boss_plate_name_greyson_pair is - so the
    # second row carries no plate at all.  Giving it one put a COMPUTAH plate
    # straight over Greyson's fill.
    shot("_gothic_pair", out, [("greyson", 0.85, False, None, True),
                               ("computah", 0.45, False, 0.35, False)])
    shot("_gothic_mixed", out, [("eric", 0.60, False, 0.55)], with_player=True)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else ".")
