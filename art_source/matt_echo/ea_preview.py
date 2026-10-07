"""Previews for the Echo Roars approval pass. Reads the project's art; writes only into the folder it
is given (never the project; guard.py refuses it). A bare run writes nothing.

    python ea_preview.py <out_dir>

  matt_echo_approval.png / _3x.png   the three approval frames (f0, f1, f4), 1x and nearest 3x
  contact_sheet.png                  live idle + roar beside the new sheet at 4x, then game scale (3x)
                                     on the arena mat
  arena_mockup.png                   1920x1080: the arena MattBossFightScene uses, Matt at HOME, Burak,
                                     a red roar ring (+ its echo), a dashed ghost ring, the gold BOOMBURST
                                     wall, at real scale, and the boss-bar block outlined
  arena_moments.png                  the same arena at the three moments, side by side at half size
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard  # noqa: E402,F401
import env  # noqa: E402
import ea_base as E  # noqa: E402,F401
from ea_base import B, F, V  # noqa: E402
import ea_echo as EC  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

LIVE = env.LIVE
ENV_DIR = os.path.join(LIVE, 'Assets', 'Environment')
PLAYER_SHEET = os.path.join(LIVE, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
SCALE = 3
HOME = (960, 620)                    # his feet (MattStateMachine HOME)
ANCHOR = (48, 95)                    # MattArtLayout.ANCHOR: SPRITE_OFFSET (0, -48) at scale 3
MOUTH = (48, 51)                     # the roar mouth: every Echo ring's centre
PLAYER_AT = (1290, 772)
BOSS_BAR = (680, 36, 1240, 180)
BG = (14, 14, 18, 255)


def font(n):
    for f in ('arialbd.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def live(name):
    return Image.open(os.path.join(env.LIVE_MATT, name + '.png')).convert('RGBA')


def frame(sheet, i):
    return sheet.crop((96 * i, 0, 96 * i + 96, 96))


def texel_to_screen(tx, ty):
    """Texel (tx, ty) of a 96x96 Matt frame drawn at HOME, to the centre of that texel on screen."""
    left = HOME[0] - SCALE * ANCHOR[0]
    top = HOME[1] - SCALE * (ANCHOR[1] + 1)
    return (left + SCALE * tx + SCALE / 2.0, top + SCALE * ty + SCALE / 2.0)


# ---------------------------------------------------------------------------------------- the arena
def nearest(im, w, h):
    return im.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.NEAREST)


def paste_centered(dst, im, cx, cy):
    dst.alpha_composite(im, (int(round(cx - im.width / 2.0)), int(round(cy - im.height / 2.0))))


def rope(dst, tex, pos, scale, region=None, rot=False):
    im = tex
    if region:
        x0, y0, w, h = region
        im = tex.crop((int(round(x0)), int(round(y0)), int(round(x0 + w)), int(round(y0 + h))))
    im = nearest(im, im.width * scale[0], im.height * scale[1])
    if rot:
        im = im.rotate(-90, expand=True)          # Godot's +90 degrees, clockwise on a y-down screen
    paste_centered(dst, im, *pos)


def pole(dst, tex, pos, scale, fh=False, fv=False):
    im = tex
    if fh:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if fv:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    paste_centered(dst, nearest(im, im.width * scale[0], im.height * scale[1]), *pos)


def arena():
    """ArenaScene.tscn's drawing order and transforms, frame 0 of both crowds."""
    out = Image.new('RGBA', (1920, 1080), (0, 0, 0, 255))
    ring = Image.open(os.path.join(ENV_DIR, 'arena_ringside.png')).convert('RGBA')
    out.alpha_composite(nearest(ring, 1920, 1080), (0, 0))
    rc = Image.open(os.path.join(ENV_DIR, 'arena_ringside_crowd.png')).convert('RGBA').crop((0, 0, 640, 360))
    out.alpha_composite(nearest(rc, 1920, 1080), (0, 0))
    crowd = Image.open(os.path.join(ENV_DIR, 'crowd_v3.png')).convert('RGBA').crop((0, 0, 640, 40))
    paste_centered(out, nearest(crowd, 1920, 120), 960, 60)
    mat = Image.open(os.path.join(ENV_DIR, 'arena_mat.png')).convert('RGBA')
    out.alpha_composite(nearest(mat, mat.width * 3, mat.height * 3), (111, 99 + 5 * 3))
    return out


