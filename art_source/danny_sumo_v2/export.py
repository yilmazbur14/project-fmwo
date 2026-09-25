"""Build the approval-pass sheet for Danny's sumo redesign and everything that goes with it.

  python export.py <preview-dir> --ship

(Gated 2026-09-24: without --ship it refuses and writes nothing. The approval pass it writes,
Sumo/danny_sumo_redesign.png, is superseded by the shipped sheets; see export_all.py.)

Writes (new files only; no live Danny sheet is touched):
  Assets/Characters/Danny/Sumo/danny_sumo_redesign.png       2 frames of 176x144, horizontal strip
  Assets/Characters/Danny/Sumo/danny_sumo_redesign.aseprite  saved from that PNG by the Aseprite CLI
and in <preview-dir>:
  danny_redesign_before_after_4x.png   small form | approved idle | redesign f0 | f1, dark background
  danny_redesign_3x_on_mat.png         each frame at 3x on the arena mat beside the player
  roundtrip.png                        the .aseprite exported back, for the pixel_diff check

Frame 0: the idle ready stance (sleepy, bubble). Frame 1: the hundred-hand slap winding up (awake).
Contract, as the approved sheets: 176x144 frames, anchor (88, 144), soles' keyline on row 143.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from PIL import Image  # noqa: E402

import danny_v2  # noqa: E402
import slap  # noqa: E402
import previews  # noqa: E402
import measure  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ASEPRITE = r"C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe"
SUMO = os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'Sumo')
OUT_PNG = os.path.join(SUMO, 'danny_sumo_redesign.png')
OUT_ASE = os.path.join(SUMO, 'danny_sumo_redesign.aseprite')
FW, FH = 176, 144


def build_sheet():
    frames = [danny_v2.build().image(), slap.build().image()]
    sheet = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        assert f.size == (FW, FH), f.size
        sheet.alpha_composite(f, (i * FW, 0))
    return sheet


def contract(sheet):
    """The frame contract, checked rather than assumed."""
    for i in range(sheet.width // FW):
        f = sheet.crop((i * FW, 0, i * FW + FW, FH))
        x0, y0, x1, y1 = f.getbbox()
        a = f.getchannel('A')
        edge = [x for x in range(FW) if a.getpixel((x, FH - 1))]
        print('  frame %d: bbox %s, lowest opaque row %d, soles on row 143 at x %d..%d, bbox centre x %.1f'
              % (i, (x0, y0, x1, y1), y1 - 1, min(edge), max(edge), (x0 + x1) / 2.0))
        assert y1 - 1 == FH - 1, 'soles must sit on row 143'


def main(prev):
    os.makedirs(prev, exist_ok=True)
    for p in (OUT_PNG, OUT_ASE):
        if os.path.exists(p):
            print('overwriting the approval-pass file', os.path.basename(p))
    sheet = build_sheet()
    sheet.save(OUT_PNG)
    print('wrote', OUT_PNG)
    contract(sheet)

    # the editable file, saved by Aseprite itself from the PNG, then exported back and compared
    subprocess.run([ASEPRITE, '-b', OUT_PNG, '--save-as', OUT_ASE], check=True)
    rt = os.path.join(prev, 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', OUT_ASE, '--save-as', rt], check=True)
    print('wrote', OUT_ASE)
    d = pixel_diff(Image.open(OUT_PNG), Image.open(rt))
    print('  round trip .png -> .aseprite -> .png: %s' % ('pixel-identical' if d is None else d))

    # numbers: before (the approved sumo and the small form) and after
    print('measured (keyline = the colour on the silhouette edge):')
    before = [(os.path.join(SUMO, 'danny_sumo_idle.png'), 'approved sumo idle'),
              (os.path.join(SUMO, 'danny_sumo_slap.png'), 'approved sumo slap'),
              (os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'danny.png'), 'small form')]
    for path, name in before:
        print('  ' + measure.fmt('BEFORE ' + name, measure.measure(Image.open(path))))
    print('  ' + measure.fmt('AFTER  redesign sheet', measure.measure(sheet)))
    for i in range(2):
        f = sheet.crop((i * FW, 0, i * FW + FW, FH))
        print('  ' + measure.fmt('AFTER    frame %d' % i, measure.measure(f)))

    previews.before_after(sheet, prev)
    previews.scale_preview(sheet, prev)
    print('previews in', prev)


if __name__ == '__main__':
    if '--ship' not in sys.argv:
        raise SystemExit('export.py writes into Assets/Characters/Danny/Sumo; pass --ship to do that '
                         '(nothing was written)')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else os.path.join(HERE, 'out'))
