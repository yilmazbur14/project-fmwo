"""Approval previews for the player's combo, written into a folder you name (required; a bare run prints
this and writes nothing, and a folder inside Assets/ is refused):

    python combo_previews.py <out_dir>                  # from the grids in combo_frames
    python combo_previews.py <out_dir> --sheet <png>    # from a written player_combo_sheet.png instead

It writes:
    combo_chain_down.gif, combo_chain_up.gif, combo_chain_left.gif, combo_chain_right.gif
        hit 1 (player_4dir_sheet.png columns 5-8), then hit 2, then hit 3, at game speed: four frames of
        80, 90, 80, 80 ms (~83 ms each; GIF delays are whole centiseconds), the extension held 80 ms,
        120 ms of idle between hits, a 400 ms idle lead-in and a 700 ms idle tail. 8x, nearest neighbour.
    combo_contact.png
        one row per facing, hit 1 | hit 2 | hit 3, 8x, on a neutral dark ground with gaps between cells.
    combo_in_context.gif
        all four facings playing the same chain side by side over a crop of the ring floor
        (Assets/Environment/arena_mat.png, which ArenaScene draws at 3x like the player), the whole scene
        at 3x: the size it plays at.
    combo_in_context.png
        the same floor, frozen on each hit's extension: rows hit 1, 2, 3; columns DOWN, UP, LEFT, RIGHT.
It only reads player_4dir_sheet.png and arena_mat.png.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import combo_frames as F  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

MAT = os.path.join(F.ROOT, 'Assets', 'Environment', 'arena_mat.png')
ASSETS = os.path.join(F.ROOT, 'Assets')
GROUND = (35, 35, 41)            # the neutral dark ground
PANEL = (52, 52, 61)             # behind each cell on the contact sheet
TEXT = (205, 205, 215)
HIT_MS = (80, 90, 80, 80)        # ~83 ms a frame; the fourth (extension) held 80 ms
IDLE_BETWEEN, LEAD_IN, TAIL = 120, 400, 700


# ------------------------------------------------------------------ cells
def combo_cells(sheet_path=None):
    """{facing: [8 RGBA cells]} from the grids, or cut from a written sheet."""
    if sheet_path is None:
        return {f: [F.cell_image(g) for g in F.FRAMES[f]] for f in F.FACINGS}
    with Image.open(sheet_path) as im:
        im = im.convert('RGBA')
        return {f: [im.crop((c * F.W, r * F.H, c * F.W + F.W, r * F.H + F.H)) for c in range(8)]
                for r, f in enumerate(F.FACINGS)}


def chain(facing, cells):
    """[(cell, ms)] for idle, hit 1, idle, hit 2, idle, hit 3, idle."""
    r = F.FACINGS.index(facing)
    idle = F.base_cell(r, F.IDLE_COL)
    hit1 = [F.base_cell(r, c) for c in F.HIT1_COLS]
    seq = [(idle, LEAD_IN)]
    seq += list(zip(hit1, HIT_MS)) + [(idle, IDLE_BETWEEN)]
    seq += list(zip(cells[facing][0:4], HIT_MS)) + [(idle, IDLE_BETWEEN)]
    seq += list(zip(cells[facing][4:8], HIT_MS)) + [(idle, TAIL)]
    return seq


def zoom(im, z):
    return im.resize((im.width * z, im.height * z), Image.NEAREST)


def palette_image(colours):
    """A P-mode image carrying exactly these colours, for quantizing without dithering."""
    colours = sorted(set(colours))
    assert len(colours) <= 256, len(colours)
    flat = [v for c in colours for v in c]
    flat += flat[:3] * (256 - len(colours))
    pal = Image.new('P', (1, 1))
    pal.putpalette(flat)
    return pal


def save_gif(frames, durations, path):
    """RGB frames -> GIF with one shared palette of their exact colours (no dithering, no drift)."""
    colours = set()
    for im in frames:
        colours |= {c for n, c in im.getcolors(1 << 20)}
    pal = palette_image(colours)
    ps = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in frames]
    ps[0].save(path, save_all=True, append_images=ps[1:], duration=list(durations), loop=0,
               optimize=False, disposal=1)
    return path


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                                  # older Pillow: the fixed bitmap font
        return ImageFont.load_default()


# ------------------------------------------------------------------ the previews
def chain_gifs(cells, out_dir, z=8):
    paths = []
    for facing in F.FACINGS:
        frames, durs = [], []
        for cell, ms in chain(facing, cells):
            bg = Image.new('RGBA', (F.W, F.H), GROUND + (255,))
            bg.alpha_composite(cell)
            frames.append(zoom(bg, z).convert('RGB'))
            durs.append(ms)
        paths.append(save_gif(frames, durs, os.path.join(out_dir, 'combo_chain_%s.gif' % facing.lower())))
    return paths


def contact_sheet(cells, out_dir, z=8):
    cw = F.W * z
    gap, group_gap, left, top, margin = 8, 40, 150, 76, 20
    width = margin * 2 + left + 12 * cw + 9 * gap + 2 * group_gap
    height = margin * 2 + top + 4 * cw + 3 * gap
    im = Image.new('RGB', (width, height), GROUND)
    d = ImageDraw.Draw(im)
    big, small = font(28), font(20)
    groups = (('hit 1  (player_4dir_sheet cols 5-8)', None),
              ('hit 2  (player_combo_sheet cols 0-3)', 0), ('hit 3  (player_combo_sheet cols 4-7)', 4))
    names = (('guard', 'chamber', 'travel', 'extension'),) * 2 + (('guard', 'chamber', 'drive', 'extension'),)
    for r, facing in enumerate(F.FACINGS):
        y = margin + top + r * (cw + gap)
        d.text((margin, y + cw // 2 - 14), facing, fill=TEXT, font=big)
        for g, (title, first) in enumerate(groups):
            gx = margin + left + g * (4 * cw + 3 * gap + group_gap)
            if r == 0:
                d.text((gx, margin), title, fill=TEXT, font=big)
            for i in range(4):
                x = gx + i * (cw + gap)
                if r == 0:
                    d.text((x + 6, margin + 40), '%d %s' % (i, names[g][i]), fill=TEXT, font=small)
                cell = F.base_cell(r, F.HIT1_COLS[i]) if first is None else cells[facing][first + i]
                panel = Image.new('RGBA', (F.W, F.H), PANEL + (255,))
                panel.alpha_composite(cell)
                im.paste(zoom(panel, z).convert('RGB'), (x, y))
    path = os.path.join(out_dir, 'combo_contact.png')
    im.save(path)
    return path


def in_context(cells, out_dir, z=3):
    """Four facings side by side over the ring floor, at the game's 3x."""
    with Image.open(MAT) as m:
        floor = m.convert('RGBA').crop((40, 96, 240, 160))           # 200 x 64 of worn canvas
    seqs = [chain(f, cells) for f in F.FACINGS]
    frames, durs = [], []
    for k in range(len(seqs[0])):
        im = floor.copy()
        for i, seq in enumerate(seqs):
            im.alpha_composite(seq[k][0], (20 + i * 44, 28))
        frames.append(zoom(im, z).convert('RGB'))
        durs.append(seqs[0][k][1])
    gif = save_gif(frames, durs, os.path.join(out_dir, 'combo_in_context.gif'))
    # the still: rows hit 1, 2, 3 at full extension; columns DOWN, UP, LEFT, RIGHT
    with Image.open(MAT) as m:
        floor = m.convert('RGBA').crop((40, 60, 240, 172))
    for j, (row_cells) in enumerate([[F.base_cell(r, 8) for r in range(4)],
                                     [cells[f][3] for f in F.FACINGS],
                                     [cells[f][7] for f in F.FACINGS]]):
        for i, cell in enumerate(row_cells):
            floor.alpha_composite(cell, (20 + i * 44, 2 + j * 36))
    still = os.path.join(out_dir, 'combo_in_context.png')
    zoom(floor, z).convert('RGB').save(still)
    return gif, still


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return path == root or path.startswith(root + os.sep)


def main(argv):
    args = list(argv)
    sheet = None
    if '--sheet' in args:
        i = args.index('--sheet')
        if i + 1 >= len(args):
            print(__doc__)
            return 2
        sheet = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or args[0].startswith('--'):
        print(__doc__)
        return 2
    out_dir = os.path.abspath(args[0])
    if _under(out_dir, ASSETS):
        print('refused: %s is inside Assets/; previews never go there.' % out_dir)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    cells = combo_cells(sheet)
    written = chain_gifs(cells, out_dir) + [contact_sheet(cells, out_dir)] + list(in_context(cells, out_dir))
    for p in written:
        print(p)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
