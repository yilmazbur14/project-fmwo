"""Review sheet for the feint badge (feint.py): the recommended X and two alternatives beside the two
tells they must not be mistaken for, at 4x, on the dark spotlight and on the lit arena, each with its
greyscale proof - and a game-scale strip of each over a rushing clone.

    python previews_feint.py <out_dir>

It writes only into <out_dir>. It reads the shipped demon_light.png for the red and yellow references
and never writes a sheet.
"""
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import feint                                            # noqa: E402

PROJ = os.path.abspath(os.path.join(_HERE, '..', '..'))


def A(*p):
    return os.path.join(PROJ, 'Assets', *p)


def load(path):
    return np.asarray(Image.open(path).convert('RGBA'), dtype=np.float32)


def cv_arr(cv):
    return np.asarray(Image.fromarray(np.array(cv.rgba(), dtype=np.uint8), 'RGBA'), dtype=np.float32)


def over(dst, src, x, y):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] / 255.0
    dst[y0:y1, x0:x1, :3] = s[..., :3] * a + dst[y0:y1, x0:x1, :3] * (1 - a)


def add(dst, src, x, y):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] / 255.0
    dst[y0:y1, x0:x1, :3] = np.minimum(255, dst[y0:y1, x0:x1, :3] + s[..., :3] * a)


def texel_arena(dark):
    """the arena at ONE TEXEL PER PIXEL (640x360, the view / 3): ringside, crowd, mat - and for the dark
    row the Demon's darkness and his spotlight pool on the middle of the ring"""
    img = np.zeros((360, 640, 4), np.float32)
    img[..., 3] = 255
    over(img, load(A('Environment', 'arena_ringside.png')), 0, 0)
    over(img, load(A('Environment', 'crowd_v2.png'))[:, 0:640], 0, 0)
    over(img, load(A('Environment', 'arena_mat.png')), 37, 38)
    if dark:
        over(img, load(A('Characters', 'Carter', 'Demon', 'demon_darkness.png')), 0, 0)
        pool = load(A('Characters', 'Carter', 'Demon', 'demon_spotlight_pool.png'))
        add(img, pool, 320 - 80, 191 - 186)
    return img


def grey(img):
    g = img[..., 0] * 0.299 + img[..., 1] * 0.587 + img[..., 2] * 0.114
    out = img.copy()
    out[..., 0] = out[..., 1] = out[..., 2] = g
    return out


def badges():
    """(label, 4 frames as arrays): the two tells to be told apart from, then the three candidates"""
    light = load(A('Characters', 'Carter', 'Demon', 'demon_light.png'))
    red = [light[:, i * 24:(i + 1) * 24] for i in range(4)]
    yellow = [light[:, i * 24:(i + 1) * 24] for i in range(4, 8)]
    return [('red: PARRY (existing)', red),
            ('yellow: DODGE tell / old feint (existing)', yellow),
            ('A  X - RECOMMENDED', [cv_arr(feint.cross(i)) for i in range(4)]),
            ('B  stop-octagon', [cv_arr(feint.octagon(i)) for i in range(4)]),
            ('C  slashed circle', [cv_arr(feint.slashed(i)) for i in range(4)])]


def sheet_4x(out):
    """every set's four frames at 4x on a patch of the real ground: the dark spotlight's edge, and the
    lit mat. Then the same again in greyscale."""
    sets = badges()
    Z = 4
    cell = 24 * Z
    gap = 8
    grounds = {True: texel_arena(True), False: texel_arena(False)}
    # the patch each badge sits on, in texels: the rim of the pool in the dark, open mat in the light
    patch = {True: (250, 150), False: (180, 120)}
    rows = []
    for dark in (True, False):
        g = grounds[dark]
        px, py = patch[dark]
        row = np.zeros((cell + 2 * gap, (cell + gap) * 4 * len(sets) + gap * len(sets) * 3, 4), np.float32)
        row[..., 3] = 255
        row[..., :3] = 12
        x = gap
        for label, frs in sets:
            for i, fr in enumerate(frs):
                bg = g[py:py + 24, px + i * 24:px + i * 24 + 24].copy()
                over(bg, fr, 0, 0)
                big = bg.repeat(Z, 0).repeat(Z, 1)
                row[gap:gap + cell, x:x + cell] = big
                x += cell + gap
            x += gap * 3
        rows.append(row)
    colour = np.concatenate(rows, 0)
    both = np.concatenate([colour, np.zeros((16, colour.shape[1], 4), np.float32) + [12, 12, 12, 255],
                           grey(colour)], 0)
    im = Image.fromarray(np.clip(both[..., :3], 0, 255).astype(np.uint8))
    from PIL import ImageDraw
    head = Image.new('RGB', (im.width, 22), (12, 12, 12))
    d = ImageDraw.Draw(head)
    x = gap
    for label, _ in sets:
        d.text((x, 5), label, fill=(235, 235, 240))
        x += (cell + gap) * 4 + gap * 3
    final = Image.new('RGB', (im.width, im.height + 22), (12, 12, 12))
    final.paste(head, (0, 0))
    final.paste(im, (0, 22))
    path = os.path.join(out, 'feint_badges_4x.png')
    final.save(path)
    print('  ', path, final.size)


def in_context(out):
    """game scale (3 px a texel), on the dark spotlight: a rushing clone with each set's HOLD frame on
    its light anchor - (0, -175) px from its feet (CarterArtLayout.clone_light_anchor)"""
    g = texel_arena(True).repeat(3, 0).repeat(3, 1)
    clone = load(A('Characters', 'Carter', 'Demon', 'demon_clone.png'))[:, 5 * 48:6 * 48]
    sets = badges()
    tiles = []
    for label, frs in sets:
        tile = g[330:330 + 330, 700:700 + 240].copy()
        feet = (120, 300)
        over(tile, clone.repeat(3, 0).repeat(3, 1), feet[0] - 24 * 3, feet[1] - 47 * 3)
        hold = frs[2]
        over(tile, hold.repeat(3, 0).repeat(3, 1), feet[0] - 12 * 3, feet[1] - 175 - 12 * 3)
        tiles.append(tile)
    gap = 10
    W = sum(t.shape[1] for t in tiles) + gap * (len(tiles) + 1)
    img = np.zeros((tiles[0].shape[0] + 2 * gap, W, 4), np.float32) + [12, 12, 12, 255]
    x = gap
    for t in tiles:
        img[gap:gap + t.shape[0], x:x + t.shape[1]] = t
        x += t.shape[1] + gap
    path = os.path.join(out, 'feint_in_context_game_scale.png')
    Image.fromarray(np.clip(img[..., :3], 0, 255).astype(np.uint8)).save(path)
    print('  ', path, img.shape[1], 'x', img.shape[0])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('usage: python previews_feint.py <out_dir>')
    os.makedirs(sys.argv[1], exist_ok=True)
    sheet_4x(sys.argv[1])
    in_context(sys.argv[1])
