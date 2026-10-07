"""Ship the approved puppet-master set (user approval 2026-09-28: BLUE strings on the puppets'
backs only, the 1.3x hands, the claw heights as drawn) into the game, as NEW files only.

A bare run writes nothing:

    python jp_ship.py              # print this and exit
    python jp_ship.py --stage      # stage and audit everything in a temp folder; write nothing to the project
    python jp_ship.py --ship       # stage, audit, then create the game files listed in manifest()

What ships (every PNG with its .aseprite beside it):
  Assets/Characters/Jordan/God/          the 7 anims (control, summon both/left/right, yank right/left, hit)
                                         and each one's _aura strip
  Assets/Characters/Jordan/God/Rift/     the standard and wide rift, summon and despawn, back/front/glow
  Assets/Characters/Jordan/God/Strings/  the blue string tile and the blue fingertip knot
  Scripts/JordanGodTips.gd               the fingertip, tension, timing and rift data (generated)

Safety: every file is created EXCLUSIVELY (open 'x'); nothing that exists is ever overwritten, and the
run refuses before writing anything if any target exists. An audit hook allows writes only to those
exact paths (plus the two new folders and this folder's shipped.json) and refuses every other write
under Assets/, Scripts/, art_source/jordan_god/ or project.godot, and any process but Aseprite and a
Godot parse check that runs on a scratch project in the temp folder (never on this project, so nothing
is imported). The staged PNGs must be pixel-identical to the approved files in approval/ and to a
fresh build of the rig; each .aseprite must round-trip to its PNG; the GDScript must parse and load.
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
import jp_anims as A  # noqa: E402
import jp_export as X  # noqa: E402
import jp_rift as RF  # noqa: E402
import jp_puppets as PP  # noqa: E402
import jp_scene as SC  # noqa: E402
import jg_base as B  # noqa: E402
sys.path.insert(0, os.path.dirname(HERE))
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = B.ROOT
APPROVAL = os.path.join(HERE, 'approval')
RECORD = os.path.join(HERE, 'shipped.json')
GODOT = os.environ.get('GODOT', r'C:\Users\theyi\Downloads\Godot_v4.6.3-stable_win64.exe\Godot.exe.exe')
GOD_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'God')
RIFT_DIR = os.path.join(GOD_DIR, 'Rift')
STR_DIR = os.path.join(GOD_DIR, 'Strings')
TIPS_GD = os.path.join(ROOT, 'Scripts', 'JordanGodTips.gd')
RES = 'res://Assets/Characters/Jordan/God/'


def _nc(p):
    return os.path.normcase(os.path.realpath(p))


def _under(p, root):
    a, b = _nc(p), _nc(root)
    return a == b or a.startswith(b + os.sep)


def anim_key(key):
    return 'hit' if key == 'hit' else 'puppeteer_' + key


def manifest():
    """[(sprite name, target folder)] for every PNG + .aseprite pair that ships."""
    out = []
    for key, stem, n, times, loop, fn, phase in A.anims():
        out.append((stem, GOD_DIR))
        out.append((stem + '_aura', GOD_DIR))
    for name, seq, prof in X.RIFTS:
        for layer in ('back', 'front', 'glow'):
            out.append(('%s_%s' % (name, layer), RIFT_DIR))
    out.append(('puppet_string_blue', STR_DIR))
    out.append(('puppet_string_knot_blue', STR_DIR))
    return out


def targets():
    t = []
    for name, folder in manifest():
        t.append(os.path.join(folder, name + '.png'))
        t.append(os.path.join(folder, name + '.aseprite'))
    t.append(TIPS_GD)
    return t


# ------------------------------------------------------------------ the guard

def install_guard(allowed_files, allowed_dirs):
    forbidden = [_nc(p) for p in (os.path.join(ROOT, 'Assets'), os.path.join(ROOT, 'Scripts'),
                                   os.path.join(ROOT, 'art_source', 'jordan_god'), os.path.join(ROOT, 'project.godot'))]
    ok_files = {_nc(p) for p in allowed_files}
    ok_dirs = {_nc(p) for p in allowed_dirs}
    root_nc = os.path.normcase(os.path.realpath(ROOT))

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
            exe, argv = args[0], args[1]
            line = argv if isinstance(argv, str) else subprocess.list2cmdline([os.fspath(a) for a in argv])
            if line.startswith('"'):
                first, rest = line[1:line.index('"', 1)], line[line.index('"', 1) + 1:]
            else:
                first, _, rest = line.partition(' ')
            if _nc(first) == _nc(X.ASE):
                if any(b in os.path.normcase(rest) for b in forbidden):
                    raise PermissionError('guard: refusing an Aseprite argument under a protected path')
                return
            if _nc(first) == _nc(GODOT):
                # the parse check: only ever on the scratch project, never on this one
                if root_nc in os.path.normcase(rest):
                    raise PermissionError('guard: refusing to run Godot on the project')
                return
            raise PermissionError('guard: refusing to launch %s' % first)

    sys.addaudithook(hook)


# ------------------------------------------------------------------ the GDScript data

def _v(p):
    return 'Vector2(%d, %d)' % (p[0], p[1])


def _f(x):
    s = ('%.3f' % x).rstrip('0')
    return s + '0' if s.endswith('.') else s


def tips_gd(god):
    anims = A.anims()
    L = []
    L.append('# Generated by art_source/jordan_puppeteer/jp_ship.py from the approved puppeteer rig (user approval')
    L.append('# 2026-09-28). Do not edit: change the rig and re-run it.')
    L.append('#')
    L.append('# Demon-god Jordan\'s puppeteer sheets (Assets/Characters/Jordan/God/jordan_god_puppeteer_*.png and')
    L.append('# jordan_god_hit.png, each with an _aura strip to add over it): every frame is 320x224, anchor texel')
    L.append('# (160, 223), placed as the hover is (the anchor texel\'s top-left corner on GOD_POINT, scale 3).')
    L.append('#')
    L.append('# TIPS[anim][frame] = {&"left": [5 x Vector2], &"right": [5 x Vector2]}: the claw-point texel each string')
    L.append('#   hangs from, in frame texels (x right, y down, the frame\'s bob included), in the order index, middle,')
    L.append('#   ring, little, thumb. &"left" is the screen-left hand (his right). A string starts at the texel\'s')
    L.append('#   centre: on screen, GOD_POINT + (tip + Vector2(0.5, 0.5) - Vector2(160, 223)) * 3.')
    L.append('# TENSION[anim][frame] = {&"left": float, &"right": float}: 0 slack .. 1 taut; a working hand is 0.7.')
    L.append('# TIMES[anim]: seconds per frame. NEXT[anim]: what plays after it, from frame NEXT_FRAME[anim] (the yanks')
    L.append('#   ride hover poses 0-3, so the control loop picks up on its frame 4).')
    L.append('# PAIRS[puppet]: the two TIPS indices its two strings leave from; both end on its back hook.')
    L.append('# RIFT[size]: the rift overlays in Rift/. Per frame, back draws behind the puppet, front in front of it,')
    L.append('#   glow is added over it; the anchor texel goes on the puppet\'s feet point, and the puppet is clipped at')
    L.append('#   the anchor row while it is in the rift. A loop is [first, last]: those frames repeat seamlessly while')
    L.append('#   a puppet is still rising or sinking.')
    L.append('# The strings (Strings/): puppet_string_blue.png is a 16x3 Line2D tile (glow, core, glow; one hot bead')
    L.append('#   for a pulse scrolled up the string), puppet_string_knot_blue.png a 5x5 glow to ADD on each fingertip.')
    L.append('#   Colours: core #66C6EC, glow #17385A (added), knot #2B6C99 (added), hot #D2F6FF.')
    L.append('# Every key in this file is a StringName.')
    L.append('extends RefCounted')
    L.append('')
    L.append('const TIPS := {')
    for key, stem, n, times, loop, fn, phase in anims:
        L.append('\t&"%s": [' % anim_key(key))
        for f in god[key]:
            left = ', '.join(_v(f['tips']['left'][d]) for d in SC.DIGIT_ORDER)
            right = ', '.join(_v(f['tips']['right'][d]) for d in SC.DIGIT_ORDER)
            L.append('\t\t{&"left": [%s],' % left)
            L.append('\t\t\t&"right": [%s]},' % right)
        L.append('\t],')
    L.append('}')
    L.append('')
    L.append('const TENSION := {')
    for key, stem, n, times, loop, fn, phase in anims:
        L.append('\t&"%s": [' % anim_key(key))
        frames = ['{&"left": %s, &"right": %s}' % (_f(f['tension']['left']), _f(f['tension']['right']))
                  for f in god[key]]
        for i in range(0, len(frames), 3):
            L.append('\t\t' + ', '.join(frames[i:i + 3]) + ',')
        L.append('\t],')
    L.append('}')
    L.append('')
    L.append('const TIMES := {')
    for key, stem, n, times, loop, fn, phase in anims:
        L.append('\t&"%s": [%s],' % (anim_key(key), ', '.join(_f(t) for t in times)))
    L.append('}')
    L.append('')
    nxt = {k: 'puppeteer_control' for k in ('control', 'summon_both', 'summon_left', 'summon_right', 'yank_right',
                                            'yank_left', 'hit')}
    nxt_frame = {k: 0 for k in nxt}
    nxt_frame['yank_right'] = nxt_frame['yank_left'] = A.YANK_BODY[-1] + 1
    L.append('const NEXT := {')
    for key, stem, n, times, loop, fn, phase in anims:
        L.append('\t&"%s": &"%s",' % (anim_key(key), nxt[key]))
    L.append('}')
    L.append('')
    L.append('const NEXT_FRAME := {')
    for key, stem, n, times, loop, fn, phase in anims:
        L.append('\t&"%s": %d,' % (anim_key(key), nxt_frame[key]))
    L.append('}')
    L.append('')
    L.append('const PAIRS := {&"greyson": [0, 1], &"matt": [2, 3], &"burak": [2, 3], &"danny": [2, 3]}')
    L.append('')
    L.append('const RIFT := {')
    for size, prof, pups in (('standard', RF.STD, ('greyson', 'matt', 'burak')), ('wide', RF.WIDE, ('danny',))):
        pre = 'puppet_rift_' if prof is RF.STD else 'puppet_rift_wide_'
        L.append('\t&"%s": {' % size)
        L.append('\t\t&"size": Vector2(%d, %d), &"anchor": Vector2(%d, %d),' % (prof.W, prof.H, prof.ANCHOR[0],
                                                                               prof.ANCHOR[1]))
        L.append('\t\t&"summon_times": [%s], &"summon_loop": [%d, %d],' % (
            ', '.join(_f(t) for t in RF.SUMMON_TIMES), RF.SUMMON_LOOP[0], RF.SUMMON_LOOP[1]))
        L.append('\t\t&"despawn_times": [%s], &"despawn_loop": [%d, %d],' % (
            ', '.join(_f(t) for t in RF.DESPAWN_TIMES), RF.DESPAWN_LOOP[0], RF.DESPAWN_LOOP[1]))
        L.append('\t\t&"puppets": [%s],' % ', '.join('&"%s"' % p for p in pups))
        L.append('\t\t&"sheets": {')
        for seq in ('summon', 'despawn'):
            for layer in ('back', 'front', 'glow'):
                L.append('\t\t\t&"%s_%s": "%sRift/%s%s_%s.png",' % (seq, layer, RES, pre, seq, layer))
        L.append('\t\t},')
        L.append('\t},')
    L.append('}')
    return '\n'.join(L) + '\n'


CHECK_GD = r'''extends SceneTree


func _init() -> void:
	var T = load("res://JordanGodTips.gd")
	var points := 0
	var frames := 0
	for anim in T.TIPS:
		for f in T.TIPS[anim]:
			frames += 1
			points += f[&"left"].size() + f[&"right"].size()
	print("CHECK anims=%d frames=%d points=%d" % [T.TIPS.size(), frames, points])
	print("CHECK tension=%d times=%d next=%d next_frame=%d pairs=%d rift=%d" % [T.TENSION.size(), T.TIMES.size(),
		T.NEXT.size(), T.NEXT_FRAME.size(), T.PAIRS.size(), T.RIFT.size()])
	print("CHECK hit0.left0=%s control0.right4=%s wide.size=%s std.loop=%s" % [T.TIPS[&"hit"][0][&"left"][0],
		T.TIPS[&"puppeteer_control"][0][&"right"][4], T.RIFT[&"wide"][&"size"], T.RIFT[&"standard"][&"summon_loop"]])
	quit()
'''


def godot_check(stage, text):
    proj = os.path.join(stage, 'godot_check')
    os.makedirs(proj)
    with open(os.path.join(proj, 'project.godot'), 'w') as f:
        f.write('config_version=5\n\n[application]\n\nconfig/name="tips_check"\n')
    with open(os.path.join(proj, 'JordanGodTips.gd'), 'w', newline='\n') as f:
        f.write(text)
    with open(os.path.join(proj, 'check.gd'), 'w', newline='\n') as f:
        f.write(CHECK_GD)
    r = subprocess.run([GODOT, '--headless', '--path', proj, '--script', 'res://check.gd'], capture_output=True,
                       text=True, timeout=120)
    out = (r.stdout or '') + (r.stderr or '')
    checks = [ln for ln in out.splitlines() if ln.startswith('CHECK')]
    errors = [ln for ln in out.splitlines() if 'ERROR' in ln or 'Parse Error' in ln or 'SCRIPT ERROR' in ln]
    return r.returncode, checks, errors


# ------------------------------------------------------------------ staging

def _sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def stage():
    """Build, audit, stage. Returns (ok, lines, stage dir, {target: staged file})."""
    lines = []
    god, ims = X.build_all()
    ok, audit_lines = X.audit(god, ims)
    lines += ['audit: ' + ('passed' if ok else 'FAILED')] + [ln for ln in audit_lines if 'FAIL' in ln]
    tmp = tempfile.mkdtemp(prefix='jpup_ship_')
    staged = {}
    for name, folder in manifest():
        src_png = os.path.join(APPROVAL, name + '.png')
        src_ase = os.path.join(APPROVAL, name + '.aseprite')
        d1 = pixel_diff(ims[name], Image.open(src_png))
        if d1:
            ok = False
            lines.append('%s: the rig no longer builds the approved PNG: %s' % (name, d1))
        for src, ext in ((src_png, '.png'), (src_ase, '.aseprite')):
            dst = os.path.join(tmp, name + ext)
            shutil.copyfile(src, dst)
            staged[os.path.join(folder, name + ext)] = dst
        back = os.path.join(tmp, name + '_rt.png')
        X.aseprite(os.path.join(tmp, name + '.aseprite'), '--sheet', back, '--sheet-type', 'horizontal')
        d2 = pixel_diff(Image.open(os.path.join(tmp, name + '.png')), Image.open(back))
        if d2:
            ok = False
            lines.append('%s: the .aseprite does not round-trip: %s' % (name, d2))
        im = Image.open(os.path.join(tmp, name + '.png'))
        st = B.stats(im.convert('RGBA'))
        if st['semi']:
            ok = False
            lines.append('%s: semi-alpha texels: %d' % (name, st['semi']))
    text = tips_gd(god)
    # the table must say exactly what the approved JSON says
    with open(os.path.join(APPROVAL, 'jordan_puppeteer_fingertips.json')) as f:
        approved = json.load(f)
    for key, stem, n, times, loop, fn, phase in A.anims():
        jk = 'puppeteer_' + key if key != 'hit' else 'jordan_god_hit'
        want = approved['anims'][jk]['tips']
        got = [{s: [list(god[key][i]['tips'][s][d]) for d in SC.DIGIT_ORDER] for s in ('left', 'right')}
               for i in range(n)]
        if want != got:
            ok = False
            lines.append('%s: the fingertips differ from the approved table' % key)
    gd = os.path.join(tmp, 'JordanGodTips.gd')
    with open(gd, 'w', newline='\n') as f:
        f.write(text)
    staged[TIPS_GD] = gd
    code, checks, errors = godot_check(tmp, text)
    lines += ['godot parse check (scratch project): exit %d' % code] + checks + errors
    if code != 0 or errors or len(checks) != 3:
        ok = False
    return ok, lines, tmp, staged


def ship(staged):
    exist = [p for p in staged if os.path.exists(p)]
    if exist:
        raise SystemExit('refusing: these already exist, nothing written:\n  ' + '\n  '.join(exist))
    for d in (RIFT_DIR, STR_DIR):
        if not os.path.isdir(d):
            os.mkdir(d)
    record = {}
    done = []
    for target, src in staged.items():
        with open(src, 'rb') as f:
            data = f.read()
        with open(target, 'xb') as f:            # exclusive: never overwrites
            f.write(data)
        h = _sha(target)
        if h != hashlib.sha256(data).hexdigest():
            raise SystemExit('%s: written bytes differ from the staged file' % target)
        rel = os.path.relpath(target, ROOT).replace('\\', '/')
        record[rel] = h
        done.append(rel)
    with open(RECORD, 'x') as f:
        json.dump(record, f, indent=1, sort_keys=True)
    return done, record


def main(argv):
    if not argv or argv[0] not in ('--stage', '--ship'):
        print(__doc__)
        return 2
    allowed = targets() + [RECORD]
    for p in allowed:
        if not (_under(p, os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'God')) or _nc(p) == _nc(TIPS_GD)
                or _nc(p) == _nc(RECORD)):
            raise SystemExit('refusing: %s is outside the ship folders' % p)
    install_guard(allowed if argv[0] == '--ship' else [], [RIFT_DIR, STR_DIR] if argv[0] == '--ship' else [])
    ok, lines, tmp, staged = stage()
    for ln in lines:
        print(ln)
    print('staged %d files in %s' % (len(staged), tmp))
    for target, src in staged.items():
        print('  %-72s %s' % (os.path.relpath(target, ROOT).replace('\\', '/'), _sha(src)[:16]))
    if not ok:
        print('staging FAILED: nothing shipped')
        return 1
    if argv[0] == '--ship':
        done, record = ship(staged)
        print('shipped %d files; hashes recorded in %s' % (len(done), os.path.relpath(RECORD, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
