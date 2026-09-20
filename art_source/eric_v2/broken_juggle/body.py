"""Whole-body assembly on top of jr: a pose = torso-group transform + head + limbs + cape, in z order.

Pose dictionary keys (all frame px / degrees clockwise):
    hip      frame point where the 96-space pelvis (48, 76) lands
    ang      torso group rotation about the pelvis
    head     (d_ang, dx, dy): head rotation relative to the torso, and a nudge of the neck point
    expr     faces.EXPR key
    arms     {'L': dict(elbow=(x,y), wrist=(x,y), hand='fist'|'fist_h'|'open', hand_ang=deg), 'R': ...}
             L = viewer-left arm (his right), R = viewer-right arm
    legs     {'L': dict(knee=(x,y), ankle=(x,y), foot_ang=deg), 'R': ...} or 'idle' (standing stamp)
    cape     callable(layer, pose) drawing the cape layer, or None for the idle cape
    order    optional explicit z order of layer names
"""
import math
import jr
import faces
from jr import Layer, Tf, about, FW, FH
from lib import PALC, BLACK

PELVIS96 = (48.0, 76.0)
NECK96_BODY = (48.0, 40.0)          # where the neck sits on the torso group (96-space)
SHOULDER96 = {'L': (27.0, 50.0), 'R': (69.0, 50.0)}   # arm sockets under the pauldrons
HIP96 = {'L': (33.0, 80.0), 'R': (63.0, 80.0)}         # leg sockets under the tassets


def torso_tf(pose):
    return Tf(PELVIS96, pose['hip'], pose.get('ang', 0.0))


def joint(pose, p96):
    return torso_tf(pose).pt(*p96)


def head_tf(pose):
    tf = torso_tf(pose)
    nx, ny = tf.pt(*NECK96_BODY)
    da, dx, dy = pose.get('head', (0.0, 0.0, 0.0))
    # the idle neck point (128, 147.2) is the torso's (48, 40) point: keep the same relation
    return jr.HeadTf((nx + dx, ny + dy), tf.a + da)


def arm(lay, shoulder, a):
    """upper arm (chain) + elbow cop + forearm (plate) + hand"""
    el, wr = a['elbow'], a['wrist']
    jr.limb(lay, shoulder, el, a.get('uw', 9), ramp='chain')
    jr.limb(lay, el, wr, a.get('fw', 9), ramp='plate')
    jr.cop(lay, el, 4.6, 4.4)
    h = a.get('hand', 'fist')
    if h == 'fist':
        jr.fist(lay, wr[0] + a.get('hdx', 0), wr[1] + a.get('hdy', 0))
    elif h == 'fist_h':
        jr.fist(lay, wr[0] + a.get('hdx', 0), wr[1] + a.get('hdy', 0), horizontal=True)
    elif h == 'open':
        ha = a.get('hand_ang')
        if ha is None:
            ha = math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0])) - 90
        jr.gauntlet_open(lay, wr, ha, spread=a.get('spread', 1.0), curl=a.get('curl', 0.0),
                         mirror=a.get('mirror', False))


def kneel_leg(lay, hip, g):
    """a knee planted on the mat seen from the front: short foreshortened cuisse + a big knee cop; the
    shin runs back out of sight and the sabaton's toe peeks out behind the knee"""
    kn = g['knee']
    toe = g.get('toe')
    if toe:
        cv = lay.cv()
        jr.wf()
        import lib
        m = lib.ell(toe[0], toe[1], 5.2, 2.6)
        cv.part(m, 'plate', ('sphere', toe[0] - 1.5, toe[1] - 1.0, 6.0, 3.4, 0.1), th=jr.TH_METAL, bias=1)
    jr.limb(lay, hip, kn, g.get('tw', 11), ramp='plate')
    jr.cop(lay, kn, g.get('krx', 6.8), g.get('kry', 4.6))


def leg(lay, hip, g):
    if g.get('kneel'):
        return kneel_leg(lay, hip, g)
    jr.leg_front(lay, hip, g['knee'], g['ankle'], foot_ang=g.get('foot_ang'), thigh_w=g.get('tw', 11.0),
                 dark=g.get('dark', 0), thigh=g.get('thigh', True), foot_w=g.get('fw', 15.0), boot=g.get('boot'))


def render(pose):
    """returns (frame Layer, dict of named layers)"""
    tf = torso_tf(pose)
    L = {}

    def new(name):
        L[name] = Layer()
        return L[name]

    # cape
    cape = pose.get('cape')
    if cape is None:
        jr.cape_idle(new('cape'), tf)
    elif cape is not False:
        cape(new('cape'), pose)
    # legs
    legs = pose.get('legs', 'idle')
    if legs == 'idle':
        s = tf.shift()
        jr.legs_idle(new('legs'), *(s or (0, 0)))
    elif legs:
        for side in ('L', 'R'):
            if side in legs:
                leg(new('leg' + side), joint(pose, HIP96[side]), legs[side])
    jr.flap(new('flap'), tf)
    jr.tassets(new('tassets'), tf, flare=pose.get('flare', 0.0))
    jr.belt(new('belt'), tf)
    jr.torso(new('torso'), tf, *pose.get('torso', (0.0, 0.0)))
    jr.buckle(new('buckle'), tf)
    jr.gorget(new('gorget'), tf)
    so = pose.get('shoulders', (0, 0))
    stf = Tf(PELVIS96, (pose['hip'][0] + so[0], pose['hip'][1] + so[1]), tf.a)
    jr.pauldron(new('paulL'), stf, 0)
    jr.pauldron(new('paulR'), stf, 1)
    arms = pose.get('arms', {})
    for side in ('L', 'R'):
        if side in arms:
            sh = stf.pt(*SHOULDER96[side])
            arm(new('arm' + side), arms[side].get('shoulder', sh), arms[side])
    ht = head_tf(pose)
    ex = pose.get('expr', 'idle')
    jr.render_head(new('head'), ht, expr=faces.expr(ex))
    for name, fn in pose.get('extra', {}).items():
        fn(new(name), pose)
    order = pose.get('order') or default_order(pose)
    fr = Layer()
    for name in order:
        if name in L:
            fr.over(L[name])
    return fr, L


def default_order(pose):
    return ['back', 'cape', 'armR_back', 'legL', 'legR', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle',
            'gorget', 'armL_under', 'paulL', 'paulR', 'armL', 'armR', 'head', 'front']
