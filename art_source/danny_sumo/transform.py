"""Danny's evolution: the beat list, the FireRed-style silhouette flash, and
the preview renders (GIFs, contact sheet, arena mockups).

Shared staging contract
-----------------------
Both forms are composited into the SAME 176x144 frame so they can alternate in
place with one anchor:
    anchor          bottom-centre of the frame, (88, 144) in frame pixels
    small form      its own 64x64 frame pasted at (+56, +80) inside the big one
                    (centre 87.5, feet on y = 143)
    big form        fills the 176x144 frame, feet on y = 143
Both render at scale 3, like Carter and beast Bixby.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pngio import write_png, upscale, read_png       # noqa: E402
from gifio import write_gif                          # noqa: E402
from rig import to_pix                                # noqa: E402
import danny_small as SM                              # noqa: E402
import danny_honda as SU                               # noqa: E402

BW, BH = 176, 144            # the shared transformation frame
SMALL_OX, SMALL_OY = 56, 80  # where the 64x64 small form sits inside it

WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


# --------------------------------------------------------------- compositing
def big_frame(pix, ox=0, oy=0, W=BW, H=BH):
    out = [[CLEAR] * W for _ in range(H)]
    for y, row in enumerate(pix):
        ty = y + oy
        if not (0 <= ty < H):
            continue
        for x, p in enumerate(row):
            tx = x + ox
            if p[3] and 0 <= tx < W:
                out[ty][tx] = p
    return out


def small_in_big(key, dx=0, dy=0):
    return big_frame(to_pix(SM.build(key)), SMALL_OX + dx, SMALL_OY + dy)


def sumo_in_big(pose, dx=0, dy=0):
    return big_frame(to_pix(SU.build(pose)), dx, dy)


def silhouette(frame, colour=WHITE):
    return [[colour if p[3] else CLEAR for p in row] for row in frame]


def drain(frame, t):
    """Push every colour toward flat white; t=0 untouched, t=1 silhouette."""
    out = []
    for row in frame:
        r = []
        for p in row:
            if not p[3]:
                r.append(CLEAR)
            else:
                r.append((int(p[0] + (255 - p[0]) * t),
                          int(p[1] + (255 - p[1]) * t),
                          int(p[2] + (255 - p[2]) * t), 255))
        out.append(r)
    return out


# ============================================================== THE BEAT LIST
# (label, frame-builder, duration in ms).  Timings are the proposal; the coder
# can read them straight off this table.
FLASH_HOLDS = [340, 300, 260, 220, 180, 145, 115, 90, 70, 60, 55, 50, 50, 50]
# 14 holds => 13 swaps.  Starts on the SMALL form, lands on the BIG one.


def beats():
    """The approved beat list, now driven by the PRODUCTION sheets.
    Durations are the ones baked into sheets.py, and the pre-flash beats still
    total exactly what was approved -- the extra in-between frames subdivide
    those beats rather than lengthening them."""
    B = []
    # 1. walk-in: danny_walk looped twice, 8 frames at 160 ms
    walk = ['walk_a', 'walk_pass', 'walk_b', 'walk_pass2']
    for i in range(8):
        B.append(('walk %d' % i, small_in_big(walk[i % 4], dx=-72 + i * 9),
                  160, dict(stage='ring')))
    # 2. arrives: hold danny_walk frame 1 (both feet down, arms at his sides)
    B.append(('arrive', small_in_big('walk_pass'), 500, dict(stage='ring')))
    # 3-4. danny_grip: reach, grip, then strain ping-ponging
    B.append(('grip 0 reach', small_in_big('reach'), 140, dict(stage='ring')))
    B.append(('grip 1 grip', small_in_big('grip'), 280, dict(stage='ring')))
    for i, k in enumerate(('strain', 'grip', 'strain')):
        B.append(('grip 2 %s' % k, small_in_big(k), 90, dict(stage='ring')))
    # 5. danny_tear
    B.append(('tear 0', small_in_big('tear'), 200, dict(stage='ring', shake=2)))
    B.append(('tear 1', small_in_big('tear_wide'), 60, dict(stage='ring',
                                                            shake=2)))
    B.append(('tear 2', small_in_big('shirt_off'), 340, dict(stage='ring')))
    # 6. danny_flex
    B.append(('flex 0', small_in_big('flex_rise'), 120, dict(stage='ring')))
    B.append(('flex 1', small_in_big('flex'), 300, dict(stage='ring')))
    B.append(('flex 2', small_in_big('flex_in'), 300, dict(stage='ring')))
    B.append(('flex 3', small_in_big('flex_out'), 300, dict(stage='ring')))
    # 7. the crowd goes quiet, the arena drops away, the colour drains
    base = small_in_big('flex_in')          # = danny_sumo_evolve frame 0
    for i, t in enumerate((0.35, 0.7, 1.0)):
        B.append(('drain %d' % i, drain(base, t), 110,
                  dict(stage='dark', dim=(i + 1) / 3.0)))
    # 8. THE FLASH: evolve frames 0 and 1 as flat white, accelerating
    small_sil = silhouette(base)
    big_sil = silhouette(sumo_in_big('awake'))
    for i, ms in enumerate(FLASH_HOLDS):
        B.append(('flash %d' % i, small_sil if i % 2 == 0 else big_sil, ms,
                  dict(stage='dark', dim=1.0, burst=min(1.0, 0.25 + i * 0.09))))
    # 9. white-out, then he lands
    B.append(('white out', silhouette(sumo_in_big('awake')), 120,
              dict(stage='white')))
    B.append(('land', sumo_in_big('land', dy=2), 160,
              dict(stage='ring', shake=4, dust=1.0)))
    B.append(('settle', sumo_in_big('awake'), 400, dict(stage='ring', dust=0.5)))
    B.append(('idle', sumo_in_big('idle'), 700, dict(stage='ring')))
    return B


def flash_beats():
    """Just the flash, for the second GIF."""
    B = []
    base = small_in_big('flex_in')
    for i, t in enumerate((0.35, 0.7, 1.0)):
        B.append(('drain %d' % i, drain(base, t), 110,
                  dict(stage='dark', dim=(i + 1) / 3.0)))
    small_sil = silhouette(small_in_big('flex_in'))
    big_sil = silhouette(sumo_in_big('awake'))
    for i, ms in enumerate(FLASH_HOLDS):
        B.append(('flash %d' % i, small_sil if i % 2 == 0 else big_sil, ms,
                  dict(stage='dark', dim=1.0, burst=min(1.0, 0.25 + i * 0.09))))
    B.append(('white out', silhouette(sumo_in_big('awake')), 120,
              dict(stage='white')))
    B.append(('land', sumo_in_big('land', dy=2), 160,
              dict(stage='ring', shake=4, dust=1.0)))
    B.append(('idle', sumo_in_big('idle'), 900, dict(stage='ring')))
    return B


# ==================================================================== STAGE
SW, SH = 344, 208            # native-pixel stage for the GIFs
FLOOR_Y = 184                # the sprite's feet land here
FLOOR = (136, 179, 100, 255)
FLOOR_D = (108, 148, 78, 255)
ROPE = (255, 255, 255, 255)
CROWD = (34, 32, 52, 255)
CROWD_HI = (69, 40, 60, 255)


def make_stage(dim=0.0, white=False):
    px = [[(0, 0, 0, 255)] * SW for _ in range(SH)]
    for y in range(SH):
        for x in range(SW):
            if y < 34:
                c = CROWD_HI if ((x * 7 + y * 13) % 9 == 0) else CROWD
            elif y < 40:
                c = ROPE if y in (35, 38) else (0, 0, 0, 255)
            else:
                c = FLOOR_D if ((y - 40) // 14 + x // 14) % 2 == 0 else FLOOR
            px[y][x] = c
    if white:
        return [[WHITE] * SW for _ in range(SH)]
    if dim > 0:
        k = 1.0 - 0.88 * dim
        px = [[(int(c[0] * k), int(c[1] * k), int(c[2] * k), 255) for c in row]
              for row in px]
    return px


def draw_burst(px, strength, cx, cy):
    """Radial white speed lines behind the evolving sprite."""
    import math
    n = 16
    for i in range(n):
        a = (i + 0.5) * 2 * math.pi / n
        r0 = 26 + (1.0 - strength) * 40
        r1 = r0 + 30 + strength * 70
        v = int(90 + 165 * strength)
        col = (v, v, v, 255)
        r = r0
        while r < r1:
            x = int(cx + math.cos(a) * r)
            y = int(cy + math.sin(a) * r * 0.85)
            if 0 <= x < SW and 0 <= y < SH:
                px[y][x] = col
            r += 1.0


def draw_dust(px, strength, cx):
    import math
    for i in range(22):
        a = math.pi * (i / 21.0)
        r = 28 + 62 * strength
        x = int(cx + math.cos(math.pi + a) * r)
        y = int(FLOOR_Y - 2 - math.sin(a) * 14 * strength)
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                X, Y = x + dx, y + dy
                if 0 <= X < SW and 0 <= Y < SH:
                    px[Y][X] = (214, 190, 150, 255)


def blit(dst, src, ox, oy):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        ty = y + oy
        if not (0 <= ty < H):
            continue
        for x, p in enumerate(row):
            tx = x + ox
            if p[3] and 0 <= tx < W:
                dst[ty][tx] = p


PLAYER_SHEET = os.path.normpath(os.path.join(
    HERE, '..', '..', 'Assets', 'Characters', 'MainPlayer',
    'player_4dir_sheet.png'))


def player_pix(col=0, row=0):
    w, h, p = read_png(PLAYER_SHEET)
    return [[p[row * 32 + y][col * 32 + x] for x in range(32)] for y in range(32)]


def compose(beat, show_player=True):
    label, frame, ms, opt = beat
    stage = opt.get('stage', 'ring')
    px = make_stage(dim=opt.get('dim', 0.0), white=(stage == 'white'))
    cx = SW // 2
    if opt.get('burst'):
        draw_burst(px, opt['burst'], cx, FLOOR_Y - 46)
    if show_player and stage == 'ring':
        # the player, 32x32 at 2x, standing where the arena puts him
        pl = player_pix(0, 0)
        pl2 = [[pl[y // 2][x // 2] for x in range(64)] for y in range(64)]
        blit(px, pl2, 40, FLOOR_Y - 58)
    sx = opt.get('shake', 0)
    ox = cx - BW // 2 + (sx if sx else 0)
    oy = FLOOR_Y - (BH - 1) - 1
    blit(px, frame, ox, oy)
    if opt.get('dust'):
        draw_dust(px, opt['dust'], cx)
    return px


def render_gif(path, beat_list, scale=2, show_player=True):
    frames, durs = [], []
    for b in beat_list:
        px = compose(b, show_player)
        w2, h2, p2 = upscale(SW, SH, px, scale)
        frames.append(p2)
        durs.append(b[2])
    write_gif(path, frames, durs, bg=(0, 0, 0))
    print('  ', os.path.basename(path), len(frames), 'frames',
          sum(durs), 'ms', os.path.getsize(path) // 1024, 'KB')
    return path
