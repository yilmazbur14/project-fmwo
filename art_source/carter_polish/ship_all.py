"""Render, check and (with --ship) write Carter's core combat set in the polish style.

    python ship_all.py              # render + lint + numbers + previews into the scratchpad ONLY
    python ship_all.py --ship       # ... and overwrite the live sheets in Assets/Characters/Carter

Every sheet keeps its file name, size, frame count and frame order (combat.SHEETS). With --ship each
PNG is written whole to a temp file beside it and moved over the live one in one os.replace, because
the user plays with the Godot editor open; its .aseprite is saved by Aseprite's CLI the same way, then
read back and compared with imgdiff.pixel_diff. Nothing is written if any sheet fails its lint.

Previews (scratchpad carter_polish/all_sheets): contact_sheet_4x.png, before_after_2x.png and one GIF
per animation at 3x, timed from Scripts/CarterArtLayout.gd.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.dont_write_bytecode = True

from PIL import Image, ImageDraw                                              # noqa: E402
import lib                                                                    # noqa: E402
import combat                                                                 # noqa: E402
import mark as MK                                                             # noqa: E402
from imgdiff import pixel_diff                                                # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Carter')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
PREVIEWS = os.environ.get('CARTER_POLISH_PREVIEWS', os.path.join(
    os.environ.get('TEMP', tempfile.gettempdir()), 'claude',
    'C--Users-theyi-OneDrive-Documents-new-game-project', 'a7fc2846-afef-472d-979b-e17143793a0f',
    'scratchpad', 'carter_polish', 'all_sheets'))
F = 96
BG = (30, 32, 40, 255)

# seconds per frame, from Scripts/CarterArtLayout.gd (FINAL_ANIMS / FINAL_AURA)
TIMES = {
    'carter_idle.png': [0.18],
    'carter_eye_flash.png': [0.12, 0.09, 0.09, 0.26],
    'carter_rush.png': [0.05, 0.045, 0.06, 0.055],
    'carter_rush_pass.png': [0.045, 0.05, 0.07],
    'carter_spent.png': [0.2, 0.17, 0.17, 0.2],
    'carter_hit.png': [0.07, 0.09],
    'carter_defeat.png': [0.11, 0.11, 0.10, 0.13, 0.18, 0.7],
    'carter_aura.png': [0.11],
    'carter_akuma.png': [0.8],
    'carter_akuma_pose.png': [1.0],
}
LOOPS = {'carter_idle.png', 'carter_spent.png', 'carter_aura.png', 'carter_akuma.png'}
NO_FEET = {'carter_aura.png'}


def render(name):
    fn, n = combat.SHEETS[name]
    sheet = Image.new('RGBA', (F * n, F), (0, 0, 0, 0))
    for i in range(n):
        sheet.alpha_composite(fn(i).image(), (i * F, 0))
    return sheet


def lint(name, im):
    errs = []
    live = Image.open(os.path.join(ASSETS, name))
    if im.size != live.size:
        errs.append('size %s, the live sheet is %s' % (im.size, live.size))
    st = lib.stats(im)
    if st['alphas'] not in ([0, 255], [255]):
        errs.append('non-binary alpha')
    pal = {v[:3] for v in lib.PAL.values()}
    if any(c[3] and c[:3] not in pal for c in lib.flat(im)):
        errs.append('colours outside the palette')
    if name not in NO_FEET:
        for f in range(im.width // F):
            rows = [y for y in range(F) for x in range(f * F, f * F + F) if im.getpixel((x, y))[3]]
            if max(rows) != 95:
                errs.append('frame %d: lowest opaque row %d, not 95' % (f, max(rows)))
    if name == 'carter_akuma.png':
        # the mark on frame 2 must be the mark rig's own pixels, exactly where the glow expects them
        ten = MK.ten_back()
        bad = [q for q, k in ten.items() if im.getpixel((2 * F + q[0], q[1]))[:3] != lib.PAL[k][:3]]
        if bad:
            errs.append('frame 2: %d mark pixels differ from intro_sigil.paint_rest' % len(bad))
    return errs


def write_whole(path, im):
    """The whole PNG to `name.png.part` beside it (an extension Godot never imports), then one
    os.replace, so the open editor only ever sees the old file or the new one."""
    tmp = path + '.part'
    im.save(tmp, format='PNG')
    os.replace(tmp, path)


def ship_one(name, im):
    png = os.path.join(ASSETS, name)
    ase = os.path.splitext(png)[0] + '.aseprite'
    write_whole(png, im)
    work = tempfile.mkdtemp()
    tmp_ase = os.path.join(work, os.path.basename(ase))
    subprocess.run([ASEPRITE, '-b', png, '--save-as', tmp_ase], check=True, capture_output=True)
    os.replace(tmp_ase, ase)
    back = os.path.join(work, 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    return pixel_diff(Image.open(png), Image.open(back))


# ------------------------------------------------------------------ previews

def label(im, text, x, y):
    ImageDraw.Draw(im).text((x, y), text, fill=(235, 235, 240, 255))


def contact_sheet(sheets, s=4):
    w = max(im.width for im in sheets.values()) * s + 40
    h = sum(F * s + 30 for _ in sheets) + 20
    out = Image.new('RGBA', (w, h), BG)
    y = 10
    for name, im in sheets.items():
        label(out, name, 20, y)
        out.alpha_composite(lib.upscale(im, s), (20, y + 16))
        y += F * s + 30
    return out


def before_after(sheets, s=2):
    rows = []
    for name, im in sheets.items():
        old = Image.open(os.path.join(ASSETS, name)).convert('RGBA')
        rows.append((name, old, im))
    w = max(r[1].width + r[2].width for r in rows) * s + 80
    h = len(rows) * (F * s + 26) + 20
    out = Image.new('RGBA', (w, h), BG)
    y = 10
    for name, old, new in rows:
        label(out, name + '   before | after', 20, y)
        out.alpha_composite(lib.upscale(old, s), (20, y + 14))
        out.alpha_composite(lib.upscale(new, s), (40 + old.width * s, y + 14))
        y += F * s + 26
    return out


def gif(name, im, s=3, under=None):
    n = im.width // F
    times = TIMES[name]
    frames, durs = [], []
    for i in range(n):
        fr = Image.new('RGBA', (F * s, F * s), BG)
        if under is not None:
            fr.alpha_composite(lib.upscale(under, s))
        fr.alpha_composite(lib.upscale(im.crop((i * F, 0, i * F + F, F)), s))
        frames.append(fr.convert('RGB'))
        durs.append(int(round(1000 * times[min(i, len(times) - 1)])))
    if name not in LOOPS:
        durs[-1] += 600          # hold the last frame so a one-shot reads before it loops
    path = os.path.join(PREVIEWS, name.replace('.png', '_3x.gif'))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)
    return path


def aura_gif(aura_im, idle_im, s=3):
    """the ambient aura at its own rate (0.11 s) under the idle loop (0.18 s), as the game layers them"""
    frames, durs = [], []
    t = 0.0
    for step in range(36):
        a = aura_im.crop(((step % 6) * F, 0, (step % 6) * F + F, F))
        r, g, b, al = a.split()
        a = Image.merge('RGBA', (r, g, b, al.point(lambda v: int(v * 0.75))))
        k = int(t / 0.18) % 4
        fr = Image.new('RGBA', (F * s, F * s), BG)
        fr.alpha_composite(lib.upscale(a, s))
        fr.alpha_composite(lib.upscale(idle_im.crop((k * F, 0, k * F + F, F)), s))
        frames.append(fr.convert('RGB'))
        durs.append(110)
        t += 0.11
    path = os.path.join(PREVIEWS, 'carter_aura_under_idle_3x.gif')
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)
    return path


def main():
    shipping = '--ship' in sys.argv
    os.makedirs(PREVIEWS, exist_ok=True)
    sheets, failed = {}, False
    print('%-24s %-10s %6s %8s %8s' % ('sheet', 'size', 'frames', 'colours', 'black'))
    for name in combat.SHEETS:
        im = render(name)
        sheets[name] = im
        st = lib.stats(im)
        errs = lint(name, im)
        print('%-24s %-10s %6d %8d %7.1f%%%s' % (name, '%dx%d' % im.size, im.width // F, st['colours'],
                                                100 * st['black'], '' if not errs else '   LINT: ' + '; '.join(errs)))
        failed |= bool(errs)
    body = [n for n in sheets if n != 'carter_aura.png']
    allpx = [c for n in body for c in lib.flat(sheets[n]) if c[3]]
    black = sum(1 for c in allpx if c[:3] == (0, 0, 0))
    print('all figure sheets together: %d colours, %.1f%% black' % (len(set(allpx)), 100.0 * black / len(allpx)))
    for name, im in sheets.items():
        im.save(os.path.join(PREVIEWS, name))
    contact_sheet(sheets).save(os.path.join(PREVIEWS, 'contact_sheet_4x.png'))
    before_after(sheets).save(os.path.join(PREVIEWS, 'before_after_2x.png'))
    for name, im in sheets.items():
        gif(name, im)
    aura_gif(sheets['carter_aura.png'], sheets['carter_idle.png'])
    print('previews in', PREVIEWS)
    if failed:
        print('LINT FAILED - nothing written')
        return 1
    if shipping:
        bad = 0
        for name, im in sheets.items():
            d = ship_one(name, im)
            print('wrote %-24s round trip: %s' % (name, d or 'identical'))
            bad += bool(d)
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
