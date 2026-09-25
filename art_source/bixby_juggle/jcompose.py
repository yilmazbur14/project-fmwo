"""Compose a juggle frame from the rig's layers.

A frame is the body layer plus the three head layers, each built in the rig's own upright frame (lit for
its own turn, relight.py) and then placed into the 256x256 juggle frame by jrot.turn: exact for multiples
of 90 degrees, RotSprite otherwise. By default the heads turn with the body; a head can instead loll on
its own, turning about the point where it joins its neck, which stays where the body's turn puts it.

Everything is built on an unclipped canvas, so a head thrown up past the rig frame's top edge (the rig's
own canvas clips at 0..192 x 0..160) keeps its crest.
"""
import contextlib
import math

import numpy as np

import jcommon as C
import jfaces  # noqa: F401  (registers the juggle's expressions)
import jrig
import jrot
import heads
import frame as FR
import rig_heads
from pal import BCanvas

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Free(BCanvas):
    """A BCanvas that never clips: parts may sit at negative coordinates or past 192x160."""

    def stamp(self, part, outline=True, keep_line=False):
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in N4:
                    q = (x + dx, y + dy)
                    if q not in body:
                        self.px[q] = 'k'
        for q, k in part.items():
            self.px[q] = k


@contextlib.contextmanager
def unclipped():
    """jrig's and rig_heads' canvases, unclipped, for the length of a build."""
    saved = (jrig.BCanvas, rig_heads.BCanvas)
    jrig.BCanvas = Free
    rig_heads.BCanvas = Free
    try:
        yield
    finally:
        jrig.BCanvas, rig_heads.BCanvas = saved


def arr_of(px, pad=2):
    """A key array holding a canvas's pixels, and the local coordinate of its [0, 0]."""
    xs = [p[0] for p in px]
    ys = [p[1] for p in px]
    x0, y0 = min(xs) - pad, min(ys) - pad
    w, h = max(xs) - x0 + 1 + pad, max(ys) - y0 + 1 + pad
    return jrot.to_arr(px, w, h, -x0, -y0), (x0, y0)


class Layer:
    def __init__(self, px, pivot, dest, theta=0.0, scale=(1.0, 1.0), post=(1.0, 1.0), name=''):
        self.px, self.pivot, self.dest, self.theta = px, pivot, dest, theta
        self.scale, self.post, self.name = scale, post, name

    def render(self, W=C.W, H=C.H):
        if not self.px:
            return np.zeros((H, W), np.uint8)
        a, (x0, y0) = arr_of(self.px)
        piv = (self.pivot[0] - x0, self.pivot[1] - y0)
        return jrot.turn(a, self.theta, piv, W, H, self.dest, self.scale[0], self.scale[1],
                         post=self.post)


def compose(layers, W=C.W, H=C.H):
    out = np.zeros((H, W), np.uint8)
    for L in layers:
        out = jrot.over(out, L.render(W, H))
    return out


def rot(theta, v):
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])


def place(theta, pivot, dest, p, post=(1.0, 1.0)):
    """Where local point p lands under a layer's turn."""
    r = rot(theta, (p[0] - pivot[0], p[1] - pivot[1]))
    return (dest[0] + r[0] * post[0], dest[1] + r[1] * post[1])


def mid_join(P):
    """The middle head's neck join: its throat, above the collar, in the rig's frame."""
    xf = rig_heads.mid_xf(P.get('mid', {}), P.get('bob', 0))
    x, y = xf.p(heads.HX, 78)
    return (int(round(x)), int(round(y)))


def side_join(P, left=False):
    """A side head's neck join: the top of its neck, in the rig's frame."""
    nb, nt = P.get('neck', ((118, 98), (142, 82)))
    if left:
        nl = P.get('neck_left') or (nb, nt)
        return (191 - int(round(nl[1][0])), int(round(nl[1][1] + P.get('bob', 0))))
    return (int(round(nt[0])), int(round(nt[1] + P.get('bob', 0))))


