"""Mock screenshots of a Flyby pass, composited on real arena captures in the fight's draw order
(the plan's section 6):

  arena (mat, crowd)                                   the capture without HUD
  floor layer, sort 101: projection / burn / die-down  bixby_inferno_flood.png tiles, laid exactly as
                                                       BixbyInfernoFloodScript._lay_final lays them
  Bixby on the pass, sort 114                          a Flyby frame at 3x, anchor at screen y 300
  curtain, sort 114.5                                  the curtain sprite tiled down from the exit row
  rim, sort 115                                        the 6 px gold line on the safe column's edge
  ropes, z 1                                           lifted from the capture, drawn over all of it
  player, HUD                                          the player from the capture; the boss bar block
                                                       at 0.3 alpha (inferno_hud_fade_alpha)

Reads the live flood sheet and the captures; writes only where it is told (the build script's guard).
"""
import fb_common  # noqa: F401
import os

from PIL import Image

import fb_common as C

CAP = os.path.join(r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project',
                   'a7fc2846-afef-472d-979b-e17143793a0f', 'scratchpad', 'liam_elements', 'cap')
FLOOD = os.path.join(C.BIXBY_ASSETS, 'bixby_inferno_flood.png')

# BixbyInfernoArtLayout / the plan
AREA = (105, 105, 1710, 870)                 # INFERNO_AREA: x, y, w, h
GRID = (10, 10)
TILE = (57, 29)
FRAME = (57, 41)
SMOULDER, BURN, DIE = [0, 1], [4, 5, 6, 7], [8, 9, 10]
FRAME_TIME, WARN_FRAME_TIME, FAINT_ALPHA = 0.11, 0.06, 0.45
DIE_TIME = 0.45
RIM_COLOUR = (255, 217, 89)                  # Color(1.0, 0.85, 0.35)
RIM_WIDTH = 6
SPEED, SAFE_W, BURN_TIME, CURTAIN_PX = 540.0, 204.0, 0.8, 96
BOSS_HUD_BOX = (700, 0, 1220, 190)           # the boss bar, its plate and the Break gauge
HUD_FADE = 0.3


def load(name):
    return Image.open(os.path.join(CAP, name)).convert('RGBA')


def flood_frames():
    sheet = Image.open(FLOOD).convert('RGBA')
    n = sheet.width // FRAME[0]
    return [sheet.crop((i * FRAME[0], 0, (i + 1) * FRAME[0], FRAME[1])).resize((FRAME[0] * 3, FRAME[1] * 3),
                                                                             Image.NEAREST) for i in range(n)]


def pass_geometry(direction, width=SAFE_W):
    x0, y0, w, h = AREA
    x1 = x0 + w
    if direction > 0:
        return dict(entry=x0, safe_edge=x1 - width, burnable=(x0, x1 - width), safe=(x1 - width, x1))
    return dict(entry=x1, safe_edge=x0 + width, burnable=(x0 + width, x1), safe=(x0, x0 + width))


def spans(direction, t_since_T):
    """The four spans (lo, hi) at time t after the front starts (the plan's section 4)."""
    g = pass_geometry(direction)
    lo, hi = g['burnable']
    xe = g['entry']
    mouth = xe + direction * SPEED * t_since_T

    def clamp(v):
        return max(lo, min(hi, v))

    def order(a, b):
        return (min(a, b), max(a, b))
    front = clamp(mouth)
    if t_since_T < 0:
        return dict(front=front, mouth=mouth, projection=(lo, hi), curtain=None, hurting=None, dying=None)
    xs = g['safe_edge']
    proj = order(front, xs)
    cur = order(mouth - direction * CURTAIN_PX, mouth)
    cur = (max(cur[0], lo), min(cur[1], hi))
    hurt_back = xe + direction * SPEED * (t_since_T - BURN_TIME)
    hurt = order(clamp(hurt_back), front)
    die_back = xe + direction * SPEED * (t_since_T - BURN_TIME - DIE_TIME)
    die = order(clamp(die_back), clamp(hurt_back))
    return dict(front=front, mouth=mouth, projection=proj, curtain=cur, hurting=hurt, dying=die)


