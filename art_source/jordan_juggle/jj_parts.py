"""Jordan v2's juggle parts, in the rig's BUILD coordinates, every one lit for the turn it will get.

v2 (art_source/jordan_v2) is thin and frail: stick arms about 3 texels wide with bony elbows, stick
legs with bony knees, the tee hanging off him in drooping sleeves. So an arm here is jv2_body.limb (a
capsule chain with bony knobs) and its sleeve jv2_body.sleeve, both through jj_light so their lit
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


def _bend(pts, knee_y=77.0, knee_dx=0.0, foot_dx=0.0, top=71.0, foot_y=84.0):
    """A leg outline bent at the knee: points between the hip and the ankle pushed sideways by a bump
    that peaks at the knee, the ankle and the hem below it shifted by foot_dx."""
    out = []
    for (x, y) in pts:
        if y >= foot_y:
            dx = foot_dx
        elif y > top:
            t = (y - top) / (foot_y - top)
            bump = 1.0 - abs(y - knee_y) / max(1.0, (foot_y - top) / 2.0)
            dx = knee_dx * max(0.0, bump) + foot_dx * t
        else:
            dx = 0.0
        out.append((x + dx, y))
    return out


def dangling(knee_dx=2.5, foot_dx=-1.0):
    """Legs let go at the top of the arc: the thin legs bent a little at their bony knees, the feet
    trailing back, the denim still bunched at the ankles. v2's own jeans rules and drawing."""
    near = _bend(V2.NEAR_LEG, knee_dx=knee_dx, foot_dx=foot_dx)
    far = _bend(V2.FAR_LEG, knee_dx=knee_dx, foot_dx=foot_dx)
    near_hem = [(x + foot_dx, y) for (x, y) in V2.NEAR_HEM]
    far_hem = [(x + foot_dx, y) for (x, y) in V2.FAR_HEM]
    kx = int(round(knee_dx))
    fx = int(round(foot_dx))
    details = (
        ('stroke', [(50, 66), (50, 71)], 'n', None),
        ('pix', [(46 + kx, 76), (47 + kx, 77), (46 + kx, 77), (47 + kx, 78)], 's', None),
        ('pix', [(51 + kx, 76), (50 + kx, 77), (51 + kx, 77), (51 + kx, 78)], 's', None),
        ('stroke', [(44 + kx, 80), (46 + kx, 81)], 'n', 'N'),
        ('stroke', [(53 + kx, 80), (55 + kx, 81)], 'n', 'N'),
        ('stroke', [(40 + fx, 85), (42 + fx, 86), (45 + fx, 85)], 'n', 'NsS'),
        ('stroke', [(40 + fx, 87), (43 + fx, 87), (45 + fx, 86)], 's', 'N'),
        ('stroke', [(53 + fx, 85), (55 + fx, 86), (58 + fx, 85)], 'n', 'Ns'),
        ('stroke', [(54 + fx, 87), (57 + fx, 87)], 's', 'N'),
    )

    def f(light):
        part = L.jeans(near, far, V2.HIPS, near_hem, far_hem, details, light)
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
        return [((mx, my), (ax, ay), 2.9, 2.7)]

    def crease(knee, ankle):
        kx, ky = knee
        ax, ay = ankle
        sx, sy = ax + (kx - ax) * 0.3, ay + (ky - ay) * 0.3
        return [([(int(round(kx - 2)), int(round(ky + 2))), (int(round(kx - 4)), int(round(ky + 3)))], 'n', 'Ns'),
                ([(int(round(sx - 2)), int(round(sy))), (int(round(sx + 2)), int(round(sy - 1)))], 'n', 'NsS'),
                ([(int(round(sx - 2)), int(round(sy + 1))), (int(round(sx + 1)), int(round(sy + 1)))], 's', 'N')]

    def f(light):
        (h0, k0, a0), (h1, k1, a1) = near, far
        far_leg = L.denim_limb([(h1, k1, 2.4, 2.1), (k1, a1, 1.9, 1.8)] + ankle_stack(k1, a1), light,
                               near=False, knobs=((k1[0], k1[1], 2.5),))
        L.denim_details(far_leg, crease(k1, a1))
        near_leg = L.denim_limb([(h0, k0, 2.6, 2.3), (k0, a0, 2.0, 1.9)] + ankle_stack(k0, a0), light,
                                near=True, knobs=((k0[0], k0[1], 2.7),))
        L.denim_details(near_leg, crease(k0, a0))
        hips = L.denim_limb([((42.5, 67), (55.5, 67), 3.4, 3.4)], light, near=True)
        L.denim_details(hips, [([(50, 64), (50, 70)], 'n', None)])
        front = dict(hips)
        front.update(near_leg)
        far_s, near_s = V2.shoes()
        return [(J.moved(far_s, *shoe_far), False, 'shoe_far'), (far_leg, True, 'legs'),
                (front, True, 'legs'), (J.moved(near_s, *shoe_near), False, 'shoe_near')]
    return f


