"""Danny's mat shadow while he is in the air: danny_leap_shadow.png.

Three frames of 144x28, the same piece Mason and Eric have: a solid pure-black ellipse centred in its
frame (pivot (72, 14)), so a centred Sprite2D drops it on the feet point; the code sets the alpha
(both their JUGGLE_SHADOWs use 0.35). Frame 0 is him low, frame 2 high.

Sized off Danny, not off the others. Mason's low frame (54 px) is a touch narrower than his 58-texel
belly; Eric's (44 px) matches his stance. Danny's sumo stance is 171 texels from toe to toe, but his
mass is the torso and thighs, about 132 across, so his low ellipse is 132 wide: the heaviest shadow
in the cast, which is the point -- the mat should look like something enormous is hanging over it.
"""
from PIL import Image

W, H, FRAMES = 144, 28, 3
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)
# half-width, half-height per frame: low, middle, high
SIZES = ((66.0, 11.5), (49.0, 8.5), (33.0, 6.0))


def frame(rx, ry):
    im = Image.new('RGBA', (W, H), CLEAR)
    cx, cy = W / 2.0, H / 2.0
    for y in range(H):
        for x in range(W):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1.0:
                im.putpixel((x, y), BLACK)
    return im


def sheet():
    out = Image.new('RGBA', (W * FRAMES, H), CLEAR)
    for i, s in enumerate(SIZES):
        out.alpha_composite(frame(*s), (i * W, 0))
    return out


def sizes(im):
    out = []
    for i in range(FRAMES):
        b = im.crop((i * W, 0, i * W + W, H)).getbbox()
        out.append('%dx%d' % (b[2] - b[0], b[3] - b[1]))
    return out
