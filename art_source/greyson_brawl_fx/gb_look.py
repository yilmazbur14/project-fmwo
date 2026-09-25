"""Iteration viewer: each sheet zoomed on the mat's green and on the dark ringside."""
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gb_pal as pal        # noqa: E402

# where the zooms go: never beside the rig. The first argument is required.
OUT = sys.argv[1] if len(sys.argv) > 1 else None
MAT = (126, 168, 91, 255)
DARK = (25, 23, 37, 255)


def show(name, frames, z, gap=2):
    im = pal.strip(frames)
    fw, fh = len(frames[0][0]), len(frames[0])
    n = len(frames)
    rows = []
    for bg in (MAT, DARK):
        row = Image.new('RGBA', ((fw + gap) * n * z, fh * z), (60, 60, 60, 255))
        for i in range(n):
            fr = im.crop((i * fw, 0, i * fw + fw, fh))
            b = Image.new('RGBA', fr.size, bg)
            b.alpha_composite(fr)
            row.paste(b.resize((fw * z, fh * z), Image.NEAREST), (i * (fw + gap) * z, 0))
        rows.append(row)
    out = Image.new('RGBA', (rows[0].width, rows[0].height * 2 + 6), (0, 0, 0, 255))
    out.paste(rows[0], (0, 0))
    out.paste(rows[1], (0, rows[0].height + 6))
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, name + '.png'))
    print(name, pal.stats(im), im.size)


if __name__ == '__main__':
    if OUT is None:
        sys.exit('usage: python gb_look.py <out_dir> [debris land rubble arrow punch]')
    which = sys.argv[2:] or ['debris', 'land']
    if 'debris' in which:
        import gb_debris as d
        show('debris', d.debris_frames(), 6)
        show('debris_shadow', d.shadow_frames(), 8)
    if 'land' in which:
        import gb_debris as d
        show('debris_land', d.land_frames(), 4)
    if 'rubble' in which:
        import gb_rubble as r
        show('rubble_mound', r.mound_frames(), 3)
        show('rubble_bits', r.bits_frames(), 6)
    if 'arrow' in which:
        import gb_arrow as a
        show('arrow', a.frames(), 6)
    if 'punch' in which:
        import gb_punch as p
        show('hook', p.hook_frames(), 3)
        show('straight', p.straight_frames(), 4)
        show('impact', p.impact_frames(), 4)
