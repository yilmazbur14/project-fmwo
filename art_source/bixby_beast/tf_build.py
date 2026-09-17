"""Build the transformation sheets and previews.
  python tf_build.py build     -> ../final_tf/bixby_transform.png (13x2 grid of 320x256) + layer sheets,
                                  bixby_transform_aura.png, bixby_transform_shockwave.png, lint + margin checks
  python tf_build.py previews  -> full-sequence GIF over the arena, contact sheets, 1920x1080 stills
                                  (env BIXBY_TF_PREVIEWS, BIXBY_ARENA_PNG)"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pal import PALC
from pngio import read_png, write_png, crop, scale, blank
import bixby_transform as BT
import tf_stages as ST
import tf_fx as TFX
import fx2 as FX
import small_art as SA
import faces2 as F2

OUT = os.path.join(HERE, '..', 'final_tf')
PREVIEWS = os.environ.get('BIXBY_TF_PREVIEWS', os.path.join(HERE, '..', 'bixby_transform_previews'))
ARENA = os.environ.get('BIXBY_ARENA_PNG', os.path.join(HERE, '..', 'arena_render', 'arena00000002.png'))
ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
FLOOR = (136, 180, 99, 255)
COLS, ROWS = 13, 2
TW, TH = ST.TW, ST.TH
ALLOWED = set(PALC.values()) | set(FX.FX_PAL.values()) | set(SA.BPAL.values()) | set(SA.LPAL.values()) | set(F2.EXTRA.values())

# ------------------------------------------------------------------ optional overlays
AURA_FRAMES = 4
SHOCK_FRAMES = 5
SHOCK_W, SHOCK_H = 320, 96          # centre (160, 48) sits on the feet anchor


def aura_frame(t):
    cv = ST.blank()
    TFX.embers_rising(cv, (ST.AX - 60, ST.AY - 150, ST.AX + 60, ST.AY - 6), t=t, n=30, seed=7,
                      speed=(150 - 6) / AURA_FRAMES, sizes=(1, 1, 2))
    TFX.ember_swirl(cv, ST.AX, ST.AY - 16, t=t * 1.6, n=16, rx=58, ry=32, seed=11)
    for k in range(3):                                   # low flame licks around his feet
        x = ST.AX - 34 + k * 34
        h = 7 + 3 * math.sin(t * 1.6 + k)
        for j in range(int(h)):
            u = j / max(1.0, h)
            cv.put(int(x + math.sin(t + k + u * 2) * 2), int(ST.AY - 6 - j), PALC['O' if u < 0.4 else ('o' if u < 0.75 else 'F')])
    return cv


def shock_frame(k):
    lib.set_size(SHOCK_W, SHOCK_H)
    cv = Canvas(SHOCK_W, SHOCK_H)
    r = [18, 48, 84, 120, 150][k]
    ry = min(44.0, r * 0.30)
    thick = [5, 4, 3, 2, 2][k]
    cols = [('W', 'L', 'O'), ('W', 'O', 'o'), ('L', 'O', 'o'), ('O', 'o', 'F'), ('o', 'F', 'r')][k]
    TFX.ring(cv, SHOCK_W // 2, 48, r, ry, thick=thick, colours=cols)
    if k >= 2:                                           # dust kicked up at the leading edge
        for s in (-1, 1):
            for j in range(3):
                x = SHOCK_W // 2 + s * (r - 4 - j * 9)
                FX.puff(cv, x, 48 - ry * 0.25 - j * 2, 4.0 - j * 0.8, seed=31 + k * 7 + j, kind='dust')
    return cv


# ------------------------------------------------------------------ build
def lint(path):
    w, h, px = read_png(path)
    alphas, off = set(), {}
    for row in px:
        for p in row:
            p = tuple(p)
            alphas.add(p[3])
            if p[3] and p not in ALLOWED:
                off[p] = off.get(p, 0) + 1
    ok = alphas <= {0, 255} and not off
    print('  lint %-34s %dx%d alphas=%s off-palette=%s %s' % (os.path.basename(path), w, h, sorted(alphas),
                                                             len(off), 'OK' if ok else 'FAIL ' + str(list(off)[:3])))
    return ok


def grid_sheet(frames, layer=None):
    sheet = Canvas(TW * COLS, TH * ROWS)
    for i, fr in enumerate(frames):
        cv = fr[layer] if layer else BT.flatten(fr)
        sheet.blit(cv, TW * (i % COLS), TH * (i // COLS))
    return sheet


def build():
    os.makedirs(OUT, exist_ok=True)
    frames = BT.frames()
    assert len(frames) == COLS * ROWS, len(frames)
    grid_sheet(frames).save(os.path.join(OUT, 'bixby_transform.png'))
    for L in BT.LAYERS:
        grid_sheet(frames, L).save(os.path.join(OUT, 'layer_transform_%s.png' % L))
    aura = Canvas(TW * AURA_FRAMES, TH)
    for t in range(AURA_FRAMES):
        aura.blit(aura_frame(t), TW * t, 0)
    aura.save(os.path.join(OUT, 'bixby_transform_aura.png'))
    shock = Canvas(SHOCK_W * SHOCK_FRAMES, SHOCK_H)
    for k in range(SHOCK_FRAMES):
        shock.blit(shock_frame(k), SHOCK_W * k, 0)
    shock.save(os.path.join(OUT, 'bixby_transform_shockwave.png'))
    ok = True
    for n in ('bixby_transform.png', 'bixby_transform_aura.png', 'bixby_transform_shockwave.png'):
        ok &= lint(os.path.join(OUT, n))
    bad = 0
    for i, fr in enumerate(frames):
        cv = BT.flatten(fr)
        bad += sum(1 for y in range(cv.h) for x in range(cv.w)
                   if cv.px[y][x] is not None and (x < 1 or x > cv.w - 2 or y < 1 or y > cv.h - 2))
    print('  frame-edge pixels:', bad)
    print('BUILD', 'OK' if ok else 'FAIL')
    return frames


# ------------------------------------------------------------------ previews
def sheet_frames(path, fw, fh, cols=None):
    w, h, px = read_png(path)
    px = [[tuple(p) for p in row] for row in px]
    cols = cols or (w // fw)
    out = []
    for r in range(h // fh):
        for c in range(cols):
            out.append(crop(px, fw * c, fh * r, fw, fh))
    return out


def blit(dst, src, x0, y0, s=1):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if not p[3]:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if 0 <= yy < H:
                    rr = dst[yy]
                    for dx in range(s):
                        xx = x0 + x * s + dx
                        if 0 <= xx < W:
                            rr[xx] = p


def arena_base():
    w, h, px = read_png(ARENA)
    px = [[tuple(p) for p in row] for row in px]
    for y in range(870, 932):
        for x in range(940, 982):
            px[y][x] = FLOOR
    return px


def stage_still(frame_px, throne, s=3, gx=960, gy=760):
    """the transformation on the arena floor with Liam's empty throne behind him"""
    px = arena_base()
    blit(px, throne, gx - 200 * s, gy - 150 * s, s)          # throne bottom sits above/behind the anchor
    blit(px, frame_px, gx - 160 * s, gy - 251 * s, s)
    return px


