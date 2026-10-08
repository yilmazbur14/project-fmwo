"""Prove the scratch copies of the Liam rig and the puppet rig reproduce live/approved sheets pixel-identically."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import guard  # noqa
sys.path.insert(0, os.path.join(HERE, 'liam_rig'))
sys.path.insert(0, os.path.join(HERE, 'pup_rig'))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
from PIL import Image
from imgdiff import pixel_diff
P = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
import le_full as F, le_build as LB
ok = True
for name, fn in (('cast_right', F.cast_right), ('talk_elements', F.talk_elements), ('cast_left', F.cast_left)):
    frames = [f[0] for f in fn()]
    im = LB.strip(frames)
    live = Image.open(P + '/Assets/Characters/Liam/Elements/liam_%s.png' % name)
    d = pixel_diff(im, live)
    print('liam rig', name, 'IDENTICAL' if not d else d)
    ok &= not d
import jp_bosses as B, jp_ship as SH, jp_core as C
for key, rel, fw, live in (('matt', 'Matt/matt_idle.png', 96, 'Jordan/Puppets/matt/matt_idle.png'),
                           ('mason', 'Mason/mason_sheet.png', 64, 'Jordan/Puppets/mason/mason_sheet.png')):
    sheet, infos, problems = SH.build_sheet(B.BOSSES[key], rel, fw)
    d = pixel_diff(sheet, Image.open(P + '/Assets/Characters/' + live))
    print('puppet rig', rel, 'IDENTICAL' if not d else d, '| problems', problems[:3])
    ok &= not d
# the unshipped Liam puppet (approval take B) from the same recipe
im, info = C.treat(B.BOSSES['liam'], B.BOSSES['liam'].src(0), 'B')
d = pixel_diff(im, Image.open(P + '/art_source/jordan_puppets/approval/liam/liam_idle_B.png'))
print('puppet rig liam idle B', 'IDENTICAL' if not d else d)
ok &= not d
print('ALL IDENTICAL' if ok else 'MISMATCH')
