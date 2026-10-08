"""Optional credits still: the champion from behind, cup raised to the roaring crowd, backlit.

640x360 (drawn at 3x like every screen). Nothing of Burak is redrawn: his figure IS the approved
victory-screen sprite (Assets/UI/Screens/victory_player.png, back view, gloves raised), pushed
into silhouette (its own keyline kept, the fills sunk to night tones) with a 1-px rim light on
every edge the light behind him reaches. The cup between his gloves is the chosen take's own
silhouette, enlarged so its plinth spans his gloves, dark gold with a blazing rim and one glint.
The crowd beyond is the roar frame of the arena's own crowd band, every spectator a silhouette,
with their camera flashes left burning.
"""
import os
import random
import sys
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
from common import ASSETS, save
import trophy as T
import fx_screen as FS

W, H = 640, 360
VP = os.path.join(ASSETS, 'UI', 'Screens', 'victory_player.png')
BURAK_AT = (284, 222)            # victory_player's top-left in the still
CUP_SCALE = 3.4

GLOW = [((300, 150), (20, 16, 30)), ((210, 104), (34, 25, 40)), ((140, 70), (56, 38, 48)),
        ((84, 44), (88, 60, 56)), ((44, 24), (128, 90, 66))]
RIM = (255, 236, 170)
RIM_CUP = (251, 210, 60)
CUP_FILL = (70, 44, 16)
CUP_FILL_LIT = (104, 66, 22)


def rim_pass(a, lit_rgb, body_rgb_fn, rim_rgb, rim2_rgb=None):
    """a: bool mask. Pixels with an empty neighbour above / left / right get the rim; the rest
    get body_rgb_fn(y, x)."""
    h, w = a.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            if not a[y, x]:
                continue
            up = y > 0 and a[y - 1, x]
            lf = x > 0 and a[y, x - 1]
            rt = x < w - 1 and a[y, x + 1]
            if not up or not lf or not rt:
                c = rim_rgb
            elif rim2_rgb and ((y > 1 and not a[y - 2, x]) or (x > 1 and not a[y, x - 2])):
                c = rim2_rgb
            else:
                c = body_rgb_fn(y, x)
            out[y, x] = tuple(c) + (255,)
    return Image.fromarray(out, 'RGBA')


def burak_silhouette():
    vp = Image.open(VP).convert('RGBA')
    rgb = np.asarray(vp)[..., :3].astype(np.int32)
    a = np.asarray(vp)[..., 3] > 0

    def body(y, x):
        r, g, b = rgb[y, x]
        if r + g + b < 60:
            return (0, 0, 0)                           # his own keyline stays pure black
        lum = (r * 3 + g * 6 + b) / 10
        return (int(10 + lum * 0.10), int(9 + lum * 0.08), int(16 + lum * 0.10))
    return rim_pass(a, None, body, RIM, (120, 100, 80))


