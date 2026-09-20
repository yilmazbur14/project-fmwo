"""Game-scale review mocks: the key frames composited into a real captured frame of Eric's arena
(1920x1080, captured from EricBossFightScene with his and the player's sprites hidden), with the
player at 2x for scale and the existing daze stars at the proposed head pixel.

Placement follows the scenes exactly:
  Eric   body origin (960, 380), scale 3, Sprite2D offset (0,-32) centred -> frame texel (fx, fy) is
         drawn at screen (ox - 384 + 3fx, oy - 384 + 3fy). A juggle lift moves only the sprite offset up.
  Player body origin, scale 2: 4-direction frames (32x32) centred on it; uppercut frames (48x64) centred
         on it with offset (0,-16) texels. Feet sit 30 px under the origin.
  Stars  daze_stars.png frame 0, 3x, pivot (24,13) on the head pixel.

    python mock.py <keys_dir> <arena_png> <out_dir>
"""
import os
import sys
from PIL import Image

ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets'
PLAYER4 = ASSETS + '/Characters/MainPlayer/player_4dir_sheet.png'
UPPER = ASSETS + '/Characters/MainPlayer/player_uppercut.png'
STARS = ASSETS + '/Effects/daze_stars.png'
MAT_FEET_Y = 572          # Eric's feet row on screen at his spawn (texel row 191, bottom edge)
CRATER_TEXEL_Y = 188      # crater centre (64,25) sits on his frame texel (128,188): the impact point


def eric(canvas, frame_png, origin=(960, 380), lift=0, flip=False):
    im = Image.open(frame_png).convert('RGBA')
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    big = im.resize((im.size[0] * 3, im.size[1] * 3), Image.NEAREST)
    canvas.alpha_composite(big, (int(origin[0] - 384), int(origin[1] - 384 - lift)))


def eric_px(origin, fx, fy, lift=0):
    return (origin[0] - 384 + 3 * fx + 1.5, origin[1] - 384 + 3 * fy + 1.5 - lift)


def decal(canvas, png, centre, pivot, scale=3):
    im = Image.open(png).convert('RGBA')
    big = im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)
    canvas.alpha_composite(big, (int(centre[0] - pivot[0] * scale), int(centre[1] - pivot[1] * scale)))


def player(canvas, frame, feet, sheet='4dir', flip=False):
    if sheet == '4dir':
        im = Image.open(PLAYER4).convert('RGBA')
        fw, fh, cols = 32, 32, 10
        c, r = frame % cols, frame // cols
        f = im.crop((c * fw, r * fh, c * fw + fw, r * fh + fh))
        off = (0, 0)
    else:
        im = Image.open(UPPER).convert('RGBA')
        fw, fh = 48, 64
        f = im.crop((frame * fw, 0, frame * fw + fw, fh))
        off = (0, -16)
    if flip:
        f = f.transpose(Image.FLIP_LEFT_RIGHT)
    big = f.resize((fw * 2, fh * 2), Image.NEAREST)
    ox, oy = feet[0], feet[1] - 30
    canvas.alpha_composite(big, (int(ox - fw + off[0] * 2), int(oy - fh + off[1] * 2)))


def stars(canvas, at, frame=0):
    im = Image.open(STARS).convert('RGBA')
    f = im.crop((frame * 48, 0, frame * 48 + 48, 24)).resize((144, 72), Image.NEAREST)
    canvas.alpha_composite(f, (int(at[0] - 72), int(at[1] - 39)))


def shadow(canvas, centre, rx, ry, alpha=90):
    sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    px = sh.load()
    cx, cy = centre
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            # chunky: evaluate on the 3 px texel grid so the shadow stays pixel art
            tx, ty = (x - cx) // 3 * 3 + 1.5, (y - cy) // 3 * 3 + 1.5
            if (tx / rx) ** 2 + (ty / ry) ** 2 <= 1.0:
                px[x, y] = (0, 0, 0, alpha)
    canvas.alpha_composite(sh)


