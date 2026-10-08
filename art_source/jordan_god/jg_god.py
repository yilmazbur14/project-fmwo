"""Demon-god Jordan, final: A2 (the full mask), no fire column (the user's pick, 2026-09-28).

The full set, every frame drawn from the approved A2 rig (jg_lord) at a Pose:
  hover  6 frames, 320x224, anchor (160, 223); a bob of up to 3 texels drawn in (0,1,2,3,2,1 rows
         up), the wings breathing a beat behind the body, the tail swinging behind that, each crown
         horn licking on its own beat, the core and the lava cracks swelling once per loop, embers
         riding up off the crown and the tail. With no fire column under him, a lava seam runs
         down the tail so his lower half reads hanging in the void.
  talk   2 frames in hover frame 0's pose: the furnace grin shut, then open and flaring.
  aura   6 frames, additive, no keyline: a warm haze ring outside his silhouette, frame-locked
         to the hover (same bob), breathing with the core.

Nothing here writes a file (jg_export does).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402
import jg_lord as L  # noqa: E402
from jg_lord_pal import PAL_A2  # noqa: E402

W, H = L.W, L.H
ANCHOR = L.ANCHOR
N = 6
BOB = [0, 1, 2, 3, 2, 1]          # rows up, per frame: a 3-texel bob drawn in
FRAME_TIME = 0.14                 # seconds per hover frame (the contract allows 0.12-0.16)

# embers: (x, y at birth, drift per frame, frame of birth); each lives 4 frames, rising 2 rows
# a frame and cooling O -> r -> T -> R. Births are staggered so a few are always in the air.
EMBER_LIFE = ('O', 'r', 'T', 'R')
EMBERS = [
    (132, 66, -0.3, 0), (143, 55, 0.2, 2), (152, 52, -0.2, 4), (178, 44, 0.4, 1),
    (187, 66, 0.3, 3), (176, 57, -0.2, 5), (125, 104, -0.3, 1), (194, 104, 0.3, 4),
    (136, 196, -0.2, 2), (184, 203, 0.2, 5), (201, 200, 0.2, 0), (147, 208, -0.3, 3),
]


def ember_specks(frame):
    out = []
    for (x0, y0, drift, born) in EMBERS:
        age = (frame - born) % N
        if age < len(EMBER_LIFE):
            x = int(round(x0 + drift * age))
            y = y0 - 2 * age
            out.append((x, y, EMBER_LIFE[age]))
    return out


def pose(frame, mouth_open=False):
    ph = 2 * math.pi * frame / N
    return L.Pose(
        wing_lift=2.0 * math.sin(ph),                 # down on the rise, up on the fall: a breath
        wing_spread=-0.035 * math.sin(ph),            # the fan folds a little on the downstroke
        flame=ph,                                     # each horn licks on its own beat
        glow=1.0 + 0.12 * math.cos(ph),               # cracks swell once a loop
        core=1.0 + 0.10 * math.cos(ph),               # the core breathes with them
        tail_sway=1.8 * math.sin(ph - 1.6),           # the tail swings a beat behind the wings
        tail_seam=True,
        mouth_open=mouth_open,
        embers=ember_specks(frame),
    )


def _bobbed(px, bob):
    return {(x, y - bob): k for (x, y), k in px.items() if 0 <= y - bob < H}


def hover_px(frame):
    return _bobbed(L.build('A2', pose(frame), seat=False), BOB[frame % N])


def talk_px(open_):
    return _bobbed(L.build('A2', pose(0, mouth_open=open_), seat=False), BOB[0])


def effect_pixels(frame):
    """Texels that are effects by design (embers), so the audit does not call them strays."""
    return {(x, y - BOB[frame % N]) for (x, y, k) in ember_specks(frame)}


# ------------------------------------------------------------------ aura (additive)

AURA = {
    'x': B.hx('3E0E0A'),     # nearest the body
    'y': B.hx('2A0907'),
    'z': B.hx('160404'),     # the outer breath
}


AURA_PAD = 8                                   # the aura frame is 8 texels bigger on each side
AURA_W, AURA_H = W + 2 * AURA_PAD, H + AURA_PAD   # 336x232: no haze is ever clipped
AURA_ANCHOR = (ANCHOR[0] + AURA_PAD, ANCHOR[1])  # (168, 223): the same point as his anchor


def aura_px(frame):
    """A warm haze ring outside his silhouette: 2 texels of the brightest step, then two more,
    breathing a texel wider when the core swells, then a thinning checker. Additive: the dark
    reds only add light. In the aura's own frame (AURA_W x AURA_H, anchor AURA_ANCHOR)."""
    body = hover_px(frame)
    solid = {(x + AURA_PAD, y) for (x, y) in body}
    ph = 2 * math.pi * frame / N
    extra = 1 if math.cos(ph) > 0.3 else 0
    rings = [('x', 2), ('y', 2 + extra), ('z', 2)]
    out = {}
    frontier = set(solid)
    seen = set(solid)
    for key, width in rings:
        for _ in range(width):
            nxt = set()
            for p in frontier:
                for q in B.neighbours8(p):
                    if q not in seen and 0 <= q[0] < AURA_W and 0 <= q[1] < AURA_H:
                        nxt.add(q)
            for q in nxt:
                if key == 'z' and (q[0] + q[1]) % 2:
                    continue            # the outermost step is a checker: the haze thins out
                out[q] = key
            seen |= nxt
            frontier = nxt
    return out


# ------------------------------------------------------------------ images

def strip(frames_px, pal, w=W, h=H):
    from PIL import Image
    im = Image.new('RGBA', (w * len(frames_px), h), (0, 0, 0, 0))
    for i, px in enumerate(frames_px):
        im.alpha_composite(B.image(px, w, h, pal), (i * w, 0))
    return im


def hover_image():
    return strip([hover_px(i) for i in range(N)], PAL_A2)


def talk_image():
    return strip([talk_px(False), talk_px(True)], PAL_A2)


def aura_image():
    return strip([aura_px(i) for i in range(N)], AURA, AURA_W, AURA_H)


if __name__ == '__main__':
    out = sys.argv[1]
    im = hover_image()
    B.up(im, 2, bg=(14, 10, 24, 255)).save(os.path.join(out, 'god_hover_2x.png'))
    for i in range(N):
        px = hover_px(i)
        print('frame', i, 'lowest row', max(y for (x, y) in px), 'top row', min(y for (x, y) in px))
