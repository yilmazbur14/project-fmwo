"""Matt's mat shadow while he is in the air: matt_leap_shadow.png.

Three frames of 80x24, the house piece (Eric's and Mason's leap shadows): a solid pure-black ellipse
centred in its frame so it sits under the feet point, the code applying the alpha (Mason's
JUGGLE_SHADOW uses 0.35 at scale 3). Frame 0 is him low, frame 2 him high.

Sized off Matt. Mason's low ellipse (54 wide) covers his belly overhang on a 64 frame; Eric's (44)
his 44-texel stance on a 128 frame. Matt's trainers span 46 texels (x 25-71 on his 96 frame) and
his shoulders 62 (the speaker ports, x 17-79), so his low ellipse is 64 wide: under the whole of
his shoulders, which is what the eye reads as "something heavy is up there".

He has no three-frame shadow of his own: FX/matt_glass_shadow.png is a single 20x8 frame drawn for
the Glass Row sheets, which another artist owns and which this never touches.
"""
from PIL import Image

W, H, FRAMES = 80, 24, 3
BLACK = (0, 0, 0, 255)
# half-width, half-height per frame: low, middle, high
SIZES = ((32.0, 9.0), (24.0, 6.8), (16.0, 4.8))


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