def scale3x(img):
    """AdvMAME3x / Scale3x: a pixel-art enlarger that keeps the palette and hard edges and
    rounds the diagonals, so the cup gains resolution without new colours or blur."""
    src = np.asarray(img)
    h, w = src.shape[:2]
    key = src[..., 0].astype(np.int64) << 24 | src[..., 1].astype(np.int64) << 16 |         src[..., 2].astype(np.int64) << 8 | src[..., 3].astype(np.int64)
    out = np.zeros((h * 3, w * 3, 4), dtype=np.uint8)

    def P(y, x):
        y = min(max(y, 0), h - 1)
        x = min(max(x, 0), w - 1)
        return key[y, x], src[y, x]
    for y in range(h):
        for x in range(w):
            A, _ = P(y - 1, x - 1); B, cb = P(y - 1, x); C, _ = P(y - 1, x + 1)
            D, cd = P(y, x - 1); E, ce = P(y, x); F, cf = P(y, x + 1)
            G, _ = P(y + 1, x - 1); H_, ch = P(y + 1, x); I, _ = P(y + 1, x + 1)
            o = [ce] * 9
            if B != H_ and D != F:
                if D == B: o[0] = cd
                if (D == B and E != C) or (B == F and E != A): o[1] = cb
                if B == F: o[2] = cf
                if (D == B and E != G) or (D == H_ and E != A): o[3] = cd
                if (B == F and E != I) or (H_ == F and E != C): o[5] = cf
                if D == H_: o[6] = cd
                if (D == H_ and E != I) or (H_ == F and E != G): o[7] = ch
                if H_ == F: o[8] = cf
            for k in range(9):
                out[y * 3 + k // 3, x * 3 + k % 3] = o[k]
    return Image.fromarray(out, 'RGBA')


def cup_silhouette(take):
    """The chosen cup at 3x via Scale3x, backlit: its colours sunk toward the night, its own black
    keyline kept, and a rim along every edge the light behind it reaches."""
    big = scale3x(T.trophy(take, back=True).image())
    rgb = np.asarray(big)[..., :3].astype(np.int32)
    a = np.asarray(big)[..., 3] > 0

    def body(y, x):
        r, g, b = rgb[y, x]
        if r + g + b < 30:
            return (0, 0, 0)
        return (int(r * 0.42), int(g * 0.34), int(b * 0.30))
    return rim_pass(a, None, body, RIM_CUP, (184, 104, 27))


def build(take='A'):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    cx, cy = 320, 168
    for (rx, ry), c in GLOW:                           # the lights beyond the crowd, in steps
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=c + (255,))
    # the crowd beyond: the roar frame of the arena band, every spectator a silhouette, flashes on
    band = Image.open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'crowd',
                                   'crowd_v3_roar.png')).convert('RGBA')
    fr = band.crop((8 * 640, 0, 9 * 640, 34))
    bp = np.asarray(fr).copy()
    op = bp[..., 3] > 0
    white = (bp[..., 0] == 255) & (bp[..., 1] == 255) & (bp[..., 2] == 255)
    flash = white.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):      # a flash's four arms
        flash |= np.roll(np.roll(white, dy, 0), dx, 1) & op & (bp[..., 2] > 240)
    top = op & ~np.roll(op, 1, 0)                         # spectators' top edges catch the glow
    bp[op & ~flash, :3] = (12, 10, 18)
    bp[top & ~flash, :3] = (70, 50, 56)
    img.alpha_composite(Image.fromarray(bp, 'RGBA'), (0, 192))
    # the ring floor in the dark
    d.rectangle((0, 230, W, H), fill=(8, 10, 10, 255))
    d.ellipse((150, 318, 490, 352), fill=(18, 20, 18, 255))
    # the champion, and the cup between his gloves
    cup = cup_silhouette(take)
    sp = T.spec(take)
    plinth_bottom_y = BURAK_AT[1] + 13
    burak = burak_silhouette()
    img.alpha_composite(cup, (320 - cup.width // 2, plinth_bottom_y - cup.height))
    img.alpha_composite(burak, BURAK_AT)
    # one big glint on the cup's lit lip
    gx, gy = 320 - cup.width // 2 + int(cup.width * 0.22), plinth_bottom_y - cup.height + 4
    for r, c in ((24, RIM), (12, (255, 255, 255))):
        d.line((gx - r, gy, gx + r, gy), fill=c)
        d.line((gx, gy - int(r * 1.2), gx, gy + int(r * 1.2)), fill=c)
    d.rectangle((gx - 1, gy - 1, gx + 1, gy + 1), fill=(255, 255, 255))
    # confetti drifting down through the light
    rng = random.Random(5)
    px = img.load()
    for _ in range(170):
        x, y = rng.uniform(0, W), rng.uniform(0, 300)
        dist = ((x - cx) / 300) ** 2 + ((y - cy) / 170) ** 2
        pair = rng.choice(FS.PAIRS) if dist < 1 else ((48, 40, 58), (32, 28, 40))
        for dx, dy, t in FS.SHAPES[rng.randrange(4)]:
            X, Y = int(x) + dx, int(y) + dy
            if 0 <= X < W and 0 <= Y < H:
                px[X, Y] = (pair[0] if t == 'L' else pair[1]) + (255,)
    return img


if __name__ == '__main__':
    for take in ('A', 'B'):
        print(save(build(take), f'credits/credits_still_{take}.png'))
