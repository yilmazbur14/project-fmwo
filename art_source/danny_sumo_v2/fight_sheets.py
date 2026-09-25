"""Danny's fight sheets (the user's brief of 2026-09-24): every frame as a spec for fight.build, with
its timing and the frame it is drawn in. The side-view headbutt is fight_side.py's.

A sheet is a horizontal strip, frame 0 leftmost. `size` is one frame; `oy` is how far the rig's own
176x144 coordinates are moved down inside it (a taller frame keeps the feet on its bottom row).
"""
import fight as FT
import fight_tuck as TK
import fight_side as SD

AWAKE = dict(eyes='awake', bubble=0)
SMUG = dict(eyes='lazy', mouth='smirk')
SEAT = dict(legs='sit', arms=('rest', 'rest'))
AIR = dict(legs='airv', arms=('cock', 'cock'), bubble=0)
PUSH = dict(arms=('push', 'push'), bubble=0)
STRAIN = dict(PUSH, eyes='squeeze', mouth='grit')


def tuck(sx=1.0, sy=1.0, deg=0.0, move=(0.0, 0.0), **kw):
    """A frame of the Sumo Smash tuck (fight_tuck): squash / stretch about the rear, a rock about
    a pivot just above it (so the rear stays put), and the tuck's own options."""
    return dict(tuck=dict(kw, xf=TK.Xf(sx=sx, sy=sy, base=(87.5, 143.0), deg=deg, pivot=(87.5, 138.0), move=move)))


def side(ground=False, **kw):
    """A side-view frame (fight_side), drawn facing right; ground=True sets its lowest point on the
    floor row (the frames whose feet are on the mat)."""
    return dict(side=kw, ground=ground)


# the head turned 50 degrees in the frame, crown first, the face looking down the line of flight
TORPEDO = dict(hip=(104.0, 92.0), lean=90.0, head=-40.0, arm=0.0, elbow=12.0, foot=72.0, flutter=40.0,
               far=((0.0, 0.0, 72.0), (6.0, 0.0)))


def cock(sh, el=0.0):
    return {1: (sh, el), -1: (sh, el)}


def palms(x, y, s):
    return {1: (x, y, s), -1: (x, y, s)}


