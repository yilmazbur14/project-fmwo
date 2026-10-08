import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ea_base as E
from ea_base import F, B, V
import ea_echo as EC
import mi_anchors as AN
import mi_roar
import env

s = int(sys.argv[1]) if len(sys.argv) > 1 else 4
tag = sys.argv[2] if len(sys.argv) > 2 else 'v'
figs = EC.figs()
pxs = [F.px_of(f) for f in figs]
for i, (f, px) in enumerate(zip(figs, pxs)):
    im = B.image(px)
    st = B.stats(im)
    a = B.audit(px, f.fx)
    anc = AN.anchors(f, px)
    print('f%d black %.1f%% colours %d bbox %s crest_top %s mouth %s audit %s' % (
        i, 100 * st['black'], st['colours'], B.bbox(px), anc['crest_top'], anc['mouth'],
        {k: v[:4] for k, v in a.items() if v} or 'clean'))
roar = B.image(F.px_of(mi_roar.figs()[1]))
ims = [B.image(p) for p in pxs] + [roar]
out = V.frames_row(ims, s, labels=EC.LABELS + ['live roar f1'])
out.save(os.path.join(env.WORK, 'echo_%s.png' % tag))
