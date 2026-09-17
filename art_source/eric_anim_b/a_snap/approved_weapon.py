"""The approved v2 sword/arm drawing (from sword128.py) as a movable layer."""
import rig
import lib
import sword128
from weapons import FIST_V


def weapon_layer(parts=('arm', 'blade', 'hilt')):
    fr = rig.Frame()
    cv = fr.as_canvas()
    if 'arm' in parts:
        sword128.arm(cv)
    if 'blade' in parts:
        sword128.blade(cv)
    if 'hilt' in parts:
        sword128.hilt(cv)
    return fr.rgba()


_W = {}


def draw(fr, dx=0, dy=0, fist_dx=None, fist_dy=None, arm_dx=None, arm_dy=None):
    """draw approved arm + sword + fist onto frame with offsets"""
    if not _W:
        _W['arm'] = weapon_layer(('arm',))
        _W['sword'] = weapon_layer(('blade', 'hilt'))
    adx = dx if arm_dx is None else arm_dx
    ady = dy if arm_dy is None else arm_dy
    fr.put(_W['arm'], adx, ady, 0, 0)
    fr.put(_W['sword'], dx, dy, 0, 0)
    fc = sword128.SW.P(-10.0, 0)
    x0, y0 = int(round(fc[0])) - 6, int(round(fc[1])) - 6
    fdx = dx if fist_dx is None else fist_dx
    fdy = dy if fist_dy is None else fist_dy
    pts = rig.stamp_mask(FIST_V, x0 + fdx, y0 + fdy)
    rig.cast_shadow_pts(fr, pts, 1, 2)
    fr.stamp(FIST_V, x0 + fdx, y0 + fdy)
