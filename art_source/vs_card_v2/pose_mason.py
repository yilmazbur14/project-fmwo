"""MASON - the nugget bucket hugged to his chest, grinning over the rim at Burak.

Built from his own pixels: mason_sheet.png frame 15, the bucket frame - the red-and-white bucket
held in front of him in both hands, the nuggets heaped to his chin, the open grin. That frame is
already the gesture and already lit from the upper left, so nothing is moved or mirrored: every
identifying feature is his sheet's own (the red comb, the yellow hood, the white earmuffs with their
+ and x, the brown face with the wide white eyes, teeth and tongue, the tan nugget arms).

One effect, also his own: frame 13's four-point sparkle, twice, either side of his comb.

Then Scale2x (pxkit), and the 2x pass (detail), the one thing the 1x frame has no room for: his
eyes. In the frame they are two 3 x 3 whites with a 1 px pupil at the bottom, looking down into the
bucket. On the card he looks over the rim at Burak, and the eyes are built the way Matt's are
(STYLE.md): a black lid along the top of each white, and a bigger black iris turned toward Burak,
up off the bucket. The whites keep their round Scale2x corners - still his wide "O_O" look. There is
no glint: on a white eye a 2-texel iris has no room for one that reads (the glint variants tried
read cross-eyed at 3x), so the white itself is the eye's light.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402
import grids as G                                                             # noqa: E402

SOURCE = "Mason/mason_sheet.png"
FRAME = 15
W = 64

# The 2x eyes, one grid each, over the Scale2x whites (2x frame coordinates, before the crop).
# '#' ink, 'w' his white, '.' leave the Scale2x pixel alone.
EYE = """
######
wwwwww
w##www
w##www
w##www
.wwww.
"""
EYES_AT = [(56, 34), (66, 34)]
LEGEND = {"#": "#000000", "w": "#FFFFFF"}


# The one effect (STYLE.md): the four-point sparkle his own sheet puts round his head when the nuggets
# are good (mason_sheet frame 13, rows 8-14), two of them, set either side of the comb at 1x so they
# get the same Scale2x as the rest of him.
SPARKLE = """
...#...
..#8#..
.##8##.
#88a88#
.##8##.
..#8#..
...#...
"""
SPARKLE_LEGEND = {"#": "#000000", "8": "#FBF236", "a": "#FFFFFF"}
SPARKLES_AT = [(9, 4), (47, 1)]


def frame():
    f = P.load(SOURCE, (FRAME * W, 0, FRAME * W + W, W))
    G.check(SPARKLE, "SPARKLE")
    for at in SPARKLES_AT:
        G.stamp(f, SPARKLE, SPARKLE_LEGEND, at)
    return f


def source():
    return P.load(SOURCE, (FRAME * W, 0, FRAME * W + W, W))


def detail(im):
    G.check(EYE, "EYE")
    for at in EYES_AT:
        G.stamp(im, EYE, LEGEND, at)
    return im


def build():
    im = detail(P.scale2x(frame()))
    return im.crop(im.getbbox())


if __name__ == "__main__":
    out = sys.argv[1]
    b = build()
    P.save_zoom(b, os.path.join(out, "mason_pose_2x_4x.png"), 4)
    import gridview as GV
    full = detail(P.scale2x(frame()))
    GV.grid(full, (44, 24, 84, 62), 16, os.path.join(out, "mason_pose_face_grid.png"))
    print("source", P.numbers(source()))
    print("2x", b.size, P.numbers(b))
