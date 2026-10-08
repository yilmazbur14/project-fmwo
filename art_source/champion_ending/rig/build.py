"""Builds every approval file into the approval folder (and nowhere else - common.save guards it).

    python build.py
"""
import json
import sys
sys.dont_write_bytecode = True
from PIL import Image
from common import save, stats, paste, grid_to_image, PROP
import trophy as T
import burak as BK
import champion as C
import fx as FX
import fx_screen as FS

TAKES = ('A', 'B')


def hstrip(frames):
    w, h = frames[0].size
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


# ---------------------------------------------------------------- trophy waiting on the stand
IDLE = [  # (shine phase or None, spark or None, seconds)
    (None, None, 0.60), (3, None, 0.05), (8, None, 0.05), (13, None, 0.05), (18, None, 0.05),
    (23, None, 0.05), (None, None, 0.35), (None, 'small', 0.06), (None, 'big', 0.08),
    (None, 'small', 0.06), (None, None, 0.45),
]


def stand_cell(take=None, shine=None, spark=None):
    """The stand (and the waiting cup) in the champion sheet's 40x64 registration."""
    ox, oy = C.BODY_AT
    cell = Image.new('RGBA', C.CELL, (0, 0, 0, 0))
    paste(cell, T.stand().image(), (ox + C.STAND_AT[0], oy + C.STAND_AT[1]))
    if take:
        tx, ty = C.trophy_xy(take, 'arrive')
        tx, ty = ox + tx, oy + ty
        paste(cell, C.trophy_image(take, shine), (tx, ty))
        if spark:
            fxl = Image.new('RGBA', C.CELL, (0, 0, 0, 0))
            sx, sy = C.SPARK_AT[take]
            FX.spark(fxl, spark, tx + sx, ty + sy)
            cell.alpha_composite(fxl)
    return cell


def build_props():
    out = {}
    for take in TAKES:
        save(T.trophy(take).image(), f'trophy/trophy_{take}.png')
        frames = [stand_cell(take, sh, sp) for sh, sp, _ in IDLE]
        save(hstrip(frames), f'trophy/trophy_stand_idle_{take}.png')
        out[take] = frames
    save(stand_cell(None), 'trophy/stand_empty.png')
    return out


def build_champion():
    sheets = {}
    for take in TAKES:
        frames = [C.compose(take, n) for n in BK.ORDER]
        save(hstrip(frames), f'champion/champion_lift_{take}.png')
        # the layers, for the layered .aseprite (and for a coder who wants the cup separate)
        lay = {k: [] for k in ('burak', 'stand', 'trophy', 'grip', 'fx')}
        for n in BK.ORDER:
            for k, im in C.layers(take, n).items():
                lay[k].append(im)
        for k, fr in lay.items():
            save(hstrip(fr), f'champion/layers_{take}/{k}.png')
        sheets[take] = frames
    return sheets


def build_fx():
    save(hstrip(FS.confetti_burst()), 'fx/confetti_burst.png')
    save(hstrip(FS.confetti_rain()), 'fx/confetti_rain.png')
    save(hstrip(FS.spot_sweep()), 'fx/spot_sweep.png')
    save(hstrip(FS.lift_flash()), 'fx/lift_flash.png')


def check_arrive_swap(sheets, idle):
    """Frame 0 of the champion sheet must equal the player's own idle_down cell drawn over the
    waiting trophy sprite, so the swap at the mark is invisible."""
    import burak
    ox, oy = C.BODY_AT
    res = {}
    for take in TAKES:
        comp = Image.new('RGBA', C.CELL, (0, 0, 0, 0))
        player = Image.new('RGBA', C.CELL, (0, 0, 0, 0))
        player.paste(burak.sheet_cell(0, 0), (ox, oy))
        comp.alpha_composite(player)            # the player is behind the stand (y-sort)
        comp.alpha_composite(idle[take][0])
        res[take] = comp.tobytes() == sheets[take][0].tobytes()
    return res


if __name__ == '__main__':
    idle = build_props()
    sheets = build_champion()
    build_fx()
    swap = check_arrive_swap(sheets, idle)
    print('arrive swap pixel-identical:', swap)
    for take in TAKES:
        # Burak's own pixels, measured on his layer only
        b = Image.open(f'../champion/layers_{take}/burak.png')
        g = Image.open(f'../champion/layers_{take}/grip.png')
        both = Image.new('RGBA', b.size); both.alpha_composite(b); both.alpha_composite(g)
        print(take, 'burak layer', stats(both), '| full sheet', stats(Image.open(f'../champion/champion_lift_{take}.png')))
