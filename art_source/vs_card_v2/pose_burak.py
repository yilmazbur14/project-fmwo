"""BURAK - the fist up: the Pokémon trainer's VS pose, on the boxer.

The one drawn figure on the cards. His sprite is 15x25 px; filling a pose from it would need 5x
blocks. So he is drawn - but drawn the way the bosses' poses are made, so he sits on the card at
their density (STYLE.md): as a SPRITE at the bosses' sprite scale (a head about Eric's), then the
same Scale2x the bosses get.

Identity, exact, from player_4dir_sheet.png and the approved bust_burak.png: black spiky hair, a
red headband with two trailing tails, bare boxer's build, blue gloves, and no white anywhere - so no
sclera and no catchlight; his eyes stay dark shapes cut into skin. Ramps are the approved bust's.

The pose, by the user's direction (2026-09-23): "something generic like pokemon does it where its
just a fist up pose of the actual character". Waist-up, three-quarters to the VS, calm and set, his
lead glove raised close in front of his chest in the foreground - Lucas's VS portrait, gloved. The
other arm hangs out of frame. The headband tails trail back behind him.

Lit from the upper LEFT like every VS pose (STYLE.md): the broad side of his face and the near
shoulder take the light, the glove's upper left carries its shine.

Coordinates are 1x: half the band (320 x 132 -> 160 x 66) plus the reach to the seam, 176 x 66.
Every limb and muscle is its own keylined form; muscle-on-muscle lines are a dark skin tone, limb
over body is black (Josh's and Carter's sprites separate theirs the same way).
"""
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402
import grids as G                                                             # noqa: E402
import burak_head as BH                                                       # noqa: E402
import burak_glove as BG                                                      # noqa: E402
from volume import Painter, rgba, LIGHT                                       # noqa: E402

SK_HI, SK_LT, SK, SK_MD, SK_SH, SK_DK = "#F0BE8C", "#E2A874", "#D79864", "#BE8254", "#AC714F", "#7A4A33"
BL_HI, BL_LT, BL, BL_MD, BL_DK = "#6BA8E0", "#3883C9", "#2464BD", "#162FBB", "#0E1C72"
BA_HI, BA, BA_DK = "#D95763", "#AC3232", "#6E1F22"
HR_LT, HR, BK = "#2E2E3A", "#1A1A22", "#000000"
PALETTE = [SK_HI, SK_LT, SK, SK_MD, SK_SH, SK_DK, BL_HI, BL_LT, BL, BL_MD, BL_DK,
           BA_HI, BA, BA_DK, HR_LT, HR, BK]
W1, H1 = 176, 66
# 3-4 tones a material (STYLE.md): shadow, mid, base, light; the rim/shine is the one accent
SKIN4, SKIN_CUTS = [SK_SH, SK_MD, SK, SK_LT], [-0.20, 0.22, 0.60]
BLUE4, BLUE_CUTS = [BL_DK, BL_MD, BL, BL_LT], [-0.25, 0.18, 0.62]
RED3, RED_CUTS = [BA_DK, BA, BA_HI], [0.00, 0.62]
HAIR3, HAIR_CUTS = [BK, HR, HR_LT], [-0.35, 0.55]


