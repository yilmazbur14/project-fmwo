"""Jordan's room - layout constants and the light fields everything is shaded from.

Room contract (finale build plan):
  * 640x360 texels at 3x (1920x1080), five layers from the screen origin, bottom
    to top: room_floor, room_walls, room_furniture, room_props, room_clutter.
  * 3/4 top-down like the arena: the back wall face-on, its base line at row 150;
    side and near walls only as their top caps.
  * The door is an opening in the back wall at x 40-104; everyone enters through
    it walking down.
  * Desk, monitors and PC against the back wall right of centre; the chair spot
    in front of the desk is left empty (the chair is on Jordan's seated sheet).
  * All furniture stands against the back wall; floor clutter is flat.
  * Walkable floor about rows 160-350, kept clear for two loose rows of bosses.

Scale, set by Jordan (87 texels tall on his 96x96 sheet): 48 texels per metre
of height and width, 32 per metre of floor depth. The wall is 146 texels high.
All coordinates are native texels (x 0..639, y 0..359).
"""
import numpy as np

from jr_lib import W, H

# ---------------------------------------------------------------- shell
TOPCAP_Y1 = 3          # back wall's top cap: y 0..3
WALL_Y0 = 4            # back wall face: y 4..149
FLOOR_Y = 150          # floor: y 150..349  (the back wall's base line)
NEAR_Y = 350           # near wall cap: y 350..359
LX = 10                # left wall cap: x 0..9, room interior starts at 10
RX = 630               # right wall cap: x 630..639, interior ends at 629
BASEBOARD_Y = 140      # skirting board: y 140..149
LED_Y = 8              # RGB strip under the crown moulding
PLANK = 8              # floor board row height

# door: an opening in the back wall
DOOR_X0, DOOR_X1 = 40, 104          # outside of the casing
DOOR_OPEN_X0, DOOR_OPEN_X1 = 45, 99  # clear opening
DOOR_TOP = 40                        # top of the head casing
DOOR_OPEN_TOP = 46                   # top of the clear opening
THRESHOLD_Y = FLOOR_Y                # the sill line everyone steps over

# desk (right of centre) and the empty chair spot in front of it
DESK_X0, DESK_X1 = 340, 482
DESK_DEPTH = 18                      # floor rows under the desk (0.56 m)
DESK_FRONT_Y = FLOOR_Y + DESK_DEPTH  # 168: front bottom edge on the floor
DESK_TOP_H = 36                      # 0.75 m
DESK_TOP_Y = FLOOR_Y - DESK_TOP_H    # 114: back edge of the top
DESK_LIP_Y = DESK_FRONT_Y - DESK_TOP_H  # 132: front edge of the top
CHAIR_POINT = (411, 196)             # centre of the chair's five-star base on the floor
MON_CX, MON_CY = 411, 100            # centre of the monitor light

PC_X0, PC_X1 = 488, 510

# walkable floor (feet positions), clockwise: rows 163..349 wall to wall, the
# doorway notch up to the sill, less the desk front, the empty chair spot and the PC
WALKABLE = [(14, 163), (45, 163), (45, 152), (99, 152), (99, 163), (336, 163), (336, 170),
            (378, 170), (378, 216), (446, 216), (446, 170), (516, 170), (516, 163),
            (626, 163), (626, 349), (14, 349)]
CHAIR_SPOT = (378, 168, 446, 216)    # kept empty for the chair on Jordan's seated sheet

_yy, _xx = np.mgrid[0:H, 0:W]
XX = _xx + 0.5
YY = _yy + 0.5


def _ell(cx, cy, rx, ry):
    return np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)


def _sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- lights
def monitor_wall():
    """Screen glow on the back wall round the monitors."""
    d = _ell(MON_CX, MON_CY - 2, 78, 44)
    return 1.0 - _sm(0.35, 1.0, d)


def monitor_floor():
    """Blurple pool thrown on the boards in front of the desk (the empty chair spot
    sits in the middle of it)."""
    d = _ell(MON_CX, DESK_FRONT_Y + 14, 118, 50)
    return 1.0 - _sm(0.25, 1.0, d)


def led_wall():
    y = YY
    return (1.0 - _sm(LED_Y + 1, LED_Y + 26, y)) * (y > LED_Y)


def hall_floor():
    """Warm hallway light falling out of the doorway onto the boards."""
    x, y = XX, YY
    t = np.clip((y - FLOOR_Y) / 90.0, 0.0, 1.0)            # 0 at the sill, 1 at 90 rows down
    left = DOOR_OPEN_X0 - 2 - t * 22
    right = DOOR_OPEN_X1 + 2 + t * 26
    inside = (x >= left) & (x <= right) & (y >= FLOOR_Y)
    edge = np.minimum(x - left, right - x)
    soft = _sm(0.0, 9.0, edge)
    fade = 1.0 - _sm(0.1, 1.0, t)
    return inside * soft * fade


def pc_glow():
    return 1.0 - _sm(0.0, 1.0, _ell((PC_X0 + PC_X1) / 2, FLOOR_Y + 14, 30, 12))
