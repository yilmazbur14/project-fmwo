"""Jordan v2's juggle parts, in the rig's BUILD coordinates, every one lit for the turn it will get.

v2 (art_source/jordan_v2) is thin and frail, SKINNY since 2026-09-28 (art_source/jordan_fit/skinny):
stick arms about 2 texels wide with bony elbows, stick legs with bony knees, the tee tight on him (the
fitted tee made tighter the same day; until then it hung off him in drooping sleeves). So an arm here is jv2_body.limb (a capsule chain with bony knobs) and its sleeve v2's fitted
short sleeve on that arm (jj_light.fitted_sleeve), both through jj_light so their lit
edges face the key light; the legs are jv2_body.legs' jeans rules on thin leg polygons (standing,
leaning, dangling) or, drawn up level in the tuck, thin capsule legs with bony knee knobs and the
denim bunched at the ankles. The hands, the sneakers and the box are the approved maps (the
sneakers with v2's one added keyline at the near toe).

Each helper returns [(part, outline, owner)] in stamp order.
"""
import jj_base as J
import jj_light as L
from jj_base import S, jordan

V2 = J.V2


def shoes(dx_near=0, dy_near=0, dx_far=0, dy_far=0):
    far, near = V2.shoes()
    return [(J.moved(far, dx_far, dy_far), False, 'shoe_far'),
            (J.moved(near, dx_near, dy_near), False, 'shoe_near')]


# ------------------------------------------------------------------------------ legs
def standing(light):
    """v2's standing jeans and sneakers."""
    return [(L.legs(light), True, 'legs')] + shoes()


def leaning(back):
    """v2's standing jeans rocked back on his heels (janim_defeat.lean_jeans's shear): rows slide
    left more the higher they are, the ankles fixed."""
    def f(light):
        part = L.legs(light)
        part = {(x - int(round(back * max(0, 88 - y) / 24.0)), y): k for (x, y), k in part.items()}
        return [(part, True, 'legs')] + shoes()
    return f


def _bend_dx(y, knee_y=77.0, knee_dx=0.0, foot_dx=0.0, top=71.0, foot_y=84.0):
    """How far a leg row is pushed sideways when the leg bends at the knee: a bump that peaks at the
    knee, the ankle and the hem below it shifted by foot_dx."""
    if y >= foot_y:
        return foot_dx
    if y > top:
        t = (y - top) / (foot_y - top)
        bump = 1.0 - abs(y - knee_y) / max(1.0, (foot_y - top) / 2.0)
        return knee_dx * max(0.0, bump) + foot_dx * t
    return 0.0


def _bend(px, **kw):
    """A leg (pixel set, the rig's row spans) bent at the knee: each row moved by _bend_dx."""
    return {(x + int(round(_bend_dx(y, **kw))), y) for (x, y) in px}


def dangling(knee_dx=2.5, foot_dx=-1.0):
    """Legs let go at the top of the arc: the thin legs bent a little at their bony knees, the feet
    trailing back, the denim still bunched at the ankles. v2's own jeans rules and drawing (the skinny
    jeans' row spans since 2026-09-28; the fitted jeans' polygons were bent the same way)."""
    near_px, far_px, hips_px = V2.leg_pixels()
    near = _bend(near_px, knee_dx=knee_dx, foot_dx=foot_dx)
    far = _bend(far_px, knee_dx=knee_dx, foot_dx=foot_dx)
    kx = int(round(knee_dx))
    fx = int(round(foot_dx))
    fly, cap_n, cap_f, fold_n, fold_f, _drag_n, _drag_f, st1, st2, st3, st4 = V2.LEG_DETAILS
    details = (fly,) + tuple((kind, [(x + kx, y) for (x, y) in pts], key, only)
                             for kind, pts, key, only in (cap_n, cap_f, fold_n, fold_f))         + tuple((kind, [(x + fx, y) for (x, y) in pts], key, only) for kind, pts, key, only in (st1, st2, st3, st4))

    def f(light):
        part = L.jeans(near, far, hips_px, None, None, details, light, split_y=V2.LEG_SPLIT_Y)
        return [(part, True, 'legs')] + shoes(fx, 0, fx, 0)
    return f


