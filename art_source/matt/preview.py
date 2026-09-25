"""Previews: frames at 5x on the dark ground, the game-scale line-up on the arena mat, and the
reference strip. Reads the project's assets; writes only to the folder it is given."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pal
from pal import lib
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(pal.HERE))
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
CARTER = os.path.join(ROOT, 'Assets', 'Characters', 'Carter', 'carter_polish.png')
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')


def frames_5x(frames, path, pad=4):
    w = sum(f.width for f in frames) + pad * (len(frames) + 1)
    h = max(f.height for f in frames) + 2 * pad
    out = Image.new('RGBA', (w, h), lib.BG)
    x = pad
    for f in frames:
        out.alpha_composite(f, (x, pad))
        x += f.width + pad
    lib.upscale(out, 5).save(path)


def lineup(frames, path):
    """Native-resolution composite on a crop of the mat, then 3x: every sprite in this game draws
    at 3x, the mat included, so this is what the fight shows (minus the camera)."""
    mat = Image.open(MAT).convert('RGBA')
    sheet = Image.open(PLAYER).convert('RGBA')
    player = sheet.crop((0, 96, 32, 128))         # row 3: side view, facing right
    carter = Image.open(CARTER).convert('RGBA').crop((0, 0, 96, 96))
    w = 32 + 96 + 96 * len(frames) + 8 * (len(frames) + 3)
    crop_x, crop_y = 120, 80
    ground = mat.crop((crop_x, crop_y, crop_x + w, crop_y + 110))
    base_y = 104                                   # the row everyone's feet stand on
    x = 8
    ground.alpha_composite(player, (x, base_y - 28))  # player feet are on row 28 of its frame
    x += 32 + 8
    ground.alpha_composite(carter, (x, base_y - 95))
    x += 96 + 8
    for f in frames:
        ground.alpha_composite(f, (x, base_y - 95))
        x += 96 + 8
    lib.upscale(ground, 3).save(path)


def refs_strip(frames, refs, path, h=300):
    ims = []
    for r in refs:
        im = Image.open(r).convert('RGBA')
        s = h / im.height
        ims.append(im.resize((int(im.width * s), h), Image.LANCZOS))
    for f in frames:
        s = h // f.height
        big = lib.upscale(lib.on_bg(f), s)
        ims.append(big)
    w = sum(i.width for i in ims) + 10 * (len(ims) + 1)
    out = Image.new('RGBA', (w, h + 20), (30, 32, 38, 255))
    x = 10
    for i in ims:
        out.alpha_composite(i, (x, 10))
        x += i.width + 10
    out.save(path)
