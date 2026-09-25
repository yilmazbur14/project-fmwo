"""Build every Inferno effects sheet, check it, and (only with --write) ship it to Assets/Characters/Bixby.

  python export.py                  build into the scratchpad (out/), print the numbers, touch nothing else
  python export.py --write          also copy each PNG into Assets in one write, save its .aseprite beside it
                                    with the Aseprite CLI, and round-trip that .aseprite back to a PNG checked
                                    by art_source/imgdiff.py pixel_diff
  python export.py --write --only NAME [NAME ...] --replace NAME [NAME ...]
                                    ship only the named sheets, and allow replacing those already-shipped
                                    files (by file name); unnamed sheets are left alone

It never overwrites a file in Assets that isn't named on --replace, so a bare --write can't clobber anyone
else's sheet, and a bare run (no --write) writes only into the scratchpad.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import burst  # noqa: E402
import edge  # noqa: E402
import fireball  # noqa: E402
import flood  # noqa: E402
import impact  # noqa: E402
import marker  # noqa: E402
import pal  # noqa: E402
import suction  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

from PIL import Image  # noqa: E402

ASSETS = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby'
SCRATCH = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_inferno_fx/out'
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'


def sheets():
    """name -> (image, frame size, layout note)."""
    fb = fireball.frames()
    return {
        'bixby_fireball.png': (pal.sheet(fb), (16, 24), '2 rows x 4: row 0 rising, row 1 falling'),
        'bixby_fireball_marker.png': (pal.sheet([marker.frames()]), (44, 22), '4 frames'),
        'bixby_fireball_impact.png': (impact.image(impact.frames()), (48, 40), '5 frames'),
        'bixby_inferno_flood.png': (pal.sheet([flood.frames()]), (57, 41), '11 frames'),
        'bixby_inferno_edge.png': (pal.sheet([edge.frames()]), (edge.W, edge.H), '11 frames'),
        'bixby_inferno_burst.png': (pal.sheet([burst.frames()]), (64, 64), '7 frames'),
        'bixby_suction.png': (pal.sheet(suction.frames()), (24, 24), '3 rows x 4: 0, 45, 90 degrees'),
    }


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('aseprite %s failed: %s %s' % (args, r.stdout, r.stderr))


def names_after(argv, flag):
    """The file names listed after a flag, up to the next flag."""
    if flag not in argv:
        return None
    out = []
    for a in argv[argv.index(flag) + 1:]:
        if a.startswith('--'):
            break
        out.append(a)
    return set(out)


def main(argv):
    write = '--write' in argv
    replace = names_after(argv, '--replace') or set()
    only = names_after(argv, '--only')
    os.makedirs(SCRATCH, exist_ok=True)
    built = sheets()
    for name, (im, (fw, fh), note) in built.items():
        assert im.width % fw == 0 and im.height % fh == 0, (name, im.size, (fw, fh))
        path = os.path.join(SCRATCH, name)
        im.save(path)
        st = pal.stats(im)
        print('%-28s %4dx%-3d frames %dx%d (%s)  colours %2d  black %5.2f%%  semi %d'
              % (name, im.width, im.height, fw, fh, note, st['colours'], st['black%'], st['semi']))
    if not write:
        print('built into', SCRATCH, '(pass --write to ship)')
        return 0
    bad = 0
    for name in built:
        if only is not None and name not in only:
            continue
        src = os.path.join(SCRATCH, name)
        dst = os.path.join(ASSETS, name)
        ase = dst[:-4] + '.aseprite'
        for p in (dst, ase):
            if os.path.exists(p) and os.path.basename(p).replace('.aseprite', '.png') not in replace:
                print('REFUSED: %s exists; name it on --replace to overwrite' % p)
                return 1
        shutil.copyfile(src, dst)                      # one write into Assets
        aseprite(dst, '--save-as', ase)
        rt = os.path.join(SCRATCH, 'roundtrip_' + name)
        aseprite(ase, '--save-as', rt)
        diff = pixel_diff(Image.open(dst), Image.open(rt))
        same_src = pixel_diff(Image.open(src), Image.open(dst))
        print('%-28s shipped; .aseprite round trip: %s; copy check: %s'
              % (name, diff or 'identical', same_src or 'identical'))
        bad += bool(diff) + bool(same_src)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
