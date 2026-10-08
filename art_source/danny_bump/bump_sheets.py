"""Danny's new body sheets for the approval pass: every frame as a spec, its timing, and the frame it is placed in.

Frame lists follow the architect's addendum (scratchpad/danny_addendum1.md, D.1); sizes, anchors and timings are
this rig's (the addendum adopts them). Horizontal strips, frame 0 leftmost, every grounded frame with its lowest
texel on the bottom row, his mass on the frame's middle column.

  danny_sumo_bump   SIDE VIEW facing right (the approved headbutt's view; the code flips it to charge left):
                    0 stomp, 1 belly slap, 2 crouch (held: the tell), 3-6 run loop (belly first), 7 contact (belly
                    flattened), 8 rebound (knocked back off a parry), 9 skid (heels dug in), 10 slip (feet out
                    from under him on his own worm puddle)
  danny_sumo_back   0 knocked off the fists (front view: the slam's own tuck, so the cut from the slam is seamless),
                    1 flipped over backward (side view), 2 crashes onto his back, 3-6 dazed loop (legs kicking,
                    stars), 7 flinch (punched), 8-9 rocks back and up onto his feet (side view), 10 up, facing the
                    camera (front view: hands over to danny_sumo_idle f0)

A spec is {'side': bump_rig.build_side spec}, {'tuck': fight_tuck spec} or {'front': fight.build spec}, plus:
  ground   True: the lowest texel sits on the frame's floor row (default); False: `lift` texels above it
  lift     how far an airborne frame's lowest texel is above the floor row
  dx       a sideways nudge inside the frame (texels, + right)
  stars    the daze ring's phase (degrees), baked over his face
"""
import bump_rig as R

FS, TK, FT = R.FS, R.TK, R.FT


def W(**kw):
    """A side pose in world angles, with the collar seated low enough to show under his jowl in profile."""
    kw.setdefault('collar_low', True)
    return R.world(**kw)


# ------------------------------------------------------------------ THE BELLY BUMP
HIP = (110.0, 100.0)
STAND = 50.0          # the hip joint's height over the soles in a standing crouch (both feet planted)
RUN = dict(hip=HIP, lean=-16.0, head=22.0, belly=-0.45, eyes='glare', mouth='grit', flutter=30.0)


def run(**kw):
    return W(**dict(RUN, **{k: v for k, v in kw.items() if k in RUN}),
             **{k: v for k, v in kw.items() if k not in RUN})


BUMP_FRAMES = [
    # STOMP (shiko): the near foot just driven into the mat out in front, down in a deep crouch, hands on his knees,
    # a kiai (the code shakes 3 and puffs sumo dust at the foot)
    ('stomp', dict(side=W(hip=HIP, lean=6.0, head=-4.0, eyes='squeeze', mouth='shout', flutter=-14.0, wobble=1,
                          wobble_span=(-40.0, 0.0), stomp=True,
                          arm=-38, fore=-12, thigh=-78, calf=-4, foot=0, far_leg=(-66, 30, 0), far_arm=(-14, 26))),
     250),
    # BELLY SLAP: up out of the crouch, the palm smacked on his belly, the wobble running over it
    ('slap', dict(side=W(hip=HIP, lean=-4.0, head=4.0, eyes='squeeze', mouth='shout', flutter=-10.0, wobble=2,
                         wobble_span=(-40.0, 0.0), hand='open', smack=(3, 9, -60, 60), belly=-0.2,
                         arm=-14, fore=-88, thigh=-70, calf=R.calf_for(STAND, -70), foot=0,
                         far_leg=(-52, R.calf_for(STAND, -52), 0), far_arm=(20, 50))),
     200),
    # CROUCH (held, the red read): low, leaning back, the belly thrust out and still wobbling, the arms swept back;
    # the sleepy lid and a smug little smirk (his block's sleepy-smug, in profile)
    ('crouch', dict(side=W(hip=HIP, lean=-20.0, head=20.0, eyes='lid', mouth='smug', flutter=14.0, belly=-0.55,
                           wobble=1, arm=45, fore=70, thigh=-74, calf=R.calf_for(46.0, -74), foot=0,
                           far_leg=(-56, R.calf_for(46.0, -56), 0), far_arm=(62, 92))),
     350),
    # THE CHARGE: a low, heavy shuffle, belly first, arms swept back (loop 3-6)
    ('run_a', dict(side=run(arm=30, fore=45, thigh=-72, calf=-22, foot=8, far_leg=(55, 58, -35), far_arm=(58, 80))), 60),
    ('run_b', dict(side=run(arm=36, fore=52, thigh=-55, calf=22, foot=0, far_leg=(-78, 20, -10), far_arm=(52, 76),
                            belly=-0.5)), 60),
    ('run_c', dict(side=run(arm=42, fore=58, thigh=55, calf=58, foot=-35, far_leg=(-72, -22, 8), far_arm=(48, 70))), 60),
    ('run_d', dict(side=run(arm=36, fore=52, thigh=-78, calf=20, foot=-10, far_leg=(-55, 22, 0), far_arm=(52, 76),
                            belly=-0.5)), 60),
    # CONTACT: the belly slammed flat against them and rippling, the arms whipped back, the lead foot braking
    ('contact', dict(side=W(hip=HIP, lean=-24.0, head=26.0, eyes='squeeze', mouth='shout', flutter=40.0, belly=0.6,
                            wobble=2, wobble_span=(-48.0, 6.0),
                            arm=60, fore=88, thigh=-66, calf=-28, foot=12, far_leg=(40, 62, -30), far_arm=(76, 110))),
     120),
    # REBOUND (parried): stopped dead, the fists sunk in his belly; the jolt throws his arms forward, his eyes pop
    ('rebound', dict(side=W(hip=HIP, lean=-30.0, head=14.0, eyes='wide', mouth='ow', flutter=-20.0, belly=0.8,
                            wobble=1, wobble_span=(-44.0, 4.0), hand='open', far_hand='open',
                            sweat=[(31.0, -24.0)],
                            arm=-48, fore=-82, thigh=-64, calf=-26, foot=18, far_leg=(-18, 36, 0),
                            far_arm=(-30, -64))),
     350),
    # SKID: heels dug in, leaning back, arms thrown forward to stop himself
    ('skid', dict(side=W(hip=HIP, lean=-26.0, head=20.0, eyes='wide', mouth='grit', flutter=-30.0, belly=-0.2,
                         hand='open', far_hand='open', sweat=[(31.0, -24.0)],
                         arm=-70, fore=-100, thigh=-60, calf=-44, foot=32, far_leg=(-4, 66, 0), far_arm=(-52, -84))),
     350),
    # SLIP: his feet shoot out from under him on his own worms; falling back, arms flung up, eyes popping
    ('slip', dict(side=W(hip=HIP, lean=-58.0, head=-10.0, eyes='wide', mouth='ow', flutter=-60.0, belly=-0.2,
                         hand='open', far_hand='open', shock=True, sweat=[(31.0, -24.0)],
                         arm=150, fore=120, thigh=-120, calf=-100, foot=10, far_leg=(-100, -70, 20),
                         far_arm=(-150, -120)), dx=-24),
     300),
]

