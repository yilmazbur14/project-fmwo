"""Computah's 64x64 dialogue portrait / VS-card bust.

WHY IT IS BUILT AND NOT DRAWN
`VsCardArtLayout.CARDS["computah"]["portrait"]` points at
Assets/Characters/Computah/portrait.png, which did not exist, so his half of the
pre-fight card drew no bust at all.  The house rule for anything derived from a
character (see the Eric bust that had to be re-done) is that it must hit the SOURCE
SHEET'S MEASURED NUMBERS - keyline ratio and colour count - and that the way to get
there is to start from the character's own pixels rather than to redraw him small:
a redraw makes three-pixel eyes into slabs and he stops being himself.

So the base is a straight 1:1 crop of computah_idle.png frame 0 - the full-charge
row, which is the only one whose antenna ball is green - at (16, 8).  That crop is
chosen, not arbitrary: it is the one framing that gets the antenna ball, both
ear-pods, the red LED eyes, the toothy grin, both pauldrons AND the whole four-cell
capacitor (its frame rows land exactly on 53 and 63) inside 64x64 with the bust
bleeding off the bottom edge the way every other boss portrait does.  1:1 means zero
rescale distortion: every feature is literally his.

WHAT IS ADDED ON TOP
A crop alone carries the same density as the sprite, and derived art is supposed to
carry more.  The passes below are the ones the Eric bust needed - a keyline pass that
separates the shapes the 96x96 sprite had to merge, a rim light where a plate meets
its keyline on the lit (upper-left) side and a dark edge under it, and the face
detail a portrait has room for and a fighting sprite does not.  No feature is
invented: every colour is one he already carries on a shipped sheet, and the only
silhouette change is closing the antenna ball's crown, which the crop cut.

TARGETS, MEASURED
computah_idle.png runs 21.2-21.6% #0C111A over 27-29 colours with zero pure black.
`measure()` prints this portrait's numbers against that so a later edit cannot drift.

  python portrait.py            # rebuild and measure
  python portrait.py --ship     # ...and copy to Assets/Characters/Computah
"""
import os
import shutil
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHIP = os.path.join(HERE, "..", "..", "Assets", "Characters", "Computah")
SOURCE = os.path.join(SHIP, "computah_idle.png")

CROP = (16, 8)          # top-left of the 64x64 window into idle frame 0
KEYLINE = (0x0C, 0x11, 0x1A)

# Every colour below appears on a shipped Computah sheet.  The letters are the ones
# the working grids in this topic use.
PAL = {
    "#": "#0C111A",                                             # keyline
    "9": "#C892F2", "8": "#A063DC", "7": "#7C3BB4",              # armour purple
    "6": "#592687", "5": "#391555",
    "F": "#F2F8FF", "E": "#D8E4F2", "C": "#CEDCEA", "A": "#A6B8CC",   # shell
    "B": "#8091A8", "S": "#5E6C82", "s": "#3F4A5C",
    "D": "#6C7A8E", "d": "#3C4757", "t": "#2A3341", "T": "#1A212C",   # recesses
    "g": "#2B3444", "G": "#222A38", "h": "#1A202B",              # faceplate glass
    "H": "#131821", "J": "#0D1118",
    "a": "#A9FFB4", "e": "#4FE066", "n": "#1F9A38", "N": "#2A7A3C",   # capacitor
    "R": "#FF4436", "r": "#93302C",                              # LED eyes
    # The one colour the portrait adds, lifted off computah_beam_charge.png:
    "o": "#FF7055",                                              # eye bloom
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PAL.items()}


class Art:
    def __init__(self, im):
        self.im = im
        self.px = im.load()

    def run(self, y, x0, x1, key):
        """One horizontal run, inclusive.  `.` clears to transparent."""
        for x in range(x0, x1 + 1):
            self.px[x, y] = (0, 0, 0, 0) if key == "." else RGB[key] + (255,)

    def col(self, x, y0, y1, key):
        for y in range(y0, y1 + 1):
            self.px[x, y] = (0, 0, 0, 0) if key == "." else RGB[key] + (255,)

    def dots(self, key, *pts):
        for x, y in pts:
            self.px[x, y] = (0, 0, 0, 0) if key == "." else RGB[key] + (255,)

    def over(self, y, x0, x1, key, only):
        """Like run(), but only where the pixel is currently one of `only` - how the
        rim light is laid without eating the shape next to it."""
        want = {RGB[k] for k in only}
        for x in range(x0, x1 + 1):
            p = self.px[x, y]
            if p[3] > 128 and p[:3] in want:
                self.px[x, y] = RGB[key] + (255,)


def build():
    src = Image.open(SOURCE).convert("RGBA").crop((0, 0, 96, 96))
    art = Art(src.crop((CROP[0], CROP[1], CROP[0] + 64, CROP[1] + 64)))

    _antenna(art)
    _face(art)
    _keyline(art)
    _rim(art)
    _chest(art)
    return art.im


# ---------------------------------------------------------------------------
def _antenna(a):
    """The crop cuts the ball's crown off at row 0, which leaves the silhouette
    open.  Close it: the top row becomes the ball's outline, so the orb is whole and
    one row shorter rather than sliced."""
    a.run(0, 3, 7, "#")


