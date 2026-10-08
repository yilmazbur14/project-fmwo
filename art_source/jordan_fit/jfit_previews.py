"""Approval-pass outputs for Jordan's fitted Peach tee. Writes ONLY into art_source/jordan_fit/ (this
folder); any other output folder, and anything that resolves (realpath) under Assets/, is refused.

    python jfit_previews.py            # print this and exit
    python jfit_previews.py --write    # write the files below into this folder

  jordan_fit_compare_3x.png   before | after at game scale, in screen pixels: idle f0 and summon f2
                              (the fist-pump) at 3x as his Sprite2D draws them, the portrait at 2x as
                              the dialogue balloon draws it (a 128x128 TextureRect)
  jordan_fit_compare_6x.png   the same pairs at 6x
  jordan_fit_ingame_crop.png  before | after cropped round him from the two in-game captures, 1:1 and 2x
                              (needs jfit_capture.gd's two 1920x1080 PNGs; skipped without them)
  jordan_fit_idle_f0.png      the fitted art itself, 1x, each with its .aseprite beside it
  jordan_fit_summon_f2.png      (round-tripped through Aseprite's CLI and compared pixel for pixel)
  jordan_fit_portrait.png
  jordan_fit_idle_strip.png   all four fitted idle frames (384x96), which the in-game capture swaps in

The 1920x1080 in-game mock is jfit_capture.gd's (run through Godot; see its header).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jfit_frames as FR  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

B = FR.B
ROOT = FR.ROOT
ASEPRITE = B.ASEPRITE
BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
INK = (225, 225, 232, 255)
DIM = (150, 152, 165, 255)


def _font(size, bold=False):
    for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'), 'arial.ttf'):
        try:
            return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', name), size)
        except OSError:
            continue
    return ImageFont.load_default()


F_HEAD, F_CAP, F_SUB = _font(18, True), _font(15, True), _font(13)


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def _guard(path):
    if _under(path, os.path.join(ROOT, 'Assets')):
        raise SystemExit('refusing %s: nothing goes under Assets/ in the approval pass' % path)
    if not _under(path, HERE):
        raise SystemExit('refusing %s: outputs stay in art_source/jordan_fit/' % path)
    return path


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def tile(im, s, caption, sub='', min_w=0):
    big = up(im, s)
    pad = 44 if sub else 26
    w = max(big.width, min_w)
    out = Image.new('RGBA', (w, big.height + pad), DARK)
    out.paste(big, ((w - big.width) // 2, pad))
    d = ImageDraw.Draw(out)
    d.text((4, 3), caption, fill=INK, font=F_CAP)
    if sub:
        d.text((4, 23), sub, fill=DIM, font=F_SUB)
    return out


def hstack(ims, gap, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def vstack(ims, gap, bg=DARK):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def framed(im, title, pad=16):
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad + 28), DARK)
    ImageDraw.Draw(out).text((pad, 8), title, fill=INK, font=F_HEAD)
    out.paste(im, (pad, pad + 28))
    return out


def _pct(s):
    return 'black %.1f%%, %d colours' % (100 * s['black'], s['colours'])


def compare(sprite_scale, portrait_scale, title, rows=1):
    idle_b, idle_a = B.image(FR.idle_f0(False)), B.image(FR.idle_f0(True))
    pump_b, pump_a = B.image(FR.summon_f2(False)), B.image(FR.summon_f2(True))
    port_b, port_a = FR.portrait(False), FR.portrait(True)
    pairs = []
    for name, b, a, s in (('idle f0', idle_b, idle_a, sprite_scale), ('summon f2 (fist-pump)', pump_b, pump_a, sprite_scale),
                          ('portrait', port_b, port_a, portrait_scale)):
        tb = tile(b, s, 'BEFORE  %s' % name, 'live v2: ' + _pct(FR.stats(b)), min_w=250)
        ta = tile(a, s, 'AFTER  %s, fitted' % name, _pct(FR.stats(a)), min_w=250)
        pairs.append(hstack([tb, ta], 6))
    if rows == 1:
        body = hstack(pairs, 30)
    else:
        body = vstack([hstack(pairs[:2], 30), pairs[2]], 24)
    return framed(body, title)


def ingame_crop(out):
    """Before | after from the two in-game captures (jfit_capture.gd), 1:1 screen pixels round him."""
    paths = [os.path.join(out, n + '.png') for n in ('jordan_fit_ingame_before_1920x1080', 'jordan_fit_ingame_1920x1080')]
    if not all(os.path.exists(p) for p in paths):
        print('no in-game captures yet (run jfit_capture.gd), skipping the crop')
        return None
    box = (770, 196, 1150, 530)
    ims = [Image.open(p).convert('RGBA').crop(box) for p in paths]
    tiles = [tile(ims[0], 1, 'BEFORE  in the fight, 1:1 screen pixels', 'live v2 (jordan_idle.png f0)'),
             tile(ims[1], 1, 'AFTER  the fitted tee, same frame', 'jordan_fit_idle_strip.png f0 swapped in at runtime')]
    one = framed(hstack(tiles, 8), 'IN GAME at play size (crops of the two 1920x1080 captures)')
    two = framed(hstack([tile(im, 2, c) for im, c in zip(ims, ('BEFORE, 2x', 'AFTER, 2x'))], 8),
                 'The same crops at 2x')
    return vstack([one, two], 10)


def write_art(name, im, out_dir):
    """PNG + .aseprite (Aseprite CLI), built in a temp folder and moved into place, and the .aseprite
    re-exported and compared with the PNG pixel for pixel where they landed."""
    png = _guard(os.path.join(out_dir, name + '.png'))
    ase = _guard(os.path.join(out_dir, name + '.aseprite'))
    tmp = tempfile.mkdtemp(prefix='jfit_')
    tpng, tase = os.path.join(tmp, name + '.png'), os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    subprocess.run([ASEPRITE, '-b', tpng, '--save-as', tase], check=True, capture_output=True)
    os.replace(tpng, png)
    os.replace(tase, ase)
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    return FR.pixel_diff(Image.open(png), Image.open(back))


def main(argv):
    if argv[:1] != ['--write']:
        print(__doc__)
        return 2
    for ln in FR.check():
        print(ln)
    out = HERE
    c3 = compare(3, 2, 'GAME SCALE: Jordan at 3x as his Sprite2D draws him, the portrait at 2x as the dialogue balloon '
                       'shows it. Left of each pair live v2, right the fitted tee.')
    c3.save(_guard(os.path.join(out, 'jordan_fit_compare_3x.png')))
    c6 = compare(6, 6, 'CLOSE-UP at 6x. Left of each pair live v2, right the fitted tee.', rows=2)
    c6.save(_guard(os.path.join(out, 'jordan_fit_compare_6x.png')))
    print('wrote jordan_fit_compare_3x.png', c3.size, 'and jordan_fit_compare_6x.png', c6.size)
    ic = ingame_crop(out)
    if ic is not None:
        ic.save(_guard(os.path.join(out, 'jordan_fit_ingame_crop.png')))
        print('wrote jordan_fit_ingame_crop.png', ic.size)
    strip = Image.new('RGBA', (384, 96), (0, 0, 0, 0))
    for i, px in enumerate(FR.idle_strip(True)):
        strip.alpha_composite(B.image(px), (96 * i, 0))
    for name, im in (('jordan_fit_idle_f0', B.image(FR.idle_f0(True))),
                     ('jordan_fit_summon_f2', B.image(FR.summon_f2(True))),
                     ('jordan_fit_portrait', FR.portrait(True)),
                     ('jordan_fit_idle_strip', strip)):
        d = write_art(name, im, out)
        print('wrote %s.png %s + .aseprite, round trip: %s' % (name, im.size, d or 'identical'))
    for name, b, a in FR.numbers():
        print('%-22s before: black %5.2f%%, colours %2d, opaque %4d | after: black %5.2f%%, colours %2d, opaque %4d'
              % (name, 100 * b['black'], b['colours'], b['opaque'], 100 * a['black'], a['colours'], a['opaque']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
