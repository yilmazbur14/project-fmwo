"""Review images for Greyson's portrait. Writes ONLY into the session scratchpad (portrait.PREVIEWS).

    python -B previews.py

  greyson_portrait_before_after.png           the user's 05-27 drawing and the new portrait at 6x,
                                              beside the crop of frame 0 it came from at 9x (the
                                              same size)
  greyson_portrait_balloon_before_after.png   the dialogue balloon as Scenes/balloon.tscn lays it
                                              out, at screen size, with one of his lines, before and
                                              after
  greyson_portrait_in_the_cast.png            his portrait frame beside Jordan's and Josh's
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import portrait as P                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                      # noqa: E402

A = os.path.join(P.ROOT, 'Assets')
UI = os.path.join(A, 'UI')
FONT = os.path.join(P.ROOT, 'fonts', 'PixelifySans.ttf')
LINE = "Get UP, Computah! I skipped the gym for this!"          # Dialogue/ComputahOutro.dialogue
DARK = (10, 10, 12, 255)


def up(im, s, bg=P.K.BG):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im.convert('RGBA'))
    return b.resize((im.width * s, im.height * s), Image.NEAREST)


def label(im, text, pad=18):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 3), text, fill=(220, 220, 228, 255))
    return out


def row(ims, gap=10, bg=DARK):
    out = Image.new('RGBA', (sum(i.width for i in ims) + gap * (len(ims) - 1), max(i.height for i in ims)), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def nine(tex, w, h, m):
    """A StyleBoxTexture's nine-slice (stretch mode, the default) with equal margins m."""
    tw, th = tex.size
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    xs = [(0, m, 0, m), (m, tw - m, m, w - m), (tw - m, tw, w - m, w)]
    ys = [(0, m, 0, m), (m, th - m, m, h - m), (th - m, th, h - m, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            out.alpha_composite(tex.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST), (dx0, dy0))
    return out


def portrait_frame(im):
    pframe = Image.open(os.path.join(UI, 'ui_portrait_frame_3x.png')).convert('RGBA')
    pf = nine(pframe, 176, 176, 24)
    pf.alpha_composite(im.convert('RGBA').resize((128, 128), Image.NEAREST), (24, 24))
    return pf


def balloon(im, name='Greyson', line=LINE):
    """The balloon at screen size: the 3x dialogue frame nine-sliced to 1596x252 (30px margins),
    the portrait frame (24px margins) round the 128x128 portrait, 30px apart, the name and the line
    in Pixelify Sans at the theme's 33px."""
    frame = Image.open(os.path.join(UI, 'ui_dialogue_frame_3x.png')).convert('RGBA')
    panel = nine(frame, 1596, 252, 30)
    panel.alpha_composite(portrait_frame(im), (30, 30))
    d = ImageDraw.Draw(panel)
    font = ImageFont.truetype(FONT, 33)
    d.text((236, 30), name, font=font, fill=(255, 255, 255, 255))
    d.text((236, 74), line, font=font, fill=(235, 235, 240, 255))
    scene = Image.new('RGBA', (1636, 292), (34, 32, 52, 255))
    scene.alpha_composite(panel, (20, 20))
    return scene


def main():
    old = Image.open(os.path.join(P.HERE, 'user_portrait_0527.png')).convert('RGBA')   # the user's 05-27 drawing
    new = Image.open(os.path.join(P.PREVIEWS, 'build', 'portrait.png')).convert('RGBA')
    src = Image.open(P.SPRITE).convert('RGBA').crop((P.SX0, P.SY0, P.SX0 + P.N, P.SY0 + P.N))
    a = row([label(up(old, 6), 'BEFORE: portrait.png, the user\'s drawing (05-27), 6x'),
             label(up(new, 6), 'AFTER: portrait.png from the approved redesign, 6x'),
             label(up(src, 9), 'source: greyson_redesign.png f0, x35..77 y25..67, 9x')])
    b = row([label(balloon(old).crop((20, 20, 760, 272)), 'BEFORE'),
             label(balloon(new).crop((20, 20, 760, 272)), 'AFTER')])
    cast = [label(portrait_frame(new), 'Greyson (new)')]
    for who in ('Jordan', 'Josh'):
        cast.append(label(portrait_frame(Image.open(os.path.join(A, 'Characters', who, 'portrait.png'))), who))
    c = row(cast, bg=(34, 32, 52, 255))
    for im, name in ((a, 'greyson_portrait_before_after.png'), (b, 'greyson_portrait_balloon_before_after.png'),
                     (c, 'greyson_portrait_in_the_cast.png')):
        p = os.path.join(P.PREVIEWS, name)
        im.save(p)
        print(p)


if __name__ == '__main__':
    main()
