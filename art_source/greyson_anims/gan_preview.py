"""Previews of Greyson's attack sheets. Writes ONLY into a preview folder (the session scratchpad by
default, or the folder given); a folder inside the live Assets tree is refused (by realpath).

    python -B gan_preview.py [out_dir] [sheet ...]

  <sheet>_4x.png    the sheet's frames at 4x on the preview background, labelled with their times
  <sheet>_3x.gif    the animation at game scale, at its intended timings
  contact_4x.png    every sheet, one row each
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

DEFAULT_OUT = os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\greyson_anims')
BG = (46, 49, 58, 255)
DARK = (16, 17, 22, 255)
SHEETS = ('gan_idle', 'gan_throw', 'gan_teleport', 'gan_slam', 'gan_hit', 'gan_broken', 'gan_defeat',
          'gan_victory')


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def modules(names=None):
    out = []
    for n in SHEETS:
        try:
            m = __import__(n)
        except ImportError:
            continue
        if names and m.NAME not in names and n not in names:
            continue
        out.append(m)
    return out


def on_bg(im):
    o = Image.new('RGBA', im.size, BG)
    o.alpha_composite(im)
    return o


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def frame_images(mod):
    return [B.image(px) for px, _fx in mod.frames()]


def strip_4x(mod, s=4, lh=18):
    fr = frame_images(mod)
    w = len(fr) * (112 * s + 6) + 6
    out = Image.new('RGBA', (w, 112 * s + lh + 6), DARK)
    d = ImageDraw.Draw(out)
    for i, im in enumerate(fr):
        x = 6 + i * (112 * s + 6)
        t = mod.TIMES[min(i, len(mod.TIMES) - 1)]
        d.text((x + 2, 3), '%s f%d  %.2fs%s' % (mod.NAME, i, t, '  (loops)' if mod.LOOP and i == 0 else ''),
               fill=(228, 228, 234, 255))
        out.alpha_composite(up(on_bg(im), s), (x, lh))
    return out


def gif(mod, path, s=3, hold_end=0.6):
    fr = frame_images(mod)
    ims, durs = [], []
    for i, im in enumerate(fr):
        ims.append(up(on_bg(im), s).convert('RGB'))
        durs.append(int(round(1000 * mod.TIMES[min(i, len(mod.TIMES) - 1)])))
    if not mod.LOOP:
        durs[-1] += int(hold_end * 1000)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1,
                optimize=False)


def main(argv):
    out = os.path.abspath(argv[0]) if argv else DEFAULT_OUT
    if _under(out, os.path.join(B.ROOT, 'Assets')):
        raise SystemExit('refusing %s: previews never go into Assets' % out)
    os.makedirs(out, exist_ok=True)
    mods = modules(argv[1:])
    strips = []
    for m in mods:
        st = strip_4x(m)
        st.save(os.path.join(out, m.NAME + '_4x.png'))
        gif(m, os.path.join(out, m.NAME + '_3x.gif'))
        strips.append(st)
    if len(strips) > 1:
        w = max(s.width for s in strips)
        h = sum(s.height + 4 for s in strips)
        c = Image.new('RGBA', (w, h), DARK)
        y = 0
        for s in strips:
            c.alpha_composite(s, (0, y))
            y += s.height + 4
        c.save(os.path.join(out, 'contact_4x.png'))
    print('previews in', out)


if __name__ == '__main__':
    main(sys.argv[1:])
