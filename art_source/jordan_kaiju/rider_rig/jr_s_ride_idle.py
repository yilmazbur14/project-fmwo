"""jordan_ride_idle: 4 frames, looping (0.2, 0.16, 0.2, 0.16). Astride the kaiju's head, the open box
held up beside his face, the other hand on his hip, admiring the box.

  0  the approved rider, pixel for pixel (approval/kaiju_mounted_idle.aseprite, layer 'rider')
  1  breath out: everything above the seat sinks a pixel; the dangling sneaker swings back a pixel
  2  still sunk, the sneaker back under him, a glint off the box's swung-out window panel
  3  breathing back in to the approved height, the sneaker swinging a pixel forward

The approved rider keeps his near hand on his hip (not on a plate), so the loop does too.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_rider as RR  # noqa: E402
import jr_sheet as S   # noqa: E402

NAME = 'jordan_ride_idle'
TIMES = [0.2, 0.16, 0.2, 0.16]
LOOP = True
KIND = 'ride'
OFFSET = (-5, 5)             # build -> frame: the seat texel (49, 70) lands on (44, 75)
NOTE = ('SEAT is the texel that sits on the kaiju RIDER_SEAT; f0 == the approved rider layer cropped at '
        'kaiju-frame offset (83, -10) (rider layer px (x, y) -> sheet (x - 83, y + 10)).')


def sparkle(cx, cy):
    out = {(cx, cy): 'W'}
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out[(cx + dx, cy + dy)] = 'Q'
    return out


def ride_anchors(fig, extra=None):
    a = {'SEAT': F.SEAT_PT, 'CROWN': S.crown(fig.px, fig.pts['head'])}
    if extra:
        a.update(extra)
    return a


def to_frame(fig, extra=None, note=''):
    return S.to_frame(fig, OFFSET, ride_anchors(fig, extra), note=note)


def build(i):
    if i == 0:
        return RR.rider(approved=True), 'the approved rider'
    if i == 1:
        return RR.rider(up=(0, 1), shin=(-1, 0)), 'breath out, sneaker swings back'
    if i == 2:
        fig = RR.rider(up=(0, 1), shin=(0, 0))
        fig.fxput(sparkle(83, 28), under=True)            # off the swung-out panel (the approved idle's glint)
        return fig, 'sunk, a glint off the box'
    fig = RR.rider(up=(0, 0), shin=(1, 0))
    return fig, 'breath in, sneaker swings forward'


def frames():
    out = []
    for i in range(4):
        fig, note = build(i)
        fr = to_frame(fig, note=note)
        S.fill_holes(fr.px)
        if i == 0:
            # the approved rider's one heel pixel that sat over the kaiju's skin, kept as approved
            fr.allow_gaps = {(44, 88)}
            fr.note += '; the heel pixel (44, 88) touches the kaiju behind it, as approved'
        out.append(fr)
    return out


def check_f0():
    """f0 must be the approved rider layer, pixel for pixel, at the documented offset."""
    from PIL import Image
    ref = Image.open(os.path.join(C.RIDER, 'ref', 'kaiju_mounted_idle_rider.png')).convert('RGBA')
    fr = frames()[0]
    im = Image.new('RGBA', ref.size, (0, 0, 0, 0))
    for (x, y), k in fr.px.items():
        im.putpixel((x + 83, y - 10), C.PAL[k])
    return C.pixel_diff(im, ref)


if __name__ == '__main__':
    print('f0 vs the approved rider layer:', check_f0() or 'IDENTICAL')
