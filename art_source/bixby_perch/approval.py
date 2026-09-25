"""The approval still (scratch only): key poses on the arena at game scale with him on the middle of the
top rope (x 960), the rope and its gate doorway drawn over him as the arena draws them, the boss bar and
name plate marked (the fight fades them while he is perched), the player for scale, and on the breath a
rough sketch of the 130-degree cone the effects artist will draw.

    python approval.py
"""
import math

from PIL import Image, ImageDraw

import arena_bg
import mouths
import sheet
import stage
from common import SCRATCH, ANCHOR, ROPE

CONE_HALF = 65.0
INFERNO_AREA = (105, 105, 1815, 975)       # BixbyInfernoArtLayout.INFERNO_AREA, as x0, y0, x1, y1


def to_screen(pt):
    return (stage.PERCH_X + (pt[0] - ANCHOR[0]) * 3, stage.PERCH_Y + (pt[1] - ANCHOR[1]) * 3)


def cone_mask(apex, half=CONE_HALF, area=INFERNO_AREA):
    ax, ay = apex
    tn = math.tan(math.radians(half))
    m = Image.new('L', (1920, 1080), 0)
    px = m.load()
    x0, y0, x1, y1 = area
    for y in range(max(y0, int(ay)), y1):
        w = (y - ay) * tn
        for x in range(max(x0, int(ax - w)), min(x1, int(ax + w) + 1)):
            px[x, y] = 255
    return m


def coverage(apex, half=CONE_HALF, area=INFERNO_AREA):
    ax, ay = apex
    tn = math.tan(math.radians(half))
    x0, y0, x1, y1 = area
    inside = 0
    for y in range(y0, y1):
        if y < ay:
            continue
        w = (y - ay) * tn
        inside += max(0, min(x1, ax + w) - max(x0, ax - w))
    return inside / float((x1 - x0) * (y1 - y0))


def label(d, xy, text, fill=(255, 255, 255, 255)):
    x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0, 255))
    d.text((x, y), text, fill=fill)


def scene(frame, cone_apex=None, player_at=(1180, 760), player_facing=1):
    bg = arena_bg.arena(ropes=False)
    if cone_apex is not None:
        # the cone the effects artist carries across the arena, sketched on the floor under him
        m = cone_mask(cone_apex)
        glow = Image.new('RGBA', (1920, 1080), (255, 120, 30, 0))
        glow.putalpha(m.point(lambda v: 110 if v else 0))
        bg.alpha_composite(glow)
        over = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        ax, ay = cone_apex
        for sgn in (-1, 1):
            a = math.radians(CONE_HALF)
            L = 1400
            d.line((ax, ay, ax + sgn * math.sin(a) * L, ay + math.cos(a) * L), fill=(255, 210, 90, 230), width=3)
        bg.alpha_composite(over)
    p = stage.player(player_facing)
    bg.alpha_composite(p, (player_at[0] - 48, player_at[1] - 80))
    stage.place(bg, frame)
    arena_bg.top_ropes(bg)
    stage.hud_boxes(bg, alpha=40, outline=235)
    return bg


def annotate(img, title, mouth_pts, apex=None):
    d = ImageDraw.Draw(img)
    for pt, col in zip(mouth_pts, ((255, 255, 0), (0, 255, 255), (255, 0, 255))):
        x, y = to_screen(pt)
        x, y = x + 1, y + 1
        d.line((x - 9, y, x + 9, y), fill=col + (255,), width=2)
        d.line((x, y - 9, x, y + 9), fill=col + (255,), width=2)
    if apex is not None:
        x, y = to_screen(apex)
        d.ellipse((x - 8, y - 8, x + 8, y + 8), outline=(255, 255, 255, 255), width=3)
    label(d, (arena_bg.HUD_BAR[0] + 6, arena_bg.HUD_BAR[1] + 6), 'boss bar (faded while perched)', (255, 200, 200, 255))
    label(d, (arena_bg.HUD_PLATE[0] + 6, arena_bg.HUD_PLATE[1] + 6), 'name plate (faded)', (200, 230, 255, 255))
    label(d, (1260, 112), 'top rope: PERCH_ROPE_ROW %d = screen y 100; doorway x 852..1067' % ROPE)
    label(d, (20, 1040), title, (255, 255, 180, 255))


def build():
    ims = sheet.frames()
    rows, apex = mouths.table()
    panels = []
    for i, title in ((2, 'perch (frame 2)'), (4, 'volley (frame 4)'), (8, 'inhale (frame 8)')):
        sc = scene(ims[i])
        annotate(sc, title, rows[i])
        panels.append(sc.crop((640, 0, 1280, 1080)))
    ap = apex[11]
    ap_screen = to_screen(ap)
    breath = scene(ims[11], cone_apex=ap_screen, player_at=(1690, 330))
    annotate(breath, 'perch_breath (frame 11): cone apex texel %s = screen %s, half-angle %d deg, covers %.0f%% of '
             'INFERNO_AREA' % (ap, tuple(int(v) for v in ap_screen), CONE_HALF, 100 * coverage(ap_screen)),
             rows[11], ap)
    out = Image.new('RGBA', (1920, 2160), (12, 12, 16, 255))
    for j, p in enumerate(panels):
        out.alpha_composite(p, (j * 640, 0))
    d = ImageDraw.Draw(out)
    for j in (1, 2):
        d.line((j * 640, 0, j * 640, 1080), fill=(12, 12, 16, 255), width=4)
    out.alpha_composite(breath, (0, 1080))
    d.line((0, 1080, 1920, 1080), fill=(12, 12, 16, 255), width=4)
    assert out.getextrema()[3][0] == 255, 'the still has see-through pixels'
    out.save(SCRATCH + 'approval.png')
    return out, ap_screen


if __name__ == '__main__':
    out, ap = build()
    print('apex on screen', ap, 'coverage %.1f%%' % (100 * coverage(ap)))
    print('wrote', SCRATCH + 'approval.png')
