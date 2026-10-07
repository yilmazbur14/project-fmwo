"""Keeping Jordan lit from the upper left while he turns.

His rig does not shade from surface normals: every volume is lit by RULES laid along the build
frame's axes. A limb (jordan.arm) gets a lit rim on its left edge and its top edge and a shaded rim
on its right and bottom; a sleeve (jordan.sleeve) and the neck the same left/right pair; the jeans
(jordan.legs, janim_defeat.jeans) and the shirt (torso.shirt) are shaded across each ROW, lit at the
row's left end and darkest at its right. So the rig's light is "from the left, and from above".

Turn the body theta clockwise and those rules turn with it. The fix keeps the rig's own shapes and
its own rules and only asks which of the body's own edges face the key light now:

  Light(theta).h   'left' or 'right': the side edge whose screen bearing is nearer the upper left.
                   The rims' first pass lights it, the second shades the other one, and the row
                   spans run from it (so a mirrored span is the same cylinder lit from its other side)
  Light(theta).v   'top' or 'bottom': the same for the rims' up/down pass

For any theta from about -45 to 135 degrees that is the rig's own left and top, and nothing changes;
upside down it is the right and the bottom. Every part below is the rig's function copied line for
line with those two choices made parameters, and at the rig's own light each is the rig's part pixel
for pixel (_selftest). The shapes, the folds, the print, the seams, the stains: all untouched.

The hand-drawn maps (the head, the hands, the sneakers) carry their light baked in. They are re-lit
the way Matt's face was (art_source/matt_juggle/mj_fig.relight_keep_counts): each pixel is ranked by
its own tone shifted by how much the turned light brightens or darkens a smooth volume there, and the
map's own tones are handed back out in the numbers the drawing had. The light moves; the style (a
thin highlight, a broad shadow) stays; detail tones outside the ranked set stay exactly as drawn.

The box is lit from its left (a lit gold bar left, a dark one right, the header darkening rightward):
upside down its frame's tones are mirrored side for side while the star and the plumber stay as they
are.
"""
import math

import jj_base as J
from jj_base import S, jordan, lib
from lib import fill, poly, rim, stroke, amap

DIRS = {'left': (-1, 0), 'right': (1, 0), 'top': (0, -1), 'bottom': (0, 1)}
OPP = {'left': 'right', 'right': 'left', 'top': 'bottom', 'bottom': 'top'}


class Light:
    """Which of the body's own edges face the key light when it is turned theta clockwise."""

    def __init__(self, theta=0.0):
        self.theta = theta

        def score(name):
            sx, sy = J.rot2(DIRS[name], theta)
            return sx * J.LIGHT[0] + sy * J.LIGHT[1]
        # ties (to 1e-9) go to the rig's own choice, so theta 0 is the rig exactly
        self.h = 'left' if score('left') >= score('right') - 1e-9 else 'right'
        self.v = 'top' if score('top') >= score('bottom') - 1e-9 else 'bottom'

    @property
    def default(self):
        return self.h == 'left' and self.v == 'top'

    def rim_dirs(self):
        return DIRS[self.h], DIRS[self.v], DIRS[OPP[self.h]], DIRS[OPP[self.v]]

    def __repr__(self):
        return 'Light(%g: %s, %s)' % (self.theta, self.h, self.v)


RIG = Light(0.0)


# ------------------------------------------------------------------------------ the rule parts
# Jordan v2's rule parts (art_source/jordan_v2/jv2_body.py), each copied line for line with the
# edges it lights made to face the key light for the turn. At the rig's own light every one is the
# v2 rig's part pixel for pixel (_selftest).
V2 = J.V2
ellipse = J.lib.ellipse


def limb(segments, knobs=(), base='d', lit='e', shade='c', light=RIG):
    """jv2_body.limb: a stick arm (capsules and bony knobs) with its rims facing the light. Callers
    pass the fitted build's radii; like the rig (SKINNY, 2026-09-28) it takes ARM_THIN off every
    segment's radius and KNOB_THIN off every knob's."""
    lh, lv, sh_, sv = light.rim_dirs()
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= J.kit.capsule(p0, p1, max(V2.MIN_R, r0 - V2.ARM_THIN), max(V2.MIN_R, r1 - V2.ARM_THIN))
    for (cx, cy, r) in knobs:
        r = max(V2.MIN_KNOB, r - V2.KNOB_THIN)
        shape |= ellipse(cx, cy, r, r)
    part = fill(shape, base)
    rim(part, lit, *lh)
    rim(part, lit, *lv, only=base)
    rim(part, shade, *sh_)
    rim(part, shade, *sv, only=base)
    return part