def tucked(near=((44, 68), (63, 70), (54, 82)), far=((54, 67), (66, 65.5), (59, 79)),
           shoe_near=(14, -7), shoe_far=(6, -10)):
    """The backflip's tuck on stick legs: each a thin thigh drawn up level to a bony knee and a thin
    shin folded back under the seat, the loose denim bunched at the ankle, lit round its own bend
    (jj_light.denim_limb). The far leg goes down first; the seat and the near leg are one keylined part
    over it, so its outline is the split."""
    def ankle_stack(knee, ankle):
        # the denim bunched above the ankle: a short fat band across the shin
        kx, ky = knee
        ax, ay = ankle
        mx, my = ax + (kx - ax) * 0.18, ay + (ky - ay) * 0.18
        return [((mx, my), (ax, ay), 2.4, 2.2)]

    def crease(knee, ankle):
        kx, ky = knee
        ax, ay = ankle
        sx, sy = ax + (kx - ax) * 0.3, ay + (ky - ay) * 0.3
        return [([(int(round(kx - 2)), int(round(ky + 2))), (int(round(kx - 4)), int(round(ky + 3)))], 'n', 'Ns'),
                ([(int(round(sx - 2)), int(round(sy))), (int(round(sx + 2)), int(round(sy - 1)))], 'n', 'NsS'),
                ([(int(round(sx - 2)), int(round(sy + 1))), (int(round(sx + 1)), int(round(sy + 1)))], 's', 'N')]

    def f(light):
        (h0, k0, a0), (h1, k1, a1) = near, far
        # skinny (2026-09-28): every leg radius 0.5 thinner (a pixel off the width, as the standing jeans
        # lost), the seat the skinny waist's width (x 43-55, its fly on column 49)
        far_leg = L.denim_limb([(h1, k1, 1.9, 1.6), (k1, a1, 1.4, 1.3)] + ankle_stack(k1, a1), light,
                               near=False, knobs=((k1[0], k1[1], 2.0),))
        L.denim_details(far_leg, crease(k1, a1))
        near_leg = L.denim_limb([(h0, k0, 2.1, 1.8), (k0, a0, 1.5, 1.4)] + ankle_stack(k0, a0), light,
                                near=True, knobs=((k0[0], k0[1], 2.2),))
        L.denim_details(near_leg, crease(k0, a0))
        hips = L.denim_limb([((46.0, 67), (52.0, 67), 3.4, 3.4)], light, near=True)
        L.denim_details(hips, [([(49, 64), (49, 70)], 'n', None)])
        front = dict(hips)
        front.update(near_leg)
        far_s, near_s = V2.shoes()
        return [(J.moved(far_s, *shoe_far), False, 'shoe_far'), (far_leg, True, 'legs'),
                (front, True, 'legs'), (J.moved(near_s, *shoe_near), False, 'shoe_near')]
    return f


# ------------------------------------------------------------------------------ arms
FAR_SHOULDER = (57.8, 48.5)        # jv2_body's far arm root, inside the fitted sleeve
NEAR_SHOULDER = (40.6, 49.2)       # jv2_body's near arm root
# (until 2026-09-28 the arms here wore v2's drooping sleeves, NEAR_SLEEVE / FAR_SLEEVE; each arm now
# wears v2's fitted short sleeve on its own upper arm, jj_light.fitted_sleeve)
# v2's thin wrist under the far hand: jv2_body.far_arm_box ends its forearm at (64.4, 49.8) under
# FAR_HAND_BOX placed at (61, 44), so the stick runs into the hand's wrist texel. The shipped taunt
# puts its wrist in the same place (BOX_TOP_LEFT + (1.4, 22.8), the hand at BOX_TOP_LEFT + (-2, 17)).
FAR_WRIST = (64.4 - 61, 49.8 - 44)
assert abs(-2 + FAR_WRIST[0] - S.TAUNT_WRIST[0]) < 1e-9 and abs(17 + FAR_WRIST[1] - S.TAUNT_WRIST[1]) < 1e-9


def _moved_pts(pts, dx, dy=0):
    return [(x + dx, y + dy) for (x, y) in pts]


def far_arm_up(box_dy=0, light=L.RIG):
    """The far arm raised under the box as the shipped v2 taunt raises it (janim_taunt.far_arm_up), so
    the punish window runs straight into the hit: a stick arm out of the sleeve fallen back and bunched
    at his shoulder, a bony elbow, the wrist under the hand (box_high's). The arm's inner side catches
    the light while the light is the rig's own (the only frames that raise it: the hit and the lift)."""
    bx0, by0 = S.BOX_TOP_LEFT
    wx, wy = bx0 - 2 + FAR_WRIST[0], by0 + 17 + box_dy + FAR_WRIST[1]     # box_high's hand
    (r0, r1), (r2, r3) = S.TAUNT_RADII
    arm = L.limb([(S.TAUNT_SHOULDER, S.TAUNT_ELBOW, r0, r1), (S.TAUNT_ELBOW, (wx, wy), r2, r3)],
                 knobs=(S.TAUNT_KNOB,), base='c', lit='d', shade='b', light=light)
    if light.default:
        ix, iy = S.TAUNT_INNER_LIT
        for (x, y) in list(arm):
            if arm[(x, y)] == 'c' and x <= ix and y <= iy:
                arm[(x, y)] = 'd'
    sl = L.raised_sleeve_far(arm, light)
    through = {q: k for q, k in arm.items() if q[1] in S.TAUNT_THROUGH_ROWS}
    return [(arm, True, 'arm_far'), (sl, True, 'sleeve_far'), (through, False, 'arm_far')]


