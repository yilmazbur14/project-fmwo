"""The approval mock: the whole cutscene composited on real arena captures (Godot movie writer,
player + HUD hidden, crowd stepped through calm / cheer / roar in-engine), at the game's texel
scale, then scaled 2x (full screen) and 4x (close-up) with nearest-neighbour.

Timing is COMPRESSED for the GIF: the drop lands at 6.5 s here; in the game it is the song's drop
(~9-10 s in) and the gather loop absorbs the difference. See contract.json for the real rules.

    python mock.py [A|B]
"""
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont
from common import save, OUT, ASSETS
import champion as C
import burak as BK
import build as BD
import fx_screen as FS

TAKE = sys.argv[1] if len(sys.argv) > 1 else 'A'
CAP = os.path.realpath(os.path.join(OUT, '..', 'cap'))
FPS = 20
DT = 1.0 / FPS

# where things sit, in texels (screen px / 3)
BODY = (304, 149)                          # body (0,0) at the mark: sprite centre = screen (960, 495)
CELL_AT = (BODY[0] - C.BODY_AT[0], BODY[1] - C.BODY_AT[1])
WALK_FROM_Y = 10                           # body y at the top doorway (feet on the rope line)

T_FADE_IN = 0.5
T_WALK0, T_WALK1 = 0.5, 2.8
SEQ = [('arrive', 0.30), ('take_in', 0.40), ('reach', 0.15), ('grab', 0.25)]
T_DROP = 6.5
T_FADE0, T_FADE1 = 10.5, 13.0
T_END = 16.0
T_CRED0, T_CRED1 = 13.6, 14.4           # optional credits still fades in on the black
CAPTION = (3.0, 6.4, 'ANNOUNCER: "And announcing your new discord champion of this server...."')

bgs = [Image.open(os.path.join(CAP, f'bg_state_{s:02d}.png')).convert('RGBA') for s in range(11)]
sheet = Image.open(os.path.join(ASSETS, 'Characters/MainPlayer/player_4dir_sheet.png')).convert('RGBA')
walk = [sheet.crop((c * 32, 0, c * 32 + 32, 32)) for c in range(5)]
champ = {n: C.compose(TAKE, n) for n in BK.ORDER}
idle = [BD.stand_cell(TAKE, sh, sp) for sh, sp, _ in BD.IDLE]
idle_t = [d for _, _, d in BD.IDLE]
burst = FS.confetti_burst()
rain = FS.confetti_rain()
spots = FS.spot_sweep()
flash = FS.lift_flash()


def loop_pick(frames_t, t):
    """Index into a loop of per-frame durations at time t."""
    total = sum(frames_t)
    t = t % total
    for i, d in enumerate(frames_t):
        if t < d:
            return i
        t -= d
    return len(frames_t) - 1


def crowd_state(t):
    if T_WALK0 <= t < T_WALK1 + 0.3:
        return 3 + int(t / 0.15) % 2                    # cheer as he walks back in
    if t >= T_DROP:
        return 7 + int((t - T_DROP) / 0.10) % 4         # ROAR from the drop on
    return int(t / 0.35) % 3                            # calm, hushed for the announcer


def burak_state(t):
    """('walk', frame, body_y) or ('champ', name)."""
    if t < T_WALK1:
        u = max(0.0, (t - T_WALK0) / (T_WALK1 - T_WALK0))
        y = round(WALK_FROM_Y + (BODY[1] - WALK_FROM_Y) * u)
        return ('walk', int(max(0, t - T_WALK0) / 0.1667) % 5 if t >= T_WALK0 else 0, y)
    tt = T_WALK1
    for name, d in SEQ:
        if t < tt + d:
            return ('champ', name)
        tt += d
    if t < T_DROP:
        return ('champ', 'gather_a' if int((t - tt) / 0.10) % 2 == 0 else 'gather_b')
    if t < T_DROP + 0.10:
        return ('champ', 'lift')
    if t < T_DROP + 0.20:
        return ('champ', 'settle')
    k = int((t - T_DROP - 0.20) / 0.20) % 4
    return ('champ', ['hold_1', 'hold_2', 'hold_3', 'hold_4'][k])


