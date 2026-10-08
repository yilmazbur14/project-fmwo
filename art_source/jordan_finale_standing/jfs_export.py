"""Write Jordan's four standing finale sheets, each PNG with its .aseprite beside it, and their
previews.

    python jfs_export.py            # print this and exit; writes nothing
    python jfs_export.py --check    # build and audit every frame, print the numbers; writes nothing
    python jfs_export.py --write    # ...then write into THIS folder: the four sheets (.png + .aseprite)
                                    # and preview/ (the 4x contact sheet, a GIF per sheet, the room mocks)
    python jfs_export.py --ship     # ...then write the four sheets as NEW files into
                                    # Assets/Characters/Jordan/ (approved by the user 2026-09-28); refuses
                                    # if any of the eight files already exists

--ship writes only these eight names: jordan_getup, jordan_walk_away, jordan_rage, jordan_zap
(.png and .aseprite), into Assets/Characters/Jordan/ and nowhere else; each is built in a temp folder,
round-tripped, moved into place in one step and checked again where it landed.

It refuses any output path that resolves (realpath, so 8.3 short names can't slip past) outside
art_source/jordan_finale_standing/ or under Assets/. Each .aseprite is made by Aseprite's CLI from its
PNG, and re-exported and compared with it pixel for pixel (art_source/imgdiff.pixel_diff: alpha
everywhere, colour wherever a pixel shows) where both landed.

Checked for every frame before anything is written: 96x96, the strip horizontal with frame 0 leftmost,
the lowest drawn row 95, every colour one of the approved v2 sheet's 40 (jordan_redesign_v2.png), the
black pure #000000, no semi-alpha, no keyline gaps, stray pixels or pinholes (effects - sparks, steam,
dust, the zap's energy - float free by design and are exempt from the gap and stray checks).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jfs_base as B  # noqa: E402
import jfs_getup  # noqa: E402
import jfs_walk  # noqa: E402
import jfs_rage  # noqa: E402
import jfs_zap  # noqa: E402
import jfs_previews as PV  # noqa: E402
from PIL import Image  # noqa: E402

MODULES = [jfs_getup, jfs_walk, jfs_rage, jfs_zap]
LABELS = {
    'jordan_getup': [('the snap', 'head jerks up glaring, grips the box'), ('the kneel', 'up on one knee, box snatched up'),
                     ('rising', 'pushing up, box at his hip, the vein'), ('up and furious', 'the stance he storms off from')],
    'jordan_walk_away': [('right foot down', 'dust; left heel lifting'), ('down on the right', 'body a row lower'),
                         ('passing', 'left foot swung through'), ('left foot down', 'dust; right heel lifting'),
                         ('down on the left', 'body a row lower'), ('passing', 'right foot swung through')],
    'jordan_rage': [('shut', 'seething, teeth clenched'), ('open', 'shouting, jolted a pixel')],
    'jordan_zap': [('wind-up', 'arm flung up, sparks gathering'), ('thrust', 'pointing, the energy bursts'),
                   ('hold', 'the zap line leaves the fingertip'), ('recover', 'arm dropping, smoking (held)'),
                   ('arms up', 'the disintegrate-the-rest beat')],
}
# where the zap line should leave his hand, in frame texels (facing right; mirror x for facing left)
ZAP_TIP = (jfs_zap.ZAP_TIP_BUILD[0] + B.ANCHOR_SHIFT, jfs_zap.ZAP_TIP_BUILD[1])
ZAP_ORB = (ZAP_TIP[0] + 3, ZAP_TIP[1])          # the hold's white-hot ball, just off the fingertip


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def _guard(path):
    if _under(path, os.path.join(B.ROOT, 'Assets')):
        raise SystemExit('refusing %s: nothing is shipped from the approval pass' % path)
    if not _under(path, HERE):
        raise SystemExit('refusing %s: outputs stay in art_source/jordan_finale_standing/' % path)
    return path


def approved_colours():
    im = Image.open(os.path.join(B.ROOT, 'Assets', 'Characters', 'Jordan', 'jordan_redesign_v2.png')).convert('RGBA')
    return {c for c in im.getdata() if c[3]}


def screen_offset(texel, facing_left=False):
    """A frame texel's centre relative to his node origin (his feet), in screen px at scale 3, as
    StoryActor places a 96x96 frame with feet (48, 95)."""
    x = (texel[0] + 0.5 - 48) * 3
    y = (texel[1] + 0.5 - 96) * 3
    return (-x if facing_left else x, y)


def check(mod, allowed):
    frames = mod.frames()
    problems, rows = [], []
    for i, (px, fx) in enumerate(frames):
        im = B.to_image(px)
        st = B.stats(im)
        cols = {c for c in im.getdata() if c[3]}
        a = B.audit(px, fx)
        low = max(y for (x, y) in px)
        body = {q: k for q, k in px.items() if q not in fx}
        alone = sum(1 for k in body.values() if k == 'k') / max(1, len(body))
        tag = '%s f%d' % (mod.NAME, i)
        if cols - allowed:
            problems.append('%s: colours outside the approved 40: %s' % (tag, sorted(cols - allowed)[:4]))
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        if a['gaps'] or a['lone'] or a['holes'] or a['keys']:
            problems.append('%s: gaps %s lone %s holes %s keys %s' % (tag, a['gaps'][:4], a['lone'][:4], a['holes'][:4],
                                                                  a['keys']))
        if low != 95:
            problems.append('%s: lowest drawn row %d, not 95' % (tag, low))
        rows.append((i, st, len(cols), alone, len(body), B.bbox(px)))
    strip = Image.new('RGBA', (96 * len(frames), 96), (0, 0, 0, 0))
    for i, (px, fx) in enumerate(frames):
        strip.alpha_composite(B.to_image(px), (96 * i, 0))
    return frames, strip, rows, problems


def write_sheet(name, im, folder):
    png = _guard(os.path.join(folder, name + '.png'))
    ase = _guard(os.path.join(folder, name + '.aseprite'))
    tmp = tempfile.mkdtemp(prefix='jfs_')
    tpng, tase = os.path.join(tmp, name + '.png'), os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    subprocess.run([B.V2B.ASEPRITE, '-b', tpng, '--save-as', tase], check=True, capture_output=True)
    os.replace(tpng, png)
    os.replace(tase, ase)
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([B.V2B.ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    return B.pixel_diff(Image.open(png), Image.open(back))


SHIP_DIR = os.path.join(B.ROOT, 'Assets', 'Characters', 'Jordan')


def _sha(path):
    import hashlib
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def ship(built):
    """The four sheets as NEW files in Assets/Characters/Jordan/."""
    targets = [(mod, os.path.join(SHIP_DIR, mod.NAME + ext)) for mod, _f, _s, _r in built for ext in ('.png', '.aseprite')]
    for mod, t in targets:
        if os.path.normcase(os.path.realpath(os.path.dirname(t))) != os.path.normcase(os.path.realpath(SHIP_DIR)):
            raise SystemExit('refusing %s: not in Assets/Characters/Jordan/' % t)
        if os.path.exists(t):
            raise SystemExit('refusing: %s already exists (the standing sheets ship as new files only)' % t)
    status = 0
    for mod, frames, strip, rows in built:
        tmp = tempfile.mkdtemp(prefix='jfs_ship_')
        tpng, tase = os.path.join(tmp, mod.NAME + '.png'), os.path.join(tmp, mod.NAME + '.aseprite')
        strip.save(tpng)
        subprocess.run([B.V2B.ASEPRITE, '-b', tpng, '--save-as', tase], check=True, capture_output=True)
        back = os.path.join(tmp, 'rt.png')
        subprocess.run([B.V2B.ASEPRITE, '-b', tase, '--save-as', back], check=True, capture_output=True)
        d = B.pixel_diff(Image.open(tpng), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (mod.NAME, d))
        png, ase = os.path.join(SHIP_DIR, mod.NAME + '.png'), os.path.join(SHIP_DIR, mod.NAME + '.aseprite')
        os.replace(tpng, png)
        os.replace(tase, ase)
        back2 = os.path.join(tmp, 'rt2.png')
        subprocess.run([B.V2B.ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
        d1 = B.pixel_diff(Image.open(png), strip)
        d2 = B.pixel_diff(Image.open(png), Image.open(back2))
        print('shipped %s  sha256 %s' % (png, _sha(png)))
        print('shipped %s  sha256 %s' % (ase, _sha(ase)))
        print('   landed PNG vs build: %s; landed .aseprite vs PNG: %s' % (d1 or 'identical', d2 or 'identical'))
        status |= 1 if (d1 or d2) else 0
    return status


def main(argv):
    if argv[:1] not in (['--check'], ['--write'], ['--ship']):
        print(__doc__)
        return 2
    allowed = approved_colours()
    assert len(allowed) == 40, len(allowed)
    built, problems = [], []
    for mod in MODULES:
        frames, strip, rows, pr = check(mod, allowed)
        built.append((mod, frames, strip, rows))
        problems += pr
    for mod, frames, strip, rows in built:
        print('%s.png  %dx%d, %d frames, times %s%s' % (mod.NAME, strip.width, strip.height, len(frames), mod.TIMES,
                                                       ', loops' if mod.LOOP else ', once'))
        for i, st, ncol, alone, n, bb in rows:
            print('   f%d  opaque %4d  colours %2d  black %5.2f%% (him alone %5.2f%%)  rows %d..%d  x %d..%d'
                  % (i, st['opaque'], ncol, 100 * st['black'], 100 * alone, bb[1], bb[3], bb[0], bb[2]))
        sheet = B.stats(strip)
        print('   sheet: colours %d, black %.2f%%' % (sheet['colours'], 100 * sheet['black']))
    print('zap tip (fingertip) texel %s, the hold\'s orb %s; from his feet at scale 3: facing right %s, facing left %s'
          % (ZAP_TIP, ZAP_ORB, screen_offset(ZAP_ORB), screen_offset(ZAP_ORB, True)))
    print('problems:', problems or 'none')
    if problems:
        return 1
    if argv[0] == '--ship':
        return ship(built)
    if argv[0] != '--write':
        return 0
    status = 0
    for mod, frames, strip, rows in built:
        d = write_sheet(mod.NAME, strip, HERE)
        print('wrote %s.png + .aseprite, round trip: %s' % (mod.NAME, d or 'identical'))
        status |= 1 if d else 0
    prev = _guard(os.path.join(HERE, 'preview'))
    os.makedirs(prev, exist_ok=True)
    sheets = [(mod, frames, LABELS[mod.NAME]) for mod, frames, strip, rows in built]
    PV.contact(sheets).save(_guard(os.path.join(prev, 'contact_4x.png')))
    for mod, frames, strip, rows in built:
        bg = PV.ARENA_MAT if mod.NAME in ('jordan_getup', 'jordan_walk_away') else PV.ROOM_FLOOR
        if mod.NAME == 'jordan_zap':
            PV.save_gif(_guard(os.path.join(prev, 'jordan_zap.gif')), PV.gif_frames(frames[:4], bg=bg), mod.TIMES[:4], loop=False)
            PV.save_gif(_guard(os.path.join(prev, 'jordan_zap_arms_up.gif')), PV.gif_frames(frames[4:], bg=bg), [1.0])
        else:
            PV.save_gif(_guard(os.path.join(prev, mod.NAME + '.gif')), PV.gif_frames(frames, bg=bg), mod.TIMES, loop=mod.LOOP)
    walk_frames = [f for m, f, s_, r in built if m is jfs_walk][0]
    ims, durs = PV.walk_moving(walk_frames, jfs_walk.TIMES)
    PV.save_gif(_guard(os.path.join(prev, 'jordan_walk_away_moving.gif')), ims, durs)
    rage = B.to_image(jfs_rage.frames()[1][0])
    PV.room_mock(rage, title='jordan_rage f1 at game scale in the room: at JORDAN_STAND_POINT (1260,700), mirrored to '
                             'face the talk spot; Carter, Josh, Liam, Matt and the player on their marks').save(
        _guard(os.path.join(prev, 'room_mock_rage.png')))
    zap = B.to_image(jfs_zap.frames()[2][0])
    ox, oy = screen_offset(ZAP_ORB, True)
    tip = (PV.LAYOUT['STAND'][0] + ox, PV.LAYOUT['STAND'][1] + oy)
    PV.room_mock(zap, zap_tip=tip, title='jordan_zap f2 (hold) facing Liam, the zap line drawn from the reported '
                                         'fingertip').save(_guard(os.path.join(prev, 'room_mock_zap.png')))
    print('previews written to', prev)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
