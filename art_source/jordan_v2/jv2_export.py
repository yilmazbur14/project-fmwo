"""Write Jordan v2's approval sprite: jordan_redesign_v2.png (2 frames of 96x96 side by side, feet on
row 95, body centred on column 48: 0 idle with the box, 1 the fist-pump), the .aseprite beside it, and
a round-trip check that the .aseprite re-exports to exactly the same pixels (imgdiff.pixel_diff:
alpha everywhere and colour wherever a pixel shows).

A bare run writes nothing:

    python jv2_export.py                   # print this and exit
    python jv2_export.py <scratch_dir>     # write both files there, for checking
    python jv2_export.py --ship            # write Assets/Characters/Jordan/jordan_redesign_v2.{png,aseprite}

A scratch folder that resolves into the live Assets tree is refused (realpath, so 8.3 short names
can't slip past); only --ship writes there. It only ever writes those two file names, never the
approved jordan_redesign.png or any sheet of the animation set. Nothing is written unless both frames
pass the audit (no keyline gaps, stray pixels, pinholes, semi-alpha or keys outside the approved 40).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jv2_base as B  # noqa: E402
import jv2_frames as F  # noqa: E402
from PIL import Image  # noqa: E402

NAME = 'jordan_redesign_v2'


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def sheet():
    f0, f1 = F.frames()
    out = Image.new('RGBA', (192, 96), (0, 0, 0, 0))
    out.alpha_composite(f0, (0, 0))
    out.alpha_composite(f1, (96, 0))
    return out, (f0, f1)


def check(frames):
    """Every frame must be clean and stand on row 95, and the face must still be the approved face
    pixel for pixel; returns printable lines, raises on a problem."""
    import jv2_head
    if not jv2_head._selftest():
        raise SystemExit('refusing to write: the face rows no longer match the approved rig')
    lines, bad = [], []
    for i, f in enumerate(frames):
        st = B.stats(f)
        a = B.audit(F.frame_px(i), F.fx_pixels(i))
        bb = f.getbbox()
        lines.append('frame %d: opaque %d, colours %d, black %.1f%%, rows %d..%d (%d tall), semi %d, '
                     'gaps %d, lone %d, holes %d, stray keys %s'
                     % (i, st['opaque'], st['colours'], 100 * st['black'], bb[1], bb[3] - 1, bb[3] - bb[1],
                        st['semi'], len(a['gaps']), len(a['lone']), len(a['holes']), a['keys'] or 'none'))
        if st['semi'] or a['gaps'] or a['lone'] or a['holes'] or a['keys'] or bb[3] != 96:
            bad.append(i)
    if bad:
        raise SystemExit('\n'.join(lines) + '\nrefusing to write: frame(s) %s fail the audit' % bad)
    return lines


def aseprite(*args):
    subprocess.run([B.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == '--ship':
        out_dir = B.ASSETS
    else:
        out_dir = os.path.abspath(argv[0])
        if _under(out_dir, os.path.join(B.ROOT, 'Assets')):
            raise SystemExit('refusing %s: it is inside the live Assets tree; use --ship to publish' % out_dir)
    im, frames = sheet()
    lines = check(frames)
    tmp = tempfile.mkdtemp(prefix='jv2_')
    tmp_png = os.path.join(tmp, NAME + '.png')
    tmp_ase = os.path.join(tmp, NAME + '.aseprite')
    im.save(tmp_png)
    aseprite(tmp_png, '--save-as', tmp_ase)
    back = os.path.join(tmp, 'rt.png')
    aseprite(tmp_ase, '--save-as', back)
    d = B.pixel_diff(Image.open(tmp_png), Image.open(back))
    if d:
        raise SystemExit('the .aseprite does not round-trip: %s' % d)
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, NAME + '.png')
    ase = os.path.join(out_dir, NAME + '.aseprite')
    os.replace(tmp_png, png)
    os.replace(tmp_ase, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    aseprite(ase, '--save-as', back2)
    d2 = B.pixel_diff(Image.open(png), Image.open(back2))
    print('wrote', png, im.size)
    print('wrote', ase)
    print('round trip (.aseprite -> png vs png, where they landed):', d2 or 'identical')
    for ln in lines:
        print(ln)
    st = B.stats(im)
    print('sheet: opaque %d, colours %d, black %.1f%%, semi %d' % (st['opaque'], st['colours'], 100 * st['black'],
                                                                  st['semi']))
    return 1 if d2 else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
