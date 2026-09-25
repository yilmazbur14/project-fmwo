"""Build Danny's fight effects (and his tug-of-war meter), check them, and (only with --ship) ship them:
the FX to Assets/Characters/Danny/FX, the meter to Assets/UI (each part with its pre-scaled _3x copy).

  python dfx_export.py                 build every sheet into the scratchpad (OUT) and print the numbers;
                                       touches nothing in the project
  python dfx_export.py --ship --only NAME [NAME ...] [--replace NAME ...]
                                       copy the named sheets into the project, save each .aseprite beside it
                                       with the Aseprite CLI, and round-trip that .aseprite back to a PNG checked
                                       by art_source/imgdiff.py pixel_diff (a meter part's _3x copy is checked
                                       against its 1x part upscaled)

--only is required with --ship, and it never overwrites a file in the project that isn't named on --replace,
so nothing can be shipped by accident and no shipped sheet can be clobbered. NAME is the 1x PNG's file name.
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

import dfx_pal as pal  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

PROJ = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
FX_DIR = PROJ + '/Assets/Characters/Danny/FX'
UI_DIR = PROJ + '/Assets/UI'
OUT = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/danny_fx/out'
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'

SHEETS = [
    ('dfx_glob', 'danny_worm_glob.png'), ('dfx_splat', 'danny_worm_splat.png'),
    ('dfx_puddle', 'danny_worm_puddle.png'), ('dfx_root', 'danny_worm_root.png'),
    ('dfx_target', 'danny_slam_target.png'), ('dfx_impact', 'danny_slam_impact.png'),
    ('dfx_quake', 'danny_quake_ring.png'), ('dfx_trail', 'danny_headbutt_trail.png'),
    ('dfx_zzz', 'danny_sleep_z.png'), ('dfx_regen', 'danny_regen.png'), ('dfx_skid', 'danny_sumo_dust.png'),
]


def build():
    """name -> (1x image, destination folder, note, make_3x)"""
    out = {}
    for mod, name in SHEETS:
        m = __import__(mod)
        if hasattr(m, 'rows_of_frames'):
            im = pal.sheet(m.rows_of_frames())
            n = '%d x %d of %dx%d' % (m.FRAMES, m.ROWS, m.FRAME_SIZE[0], m.FRAME_SIZE[1])
        else:
            fr = m.frames()
            im = pal.strip(fr)
            assert im.size == (m.FRAME_SIZE[0] * len(fr), m.FRAME_SIZE[1]), (name, im.size)
            n = '%d frames of %dx%d' % (len(fr), m.FRAME_SIZE[0], m.FRAME_SIZE[1])
        out[name] = (im, FX_DIR, '%s  (%s)' % (n, m.NOTE), False)
    import dfx_tug as tug
    for part, frames in tug.parts().items():
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
    if only:
        unknown = only - set(built)
        if unknown:
            print('REFUSED: no such sheet: %s' % ', '.join(sorted(unknown)))
            return 1
    for name, (im, dest, note, make3) in built.items():
        im.save(os.path.join(OUT, name))
        if make3:
            up3(im).save(os.path.join(OUT, name[:-4] + '_3x.png'))
        st = pal.stats(im)
        print('%-28s %5dx%-4d colours %2d  alphas %-22s %s' % (name, im.width, im.height, st['colours'],
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
        targets = [dst, ase] + ([dst[:-4] + '_3x.png'] if make3 else [])
        for p in targets:
            if os.path.exists(p) and name not in replace:
                print('REFUSED: %s exists; name %s on --replace to overwrite' % (p, name))
                return 1
        shutil.copyfile(src, dst)
        aseprite(dst, '--save-as', ase)
        rt = os.path.join(OUT, 'roundtrip_' + name)
        aseprite(ase, '--save-as', rt)
        diff = pixel_diff(Image.open(dst), Image.open(rt))
        same_src = pixel_diff(Image.open(src), Image.open(dst))
        line = '%-28s shipped to %s; .aseprite round trip: %s; copy check: %s' % (
            name, os.path.relpath(dest, PROJ), diff or 'identical', same_src or 'identical')
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
