"""A finished juggle frame: Matt rendered and turned (mj_poses), then his effects (mj_fx).

frame(i) -> Built with
    px      the frame's key map (him plus effects)
    body    his pixels only (the figure, before effects)
    owner   which rig part owns each of his pixels
    fx      the effect pixels (which float free of a keyline by design)
"""
import mj_base as J
import mj_poses as MP


class Built:
    def __init__(self, name, px, body, owner, fx, hold, spec):
        self.name, self.px, self.body, self.owner, self.fx = name, px, body, owner, fx
        self.hold, self.spec = hold, spec


def frame(i, effects=True):
    spec = MP.FRAMES[i]()
    body, owner = MP.render(spec)
    body = {p: k for p, k in body.items() if 0 <= p[0] < J.W and 0 <= p[1] < J.H}
    px = dict(body)
    fx = set()
    if effects:
        import mj_fx
        fx = mj_fx.add(i, spec, px, body)
    return Built(spec.name, px, body, owner, fx, spec.hold, spec)


def frames(effects=True):
    return [frame(i, effects) for i in range(len(MP.FRAMES))]
