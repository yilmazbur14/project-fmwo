"""carter_aura.png: the ambient aura drawn UNDER him on its own node (CarterArtLayout.FINAL_AURA:
6 frames of 96x96, 0.11 s each, looping, at alpha 0.75). It is one field for every pose, so it frames
the standing figure loosely rather than hugging any one silhouette.

    frame(i)  -> {(x, y): key} for frame i of 6

Same idea as the approved overlay - big wisps curling off his shoulders, arms, head and legs - drawn
the way his own flames now are: separate tongues edged in the dark violet, red-hot where they leave
him, violet at the tips, instead of 1px arcs and scattered dots. The tips lick on a sine so frame 5
runs back into frame 0 with no seam.
"""
import math
from lib import erode, grow
import aura as AU
import stand as ST

N = 6

# (root, bend, curl, tip), root width, phase. Left side; the right side mirrors them.
WISPS_L = [
    ([(25.0, 52.0), (14.0, 44.0), (13.0, 30.0), (5.0, 21.0)], 5.2, 0.0),     # shoulder, the big one
    ([(21.0, 64.0), (10.0, 60.0), (6.0, 50.0), (1.0, 45.0)], 4.2, 2.1),      # upper arm
    ([(30.0, 83.0), (19.0, 82.0), (13.0, 74.0), (6.0, 70.0)], 3.8, 4.2),     # thigh
    ([(37.0, 31.0), (28.0, 22.0), (29.0, 12.0), (21.0, 4.0)], 4.2, 1.0),     # temple, over the flames
]


def _specs(i):
    specs = []
    t = 2.0 * math.pi * i / N
    for side in (0, 1):
        for n, (ctrl, w0, ph) in enumerate(WISPS_L):
            c = list(ctrl)
            amp = (2.2, 3.0)
            c[2] = (c[2][0] + math.sin(t + ph) * amp[0] * 0.6, c[2][1] + math.cos(t + ph) * 1.0)
            c[3] = (c[3][0] + math.sin(t + ph + 0.8) * amp[1], c[3][1] + math.cos(t + ph + 0.8) * 1.6)
            if side:
                c = [(95.0 - x, y) for x, y in c]
            w = w0 * (1.0 + 0.10 * math.sin(t + ph + 1.7))
            specs.append((c, w, 1.0))
    return specs


def frame(i, body=None):
    """body: the pixels his standing frame covers (for where the wisps run hot); defaults to frame 0's
    body without its own aura."""
    if body is None:
        body = set(ST.body().px)
    near = grow(body, 10)
    part = {}
    for ctrl, w0, w1 in _specs(i):
        whole = AU.tendril(ctrl, w0, w1)
        rings = [whole] + [erode(whole, d) for d in range(1, 3)]
        for q in whole:
            depth = 0 if q not in rings[1] else (1 if q not in rings[2] else 2)
            hot = q in near
            part[q] = (('U', 'z', 'Y') if hot else ('U', 'S', 'R'))[depth]
    return part