def _face(a):
    """The eyes are six pixels of red each and they are most of who he is, so nothing
    here touches their shape.  What a portrait adds is what the glass does with them:
    a lit corner inside each lens, the shadow each one drops onto the plate, and the
    brow's own shadow across the rest of it."""
    for ex in (20, 36):                          # the two LED blocks, x ex..ex+5
        a.dots("o", (ex + 1, 21), (ex + 2, 21))  # lit corner of the lens
        a.run(26, ex, ex + 5, "#")               # the shadow it drops on the glass
    # The brow bar overhangs the plate, so it shades the glass everywhere the LEDs
    # are not - which is also what lines the top of the lenses up with the brow.
    a.run(20, 17, 19, "#")
    a.run(20, 26, 35, "#")
    a.run(20, 42, 44, "#")
    # A bezel glint down the plate's lit edge, and the light the lower bar bounces
    # back up into the glass.  One step each, not a gradient: this is still glass,
    # and anything busier reads as dirt at the 1.5x the VS card draws him at.
    a.col(17, 21, 25, "g")
    a.col(17, 27, 31, "g")
    a.over(31, 18, 43, "g", "G")


def _keyline(a):
    """The separations the 96x96 sprite had no room for.  Every one is between two
    parts that are already there - nothing here draws a new part."""
    # The helmet's left flare is the same purple as the dome behind it, told apart
    # only by a tone step.  Close up that wants an edge.
    a.dots("#", (19, 15), (20, 15), (19, 16), (19, 17))
    # The ear-pod grilles are a flat slot on the sprite.  Dropping their lower half a
    # step gives them a floor, which is the only reason they read as holes.
    a.over(31, 9, 12, "T", "t")
    a.over(31, 49, 52, "T", "t")
    # The collar under the neck is four flat rows of purple on the sprite; a seam at
    # its waist reads as the two plates the body actually has.
    a.run(49, 18, 39, "#")
    a.dots("#", (40, 49), (41, 49))


def _rim(a):
    """1px lit edge where a plate meets its keyline on the upper-left, 1px dark edge
    under it on the lower-right.  This is the pass that turns a flat crop into
    volume, and it is the one the Eric bust was missing.  Every run is guarded by the
    tones it is allowed to overwrite, so it cannot spill into the shape next door."""
    # Helmet dome: lit crown, shaded lower right.
    for y, x0, x1 in ((10, 29, 35), (11, 26, 31), (12, 24, 27), (13, 23, 25)):
        a.over(y, x0, x1, "9", "89")
    for y, x0, x1 in ((15, 42, 45), (16, 43, 47), (17, 44, 48)):
        a.over(y, x0, x1, "6", "7")
    # Ear-pods: the housings, not the grille discs, which are already modelled.
    a.over(25, 8, 10, "9", "8")
    a.over(26, 7, 8, "9", "8")
    a.over(27, 6, 7, "9", "8")
    a.over(25, 47, 48, "8", "7")
    a.over(26, 46, 47, "8", "7")
    # Pauldrons: the lit cap of each ball.
    a.over(44, 6, 10, "9", "8")
    a.over(45, 4, 6, "9", "8")
    a.over(43, 46, 49, "9", "8")
    a.over(44, 44, 46, "9", "8")
    # The jaw wedge catches the light along its top edge; its underside goes dark.
    a.over(35, 19, 26, "F", "CA")
    a.over(40, 22, 26, "B", "A")


def _chest(a):
    """The capacitor is the loudest thing he owns.  Close up it gets the light it
    throws back onto its own bezel."""
    a.over(52, 20, 42, "n", "7")
    a.over(53, 21, 42, "n", "N")
    a.dots("a", (21, 54), (21, 55))


# ---------------------------------------------------------------------------
def measure(im, label="portrait.png"):
    d = [p for p in im.convert("RGBA").get_flattened_data() if p[3] > 128]
    c = Counter(p[:3] for p in d)
    key = 100.0 * c[KEYLINE] / len(d)
    black = c.get((0, 0, 0), 0)
    print("%-16s opaque %4d  keyline %4.1f%%  colours %2d  pure black %d"
          % (label, len(d), key, len(c), black))
    return key, len(c), black


def sheet_band():
    """What his own sheets measure, per frame, so the portrait is judged against the
    art it is derived from and not against a rule of thumb."""
    lo_k, hi_k, lo_n, hi_n = 100.0, 0.0, 99, 0
    for name in ("computah_idle.png", "computah_run.png", "computah_beam_fire.png",
                 "computah_hit.png", "computah_defeat.png", "computah_uppercut.png"):
        im = Image.open(os.path.join(SHIP, name)).convert("RGBA")
        px = im.load()
        for f in range(im.width // 96):
            c = Counter(px[x, y][:3] for y in range(96)
                        for x in range(f * 96, (f + 1) * 96) if px[x, y][3] > 128)
            k = 100.0 * c[KEYLINE] / sum(c.values())
            lo_k, hi_k = min(lo_k, k), max(hi_k, k)
            lo_n, hi_n = min(lo_n, len(c)), max(hi_n, len(c))
    return lo_k, hi_k, lo_n, hi_n


def main(ship=False):
    im = build()
    out = os.path.join(HERE, "computah_portrait.png")
    im.save(out)
    k, n, black = measure(im)
    lk, hk, ln, hn = sheet_band()
    print("%-16s              %4.1f-%4.1f%%          %2d-%2d          0"
          % ("his sheets", lk, hk, ln, hn))
    bad = black or not (lk <= k <= hk) or not (ln <= n <= hn)
    print("IN BAND" if not bad else "OUT OF BAND")
    if ship and not bad:
        shutil.copyfile(out, os.path.join(SHIP, "portrait.png"))
        print("shipped portrait.png")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main("--ship" in sys.argv))
