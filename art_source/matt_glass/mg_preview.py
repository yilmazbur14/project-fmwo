"""Previews of the Glass Row / Deafening Yell art, written ONLY to the scratch folder (mg_base.SCRATCH):

    python mg_preview.py

    glass_sheets_4x.png      every Matt frame at 4x, labelled with its timing
    glass_player_8x.png      the player's 18 columns (row 1) at 8x
    glass_in_arena_3x.png    game scale: Matt at his station and the player on row F, on the mat
    matt_stomp.gif, matt_fury.gif, matt_yell_up.gif, player_*.gif   the timings as the plan sets them
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mg_base as M  # noqa: E402
from mg_base import B, F  # noqa: E402
import mg_matt as MM  # noqa: E402
import mg_player as P  # noqa: E402
import mi_view as V  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT = M.SCRATCH


def frames(fn):
    return [B.image(F.px_of(f)) for f in fn()]


def main():
    os.makedirs(OUT, exist_ok=True)
    stomp, fury, yell = frames(MM.stomp_figs), frames(MM.fury_figs), frames(MM.yell_up_figs)
    sheets = [
        ('matt_stomp', stomp, ['rising 0.15', 'KNEE HIGH (tell) 0.30', 'SLAM 0.08', 'recoil hold']),
        ('matt_fury', fury, ['L up 0.08', 'L SLAM 0.08', 'R up 0.08', 'R SLAM 0.08']),
        ('matt_yell_up', yell, ['breath 0.25', 'tipped 0.25', 'YELL 0.06', 'YELL 0.06', 'YELL 0.06']),
    ]
    rows = [V.label(V.frames_row(fr, 4, labels), name) for name, fr, labels in sheets]
    V.col(rows, gap=10).save(os.path.join(OUT, 'glass_sheets_4x.png'))

    cols = P.columns()
    cards = [V.label(V.up(P.image(px), 8), '%d %s %s' % (c, name, t)) for c, name, px, t in cols]
    V.col([V.row(cards[:9], gap=6), V.row(cards[9:], gap=6)], gap=6).save(os.path.join(OUT, 'glass_player_8x.png'))

    V.gif(stomp, os.path.join(OUT, 'matt_stomp.gif'), 3, [150, 300, 80, 900])
    V.gif(fury * 4, os.path.join(OUT, 'matt_fury.gif'), 3, [80] * 16)
    V.gif(yell[:2] + yell[2:] * 8, os.path.join(OUT, 'matt_yell_up.gif'), 3, [250, 250] + [60] * 24)
    pim = {c: P.image(px) for c, name, px, t in cols}
    V.gif([pim[0], pim[1]] * 4, os.path.join(OUT, 'player_rooted.gif'), 6, [200] * 8)
    V.gif([pim[c] for c in (0, 2, 3, 4, 5, 0, 1)], os.path.join(OUT, 'player_knock.gif'), 6,
          [400, 120, 60, 80, 80, 200, 400])
    V.gif([pim[6]] + [pim[c] for c in (7, 8, 9)] * 5 + [pim[10], pim[11]], os.path.join(OUT, 'player_ears_resist.gif'), 6,
          [80] + [70] * 15 + [120, 800])
    V.gif([pim[c] for c in (12, 13, 14, 15)] * 3, os.path.join(OUT, 'player_dizzy.gif'), 6, [140] * 12)
    V.gif([pim[0], pim[16], pim[17], pim[0]], os.path.join(OUT, 'player_glass.gif'), 6, [400, 100, 200, 600])

    # game scale: the screen from x 660-1260, y 40-640 at native texels (the mat and every sprite
    # are drawn at 3x), Matt's feet at his station (960, 350), the player's on row F (960, 472)
    mat = Image.open(V.MAT).convert('RGBA')
    tile = mat.crop((150, 60, 350, 260))

    def panel(matt_im, player_im, title):
        g = Image.new('RGBA', (200, 200))
        g.paste(tile, (0, 0))
        ov = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        x0, x1 = (677 - 660) // 3, (1241 - 660) // 3
        d.rectangle([x0, (350 - 40) // 3, x1, 200], fill=(179, 182, 242, 26))
        g.alpha_composite(ov)
        g.alpha_composite(player_im, ((960 - 660) // 3 - 16, (472 - 40) // 3 - 28))
        g.alpha_composite(matt_im, ((960 - 660) // 3 - 48, (350 - 40) // 3 - 95))
        return V.label(g.resize((600, 600), Image.NEAREST), title)

    mock = V.col([
        V.row([panel(stomp[1], pim[0], 'TELL: knee high / player rooted'),
               panel(stomp[2], pim[2], 'SLAM / player brace'),
               panel(fury[1], pim[1], 'FURY: left slam / rooted B')], gap=10),
        V.row([panel(yell[1], pim[6], 'DEAFEN TELL: tipped / ears in'),
               panel(yell[3], pim[8], 'DEAFEN: yell up / ears'),
               panel(fury[2], pim[17], 'fury right up / glass hop')], gap=10),
    ], gap=10)
    mock.save(os.path.join(OUT, 'glass_in_arena_3x.png'))
    for f in sorted(os.listdir(OUT)):
        if f.startswith(('glass_', 'matt_', 'player_')) and f.endswith(('.png', '.gif')):
            print(os.path.join(OUT, f))


if __name__ == '__main__':
    main()
