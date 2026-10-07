"""Write the puppet-master approval pass into art_source/jordan_puppeteer/approval/ and nowhere
else. Nothing here ships: it waits for the user's approval.

A bare run writes nothing:

    python jp_export.py            # print this and exit
    python jp_export.py --check    # build and audit everything; write nothing
    python jp_export.py --write    # write the approval files (PNG + .aseprite each, GIFs, JSON, mocks)

Guards: the output folder must be approval/ beside this script (checked by realpath, so an 8.3
short name cannot slip past), and an audit hook refuses any write, rename, delete or mkdir under
Assets/, art_source/jordan_god/ or project.godot for the whole run, and any process but Aseprite.
Each .aseprite is built by the Aseprite CLI (frames, per-frame durations and a tag), exported back
as a horizontal sheet and compared pixel for pixel with its PNG before either file is kept.
Nothing is written unless every god frame passes the audit (no keyline gaps, stray specks or
pinholes on the body, no semi-alpha anywhere, his lowest texel on row 223 minus the frame's bob,
and every claw point above the rifts, with the working ones well above the puppets' hooks).
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jp_rig as R  # noqa: E402
import jp_anims as A  # noqa: E402
import jp_rift as RF  # noqa: E402
import jp_scene as SC  # noqa: E402
import jp_strings as S  # noqa: E402
import jp_puppets as PP  # noqa: E402
import jg_base as B  # noqa: E402
import jg_god as G  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_runes as RU  # noqa: E402
sys.path.insert(0, os.path.dirname(HERE))
from imgdiff import pixel_diff  # noqa: E402
from jg_lord_pal import PAL_A2  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = B.ROOT
OUT = os.path.join(HERE, 'approval')
ASE = B.ASEPRITE

# the plan's back hooks sit on screen y 220-300 with him at (960, 600): frame rows 96-123. The rifts
# open on the puppets' feet, y 416-440: frame rows 161-169.
HOOK_ROW_MIN = 96
RIFT_ROW_MIN = 161
WORKING_ROW_MAX = 70          # a working claw point (control, yank, hit, the summon's high frames)


def _nc(p):
    return os.path.normcase(os.path.realpath(p))


def _under(path, root):
    p, r = _nc(path), _nc(root)
    return p == r or p.startswith(r + os.sep)


FORBIDDEN = [os.path.join(ROOT, 'Assets'), os.path.join(ROOT, 'art_source', 'jordan_god'),
             os.path.join(ROOT, 'project.godot')]


def install_guard():
    bad = [_nc(p) for p in FORBIDDEN]

    def hit(p):
        try:
            rp = _nc(os.fspath(p))
        except (TypeError, ValueError):
            return False
        return any(rp == b or rp.startswith(b + os.sep) for b in bad)

    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & write_flags)
            if writing and hit(path):
                raise PermissionError('guard: refusing to write %s' % path)
        elif event in ('os.remove', 'os.unlink', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.replace',
                       'shutil.copyfile', 'shutil.copytree', 'shutil.move', 'shutil.rmtree', 'os.truncate'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and hit(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event == 'subprocess.Popen':
            exe, argv = args[0], args[1]
            if isinstance(argv, (list, tuple)):
                first, rest = os.fspath(argv[0]), [os.fspath(a) for a in argv[1:]]
                line = ' '.join(rest)
            else:
                # Windows hands the hook one command line: "C:\\...\\Aseprite.exe" -b ...
                line = os.fsdecode(argv)
                if line.startswith('"'):
                    first = line[1:line.index('"', 1)]
                    line = line[line.index('"', 1) + 1:]
                else:
                    first, _, line = line.partition(' ')
            if exe is not None and _nc(os.fsdecode(exe)) != _nc(ASE):
                raise PermissionError('guard: refusing to launch %s' % exe)
            if _nc(first) != _nc(ASE):
                raise PermissionError('guard: refusing to launch %s' % first)
            low = os.path.normcase(line)
            for b in bad:
                if b in low:
                    raise PermissionError('guard: refusing an Aseprite argument under a protected path: %s' % b)

    sys.addaudithook(hook)


# ------------------------------------------------------------------ build

ANIMS = A.anims()      # (key, stem, n, times, loop, frame_fn, aura_phase_fn)
HIGH_POSES = {'ready', 'top', 'hang', 'settle', 'slack', 'pull', 'hold', 'return'}


def god_frames():
    out = {}
    for key, stem, n, times, loop, fn, phase in ANIMS:
        frames = []
        for i in range(n):
            px, tips, ten, fx = fn(i)
            frames.append({'px': px, 'tips': tips, 'tension': ten, 'fx': fx, 'aura': A.aura_px(px, phase(i)),
                           'bob': bob_of(key, i), 'pose': pose_of(key, i)})
        out[key] = frames
    return out


def bob_of(key, i):
    if key == 'control':
        return G.BOB[i]
    if key.startswith('summon'):
        return A.SUMMON_BOB[i]
    if key.startswith('yank'):
        return G.BOB[A.YANK_BODY[i]]
    return A.HIT_BOB[i]


def pose_of(key, i):
    if key == 'control':
        return 'work %d' % i
    if key.startswith('summon'):
        return A.SUMMON_ARM[i][0]
    if key.startswith('yank'):
        return A.YANK_ARM[i][0]
    return ('jolt', 'recoil')[i]


def strip(frames, key, pal, w, h):
    im = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.alpha_composite(B.image(f[key], w, h, pal), (i * w, 0))
    return im


RIFTS = [('puppet_rift_%s' % seq, seq, 'std') for seq in ('summon', 'despawn')] + \
        [('puppet_rift_wide_%s' % seq, seq, 'wide') for seq in ('summon', 'despawn')]


def build_all():
    god = god_frames()
    ims = {}
    for key, stem, n, times, loop, fn, phase in ANIMS:
        ims[stem] = strip(god[key], 'px', PAL_A2, R.W, R.H)
        ims[stem + '_aura'] = strip(god[key], 'aura', G.AURA, G.AURA_W, G.AURA_H)
    for name, seq, prof in RIFTS:
        trio = RF.images(RF.SEQS[seq][0](), RF.PROFILES[prof])
        for layer, im in zip(('back', 'front', 'glow'), trio):
            ims['%s_%s' % (name, layer)] = im
    for take in ('red', 'blue'):
        ims['puppet_string_%s' % take] = S.string_tile(take)
        ims['puppet_string_knot_%s' % take] = S.knot_sprite(take)
    return god, ims


def sprite_meta():
    """frame width, frames, durations and tag for each .aseprite"""
    meta = {}
    for key, stem, n, times, loop, fn, phase in ANIMS:
        meta[stem] = (R.W, n, times, key)
        meta[stem + '_aura'] = (G.AURA_W, n, times, key + '_aura')
    for name, seq, prof in RIFTS:
        specs_fn, times, loop = RF.SEQS[seq]
        P = RF.PROFILES[prof]
        for layer in ('back', 'front', 'glow'):
            meta['%s_%s' % (name, layer)] = (P.W, len(specs_fn()), times, '%s_%s' % (seq, layer))
    for take in ('red', 'blue'):
        meta['puppet_string_%s' % take] = (16, 1, [1.0], 'string')
        meta['puppet_string_knot_%s' % take] = (5, 1, [1.0], 'knot')
    return meta


# ------------------------------------------------------------------ audit

def audit(god, ims):
    ok = True
    lines = []
    hover = [G.hover_px(i) for i in range(G.N)]
    hst = B.stats(G.hover_image())
    lines.append('approved hover sheet: %d colours, black %.1f%%' % (hst['colours'], 100 * hst['black']))
    for key, stem, n, times, loop, fn, phase in ANIMS:
        st = B.stats(ims[stem])
        lines.append('%s: %d frames (%s s), %d colours, black %.1f%%, semi %d' % (
            stem, n, ', '.join('%.2f' % t for t in times), st['colours'], 100 * st['black'], st['semi']))
        ok &= st['semi'] == 0
        for i, f in enumerate(god[key]):
            px = f['px']
            a = B.audit(px, fx=f['fx'])
            body = {p: k for p, k in px.items() if p not in f['fx']}
            low = max(y for (x, y) in body)
            top = min(y for (x, y) in px)
            want = R.ANCHOR[1] - f['bob']
            rows = [t[1] for s in ('left', 'right') for t in f['tips'][s].values()]
            tip_hi, tip_lo = min(rows), max(rows)
            high = f['pose'].startswith('work') or f['pose'] in HIGH_POSES or key == 'hit'
            tip_bad = tip_lo >= RIFT_ROW_MIN or (high and tip_lo > WORKING_ROW_MAX)
            diff = ''
            if key == 'control':
                d = {p for p in set(px) | set(hover[i]) if px.get(p) != hover[i].get(p)}
                central = [p for p in d if 141 <= p[0] <= 178 and p[1] < 118]
                diff = ', %d texels differ from hover %d (%d in the head/neck column above the shoulders)' % (
                    len(d), i, len(central))
            bad = a['gaps'] or a['lone'] or a['holes'] or low != want or top < 0 or tip_bad
            ok &= not bad
            lines.append('  %-12s %d %-7s bob %d, lowest row %d (want %d), top row %d, claw points rows %d-%d, '
                         'gaps %d lone %d holes %d%s%s' % (key, i, f['pose'], f['bob'], low, want, top, tip_hi, tip_lo,
                                                          len(a['gaps']), len(a['lone']), len(a['holes']), diff,
                                                          '  <-- FAIL' if bad else ''))
    for name in sorted(ims):
        if name.startswith('jordan_god'):
            continue
        st = B.stats(ims[name])
        ok &= st['semi'] == 0
        lines.append('%-36s %4dx%-3d colours %2d  semi %d' % (name, ims[name].width, ims[name].height, st['colours'],
                                                             st['semi']))
    return ok, lines


# ------------------------------------------------------------------ fingertip table

def texel_px(x, y):
    return [round((x + 0.5 - R.ANCHOR[0]) * SC.SCALE, 1), round((y + 0.5 - R.ANCHOR[1]) * SC.SCALE, 1)]


def fingertip_table(god):
    anims = {}
    worst_working, worst_any = 0, 0
    for key, stem, n, times, loop, fn, phase in ANIMS:
        tips, tips_px, tension, bob, poses = [], [], [], [], []
        for i, f in enumerate(god[key]):
            tips.append({s: [list(f['tips'][s][d]) for d in SC.DIGIT_ORDER] for s in ('left', 'right')})
            tips_px.append({s: [texel_px(*f['tips'][s][d]) for d in SC.DIGIT_ORDER] for s in ('left', 'right')})
            tension.append({s: round(v, 2) for s, v in f['tension'].items()})
            bob.append(f['bob'])
            poses.append(f['pose'])
            lo = max(t[1] for s in ('left', 'right') for t in f['tips'][s].values())
            worst_any = max(worst_any, lo)
            if f['pose'].startswith('work') or f['pose'] in HIGH_POSES or key == 'hit':
                worst_working = max(worst_working, lo)
        entry = {'sheet': stem + '.png', 'aura': stem + '_aura.png', 'frames': n,
                 'times': [round(t, 3) for t in times], 'loop': loop, 'poses': poses, 'bob': bob,
                 'tension': tension, 'tips': tips, 'tips_px': tips_px}
        if key.startswith('summon'):
            entry['then'] = 'puppeteer_control from frame 0'
        elif key.startswith('yank'):
            entry['then'] = 'puppeteer_control from frame 4 (the yank rides hover poses 0-3)'
        elif key == 'hit':
            entry['then'] = 'puppeteer_control from frame 0'
        anims['puppeteer_' + key if key != 'hit' else 'jordan_god_hit'] = entry
    return {
        'about': 'Demon-god Jordan, puppet master (approval pass). The claw points the strings hang from, per '
                 'frame, for every anim. All anims share the hover frame: 320x224, anchor (160, 223), drawn at '
                 'offset (-160, -223), scale 3.',
        'frame': [R.W, R.H], 'anchor': list(R.ANCHOR), 'scale': SC.SCALE,
        'format': 'tips[frame] = {left: [5 points], right: [5 points]}, each point [x, y] in frame texels (x right, '
                  'y down, 0-based, the bob already in). The string starts at that texel\'s centre. left = the '
                  'screen-left hand (his right), right = the screen-right hand (his left).',
        'digit_order': list(SC.DIGIT_ORDER),
        'pairs': {'inner': [0, 1], 'outer': [2, 3]},
        'pair_rule': 'two strings per puppet: a puppet whose back hook lies further from his centre line than its '
                     'hand\'s claws takes the outer pair (ring, little), one under or inside the hand takes the '
                     'inner pair (index, middle). With the plan\'s spots: Greyson inner, Matt outer, Captain Burak '
                     'outer, Danny outer. Point 4 (the thumb) is spare.',
        'tips_px_convention': 'tips_px = screen px from GOD_POINT = ((x + 0.5 - 160) * 3, (y + 0.5 - 223) * 3): the '
                              'sheet is placed with its anchor texel\'s top-left corner on GOD_POINT.',
        'tension': 'per hand, 0 = slack .. 1 = taut (the preview sags a string (1 - tension) x 12% of its span at '
                   'its middle; a slack one also ripples). A working hand is 0.7.',
        'hooks_check': 'the plan\'s back hooks are on frame rows %d-123 (screen y 220-300). Every working claw point '
                       '(control, the yanks, the hit, and the summon\'s ready, top, hang and settle frames) is on row '
                       '%d or higher up, so its strings run down. The lowest claw point of any frame (the summon\'s '
                       'dip) is row %d, above the rifts on rows %d-169.' % (HOOK_ROW_MIN, worst_working, worst_any,
                                                                             RIFT_ROW_MIN),
        'summon_sync': {
            'rift_starts_on': 'summon frame 1 (dip): rift summon frame 0 (the crack) under each puppet',
            'strings_appear_on': 'summon frame 1 (dip): cast from the claw points down into the crack',
            'puppet_rises_from': 'summon frame 3 (yank): feet from one puppet height under the rift anchor to the '
                                 'anchor in about 0.30 s, fast then easing (the preview uses 1 - (1 - t)^2)',
            'rift_open_loop': 'rift summon frames 3-5 loop seamlessly if the rise needs longer',
        },
        'yank_sync': 'yank frame 1 (pull) is the jerk: start Danny\'s leap on it',
        'hit_sync': 'run the bead up the strings (string texture scrolling, or the knot sprite moved along them) '
                    'for about 0.25 s, then play jordan_god_hit',
        'anims': anims,
    }


# ------------------------------------------------------------------ previews

def _quantize_all(frames, colours=255):
    """One shared palette for a GIF, built from a montage of up to 16 of its frames."""
    pick = frames[::max(1, len(frames) // 16)][:16]
    w, h = pick[0].size
    mont = Image.new('RGB', (w, h * len(pick)))
    for i, f in enumerate(pick):
        mont.paste(f.convert('RGB'), (0, i * h))
    pal = mont.quantize(colors=colours, method=Image.MEDIANCUT)
    return [f.convert('RGB').quantize(palette=pal, dither=Image.NONE) for f in frames]


def save_gif(path, frames, durs):
    q = _quantize_all(frames)
    ms = [max(20, int(round(d * 100)) * 10) for d in durs]
    q[0].save(path, save_all=True, append_images=q[1:], duration=ms, loop=0, disposal=1, optimize=False)
    return len(frames), sum(ms) / 1000.0


def _ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2


def _seq_frame(t, t0, times):
    """Index into a one-shot sequence started at t0 (None before it or after it)."""
    if t < t0:
        return None
    acc = t0
    for i, d in enumerate(times):
        if t < acc + d - 1e-9:
            return i
        acc += d
    return None


class Timeline:
    def __init__(self):
        self.god = []
        self.t = 0.0

    def play(self, anim, frames, times):
        start = self.t
        for i, d in zip(frames, times):
            self.god.append((self.t, anim, i, d))
            self.t += d
        return start

    def god_at(self, t):
        for (t0, anim, i, d) in self.god:
            if t0 <= t < t0 + d - 1e-9:
                return anim, i
        return self.god[-1][1], self.god[-1][2]


def render(tl, pups_at, take, crop, scale, tick=0.02):
    """Sample a timeline: a GIF frame whenever the composed state changes."""
    frames, durs = [], []
    last, ms, t = None, 0.0, 0.0
    while t < tl.t - 1e-9:
        anim, gi = tl.god_at(t)
        runes = int(t / RU.FRAME_TIME + 1e-9) % RU.FRAMES
        pups = pups_at(t)
        key = (anim, gi, runes, repr(pups))
        if key != last:
            if last is not None:
                durs.append(ms)
            nat = SC.compose(god=(anim, gi), runes=runes, take=take, puppets=pups, player=False)
            frames.append(nat.crop(crop).resize(((crop[2] - crop[0]) * scale, (crop[3] - crop[1]) * scale),
                                                Image.NEAREST))
            last, ms = key, 0.0
        ms += tick
        t += tick
    durs.append(ms)
    return frames, durs


CTRL = list(range(A.CONTROL_N))
CTRL_T = [A.CONTROL_TIME] * A.CONTROL_N
CROP_A1 = (150, 0, 490, 230)      # attack 1: the god and both puppets
CROP_A2 = (140, 0, 520, 230)      # attack 2: Captain Burak far left, Danny far right


def summon_preview(which, take='red'):
    """Attack 1. control (1 loop) -> summon (the pulled puppet(s) rise out of their rifts) -> control
    (1 loop) -> despawn (strings go limp, the rift swallows them) -> a beat."""
    tl = Timeline()
    tl.play('control', CTRL, CTRL_T)
    t_sum = tl.play('summon_' + which, list(range(A.SUMMON_N)), A.SUMMON_TIMES)
    tl.play('control', CTRL, CTRL_T)
    t_des = tl.play('control', CTRL, CTRL_T)
    pulled = {'left': ['greyson'], 'right': ['matt'], 'both': ['greyson', 'matt']}[which]
    t_rift = t_sum + A.SUMMON_TIMES[0]
    t_yank = t_sum + sum(A.SUMMON_TIMES[:3])

    def pups(t):
        out = []
        for name in ('greyson', 'matt'):
            if name not in pulled:
                out.append({'name': name, 'rise': 1.0, 'strings': True})
                continue
            p = {'name': name, 'strings': True}
            rk = _seq_frame(t, t_rift, RF.SUMMON_TIMES)
            dk = _seq_frame(t, t_des, RF.DESPAWN_TIMES)
            if t < t_rift:
                p['rise'], p['strings'] = None, False
            elif rk is not None:
                p['rift'] = ('summon', rk)
                u = (t - t_yank) / 0.30
                p['rise'] = 0.0 if u < 0 else round(_ease_out(u) * 24) / 24.0
            elif t < t_des:
                p['rise'] = 1.0
            elif dk is not None:
                p['rift'] = ('despawn', dk)
                u = (t - t_des - RF.DESPAWN_TIMES[0]) / sum(RF.DESPAWN_TIMES[1:4])
                p['rise'] = 1.0 if u < 0 else max(0.0, 1.0 - round(u * u * 24) / 24.0)
                p.update(tension=0.0, bow=2.0, wave=3.5 if dk == 0 else 5.0, strings=dk <= 1)
                if p['rise'] <= 0.0:
                    p['rise'] = None
            else:
                p['rise'], p['strings'] = None, False
            out.append(p)
        return out

    return render(tl, pups, take, CROP_A1, 2)


def control_preview(take='red', loops=4):
    tl = Timeline()
    for _ in range(loops):
        tl.play('control', CTRL, CTRL_T)
    pups = lambda t: [{'name': 'greyson', 'rise': 1.0, 'strings': True},  # noqa: E731
                      {'name': 'matt', 'rise': 1.0, 'strings': True}]
    return render(tl, pups, take, CROP_A1, 2)


def yank_preview(which, take='red'):
    """Attack 2: the hand's quick pull hops its puppet (Danny on the right, Captain Burak on the
    left): control, yank, control, twice."""
    tl = Timeline()
    marks = []
    for _ in range(2):
        tl.play('control', CTRL, CTRL_T)
        marks.append(tl.play('yank_' + which, list(range(A.YANK_N)), A.YANK_TIMES))
        tl.play('control', [4, 5], CTRL_T[:2])
    who = 'danny' if which == 'right' else 'captain_burak'

    def pups(t):
        lift = 0.0
        for t0 in marks:
            u = (t - (t0 + A.YANK_TIMES[0])) / 0.45          # the hop starts on the pull
            if 0 <= u < 1:
                lift = round(16 * 4 * u * (1 - u))
        out = []
        for name in ('captain_burak', 'danny'):
            p = {'name': name, 'rise': 1.0, 'strings': True}
            if name == who:
                p['lift'] = lift
            out.append(p)
        return out

    return render(tl, pups, take, CROP_A2, 2)


def hit_preview(take='red'):
    """Attack 1: the damage runs up Greyson's strings as a bead (0.25 s), then he flinches."""
    tl = Timeline()
    tl.play('control', CTRL, CTRL_T)
    t_pulse = tl.t
    tl.play('control', [0, 1], CTRL_T[:2])                    # 0.28 s: the bead climbs
    t_hit = tl.play('hit', list(range(A.HIT_N)), A.HIT_TIMES)
    tl.play('control', CTRL, CTRL_T)

    def pups(t):
        g = {'name': 'greyson', 'rise': 1.0, 'strings': True}
        u = (t - t_pulse) / 0.25
        if 0 <= u < 1.0:
            g['pulse'] = round(u * 12) / 12.0
        return [g, {'name': 'matt', 'rise': 1.0, 'strings': True}]

    return render(tl, pups, take, CROP_A1, 2)


