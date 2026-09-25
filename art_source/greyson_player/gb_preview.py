"""Previews of player_final_brawl, written ONLY to a scratch folder (never Assets/):

    python gb_preview.py [out_dir]     # default: the session scratchpad's greyson_fight/player/

    player_final_brawl_4x.png          the ten poses (row 1, the back view) at 4x, labelled
    player_final_brawl_mock_3x.png     game scale: tight below Greyson's approved sprite
                                       (greyson_redesign f0, 112x112, feet (56,111), 3x) on the mat,
                                       plus the existing finisher uppercut at the same spot
    brawl_guard.gif, brawl_slips.gif, brawl_parry_hit.gif   the moves at the suggested timings, 4x

Reads the project's assets; writes nothing else.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gb_player as G  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCRATCH = (r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
           r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\greyson_fight\player')
MAT = os.path.join(G.ROOT, 'Assets', 'Environment', 'arena_mat.png')
GREYSON = os.path.join(G.ROOT, 'Assets', 'Characters', 'Greyson', 'greyson_redesign.png')
UPPERCUT = os.path.join(G.PLAYER_DIR, 'player_uppercut.png')
BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
INK = (225, 225, 232, 255)
LABELS = ['0 guard', '1 guard bounce', '2 slip L half', '3 slip L full', '4 slip R half', '5 slip R full',
          '6 parry snap', '7 parry absorb', '8 hit lands', '9 hit reel']
# the player's soles this many texels below Greyson's in the mock: in front of him, overlapping his shins
GAP = 12


def up(im, s):
    base = Image.new('RGBA', im.size, BG)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def label(im, text, pad=14):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((2, 1), text, fill=INK)
    return out


def row(ims, gap=6):
    out = Image.new('RGBA', (sum(i.width for i in ims) + gap * (len(ims) - 1), max(i.height for i in ims)), DARK)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def col(ims, gap=6):
    out = Image.new('RGBA', (max(i.width for i in ims), sum(i.height for i in ims) + gap * (len(ims) - 1)), DARK)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def frames():
    return [G.image(G.g(grid)) for name, grid in G.FRAMES]


def uppercut_frame(i):
    """The shipped finisher uppercut's frame i (48x64, facing right). Its bottom 32x32 lines up with the
    player's cell (FinisherArtLayout offset (0,-16)), so it goes at cell (-8, -32)."""
    sheet = Image.open(UPPERCUT).convert('RGBA')
    return sheet.crop((48 * i, 0, 48 * i + 48, 64))


def mock(fr):
    """Native texels (the mat and every sprite are drawn at 3x in game), then x3. Greyson's feet on
    (80, 150) of a 160x170 mat patch; the player on his centre line, soles GAP texels below his."""
    mat = Image.open(MAT).convert('RGBA')
    grey = Image.open(GREYSON).convert('RGBA').crop((0, 0, 112, 112))
    fx, fy = 80, 150

    def panel(sprite, title, big=False):
        g = Image.new('RGBA', (160, 170))
        g.paste(mat.crop((200, 60, 360, 230)), (0, 0))
        g.alpha_composite(grey, (fx - 56, fy - 111))
        if big:
            g.alpha_composite(sprite, (fx - 16 - 8, fy + GAP - 28 - 32))
        else:
            g.alpha_composite(sprite, (fx - 16, fy + GAP - 28))
        return label(g.resize((480, 510), Image.NEAREST), title, pad=16)

    brawl = [panel(fr[0], 'GUARD'), panel(fr[3], 'SLIP LEFT (full)'), panel(fr[5], 'SLIP RIGHT (full)'),
             panel(fr[6], 'PARRY (snap)'), panel(fr[8], 'HIT (lands)')]
    upper = [panel(uppercut_frame(i), 'existing uppercut f%d%s' % (i, t), big=True)
             for i, t in ((1, ' (charge)'), (4, ' (launch)'), (6, ' (rise)'), (7, ' (apex)'))]
    return col([row(brawl, gap=8), row(upper, gap=8)], gap=8)


def gif(path, fr, seq, times, s=4):
    ims = []
    for i in seq:
        base = Image.new('RGBA', (32 * s, 32 * s), BG)
        base.alpha_composite(fr[i].resize((32 * s, 32 * s), Image.NEAREST))
        ims.append(base.convert('P', palette=Image.ADAPTIVE, colors=16))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=times, loop=0, disposal=2)


def main(argv):
    out = os.path.abspath(argv[0]) if argv else SCRATCH
    assets = os.path.normcase(os.path.realpath(os.path.join(G.ROOT, 'Assets')))
    real = os.path.normcase(os.path.realpath(out))
    if real == assets or real.startswith(assets + os.sep):
        print('refused: previews never go into Assets/')
        return 2
    os.makedirs(out, exist_ok=True)
    fr = frames()
    cards = [label(up(im, 4), t) for im, t in zip(fr, LABELS)]
    col([row(cards[:5]), row(cards[5:])]).save(os.path.join(out, 'player_final_brawl_4x.png'))
    mock(fr).save(os.path.join(out, 'player_final_brawl_mock_3x.png'))
    gif(os.path.join(out, 'brawl_guard.gif'), fr, [0, 1] * 6, [160] * 12)
    gif(os.path.join(out, 'brawl_slips.gif'), fr, [0, 1, 0, 2, 3, 2, 0, 1, 0, 4, 5, 4, 0, 1],
        [160, 160, 160, 40, 300, 60, 160, 160, 160, 40, 300, 60, 160, 160])
    gif(os.path.join(out, 'brawl_parry_hit.gif'), fr, [0, 1, 0, 6, 7, 0, 1, 0, 8, 9, 0, 1],
        [160, 160, 160, 50, 120, 160, 160, 160, 100, 250, 160, 160])
    for f in sorted(os.listdir(out)):
        if f.startswith(('player_final_brawl_', 'brawl_')) and f.endswith(('.png', '.gif')):
            print(os.path.join(out, f))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
