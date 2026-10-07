"""Presentation for the maze wall's approval pass: the strip, the contact sheet, the GIFs and the
1920x1080 maze mocks. Reads the game's PNGs (the void, the god, his runes, the player's Glass Row
pose, Matt's glass tile); nothing in this module writes a file.

Placement follows PLAN.md section 3: block (c, r) has its soles at (960 + 96c, 896 - 60r); a wall's
anchor texel (16, last row) sits with its bottom edge on the cell's front edge, (960 + 96c,
926 - 60r), every sprite at scale 3. The stage is sorted by soles, as the game must sort it."""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vw_block as V  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE)) if os.path.basename(os.path.dirname(HERE)) == 'art_source' \
    else r'C:\Users\theyi\OneDrive\Documents\new-game-project'
A = os.path.join(ROOT, 'Assets')
VOID = os.path.join(A, 'Environment', 'Void', 'void_bg.png')
GOD = os.path.join(A, 'Characters', 'Jordan', 'God', 'jordan_god_hover.png')
RUNES = os.path.join(A, 'Characters', 'Jordan', 'God', 'jordan_god_runes.png')
PLAYER = os.path.join(A, 'Characters', 'MainPlayer', 'player_glass_row.png')
GLASS = os.path.join(A, 'Characters', 'Matt', 'FX', 'matt_glass_floor.png')

S = 3
CELL = (96, 60)
ORIGIN = (960, 896)                  # soles of block (0, 0)
PLAYER_ORIGIN_UP = 42                # the player's origin is soles - (0, 42)
GOD_POINT = (960, 600)
GOD_ANCHOR = (160, 223)
RUNES_CENTRE = (960, 600 - 296)      # JordanFinaleLayout.RUNES_OFFSET from the god's point
VOID_COLOUR = (13, 9, 26, 255)       # the void's own mid-dark step (jg_void STEPS[2])

# PLAN.md section 3: the path in order, the back glass, Greyson's block
PATH = [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (1, 5), (0, 5), (-1, 5), (-2, 5),
        (-3, 5), (-4, 5), (-4, 6), (-4, 7), (-3, 7), (-2, 7), (-1, 7)]
START, GOAL = PATH[0], PATH[-1]
BACK_GLASS = (0, -1)
GREYSON = (-1, 8)

# suggested timings, seconds (frame 4 holds for the plan's WALL_SHOW)
TIMES = [0.07, 0.07, 0.09, 0.12, 1.5, 0.10, 0.10, 0.10]
RIPPLE = 0.02                        # the plan's stagger between blocks


# ------------------------------------------------------------------ images

def image(px, fh):
    w, h = V.size(fh)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ld = im.load()
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            ld[x, y] = V.PAL[k]
    return im


def strip(frames, fh):
    w, h = V.size(fh)
    out = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, px in enumerate(frames):
        out.alpha_composite(image(px, fh), (i * w, 0))
    return out


def big(im, s=S):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def up(im, s, bg=VOID_COLOUR):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im)
    return big(b, s)


def font(size):
    try:
        return ImageFont.truetype('arial.ttf', size)
    except OSError:
        return ImageFont.load_default()


# ------------------------------------------------------------------ the maze

def soles(cell):
    c, r = cell
    return (ORIGIN[0] + CELL[0] * c, ORIGIN[1] - CELL[1] * r)


def walls():
    """Every block in c -5..3, r -1..8 that is 8-adjacent to the path and not on it, except
    Greyson's block and the back glass."""
    P = set(PATH)
    out = []
    for c in range(-5, 4):
        for r in range(-1, 9):
            if (c, r) in P or (c, r) in (GREYSON, BACK_GLASS):
                continue
            if any((c + dc, r + dr) in P for dc in (-1, 0, 1) for dr in (-1, 0, 1) if dc or dr):
                out.append((c, r))
    return out


