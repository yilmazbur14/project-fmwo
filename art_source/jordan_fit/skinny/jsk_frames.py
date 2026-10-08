"""The skinny approval pass's frames, before and after, built in memory from the rigs. It writes PNGs
only into the folder it is given, which must be this folder or lie outside the project (a temp
folder): nothing can land under Assets/ or in another rig's folder.

    python jsk_frames.py fight   <out dir>   idle f0, summon f2 (= v2's frame 1), the 4 idle frames
    python jsk_frames.py rage    <out dir>   jordan_rage f0 (the standing finale)
    python jsk_frames.py seated  <out dir>   jordan_seated f6 (friendly, mouth shut)
    python jsk_frames.py measure             janim_measure's layout numbers, fitted vs skinny (no files)

Each family runs in its own process: the standing finale's base applies jfit_body over v2 as it loads
and the seated finale imports its own rig, so jsk_previews.py calls this once per family.
"before" is each rig as it stands, proved equal to the live PNG pixel for pixel; "after" is the same
builder inside jsk_body.skinny(). One JSON line of numbers per frame goes to stdout.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(ART)
LIVE = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan')
sys.path.insert(0, HERE)
sys.path.insert(0, ART)
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def out_dir(path):
    if _under(path, ROOT) and not _under(path, HERE):
        raise SystemExit('refusing %s: inside the project, frames go only into %s' % (path, HERE))
    os.makedirs(path, exist_ok=True)
    return path


def live_frame(rel, i, size):
    return Image.open(os.path.join(LIVE, rel)).convert('RGBA').crop((size * i, 0, size * i + size, size))


def numbers(name, im, audit):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    op = [c for c in data if c[3] > 0]
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    print(json.dumps({'frame': name, 'opaque': len(op), 'black': round(black / max(1, len(op)), 4),
                      'colours': len(set(op)), 'semi': sum(1 for c in data if 0 < c[3] < 255),
                      'gaps': len(audit['gaps']), 'lone': len(audit['lone']), 'holes': len(audit['holes']),
                      'keys': audit['keys'], 'size': im.size}))


def save(im, folder, name):
    im.save(os.path.join(folder, name + '.png'))


def check_live(name, im, ref):
    d = pixel_diff(im, ref)
    if d:
        raise SystemExit('%s: the rig as it stands no longer matches the live file: %s' % (name, d))


def fight(folder):
    import jsk_body as K
    import jv2_frames as F
    sys.path.append(os.path.join(ART, 'jordan_anims'))
    import janim_base as AB
    import janim_idle as AI
    B = K.B
    shots = (('idle_f0', 0, 'jordan_idle.png', 0), ('summon_f2', 1, 'jordan_summon.png', 2))
    for name, v2f, rel, i in shots:
        im = B.image(F.frame_px(v2f))
        check_live(name, im, live_frame(rel, i, 96))
        save(im, folder, 'before_' + name)
        numbers('before_' + name, im, B.audit(F.frame_px(v2f), F.fx_pixels(v2f)))
    with K.skinny():
        for name, v2f, rel, i in shots:
            px = F.frame_px(v2f)
            im = B.image(px)
            save(im, folder, 'after_' + name)
            numbers('after_' + name, im, B.audit(px, F.fx_pixels(v2f)))
        strip = Image.new('RGBA', (384, 96), (0, 0, 0, 0))
        for i, b in enumerate(AI.builders()):
            cv, fx = b()
            px = AB.finish(cv)
            im = AB.to_image(px)
            numbers('after_idle_strip_f%d' % i, im, AB.audit(px, {(x + AB.ANCHOR_SHIFT, y) for (x, y) in fx}))
            strip.alpha_composite(im, (96 * i, 0))
        save(strip, folder, 'after_idle_strip')
    print(json.dumps({'variant': K.VARIANT}))


def rage(folder):
    sys.path.insert(0, os.path.join(ART, 'jordan_finale_standing'))
    import jfs_base as FB   # applies jfit_body over v2 as it loads
    import jfs_rage as R
    import jsk_body as K

    def render():
        cv, fx = R.build('glare_shut', (0, 0))
        return FB.fill_holes(FB.finish(cv)), {(x + FB.ANCHOR_SHIFT, y) for (x, y) in fx}
    px, fx = render()
    im = FB.to_image(px)
    check_live('rage_f0', im, live_frame('jordan_rage.png', 0, 96))
    save(im, folder, 'before_rage_f0')
    numbers('before_rage_f0', im, FB.audit(px, fx))
    with K.skinny(jf=FB.JF):
        px, fx = render()
        im = FB.to_image(px)
        save(im, folder, 'after_rage_f0')
        numbers('after_rage_f0', im, FB.audit(px, fx))


def seated(folder):
    sys.path.insert(0, os.path.join(ART, 'jordan_finale_chars'))
    import jfc_base as CB
    import jfc_front as CF
    import jsk_body as K

    def render():
        cv, fx = CF.build('friendly_shut', 'wave', 'rest')
        return cv.px, fx
    px, fx = render()
    im = CB.image(px)
    check_live('seated_f6', im, live_frame(os.path.join('Room', 'jordan_seated.png'), 6, 128))
    save(im, folder, 'before_seated_f6')
    numbers('before_seated_f6', im, CB.audit(px, fx))
    with K.skinny(seated=(CB, CF)):
        px, fx = render()
        im = CB.image(px)
        save(im, folder, 'after_seated_f6')
        numbers('after_seated_f6', im, CB.audit(px, fx))
        print(json.dumps({'check_fit_matches': CF.check_fit_matches()}))


def measure():
    """janim_measure.report() as the rig stands and with the skinny build. janim_base's approved-frame
    check compares with the shipped v2 PNG, which the skinny frames do not equal by design, so for the
    skinny run approved_frame() returns the patched rig's frame (make_frames still proves each sheet's
    approved frame is that rig frame, pixel for pixel)."""
    import difflib
    import subprocess
    code = ('import sys; sys.dont_write_bytecode = True; sys.path[:0] = [%r, %r]\n'
            'import jsk_body as K, janim_base as AB, janim_measure as JM\n'
            'if %%s:\n    K.apply(); AB.approved_frame = lambda i: AB.jv2_frames.frame_px(i)\n'
            'print(JM.report())\n') % (HERE, os.path.join(ART, 'jordan_anims'))
    runs = [subprocess.run([sys.executable, '-c', code % flag], capture_output=True, text=True, check=True).stdout
            for flag in ('False', 'True')]
    diff = list(difflib.unified_diff(runs[0].splitlines(), runs[1].splitlines(), 'fitted', 'skinny', lineterm=''))
    print(runs[1])
    print('layout numbers, fitted vs skinny:', '\n'.join(diff) if diff else 'IDENTICAL (every body box, head, crown, '
          'hand, box, fist, pop, star and glint point)')


if __name__ == '__main__':
    fam = sys.argv[1] if len(sys.argv) > 1 else ''
    if fam == 'measure':
        measure()
    elif fam in ('fight', 'rage', 'seated') and len(sys.argv) > 2:
        {'fight': fight, 'rage': rage, 'seated': seated}[fam](out_dir(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(2)