def rift_preview(seq, who='matt', take='red', scale=3):
    """Close-up of one rift with a stand-in rising (summon) or sinking (despawn), its strings
    coming down from above the frame."""
    specs = RF.SEQS[seq][0]()
    times = RF.SEQS[seq][1]
    prof = PP.PUPPETS[who]['rift']
    P = RF.PROFILES[prof]
    img, feet, hook = PP.placeholder(who)
    top = img.height - P.ANCHOR[1] + 12
    W_, H_ = P.W, P.H + top
    fx, fy = P.ANCHOR[0], P.ANCHOR[1] + top
    bgv = SC.backdrop().crop((300 - W_ // 2, 100, 300 - W_ // 2 + W_, 100 + H_))
    tips = [(fx - 6, -2), (fx + 6, -2)]            # two strings from above the frame
    rise = [None, None, 0.0, 0.35, 0.72, 0.94, 1.0, 1.0] if seq == 'summon' else [1.0, 1.0, 0.55, 0.12, None, None]
    frames, durs = [], []
    for k, spec in enumerate(specs):
        b, f, g = RF.frame(spec, P)
        canvas = bgv.copy()
        canvas.alpha_composite(B.image(b, P.W, P.H, RF.PAL), (0, top))
        if rise[k] is not None:
            depth = int(round((1 - rise[k]) * img.height))
            tlp = (fx - feet[0], fy + depth - feet[1])
            hook_at = (tlp[0] + hook[0], tlp[1] + hook[1])
            if seq == 'summon' or k <= 1:
                slack = seq == 'despawn'
                strings = []
                for j, p0 in enumerate(tips):
                    pts = S.curve(p0, (hook_at[0] + (j - 0.5) * 4, hook_at[1]),
                                  0.0 if slack else (1.0 if k >= 3 else 0.5),
                                  bow=(2 if slack else 0) * (1 if j % 2 else -1),
                                  wave=(3.5 if k == 0 else 5.0) if slack else 0.0, phase=j * 1.3)
                    pts = [q for q in pts if q[1] <= fy]          # they go under the floor with the puppet
                    if len(pts) > 1:
                        strings.append(pts)
                S.draw(canvas, strings, take)
            rows = img.height - depth
            if rows > 0:
                SC._paste_clipped(canvas, img.crop((0, 0, img.width, rows)), tlp)
        elif seq == 'summon':
            S.draw(canvas, [S.curve(p0, (fx, fy), 0.4) for p0 in tips], take)
        SC._add(canvas, B.image(g, P.W, P.H, RF.GLOW_PAL), (0, top))
        canvas.alpha_composite(B.image(f, P.W, P.H, RF.PAL), (0, top))
        frames.append(canvas.resize((W_ * scale, H_ * scale), Image.NEAREST))
        durs.append(times[k] + (0.5 if k == len(specs) - 1 else 0.0))
    return frames, durs


def mock(which, take):
    """1920x1080 in-game mocks on the plan's spots.
    a1: attack 1, the left hand at the top of its yank (summon_left frame 4): Greyson half out of
        his rift on taut strings, Matt standing on the right hand's working strings.
    a1_control: attack 1, both standing, the working loop (control frame 1).
    a2: attack 2, the right hand's quick pull held (yank_right frame 2) over Danny, Captain Burak on
        the left hand's working strings (the hop itself is in the yank GIF)."""
    if which == 'a1':
        n = SC.compose(god=('summon_left', 4), runes=5, take=take,
                       puppets=[{'name': 'greyson', 'rise': 0.55, 'rift': ('summon', 4), 'strings': True},
                                {'name': 'matt', 'rise': 1.0, 'strings': True}])
    elif which == 'a1_control':
        n = SC.compose(god=('control', 1), runes=5, take=take,
                       puppets=[{'name': 'greyson', 'rise': 1.0, 'strings': True},
                                {'name': 'matt', 'rise': 1.0, 'strings': True}])
    else:
        n = SC.compose(god=('yank_right', 2), runes=9, take=take,
                       puppets=[{'name': 'captain_burak', 'rise': 1.0, 'strings': True},
                                {'name': 'danny', 'rise': 1.0, 'strings': True}])
    return SC.screen(n)


def contact_sheet(ims, god):
    """One page: the two string takes (attack 1 mock, half size), attack 2, every god anim frame by
    frame at 1x over the void with its claw points marked, the rift sequences, the string sprites."""
    pad = 16
    W_ = 1952
    parts = []
    txt = (226, 222, 240, 255)
    sub = (200, 196, 214, 255)
    row = Image.new('RGBA', (W_, 60 + 540 + 24), (10, 8, 16, 255))
    d = ImageDraw.Draw(row)
    d.text((pad, 10), 'Demon-god Jordan, puppet master: approval pass. 1920x1080 mocks at half size on the build plan\'s '
                      'spots. Greyson, Matt, Captain Burak and Danny are PLACEHOLDERS (greyed approved idles).', fill=txt)
    d.text((pad, 28), 'Attack 1, left: RED take, right: BLUE take. The left hand at the top of its yank (summon_left '
                      'frame 4), Greyson half out of his rift, Matt on the right hand\'s working strings.', fill=txt)
    x = pad
    for take in ('red', 'blue'):
        m = mock('a1', take).resize((960, 540), Image.NEAREST)
        row.paste(m, (x, 60))
        d.text((x, 60 + 540 + 6), '%s take: core %s, glow %s (added), knot %s' % (
            take.upper(), '#%02X%02X%02X' % S.TAKES[take]['core'][:3], '#%02X%02X%02X' % S.TAKES[take]['glow'][:3],
            '#%02X%02X%02X' % S.TAKES[take]['hot'][:3]), fill=txt)
        x += 960
    parts.append(row)
    row = Image.new('RGBA', (W_, 30 + 540 + 10), (10, 8, 16, 255))
    d = ImageDraw.Draw(row)
    d.text((pad, 8), 'Attack 2 (red): the right hand\'s quick pull held (yank_right frame 2) over Danny; Captain '
                     'Burak on the left hand. Right: attack 1 in the working loop (control frame 1).',
           fill=txt)
    row.paste(mock('a2', 'red').resize((960, 540), Image.NEAREST), (pad, 30))
    row.paste(mock('a1_control', 'red').resize((960, 540), Image.NEAREST), (pad + 960, 30))
    parts.append(row)
    back = SC.backdrop().crop((160, 0, 480, 201))
    crop = (40, 30, 280, 224)
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    for key, stem, n, times, loop, fn, phase in ANIMS:
        row = Image.new('RGBA', (W_, ch + 36), (10, 8, 16, 255))
        d = ImageDraw.Draw(row)
        d.text((pad, 4), '%s: %d frames, %s s%s. Green: the claw points (tips).' % (
            stem, n, ', '.join('%.2f' % t for t in times), ' (loops)' if loop else ''), fill=txt)
        for i in range(n):
            tile = Image.new('RGBA', (R.W, R.H), (0, 0, 0, 255))
            tile.alpha_composite(back, (0, 23))
            tile.alpha_composite(RU.frame_image(0), (int(round(L.CORE[0] - 95.5)), int(round(L.CORE[1] - 95.5))))
            tile.alpha_composite(ims[stem].crop((i * R.W, 0, (i + 1) * R.W, R.H)))
            dd = ImageDraw.Draw(tile)
            for side in ('left', 'right'):
                for dg, (tx, ty) in god[key][i]['tips'][side].items():
                    dd.point((tx, ty), fill=(0, 255, 0, 255))
            t = tile.crop(crop)
            xx = pad + i * (cw + 6)
            if xx + cw > W_:
                break
            row.paste(t, (xx, 20))
            d.text((xx + 2, 20 + ch + 2), god[key][i]['pose'], fill=sub)
        parts.append(row)
    for name, seq, prof in RIFTS:
        specs = RF.SEQS[seq][0]()
        times = RF.SEQS[seq][1]
        loop = RF.SEQS[seq][2]
        P = RF.PROFILES[prof]
        scale = 1
        row = Image.new('RGBA', (W_, P.H * scale + 40), (10, 8, 16, 255))
        d = ImageDraw.Draw(row)
        d.text((pad, 4), '%s: %d frames of %dx%d, anchor %s (the puppet\'s feet), %s s; frames %d-%d loop. Back + glow '
                         '(added) + front over the void.' % (name, len(specs), P.W, P.H, P.ANCHOR,
                                                              ', '.join('%.2f' % t for t in times), loop[0], loop[1]),
               fill=txt)
        for k, spec in enumerate(specs):
            b, f, g = RF.frame(spec, P)
            c = SC.backdrop().crop((250, 200, 250 + P.W, 200 + P.H)).copy()
            c.alpha_composite(B.image(b, P.W, P.H, RF.PAL))
            SC._add(c, B.image(g, P.W, P.H, RF.GLOW_PAL), (0, 0))
            c.alpha_composite(B.image(f, P.W, P.H, RF.PAL))
            xx = pad + k * (P.W + 8)
            if xx + P.W > W_:
                break
            row.paste(c, (xx, 18))
            d.text((xx + 2, 18 + P.H + 2), spec['name'], fill=sub)
        parts.append(row)
    row = Image.new('RGBA', (W_, 110), (10, 8, 16, 255))
    d = ImageDraw.Draw(row)
    d.text((pad, 4), 'string tiles (16x3: glow / core / glow, one hot bead) and fingertip knots (5x5, added), 12x',
           fill=txt)
    xx = pad
    for take in ('red', 'blue'):
        for nm in ('puppet_string_%s' % take, 'puppet_string_knot_%s' % take):
            im = ims[nm]
            big = Image.new('RGBA', im.size, (4, 3, 10, 255))
            big.alpha_composite(im)
            big = big.resize((im.width * 12, im.height * 12), Image.NEAREST)
            row.paste(big, (xx, 22))
            d.text((xx, 22 + big.height + 4), nm, fill=sub)
            xx += big.width + 40
    parts.append(row)
    sheet = Image.new('RGBA', (W_, sum(p.height for p in parts)), (10, 8, 16, 255))
    y = 0
    for p in parts:
        sheet.paste(p, (0, y))
        y += p.height
    return sheet


# ------------------------------------------------------------------ writing

LUA = r'''
local src = app.params["src"]
local out = app.params["out"]
local n = tonumber(app.params["n"])
local fw = tonumber(app.params["fw"])
local durs = {}
for d in string.gmatch(app.params["durs"], "[^,]+") do table.insert(durs, tonumber(d)) end
local strip = Image{ fromFile = src }
local fh = strip.height
local spr = Sprite(fw, fh, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = app.params["layer"]
for i = 1, n do
  if i > 1 then spr:newEmptyFrame() end
  local img = Image(fw, fh, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0))
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = durs[((i - 1) % #durs) + 1]
end
local tag = spr:newTag(1, n)
tag.name = app.params["tag"]
spr:saveAs(out)
'''


def aseprite(*args):
    subprocess.run([ASE, '-b'] + list(args), check=True, capture_output=True)


def write(god, ims):
    if not _under(OUT, os.path.join(ROOT, 'art_source', 'jordan_puppeteer', 'approval')):
        raise SystemExit('refusing: %s is not art_source/jordan_puppeteer/approval' % OUT)
    for p in FORBIDDEN:
        if _under(OUT, p):
            raise SystemExit('refusing: %s is under %s' % (OUT, p))
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='jpup_')
    lua = os.path.join(tmp, 'mk.lua')
    with open(lua, 'w') as f:
        f.write(LUA)
    meta = sprite_meta()
    done = []
    for name, im in ims.items():
        fw, n, times, tag = meta[name]
        tpng = os.path.join(tmp, name + '.png')
        tase = os.path.join(tmp, name + '.aseprite')
        im.save(tpng)
        additive = name.endswith(('_glow', '_aura')) or 'knot' in name
        aseprite('--script-param', 'src=' + tpng, '--script-param', 'out=' + tase, '--script-param', 'n=%d' % n,
                 '--script-param', 'fw=%d' % fw, '--script-param', 'durs=' + ','.join('%.3f' % t for t in times),
                 '--script-param', 'layer=' + ('glow (additive)' if additive else 'art'),
                 '--script-param', 'tag=' + tag, '--script', lua)
        back = os.path.join(tmp, name + '_rt.png')
        aseprite(tase, '--sheet', back, '--sheet-type', 'horizontal')
        d = pixel_diff(Image.open(tpng), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
        for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
            with open(src, 'rb') as f:
                data = f.read()
            with open(os.path.join(OUT, name + ext), 'wb') as f:
                f.write(data)
        done.append('%s.png + .aseprite (%d frame%s, round trip identical)' % (name, n, '' if n == 1 else 's'))
    with open(os.path.join(OUT, 'jordan_puppeteer_fingertips.json'), 'w') as f:
        json.dump(fingertip_table(god), f, indent=1)
    done.append('jordan_puppeteer_fingertips.json')
    names = {('a1', 'red'): 'jordan_puppeteer_mock_red.png', ('a1', 'blue'): 'jordan_puppeteer_mock_blue.png',
             ('a1_control', 'red'): 'jordan_puppeteer_mock_control_red.png',
             ('a2', 'red'): 'jordan_puppeteer_mock_attack2_red.png'}
    for (which, take), name in names.items():
        mock(which, take).save(os.path.join(OUT, name))
        done.append('%s (1920x1080)' % name)
    cs = contact_sheet(ims, god)
    cs.save(os.path.join(OUT, 'jordan_puppeteer_contact.png'))
    done.append('jordan_puppeteer_contact.png %s' % (cs.size,))
    gifs = [('jordan_god_puppeteer_control.gif', lambda: control_preview('red')),
            ('jordan_god_puppeteer_summon_both.gif', lambda: summon_preview('both', 'red')),
            ('jordan_god_puppeteer_summon_both_blue.gif', lambda: summon_preview('both', 'blue')),
            ('jordan_god_puppeteer_summon_left.gif', lambda: summon_preview('left', 'red')),
            ('jordan_god_puppeteer_summon_right.gif', lambda: summon_preview('right', 'red')),
            ('jordan_god_puppeteer_yank_right.gif', lambda: yank_preview('right', 'red')),
            ('jordan_god_puppeteer_yank_left.gif', lambda: yank_preview('left', 'red')),
            ('jordan_god_hit.gif', lambda: hit_preview('red')),
            ('puppet_rift_summon.gif', lambda: rift_preview('summon', 'matt')),
            ('puppet_rift_despawn.gif', lambda: rift_preview('despawn', 'matt')),
            ('puppet_rift_wide_summon.gif', lambda: rift_preview('summon', 'danny')),
            ('puppet_rift_wide_despawn.gif', lambda: rift_preview('despawn', 'danny'))]
    for name, make in gifs:
        frames, durs = make()
        n, secs = save_gif(os.path.join(OUT, name), frames, durs)
        done.append('%s: %d frames, %.2f s, %d KB' % (name, n, secs, os.path.getsize(os.path.join(OUT, name)) // 1024))
    return done


def main(argv):
    if not argv or argv[0] not in ('--check', '--write'):
        print(__doc__)
        return 2
    install_guard()
    god, ims = build_all()
    ok, lines = audit(god, ims)
    for ln in lines:
        print(ln)
    if not ok:
        print('audit FAILED: nothing written')
        return 1
    if argv[0] == '--write':
        for ln in write(god, ims):
            print('wrote', ln)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