# ------------------------------------------------------------------ ON HIS BACK
LHIP = (140.0, 110.0)
LIE = dict(hip=LHIP, lean=-90.0, head=0.0, eyes='x', mouth='tongue', flutter=-60.0)


def lie(**kw):
    base = dict(LIE)
    for k in list(kw):
        if k in base:
            base[k] = kw.pop(k)
    return W(**base, **kw)


def tuck(sx=1.0, sy=1.0, deg=0.0, **kw):
    return dict(tuck=dict(kw, xf=TK.Xf(sx=sx, sy=sy, base=(87.5, 143.0), deg=deg, pivot=(87.5, 138.0))))


BACK_FRAMES = [
    # BOUNCE: knocked off the fists: the slam's own tuck (front view) smacked from below, eyes screwed shut...
    ('bounce_a', tuck(sx=1.04, sy=0.9, deg=-6.0, eyes='squeeze', mouth='shout', head=(0, 14)), 150),
    # ...then flung over backward, the tuck bursting open, arms thrown up (the code carries him on the arc)
    ('bounce_b', dict(side=W(hip=LHIP, lean=-50.0, head=-14.0, eyes='wide', mouth='ow', flutter=-70.0, hand='open',
                             far_hand='open', arm=-200.0, fore=-235.0, thigh=-160.0, calf=-40.0, foot=-30.0,
                             far_leg=(-150.0, -35.0, -30.0), far_arm=(140.0, 110.0))), 300),
    # LAND: crashes onto his back, squashed flat, legs flung up
    ('land', dict(side=lie(eyes='squeeze', mouth='ow', squash=(1.06, 0.88, (140.0, 150.0)), hand='open', far_hand='open',
                           arm=100, fore=130, thigh=205, calf=235, foot=-20, far_leg=(222, 262, -10), far_arm=(118, 150))),
     150),
    # DAZED: on his back like a flipped beetle, legs kicking, stars going round (loop 3-6)
    ('daze_a', dict(side=lie(arm=55, fore=95, hand='open', thigh=205, calf=175, foot=-20, far_leg=(225, 260, -20),
                             far_arm=(75, 100)), stars=0), 140),
    ('daze_b', dict(side=lie(arm=62, fore=108, hand='open', thigh=214, calf=240, foot=-10, far_leg=(210, 190, -25),
                             far_arm=(80, 110), belly=0.08), stars=30), 140),
    ('daze_c', dict(side=lie(arm=55, fore=95, hand='open', thigh=222, calf=258, foot=-10, far_leg=(200, 168, -20),
                             far_arm=(75, 100)), stars=60), 140),
    ('daze_d', dict(side=lie(arm=52, fore=94, hand='open', thigh=212, calf=208, foot=-20, far_leg=(215, 235, -20),
                             far_arm=(70, 95), belly=-0.08), stars=90), 140),
    # FLINCH: punched: the whole mass jolts, legs jerk up stiff, eyes screwed shut, the stars knocked loose
    ('flinch', dict(side=lie(eyes='squeeze', mouth='ow', squash=(1.03, 0.94, (140.0, 150.0)), belly=0.3, wobble=1,
                             wobble_span=(-48.0, 4.0), hand='open', far_hand='open',
                             arm=96, fore=76, thigh=196, calf=196, foot=-30, far_leg=(206, 214, -30),
                             far_arm=(112, 88)), stars=15), 120),
    # ROLL UP: knees hauled to his chest, he rocks back onto his shoulders...
    ('roll_a', dict(side=W(hip=LHIP, lean=-112.0, head=10.0, eyes='squeeze', mouth='grit', flutter=-80.0,
                           arm=175, fore=235, thigh=165, calf=250, foot=-60, far_leg=(160, 245, -60),
                           far_arm=(185, 240))), 150),
    # ...rocks forward up onto his feet in a squat, hands on his knees...
    ('roll_b', dict(side=W(hip=LHIP, lean=24.0, head=-14.0, eyes='glare', mouth='grit', flutter=-10.0,
                           arm=-30, fore=-8, thigh=-84, calf=4, foot=0, far_leg=(-80, 8, 0), far_arm=(-24, -4))), 150),
    # ...and up, turned back to the camera, shaking it off (hands over to danny_sumo_idle f0)
    ('roll_c', dict(front=dict(eyes='half', mouth='frown', bubble=0, body=(0, 2), head_dy=1, belly=1)), 150),
]