class Sheet:
    """A 1x canvas painted in keylined, cel-shaded forms."""

    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.masks = {}
        self._tone = Painter(1, 1).tone

    def mask(self, pts):
        m = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(m).polygon([tuple(q) for q in pts], fill=255)
        return m

    def form(self, name, pts, ramp, bulge, cuts, ring=BK, clip=None):
        """A shape ringed by a 1-texel line (`ring`), cel-shaded by its bulge under LIGHT. `clip`
        keeps the ring inside another form (muscle lines stop at the body's own silhouette)."""
        m = self.mask(pts)
        if ring:
            grown = m.filter(ImageFilter.MaxFilter(3))
            if clip:
                grown = ImageChops.multiply(grown, self.masks[clip])
            self.im.paste(rgba(ring), (0, 0), grown)
        rr = [rgba(c) for c in ramp]
        a, mk = self.im.load(), m.load()
        bb = m.getbbox()
        if bb:
            for y in range(bb[1], bb[3]):
                for x in range(bb[0], bb[2]):
                    if mk[x, y] > 128:
                        a[x, y] = self._tone(x, y, bulge, rr, cuts, LIGHT)
        self.masks[name] = m
        return m

    def rim(self, name, colour, dirs=((-1, 0), (-1, -1), (0, -1)), only=None, rows=None):
        """One texel of light along the edge of `name` that faces the light (upper left)."""
        mk = self.masks[name].load()
        a = self.im.load()
        w, h = self.im.size
        only = {rgba(o) for o in only} if only else None
        hits = []
        bb = self.masks[name].getbbox()
        for y in range(bb[1], bb[3]):
            if rows and not (rows[0] <= y < rows[1]):
                continue
            for x in range(bb[0], bb[2]):
                if mk[x, y] <= 128:
                    continue
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or mk[nx, ny] <= 128:
                        if only is None or a[x, y] in only:
                            hits.append((x, y))
                        break
        for q in hits:
            a[q] = rgba(colour)

    def px(self, pts, colour):
        a = self.im.load()
        for (x, y) in pts:
            if 0 <= x < self.im.width and 0 <= y < self.im.height:
                a[x, y] = rgba(colour)

    def line(self, pts, colour=BK, inside=None):
        m = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(m).line([tuple(q) for q in pts], fill=255, width=1)
        if inside:
            m = ImageChops.multiply(m, self.masks[inside])
        self.im.paste(rgba(colour), (0, 0), m)


# ---- the forms at 1x, back to front ------------------------------------------------------------
TAIL_A = [(74, 15), (64, 11), (53, 7), (42, 5), (32, 6), (38, 10), (48, 12), (58, 15), (68, 20)]
TAIL_B = [(73, 21), (63, 23), (52, 24), (41, 25), (30, 29), (37, 31), (49, 30), (61, 29), (72, 27)]
# chibi proportions, as the house sprites have them: shoulders under two head-widths
TORSO = [(80, 44), (90, 39), (104, 37), (118, 38), (128, 42), (134, 52), (136, 66), (76, 66)]
TRAP = [(99, 36), (90, 39), (82, 43), (88, 45), (99, 43)]
DELT = [(70, 60), (71, 50), (75, 44), (82, 41), (90, 43), (94, 49), (93, 56), (88, 61), (78, 63)]
UPPER = [(72, 58), (80, 62), (90, 60), (92, 66), (72, 66)]
PEC_NEAR = [(92, 46), (100, 43), (108, 44), (110, 51), (106, 56), (96, 56), (92, 52)]
PEC_FAR = [(110, 44), (118, 43), (125, 47), (124, 54), (116, 56), (110, 53)]
ABS = [[(96, 58), (103, 58), (103, 63), (96, 63)], [(105, 58), (111, 58), (111, 63), (105, 63)],
       [(96, 64), (103, 64), (103, 67), (96, 67)], [(105, 64), (111, 64), (111, 67), (105, 67)]]
FORE = [(114, 58), (128, 57), (130, 66), (113, 66)]
NECK = [(98, 30), (113, 30), (116, 44), (96, 45)]
HAIR = [(84, 32), (80, 26), (78, 18), (75, 12), (71, 6), (78, 8), (78, 1), (85, 5), (88, -1),
        (94, 4), (99, 0), (103, 5), (109, 2), (111, 8), (117, 6), (116, 11), (121, 12), (121, 15),
        (112, 15), (102, 15), (95, 17), (94, 22), (92, 21), (88, 18), (88, 28), (88, 32)]
BAND = [(84, 17), (92, 14), (102, 13), (111, 13), (119, 14), (120, 19), (111, 18), (102, 18),
        (93, 20), (86, 23)]
