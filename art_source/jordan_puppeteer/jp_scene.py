"""Compose the previews on the game's own grid: 640x360 texels, every layer at 1 texel = 3 screen
px, so the mock's pixels line up exactly as the game draws them (scale 3, nearest).

Staging, per the build plan (jordan_puppet_master/PLAN.md): Jordan on the finale's GOD_POINT
(960, 600) px. Attack 1: Greyson's feet at (864, 416) on the left hand, Matt's at (1248, 416) on
the right. Attack 2: Captain Burak's at (640, 440) on the left hand, Danny's at (1300, 440) on
the right. The player at the bottom centre. The puppets are PLACEHOLDERS (greyed approved idles).

Two strings per puppet (the plan's default): from two claw points of its hand to its back hook -
the inner pair (index, middle) for a puppet under or inside its hand, the outer pair (ring,
little) for one further out. They draw behind the puppets, so they vanish behind the head and
shoulders on the way to the hook.

Layer order: void, rune circle, god, aura (added), strings (glow added, core opaque), rift backs,
puppets (clipped at their rift's anchor row while in it), rift glows (added), rift fronts, player.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import jp_anims as A  # noqa: E402
import jp_puppets as PP  # noqa: E402
import jp_rift as RF  # noqa: E402
import jp_rig as R  # noqa: E402
import jp_strings as S  # noqa: E402
import jg_base as B  # noqa: E402
import jg_god as G  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_runes as RU  # noqa: E402
import jg_void as V  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

SCALE = 3
NATIVE = (640, 360)
GOD_POINT = (960, 600)                     # px: the anchor texel's top-left corner goes here
GOD_TL = (GOD_POINT[0] // SCALE - A.ANCHOR[0], GOD_POINT[1] // SCALE - A.ANCHOR[1])     # (160, -23)
FEET_PX = {'greyson': (864, 416), 'matt': (1248, 416), 'captain_burak': (640, 440), 'danny': (1300, 440)}
PUPPET_FEET = {k: (int(round(x / SCALE)), int(round(y / SCALE))) for k, (x, y) in FEET_PX.items()}
HAND_OF = {'greyson': 'left', 'matt': 'right', 'captain_burak': 'left', 'danny': 'right'}
DIGIT_ORDER = ('index', 'middle', 'ring', 'little', 'thumb')
PAIRS = {'inner': (0, 1), 'outer': (2, 3)}
HOOK_SPREAD = 1.5                          # texels between neighbouring strings' ends on the back hook
PLAYER_FEET = (320, 334)                   # bottom centre

_cache = {}


def _cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


ANIMS = {a[0]: a for a in A.anims()}


def god_frame(anim, i):
    """(image, aura image, tips, tension) for an anim key ('control', 'summon_both', 'yank_right',
    'hit', ...) and frame."""
    def make():
        key, stem, n, times, loop, fn, phase = ANIMS[anim]
        px, tips, ten, fx = fn(i)
        im = R.image(px)
        au = B.image(A.aura_px(px, phase(i)), G.AURA_W, G.AURA_H, G.AURA)
        return im, au, tips, ten
    return _cached(('god', anim, i), make)


def rift_frame(seq, k, prof):
    def make():
        specs = RF.SEQS[seq][0]()
        P = RF.PROFILES[prof]
        b, f, g = RF.frame(specs[k], P)
        return (B.image(b, P.W, P.H, RF.PAL), B.image(f, P.W, P.H, RF.PAL), B.image(g, P.W, P.H, RF.GLOW_PAL))
    return _cached(('rift', seq, k, prof), make)


def rune_frame(i):
    return _cached(('runes', i % RU.FRAMES), lambda: RU.frame_image(i % RU.FRAMES))


def backdrop():
    return _cached('void', V.backdrop)


def placeholder(name):
    return _cached(('pup', name), lambda: PP.placeholder(name))


def player_cell():
    return _cached('player', lambda: Image.open(B.PLAYER_PNG).convert('RGBA').crop((0, 0, 32, 32)))


def _add(native, layer, at):
    """Add `layer` (RGBA, opaque colours) onto native at `at`, additively."""
    tmp = Image.new('RGB', native.size, (0, 0, 0))
    tmp.paste(layer.convert('RGB'), at, layer)
    out = ImageChops.add(native.convert('RGB'), tmp).convert('RGBA')
    native.paste(out)


def _paste_clipped(native, im, at):
    """alpha_composite that tolerates a layer hanging off the canvas."""
    x, y = at
    x0, y0 = max(0, -x), max(0, -y)
    if x0 >= im.width or y0 >= im.height:
        return
    part = im.crop((x0, y0, im.width, im.height))
    native.alpha_composite(part, (x + x0, y + y0))


def string_pair(name, tips_side, hook_at):
    """The two claw points a puppet's strings leave from: the outer pair if its hook lies further
    from his centre line than the hand's claws, else the inner pair."""
    xs = [tips_side[d][0] for d in DIGIT_ORDER[:4]]
    mid = sum(xs) / 4.0 + GOD_TL[0]
    centre = GOD_TL[0] + 159.5
    outward = abs(hook_at[0] - centre) > abs(mid - centre)
    return PAIRS['outer' if outward else 'inner']


