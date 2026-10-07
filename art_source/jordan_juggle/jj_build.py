"""A finished juggle frame: Jordan rendered and turned (jj_poses), then his effects (jj_fx).

frame(i) -> Built with
    px      the frame's key map (him plus effects)
    body    his pixels only (the figure, before effects)
    owner   which rig part owns each of his pixels
    fx      the effect pixels (which float free of a keyline by design)
"""
import jj_base as J
import jj_poses as MP


class Built:
    def __init__(self, name, px, body, owner, fx, hold, spec):
        self.name, self.px, self.body, self.owner, self.fx = name, px, body, owner, fx
        self.hold, self.spec = hold, spec


def seal_sneakers(body, owner):
    """The approved sneakers light a few edge texels with no keyline over them (janim_export's
    SNEAKER_QUIRKS: on the standing frames the jeans' hem sits against them). Wherever a sneaker is
    left touching open air in a juggle frame, the gap gets the keyline the rest of him has."""
    add = []
    for (x, y), k in body.items():
        if k == 'k' or not str(owner.get((x, y), '')).startswith('shoe'):
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in body:
                add.append(q)
    for q in add:
        body[q] = 'k'
        owner[q] = 'shoe_seal'
    return len(set(add))


def seal_hands(body, owner):
    """A hand map's corner texel left touching open air gets the keyline the rest of him has. Until
    2026-09-28 the sack tee always lay under the hands' edges; the fitted tee leaves one open, on the
    hug's grip in the second lying frame."""
    add = []
    for (x, y), k in body.items():
        if k == 'k' or not str(owner.get((x, y), '')).startswith('hand'):
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in body:
                add.append(q)
    for q in add:
        body[q] = 'k'
        owner[q] = 'hand_seal'
    return len(set(add))


def frame(i, effects=True):
    spec = MP.FRAMES[i]()
    body, owner = MP.render(spec)
    body = {p: k for p, k in body.items() if 0 <= p[0] < J.W and 0 <= p[1] < J.H}
    seal_sneakers(body, owner)
    seal_hands(body, owner)
    px = dict(body)
    fx = set()
    if effects:
        import jj_fx
        fx = jj_fx.add(i, spec, px, body, owner)
    return Built(spec.name, px, body, owner, fx, spec.hold, spec)


def frames(effects=True):
    return [frame(i, effects) for i in range(len(MP.FRAMES))]
