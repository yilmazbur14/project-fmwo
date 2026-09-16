"""Uber driver sprite library: palette, part parsing, composition, PNG I/O."""
import zlib, struct

PAL = {
    'K': '#000000',  # outline
    # skin - the cast's warm tan ramp (Mason / Jordan)
    'A': '#FADCB8', 'S': '#EEC39A', 's': '#D6AA7C', 'd': '#AE8358', 'D': '#90765E',
    # hair (dark brown)
    'H': '#2E1F1A', 'h': '#4A332B',
    # eye white / drawstring
    'W': '#FFFFFF', 'w': '#C9CFD6',
    # charcoal "black" ramp - cap, trousers, cuffs
    'E': '#6A6F82', 'T': '#4E5263', 'B': '#383B48', 'b': '#272933', 'Z': '#1B1C23',
    # hoodie green - muted take on the delivery-app green
    'Q': '#7EE693', 'L': '#4ECC74', 'G': '#2AA85E', 'g': '#1A8050', 'X': '#125C44',
    # sneakers (knocked-down white, Jordan's ramp)
    'N': '#E8E6E0', 'U': '#CBC8C0', 'n': '#9B968C', 'M': '#5C5850',
    # kraft paper bag - more saturated/orange than skin so they never merge
    'Y': '#E6B872', 'O': '#CC9650', 'R': '#B07A3C', 'r': '#8A5A2B', 'V': '#613E1F',
}

# one step darker, for the far-side limbs
FAR = {'Q': 'L', 'L': 'G', 'G': 'g', 'g': 'X',
       'A': 'S', 'S': 's', 's': 'd', 'd': 'D',
       'E': 'T', 'T': 'B', 'B': 'b', 'b': 'Z',
       'N': 'U', 'U': 'n', 'n': 'M'}

FW, FH = 64, 64


def part(text):
    """Multi-line string -> list of rows. '.' and ' ' are transparent."""
    rows = [r for r in text.strip('\n').split('\n')]
    rows = [r.rstrip() for r in rows]
    for r in rows:
        for c in r:
            if c not in '. ' and c not in PAL:
                raise ValueError('bad char %r in part' % c)
    return rows


def remap(rows, table):
    return [''.join(table.get(c, c) for c in r) for r in rows]


def new_frame():
    return [[None] * FW for _ in range(FH)]


def paste(frame, rows, ox, oy):
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c in '. ':
                continue
            x, y = ox + i, oy + j
            if 0 <= x < FW and 0 <= y < FH:
                frame[y][x] = c
            else:
                raise ValueError('pixel out of frame at %d,%d' % (x, y))


def to_rgba(c):
    if c is None:
        return (0, 0, 0, 0)
    hx = PAL[c].lstrip('#')
    return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16), 255)


def write_png(path, frames, scale=1, bg=None):
    """frames: list of 64x64 grids laid out as a horizontal strip."""
    n = len(frames)
    w, h = FW * n * scale, FH * scale
    raw = bytearray()
    for y in range(FH):
        line = bytearray()
        for f in frames:
            for x in range(FW):
                px = to_rgba(f[y][x])
                if px[3] == 0 and bg:
                    px = bg(x, y)
                line += bytes(px) * scale
        for _ in range(scale):
            raw += b'\x00' + line

    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)


def checker(x, y):
    return (210, 210, 210, 255) if ((x // 4) + (y // 4)) % 2 == 0 else (170, 170, 170, 255)


def dump(frame):
    out = ['    ' + ''.join(str(x % 10) for x in range(FW))]
    for y, row in enumerate(frame):
        out.append('%3d ' % y + ''.join(c if c else '.' for c in row))
    return '\n'.join(out)


def write_crop(path, frames, x0, y0, x1, y1, scale=10, bg=checker):
    """Crop the same inclusive region from each frame, laid side by side, 1px gap."""
    n = len(frames)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    W = (cw + 1) * n - 1
    grid = []
    for y in range(y0, y1 + 1):
        row = []
        for i, f in enumerate(frames):
            for x in range(x0, x1 + 1):
                c = f[y][x]
                row.append(to_rgba(c) if c else bg(x - x0, y - y0))
            if i < n - 1:
                row.append((255, 0, 255, 255))
        grid.append(row)
    raw = bytearray()
    for row in grid:
        line = bytearray()
        for px in row:
            line += bytes(px) * scale
        for _ in range(scale):
            raw += b'\x00' + line

    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', W * scale, ch * scale, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)
