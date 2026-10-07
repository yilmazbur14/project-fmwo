"""JORDAN'S PUPPETS - CONCEPT ART (2026-09-28). An approval pass: nothing here ships.

The user: "draw up some concept art for the rest of the undead bosses (not liam and not computah)".
So ERIC, MASON, JOSH and CARTER as Jordan's puppets IN ACTION, in the approved look (take B, "blue"),
for designing combination attacks later. Per boss: his approved idle and signature poses off his own
fight sheets, run through the same recipe the shipped twins came from (../jp_core.treat with
../jp_bosses), at 3x (game scale) and at 6x, the BACK hook marked on every pose (the strings tie on
there and nowhere else), with a note per pose of what the recipe carried by itself and what was, or
would be, hand work. Then two 1920x1080 in-fight mocks in the approved staging (option B: the whole
view at 2 px a texel), two puppets in each hanging from Jordan's blue strings by the back hook.
The pairings are for DISPLAY ONLY: no attack is designed here.

Reads, never writes: the fight sheets under Assets/Characters; the recipe (jp_core, jp_bosses,
jp_palette in ..); the approved idles (../approval/<boss>/<boss>_after_B_1x.png and _hooks.json);
the puppeteer artist's staging (art_source/jordan_puppeteer/staging/jp_staging.py: the void, the god,
his runes and aura, the blue strings, his fingertips), imported for its functions, its writer never
run. Writes only into this folder, and only with --write: an audit hook refuses any other write, and
the only program it lets run is Aseprite, saving the .aseprite beside each pose strip in here.

    python jp_concepts.py            # print this; writes nothing
    python jp_concepts.py --check    # build and audit everything, print the notes; writes nothing
    python jp_concepts.py --write    # write the sheets, the strips, the mocks and notes.json here

What --write makes, per boss (eric, mason, josh, carter):
  <boss>_concept_3x.png          the approved idle + the poses at game scale on the void
  <boss>_concept_6x.png          the same at 6x, with the notes under each pose
  <boss>_poses_1x.png/.aseprite  the treated frames themselves, one cell each, feet on one anchor
and concept_mock_eric_josh.png, concept_mock_mason_carter.png (1920x1080), notes.json.

On every pose the BACK hook is marked with a magenta ring and the two blue strings run up from it.
Front and three-quarter views: the point is between the shoulder blades BEHIND the body, so the
strings are drawn under the sprite and vanish behind it. Back views: the ring is drawn on his back
by hand and the strings run over the sprite into it.
"""
import copy
import json
import os
import subprocess
import sys
import textwrap

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PUPS = os.path.dirname(HERE)                                      # art_source/jordan_puppets
ART = os.path.dirname(PUPS)                                       # art_source
ROOT = os.path.dirname(ART)
STAGING = os.path.join(ART, 'jordan_puppeteer', 'staging')
APPROVAL = os.path.join(PUPS, 'approval')
VOID_BG = os.path.join(ROOT, 'Assets', 'Environment', 'Void', 'void_bg.png')
TAKE = 'B'

# ------------------------------------------------------------------ the guard


def _real(p):
    return os.path.normcase(os.path.realpath(os.fspath(p)))


def _inside(p, root):
    rp, r = _real(p), _real(root)
    return rp == r or rp.startswith(r + os.sep)


def _split_cmdline(s):
    out, cur, quoted = [], '', False
    for ch in s:
        if ch == '"':
            quoted = not quoted
        elif ch == ' ' and not quoted:
            if cur:
                out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def install_guard(write_root, aseprite):
    """Refuse every write, rename or removal outside `write_root` (None: refuse every one of them),
    and every program but Aseprite, which may only be handed files inside `write_root`."""
    ase = _real(aseprite)

    def is_path(a):
        return isinstance(a, (str, bytes, os.PathLike))

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and
                       flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
            if writing and (write_root is None or not _inside(path, write_root)):
                raise PermissionError('concepts guard: refusing to write %s' % (path,))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                       'os.truncate', 'os.chmod', 'os.symlink', 'os.link', 'shutil.copyfile',
                       'shutil.copytree', 'shutil.move', 'shutil.rmtree'):
            for a in args:
                if is_path(a) and (write_root is None or not _inside(a, write_root)):
                    raise PermissionError('concepts guard: refusing %s on %s' % (event, a))
        elif event in ('os.system', 'os.exec', 'os.spawn', 'os.startfile', 'os.posix_spawn'):
            raise PermissionError('concepts guard: refusing %s' % event)
        elif event == 'subprocess.Popen':
            if write_root is None:
                raise PermissionError('concepts guard: --check launches nothing')
            argv = args[1]
            if isinstance(argv, bytes):
                argv = argv.decode()
            # on Windows the event carries the joined command line: split it back (quotes group)
            argv = _split_cmdline(argv) if isinstance(argv, str) else [os.fspath(a) for a in argv]
            if not argv or _real(argv[0]) != ase:
                raise PermissionError('concepts guard: only Aseprite may run, not %s' % (argv[:1],))
            for a in argv[1:]:
                if is_path(a) and str(a).lower().endswith(('.png', '.aseprite')) and not _inside(a, write_root):
                    raise PermissionError('concepts guard: Aseprite may only touch files in here, not %s' % a)

    sys.addaudithook(hook)


# ------------------------------------------------------------------ the poses

# Each anim's frames on the multi-anim sheets, as the scenes play them (EricScene.tscn and
# MasonScene.tscn animation tracks, JoshArtLayout / CarterArtLayout FINAL_ANIMS). A sheet not listed
# is one anim. A ring is kept on a pose only if the tracker finds it on EVERY frame of the pose's anim
# (the shipped sheets' all-or-nothing rule, taken per anim), so nothing here would pop in and out.
ANIMS = {
    'Eric/eric_sheet_v2.png': {
        'earthquake': range(0, 11), 'recover': [11, 12], 'whirlwind': range(13, 21), 'idle': range(21, 27),
        'downed': range(27, 32), 'throw_windup': [32, 33], 'throw_release': [34, 35], 'empty_wait': [36, 37],
        'recall_reach': [38], 'recall_catch': [39]},
    'Eric/eric_bearhug_v2.png': {
        'hug_plant': [0], 'hug_charge': [1, 2], 'hug_lunge': [3, 4], 'hug_whiff': [5], 'hug_stumble': [6],
        'hug_grab': [7], 'hug_squeeze': [8, 9, 10], 'hug_toss': [11], 'hug_toss_end': [12], 'hug_retrieve': [13, 14]},
    'Eric/eric_broken.png': {'broken_final': range(0, 5), 'broken_final_loop': [5, 6, 7]},
    'Eric/eric_juggle.png': {'juggle_hit_final': [0, 1], 'juggle_tumble_final': [2, 3, 4, 5],
                             'juggle_crash_final': [6, 7, 8, 9]},
    'Mason/mason_sheet.png': {
        'idle': [0, 1], 'waddle': [2, 3, 4, 5], 'poop': [6, 7], 'eat': [8, 9], 'phone': [10, 11], 'hit': [12],
        'defeated': [13, 14], 'nugget_toss': [15, 16, 17], 'nugget_hold': [18]},
    'Mason/mason_juggle.png': {'juggle_hit_final': [0, 1], 'juggle_tumble_final': [2, 3, 4, 5, 6],
                               'juggle_crash_final': [7, 8, 9], 'juggle_down_final': [10, 11]},
}

