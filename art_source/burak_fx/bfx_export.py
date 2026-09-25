"""Build Captain Burak's effects, check them, and (only with --ship) ship them to
Assets/Characters/BurakBoss/FX.

  python bfx_export.py                 build every sheet into the scratchpad (OUT) and print the numbers;
                                       touches nothing in the project
  python bfx_export.py --ship --only NAME [NAME ...] [--replace NAME ...]
                                       copy the named sheets into Assets/Characters/BurakBoss/FX, save each
                                       .aseprite beside it with the Aseprite CLI, and round-trip that
                                       .aseprite back to a PNG checked by art_source/imgdiff.py pixel_diff

--only is required with --ship, and it never overwrites a file in Assets that isn't named on --replace, so
nothing can be shipped by accident and no shipped sheet can be clobbered.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image  # noqa: E402

import bfx_pal as pal  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ASSETS = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/BurakBoss/FX'
OUT = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/burak_fx/out'
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'

SHEETS = [
    ('bfx_barrel', 'burak_barrel.png'), ('bfx_blast', 'burak_blast.png'),
    ('bfx_screen', 'burak_blast_screen.png'), ('bfx_ball', 'burak_ball.png'), ('bfx_pips', 'burak_pips.png'),
    ('bfx_break', 'burak_barrel_break.png'), ('bfx_land', 'burak_barrel_land.png'),
    ('bfx_marker', 'burak_barrel_marker.png'), ('bfx_muzzle', 'burak_muzzle.png'),
    ('bfx_slash', 'burak_slash_trail.png'), ('bfx_clash', 'burak_clash.png'),
]


def sheets():
    out = {}
    for mod, name in SHEETS:
        if os.path.exists(os.path.join(HERE, mod + '.py')):
            m = __import__(mod)
            out[name] = (m.frames(), m.FRAME_SIZE, m.NOTE)
    return out


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
    built = sheets()
    for name, (frames, (fw, fh), note) in built.items():
        im = pal.strip(frames)
        assert im.size == (fw * len(frames), fh), (name, im.size)
        im.save(os.path.join(OUT, name))
        st = pal.stats(im)
        print('%-24s %5dx%-4d %2d frames of %dx%d  colours %2d  alphas %s  (%s)'
              % (name, im.width, im.height, len(frames), fw, fh, st['colours'], st['alphas'], note))
    if not ship:
        print('built into', OUT, '(pass --ship --only NAME ... to ship)')
        return 0
    os.makedirs(ASSETS, exist_ok=True)
    bad = 0
    for name in built:
        if name not in only:
            continue
        src = os.path.join(OUT, name)
        dst = os.path.join(ASSETS, name)
        ase = dst[:-4] + '.aseprite'
        for p in (dst, ase):
            if os.path.exists(p) and os.path.basename(p).replace('.aseprite', '.png') not in replace:
                print('REFUSED: %s exists; name it on --replace to overwrite' % p)
                return 1
        shutil.copyfile(src, dst)
        aseprite(dst, '--save-as', ase)
        rt = os.path.join(OUT, 'roundtrip_' + name)
        aseprite(ase, '--save-as', rt)
        diff = pixel_diff(Image.open(dst), Image.open(rt))
        same_src = pixel_diff(Image.open(src), Image.open(dst))
        print('%-24s shipped; .aseprite round trip: %s; copy check: %s'
              % (name, diff or 'identical', same_src or 'identical'))
        bad += bool(diff) + bool(same_src)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
