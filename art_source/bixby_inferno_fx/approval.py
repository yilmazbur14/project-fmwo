"""The Inferno approval stills, composed at the game's 1920x1080 and reduced to 1280x720 (every 3x texel
lands on exactly 2x2 px, as the game draws it in a 1280x720 window). Writes into the scratchpad only.

  approval.png         the breath: the cone burning down the ring from the top-centre, both upper corners
                       safe, the player in the left one
  approval_inhale.png  the inhale before it: the faint smoulder over the cone, markers, falling fireballs,
                       an impact and a scorch, suction streaks pulling at the player

The arena is rebuilt from its own assets (ringside, crowd frame 4, mat) with the ropes, posts and bottom HUD
copied from a movie-writer capture of the Liam fight (fights/after/LiamBixby/f00000119.png). The capture's
top HUD predates the name plate, so the boss bar and plate are marked as translucent boxes where the
current HUD puts them (the code fades them while he perches). Bixby is the approved redesign's frame 2 as a
stand-in for the perch poses, hung at perch_point (row 40 on the rope). His side mouths sit lower and wider
than a perch pose's will, so short streams in the burst's own style bridge them to the burst's entries: the
perch art's mouth flames will do that job.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import burst  # noqa: E402
import edge  # noqa: E402
import fireball  # noqa: E402
import flood  # noqa: E402
import impact  # noqa: E402
import marker  # noqa: E402
import pal  # noqa: E402
import suction  # noqa: E402

ROOT = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
SCRATCH = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad'
CAPTURE = SCRATCH + '/fights/after/LiamBixby/f00000119.png'
OUT = SCRATCH + '/bixby_inferno_fx'
S = 3

# Arena geometry (px), from ArenaScene.tscn and BixbyInfernoArtLayout.gd
MAT_AT = (111, 114)
FLOOR = (114, 114, 1805, 967)              # the mat not under a rope
AREA = (105, 105, 1815, 975)               # INFERNO_AREA
APEX = (960, 145)                          # the cone's apex, as the code has it (45 px under the rope)
TAN = math.tan(math.radians(25.0))         # its edges run 25 degrees below horizontal (65 from vertical)
BIXBY_ORIGIN = (960 - 96 * S, 100 - 40 * S)   # frame 2 hung with row 40 on the rope (perch_point)
BAR = (720, 100, 1200, 154)
PLATE = (816, 3, 1104, 81)


def texels(im, scale=S):
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def paste(dst, im, x, y):
    """alpha_composite that clips at the canvas edges."""
    sx, sy = max(0, -x), max(0, -y)
    if sx >= im.width or sy >= im.height or x >= dst.width or y >= dst.height:
        return
    part = im.crop((sx, sy, min(im.width, dst.width - x + sx), min(im.height, dst.height - y + sy)))
    dst.alpha_composite(part, (max(0, x), max(0, y)))


def arena():
    cap = Image.open(CAPTURE).convert('RGBA')
    recon = Image.new('RGBA', (1920, 1080), (0, 0, 0, 255))
    recon.alpha_composite(texels(Image.open(ROOT + '/Assets/Environment/arena_ringside.png').convert('RGBA')))
    crowd = Image.open(ROOT + '/Assets/Environment/crowd_v2.png').convert('RGBA').crop((4 * 640, 0, 5 * 640, 40))
    recon.alpha_composite(texels(crowd), (0, 0))
    recon.alpha_composite(texels(Image.open(ROOT + '/Assets/Environment/arena_mat.png').convert('RGBA')), MAT_AT)
    cp, rp = cap.load(), recon.load()
    x0, y0, x1, y1 = FLOOR
    for y in range(1080):
        for x in range(1920):
            if x0 <= x <= x1 and y0 <= y <= y1:
                continue                                  # the floor: clean mat, no intro set dressing
            if 680 <= x <= 1240 and 30 <= y <= 92:
                continue                                  # the capture's stale boss HUD
            if cp[x, y] != rp[x, y]:
                rp[x, y] = cp[x, y]                       # ropes, posts, bottom HUD
    return recon, cap


def ropes_over(dst, cap):
    """The ropes are drawn at z 1, over the flood and over a perched Bixby: copy their bands back on top."""
    for box in ((92, 93, 1826, 114), (92, 93, 114, 988), (1806, 93, 1826, 988), (92, 968, 1826, 988)):
        dst.alpha_composite(cap.crop(box), (box[0], box[1]))


def in_cone(x, y):
    """Inside the breath: below both slanted edges (true 25 degrees, as the code clips) and inside the area."""
    return AREA[0] <= x < AREA[2] and y < AREA[3] and y >= APEX[1] + abs(x + 0.5 - APEX[0]) * TAN


def flood_layer(loop, alpha=1.0, step=0):
    """The flood's tiles laid over INFERNO_AREA on its 57x29 grid (one tile ahead per tile, 10 per row),
    clipped to the cone. The tongue rows of the top row rise over the rope line."""
    layer = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    tiles = [texels(pal.to_image(f)) for f in loop]
    cols = int(math.ceil((AREA[2] - AREA[0]) / (57 * S)))
    rows = int(math.ceil((AREA[3] - AREA[1]) / (29 * S)))
    for r in range(rows):
        for c in range(cols):
            paste(layer, tiles[(step + r * cols + c) % len(tiles)], AREA[0] + c * 57 * S, AREA[1] + r * 29 * S - 12 * S)
    lp = layer.load()
    for y in range(1080):
        for x in range(1920):
            if lp[x, y][3] and not in_cone(x, y):
                lp[x, y] = (0, 0, 0, 0)
    if alpha < 1.0:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    return layer


def edge_layer(loop, alpha=1.0, step=0):
    """Edge pieces along both slanted edges: right as drawn, left flipped, one frame ahead per piece."""
    layer = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    right = [texels(pal.to_image(f)) for f in loop]
    left = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in right]
    step_x, step_y = edge.W * S, edge.RISE * edge.W // edge.RUN * S        # (90, 42) px
    for k in range(11):
        y = APEX[1] + step_y * k - edge.LINE_Y0 * S
        paste(layer, right[(step + k) % len(right)], APEX[0] + step_x * k, y)
        paste(layer, left[(step + k) % len(left)], APEX[0] - step_x * (k + 1), y)
    lp = layer.load()
    for y in range(1080):
        for x in range(1920):
            if lp[x, y][3] and not (AREA[0] <= x < AREA[2] and y < AREA[3]):
                lp[x, y] = (0, 0, 0, 0)
    if alpha < 1.0:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    return layer


def bixby():
    sheet = Image.open(ROOT + '/Assets/Characters/Bixby/bixby_beast_redesign.png').convert('RGBA')
    return texels(sheet.crop((2 * 192, 0, 3 * 192, 160)))


def player(col, row):
    sheet = Image.open(ROOT + '/Assets/Characters/MainPlayer/player_4dir_sheet.png').convert('RGBA')
    return texels(sheet.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)))


def hud_marks(dst):
    """The boss bar and name plate, faded as the code will fade them while he perches."""
    over = Image.new('RGBA', dst.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for box in (PLATE, BAR):
        d.rectangle(box, fill=(20, 16, 30, 70), outline=(238, 244, 247, 120), width=3)
    x0, y0, x1, y1 = BAR
    d.rectangle((x0 + 12, y0 + 16, x1 - 12, y1 - 16), fill=(180, 36, 36, 70))
    dst.alpha_composite(over)


def burst_bridges(dst, origin, f):
    """Stand-in mouth flames, level, from frame 2's side mouths into the burst's side entries (the perch
    art's own mouth flames will do this). Mouths measured on frame 2 at texels (38, 95) and (153, 95)."""
    from firelib import rings, put
    ox, oy = 30, 4                                      # this little canvas's texel origin, in burst texels
    g = [['.'] * 130 for _ in range(40)]
    shape = set()
    for mouth, entry in ((-26, burst.ENTRY['left']), (89, burst.ENTRY['right'])):
        m = (mouth + ox, 14 + oy)
        e = (entry[0] + ox + (2 if mouth < 0 else -2), entry[1] + oy)
        mid = ((m[0] + e[0]) / 2.0, (m[1] + e[1]) / 2.0 + 1.5)
        shape |= burst.stroke(m, mid, e, 2.6, 3.8, wobble=0.2, phase=0.3 * f, steps=30)
    shape = {(x, y) for (x, y) in shape if 0 <= x < 130 and 0 <= y < 40}
    for (x, y), dd in rings(shape).items():
        put(g, x, y, ('r', 'N', 'p', 'P', 'Y')[min(dd, 4)])
    paste(dst, texels(pal.to_image(g)), origin[0] - ox * S, origin[1] - oy * S)


def streak(im_rows, angle):
    """Pick a suction frame for a flight angle (degrees, y down) by the 3 rows and their flips."""
    a = int(round(angle / 45.0)) % 8
    table = {0: (0, False, False), 1: (1, False, False), 2: (2, False, False), 3: (1, True, False),
             4: (0, True, False), 5: (1, True, True), 6: (2, False, True), 7: (1, False, True)}
    row, fh, fv = table[a]
    im = im_rows[row]
    if fh:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if fv:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im


def save_pair(canvas, name):
    full = os.path.join(OUT, name.replace('.png', '_1920.png'))
    small = os.path.join(OUT, name)
    canvas.convert('RGB').save(full)
    canvas.convert('RGB').resize((1280, 720), Image.NEAREST).save(small)
    print(small)
    print(full)


def breath_still(base, cap):
    c = base.copy()
    fr = flood.frames()
    er = edge.frames()
    c.alpha_composite(flood_layer(fr[4:8], step=1))
    c.alpha_composite(edge_layer(er[4:8], step=2))
    paste(c, bixby(), *BIXBY_ORIGIN)
    b = burst.frames()[3]
    origin = (APEX[0] - 32 * S, 222)                     # middle entry on frame 2's middle jaw
    burst_bridges(c, origin, 1)
    paste(c, texels(pal.to_image(b)), *origin)
    ropes_over(c, cap)
    # the player in the upper-left safe corner, facing him
    paste(c, player(0, 3), 330 - 48, 250 - 48)
    hud_marks(c)
    save_pair(c, 'approval.png')


def inhale_still(base, cap):
    c = base.copy()
    fr = flood.frames()
    er = edge.frames()
    c.alpha_composite(flood_layer(fr[0:2], alpha=0.45))
    c.alpha_composite(edge_layer(er[0:2], alpha=0.45))
    mouth = (960, 205)
    # the scorch left by an earlier ball, then markers at each stage with their balls coming down
    scorch = Image.open(ROOT + '/Assets/Characters/Bixby/bixby_fire_scorch.png').convert('RGBA').crop((0, 0, 40, 40))
    paste(c, texels(scorch), 1330 - 20 * S, 700 - 31 * S)
    mk = [texels(pal.to_image(m)) for m in marker.frames()]
    fb = [texels(pal.to_image(f)) for f in fireball.frames()[1]]
    drops = [((560, 620), 0, None), ((1180, 520), 1, None), ((760, 820), 2, 150), ((1500, 840), 3, 60),
             ((420, 430), 1, None), ((1060, 690), 2, 330)]
    for (x, y), f, above in drops:
        paste(c, mk[f], x - 22 * S, y - 11 * S)
    im = [texels(i) for i in [impact.image(impact.frames())]][0]
    paste(c, im.crop((2 * 48 * S, 0, 3 * 48 * S, 40 * S)), 1420 - 24 * S, 380 - 28 * S)
    paste(c, bixby(), *BIXBY_ORIGIN)
    ropes_over(c, cap)
    # the player, dragged up toward him from the left
    px, py = 640, 470
    paste(c, player(1, 1), px - 48, py - 48)
    # suction streaks: most near the player, all flying at the mouth
    sx = [texels(pal.to_image(f)) for f in [r[1] for r in suction.frames()]]
    for (x, y) in ((560, 560), (700, 380), (540, 420), (760, 520), (820, 440), (470, 520), (1180, 420),
                   (1320, 300), (880, 330), (620, 300), (1060, 300)):
        ang = math.degrees(math.atan2(mouth[1] - y, mouth[0] - x))
        s = streak(sx, ang)
        paste(c, s, x - 12 * S, y - 12 * S)
    # the falling balls, over everything
    for (x, y), f, above in drops:
        if above is not None:
            paste(c, fb[(x // 7) % 4], x - 8 * S, y - above - 17 * S)
    hud_marks(c)
    save_pair(c, 'approval_inhale.png')


if __name__ == '__main__':
    base, cap = arena()
    which = sys.argv[1:] or ['breath', 'inhale']
    if 'breath' in which:
        breath_still(base, cap)
    if 'inhale' in which:
        inhale_still(base, cap)
