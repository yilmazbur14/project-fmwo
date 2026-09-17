"""Review previews for the defense / hype art. Built from the files exported into the project (or --draft).
  python previews.py [hud] [parry] [guard] [super] [gifs] [closeup]
Outputs go to DH_PREVIEWS (the scratchpad defense_hype_draft folder)."""
import sys
sys.dont_write_bytecode = True
import math, subprocess
from dh_common import *
from gifio import write_gif
import assets

A = assets.load()
OUT = PREVIEWS.rstrip('/') + '/'
FLOOR = (136, 180, 99)
APRON = (113, 152, 79)
SHEET = from_png(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png')
UPC = from_png(PROJ + 'Assets/Characters/MainPlayer/player_uppercut.png')
IMP = from_png(PROJ + 'Assets/Effects/uppercut_impact.png')
DAZE = from_png(PROJ + 'Assets/Effects/daze_stars.png')
HEART = from_png(PROJ + 'Assets/UI/hearttest.png')
HEART_HALF = from_png(PROJ + 'Assets/UI/hearthalftest.png')
HEART_EMPTY = from_png(PROJ + 'Assets/UI/emptyhearttest.png')
QTE_FULL_TEXT = from_png(PROJ + 'Assets/UI/qte_full_text_3x.png')

# ------------------------------------------------------------------ HUD layout (screen px, all UI at 3x)
HEARTS_Y = 952          # heart HBox top (was 988): moved up 36 px to make room for the stamina bar
STAMINA_XY = (10, 1026)  # stamina frame top-left; the 3x frame is 264x45
HYPE_XY = (1539, 946)    # hype canvas top-left; the 3x canvas is 369x126
HYPE_LABEL = (26 * 3, 6 * 3)
HYPE_FILL = (28 * 3, 26 * 3)
STAM_FILL = (7 * 3, 5 * 3)


# ------------------------------------------------------------------ image helpers
def rgb(w, h, col):
    return [[col] * w for _ in range(h)]


def paste(img, c, x0, y0, s=1, flip=False, clip=None):
    H, W = len(img), len(img[0])
    cw = c.w if clip is None else min(c.w, clip)
    for y in range(c.h):
        row = c.p[y]
        for x in range(cw):
            v = row[(c.w - 1 - x) if flip else x]
            if not v:
                continue
            col = hex2rgb(v)
            for dy in range(s):
                Y = y0 + y * s + dy
                if 0 <= Y < H:
                    r = img[Y]
                    for dx in range(s):
                        X = x0 + x * s + dx
                        if 0 <= X < W:
                            r[X] = col


def save(img, name):
    write_png(OUT + name, len(img[0]), len(img), [[p + (255,) for p in row] for row in img])
    print('wrote', name)


def frames_of(sheet, fw, fh, row=0):
    n = sheet.w // fw
    return [crop(sheet, i * fw, row * fh, fw, fh) for i in range(n)]


def region(img, x0, y0, w, h, s):
    out = []
    for y in range(h):
        src = img[y0 + y]
        r = []
        for x in range(w):
            r.extend([src[x0 + x]] * s)
        for _ in range(s):
            out.append(list(r))
    return out


# ------------------------------------------------------------------ tiny label font (3x5)
FONT = {
    'A': ["XXX", "X.X", "XXX", "X.X", "X.X"], 'B': ["XX.", "X.X", "XX.", "X.X", "XX."],
    'C': ["XXX", "X..", "X..", "X..", "XXX"], 'D': ["XX.", "X.X", "X.X", "X.X", "XX."],
    'E': ["XXX", "X..", "XX.", "X..", "XXX"], 'F': ["XXX", "X..", "XX.", "X..", "X.."],
    'G': ["XXX", "X..", "X.X", "X.X", "XXX"], 'H': ["X.X", "X.X", "XXX", "X.X", "X.X"],
    'I': ["XXX", ".X.", ".X.", ".X.", "XXX"], 'J': ["..X", "..X", "..X", "X.X", "XXX"],
    'K': ["X.X", "XX.", "X..", "XX.", "X.X"], 'L': ["X..", "X..", "X..", "X..", "XXX"],
    'M': ["X.X", "XXX", "XXX", "X.X", "X.X"], 'N': ["XX.", "X.X", "X.X", "X.X", "X.X"],
    'O': ["XXX", "X.X", "X.X", "X.X", "XXX"], 'P': ["XXX", "X.X", "XXX", "X..", "X.."],
    'Q': ["XXX", "X.X", "X.X", "XXX", "..X"], 'R': ["XX.", "X.X", "XX.", "X.X", "X.X"],
    'S': ["XXX", "X..", "XXX", "..X", "XXX"], 'T': ["XXX", ".X.", ".X.", ".X.", ".X."],
    'U': ["X.X", "X.X", "X.X", "X.X", "XXX"], 'V': ["X.X", "X.X", "X.X", "X.X", ".X."],
    'W': ["X.X", "X.X", "XXX", "XXX", "X.X"], 'X': ["X.X", "X.X", ".X.", "X.X", "X.X"],
    'Y': ["X.X", "X.X", ".X.", ".X.", ".X."], 'Z': ["XXX", "..X", ".X.", "X..", "XXX"],
    '0': ["XXX", "X.X", "X.X", "X.X", "XXX"], '1': [".X.", "XX.", ".X.", ".X.", "XXX"],
    '2': ["XXX", "..X", "XXX", "X..", "XXX"], '3': ["XXX", "..X", "XXX", "..X", "XXX"],
    '4': ["X.X", "X.X", "XXX", "..X", "..X"], '5': ["XXX", "X..", "XXX", "..X", "XXX"],
    '6': ["XXX", "X..", "XXX", "X.X", "XXX"], '7': ["XXX", "..X", "..X", "..X", "..X"],
    '8': ["XXX", "X.X", "XXX", "X.X", "XXX"], '9': ["XXX", "X.X", "XXX", "..X", "XXX"],
    ' ': ["...", "...", "...", "...", "..."], '.': ["...", "...", "...", "...", ".X."],
    '-': ["...", "...", "XXX", "...", "..."], '+': ["...", ".X.", "XXX", ".X.", "..."],
    '(': [".X", "X.", "X.", "X.", ".X"], ')': ["X.", ".X", ".X", ".X", "X."], '=': ["...", "XXX", "...", "XXX", "..."],
    '%': ["X.X", "..X", ".X.", "X..", "X.X"], '/': ["..X", "..X", ".X.", "X..", "X.."], ':': ["...", ".X.", "...", ".X.", "..."],
    '_': ["...", "...", "...", "...", "XXX"], ',': ["...", "...", "...", ".X.", "X.."], '!': [".X.", ".X.", ".X.", "...", ".X."],
}


def text(img, s, x, y, scale, col, shadow=True):
    def draw(xo, yo, c):
        cx = xo
        for ch in s.upper():
            g = FONT.get(ch, FONT[' '])
            for j, row in enumerate(g):
                for i, v in enumerate(row):
                    if v == 'X':
                        for dy in range(scale):
                            for dx in range(scale):
                                Y, X = yo + j * scale + dy, cx + i * scale + dx
                                if 0 <= Y < len(img) and 0 <= X < len(img[0]):
                                    img[Y][X] = c
            cx += (len(g[0]) + 1) * scale
    if shadow:
        draw(x + scale // 2 + 1, y + scale // 2 + 1, (0, 0, 0))
    draw(x, y, col)


# ------------------------------------------------------------------ arena background
def arena_png():
    p = WORK + '/render_arena/arena00000002.png'
    if not os.path.exists(p):
        os.makedirs(WORK + '/render_arena', exist_ok=True)
        subprocess.run([GODOT, '--path', PROJ.rstrip('/'), '--write-movie', WORK + '/render_arena/arena.png',
                        '--fixed-fps', '30', '--quit-after', '3', 'res://Scenes/Core/ArenaScene.tscn'],
                       capture_output=True, text=True)
    return p


_ARENA = None


def arena():
    """the arena render with the default player removed, the hearts erased (they are redrawn as HUD),
    and Eric's boss bar + name copied in from the Eric fight render"""
    global _ARENA
    if _ARENA is None:
        w, h, px = read_png(arena_png())
        img = [[p[:3] for p in row] for row in px]
        for y in range(870, 932):
            for x in range(940, 980):
                img[y][x] = FLOOR
        for y in range(990, 1077):
            for x in range(0, 300):
                img[y][x] = APRON if (988 <= y <= 1009 and x >= 83) else (0, 0, 0)
        ep = WORK + '/render_eric/eric00000089.png'
        if not os.path.exists(ep):
            # Godot's movie writer writes nothing into the project (never use run_project with a scene)
            os.makedirs(WORK + '/render_eric', exist_ok=True)
            subprocess.run([GODOT, '--path', PROJ.rstrip('/'), '--write-movie', WORK + '/render_eric/eric.png',
                            '--fixed-fps', '30', '--quit-after', '90', 'res://Scenes/Bosses/EricBossFightScene.tscn'],
                           capture_output=True, text=True)
        if os.path.exists(ep):
            w2, h2, px2 = read_png(ep)
            for y in range(40, 96):
                for x in range(760, 1162):
                    img[y][x] = px2[y][x][:3]
        _ARENA = img
    return [list(r) for r in _ARENA]


# ------------------------------------------------------------------ characters
ERIC_SHEET = None


def eric(frame):
    global ERIC_SHEET
    if ERIC_SHEET is None:
        ERIC_SHEET = from_png(PROJ + 'Assets/Characters/Eric/eric_sheet_v2.png')
    return crop(ERIC_SHEET, frame * 256, 0, 256, 192)


def paste_eric(img, frame, ex, ef, flip=False):
    """ex: world x of texel column 128 (mirrored when flipped); ef: world y of the feet (texel row 191 bottom)"""
    c = eric(frame)
    x0 = ex - (128 if not flip else 127) * 3
    paste(img, c, x0, ef - 192 * 3, 3, flip=flip)


def player_cell(row, col):
    return cell(SHEET, col, 32, 32, row)


# ------------------------------------------------------------------ HUD
def draw_hearts(img, hp=6, y0=HEARTS_Y):
    tex = []
    for i in range(3):
        v = hp - 2 * i
        tex.append(HEART if v >= 2 else (HEART_HALF if v == 1 else HEART_EMPTY))
    for i, t in enumerate(tex):
        x0 = i * 96
        for Y in range(92):
            ty = int((Y + 0.5) * 32 / 92)
            for X in range(92):
                tx = int((X + 0.5) * 32 / 92)
                v = t.p[ty][tx]
                if v:
                    img[y0 + Y][x0 + X] = hex2rgb(v)


def draw_stamina(img, frac=1.0, state='normal', flash=0, xy=STAMINA_XY):
    x, y = xy
    if state == 'broken':
        paste(img, frames_of(A['stamina_bar_broken_3x'], 264, 45)[flash], x, y)
        return
    paste(img, A['stamina_bar_frame_3x'], x, y)
    fill = A['stamina_bar_fill_3x'] if state == 'normal' else frames_of(A['stamina_bar_low_3x'], 222, 15)[flash]
    n = int(math.floor(fill.w * frac))
    if n > 0:
        paste(img, fill, x + STAM_FILL[0], y + STAM_FILL[1], clip=n)


def draw_hype(img, frac=0.0, full_frame=None, xy=HYPE_XY):
    x, y = xy
    paste(img, A['hype_meter_frame_3x'], x, y)
    fill = A['hype_meter_fill_3x']
    n = int(math.floor(fill.w * frac))
    if n > 0:
        paste(img, fill, x + HYPE_FILL[0], y + HYPE_FILL[1], clip=n)
    if full_frame is not None:
        paste(img, frames_of(A['hype_meter_full_3x'], 369, 126)[full_frame], x, y)
    label = frames_of(A['hype_label_3x'], 156, 60)[1 if full_frame is not None else 0]
    paste(img, label, x + HYPE_LABEL[0], y + HYPE_LABEL[1])


def popup(img, name, frame, cx, bottom):
    s3 = A[name + '_3x']
    fw = s3.w // 2
    fr = frames_of(s3, fw, 60)[frame]
    bb = bbox(fr)
    paste(img, fr, cx - fw // 2, bottom - (bb[3] + 1))


# ------------------------------------------------------------------ 1) HUD mockup
def mock_hud():
    img = arena()
    paste_eric(img, 21, 1010, 600)
    paste(img, player_cell(3, 0), 700, 528, 2)
    draw_hearts(img, 5)
    draw_stamina(img, 0.5)
    draw_hype(img, 0.7)
    save(img, 'mockup_1_hud_stamina50_hype70.png')
    return img


# ------------------------------------------------------------------ 2) PARRY
EX, EF = 760, 640


def parry_scene():
    img = arena()
    paste_eric(img, 20, EX, EF)
    tip_x, tip_y = EX + (248 - 128) * 3, EF - (192 - 154) * 3      # blade tip, world px
    ptl = (tip_x - 16, tip_y - 13)                                  # left-facing block: glove texel (11, 6)
    paste(img, player_cell(2, 9), ptl[0], ptl[1], 2)
    return img, ptl, (tip_x + 1, tip_y + 1)


def mock_parry():
    img, ptl, contact = parry_scene()
    fl = frames_of(A['parry_flash'], 64, 64)[1]
    paste(img, fl, contact[0] - 64, contact[1] - 64, 2)
    popup(img, 'popup_parry', 1, ptl[0] + 40, ptl[1] - 28)
    draw_hearts(img, 5)
    draw_stamina(img, 0.78)
    draw_hype(img, 0.86)
    save(img, 'mockup_2_parry.png')
    save(region(img, 700, 330, 640, 360, 3), 'mockup_2_parry_zoom3x.png')
    return img


# ------------------------------------------------------------------ 3) GUARD BREAK
def mock_guard():
    img = arena()
    paste_eric(img, 21, EX, EF)
    ptl = (1104, 513)
    gb = A['player_guard_break']
    paste(img, crop(gb, 0, 2 * 32, 32, 32), ptl[0], ptl[1], 2)       # left-facing, sway frame 0
    anchor = (ptl[0] + 16 * 2, ptl[1] + 3 * 2)                     # player-frame texel (16, 3)
    stars = frames_of(A['guard_break_stars'], 32, 16)[1]
    paste(img, stars, anchor[0] - 16 * 2, anchor[1] - 9 * 2, 2)
    popup(img, 'popup_guard_break', 1, anchor[0], anchor[1] - 9 * 2 - 6)
    draw_hearts(img, 5)
    draw_stamina(img, 0.0, 'broken', 1)
    draw_hype(img, 0.35)
    save(img, 'mockup_3_guard_break.png')
    save(region(img, 820, 330, 640, 360, 3), 'mockup_3_guard_break_zoom3x.png')
    return img


# ------------------------------------------------------------------ 4) SUPERCHARGED uppercut (1.5x finisher zoom)
EFEET = 560
PX, PY = 996, 564
CAMX, CAMY = 1010, 430
IMPACT_OFFSET = (40, -40)


def zoom_view(world, cx, cy, z=1.5, W=1920, H=1080):
    out = []
    left, top = cx - W / (2 * z), cy - H / (2 * z)
    WH, WW = len(world), len(world[0])
    xs = [int((left + (X + 0.5) / z) // 1) for X in range(W)]
    for Y in range(H):
        wy = int((top + (Y + 0.5) / z) // 1)
        if 0 <= wy < WH:
            row = world[wy]
            out.append([row[x] if 0 <= x < WW else (0, 0, 0) for x in xs])
        else:
            out.append([(0, 0, 0)] * W)
    return out


def world_to_screen(x, y, cx=CAMX, cy=CAMY, z=1.5, W=1920, H=1080):
    return int(round((x - (cx - W / (2 * z))) * z)), int(round((y - (cy - H / (2 * z))) * z))


def super_world(upc_frame, imp_frame, super_art=True):
    world = arena()
    er = eric(27)
    E_top = EFEET - 192 * 3
    E_left = 1000 - (255 - 165) * 3
    paste(world, er, E_left, E_top, 3, flip=True)
    if imp_frame is not None:
        ix, iy = PX + (27 - 24) * 2 + IMPACT_OFFSET[0], PY - 96 + 14 * 2 + IMPACT_OFFSET[1]
        imp = frames_of(A['uppercut_impact_super'] if super_art else IMP, 96, 96)[imp_frame]
        paste(world, imp, ix - 96, iy - 96, 2)
    up = frames_of(A['player_uppercut_super'] if super_art else UPC, 48, 64)[upc_frame]
    paste(world, up, PX - 48, PY - 96, 2)
    return world


def mock_super():
    world = super_world(5, 1)
    img = zoom_view(world, CAMX, CAMY)
    draw_hearts(img, 5)
    draw_stamina(img, 0.6)
    draw_hype(img, 1.0, full_frame=0)
    save(img, 'mockup_4_supercharged_uppercut.png')
    # the approved normal version beside it, for comparison
    w2 = super_world(5, 1, super_art=False)
    img2 = zoom_view(w2, CAMX, CAMY)
    cmp_img = rgb(1920, 540, (30, 30, 40))
    half = [row[::2] for row in img2[::2]]
    half_s = [row[::2] for row in img[::2]]
    for y in range(540):
        cmp_img[y][:960] = half[y]
        cmp_img[y][960:] = half_s[y]
    text(cmp_img, 'APPROVED NORMAL', 20, 16, 4, (255, 255, 255))
    text(cmp_img, 'SUPERCHARGED (NEW)', 980, 16, 4, (255, 240, 120))
    save(cmp_img, 'mockup_4b_normal_vs_super.png')


# ------------------------------------------------------------------ GIFs
def gif_frames_scaled(frames, s, bg, pad=0):
    out = []
    for c in frames:
        img = rgb((c.w + 2 * pad) * s, (c.h + 2 * pad) * s, bg)
        paste(img, c, pad * s, pad * s, s)
        out.append(img)
    return out


def gifs():
    DARK = (38, 38, 52)
    # UI states in motion, at the in-game 3x size, on the arena's bottom band colours
    frames, durs = [], []
    for step in range(28):                                   # stamina drains, goes low, breaks, refills
        img = rgb(300, 70, (0, 0, 0))
        if step < 10:
            draw_stamina(img, 1.0 - step * 0.075, xy=(18, 12))
        elif step < 16:
            draw_stamina(img, 0.22, 'low', step % 2, xy=(18, 12))
        elif step < 22:
            draw_stamina(img, 0.0, 'broken', step % 2, xy=(18, 12))
        else:
            draw_stamina(img, (step - 21) * 0.17, xy=(18, 12))
        frames.append(img)
        durs.append(12)
    write_gif(OUT + 'gif_stamina_states_3x.gif', frames, durs)
    print('gif stamina')
    frames, durs = [], []
    for step in range(30):
        img = rgb(400, 140, (0, 0, 0))
        if step < 14:
            draw_hype(img, step / 13.0, xy=(16, 8))
            durs.append(10)
        else:
            draw_hype(img, 1.0, full_frame=(step - 14) % 4, xy=(16, 8))
            durs.append(8)
        frames.append(img)
    write_gif(OUT + 'gif_hype_fill_then_full_3x.gif', frames, durs)
    print('gif hype')
    # popups (3x, cycling their two frames)
    frames = []
    for k in range(8):
        img = rgb(440, 300, (70, 90, 60))
        for i, (n, fw) in enumerate([('popup_parry', 216), ('popup_perfect', 288), ('popup_guard_break', 408),
                                     ('popup_hype', 192)]):
            fr = frames_of(A[n + '_3x'], fw, 60)[k % 2]
            paste(img, fr, (440 - fw) // 2, 10 + i * 72)
        frames.append(img)
    write_gif(OUT + 'gif_popups_3x.gif', frames, [9] * 8)
    print('gif popups')
    # effects at 4x on the arena floor
    for name, fw, fh, durs_ms, pad in [('block_spark', 32, 32, [40, 50, 60, 70], 2),
                                       ('parry_flash', 64, 64, [30, 50, 60, 70, 80], 0),
                                       ('guard_break_stars', 32, 16, [100] * 6, 2),
                                       ('uppercut_impact_super', 96, 96, [40, 60, 60, 70, 80, 90, 100], 0)]:
        fr = frames_of(A[name], fw, fh)
        s = 4 if fw <= 64 else 3
        loop = name == 'guard_break_stars'
        imgs = gif_frames_scaled(fr + ([] if loop else [Canvas(fw, fh)]), s, FLOOR, pad)
        write_gif(OUT + 'gif_%s_%dx.gif' % (name, s), imgs, [max(2, d // 10) for d in durs_ms] + ([] if loop else [40]))
        print('gif', name)
    # guard break: all four directions ping-pong with the stars, 4x
    gb = A['player_guard_break']
    st = frames_of(A['guard_break_stars'], 32, 16)
    order = [0, 1, 2, 1]
    frames = []
    for t in range(12):
        img = rgb(4 * 36 * 4, 44 * 4, FLOOR)
        for r in range(4):
            f = order[t % 4]
            body = crop(gb, f * 32, r * 32, 32, 32)
            paste(img, body, (4 + r * 36) * 4, 12 * 4, 4)
            # contract: the stars' pivot texel (16, 9) goes on player-frame texel (16, 3)
            paste(img, st[t % 6], (4 + r * 36 + 16 - 16) * 4, (12 + 3 - 9) * 4, 4)
        frames.append(img)
    write_gif(OUT + 'gif_player_guard_break_4dirs_4x.gif', frames, [15] * 12)
    print('gif guard break')
    # perfect dodge: player dashes right through a (dummy) swing, ghosts left behind, 3x
    trail = A['perfect_dodge_trail']
    frames, durs = [], []
    xs = [10, 10, 34, 58, 82, 82, 82, 82, 82, 82]
    for t in range(10):
        img = rgb(140 * 3, 44 * 3, FLOOR)
        for g, gx in enumerate([10, 30, 50, 70]):
            age = t - 2 - g // 1
            if 0 <= age < 4 and gx < xs[t]:
                paste(img, crop(trail, age * 32, 3 * 32, 32, 32), gx * 3, 6 * 3, 3)
        paste(img, player_cell(3, 0), xs[t] * 3, 6 * 3, 3)
        frames.append(img)
        durs.append(30 if t in (0, 9) else 6)
    write_gif(OUT + 'gif_perfect_dodge_trail_3x.gif', frames, durs)
    print('gif dodge')
    # supercharged uppercut: full move at 4x, then the in-scene contact at 1.5x zoom crop
    sup = frames_of(A['player_uppercut_super'], 48, 64)
    seq = [(player_std48(), 40)]
    for _ in range(3):
        for i in range(3):
            seq.append((sup[i], 8))
    for i, d in zip(range(3, 10), [5, 6, 6, 6, 14, 10, 16]):
        seq.append((sup[i], d))
    seq.append((player_std48(), 60))
    imgs = gif_frames_scaled([c for c, _ in seq], 4, FLOOR, 8)
    write_gif(OUT + 'gif_player_uppercut_super_4x.gif', imgs, [d for _, d in seq])
    print('gif uppercut super')
    frames, durs = [], []
    for step, (uf, imf, d) in enumerate([(4, None, 6), (5, 0, 4), (5, 1, 6), (6, 2, 6), (7, 3, 7), (7, 4, 8),
                                         (8, 5, 9), (9, 6, 10), (9, None, 40)]):
        w = super_world(uf, imf)
        z = zoom_view(w, CAMX, CAMY)
        crop_img = [row[600:1400] for row in z[300:900]]
        small = [row[::2] for row in crop_img[::2]]
        frames.append(small)
        durs.append(d)
    write_gif(OUT + 'gif_supercharged_contact_on_eric.gif', frames, durs)
    print('gif contact')


def player_std48():
    c = Canvas(48, 64)
    c.blit(player_cell(3, 0), 8, 32)
    return c


# ------------------------------------------------------------------ 6x close-up sheet of every UI piece
def closeup():
    S = 6
    items = [
        ('STAMINA_BAR_FRAME 88X15 9-SLICE L7 T6 R8 B6', A['stamina_bar_frame'], 1),
        ('STAMINA_BAR_FILL 74X5 AT (7,5)', A['stamina_bar_fill'], 1),
        ('STAMINA_BAR_LOW 2 X 74X5', A['stamina_bar_low'], 2),
        ('STAMINA_BAR_BROKEN 2 X 88X15', A['stamina_bar_broken'], 2),
        ('HYPE_METER_FRAME 123X42 FIXED', A['hype_meter_frame'], 1),
        ('HYPE_METER_FILL 88X5 AT (28,26)', A['hype_meter_fill'], 1),
        ('HYPE_METER_FULL 4 X 123X42', A['hype_meter_full'], 4),
        ('HYPE_LABEL 2 X 52X20 AT (26,6)', A['hype_label'], 2),
        ('POPUP_PARRY 2 X 72X20', A['popup_parry'], 2),
        ('POPUP_PERFECT 2 X 96X20', A['popup_perfect'], 2),
        ('POPUP_GUARD_BREAK 2 X 136X20', A['popup_guard_break'], 2),
        ('POPUP_HYPE 2 X 64X20', A['popup_hype'], 2),
    ]
    GAP = 14
    LBL = 34
    maxw = 0
    layout = []
    y = GAP
    for label, sheet, n in items:
        fw = sheet.w // n
        if n == 4:                                  # 2x2 to keep the sheet a sane width
            w = (2 * fw * S + GAP)
            h = 2 * sheet.h * S + GAP
        else:
            w = n * fw * S + (n - 1) * GAP
            h = sheet.h * S
        layout.append((label, sheet, n, fw, y))
        y += LBL + h + GAP * 2
        maxw = max(maxw, w)
    W_ = maxw + 2 * GAP
    img = rgb(W_, y, (46, 46, 60))
    for label, sheet, n, fw, y0 in layout:
        text(img, label, GAP, y0, 4, (235, 235, 245))
        for i in range(n):
            fr = crop(sheet, i * fw, 0, fw, sheet.h)
            if n == 4:
                x = GAP + (i % 2) * (fw * S + GAP)
                yy = y0 + LBL + (i // 2) * (sheet.h * S + GAP)
            else:
                x = GAP + i * (fw * S + GAP)
                yy = y0 + LBL
            # checker behind so transparency is visible
            for Y in range(sheet.h * S):
                for X in range(fw * S):
                    img[yy + Y][x + X] = (70, 70, 90) if ((X // (S * 2)) + (Y // (S * 2))) % 2 else (62, 62, 80)
            paste(img, fr, x, yy, S)
    save(img, 'closeup_ui_6x.png')


if __name__ == '__main__':
    which = [a for a in sys.argv[1:] if not a.startswith('--')] or ['hud', 'parry', 'guard', 'super', 'gifs', 'closeup']
    if 'hud' in which:
        mock_hud()
    if 'parry' in which:
        mock_parry()
    if 'guard' in which:
        mock_guard()
    if 'super' in which:
        mock_super()
    if 'gifs' in which:
        gifs()
    if 'closeup' in which:
        closeup()
