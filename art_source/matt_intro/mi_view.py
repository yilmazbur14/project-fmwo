"""Preview helpers: frames upscaled on the dark ground with labels, ruled grids for placing edits,
game-scale line-ups on the arena mat, GIFs. Reads the project's assets; writes only to the folder
it is given (the session scratchpad by default)."""
import os

from PIL import Image, ImageDraw

import mi_base as B

BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
MAT = os.path.join(B.ROOT, 'Assets', 'Environment', 'arena_mat.png')


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im.convert('RGBA'))
    return out


def up(im, s, bg=BG):
    base = on_bg(im, bg) if bg else im.convert('RGBA')
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def label(im, text, pad=16, col=(225, 225, 232, 255), bg=DARK):
    out = Image.new('RGBA', (im.width, im.height + pad), bg)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((3, 2), text, fill=col)
    return out


def row(ims, gap=8, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def col(ims, gap=8, bg=DARK):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def ruled(im, s, x0=0, y0=0, major=5, bg=BG):
    """Upscaled with a faint pixel grid, every `major`th line stronger, coordinates in the margin."""
    big = up(im, s, bg)
    d = ImageDraw.Draw(big, 'RGBA')
    for gx in range(0, big.width, s):
        strong = ((gx // s) + x0) % major == 0
        d.line([(gx, 0), (gx, big.height)], fill=(255, 80, 200, 80) if strong else (255, 255, 255, 18))
    for gy in range(0, big.height, s):
        strong = ((gy // s) + y0) % major == 0
        d.line([(0, gy), (big.width, gy)], fill=(255, 80, 200, 80) if strong else (255, 255, 255, 18))
    m = 22
    out = Image.new('RGBA', (big.width + m, big.height + m), DARK)
    out.paste(big, (m, m))
    d = ImageDraw.Draw(out)
    for i in range(im.width):
        if (i + x0) % major == 0:
            d.text((m + i * s + 1, 5), str(x0 + i), fill=(255, 140, 220, 255))
    for j in range(im.height):
        if (j + y0) % major == 0:
            d.text((1, m + j * s + 1), str(y0 + j), fill=(255, 140, 220, 255))
    return out


def frames_row(frames, s, labels=None, bg=BG):
    ims = []
    for i, f in enumerate(frames):
        im = f if isinstance(f, Image.Image) else B.image(f)
        big = up(im, s, bg)
        ims.append(label(big, labels[i]) if labels else big)
    return row(ims)


def on_mat(frames, s=3, pad=6, crop=(120, 80)):
    """Frames side by side at native size on a crop of the arena mat, then scaled s: what the
    fight shows at scale 3."""
    mat = Image.open(MAT).convert('RGBA')
    w = 96 * len(frames) + pad * (len(frames) + 1)
    tile = mat.crop((crop[0], crop[1], crop[0] + 300, crop[1] + 104))   # the mat is 565 wide: tile it
    ground = Image.new('RGBA', (w, 104))
    for tx in range(0, w, tile.width):
        ground.paste(tile, (tx, 0))
    x = pad
    for f in frames:
        im = f if isinstance(f, Image.Image) else B.image(f)
        ground.alpha_composite(im, (x, 4))
        x += 96 + pad
    return ground.resize((ground.width * s, ground.height * s), Image.NEAREST)


def gif(frames, path, s, durations, bg=BG, loop=0):
    ims = []
    for f in frames:
        im = f if isinstance(f, Image.Image) else B.image(f)
        ims.append(up(im, s, bg).convert('P', palette=Image.ADAPTIVE, colors=255))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durations, loop=loop, disposal=2)


def save(im, name, sub='work'):
    d = os.path.join(B.SCRATCH, sub)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    im.save(p)
    return p
