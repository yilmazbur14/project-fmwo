"""Previews for the standing finale sheets. Images only; jfs_export.py decides where they go (this
folder's preview/, never Assets/).

  contact(sheets)      every frame of every sheet at 4x, labelled with its sheet, index, what it is and
                       its suggested time
  gif(mod)             one sheet at game speed (its suggested times), at 3x, on the floor it plays on
  room_mock(...)       him standing in the approved room at game scale (1920x1080), mirrored to face
                       the talk spot as the code shows him, with the player and three cameo bosses on
                       their marks, and a second copy with the zap at Liam
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = B.ROOT
BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
INK = (225, 225, 232, 255)
DIM = (150, 152, 165, 255)
ARENA_MAT = (136, 180, 99, 255)        # the arena's green (the get-up and the walk play on it)
ROOM_FLOOR = (78, 46, 52, 255)         # the room's floorboards, roughly (the rage and the zap)


def _font(size, bold=False):
    for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'), 'arial.ttf'):
        try:
            return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', name), size)
        except OSError:
            continue
    return ImageFont.load_default()


F_HEAD, F_CAP, F_SUB = _font(20, True), _font(14, True), _font(12)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def contact(sheets, scale=4):
    """sheets: [(module, [(px, fx)], [labels])]."""
    pad, gap = 16, 10
    rows = []
    for mod, frames, labels in sheets:
        tiles = []
        for i, ((px, fx), lab) in enumerate(zip(frames, labels)):
            im = B.to_image(px)
            big = up(im, scale)
            t = Image.new('RGBA', (big.width, big.height + 44), DARK)
            t.paste(big, (0, 44))
            d = ImageDraw.Draw(t)
            d.text((4, 2), 'f%d  %s' % (i, lab[0]), fill=INK, font=F_CAP)
            d.text((4, 22), '%.3f s   %s' % (mod.TIMES[i], lab[1]), fill=DIM, font=F_SUB)
            tiles.append(t)
        w = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
        row = Image.new('RGBA', (w, tiles[0].height + 30), DARK)
        ImageDraw.Draw(row).text((0, 2), '%s.png  %d frames of 96x96, anchor (48, 95)%s' % (
            mod.NAME, len(frames), ', loops' if mod.LOOP else ', once'), fill=INK, font=F_HEAD)
        x = 0
        for t in tiles:
            row.paste(t, (x, 30))
            x += t.width + gap
        rows.append(row)
    W = max(r.width for r in rows) + 2 * pad
    H = sum(r.height for r in rows) + pad * (len(rows) + 1)
    out = Image.new('RGBA', (W, H), DARK)
    y = pad
    for r in rows:
        out.paste(r, (pad, y))
        y += r.height + pad
    return out


def gif_frames(frames, scale=3, bg=BG, pad=12):
    ims = []
    for px, fx in frames:
        im = B.to_image(px)
        base = Image.new('RGBA', (96 + 2 * pad, 96 + 2 * pad), bg)
        base.alpha_composite(im, (pad, pad))
        ims.append(base.resize((base.width * scale, base.height * scale), Image.NEAREST).convert('RGB'))
    return ims


def save_gif(path, ims, times, loop=True):
    durs = [int(round(1000 * times[min(i, len(times) - 1)])) for i in range(len(ims))]
    if not loop:
        durs[-1] = max(durs[-1], 900)          # hold the last frame, as the game does
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1, optimize=False)


#THE ROOM MOCK

def _sheet_frame(path, i, fw, fh, row=0):
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    return im.crop((fw * i, fh * row, fw * i + fw, fh * row + fh))


def place(canvas, frame, feet, at, flip=False, scale=3):
    """Put a frame on the 1920x1080 canvas as StoryActor does: the frame's rect set so its feet texel's
    left edge and its bottom edge sit on the node origin, the texture mirrored inside that same rect
    when it faces left (StoryActor only negates an offset of zero for these centred sheets)."""
    fw, fh = frame.size
    im = frame.transpose(Image.FLIP_LEFT_RIGHT) if flip else frame
    big = im.resize((fw * scale, fh * scale), Image.NEAREST)
    x = int(round(at[0] - feet[0] * scale))
    y = int(round(at[1] - (feet[1] + 1) * scale))
    canvas.alpha_composite(big, (x, y))


LAYOUT = {
    'STAND': (1260, 700), 'TALK': (1080, 600),
    'liam': (1060, 780), 'carter': (940, 620), 'josh': (860, 790), 'matt': (380, 790),
}


def room_mock(jordan_frame, zap_tip=None, title=''):
    room = Image.open(os.path.join(ROOT, 'art_source', 'jordan_room', 'approval', 'jordan_room_1080.png')).convert('RGBA')
    cv = room.copy()
    actors = [
        # (y-sort feet y, frame, feet, point, flip)
        (LAYOUT['carter'][1], _sheet_frame('Assets/Characters/Carter/carter_idle.png', 0, 96, 96), (48, 95), LAYOUT['carter'], False),
        (LAYOUT['TALK'][1], _sheet_frame('Assets/Characters/MainPlayer/player_4dir_sheet.png', 0, 32, 32, row=3), (16, 28),
         LAYOUT['TALK'], False),
        (LAYOUT['liam'][1], _sheet_frame('Assets/Characters/Liam/liam.png', 0, 64, 64), (32, 63), LAYOUT['liam'], False),
        (LAYOUT['josh'][1], _sheet_frame('Assets/Characters/Josh/josh_idle.png', 0, 80, 80), (40, 79), LAYOUT['josh'], False),
        (LAYOUT['matt'][1], _sheet_frame('Assets/Characters/Matt/matt_idle.png', 0, 96, 96), (48, 95), LAYOUT['matt'], False),
        (LAYOUT['STAND'][1], jordan_frame, (48, 95), LAYOUT['STAND'], True),
    ]
    for _y, frame, feet, at, flip in sorted(actors, key=lambda a: a[0]):
        place(cv, frame, feet, at, flip, 3)
    if zap_tip is not None:
        d = ImageDraw.Draw(cv)
        d.line([zap_tip, (LAYOUT['liam'][0], LAYOUT['liam'][1] - 90)], fill=(255, 77, 191, 255), width=6)
    if title:
        d = ImageDraw.Draw(cv)
        d.rectangle([0, 0, 1920, 36], fill=(14, 14, 18, 230))
        d.text((12, 6), title, fill=INK, font=F_HEAD)
    return cv


def walk_moving(frames, times, speed_px=200.0, seconds=2.4, scale=3, bg=ARENA_MAT):
    """The walk-away as the arena plays it: the loop on his body while it moves up the screen at the
    walk-out's WALK_SPEED (200 px/s at scale 3), so the stomp can be judged against the travel."""
    step = times[0]
    n = int(round(seconds / step))
    travel = speed_px * seconds
    W, H = 96 * scale + 60, int(travel + 96 * scale + 40)
    ims = []
    for i in range(n):
        px, fx = frames[i % len(frames)]
        im = B.to_image(px).resize((96 * scale, 96 * scale), Image.NEAREST)
        c = Image.new('RGBA', (W, H), bg)
        y = int(round(H - 20 - 96 * scale - speed_px * step * i))
        c.alpha_composite(im, (30, y))
        ims.append(c.convert('RGB'))
    return ims, [step] * n
