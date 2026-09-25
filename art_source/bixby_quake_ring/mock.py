"""Review previews for the quake ring. Writes ONLY into the scratchpad preview folder, never into Assets.

  python mock.py [sheet.png]     rings at three radii over the arena, the same with the hurt band traced, a 4x
                                 sheet, and a GIF of a ring rolling out. With no sheet it builds one in memory.

The arena is a real frame of the fight (the coder's capture) with the mat under the ropes cleaned back to
arena_mat.png, so the rope, crowd and HUD are the game's own. Bixby (pound frame 5, where he stood in that
frame) and the player (cut from the same frame) are placed and y-sorted with the ring's segments, and the
segments are placed by placement.py, exactly as the ring script should place them.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import placement as P  # noqa: E402

PROJECT = r'C:/Users/theyi/OneDrive/Documents/new-game-project/'
SCRATCH = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/'
PREV = SCRATCH + 'bixby_quake_ring/'
STILL = SCRATCH + 'bixby_combined_v2/still_1_pound_rings.png'

FEET = (1131, 639)                  # his feet in that frame were (1132, 640); on the texel grid here
SCALE = 3
# The ropes' inside: a segment is drawn only while all of it is in here (the ring script culls the same way).
ROPES = (113, 114, 1805, 964)
HUD = (712, 92, 1208, 184)          # the boss bar, left as the frame drew it
PLAYER_BOX = (1262, 812, 1336, 912) # the player in the capture frame
MAT_GREEN = (160, 196, 128, 255)


def clean_plate():
    frame = Image.open(STILL).convert('RGBA')
    mat = Image.open(PROJECT + 'Assets/Environment/arena_mat.png').convert('RGBA')
    big = mat.resize((mat.width * SCALE, mat.height * SCALE), Image.NEAREST)
    mat_layer = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    mat_layer.paste(big, (111, 114))
    plate = frame.copy()
    x0, y0, x1, y1 = 123, 124, 1795, 958
    region = mat_layer.crop((x0, y0, x1, y1))
    plate.paste(region, (x0, y0))
    # put the HUD back
    plate.paste(frame.crop(HUD), HUD[:2])
    return plate, frame, mat_layer


def player_sprite(frame, mat_layer):
    """The player cut out of the capture frame: every texel there that isn't the clean mat."""
    box = PLAYER_BOX
    a = frame.crop(box)
    b = mat_layer.crop(box)
    out = Image.new('RGBA', a.size, (0, 0, 0, 0))
    pa, pb, po = a.load(), b.load(), out.load()
    for y in range(a.height):
        for x in range(a.width):
            if pa[x, y][:3] != pb[x, y][:3]:
                po[x, y] = pa[x, y]
    bb = out.getbbox()
    out = out.crop(bb)
    feet = (box[0] + bb[0] + out.width // 2, box[1] + bb[3])
    return out, feet


def bixby_layers():
    pound = Image.open(PROJECT + 'Assets/Characters/Bixby/bixby_pound.png').convert('RGBA')
    f5 = pound.crop((5 * 192, 0, 6 * 192, 160)).resize((192 * SCALE, 160 * SCALE), Image.NEAREST)
    shadow = Image.open(PROJECT + 'Assets/Characters/Bixby/bixby_beast_shadow_ground.png').convert('RGBA')
    sh = shadow.crop((0, 0, 192, 48)).resize((192 * SCALE, 48 * SCALE), Image.NEAREST)
    alpha = sh.getchannel('A').point(lambda v: int(v * 0.38))
    sh.putalpha(alpha)
    return f5, (FEET[0] - 96 * SCALE, FEET[1] - 151 * SCALE), sh, (FEET[0] - 96 * SCALE, FEET[1] - 25 * SCALE)


class Sheet:
    """The ring sheet cut into frames, each scaled to the screen, with each row's pivot and drawn box."""

    def __init__(self, im, frame_w, frame_h, pivots_y):
        self.im = im.convert('RGBA')
        self.fw, self.fh = frame_w, frame_h
        self.rows = self.im.height // frame_h
        self.cols = self.im.width // frame_w
        self.py = pivots_y
        self.cache = {}
        self.boxes = []
        for r in range(self.rows):
            u = None
            for c in range(self.cols):
                bb = self.frame(r, c, False, scaled=False).getbbox()
                if bb:
                    u = bb if u is None else (min(u[0], bb[0]), min(u[1], bb[1]), max(u[2], bb[2]), max(u[3], bb[3]))
            # the drawn box relative to the pivot, in px (the same flipped, as the pivot is centred)
            px = self.fw // 2
            l = (u[0] - px) * SCALE
            r_ = (u[2] - px) * SCALE
            self.boxes.append((min(l, -r_), (u[1] - self.py[r]) * SCALE, max(r_, -l), (u[3] - self.py[r]) * SCALE))

    def frame(self, row, col, flip, scaled=True):
        key = (row, col, flip, scaled)
        if key not in self.cache:
            f = self.im.crop((col * self.fw, row * self.fh, (col + 1) * self.fw, (row + 1) * self.fh))
            if flip:
                f = f.transpose(Image.FLIP_LEFT_RIGHT)
            if scaled:
                f = f.resize((self.fw * SCALE, self.fh * SCALE), Image.NEAREST)
            self.cache[key] = f
        return self.cache[key]


def ring_items(sheet, radius, beat, centre=FEET):
    """(sort y, order, image, top-left) for every drawn segment of a ring."""
    items = []
    for i, theta, (x, y), phi, row, flip in P.segments(radius, centre):
        l, t, r, b = sheet.boxes[row]
        if not (ROPES[0] <= x + l and x + r <= ROPES[2] and ROPES[1] <= y + t and y + b <= ROPES[3]):
            continue
        img = sheet.frame(row, (beat + i) % sheet.cols, flip)
        items.append((y, i, img, (int(x - sheet.fw // 2 * SCALE), int(y - sheet.py[row] * SCALE))))
    return items


def compose(sheet, radii, beat, player_at=None, trace=False):
    plate, frame, mat_layer = clean_plate()
    body, body_at, shadow, shadow_at = bixby_layers()
    ply, _ = player_sprite(frame, mat_layer)
    canvas = plate.copy()
    canvas.alpha_composite(shadow, shadow_at)
    items = [(FEET[1], -1, body, body_at)]
    if player_at:
        items.append((player_at[1], -1, ply, (player_at[0] - ply.width // 2, player_at[1] - ply.height)))
    for rad in radii:
        items += ring_items(sheet, rad, beat)
    items.sort(key=lambda it: (it[0], it[1]))
    for _, _, img, at in items:
        canvas.alpha_composite(img, (max(0, at[0]), max(0, at[1])), (max(0, -at[0]), max(0, -at[1])))
    if trace:
        d = ImageDraw.Draw(canvas)
        for rad in radii:
            for rr, col in ((rad - 36, (0, 255, 255, 255)), (rad, (255, 255, 255, 255)), (rad + 36, (0, 255, 255, 255))):
                pts = [(FEET[0] + rr * math.cos(a / 180 * math.pi), FEET[1] + P.K * rr * math.sin(a / 180 * math.pi))
                       for a in range(0, 361, 2)]
                d.line(pts, fill=col, width=1)
    return canvas


def sheet_x4(sheet, path, names=None):
    """The sheet at 4x over mat green, frame grid, pivot crosses, row labels down the left."""
    im = sheet.im
    lab = 110
    big = im.resize((im.width * 4, im.height * 4), Image.NEAREST)
    base = Image.new('RGBA', (big.width + lab, big.height + 24), (30, 34, 30, 255))
    mat = Image.new('RGBA', big.size, MAT_GREEN)
    mat.alpha_composite(big)
    base.paste(mat, (lab, 24))
    d = ImageDraw.Draw(base)
    for x in range(0, big.width + 1, sheet.fw * 4):
        d.line([(lab + x, 24), (lab + x, 24 + big.height)], fill=(40, 60, 40, 255))
    for y in range(0, big.height + 1, sheet.fh * 4):
        d.line([(lab, 24 + y), (lab + big.width, 24 + y)], fill=(40, 60, 40, 255))
    for c in range(sheet.cols):
        d.text((lab + c * sheet.fw * 4 + 6, 6), 'frame %d' % c, fill=(230, 230, 230, 255))
    for r in range(sheet.rows):
        name = names[r] if names else ''
        d.text((6, 24 + r * sheet.fh * 4 + 50), 'row %d %s' % (r, name), fill=(230, 230, 230, 255))
        for c in range(sheet.cols):
            cx = lab + c * sheet.fw * 4 + sheet.fw // 2 * 4
            cy = 24 + r * sheet.fh * 4 + sheet.py[r] * 4
            d.line([(cx - 5, cy), (cx + 5, cy)], fill=(0, 255, 255, 255))
            d.line([(cx, cy - 5), (cx, cy + 5)], fill=(0, 255, 255, 255))
    base.save(path)
    return path


def diagnostic(sheet, radius, path, centre=FEET):
    """One ring over the clean arena with every pivot marked and labelled row / f(lipped), and the culled
    ones crossed out: to check an implementation of the placement against this one."""
    canvas = compose(sheet, [radius], 0)
    d = ImageDraw.Draw(canvas)
    for i, theta, (x, y), phi, row, flip in P.segments(radius, centre):
        l, t, r, b = sheet.boxes[row]
        culled = not (ROPES[0] <= x + l and x + r <= ROPES[2] and ROPES[1] <= y + t and y + b <= ROPES[3])
        col = (255, 60, 60, 255) if culled else (0, 255, 255, 255)
        d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=col)
        d.text((x + 4, y + 2), '%d%s' % (row, 'f' if flip else ''), fill=(255, 255, 255, 255))
    canvas.save(path)
    return path


def gif(sheet, path, r0=187.0, speed=200.0, frame_time=0.08, until=1500.0, player_at=None, crop=None,
        scale=(2, 3), radii_behind=()):
    """A ring rolling out at `speed` px of floor a second, one GIF frame per animation frame (frame_time),
    neighbouring segments a frame apart as the ring script plays them. scale (n, d): n/d of the screen, with
    (2, 3) every 3-px texel becomes exactly 2 px."""
    frames = []
    rad, beat = r0, 0
    n, d = scale
    while rad <= until:
        im = compose(sheet, [rad] + [rad + b for b in radii_behind], beat, player_at)
        if crop:
            im = im.crop(crop)
        im = im.resize((im.width * n // d, im.height * n // d), Image.NEAREST)
        frames.append(im.convert('RGB'))
        rad += speed * frame_time
        beat += 1
    pal = frames[len(frames) // 2].quantize(colors=255, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(frame_time * 1000), loop=0, optimize=True)
    return path, len(frames)


def build_sheet():
    import ring
    from ringpal import sheet as make_sheet
    rows = ring.layout()
    im = make_sheet([cut for cut, _ in rows])
    return im, ring.FRAME_W, ring.FRAME_H, [ring.PIVOT[1]] * len(rows)


if __name__ == '__main__':
    os.makedirs(PREV, exist_ok=True)
    im, fw, fh, pys = build_sheet()
    sheet = Sheet(im, fw, fh, pys)
    tag = sys.argv[1] if len(sys.argv) > 1 else 'mock'
    radii = [300.0, 620.0, 980.0]
    player = (1470, 900)
    compose(sheet, radii, 0, player).save(PREV + '%s_three_radii.png' % tag)
    compose(sheet, radii, 0, player, trace=True).save(PREV + '%s_three_radii_band.png' % tag)
    print(sheet_x4(sheet, PREV + '%s_sheet_x4.png' % tag))
    print('boxes', sheet.boxes)
