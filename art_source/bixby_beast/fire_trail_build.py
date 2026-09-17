"""Build the fire-trail sheets + previews.
  python fire_trail_build.py build      -> ../final_trail/bixby_fire_trail.png (+ layer strips), bixby_fire_scorch.png, lint
  python fire_trail_build.py previews   -> GIFs, 6x close-up, 1920x1080 arena mockup (env BIXBY_TRAIL_PREVIEWS, BIXBY_ARENA_PNG)"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pal import PALC
from pngio import read_png, write_png, crop, scale, blank
import fire_trail as FT
import fx2 as FX

OUT = os.path.join(HERE, '..', 'final_trail')
PREVIEWS = os.environ.get('BIXBY_TRAIL_PREVIEWS', os.path.join(HERE, '..', 'bixby_fire_trail_previews'))
ARENA = os.environ.get('BIXBY_ARENA_PNG', os.path.join(HERE, '..', 'arena_render', 'arena00000002.png'))
ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
FLOOR = (136, 180, 99, 255)
ALLOWED = set(FX.FX_PAL.values())


def lint(path):
    w, h, px = read_png(path)
    alphas, off = set(), 0
    for row in px:
        for p in row:
            p = tuple(p)
            alphas.add(p[3])
            if p[3] and p not in ALLOWED:
                off += 1
    ok = alphas <= {0, 255} and off == 0
    print('  lint %-26s %dx%d alphas=%s off-palette=%d %s' % (os.path.basename(path), w, h, sorted(alphas), off, 'OK' if ok else 'FAIL'))
    return ok


def margins(frames, m=1):
    bad = 0
    for i, cv in enumerate(frames):
        for y in range(cv.h):
            for x in range(cv.w):
                if cv.px[y][x] is not None and (x < m or x > cv.w - 1 - m or y < m or y > cv.h - 1 - m):
                    bad += 1
    return bad


def build():
    os.makedirs(OUT, exist_ok=True)
    fr = FT.all_frames()
    n = len(fr)
    comp, fire_l, smoke_l = Canvas(FT.FW * n, FT.FH), Canvas(FT.FW * n, FT.FH), Canvas(FT.FW * n, FT.FH)
    for i, (fire, smoke) in enumerate(fr):
        fire_l.blit(fire, FT.FW * i, 0)
        smoke_l.blit(smoke, FT.FW * i, 0)
        comp.blit(fire, FT.FW * i, 0)
        comp.blit(smoke, FT.FW * i, 0)
    comp.save(os.path.join(OUT, 'bixby_fire_trail.png'))
    fire_l.save(os.path.join(OUT, 'layer_trail_fire.png'))
    smoke_l.save(os.path.join(OUT, 'layer_trail_smoke.png'))
    sc = Canvas(FT.FW * 2, FT.FH)
    for k in range(2):
        sc.blit(FT.scorch(k), FT.FW * k, 0)
    sc.save(os.path.join(OUT, 'bixby_fire_scorch.png'))
    ok = lint(os.path.join(OUT, 'bixby_fire_trail.png')) & lint(os.path.join(OUT, 'bixby_fire_scorch.png'))
    mb = margins([c for f in fr for c in f] + [FT.scorch(0), FT.scorch(1)])
    print('  margin (1px) violations:', mb)
    print('BUILD', 'OK' if ok and mb == 0 else 'FAIL')


# ------------------------------------------------------------------ previews
def sheet(path, fw, fh):
    w, h, px = read_png(path)
    px = [[tuple(p) for p in row] for row in px]
    return [crop(px, fw * i, 0, fw, fh) for i in range(w // fw)]


def flip_h(fr):
    return [list(reversed(r)) for r in fr]


def blit(dst, src, x0, y0, s=1):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if not p[3]:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if 0 <= yy < H:
                    r = dst[yy]
                    for dx in range(s):
                        xx = x0 + x * s + dx
                        if 0 <= xx < W:
                            r[xx] = p


def shade(dst, src, x0, y0, s=1, alpha=0.38):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if not p[3]:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if 0 <= yy < H:
                    r = dst[yy]
                    for dx in range(s):
                        xx = x0 + x * s + dx
                        if 0 <= xx < W:
                            q = r[xx]
                            r[xx] = (int(round(q[0] * (1 - alpha))), int(round(q[1] * (1 - alpha))), int(round(q[2] * (1 - alpha))), 255)


IGNITE, BURN, OUT_ = [0, 1, 2], [3, 4, 5, 6], [7, 8, 9]


def previews():
    from gifio2 import write_gif
    os.makedirs(PREVIEWS, exist_ok=True)
    T = sheet(os.path.join(OUT, 'bixby_fire_trail.png'), 40, 40)
    S = sheet(os.path.join(OUT, 'bixby_fire_scorch.png'), 40, 40)

    def single(frames, delays, name, s=4):
        outs = []
        for f in frames:
            cv = blank(48, 44, FLOOR)
            blit(cv, f, 4, 2)
            outs.append(cv)
        write_gif(os.path.join(PREVIEWS, name), outs, delays, scale=s)
        print('gif', name)
    single([T[i] for i in IGNITE] + [T[3]], [7, 7, 9, 40], 'fire_trail_ignite_4x.gif')
    single([T[i] for i in BURN], [11, 11, 11, 11], 'fire_trail_burn_loop_4x.gif')
    single([T[6]] + [T[i] for i in OUT_] + [S[0], S[1]], [30, 12, 14, 18, 40, 60], 'fire_trail_burnout_4x.gif')
    # a row of 8 patches, 32 texels apart, alternate flips, staggered loop phases (how the coder should place them)
    outs = []
    for t in range(4):
        cv = blank(32 * 7 + 48, 48, FLOOR)
        for i in range(8):
            f = T[3 + (t + i * 3) % 4]
            blit(cv, flip_h(f) if i % 2 else f, 4 + 32 * i, 4)
        outs.append(cv)
    write_gif(os.path.join(PREVIEWS, 'fire_trail_row_of_8_3x.gif'), outs, [11] * 4, scale=3)
    print('gif fire_trail_row_of_8_3x.gif')
    # 6x close-up: igniting patch, two burning patches (one flipped), a patch burning out, then a scorch mark
    cv = blank(32 * 4 + 48, 52, FLOOR)
    states = [(S[0], False), (T[7], True), (T[5], False), (T[4], True), (T[2], False)]
    for i, (f, fl) in enumerate(states):
        blit(cv, flip_h(f) if fl else f, 4 + 32 * i, 8)
    write_png(os.path.join(PREVIEWS, 'fire_trail_closeup_6x.png'), cv[0].__len__() * 6, len(cv) * 6, scale(cv, 6))
    print('closeup fire_trail_closeup_6x.png')
    mockup(T, S)


def mockup(T, S):
    w, h, px = read_png(ARENA)
    px = [[tuple(p) for p in row] for row in px]
    for y in range(870, 932):
        for x in range(940, 982):
            px[y][x] = FLOOR
    B = 3
    fire = sheet(ASSETS + 'Bixby/bixby_beast_firebreath.png', 192, 256)
    hshadow = sheet(ASSETS + 'Bixby/bixby_beast_shadow.png', 192, 48)
    player = crop([[tuple(p) for p in r] for r in read_png(ASSETS + 'MainPlayer/player_4dir_sheet.png')[2]], 0, 32, 32, 32)
    ax, ay = 1350, 548                     # beast hover anchor on screen
    gx, gy = ax, ay + 40 * B               # ground point under it
    trail_y = 830                          # the breath meets the floor here (fire frame row ~245)
    # hover shadow
    shade(px, hshadow[1], gx - 96 * B, gy - 25 * B, B)
    # trail: newest patch under the stream, oldest far left; one gap (slot 5) left open
    slots = [(0, 1), (1, 2), (2, 4), (3, 6), (4, 3), (5, None), (6, 5), (7, 8)]
    for i, fi in slots:
        if fi is None:
            continue
        cx = ax - i * 32 * B
        f = T[fi]
        if i % 2:
            f = flip_h(f)
        blit(px, f, cx - 20 * B, trail_y - 31 * B, B)
    # the breath itself (approved sheet, full stream frame) drawn over the newest patch
    blit(px, fire[2], ax - 96 * B, ay - 151 * B, B)
    # player on the far side of the fire, facing up toward the gap
    blit(px, player, ax - 5 * 32 * B - 16 * 2, trail_y + 96 - 16 * 2, 2)
    out = os.path.join(PREVIEWS, 'mockup_arena_fire_trail_1920x1080.png')
    write_png(out, 1920, 1080, px)
    print('mockup', out)


if __name__ == '__main__':
    what = sys.argv[1:] or ['build', 'previews']
    if 'build' in what:
        build()
    if 'previews' in what:
        previews()
