"""The dialogue balloon as Scenes/balloon.tscn lays it out, at screen size, for checking a portrait
in place - the same mock art_source/jordan_derived/previews.py drew Jordan's in, rebuilt here so this
rig never imports Jordan's (which pulls in his whole sprite rig).

From balloon.tscn: the PanelContainer sits at offsets 162/-162 and -264/-12 on 1920x1080 (1596x252),
styled by ui_dialogue_frame_3x.png as a StyleBoxTexture with 30px texture and content margins; inside
it an HBoxContainer (separation 30) holds the PortraitFrame, ui_portrait_frame_3x.png with 24px
margins round the 128x128 portrait (balloon.gd shows the 64x64 file at 2x, filter nearest - the
project's default_texture_filter is 0), then the name and the line in the theme's font, Pixelify
Sans at 33px. Writes nothing; returns an image.
"""
import os

import k923 as K
from PIL import Image, ImageDraw, ImageFont

UI = os.path.join(K.ASSETS, 'UI')
FONT = os.path.join(K.ROOT, 'fonts', 'PixelifySans.ttf')


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


def balloon(portrait, name, line):
    frame = Image.open(os.path.join(UI, 'ui_dialogue_frame_3x.png')).convert('RGBA')
    pframe = Image.open(os.path.join(UI, 'ui_portrait_frame_3x.png')).convert('RGBA')
    W, H = 1596, 252
    scene = Image.new('RGBA', (W + 40, H + 40), (34, 32, 52, 255))
    panel = nine(frame, W, H, 30)
    pf = nine(pframe, 128 + 48, 128 + 48, 24)
    pf.alpha_composite(portrait.convert('RGBA').resize((128, 128), Image.NEAREST), (24, 24))
    panel.alpha_composite(pf, (30, 30))
    d = ImageDraw.Draw(panel)
    font = ImageFont.truetype(FONT, 33)
    x = 30 + 176 + 30
    d.text((x, 30), name, font=font, fill=(255, 255, 255, 255))
    d.text((x, 30 + 44), line, font=font, fill=(235, 235, 240, 255))
    scene.alpha_composite(panel, (20, 20))
    return scene
