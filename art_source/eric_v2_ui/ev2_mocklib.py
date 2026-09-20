"""Compositing helpers for the game-scale mocks. The base layers are real captures of Eric's fight
(capture_layers.gd): the world with his and the player's sprites hidden, and the HUD alone on a
transparent background. Sprites and the new UI are placed the way the scenes place them:
  Eric    body origin, scale 3, Sprite2D centred at (0,-32) texels: frame texel (fx, fy) is drawn at
          (ox - 384 + 3fx, oy - 384 + 3fy).
  Player  body origin, scale 2: 4-direction frames (32x32) centred on it; uppercut frames (48x64)
          centred on it with offset (0,-16) texels.
  HUD     CanvasLayer, unaffected by the finisher's zoom; the _3x art at scale 1.
The finisher's zoom is ScreenView.apply(): screen = zoom * world + round(view/2 - centre * zoom).

The captures live outside the project, in EV2_CAPTURES (default <work>/captures). Make them with:
  CAP_OUT=<that dir> CAP_MODE=v1 Godot.exe --path <project> --position 100,100 --resolution 480x270
      --fixed-fps 30 --script art_source/eric_v2_ui/capture_layers.gd
The small window still yields 1920x1080 frames: the script renders the root viewport at that size."""
import os
from PIL import Image, ImageDraw, ImageFont
from ev2_common import work

ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/'
FONT = 'C:/Users/theyi/OneDrive/Documents/new-game-project/fonts/PixelifySans.ttf'
CAP = (os.environ.get('EV2_CAPTURES') or work('captures')).replace(os.sep, '/')
VIEW = (1920, 1080)

_cache = {}


def img(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert('RGBA')
    return _cache[path]


def canvas_img(c, scale=1):
    """a Canvas (hex strings / None) -> PIL RGBA, nearest-scaled"""
    im = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
    px = im.load()
    for y in range(c.h):
        for x in range(c.w):
            v = c.p[y][x]
            if v:
                px[x, y] = (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255)
    if scale != 1:
        im = im.resize((c.w * scale, c.h * scale), Image.NEAREST)
    return im


def world():
    return img(os.path.join(CAP, 'world_v1.png')).copy()


def hud():
    return img(os.path.join(CAP, 'hud_v1.png'))


def eric(layer, frame, origin=(960, 380), flip=False, lift=0, sheet='Characters/Eric/eric_sheet_v2.png'):
    s = img(ASSETS + sheet)
    f = s.crop((frame * 256, 0, frame * 256 + 256, 192))
    if flip:
        f = f.transpose(Image.FLIP_LEFT_RIGHT)
    f = f.resize((768, 576), Image.NEAREST)
    layer.alpha_composite(f, (int(origin[0] - 384), int(origin[1] - 384 - lift)))


def eric_point(texel, origin=(960, 380), flip=False):
    """screen/world position of the centre of a texel on Eric's frames"""
    fx, fy = texel
    if flip:
        fx = 255 - fx
    return (origin[0] - 384 + 3 * fx + 1.5, origin[1] - 384 + 3 * fy + 1.5)


def player4(layer, frame, body, flip=False):
    s = img(ASSETS + 'Characters/MainPlayer/player_4dir_sheet.png')
    c, r = frame % 10, frame // 10
    f = s.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    if flip:
        f = f.transpose(Image.FLIP_LEFT_RIGHT)
    f = f.resize((64, 64), Image.NEAREST)
    layer.alpha_composite(f, (int(body[0] - 32), int(body[1] - 32)))


def player_up(layer, frame, body, flip=False, super_=False):
    s = img(ASSETS + 'Characters/MainPlayer/player_uppercut%s.png' % ('_super' if super_ else ''))
    f = s.crop((frame * 48, 0, frame * 48 + 48, 64))
    if flip:
        f = f.transpose(Image.FLIP_LEFT_RIGHT)
    f = f.resize((96, 128), Image.NEAREST)
    layer.alpha_composite(f, (int(body[0] - 48), int(body[1] - 32 - 64)))


def place(layer, im, at):
    layer.alpha_composite(im, (int(round(at[0])), int(round(at[1]))))


def zoomed(world_layer, zoom, focus, shake=(0, 0)):
    """the world as ScreenView draws it at `zoom` around `focus`"""
    hx, hy = VIEW[0] / 2.0 / zoom, VIEW[1] / 2.0 / zoom
    cx = min(max(focus[0], hx), VIEW[0] - hx)
    cy = min(max(focus[1], hy), VIEW[1] - hy)
    ox = round(VIEW[0] / 2.0 - cx * zoom) + shake[0]
    oy = round(VIEW[1] / 2.0 - cy * zoom) + shake[1]
    out = world_layer.transform(VIEW, Image.AFFINE, (1.0 / zoom, 0, -ox / zoom, 0, 1.0 / zoom, -oy / zoom),
                                resample=Image.NEAREST, fillcolor=(0, 0, 0, 255))
    to_screen = lambda p: (zoom * p[0] + ox, zoom * p[1] + oy)
    return out, to_screen


def label(im, text, at, size=26, fill=(251, 242, 54), bg=(16, 14, 26, 230)):
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, size)
    box = d.textbbox(at, text, font=font)
    d.rectangle((box[0] - 8, box[1] - 6, box[2] + 8, box[3] + 6), fill=bg)
    d.text(at, text, font=font, fill=fill)


def zoom_crop(im, box, s):
    c = im.crop(box)
    return c.resize((c.width * s, c.height * s), Image.NEAREST)