# The game's own tint on a Wild Cards clone (JoshArtLayout.WILD_CLONE_TINT): the clones are his sheets
# drawn as see-through blue ghosts. Shown as the game would draw it over the puppet: no new art.
WILD_CLONE_TINT = (0.55, 0.72, 1.0, 0.78)

POSES = {
    'eric': [
        dict(key='quake', title='Quake stomp: the wind-up', sheet='Eric/eric_sheet_v2.png', fw=256, frame=4,
             anim='earthquake',
             look='The held overhead of the earthquake, the frame the player reads. Greatsword iron, the '
                  'plate bleached bone, beard and cape blood: all table work.'),
        dict(key='whirlwind', title='Whirlwind: his back to us', sheet='Eric/eric_sheet_v2.png', fw=256,
             frame=16, anim='whirlwind', back_view=True,
             look='A back view: the tracker has no front-view part to hold on to, so every ring is off and the '
                  'back ring is drawn by hand on the cape between the pauldrons. The slash arc goes bone.'),
        dict(key='throw', title='Sword throw: the release', sheet='Eric/eric_sheet_v2.png', fw=256, frame=34,
             anim='throw_release',
             look='The sword leaving his hand. The flying sword is its own sprite (eric_thrown_sword_v2): '
                  'every one of its colours is already in his table, so it carries as iron by itself.'),
        dict(key='bearhug', title='Bear hug: the lunge', sheet='Eric/eric_bearhug_v2.png', fw=256, frame=4,
             anim='hug_lunge',
             look='The cape flung open. Its lit flap (B83246) is the one colour of this sheet his table '
                  'lacked: added here as bright blood (R4). The motion lines go bone.'),
    ],
    'mason': [
        dict(key='poop', title='Poo bomb: the squat', sheet='Mason/mason_sheet.png', fw=64, frame=6, anim='poop',
             look='The squat, sweat flying (the drops go rune-blue). His eyes are screwed shut (< >): the '
                  'sockets overlay would light two round pupils over them, so the squint is kept and lit by '
                  'hand instead (f7 has his eyes open and keeps the overlay).'),
        dict(key='phone', title='Phone call: the Uber', sheet='Mason/mason_sheet.png', fw=64, frame=10,
             anim='phone',
             look='The phone goes pitch black. His raised arm is not the idle arm, so its wrist ring is off '
                  '(and so the whole anim keeps only the rings found on both its frames).'),
        dict(key='nuggets', title='Nugget toss: the heave', sheet='Mason/mason_sheet.png', fw=64, frame=17,
             anim='nugget_toss',
             look='The bucket goes blood and bone stripes; the fried nuggets map to blood, so he now hurls '
                  'raw red chunks (a question: bone like his costume instead?).'),
    ],
    'josh': [
        dict(key='wild_hold', title='Wild Cards: the wind-up he holds', sheet='Josh/josh_throw.png', fw=80,
             frame=0, anim='throw',
             look='wild_hold: the card cocked by his head. The card\'s gold flare shares his button gold, '
                  'so it goes bone with them: it no longer glows (a region could make it rune-blue).'),
        dict(key='throw', title='Wild Cards: the throw', sheet='Josh/josh_throw.png', fw=80, frame=1, anim='throw',
             look='The release; the gold arc goes bone. The hat tips on this frame and the tracker loses the '
                  'crown: its head ring is set by hand here, and that one frame keeps the ring on the whole '
                  'throw (without it the all-or-nothing rule drops it from all four).'),
        dict(key='glide', title='Glide (the finale cameo)', sheet='Josh/josh_glide.png', fw=80, frame=1,
             anim='glide',
             look='Riding pose; the card under him is its own sprite (Cards/josh_glider.png) in a gold '
                  'palette his table does not cover, so it is not drawn here. Only the head ring survives.'),
        dict(key='clone', title='A Wild Cards clone (the game\'s tint)', sheet='Josh/josh_throw.png', fw=80,
             frame=0, anim='throw', tint=WILD_CLONE_TINT,
             look='The clones are his own sheets tinted see-through blue in code: over the puppet the same '
                  'tint reads as a ghost of the puppet. No new art. Strings on a clone: a question.'),
    ],
    'carter': [
        dict(key='raging_demon', title='Raging Demon: the glare', sheet='Carter/carter_eye_flash.png', fw=96,
             frame=3, anim='carter_eye_flash',
             look='The control-loss frame the yank holds. Every ring tracks. The eye beams and the aura\'s '
                  'hot core turn rune-blue inside blood spikes; the face is not the idle face, so the jaw '
                  'and socket overlays sit out (his eyes glow by the table anyway).'),
        dict(key='beam_rush', title='Beam Rush: committed', sheet='Carter/carter_rush.png', fw=96, frame=3,
             anim='carter_rush',
             look='The frame the player reads before the strike. Head ring and face carry; the torso is '
                  'turned, so the back point rides the head (via crown) and the limb rings are off.'),
        dict(key='messatsu', title='Messatsu: the charge', sheet='Carter/carter_messatsu_charge.png', fw=96,
             frame=0, anim='carter_messatsu_charge',
             look='Palms cupped at the hip. The head is lower and turned: the face overlays sit out, the '
                  'eyes still glow by the table. Head ring only.'),
        dict(key='clone', title='A Raging Demon clone (FX sprite)', sheet='Carter/Demon/demon_clone.png', fw=48,
             frame=5, anim='demon_clone', fx=True, feet=(24, 47),
             look='An effect sheet, recoloured by table only: purple goes blood, the red eyes go the family '
                  'glow. Its authored fade (alpha 212) is kept. The red/yellow parry tell is the light over '
                  'it (demon_light, demon_feint), untouched.'),
    ],
}

# Hand data for the concept frames, kept here rather than in ../jp_bosses (which the shipped twins
# are rebuilt from and stay byte-identical to).
HAND = {
    'eric': {
        # the cape's lit flap, drawn only on the bear hug's lunge: one step up the blood ramp
        'table': 'cloth R4 B83246',
        # whirlwind f16 shows his back: the back ring on the cape, between the pauldrons
        'hooks': {('Eric/eric_sheet_v2.png', 16): {'back': (127, 154)}},
    },
    'josh': {
        # throw f1: the hat tips and the tracker loses the crown (0.67 of 0.7). Set by hand at the
        # crown's own offset that frame (+4, +1), the head ring is on all four throw frames, so the
        # all-or-nothing rule keeps it on the whole throw (and on wild_hold, its frame 0)
        'hooks': {('Josh/josh_throw.png', 1): {'head': (52, 11)}},
    },
    'mason': {
        # the squat (poop f6) screws his eyes shut: < >. The sockets overlay would light two round
        # pupils over them; this keeps his squint and lights it instead, the way Danny's slam does
        'overlays': {('Mason/mason_sheet.png', 6): [
            ('squint', [(28, 23, '|mgh|\n|gmm|\n|mgh|'), (33, 23, '|hgm|\n|mmg|\n|hgm|')]),
        ]},
    },
}
# Carter's clone: his own table, but its red eyes go the family glow like his own eyes do.
CARTER_CLONE_EYES = 'eye G1 FF4A3C\neye G2 C01830'

