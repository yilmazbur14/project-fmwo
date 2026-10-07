"""Shared bits for the champion-cutscene approval rig.

Everything this rig writes goes under the approval folder (OUT). save() refuses any path whose
realpath is not inside it, so nothing here can land in the project's Assets or any live repo path.
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.realpath(__file__))
OUT = os.path.realpath(os.path.join(HERE, ".."))          # .../champion/approval
PROJECT = r"C:\Users\theyi\OneDrive\Documents\new-game-project"
ASSETS = os.path.join(PROJECT, "Assets")


def _inside(path, root):
    p = os.path.realpath(path)
    r = os.path.realpath(root)
    return p == r or p.startswith(r + os.sep)


def save(img, rel):
    """Save under the approval folder only."""
    path = os.path.join(OUT, rel)
    if not _inside(path, OUT) or _inside(path, PROJECT):
        raise SystemExit(f"refusing to write outside the approval folder: {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def hexc(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


# ---------------------------------------------------------------- Burak (measured, 4dir sheet)
# 7 colours, no keyline: black is only his hair and shoes (13.9% of the 4dir sheet).
BURAK = {
    'K': hexc('000000'),   # hair, shoes
    'b': hexc('2464BD'),   # shorts, gloves
    's': hexc('D79864'),   # skin
    'd': hexc('AC714F'),   # skin shade
    'r': hexc('AC3232'),   # headband, eyes
    'B': hexc('162FBB'),   # shorts / glove shade
    'c': hexc('3883C9'),   # waistband / glove light
}

# ---------------------------------------------------------------- trophy + stand (props)
# Props carry the cast's pure-black keyline (Mason-style), a 5-step hue-shifted gold ramp and
# white speculars.
PROP = {
    'K': hexc('000000'),
    'W': hexc('FFFFFF'),   # specular
    '1': hexc('FFF4A3'),   # pale highlight
    '2': hexc('FBD23C'),   # bright gold
    '3': hexc('E6A21E'),   # base gold
    '4': hexc('B8681B'),   # shade
    '5': hexc('7A3E17'),   # deep shade
    # Burak's own blues for the glove emblem (ties the cup to him)
    'b': hexc('2464BD'), 'c': hexc('3883C9'), 'B': hexc('162FBB'),
    # arena navy (the ringside skirt) for plinth / stand
    'n': hexc('222034'), 'm': hexc('3F3F74'), 'o': hexc('2C2A42'),
    # red: crest / velvet
    'R': hexc('AC3232'), 'r': hexc('D95763'), 'q': hexc('6E1E2A'),
    'w': hexc('CBDBFC'),   # cool white (cuff, plate engraving)
}


def grid_to_image(rows, pal, img=None, at=(0, 0)):
    """Paint an ASCII grid ('.' clear) onto img (or a fresh image) at `at`."""
    h = len(rows)
    w = max(len(r) for r in rows)
    if img is None:
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    ox, oy = at
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.' or ch == ' ':
                continue
            X, Y = ox + x, oy + y
            if 0 <= X < img.width and 0 <= Y < img.height:
                px[X, Y] = pal[ch]
    return img


def paste(dst, src, at):
    """Alpha-composite src onto dst at integer `at`, clipped."""
    layer = Image.new('RGBA', dst.size, (0, 0, 0, 0))
    layer.paste(src, at, src)
    dst.alpha_composite(layer)
    return dst


def zoom(img, k, bg=(127, 127, 159, 255)):
    base = Image.new('RGBA', img.size, bg)
    base.alpha_composite(img)
    return base.resize((img.width * k, img.height * k), Image.NEAREST)


def stats(img, black=(0, 0, 0)):
    px = [p for p in img.getdata() if p[3] > 0]
    cols = {p[:3] for p in px}
    blk = sum(1 for p in px if p[:3] == black)
    semi = sum(1 for p in px if 0 < p[3] < 255)
    return dict(opaque=len(px), colours=len(cols), black=round(100 * blk / max(1, len(px)), 1),
                semi=semi)
