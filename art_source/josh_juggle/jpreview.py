"""The juggle at game scale, as a GIF: the player's uppercut, the hit, the tumble looping while he
rises and falls, the crash and the lying loop, over the arena mat, with the player for scale and
the boss's shadow on the mat while he is up. Everything is drawn at the game's 3x; one GIF pixel is
one screen pixel. Used by Josh's and Danny's juggle rigs; writes only where it is told to.

The flight is one arc from the contact to the crash, as long as the hit plus `loops` tumble loops.
The fight's own gravity (PlayerFinisher.juggle_gravity 2900) would throw him about 400 px high to
stay up that long, so the preview's arc is scaled to `apex` instead; the finisher also scales his
real lift to fit the arena (juggle_headroom). The camera is held still (the fight zooms in).
"""
import os

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
S = 3
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER_4DIR = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
PLAYER_UPPERCUT = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_uppercut.png')
# FinisherArtLayout.FINAL_PLAYER: the uppercut steps and seconds; the contact is step 2.
UPPERCUT = [(3, 0.05), (4, 0.06), (5, 0.06), (6, 0.06), (7, 0.14), (8, 0.10), (9, 0.16)]
CONTACT_STEP = 2
LEFT_ROW = 2               # player_4dir_sheet rows: DOWN, UP, LEFT, RIGHT


def _frames(path, fw, fh, n=None):
    im = Image.open(path).convert('RGBA')
    n = n or im.width // fw
    return [im.crop((i * fw, 0, i * fw + fw, fh)) for i in range(n)]


def _big(im):
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


def render(out, sheet, fw, fh, feet, times, idle, idle_feet, shadow, canvas=(660, 700), boss_x=250,
           ground_y=640, player_x=470, apex=240, loops=2, lying_loops=3, step=0.04, lead=0.35):
    """sheet: the juggle strip (PIL image); times: seconds per frame (12); idle: the boss standing
    before the hit (PIL image) and idle_feet its feet texel; shadow: dict(image, hframes, pivot,
    alpha, step) or None."""
    frames = [sheet.crop((i * fw, 0, i * fw + fw, fh)) for i in range(sheet.width // fw)]
    big = [_big(f) for f in frames]
    idle_big = _big(idle)
    mat = _big(Image.open(MAT).convert('RGBA'))
    W, H = canvas
    # a patch of the mat behind the ring's middle, the size of the canvas
    mx = max(0, mat.width // 2 - W // 2)
    my = max(0, mat.height - H)
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    bg.alpha_composite(mat.crop((mx, my, mx + W, my + H)))
    p_idle = _big(_frames(PLAYER_4DIR, 32, 32, 40)[0])
    p4 = Image.open(PLAYER_4DIR).convert('RGBA')
    p_left = _big(p4.crop((0, LEFT_ROW * 32, 32, LEFT_ROW * 32 + 32)))
    upper = [_big(f.transpose(Image.FLIP_LEFT_RIGHT)) for f in _frames(PLAYER_UPPERCUT, 48, 64)]
    sh_frames = None
    if shadow:
        sw = shadow['image'].width // shadow['hframes']
        sh_frames = [_big(shadow['image'].crop((i * sw, 0, i * sw + sw, shadow['image'].height)))
                     for i in range(shadow['hframes'])]

    # ---- the timeline: (start, boss frame or 'idle', lift, player image)
    t_contact = lead + sum(d for _, d in UPPERCUT[:CONTACT_STEP])
    loop = sum(times[2:7])
    flight = times[0] + times[1] + loops * loop
    g = 8.0 * apex / (flight * flight)
    v = g * flight / 2.0

    def boss_at(t):
        if t < t_contact:
            return 'idle', 0.0
        u = t - t_contact
        if u < flight:
            lift = max(0.0, v * u - 0.5 * g * u * u)
            if u < times[0]:
                return 0, lift
            if u < times[0] + times[1]:
                return 1, lift
            w = (u - times[0] - times[1]) % loop
            acc = 0.0
            for i in range(2, 7):
                acc += times[i]
                if w < acc:
                    return i, lift
            return 6, lift
        u -= flight
        for i in (7, 8, 9):
            if u < times[i]:
                return i, 0.0
            u -= times[i]
        w = u % (times[10] + times[11])
        return (10 if w < times[10] else 11), 0.0

    def player_at(t):
        if t < lead:
            return p_left
        u = t - lead
        for f, d in UPPERCUT:
            if u < d:
                return upper[f]
            u -= d
        return p_left

    end = t_contact + flight + times[7] + times[8] + times[9] + lying_loops * (times[10] + times[11])
    # sample every `step`, and every frame boundary exactly
    cuts = set()
    t = 0.0
    while t < end:
        cuts.add(round(t, 4))
        t += step
    acc = t_contact
    cuts.add(round(acc, 4))
    for i in (0, 1):
        acc += times[i]
        cuts.add(round(acc, 4))
    cuts.add(round(end, 4))
    cuts = sorted(c for c in cuts if c <= end)

    out_frames, durs = [], []
    last_key = None
    for a, b in zip(cuts, cuts[1:]):
        bf, lift = boss_at(a + 1e-6)
        pim = player_at(a + 1e-6)
        key = (bf, int(round(lift)), id(pim))
        if key == last_key:
            durs[-1] += b - a
            continue
        last_key = key
        im = bg.copy()
        if sh_frames and bf != 'idle' and lift > 0.5:
            k = min(len(sh_frames) - 1, int(lift / shadow['step']))
            s = sh_frames[k].copy()
            alpha = s.getchannel('A').point(lambda x: int(x * shadow['alpha']))
            s.putalpha(alpha)
            px_, py_ = shadow['pivot']
            im.alpha_composite(s, (int(boss_x - (px_ + 0.5) * S), int(ground_y - (py_ + 0.5) * S)))
        if bf == 'idle':
            im.alpha_composite(idle_big, (int(boss_x - (idle_feet[0] + 0.5) * S),
                                          int(ground_y - (idle_feet[1] + 1) * S)))
        else:
            im.alpha_composite(big[bf], (int(boss_x - (feet[0] + 0.5) * S),
                                         int(ground_y - (feet[1] + 1) * S - round(lift))))
        # the player: the 4-direction frame's bottom-centre on his feet; the uppercut's 48x64 frames
        # line their bottom 32x32 up with it
        im.alpha_composite(pim, (int(player_x - pim.width / 2), int(ground_y - pim.height)))
        out_frames.append(im.convert('RGB'))
        durs.append(b - a)
    durs[-1] += 0.6                      # a beat on the last lying frame before it loops
    pal = out_frames[len(out_frames) // 2].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in out_frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=[max(20, int(round(d * 1000))) for d in durs],
              loop=0, disposal=1, optimize=True)
    return len(q), sum(durs), g
