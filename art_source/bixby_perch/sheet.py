"""Build the 16 perch frames, in sheet order, as 192x256 RGBA images."""
from PIL import Image

from common import FW, FH, TOP_ROW
import perch
import poses

NAMES = [('perch_land', 2), ('perch', 2), ('volley', 3), ('inhale', 3), ('rear_back', 1),
         ('perch_breath', 2), ('spent', 1), ('release', 2)]


def index_table():
    out, i = {}, 0
    for name, n in NAMES:
        out[name] = list(range(i, i + n))
        i += n
    return out


def frames(check=True):
    import rig
    ims = [perch.build(P).image() for P in poses.frames()]
    ims.append(rig.build(poses.release_upright()).image())
    assert len(ims) == 16, len(ims)
    for i, im in enumerate(ims):
        assert im.size == (FW, FH), im.size
        if check:
            bb = im.getbbox()
            # the headroom: nothing above ROPE - 33 (it would leave the top of the screen)
            assert bb is None or bb[1] >= TOP_ROW, 'frame %d draws on row %d, above row %d' % (i, bb[1], TOP_ROW)
    return ims


def strip(ims):
    out = Image.new('RGBA', (FW * len(ims), FH), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        out.alpha_composite(im, (i * FW, 0))
    return out
