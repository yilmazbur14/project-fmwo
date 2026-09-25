"""His aura on these sheets: the polish flames (aura.py - separate tongues, red at the root, violet at
the tip, dark-violet edged, a pixel of air off his keyline, no haze), animated.

The approved sheet has two still sets, IDLE (seven tongues: skull, temples, shoulders) and FLARE (the
same seven bigger, plus pairs off the elbows and the legs). Every frame here is built from those:

    idle(k) / flare(k)        the approved set, licking: roots fixed, bends and tips wandering on a
                              phase, so consecutive k make a flicker (k over n frames loops cleanly
                              when loop=n is given)
    between(t, k)             IDLE growing into FLARE (the flare frames scale with the mark's level)
    sweep(specs, lean, droop) dragged sideways by a turn, tips most (the turn's motion)
    squeeze(specs, s)         narrowed with the body when he is edge-on
    gather(t, k)              the entrance's gathering, redrawn as tongues: licks converging on the
                              mark and flames rising off the floor (intro_frames.gather_specs' own
                              paths, so the timing of the gather is the approved one)
    grow_in(specs, f)         a set shrunk toward its roots (the crown arriving in the materialise)

    stamp(px, specs, order=None, heat=0.0, embers=())  -> px with the flames behind the figure

Heat (0..1) is aura.flames' own: the hot zone reaches further out of him and the cores go orange-
white. The flare and burn frames drive it from the mark's level, which is what intro_lib.aura_heat
did for the approved sheet's wisps.
"""
import math
from lib import grow
import aura as AU
import rig


def _lick(specs, k, amp, loop=None):
    out = []
    for j, (ctrl, w0, w1) in enumerate(specs):
        c = list(ctrl)
        ph = (2.0 * math.pi * k / loop) if loop else k * 1.9
        a = ph + j * 2.39
        if len(c) >= 4:
            x2, y2 = c[2]
            x3, y3 = c[3]
            c[2] = (x2 + math.sin(a) * amp * 0.55, y2 + math.cos(a * 1.0 + 0.6) * amp * 0.45)
            c[3] = (x3 + math.sin(a + 0.9) * amp, y3 - (0.5 + 0.5 * math.cos(a + 0.3)) * amp)
        out.append((c, w0 * (1.0 + 0.07 * math.sin(a + 1.3)), w1))
    return out


def idle(k=0, amp=1.3, loop=None):
    return _lick(AU.IDLE, k, amp, loop), list(AU.IDLE_ORDER)


def flare(k=0, amp=1.5, loop=None):
    return _lick(AU.FLARE, k, amp, loop), list(AU.FLARE_ORDER)


def between(t, k=0, amp=1.4, loop=None):
    """IDLE (t=0) into FLARE (t=1); the flare's extra pairs grow in from their roots past t=0.25."""
    t = max(0.0, min(1.0, t))
    specs = []
    for j, (ctrl, w0, w1) in enumerate(AU.FLARE):
        if j < len(AU.IDLE):
            ci, wi, _ = AU.IDLE[j]
            c = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(ci, ctrl)]
            specs.append((c, wi + (w0 - wi) * t, w1))
        else:
            f = max(0.0, (t - 0.25) / 0.75)
            specs.append(grow_in([(ctrl, w0, w1)], f)[0])
    order = [j for j in AU.FLARE_ORDER if j < len(AU.IDLE) or t > 0.3]
    return _lick(specs, k, amp, loop), order


def grow_in(specs, f):
    """Shrink each tongue toward its root: f=1 is the tongue, f=0 nothing."""
    out = []
    for ctrl, w0, w1 in specs:
        bx, by = ctrl[0]
        c = [(bx + (x - bx) * f, by + (y - by) * f) for x, y in ctrl]
        out.append((c, max(0.0, w0 * (0.35 + 0.65 * f)) if f > 0 else 0.0, w1))
    return out


def sweep(specs, lean, droop=0.0):
    out = []
    for ctrl, w0, w1 in specs:
        n = len(ctrl) - 1
        c = [(x + lean * (i / n) ** 2, y + droop * (i / n) ** 2) for i, (x, y) in enumerate(ctrl)]
        out.append((c, w0, w1))
    return out


def squeeze(specs, s, cx=47.5):
    return [([(cx + (x - cx) * s, y) for x, y in ctrl], w0 * (0.55 + 0.45 * s), w1)
            for ctrl, w0, w1 in specs]


def shift(specs, dx):
    return [([(x + dx, y) for x, y in ctrl], w0, w1) for ctrl, w0, w1 in specs]


def gather(t, k):
    """The approved gather paths (intro_frames.gather_specs) in pixel space: six licks converging on
    the mark from above and the sides, five rising off the floor; t 0 far and thin, 1 pulled in.
    Returns (specs, sparks)."""
    return rig.fx.gather(t, k)


def stamp(px, specs, order=None, heat=0.0, embers=(), gap=1):
    """Flames behind the figure, a pixel of air off it; embers where the canvas is still empty."""
    body = set(px)
    live = [i for i in (order if order is not None else range(len(specs))) if specs[i][1] > 0.6]
    part = AU.flames(specs, grow(body, gap) if gap else body, live, heat=heat) if live else {}
    out = dict(px)
    for q, key in part.items():
        if q not in out and 0 <= q[0] < 96 and 0 <= q[1] < 96:
            out[q] = key
    if embers:
        for q, key in AU.embers(embers).items():
            if q not in out and 0 <= q[0] < 96 and 0 <= q[1] < 96:
                out[q] = key
    return out


def drift(embers, k, rise=2):
    """embers climbing a little each frame"""
    out = []
    for x, y, hot in embers:
        yy = y - k * rise
        if yy > 1:
            out.append((x + (1 if (k + x) % 3 == 0 else 0), yy, hot))
    return out