def sleeve(pts, hem, lit=True, light=RIG):
    """jv2_body.sleeve: a sleeve on any outline, lit on the side toward the light, its underside dark."""
    lh, _, sh_, sv = light.rim_dirs()
    s = fill(poly(pts), 'R')
    rim(s, 'T' if lit else 'R', *lh)
    rim(s, 'V', *sh_)
    rim(s, 'v', *sv, only='RV')
    stroke(s, [(int(round(x)), int(round(y))) for (x, y) in hem], '1')
    return s


def raised_sleeve_far(arm, light=RIG):
    """The fitted taunt's far sleeve (jv2_body.far_raised_cuff, 2026-09-28; until then the bunched
    sleeve jj_snap.TAUNT_SLEEVE), ridden up round the top of the raised arm, on his shadow side: no lit
    rim, its shade rims on the edges away from the light. The fold and the trim across the opening are
    drawing and stay where they are."""
    _, _, sh_, sv = light.rim_dirs()
    part = fill(poly([(99.2 - x, y) for (x, y) in V2.RAISED_CUFF]), 'R')
    rim(part, 'V', *sh_)
    rim(part, 'v', *sv, only='RV')
    stroke(part, [(59, 47), (58, 49)], 'V', only='R')
    top = min(y for (x, y) in part)
    for (x, y) in list(part):
        if y == top:
            part[(x, y)] = '1'
    return part


def neck(dx, light=RIG):
    """jv2_body.neck: the thin neck craning forward, the Adam's apple, the collar skin. The jaw's
    shadow is the jaw's and stays; the neck's own shade and the shadow it throws on the chest fall
    on its side away from the light."""
    lh, _, sh_, _ = light.rim_dirs()
    o = dx - 3
    col = poly([(47.2 + o * 0.3, 46), (50.8 + o * 0.3, 46), (52.2 + o, 43), (54.2 + o, 40.5),
                (54.6 + o, 37), (50.2 + o, 37), (50.2 + o, 40.5), (48.4 + o * 0.5, 43)])
    skin = poly([(43.4, 43), (56, 43), (55, 44.8), (51.6, 46.4), (48, 46.4), (44.4, 44.8)])
    n = fill(skin, 'c')
    column = fill(col, 'c')
    rim(column, 'd', *lh)
    rim(column, 'b', *sh_)
    n.update(column)
    away = sh_[0]
    for (x, y) in list(n):
        if y <= 39:
            n[(x, y)] = 'b'
        elif y == 40 and (x + away, y) not in n:
            n[(x, y)] = 'b'
    ax = int(round(53.5 + o))
    n[(ax, 41)] = 'd'
    n[(ax, 42)] = 'b'
    for (x, y) in list(n):
        if (x, y) not in column and y >= 43 and (x - away, y) in column:
            n[(x, y)] = 'b'
    return n


def _span(pixels, y):
    xs = [x for (x, yy) in pixels if yy == y]
    return (min(xs), max(xs)) if xs else None


def _mir(x, lo, hi, flip):
    return (-x, -hi, -lo) if flip else (x, lo, hi)


def _px(shape):
    """A leg given as a pixel set (the skinny rig's row spans) or as polygon points."""
    return set(shape) if isinstance(shape, (set, frozenset)) else poly(shape)