MOCKS = [
    dict(name='concept_mock_eric_josh',
         caption=['Eric: the quake stomp wind-up (eric_sheet_v2 f4)',
                  'Josh: the Wild Cards wind-up (josh_throw f0), mirrored to face the player as the game flips him'],
         puppets=[('eric', 'quake', (600, 690), 'left', False), ('josh', 'wild_hold', (1330, 690), 'right', True)]),
    dict(name='concept_mock_mason_carter',
         caption=['Mason: the nugget toss (mason_sheet f17)',
                  'Carter: the Beam Rush, committed (carter_rush f3), mirrored to face the player as the game flips him'],
         puppets=[('mason', 'nuggets', (640, 690), 'left', False), ('carter', 'beam_rush', (1300, 690), 'right', True)]),
]
PLAYER_AT = (960, 870)

# The body sheets each boss would need as a puppet, and the effect/prop sheets beside them: the
# survey measures what the recipe carries on every frame (for the ship-later list in notes.json).
SURVEY = {
    'eric': [('Eric/eric_sheet_v2.png', 256), ('Eric/eric_bearhug_v2.png', 256), ('Eric/eric_winded.png', 256),
             ('Eric/eric_broken.png', 256), ('Eric/eric_juggle.png', 256)],
    'mason': [('Mason/mason_sheet.png', 64), ('Mason/mason_juggle.png', 128)],
    'josh': [('Josh/josh_throw.png', 80), ('Josh/josh_glide.png', 80), ('Josh/josh_intro.png', 80),
             ('Josh/josh_mount.png', 80), ('Josh/josh_dismount.png', 80), ('Josh/josh_recovery.png', 80),
             ('Josh/josh_hit.png', 80), ('Josh/josh_defeat.png', 80), ('Josh/josh_juggle.png', 160)],
    'carter': [('Carter/carter_eye_flash.png', 96), ('Carter/carter_rush.png', 96), ('Carter/carter_rush_pass.png', 96),
               ('Carter/carter_messatsu_charge.png', 96), ('Carter/carter_messatsu_fire.png', 96),
               ('Carter/carter_intro.png', 96), ('Carter/carter_spent.png', 96), ('Carter/carter_hit.png', 96),
               ('Carter/carter_defeat.png', 96), ('Carter/carter_juggle.png', 192)],
}
PROPS = {
    'eric': ['Eric/eric_thrown_sword_v2.png', 'Eric/eric_sword_planted_v2.png', 'Eric/eric_broken_sword.png'],
    'mason': ['Mason/poo_bomb.png', 'Mason/poo_explosion.png', 'Mason/nugget_meteor.png', 'Mason/nugget_target.png',
              'Mason/nugget_impact.png', 'Mason/fry_trail.png', 'Mason/uber_driver.png'],
    'josh': ['Josh/Cards/card_burst.png', 'Josh/Cards/card_burst_rain.png', 'Josh/Cards/card_projectile.png',
             'Josh/Cards/josh_glider.png'],
    'carter': ['Carter/Demon/demon_clone.png', 'Carter/Demon/demon_clone_ghost.png'],
}
BOSS_ORDER = ['eric', 'mason', 'josh', 'carter']
AUDITED = ('gaps', 'lone', 'holes', 'bad_keys', 'silhouette', 'edge_black_lost')
RING_NAMES = ('head', 'wrist_l', 'wrist_r', 'knee_l', 'knee_r')
FACE_OVERLAYS = ('sockets', 'jaw')

# ------------------------------------------------------------------ loading (after the guard)

C = JB = PAL = ST = pixel_diff = Image = ImageDraw = ImageFont = None


def load():
    global C, JB, PAL, ST, pixel_diff, Image, ImageDraw, ImageFont
    sys.path.insert(0, PUPS)
    import jp_core as C  # noqa: E402
    import jp_bosses as JB  # noqa: E402
    import jp_palette as PAL  # noqa: E402
    from imgdiff import pixel_diff  # noqa: E402  (art_source/imgdiff.py; jp_core put art_source on the path)
    from PIL import Image, ImageDraw, ImageFont  # noqa: E402
    sys.path.insert(0, STAGING)
    import jp_staging as ST  # noqa: E402  (its main() is never called)


def font(size, bold=False):
    name = 'consolab.ttf' if bold else 'consola.ttf'
    try:
        return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', name), size)
    except OSError:
        return ImageFont.load_default()


# ------------------------------------------------------------------ building the frames

_concept = {}


def concept_boss(name):
    """The boss's recipe with this pass's hand data on top (a copy: jp_bosses is left as it is)."""
    if name not in _concept:
        _concept[name] = _make_concept_boss(name)
    return _concept[name]


def _make_concept_boss(name):
    b = copy.copy(JB.BOSSES[name])
    h = HAND.get(name, {})
    if h.get('table'):
        t = dict(b.table)
        t.update(C.table(h['table']))
        b.table = t
    fd = copy.deepcopy(b.frame_data)
    for (rel, f), hooks in h.get('hooks', {}).items():
        per = fd.setdefault(rel, {}).setdefault('hooks', {}).setdefault(f, {})
        for hk, at in hooks.items():
            # the boss's own ring for that hook; the back ring (never drawn on a front view) takes the
            # size his other rings are
            st = b.hooks.get(hk, {}).get('stamp') or b.hooks['head']['stamp']
            per[hk] = (at, st)
    for (rel, f), ovs in h.get('overlays', {}).items():
        per = fd.setdefault(rel, {}).setdefault('overlays', {}).setdefault(f, [])
        for name, stamps in ovs:
            per.append({'name': name, 'px': C.merge(*[C.stamp(x, y, rows) for (x, y, rows) in stamps])})
    b.frame_data = fd
    return b


def hand_overlays(bname, rel, f):
    return [name for name, _st in HAND.get(bname, {}).get('overlays', {}).get((rel, f), [])]


_cache = {}


def treated(b, rel, fw, f, skip=()):
    k = (b.name, id(b), rel, f, tuple(sorted(skip)))
    if k not in _cache:
        fh = C.sheet(rel).shape[0]
        src = C.frame(rel, fw, fh, f)
        im, info = C.treat(b, src, TAKE, key_src=b.key_frame(), sheet_rel=rel, frame_no=f, skip_rings=skip)
        info.pop('work', None)
        _cache[k] = (src, im, info)
    return _cache[k]


def anim_frames(rel, fw, anim):
    table = ANIMS.get(rel)
    if table and anim in table:
        return list(table[anim])
    return list(range(C.frames_in(rel, fw)))


def rings_for_rule(info):
    """The rings the all-or-nothing rule weighs: every ring drawn, tracked or set by hand, but the
    back ring, which is only ever drawn (by hand) on a back view, where the strings tie on."""
    return [r for r in info.get('rings_drawn', []) if r != 'back']


