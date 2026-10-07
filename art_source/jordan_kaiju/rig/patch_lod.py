import os
HERE = os.path.dirname(os.path.abspath(__file__))


def sub(path, old, new, count=1):
    p = os.path.join(HERE, path)
    s = open(p).read()
    if old not in s:
        raise SystemExit('not found in %s: %r' % (path, old[:80]))
    s = s.replace(old, new, count)
    open(p, 'w').write(s)


sub('kjr.py', """        self.px = {}
        self.owner = {}

    def inb(self, q):""", """        self.px = {}
        self.owner = {}
        self.lod = False             # small sizes: only the silhouette, the plates and the belly band keep lines

    def inb(self, q):""")
sub('kjr.py', """    def stamp(self, part, outline=True, cast=2, floor=None, owner=None):
        if floor is not None:""", """    def stamp(self, part, outline=True, cast=2, floor=None, owner=None, keep_line=False):
        if self.lod and not keep_line:
            outline, cast = False, 0
        if floor is not None:""")
sub('kjr.py', """def belly(rig, part, info):""", """def belly(rig, part, info, seams=True):""")
sub('kjr.py', """        if int(a) % step == 0 and rel < 0.92 and along < tot - 7 * rig.sc / BASE_SC:
            part[q] = 'k'""", """        if seams and int(a) % step == 0 and rel < 0.92 and along < tot - 7 * rig.sc / BASE_SC:
            part[q] = 'k'""")

# render: lod switch
sub('kjr_render.py', """                halo=False, spark_pts=(), feet=R.FEET, size=(R.FW, R.FH), floor=True, star_sole=False):""",
    """                halo=False, spark_pts=(), feet=R.FEET, size=(R.FW, R.FH), floor=True, star_sole=False,
                lod=None):""")
sub('kjr_render.py', """    cv = R.KCanvas(*size)
    sole = rig.floor() if floor else None""", """    cv = R.KCanvas(*size)
    if lod is None:
        lod = sc < LOD_BELOW * R.BASE_SC
    cv.lod = lod
    sole = rig.floor() if floor else None""")
sub('kjr_render.py', """                    cv.stamp(part, cast=0 if row == 'far' else 1, floor=tail_floor)""",
    """                    cv.stamp(part, cast=0 if row == 'far' else 1, floor=tail_floor, keep_line=True)""")
sub('kjr_render.py', """        R.belly(rig, torso, tinfo)
        cv.stamp(torso""", """        R.belly(rig, torso, tinfo, seams=not lod)
        cv.stamp(torso""")
sub('kjr_render.py', """    cv.stamp(R.claws(rig, R.FFOOT_TIPS, 3), cast=0, floor=sole)
    if star_sole:""", """    if not lod:
        cv.stamp(R.claws(rig, R.FFOOT_TIPS, 3), cast=0, floor=sole)
    if star_sole:""")
sub('kjr_render.py', """    cv.stamp(R.claws(rig, R.F_TIPS, 3), cast=0, floor=sole)""", """    if not lod:
        cv.stamp(R.claws(rig, R.F_TIPS, 3), cast=0, floor=sole)""")
sub('kjr_render.py', """    cv.stamp(R.claws(rig, R.NFOOT_TIPS, 3), cast=0, floor=sole)""", """    if not lod:
        cv.stamp(R.claws(rig, R.NFOOT_TIPS, 3), cast=0, floor=sole)""")
sub('kjr_render.py', """    cv.stamp(R.claws(rig, R.N_TIPS, 3.5), cast=0, floor=sole)""", """    if not lod:
        cv.stamp(R.claws(rig, R.N_TIPS, 3.5), cast=0, floor=sole)""")
sub('kjr_render.py', """    if not rig.rest:
        R.remove_islands(cv.px, keep=fx)
        R.seal(cv.px, fx)""", """    if not rig.rest:
        R.remove_islands(cv.px, keep=fx, min_size=14 if not lod else 3)
        R.seal(cv.px, fx)""")
sub('kjr_render.py', """FX_KEYS = set('XKJI8WQPqOY')""", """FX_KEYS = set('XKJI8WQPqOY')
LOD_BELOW = 0.42                     # below this share of the fight size, draw the simplified kaiju""")
print('patched')