def jeans(near, far, hips, near_hem=None, far_hem=None, details=(), light=RIG, split_y=70):
    """jv2_body.legs' jeans rules on any legs (pixel sets or polygons): the near leg lit down its edge
    toward the light ('S', then 's'), 'n' on the far edge; the far leg dark at both edges with its one
    lit line inside the lit one; the hips across the whole width. Lit from whichever side edge faces
    the key light. near_hem / far_hem: the stacks at the ankles, part of each leg."""
    near_px = _px(near) | (_px(near_hem) if near_hem else set())
    far_px = _px(far) | (_px(far_hem) if far_hem else set())
    hips_px = _px(hips)
    part = fill(near_px | far_px | hips_px, 'N')
    flip = light.h == 'right'
    for (x, y) in list(part):
        if (x, y) in near_px and y >= split_y:
            x2, lo, hi = _mir(x, *_span(near_px, y), flip)
            k = 'S' if x2 == lo else ('s' if x2 == lo + 1 else ('n' if x2 == hi else 'N'))
        elif (x, y) in far_px and y >= split_y:
            x2, lo, hi = _mir(x, *_span(far_px, y), flip)
            k = 's' if x2 == lo + 1 else ('n' if x2 in (lo, hi) else 'N')
        else:
            x2, lo, hi = _mir(x, *_span(part, y), flip)
            k = 'S' if x2 == lo else ('s' if x2 == lo + 1 else ('n' if x2 >= hi - 1 else 'N'))
        part[(x, y)] = k
    for kind, pts, key, only in details:
        if kind == 'stroke':
            stroke(part, pts, key, only=only)
        else:
            for q in pts:
                if q in part and (only is None or part[q] in only):
                    part[q] = key
    return part


# jv2_body.legs' own drawing (the skinny jeans', 2026-09-28): the fly, the bony kneecaps, the folds
# behind the knees, the drag down each thigh, the stacks at the ankles.
V2_LEG_DETAILS = V2.LEG_DETAILS


def legs(light=RIG):
    """jv2_body.legs (the skinny standing jeans, row spans), lit from the side edge facing the light."""
    near, far, hips = V2.leg_pixels()
    return jeans(near, far, hips, None, None, V2_LEG_DETAILS, light, split_y=V2.LEG_SPLIT_Y)


def denim_limb(segments, light=RIG, near=True, knobs=()):
    """A bent jeans leg as a capsule chain with bony knee knobs, shaded by the rig's rim rules (the
    row rule is right for an upright leg and flat for a thigh drawn up level): 'S' on the edge
    toward the light with 's' inside it, 'n' on the far edge, the up/down pass after, as
    jv2_body.limb does its arms. The far leg (near=False) keeps its lit edge to 's'."""
    lh, lv, sh_, sv = light.rim_dirs()
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= J.kit.capsule(p0, p1, r0, r1)
    for (cx, cy, r) in knobs:
        shape |= ellipse(cx, cy, r, r)
    part = fill(shape, 'N')
    rim(part, 'S' if near else 's', *lh)
    if near:
        rim(part, 's', *lh, depth=2, only='N')
    rim(part, 's', *lv, only='N')
    rim(part, 'n', *sh_, depth=1 if near else 2)
    rim(part, 'n', *sv, only='N')
    return part


def denim_details(part, strokes):
    """Jeans drawing laid over a leg: creases and stacked hems, each only over denim."""
    for pts, key, only in strokes:
        stroke(part, pts, key, only=only)
    return part


def shirt(frame=0, light=RIG):
    """jv2_body.shirt, the SKINNY build's tee (2026-09-28: the fitted tee made tighter the same day;
    until then a sack with long drapes), its cloth turned like a cylinder lit from the side edge that
    faces the light. The collar, the seam, the print (its side outline columns cropped, as the rig
    crops them), the folds and the scruff are the rig's, where the rig put them."""
    part = fill(poly(V2.TORSO), 'R')
    for x, yc in V2.COLLAR.items():
        for y in range(40, yc):
            part.pop((x, y), None)
    flip = light.h == 'right'
    red = {'lit': 'T', 'base': 'R', 'shade': 'V', 'deep': 'v'}
    pink = {'lit': 'Q', 'base': 'P', 'shade': 'q', 'deep': 'q'}
    for (x, y) in list(part):
        lo, hi = _span(part, y)
        t = (x - lo) / max(1, hi - lo)
        if flip:
            t = 1.0 - t
        ramp = pink if y >= V2.BAND_Y else red
        k = ramp['base']
        if t <= 0.06:
            k = ramp['lit']
        elif t >= 0.95:
            k = ramp['deep']
        elif t >= 0.76:
            k = ramp['shade']
        elif y < V2.BAND_Y and 0.1 <= t <= 0.24 and 46 <= y <= 52:
            k = ramp['lit']
        part[(x, y)] = k
    for x, yc in V2.COLLAR.items():
        if (x, yc) in part:
            part[(x, yc)] = '1'
    for (x, y) in list(part):
        if y == V2.BAND_Y and (x < V2.PRINT_X0 or x > V2.PRINT_X1):
            part[(x, y)] = 'k'
    for q, k in V2.print_part().items():
        if q in part:
            part[q] = k

    def fold(pts, key='q', only='PQ'):
        for q in pts:
            if q in part and part[q] in only:
                part[q] = key
    if frame == 0:
        fold(((42, 64), (43, 64), (44, 64), (45, 65), (46, 65)))
        fold(((42, 63), (43, 63), (45, 64)), 'Q', 'P')
        fold(((42, 66), (43, 66), (44, 67), (45, 67)))
        fold(((44, 66),), 'Q', 'P')
    else:
        fold(((43, 66), (44, 66), (45, 67), (46, 67)))
        fold(((44, 65), (45, 66)), 'Q', 'P')
    fold(((52, 68), (51, 67)))
    for q in ((55, 46), (56, 46), (56, 47)):
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'b'
    for q in ((54, 66), (55, 66), (55, 67)):
        if q in part:
            part[q] = 'c'
    return part