def rings_by_tracker(info):
    how = info.get('hook_how', {})
    return [r for r in info.get('rings_drawn', []) if how.get(r) != 'by hand']


def build_pose(bname, pose):
    b = concept_boss(bname)
    rel, fw, f = pose['sheet'], pose['fw'], pose['frame']
    fh = C.sheet(rel).shape[0]
    if pose.get('fx'):
        return build_fx(b, pose)
    frames = anim_frames(rel, fw, pose['anim'])
    found = {}
    for g in frames:
        for r in rings_for_rule(treated(b, rel, fw, g)[2]):
            found[r] = found.get(r, 0) + 1
    keep = {r for r, n in found.items() if n == len(frames)}
    _src, _im, info0 = treated(b, rel, fw, f)
    here = set(rings_for_rule(info0))
    skip = here - keep
    src, im, info = treated(b, rel, fw, f, skip)
    how = info.get('hook_how', {})
    p = {
        'pose': pose, 'boss': bname, 'im': im, 'src': src, 'frame_size': (fw, fh),
        'feet': JB.BOSSES[bname].feet if fw == JB.BOSSES[bname].fw else (fw // 2, fh - 1),
        'back': info['hooks'].get('back'), 'back_how': how.get('back', 'not placed'),
        'back_drawn': how.get('back') == 'by hand',
        'anim_frames': frames, 'rings_found_on_frame': sorted(here), 'rings_kept': sorted(keep & here),
        'rings_left_off': {r: '%d/%d frames' % (found.get(r, 0), len(frames)) for r in sorted(skip)},
        'rings_hand': [r for r, v in how.items() if v == 'by hand' and r in info.get('rings_drawn', [])],
        'rings_missing': [r for r in RING_NAMES if r not in here and r not in how],
        'overlays_hand': hand_overlays(bname, rel, f),
        'parts': {k: bool(v[3]) for k, v in info['parts'].items()},
        'overlays_skipped': [s for s in info['skipped'] if not s.startswith('hook:')],
        'unknown': info['unknown'], 'lint': {k: info['lint'][k] for k in AUDITED},
        'unblack': info['unblack'], 'table_added': {},
        'stats': info['stats'],
    }
    h = HAND.get(bname, {})
    if h.get('table'):
        added = C.table(h['table'])
        used = {hx for hx in added if (src[..., :3].reshape(-1, 3) == [int(hx[i:i + 2], 16) for i in (0, 2, 4)])
                .all(axis=1).any()}
        p['table_added'] = {hx: added[hx] for hx in sorted(used)}
    if pose.get('tint'):
        p['tint'] = pose['tint']
    return p


def build_fx(b, pose):
    """An effect sheet: recoloured by table only (no tracking, no overlays, no keyline pass), its
    authored alpha kept exactly."""
    rel, fw, f = pose['sheet'], pose['fw'], pose['frame']
    fh = C.sheet(rel).shape[0]
    src = C.frame(rel, fw, fh, f)
    t = dict(b.table)
    t.update(C.table(CARTER_CLONE_EYES))
    wk, unknown = C.recolour(src, t)
    im = wk.image(TAKE)
    a = C.np.array(im)
    a[..., 3] = C.np.where(a[..., 3] > 0, src[..., 3], 0)
    im = Image.fromarray(a, 'RGBA')
    keys = set(C.np.unique(wk.key[wk.key != '']).tolist())
    return {
        'pose': pose, 'boss': b.name, 'im': im, 'src': src, 'frame_size': (fw, fh), 'feet': pose['feet'],
        'back': None, 'back_how': 'none (an effect, not a puppet)', 'back_drawn': False, 'fx': True,
        'anim_frames': [f], 'rings_found_on_frame': [], 'rings_kept': [], 'rings_left_off': {},
        'rings_hand': [], 'rings_missing': [], 'parts': {}, 'overlays_skipped': [],
        'unknown': unknown, 'lint': {'bad_keys': sorted(keys - set(PAL.KEYS))},
        'unblack': {}, 'table_added': C.table(CARTER_CLONE_EYES),
        'stats': C.stats_img(im),
        'alpha_kept': sorted({int(v) for v in C.np.unique(src[..., 3]) if v}),
    }


def build_idle(bname):
    b = JB.BOSSES[bname]
    im = Image.open(os.path.join(APPROVAL, bname, '%s_after_B_1x.png' % bname)).convert('RGBA')
    with open(os.path.join(APPROVAL, bname, '%s_hooks.json' % bname)) as fh:
        hk = json.load(fh)['frames'][str(b.idle[0])]
    # the approved pixels, checked against a fresh run of the recipe on the same frame
    _src, again, info = treated(b, b.sheet, b.fw, b.idle[0])
    d = pixel_diff(im, again)
    pose = dict(key='idle', title='Idle (approved, take B)', sheet=b.sheet, fw=b.fw, frame=b.idle[0], anim='idle',
                look='The approved look, exactly: the finale idle frame from the approval pass.')
    return {
        'pose': pose, 'boss': bname, 'im': im, 'src': C.frame(b.sheet, b.fw, b.fh, b.idle[0]),
        'frame_size': (b.fw, b.fh), 'feet': b.feet, 'back': tuple(hk['back']), 'back_how': 'approved',
        'back_drawn': False, 'anim_frames': list(b.idle), 'rings_found_on_frame': sorted(
            r for r in RING_NAMES if r in hk), 'rings_kept': sorted(r for r in RING_NAMES if r in hk),
        'rings_left_off': {}, 'rings_hand': [], 'rings_missing': [], 'parts': {}, 'overlays_skipped': [],
        'unknown': {}, 'lint': {k: [] for k in AUDITED}, 'unblack': {}, 'table_added': {},
        'stats': C.stats_img(im), 'recipe_rerun_identical': d is None,
    }


def audit(p):
    """The twin rule and the palette on a puppet pose (an effect keeps its own authored alpha)."""
    probs = []
    if p['pose'].get('fx'):
        a = C.np.array(p['im'])
        if ((a[..., 3] > 0) != (p['src'][..., 3] > 0)).any():
            probs.append('silhouette differs from the source')
        if (a[..., 3] != p['src'][..., 3]).any():
            probs.append('alpha differs from the source')
        if p['lint']['bad_keys']:
            probs.append('keys off the palette: %s' % p['lint']['bad_keys'])
        if p['unknown']:
            probs.append('unmapped colours %s' % p['unknown'])
        return probs
    for k in AUDITED:
        if p['lint'].get(k):
            probs.append('%d %s %s' % (len(p['lint'][k]), k, p['lint'][k][:4]))
    if p['unknown']:
        probs.append('unmapped colours %s' % p['unknown'])
    a = C.np.array(p['im'])
    if ((a[..., 3] > 0) & (a[..., 3] < 255)).any():
        probs.append('semi-alpha')
    if ((a[..., 3] > 0) != (p['src'][..., 3] > 0)).any():
        probs.append('silhouette differs from the source')
    pal = {tuple(v[:3]) for v in PAL.colours(TAKE).values()}
    cols = {tuple(c) for c in a[a[..., 3] > 0][:, :3].tolist()}
    if cols - pal:
        probs.append('colours off the take-B palette: %d' % len(cols - pal))
    if p['pose']['key'] == 'idle' and not p.get('recipe_rerun_identical', True):
        probs.append('the approved idle no longer matches a fresh run of the recipe')
    return probs


# ------------------------------------------------------------------ notes

def notes_for(p):
    """(kind, text) lines: AUTO (what the recipe carried by itself), HAND (what this pass did by hand),
    SHIP (what shipping this anim would still need), LOOK (the artist's note)."""
    pose, out = p['pose'], []
    if pose['key'] == 'idle':
        out.append(('AUTO', 'rings: %s; back %s (approved hooks)' % (', '.join(p['rings_kept']), list(p['back']))))
        out.append(('LOOK', pose['look']))
        return out
    if p.get('fx'):
        out.append(('AUTO', 'recoloured by his table; alpha as authored (%s)' % ', '.join(map(str, p['alpha_kept']))))
        out.append(('HAND', 'table: the clone\'s red eyes FF4A3C, C01830 -> glow G1, G2 (his aura table has them as flare)'))
        out.append(('LOOK', pose['look']))
        return out
    parts = p['parts']
    face = [o for o in FACE_OVERLAYS if o in JB_OVERLAY_NAMES(p['boss'])]
    face_ok = [o for o in face if o not in p['overlays_skipped']]
    other_skipped = [o for o in p['overlays_skipped'] if o not in FACE_OVERLAYS]
    auto = ['palette + keyline + tatter']
    if face:
        auto.append('face: ' + (', '.join(face_ok) if face_ok else 'overlays sit out (face not the idle face)') +
                    (' (then repainted by hand)' if face_ok and p.get('overlays_hand') else ''))
    if other_skipped:
        auto.append('not placed: ' + ', '.join(other_skipped))
    rings = [r for r in p['rings_kept'] if r not in p['rings_hand']]
    auto.append('rings: ' + (', '.join(rings) if rings else 'none'))
    out.append(('AUTO', '; '.join(auto)))
    how = p['back_how']
    where = 'behind the body, strings under the sprite'
    if p['back_drawn']:
        where = 'ring drawn on his back, strings over the sprite'
    out.append(('AUTO' if how in ('tracked', 'approved') or how.startswith('via') else 'HAND',
                'back %s: %s (%s)' % (list(p['back']) if p['back'] else '-', how if how != 'by hand' else 'set by hand', where)))
    hand = []
    others = [r for r in p['rings_hand'] if r != 'back']
    if others:
        hand.append('ring set by hand on this frame: ' + ', '.join(others))
    if p.get('overlays_hand'):
        hand.append('drawn by hand: ' + ', '.join(p['overlays_hand']))
    if p['table_added']:
        hand.append('table: +' + ', '.join('%s -> %s %s' % (hx, m, k) for hx, (m, k) in p['table_added'].items()))
    if hand:
        out.append(('HAND', '; '.join(hand)))
    ship = []
    if p['rings_left_off']:
        ship.append('left off (not on every frame of %s): %s' % (
            pose['anim'], ', '.join('%s %s' % kv for kv in p['rings_left_off'].items())))
    missing = [r for r in p['rings_missing'] if r not in p['rings_left_off']]
    if missing:
        ship.append('not found: ' + ', '.join(missing))
    if ship:
        out.append(('SHIP', 'rings ' + '; '.join(ship) + ': by hand, or left off'))
    out.append(('LOOK', pose['look']))
    return out


def JB_OVERLAY_NAMES(bname):
    return [o['name'] for o in JB.BOSSES[bname].overlays]


# ------------------------------------------------------------------ drawing

BG = (46, 49, 58, 255)
PANEL_BG = (22, 20, 28, 255)
WHITE = (236, 233, 244, 255)
DIM = (150, 146, 170, 255)
KIND_COL = {'AUTO': (132, 214, 160, 255), 'HAND': (255, 186, 110, 255), 'SHIP': (120, 196, 240, 255),
            'LOOK': (214, 210, 226, 255)}
MARK = (255, 60, 220, 255)


def blue():
    return ST.S.TAKES['blue']


def tinted(im, tint):
    a = C.np.array(im).astype(float)
    a[..., 0] *= tint[0]
    a[..., 1] *= tint[1]
    a[..., 2] *= tint[2]
    a[..., 3] *= tint[3]
    return Image.fromarray(C.np.clip(a + 0.5, 0, 255).astype(C.np.uint8), 'RGBA')


def string_layer(size, hook, top=0):
    """Two blue strings, one texel wide and two apart, from the top of a native-size layer down to
    the hook: glow (added) and core, as jp_staging draws them."""
    T = blue()
    hx, hy = hook
    core, glow = ST.S.string_texels([[(hx - 1, top), (hx - 1, hy)], [(hx + 1, top), (hx + 1, hy)]])
    add = Image.new('RGB', size, (0, 0, 0))
    lay = Image.new('RGBA', size, (0, 0, 0, 0))
    pa, pl = add.load(), lay.load()
    for (x, y) in glow:
        if 0 <= x < size[0] and 0 <= y < size[1]:
            pa[x, y] = T['glow'][:3]
    for (x, y) in core:
        if 0 <= x < size[0] and 0 <= y < size[1]:
            pl[x, y] = T['core']
    return add, lay


def add_rgb(base, add):
    from PIL import ImageChops
    rgb = ImageChops.add(base.convert('RGB'), add)
    out = rgb.convert('RGBA')
    out.putalpha(base.getchannel('A'))
    return out


def figure_box(p):
    """The pose's drawn box, taken over the sprite and the hook, in its frame texels."""
    bb = p['im'].getbbox() or (0, 0, 1, 1)
    if p['back']:
        bx, by = p['back']
        bb = (min(bb[0], bx - 3), min(bb[1], by - 3), max(bb[2], bx + 4), max(bb[3], by + 4))
    return bb


def panel_native(p, top_pad, bottom_pad, side_pad, bg):
    """The pose on a native (1 texel = 1 px) canvas cropped round its figure, the strings drawn from
    the canvas top to the back hook (under the sprite on a front view, over it on a back view).
    Returns (image, hook position on it or None, feet position on it)."""
    bb = figure_box(p)
    fw, fh = p['frame_size']
    fx, fy = p['feet']
    x0 = bb[0] - side_pad
    y0 = bb[1] - top_pad
    x1 = bb[2] + side_pad
    y1 = max(bb[3], fy + 1) + bottom_pad
    W, H = x1 - x0, y1 - y0
    canvas = bg.copy() if isinstance(bg, Image.Image) else Image.new('RGBA', (W, H), bg)
    if canvas.size != (W, H):
        canvas = canvas.crop((0, 0, W, H))
    sprite = p['im'] if not p.get('tint') else tinted(p['im'], p['tint'])
    hook = None
    if p['back'] and not p.get('tint'):
        hook = (p['back'][0] - x0, p['back'][1] - y0)
        add, lay = string_layer((W, H), hook)
        if not p['back_drawn']:
            canvas = add_rgb(canvas, add)
            canvas.alpha_composite(lay)
            canvas.alpha_composite(sprite, (-x0, -y0))
        else:
            canvas.alpha_composite(sprite, (-x0, -y0))
            canvas = add_rgb(canvas, add)
            canvas.alpha_composite(lay)
    else:
        canvas.alpha_composite(sprite, (-x0, -y0))
    return canvas, hook, (fx - x0, fy - y0)


def tile_void(W, H):
    bg = Image.open(VOID_BG).convert('RGBA')
    out = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for yy in range(0, H, bg.height):
        for xx in range(0, W, bg.width):
            out.alpha_composite(bg, (xx, yy))
    return out


def mark(d, hook, s, r=None, label=None, f=None):
    cx, cy = (hook[0] + 0.5) * s, (hook[1] + 0.5) * s
    r = r or max(6, int(2.6 * s))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=MARK, width=2)
    if label and f:
        d.text((cx + r + 4, cy - r - 2), label, fill=MARK, font=f)


