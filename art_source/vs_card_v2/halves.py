"""The two halves of the band, drawn for poses instead of busts - the contained Platinum rule.

Same block, seam and rules as the shipped halves (art_source/vs_card/card.py band_halves, imported
read-only and never modified), and the same 640 x 132 at BAND_AT, so they drop into the game as-is.
One thing changes: the layering, because a pose can now reach the seam.

    block (ramp, emblem, speed line) -> pose + drop halo, CLIPPED to its own half -> the seam's black
    rule and accent hairlines -> the top and bottom rules

So a pose is framed by its half on all three sides the way Platinum's VS portraits are: cropped by
the top and bottom rules, cut by the seam (Eric's blade stops at it), never over the other half.
With the shipped busts - which never reach the seam - this order rebuilds the shipped halves byte
for byte, which the __main__ check proves.
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "vs_card"))
import layout as LY                                                           # noqa: E402
import card as C                                                              # noqa: E402  (read-only)
import emblems                                                                # noqa: E402  (read-only)
from pxlib import hx, poly                                                    # noqa: E402  (read-only)

W, BH = LY.BAND_W, LY.BAND_H
ST, SB = LY.SPLIT_TOP, LY.SPLIT_BOTTOM
INK = "#000000"
BURAK_RAMP = ["#15131F", "#222034", "#2E2C4A", "#3F3F74", "#3A5BA8"]
BURAK_STRIPE = "#3A5BA8"


def _mask(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([tuple(q) for q in pts], fill=255)
    return m


def left_pts(oy):
    return [(0, oy), (ST, oy), (SB, oy + BH), (0, oy + BH)]


def right_pts(oy, grow=0):
    return [(ST - grow, oy), (W, oy), (W, oy + BH), (SB - grow, oy + BH)]


def _top_rule(size, oy, mask):
    r = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(r)
    d.rectangle([0, oy, W - 1, oy + 2], fill=hx(INK))
    d.line([(0, oy + 3), (W - 1, oy + 3)], fill=hx("#4A4A82"))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(r, (0, 0), mask)
    return out


def _bottom_rule(size, oy, mask):
    r = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(r)
    d.rectangle([0, oy + BH - 3, W - 1, oy + BH - 1], fill=hx(INK))
    d.line([(0, oy + BH - 4), (W - 1, oy + BH - 4)], fill=hx("#0B0A12"))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(r, (0, 0), mask)
    return out


def _pose_layer(size, pose, at, halo=True):
    """The pose with the shipped drop halo (C.drop_halo: #0B0A12, offset 3,3, spread 1) under it."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    if halo:
        C.drop_halo(layer, pose, at)
    layer.alpha_composite(pose, at) if at[0] >= 0 and at[1] >= 0 else layer.paste(pose, at, pose)
    return layer


def left_block(oy, ramp=BURAK_RAMP, stripe=BURAK_STRIPE):
    size = (W, BH + oy)
    lc = C.banded(W, BH, ramp, -58, 9)
    ImageDraw.Draw(lc).line([(ST - 13, 0), (SB - 13, BH)], fill=hx(stripe), width=2)
    L = Image.new("RGBA", size, (0, 0, 0, 0))
    L.paste(lc, (0, oy), _mask((W, BH), left_pts(0)))
    return L


def _clipped(layer, mask):
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.paste(layer, (0, 0), mask)
    return out


def _seam(size, accent):
    """The seam's border on its own layer, so it goes over the poses like a panel's frame: the black
    rule and the two accent hairlines (card.band_halves draws the same three)."""
    R = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(R)
    d.line([(ST, 0), (SB, BH)], fill=hx(INK), width=5)
    d.line([(ST + 4, 0), (SB + 4, BH)], fill=hx(accent[0]), width=2)
    d.line([(ST + 6, 0), (SB + 6, BH)], fill=hx(accent[1]), width=1)
    return R


def _speed_line(block):
    """The white speed line parallel to the seam belongs to the block's graphic, so it goes UNDER
    the pose (card.band_halves draws it at +22 texels from the seam)."""
    ImageDraw.Draw(block).line([(ST + 22, 0), (SB + 22, BH)], fill=hx("#EAF0F6"), width=1)


def left_half(pose, at, ramp=BURAK_RAMP, stripe=BURAK_STRIPE):
    """Burak's half. `at` is the pose's top-left in the band. The pose is clipped to the half."""
    size = (W, BH)
    lm = _mask(size, left_pts(0))
    L = left_block(0, ramp, stripe)
    L.alpha_composite(_clipped(_pose_layer(size, pose, at), lm))
    L.alpha_composite(_top_rule(size, 0, lm))
    L.alpha_composite(_bottom_rule(size, 0, lm))
    return L


def right_half(pose, at, ramp, accent, mark, under=None, over=None):
    """A boss's half: the block and its emblem, the pose clipped to the half, then the seam and the
    rules over it. `under` draws on the block before the pose, `over` on the pose before the seam."""
    size = (W, BH)
    rm = _mask(size, right_pts(0))
    R = Image.new("RGBA", size, (0, 0, 0, 0))
    block = right_block_plain(ramp, mark)
    _speed_line(block)
    if under:
        under(block, 0)
    R.paste(block, (0, 0), rm)
    layer = _pose_layer(size, pose, at)
    if over:
        over(layer, 0)
    R.alpha_composite(_clipped(layer, rm))
    R.alpha_composite(_seam(size, accent))
    rmg = _mask(size, right_pts(0, grow=3))
    R.alpha_composite(_top_rule(size, 0, rmg))
    R.alpha_composite(_bottom_rule(size, 0, rmg))
    return R


def right_block_plain(ramp, mark):
    """The boss's banded block with its ghosted emblem, full width, unmasked."""
    rc = C.banded(W, BH, ramp, -58, 11, flip=True)
    shape, mc, ma = mark
    wm = Image.new("RGBA", (W, BH), (0, 0, 0, 0))
    if shape == "rings":
        # Matt's roar: three sound rings in the emblems' own box (centre 0.80w, half-size 0.40h).
        # vs_card/emblems.py is read-only, so this one shape lives here.
        cx, cy, arm = int(W * 0.80), BH // 2, int(BH * 0.40)
        d = ImageDraw.Draw(wm)
        for r, width in ((arm, 7), (int(arm * 0.66), 6), (int(arm * 0.34), 5)):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=hx(mc), width=width)
    for pts in ([] if shape == "rings" else emblems.emblem(shape, W, BH)):
        poly(wm, pts, mc)
    wm.putalpha(wm.split()[3].point(lambda v: ma if v else 0))
    rc.alpha_composite(wm)
    return rc


def legacy_check():
    """The shipped Eric halves, rebuilt HERE - this module's block, seam, rules and layering - from
    the shipped busts. Both must come out identical to Assets/UI/VsCard, which proves the only thing
    the new halves change is what stands in them."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    from imgdiff import pixel_diff
    burak = Image.open(LY.SHIPPED + "bust_burak.png").convert("RGBA")
    eric = Image.open(LY.SHIPPED + "bust_eric.png").convert("RGBA")
    L = left_half(burak, (86, 14))
    R = right_half(eric, (404, 14), ["#525A74", "#7A86A0", "#A3B1C2", "#CDD7E2", "#EAF0F6"],
                   ("#C48A2C", "#F2C457"), ("cross", "#B0242A", 52))
    sl = Image.open(LY.SHIPPED + "band_left.png").convert("RGBA")
    sr = Image.open(LY.SHIPPED + "band_right_eric.png").convert("RGBA")
    return pixel_diff(L, sl), pixel_diff(R, sr)


if __name__ == "__main__":
    dl, dr = legacy_check()
    print("shipped band_left rebuilt:", dl or "identical")
    print("shipped band_right_eric rebuilt:", dr or "identical")
