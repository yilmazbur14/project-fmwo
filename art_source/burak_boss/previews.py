"""Approval previews for Captain Burak. Writes ONLY to the folder given (the session scratchpad),
never into Assets/:

    python previews.py <out_dir> [<photo_dir>]

  frames_4x.png        both frames at 4x, plus frame 1 without its baked-in shot effects
  arena_3x.png         game scale (3x) on the arena mat: frame 0, frame 1, Matt (the newest approved
                       boss) and the player sprite, everyone on one floor line
  face_vs_photos.png   the face at 8x (both expressions) beside crops of the four photos
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import burak  # noqa: E402
import kit  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def asset(*parts):
    return Image.open(os.path.join(ROOT, 'Assets', *parts)).convert('RGBA')


def frames_4x(f0, f1, f1_clean):
    a = kit.label(kit.up(f0, 4), 'frame 0: idle')
    b = kit.label(kit.up(f1, 4), 'frame 1: the shot (FX baked in for approval)')
    c = kit.label(kit.up(f1_clean, 4), 'frame 1 without the FX, for judging the gun')
    return kit.row([a, b, c], gap=12)


def arena_3x(f0, f1):
    """Everyone at the game's 3x on the arena mat: Burak's two frames, Matt (96x96, the newest
    approved boss) and the player (32x32 frames, facing left toward them)."""
    mat = asset('Environment', 'arena_mat.png')
    matt = asset('Characters', 'Matt', 'matt.png').crop((0, 0, 96, 96))
    player = asset('Characters', 'MainPlayer', 'player_4dir_sheet.png').crop((0, 64, 32, 96))
    w, h = 360, 120
    scene = mat.crop((100, 60, 100 + w, 60 + h)).copy()
    floor = 112                                   # the row everyone stands on
    scene.alpha_composite(f0, (6, floor - 96))
    scene.alpha_composite(f1, (100, floor - 96))
    scene.alpha_composite(matt, (200, floor - 96))
    scene.alpha_composite(player, (306, floor - 32))
    return kit.label(kit.up(scene, 3, bg=(0, 0, 0, 255)),
                     'game scale (3x) on the arena mat: Burak frame 0, frame 1, Matt (approved boss), the player')


PHOTO_CROPS = {
    '15.jpg': (250, 880, 910, 1720),
    '16.jpg': (930, 380, 1260, 760),
    '17.jpg': (280, 660, 1160, 1600),
    '18.webp': (0, 640, 923, 1990),
}


def face_vs_photos(f0, f1, photo_dir, height=400):
    ims = []
    for name, box in PHOTO_CROPS.items():
        p = os.path.join(photo_dir, name) if photo_dir else ''
        if not p or not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGBA').crop(box)
        s = height / im.height
        ims.append(kit.label(im.resize((max(1, int(im.width * s)), height), Image.LANCZOS), name))
    box = (22, 0, 76, 50)
    ims.append(kit.label(kit.up(f0.crop(box), 8), 'sprite face, idle (8x)'))
    ims.append(kit.label(kit.up(f1.crop(box), 8), 'sprite face, the shot (8x)'))
    return kit.row(ims, gap=10)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    out = sys.argv[1]
    photos = sys.argv[2] if len(sys.argv) > 2 else ''
    os.makedirs(out, exist_ok=True)
    f0, f1 = burak.frames()
    f1_clean = kit.image(burak.frame_px(1, fx=False))
    frames_4x(f0, f1, f1_clean).save(os.path.join(out, 'frames_4x.png'))
    arena_3x(f0, f1).save(os.path.join(out, 'arena_3x.png'))
    face_vs_photos(f0, f1, photos).save(os.path.join(out, 'face_vs_photos.png'))
    print('previews written to', out)