def lay_floor(canvas, span, frame_for, alpha=1.0, flip=False):
    """Tiles on every grid bed meeting the span, each clipped to the span's x and the floor's y."""
    if span is None or span[1] - span[0] <= 0:
        return
    frames = flood_frames()
    x0, y0, w, h = AREA
    bw, bh = TILE[0] * 3, TILE[1] * 3
    rise = (FRAME[1] - TILE[1]) * 3
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    i = 0
    for row in range(GRID[1]):
        for col in range(GRID[0]):
            cx, cy = x0 + col * bw, y0 + row * bh
            if cx + bw <= span[0] or cx >= span[1]:
                continue
            f = frames[frame_for(i, cx + bw / 2.0)]
            layer.alpha_composite(f, (int(cx), int(cy - rise)))
            i += 1
    # clip to the span and the floor
    mask = Image.new('L', canvas.size, 0)
    mask.paste(255, (int(round(span[0])), y0, int(round(span[1])), y0 + h))
    if alpha < 1.0:
        a = layer.split()[3].point(lambda v: int(v * alpha))
        layer.putalpha(a)
    clipped = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    clipped.paste(layer, (0, 0), mask)
    canvas.alpha_composite(clipped)


def rope_overlay(arena):
    """The ropes and corner posts (z 1) lifted from the capture: pure black and white along the four
    rope bands, the gold posts in the corners."""
    w, h = arena.size
    px = arena.load()
    out = Image.new('RGBA', arena.size, (0, 0, 0, 0))
    op = out.load()
    bands = [(85, 88, 1835, 116), (85, 958, 1835, 992), (85, 88, 121, 992), (1799, 88, 1835, 992)]
    posts = [(84, 66, 140, 176), (1780, 66, 1836, 176), (84, 924, 140, 994), (1780, 924, 1836, 994)]
    for (x0, y0, x1, y1) in bands:
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = px[x, y]
                if c[:3] in ((0, 0, 0), (255, 255, 255)):
                    op[x, y] = c
    for (x0, y0, x1, y1) in posts:
        for y in range(y0, y1):
            for x in range(x0, x1):
                r, g, b, a = px[x, y]
                gold = r > 120 and g > 90 and b < 110 and r > b + 50 and g > b + 30
                if gold or (r, g, b) in ((0, 0, 0), (255, 255, 255)):
                    op[x, y] = (r, g, b, 255)
    return out


def hud_layers():
    """(boss HUD at full strength, player HUD): the HUD's own pixels, lifted as capture-with-HUD minus
    capture-without."""
    a, b = load('arena_hud.png'), load('arena_nohud.png')
    pa, pb = a.load(), b.load()
    boss = Image.new('RGBA', a.size, (0, 0, 0, 0))
    player = Image.new('RGBA', a.size, (0, 0, 0, 0))
    bp, pp = boss.load(), player.load()
    bx0, by0, bx1, by1 = BOSS_HUD_BOX
    for y in range(a.height):
        for x in range(a.width):
            if pa[x, y] != pb[x, y]:
                if bx0 <= x < bx1 and by0 <= y < by1:
                    bp[x, y] = pa[x, y]
                else:
                    pp[x, y] = pa[x, y]
    return boss, player


def player_sprite():
    """The player lifted from the capture (with player minus without), and where he stood."""
    a, b = load('arena_player.png'), load('arena_nohud.png')
    pa, pb = a.load(), b.load()
    box = (880, 780, 1040, 920)
    sp = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    sp_px = sp.load()
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            if pa[x, y] != pb[x, y]:
                sp_px[x - box[0], y - box[1]] = pa[x, y]
    return sp, (box[0], box[1])


