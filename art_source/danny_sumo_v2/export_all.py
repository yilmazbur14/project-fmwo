"""Write every evolved-form sheet of Danny's sumo from the approved redesign, in place.

  python export_all.py <preview-dir>          lint and previews only; nothing under Assets is touched
  python export_all.py <preview-dir> --ship   lint, write, .aseprite, round-trip, previews

(Gated 2026-09-24: a bare run used to write the live sheets. --dry is still accepted and means the
same as leaving --ship off.)

For each of anim.SHEETS it builds the whole strip in memory, lints it, writes the PNG once into
Assets/Characters/Danny/Sumo/, saves the .aseprite beside it with the Aseprite CLI, exports that
back and pixel_diffs it against the PNG, and measures it. Previews: a contact sheet of every
sheet at 3x, and one GIF per sheet at 2x on the old sheets' timings (the evolve GIF plays the
transformation's drain and flash from art_source/danny_sumo/transform.py over frames 0 and 1).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from PIL import Image, ImageDraw  # noqa: E402

import anim  # noqa: E402
import measure  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ASEPRITE = r"C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe"
SUMO = os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'Sumo')
FW, FH = anim.FW, anim.FH
GROUND = 143
BG = (46, 49, 58, 255)
FLOOR = (78, 82, 96, 255)
# transform.py: the drain before the flash, and the flash's accelerating holds (small first)
DRAIN = [(0.35, 110), (0.7, 110), (1.0, 110)]
FLASH_HOLDS = [340, 300, 260, 220, 180, 145, 115, 90, 70, 60, 55, 50, 50, 50]


def frames_of(sheet):
    return [sheet.crop((i * FW, 0, i * FW + FW, FH)) for i in range(sheet.width // FW)]


def lint(name, sheet):
    """The frame contract, checked: silhouette keyline unbroken, nothing cut by any of the frame's
    four borders (the floor row may carry only keyline), soles on the ground row."""
    problems = []
    for i, f in enumerate(frames_of(sheet)):
        if name == 'danny_sumo_evolve' and i == 0:
            # the approved small form, pasted verbatim (its flex sparkles carry no keyline by design)
            flex = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'danny_flex.png')).convert('RGBA')
            paste = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
            paste.alpha_composite(flex.crop((128, 0, 192, 64)), (56, 80))
            d = pixel_diff(f, paste)
            if d is not None:
                problems.append('f0 is not danny_flex frame 2 at (+56, +80): %s' % d)
            continue
        px = f.load()
        bad_edge = cut = 0
        for y in range(FH):
            for x in range(FW):
                c = px[x, y]
                if not c[3] or c[:3] == (0, 0, 0):
                    continue
                if x in (0, FW - 1) or y in (0, FH - 1):
                    cut += 1                                    # colour on a border: something is cut off
                for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= q[0] < FW and 0 <= q[1] < FH) or not px[q][3]:
                        bad_edge += 1
                        break
        low = f.getbbox()[3] - 1
        if bad_edge:
            problems.append('f%d: %d silhouette pixels without keyline' % (i, bad_edge))
        if cut:
            problems.append('f%d: %d pixels cut by the frame border' % (i, cut))
        if low != GROUND:
            problems.append('f%d: lowest row %d, not %d' % (i, low, GROUND))
    return problems


def gif(path, frames, durations, scale=2):
    out = []
    for f in frames:
        W, H = FW * scale + 16, FH * scale + 12
        im = Image.new('RGBA', (W, H), BG)
        ImageDraw.Draw(im).rectangle([0, 6 + FH * scale, W, 6 + FH * scale + 1], fill=FLOOR)
        im.alpha_composite(f.resize((FW * scale, FH * scale), Image.NEAREST), (8, 6))
        out.append(im.convert('RGB'))
    pal = [o.convert('P', palette=Image.ADAPTIVE, colors=255) for o in out]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations, loop=0, disposal=1,
                optimize=False)


def silhouette(f, colour=(255, 255, 255, 255)):
    s = Image.new('RGBA', f.size, (0, 0, 0, 0))
    s.paste(colour, (0, 0), f.getchannel('A'))
    return s


def drain(f, t):
    r, g, b, a = f.split()
    lift = lambda ch: ch.point(lambda v: int(v + (255 - v) * t))  # noqa: E731
    return Image.merge('RGBA', (lift(r), lift(g), lift(b), a))


def evolve_gif(path, sheet):
    f0, f1, f2 = frames_of(sheet)
    seq = [(f0, 300)] + [(drain(f0, t), ms) for t, ms in DRAIN]
    for i, ms in enumerate(FLASH_HOLDS):
        seq.append((silhouette(f0 if i % 2 == 0 else f1), ms))
    seq += [(silhouette(f1), 120), (f2, 160), (f1, 400)]
    gif(path, [s for s, _ in seq], [ms for _, ms in seq])


def contact(path, sheets, scale=3):
    label_h = 12
    rows = [(n, s) for n, s in sheets]
    W = max(s.width for _, s in rows) * scale + 2 * 8
    H = sum(FH * scale + label_h * scale + 8 for _ in rows) + 8
    im = Image.new('RGBA', (W, H), BG)
    d = ImageDraw.Draw(im)
    y = 8
    for name, s in rows:
        spec = anim.SHEETS[name][0]
        d.text((8, y), '%s  (%d frames)   %s' % (name, len(spec), anim.SHEETS[name][1]), fill=(230, 230, 240, 255))
        for i, (_, ms) in enumerate(spec):
            d.text((8 + i * FW * scale + 4, y + label_h * scale - 14), 'f%d  %s' % (i, ('%d ms' % ms) if ms else
                                                                                  '(state machine)'),
                   fill=(170, 175, 200, 255))
        y += label_h * scale
        im.alpha_composite(s.resize((s.width * scale, FH * scale), Image.NEAREST), (8, y))
        for i in range(1, s.width // FW):
            d.line([(8 + i * FW * scale, y), (8 + i * FW * scale, y + FH * scale - 1)], fill=(70, 74, 88, 255))
        d.line([(8, y + FH * scale), (8 + s.width * scale, y + FH * scale)], fill=FLOOR)
        y += FH * scale + 8
    im.save(path)


def main(prev, dry=True):
    os.makedirs(prev, exist_ok=True)
    for name, d in anim.check_approved():
        print('approved %-8s rebuilt: %s' % (name, 'pixel-identical' if d is None else d))
        assert d is None, 'the approved frame no longer rebuilds'
    built = []
    for name in anim.SHEETS:
        sheet = anim.build_sheet(name)
        problems = lint(name, sheet)
        print('%-18s %4d x %d  %d frames  lint: %s' % (name, sheet.width, sheet.height, sheet.width // FW,
                                                       '; '.join(problems) or 'clean'))
        assert not problems, name
        built.append((name, sheet))

    if not dry:
        for name, sheet in built:
            png = os.path.join(SUMO, name + '.png')
            ase = os.path.join(SUMO, name + '.aseprite')
            sheet.save(png)                                     # the one write of this PNG
            subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
            rt = os.path.join(prev, name + '_roundtrip.png')
            subprocess.run([ASEPRITE, '-b', ase, '--save-as', rt], check=True)
            d = pixel_diff(Image.open(png), Image.open(rt))
            print('  %-18s .png -> .aseprite -> .png: %s' % (name, 'pixel-identical' if d is None else d))
            assert d is None, name
            os.remove(rt)

    print('measured:')
    for name, sheet in built:
        print('  ' + measure.fmt(name, measure.measure(sheet)))
        for i, f in enumerate(frames_of(sheet)):
            print('  ' + measure.fmt('    f%d  (%s ms)' % (i, anim.SHEETS[name][0][i][1] or 'sm'), measure.measure(f)))

    contact(os.path.join(prev, 'danny_sumo_sheets_3x.png'), built)
    for name, sheet in built:
        path = os.path.join(prev, name + '_2x.gif')
        if name == 'danny_sumo_evolve':
            evolve_gif(path, sheet)
        else:
            gif(path, frames_of(sheet), [ms for _, ms in anim.SHEETS[name][0]])
    print('previews in', prev)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else os.path.join(HERE, 'out'), dry='--ship' not in sys.argv)
