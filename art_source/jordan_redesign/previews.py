"""Approval previews for Jordan's redesign. Writes ONLY to the preview folder given (the session
scratchpad), never into Assets/.

    python previews.py <out_dir>

  before_after_5x.png    the old jordan.png beside the two new frames, all at 5x
  scale_on_mat_3x.png    the new frames at game scale (3x) on the arena mat, beside the player
                         sprite and a funko figure, which the game also draws at 3x
  refs_strip.png         the four photo references beside the new frames
  face_8x.png            the face close-up at 8x, both frames, so the patchy beard can be judged
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402
import jordan  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
REFS = os.environ.get('JORDAN_REFS', '')
DARK = (10, 10, 12, 255)
BG = kit.BG


def asset(*parts):
    return Image.open(os.path.join(ROOT, 'Assets', *parts)).convert('RGBA')


def label(im, text, pad=18, col=(220, 220, 228, 255)):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 3), text, fill=col)
    return out


def before_after(f0, f1):
    old = asset('Characters', 'Jordan', 'jordan.png')
    # the old sprite is 64x64; seat it on a 96x96 tile with its feet on the bottom row, centred
    tile = Image.new('RGBA', (96, 96), (0, 0, 0, 0))
    tile.alpha_composite(old, (16, 32))
    a = label(kit.up(tile, 5), 'before: jordan.png (64x64)')
    b = label(kit.up(f0, 5), 'after: frame 0 idle (96x96)')
    c = label(kit.up(f1, 5), 'after: frame 1 fist-pump')
    return kit.row([a, b, c], gap=10)


def scale_on_mat(f0, f1):
    """Everything at the game's 3x: the mat, Jordan, the player (32x32 frames) and a funko (24x24)."""
    mat = asset('Environment', 'arena_mat.png')
    player = asset('Characters', 'MainPlayer', 'player_4dir_sheet.png').crop((0, 64, 32, 96))  # row 2: facing left, toward him
    funko = asset('Characters', 'Jordan', 'Funkos', 'funko_plumber.png').crop((24, 0, 48, 24))
    w, h = 300, 150
    scene = mat.crop((140, 70, 140 + w, 70 + h)).copy()
    floor = 128                                     # the row everyone stands on
    scene.alpha_composite(f0, (20, floor - 96))
    scene.alpha_composite(f1, (112, floor - 96))
    scene.alpha_composite(funko, (206, floor - 24))
    scene.alpha_composite(player, (244, floor - 32))
    return label(kit.up(scene, 3), 'game scale (3x) on the arena mat: frame 0, frame 1, a funko figure, the player')


def refs_strip(f0, f1, height=384):
    ims = []
    for name in ('10.webp', '11.png', '12.webp', '13.webp'):
        p = os.path.join(REFS, name)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGBA')
        s = height / im.height
        ims.append(label(im.resize((max(1, int(im.width * s)), height), Image.LANCZOS), name))
    ims.append(label(kit.up(f0, 4), 'frame 0'))
    ims.append(label(kit.up(f1, 4), 'frame 1'))
    return kit.row(ims, gap=10)


def face(f0, f1):
    box = (34, 5, 62, 41)
    a = label(kit.up(f0.crop(box), 8), 'face 8x: frame 0')
    b = label(kit.up(f1.crop(box), 8), 'face 8x: frame 1')
    return kit.row([a, b], gap=10)


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    f0, f1 = jordan.frames()
    before_after(f0, f1).save(os.path.join(out, 'before_after_5x.png'))
    scale_on_mat(f0, f1).save(os.path.join(out, 'scale_on_mat_3x.png'))
    refs_strip(f0, f1).save(os.path.join(out, 'refs_strip.png'))
    face(f0, f1).save(os.path.join(out, 'face_8x.png'))
    print('previews written to', out)
