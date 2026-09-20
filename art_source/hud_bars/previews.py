"""HUD previews at 1920x1080 over a real arena frame.

The point of these is FOOTPRINT. The boss block grows from y 36..114 to y 22..138,
and a stacked pair reaches y 174, so the user needs to see how much of the top of
the arena it eats before the flag flips.

Renders both nameplate arrangements (centred over the bar's top rim, and riding
the bar's left end as a tab) at full / 60% / 20% health, plus the two-bar
Greyson + Computah case.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image
from barlib import up3, canvas, rgba, KEY
import boss_bar as BB
import player_hp as PH
import plates as PL
from vs_card import bosses

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
UI = PROJ + "/Assets/UI/"
SW, SH = 1920, 1080

# --- layout, whole screen px, straight off the build plan -----------------
BAR_AT = (720, 60)
BAR_WH = (480, 54)
FILL_AT = (732, 72)
FILL_WH = (456, 36)
ROW_PITCH = 60
PLATE_CENTRED = (816, 22)
PLATE_TAB = (702, 30)
TRAY_AT = (10, 954)
HEART_AT = [(34, 963), (112, 963), (190, 963)]
STAMINA_AT = (10, 1026)


def arena():
    bg = Image.open(PROJ + "/Assets/Environment/arena_ringside.png").convert("RGBA")
    mat = Image.open(PROJ + "/Assets/Environment/arena_mat.png").convert("RGBA")
    bg.alpha_composite(mat, ((640 - mat.width) // 2, 360 - mat.height - 10))
    return up3(bg)


def boss_row(img, key, ratio, y, low=False):
    b = bosses.by_key(key)
    img.alpha_composite(up3(BB.frame_back()), (BAR_AT[0], y))
    fill = BB.fill(b["ramp"], b["mark"][1])
    w = max(0, int(round(FILL_WH[0] * ratio)))
    if w:
        img.alpha_composite(up3(fill).crop((0, 0, w, FILL_WH[1])), (FILL_AT[0], y + 12))
    if low:
        pulse = up3(BB.low_pulse()[1])
        if w:
            img.alpha_composite(pulse.crop((0, 0, w, FILL_WH[1])), (FILL_AT[0], y + 12))
    over = BB.frame_over_low() if low else BB.frame_over()
    img.alpha_composite(up3(over), (BAR_AT[0], y))


OVERLAP = 10          # the plate laps the bar's top rim by this much


def nameplate(img, key, mode, y):
    lines = PL.plate_lines(key)
    tall = len(lines) > 1
    p = up3(PL.plate(tall))
    # Bottom of the plate sits OVERLAP px inside the bar's top rim, so the two
    # read as one object. Deriving the top from the plate height is what keeps
    # the single and the tall (pair) plate consistent.
    if mode == "centred":
        at = (PLATE_CENTRED[0], y + OVERLAP - p.height)
    else:
        at = (BAR_AT[0] - 18, y + OVERLAP + 6 - p.height)
    img.alpha_composite(p, at)
    img.alpha_composite(up3(PL.emblem(key)), (at[0] + 9, at[1] + 9))
    ty = at[1] + (12 if tall else 9)
    for line in lines:
        im, _ = PL.name_art(line)
        im3 = up3(im)
        img.alpha_composite(im3, (at[0] + 54 + (216 - im3.width) // 2, ty))
        ty += im3.height + 6


def player_column(img, halves=6, warn=False):
    img.alpha_composite(up3(PH.tray(2 if warn else 0)), TRAY_AT)
    full, half = halves // 2, halves % 2
    for i, at in enumerate(HEART_AT):
        if i < full:
            h = PH.heart_full()
        elif i == full and half:
            h = PH.heart_half()
        else:
            h = PH.heart_empty()
        img.alpha_composite(up3(h), at)
    for n in ("stamina_bar_frame_3x.png",):
        if os.path.exists(UI + n):
            img.alpha_composite(Image.open(UI + n).convert("RGBA"), STAMINA_AT)


PAIR_BAR_Y = 78       # a two-line plate cannot clear the screen at y=60


def scene(key, ratio, mode, rows=None, halves=6):
    img = arena()
    rows = rows or [(key, ratio)]
    top = PAIR_BAR_Y if len(rows) > 1 else BAR_AT[1]
    for i, (k, r) in enumerate(rows):
        y = top + i * ROW_PITCH
        boss_row(img, k, r, y, low=(r <= 0.25))
    nameplate(img, key, mode, top)
    player_column(img, halves, warn=(halves <= 1))
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    jobs = []
    for mode in ("centred", "tab"):
        for label, ratio, halves in (("full", 1.0, 6), ("60", 0.6, 4), ("20", 0.2, 1)):
            jobs.append(("hud_%s_eric_%s" % (mode, label), dict(key="eric", ratio=ratio, mode=mode, halves=halves)))
        jobs.append(("hud_%s_pair_greyson" % mode,
                     dict(key="greyson", ratio=0.75, mode=mode, halves=5,
                          rows=[("greyson", 0.75), ("computah", 0.4)])))
    for name, kw in jobs:
        p = os.path.join(out, name + ".png")
        scene(**kw).convert("RGB").save(p)
        print(p)
