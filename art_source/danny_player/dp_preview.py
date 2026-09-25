"""Previews of player_sumo_push, written ONLY to a scratch folder (never Assets/):

    python dp_preview.py [out_dir]     # default: the session scratchpad's danny_anims/player/

    player_sumo_push_strip_3x.png   row 1 (the back view) at game scale 3x, labelled with timings
    player_sumo_push_8x.png         the same at 8x on a texel grid, soles row and centre column marked
    player_sumo_push_mock_3x.png    game scale against Danny's idle f0 (176x144, feet (88,143), 3x) on the
                                    mat: the clinch frames with the gloves on his apron, then the push-out
    push_win.gif, push_lose.gif     the two endings at the suggested timings, 3x

Reads the project's assets; writes nothing else.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dp_player as P  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCRATCH = (r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
           r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\danny_anims\player')
MAT = os.path.join(P.ROOT, 'Assets', 'Environment', 'arena_mat.png')
DANNY_IDLE = os.path.join(P.ROOT, 'Assets', 'Characters', 'Danny', 'Sumo', 'danny_sumo_idle.png')
BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
INK = (225, 225, 232, 255)
LABELS = ['0 set 0.20', '1 strain A', '2 strain B', '3 shove (hold)', '4 skid A', '5 skid B',
          '6 launched 0.30', '7 on back (hold)']


def up(im, s, grid=False):
    base = Image.new('RGBA', im.size, BG)
    base.alpha_composite(im)
    big = base.resize((im.width * s, im.height * s), Image.NEAREST)
    if grid:
        d = ImageDraw.Draw(big, 'RGBA')
        for gx in range(0, big.width, s):
            d.line([(gx, 0), (gx, big.height)], fill=(255, 255, 255, 36 if (gx // s) % 4 == 0 else 10))
        for gy in range(0, big.height, s):
            d.line([(0, gy), (big.width, gy)], fill=(255, 255, 255, 36 if (gy // s) % 4 == 0 else 10))
        d.line([(0, 29 * s - 1), (big.width, 29 * s - 1)], fill=(255, 90, 90, 140))
        d.line([(16 * s, 0), (16 * s, big.height)], fill=(90, 255, 90, 70))
    return big


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
    return [P.image(P.g(grid)) for name, grid in P.PUSH]


def mock(fr):
    """Native texels (every sprite and the mat are drawn at 3x in game), then x3. Danny's feet on
    (100, 150) of a 200x200 mat patch; the player on his centre line, his strain gloves' top edge on
    Danny's apron at Danny row 128, which puts the player's soles 11 texels (33 px) in front of Danny's."""
    mat = Image.open(MAT).convert('RGBA')
    danny = Image.open(DANNY_IDLE).convert('RGBA').crop((0, 0, 176, 144))
    fx, fy = 100, 150
    glove_top = fy - 143 + 128                     # Danny's apron row in the patch
    clinch_sole = glove_top + (28 - 3)             # strain gloves' top is row 3, soles row 28

    def panel(im, sole, title, dx=0):
        g = Image.new('RGBA', (200, 212))
        g.paste(mat.crop((180, 40, 380, 252)), (0, 0))
        g.alpha_composite(danny, (fx - 88, fy - 143))
        g.alpha_composite(im, (fx - 16 + dx, sole - 28))
        return label(g.resize((600, 636), Image.NEAREST), title, pad=16)

    return col([
        row([panel(fr[0], clinch_sole, 'SET: the lock-up (pre-contact)'),
             panel(fr[1], clinch_sole, 'STRAIN A: gloves on the apron'),
             panel(fr[3], clinch_sole, 'SHOVE: he wins (steps up-screen)')], gap=8),
        row([panel(fr[4], clinch_sole, 'SKID A: losing ground'),
             panel(fr[6], clinch_sole + 14, 'LAUNCHED: shoved off his feet'),
             panel(fr[7], clinch_sole + 30, 'ON BACK: out, flat on his back')], gap=8),
    ], gap=8)


def gif(path, fr, seq, times, s=3):
    ims = []
    for i in seq:
        base = Image.new('RGBA', (32 * s, 32 * s), BG)
        base.alpha_composite(fr[i].resize((32 * s, 32 * s), Image.NEAREST))
        ims.append(base.convert('P', palette=Image.ADAPTIVE, colors=16))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=times, loop=0, disposal=2)


def main(argv):
    out = os.path.abspath(argv[0]) if argv else SCRATCH
    assets = os.path.normcase(os.path.realpath(os.path.join(P.ROOT, 'Assets')))
    real = os.path.normcase(os.path.realpath(out))
    if real == assets or real.startswith(assets + os.sep):
        print('refused: previews never go into Assets/')
        return 2
    os.makedirs(out, exist_ok=True)
    fr = frames()
    row([label(up(im, 3), t) for im, t in zip(fr, LABELS)]).save(
        os.path.join(out, 'player_sumo_push_strip_3x.png'))
    col([row([label(up(im, 8, grid=True), t) for im, t in zip(fr[:4], LABELS[:4])]),
         row([label(up(im, 8, grid=True), t) for im, t in zip(fr[4:], LABELS[4:])])]).save(
        os.path.join(out, 'player_sumo_push_8x.png'))
    mock(fr).save(os.path.join(out, 'player_sumo_push_mock_3x.png'))
    gif(os.path.join(out, 'push_win.gif'), fr, [0] + [1, 2] * 5 + [3], [200] + [100] * 10 + [1200])
    gif(os.path.join(out, 'push_lose.gif'), fr, [0] + [1, 2] * 2 + [4, 5] * 5 + [6, 7],
        [200] + [100] * 4 + [80] * 10 + [300, 1500])
    for f in sorted(os.listdir(out)):
        if f.startswith(('player_sumo_push_', 'push_')) and f.endswith(('.png', '.gif')):
            print(os.path.join(out, f))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
