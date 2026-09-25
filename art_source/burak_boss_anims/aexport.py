"""Write Captain Burak's fight body sheets: each <sheet>.png (frames in a strip, frame 0 leftmost) with
its .aseprite beside it, the .aseprite round-tripped through Aseprite against the PNG pixel for pixel
(imgdiff), the full audit (aaudit) run on every frame, and the anchors printed for the coder.

A bare run writes nothing:

    python aexport.py <out_dir> [SHEET ...]   write the named sheets (default all) into <out_dir>
    python aexport.py --ship [SHEET ...]      write them into Assets/Characters/BurakBoss/

--ship is the only way this script touches Assets/, and it only ever writes <sheet>.png and
<sheet>.aseprite for the sheets named in sheets.SHEETS. A sheet that fails its audit is not written.
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import aaudit  # noqa: E402
import akit as A  # noqa: E402
import kit  # noqa: E402
import sheets as S  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ASSET_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'BurakBoss')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')


def strip(name):
    frames = S.SHEETS[name]()
    P0 = frames[0][1]
    im = Image.new('RGBA', (P0.fw * len(frames), P0.fh), (0, 0, 0, 0))
    for i, (n, P, h) in enumerate(frames):
        im.paste(A.image(P), (i * P.fw, 0))
    return im, frames


def write_sheet(name, out_dir, allowed):
    im, frames = strip(name)
    bad = []
    lines = []
    for i, (n, P, hold) in enumerate(frames):
        r = aaudit.audit_frame(A.render(P), P.fw, P.fh, allowed, bust=P.crop is not None)
        crown, mouth = aaudit.crown_mouth(P)
        anc = S.anchors(name, i, P)
        bad += ['f%d: %s' % (i, b) for b in r['bad']]
        lines.append('  f%-2d %-9s %.2fs  opaque %4d  colours %2d  black %4.1f%%  crown %s  mouth %s  %s'
                     % (i, n, hold, r['opaque'], r['colours'], 100 * r['black'], crown, mouth,
                        '  '.join('%s %s' % kv for kv in anc.items())))
    st = kit.stats(im)
    print('%s: %d frames of %dx%d, %dx%d; sheet colours %d, black %.1f%%'
          % (name, len(frames), frames[0][1].fw, frames[0][1].fh, im.width, im.height, st['colours'],
             100 * st['black']))
    for line in lines:
        print(line)
    if bad:
        print('  NOT WRITTEN, audit failed:', bad)
        return False
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    im.save(png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d1, d2 = pixel_diff(im, Image.open(png)), pixel_diff(im, Image.open(back))
    print('  wrote %s and .aseprite; png vs build %s, aseprite round trip %s'
          % (png, d1 or 'identical', d2 or 'identical'))
    return not (d1 or d2)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = ASSET_DIR if argv[0] == '--ship' else os.path.abspath(argv[0])
    if argv[0] != '--ship' and os.path.normcase(out_dir).startswith(os.path.normcase(os.path.join(ROOT, 'Assets'))):
        print('refusing to write into Assets/ without --ship')
        return 2
    names = argv[1:] or list(S.SHEETS)
    unknown = [n for n in names if n not in S.SHEETS]
    if unknown:
        print('unknown sheets:', unknown)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    allowed = aaudit.approved_colours()
    ok = True
    for name in names:
        ok = write_sheet(name, out_dir, allowed) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
