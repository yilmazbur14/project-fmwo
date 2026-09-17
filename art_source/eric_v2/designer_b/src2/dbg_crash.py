import sys
import faulthandler
faulthandler.enable()
step = sys.argv[1]
print('step', step, flush=True)
from base2 import *
print('base2 ok', flush=True)
import views2
if step == 'views':
    V, L = views2.build(45, -1)
    print('views ok', flush=True)
elif step == 'arc':
    import whirl2
    b = whirl2.arc_band(45.0, 'back')
    print('arc ok', len(b), flush=True)
elif step == 'sword':
    import whirl2
    from sword2 import Sword2
    fr = R.Frame()
    wf()
    Sword2((140, 164), 10.0, 1.0).draw(fr.canvas())
    print('sword ok', flush=True)
elif step == 'arc_then_views':
    import whirl2
    b = whirl2.arc_band(45.0, 'back')
    print('arc ok', flush=True)
    V, L = views2.build(45, -1)
    print('views ok', flush=True)
elif step == 'frame':
    import whirl2
    whirl2.whirl_frame(int(sys.argv[2]))
    print('frame ok', flush=True)
