"""Zoomed views with a coordinate grid, for placing hand detail by the texel.

    grid(im, box, f, out)   crop `box` of `im`, zoom by f, rule every texel, label every 5th
"""
from PIL import Image, ImageDraw


def grid(im, box, f, out, bg=(34, 32, 52, 255), step=5):
    x0, y0, x1, y1 = box
    c = im.crop(box)
    b = Image.new("RGBA", c.size, bg)
    b.alpha_composite(c)
    z = b.resize((c.width * f, c.height * f), Image.NEAREST)
    pad = 22
    o = Image.new("RGBA", (z.width + pad, z.height + pad), (10, 10, 16, 255))
    o.paste(z, (pad, pad))
    d = ImageDraw.Draw(o)
    for i in range(c.width + 1):
        col = (255, 255, 0, 110) if (x0 + i) % step == 0 else (90, 90, 120, 60)
        d.line([(pad + i * f, pad), (pad + i * f, pad + z.height)], fill=col)
        if (x0 + i) % step == 0 and i < c.width:
            d.text((pad + i * f + 1, 2), str(x0 + i), fill=(255, 255, 0, 255))
    for j in range(c.height + 1):
        col = (255, 255, 0, 110) if (y0 + j) % step == 0 else (90, 90, 120, 60)
        d.line([(pad, pad + j * f), (pad + z.width, pad + j * f)], fill=col)
        if (y0 + j) % step == 0 and j < c.height:
            d.text((1, pad + j * f + 1), str(y0 + j), fill=(255, 255, 0, 255))
    o.save(out)
