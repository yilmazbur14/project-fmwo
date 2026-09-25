"""Jordan's mat shadow while he is in the air: jordan_leap_shadow.png.

Three frames of 64x16, the house piece (Eric's, Mason's and Matt's leap shadows): a solid pure-black
ellipse centred in its frame so it sits under the feet point, the code applying the alpha (Mason's
JUGGLE_SHADOW uses 0.35 at scale 3). Frame 0 is him low, frame 2 him high.

Sized off Jordan: his sneakers span 30 texels (x 37-66 on his 96 frame) and his shoulders about the
same, with the box hugged out past his far side to x 74, so his low ellipse is 46 wide, between
Eric's 44 and Mason's 54: a slim man carrying something.

Re-checked for v2 (2026-09-24), and kept: what sets his footprint did not move. The sneakers are the
approved maps (x 36-63 on both sprites), the hugged box still reaches x 74, and v2's sack of a tee is
if anything wider at the hip (26 texels against v1's 23); the thin arms and legs sit inside those.
Both sprites' silhouettes are 48 texels wide (v1 x 27-75, v2 x 29-77).

He has no shadow sheet of his own.
"""
from PIL import Image

W, H, FRAMES = 64, 16, 3
BLACK = (0, 0, 0, 255)
# half-width, half-height per frame: low, middle, high
SIZES = ((23.0, 7.0), (17.5, 5.2), (12.0, 4.0))


def frame(rx, ry):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cx, cy = W / 2.0, H / 2.0
    for y in range(H):
        for x in range(W):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1.0:
                g.putpixel((x, y), BLACK)
    return g


def sheet():
    out = Image.new('RGBA', (W * FRAMES, H), (0, 0, 0, 0))
    for i, s in enumerate(SIZES):
        out.paste(frame(*s), (W * i, 0))
    return out


def sizes(im):
    res = []
    for i in range(FRAMES):
        bb = im.crop((W * i, 0, W * i + W, H)).getbbox()
        res.append('%dx%d' % (bb[2] - bb[0], bb[3] - bb[1]))
    return res


if __name__ == '__main__':
    print('ellipses', sizes(sheet()))
