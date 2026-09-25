"""Danny's juggle sheet and his mat shadow.

    python dexport.py           build, lint and print the layout numbers. It writes NOTHING, anywhere.
    python dexport.py --preview also the previews (sheets, 4x strip, grid, the game-scale GIF) into the
                                scratch folder (JUGGLE_PREVIEW_DANNY). Nothing under Assets is touched.
    python dexport.py --ship    build and lint, then into Assets/Characters/Danny/Sumo/ (beside his other
                                evolved-form sheets): danny_juggle.png + .aseprite and
                                danny_leap_shadow.png + .aseprite, each written through a temp file, saved
                                as .aseprite with the Aseprite CLI, exported back and compared pixel for
                                pixel (art_source/imgdiff.py). A lint failure or a round-trip difference
                                stops it before anything lands.

Never run another art_source export script bare: most default to the live Assets.
The modules here are named d* on purpose: danny_sumo_v2, josh_redesign and josh_juggle all have an
export.py / measure.py / zoom.py, and a bare name must never pick up another folder's.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dposes as PZ             # noqa: E402
import dparts as D              # noqa: E402
import dlint                    # noqa: E402
import dview as V               # noqa: E402
import dshadow                  # noqa: E402
from PIL import Image           # noqa: E402

K = D.K
AS = os.path.dirname(HERE)
jpreview = D.load('jpreview', os.path.join(AS, 'josh_juggle', 'jpreview.py'))
imgdiff = D.load('imgdiff', os.path.join(AS, 'imgdiff.py'))

NAME = 'danny_juggle'
SHADOW = 'danny_leap_shadow'
SUMO = os.path.normpath(os.path.join(AS, '..', 'Assets', 'Characters', 'Danny', 'Sumo'))
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
    air = list(range(1, 7))
    top_all = min(min(y for (x, y) in frames[i]) for i in air)
    top_body = min(min(y for (x, y) in bodies[i]) for i in air)
    cx = [sum(x for x, y in bodies[i]) / len(bodies[i]) for i in range(2, 7)]
    cy = [sum(y for x, y in bodies[i]) / len(bodies[i]) for i in range(2, 7)]
    return dict(top_all=top_all, top_body=top_body, centroid=(sum(cx) / len(cx), sum(cy) / len(cy)))


def ship_one(im, name):
    tmp = tempfile.mkdtemp()
    png_t = os.path.join(tmp, name + '.png')
    ase_t = os.path.join(tmp, name + '.aseprite')
    back = os.path.join(tmp, 'rt.png')
    im.save(png_t)
    subprocess.run([ASEPRITE, '-b', png_t, '--save-as', ase_t], check=True, capture_output=True)
    subprocess.run([ASEPRITE, '-b', ase_t, '--save-as', back], check=True, capture_output=True)
    d = imgdiff.pixel_diff(Image.open(png_t), Image.open(back))
    if d:
        raise SystemExit('%s: round trip differs before shipping: %s' % (name, d))
    png = os.path.join(SUMO, name + '.png')
    ase = os.path.join(SUMO, name + '.aseprite')
    shutil.copyfile(png_t, png)
    shutil.copyfile(ase_t, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    return png, ase, imgdiff.pixel_diff(Image.open(png), Image.open(back2)), imgdiff.pixel_diff(Image.open(png), im)


def previews(sheet, shadow, frames):
    os.makedirs(V.SCRATCH, exist_ok=True)
    sheet.save(os.path.join(V.SCRATCH, NAME + '.png'))
    shadow.save(os.path.join(V.SCRATCH, SHADOW + '.png'))
    strip = Image.new('RGBA', sheet.size, (46, 49, 58, 255))
    strip.alpha_composite(sheet)
    strip.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(
        os.path.join(V.SCRATCH, NAME + '_strip_4x.png'))
    V.grid(frames, 2, cols=4, names=[n for n, _, _ in PZ.FRAMES]).save(
        os.path.join(V.SCRATCH, NAME + '_grid_2x.png'))
    sh4 = Image.new('RGBA', shadow.size, (120, 124, 136, 255))
    sh4.alpha_composite(shadow)
    sh4.resize((shadow.width * 4, shadow.height * 4), Image.NEAREST).save(
        os.path.join(V.SCRATCH, SHADOW + '_4x.png'))
    idle = Image.open(os.path.join(SUMO, 'danny_sumo_idle.png')).convert('RGBA').crop((0, 0, D.FW, D.FH))
    gif_path = os.path.join(V.SCRATCH, NAME + '_game.gif')
    n, dur, g = jpreview.render(gif_path, sheet, PZ.W, PZ.H, PZ.FEET, [t for _, _, t in PZ.FRAMES],
                                idle, (88, 143),
                                dict(image=shadow, hframes=3, pivot=(72, 14), alpha=0.35, step=100.0),
                                canvas=(1120, 820), boss_x=480, ground_y=790, player_x=742, apex=150)
    print('previews in %s (GIF: %d frames, %.2f s)' % (V.SCRATCH, n, dur))


def main():
    shipping = '--ship' in sys.argv
    preview = '--preview' in sys.argv
    fatal = dlint.main(verbose=True)
    sheet, frames, bodies = build()
    shadow = dshadow.sheet()
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
    print('shadow           %s %dx%d: 3 frames of %dx%d, pivot (72, 14), ellipses %s'
          % (SHADOW, shadow.width, shadow.height, dshadow.W, dshadow.H, ' '.join(dshadow.sizes(shadow))))
    if preview:
        previews(sheet, shadow, frames)
    if fatal:
        raise SystemExit('lint failed; nothing shipped')
    if shipping:
        for im, name in ((sheet, NAME), (shadow, SHADOW)):
            png, ase, d2, d3 = ship_one(im, name)
            print('\nwrote %s\nwrote %s' % (png, ase))
            print('round trip .aseprite -> .png: %s' % (d2 or 'pixel-identical'))
            print('shipped .png vs the build:   %s' % (d3 or 'pixel-identical'))
            if d2 or d3:
                raise SystemExit(1)
    elif not preview:
        print('\n(nothing written: --preview for the previews, --ship for Assets/Characters/Danny/Sumo/)')


if __name__ == '__main__':
    main()