def previews():
    from gifio2 import write_gif
    os.makedirs(PREVIEWS, exist_ok=True)
    F = sheet_frames(os.path.join(OUT, 'bixby_transform.png'), TW, TH, COLS)
    thr = read_png(ASSETS + 'Liam/Entrance/liam_throne.png')
    throne = [[tuple(p) for p in row] for row in thr[2]]
    # ---- GIF over the arena (2x of a 480x300 window around him)
    wx, wy, ww, wh = 960 - 460, 104, 920, 800        # the whole sprite at 3x game scale, plus floor and throne
    def gif_frame(i):
        px = stage_still(F[i], throne, s=3)
        return [row[wx:wx + ww] for row in px[wy:wy + wh]]
    delays = [max(2, int(round(BT.MS[i] / 10))) for i in range(len(F))]
    write_gif(os.path.join(PREVIEWS, 'bixby_transform_full_3x.gif'), gif_frame, delays, scale=1)
    print('gif bixby_transform_full_3x.gif', sum(BT.MS), 'ms total')
    # ---- contact sheets
    for s, name, cols in ((1, 'bixby_transform_contact_1x.png', 7), (3, 'bixby_transform_contact_3x.png', 4)):
        rows = (len(F) + cols - 1) // cols
        W, H = cols * TW * s, rows * TH * s
        img = [[FLOOR] * W for _ in range(H)]
        for i, f in enumerate(F):
            blit(img, f, (i % cols) * TW * s, (i // cols) * TH * s, s)
        write_png(os.path.join(PREVIEWS, name), W, H, img)
        print('contact', name, W, 'x', H)
    # ---- 1920x1080 stills of the biggest beats
    for i, tag in ((6, 'ignite'), (14, 'swell'), (17, 'wings'), (20, 'detonation'), (23, 'reveal')):
        px = stage_still(F[i], throne, s=3)
        out = os.path.join(PREVIEWS, 'still_%02d_%s_1920x1080.png' % (i, tag))
        write_png(out, 1920, 1080, px)
        print('still', os.path.basename(out))


if __name__ == '__main__':
    what = sys.argv[1:] or ['build', 'previews']
    if 'build' in what:
        build()
    if 'previews' in what:
        previews()
