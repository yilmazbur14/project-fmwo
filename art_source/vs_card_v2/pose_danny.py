"""DANNY - the slap drawn back, one palm thrust at Burak and the other raised, eyes half shut behind
the snot bubble: the sleeping giant, not quite awake, already swinging.

Built from his own pixels, both from the approved sumo redesign (Assets/Characters/Danny/Sumo/):
  * danny_sumo_slap.png frame 2        - the base: the palm on the side toward Burak thrust out in
                                         front of his chest, the other hand raised high, drawn back
                                         for the next slap. Native, so lit from the upper left; the
                                         pitch's danny_sumo_redesign frame 1 has the same two hands
                                         with the thrust palm on the side AWAY from Burak, and
                                         mirroring it would move the light (STYLE.md)
  * danny_sumo_redesign.png frame 0    - the face: his relaxed brows, the nose with the snot bubble
                                         swelling from it, and the sleeping pout. Slap frame 2's head
                                         sits exactly where frame 0's does (they differ only in the
                                         eyes, the nose and mouth, and the arm), so the face is taken
                                         across texel for texel
The eyes are the one thing drawn: frame 0's are shut, the pitch has them half shut. His own closed
lid stays as the heavy upper lid; under it a one-texel slit of his white opens, with his own dark
iris (#222034) turned toward Burak, and the lower lid closes it (EYE_*).

He is used at 1x: his sheet's head is already card-sized (STYLE.md), and the silhouette keyline is
grown outward by one texel so it matches everyone else's 2.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402
import grids as G                                                             # noqa: E402

SLAP = ("Danny/Sumo/danny_sumo_slap.png", 2)
SLEEP = ("Danny/Sumo/danny_sumo_redesign.png", 0)
FW, FH = 176, 144

# frame 0's face, taken across: the brows and eyes, then the nose, bubble and mouth (frame coords).
# The second box stops at x 76 so slap frame 2's forearm, which crosses the ruff there, stays.
FACE_BOXES = [(64, 27, 112, 35), (76, 35, 105, 52)]

# the half-shut eyes, over frame 0's shut ones: '#' ink, 'w' his white, 'i' his iris, '.' leave
EYE_L = """
..............
..............
.#iiwwwwwwww#.
"""
EYE_R = """
..............
..............
.#iiwwwwwwww#.
"""
EYES_AT = [(66, 30), (96, 30)]
EYE_LEGEND = {"#": "#000000", "w": "#FFFFFF", "i": "#222034"}


def frame(spec):
    path, i = spec
    return P.load(path, (i * FW, 0, i * FW + FW, FH))


def assemble():
    base = frame(SLAP)
    face = frame(SLEEP)
    b, f = base.load(), face.load()
    for x0, y0, x1, y1 in FACE_BOXES:
        for y in range(y0, y1):
            for x in range(x0, x1):
                b[x, y] = f[x, y]
    for grid, at in ((EYE_L, EYES_AT[0]), (EYE_R, EYES_AT[1])):
        G.check(grid, "EYE")
        G.stamp(base, grid, EYE_LEGEND, at)
    return base


def build():
    im = P.outline(assemble())          # the silhouette keyline, grown to 2
    return im.crop(im.getbbox())


if __name__ == "__main__":
    out = sys.argv[1]
    a = assemble()
    P.save_zoom(a, os.path.join(out, "danny_pose_1x_4x.png"), 4)
    import gridview as GV
    GV.grid(a, (56, 20, 120, 56), 14, os.path.join(out, "danny_pose_face_grid.png"))
    b = build()
    print("slap 2", P.numbers(frame(SLAP)), "sleep 0", P.numbers(frame(SLEEP)))
    print("pose", b.size, P.numbers(b))
