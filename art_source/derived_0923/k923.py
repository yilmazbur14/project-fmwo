"""Shared kit for the 2026-09-23 derived-art jobs (art_source/derived_0923): paths, measuring,
the .aseprite round trip and preview helpers.

The three jobs, each its own script, each writing ONLY to the scratchpad unless run with --ship:
    burak_portrait.py   Assets/Characters/Burak/portrait.png (+ .aseprite), from his approved VS pose
    ladder.py           Assets/UI/Screens/rank_icons.png frame 3 (Matt) / frame 2 (Computah) + .aseprite
    menu.py             Assets/UI/Screens/main_menu_bg.png, the [matt] silhouette on tier 4 (+ .aseprite)

Named k923, not kit/lib/dkit, so it can never shadow a rig module of those names that one of the
pipelines imported here pulls in (vs_card_v2's pxkit, victory_screen's cv, main_menu's lib).

Nothing in this module writes into Assets/. Previews go to PREVIEWS (the session scratchpad).
"""
import hashlib
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ART = os.path.join(ROOT, 'art_source')
ASSETS = os.path.join(ROOT, 'Assets')
SCRATCH = os.environ.get(
    'DERIVED_0923_SCRATCH',
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad')
PREVIEWS = os.path.join(SCRATCH, 'derived_0923')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

if ART not in sys.path:
    sys.path.append(ART)
from imgdiff import pixel_diff                                    # noqa: E402
from PIL import Image, ImageDraw                                  # noqa: E402


# ---------------------------------------------------------------------------------------- numbers
def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def stats(im, key=(0, 0, 0)):
    """Opaque count, distinct opaque colours, the share of opaque pixels that are `key` (the
    character's keyline colour), and the alpha values present."""
    px = flat(im.convert('RGBA'))
    op = [c for c in px if c[3] > 0]
    hit = sum(1 for c in op if c[:3] == tuple(key))
    return {'opaque': len(op), 'colours': len({c for c in op}), 'key': hit / max(1, len(op)),
            'key_px': hit, 'alphas': sorted({c[3] for c in px})}


def fmt(name, s, key='black'):
    return '%-44s %5d px  %s %5.1f%%  colours %2d' % (name, s['opaque'], key, 100 * s['key'], s['colours'])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    with open(path, 'rb') as f:
        return sha(f.read())


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


# ---------------------------------------------------------------------------------------- aseprite
def aseprite(args):
    r = subprocess.run([ASEPRITE, '-b'] + args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('aseprite %s failed: %s %s' % (args, r.stdout, r.stderr))
    return r


def ase_from_png(png, ase):
    """Save a PNG as a one-layer .aseprite, then prove the .aseprite re-exports to exactly the PNG's
    pixels (imgdiff.pixel_diff). Returns the diff, or None when identical."""
    aseprite([png, '--save-as', ase])
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    aseprite([ase, '--save-as', back])
    return pixel_diff(Image.open(png), Image.open(back))


# ---------------------------------------------------------------------------------------- previews
BG = (46, 49, 58, 255)
DARK = (10, 10, 12, 255)


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im.convert('RGBA'))
    return out


def up(im, s, bg=BG):
    base = on_bg(im, bg) if bg else im.convert('RGBA')
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def gridded(im, s, major=5, bg=BG):
    big = up(im, s, bg)
    d = ImageDraw.Draw(big, 'RGBA')
    for gx in range(0, big.width, s):
        d.line([(gx, 0), (gx, big.height)], fill=(255, 80, 200, 90) if (gx // s) % major == 0 else (255, 255, 255, 26))
    for gy in range(0, big.height, s):
        d.line([(0, gy), (big.width, gy)], fill=(255, 80, 200, 90) if (gy // s) % major == 0 else (255, 255, 255, 26))
    return big


def ruled(im, s, major=5, bg=BG, x0=0, y0=0):
    """gridded() with the coordinates of every `major`th pixel written in a margin."""
    big = gridded(im, s, major, bg)
    m = 26
    out = Image.new('RGBA', (big.width + m, big.height + m), DARK)
    out.paste(big, (m, m))
    d = ImageDraw.Draw(out)
    for i in range(0, im.width, major):
        d.text((m + i * s + 1, 5), str(x0 + i), fill=(255, 140, 220, 255))
    for j in range(0, im.height, major):
        d.text((1, m + j * s + 1), str(y0 + j), fill=(255, 140, 220, 255))
    return out


def label(im, text, pad=18, col=(220, 220, 228, 255)):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 3), text, fill=col)
    return out


def row(ims, gap=10, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def col(ims, gap=10, bg=DARK):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def preview(im, name):
    os.makedirs(PREVIEWS, exist_ok=True)
    p = os.path.join(PREVIEWS, name)
    im.save(p)
    return p


def refuse_live(path):
    """Scratch writers call this: a path inside Assets/ is refused outright."""
    if os.path.normcase(os.path.abspath(path)).startswith(os.path.normcase(ASSETS)):
        raise RuntimeError('refusing to write inside Assets/ without --ship: %s' % path)
    return path
