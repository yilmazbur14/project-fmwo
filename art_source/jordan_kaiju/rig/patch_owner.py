import os
HERE = os.path.dirname(os.path.abspath(__file__))


def sub(path, old, new, count=1):
    p = os.path.join(HERE, path)
    s = open(p).read()
    if old not in s:
        raise SystemExit('not found in %s: %r' % (path, old[:80]))
    s = s.replace(old, new, count)
    open(p, 'w').write(s)


# owner tracking in KCanvas
sub('kjr.py', """class KCanvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def inb(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, cast=2, floor=None):""", """class KCanvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}
        self.owner = {}

    def inb(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, cast=2, floor=None, owner=None):""")
sub('kjr.py', """        for q in ring:
            if self.inb(q) and (floor is None or q[1] <= floor):
                self.px[q] = 'k'
        for q, k in part.items():
            if self.inb(q):
                self.px[q] = k


#PART SPECS""", """        for q in ring:
            if self.inb(q) and (floor is None or q[1] <= floor):
                self.px[q] = 'k'
                self.owner[q] = None
        for q, k in part.items():
            if self.inb(q):
                self.px[q] = k
                self.owner[q] = owner


#PART SPECS""")
sub('kjr.py', """def gloss(rig, px, skip_bones=()):
    if rig.sc < 0.5 * BASE_SC:
        return
    for b, pts in GLOSS:
        if b in skip_bones:
            continue
        for (x, y) in rig.tline(b, pts):
            if px.get((x, y)) in ('@', '+', '=', '&'):
                px[(x, y)] = '~'
            q = (x, y + 1)
            if px.get(q) in ('@', '+', '&'):
                px[q] = '='""", """# which part each detail line belongs to (it is only drawn where that part shows)
GLOSS_OWNER = ['near_leg', 'chest', 'chest', 'head', 'head', 'tail_back', 'n_upper', 'belly']
CREASE_OWNER = ['near_leg', 'far_leg']
FOLD_OWNER = ['chest', 'chest', 'n_fore', 'tail_front', 'tail_front', 'tail_front']


def _ok(owner, q, want):
    return owner is None or want is None or owner.get(q) == want


def gloss(rig, px, skip_bones=(), owner=None):
    if rig.sc < 0.5 * BASE_SC:
        return
    for (b, pts), want in zip(GLOSS, GLOSS_OWNER):
        if b in skip_bones:
            continue
        for (x, y) in rig.tline(b, pts):
            if px.get((x, y)) in ('@', '+', '=', '&') and _ok(owner, (x, y), want):
                px[(x, y)] = '~'
            q = (x, y + 1)
            if px.get(q) in ('@', '+', '&') and _ok(owner, q, want):
                px[q] = '='""")
sub('kjr.py', """def lines_k(rig, px, table, skip_bones=(), min_sc=0.5, any_key=False):
    if rig.sc < min_sc * BASE_SC:
        return
    for b, pts in table:
        if b in skip_bones:
            continue
        for q in rig.tline(b, pts):
            if px.get(q) not in (None, 'k') and (any_key or px.get(q) in ('#', '%', '&', '@', '+', '=', '~')):
                px[q] = 'k'""", """def lines_k(rig, px, table, skip_bones=(), min_sc=0.5, any_key=False, owner=None, owners=None):
    if rig.sc < min_sc * BASE_SC:
        return
    for i, (b, pts) in enumerate(table):
        if b in skip_bones:
            continue
        want = owners[i] if owners else None
        for q in rig.tline(b, pts):
            if px.get(q) not in (None, 'k') and (any_key or px.get(q) in ('#', '%', '&', '@', '+', '=', '~')) \\
                    and _ok(owner, q, want):
                px[q] = 'k'""")

p = os.path.join(HERE, 'kjr.py')
s = open(p).read()
s += '''

def remove_islands(px, keep=(), min_size=14):
    """Drop small loose clumps (8-connected) that a floor clip or a buried part can leave behind;
    `keep` pixels (effects) are left alone and do not count."""
    seen = set()
    drop = []
    for q in list(px):
        if q in seen or q in keep:
            continue
        comp, stack = [], [q]
        seen.add(q)
        while stack:
            c = stack.pop()
            comp.append(c)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (c[0] + dx, c[1] + dy)
                    if n in px and n not in seen and n not in keep:
                        seen.add(n)
                        stack.append(n)
        if len(comp) < min_size:
            drop.extend(comp)
    for q in drop:
        del px[q]
    return drop


def tail_ground(pose, base_y=163.0):
    """Keep the tail's forward curl lying on the mat however the hips move: turn the tail root (t1,
    on top of any turn the pose already gives it) until the curl's start sits back on its rest height,
    then turn the curl (t3) level again."""
    extra1 = pose.get('t1', (0.0, 0.0, 0.0))[0]
    extra3 = pose.get('t3', (0.0, 0.0, 0.0))[0]
    p3 = BONES['t3'][1]

    def y_at(a):
        q = dict(pose)
        q['t1'] = (extra1 + a, 0.0, 0.0)
        return Rig(q).W('t2', p3)[1]
    lo, hi = -80.0, 80.0
    f_lo, f_hi = y_at(lo) - base_y, y_at(hi) - base_y
    if f_lo * f_hi > 0:
        a = lo if abs(f_lo) < abs(f_hi) else hi
    else:
        for _ in range(40):
            mid = (lo + hi) / 2.0
            fm = y_at(mid) - base_y
            if (fm > 0) == (f_hi > 0):
                hi, f_hi = mid, fm
            else:
                lo, f_lo = mid, fm
        a = (lo + hi) / 2.0
    pose['t1'] = (extra1 + a, 0.0, 0.0)
    rot2 = Rig(pose).rot['t2']
    pose['t3'] = (extra3 - rot2, 0.0, 0.0)
    return pose
'''
open(p, 'w').write(s)

