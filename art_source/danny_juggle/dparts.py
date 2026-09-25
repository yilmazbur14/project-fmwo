"""Danny's juggle parts, on top of his approved evolved-form rig (art_source/danny_sumo_v2, imported
read-only; art_source/danny_sumo/evolved.py points there too).

His rig SHADES by itself: every sculpted form is lit by sumo_lib.intensity from the key light, on its
own inflated volume. So a turned frame is relit the most faithful way there is -- the rig renders him
in his own frame with the light (and the cast-shadow offset) turned the OTHER way, and the frame is
then turned. The volume is his rig's own; only the normal has turned relative to the light. Two
things in his rig are painted rather than shaded, and they get jkit's rank-preserving relight on top:
the face's cel bands (face.face_base: a lit left cheek, a shaded right side) and the tones inside
the feature maps. The snot bubble is a sphere, so it is drawn upright after the turn, its highlight
at the upper left like everything else.

New drawing, all of it expression, in his rig's own map format:
  EYE_SQUEEZE   eyes screwed shut (> <), for the uppercut and the crash;
  EYE_X         knocked out;
  MOUTH_TONGUE  the approved slack mouth with the tongue lolling out over the lower lip.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AS = os.path.dirname(HERE)
V2 = os.path.join(AS, 'danny_sumo_v2')
# His rig's folder goes on the path AFTER this one, so his rig's modules (anim, face, sumo_lib ...)
# are found without any of them shadowing this folder's. The shared juggle kit is loaded by its file
# path and never put on the path: josh_juggle, danny_sumo_v2 and josh_redesign all have modules with
# common names (export, measure, zoom, lint, poses), and one folder's must never answer for another's.
for p in (V2, AS):
    if p not in sys.path:
        sys.path.append(p)


def load(name, path):
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


K = load('jkit', os.path.join(AS, 'josh_juggle', 'jkit.py'))
import anim                     # noqa: E402
import sumo_lib as L            # noqa: E402
import face as F                # noqa: E402

PAL = L.PAL
FW, FH = anim.FW, anim.FH       # his own frame, 176 x 144, soles on row 143

# His ramps, dark -> light, by key (sumo_lib.PAL). The two knits share one colour (5B6EE1) under
# different keys, so they stay apart here.
FAMILIES = {
    'skin': '1234567', 'lknit': 'uvwx', 'dknit': 'UVBX', 'red': 'mMRr', 'gold': 'gOoYy', 'white': 'hHW',
}
BODY_KEYS = set('1234567uvwxUVBXmMRrgOoYyhHWs')


# ------------------------------------------------------------------ NEW FACE MAPS
EYE_SQUEEZE_L = [
    # x: 0-4   5-9   10-13      screwed shut: the lids clamped into a chevron pointing at the nose,
    # centred where his open eye is. Drawn from row 28, so the beanie's cuff (stamped after the
    # features, its keyline on row 27) never eats the top of it.
    "..33. ..... ....",    # 0  the crease the squeeze pushes up
    "..kkk k.... ....",    # 1
    "....k kkk.. ....",    # 2
    "..... .kkkk k...",    # 3  the point, pressed toward the nose
    "....k kkk.. ....",    # 4
    "..kkk k.... ....",    # 5
    "..33. ..... ....",    # 6
]
EYE_X_L = [
    # knocked out: a bold X on his eye, from row 29, clear of the cuff
    "...kk ....k k...",    # 0
    "....k k..kk ....",    # 1
    ".... .kkkk. ....",    # 2
    ".... .kkkk. ....",    # 3
    "....k k..kk ....",    # 4
    "...kk ....k k...",    # 5
    "..33. ...33 ....",    # 6  the slack lids
]
MOUTH_TONGUE = [
    # x: 78-82 83-87 88-92 93-97   the approved slack mouth, the tongue hanging out over the lip
    "..... 33333 333.. .....",    # 0 under the nose
    "..... .kkkk kkkk. .....",    # 1 upper lip
    "..... k1111 1111k .....",    # 2 hanging open
    "..... k11rr rr11k .....",    # 3 the tongue
    "..... .k1rr rrr1k .....",    # 4
    "..... .4krr rrk4. .....",    # 5 lower lip, the tongue over it
    "..... ..4kr Rrk.. .....",    # 6 hanging
    "..... ...kk kk... .....",    # 7
]


def _pad(rows, w):
    out = []
    for r in rows:
        r = r.replace(' ', '')
        out.append(r + '.' * (w - len(r)))
    return out


def _mirror_eye(rows):
    return [''.join(F.DOWN.get(c, c) for c in r[::-1]) for r in rows]


for _n, _rows, _top in (('squeeze', EYE_SQUEEZE_L, 28), ('x', EYE_X_L, 29)):
    _l = _pad(_rows, 14)
    anim.EYES[_n] = (_l, _mirror_eye(_l), _top)
anim.MOUTHS.setdefault('tongue', _pad(MOUTH_TONGUE, 20))


# ------------------------------------------------------------------ RENDERING, RELIT
LIGHT0 = tuple(float(v) for v in L.LIGHT)
_DEFAULTS = L.intensity.__defaults__
_SHADOW = anim.SHADOW
_STAMP = L.Canvas.stamp
_FACE_BASE = F.face_base


def _turn(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


_HEAD = anim.head


class Render:
    """One frame of his rig, drawn for a turn of `deg`: `px` the key map in his own frame,
    `owner` the stamp that last wrote each pixel (its index into `parts`, the silhouettes; -1 for
    pixels written straight onto the canvas, the features), `face` the face mask, `spec` the pose.

    part='body' draws everything but his head (the rig's own anim.head is skipped); part='head' draws
    only the head, on its own, exactly as anim.head draws it. A body flattened on the mat is squashed;
    his head is not (a head is round from every side, and his face must stay readable), so the two
    are drawn apart and the head laid back on."""

    def __init__(self, spec, deg, part='all'):
        self.spec = dict(anim.DEFAULT, **spec)
        self.deg = deg
        self.part = part
        self.parts, self.owner, self.face = [], {}, set()
        lx, ly = _turn(LIGHT0, -deg)
        sx, sy = _turn(_SHADOW, -deg)
        rec = self

        def stamp(cv, part, outline=True, shadow=None, shadow_steps=1, line_key='k', under=0):
            before = dict(cv.px)
            _STAMP(cv, part, outline, shadow, shadow_steps, line_key, under)
            idx = len(rec.parts)
            rec.parts.append(set(part))
            for q, k in cv.px.items():
                if before.get(q) != k or q in part:
                    rec.owner[q] = idx

        def face_base(mask, dx=0, dy=0):
            rec.face = set(mask)
            return _FACE_BASE(mask, dx, dy)

        L.intensity.__defaults__ = (_DEFAULTS[0], _DEFAULTS[1], _DEFAULTS[2], (lx, ly, LIGHT0[2]), _DEFAULTS[4])
        anim.SHADOW = (int(round(sx)), int(round(sy)))
        L.Canvas.stamp = stamp
        F.face_base = face_base
        if part == 'body':
            anim.head = lambda cv, s: None
        try:
            if part == 'head':
                cv = L.Canvas()
                _HEAD(cv, self.spec)
                L.clean_lone(cv.px)
            else:
                cv = anim.build_frame(self.spec)
        finally:
            L.intensity.__defaults__ = _DEFAULTS
            anim.SHADOW = _SHADOW
            L.Canvas.stamp = _STAMP
            F.face_base = _FACE_BASE
            anim.head = _HEAD
        self.px = cv.px
        for q in self.px:
            self.owner.setdefault(q, -1)

    # where the face's features sit (for a crisp RotSprite turn), in his own frame
    def features(self):
        s = self.spec
        dx, dy = s['body'][0], s['body'][1] + s['head_dy']
        el, er, ey = anim.EYES[s['eyes']]
        boxes = [(66 + dx, ey + dy, 14, 7), (96 + dx, ey + dy, 14, 7), (81 + dx, 31 + dy, 15, 11),
                 (78 + dx, 43 + dy, 20, 8)]
        out = []
        for (x0, y0, w, h) in boxes:
            f = {}
            for x in range(x0, x0 + w):
                for y in range(y0, y0 + h):
                    k = self.px.get((x, y))
                    if k is not None and k in 'kWU1r' and (x, y) in self.face:
                        f[(x, y)] = k
            out.append((f, '5'))
        return out

    def head_centre(self):
        """The middle of his head (face and beanie), his own frame: what the head turns about."""
        s = self.spec
        return (87.5 + s['body'][0], 27.0 + s['body'][1] + s['head_dy'])

    def nostril(self):
        """The point his snot bubble grows from (anim.head's), in his own frame."""
        s = self.spec
        return (92.6 + s['body'][0], 41.5 + s['body'][1] + s['head_dy'])


# The face's painted tones: the rank-preserving relight (jkit), on the face mask's own dome.
def _face_slope():
    r = Render({}, 0)
    face = {q: k for q, k in r.px.items() if q in r.face and k in FAMILIES['skin']}
    nrm = K.normals(r.face)
    return K.fit_slopes(face, nrm, {'skin': FAMILIES['skin']})['skin']


FACE_SLOPE = None


def relight_face(r, gain=1.0):
    """Turn the light on the painted face for a frame turned by r.deg."""
    global FACE_SLOPE
    if not r.deg or not r.face:
        return dict(r.px)
    if FACE_SLOPE is None:
        FACE_SLOPE = _face_slope()
    f = K.Fig(FW, FH)
    f.px = {q: k for q, k in r.px.items() if q in r.face and k in FAMILIES['skin']}
    f.lab = {q: 'face' for q in f.px}
    f.masks = {'face': set(r.face)}
    nrm = K.normals(r.face)
    lit = K.relight(f, r.deg, {'skin': FAMILIES['skin']}, {'skin': FACE_SLOPE}, gain=gain,
                    nrm={q: nrm[q] for q in f.px if q in nrm})
    out = dict(r.px)
    out.update(lit)
    return out


def bubble(cx, cy, r):
    """His snot bubble, upright: face.bubble, lit at its upper left whatever he is doing."""
    return F.bubble(cx, cy, r=r)


POP = anim.POP
