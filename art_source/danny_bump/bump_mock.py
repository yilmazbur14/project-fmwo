"""The approval pass's in-game views: the new art at game scale (3x) on the real arena.

  arena_capture.png   a 1920x1080 still of the live Danny fight (the scene, its HUD, Danny and the player hidden),
                      captured by cap_arena.gd.txt through Godot's own renderer (windowed at 100,100; nothing written
                      into the project). Everything else here is composited on it at the scene's own positions.

Makes, into the folder it is given (bump_export.py decides which, and guards every write):
  danny_bump_mock_1920x1080.png    the ring-out: Danny's belly slammed into the player at the right rope, the rope
                                   bowing under them, with the Spit's puddles on the mat round them
  danny_onback_mock_1920x1080.png  the payoff: Danny dazed on his back beside the player, a hop's worm splash
                                   soaking into the mat behind them
  gif_belly_bump.gif               wind-up, charge, contact, the shove into the ropes, the skid back
  gif_bounce_onto_back.gif         the fifth slam parried: off the fists, flipped over, dazed on his back, a punch,
                                   rolled back up to the idle
  gif_worm_splash.gif              a hop landing: the splash zone's outline (code-drawn, mocked here), the worms
                                   flying out to its edge, the landing puddle's approved splat, the hop back up
Approved sheets are only READ (Assets/Characters/Danny/Sumo, Danny/FX, MainPlayer/player_4dir_sheet.png).
"""
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SUMO = os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'Sumo')
FXD = os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'FX')
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
ARENA = os.path.join(HERE, 'arena_capture.png')
S3 = 3
FLOOR_FLATTEN = 0.36


