"""Approval mocks for Greyson's doom orb, at game scale on a real capture of his fight (its HUD included):
stills at stages 1, 3 and 5 during a pose, and two GIFs, a bank and a hit. Writes into the directory you name.

  python gdo_mock.py --out DIR --base CLEAN_ARENA.png
CLEAN_ARENA.png is a 1920x1080 capture of the fight with the floor cleared (the boss bar, his empty hype meter and
the player's HUD kept). Greyson is his shipped pose sheets at HOME (960, 560); the player his 4-dir sheet.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'greyson_fx'))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import gfx_pal as pal  # noqa: E402
import gfx_meter as M  # noqa: E402
import gdo_art as A  # noqa: E402

PROJ = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
CHAR = PROJ + '/Assets/Characters/Greyson/'
FX = CHAR + 'FX/'
PLAYER = PROJ + '/Assets/Characters/MainPlayer/player_4dir_sheet.png'
HOME = (960, 560)
CROWN_Y = HOME[1] - (111 - 26) * 3 - 3        # his crown in a pose, texel (56, 26): y 302
FOOT = (HOME[0], CROWN_Y - 6)                 # the orb's foot, 2 texels over his crown: (960, 296)
METER = (1212, 97)
FIGHTER_TINT = (0.8, 0.88, 1.0)
S = 3


def up(im, s=S):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def paste(base, im, x, y):
    base.alpha_composite(im, (int(round(x)), int(round(y)))) if x >= 0 and y >= 0 and \
        x + im.width <= base.width and y + im.height <= base.height else _paste_clip(base, im, int(round(x)), int(round(y)))


def _paste_clip(base, im, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.width, x + im.width), min(base.height, y + im.height)
    if x1 > x0 and y1 > y0:
        base.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def add_blend(base, im, x, y):
    """Godot's additive blend: base + rgb * a."""
    x, y = int(round(x)), int(round(y))
    region = (max(0, x), max(0, y), min(base.width, x + im.width), min(base.height, y + im.height))
    if region[2] <= region[0] or region[3] <= region[1]:
        return
    b = base.crop(region)
    g = im.crop((region[0] - x, region[1] - y, region[2] - x, region[3] - y))
    bp, gp = b.load(), g.load()
    for yy in range(b.height):
        for xx in range(b.width):
            r, gg, bb, a = gp[xx, yy]
            if a:
                R, G, Bb, Aa = bp[xx, yy]
                bp[xx, yy] = (min(255, R + r * a // 255), min(255, G + gg * a // 255), min(255, Bb + bb * a // 255), Aa)
    base.paste(b, region[:2])


def modulate(im, k):
    m = [1.0 + (t - 1.0) * k for t in FIGHTER_TINT]
    r, g, b, a = im.split()
    return Image.merge('RGBA', (r.point(lambda v: int(v * m[0])), g.point(lambda v: int(v * m[1])),
                                b.point(lambda v: min(255, int(v * m[2]))), a))


def with_alpha(im, k):
    r, g, b, a = im.split()
    return Image.merge('RGBA', (r, g, b, a.point(lambda v: int(v * k))))


CACHE = {}


def sheet(path):
    if path not in CACHE:
        CACHE[path] = Image.open(path).convert('RGBA')
    return CACHE[path]


def frames_of(name):
    """The doom-orb sheets as 3x images, row by row."""
    if name not in CACHE:
        CACHE[name] = [[up(pal.to_image(fr)) for fr in row] for row in A.SHEETS[name][0]()]
    return CACHE[name]


def greyson(layer, anim, f):
    fr = sheet(CHAR + 'greyson_%s.png' % anim).crop((f * 112, 0, f * 112 + 112, 112))
    paste(layer, up(fr), HOME[0] - 56 * S, HOME[1] - 112 * S)


def player(layer, pos, col, row):
    fr = sheet(PLAYER).crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))
    paste(layer, up(fr), pos[0] - 48, pos[1] - 48)


def light(base, k):
    if k <= 0:
        return
    im = up(sheet(FX + 'greyson_bomb_light.png'))
    base.alpha_composite(with_alpha(im, k))


def meter(base, lit, pop=-1, pop_f=0, full=False):
    P = M.parts()
    if full:
        base.alpha_composite(up(P['greyson_hype_full'][0].image()), METER)
        return
    cell = up(P['greyson_hype_cell'][0].image())
    for k in range(lit):
        paste(base, cell, METER[0] + S * (M.CELL_X0 + M.PITCH * k), METER[1] + S * M.CELL_Y)
    if pop >= 0:
        paste(base, up(P['greyson_hype_pop'][pop_f].image()), METER[0] + S * (M.CELL_X0 - 2 + M.PITCH * pop),
              METER[1] + S * (M.CELL_Y - 2))