def frame(t):
    img = bgs[crowd_state(t)].copy()
    since = t - T_DROP
    if since >= 0:                                       # house lights dip so the spots read
        a = int(90 * min(1.0, since / 0.3))
        img.alpha_composite(Image.new('RGBA', img.size, (8, 6, 20, a)))
    st = burak_state(t)
    if since >= 0:                                       # the impact rays go BEHIND him: the
        fk = int(since / 0.05)                           # lift pose stays readable on the drop
        if fk < len(flash):
            img.alpha_composite(flash[fk])
    if st[0] == 'walk':
        _, f, y = st
        img.alpha_composite(walk[f], (BODY[0], y))
        img.alpha_composite(idle[loop_pick(idle_t, t)], CELL_AT)
    else:
        img.alpha_composite(champ[st[1]], CELL_AT)
    if since >= 0:
        sk = int(since / 0.06)
        img.alpha_composite(spots[sk] if sk < 8 else spots[8 + int(since / 0.15) % 2])
        if since >= 1.0:
            img.alpha_composite(rain[int(since / 0.12) % 4])
        bk = int(since / 0.05)
        if bk < len(burst):
            img.alpha_composite(burst[bk])
    if T_FADE0 <= t:
        a = int(255 * min(1.0, (t - T_FADE0) / (T_FADE1 - T_FADE0)))
        img.alpha_composite(Image.new('RGBA', img.size, (0, 0, 0, a)))
    if t >= T_CRED0:
        cred = Image.open(os.path.join(OUT, 'credits', f'credits_still_{TAKE}.png')).convert('RGBA')
        a = min(1.0, (t - T_CRED0) / (T_CRED1 - T_CRED0))
        img = Image.blend(Image.new('RGBA', img.size, (0, 0, 0, 255)), cred, a)
    if t < T_FADE_IN:
        a = int(255 * (1 - t / T_FADE_IN))
        img.alpha_composite(Image.new('RGBA', img.size, (0, 0, 0, a)))
    return img, st


def caption(img, t, st, k):
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=11 * k)
    small = ImageFont.load_default(size=8 * k)
    if CAPTION[0] <= t < CAPTION[1]:
        d.rectangle((0, img.height - 26 * k, img.width, img.height), fill=(0, 0, 0))
        d.text((10 * k, img.height - 20 * k), CAPTION[2], fill=(255, 244, 163), font=font)
    label = f't {t:5.2f}s   ' + (st[1] if st[0] == 'champ' else 'walk-in')
    if t >= T_FADE0:
        label = f't {t:5.2f}s   ' + ('fade to black' if t < T_CRED0 else 'credits still (optional)')
    if abs(t - T_DROP) < 0.25:
        label += '   << BEAT DROP: LIFT >>'
    d.text((4 * k, 2 * k), label, fill=(255, 255, 255), font=small, stroke_width=k, stroke_fill=(0, 0, 0))


def gif(frames, path, durations):
    # one shared palette for every frame, no dithering: pixel art stays pixel art
    picks = [int(len(frames) * f) for f in (0.0, 0.2, 0.4, 0.45, 0.55, 0.65, 0.75, 0.82, 0.9, 0.99)]
    sample = Image.new('RGB', (frames[0].width, frames[0].height * len(picks)))
    for i, j in enumerate(picks):
        sample.paste(frames[j].convert('RGB'), (0, i * frames[0].height))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    full = os.path.join(OUT, path)
    q[0].save(full, save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=False,
              disposal=1)
    return full


def contact(times, path, box=(240, 60, 400, 210), k=3, cols=6):
    w, h = (box[2] - box[0]) * k, (box[3] - box[1]) * k
    rows = (len(times) + cols - 1) // cols
    sheet = Image.new('RGB', (w * cols, h * rows), (0, 0, 0))
    for i, t in enumerate(times):
        img, st = frame(t)
        c = img.crop(box).resize((w, h), Image.NEAREST)
        caption(c, t, st, 1)
        sheet.paste(c.convert('RGB'), ((i % cols) * w, (i // cols) * h))
    return save(sheet, path)


if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[2] == 'contact':
    ts = [1.0, 2.0, 2.85, 3.2, 3.55, 3.75, 4.0, 4.1, T_DROP, T_DROP + 0.05, T_DROP + 0.12,
          T_DROP + 0.25, T_DROP + 0.45, T_DROP + 0.65, T_DROP + 0.85, T_DROP + 1.6, T_DROP + 4.5, 12.0]
    print(contact(ts, f'work/contact_{TAKE}.png'))
    sys.exit(0)

if __name__ == '__main__':
    n = int(T_END * FPS)
    full, close = [], []
    for i in range(n):
        t = i * DT
        img, st = frame(t)
        big = img.resize((1280, 720), Image.NEAREST)
        caption(big, t, st, 2)
        full.append(big)
        if 2.4 <= t < 10.6:
            c = img.crop((240, 60, 400, 210)).resize((640, 600), Image.NEAREST)
            caption(c, t, st, 2)
            close.append(c)
    p1 = gif(full, f'mock/champion_mock_{TAKE}.gif', [int(DT * 1000)] * len(full))
    p2 = gif(close, f'mock/champion_closeup_{TAKE}.gif', [int(DT * 1000)] * len(close))
    # stills for a quick look: the drop frame and a hold frame
    for name, t in (('arrive', 3.0), ('gather', 5.0), ('drop', T_DROP + 0.01), ('hold', T_DROP + 1.5)):
        img, st = frame(t)
        save(img.resize((1280, 720), Image.NEAREST), f'mock/still_{TAKE}_{name}.png')
    print(p1, os.path.getsize(p1) // 1024, 'KB |', p2, os.path.getsize(p2) // 1024, 'KB')