SHEETS = {
    # ---------------------------------------------------------------- ATTACK 1: THE WORM SPIT
    'danny_sumo_spit': dict(size=(176, 144), oy=0, frames=[
        ('heave', dict(AWAKE, body=(0, 2), belly=3, eyes='squeeze', mouth='purse', puff=0.35, head_dy=1), 130),
        ('puff', dict(AWAKE, body=(0, 0), eyes='wide', mouth='purse', puff=1.0), 170),
        # the wind-up: no headroom to rear back, so he cocks it to the side like a pitcher, arms up
        ('lean', dict(AWAKE, body=(-2, 1), head_dx=-1, head_tilt=-7, eyes='squeeze', mouth='purse', puff=1.0,
                      arms=('cock', 'cock'), cock_rot=cock(3)), 150),
        ('spit', dict(AWAKE, body=(2, 5), head_dx=1, head_dy=2, head_tilt=7, arms=('limp', 'limp'), mouth='spit',
                      jaw=3), 110),
        ('spit2', dict(AWAKE, body=(-2, 5), head_dx=-1, head_dy=2, head_tilt=-7, arms=('limp', 'limp'), mouth='spit',
                       jaw=3), 110),
        ('recover', dict(body=(0, 1), belly=1, eyes='half', mouth='slack', drool=True, bubble=0), 240),
    ], note='once: 0-2 wind up, 3 spits worm puddle 1, 4 spits puddle 2, 5 settles back to idle'),

    # ---------------------------------------------------------------- ATTACK 2: THE SUMO SMASH
    'danny_sumo_jump': dict(size=(176, 160), oy=16, frames=[
        ('crouch', dict(AWAKE, body=(0, 7), belly=1, head_dy=1, arms=('limp', 'limp'), mouth='grit'), 180),
        ('launch', dict(AWAKE, body=(0, -14), arms=('cock', 'cock'), cock_rot=cock(3), mouth='shout'), 80),
        ('tuck', tuck(sx=0.97, sy=1.04, mouth='shout'), 100),
    ], note='once, then danny_sumo_air; 0-1 feet on the floor row, 2 rear on it (the code lifts from 2)'),
    'danny_sumo_air': dict(size=(176, 144), oy=0, frames=[
        ('hover_a', tuck(deg=-3.0), 120),
        ('hover_b', tuck(deg=-1.0, sy=1.015), 120),
        ('hover_c', tuck(deg=2.5), 120),
        ('hover_d', tuck(deg=0.5, sy=1.015), 120),
    ], note='loop while he hangs and tracks; the rear is on the floor row, the code lifts the sprite'),
    'danny_sumo_slam': dict(size=(176, 144), oy=0, frames=[
        ('descend', tuck(sx=0.95, sy=1.06, mouth='shout'), 60),
        ('impact', tuck(sx=1.07, sy=0.8, eyes='squeeze', mouth='shout', head=(0, 16)), 100),
        ('rebound', tuck(sx=0.95, sy=1.07, mouth='shout', head=(0, 10)), 80),
    ], note='descend (falling), impact (rear on the floor: the quake ring), rebound (back up); x5'),

    # ---------------------------------------------------------------- THE NAP
    'danny_sumo_sleep': dict(size=(176, 144), oy=0, frames=[
        ('sleep_a', dict(SEAT, body=(0, 11), head_dy=4, head_dx=2, head_tilt=15, eyes='sleepy', mouth='snore',
                         bubble=3, drool=True), 300),
        ('sleep_b', dict(SEAT, body=(0, 11), belly=1, head_dy=5, head_dx=2, head_tilt=16, eyes='sleepy',
                         mouth='snore', bubble=4, drool=True), 280),
        ('sleep_c', dict(SEAT, body=(0, 11), belly=2, head_dy=5, head_dx=2, head_tilt=17, eyes='sleepy',
                         mouth='snore', bubble=5, drool=True), 360),
        ('sleep_d', dict(SEAT, body=(0, 11), belly=1, head_dy=5, head_dx=2, head_tilt=16, eyes='sleepy',
                         mouth='snore', bubble=4, drool=True), 280),
    ], note='loop while he regenerates'),
    'danny_sumo_sleep_hit': dict(size=(176, 144), oy=0, frames=[
        ('flinch', dict(SEAT, body=(0, 9), head_dy=2, head_dx=1, head_tilt=6, eyes='scrunch', mouth='grit',
                        bubble=0, pop=True), 90),
        ('snort', dict(SEAT, body=(0, 11), head_dy=4, head_dx=2, head_tilt=13, eyes='sleepy', mouth='purse',
                       bubble=1), 170),
    ], note='once per hit, then back to danny_sumo_sleep (the bubble pops and starts again)'),

    # ---------------------------------------------------------------- ATTACK 3: THE SUMO HEADBUTT
    'danny_sumo_headbutt': dict(size=(224, 144), oy=0, frames=[
        ('windup', side(ground=True, hip=(104.0, 104.0), lean=56.0, head=-34.0, arm=14.0, elbow=8.0, thigh=-122.0,
                        knee=96.0, foot=-30.0, far=((-114.0, 92.0, -34.0), (5.0, 0.0)), lift=0.05), 170),
        ('launch', side(ground=True, hip=(104.0, 96.0), lean=72.0, head=-22.0, arm=4.0, elbow=8.0, thigh=-2.0, knee=10.0,
                        foot=40.0, far=((-14.0, 22.0, 30.0), (6.0, 0.0)), mouth='shout', flutter=20.0), 60),
        ('flight_a', side(**TORPEDO), 50),
        ('flight_b', side(**dict(TORPEDO, hip=(104.0, 91.0), foot=66.0, flutter=58.0, elbow=10.0,
                                 far=((2.0, -2.0, 78.0), (6.0, 1.0)))), 50),
        ('bonk', side(**dict(TORPEDO, eyes='squeeze', mouth='ow', flutter=10.0,
                             squash=(0.84, 1.1, (200.0, 81.0)))), 90),
        # the rebound: thrown back off the target, head and torso first, arms and legs lagging forward
        ('recoil', side(hip=(92.0, 104.0), lean=-18.0, head=-14.0, arm=-58.0, elbow=-12.0, thigh=-58.0, knee=52.0,
                        foot=20.0, eyes='wide', mouth='ow', hand='open', flutter=-30.0,
                        far=((-70.0, 60.0, 16.0), (7.0, 0.0))), 140),
    ], note='0 wind-up (feet on the mat), 1 launch (toes leaving it), loop 2-3 in flight, 4 bonk on contact or '
            'parry, 5 recoil; faces right, the code flips it'),

    # ---------------------------------------------------------------- THE ENDING
    'danny_sumo_block': dict(size=(176, 144), oy=0, frames=[
        ('block_a', dict(SMUG, arms=('cock', 'cock'), bubble=2), 220),
        ('block_b', dict(SMUG, arms=('cock', 'cock'), belly=1, head_dy=1, bubble=3, cock_rot=cock(0, 3)), 200),
        ('block_c', dict(SMUG, arms=('cock', 'cock'), belly=2, head_dy=1, bubble=4, eyes='sleepy'), 300),
        ('block_d', dict(SMUG, arms=('cock', 'cock'), belly=1, head_dy=1, bubble=3, cock_rot=cock(0, 3)), 200),
    ], note='loop while he fills the gateway'),
    'danny_sumo_push': dict(size=(176, 144), oy=0, frames=[
        # The clinch (the plan: Danny's feet at GATE_BLOCK y 500, the player's 48 px = 16 texels below,
        # the player's gloves 26 texels up): his palms come down to his apron, their centres near row
        # 128, close either side of the middle so the gloves meet their inner edges.
        ('set', dict(PUSH, body=(0, 8), head_dy=2, push_at=palms(75, 120, 1.1), eyes='awake', mouth='frown'), 200),
        ('strain_a', dict(STRAIN, body=(-1, 9), head_dy=2, push_at=palms(75, 119, 1.1), sweat=[(52, 22)],
                          foot_l=(-1, 0)), 90),
        ('strain_b', dict(STRAIN, body=(1, 9), head_dy=3, push_at=palms(75, 120, 1.1), sweat=[(52, 24)],
                          foot_r=(1, 0)), 90),
        ('strain_c', dict(STRAIN, body=(0, 10), head_dy=2, push_at=palms(75, 118, 1.1), sweat=[(52, 26), (118, 20)]),
         90),
        # the winning shove (SF6's Show of Force): both palms thrust down-screen, the body lunging after them
        ('win', dict(PUSH, body=(0, 10), head_dy=3, push_at=palms(71, 115, 1.35), foot_r=(0, -3),
                     eyes='awake', mouth='shout'), 150),
        # the losing skid: palms driven back up toward him, the body leaning into it, sliding up-screen
        ('skid', dict(STRAIN, body=(0, 7), head_dy=1, push_at=palms(76, 116, 1.05), eyes='wide', mouth='grit',
                      sweat=[(50, 20), (120, 22)]), 120),
        # pushed out: off balance backward, then toppling back away from the camera, soles up at us
        ('out_a', dict(AWAKE, body=(0, 1), head_dy=-2, arms=('cock', 'cock'), cock_rot=cock(3), foot_l=(0, -6),
                       eyes='wide', mouth='ow'), 110),
        ('out_b', dict(AIR, body=(0, 12), leg_deg=42, head_dy=-2, cock_rot=cock(10), eyes='wide', mouth='ow'), 220),
    ], note='0 set; loop 1-3 while it is even; 4 when he gains; 5 when he loses ground; 6-7 pushed out'),
}


def close_pinholes(px):
    """A transparent texel boxed in on four sides is filled: keyline if two of its neighbours are,
    else the commonest neighbour (danny_juggle/dposes.finish)."""
    for _ in range(2):
        for q in FT.K.pinholes(px):
            n = [px[(q[0] + dx, q[1] + dy)] for dx, dy in FT.K.N4]
            px[q] = 'k' if n.count('k') >= 2 else max(sorted(set(n)), key=n.count)
    return px


def frame_px(spec):
    return close_pinholes(_frame_px(spec))


def _frame_px(spec):
    if 'tuck' in spec:
        return FT.floor_clip(TK.build(spec['tuck']).px)
    if 'side' in spec:
        px = SD.build(spec['side'])[0].px
        if spec.get('ground'):
            low = max(y for (x, y) in px)
            px = {(x, y + 143 - low): k for (x, y), k in px.items()}
        return FT.floor_clip(px)
    return FT.floor_clip(FT.build(spec, free=True).px)


def frame_image(sheet, spec):
    w, h = SHEETS[sheet]['size']
    ox = 0 if 'side' in spec else (w - 176) // 2
    return FT.image_of(frame_px(spec), w, h, ox, SHEETS[sheet]['oy'])
