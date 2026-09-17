"""1920x1080 comparison: Carter's elbow-drop telegraph and impact, old vs the new ~1.6x v2,
at game scale on the arena render. Dashed outlines show the scene's current hitbox
(CapsuleShape2D r34 h120, rotated 90) and a same-shape capsule at the new r55 (h = 1.6x)."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compose import *

DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'previews')
os.makedirs(DEST, exist_ok=True)
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/'
RENDER = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
          'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/player_facing/renders/clean/f00000150.png')

et1 = Sheet(PROJ + 'Characters/Mason/elbow_target.png', 48, 48)
ei1 = Sheet(PROJ + 'Characters/Mason/elbow_impact.png', 64, 64)
et2 = Sheet(os.path.join(OUT, 'elbow_target_v2.png'), 76, 76)
ei2 = Sheet(os.path.join(OUT, 'elbow_impact_v2.png'), 104, 104)
carter = Sheet(PROJ + 'Characters/Mason/carter_elbowdrop.png', 64, 64)
player = Sheet(PROJ + 'Characters/MainPlayer/player_4dir_sheet.png', 32, 32)
S = 3
CYAN = (90, 230, 255)

c = Canvas.from_png(RENDER)
c.rect(852, 178, 1062, 388, MAT)          # clear Mason + player baked into the render


def carter_landed(cx, cy):
    # scene: CarterSprite offset (5.5, -29) at scale 3, elbow tip (26.5, 61) of frame 2 on the node
    c.place(carter.frame(2), cx + 5.5 * S, cy - 29 * S, S)


# ---------------------------------------------------------------- telegraphs
OLD_T = (520, 330)
NEW_T = (1290, 330)
c.place(et1.frame(1), OLD_T[0], OLD_T[1], S)
c.place(et2.frame(1), NEW_T[0], NEW_T[1], S)
c.place(player.frame(2, 1), OLD_T[0], OLD_T[1] - 20, 2)
c.place(player.frame(2, 1), NEW_T[0], NEW_T[1] - 20, 2)
capsule_outline(c, OLD_T[0], OLD_T[1], 34, 120, CYAN, dash=10)
capsule_outline(c, NEW_T[0], NEW_T[1], 55, 192, CYAN, dash=10)
text(c, 300, 150, 4, 'OLD ELBOW_TARGET 48X48')
text(c, 1010, 150, 4, 'NEW ELBOW_TARGET_V2 76X76')
text(c, 330, 440, 3, 'HITBOX R34 H120 (SCENE NOW)', col=CYAN)
text(c, 1090, 470, 3, 'R55 CAPSULE H192 (1.6X)', col=CYAN)

# ---------------------------------------------------------------- impacts (frames 1 and 2), Carter landed in frame 1
OLD_I = [(1, (405, 740)), (2, (640, 740))]
NEW_I = [(1, (1105, 760)), (2, (1450, 760))]
for f, (x, y) in OLD_I:
    c.place(ei1.frame(f), x, y, S)
for f, (x, y) in NEW_I:
    c.place(ei2.frame(f), x, y, S)
carter_landed(*OLD_I[0][1])
carter_landed(*NEW_I[0][1])
text(c, 250, 555, 4, 'OLD ELBOW_IMPACT 64X64')
text(c, 960, 555, 4, 'NEW ELBOW_IMPACT_V2 104X104')

out = os.path.join(DEST, 'mockup_carter_elbow_old_vs_v2_1920x1080.png')
c.save(out)
print('wrote', out)
