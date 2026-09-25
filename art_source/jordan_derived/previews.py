"""Review images for the portrait. Writes ONLY into the session scratchpad (dkit.PREVIEWS), never Assets/.

    python previews.py [portrait.png]    # default: the build in the scratchpad

  portrait_6x_vs_sprite.png   the sprite's head (frame 0 of jordan_redesign.png) at 6x and at 9x -
                              the portrait's own size - beside the portrait at 6x
  portrait_in_balloon.png     the dialogue balloon as Scenes/balloon.tscn lays it out, at screen
                              size: the 3x dialogue frame nine-sliced to 1596x252 (30px margins),
                              the 3x portrait frame (24px margins) round the 128x128 portrait, 30px
                              apart, the name and a line of his in Pixelify Sans at the theme's 33px
The ladder and menu before/after strips are written by ladder.py and menu.py, which own that data.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dkit                                                      # noqa: E402
from PIL import Image, ImageDraw, ImageFont                      # noqa: E402

UI = os.path.join(dkit.ASSETS, 'UI')
FONT = os.path.join(dkit.ROOT, 'fonts', 'PixelifySans.ttf')
LINE = "So you're the newcomer everyone keeps pinging me about."   # Dialogue/JordanPreFight.dialogue


def nine(tex, w, h, m):
    """A StyleBoxTexture's nine-slice (stretch mode, the default) with equal margins m."""
    tw, th = tex.size
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    xs = [(0, m, 0, m), (m, tw - m, m, w - m), (tw - m, tw, w - m, w)]
    ys = [(0, m, 0, m), (m, th - m, m, h - m), (th - m, th, h - m, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            piece = tex.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.alpha_composite(piece, (dx0, dy0))
    return out


def balloon(portrait):
    frame = Image.open(os.path.join(UI, 'ui_dialogue_frame_3x.png')).convert('RGBA')
    pframe = Image.open(os.path.join(UI, 'ui_portrait_frame_3x.png')).convert('RGBA')
    W, H = 1596, 252                                   # offsets 162/-162, -264/-12 on 1920x1080
    scene = Image.new('RGBA', (W + 40, H + 40), (34, 32, 52, 255))
    panel = nine(frame, W, H, 30)
    pf = nine(pframe, 128 + 48, 128 + 48, 24)
    pf.alpha_composite(portrait.convert('RGBA').resize((128, 128), Image.NEAREST), (24, 24))
    panel.alpha_composite(pf, (30, 30))
    d = ImageDraw.Draw(panel)
    font = ImageFont.truetype(FONT, 33)
    x = 30 + 176 + 30
    d.text((x, 30), 'Jordan', font=font, fill=(255, 255, 255, 255))
    d.text((x, 30 + 44), LINE, font=font, fill=(235, 235, 240, 255))
    scene.alpha_composite(panel, (20, 20))
    return scene


def compare(portrait):
    sprite = Image.open(dkit.SPRITE).convert('RGBA')
    head = sprite.crop((27, 8, 70, 51))              # the portrait's own window on frame 0
    return dkit.row([dkit.label(dkit.up(head, 6), 'sprite frame 0, x27..69 y8..50, 6x'),
                     dkit.label(dkit.up(head, 9), 'the same at 9x (the portrait\'s size at 6x)'),
                     dkit.label(dkit.up(portrait, 6), 'portrait.png 64x64 at 6x')])


def main(path=None):
    path = path or os.path.join(dkit.PREVIEWS, 'build', 'portrait.png')
    im = Image.open(path).convert('RGBA')
    print(dkit.preview(compare(im), 'portrait_6x_vs_sprite.png'))
    print(dkit.preview(balloon(im), 'portrait_in_balloon.png'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