def ropes(out):
    b = Image.open(os.path.join(ENV_DIR, 'boundaries.png')).convert('RGBA')
    p = Image.open(os.path.join(ENV_DIR, 'pole.png')).convert('RGBA')
    s = (7.783335, 6.9375)
    rope(out, b, (960 - 608, 100 + 14), s, (0, 0, 128.47955, 32))
    rope(out, b, (960 + 667.5, 100 + 14), s, (156.22682, 0, 143.77318, 32))
    rope(out, b, (100 - 8, 540 + 31.41027), (3.9833364, 6.9375), rot=True)
    rope(out, b, (1820 - 15, 540 + 27.50096), (3.9273026, 6.9375), rot=True)
    rope(out, b, (960 - 609.25, 980 + 8), s, (0, 0, 128.80088, 32))
    rope(out, b, (960 + 666.25, 980 + 8), s, (156.54815, 0, 143.45185, 32))
    pole(out, p, (960 - 855, 107), (1.5859377, 2.03125))
    pole(out, p, (960 + 847, 109), (1.5859377, 2.03125), fh=True)
    pole(out, p, (960 - 847, 964), (1.5859377, 1.1875007), fv=True)
    pole(out, p, (960 + 846, 965), (1.5859377, 1.1875007), fh=True, fv=True)


