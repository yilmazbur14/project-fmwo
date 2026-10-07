"""Does the scratch copy of the rig rebuild the LIVE sheets pixel for pixel?"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard  # noqa
import env
from PIL import Image
import mg_base as M
from mg_base import B, F
import mg_matt as MM
import mi_roar
import mf_idle, mf_shout, mf_recover
from imgdiff import pixel_diff

# the modules must come from the scratch copy
for m in (B, F, MM, mi_roar, mf_idle, mf_shout):
    assert os.path.normcase(m.__file__).startswith(os.path.normcase(env.RIG)), m.__file__
print('rig copy at', env.RIG)
print('B.ASSETS ->', B.ASSETS)

def live(name):
    return Image.open(os.path.join(env.LIVE_MATT, name + '.png')).convert('RGBA')

sheets = [
    ('matt_roar', mi_roar.figs),
    ('matt_idle', mf_idle.Idle.figs),
    ('matt_yell_tell', mf_shout.YellTell.figs),
    ('matt_mystic_cast', mf_shout.MysticCast.figs),
    ('matt_recover', mf_recover.Recover.figs),
    ('matt_stomp', MM.stomp_figs),
    ('matt_fury', MM.fury_figs),
    ('matt_yell_up', MM.yell_up_figs),
]
ok = True
for name, fn in sheets:
    frames = [F.px_of(f) for f in fn()]
    im = B.strip(frames)
    d = pixel_diff(im, live(name))
    print('%-18s %d frames  vs live: %s' % (name, len(frames), d or 'IDENTICAL'))
    ok &= d is None
# the approved matt.png from the base rig
d = pixel_diff(B.strip([B.matt.build(False).image(), B.matt.build(True).image()]), live('matt'))
print('%-18s vs live: %s' % ('matt (approved)', d or 'IDENTICAL'))
ok &= d is None
print('ALL IDENTICAL' if ok else 'MISMATCH')
