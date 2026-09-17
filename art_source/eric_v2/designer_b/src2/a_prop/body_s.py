"""Scaled Eric body layers (96-space canvases) for the proportion pass."""
import scaled as SC
import lib
import parts
from parts import (cape, flap, tassets, belt, torso, torso_details, gorget, pauldron, ID)
from parts import mirror as mirror96
import head_s

_CACHE = {}


def _layer(fn):
    lib.W = lib.H = 96
    cv = lib.Canvas()
    with SC.scaled_geometry():
        fn(cv)
    return cv.rgba()


def _torso(cv):
    tm = torso(cv)
    torso_details(cv, tm)


def _paul(f):
    def go(cv):
        d, l1, l2 = pauldron(cv, f)
        SC.pauldron_details_s(cv, f, d, l1, l2)
    return go


def _tass(cv):
    tassets(cv)
    SC.tasset_details_s(cv)


def _head(cv):
    head_s.render(cv)


LAYERS = [
    ('cape', cape), ('legs', SC.stamp_legs_s), ('flap', flap), ('tassets', _tass), ('belt', belt),
    ('torso', _torso), ('buckle', SC.belt_details_s), ('gorget', gorget),
    ('paulL', _paul(ID)), ('paulR', _paul(mirror96)), ('armR_front', SC.akimbo_arm_s), ('head', _head),
]


def layers():
    if not _CACHE:
        for name, fn in LAYERS:
            if name == 'head':
                lib.W = lib.H = 96
                cv = lib.Canvas()
                fn(cv)
                _CACHE[name] = cv.rgba()
            else:
                _CACHE[name] = _layer(fn)
    return _CACHE


ORDER = ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'paulL', 'paulR', 'armR_front', 'head']