# render: owners on stamps
sub('kjr_render.py', """    def stamp(spec, cast=2, fl='sole', **kw):
        part, _ = shaded(rig, rest, spec, **kw)
        cv.stamp(part, cast=cast, floor=sole if fl == 'sole' else fl)
        return part""", """    def stamp(spec, cast=2, fl='sole', owner=None, **kw):
        part, _ = shaded(rig, rest, spec, **kw)
        cv.stamp(part, cast=cast, floor=sole if fl == 'sole' else fl, owner=owner)
        return part""")
sub('kjr_render.py', "    stamp(R.TAIL_BACK, seed=3)", "    stamp(R.TAIL_BACK, seed=3, owner='tail_back')")
sub('kjr_render.py', "    stamp(R.FAR_LEG, bias=-0.14, seed=5, bounce=0.2)",
    "    stamp(R.FAR_LEG, bias=-0.14, seed=5, bounce=0.2, owner='far_leg')")
sub('kjr_render.py', "    ff = stamp(R.FAR_FOOT, bias=-0.12, bounce=0.2)",
    "    ff = stamp(R.FAR_FOOT, bias=-0.12, bounce=0.2, owner='far_foot')")
sub('kjr_render.py', """        R.belly(rig, torso, tinfo)
        cv.stamp(torso, floor=sole)""", """        R.belly(rig, torso, tinfo)
        cv.stamp(torso, floor=sole, owner='belly' if spec is R.BELLY else 'chest')""")
sub('kjr_render.py', """    cv.stamp(nl, floor=sole)
    stamp(R.NEAR_FOOT, bounce=0.2)""", """    cv.stamp(nl, floor=sole, owner='near_leg')
    stamp(R.NEAR_FOOT, bounce=0.2, owner='near_foot')""")
sub('kjr_render.py', "    cv.stamp(tf, floor=tail_floor)", "    cv.stamp(tf, floor=tail_floor, owner='tail_front')")
sub('kjr_render.py', """        cv.stamp(hd, floor=sole)
        fx |= R.mouth""", """        cv.stamp(hd, floor=sole, owner='head')
        fx |= R.mouth""")
sub('kjr_render.py', """    cv.stamp(up, floor=sole)
    stamp(R.N_FORE, bias=0.02, cast=1, bounce=0.2)""", """    cv.stamp(up, floor=sole, owner='n_upper')
    stamp(R.N_FORE, bias=0.02, cast=1, bounce=0.2, owner='n_fore')""")
sub('kjr_render.py', """    R.gloss(rig, cv.px, skip)
    R.lines_k(rig, cv.px, R.KNEE_CREASES, skip, any_key=True)
    R.lines_k(rig, cv.px, R.FOLDS, skip)""", """    R.gloss(rig, cv.px, skip, owner=cv.owner)
    R.lines_k(rig, cv.px, R.KNEE_CREASES, skip, any_key=True, owner=cv.owner, owners=R.CREASE_OWNER)
    R.lines_k(rig, cv.px, R.FOLDS, skip, owner=cv.owner, owners=R.FOLD_OWNER)""")
sub('kjr_render.py', """            if ch != '.' and cv.px.get(q) not in (None, 'k'):
                cv.px[q] = ch


def _star_sole""", """            if ch != '.' and cv.px.get(q) not in (None, 'k') and cv.owner.get(q) == 'far_foot':
                cv.px[q] = ch


def _star_sole""")
sub('kjr_render.py', """    fx |= R.close_holes(cv.px)
    fx = {q for q in fx if q in cv.px and cv.px[q] in FX_KEYS}
    info = anchors(rig, cv.px, groups, head)""", """    if not rig.rest:
        R.remove_islands(cv.px, keep=fx)
    fx |= R.close_holes(cv.px)
    fx = {q for q in fx if q in cv.px and cv.px[q] in FX_KEYS}
    info = anchors(rig, cv.px, groups, head)""")
print('patched')
