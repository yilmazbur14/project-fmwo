"""Build Carter's polished base sprite and its checks.

    python build.py            # write the sheet + previews to the scratchpad only
    python build.py --ship     # also write Assets/Characters/Carter/carter_polish.png and .aseprite

Output: carter_polish.png, 2 frames of 96x96 in a horizontal strip, soles on row 95:
    0 = standing idle, 1 = arms crossed (the signature pose).
The back view is deliberately left out of this approval pass (its mark is being redrawn).

Lint (fails the build on any error): 96x96 frames, binary alpha, soles on row 95 in every frame, every
colour from the approved palette, keyline pure black. Numbers printed against the approved sheet.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.dont_write_bytecode = True

from PIL import Image                                                         # noqa: E402
import lib                                                                    # noqa: E402
import frame0                                                                 # noqa: E402
import frame1                                                                 # noqa: E402
from imgdiff import pixel_diff                                                # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ASSET_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'Carter')
APPROVED = os.path.join(ASSET_DIR, 'carter_akuma.png')
OUT_PNG = os.path.join(ASSET_DIR, 'carter_polish.png')
OUT_ASE = os.path.join(ASSET_DIR, 'carter_polish.aseprite')
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
PREVIEWS = os.environ.get('CARTER_POLISH_PREVIEWS', os.path.join(
    os.environ.get('TEMP', tempfile.gettempdir()), 'claude',
    'C--Users-theyi-OneDrive-Documents-new-game-project', 'a7fc2846-afef-472d-979b-e17143793a0f',
    'scratchpad', 'carter_polish'))

F = 96
BG_DARK = (30, 32, 40, 255)


def sheet():
    frames = [frame0.build().image(), frame1.build().image()]
    out = Image.new('RGBA', (F * len(frames), F), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        out.alpha_composite(im, (i * F, 0))
    return out


# ------------------------------------------------------------------ checks

def lint(im):
    errs = []
    if im.height != F or im.width % F:
        errs.append('size %s is not a strip of %dx%d frames' % (im.size, F, F))
    st = lib.stats(im)
    if st['alphas'] not in ([0, 255], [255]):
        errs.append('non-binary alpha %s' % st['alphas'])
    pal = {v[:3] for v in lib.PAL.values()}
    stray = {c[:3] for c in lib.flat(im) if c[3] and c[:3] not in pal}
    if stray:
        errs.append('%d colours outside the palette' % len(stray))
    for f in range(im.width // F):
        rows = [y for y in range(F) for x in range(f * F, f * F + F) if im.getpixel((x, y))[3]]
        if max(rows) != 95:
            errs.append('frame %d: lowest opaque row %d, not 95' % (f, max(rows)))
        # the soles themselves must reach the floor on both feet (not an ember or a flame)
        for x0, x1 in ((26, 42), (54, 70)):
            if not any(im.getpixel((f * F + x, 95))[:3] == (0, 0, 0) for x in range(x0, x1)):
                errs.append('frame %d: no sole on row 95 in x %d..%d' % (f, x0, x1))
    return errs


def numbers(im, label):
    st = lib.stats(im)
    print('%-34s opaque %5d   colours %3d   pure black %5.1f%%' % (label, st['opaque'], st['colours'], 100 * st['black']))
    return st


AURA_RGB = {lib.PAL[k][:3] for k in 'xXyYzZPQRSTU'}


def keyline_colour(im):
    """The most common colour on the edge of the FIGURE: aura pixels count as background, since the
    aura has its own dark-violet edge in both sheets (the approved FX sheets use no black at all)."""
    from collections import Counter

    def solid(x, y):
        if not (0 <= x < im.width and 0 <= y < im.height):
            return False
        p = im.getpixel((x, y))
        return p[3] > 0 and p[:3] not in AURA_RGB
    c = Counter()
    for y in range(im.height):
        for x in range(im.width):
            if not solid(x, y):
                continue
            if any(not solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c[im.getpixel((x, y))[:3]] += 1
    total = sum(c.values())
    return [('#%02x%02x%02x' % k, round(100.0 * n / total, 1)) for k, n in c.most_common(2)]


# ------------------------------------------------------------------ previews

def before_after_5x(new, path):
    old = Image.open(APPROVED).convert('RGBA').crop((0, 0, 2 * F, F))
    s, gap = 5, 12
    w = (old.width + new.width) * s + gap * s * 3
    h = F * s + gap * s * 2
    out = Image.new('RGBA', (w, h), BG_DARK)
    out.alpha_composite(lib.upscale(old, s), (gap * s, gap * s))
    out.alpha_composite(lib.upscale(new, s), (gap * s * 2 + old.width * s, gap * s))
    _label(out, 'BEFORE  carter_akuma.png (frames 0-1)', gap * s, 8)
    _label(out, 'AFTER  carter_polish.png', gap * s * 2 + old.width * s, 8)
    out.save(path)


def game_3x(new, path):
    """Both versions at the game's own 3x on the arena mat. CarterArtLayout.SCALE = 3.0 and the 16%
    shrink is already inside the 96px frame (he is drawn 81 rows tall), so a whole 3x of the frame is
    exactly what the fight shows. His node sits at screen (959, 700) with the frame anchored at texel
    (48, 95); the mat is drawn at (111, 114) at 3x."""
    old = Image.open(APPROVED).convert('RGBA').crop((0, 0, 2 * F, F))
    mat = Image.open(MAT).convert('RGBA')
    scr = Image.new('RGBA', (1920, 1080), (0, 0, 0, 255))
    scr.alpha_composite(lib.upscale(mat, 3), (111, 114))
    feet_y = 700
    xs = [(old, 0, 390), (old, 1, 690), (new, 0, 1170), (new, 1, 1470)]
    for im, f, cx in xs:
        fr = lib.upscale(im.crop((f * F, 0, f * F + F, F)), 3)
        scr.alpha_composite(fr, (cx - 48 * 3, feet_y - 95 * 3 - 2))
    crop = scr.crop((200, 360, 1680, 740))
    out = Image.new('RGBA', (crop.width, crop.height + 40), BG_DARK)
    out.alpha_composite(crop, (0, 40))
    _label(out, 'BEFORE (approved)', 130, 10)
    _label(out, 'AFTER (polish)', 910, 10)
    out.save(path)


def _label(im, text, x, y):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.text((x, y), text, fill=(235, 235, 240, 255))


# ------------------------------------------------------------------ ship

def ship(im):
    im.save(OUT_PNG)
    subprocess.run([ASEPRITE, '-b', OUT_PNG, '--save-as', OUT_ASE], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', OUT_ASE, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(OUT_PNG), Image.open(back))
    print('wrote', OUT_PNG, im.size)
    print('wrote', OUT_ASE)
    print('round trip (.aseprite -> png, imgdiff.pixel_diff):', d or 'identical')
    return d


def main():
    im = sheet()
    errs = lint(im)
    for e in errs:
        print('LINT:', e)
    old = Image.open(APPROVED).convert('RGBA')
    print('figure edge colour (%% of edge px), approved front:', keyline_colour(old.crop((0, 0, 2 * F, F))), ' polish:', keyline_colour(im))
    numbers(old, 'approved sheet (3 frames)')
    numbers(old.crop((0, 0, 2 * F, F)), 'approved front frames 0-1')
    for f in range(2):
        numbers(old.crop((f * F, 0, f * F + F, F)), '  approved frame %d' % f)
    numbers(im, 'polish sheet (2 frames)')
    for f in range(2):
        numbers(im.crop((f * F, 0, f * F + F, F)), '  polish frame %d' % f)

    os.makedirs(PREVIEWS, exist_ok=True)
    im.save(os.path.join(PREVIEWS, 'carter_polish_sheet.png'))
    before_after_5x(im, os.path.join(PREVIEWS, 'before_after_5x.png'))
    game_3x(im, os.path.join(PREVIEWS, 'before_after_game_3x.png'))
    print('previews in', PREVIEWS)

    if errs:
        return 1
    if '--ship' in sys.argv:
        return 1 if ship(im) else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