# ------------------------------------------------------------------------------ arms
FAR_SHOULDER = (57.8, 48.5)        # jv2_body's far arm root, inside the drooping sleeve
NEAR_SHOULDER = (40.6, 49.2)       # jv2_body's near arm root
# jv2_body's drooping sleeves: the near one reaching almost to the elbow, the far one in shade
NEAR_SLEEVE = ([(44.2, 43.4), (41.4, 44.6), (38.6, 47.2), (35.4, 51.6), (33.6, 54.0), (37.6, 57.8),
                (41.2, 55.2), (42.6, 51.6), (43.4, 47.6)], [(34, 54), (37, 57)])
FAR_SLEEVE = ([(55.6, 43.4), (58.4, 44.8), (60.8, 47.6), (62.4, 51.2), (63, 53.8), (58.8, 55.4),
               (57.4, 51), (57, 47)], [(59, 55), (62, 54)])
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
    elbow, the drooping sleeve, the fingers splayed."""
    arm = L.limb([((NEAR_SHOULDER[0] + dx, NEAR_SHOULDER[1]), (32.4 + dx, 54), 1.55, 1.45),
                  ((32.4 + dx, 54), (26.4 + dx, 56.6), 1.45, 1.3)],
                 knobs=((32.4 + dx, 54.2, 1.9),), light=light)
    sl = L.sleeve(_moved_pts(NEAR_SLEEVE[0], dx), _moved_pts(NEAR_SLEEVE[1], dx), light=light)
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
    """(back, front) lists: the far stick arm behind the box with its drooping sleeve; then the box,
    the far hand under it, the near stick arm across his belly, its sleeve and its hand."""
    bx, by = box_at
    far_arm = L.limb([(FAR_SHOULDER, (62.6, 57), 1.5, 1.4), ((62.6, 57), (bx + 10.5, by + 21), 1.4, 1.3)],
                     knobs=((62.6, 57.2, 1.8),), base='c', lit='d', shade='b', light=light)
    far_sl = L.sleeve(FAR_SLEEVE[0], FAR_SLEEVE[1], lit=False, light=light)
    box = L.box_part((bx, by), theta)
    near_arm = L.limb([(NEAR_SHOULDER, (37.6, 57.8), 1.55, 1.45), ((37.6, 57.8), (bx - 1.5, by + 12.5), 1.45, 1.3)],
                      knobs=((37.6, 58.0, 1.9),), light=light)
    near_sl = L.sleeve(NEAR_SLEEVE[0], NEAR_SLEEVE[1], light=light)
    grip = S.amap(HAND_GRIP, bx - 3, by + 9)
    under = S.amap(HAND_UNDER, bx + 5, by + 19)
    back = [(far_arm, True, 'arm_far'), (far_sl, True, 'sleeve_far')]
    front = [(box, False, 'box'), (under, False, 'hand_far'), (near_arm, True, 'arm_near'),
             (near_sl, True, 'sleeve_near'), (grip, False, 'hand_near')]
    return back, front