def orb(base, stage, f, glow=True):
    """Stage 1-6, frame f, its foot on FOOT: the additive glow under it, then the orb."""
    s = stage - 1
    x, y = FOOT[0] - A.FOOT[0] * S, FOOT[1] - A.FOOT[1] * S
    if glow:
        add_blend(base, frames_of('greyson_doom_orb_glow')[s][f], x, y)
    paste(base, frames_of('greyson_doom_orb')[s][f], x, y)


def orb_centre(stage):
    return (FOOT[0], FOOT[1] - A.RADII[stage - 1] * S)


def vignette(base, k):
    if k <= 0:
        return
    base.alpha_composite(with_alpha(up(pal.to_image(A.vignette_frame())), k))


def streak(base, pos, vel, f, which='greyson_hype_streak'):
    ang = math.degrees(math.atan2(vel[1], vel[0]))
    row = int(round(ang / 22.5)) % 16
    im = frames_of(which)[row][f % 4]
    paste(base, im, pos[0] - A.SC[0] * S, pos[1] - A.SC[1] * S)


def label(base, xy, text, size=22):
    d = ImageDraw.Draw(base)
    font = ImageFont.load_default(size=size)
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    x, y = xy
    d.rectangle((x - 6, y - 4, x + r - l + 6, y + b - t + 6), fill=(20, 20, 28, 225))
    d.text((x - l, y - t), text, fill=(255, 255, 255, 255), font=font)


def scene(base_img, stage, pose, pose_f, orb_f=0, light_k=None, vig=0.0, player_at=(700, 620), player_cf=(0, 3),
          lit=None, pop=-1, pop_f=0, show_orb=True, extra=None):
    c = base_img.copy()
    k = (stage / 6.0) * 0.6 if light_k is None else light_k
    light(c, k)
    fig = Image.new('RGBA', c.size, (0, 0, 0, 0))
    player(fig, player_at, *player_cf)
    greyson(fig, pose, pose_f)
    c.alpha_composite(modulate(fig, k))
    if show_orb and stage >= 1:
        orb(c, stage, orb_f)
    if extra:
        extra(c)
    vignette(c, vig)
    meter(c, stage if lit is None else lit, pop, pop_f)
    return c


# ------------------------------------------------------------------------------------------------ the stills
def stills(base_img, out):
    specs = [(1, 'pose_b', 'STAGE 1 (one pose banked): a small spirit bomb forms over his head'),
             (3, 'pose_a', 'STAGE 3: bigger, crackling with his violet lightning, the floor lit blue'),
             (5, 'pose_c', 'STAGE 5: one bank from the bomb; the violet vignette creeping in (from stage 4)')]
    for stage, pose, title in specs:
        vig = 0.0 if stage < 4 else (0.5 if stage == 4 else 0.75)
        c = scene(base_img, stage, pose, 1, orb_f=1, vig=vig)
        label(c, (40, 1030 - 60), title)
        label(c, (40, 1030 - 28), '(the meter at the top lights the same cells; Greyson: his shipped %s frame at HOME)' % pose,
              size=18)
        c.save(os.path.join(out, 'mock_stage%d.png' % stage))
        c.crop((660, 90, 1500, 640)).save(os.path.join(out, 'mock_stage%d_1to1.png' % stage))
    # the three stages side by side at 1:1, cropped round him, for comparing the growth
    row = Image.new('RGBA', (3 * 420 + 16, 440), (40, 40, 44, 255))
    for i, stage in enumerate((1, 3, 5)):
        im = Image.open(os.path.join(out, 'mock_stage%d.png' % stage)).crop((750, 150, 1170, 590))
        row.paste(im, (i * 428, 0))
    row.save(os.path.join(out, 'mock_stages_1_3_5_1to1.png'))


# ------------------------------------------------------------------------------------------------ the GIFs
def gif_frames_to(path, frames, dt):
    small = [f.resize((1280, 720), Image.NEAREST).convert('RGB') for f in frames]
    pal_frames = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT) for f in small]
    pal_frames[0].save(path, save_all=True, append_images=pal_frames[1:], duration=int(dt * 1000), loop=0,
                       disposal=1)


def crowd_starts(rnd, n):
    """Where streaks leave the crowd: the stands along the top, ringside down both sides."""
    out = []
    for i in range(n):
        side = i % 3
        if side == 0:
            out.append((rnd.uniform(200, 1720), rnd.uniform(30, 80)))
        elif side == 1:
            out.append((rnd.uniform(20, 70), rnd.uniform(200, 800)))
        else:
            out.append((rnd.uniform(1850, 1900), rnd.uniform(200, 800)))
    return out