def place_bixby(canvas, frame_img, lead_x, mouth_x, direction=1):
    """Draw a frame (192x160, drawn facing right) with its lead exit's column on screen x mouth_x."""
    big = frame_img.resize((frame_img.width * 3, frame_img.height * 3), Image.NEAREST)
    if direction < 0:
        big = big.transpose(Image.FLIP_LEFT_RIGHT)
    exit_offset = (lead_x - 96) * 3 * direction
    ax = mouth_x - exit_offset
    ox = int(round(ax - (96 * 3 if direction > 0 else (192 - 96) * 3)))
    oy = int(round(300 - 151 * 3))
    tmp = Image.new('RGBA', (canvas.width + 2000, canvas.height + 2000), (0, 0, 0, 0))
    tmp.alpha_composite(big, (ox + 1000, oy + 1000))
    canvas.alpha_composite(tmp.crop((1000, 1000, 1000 + canvas.width, 1000 + canvas.height)))


def lay_curtain(canvas, curtain_frames, span, exit_row, t_frame, direction=1):
    if span is None or span[1] - span[0] <= 0:
        return
    f = curtain_frames[t_frame % len(curtain_frames)]
    big = f.resize((f.width * 3, f.height * 3), Image.NEAREST)
    if direction < 0:
        big = big.transpose(Image.FLIP_LEFT_RIGHT)
    top = int(round(300 + 3 * (exit_row - 151)))
    x0, y0, w, h = AREA
    col = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    # the curtain's leading edge rides the mouth; it is the band [mouth - 96, mouth] for dir +1
    lead = span[1] if direction > 0 else span[0]
    left = int(round(lead - big.width)) if direction > 0 else int(round(lead))
    y = top
    while y < y0 + h:
        col.paste(big, (left, y), big)
        y += big.height
    mask = Image.new('L', canvas.size, 0)
    mask.paste(255, (int(round(span[0])), top, int(round(span[1])), y0 + h))
    clipped = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    clipped.paste(col, (0, 0), mask)
    canvas.alpha_composite(clipped)


def draw_rim(canvas, x, alpha=1.0):
    x0, y0, w, h = AREA
    rim = Image.new('RGBA', (RIM_WIDTH, h), RIM_COLOUR + (int(255 * alpha),))
    canvas.alpha_composite(rim, (int(round(x - RIM_WIDTH / 2)), y0))


def compose(frame_img, lead_x, exit_row, curtain_frames, direction, t_since_T, strong, clock_frame,
            player_at=None):
    """A full 1920x1080 mock at time t_since_T after the front starts (negative: before)."""
    arena = load('arena_nohud.png')
    canvas = arena.copy()
    sp = spans(direction, t_since_T)
    g = pass_geometry(direction)

    # floor layer
    if sp['projection'] is not None:
        ft = WARN_FRAME_TIME if strong else FRAME_TIME
        lay_floor(canvas, sp['projection'], lambda i, cx: SMOULDER[(clock_frame + i) % 2], 1.0 if strong else FAINT_ALPHA)
    if sp['hurting'] is not None:
        lay_floor(canvas, sp['hurting'], lambda i, cx: BURN[(clock_frame + i) % 4])
    if sp['dying'] is not None:
        def die_frame(i, cx):
            since = t_since_T - BURN_TIME - (cx - g['entry']) * direction / SPEED
            return DIE[max(0, min(2, int(since / (DIE_TIME / 3))))]
        lay_floor(canvas, sp['dying'], die_frame)
    # Bixby, the curtain over him, the rim over both
    place_bixby(canvas, frame_img, lead_x, sp['mouth'], direction)
    if sp['curtain'] is not None and curtain_frames:
        lay_curtain(canvas, curtain_frames, sp['curtain'], exit_row, clock_frame, direction)
    draw_rim(canvas, g['safe_edge'], 1.0 if strong or t_since_T >= 0 else 0.45)
    # ropes (z 1) over all of that
    canvas.alpha_composite(rope_overlay(arena))
    # the player, then the HUD
    if player_at is not None:
        ps, (px0, py0) = player_sprite()
        canvas.alpha_composite(ps, (int(player_at[0] - 79), int(player_at[1] - 110)))
    boss, player_hud = hud_layers()
    ba = boss.split()[3].point(lambda v: int(v * HUD_FADE))
    boss.putalpha(ba)
    canvas.alpha_composite(boss)
    canvas.alpha_composite(player_hud)
    return canvas