# ------------------------------------------------------------------ SPRITES
def sheet_frames(path, fw, fh, row=0):
    im = Image.open(path).convert('RGBA')
    return [im.crop((i * fw, row * fh, i * fw + fw, row * fh + fh)) for i in range(im.width // fw)]


class Art:
    def __init__(self, built):
        self.b = built
        self.idle = sheet_frames(os.path.join(SUMO, 'danny_sumo_idle.png'), 176, 144)
        self.air = sheet_frames(os.path.join(SUMO, 'danny_sumo_air.png'), 176, 144)
        self.slam = sheet_frames(os.path.join(SUMO, 'danny_sumo_slam.png'), 176, 144)
        self.splat = sheet_frames(os.path.join(FXD, 'danny_worm_splat.png'), 100, 52)
        self.puddle = sheet_frames(os.path.join(FXD, 'danny_worm_puddle.png'), 100, 52)
        self.dust = sheet_frames(os.path.join(FXD, 'danny_sumo_dust.png'), 72, 32, row=0)
        self.pl = {r: sheet_frames(PLAYER, 32, 32, row=r) for r in range(4)}

    def body(self, sheet, i):
        d = self.b[sheet]
        w, h = d['size']
        f = d['frames'][i]
        if d['kind'] == 'fx':
            return f['image']
        from bump_rig import FT
        return FT.image_of(f['px'], w, h)

    def fx(self, sheet, i):
        return self.b[sheet]['frames'][i]['image']


def put(canvas, im, at, anchor, flip=False, alpha=1.0):
    """Draw a 1x frame at 3x so that its texel `anchor` lands on the screen point `at`."""
    big = im.resize((im.width * S3, im.height * S3), Image.NEAREST)
    ax = anchor[0]
    if flip:
        big = big.transpose(Image.FLIP_LEFT_RIGHT)
        ax = im.width - 1 - anchor[0]
    if alpha < 1.0:
        a = big.getchannel('A').point(lambda v: int(v * alpha))
        big.putalpha(a)
    x = int(round(at[0] - ax * S3))
    y = int(round(at[1] - anchor[1] * S3))
    _paste_clipped(canvas, big, x, y)


def _paste_clipped(canvas, big, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + big.width), min(canvas.height, y + big.height)
    if x1 <= x0 or y1 <= y0:
        return
    canvas.alpha_composite(big.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def dashed_ellipse(canvas, cx, cy, rx, ry, rgba=(255, 214, 64, 178), dash=10, width=3):
    """A stand-in for the code-drawn splash-zone outline (the dodge tell's yellow at about 0.7 alpha)."""
    ov = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    n = 120
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    for i in range(n):
        if (i // 2) % 2 == 0:
            d.line((pts[i], pts[i + 1]), fill=rgba, width=width)
    canvas.alpha_composite(ov)


# ------------------------------------------------------------------ GEOMETRY FROM THE SHEETS
def anchor_of(built, sheet):
    w, h = built[sheet]['size']
    return (w // 2, h - 1)


def belly_front(built, i):
    return built['danny_sumo_bump']['frames'][i]['anchors']['belly_front']


FEET_Y = 760
PLAYER_ANCHOR = (16, 31)
PLAYER_HALF = 27                     # the player's hurtbox half-width, screen px (about 9 texels at 3x)
RIGHT_ROPE = 1805                    # the right rope's inner line, screen x (ArenaScene: rightWall)


# ------------------------------------------------------------------ THE MOCKS
def puddles(canvas, art, spots, phase=0):
    for (x, y) in spots:
        put(canvas, art.puddle[phase % 4], (x, y), (50, 26))


def mock_bump(art, built):
    """The ring-out, at the rope's peak: the player pinned against the right rope, Danny's belly slammed flat on
    them, the rope bowed out behind them; the Spit's puddles on the mat round the fight."""
    c = Image.open(ARENA).convert('RGBA')
    puddles(c, art, [(420, 380), (760, 850), (1180, 330), (1480, 900)], 1)
    px = RIGHT_ROPE - PLAYER_HALF
    near = px - PLAYER_HALF
    bf = belly_front(built, 7)
    dx = (near - (bf[0] - anchor_of(built, 'danny_sumo_bump')[0]) * S3)
    put(c, art.body('danny_sumo_bump', 7), (dx, FEET_Y), anchor_of(built, 'danny_sumo_bump'))
    put(c, art.pl[2][0], (px, FEET_Y), PLAYER_ANCHOR)
    rp = built['danny_rope_impact']['pivot']
    put(c, art.fx('danny_rope_impact', 1), (RIGHT_ROPE, FEET_Y - 48), rp)
    return c


def mock_onback(art, built):
    """The payoff: Danny dazed on his back (the loop's second frame) beside the player, a hop's splash soaking into
    the mat behind them, the landing puddle it left."""
    c = Image.open(ARENA).convert('RGBA')
    sp = built['danny_worm_splash']['pivot']
    put(c, art.puddle[2], (1340, 470), (50, 26))
    put(c, art.fx('danny_worm_splash', 4), (1340, 470), sp)
    ga = anchor_of(built, 'danny_sumo_back')
    put(c, art.body('danny_sumo_back', 4), (935, 800), ga)
    put(c, art.pl[3][7], (560, 800), PLAYER_ANCHOR)
    return c


# ------------------------------------------------------------------ THE GIFS
def to_gif(frames, durations, path, save):
    pal = [f.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
           for f in frames]
    save(pal[0], path, save_all=True, append_images=pal[1:], duration=durations, loop=0, disposal=1, optimize=False)


def lerp(a, b, t):
    return a + (b - a) * t


def gif_bump(art, built, path, save):
    """Wind-up, charge, contact, the shove to the rope, the rope's burst, the springs back and the skid."""
    crop = (560, 230, 1900, 870)
    arena = Image.open(ARENA).convert('RGBA')
    A = anchor_of(built, 'danny_sumo_bump')
    fr = built['danny_sumo_bump']['frames']
    rp = built['danny_rope_impact']['pivot']
    DT = 0.04
    X0, PX0 = 860.0, 1480.0
    frames, durs = [], []
    events = []                                           # (duration, draw function)

    def still(kind, dur, dx, px, rope=None, dust=None, pl_frame=0):
        events.append((dur, dict(kind=kind, dx=dx, px=px, rope=rope, dust=dust, pl=pl_frame)))

    still(('idle', 0), 0.30, X0, PX0)
    still(('bump', 0), 0.25, X0, PX0)
    still(('bump', 1), 0.20, X0, PX0)
    still(('bump', 2), 0.35, X0, PX0)
    # the run: 1400 px/s until the belly front meets the player's near edge
    x = X0
    t = 0.0
    k = 0
    while True:
        i = 3 + (k % 4)
        bf = (fr[i]['anchors']['belly_front'][0] - A[0]) * S3
        if x + bf >= PX0 - PLAYER_HALF:
            break
        still(('bump', i), DT, x, PX0)
        x += 1400 * DT
        t += DT
        if t >= 0.06 * (k + 1):
            k += 1
    # contact: carried to the rope at 1100 px/s, the belly pinned on them
    bf7 = (fr[7]['anchors']['belly_front'][0] - A[0]) * S3
    px = PX0
    target = RIGHT_ROPE - PLAYER_HALF
    while px < target:
        still(('bump', 7), DT, px - PLAYER_HALF - bf7, px, pl_frame=9)
        px = min(target, px + 1100 * DT)
    dx_pin = target - PLAYER_HALF - bf7
    # the rope: its burst and bow, the hit-stop, the pin
    for (ri, dur) in ((0, 0.05), (1, 0.10), (1, 0.15)):
        still(('bump', 7), dur, dx_pin, target, rope=ri, pl_frame=9)
    # the springs back 90 px over 0.20 s while he skids back 160 px over 0.35 s
    for j in range(9):
        tt = (j + 1) * DT
        ppx = target - 90 * min(1.0, tt / 0.20)
        ddx = dx_pin - 160 * min(1.0, tt / 0.35)
        ri = 2 if tt <= 0.10 else (3 if tt <= 0.17 else (4 if tt <= 0.24 else 5))
        still(('bump', 9), DT, ddx, ppx, rope=ri, dust=j % 5, pl_frame=0)
    still(('idle', 0), 0.60, dx_pin - 160, target - 90)
    for dur, e in events:
        c = arena.copy()
        puddles(c, art, [(760, 850), (1180, 330)], 1)
        sheet, i = e['kind']
        if sheet == 'idle':
            put(c, art.idle[i], (e['dx'], FEET_Y), (88, 143))
        else:
            put(c, art.body('danny_sumo_bump', i), (e['dx'], FEET_Y), A)
            if e['dust'] is not None:
                lead = e['dx'] + 40
                put(c, art.dust[e['dust']], (lead, FEET_Y), (52, 28))
        put(c, art.pl[2][e['pl']], (e['px'], FEET_Y), PLAYER_ANCHOR)
        if e['rope'] is not None:
            put(c, art.fx('danny_rope_impact', e['rope']), (RIGHT_ROPE, FEET_Y - 48), rp)
        frames.append(c.crop(crop))
        durs.append(int(round(dur * 1000)))
    to_gif(frames, durs, path, save)


def gif_bounce(art, built, path, save):
    """The fifth slam parried: the tuck drops on the player, is knocked off the fists (the front-view frame),
    flips over on the arc to the back spot, crashes onto his back, the dazed loop with a punch's flinch, the
    roll back up and the hand-over to the idle."""
    crop = (440, 100, 1680, 900)
    arena = Image.open(ARENA).convert('RGBA')
    GA = anchor_of(built, 'danny_sumo_back')
    LX, LY = 760.0, 800.0                               # the landing spot (the player's feet)
    BX = LX + 375.0                                     # the back spot: his lying box's near edge 60 px past the player's hurtbox, head toward them
    events = []
    for j in range(8):                                  # the hang, rocking
        events.append((0.06, ('air', j % 4, LX, LY - 380)))
    for j in range(6):                                  # the drop, heavier at the end
        t = (j + 1) / 6.0
        events.append((0.05, ('slam', 0, LX, LY - 380 * (1 - t ** 1.5))))
    events.append((0.15, ('back', 0, LX, LY)))          # knocked off the fists
    for j in range(7):                                  # flipped over on the arc (peak 140 px)
        t = (j + 1) / 8.0
        events.append((0.043, ('back', 1, lerp(LX, BX, t), LY - 140 * 4 * t * (1 - t))))
    events.append((0.15, ('back', 2, BX, LY)))
    order = [3, 4, 5, 6, 3, 4, 5, 6, 7, 7, 3, 4, 5, 6]
    for i in order:
        events.append((0.14 if i != 7 else 0.06, ('back', i, BX, LY)))
    for i in (8, 9, 10):
        events.append((0.15, ('back', i, BX, LY)))
    events.append((0.70, ('idle', 0, BX, LY)))
    frames, durs = [], []
    for dur, (kind, i, x, y) in events:
        c = arena.copy()
        put(c, art.pl[1][0], (LX, LY + 10), PLAYER_ANCHOR)
        if kind == 'air':
            put(c, art.air[i], (x, y), (88, 143))
        elif kind == 'slam':
            put(c, art.slam[i], (x, y), (88, 143))
        elif kind == 'idle':
            put(c, art.idle[i], (x, y), (88, 143))
        else:
            put(c, art.body('danny_sumo_back', i), (x, y), GA)
        frames.append(c.crop(crop))
        durs.append(int(round(dur * 1000)))
    to_gif(frames, durs, path, save)


def gif_splash(art, built, path, save):
    """A hop: the tuck hangs, the zone outline goes up at the latch, he drops, lands (the approved impact frame),
    the worms fly out to the zone's edge while the landing puddle's approved splat plays, he rebounds and rises;
    the puddle stays. The player waits outside the zone."""
    crop = (560, 100, 1440, 920)
    arena = Image.open(ARENA).convert('RGBA')
    SP = built['danny_worm_splash']['pivot']
    LX, LY = 960.0, 780.0
    ZRX, ZRY = 230, 83
    events = []
    for j in range(5):
        events.append((0.06, dict(dan=('air', j % 4, LY - 380), zone=j >= 2)))
    for j in range(5):
        t = (j + 1) / 5.0
        events.append((0.056, dict(dan=('slam', 0, LY - 380 * (1 - t ** 1.5)), zone=True)))
    # landing: the splash's 6 frames at 0.05 s; the landing puddle's splat over 0.40 s (0.08 a frame)
    seq = [('slam', 1, LY), ('slam', 2, LY - 10), ('slam', 2, LY - 60), ('air', 0, LY - 140), ('air', 1, LY - 230),
           ('air', 2, LY - 320), ('air', 3, LY - 380), ('air', 0, LY - 380)]
    for j in range(8):
        events.append((0.05, dict(dan=seq[j], splash=j if j < 6 else None, splat=min(4, j * 5 // 8))))
    for j in range(8):
        events.append((0.12, dict(dan=None, puddle=j % 4)))
    frames, durs = [], []
    for dur, e in events:
        c = arena.copy()
        if e.get('zone'):
            dashed_ellipse(c, LX, LY, ZRX, ZRY)
        if e.get('puddle') is not None:
            put(c, art.puddle[e['puddle']], (LX, LY), (50, 26))
        if e.get('splat') is not None:
            put(c, art.splat[e['splat']], (LX, LY), (50, 26))
        if e.get('splash') is not None:
            put(c, art.fx('danny_worm_splash', e['splash']), (LX, LY), SP)
        put(c, art.pl[1][0], (LX + 330, LY + 100), PLAYER_ANCHOR)
        if e.get('dan'):
            kind, i, y = e['dan']
            put(c, (art.air if kind == 'air' else art.slam)[i], (LX, y), (88, 143))
        frames.append(c.crop(crop))
        durs.append(int(round(dur * 1000)))
    to_gif(frames, durs, path, save)


def make_all(built, dest, save):
    need = ('danny_sumo_bump', 'danny_sumo_back', 'danny_worm_splash', 'danny_rope_impact', 'danny_big_slam_impact')
    if any(n not in built for n in need):
        print('mock/GIFs skipped: they need every sheet built')
        return
    art = Art(built)
    save(mock_bump(art, built), os.path.join(dest, 'danny_bump_mock_1920x1080.png'))
    save(mock_onback(art, built), os.path.join(dest, 'danny_onback_mock_1920x1080.png'))
    gif_bump(art, built, os.path.join(dest, 'gif_belly_bump.gif'), save)
    gif_bounce(art, built, os.path.join(dest, 'gif_bounce_onto_back.gif'), save)
    gif_splash(art, built, os.path.join(dest, 'gif_worm_splash.gif'), save)
