"""Build Greyson's doom-orb sheets (gdo_art.py) and their contract.json into a directory you name. It has NO default
destination, so a bare run does nothing but print this help; it never writes into Assets on its own.

  python gdo_export.py --out DIR           write every sheet (PNG, and its .aseprite via the Aseprite CLI, round-trip
                                           checked by art_source/imgdiff.py) plus contract.json into DIR
  python gdo_export.py --out DIR --no-ase  PNGs and contract.json only

The approval pass went to art_source/greyson_doom_orb/approval/. Shipping, once the user approves, is copying
those files into Assets/Characters/Greyson/FX/ (the coordinator's call, not this script's).
"""
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'greyson_fx'))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image  # noqa: E402

import gfx_pal as pal  # noqa: E402
import gdo_art as A  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'


def contract():
    s = A.SCALE if hasattr(A, 'SCALE') else 3
    orb_centres = [[0, -r] for r in A.RADII]
    return {
        'status': 'APPROVAL PASS 2026-09-30, not shipped. Every sheet: scale 3, whole texels, never rotated, no dither.',
        'offset_rule': 'offset = frame centre - pivot, in texels, for a centred Sprite2D at scale 3 (px = texels x 3). '
                       'Grids read row by row: frame n is column n % hframes, row n / hframes.',
        'greyson_doom_orb': {
            'file': 'greyson_doom_orb.png', 'frame': [A.OW, A.OW], 'hframes': 5, 'vframes': 6,
            'rows': 'row s = stage s + 1 (stages 1-6)',
            'pivot': list(A.FOOT), 'offset': [0, A.OW // 2 - A.FOOT[1]],
            'pivot_is': "the orb's FOOT, the bottom of its sphere: the same point on every stage, so it grows upward",
            'anchor': 'foot = his crown (GreysonArtLayout.crown(anim)) + (0, -6) px; at HOME in a pose: (960, 296)',
            'radius_texels': A.RADII, 'radius_px': [r * 3 for r in A.RADII],
            'centre_from_foot_texels': orb_centres,
            'loop_frames': [0, 1, 2, 3], 'loop_frame_time': A.FRAME_TIMES,
            'arrival_flash': {'frame': 4, 'time': A.FLASH_TIME,
                              'rule': 'as a stage banks, show its f4 once, then loop f0-f3'},
            'stage_6': 'f0 is greyson_bomb f1 pixel for pixel, less the muzzle beam: the hand-off frame',
            'hand_off': {'bomb_frame': A.BOMB_HANDOFF_FRAME,
                         'rule': "move the orb's foot to the cannon's muzzle + (0, -9) px (tween it up with the arm), "
                                 "show stage 6 f0, then swap to greyson_bomb at frame 1 with its pivot on the muzzle "
                                 "and run the gather from there (f1-f15). Only the muzzle beam appears; nothing jumps."},
            'keep_out': 'at HOME the tallest pre-bomb stage (5) with its haze and lightning tops out at y 188; the '
                        'HUD block ends at y 180 over his head. Stage 6 only shows as the spirit bomb starts and the '
                        'HUD goes. Fade the orb to 0.4 while the player overlaps it.',
        },
        'greyson_doom_orb_glow': {
            'file': 'greyson_doom_orb_glow.png', 'frame': [A.OW, A.OW], 'hframes': 5, 'vframes': 6,
            'pivot': list(A.FOOT), 'offset': [0, A.OW // 2 - A.FOOT[1]], 'blend': 'add (CanvasItemMaterial.BLEND_MODE_ADD)',
            'rule': 'the same frame index as the orb, drawn under it on the same node',
        },
        'greyson_doom_orb_burst': {
            'file': 'greyson_doom_orb_burst.png', 'frame': [A.BW_, A.BW_], 'hframes': 6, 'vframes': 2,
            'rows': 'row 0 small (stages 1-3), row 1 big (stages 4-5)',
            'pivot': [int(A.BC[0]), int(A.BC[1])], 'offset': [0, 0],
            'place': "on the orb's centre: its foot + centre_from_foot_texels[stage] x 3",
            'frame_times': A.BURST_TIMES, 'loop': False,
            'beats': 'f0 flash, f1 cracks, f2-f5 flies apart (the hurt is already over: it is the hit that pops it)',
        },
        'greyson_hype_streak': {
            'file': 'greyson_hype_streak.png', 'frame': [A.SW_, A.SW_], 'hframes': 4, 'vframes': A.HEADINGS,
            'rows': 'heading row k = round(atan2(vy, vx) / 22.5 deg) mod 16 (screen axes, y down): row 0 flying right, '
                    '4 down, 8 left, 12 up; pick it each frame from the velocity',
            'pivot': [int(A.SC[0]), int(A.SC[1])], 'offset': [0, 0], 'pivot_is': "its head; the tail trails behind",
            'frame_time': A.STREAK_TIME, 'loop': True,
            'flight': 'about 0.4 s from the crowd (the stands along the top, ringside down the sides) into the orb; '
                      'on a hit, the same sheet flying back out to the crowd',
            'alternative': 'greyson_hype_streak_cyan.png, identical layout, in the crowd energy cyan',
        },
        'greyson_doom_vignette': {
            'file': 'greyson_doom_vignette.png', 'frame': [A.VW, A.VH], 'hframes': 1,
            'pivot': [0, 0], 'screen_layer': 'top-left (0,0) at scale 3, under the HUD',
            'rule': 'from stage 4: modulate alpha 0.5 at stage 4, 0.75 at stage 5, 1.0 as the bomb starts; a heartbeat '
                    'lifts it +0.25 for 0.12 s then eases back over 0.3 s, about once every 0.9 s',
        },
    }


def main(argv):
    if '--out' not in argv:
        print(__doc__)
        return 1
    out = argv[argv.index('--out') + 1]
    ase = '--no-ase' not in argv
    os.makedirs(out, exist_ok=True)
    bad = 0
    for name, (fn, size) in A.SHEETS.items():
        rows = fn()
        im = pal.sheet(rows)
        p = os.path.join(out, name + '.png')
        im.save(p)
        st = pal.stats(im)
        line = '%-28s %5dx%-4d %d x %d of %dx%d  colours %d alphas %s' % (
            name, im.width, im.height, max(len(r) for r in rows), len(rows), size[0], size[1], st['colours'], st['alphas'])
        if ase:
            a = p[:-4] + '.aseprite'
            subprocess.run([ASEPRITE, '-b', p, '--save-as', a], check=True, capture_output=True)
            rt = os.path.join(out, '_rt_' + name + '.png')
            subprocess.run([ASEPRITE, '-b', a, '--save-as', rt], check=True, capture_output=True)
            d = pixel_diff(Image.open(p), Image.open(rt))
            os.remove(rt)
            line += '  .aseprite round trip: %s' % (d or 'identical')
            bad += bool(d)
        print(line)
    with open(os.path.join(out, 'contract.json'), 'w', encoding='utf-8') as f:
        json.dump(contract(), f, indent=2)
    print('contract.json written;', out)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
