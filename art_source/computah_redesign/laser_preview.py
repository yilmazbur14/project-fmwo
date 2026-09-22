"""Review images for the beam recolour.

  laser_before_after_3x.png   the three textures, red above green, at 3x
  laser_in_arena.png          what the fight actually shows: the aim line in both of
                              its readings and the fired beam, laid on the arena mat
                              at the real relative scales - BeamRig is scale 2 and the
                              mat is scale 3, so the beam's texels are 2/3 of the
                              canvas's and the green sits on green.

The second one is the only one worth trusting.  A beam judged on a dark background is
judged against a background this fight does not have.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview")
MAT = os.path.join(HERE, "..", "..", "Assets", "Environment", "arena_mat.png")

RIG = 2          # ComputahScene/BeamRig scale
MAT_SCALE = 3    # ArenaScene/Mat scale
AIM_DIM_ALPHA = 0.6      # ComputahBeam.AIM_DIM_ALPHA


def _pair(name):
    return (Image.open(os.path.join(HERE, "laser_red", name)).convert("RGBA"),
            Image.open(os.path.join(HERE, name)).convert("RGBA"))


def before_after(z=3, pad=10, bg=(26, 26, 34, 255)):
    names = ["computah_laser_aim.png", "computah_laser_beam.png",
             "computah_laser_fx.png"]
    pairs = [_pair(n) for n in names]
    w = sum(p[0].width * z for p in pairs) + pad * (len(pairs) + 1)
    h = max(p[0].height for p in pairs) * z * 2 + pad * 3
    sheet = Image.new("RGBA", (w, h), bg)
    x = pad
    for red, green in pairs:
        big = lambda im: im.resize((im.width * z, im.height * z), Image.NEAREST)
        sheet.alpha_composite(big(red), (x, pad))
        sheet.alpha_composite(big(green), (x, pad * 2 + max(p[0].height for p in pairs) * z))
        x += red.width * z + pad
    sheet.save(os.path.join(OUT, "laser_before_after_%dx.png" % z))
    return sheet


def _run(tex, length, row_y, alpha=1.0, scroll=0):
    """One horizontal run of a tiling beam texture, the way the Sprite2D's region
    rect plus texture_repeat draws it."""
    tile = tex.crop((0, row_y, tex.width, row_y + (23 if tex.height >= 23 else 5)))
    strip = Image.new("RGBA", (length, tile.height))
    for x in range(-tile.width, length + tile.width, tile.width):
        strip.alpha_composite(tile, (x + scroll % tile.width, 0))
    if alpha < 1.0:
        a = strip.getchannel("A").point(lambda v: int(v * alpha))
        strip.putalpha(a)
    return strip


def in_arena(length=260, pad=14):
    """Four rows on the real canvas: the aim line as the player sees it while it is
    still tracking (its dim half and its bright half), the aim line locked, and the
    shot.  Red on the left of each pair, green on the right."""
    mat = Image.open(MAT).convert("RGBA")
    rows = []
    for name, ys, alphas, label in (
            ("computah_laser_aim.png", (0,), (AIM_DIM_ALPHA, 1.0, 1.0), "aim"),
            ("computah_laser_beam.png", (0,), (1.0,), "beam")):
        red, green = _pair(name)
        for a in alphas:
            rows.append((_run(red, length, ys[0], a, 0),
                         _run(green, length, ys[0], a, 0)))
    flare_r, flare_g = _pair("computah_laser_fx.png")
    fw = flare_r.width // 2
    rh = max(r.height for r, _ in rows)
    cell_h = max(rh, fw) * RIG + pad
    sheet = Image.new("RGBA", ((length + fw) * RIG + pad * 3,
                               cell_h * len(rows) * 2 + pad), (0, 0, 0, 255))
    # One patch of canvas behind the lot, at the scale the arena draws it.
    canvas = mat.crop((0, 40, mat.width, 40 + sheet.height // MAT_SCALE + 1))
    canvas = canvas.resize((canvas.width * MAT_SCALE, canvas.height * MAT_SCALE),
                           Image.NEAREST)
    sheet.alpha_composite(canvas.crop((0, 0, sheet.width, sheet.height)), (0, 0))

    def blit(strip, flare, frame, y):
        big = strip.resize((strip.width * RIG, strip.height * RIG), Image.NEAREST)
        sheet.alpha_composite(big, (pad + fw * RIG // 2, y))
        f = flare.crop((frame * fw, 0, (frame + 1) * fw, flare.height))
        f = f.resize((fw * RIG, f.height * RIG), Image.NEAREST)
        sheet.alpha_composite(f, (pad, y + big.height // 2 - f.height // 2))

    y = pad // 2
    for i, (r, g) in enumerate(rows):
        frame = 1 if i == len(rows) - 1 else 0
        blit(r, flare_r, frame, y)
        blit(g, flare_g, frame, y + cell_h)
        y += cell_h * 2
    sheet.save(os.path.join(OUT, "laser_in_arena.png"))
    return sheet


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    before_after()
    in_arena()
    print("wrote preview/laser_before_after_3x.png and preview/laser_in_arena.png")