def sheet_3x(bname, panels):
    """Game scale on the void: every pose's feet on one floor line, the idle first."""
    s = 3
    gap = 14
    top_pad = 26                                  # texels over the tallest figure, for the titles
    nat = []
    for p in panels:
        bb = figure_box(p)
        nat.append((p, bb))
    above = max(p['feet'][1] - bb[1] for p, bb in nat) + 1
    below = max(bb[3] - (p['feet'][1] + 1) for p, bb in nat)
    below = max(below, 0) + 10
    ft, fs = font(17, True), font(13)
    probe = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    widths = []
    for i, (p, bb) in enumerate(nat):
        t = '%d  %s' % (i, p['pose']['title']) if i else p['pose']['title']
        text_px = max(probe.textlength(t, font=ft), probe.textlength(src_ref(p), font=fs)) + 24
        widths.append(max((bb[2] - bb[0]) + gap, -(-int(text_px) // s)))
    W = sum(widths) + gap
    H = top_pad + above + below
    canvas = tile_void(W, H)
    floor = top_pad + above                       # the feet row's bottom edge
    x = gap
    placed = []
    for (p, bb), w in zip(nat, widths):
        ox = x - bb[0] + (w - (bb[2] - bb[0])) // 2
        oy = floor - (p['feet'][1] + 1)
        sprite = p['im'] if not p.get('tint') else tinted(p['im'], p['tint'])
        hook = None
        if p['back'] and not p.get('tint'):
            hook = (p['back'][0] + ox, p['back'][1] + oy)
            add, lay = string_layer((W, H), hook, top=top_pad - 6)
            if p['back_drawn']:
                canvas.alpha_composite(sprite, (ox, oy))
                canvas = add_rgb(canvas, add)
                canvas.alpha_composite(lay)
            else:
                canvas = add_rgb(canvas, add)
                canvas.alpha_composite(lay)
                canvas.alpha_composite(sprite, (ox, oy))
        else:
            canvas.alpha_composite(sprite, (ox, oy))
        placed.append((p, x, w, hook))
        x += w
    big = canvas.resize((W * s, H * s), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for i, (p, x, w, hook) in enumerate(placed):
        if hook:
            mark(d, hook, s)
        t = '%d  %s' % (i, p['pose']['title']) if i else p['pose']['title']
        d.text((x * s + 4, 8), t, fill=WHITE, font=ft)
        d.text((x * s + 4, 30), src_ref(p), fill=DIM, font=fs)
    head = ['%s as Jordan\'s puppet: concept poses at GAME SCALE (3x), take B.' % JB.BOSSES[bname].title,
            'Magenta ring: the BACK hook the two blue strings tie to (behind the body on front views).']
    out = Image.new('RGBA', (big.width, big.height + 52), PANEL_BG)
    out.alpha_composite(big, (0, 52))
    dd = ImageDraw.Draw(out)
    dd.text((8, 6), head[0], fill=WHITE, font=font(16, True))
    dd.text((8, 28), head[1], fill=DIM, font=font(14))
    return out


def src_ref(p):
    pose = p['pose']
    fr = p['anim_frames']
    span = ('%d-%d' % (fr[0], fr[-1])) if len(fr) > 1 and fr == list(range(fr[0], fr[-1] + 1)) else \
        ','.join(map(str, fr))
    return '%s f%d  (%s %s)' % (os.path.basename(pose['sheet']), pose['frame'], pose['anim'], span)


def sheet_6x(bname, panels, cols):
    s = 6
    pads = (4, 4, 4)
    tiles = []
    for i, p in enumerate(panels):
        nat, hook, _feet = panel_native(p, pads[0], pads[1], pads[2], BG)
        big = nat.resize((nat.width * s, nat.height * s), Image.NEAREST)
        d = ImageDraw.Draw(big)
        if hook:
            mark(d, hook, s)
        tiles.append((p, big, i))
    colw = max(t[1].width for t in tiles)
    colw = max(colw, 520)
    fnote = font(15)
    ftitle = font(20, True)
    fref = font(15)
    chars = max(40, (colw - 16) // 8)
    blocks = []
    for p, big, i in tiles:
        lines = []
        for kind, text in notes_for(p):
            wrapped = textwrap.wrap(text, chars - 6)
            for j, ln in enumerate(wrapped):
                lines.append((kind if j == 0 else '', ln, KIND_COL[kind]))
        blocks.append((p, big, i, lines))
    rows = [blocks[k:k + cols] for k in range(0, len(blocks), cols)]
    row_imgs = []
    for row in rows:
        h_img = max(b[1].height for b in row)
        h_txt = max(len(b[3]) for b in row) * 19 + 12
        tile_h = 58 + h_img + h_txt
        row_im = Image.new('RGBA', (cols * (colw + 16) + 16, tile_h), PANEL_BG)
        d = ImageDraw.Draw(row_im)
        for c, (p, big, i, lines) in enumerate(row):
            x = 16 + c * (colw + 16)
            title = '%d  %s' % (i, p['pose']['title']) if i else p['pose']['title']
            d.text((x, 8), title, fill=WHITE, font=ftitle)
            d.text((x, 33), src_ref(p), fill=DIM, font=fref)
            row_im.alpha_composite(big, (x + (colw - big.width) // 2, 58 + (h_img - big.height)))
            y = 58 + h_img + 8
            for kind, ln, col in lines:
                if kind:
                    d.text((x, y), kind, fill=col, font=font(15, True))
                d.text((x + 48, y), ln, fill=col, font=fnote)
                y += 19
        row_imgs.append(row_im)
    head = Image.new('RGBA', (row_imgs[0].width, 40), PANEL_BG)
    ImageDraw.Draw(head).text((16, 10), '%s: concept poses at 6x, take B, with what the recipe carried (AUTO), '
                                        'what was done by hand here (HAND) and what shipping would still need (SHIP).' %
                              JB.BOSSES[bname].title, fill=WHITE, font=font(17, True))
    W = max(r.width for r in row_imgs)
    H = head.height + sum(r.height + 10 for r in row_imgs)
    out = Image.new('RGBA', (W, H), PANEL_BG)
    out.alpha_composite(head, (0, 0))
    y = head.height
    for r in row_imgs:
        out.alpha_composite(r, (0, y))
        y += r.height + 10
    return out


def strip_1x(bname, panels):
    """The treated frames, one cell each at the boss's frame size (the clone's smaller frame stands on
    the same feet anchor): what an artist would open to keep working."""
    b = JB.BOSSES[bname]
    cw, ch = b.fw, b.fh
    for p in panels:
        cw, ch = max(cw, p['frame_size'][0]), max(ch, p['frame_size'][1])
    fx, fy = b.feet
    out = Image.new('RGBA', (cw * len(panels), ch), (0, 0, 0, 0))
    cells = []
    for i, p in enumerate(panels):
        ox = i * cw + fx - p['feet'][0]
        oy = fy - p['feet'][1]
        out.alpha_composite(p['im'], (ox, oy))
        cells.append({'cell': i, 'pose': p['pose']['key'], 'sheet': p['pose']['sheet'], 'frame': p['pose']['frame'],
                      'offset_in_cell': [ox - i * cw, oy]})
    return out, (cw, ch), cells


# ------------------------------------------------------------------ the mocks (staging option B)

def mock(spec, poses):
    s = 2
    cv = ST.Canvas(s)
    cv.blit(ST.void(s), s, (0, 0))
    god, aura, tips = ST.god_frame('control', 1)
    tl = ST.god_tl()
    core = (tl[0] + (ST.L.CORE[0] + 0.5) * ST.GOD_SCALE, tl[1] + (ST.L.CORE[1] + 0.5) * ST.GOD_SCALE)
    cv.blit(ST.RU.frame_image(5), ST.GOD_SCALE, (core[0] - 96 * ST.GOD_SCALE, core[1] - 96 * ST.GOD_SCALE))
    cv.blit(god, ST.GOD_SCALE, tl)
    cv.add(aura, ST.GOD_SCALE, (tl[0] - ST.G.AURA_PAD * ST.GOD_SCALE, tl[1]))
    strings, knots, info = [], [], {}
    placed = []
    for bname, key, feet, hand, flip in spec['puppets']:
        p = poses[bname][key]
        im, fx, bk = p['im'], p['feet'], p['back']
        fw = p['frame_size'][0]
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            fx = (fw - 1 - fx[0], fx[1])
            bk = (fw - 1 - bk[0], bk[1])
        ftl = ST.feet_tl(feet, fx, s)
        hk = (ftl[0] + (bk[0] + 0.5) * s, ftl[1] + (bk[1] + 0.5) * s)
        tp = ST.tips_px(tips, hand, (2, 3))
        lens = []
        for j, p0 in enumerate(tp):
            end = (hk[0] + (j - 0.5) * 2 * s, hk[1])
            strings.append(ST.S.curve(p0, end, 0.7))
            knots.append(p0)
            lens.append(((end[0] - p0[0]) ** 2 + (end[1] - p0[1]) ** 2) ** 0.5)
        placed.append((feet[1], bname, im, ftl))
        # how much of him lands on Jordan (any shipped frame of his) and on the HUD
        big = im.getchannel('A').resize((im.width * s, im.height * s), Image.NEAREST)
        layer = Image.new('L', ST.SCREEN, 0)
        layer.paste(big, (int(ftl[0]), int(ftl[1])))
        from PIL import ImageChops
        over = ImageChops.multiply(layer, ST.god_mask()).getbbox()
        bb = im.getbbox()
        box = (ftl[0] + bb[0] * s, ftl[1] + bb[1] * s, ftl[0] + bb[2] * s, ftl[1] + bb[3] * s)
        hud = [h for h in ST.HUD if box[0] < h[0] + h[2] and h[0] < box[2] and box[1] < h[1] + h[3] and h[1] < box[3]]
        info[bname] = {'pose': key, 'sheet': p['pose']['sheet'], 'frame': p['pose']['frame'], 'mirrored': flip,
                       'feet_screen': list(feet), 'feet_world': list(to_world(feet)),
                       'back_hook_screen': [round(hk[0], 1), round(hk[1], 1)],
                       'back_hook_world': [round(v, 1) for v in to_world(hk)],
                       'hand': hand, 'fingertips': [[round(v, 1) for v in q] for q in tp],
                       'string_px': [round(v) for v in lens], 'box_screen': [round(v) for v in box],
                       'overlaps_jordan': over is not None, 'under_hud': hud}
    cv.strings(strings, knots, s)
    px, py = PLAYER_AT
    items = [(py + 0.1, 'player', None, None)] + [(y + 0.2, n, im, t) for (y, n, im, t) in placed]
    for _y, kind, im, t in sorted(items, key=lambda it: it[0]):
        if kind == 'player':
            cv.blit(ST.player_up(), s, (px - 16 * s, py - 29 * s))
        else:
            cv.blit(im, s, t)
    out = cv.im
    d = ImageDraw.Draw(out)
    # the notes stay in the top-left corner, clear of Jordan (his box starts at x 646)
    d.text((24, 18), 'CONCEPT: DISPLAY PAIRING ONLY', fill=WHITE, font=font(22, True))
    d.text((24, 46), 'no attack is designed here', fill=WHITE, font=font(16, True))
    y = 74
    for ln in wrap_px(d, 'Staging option B (approved): camera zoom 2/3, world = screen x 1.5 + (-480, -6). '
                         'Jordan at world (960, 600) = screen (960, 404) at 2x; the puppets\' 3x sprites show '
                         'at 2 px a texel. Blue strings, two per puppet, tie on at the BACK hook only: on these '
                         'front views it is behind the body, so the strings run under the sprite.',
                      font(14), 590):
        d.text((24, y), ln, fill=DIM, font=font(14))
        y += 19
    for k, ln in enumerate(spec['caption']):
        w = d.textlength(ln, font=font(16))
        d.text(((1920 - w) / 2, 1012 + 24 * k), ln, fill=WHITE, font=font(16))
    info['player_feet_screen'] = list(PLAYER_AT)
    return out, info


def wrap_px(d, text, f, width):
    lines, cur = [], ''
    for word in text.split():
        cand = (cur + ' ' + word).strip()
        if d.textlength(cand, font=f) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def to_world(p):
    return (p[0] * 1.5 - 480, p[1] * 1.5 - 6)


# ------------------------------------------------------------------ the ship-later survey

def survey(bname):
    """Every frame of the body sheets he would need, run through the recipe as it stands (no hand
    data): per anim, which rings the tracker keeps on every frame, where the back point comes from,
    whether the face overlays land, and any colour his table lacks. And the effect/prop sheets'
    colours against his table."""
    b = JB.BOSSES[bname]
    out = {'sheets': {}, 'props': {}}
    for rel, fw in SURVEY[bname]:
        n = C.frames_in(rel, fw)
        anims = ANIMS.get(rel) or {os.path.splitext(os.path.basename(rel))[0]: range(n)}
        per = {}
        for anim, frames in anims.items():
            frames = list(frames)
            found, back, face_out, unknown, lint = {}, {}, 0, {}, 0
            for f in frames:
                _src, _im, info = treated(b, rel, fw, f)
                for r in rings_by_tracker(info):
                    found[r] = found.get(r, 0) + 1
                hb = info.get('hook_how', {}).get('back', 'none')
                back[hb] = back.get(hb, 0) + 1
                if any(o in info['skipped'] for o in FACE_OVERLAYS if o in JB_OVERLAY_NAMES(bname)):
                    face_out += 1
                for hx, k in info['unknown'].items():
                    unknown[hx] = unknown.get(hx, 0) + k
                lint += sum(len(info['lint'][k]) for k in AUDITED)
            per[anim] = {
                'frames': frames,
                'rings_kept': sorted(r for r, k in found.items() if k == len(frames)),
                'rings_partial': {r: '%d/%d' % (k, len(frames)) for r, k in sorted(found.items()) if k < len(frames)},
                'back': back, 'face_overlays_out_on': face_out, 'unmapped': unknown, 'audit_issues': lint,
            }
        out['sheets'][rel] = {'frame_width': fw, 'frames': n, 'anims': per}
    for rel in PROPS[bname]:
        a = C.sheet(rel)
        op = a[..., 3] > 0
        cols = {}
        for px in a[op]:
            hx = C.hexof(px)
            cols[hx] = cols.get(hx, 0) + 1
        t = b.table_for(rel)
        unk = {hx: k for hx, k in sorted(cols.items(), key=lambda kv: -kv[1]) if hx not in t}
        semi = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())
        out['props'][rel] = {'colours': len(cols), 'unmapped': unk, 'semi_alpha_px': semi}
    return out


# ------------------------------------------------------------------ writing

def aseprite(*args):
    subprocess.run([C.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def save_strip(im, path):
    """PNG + .aseprite beside it, the .aseprite round-tripped and compared pixel for pixel."""
    base = os.path.splitext(path)[0]
    im.save(path)
    aseprite(path, '--save-as', base + '.aseprite')
    back = base + '_roundtrip.png'
    aseprite(base + '.aseprite', '--save-as', back)
    d = pixel_diff(Image.open(path), Image.open(back))
    os.remove(back)
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (os.path.basename(path), d))


def build_all(do_survey=True):
    poses, problems, notes = {}, [], {'take': TAKE, 'bosses': {}, 'mocks': {}}
    for bname in BOSS_ORDER:
        panels = [build_idle(bname)] + [build_pose(bname, pose) for pose in POSES[bname]]
        poses[bname] = {p['pose']['key']: p for p in panels}
        for p in panels:
            for pr in audit(p):
                problems.append('%s %s: %s' % (bname, p['pose']['key'], pr))
        notes['bosses'][bname] = {'poses': [pose_record(p) for p in panels]}
        if do_survey:
            notes['bosses'][bname]['ship_later'] = survey(bname)
    return poses, problems, notes


def pose_record(p):
    pose = p['pose']
    return {
        'key': pose['key'], 'title': pose['title'], 'sheet': 'res://Assets/Characters/' + pose['sheet'],
        'frame': pose['frame'], 'anim': pose['anim'], 'anim_frames': p['anim_frames'],
        'frame_size': list(p['frame_size']), 'feet': list(p['feet']),
        'back': list(p['back']) if p['back'] else None, 'back_how': p['back_how'], 'back_ring_drawn': p['back_drawn'],
        'rings_drawn': p['rings_kept'] + p['rings_hand'], 'rings_left_off': p['rings_left_off'],
        'rings_not_found': p['rings_missing'], 'overlays_skipped': p['overlays_skipped'],
        'table_added': {k: list(v) for k, v in p['table_added'].items()}, 'unmapped': p['unknown'],
        'tint_in_code': list(p['tint']) if p.get('tint') else None,
        'colours': p['stats']['colours'], 'semi_alpha_px': p['stats']['semi'],
        'notes': [[k, t] for k, t in notes_for(p)],
    }


def write(poses, notes):
    tmp_ok = []
    cols = {'eric': 3, 'mason': 4, 'josh': 3, 'carter': 3}
    for bname in BOSS_ORDER:
        panels = list(poses[bname].values())
        sheet_3x(bname, panels).save(os.path.join(HERE, '%s_concept_3x.png' % bname))
        sheet_6x(bname, panels, cols[bname]).save(os.path.join(HERE, '%s_concept_6x.png' % bname))
        strip_panels = [p for p in panels if not p.get('tint')]
        strip, cell, cells = strip_1x(bname, strip_panels)
        save_strip(strip, os.path.join(HERE, '%s_poses_1x.png' % bname))
        notes['bosses'][bname]['strip'] = {'file': '%s_poses_1x.png' % bname, 'cell': list(cell),
                                           'feet_in_cell': list(JB.BOSSES[bname].feet), 'cells': cells}
        tmp_ok.append(bname)
    for spec in MOCKS:
        im, info = mock(spec, poses)
        im.save(os.path.join(HERE, spec['name'] + '.png'))
        notes['mocks'][spec['name']] = info
    with open(os.path.join(HERE, 'notes.json'), 'w') as fh:
        json.dump(notes, fh, indent=1, default=list)
    return tmp_ok


def report(poses, problems, notes):
    for bname in BOSS_ORDER:
        print('== %s' % bname)
        for p in poses[bname].values():
            print('  %-13s %s' % (p['pose']['key'], src_ref(p)))
            for kind, text in notes_for(p):
                print('      %-4s %s' % (kind, text))
        sl = notes['bosses'][bname].get('ship_later')
        if sl:
            for rel, s in sl['sheets'].items():
                print('  ship-later %s (%d frames)' % (rel, s['frames']))
                for anim, a in s['anims'].items():
                    print('      %-20s rings kept %-28s partial %-40s back %s face-out %d unmapped %s issues %d' % (
                        anim, ','.join(a['rings_kept']) or '-', a['rings_partial'] or '-', a['back'],
                        a['face_overlays_out_on'], dict(list(a['unmapped'].items())[:4]) or '-', a['audit_issues']))
            for rel, pr in sl['props'].items():
                print('  prop %-36s colours %3d unmapped %3d semi %d' % (rel, pr['colours'], len(pr['unmapped']), pr['semi_alpha_px']))
    print('problems: %d' % len(problems))
    for pr in problems:
        print('  ' + pr)


def main(argv):
    if not argv or argv[0] not in ('--check', '--write'):
        print(__doc__)
        return 2
    writing = argv[0] == '--write'
    aseprite_path = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
    install_guard(HERE if writing else None, aseprite_path)
    load()
    if _real(C.ASEPRITE) != _real(aseprite_path):
        raise SystemExit('Aseprite path mismatch: %s vs %s' % (C.ASEPRITE, aseprite_path))
    poses, problems, notes = build_all(do_survey='--no-survey' not in argv)
    report(poses, problems, notes)
    if problems:
        print('not writing: fix the problems first' if writing else '')
        return 1
    if writing:
        write(poses, notes)
        print('wrote into %s' % HERE)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
