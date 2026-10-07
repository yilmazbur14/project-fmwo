"""Approval previews for Jordan v2. Writes ONLY into the folder given (a scratch folder), never into
Assets/ (refused, by realpath).

    python jv2_previews.py <out_dir>

  before_after_4x.png   the approved redesign beside v2, both frames, at 4x
  lineup_game_scale.png v2 on the arena mat at the game's own scale, in screen pixels: the mat and
                        every boss at 3x (Jordan v2 idle and fist-pump, Computah, Matt), the player
                        at 2x, all standing on one floor line
  hair_8x.png           the approved head beside v2's (both frames) at 8x: the greasy hair up close
  pallor_4x.png         v2 with the approved skin beside v2 with the sickly pallor (the one flag in
                        jv2_base, JV2_PALLOR=0, switches it off)
  v2_1x.png             the sheet itself on the preview background, 1:1
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jv2_base as B  # noqa: E402
import jv2_frames as F  # noqa: E402
from jv2_export import _under  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def asset(*parts):
    return Image.open(os.path.join(B.ROOT, 'Assets', *parts)).convert('RGBA')


def approved():
    im = Image.open(B.APPROVED_PNG).convert('RGBA')
    return im.crop((0, 0, 96, 96)), im.crop((96, 0, 192, 96))


def before_after(f0, f1):
    a0, a1 = approved()
    tiles = [B.label(B.up(a0, 4), 'approved: idle'), B.label(B.up(f0, 4), 'v2: idle'),
             B.label(B.up(a1, 4), 'approved: fist-pump'), B.label(B.up(f1, 4), 'v2: fist-pump')]
    return B.row(tiles, gap=10)


def _up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def lineup(f0, f1):
    """Screen pixels: the mat is 565x285 drawn at 3x in ArenaScene; bosses' Sprite2Ds are at scale 3
    with their soles on row 95; the player's body is at scale 2."""
    mat = asset('Environment', 'arena_mat.png')
    cw, ch = 340, 124                       # mat texels shown
    cx0, cy0 = (mat.width - cw) // 2 + 4, 96
    scene = _up(mat.crop((cx0, cy0, cx0 + cw, cy0 + ch)), 3)
    floor = scene.height - 36
    comp = asset('Characters', 'Computah', 'computah_idle.png').crop((0, 0, 96, 96))
    matt = asset('Characters', 'Matt', 'matt.png').crop((0, 0, 96, 96))
    player = asset('Characters', 'MainPlayer', 'player_4dir_sheet.png').crop((0, 0, 32, 32))  # row 0: facing down
    cast = [('player', player, 2), ('Jordan v2 idle', f0, 3), ('Jordan v2 fist-pump', f1, 3),
            ('Computah', comp, 3), ('Matt', matt, 3)]
    x = 24
    draw = ImageDraw.Draw(scene)
    for name, im, s in cast:
        bb = im.getbbox()
        big = _up(im.crop((bb[0], 0, bb[2], im.height)), s)
        feet = (bb[3]) * s                  # the row under the lowest opaque texel
        scene.alpha_composite(big, (x, floor - feet))
        draw.text((x, floor + 8), name, fill=(20, 24, 20, 255))
        x += big.width + 34
    return B.label(scene, 'game scale on the arena mat (screen pixels: mat and bosses 3x, player 2x)')


def hair(f0, f1):
    a0, a1 = approved()
    box = (30, 2, 68, 44)
    tiles = [B.label(B.up(a0.crop(box), 8), 'approved'), B.label(B.up(f0.crop(box), 8), 'v2: idle'),
             B.label(B.up(f1.crop((28, 1, 66, 43)), 8), 'v2: fist-pump')]
    return B.row(tiles, gap=10)


def pallor():
    p0 = F.frame_px(0)
    a = B.image(p0, pal=B.APPROVED_PAL)
    b = B.image(p0, pal=B.PAL if B.PALLOR else dict(B.APPROVED_PAL, **B.PALLOR_SKIN))
    return B.row([B.label(B.up(a, 4), 'v2 with the approved skin'), B.label(B.up(b, 4), 'v2 with the pallor')],
                 gap=10)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out = os.path.abspath(argv[0])
    if _under(out, os.path.join(B.ROOT, 'Assets')):
        raise SystemExit('refusing %s: previews never go into Assets' % out)
    os.makedirs(out, exist_ok=True)
    f0, f1 = F.frames()
    before_after(f0, f1).save(os.path.join(out, 'before_after_4x.png'))
    lineup(f0, f1).save(os.path.join(out, 'lineup_game_scale.png'))
    hair(f0, f1).save(os.path.join(out, 'hair_8x.png'))
    pallor().save(os.path.join(out, 'pallor_4x.png'))
    sheet = Image.new('RGBA', (192, 96), B.BG)
    sheet.alpha_composite(f0, (0, 0))
    sheet.alpha_composite(f1, (96, 0))
    sheet.save(os.path.join(out, 'v2_1x.png'))
    print('previews written to', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
