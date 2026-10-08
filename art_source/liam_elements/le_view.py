"""Preview helpers for the elements-phase rig: zoomed views with a 4-px grid and rulers, written only to
the scratchpad (never to the project)."""
import os

import numpy as np
from PIL import Image, ImageDraw

import le_rig as R

SCRATCH = os.environ.get('LE_SCRATCH', os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\liam_elements'))
os.makedirs(SCRATCH, exist_ok=True)


def checker(w, h, cell=4, c1=(190, 196, 204), c2=(160, 168, 178)):
    ys, xs = np.mgrid[0:h, 0:w]
    m = ((xs // cell + ys // cell) % 2) == 0
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[m] = c1 + (255,)
    out[~m] = c2 + (255,)
    return out


def rgba_of(cv_or_img):
    if isinstance(cv_or_img, np.ndarray) and cv_or_img.dtype.kind == 'U':
        return R.to_rgba(cv_or_img)
    if isinstance(cv_or_img, Image.Image):
        return np.array(cv_or_img.convert('RGBA'))
    return cv_or_img


def zoom(cv, name, s=8, grid=True, rulers=True, bg='checker', every=4):
    a = rgba_of(cv)
    h, w = a.shape[:2]
    if bg == 'checker':
        base = checker(w, h)
    else:
        base = np.zeros((h, w, 4), dtype=np.uint8)
        base[...] = tuple(bg) + (255,) if len(bg) == 3 else bg
    op = a[..., 3] > 0
    base[op] = a[op]
    im = Image.fromarray(base, 'RGBA').resize((w * s, h * s), Image.NEAREST)
    if grid:
        px = np.array(im)
        for i in range(0, w, every):
            px[:, i * s, :3] = (px[:, i * s, :3].astype(int) * 3 + np.array([255, 0, 255])) // 4
        for j in range(0, h, every):
            px[j * s, :, :3] = (px[j * s, :, :3].astype(int) * 3 + np.array([255, 0, 255])) // 4
        im = Image.fromarray(px)
    if rulers:
        M = 28
        out = Image.new('RGBA', (w * s + M, h * s + M), (40, 40, 48, 255))
        out.paste(im, (M, M))
        d = ImageDraw.Draw(out)
        for i in range(0, max(w, h), every * 2):
            if i < w:
                d.text((M + i * s + 1, 2), str(i), fill=(255, 230, 120, 255))
            if i < h:
                d.text((1, M + i * s + 1), str(i), fill=(255, 230, 120, 255))
        im = out
    p = os.path.join(SCRATCH, name)
    im.save(p)
    return p


def row(images, name, s=4, gap=6, bg=(58, 64, 84), labels=None):
    arrs = [rgba_of(x) for x in images]
    hmax = max(a.shape[0] for a in arrs)
    wsum = sum(a.shape[1] for a in arrs) + gap * (len(arrs) + 1)
    top = 12 if labels else 0
    out = Image.new('RGBA', (wsum * s, (hmax + gap * 2 + top) * s), tuple(bg) + (255,))
    x = gap
    d = ImageDraw.Draw(out)
    for i, a in enumerate(arrs):
        h, w = a.shape[:2]
        im = Image.fromarray(a, 'RGBA').resize((w * s, h * s), Image.NEAREST)
        out.alpha_composite(im, (x * s, (gap + top) * s))
        if labels:
            d.text((x * s, 2 * s), labels[i], fill=(255, 230, 120, 255))
        x += w + gap
    p = os.path.join(SCRATCH, name)
    out.save(p)
    return p
