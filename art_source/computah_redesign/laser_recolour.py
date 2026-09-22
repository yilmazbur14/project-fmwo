"""The beam projectile's palette swap: the old red laser onto the redesign's green.

WHAT THIS IS AND IS NOT
Not a redraw.  Computah's sheets already carry the beam in green - the capacitor
cells, the charge ball, the lock flare and the muzzle blast baked onto
computah_beam_fire are all #4FE066/#A9FFB4 over #0C111A - but the projectile was
never revisited, so the shipped fight fires a RED beam out of a GREEN muzzle blast
down a RED aim line.  This maps every colour of the three projectile textures onto
the green ramp and touches nothing else: same sizes, same frame counts, same alpha
on every single pixel.  LaserBeamProjectileScene indexes these by frame and
ComputahBeam measures them (BEAM_TEXTURE_HEIGHT 23, BEAM_TEXTURE_WIDTH 16,
AIM_TEXTURE_WIDTH 12, hitbox 21 so grazing the outline is free), so a pixel that
moves is a bug.  check() asserts that below.

laser_red/ holds the three shipped red textures as the input, untouched, so this is
re-runnable and so the before/after can always be rebuilt.

THE RAMP
Five of the six greens are lifted straight off the approved sheets, so the fired
beam and the muzzle blast it comes out of are literally the same colours:

    K  #0C111A   the cast keyline - what the baked muzzle blast is outlined in
    d  #145F24   THE ONE NEW COLOUR.  Green has nothing below #1F9A38 on his
                 sheets, and the red ramp's shade step sat at 62% of its mid's
                 luminance; this is #1F9A38 scaled to that same 62%, so the beam's
                 edge keeps the definition the red one had.
    m  #1F9A38   BEAM_DK  on the sheets
    l  #4FE066   BEAM_MID - the signature beam green, the cells' lit colour
    h  #A9FFB4   BEAM_HI  - the colour the lock flare is drawn in
    W  #E6FFE9   BEAM_CORE- the blown-out centre of the muzzle blast

WHY THE AIM LINE IS MAPPED ONE STEP DOWN AND THE BEAM IS NOT
The attack's whole read is "dim, flickering, scrolling" -> "solid, bright, still",
and ComputahBeam draws BOTH states from this ONE texture: the only difference is
modulate.a (0.6 on half the flicker, 1.0 locked) and the scroll offset.  Alpha is a
multiply, so the tracking-to-locked RATIO is fixed at 0.6 whatever colour is used -
what the palette controls is the ABSOLUTE level the pair sits at, and the arena mat
is bright yellow-green (#7EA85B, luma 154).  Mapped like the beam, the aim line's
body would go from #AC3232 (luma 76) to #1F9A38 (luma 121): a same-hue line at 1.27:1
against the mat instead of a complementary one at 2:1, i.e. a line that is loudest
exactly where it needs to be quiet and nearly invisible where it lies on the canvas.

So the aim line is mapped one rung down the SAME ramp.  Its dash body lands on
#145F24, luma 74.8, against the red original's 76.0 - the dim end is held to within
1.6% of what it was - while the dash's leading tip still runs up through #4FE066 to
#E6FFE9, the same near-white the beam and the muzzle blast are cored with.  Nothing
about this is a second palette: it is the same six colours, entered at a lower rung.

  python laser_recolour.py          # rebuild the three PNGs and check them
  python laser_recolour.py --ship   # ...and copy them to Assets/Characters/Computah
"""
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "laser_red")
SHIP = os.path.join(HERE, "..", "..", "Assets", "Characters", "Computah")

# The red set every one of the three textures is drawn from, by role.
RED = {
    "K": (0x42, 0x0A, 0x14),
    "d": (0x82, 0x19, 0x19),
    "m": (0xAC, 0x32, 0x32),
    "l": (0xD4, 0x96, 0x9C),
    "h": (0xF8, 0xD4, 0xD8),
    "W": (0xFF, 0xFF, 0xFF),
}
ROLE = {rgb: role for role, rgb in RED.items()}

GREEN = {
    "K": (0x0C, 0x11, 0x1A),
    "d": (0x14, 0x5F, 0x24),
    "m": (0x1F, 0x9A, 0x38),
    "l": (0x4F, 0xE0, 0x66),
    "h": (0xA9, 0xFF, 0xB4),
    "W": (0xE6, 0xFF, 0xE9),
}

# The shot and its muzzle flare: role for role, so they match the baked blast exactly.
HOT = {"K": "K", "d": "d", "m": "m", "l": "l", "h": "h", "W": "W"}
# The sight: the same ramp entered one rung lower.  See the header.
COOL = {"K": "K", "d": "d", "m": "d", "l": "m", "h": "l", "W": "W"}

FILES = (
    ("computah_laser_beam.png", HOT),
    ("computah_laser_fx.png", HOT),
    ("computah_laser_aim.png", COOL),
)


def luma(c):
    """sRGB relative luminance, the number every brightness claim here is made in."""
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def recolour(im, mapping, name):
    """A strict substitution.  Every opaque colour must be a known red, and alpha is
    copied through untouched, so the silhouette cannot move even by accident."""
    im = im.convert("RGBA")
    out = Image.new("RGBA", im.size)
    sp, op = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = sp[x, y]
            if a == 0:
                op[x, y] = (0, 0, 0, 0)
                continue
            if (r, g, b) not in ROLE:
                raise SystemExit("%s: unmapped colour #%02X%02X%02X at (%d,%d)"
                                 % (name, r, g, b, x, y))
            op[x, y] = GREEN[mapping[ROLE[(r, g, b)]]] + (a,)
    return out


def check(before, after, mapping, name):
    """The three things the scene and ComputahBeam rely on: same size, same alpha on
    every pixel, and every red role landing on exactly the pixels it used to."""
    assert before.size == after.size, "%s: size moved" % name
    a, b = before.convert("RGBA").load(), after.convert("RGBA").load()
    seen_in, seen_out, moved = set(), set(), 0
    for y in range(before.height):
        for x in range(before.width):
            p, q = a[x, y], b[x, y]
            assert p[3] == q[3], "%s: alpha moved at (%d,%d)" % (name, x, y)
            if p[3] == 0:
                continue
            want = GREEN[mapping[ROLE[p[:3]]]]
            assert q[:3] == want, "%s: (%d,%d) is not the mapped colour" % (name, x, y)
            seen_in.add(p[:3])
            seen_out.add(q[:3])
            moved += p[:3] != q[:3]
    print("  %-26s %-8s alpha identical, %d px recoloured, %d colours in -> %d out"
          % (name, "%dx%d" % before.size, moved, len(seen_in), len(seen_out)))


def main(ship=False):
    print("ramp, red -> green, by sRGB luminance:")
    for role in ("K", "d", "m", "l", "h", "W"):
        print("  %s  #%02X%02X%02X %5.1f  ->  #%02X%02X%02X %5.1f"
              % ((role,) + RED[role] + (luma(RED[role]),)
                 + GREEN[role] + (luma(GREEN[role]),)))
    print()
    for name, mapping in FILES:
        src = Image.open(os.path.join(SOURCE, name))
        out = recolour(src, mapping, name)
        check(src, out, mapping, name)
        out.save(os.path.join(HERE, name))
    if ship:
        print()
        for name, _ in FILES:
            shutil.copyfile(os.path.join(HERE, name), os.path.join(SHIP, name))
            print("  shipped %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main("--ship" in sys.argv))