# ---------------------------------------------------------------------------------------- rings
def hexa(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def draw_ring(layer, c, r, width, col, dashes=0):
    d = ImageDraw.Draw(layer)
    box = (c[0] - r, c[1] - r, c[0] + r, c[1] + r)
    if not dashes:
        d.ellipse(box, outline=col, width=max(1, int(round(width))))
        # PIL draws the stroke inward from the box: re-centre it on r
        return
    seg = 360.0 / dashes
    for k in range(dashes):
        a0 = k * seg
        d.arc(box, a0, a0 + seg * 0.6, fill=col, width=max(1, int(round(width))))


def centred_ring(layer, c, r, width, col, dashes=0):
    """A stroke of `width` centred on radius r (PIL strokes inward from the bounding box)."""
    draw_ring(layer, c, r + width / 2.0, width, col, dashes)


def red_ring(dst, c, r, alpha=1.0):
    """PLAN 3b RED: the approved yell-ring layers (edge #4F4D96 21, flank #C4C9FA 15, core #F2F3FF 9) plus an
    outer rim in his roar red #FF4A58."""
    lay = Image.new('RGBA', dst.size, (0, 0, 0, 0))
    a = int(255 * alpha)
    centred_ring(lay, c, r + 12.5, 4, hexa('FF4A58', a))
    centred_ring(lay, c, r, 21, hexa('4F4D96', a))
    centred_ring(lay, c, r, 15, hexa('C4C9FA', a))
    centred_ring(lay, c, r, 9, hexa('F2F3FF', a))
    dst.alpha_composite(lay)


def ghost_ring(dst, c, r):
    """PLAN 3b GHOST: pale steel sampled from demon_feint.png, 24 dashed arcs, 50% alpha."""
    lay = Image.new('RGBA', dst.size, (0, 0, 0, 0))
    centred_ring(lay, c, r, 15, hexa('9BADB7', 128), dashes=24)
    centred_ring(lay, c, r, 7, hexa('E6ECF2', 128), dashes=24)
    dst.alpha_composite(lay)


def gold_wall(dst, c, r):
    """PLAN 3b BOOMBURST: a leading edge #FFF3A8 10 px, the body #FFCB3C drawn 90 px behind it, the inner
    edge #C87414. Only the leading edge's first touch counts."""
    lay = Image.new('RGBA', dst.size, (0, 0, 0, 0))
    centred_ring(lay, c, r - 95, 10, hexa('C87414', 200))
    centred_ring(lay, c, r - 47.5, 85, hexa('FFCB3C', 175))
    centred_ring(lay, c, r, 10, hexa('FFF3A8', 255))
    dst.alpha_composite(lay)


# ---------------------------------------------------------------------------------------- scene
def player_sprite():
    sheet = Image.open(PLAYER_SHEET).convert('RGBA')
    up = sheet.crop((0, 32, 32, 64))          # row 1 (UP), col 0: facing him
    return nearest(up, 96, 96)


def matt_sprite(im96):
    return nearest(im96, 288, 288)


def compose(matt96, rings, labels=True):
    out = arena()
    c = texel_to_screen(*MOUTH)
    # the floor rings and the people, then the ropes over them (the fights draw the ropes at z 1)
    out.alpha_composite(matt_sprite(matt96), (HOME[0] - SCALE * ANCHOR[0], HOME[1] - SCALE * (ANCHOR[1] + 1)))
    paste_centered(out, player_sprite(), *PLAYER_AT)
    for kind, r in rings:
        {'red': lambda: red_ring(out, c, r), 'echo': lambda: red_ring(out, c, r, 0.8),
         'ghost': lambda: ghost_ring(out, c, r), 'gold': lambda: gold_wall(out, c, r)}[kind]()
    ropes(out)
    d = ImageDraw.Draw(out)
    x0, y0, x1, y1 = BOSS_BAR
    for i in range(x0, x1, 16):
        d.line([(i, y0), (min(i + 9, x1), y0)], fill=(255, 255, 255, 230), width=3)
        d.line([(i, y1), (min(i + 9, x1), y1)], fill=(255, 255, 255, 230), width=3)
    for j in range(y0, y1, 16):
        d.line([(x0, j), (x0, min(j + 9, y1))], fill=(255, 255, 255, 230), width=3)
        d.line([(x1, j), (x1, min(j + 9, y1))], fill=(255, 255, 255, 230), width=3)
    if labels:
        f = font(24)
        d.text((x0 + 10, y0 + 8), 'boss bar block (x 680-1240, y 36-180)', font=f, fill=(255, 255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0, 255))
    return out, c


def label(d, xy, text, col, size=26):
    d.text(xy, text, font=font(size), fill=col, stroke_width=4, stroke_fill=(0, 0, 0, 255))


def mockup(sheet):
    rings = [('echo', 110), ('ghost', 270), ('red', math.hypot(PLAYER_AT[0] - 961.5, PLAYER_AT[1] - 486.5) - 10),
             ('gold', 760)]
    out, c = compose(frame(sheet, 4), rings)
    d = ImageDraw.Draw(out)
    label(d, (c[0] + 118, c[1] - 120), 'ECHO: the red ring at 80%, 1 beat (~710 px) behind its roar', (255, 214, 220, 255), 22)
    label(d, (c[0] - 470, c[1] + 150), 'GHOST: pale dashed (the psych)', (230, 236, 242, 255))
    label(d, (PLAYER_AT[0] + 60, PLAYER_AT[1] - 30), 'ROAR: red-rimmed, parry', (255, 120, 132, 255))
    label(d, (c[0] - 760, c[1] + 330), 'BOOMBURST: gold wall, dash INTO it', (255, 243, 168, 255))
    label(d, (130, 1000), 'Matt f4 boomburst_blast at HOME (960,620), scale 3; every ring centred on his roar '
          'mouth, texel (48,51) = screen (%d,%d). All four ring kinds at once for comparison (a sketch, not one moment).' % (c[0], c[1]),
          (255, 255, 255, 255), 20)
    return out


def moments(sheet, roar):
    a, _ = compose(frame(roar, 1), [('echo', 90), ('red', 90 + 710)], labels=False)
    b, _ = compose(frame(sheet, 1), [('red', 80), ('ghost', 80 + 710)], labels=False)
    c, _ = compose(frame(sheet, 4), [('gold', 420)], labels=False)
    tiles = []
    for im, text in ((a, 'ROAR (matt_roar f1) and its ECHO 1 beat behind'), (b, 'PSYCH (f1): the ghost out ahead, its real red echo 1 beat behind'),
                     (c, 'BOOMBURST  (f4)')):
        half = im.resize((960, 540), Image.NEAREST)
        lab = Image.new('RGBA', (960, 40), BG)
        ImageDraw.Draw(lab).text((10, 8), text, font=font(22), fill=(240, 240, 240, 255))
        t = Image.new('RGBA', (960, 580), BG)
        t.paste(lab, (0, 0))
        t.paste(half, (0, 40))
        tiles.append(t)
    return V.row(tiles, gap=12)


# ---------------------------------------------------------------------------------------- contact sheet
def contact(sheet):
    idle, roar = live('matt_idle'), live('matt_roar')
    f = font(16)

    def tile(im, text, s, mark=False):
        big = V.up(im, s)
        lab = Image.new('RGBA', (big.width, 26), (60, 40, 10, 255) if mark else BG)
        ImageDraw.Draw(lab).text((5, 4), text, font=f, fill=(255, 230, 150, 255) if mark else (230, 230, 235, 255))
        out = Image.new('RGBA', (big.width, big.height + 26), BG)
        out.paste(lab, (0, 0))
        out.paste(big, (0, 26))
        return out
    live_row = V.row([tile(frame(idle, 0), 'LIVE matt_idle f0', 4)] +
                     [tile(frame(roar, i), 'LIVE matt_roar f%d' % i, 4) for i in range(4)])
    new_row = V.row([tile(frame(sheet, i), ('* ' if i in EC.APPROVAL else '') + EC.LABELS[i], 4, i in EC.APPROVAL)
                     for i in range(6)])
    game = V.on_mat([frame(idle, 0), frame(roar, 1), frame(sheet, 0), frame(sheet, 1), frame(sheet, 4)], 3)
    glab = Image.new('RGBA', (game.width, 30), BG)
    ImageDraw.Draw(glab).text((6, 6), 'GAME SCALE (3x) on the mat:  live idle | live roar f1 | NEW f0 inhale | '
                              'NEW f1 psych | NEW f4 blast', font=f, fill=(230, 230, 235, 255))
    head = Image.new('RGBA', (1200, 34), BG)
    ImageDraw.Draw(head).text((6, 6), 'matt_echo approval pass (* = for approval: f0, f1, f4)', font=font(20),
                              fill=(255, 255, 255, 255))
    return V.col([head, live_row, new_row, glab, game], gap=10)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out = os.path.abspath(argv[0])
    real = os.path.normcase(os.path.realpath(out))
    if real.startswith(os.path.normcase(env.LIVE)):
        print('NOT WRITTEN: %s is inside the project' % out)
        return 1
    os.makedirs(out, exist_ok=True)
    sheet = Image.open(os.path.join(out, EC.NAME + '.png')).convert('RGBA')
    roar = live('matt_roar')
    appr = Image.new('RGBA', (96 * 3, 96), (0, 0, 0, 0))
    for k, i in enumerate(EC.APPROVAL):
        appr.alpha_composite(frame(sheet, i), (96 * k, 0))
    appr.save(os.path.join(out, 'matt_echo_approval.png'))
    appr.resize((96 * 9, 288), Image.NEAREST).save(os.path.join(out, 'matt_echo_approval_3x.png'))
    contact(sheet).save(os.path.join(out, 'contact_sheet.png'))
    mockup(sheet).save(os.path.join(out, 'arena_mockup.png'))
    moments(sheet, roar).save(os.path.join(out, 'arena_moments.png'))
    print('ring centre on screen:', texel_to_screen(*MOUTH))
    print('wrote previews to', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
