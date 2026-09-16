import json

# Right half of Mason's silhouette, traced top-centre -> clockwise -> bottom-centre.
# Mirror axis x = 31.5  =>  x' = 63 - x
RIGHT = [
    # --- hood (chicken head) dome and side ---
    (32, 6), (36, 6), (39, 7), (42, 9), (44, 12),
    (45, 16), (45, 20), (44, 24), (42, 28),
    # --- shoulder pinch, so the head reads as a head and not part of the blob ---
    (41, 30),
    # --- then the costume body flares out below it ---
    (44, 32), (47, 34), (49, 36), (51, 39),
    # --- stubby wing: out, around the tip, back to the body ---
    (55, 39), (58, 41), (60, 44), (59, 47), (56, 48), (52, 46),
    # --- body right edge, widest here, then tapering in ---
    (52, 48), (51, 50), (49, 51), (46, 52), (43, 53),
    # --- right trouser leg, outer edge ---
    (42, 53), (42, 57),
    # --- right chicken foot ---
    (46, 57), (49, 58), (51, 60), (51, 63),
    (34, 63), (34, 58),
    # --- back up the inner leg ---
    (35, 57), (35, 53),
    # --- crotch / underside of the body, to centre ---
    (33, 52), (32, 52),
]

def mirror(p):
    return (63 - p[0], p[1])

full = RIGHT + [mirror(p) for p in reversed(RIGHT)]

xs = [p[0] for p in full]; ys = [p[1] for p in full]
print('points:', len(full))
print('x range', min(xs), max(xs), ' y range', min(ys), max(ys))
assert min(xs) >= 0 and max(xs) <= 63, 'x out of frame'
assert min(ys) >= 0 and max(ys) <= 63, 'y out of frame'
n = len(RIGHT)
for i in range(n):
    a = full[i]; b = full[len(full) - 1 - i]
    assert a[1] == b[1] and a[0] + b[0] == 63, 'asymmetry at %d: %s %s' % (i, a, b)
print('mirror symmetry OK')
for i in range(len(full)):
    assert full[i] != full[(i + 1) % len(full)], 'dup at %d' % i
print('no duplicate consecutive points')
print(json.dumps([{"x": x, "y": y} for x, y in full]))
