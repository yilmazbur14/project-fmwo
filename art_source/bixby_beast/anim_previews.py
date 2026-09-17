"""Previews for the beast Bixby combat set (written to scratchpad/bixby_beast_anims/):
  per-animation GIFs (3x), full combat loop GIF, defeat GIF, 1920x1080 arena mockups.
World model used everywhere: G = ground point under the boss.
  hover / fly / fire : sprite anchor (96,151) drawn at G - (0, lift) with lift = 40 texels; hover shadow centre (96,25) at G
  grounded sheets    : sprite anchor at G; ground shadow centre (96,25) at G
Shadows are solid black in the PNGs; previews blend them at 38% like the arena mockups before."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop, scale, blank
from gifio2 import write_gif

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(HERE, '..', 'final_anims')
APPROVED = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/'
OUTDIR = os.environ.get('BIXBY_ANIM_PREVIEWS', os.path.join(HERE, '..', 'bixby_beast_anims_previews'))
# arena background: Godot movie writer output, e.g.
#   Godot --path <project> --write-movie <dir>/arena.png --fixed-fps 30 --quit-after 3 res://Scenes/Core/ArenaScene.tscn
ARENA = os.environ.get('BIXBY_ARENA_PNG', os.path.join(HERE, '..', 'arena_render', 'arena00000002.png'))
PLAYER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/player_4dir_sheet.png'
FLOOR = (136, 180, 99, 255)
SHADOW_ALPHA = 0.38
LIFT = 40
os.makedirs(OUTDIR, exist_ok=True)

_cache = {}


def sheet(name, fw=192, fh=160, approved=False):
    key = (name, approved)
    if key not in _cache:
        path = os.path.join(APPROVED if approved else FINAL, name)
        w, h, px = read_png(path)
        _cache[key] = (w, h, [[tuple(p) for p in row] for row in px])
    w, h, px = _cache[key]
    return [crop(px, fw * i, 0, fw, fh) for i in range(w // fw)]


def flip_h(fr):
    return [list(reversed(row)) for row in fr]


def blit(dst, src, x0, y0):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        yy = y0 + y
        if not 0 <= yy < H:
            continue
        d = dst[yy]
        for x, p in enumerate(row):
            if p[3] and 0 <= x0 + x < W:
                d[x0 + x] = p


def shade(dst, src, x0, y0, alpha=SHADOW_ALPHA):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        yy = y0 + y
        if not 0 <= yy < H:
            continue
        d = dst[yy]
        for x, p in enumerate(row):
            xx = x0 + x
            if p[3] and 0 <= xx < W:
                q = d[xx]
                d[xx] = (int(round(q[0] * (1 - alpha))), int(round(q[1] * (1 - alpha))), int(round(q[2] * (1 - alpha))), 255)


class Stage:
    """a floor-coloured stage; G is the ground point in stage texels"""

    def __init__(self, w, h):
        self.w, self.h = w, h

    def frame(self, spr, gx, gy, lift=0, shadow=None, flip=False, extra=None):
        cv = blank(self.w, self.h, FLOOR)
        if shadow is not None:
            shade(cv, shadow, gx - 96, gy - 25)
        s = flip_h(spr) if flip else spr
        blit(cv, s, gx - 96, gy - lift - 151)
        if extra:
            for (e, ex, ey) in extra:
                blit(cv, e, ex, ey)
        return cv


def gif(name, frames, delays, s=3):
    path = os.path.join(OUTDIR, name)
    write_gif(path, frames, delays, scale=s)
    print('gif', os.path.basename(path), len(frames), 'frames')
    return path


# ------------------------------------------------------------------ sheets
def load_all():
    return dict(
        hover=sheet('bixby_beast.png', approved=True),
        fire=sheet('bixby_beast_firebreath.png', 192, 256, approved=True),
        hshadow=sheet('bixby_beast_shadow.png', 192, 48, approved=True),
        gshadow=sheet('bixby_beast_shadow_ground.png', 192, 48),
        fly=sheet('bixby_beast_fly.png'),
        land=sheet('bixby_beast_land.png'),
        recover=sheet('bixby_beast_recover.png'),
        hit=sheet('bixby_beast_hit.png'),
        takeoff=sheet('bixby_beast_takeoff.png'),
        roar=sheet('bixby_beast_roar.png'),
        defeat=sheet('bixby_beast_defeat.png'),
    )


def per_animation(A):
    st = Stage(212, 214)
    gx, gy = 106, 196
    # fly: 3-frame flap, hover shadow synced (hover frames 0, 2, 3)
    fr = [st.frame(A['fly'][i], gx, gy, LIFT, A['hshadow'][[0, 2, 3][i]]) for i in range(3)]
    gif('bixby_beast_fly_3x.gif', fr, [9, 7, 8])
    # land: descend during frame 0 (sprite drops from lift 40 to 0 while the shadow stays), impact, crouch
    fr, dl = [], []
    for lift in (40, 27, 14, 4):
        fr.append(st.frame(A['land'][0], gx, gy, lift, A['hshadow'][2]))
        dl.append(5)
    fr.append(st.frame(A['land'][1], gx, gy + 1, 0, A['gshadow'][0]))
    dl.append(14)
    fr.append(st.frame(A['land'][2], gx, gy, 0, A['gshadow'][0]))
    dl.append(40)
    gif('bixby_beast_land_3x.gif', fr, dl)
    # recover loop
    fr = [st.frame(A['recover'][i], gx, gy, 0, A['gshadow'][1]) for i in range(4)] * 2
    gif('bixby_beast_recover_3x.gif', fr, [18, 14, 18, 16] * 2)
    # hit: recover -> hit 0 -> hit 1 -> recover
    fr = [st.frame(A['recover'][0], gx, gy, 0, A['gshadow'][1]), st.frame(A['hit'][0], gx, gy, 0, A['gshadow'][1]),
          st.frame(A['hit'][1], gx, gy, 0, A['gshadow'][1]), st.frame(A['recover'][3], gx, gy, 0, A['gshadow'][1])]
    gif('bixby_beast_hit_3x.gif', fr, [40, 8, 14, 30])
    # takeoff: crouch, downbeat (still grounded), rise during frame 2 into hover frame 0
    fr, dl = [], []
    fr.append(st.frame(A['takeoff'][0], gx, gy, 0, A['gshadow'][0]))
    dl.append(22)
    fr.append(st.frame(A['takeoff'][1], gx, gy, 0, A['gshadow'][0]))
    dl.append(12)
    for lift in (8, 20, 32):
        fr.append(st.frame(A['takeoff'][2], gx, gy, lift, A['hshadow'][3]))
        dl.append(5)
    fr.append(st.frame(A['hover'][0], gx, gy, 40, A['hshadow'][0]))
    dl.append(30)
    gif('bixby_beast_takeoff_3x.gif', fr, dl)
    # roar: wind-up, then shake between frames 1 and 2
    fr = [st.frame(A['roar'][0], gx, gy, 0, A['gshadow'][0])]
    dl = [34]
    for k in range(6):
        fr.append(st.frame(A['roar'][1 + k % 2], gx + (1 if k % 2 else 0), gy, 0, A['gshadow'][0]))
        dl.append(7)
    gif('bixby_beast_roar_3x.gif', fr, dl)


DEFEAT_DELAYS = [10, 30, 16, 14, 60, 34, 12, 12, 40, 250]
DEFEAT_SHADOW = [0, 1, 1, 1, 2, 2, 2, 2, 3, 3]


def defeat_gif(A, s=3):
    st = Stage(212, 170)
    gx, gy = 106, 161
    fr = []
    for i in range(10):
        f = st.frame(A['defeat'][i], gx + (1 if i == 0 else 0), gy, 0, A['gshadow'][DEFEAT_SHADOW[i]])
        fr.append(f)
    return gif('bixby_beast_defeat_%dx.gif' % s, fr, DEFEAT_DELAYS, s)


def combat_loop(A, s=2):
    """hover -> fly (strafe right, back left flipped) -> fire breath -> land -> recover -> hit -> recover -> takeoff -> hover"""
    W, H = 420, 390
    st = Stage(W, H)
    gy = 300
    cx = W // 2
    fr, dl = [], []

    def add(f, d):
        fr.append(f)
        dl.append(d)
    hov = [0, 1, 2, 3]
    for k in range(8):
        i = hov[k % 4]
        add(st.frame(A['hover'][i], cx, gy, LIFT, A['hshadow'][i]), [12, 10, 12, 10][i])
    # strafe right then back to centre facing left
    xs = list(range(cx, cx + 96, 12))
    for n, x in enumerate(xs):
        i = n % 3
        add(st.frame(A['fly'][i], x, gy, LIFT, A['hshadow'][[0, 2, 3][i]]), 8)
    for n, x in enumerate(range(cx + 96, cx - 1, -12)):
        i = n % 3
        add(st.frame(A['fly'][i], x, gy, LIFT, flip_h(A['hshadow'][[0, 2, 3][i]]), flip=True), 8)
    # fire breath (approved sheet, 192x256 with its top-left on the hover frame's top-left)
    for i, d in ((0, 40), (1, 10), (2, 12), (1, 8), (2, 12), (1, 8), (2, 30)):
        cv = blank(W, H, FLOOR)
        shade(cv, A['hshadow'][1], cx - 96, gy - 25)
        blit(cv, A['fire'][i], cx - 96, gy - LIFT - 151)
        add(cv, d)
    # land
    for lift in (40, 27, 14, 4):
        add(st.frame(A['land'][0], cx, gy, lift, A['hshadow'][2]), 5)
    add(st.frame(A['land'][1], cx, gy + 1, 0, A['gshadow'][0]), 14)
    add(st.frame(A['land'][2], cx, gy, 0, A['gshadow'][0]), 30)
    # recover x2, hit, recover
    for k in range(8):
        add(st.frame(A['recover'][k % 4], cx, gy, 0, A['gshadow'][1]), [18, 14, 18, 16][k % 4])
    add(st.frame(A['hit'][0], cx + 1, gy, 0, A['gshadow'][1]), 8)
    add(st.frame(A['hit'][1], cx, gy, 0, A['gshadow'][1]), 14)
    for k in range(4):
        add(st.frame(A['recover'][k % 4], cx, gy, 0, A['gshadow'][1]), [18, 14, 18, 16][k % 4])
    # takeoff back to hover
    add(st.frame(A['takeoff'][0], cx, gy, 0, A['gshadow'][0]), 22)
    add(st.frame(A['takeoff'][1], cx, gy, 0, A['gshadow'][0]), 12)
    for lift in (8, 20, 32):
        add(st.frame(A['takeoff'][2], cx, gy, lift, A['hshadow'][3]), 5)
    for k in range(4):
        add(st.frame(A['hover'][k], cx, gy, LIFT, A['hshadow'][k]), [12, 10, 12, 10][k])
    return gif('bixby_beast_combat_loop_%dx.gif' % s, fr, dl, s)


# ------------------------------------------------------------------ arena mockups (1920x1080)
def blit_scaled(dst, src, x0, y0, s):
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


def shade_scaled(dst, src, x0, y0, s, alpha=SHADOW_ALPHA):
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


def arena_base():
    w, h, px = read_png(ARENA)
    px = [[tuple(p) for p in row] for row in px]
    for y in range(870, 932):          # remove the render's own player (placed again below)
        for x in range(940, 982):
            px[y][x] = FLOOR
    return px


def player_frame(row, col):
    w, h, px = read_png(PLAYER)
    return crop([[tuple(p) for p in r] for r in px], col * 32, row * 32, 32, 32)


def mockups(A):
    BOSS_S, PLAYER_S = 3, 2       # boss sprites scale 3 (scene), MainPlayer CharacterBody2D scale 2
    gx, gy = 960, 620             # ground point of the boss on screen
    # 1) recovery punish window: player right below the slumped beast, mid-punch (back view, punch frame)
    px = arena_base()
    shade_scaled(px, A['gshadow'][1], gx - 96 * BOSS_S, gy - 25 * BOSS_S, BOSS_S)
    blit_scaled(px, A['recover'][2], gx - 96 * BOSS_S, gy - 151 * BOSS_S, BOSS_S)
    pl = player_frame(1, 8)
    blit_scaled(px, pl, 960 - 16 * PLAYER_S, gy + 34 - 16 * PLAYER_S, PLAYER_S)
    out1 = os.path.join(OUTDIR, 'mockup_arena_recover_punch_1920x1080.png')
    write_png(out1, 1920, 1080, px)
    # 2) defeat hold pose, player standing back a little
    px = arena_base()
    shade_scaled(px, A['gshadow'][3], gx - 96 * BOSS_S, gy - 25 * BOSS_S, BOSS_S)
    blit_scaled(px, A['defeat'][9], gx - 96 * BOSS_S, gy - 151 * BOSS_S, BOSS_S)
    pl = player_frame(1, 0)
    blit_scaled(px, pl, 900 - 16 * PLAYER_S, gy + 190 - 16 * PLAYER_S, PLAYER_S)
    out2 = os.path.join(OUTDIR, 'mockup_arena_defeat_hold_1920x1080.png')
    write_png(out2, 1920, 1080, px)
    print('mockups', out1, out2)
    return out1, out2


if __name__ == '__main__':
    what = sys.argv[1:] or ['anims', 'defeat', 'loop', 'mockups']
    A = load_all()
    if 'anims' in what:
        per_animation(A)
    if 'defeat' in what:
        defeat_gif(A)
    if 'loop' in what:
        combat_loop(A)
    if 'mockups' in what:
        mockups(A)
