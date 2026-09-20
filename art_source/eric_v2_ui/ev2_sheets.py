"""Inspection sheets: frames laid out in rows that fit a readable width, zoomed, on a flat background,
optionally over a backdrop colour strip (to judge the art on navy, the rope, the mat)."""
import sys
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont
import ev2_mocklib as M
from ev2_common import work


def frames_sheet(frames, name, z, max_w=1900, bgs=((70, 70, 90),), pad=8):
    ims = [M.canvas_img(f, z) for f in frames]
    fw, fh = ims[0].size
    per_row = max(1, (max_w - pad) // (fw + pad))
    rows = (len(ims) + per_row - 1) // per_row
    band_h = fh + pad
    W = min(len(ims), per_row) * (fw + pad) + pad
    H = rows * band_h * len(bgs) + pad + 30
    out = Image.new('RGBA', (W, H), (16, 14, 26, 255))
    d = ImageDraw.Draw(out)
    d.text((pad, 6), '%s  %d frames of %dx%d, shown at %dx' % (name, len(frames), frames[0].w, frames[0].h, z),
           font=ImageFont.truetype(M.FONT, 20), fill=(251, 242, 54))
    y = 30
    for bg in bgs:
        for r in range(rows):
            for i in range(per_row):
                k = r * per_row + i
                if k >= len(ims):
                    break
                x = pad + i * (fw + pad)
                out.paste(Image.new('RGBA', (fw, fh), bg + (255,)), (x, y))
                out.alpha_composite(ims[k], (x, y))
            y += band_h
    out.save(work(name + '_sheet.png'))
    return out
