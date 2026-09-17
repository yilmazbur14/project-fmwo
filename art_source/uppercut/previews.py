"""Review previews for the uppercut finisher, built from the files exported into the project:
GIFs (full move, impact, daze stars), 1920x1080 arena mockups (charge / connect), 6x close-up strip."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import *
from pngio import read_png, write_png
from gifio import write_gif

import subprocess
from paths import PROJ, GODOT, WORK, work
OUT = __import__('paths').OUT.rstrip('/') + '/'
FLOOR = (136, 180, 99)

UP = from_png(PROJ + 'Assets/Characters/MainPlayer/player_uppercut.png')
IMP = from_png(PROJ + 'Assets/Effects/uppercut_impact.png')
DZ = from_png(PROJ + 'Assets/Effects/daze_stars.png')
SHEET = from_png(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png')
UI = {n: from_png(PROJ + 'Assets/UI/%s.png' % n) for n in
      ['qte_key_q', 'qte_key_w', 'qte_mash_text', 'qte_full_text', 'qte_meter_frame', 'qte_meter_fill',
       'qte_meter_full']}


def cell(src, i, w, h):
    c = Canvas(w, h)
    for y in range(h):
        c.p[y] = src.p[y][i * w:(i + 1) * w]
    return c


def std_in_48(row, col):
    c = Canvas(48, 64)
    for y in range(32):
        for x in range(32):
            c.p[32 + y][8 + x] = SHEET.p[row * 32 + y][col * 32 + x]
    return c


# ---------------------------------------------------------------- RGB image helpers
def rgb_canvas(w, h, col):
    return [[col for _ in range(w)] for _ in range(h)]


def paste(img, c, x0, y0, s=1, flip=False):
    H, W = len(img), len(img[0])
    for y in range(c.h):
        for x in range(c.w):
            v = c.p[y][(c.w - 1 - x) if flip else x]
            if not v:
                continue
            col = hex2rgb(v)
            for dy in range(s):
                Y = y0 + y * s + dy
                if 0 <= Y < H:
                    row = img[Y]
                    for dx in range(s):
                        X = x0 + x * s + dx
                        if 0 <= X < W:
                            row[X] = col


def to_rgba(img):
    return [[p + (255,) for p in row] for row in img]


# ---------------------------------------------------------------- tiny 3x5 pixel font for labels
FONT = {
    'A': ["XXX", "X.X", "XXX", "X.X", "X.X"], 'B': ["XX.", "X.X", "XX.", "X.X", "XX."],
    'C': ["XXX", "X..", "X..", "X..", "XXX"], 'D': ["XX.", "X.X", "X.X", "X.X", "XX."],
    'E': ["XXX", "X..", "XX.", "X..", "XXX"], 'F': ["XXX", "X..", "XX.", "X..", "X.."],
    'G': ["XXX", "X..", "X.X", "X.X", "XXX"], 'H': ["X.X", "X.X", "XXX", "X.X", "X.X"],
    'I': ["XXX", ".X.", ".X.", ".X.", "XXX"], 'L': ["X..", "X..", "X..", "X..", "XXX"],
    'M': ["X.X", "XXX", "XXX", "X.X", "X.X"], 'N': ["XX.", "X.X", "X.X", "X.X", "X.X"],
    'O': ["XXX", "X.X", "X.X", "X.X", "XXX"], 'P': ["XXX", "X.X", "XXX", "X..", "X.."],
    'R': ["XX.", "X.X", "XX.", "X.X", "X.X"], 'S': ["XXX", "X..", "XXX", "..X", "XXX"],
    'T': ["XXX", ".X.", ".X.", ".X.", ".X."], 'U': ["X.X", "X.X", "X.X", "X.X", "XXX"],
    'W': ["X.X", "X.X", "XXX", "XXX", "X.X"], 'X': ["X.X", "X.X", ".X.", "X.X", "X.X"],
    'Y': ["X.X", "X.X", ".X.", ".X.", ".X."], 'K': ["X.X", "XX.", "X..", "XX.", "X.X"],
    '0': ["XXX", "X.X", "X.X", "X.X", "XXX"], '1': [".X.", "XX.", ".X.", ".X.", "XXX"],
    '2': ["XXX", "..X", "XXX", "X..", "XXX"], '3': ["XXX", "..X", "XXX", "..X", "XXX"],
    '4': ["X.X", "X.X", "XXX", "..X", "..X"], '5': ["XXX", "X..", "XXX", "..X", "XXX"],
    '6': ["XXX", "X..", "XXX", "X.X", "XXX"], '7': ["XXX", "..X", "..X", "..X", "..X"],
    '8': ["XXX", "X.X", "XXX", "X.X", "XXX"], '9': ["XXX", "X.X", "XXX", "..X", "XXX"],
    ' ': ["...", "...", "...", "...", "..."], '.': ["...", "...", "...", "...", ".X."],
    '-': ["...", "...", "XXX", "...", "..."], '+': ["...", ".X.", "XXX", ".X.", "..."],
    '(': [".X", "X.", "X.", "X.", ".X"], ')': ["X.", ".X", ".X", ".X", "X."], '=': ["...", "XXX", "...", "XXX", "..."],
}


def text(img, s, x, y, scale, col):
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT[' '])
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == 'X':
                    for dy in range(scale):
                        for dx in range(scale):
                            Y, X = y + j * scale + dy, cx + i * scale + dx
                            if 0 <= Y < len(img) and 0 <= X < len(img[0]):
                                img[Y][X] = col
        cx += (len(g[0]) + 1) * scale


# ---------------------------------------------------------------- 1) full move GIF
def gif_full_move():
    S = 4
    PAD = 8

    def frame_rgb(c):
        img = rgb_canvas((48 + 2 * PAD) * S, 64 * S, FLOOR)
        paste(img, c, PAD * S, 0, S)
        return img
    seq = [(std_in_48(3, 0), 40)]
    for _ in range(3):
        for i in range(3):
            seq.append((cell(UP, i, 48, 64), 8))
    for i, d in zip(range(3, 10), [5, 6, 6, 6, 14, 10, 16]):
        seq.append((cell(UP, i, 48, 64), d))
    seq.append((std_in_48(3, 0), 60))
    frames = [frame_rgb(c) for c, _ in seq]
    write_gif(OUT + 'uppercut_full_move_4x.gif', frames, [d for _, d in seq])
    # flipped copy: what the code produces when facing left
    frames = []
    for c, _ in seq:
        img = rgb_canvas((48 + 2 * PAD) * S, 64 * S, FLOOR)
        paste(img, c, PAD * S, 0, S, flip=True)
        frames.append(img)
    write_gif(OUT + 'uppercut_full_move_facing_left_4x.gif', frames, [d for _, d in seq])


# ---------------------------------------------------------------- boss crops
def eric27():
    w, h, px = read_png(PROJ + 'Assets/Characters/Eric/eric_sheet_v2.png')
    c = Canvas(256, 192)
    for y in range(192):
        for x in range(256):
            p = px[y][27 * 256 + x]
            c.p[y][x] = '%02x%02x%02x' % p[:3] if p[3] == 255 else None
    return c


def gif_impact():
    """impact at 3x: on the plain arena floor (left) and on Eric's white armour (right)"""
    S = 3
    er = eric27()
    W_, H_ = 980, 520
    # Eric flipped; chest (flipped texel ~(127, 168)) placed at (720, 360)
    ex = 720 - (255 - 127) * S
    ey = 360 - 168 * S
    seq = []
    durs = [4, 6, 6, 7, 8, 9]
    for rep in range(2):
        for i in range(-1, 6):
            img = rgb_canvas(W_, H_, FLOOR)
            paste(img, er, ex, ey, S, flip=True)
            if i >= 0:
                fr = cell(IMP, i, 96, 96)
                paste(img, fr, 230 - 48 * S, 260 - 48 * S, S)
                paste(img, fr, 720 - 48 * S, 330 - 48 * S, S)
            seq.append((img, 30 if i < 0 else durs[i]))
    write_gif(OUT + 'uppercut_impact_3x.gif', [f for f, _ in seq], [d for _, d in seq])


