"""Build Greyson's FINAL BRAWL effect sheets. APPROVED 2026-09-24: see APPROVED.md.

    python gb_build.py <out_dir>     a scratch build, anywhere but Assets/
    python gb_build.py --ship        the shipped sheets, into Assets/Characters/Greyson/Brawl/

THERE IS NO DEFAULT OUTPUT, and nothing but --ship may write into Assets/: a bare run of an art export
once clobbered shipped art (the memory note on art exports run bare). After a --ship, re-save each
PNG as .aseprite with the Aseprite CLI and round-trip it through art_source/imgdiff.py pixel_diff.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import gb_pal as pal          # noqa: E402
import gb_debris              # noqa: E402
import gb_rubble              # noqa: E402
import gb_arrow               # noqa: E402
import gb_punch               # noqa: E402

SHEETS = [
    # name, frames, frame size (read off each module, never restated here), what
    ('brawl_debris', gb_debris.debris_frames, (gb_debris.W, gb_debris.H), 'falling chunk + dust trail'),
    ('brawl_debris_shadow', gb_debris.shadow_frames, (gb_debris.SW, gb_debris.SH), 'landing spot'),
    ('brawl_debris_land', gb_debris.land_frames, (gb_debris.LW, gb_debris.LH), 'landing impact + dust'),
    ('brawl_rubble_mound', gb_rubble.mound_frames, (gb_rubble.MW, gb_rubble.MH), 'wall/fill heaps'),
    ('brawl_rubble_bits', gb_rubble.bits_frames, (gb_rubble.BW, gb_rubble.BH), 'loose chunks'),
    ('brawl_arrow', gb_arrow.frames, (gb_arrow.W, gb_arrow.H), 'hook tell LEFT/RIGHT'),
    ('brawl_hook', gb_punch.hook_frames, (gb_punch.HW, gb_punch.HH), 'hook whoosh'),
    ('brawl_straight', gb_punch.straight_frames, (gb_punch.SW, gb_punch.SH), 'straight whoosh'),
    ('brawl_impact', gb_punch.impact_frames, (gb_punch.IW, gb_punch.IH), 'punch lands'),
]


SHIP_DIR = os.path.abspath(os.path.join(_HERE, '..', '..', 'Assets', 'Characters', 'Greyson', 'Brawl'))


def main(out, ship=False):
    real = os.path.realpath(out).replace('\\', '/').lower()
    if not ship:
        assert '/assets/' not in real + '/', 'only --ship writes into Assets: %s' % out
    os.makedirs(out, exist_ok=True)
    for name, fn, (fw, fh), what in SHEETS:
        frames = fn()
        im = pal.strip(frames)
        assert im.size == (fw * len(frames), fh), (name, im.size)
        im.save(os.path.join(out, name + '.png'))
        st = pal.stats(im)
        print('%-20s %2dx%-2d x%-2d %2d colours, alphas %s  (%s)' % (
            name, fw, fh, len(frames), st['colours'], st['alphas'], what))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('usage: python gb_build.py <out_dir> | --ship   (there is no default)')
    if sys.argv[1] == '--ship':
        main(SHIP_DIR, ship=True)
    else:
        main(sys.argv[1])