def label(canvas, text, xy):
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(canvas)
    try:
        f = ImageFont.load_default(size=26)
    except TypeError:
        f = ImageFont.load_default()
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0, 255), font=f)
    d.text((x, y), text, fill=(255, 255, 255, 255), font=f)


def main():
    keys, arena, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    K = lambda n: os.path.join(keys, n + '.png')
    base = Image.open(arena).convert('RGBA')
    O = (960, 380)
    head = tuple(float(v) for v in open(os.path.join(keys, 'broken_head_pixel.txt')).read().split())

    # 1) BROKEN: slumped by his planted sword, daze stars on, player snapped in at his side
    c = base.copy()
    eric(c, K('slumped'), O)
    stars(c, eric_px(O, *head))
    player(c, 20, (1130, MAT_FEET_Y))
    c.save(os.path.join(out, 'mock_broken.png'))

    # 2) JUGGLE: mid-air tumble 200 px above his shadow; the sword stays planted where the Break happened;
    #    the player (on his left) drops back down from the uppercut that launched him
    c = base.copy()
    eric(c, K('planted_sword'), O)
    shadow(c, (960, MAT_FEET_Y - 4), 108, 21)
    eric(c, K('tumble'), O, lift=200)
    player(c, 7, (925, MAT_FEET_Y), sheet='upper')
    c.save(os.path.join(out, 'mock_juggle_air.png'))

    # 3) KNIGHT BREAKER crash: the tier-3 shove carried him 240 px right of the Break spot, into a crater
    L2 = (1200, 380)
    crater_at = eric_px(L2, 128, CRATER_TEXEL_Y)
    c = base.copy()
    eric(c, K('planted_sword'), O)
    decal(c, K('crater_settle'), crater_at, (64, 25))
    eric(c, K('crash'), L2)
    player(c, 9, (760, MAT_FEET_Y), sheet='upper')
    c.save(os.path.join(out, 'mock_crash_crater.png'))

    # 4) lying KO'd in the crater, sword still stuck in the mat behind the player
    c = base.copy()
    eric(c, K('planted_sword'), O)
    decal(c, K('crater_held'), crater_at, (64, 25))
    eric(c, K('lying'), L2)
    player(c, 30, (770, MAT_FEET_Y))
    c.save(os.path.join(out, 'mock_lying.png'))

    # 5) WINDED: leaning on the planted sword after a chain, player closing in
    c = base.copy()
    eric(c, K('winded'), O)
    player(c, 20, (1150, MAT_FEET_Y))
    c.save(os.path.join(out, 'mock_winded.png'))

    # 6) LINE-UP: every key frame at true game scale on the mat (feet rows y 470 and 930)
    c = base.copy()
    row1 = [('reel', 330), ('kneel', 720), ('slumped', 1110), ('winded', 1500)]
    for n, x in row1:
        eric(c, K(n), (x, 470 - 192))
    stars(c, eric_px((1110, 470 - 192), *head))
    lo = (1480, 930 - 192)
    decal(c, K('crater_held'), eric_px(lo, 128, CRATER_TEXEL_Y), (64, 25))
    row2 = [('tumble', 420, 110), ('crash', 950, 0), ('lying', 1480, 0)]
    for n, x, lift in row2:
        if n == 'tumble':
            shadow(c, (x, 926), 108, 21)
        eric(c, K(n), (x, 930 - 192), lift=lift)
    player(c, 30, (1730, 470))
    player(c, 20, (1760, 930))
    for n, x in row1:
        label(c, n, (x - 40, 482))
    for n, x, lift in row2:
        label(c, n + (' (lifted 110 px)' if lift else ''), (x - 60, 940))
    c.save(os.path.join(out, 'mock_lineup.png'))
    print('mocks written to', out)


if __name__ == '__main__':
    main()
