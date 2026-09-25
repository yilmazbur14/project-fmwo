"""Greyson's arms, traced as polygons per muscle (gr_muscle.Region): the delt cap, the biceps,
the triceps ('upper'), the forearm and its brachioradialis bulge ('brach'). Coordinates are for
the LEFT arm (screen left); the right arm is built from the mirrored points and re-lit by the same
upper-left light, never mirrored as a picture.

idle: the ready stance. The lats push the upper arm out and down to a bent elbow, the forearm
      hangs to the fist beside the thigh; the biceps faces in toward the body, the triceps is
      the outer strip. Negative space between arm and lat keeps the V-taper readable.
flex: the front double biceps. The upper arm runs out level with the triceps hanging under it,
      the biceps peaks high above it as its own ball, and the forearm stands up to the fist at
      the temple. The forearm tapers to the wrist so a notch opens between it and the peak at
      the elbow crease: that notch is what makes the silhouette read as a double biceps.

Lines inside an arm are dark skin tones (LINE, or 2 steps darker); only the arm's own keyline,
where it crosses the body, is black.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gr_kit as K  # noqa: E402
from gr_kit import poly, mpts  # noqa: E402
from gr_muscle import Form, Region, RegionLayer  # noqa: E402

CUTS = (0.78, 0.48, 0.21, -0.06)

IDLE = {
    'delt': [(34.6, 50.6), (31.5, 48.9), (27.5, 48.9), (24.0, 50.6), (21.6, 53.4), (20.2, 57.0),
             (20.0, 60.6), (21.2, 63.8), (23.4, 65.4), (25.6, 62.8), (28.4, 60.6), (31.6, 58.6),
             (34.4, 56.6), (36.0, 54.4), (35.8, 52.2)],
    'upper': [(21.0, 59.0), (18.8, 62.6), (17.4, 66.2), (17.0, 69.6), (18.0, 72.6), (20.6, 74.4),
              (24.2, 74.2), (27.4, 72.0), (30.2, 68.6), (32.6, 64.8), (34.6, 61.2), (35.6, 58.2),
              (32.6, 58.0), (28.0, 59.6), (24.0, 60.4)],
    'biceps': [(25.6, 62.2), (23.8, 65.0), (23.0, 68.2), (23.6, 71.4), (25.8, 72.6), (28.6, 70.4),
               (31.0, 67.0), (33.0, 63.6), (33.6, 60.8), (29.6, 60.4)],
    'forearm': [(18.2, 71.0), (21.2, 70.2), (24.8, 71.0), (27.4, 73.4), (29.4, 76.6), (30.4, 80.0),
                (30.4, 83.0), (28.2, 84.0), (24.0, 84.0), (21.4, 82.2), (19.4, 79.0), (17.8, 75.8),
                (17.2, 73.2)],
    'brach': [(17.6, 72.4), (18.8, 70.6), (21.4, 70.2), (22.6, 72.8), (22.2, 76.4), (21.2, 79.4),
              (19.8, 79.0), (18.2, 76.0)],
}
IDLE_FORMS = {
    'delt': Form(ellipsoid=(28.0, 55.0, 9.0, 8.5)),
    'upper': Form(axis=[(30.0, 57.0), (22.0, 72.0)], r=7.5),
    'biceps': Form(axis=[(30.0, 57.0), (22.0, 72.0)], r=7.5),
    'forearm': Form(axis=[(22.0, 71.0), (26.0, 84.0)], r=6.0),
    'brach': Form(axis=[(22.0, 71.0), (26.0, 84.0)], r=6.0),
}

FLEX = {
    'delt': [(35.0, 50.0), (31.0, 47.6), (27.0, 48.2), (24.2, 50.6), (23.2, 54.0), (24.4, 57.8),
             (27.4, 60.2), (31.6, 60.2), (34.8, 58.4), (36.4, 55.4), (36.2, 52.4)],
    'biceps': [(29.4, 49.4), (28.2, 46.4), (26.4, 44.4), (24.0, 43.8), (22.0, 44.8), (20.6, 47.2),
               (20.0, 50.4), (20.6, 53.4), (22.8, 55.4), (26.0, 55.8), (28.8, 54.6), (30.2, 52.0)],
    'upper': [(33.6, 57.0), (29.0, 55.6), (24.0, 54.6), (19.0, 54.0), (14.4, 53.8), (11.6, 55.0),
              (10.8, 57.6), (12.4, 60.2), (16.0, 61.8), (21.0, 62.6), (26.0, 62.2), (30.4, 60.8),
              (33.8, 59.6)],
    'forearm': [(10.6, 56.0), (9.0, 52.4), (9.0, 48.0), (10.2, 44.2), (11.8, 41.4), (13.6, 39.8),
                (17.2, 39.6), (19.0, 41.2), (19.6, 44.2), (20.2, 47.6), (20.8, 50.8), (20.4, 54.2),
                (17.4, 56.8), (13.6, 57.4)],
    'brach': [(9.6, 53.0), (9.4, 49.4), (10.4, 45.6), (12.6, 43.0), (15.0, 44.6), (15.2, 48.4),
              (14.0, 52.0), (12.2, 54.8)],
}
FLEX_FORMS = {
    'delt': Form(ellipsoid=(29.5, 54.0, 8.5, 8.0)),
    'biceps': Form(ellipsoid=(25.0, 50.0, 7.0, 6.5)),
    'upper': Form(axis=[(33.0, 58.0), (11.0, 58.0)], r=5.5),
    'forearm': Form(axis=[(14.6, 56.0), (15.2, 40.0)], r=6.0),
    'brach': Form(axis=[(14.6, 56.0), (15.2, 40.0)], r=6.0),
}

# Muscle-on-muscle lines are a dark tone of the skin, never black (the house rule in
# art_source/vs_card_v2/STYLE.md): LINE is the deepest working skin tone. Black is only where
# the arm crosses the body, which the arm layer's own keyline draws.
LINE = '6'
SPEC = {
    # name: (amp, round_px, cast, depth)
    'upper': (1.4, 2.6, 2, 1),
    'biceps': (1.8, 3.0, 2, 2),
    'delt': (2.0, 3.2, LINE, 4),
    'forearm': (1.5, 2.6, 2, 3),       # the elbow crease: a soft shadow, not a cut across the arm
    'brach': (1.6, 2.4, 0, 3),         # the forearm's bulge is shading only (a line doubled the keyline)
}
FLEX_SPEC = dict(SPEC, biceps=(2.0, 3.4, LINE, 5), forearm=(1.5, 2.6, LINE, 3))


def _mirror_form(f):
    if f.axis is not None:
        (x0, y0), (x1, y1) = f.axis
        return Form(axis=[(K.AX - x0, y0), (K.AX - x1, y1)], r=f.r, flat=f.flat)
    cx, cy, rx, ry = f.ell
    return Form(ellipsoid=(K.AX - cx, cy, rx, ry), flat=f.flat)


def arm(pose, side):
    polys = {'idle': IDLE, 'flex': FLEX}[pose]
    forms = {'idle': IDLE_FORMS, 'flex': FLEX_FORMS}[pose]
    spec = FLEX_SPEC if pose == 'flex' else SPEC
    regions = []
    for name, pts in polys.items():
        amp, rnd, cast, depth = spec[name]
        pts = mpts(pts) if side else pts
        form = _mirror_form(forms[name]) if side else forms[name]
        regions.append(Region(name, poly(pts), amp=amp, round_px=rnd, cast=cast, depth=depth,
                              form=form))
    base = forms['upper'] if not side else _mirror_form(forms['upper'])
    lay = RegionLayer(base, regions)
    return lay.shade(cuts=CUTS)[0]
