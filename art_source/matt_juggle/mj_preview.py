"""python mj_preview.py <sheet.png> <shadow.png> <out_dir>  - the juggle previews.

  matt_juggle_4x.png        the sheet at 4x, one strip, on a checker with the frame edges marked
  matt_juggle_4x_grid.png   the same twelve frames at 4x in a 4x3 grid, for reading
  matt_juggle_game.gif      the whole sequence at game scale (3x) over the arena mat, the player
                            beside him for scale: he is uppercut (player_uppercut.png, contact on
                            its frame 5), the hit plays, the tumble loops twice while he rises and
                            falls with his shadow on the mat under him, he crashes, and lies there
                            breathing
  matt_juggle_game_key.png  a strip of the GIF's key moments, for reading without a player

Reads the sheet it is given (so it previews exactly what was exported) and writes only into
out_dir. The arc is a preview's: one rise and fall, its apex 60 texels, long enough for two
loops. The game's finisher sets the real heights (PlayerFinisher, juggle_headroom).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mj_base as J  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = J.ROOT
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_uppercut.png')
RECOVER = os.path.join(J.ASSETS, 'matt_recover.png')
SCALE = 3

# the sheet's timing (seconds), as reported to the coder: the frame specs' own holds
import mj_poses as MP  # noqa: E402
HOLDS = [fn().hold for fn in MP.FRAMES]
LOOP = (2, 6)


def checker(w, h, a=62, b=50):
    im = Image.new('RGBA', (w, h))
    p = im.load()
    for y in range(h):
        for x in range(w):
            v = a if (x + y) % 2 == 0 else b
            p[x, y] = (v, v, v, 255)
    return im


def strip4(sheet, out):
    n = sheet.width // J.W
    bg = checker(sheet.width, sheet.height)
    bg.alpha_composite(sheet)
    big = bg.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for i in range(1, n):
        d.line([i * J.W * 4, 0, i * J.W * 4, big.height], fill=(170, 40, 170, 255))
    d.line([0, J.FEET[1] * 4 + 3, big.width, J.FEET[1] * 4 + 3], fill=(60, 220, 230, 255))
    big.save(os.path.join(out, 'matt_juggle_4x.png'))
    cols, rows = 4, (n + 3) // 4
    g = Image.new('RGBA', (cols * J.W * 4, rows * J.H * 4), (34, 34, 44, 255))
    for i in range(n):
        g.paste(big.crop((i * J.W * 4, 0, (i + 1) * J.W * 4, J.H * 4)),
                ((i % cols) * J.W * 4, (i // cols) * J.H * 4))
    g.save(os.path.join(out, 'matt_juggle_4x_grid.png'))
    return big.size, g.size


# ------------------------------------------------------------------------------ the scene
SW, SH = 330, 240                  # the scene, in texels
MAT_ORIGIN = (140, 40)             # which part of the mat texture shows
FEET = (196, 214)                  # Matt's feet point in the scene
PFEET = (148, 214)                 # the player's


def frames_of(sheet, fw, fh):
    return [sheet.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(sheet.width // fw)]


def timeline(shadow_n):
    """[(seconds, state)] where state names what to draw."""
    dt = 0.02
    ev = []
    t = 0.0
    # the punish pose while the player charges
    for k in range(10):
        ev.append((dt, {'matt': ('recover', (k // 4) % 4), 'player': (k // 4) % 3, 'lift': 0}))
    # the uppercut: player frames 3.. with their holds; contact at the start of frame 5
    pl = [(3, 0.05), (4, 0.06), (5, 0.06), (6, 0.06), (7, 0.14), (8, 0.10), (9, 0.16)]
    p_start = []
    acc = 0.0
    for f, h in pl:
        p_start.append((acc, f))
        acc += h
    p_end = acc
    contact = pl[0][1] + pl[1][1]

    def player_at(s):
        f = 0
        for (st, fr) in p_start:
            if s >= st:
                f = fr
        return f if s < p_end else 0

    # Matt's sheet frames, played by their holds: launch 0-1, the loop twice, then down on landing
    seq = [0, 1] + list(range(2, 7)) * 2
    air = sum(HOLDS[i] for i in seq)
    apex = 60.0
    g = 8 * apex / (air * air)
    v = g * air / 2
    s = 0.0
    while s < contact:
        ev.append((dt, {'matt': ('recover', 0), 'player': player_at(s), 'lift': 0}))
        s += dt
    # the airborne part
    tm = 0.0
    k = 0
    acc = HOLDS[seq[0]]
    while tm < air:
        while tm >= acc and k < len(seq) - 1:
            k += 1
            acc += HOLDS[seq[k]]
        lift = max(0.0, v * tm - 0.5 * g * tm * tm)
        ev.append((dt, {'matt': ('juggle', seq[k]), 'player': player_at(s), 'lift': lift,
                        'shadow': min(shadow_n - 1, int(lift * SCALE / 100.0))}))
        tm += dt
        s += dt
    # the crash and the lying loop
    for i in (7, 8, 9):
        ev.append((HOLDS[i], {'matt': ('juggle', i), 'player': player_at(s), 'lift': 0}))
        s += HOLDS[i]
    for rep in range(3):
        for i in (10, 11):
            ev.append((HOLDS[i], {'matt': ('juggle', i), 'player': 0, 'lift': 0}))
    return ev


def compose(state, juggle, recover, player, shadow, mat):
    sc = mat.copy()
    lift = int(round(state.get('lift', 0)))
    if 'shadow' in state and lift > 0:
        sh = shadow[state['shadow']]
        a = sh.getchannel('A').point(lambda v: int(v * 0.35))
        tint = Image.new('RGBA', sh.size, (0, 0, 0, 255))
        tint.putalpha(a)
        sc.alpha_composite(tint, (FEET[0] - sh.width // 2, FEET[1] - sh.height // 2 + 1))
    # the player (drawn in front of Matt, as the finisher draws him)
    kind, i = state['matt']
    if kind == 'recover':
        sc.alpha_composite(recover[i], (FEET[0] - 48, FEET[1] - 95))
    else:
        sc.alpha_composite(juggle[i], (FEET[0] - J.FEET[0], FEET[1] - J.FEET[1] - lift))
    pf = player[state['player']]
    sc.alpha_composite(pf, (PFEET[0] - 24, PFEET[1] - 60))
    return sc


def gif(sheet, shadow_im, out):
    juggle = frames_of(sheet, J.W, J.H)
    shadow = frames_of(shadow_im, shadow_im.width // 3, shadow_im.height)
    recover = frames_of(Image.open(RECOVER).convert('RGBA'), 96, 96)
    player = frames_of(Image.open(PLAYER).convert('RGBA'), 48, 64)
    mat = Image.open(MAT).convert('RGBA').crop((MAT_ORIGIN[0], MAT_ORIGIN[1],
                                               MAT_ORIGIN[0] + SW, MAT_ORIGIN[1] + SH))
    ev = timeline(len(shadow))
    frames, durs = [], []
    last = None
    for (d, st) in ev:
        key = (st['matt'], st['player'], int(round(st.get('lift', 0))), st.get('shadow'))
        if key == last:
            durs[-1] += d
            continue
        last = key
        frames.append(compose(st, juggle, recover, player, shadow, mat))
        durs.append(d)
    big = [f.resize((SW * SCALE, SH * SCALE), Image.NEAREST) for f in frames]
    # one palette for the whole GIF, from every frame at once, so no frame is pushed off its colours
    mont = Image.new('RGB', (SW, SH * len(frames)))
    for j, f in enumerate(frames):
        mont.paste(f.convert('RGB'), (0, SH * j))
    pal_src = mont.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [b.convert('RGB').quantize(palette=pal_src, dither=Image.Dither.NONE) for b in big]
    path = os.path.join(out, 'matt_juggle_game.gif')
    q[0].save(path, save_all=True, append_images=q[1:], duration=[int(round(d * 1000)) for d in durs],
              loop=0, disposal=1)
    # a key strip of the moments that matter
    picks = []
    seen = set()
    want = [('recover', 0), ('juggle', 0), ('juggle', 1), ('juggle', 2), ('juggle', 4), ('juggle', 6),
            ('juggle', 7), ('juggle', 8), ('juggle', 10)]
    last = None
    for (d, st) in ev:
        key = (st['matt'], st['player'], int(round(st.get('lift', 0))), st.get('shadow'))
        if key == last:
            continue
        last = key
        if st['matt'] in want and st['matt'] not in seen:
            seen.add(st['matt'])
            picks.append(compose(st, juggle, recover, player, shadow, mat))
    kw = SW * 2
    strip = Image.new('RGBA', (kw * len(picks), SH * 2), (0, 0, 0, 255))
    for i, p in enumerate(picks):
        strip.paste(p.resize((SW * 2, SH * 2), Image.NEAREST), (i * kw, 0))
    strip.save(os.path.join(out, 'matt_juggle_game_key.png'))
    return path, len(frames), sum(durs)


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    sheet = Image.open(argv[0]).convert('RGBA')
    shadow = Image.open(argv[1]).convert('RGBA')
    out = argv[2]
    os.makedirs(out, exist_ok=True)
    s1, s2 = strip4(sheet, out)
    print('4x strip %s, grid %s' % (s1, s2))
    p, n, T = gif(sheet, shadow, out)
    print('gif %s: %d frames, %.2f s' % (p, n, T))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
