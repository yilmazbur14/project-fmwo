"""Jordan's puppets: presentation images for the approval pass (the before/after sheets, the lineup,
the in-game mock and the carry test). Nothing here writes a file; jp_export does.

Everything in-game is composed at the native 640x360 texels and scaled 3x with nearest neighbour,
exactly as the game draws it (canvas_items stretch, every sprite at scale 3).

Placement in the mock:
- the void: Assets/Environment/Void/void_bg.png, 640x360, full screen;
- Jordan's god: jordan_god_hover.png frame 0 (320x224, anchor (160,223)) with the anchor at screen
  (960, 600), where the finale plays him. 100 px higher (960, 500) cuts his crown and wingtips off at
  the top of the screen (his topmost texel is 35 rows under the frame top: y -64 there, y 36 here),
  and 100 px lower (960, 700) puts his claws level with the sumo Danny's head, so the strings could not
  hang down to it;
- the puppets stand on one floor line with their feet anchors on it;
- PLACEHOLDER strings, 1 texel, from his claw tips to each puppet's hooks. The BACK string is drawn
  under the puppet (it ties on between the shoulder blades, behind the body); the others over it.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jp_core as C  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCALE = 3
NATIVE = (640, 360)
VOID_BG = os.path.join(C.ROOT, 'Assets', 'Environment', 'Void', 'void_bg.png')
GOD = os.path.join(C.ROOT, 'Assets', 'Characters', 'Jordan', 'God', 'jordan_god_hover.png')
GOD_FRAME = (320, 224)
GOD_ANCHOR = (160, 223)
GOD_AT = (960, 600)
# His claw tips on hover frame 0, texels on his frame (measured: the lowest texel of each claw).
CLAWS_L = [(119, 188), (120, 189), (122, 189), (123, 190)]
CLAWS_R = [(194, 190), (197, 189), (199, 189), (200, 188)]
# Placeholder strings: pale thread in take A; in take B his rune light runs down them.
STRINGS = {'A': ((214, 206, 232, 255), (170, 160, 196, 255)),
           'B': ((102, 198, 236, 255), (43, 108, 153, 255))}
LABEL = (225, 222, 235, 255)
DARK = (12, 10, 16, 255)


def void():
    return Image.open(VOID_BG).convert('RGBA')


def god_frame(f=0):
    g = Image.open(GOD).convert('RGBA')
    return g.crop((f * GOD_FRAME[0], 0, (f + 1) * GOD_FRAME[0], GOD_FRAME[1]))


def place(anchor, screen_pt):
    """Native top-left of a layer whose texel `anchor` lands on screen point `screen_pt`."""
    return (int(round(screen_pt[0] / SCALE - anchor[0])), int(round(screen_pt[1] / SCALE - anchor[1])))


def line(draw_px, a, b, col):
    """A 1-texel Bresenham line on a PIL pixel-access object."""
    (x0, y0), (x1, y1) = (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1])))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        draw_px(x0, y0, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def label(im, text, pad=16, bg=DARK, col=LABEL):
    out = Image.new('RGBA', (im.width, im.height + pad), bg)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 2), text, fill=col)
    return out


def hstack(ims, gap=8, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.alpha_composite(i, (x, 0))
        x += i.width + gap
    return out


def vstack(ims, gap=8, bg=DARK):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.alpha_composite(i, (0, y))
        y += i.height + gap
    return out


def compare(before, after_a, after_b, name, s=6):
    """The 6x before | take A | take B sheet, cropped to the figure's box (plus a margin)."""
    bb = None
    for im in (before, after_a, after_b):
        b = im.getbbox()
        bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    bb = (max(0, bb[0] - 2), max(0, bb[1] - 2), min(before.width, bb[2] + 2), min(before.height, bb[3] + 2))
    tiles = [label(C.up(im.crop(bb), s), t) for im, t in
             ((before, '%s: before' % name), (after_a, 'take A  Blood & Ash (ember)'), (after_b, 'take B  Rune (blue)'))]
    return hstack(tiles)


def lineup(rows, bosses, gap=10, floor_pad=6):
    """Game scale (3x) on the void: one row per entry of `rows` = (label, {boss name: image}), every
    figure's feet anchor on the row's floor line, bosses in ladder order."""
    widths = {}
    for n in bosses:
        widths[n] = max(r[1][n].getbbox()[2] - r[1][n].getbbox()[0] for r in rows) + gap
    W = sum(widths.values()) + gap
    # figures are shorter than their frames: size each row to its tallest figure above the feet
    heights = []
    for _lab, ims in rows:
        heights.append(max(bosses[n].feet[1] - ims[n].getbbox()[1] + 1 for n in bosses) + floor_pad + 12)
    H = sum(heights)
    bg = void()
    canvas = Image.new('RGBA', (W, H), DARK)
    for yy in range(0, H, NATIVE[1]):
        for xx in range(0, W, NATIVE[0]):
            canvas.alpha_composite(bg, (xx, yy))
    y0 = 0
    labels = []
    for (lab, ims), h in zip(rows, heights):
        floor = y0 + h - floor_pad
        x = gap
        for n, b in bosses.items():
            im = ims[n]
            bb = im.getbbox()
            cx = x + widths[n] // 2
            ox = cx - (bb[0] + bb[2]) // 2
            oy = floor - b.feet[1]
            canvas.alpha_composite(im, (ox, oy))
            labels.append((lab, n, cx, floor))
            x += widths[n]
        labels.append((lab, None, 4, y0 + 2))
        y0 += h
    big = canvas.resize((W * SCALE, H * SCALE), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for lab, n, x, y in labels:
        if n is None:
            d.text((x * SCALE, y * SCALE), lab, fill=LABEL)
        else:
            d.text((x * SCALE - 3 * len(bosses[n].title), (y + 1) * SCALE), bosses[n].title, fill=(150, 146, 170, 255))
    return big


def mock(puppets, god_f=0, strings=True, take='A'):
    """The 1920x1080 in-game mock. `puppets`: list of dicts {boss, image, hooks, at (screen px of the
    feet anchor), strings: [(hook name, 'L'|'R', claw index)]}."""
    native = void()
    god = god_frame(god_f)
    gx, gy = place(GOD_ANCHOR, GOD_AT)
    native.alpha_composite(god, (gx, gy))
    claws = {'L': [(gx + x, gy + y) for x, y in CLAWS_L], 'R': [(gx + x, gy + y) for x, y in CLAWS_R]}
    px = native.load()

    def put(x, y, col):
        if 0 <= x < NATIVE[0] and 0 <= y < NATIVE[1]:
            px[x, y] = col

    placed = []
    for p in puppets:
        b = p['boss']
        ox, oy = place(b.feet, p['at'])
        placed.append((p, ox, oy))
    # back strings first: they run behind the puppets
    if strings:
        for p, ox, oy in placed:
            for hook, side, ci in p.get('strings', []):
                if hook == 'back' and hook in p['hooks']:
                    hx, hy = p['hooks'][hook]
                    line(put, claws[side][ci], (ox + hx, oy + hy), STRINGS[take][1])
    for p, ox, oy in placed:
        native.alpha_composite(p['image'], (ox, oy))
    if strings:
        for p, ox, oy in placed:
            for hook, side, ci in p.get('strings', []):
                if hook != 'back' and hook in p['hooks']:
                    hx, hy = p['hooks'][hook]
                    line(put, claws[side][ci], (ox + hx, oy + hy), STRINGS[take][0])
    return native.resize((NATIVE[0] * SCALE, NATIVE[1] * SCALE), Image.NEAREST)