def wall_topleft(cell, block_size):
    sx, sy = soles(cell)
    return (sx - (block_size[0] // 2) * S, sy + CELL[1] // 2 - block_size[1] * S)


def backdrop(god=False):
    canvas = big(Image.open(VOID).convert('RGBA'))
    if god:
        rb = big(Image.open(RUNES).convert('RGBA').crop((0, 0, 192, 192)))
        canvas.alpha_composite(rb, (RUNES_CENTRE[0] - rb.width // 2, RUNES_CENTRE[1] - rb.height // 2))
        g = big(Image.open(GOD).convert('RGBA').crop((0, 0, 320, 224)))
        canvas.alpha_composite(g, (GOD_POINT[0] - GOD_ANCHOR[0] * S, GOD_POINT[1] - GOD_ANCHOR[1] * S))
    return canvas


def glass_block():
    """Stand-in for the back glass (MattGlassFloor builds the real one): the tile's first 32x20."""
    return big(Image.open(GLASS).convert('RGBA').crop((0, 0, 32, 20)))


def player_sprite():
    """The Glass Row 'rooted' back view, frame 0: the maze's pose while the player waits."""
    return big(Image.open(PLAYER).convert('RGBA').crop((0, 32, 32, 64)))


def goal_pin():
    """A plain placeholder that stands on the goal and sorts like a body: a gold diamond on a post."""
    im = Image.new('RGBA', (15, 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line((7, 12, 7, 29), fill=(255, 214, 90, 255))
    d.polygon([(7, 0), (14, 6), (7, 12), (0, 6)], fill=(255, 214, 90, 255), outline=(0, 0, 0, 255))
    return big(im)


def stage(canvas, wall_images, block_size):
    """Draw the walls ({cell: image or None}), the player and the goal pin, sorted by soles
    (a tie goes to the body, which draws over a wall on its own row)."""
    items = [(soles(c)[1], 0, 'wall', c) for c, im in wall_images.items() if im is not None]
    items.append((soles(START)[1], 1, 'player', START))
    items.append((soles(GOAL)[1], 1, 'pin', GOAL))
    items.sort(key=lambda t: (t[0], t[1]))
    ps = player_sprite()
    pin = goal_pin()
    for _, _, kind, cell in items:
        if kind == 'wall':
            canvas.alpha_composite(big(wall_images[cell]), wall_topleft(cell, block_size))
        elif kind == 'pin':
            sx, sy = soles(cell)
            canvas.alpha_composite(pin, (sx - pin.width // 2, sy - pin.height))
        else:
            sx, sy = soles(cell)
            canvas.alpha_composite(ps, (sx - ps.width // 2, sy - PLAYER_ORIGIN_UP - ps.height // 2))


def floor(canvas):
    gb = glass_block()
    gx, gy = soles(BACK_GLASS)
    canvas.alpha_composite(gb, (gx - gb.width // 2, gy - gb.height // 2))


def mock(block, god=False, caption=None):
    """block: the standing frame (RGBA). The 1920x1080 mock of PLAN.md section 3's maze."""
    canvas = backdrop(god)
    floor(canvas)
    stage(canvas, {c: block for c in walls()}, block.size)
    d = ImageDraw.Draw(canvas)
    f = font(20)
    ink = dict(font=f, stroke_width=3, stroke_fill=(0, 0, 0, 255))
    sx, sy = soles(START)
    label = 'START: player stand-in (back glass below)'
    tw = d.textlength(label, font=f)
    d.text((sx - 160 - tw, sy - 12), label, fill=(235, 235, 245, 255), **ink)
    gx, gy = soles(GOAL)
    d.text((gx - 26, gy - 122), 'GOAL', fill=(255, 214, 90, 255), **ink)
    yx, yy = soles(GREYSON)
    d.text((yx - 62, yy - 100), "Greyson's gap", fill=(220, 220, 232, 255), **ink)
    if caption:
        d.text((40, 1030), caption, fill=(220, 220, 232, 255), font=font(22), stroke_width=3,
               stroke_fill=(0, 0, 0, 255))
    return canvas


# ------------------------------------------------------------------ contact sheet

def contact(takes):
    """Every frame of every take at 8x, with its suggested time; the anchor texel marked."""
    s = 8
    pad = 16
    names = ['rise 0', 'rise 1', 'rise 2', 'rise 3 (lock)', 'stand', 'vanish 0', 'vanish 1', 'vanish 2']
    rows = []
    for title, frames, fh in takes:
        w, h = V.size(fh)
        tw, th = w * s, h * s
        row = Image.new('RGBA', (len(frames) * (tw + pad) + pad, th + 70), (8, 6, 14, 255))
        d = ImageDraw.Draw(row)
        d.text((pad, 6), title, fill=(235, 235, 245, 255), font=font(18))
        for i, px in enumerate(frames):
            x0 = pad + i * (tw + pad)
            row.paste(up(image(px, fh), s), (x0, 32))
            ax, ay = V.anchor(fh)
            d.rectangle((x0 + ax * s, 32 + ay * s, x0 + ax * s + s - 1, 32 + ay * s + s - 1), outline=(255, 90, 200, 255))
            t = TIMES[i]
            d.text((x0, 32 + th + 6), '%d  %s  %s' % (i, names[i], ('%.2fs' % t) if i != 4 else 'hold'),
                   fill=(200, 200, 215, 255), font=font(15))
        rows.append(row)
    W = max(r.width for r in rows)
    note_h = 40
    sheet = Image.new('RGBA', (W, sum(r.height for r in rows) + note_h), (8, 6, 14, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    ImageDraw.Draw(sheet).text((16, y + 8), 'Pink square: the anchor texel (16, last row). 8x texels. '
                               'Rise frames end on the floor line (their bottom row is the rift glow).',
                               fill=(200, 200, 215, 255), font=font(15))
    return sheet


# ------------------------------------------------------------------ GIFs

def _palette_frames(ims):
    """Exact 'P' frames: one shared palette of every colour used (the art has far fewer than 256)."""
    import numpy as np
    arrs = []
    for im in ims:
        a = np.asarray(im.convert('RGB')).astype(np.int64)
        arrs.append(((a[:, :, 0] << 16) | (a[:, :, 1] << 8) | a[:, :, 2], a.shape[:2]))
    keys = np.unique(np.concatenate([k.ravel() for k, _ in arrs]))
    if len(keys) > 256:
        raise ValueError('%d colours: too many for a GIF' % len(keys))
    pal = []
    for k in keys.tolist():
        pal += [(k >> 16) & 255, (k >> 8) & 255, k & 255]
    pal += [0] * (768 - len(pal))
    out = []
    for k, shape in arrs:
        p = Image.fromarray(np.searchsorted(keys, k).astype(np.uint8), 'P')
        p.putpalette(pal)
        out.append(p)
    return out


def save_gif(path, ims, durations):
    """durations in seconds; merged into GIF centiseconds (identical neighbours are merged)."""
    merged_ims, merged_d = [], []
    for im, d in zip(ims, durations):
        if merged_ims and im.tobytes() == merged_ims[-1].tobytes():
            merged_d[-1] += d
        else:
            merged_ims.append(im)
            merged_d.append(d)
    frames = _palette_frames(merged_ims)
    cs = [max(2, int(round(d * 100))) * 10 for d in merged_d]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=cs, loop=0, disposal=1,
                   optimize=False)
    return len(frames)


def block_gif_frames(frames, fh, s=6, blank=0.6):
    w, h = V.size(fh)
    ims = [up(image(px, fh), s) for px in frames]
    ims.append(up(Image.new('RGBA', (w, h), (0, 0, 0, 0)), s))
    return ims, list(TIMES) + [blank]


def maze_gif_frames(frames, fh, box=(400, 300, 1330, 1010), lead=0.3, stand=1.5, tail=0.6):
    """The maze rising block by block, 0.02 s apart in order of distance from the start (a stand-in
    for whatever order the coder picks), standing, then vanishing together as the dark falls."""
    block_size = V.size(fh)
    ims = [image(px, fh) for px in frames]
    cells = walls()
    sx0, sy0 = soles(START)
    order = sorted(cells, key=lambda c: (math.hypot(soles(c)[0] - sx0, soles(c)[1] - sy0), c))
    start = {c: lead + RIPPLE * i for i, c in enumerate(order)}
    rise_ends = [sum(TIMES[:k + 1]) for k in range(4)]            # 0.07, 0.14, 0.23, 0.35
    t_vanish = max(start.values()) + rise_ends[-1] + stand
    base = backdrop(False)
    floor(base)
    out, durs = [], []
    step = RIPPLE
    t = 0.0
    t_end = t_vanish + 0.30 + tail
    while t < t_end - 1e-9:
        wall_images = {}
        for c in cells:
            if t >= t_vanish:
                k = int((t - t_vanish) / 0.10 + 1e-6)
                wall_images[c] = ims[5 + k] if k < 3 else None
                continue
            dt = t - start[c]
            if dt < 0:
                wall_images[c] = None
            elif dt < rise_ends[-1]:
                k = next(i for i, e in enumerate(rise_ends) if dt < e - 1e-9)
                wall_images[c] = ims[k]
            else:
                wall_images[c] = ims[4]
        canvas = base.copy()
        stage(canvas, wall_images, block_size)
        out.append(canvas.crop(box))
        # step finely through the ripple and the vanish, in one long frame through the stand
        if max(start.values()) + rise_ends[-1] <= t < t_vanish - step:
            d = t_vanish - t
        else:
            d = step if t < t_vanish else 0.10
        durs.append(d)
        t += d
    return out, durs