def compose(god=('control', 0), runes=0, take='red', puppets=(), player=True):
    """puppets: [{'name', 'rise' (1 standing .. 0 one height under the floor; None absent), 'lift'
    (texels off the floor, a hop), 'rift': (seq, frame) or None, 'strings': bool, 'n': 2 or 5,
    'tension': float or None (the anim's), 'bow', 'wave' (a limp string's ripple), 'pulse': 0..1
    (a bead running from the hook up to the claw)}]. Returns the native RGBA frame."""
    native = backdrop().copy()
    tl = GOD_TL
    im, au, tips, ten = god_frame(*god)
    rf = rune_frame(runes)
    cx, cy = tl[0] + L.CORE[0], tl[1] + L.CORE[1]
    _paste_clipped(native, rf, (int(round(cx - 95.5)), int(round(cy - 95.5))))
    _paste_clipped(native, im, tl)
    _add(native, au, (tl[0] - G.AURA_PAD, tl[1]))
    placed = []
    for p in puppets:
        if p.get('rise') is None:
            placed.append(None)
            continue
        img, feet, hook = placeholder(p['name'])
        fx, fy = PUPPET_FEET[p['name']]
        depth = int(round((1.0 - p['rise']) * img.height)) - int(round(p.get('lift', 0)))
        top_left = (fx - feet[0], fy + depth - feet[1])
        hook_at = (top_left[0] + hook[0], top_left[1] + hook[1])
        placed.append((img, feet, top_left, hook_at, depth))
    # strings (behind the puppets, in front of the god)
    for p, pl in zip(puppets, placed):
        if not p.get('strings') or pl is None:
            continue
        side = HAND_OF[p['name']]
        t = p.get('tension')
        t = ten[side] if t is None else t
        hook_at = pl[3]
        if p.get('n', 2) == 2:
            idx = string_pair(p['name'], tips[side], hook_at)
        else:
            idx = tuple(range(5))
        strings, knots, beads = [], [], []
        for j, k in enumerate(idx):
            tx, ty = tips[side][DIGIT_ORDER[k]]
            p0 = (tl[0] + tx, tl[1] + ty)
            off = (j - (len(idx) - 1) / 2.0) * HOOK_SPREAD * (2.5 if len(idx) == 2 else 1.0)
            end = (hook_at[0] + off, hook_at[1])
            bow = p.get('bow', 0.0) * (1 if j % 2 else -1)
            pts = S.curve(p0, end, t, bow=bow, wave=p.get('wave', 0.0), phase=j * 1.3)
            if p.get('rift'):
                floor = PUPPET_FEET[p['name']][1]
                pts = [q for q in pts if q[1] <= floor]          # a puppet in its rift: the strings go under
            if len(pts) > 1:
                strings.append(pts)
                if p.get('pulse') is not None:
                    u = 1.0 - p['pulse']                          # the bead climbs from the hook
                    q = pts[min(len(pts) - 1, int(round(u * (len(pts) - 1))))]
                    beads.append((int(round(q[0])), int(round(q[1]))))
            knots.append((int(round(p0[0])), int(round(p0[1]))))
        S.draw(native, strings, take, knots=knots, beads=beads)
    # rift backs
    for p in puppets:
        if p.get('rift'):
            prof = PP.PUPPETS[p['name']]['rift']
            P = RF.PROFILES[prof]
            b, f, g = rift_frame(p['rift'][0], p['rift'][1], prof)
            fx, fy = PUPPET_FEET[p['name']]
            _paste_clipped(native, b, (fx - P.ANCHOR[0], fy - P.ANCHOR[1]))
    # puppets, clipped at the floor while they are in a rift
    for p, pl in zip(puppets, placed):
        if pl is None:
            continue
        img, feet, top_left, hook_at, depth = pl
        rows = img.height - depth if (p.get('rift') and depth > 0) else img.height
        if rows <= 0:
            continue
        _paste_clipped(native, img.crop((0, 0, img.width, rows)), top_left)
    # rift glows (added) and fronts
    for p in puppets:
        if p.get('rift'):
            prof = PP.PUPPETS[p['name']]['rift']
            P = RF.PROFILES[prof]
            b, f, g = rift_frame(p['rift'][0], p['rift'][1], prof)
            fx, fy = PUPPET_FEET[p['name']]
            _add(native, g, (fx - P.ANCHOR[0], fy - P.ANCHOR[1]))
    for p in puppets:
        if p.get('rift'):
            prof = PP.PUPPETS[p['name']]['rift']
            P = RF.PROFILES[prof]
            b, f, g = rift_frame(p['rift'][0], p['rift'][1], prof)
            fx, fy = PUPPET_FEET[p['name']]
            _paste_clipped(native, f, (fx - P.ANCHOR[0], fy - P.ANCHOR[1]))
    if player:
        _paste_clipped(native, player_cell(), (PLAYER_FEET[0] - 16, PLAYER_FEET[1] - 31))
    return native


def screen(native):
    return native.resize((NATIVE[0] * SCALE, NATIVE[1] * SCALE), Image.NEAREST)