KNOT = [(71, 15), (78, 12), (83, 16), (81, 22), (74, 23)]


DY = 5              # the whole figure, so his eyes sit on the shared eye line (STYLE.md)


def dn(pts):
    return [(x, y + DY) for x, y in pts]


def sprite():
    s = Sheet(W1, H1)
    s.form("tail_a", dn(TAIL_A), RED3, (54, 15, 24, 8), RED_CUTS)
    s.form("tail_b", dn(TAIL_B), RED3, (52, 31, 24, 5), RED_CUTS)
    # the body: one keylined mass, then its muscles cut into it with skin-shadow lines
    s.form("torso", dn(TORSO), SKIN4, (102, 51, 36, 22), SKIN_CUTS)
    s.form("pec_far", dn(PEC_FAR), SKIN4, (114, 51, 12, 9), SKIN_CUTS, ring=SK_SH, clip="torso")
    s.form("pec_near", dn(PEC_NEAR), SKIN4, (98, 51, 12, 10), SKIN_CUTS, ring=SK_SH, clip="torso")
    for i, ab in enumerate([dn(a) for a in ABS]):
        bb = s.mask(ab).getbbox()
        if bb is None:
            continue                    # below the band's bottom rule
        s.form("abs%d" % i, ab, SKIN4, ((bb[0] + bb[2]) / 2.0 - 2, bb[1] + 1.0, 6, 4), SKIN_CUTS,
               ring=SK_MD, clip="torso")
    s.form("trap", dn(TRAP), SKIN4, (90, 43, 10, 5), SKIN_CUTS, ring=SK_SH, clip="torso")
    s.form("neck", dn(NECK), SKIN4[:3], (102, 39, 12, 12), SKIN_CUTS[:2])
    s.line(dn([(97, 45), (116, 44)]), SK_SH)            # the neck meets the chest in shadow, not ink
    s.form("delt", dn(DELT), SKIN4, (80, 53, 13, 12), SKIN_CUTS)
    s.form("upper", dn(UPPER), SKIN4, (80, 65, 12, 8), SKIN_CUTS)
    # the head: the face grid, then hair, the ear again (it sits in front of the hair), the band
    G.check(BH.FACE, "face")
    G.stamp(s.im, BH.FACE, BH.LEGEND, BH.FACE_AT)
    s.form("hair", dn(HAIR), HAIR3, (96, 9, 22, 16), HAIR_CUTS)
    ear = chr(10).join(ln[:BH.EAR_COLS] for ln in G.rows(BH.FACE))
    G.stamp(s.im, ear, BH.LEGEND, BH.FACE_AT)
    s.form("band", dn(BAND), RED3, (100, 19, 18, 5), RED_CUTS)
    s.form("knot", dn(KNOT), RED3, (76, 20, 6, 5), RED_CUTS)
    s.form("fore", dn(FORE), SKIN4, (118, 63, 10, 8), SKIN_CUTS)
    lights(s)
    # the raised lead glove, in front of everything
    G.check(BG.GLOVE, "glove")
    G.stamp(s.im, BG.GLOVE, BG.LEGEND, BG.GLOVE_AT)
    return s.im


def lights(s):
    """The one accent a material gets over its 3-4 tones: a texel of light on its lit edge."""
    s.rim("hair", HR_LT, rows=(-10, 15 + DY))
    s.rim("tail_a", BA_HI, dirs=((0, -1),))
    s.rim("tail_b", BA_HI, dirs=((0, -1),))
    for n in ("delt",):
        s.rim(n, SK_HI, only=[SK_LT])


def build():
    return P.lock(P.scale2x(sprite()), PALETTE)


if __name__ == "__main__":
    out = sys.argv[1]
    s = sprite()
    P.save_zoom(s, os.path.join(out, "burak_fist_1x_8x.png"), 8)
    im = build()
    P.save_zoom(im, os.path.join(out, "burak_fist_2x_4x.png"), 4)
    print("1x", P.numbers(s), "2x", P.numbers(im))