SHEETS = {
    'danny_sumo_bump': dict(size=(224, 168), frames=BUMP_FRAMES,
                            note='0 stomp, 1 belly slap, 2 crouch (held: the red read), loop 3-6 while he charges, '
                                 '7 contact, 8 rebound (parried), 9 skid, 10 slip; faces right, the code flips it'),
    'danny_sumo_back': dict(size=(256, 160), frames=BACK_FRAMES,
                            note='0-1 bounce (0 front view, 1 side view; the code carries him on the arc), 2 land, '
                                 'loop 3-6 dazed, 7 flinch (then back to the loop), 8-10 roll up (10 front view, '
                                 'hands over to danny_sumo_idle f0); side frames face right, his head to the LEFT'),
}


# ------------------------------------------------------------------ BUILDING A FRAME
def _stars_for(spec, phase):
    """Place the daze ring over his face: the pose is built once without stars to find the head, then the
    ring's back half goes under the body and its front half over it."""
    pz = R.SD.Pose({k: v for k, v in dict(R.DEFAULT, **spec).items() if k in R.SD.DEFAULT})
    neck = pz.neck((0.0, 0.0))
    hx = R.J(pz.neck.angle(), neck)
    face = hx((4.0, -14.0))                      # the middle of the face, head-local
    return R.daze_ring(face[0] - 2.0, face[1] - 36.0, 25.0, 7.0, phase)


def frame_px(spec):
    """The frame's key map in the rig's own coordinates (not yet placed in the sheet frame)."""
    if 'tuck' in spec:
        return FS.close_pinholes(FT.floor_clip(TK.build(spec['tuck']).px))
    if 'front' in spec:
        return FS.close_pinholes(FT.floor_clip(FT.build(spec['front'], free=True).px))
    side = dict(spec['side'])
    if spec.get('stars') is not None:
        back, front = _stars_for(side, spec['stars'])
        side['stars_back'], side['stars_front'] = back, front
    px = R.build_side(side)[0].px
    return FS.close_pinholes(px)


MASS = (5.0, -35.0)      # torso-local: the middle of his mass (the belly's centre), the frame's middle column


def mass_x(spec):
    """Where his mass sits in the rig's coordinates: the torso point MASS through the pose (side view), or the
    front view's centre line."""
    if 'tuck' in spec or 'front' in spec:
        return 87.5
    sp = dict(R.DEFAULT, **spec['side'])
    pz = R.SD.Pose({k: v for k, v in sp.items() if k in R.SD.DEFAULT})
    return pz.torso(MASS)[0]


def place(sheet, spec, px):
    """Put a frame's key map into its sheet frame: his mass on the frame's middle column (so the body holds still
    and the limbs move round it, frame to frame), the lowest texel on the floor row (or `lift` above it)."""
    w, h = SHEETS[sheet]['size']
    low = max(y for (x, y) in px)
    ox = int(round(w / 2.0 - mass_x(spec))) + spec.get('dx', 0)
    oy = (h - 1) - low - (0 if spec.get('ground', True) else spec.get('lift', 0))
    return {(x + ox, y + oy): k for (x, y), k in px.items()}, (ox, oy)


def frame_map(sheet, spec):
    px, off = place(sheet, spec, frame_px(spec))
    w, h = SHEETS[sheet]['size']
    return {q: k for q, k in px.items() if 0 <= q[0] < w and 0 <= q[1] < h}, off, px