def box_high(box_dy=0, light=L.RIG, theta=0.0):
    """The box held up high in the far hand, where the shipped v2 taunt holds it; v2's hand, its thin
    wrist."""
    bx0, by0 = S.BOX_TOP_LEFT
    box = L.box_part((bx0, by0 + box_dy), theta)
    hand = S.amap(V2.FAR_HAND_BOX, bx0 - 2, by0 + 17 + box_dy)
    return [(box, False, 'box'), (hand, False, 'hand_far')]


def near_arm_flung(dx=0, light=L.RIG):
    """The fight rig's flung arm on v2's stick arm: knocked off his hip and out behind him, a bony
    elbow, the fitted sleeve, the fingers splayed."""
    arm = L.limb([((NEAR_SHOULDER[0] + dx, NEAR_SHOULDER[1]), (32.4 + dx, 54), 1.55, 1.45),
                  ((32.4 + dx, 54), (26.4 + dx, 56.6), 1.45, 1.3)],
                 knobs=((32.4 + dx, 54.2, 1.9),), light=light)
    sl = L.fitted_sleeve((NEAR_SHOULDER[0] + dx, NEAR_SHOULDER[1]), (32.4 + dx, 54), near=True, light=light)
    hand = S.amap(S.HAND_OPEN, 19 + dx, 52)
    return [(arm, True, 'arm_near'), (sl, True, 'sleeve_near'), (hand, False, 'hand_near')]


# ------------------------------------------------------------------------------ the hug
# The box clutched to his chest: tucked up against the far side of his chest like a football, the
# far arm wrapped under it, the near arm reaching across his belly to hold its near edge. The print
# stays in view to the left of it.
HUG_BOX = (60, 44)            # the box's top-left, build coordinates

# His near hand gripping the box's near edge: the back of the hand to us, four fingers curled over
# onto the box's face, the thumb tucked under. Lit from the upper left, the rig's skin ramp.
HAND_GRIP = S.rows_of([
    ".kkkk.",
    "kdeedk",
    "kdddck",
    "kkdkck",
    "kcdcbk",
    "kcckbk",
    ".kbbk.",
])
# His far hand under the box's base, fingers curled round its bottom edge (the far side, in shade).
HAND_UNDER = S.rows_of([
    ".kkkkkk.",
    "kcdddcck",
    "kbckckbk",
    ".kbbbbk.",
    "..kkkk..",
])


def hug(light=L.RIG, theta=0.0, box_at=HUG_BOX):
    """(back, front) lists: the far stick arm behind the box with its fitted sleeve; then the box,
    the far hand under it, the near stick arm across his belly, its sleeve and its hand."""
    bx, by = box_at
    far_arm = L.limb([(FAR_SHOULDER, (62.6, 57), 1.5, 1.4), ((62.6, 57), (bx + 10.5, by + 21), 1.4, 1.3)],
                     knobs=((62.6, 57.2, 1.8),), base='c', lit='d', shade='b', light=light)
    far_sl = L.fitted_sleeve(FAR_SHOULDER, (62.6, 57), near=False, light=light)
    box = L.box_part((bx, by), theta)
    near_arm = L.limb([(NEAR_SHOULDER, (37.6, 57.8), 1.55, 1.45), ((37.6, 57.8), (bx - 1.5, by + 12.5), 1.45, 1.3)],
                      knobs=((37.6, 58.0, 1.9),), light=light)
    near_sl = L.fitted_sleeve(NEAR_SHOULDER, (37.6, 57.8), near=True, light=light)
    grip = S.amap(HAND_GRIP, bx - 3, by + 9)
    under = S.amap(HAND_UNDER, bx + 5, by + 19)
    back = [(far_arm, True, 'arm_far'), (far_sl, True, 'sleeve_far')]
    front = [(box, False, 'box'), (under, False, 'hand_far'), (near_arm, True, 'arm_near'),
             (near_sl, True, 'sleeve_near'), (grip, False, 'hand_near')]
    return back, front