# Note on the heads: their edge recipes are relit like everything else, but a face's muzzle, blaze, lips
# and teeth are hand-painted maps and head-space regions that carry their own light. Swapping their
# highlight and shade on an upside-down head fixes the light metric but turns the white blaze beige, and
# the blaze is Bixby; so a turned head keeps its painted face exactly (jlint measures the body alone for
# the relight, and the whole frame for not reading lit from below).


def figure(P, theta, pivot=C.LOCAL_PIVOT, dest=C.TUMBLE_CENTRE, loll=None, post=(1.0, 1.0),
           order=('wings', 'tails', 'body', 'left', 'right', 'mid')):
    """The layers of one posed beast turned by theta about local `pivot`, landing on frame `dest`, in
    the rig's stamp order.

    loll: {'mid'|'left'|'right': head_theta} turns that head to its own angle about its neck join (the
    middle head takes Liam's headband tails with it).
    post: a squash in screen space (the crash flattening against the mat)."""
    loll = dict(loll or {})
    hide = set(P.get('hide', ()))
    th_m = loll.get('mid', theta)
    with unclipped():
        wings = jrig.wings_canvas(P, theta)
        tails = jrig.tails_canvas(P, th_m)
        body = jrig.body_canvas(P, theta)
        th_l = loll.get('left', theta)
        th_r = loll.get('right', theta)
        left, right = jrig.side_canvases(P, th_l, th_r)
        mid = jrig.mid_canvas(P, th_m)
    out = {}
    out['wings'] = Layer(wings.px, pivot, dest, theta, post=post, name='wings')
    out['body'] = Layer(body.px, pivot, dest, theta, post=post, name='body')

    def head(name, cv, th, join):
        px = cv.px
        if th == theta:
            return Layer(px, pivot, dest, theta, post=post, name=name)
        d = place(theta, pivot, dest, join, post)
        d = (int(round(d[0])), int(round(d[1])))
        return Layer(px, join, d, th, post=post, name=name)
    if 'side' not in hide:
        out['left'] = head('left', left, th_l, side_join(P, left=True))
        out['right'] = head('right', right, th_r, side_join(P))
    if 'mid' not in hide:
        out['mid'] = head('mid', mid, th_m, mid_join(P))
    if 'tails' not in hide:
        out['tails'] = head('tails', tails, th_m, mid_join(P))
    global LAST
    LAST = (P, [out[k] for k in order if k in out and out[k].px])
    return LAST[1]


LAST = None         # (pose, layers) of the last figure built: the exporter reads its anchors off it


def plate_texel(P, layers, head_y=13):
    """Where the middle of Liam's headband plate lands in the juggle frame (head-space row 13 is the
    plate's middle, row 9 its top edge), through the middle head's own layer and turn."""
    mid = next(L for L in layers if L.name == 'mid')
    xf = rig_heads.mid_xf(P.get('mid', {}), P.get('bob', 0))
    lx, ly = xf.p(heads.HX, head_y)
    # the rig puts a pixel's centre on whole numbers, jrot.turn on +0.5
    x, y = place(mid.theta, mid.pivot, mid.dest, (lx + 0.5, ly + 0.5), mid.post)
    return (int(math.floor(x)), int(math.floor(y)))


def ground_dest(dx=0, dy=0):
    """dest for LOCAL_PIVOT when the rig's feet (96, 151) stand on the juggle frame's FEET."""
    return (C.FEET[0] + (C.LOCAL_PIVOT[0] - C.LOCAL_FEET[0]) + dx,
            C.FEET[1] + (C.LOCAL_PIVOT[1] - C.LOCAL_FEET[1]) + dy)


def np_top(a):
    """The highest drawn row of a frame array."""
    import numpy as _np
    ys = _np.nonzero(a.any(axis=1))[0]
    return int(ys.min()) if len(ys) else 0
