"""Check the scratch copy of the rigs reproduces Jordan's LIVE sheets pixel for pixel (reads only)."""
import sys
sys.dont_write_bytecode = True
import jr_common as C
import janim_idle, janim_summon, janim_taunt, janim_hit, janim_defeat
ok = True
for mod in (janim_idle, janim_summon, janim_taunt, janim_hit, janim_defeat):
    fr = mod.frames()
    im = C.JB.strip([px for px, _ in fr])
    d = C.pixel_diff(im, C.live_sheet(mod.NAME))
    print(mod.NAME, len(fr), 'frames:', d or 'IDENTICAL to the live sheet')
    ok &= not d
sys.exit(0 if ok else 1)