def fitted_sleeve(root, elbow, near=True, light=RIG, **kw):
    """jv2_body.near_sleeve / far_sleeve (the fitted short sleeve, 2026-09-28) on any arm, its lit and
    shade rims turned to the light: the outline is v2's own (jv2_body.sleeve_outline), the collar end
    and the shoulder line moved with the shoulder."""
    if near:
        mx, my = root[0] - V2.NEAR_ROOT[0], root[1] - V2.NEAR_ROOT[1]
        pts, hem = V2.sleeve_outline(root, elbow, (V2.NEAR_COLLAR[0] + mx, V2.NEAR_COLLAR[1] + my),
                                     [(x + mx, y + my) for (x, y) in V2.NEAR_SHOULDER], +1, **kw)
        return sleeve(pts, hem, True, light)
    kw.setdefault('length', 4.6)
    mx, my = root[0] - V2.FAR_ROOT[0], root[1] - V2.FAR_ROOT[1]
    pts, hem = V2.sleeve_outline(root, elbow, (V2.FAR_COLLAR[0] + mx, V2.FAR_COLLAR[1] + my),
                                 [(x + mx, y + my) for (x, y) in V2.FAR_SHOULDER], -1, **kw)
    return sleeve(pts, hem, False, light)


# ------------------------------------------------------------------------------ the box
BOX_MAP = list(S.MAP)


def box_rows(mirror):
    """The box map, its frame's tones mirrored side for side (the star and the plumber kept)."""
    if not mirror:
        return list(BOX_MAP)
    art = set(S.STAR_ART) | set(S.FIG_ART)
    out = []
    for r, row in enumerate(BOX_MAP):
        w = len(row)
        chars = []
        for c in range(w):
            if (c, r) in art:
                chars.append(row[c])
            else:
                m = row[w - 1 - c]
                # the art's own fill under a mirrored column stays the fill it sat on
                chars.append(m if (w - 1 - c, r) not in art else ('R' if 1 <= r <= 5 else 'w'))
        out.append(''.join(chars))
    return out


def box_mirror(theta, box_deg=0.0):
    """Mirror the box's tones when its own left side faces away from the light."""
    sx, sy = J.rot2((-1, 0), theta + box_deg)
    return sx * J.LIGHT[0] + sy * J.LIGHT[1] < 0


def box_part(top_left, theta=0.0):
    """The box square to his body (it turns with him) with its top-left on build point top_left,
    its frame's tones mirrored when its own left side faces away from the light."""
    return S.box_at(box_rows(box_mirror(theta)), top_left)


# ------------------------------------------------------------------------------ drawn maps
LIGHT3 = (J.LIGHT[0] * 0.8, J.LIGHT[1] * 0.8, 0.6)


def light3(theta):
    """The key light in the body's own frame for a body turned theta: R(-theta) on the screen light."""
    x, y = J.rot2(LIGHT3[:2], -theta)
    return (x, y, LIGHT3[2])


def _normal(x, y, cx, cy, rx, ry):
    nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 > 1.0:
        s = math.sqrt(d2)
        return nx / s, ny / s, 0.0
    return nx, ny, math.sqrt(1.0 - d2)


