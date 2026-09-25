"""python jj_preview.py <sheet.png> <shadow.png> <out_dir> [--before <old_sheet.png>]  - the previews.

  jordan_juggle_4x.png        the sheet at 4x, one strip, on a checker with the frame edges marked
  jordan_juggle_4x_grid.png   the same twelve frames at 4x in a 4x3 grid, for reading
  jordan_juggle_before_after_4x.png
                              with --before: each frame of the old sheet over the same frame of the
                              new one at 4x, both cropped to the same window, six pairs a row
                              (--frames 0,1,9 picks the frames; --labels 'old|new' names the rows)
  jordan_juggle_game_strip.png
                              the twelve frames at game scale (3x) on the arena mat, feet on the mat
                              line, as the game draws him, two rows of six
  jordan_juggle_game.gif    the whole sequence at game scale (3x) over the arena mat, the player
                            beside him for scale: he stands in his approved v2 idle and is
                            uppercut (player_uppercut.png, contact on its frame 5), the hit plays,
                            the tumble loops twice while he rises and falls with his shadow on the
                            mat under him, he crashes, and lies there breathing
  jordan_juggle_game_key.png  a strip of the GIF's key moments, for reading without a player

Reads the sheet it is given (so it previews exactly what was exported) and writes only into
out_dir. The arc is a preview's: one rise and fall, its apex 60 texels, long enough for two
loops. The game's finisher sets the real heights (PlayerFinisher, juggle_headroom).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jj_base as J  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = J.ROOT
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_uppercut.png')
# the lead-in: his approved v2 idle (frame 0 of jordan_redesign_v2.png); his body sheets are being
# redrawn in v2 and are not approved yet
RECOVER = J.APPROVED_V2
SCALE = 3

# the sheet's timing (seconds), as reported to the coder: the frame specs' own holds
import jj_poses as MP  # noqa: E402
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
    big.save(os.path.join(out, 'jordan_juggle_4x.png'))
    cols, rows = 4, (n + 3) // 4
    g = Image.new('RGBA', (cols * J.W * 4, rows * J.H * 4), (34, 34, 44, 255))
    for i in range(n):
        g.paste(big.crop((i * J.W * 4, 0, (i + 1) * J.W * 4, J.H * 4)),
                ((i % cols) * J.W * 4, (i // cols) * J.H * 4))
    g.save(os.path.join(out, 'jordan_juggle_4x_grid.png'))
    return big.size, g.size


# ------------------------------------------------------------------------------ the scene
SW, SH = 330, 240                  # the scene, in texels
MAT_ORIGIN = (140, 40)             # which part of the mat texture shows
FEET = (150, 214)                  # his feet point in the scene
# The player stands on the side he faces (his sheets face right, and the game turns him to face
# the player), mirrored to face him: the fist comes from the right and he goes over backwards,
# away from it, landing head-left.
PFEET = (208, 214)
PLAYER_FLIP = True


def frames_of(sheet, fw, fh):
    return [sheet.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(sheet.width // fw)]


def timeline(shadow_n):
    """[(seconds, state)] where state names what to draw."""
    dt = 0.02
    ev = []
    t = 0.0
    # the punish pose while the player charges
    for k in range(10):
        ev.append((dt, {'boss': ('recover', (k // 4) % 4), 'player': (k // 4) % 3, 'lift': 0}))
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

    # his sheet frames, played by their holds: launch 0-1, the loop twice, then down on landing
    seq = [0, 1] + list(range(2, 7)) * 2
    air = sum(HOLDS[i] for i in seq)
    apex = 60.0
    g = 8 * apex / (air * air)
    v = g * air / 2
    s = 0.0
    while s < contact:
        ev.append((dt, {'boss': ('recover', 0), 'player': player_at(s), 'lift': 0}))
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
        ev.append((dt, {'boss': ('juggle', seq[k]), 'player': player_at(s), 'lift': lift,
                        'shadow': min(shadow_n - 1, int(lift * SCALE / 100.0))}))
        tm += dt
        s += dt
    # the crash and the lying loop
    for i in (7, 8, 9):
        ev.append((HOLDS[i], {'boss': ('juggle', i), 'player': player_at(s), 'lift': 0}))
        s += HOLDS[i]
    for rep in range(3):
        for i in (10, 11):
            ev.append((HOLDS[i], {'boss': ('juggle', i), 'player': 0, 'lift': 0}))
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
    # the player (drawn in front of him, as the finisher draws him)
    kind, i = state['boss']
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
    recover = frames_of(Image.open(RECOVER).convert('RGBA'), 96, 96)[:1] * 4
    player = frames_of(Image.open(PLAYER).convert('RGBA'), 48, 64)
    if PLAYER_FLIP:
        player = [p.transpose(Image.FLIP_LEFT_RIGHT) for p in player]
    mat = Image.open(MAT).convert('RGBA').crop((MAT_ORIGIN[0], MAT_ORIGIN[1],
                                               MAT_ORIGIN[0] + SW, MAT_ORIGIN[1] + SH))
    ev = timeline(len(shadow))
    frames, durs = [], []
    last = None
    for (d, st) in ev:
        key = (st['boss'], st['player'], int(round(st.get('lift', 0))), st.get('shadow'))
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
    path = os.path.join(out, 'jordan_juggle_game.gif')
    q[0].save(path, save_all=True, append_images=q[1:], duration=[int(round(d * 1000)) for d in durs],
              loop=0, disposal=1)
    # a key strip of the moments that matter
    picks = []
    seen = set()
    want = [('recover', 0), ('juggle', 0), ('juggle', 1), ('juggle', 2), ('juggle', 4), ('juggle', 6),
            ('juggle', 7), ('juggle', 8), ('juggle', 10)]
    last = None
    for (d, st) in ev:
        key = (st['boss'], st['player'], int(round(st.get('lift', 0))), st.get('shadow'))
        if key == last:
            continue
        last = key
        if st['boss'] in want and st['boss'] not in seen:
            seen.add(st['boss'])
            picks.append(compose(st, juggle, recover, player, shadow, mat))
    kw = SW * 2
    strip = Image.new('RGBA', (kw * len(picks), SH * 2), (0, 0, 0, 255))
    for i, p in enumerate(picks):
        strip.paste(p.resize((SW * 2, SH * 2), Image.NEAREST), (i * kw, 0))
    strip.save(os.path.join(out, 'jordan_juggle_game_key.png'))
    return path, len(frames), sum(durs)


def _union_box(frames, pad=3):
    boxes = [f.getbbox() for f in frames if f.getbbox()]
    return (max(0, min(b[0] for b in boxes) - pad), max(0, min(b[1] for b in boxes) - pad),
            min(J.W, max(b[2] for b in boxes) + pad), min(J.H, max(b[3] for b in boxes) + pad))


def before_after(old, sheet, out, s=4, per_row=6, frames=None, labels=('before (v1)', 'after (v2)')):
    """Each frame of the old sheet above the same frame of the new one at s x, both cropped to the
    same window (the union of the two), labelled."""
    a, b = frames_of(old, J.W, J.H), frames_of(sheet, J.W, J.H)
    cells = []
    for i, (fa, fb) in enumerate(zip(a, b)):
        if frames is not None and i not in frames:
            continue
        box = _union_box([fa, fb])
        w, h = box[2] - box[0], box[3] - box[1]
        cell = Image.new('RGBA', (w * s, (h * s) * 2 + 36), (34, 34, 44, 255))
        for j, f in enumerate((fa, fb)):
            bg = checker(w, h)
            bg.alpha_composite(f.crop(box))
            cell.paste(bg.resize((w * s, h * s), Image.NEAREST), (0, 18 + j * (h * s + 18)))
        d = ImageDraw.Draw(cell)
        d.text((4, 3), '%d  %s' % (i, labels[0]), fill=(220, 220, 228, 255))
        d.text((4, 21 + h * s), '%d  %s' % (i, labels[1]), fill=(255, 235, 140, 255))
        cells.append(cell)
    rows = [cells[k:k + per_row] for k in range(0, len(cells), per_row)]
    W_ = max(sum(c.width for c in r) + 8 * (len(r) - 1) for r in rows)
    H_ = sum(max(c.height for c in r) for r in rows) + 8 * (len(rows) - 1)
    im = Image.new('RGBA', (W_, H_), (170, 40, 170, 255))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            im.paste(c, (x, y))
            x += c.width + 8
        y += max(c.height for c in r) + 8
    p = os.path.join(out, 'jordan_juggle_before_after_4x.png')
    im.save(p)
    return p, im.size


def game_strip(sheet, out, per_row=6):
    """The twelve frames at game scale (SCALE) on the arena mat, his feet point on the mat line, as
    the game draws the ground frames; a common window round all of them."""
    fr = frames_of(sheet, J.W, J.H)
    box = _union_box(fr, pad=4)
    w, h = box[2] - box[0], box[3] - box[1]
    mat = Image.open(MAT).convert('RGBA')
    cells = []
    for i, f in enumerate(fr):
        bg = mat.crop((MAT_ORIGIN[0] + FEET[0] - J.FEET[0] + box[0], MAT_ORIGIN[1] + FEET[1] - J.FEET[1] + box[1],
                       MAT_ORIGIN[0] + FEET[0] - J.FEET[0] + box[2], MAT_ORIGIN[1] + FEET[1] - J.FEET[1] + box[3]))
        bg.alpha_composite(f.crop(box))
        big = bg.resize((w * SCALE, h * SCALE), Image.NEAREST)
        ImageDraw.Draw(big).text((4, 3), str(i), fill=(255, 255, 255, 255))
        cells.append(big)
    rows = (len(cells) + per_row - 1) // per_row
    im = Image.new('RGBA', (per_row * (w * SCALE + 6) - 6, rows * (h * SCALE + 6) - 6), (10, 10, 12, 255))
    for i, c in enumerate(cells):
        im.paste(c, ((i % per_row) * (w * SCALE + 6), (i // per_row) * (h * SCALE + 6)))
    p = os.path.join(out, 'jordan_juggle_game_strip.png')
    im.save(p)
    return p, im.size


def main(argv):
    old = None
    picks = None
    labels = ('before (v1)', 'after (v2)')
    if '--before' in argv:
        k = argv.index('--before')
        old = Image.open(argv[k + 1]).convert('RGBA')
        argv = argv[:k] + argv[k + 2:]
    if '--frames' in argv:
        k = argv.index('--frames')
        picks = [int(v) for v in argv[k + 1].split(',')]
        argv = argv[:k] + argv[k + 2:]
    if '--labels' in argv:
        k = argv.index('--labels')
        labels = tuple(argv[k + 1].split('|'))[:2]
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 3:
        print(__doc__)
        return 2
    sheet = Image.open(argv[0]).convert('RGBA')
    shadow = Image.open(argv[1]).convert('RGBA')
    out = argv[2]
    os.makedirs(out, exist_ok=True)
    s1, s2 = strip4(sheet, out)
    print('4x strip %s, grid %s' % (s1, s2))
    if old is not None:
        print('before/after %s %s' % before_after(old, sheet, out, frames=picks, labels=labels))
    print('game-scale strip %s %s' % game_strip(sheet, out))
    p, n, T = gif(sheet, shadow, out)
    print('gif %s: %d frames, %.2f s' % (p, n, T))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
