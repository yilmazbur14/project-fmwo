"""Build Greyson's fight effects (and his hype meter), check them, and (only with --ship, after the user approves)
ship them: the FX to Assets/Characters/Greyson/FX, the meter to Assets/UI (each part with its pre-scaled _3x copy).

  python gfx_export.py                 build every sheet into the scratchpad (OUT) and print the numbers;
                                       touches nothing in the project
  python gfx_export.py --ship --only NAME [NAME ...] [--replace NAME ...]
                                       copy the named sheets into the project, save each .aseprite beside it
                                       with the Aseprite CLI, and round-trip that .aseprite back to a PNG checked
                                       by art_source/imgdiff.py pixel_diff (a meter part's _3x copy is checked
                                       against its 1x part upscaled)

--only is required with --ship, and it never overwrites a file in the project that isn't named on --replace.
"""
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image  # noqa: E402

import gfx_pal as pal  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

PROJ = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
FX_DIR = PROJ + '/Assets/Characters/Greyson/FX'
UI_DIR = PROJ + '/Assets/UI'
OUT = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/greyson_fx/out'
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
FX_MODULES = ['gfx_plate', 'gfx_erupt', 'gfx_warp', 'gfx_roar', 'gfx_bomb']


def build():
    """name.png -> (image, destination folder, note, make_3x)"""
    out = {}
    for mod in FX_MODULES:
        m = __import__(mod)
        rows_of = getattr(m, 'ROWS', {})
        for name, (fn, (fw, fh)) in m.SHEETS.items():
            if name in rows_of:
                # a grid sheet (hframes x vframes), row by row
                rows = rows_of[name]()
                im = pal.sheet(rows)
                cols = max(len(r) for r in rows)
                assert im.size == (fw * cols, fh * len(rows)), (name, im.size)
                n = sum(len(r) for r in rows)
                out[name + '.png'] = (im, FX_DIR, '%d frames of %dx%d in a grid, hframes %d vframes %d'
                                      % (n, fw, fh, cols, len(rows)), False)
                continue
            frames = fn()
            im = pal.strip(frames)
            assert im.size == (fw * len(frames), fh), (name, im.size)
            out[name + '.png'] = (im, FX_DIR, '%d frames of %dx%d' % (len(frames), fw, fh), False)
    import gfx_dissolve as D
    out['player_disintegrate.png'] = (D.sheet(), FX_DIR, '12 frames x 4 rows of 48x48', False)
    import gfx_meter as M
    for part, frames in M.parts().items():
        ims = [c.image() for c in frames]
        w, h = ims[0].size
        im = Image.new('RGBA', (w * len(ims), h), (0, 0, 0, 0))
        for i, fr in enumerate(ims):
            im.paste(fr, (i * w, 0))
        out[part + '.png'] = (im, UI_DIR, '%d x %dx%d, meter part' % (len(ims), w, h), True)
    return out


def up3(im):
    return im.resize((im.width * 3, im.height * 3), Image.NEAREST)


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('aseprite %s failed: %s %s' % (args, r.stdout, r.stderr))


def names_after(argv, flag):
    if flag not in argv:
        return None
    out = []
    for a in argv[argv.index(flag) + 1:]:
        if a.startswith('--'):
            break
        out.append(a)
    return set(out)


def main(argv):
    ship = '--ship' in argv
    replace = names_after(argv, '--replace') or set()
    only = names_after(argv, '--only')
    if ship and not only:
        print('REFUSED: --ship needs --only NAME [NAME ...]')
        return 1
    os.makedirs(OUT, exist_ok=True)
    built = build()
    if only and only - set(built):
        print('REFUSED: no such sheet: %s' % ', '.join(sorted(only - set(built))))
        return 1
    for name, (im, dest, note, make3) in built.items():
        im.save(os.path.join(OUT, name))
        if make3:
            up3(im).save(os.path.join(OUT, name[:-4] + '_3x.png'))
        st = pal.stats(im)
        print('%-30s %5dx%-4d colours %2d  alphas %-26s %s' % (name, im.width, im.height, st['colours'],
                                                              st['alphas'], note))
    if not ship:
        print('built into', OUT, '(pass --ship --only NAME ... to ship)')
        return 0
    bad = 0
    for name, (im, dest, note, make3) in built.items():
        if name not in only:
            continue
        os.makedirs(dest, exist_ok=True)
        src = os.path.join(OUT, name)
        dst = os.path.join(dest, name)
        ase = dst[:-4] + '.aseprite'
        for p in [dst, ase] + ([dst[:-4] + '_3x.png'] if make3 else []):
            if os.path.exists(p) and name not in replace:
                print('REFUSED: %s exists; name %s on --replace to overwrite' % (p, name))
                return 1
        shutil.copyfile(src, dst)
        aseprite(dst, '--save-as', ase)
        rt = os.path.join(OUT, 'roundtrip_' + name)
        aseprite(ase, '--save-as', rt)
        diff = pixel_diff(Image.open(dst), Image.open(rt))
        same_src = pixel_diff(Image.open(src), Image.open(dst))
        line = '%-30s shipped; .aseprite round trip: %s; copy check: %s' % (name, diff or 'identical', same_src or 'identical')
        bad += bool(diff) + bool(same_src)
        if make3:
            d3 = dst[:-4] + '_3x.png'
            shutil.copyfile(os.path.join(OUT, name[:-4] + '_3x.png'), d3)
            diff3 = pixel_diff(Image.open(d3), up3(Image.open(dst).convert('RGBA')))
            line += '; _3x: %s' % (diff3 or 'exact')
            bad += bool(diff3)
        print(line)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