def relight_keep_counts(px, owner, owners, model, baked, target, ramp, form, step=0.85):
    """Matt's count-keeping relight (see the module note), on a key map and its owner map."""
    cx, cy, rx, ry = model
    pts = []
    for q, o in owner.items():
        if o not in owners:
            continue
        k = px.get(q)
        if k not in form:
            continue
        n = _normal(q[0], q[1], cx, cy, rx, ry)
        d = (n[0] * target[0] + n[1] * target[1] + n[2] * target[2]
             - (n[0] * baked[0] + n[1] * baked[1] + n[2] * baked[2]))
        t = ramp.index(k)
        pts.append((t - d / step, t, q))
    if not pts:
        return 0
    counts = [sum(1 for p in pts if ramp[p[1]] == k) for k in form]
    pts.sort()
    changed, i = 0, 0
    for k, n in zip(form, counts):
        for (_, t, q) in pts[i:i + n]:
            if px[q] != k:
                px[q] = k
                changed += 1
        i += n
    return changed


def part_model(owner, name, pad=1.0):
    pts = [q for q, o in owner.items() if o == name]
    if not pts:
        return None
    xs = [x for (x, y) in pts]
    ys = [y for (x, y) in pts]
    cx, cy = (min(xs) + max(xs) + 1) / 2.0, (min(ys) + max(ys) + 1) / 2.0
    return (cx, cy, (max(xs) - min(xs) + 1) / 2.0 + pad, (max(ys) - min(ys) + 1) / 2.0 + pad)


# His ramps, light to dark (kit.PAL runs its keys dark to light).
SKIN = 'edcba'
HAIR = 'mljih'
# v2's greasy hair carries its own gloss above the hair ramp: the highlight 'A' (#A27B57) round a pale
# glint 'Y' (#FFF3B0). It is light, not drawing, so it is re-lit with the hair and goes to the side
# of the skull that faces the light (upside down it would otherwise shine on his underside).
HAIR_GLOSS = 'YAmljih'
SHOE = '321'
SOLE = '09'


# ------------------------------------------------------------------------------ self-test
def _selftest():
    ok = True
    checks = [
        ('legs', legs(), V2.legs()),
        ('neck', neck(3), V2.neck(3)),
        ('neck lean', neck(2), V2.neck(2)),
        ('shirt f0', shirt(0), V2.shirt(0)),
        ('shirt f1', shirt(1), V2.shirt(1)),
    ]
    near = V2.near_arm_hip()
    mine = limb([((40.6, 49.2), (32.4, 57.2), 1.55, 1.45), ((32.4, 57.2), (38.2, 63.2), 1.45, 1.3)],
                knobs=((32.4, 57.4, 1.9),))
    checks.append(('near arm', mine, near[0][0]))
    mine_sl = fitted_sleeve(V2.NEAR_ROOT, (32.4, 57.2), near=True)
    checks.append(('near sleeve', mine_sl, near[1][0]))
    far = V2.far_arm_box_low()
    mine_far = limb([((57.8, 48.5), (62.6, 56.4), 1.5, 1.4), ((62.6, 56.4), (63.8, 63), 1.4, 1.3)],
                    knobs=((62.6, 56.6, 1.7),), base='c', lit='d', shade='b')
    checks.append(('far arm', mine_far, far[0][0]))
    mine_fsl = fitted_sleeve(V2.FAR_ROOT, (62.6, 56.4), near=False)
    checks.append(('far sleeve', mine_fsl, far[1][0]))
    checks.append(('far cuff', raised_sleeve_far({}), V2.far_raised_cuff({})))
    for name, a, b in checks:
        same = a == b
        print('%-12s at the rig light vs the v2 rig: %s' % (name, 'identical' if same else 'DIFFERENT'))
        ok &= same
    same = box_part((61, 25), 0) == jordan.box_part(0, 0)
    print('%-12s unmirrored vs the rig box: %s' % ('box', 'identical' if same else 'DIFFERENT'))
    ok &= same
    for th in (0, -15, -40, -90, -180, -270, -340):
        print('  theta %5d -> %s' % (th, Light(th)))
    return ok


if __name__ == '__main__':
    _selftest()
