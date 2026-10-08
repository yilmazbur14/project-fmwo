"""Ship Josh's portals, TAKE B (the card-gate), as NEW files only. User approval 2026-09-28 ("defaults are
fine"): take B, the cleaned spike blade, the smear, the floor-footprint reading of the 2-texel rim,
the collar reading, the tint wash kept, the card backs and the spade sigil kept.

    python jp_portals_ship.py            # print this and exit; writes nothing
    python jp_portals_ship.py --stage    # rebuild, audit and stage in a temp folder; nothing in the project
    python jp_portals_ship.py --ship     # stage and verify, then create the files below

What ships, into Assets/Characters/Jordan/Portals/ (every PNG with its .aseprite beside it):
  portal_<kind>_<sequence>_<layer>   36 strips: spike (open, burst, hold, suck, close), body (open, hold,
                                     close) and sword (open, plunge, loop, close), each back / front / glow
  eric_sword_spike_up                eric_thrown_sword_v2 f6 without its white spin arcs (the spike's blade)
  portal_spike_smear                 the spike's smear, 3 frames (rise, full, retract), drawn behind the blade

Safety: every file is created EXCLUSIVELY (open 'x'); the run refuses before writing anything if any
target (or the record) exists. An audit hook allows writes only to those exact paths (plus the new
Portals folder and this folder's shipped.json) and refuses every other write under Assets/, Scripts/,
art_source/jordan_puppets/ or project.godot, and any process but Aseprite (never with an argument under
a protected path). Before anything is written: the rig must rebuild every approved take-B PNG pixel for
pixel; no strip may carry semi-alpha or energy outside the opening + RIM; the openings must be exactly
the contract's; every strip must be the contract's size; every .aseprite must round-trip to its PNG and
carry the contract's frame times and its tag. After: every shipped file must be byte-identical to its
take-B output, and project.godot's md5 unchanged.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jp_portals as P  # noqa: E402
import jg_base as B  # noqa: E402
sys.path.insert(0, os.path.dirname(P.PUP))            # art_source, for imgdiff
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = P.ROOT
TAKE = 'B'
SRC = os.path.join(HERE, 'take' + TAKE)
DEST = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'Portals')
RECORD = os.path.join(HERE, 'shipped.json')
PROJECT = os.path.join(ROOT, 'project.godot')
PROJECT_MD5 = 'a5de9bf23891bbb1cccedea52484f42e'


def _nc(p):
    return os.path.normcase(os.path.realpath(p))


def _sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def _md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def manifest():
    """[(name, source folder, rebuild(), (frames, frame times, tag) or None)] for every pair that ships."""
    out = []
    for kind in P.SPEC:
        for seq, tt in P.SEQS[kind]:
            for layer in ('back', 'front', 'glow'):
                out.append(('portal_%s_%s_%s' % (kind, seq, layer), SRC,
                            (lambda kind=kind, seq=seq, layer=layer: P.seq_images(TAKE, kind, seq)[layer]),
                            (kind, tt, '%s_%s' % (kind, seq))))
    out.append(('eric_sword_spike_up', HERE, lambda: P.spike_blade()[0], None))
    out.append(('portal_spike_smear', HERE, P.smear_frames, None))
    return out


def targets():
    t = []
    for name, folder, rebuild, seq in manifest():
        t.append(os.path.join(DEST, name + '.png'))
        t.append(os.path.join(DEST, name + '.aseprite'))
    return t


# ------------------------------------------------------------------ the guard

def install_guard(allowed_files, allowed_dirs):
    forbidden = [_nc(p) for p in (os.path.join(ROOT, 'Assets'), os.path.join(ROOT, 'Scripts'),
                                   os.path.join(ROOT, 'art_source', 'jordan_puppets'), PROJECT)]
    ok_files = {_nc(p) for p in allowed_files}
    ok_dirs = {_nc(p) for p in allowed_dirs}
    ase = _nc(B.ASEPRITE)

    def protected(p):
        try:
            rp = _nc(os.fspath(p))
        except (TypeError, ValueError):
            return False
        return any(rp == b or rp.startswith(b + os.sep) for b in forbidden)

    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & write_flags)
            if not writing or not protected(path):
                return
            if _nc(path) in ok_files and mode is not None and 'x' in str(mode):
                return                                   # an exclusive create of a manifest file
            raise PermissionError('guard: refusing to write %s' % path)
        elif event == 'os.mkdir':
            p = args[0]
            if protected(p) and _nc(p) not in ok_dirs:
                raise PermissionError('guard: refusing mkdir %s' % p)
        elif event in ('os.remove', 'os.unlink', 'os.rmdir', 'os.rename', 'os.replace', 'shutil.copyfile',
                       'shutil.copytree', 'shutil.move', 'shutil.rmtree', 'os.truncate'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and protected(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event == 'subprocess.Popen':
            argv = args[1]
            line = argv if isinstance(argv, str) else subprocess.list2cmdline([os.fspath(a) for a in argv])
            if line.startswith('"'):
                first, rest = line[1:line.index('"', 1)], line[line.index('"', 1) + 1:]
            else:
                first, _, rest = line.partition(' ')
            if _nc(first) != ase:
                raise PermissionError('guard: refusing to launch %s' % first)
            if any(b in os.path.normcase(rest) for b in forbidden):
                raise PermissionError('guard: refusing an Aseprite argument under a protected path')

    sys.addaudithook(hook)


# ------------------------------------------------------------------ staging

def stage():
    """Rebuild, audit, stage and verify. Returns (ok, lines, stage dir, {target: (staged, source)})."""
    ok, lines = True, []
    try:
        audit = P.audit(TAKE)
        lines.append('audit (take %s): passed - no semi-alpha, nothing outside the opening + %d-texel rim; openings %s'
                     % (TAKE, P.RIM, ', '.join('%s %s' % (k, v['opening_box']) for k, v in audit.items())))
    except SystemExit as e:
        ok = False
        lines.append('audit FAILED: %s' % e)
    tmp = tempfile.mkdtemp(prefix='jpup_portals_ship_')
    staged = {}
    for name, folder, rebuild, seq in manifest():
        png, ase = os.path.join(folder, name + '.png'), os.path.join(folder, name + '.aseprite')
        if not (os.path.isfile(png) and os.path.isfile(ase)):
            ok = False
            lines.append('%s: the approved pair is missing in %s' % (name, folder))
            continue
        d = pixel_diff(rebuild(), Image.open(png))
        if d:
            ok = False
            lines.append('%s: the rig no longer builds the approved PNG: %s' % (name, d))
        for src, ext in ((png, '.png'), (ase, '.aseprite')):
            dst = os.path.join(tmp, name + ext)
            shutil.copyfile(src, dst)
            staged[os.path.join(DEST, name + ext)] = (dst, src)
        im = Image.open(os.path.join(tmp, name + '.png')).convert('RGBA')
        semi = sum(1 for a in im.getchannel('A').getdata() if 0 < a < 255)
        if semi:
            ok = False
            lines.append('%s: %d semi-alpha texels' % (name, semi))
        if seq:
            kind, tt, tag = seq
            want = (P.SPEC[kind]['frame'][0] * len(tt), P.SPEC[kind]['frame'][1])
            if im.size != want:
                ok = False
                lines.append('%s: %s, the contract says %s' % (name, im.size, want))
        back = os.path.join(tmp, name + '_rt.png')
        data = os.path.join(tmp, name + '_rt.json')
        subprocess.run([B.ASEPRITE, '-b', os.path.join(tmp, name + '.aseprite'), '--list-tags', '--data', data,
                        '--format', 'json-array', '--sheet', back, '--sheet-type', 'horizontal'],
                       check=True, capture_output=True)
        d2 = pixel_diff(Image.open(os.path.join(tmp, name + '.png')), Image.open(back))
        if d2:
            ok = False
            lines.append('%s: the .aseprite does not round-trip: %s' % (name, d2))
        if seq:
            with open(data) as f:
                meta = json.load(f)
            durs = [fr['duration'] for fr in meta['frames']]
            tags = [(t_['name'], t_['from'], t_['to']) for t_ in meta['meta']['frameTags']]
            if durs != [int(round(t * 1000)) for t in tt] or tags != [(tag, 0, len(tt) - 1)]:
                ok = False
                lines.append('%s: frame times %s / tags %s differ from the contract' % (name, durs, tags))
    return ok, lines, tmp, staged


def ship(staged):
    exist = [t for t in staged if os.path.exists(t)] + ([RECORD] if os.path.exists(RECORD) else [])
    if exist:
        raise SystemExit('refusing: these already exist, nothing written:\n  ' + '\n  '.join(exist))
    if not os.path.isdir(DEST):
        os.mkdir(DEST)
    record = {}
    for target in sorted(staged):
        st, src = staged[target]
        with open(st, 'rb') as f:
            data = f.read()
        with open(target, 'xb') as f:                   # exclusive: never overwrites
            f.write(data)
        h = _sha(target)
        if h != _sha(src):
            raise SystemExit('%s: not byte-identical to %s' % (target, src))
        record[os.path.relpath(target, ROOT).replace('\\', '/')] = h
    with open(RECORD, 'x') as f:
        json.dump(record, f, indent=1, sort_keys=True)
    return record


def main(argv):
    if not argv or argv[0] not in ('--stage', '--ship'):
        print(__doc__)
        return 2
    before = _md5(PROJECT)
    if before != PROJECT_MD5:
        raise SystemExit('refusing: project.godot md5 is %s, expected %s (nothing written)' % (before, PROJECT_MD5))
    allowed = targets()
    for p in allowed:
        if _nc(os.path.dirname(p)) != _nc(DEST):
            raise SystemExit('refusing: %s is outside the ship folder' % p)
    install_guard(allowed if argv[0] == '--ship' else [], [DEST] if argv[0] == '--ship' else [])
    ok, lines, tmp, staged = stage()
    for ln in lines:
        print(ln)
    print('staged %d files in %s' % (len(staged), tmp))
    if not ok:
        print('staging FAILED: nothing shipped')
        return 1
    if argv[0] == '--ship':
        record = ship(staged)
        # after: every shipped file equals its take-B output, byte for byte, and project.godot is untouched
        for target, (st, src) in staged.items():
            if _sha(target) != _sha(src):
                raise SystemExit('%s: differs from %s after the ship' % (target, src))
        after = _md5(PROJECT)
        print('shipped %d files into %s; hashes in %s' % (len(record), os.path.relpath(DEST, ROOT),
                                                          os.path.relpath(RECORD, ROOT)))
        print('byte-identical to the take-%s outputs: %d/%d' % (TAKE, len(record), len(staged)))
        print('project.godot md5 before %s after %s (%s)' % (before, after, 'unchanged' if after == before
                                                               else 'CHANGED'))
        for rel, h in sorted(record.items()):
            print('  %-70s %s' % (rel, h))
    else:
        for target, (st, src) in sorted(staged.items()):
            print('  %-70s %s' % (os.path.relpath(target, ROOT).replace('\\', '/'), _sha(st)[:16]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