def gif_bank(base_img, out):
    """Stage 2 -> 3: the pose lands, the crowd's energy streaks in over 0.4 s, the orb flashes up a stage and the
    meter's third cell pops."""
    dt = 0.04
    frames = []
    rnd = random.Random(4)
    starts = crowd_starts(rnd, 9)
    delays = [rnd.uniform(0.0, 0.08) for _ in starts]
    t_bank, flight = 0.32, 0.40
    target = orb_centre(2)
    for i in range(int(1.6 / dt)):
        t = i * dt
        arrived = t >= t_bank + flight + 0.08
        stage = 3 if arrived else 2
        orb_f = int(t / A.FRAME_TIMES[stage - 1]) % 4
        flash = t_bank + flight + 0.08 <= t < t_bank + flight + 0.08 + A.FLASH_TIME
        pop_f = int((t - (t_bank + flight + 0.08)) / 0.05)
        lit = 3 if arrived else 2

        def extra(c, t=t):
            for (sx, sy), d in zip(starts, delays):
                u = (t - t_bank - d) / flight
                if not 0.0 <= u < 1.0:
                    continue
                e = u * u                                  # speeding up into the orb
                # a gentle bow: rising off the crowd, curving into the orb
                bx, by = (sx + target[0]) / 2.0, min(sy, target[1]) - 60
                x = (1 - e) ** 2 * sx + 2 * (1 - e) * e * bx + e * e * target[0]
                y = (1 - e) ** 2 * sy + 2 * (1 - e) * e * by + e * e * target[1]
                vx = 2 * (1 - e) * (bx - sx) + 2 * e * (target[0] - bx)
                vy = 2 * (1 - e) * (by - sy) + 2 * e * (target[1] - by)
                streak(c, (x, y), (vx, vy), i)
        c = scene(base_img, stage, 'pose_b', 1, orb_f=4 if flash else orb_f,
                  light_k=(stage / 6.0) * 0.6, lit=lit, pop=2 if 0 <= pop_f < 3 and arrived else -1,
                  pop_f=max(0, min(2, pop_f)), extra=extra)
        frames.append(c)
    gif_frames_to(os.path.join(out, 'gif_bank.gif'), frames, dt)
    frames[int((t_bank + 0.2) / dt)].save(os.path.join(out, 'gif_bank_streaks_still.png'))


def gif_hit(base_img, out):
    """Stage 4: the player steps in and punches; the orb cracks and flies apart, the streaks scatter back to the
    crowd, the meter drains, the light and the vignette go out."""
    dt = 0.04
    frames = []
    rnd = random.Random(8)
    ends = crowd_starts(rnd, 8)
    t_hit = 0.36
    centre = orb_centre(4)
    P = (1178, 500)                                    # on his right, clear of his cannon, punching left
    for i in range(int(1.6 / dt)):
        t = i * dt
        after = t - t_hit
        punch_col = 0 if t < t_hit - 0.12 else (7 if t < t_hit - 0.04 else (8 if t < t_hit + 0.12 else 0))
        pose, pf = ('pose_a', 1) if after < 0 else ('pose_hit', 0 if after < 0.12 else 1)
        burst_f = int(after / 0.06) if after >= 0 else -1
        k0 = (4 / 6.0) * 0.6
        k = k0 if after < 0 else max(0.0, k0 * (1 - after / 0.5))
        vig = 0.5 if after < 0 else max(0.0, 0.5 * (1 - after / 0.4))
        lit = 4 if after < 0 else max(0, 4 - int(after / 0.12))

        def extra(c, t=t, after=after, burst_f=burst_f):
            if 0 <= burst_f < 6:
                im = frames_of('greyson_doom_orb_burst')[1][burst_f]
                paste(c, im, centre[0] - A.BC[0] * S, centre[1] - A.BC[1] * S)
            if after >= 0.05:
                for j, (ex, ey) in enumerate(ends):
                    u = (after - 0.05 - 0.02 * j) / 0.45
                    if not 0.0 <= u < 1.0:
                        continue
                    e = 1 - (1 - u) ** 2                   # flung out fast, slowing
                    x, y = centre[0] + (ex - centre[0]) * e, centre[1] + (ey - centre[1]) * e
                    streak(c, (x, y), (ex - centre[0], ey - centre[1]), i + j)
        c = scene(base_img, 4, pose, pf, orb_f=int(t / A.FRAME_TIMES[3]) % 4, light_k=k, vig=vig,
                  player_at=P, player_cf=(punch_col, 2), lit=lit, show_orb=after < 0, extra=extra)
        frames.append(c)
    gif_frames_to(os.path.join(out, 'gif_hit.gif'), frames, dt)
    frames[int((t_hit + 0.07) / dt)].save(os.path.join(out, 'gif_hit_burst_still.png'))


def main(argv):
    if '--out' not in argv or '--base' not in argv:
        print(__doc__)
        return 1
    out = argv[argv.index('--out') + 1]
    base_img = Image.open(argv[argv.index('--base') + 1]).convert('RGBA')
    os.makedirs(out, exist_ok=True)
    stills(base_img, out)
    gif_bank(base_img, out)
    gif_hit(base_img, out)
    print('mocks written to', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
