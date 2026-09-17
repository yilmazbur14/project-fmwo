import fxpng
radii = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
modes = {'center-strict': (0.5, 0.0), 'center-soft': (0.5, 0.6), 'corner-strict': (0.0, 0.0), 'corner-soft': (0.0, 0.6)}
S = 18
rows_all = []
for mname, (coff, soft) in modes.items():
    band = [[(0, 0, 0, 0)] * (S * len(radii)) for _ in range(S)]
    for i, r in enumerate(radii):
        cx = cy = 8 + coff
        mask = {(x, y) for y in range(S) for x in range(S)
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r + soft * r}
        for y in range(S):
            for x in range(S):
                if (x, y) in mask:
                    band[y][i * S + x] = (200, 220, 90, 255)
                elif any((x + dx, y + dy) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    band[y][i * S + x] = (0, 0, 0, 255)
    rows_all += band
    print(mname)
W8, H8, o = fxpng.view(S * len(radii), S * len(modes), rows_all, 4, grid=(S, S))
fxpng.write_png('circle_test_4x.png', W8, H8, o)
