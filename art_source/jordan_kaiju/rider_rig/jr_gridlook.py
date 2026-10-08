"""Zoomed views with a coordinate grid, for authoring maps by hand (writes only into rider/look)."""
import sys
sys.dont_write_bytecode = True
import jr_common as C
from PIL import Image, ImageDraw


def gridlook(px, name, x0, y0, x1, y1, s=12, bg=C.BG):
    w, h = x1 - x0 + 1, y1 - y0 + 1
    im = Image.new('RGBA', (w * s + 30, h * s + 20), (20, 20, 24, 255))
    d = ImageDraw.Draw(im)
    for y in range(h):
        for x in range(w):
            k = px.get((x0 + x, y0 + y))
            col = C.PAL[k] if k else bg
            d.rectangle([30 + x * s, 20 + y * s, 30 + x * s + s - 1, 20 + y * s + s - 1], fill=col)
    for x in range(w + 1):
        X = x0 + x
        d.line([30 + x * s, 20, 30 + x * s, 20 + h * s], fill=(90, 90, 110, 255) if X % 5 else (200, 200, 90, 255))
        if x < w and X % 5 == 0:
            d.text((30 + x * s + 1, 4), str(X), fill=(230, 230, 120, 255))
    for y in range(h + 1):
        Y = y0 + y
        d.line([30, 20 + y * s, 30 + w * s, 20 + y * s], fill=(90, 90, 110, 255) if Y % 5 else (200, 200, 90, 255))
        if y < h and Y % 5 == 0:
            d.text((2, 20 + y * s + 1), str(Y), fill=(230, 230, 120, 255))
    p = C.guard_out(C.LOOK + '/' + name)
    im.save(p)
    return p


if __name__ == '__main__':
    import jr_ride as R
    px = R.build('admire')
    print(gridlook(px, 'grid_rider_build.png', 26, 6, 84, 92, 10))
