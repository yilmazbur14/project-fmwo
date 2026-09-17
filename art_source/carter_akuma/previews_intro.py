"""Previews for Carter's entrance: the animated GIFs, a 6x contact sheet and a
1920x1080 arena mockup of the mark-flare beat.

    python previews_intro.py <scratch_dir>
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, blank, paste, crop
from gifio import write_gif

A = r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters"
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else '.'
W = H = 96

# ms per frame, matching the timings quoted in the report
INTRO_MS = [140, 130, 130, 120, 120,        # materialise
            110, 100, 150, 110,             # mark flare (loops)
            70, 70, 70, 70, 100,            # turn
            240, 90, 600]                   # settle, last one holds
MARK_MS = [110, 90, 90, 150, 100, 110]

BG = (34, 28, 38, 255)
GRID = (58, 50, 66, 255)


def frames_of(path, fw, fh):
    w, h, px = read_png(path)
    n = w // fw
    return [crop(px, i * fw, 0, fw, fh) for i in range(n)], n


def flatten(f, bg=BG):
    return [[(p if p[3] else bg) for p in row] for row in f]


# ---------------------------------------------------------------- GIFs

intro, n = frames_of(A + '/Carter/carter_intro.png', W, H)
SC = 4
gf = [scale(flatten(f), SC) for f in intro]
write_gif(os.path.join(SCRATCH, 'carter_intro.gif'), gf,
          [max(2, round(m / 10.0)) for m in INTRO_MS])
print('carter_intro.gif        %dx%d  %d frames' % (W * SC, H * SC, n))

# the mark loop on its own, over a swatch of the gi navy it is painted on
gw, gh, gpx = read_png(A + '/Carter/carter_mark_glow.png')
ng = len(MARK_MS)
fw_m = gw // ng
mark = [crop(gpx, i * fw_m, 0, fw_m, gh) for i in range(ng)]
CLOTH = (29, 43, 96, 255)
mg = [scale([[(p if p[3] else CLOTH) for p in row] for row in f], 6) for f in mark]
write_gif(os.path.join(SCRATCH, 'carter_mark_loop.gif'), mg,
          [max(2, round(m / 10.0)) for m in MARK_MS])
print('carter_mark_loop.gif    %dx%d  %d frames' % (fw_m * 6, gh * 6, ng))

# ---------------------------------------------------------------- contact sheet

COLS, S, PAD, GAP = 6, 6, 14, 10
rows = (n + COLS - 1) // COLS
cw, ch = W * S, H * S
tw = PAD * 2 + COLS * cw + (COLS - 1) * GAP
th = PAD * 2 + rows * ch + (rows - 1) * GAP
sheet = blank(tw, th, BG)
for i, f in enumerate(intro):
    r, c = divmod(i, COLS)
    x0 = PAD + c * (cw + GAP)
    y0 = PAD + r * (ch + GAP)
    for y in range(ch):
        for x in range(cw):
            sheet[y0 + y][x0 + x] = GRID if (x < 2 or y < 2 or x >= cw - 2
                                             or y >= ch - 2) else BG
    paste(sheet, scale(f, S), x0, y0)
    # frame index as a run of ticks along the top edge
    for t in range(i + 1):
        tx = x0 + 5 + t * 5
        if tx + 3 < x0 + cw:
            for dx in range(3):
                for dy in range(4):
                    sheet[y0 + 4 + dy][tx + dx] = (255, 210, 120, 255)
write_png(os.path.join(SCRATCH, 'contact_intro_x6.png'), tw, th, sheet)
print('contact_intro_x6.png    %dx%d  %d frames at %dx' % (tw, th, n, S))

# ---------------------------------------------------------------- arena mockup

aw, ah, arena = read_png(os.path.join(SCRATCH, 'arena', 'frame00000002.png'))
mock = [row[:] for row in arena]

pw, ph, psheet = read_png(A + '/MainPlayer/player_4dir_sheet.png')
player = crop(psheet, 0, 0, 32, 32)

FLOOR = 880                      # a row well inside the green ring
CX = 700                         # left edge of Carter's 96x96 frame, at 3x
TOP = FLOOR - H * 3


def add(dst, src, ox, oy, s=3, mul=1.0):
    """additive composite, the way an Add-blend CanvasItem would draw it"""
    for y in range(len(src)):
        for x in range(len(src[0])):
            p = src[y][x]
            if not p[3]:
                continue
            for sy in range(s):
                for sx in range(s):
                    Y, X = oy + y * s + sy, ox + x * s + sx
                    if 0 <= Y < ah and 0 <= X < aw:
                        d = dst[Y][X]
                        dst[Y][X] = (min(255, int(d[0] + p[0] * mul)),
                                     min(255, int(d[1] + p[1] * mul)),
                                     min(255, int(d[2] + p[2] * mul)), 255)


# every layer the fight would stack, in draw order: ambient aura behind him,
# the baked peak frame, then the additive mark held back to a top-up.  At full
# strength the overlay doubles a flare that is already baked in and the sigil
# washes out to a white blob, so in the fight it wants modulate.a near 0.3.
_, _, apx = read_png(A + '/Carter/carter_aura.png')
paste(mock, scale(crop(apx, 3 * W, 0, W, H), 3), CX, TOP)
paste(mock, scale(intro[7], 3), CX, TOP)

fw2, fh2 = fw_m, gh
peak = mark[3]
MARK_OFF = (13, 23)
mx, my = CX + MARK_OFF[0] * 3, TOP + MARK_OFF[1] * 3
add(mock, peak, mx, my, mul=0.30)

# the ground flash under him
flw, flh, flash = read_png(A + '/Carter/carter_intro_flash.png')
FLASH_OFF = (-24, 66)
add(mock, flash, CX + FLASH_OFF[0] * 3, TOP + FLASH_OFF[1] * 3, mul=0.65)

# the player at 2x, feet on the same floor row, for scale
paste(mock, scale(player, 2), 1180, FLOOR - 29 * 2)

write_png(os.path.join(SCRATCH, 'arena_mockup_flare.png'), aw, ah, mock)
print('arena_mockup_flare.png  %dx%d' % (aw, ah))
half = [[mock[y][x] for x in range(0, aw, 2)] for y in range(0, ah, 2)]
write_png(os.path.join(SCRATCH, 'arena_mockup_flare_half.png'),
          len(half[0]), len(half), half)