def load_frame(path, i, fw, fh):
    w, h, px = read_png(path)
    c = Canvas(fw, fh)
    for y in range(fh):
        for x in range(fw):
            p = px[y][i * fw + x]
            c.p[y][x] = '%02x%02x%02x' % p[:3] if p[3] == 255 else None
    return c


def bbox(c):
    xs = [x for y in range(c.h) for x in range(c.w) if c.p[y][x]]
    ys = [y for y in range(c.h) for x in range(c.w) if c.p[y][x]]
    return min(xs), min(ys), max(xs), max(ys)


def gif_daze():
    """daze stars at 3x above a small boss (Mason), Eric (large) and the phase-2 mech (huge)"""
    S = 3
    mason = from_png(PROJ + 'Assets/Characters/Mason/mason.png')
    er = eric27()
    mw, mh, _ = read_png(PROJ + 'Assets/Characters/GreysonMech/greyson_mech_sheet.png')
    mech = load_frame(PROJ + 'Assets/Characters/GreysonMech/greyson_mech_sheet.png', 0, mw // 23, mh)
    bosses = [(mason, False), (er, True), (mech, False)]
    GAP = 60
    widths = []
    heights = []
    for boss, flip in bosses:
        x0, y0, x1, y1 = bbox(boss)
        widths.append((x1 - x0 + 1) * S)
        heights.append((y1 - y0 + 1) * S)
    W_ = sum(widths) + GAP * (len(bosses) + 1)
    H_ = max(heights) + 24 * S + 60
    frames = []
    for f in range(12):
        img = rgb_canvas(W_, H_, FLOOR)
        x_cursor = GAP
        for (boss, flip), bw in zip(bosses, widths):
            x0, y0, x1, y1 = bbox(boss)
            oy = H_ - 20 - (y1 + 1) * S
            ox = x_cursor - ((boss.w - 1 - x1) if flip else x0) * S
            paste(img, boss, ox, oy, S, flip=flip)
            # head top: first row that has hair/head pixels near the horizontal centre of the body
            cx = x_cursor + bw // 2
            paste(img, cell(DZ, f % 6, 48, 24), cx - 24 * S, oy + y0 * S - 22 * S + 6, S)
            x_cursor += bw + GAP
        frames.append(img)
    write_gif(OUT + 'daze_stars_3x.gif', frames, [10] * 12)


# ---------------------------------------------------------------- mockups
def ensure_arena_raw():
    """Render Scenes/Core/ArenaScene.tscn with Godot's movie writer (writes nothing into the project),
    decode the last frame twice and cache it as raw RGB (the pure-python decoder is occasionally flaky)."""
    raw = work('arena_rgb.raw')
    if os.path.exists(raw):
        return raw
    movie = work('arena_render/arena.png')
    os.makedirs(os.path.dirname(movie), exist_ok=True)
    subprocess.run([GODOT, '--path', PROJ.rstrip('/'), '--write-movie', movie, '--fixed-fps', '30',
                    '--quit-after', '3', 'res://Scenes/Core/ArenaScene.tscn'], capture_output=True, text=True)
    last = work('arena_render/arena00000002.png')

    def decode():
        for _ in range(6):
            try:
                w, h, px = read_png(last)
                return bytes(v for row in px for p in row for v in p[:3])
            except Exception:
                pass
        raise SystemExit('could not decode ' + last)
    a, b = decode(), decode()
    assert a == b, 'arena decode mismatch'
    open(raw, 'wb').write(a)
    return raw


def arena_world():
    raw = open(ensure_arena_raw(), 'rb').read()      # verified decode of the Godot render
    img = [[(raw[(y * 1920 + x) * 3], raw[(y * 1920 + x) * 3 + 1], raw[(y * 1920 + x) * 3 + 2])
            for x in range(1920)] for y in range(1080)]
    # remove the default-position player (world 949..970, 876..925) -> floor colour
    for y in range(870, 932):
        for x in range(940, 980):
            img[y][x] = FLOOR
    # lift out the HUD hearts (screen space, the red pixels only) so they are not zoomed with the world
    hearts = {}
    for y in range(990, 1075):
        for x in range(0, 300):
            p = img[y][x]
            if p[0] > 120 and p[1] < 90:
                hearts[(x, y)] = p
                img[y][x] = (0, 0, 0) if y > 1010 else img[y][x - 1 if x > 0 else x]
    return img, hearts


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


def world_to_screen(x, y, cx, cy, z=1.5, W=1920, H=1080):
    return int(round((x - (cx - W / (2 * z))) * z)), int(round((y - (cy - H / (2 * z))) * z))


EFEET = 560          # Eric's feet line (world y)
PX, PY = 996, 564    # player sprite centre (feet bottom at PY + 26 = 590, a step in front of Eric)
CAMX, CAMY = 1010, 430
IMPACT_OFFSET = (40, -40)   # impact centre relative to the fist tip (world px): pushed onto the boss


def compose_mockup(kind):
    world, hearts = arena_world()
    er = eric27()
    E_top = EFEET - 192 * 3
    E_left = 1000 - (255 - 165) * 3       # flipped: body spans texel 90..181
    paste(world, er, E_left, E_top, 3, flip=True)
    head_x = E_left + (255 - 127) * 3
    head_top = E_top + 118 * 3
    if kind == 'charge':
        paste(world, cell(DZ, 1, 48, 24), head_x - 72, head_top - 60, 3)
    fidx = 2 if kind == 'charge' else 5
    if kind == 'connect':
        # impact on the boss, centred just above the rising fist (frame 5 fist top-centre = texel (27, 14))
        ix, iy = PX + (27 - 24) * 2 + IMPACT_OFFSET[0], PY - 96 + 14 * 2 + IMPACT_OFFSET[1]
        paste(world, cell(IMP, 1, 96, 96), ix - 144, iy - 144, 3)
    # the player is drawn above the impact so he stays readable
    paste(world, cell(UP, fidx, 48, 64), PX - 48, PY - 96, 2)
    img = zoom_view(world, CAMX, CAMY)
    for (x, y), p in hearts.items():
        img[y][x] = p
    sx, sy = world_to_screen(PX, PY, CAMX, CAMY)
    feet_y = world_to_screen(PX, PY + 26, CAMX, CAMY)[1]
    meter_x = sx - 108
    meter_y = feet_y + 36
    if kind == 'charge':
        paste(img, cell(UI['qte_key_q'], 1, 32, 32), meter_x - 96 - 18, meter_y - 24, 3)
        paste(img, cell(UI['qte_key_w'], 0, 32, 32), meter_x + 216 + 18, meter_y - 24, 3)
        paste(img, UI['qte_meter_frame'], meter_x, meter_y, 3)
        fill = UI['qte_meter_fill']
        half = Canvas(fill.w // 2, fill.h)
        for y in range(fill.h):
            half.p[y] = fill.p[y][:fill.w // 2]
        paste(img, half, meter_x + 21, meter_y + 15, 3)
        paste(img, cell(UI['qte_mash_text'], 1, 64, 20), sx - 96, meter_y + 54, 3)
    else:
        paste(img, cell(UI['qte_meter_full'], 0, 72, 16), meter_x, meter_y, 3)
        paste(img, cell(UI['qte_full_text'], 1, 64, 20), sx - 96, meter_y + 54, 3)
    name = 'mockup_a_charge.png' if kind == 'charge' else 'mockup_b_uppercut_connects.png'
    write_png(OUT + name, 1920, 1080, to_rgba(img))
    return name


# ---------------------------------------------------------------- 6x close-up strip
def closeup_strip():
    S = 6
    cells = [('ORIGINAL IDLE', std_in_48(3, 0)), ('ORIGINAL PUNCH', std_in_48(3, 8))]
    names = ['0 CHARGE A', '1 CHARGE B', '2 CHARGE C', '3 LAUNCH', '4 RISE 1', '5 RISE 2', '6 RISE 3',
             '7 APEX', '8 FALL', '9 LAND']
    for i, n in enumerate(names):
        cells.append((n, cell(UP, i, 48, 64)))
    GAP = 18
    W_ = len(cells) * (48 * S + GAP) + GAP
    H_ = 64 * S + 80
    img = rgb_canvas(W_, H_, (40, 42, 54))
    for k, (label, c) in enumerate(cells):
        x0 = GAP + k * (48 * S + GAP)
        for y in range(64 * S):
            for x in range(48 * S):
                img[20 + y][x0 + x] = FLOOR if k >= 2 else (120, 150, 100)
        # ground line (feet bottom row y=60 -> bottom edge 61)
        gy = 20 + 61 * S
        for x in range(48 * S):
            if (x // S) % 2 == 0:
                img[gy][x0 + x] = (70, 100, 50)
        paste(img, c, x0, 20, S)
        text(img, label, x0 + 4, 20 + 64 * S + 16, 4, (230, 230, 240))
    write_png(OUT + 'uppercut_frames_closeup_6x.png', W_, H_, to_rgba(img))


if __name__ == '__main__':
    which = sys.argv[1:] or ['gif', 'impact', 'daze', 'mock', 'strip']
    if 'gif' in which:
        gif_full_move()
        print('full move gif')
    if 'impact' in which:
        gif_impact()
        print('impact gif')
    if 'daze' in which:
        gif_daze()
        print('daze gif')
    if 'mock' in which:
        print(compose_mockup('charge'), compose_mockup('connect'))
    if 'strip' in which:
        closeup_strip()
        print('strip')
