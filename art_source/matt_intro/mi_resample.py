"""Pixel-art upscaling that never invents a colour: the method of the cast's derived portraits
(art_source/jordan_derived/dkit.resample, itself Josh's), generalised from 3:2 to any block ratio.

Every source pixel lands on exactly one output pixel; each block of q source pixels becomes p output
pixels, the extra ones being 'between' pixels that copy one of their two neighbours (never a blend),
chosen so a keyline stays one pixel wide, a one-pixel feature stays one pixel, and a diagonal keyline
stays joined. 3:2 is the cast's 1.5x (and reproduces dkit's axis layout); 5:4 is 1.25x.
"""

# per ratio: for each output position in a block, the source offsets it reads (two = a between pixel)
LAYOUTS = {
    (3, 2): [(0,), (0, 1), (1,)],
    (5, 4): [(0,), (1,), (1, 2), (2,), (3,)],
}


def omap(u, p, q):
    """Source offset -> output offset."""
    lay = LAYOUTS[(p, q)]
    b, r = divmod(u, q)
    for o, srcs in enumerate(lay):
        if srcs == (r,):
            return p * b + o
    raise ValueError(u)


def _axis(o, p, q):
    b, r = divmod(o, p)
    return [q * b + s for s in LAYOUTS[(p, q)][r]]


def _pick(a, b, aa, bb):
    """The between pixel of a and b (aa, bb: the pixels beyond each). Never a blend."""
    if a == b:
        return a
    if a is None or b is None:
        o = b if a is None else a
        return None if o == 'k' else o          # a silhouette keyline stays one pixel wide
    if a == 'k':
        return b                                 # so does an interior one
    if b == 'k':
        return a
    a_thin, b_thin = aa != a, bb != b
    if a_thin and not b_thin:
        return b                                 # a one-pixel feature stays one pixel
    if b_thin and not a_thin:
        return a
    return a


def resample(px, sx0, sy0, n, p, q):
    """The n x n source window at (sx0, sy0) of key map px, scaled p/q."""
    def g(x, y):
        return px.get((sx0 + x, sy0 + y))

    out = {}
    size = omap(n - 1, p, q) + 1
    for oy in range(size):
        ys = _axis(oy, p, q)
        for ox in range(size):
            xs = _axis(ox, p, q)
            if len(xs) == 1 and len(ys) == 1:
                v = g(xs[0], ys[0])
            elif len(ys) == 1:
                y = ys[0]
                v = _pick(g(xs[0], y), g(xs[1], y), g(xs[0] - 1, y), g(xs[1] + 1, y))
            elif len(xs) == 1:
                x = xs[0]
                v = _pick(g(x, ys[0]), g(x, ys[1]), g(x, ys[0] - 1), g(x, ys[1] + 1))
            else:
                tl, tr, bl, br = g(xs[0], ys[0]), g(xs[1], ys[0]), g(xs[0], ys[1]), g(xs[1], ys[1])
                if (tl == br == 'k' and 'k' not in (tr, bl)) or (tr == bl == 'k' and 'k' not in (tl, br)):
                    v = 'k'                      # a diagonal keyline stays joined
                else:
                    top = _pick(tl, tr, g(xs[0] - 1, ys[0]), g(xs[1] + 1, ys[0]))
                    bot = _pick(bl, br, g(xs[0] - 1, ys[1]), g(xs[1] + 1, ys[1]))
                    v = _pick(top, bot, top, bot)
            if v is not None:
                out[(ox, oy)] = v
    # two diagonal source keyline pixels whose images land two apart get the one bridge pixel
    for y in range(n):
        for x in range(n):
            if g(x, y) != 'k':
                continue
            for dx in (1, -1):
                qx, qy = x + dx, y + 1
                if not (0 <= qx < n and qy < n) or g(qx, qy) != 'k' or 'k' in (g(qx, y), g(x, qy)):
                    continue
                P, Q = (omap(x, p, q), omap(y, p, q)), (omap(qx, p, q), omap(qy, p, q))
                if abs(P[0] - Q[0]) <= 1 and abs(P[1] - Q[1]) <= 1:
                    continue
                cands = [(bx, by) for bx in range(min(P[0], Q[0]), max(P[0], Q[0]) + 1)
                         for by in range(min(P[1], Q[1]), max(P[1], Q[1]) + 1)
                         if (bx, by) not in (P, Q) and max(abs(bx - P[0]), abs(by - P[1])) <= 1
                         and max(abs(bx - Q[0]), abs(by - Q[1])) <= 1]
                if cands and not any(out.get(c) == 'k' for c in cands):
                    out[cands[0]] = 'k'
    return out


def _selftest():
    """3:2 must match the cast's own resampler (jordan_derived/dkit.resample) on a real sprite."""
    import os
    import sys
    import mi_base as B
    sys.path.insert(0, os.path.join(B.ART, 'jordan_derived'))
    # dkit imports Jordan's rig as 'kit'; load it in isolation and only use its resample
    import importlib.util
    spec = importlib.util.spec_from_file_location('dkit_for_test', os.path.join(B.ART, 'jordan_derived', 'dkit.py'))
    try:
        dk = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dk)
    except Exception as e:                                  # Jordan's rig not importable here
        print('dkit not importable (%s); skipped' % e)
        return
    px = B.approved_frame_px(0)
    a = dk.resample(px, 27, 10, 43)
    b = resample(px, 27, 10, 43, 3, 2)
    print('3:2 vs dkit.resample on Matt f0:', 'identical' if a == b else 'DIFFERENT')


if __name__ == '__main__':
    _selftest()
