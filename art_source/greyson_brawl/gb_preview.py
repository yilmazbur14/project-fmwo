"""Previews of Greyson's brawl frames, written ONLY to the scratch folder (gb_base.SCRATCH):

    python -B gb_preview.py          # the approval pass (below)
    python -B gb_preview.py sheets   # the punching half: <sheet>_4x.png strips and
                                     # <sheet>_staged.gif, each punch at the game's framing with
                                     # the player stand-in answering it (landed, then dodged)

    brawl_approval_4x.png       the approval frames at 4x, each with its anchors marked
    brawl_mock_zoom15.png       the brawl as the game frames it (PLAN_BRAWL.md section 4): his feet
                                at (960, 560), the player at 2x in front of him (a nearest-neighbour
                                x2 of the approved player_final_brawl.png standing in for the redraw)
                                with soles at (960, 572), the camera at zoom 1.5 on (960, 402);
                                three moments side by side, each the full 1920x1080 view scaled down
    brawl_mock_zoom15_crop.png  the same three, cropped to the fighters at full zoom-1.5 size
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gb_base as B  # noqa: E402
import gb_fig as F  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

K = B.K
OUT = B.SCRATCH
BG = (46, 49, 58, 255)
ROOT = B.G.B.ROOT
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_final_brawl.png')
FEET_W = (960, 560)          # his feet, world px
SOLES_W = (960, 572)         # the player's soles
ZOOM, FOCUS = 1.5, (960, 402)
MARK = {'crown': (0, 255, 255), 'chin': (255, 0, 255), 'fist': (255, 200, 0), 'gauntlet': (0, 255, 0),
        'muzzle': (255, 90, 90), 'contact': (255, 255, 255)}


def up(im, s, bg=BG):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im)
    return b.resize((im.width * s, im.height * s), Image.NEAREST)


def marked(im, anc, s=4):
    big = up(im, s)
    d = ImageDraw.Draw(big)
    for k, p in anc.items():
        if p is None:
            continue
        x, y = p
        c = MARK[k] + (255,)
        d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], outline=c)
        d.line([(x * s - 5, y * s + s // 2), (x * s + s + 4, y * s + s // 2)], fill=c)
        d.line([(x * s + s // 2, y * s - 5), (x * s + s // 2, y * s + s + 4)], fill=c)
    return big


def player_cell(col):
    """The approved 1x back view (row 1, UP), column col, doubled nearest-neighbour."""
    sheet = Image.open(PLAYER).convert('RGBA')
    cell = sheet.crop((col * 32, 32, col * 32 + 32, 64))
    return cell.resize((64, 64), Image.NEAREST)


def world(greyson_im, player_col):
    """The whole screen at zoom 1.5 (1920x1080) around FOCUS."""
    vw, vh = 1920 / ZOOM, 1080 / ZOOM
    x0, y0 = FOCUS[0] - vw / 2, FOCUS[1] - vh / 2
    wx0, wy0, ww, wh = int(x0), int(y0), int(vw), int(vh)
    canvas = Image.new('RGBA', (ww, wh), (0, 0, 0, 255))
    mat = Image.open(MAT).convert('RGBA')
    mat3 = mat.resize((mat.width * 3, mat.height * 3), Image.NEAREST)
    for ty in range(-mat3.height, wh + mat3.height, mat3.height):
        for tx in range(-mat3.width, ww + mat3.width, mat3.width):
            canvas.paste(mat3, (tx - (wx0 % mat3.width), ty - (wy0 % mat3.height)))
    g3 = greyson_im.resize((336, 336), Image.NEAREST)
    canvas.alpha_composite(g3, (FEET_W[0] - 168 - wx0, FEET_W[1] - 336 - wy0))
    p2 = player_cell(player_col).resize((192, 192), Image.NEAREST)     # the 2x cell at scale 3
    # the doubled cell's soles (1x row 28 -> rows 56-57) end at the player's soles; its centre
    # column (1x 15.5 -> 32) on x 960
    canvas.alpha_composite(p2, (SOLES_W[0] - 32 * 3 - wx0, SOLES_W[1] - 58 * 3 - wy0))
    return canvas.resize((1920, 1080), Image.NEAREST)


def main():
    os.makedirs(OUT, exist_ok=True)
    frames = [(t, *fn(**kw)) for t, fn, kw in F.APPROVAL]
    cards = []
    for title, cv, anc in frames:
        big = marked(cv.image(), anc)
        c = Image.new('RGBA', (big.width, big.height + 40), (18, 18, 24, 255))
        c.paste(big, (0, 40))
        d = ImageDraw.Draw(c)
        st = K.stats(cv.image())
        d.text((4, 3), '%s   black %.1f%%  colours %d' % (title, 100 * st['black'], st['colours']),
               fill=(230, 230, 236, 255))
        d.text((4, 20), '  '.join('%s %s' % kv for kv in anc.items()), fill=(200, 200, 210, 255))
        cards.append(c)
    w = sum(c.width for c in cards) + 8 * (len(cards) - 1)
    out = Image.new('RGBA', (w, cards[0].height), (10, 10, 14, 255))
    x = 0
    for c in cards:
        out.paste(c, (x, 0))
        x += c.width + 8
    p = os.path.join(OUT, 'brawl_approval_4x.png')
    out.save(p)
    print(p)
    # the mock: guard vs the player's guard; the hook landing on the player (their "hit lands");
    # dazed, the player in guard in front of him
    shots = [world(frames[0][1].image(), 0), world(frames[1][1].image(), 8), world(frames[2][1].image(), 0)]
    small = [s.resize((640, 360), Image.LANCZOS) for s in shots]
    full = Image.new('RGBA', (640 * 3 + 16, 360), (10, 10, 14, 255))
    for i, s in enumerate(small):
        full.paste(s, (i * 648, 0))
    p = os.path.join(OUT, 'brawl_mock_zoom15.png')
    full.save(p)
    print(p)
    # crop to the fighters at the real zoom-1.5 size: world x 760-1160, y 200-600
    crops = []
    for s in shots:
        cx0 = int((760 - (FOCUS[0] - 640)) * ZOOM)
        cy0 = int((200 - (FOCUS[1] - 360)) * ZOOM)
        crops.append(s.crop((cx0, cy0, cx0 + 600, cy0 + 600)))
    cw = Image.new('RGBA', (600 * 3 + 16, 600), (10, 10, 14, 255))
    for i, c in enumerate(crops):
        cw.paste(c, (i * 608, 0))
    p = os.path.join(OUT, 'brawl_mock_zoom15_crop.png')
    cw.save(p)
    print(p)


if __name__ == '__main__' and len(sys.argv) == 1:
    main()


# ------------------------------------------------------------------------------------ the sheets
def strip_4x(name, frames):
    """frames: [(label, image, anchors)] -> a labelled 4x strip."""
    s = 4
    w = 112 * s
    out = Image.new('RGBA', (w * len(frames) + 6 * (len(frames) - 1), 112 * s + 40), (18, 18, 24, 255))
    d = ImageDraw.Draw(out)
    for i, (label, im, anc) in enumerate(frames):
        x = i * (w + 6)
        out.paste(up(im, s), (x, 40))
        st = K.stats(im)
        d.text((x + 3, 3), '%s f%d %s   black %.1f%%  colours %d' % (name, i, label, 100 * st['black'], st['colours']),
               fill=(230, 230, 236, 255))
        d.text((x + 3, 20), '  '.join('%s %s' % kv for kv in anc.items() if kv[1] is not None),
               fill=(190, 190, 200, 255))
    return out


def staged(greyson_im, player_col):
    """One moment at the game's framing (zoom 1.5), cropped to the fighters (world x 760-1160,
    y 200-600, so 600x600)."""
    shot = world(greyson_im, player_col)
    cx0 = int((760 - (FOCUS[0] - 640)) * ZOOM)
    cy0 = int((200 - (FOCUS[1] - 360)) * ZOOM)
    return shot.crop((cx0, cy0, cx0 + 600, cy0 + 600))


def gif(shots, durations, path):
    pal = [s.convert('P', palette=Image.ADAPTIVE, colors=255) for s in shots]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations, loop=0, disposal=2)


def sheets_main():
    import gb_sheets as S
    os.makedirs(OUT, exist_ok=True)
    built = {name: [(label, cv.image(), anc) for label, cv, anc in S.build_sheet(name)] for name in S.SHEETS}
    for name, frames in built.items():
        p = os.path.join(OUT, name + '_4x.png')
        strip_4x(name, frames).save(p)
        print(p)
    im = {name: [f[1] for f in frames] for name, frames in built.items()}
    guard = im['greyson_brawl_guard']
    g0 = [(guard[i], 0 if i % 2 == 0 else 1, 140) for i in range(4)]
    # the player stand-in's columns: 0-1 guard, 2-3 slip L, 4-5 slip R, 6-7 parry, 8-9 hit
    plays = {
        'greyson_brawl_guard': g0 * 3,
        'greyson_brawl_hook_l': g0 + [
            (im['greyson_brawl_hook_l'][0], 0, 430), (im['greyson_brawl_hook_l'][1], 8, 100),
            (im['greyson_brawl_hook_l'][2], 9, 160), (im['greyson_brawl_hook_l'][4], 0, 160)] + g0 + [
            (im['greyson_brawl_hook_l'][0], 0, 300), (im['greyson_brawl_hook_l'][0], 2, 50),
            (im['greyson_brawl_hook_l'][1], 3, 100), (im['greyson_brawl_hook_l'][3], 3, 160),
            (im['greyson_brawl_hook_l'][4], 2, 160)],
        'greyson_brawl_hook_r': g0 + [
            (im['greyson_brawl_hook_r'][0], 0, 430), (im['greyson_brawl_hook_r'][1], 8, 100),
            (im['greyson_brawl_hook_r'][2], 9, 160), (im['greyson_brawl_hook_r'][4], 0, 160)] + g0 + [
            (im['greyson_brawl_hook_r'][0], 0, 300), (im['greyson_brawl_hook_r'][0], 4, 50),
            (im['greyson_brawl_hook_r'][1], 5, 100), (im['greyson_brawl_hook_r'][3], 5, 160),
            (im['greyson_brawl_hook_r'][4], 4, 160)],
        'greyson_brawl_straight': g0 + [
            (im['greyson_brawl_straight'][0], 0, 300), (im['greyson_brawl_straight'][0], 6, 130),
            (im['greyson_brawl_straight'][1], 7, 100), (im['greyson_brawl_straight'][2], 7, 120),
            (im['greyson_brawl_straight'][3], 0, 180), (im['greyson_brawl_straight'][4], 0, 160)] + g0 + [
            (im['greyson_brawl_straight'][0], 0, 430), (im['greyson_brawl_straight'][1], 8, 250),
            (im['greyson_brawl_straight'][4], 9, 160)],
        'greyson_brawl_rocked': g0 + [
            (im['greyson_brawl_rocked'][0], 7, 120), (im['greyson_brawl_rocked'][1], 0, 130)] + [
            (F.dazed()[0].image(), 0, 900)],
    }
    for name, seq in plays.items():
        shots = [staged(g, pc) for g, pc, _ in seq]
        p = os.path.join(OUT, name + '_staged.gif')
        gif(shots, [dur for _, _, dur in seq], p)
        print(p)


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'sheets':
    sheets_main()
