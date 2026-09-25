"""Josh's juggle sheet.

    python export.py            build, lint and print the layout numbers. It writes NOTHING, anywhere.
    python export.py --preview  also the previews (sheet, 4x strip, grid, the game-scale GIF) into the
                                scratch folder (JUGGLE_PREVIEW). Nothing under Assets is touched.
    python export.py --ship     build and lint, then Assets/Characters/Josh/josh_juggle.png and .aseprite:
                                written through a temp file, the .aseprite saved with the Aseprite CLI,
                                exported back and compared pixel for pixel (art_source/imgdiff.py);
                                a lint failure or a round-trip difference stops it before anything lands.

Never run another art_source export script bare: most default to the live Assets.

Josh keeps his own shadow: Assets/Characters/Josh/Cards/josh_shadow.png (4 frames of 80x24, pivot
(40, 12), the frame index is his height), the one his glider flight already uses, so there is no
josh_leap_shadow.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import poses as PZ              # noqa: E402
import jparts as P              # noqa: E402
import jkit as K                # noqa: E402
import lint                     # noqa: E402
import view as V                # noqa: E402
import jpreview                 # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image           # noqa: E402

NAME = 'josh_juggle'
ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh'))
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
TAGS = {'launch': (0, 1), 'tumble': (2, 6), 'crash': (7, 9), 'down': (10, 11)}


def build():
    frames, bodies = [], []
    for name, fn, _ in PZ.FRAMES:
        frames.append(fn())
        bodies.append(dict(PZ.REC['body']))
    sheet = Image.new('RGBA', (PZ.W * len(frames), PZ.H), (0, 0, 0, 0))
    for i, px in enumerate(frames):
        sheet.alpha_composite(V.image(px), (PZ.W * i, 0))
    return sheet, frames, bodies


def layout(frames, bodies):
    """The numbers the coder wires: tumble centre, top row, and where he is on each frame."""
    air = list(range(1, 7))
    top_all = min(min(y for (x, y) in frames[i]) for i in air)
    top_body = min(min(y for (x, y) in bodies[i]) for i in air)
    cx = [sum(x for x, y in bodies[i]) / len(bodies[i]) for i in range(2, 7)]
    cy = [sum(y for x, y in bodies[i]) / len(bodies[i]) for i in range(2, 7)]
    return dict(top_all=top_all, top_body=top_body,
                centroid=(sum(cx) / len(cx), sum(cy) / len(cy)))


def ship(sheet):
    tmp = tempfile.mkdtemp()
    png_t = os.path.join(tmp, NAME + '.png')
    ase_t = os.path.join(tmp, NAME + '.aseprite')
    back = os.path.join(tmp, 'rt.png')
    sheet.save(png_t)
    subprocess.run([ASEPRITE, '-b', png_t, '--save-as', ase_t], check=True, capture_output=True)
    subprocess.run([ASEPRITE, '-b', ase_t, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png_t), Image.open(back))
    if d:
        raise SystemExit('round trip differs before shipping: %s' % d)
    png = os.path.join(ASSETS, NAME + '.png')
    ase = os.path.join(ASSETS, NAME + '.aseprite')
    shutil.copyfile(png_t, png)
    shutil.copyfile(ase_t, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    d2 = pixel_diff(Image.open(png), Image.open(back2))
    d3 = pixel_diff(Image.open(png), sheet)
    return png, ase, d2, d3


def previews(sheet, frames):
    os.makedirs(V.SCRATCH, exist_ok=True)
    sheet.save(os.path.join(V.SCRATCH, NAME + '.png'))
    strip = Image.new('RGBA', sheet.size, (46, 49, 58, 255))
    strip.alpha_composite(sheet)
    strip.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(
        os.path.join(V.SCRATCH, NAME + '_strip_4x.png'))
    V.grid(frames, 4, cols=4, names=[n for n, _, _ in PZ.FRAMES]).save(
        os.path.join(V.SCRATCH, NAME + '_grid_4x.png'))
    gif_path = os.path.join(V.SCRATCH, NAME + '_game.gif')
    idle = Image.open(os.path.join(ASSETS, 'josh_idle.png')).convert('RGBA').crop((0, 0, 80, 80))
    shadow = dict(image=Image.open(os.path.join(ASSETS, 'Cards', 'josh_shadow.png')).convert('RGBA'),
                  hframes=4, pivot=(40, 12), alpha=0.35, step=80.0)
    n, dur, g = jpreview.render(gif_path, sheet, PZ.W, PZ.H, PZ.FEET, [t for _, _, t in PZ.FRAMES],
                                idle, (40, 79), shadow, canvas=(600, 620), boss_x=230, ground_y=585,
                                player_x=372, apex=220)
    print('previews in %s (GIF: %d frames, %.2f s)' % (V.SCRATCH, n, dur))


def main():
    shipping = '--ship' in sys.argv
    preview = '--preview' in sys.argv
    fatal = lint.main(verbose=True)
    sheet, frames, bodies = build()
    lay = layout(frames, bodies)
    print()
    print('sheet            %dx%d: %d frames of %dx%d (hframes %d)'
          % (sheet.width, sheet.height, len(frames), PZ.W, PZ.H, len(frames)))
    print('feet             %s' % (PZ.FEET,))
    print('tumble_centre    %s  (the pivot he turns on in 2-6; his drawn centroid there is %.1f, %.1f)'
          % (PZ.AIR_AT, lay['centroid'][0], lay['centroid'][1]))
    print('top_row          %d  (highest drawn row on an air frame, 1-6; his body alone reaches %d)'
          % (lay['top_all'], lay['top_body']))
    for tag, (a, b) in TAGS.items():
        print('  %-7s frames %d-%d  %s' % (tag, a, b, ', '.join('%.2f' % PZ.FRAMES[i][2] for i in range(a, b + 1))))
    if preview:
        previews(sheet, frames)
    if fatal:
        raise SystemExit('lint failed; nothing shipped')
    if shipping:
        png, ase, d2, d3 = ship(sheet)
        print('\nwrote %s\nwrote %s' % (png, ase))
        print('round trip .aseprite -> .png: %s' % (d2 or 'pixel-identical'))
        print('shipped .png vs the build:   %s' % (d3 or 'pixel-identical'))
        if d2 or d3:
            raise SystemExit(1)
    elif not preview:
        print('\n(nothing written: --preview for the previews, --ship for Assets/Characters/Josh/%s.png)' % NAME)


if __name__ == '__main__':
    main()
