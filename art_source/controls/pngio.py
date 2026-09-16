"""Minimal pure-python PNG read/write (RGBA8). No PIL available."""
import zlib, struct


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path):
    """Returns (w, h, pixels) where pixels[y][x] = (r,g,b,a)."""
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
    pos = 8
    idat = b''
    plte = None
    trns = None
    w = h = bitdepth = ctype = interlace = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bitdepth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
        elif typ == b'PLTE':
            plte = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif typ == b'tRNS':
            trns = chunk
        elif typ == b'IDAT':
            idat += chunk
        elif typ == b'IEND':
            break
    assert interlace == 0, 'interlaced not supported'
    raw = zlib.decompress(idat)
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    assert bitdepth in (8,) or (ctype == 3 and bitdepth in (1, 2, 4, 8)), f'bitdepth {bitdepth} ctype {ctype}'
    if ctype == 3:
        bpp_bits = bitdepth
        stride = (w * bpp_bits + 7) // 8
        bpp = 1
    else:
        bpp = chans
        stride = w * bpp
    rows = []
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        ft = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ft == 1:
                line[x] = (line[x] + a) & 255
            elif ft == 2:
                line[x] = (line[x] + b) & 255
            elif ft == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif ft == 4:
                line[x] = (line[x] + _paeth(a, b, c)) & 255
        rows.append(line)
        prev = line
    pix = []
    for y in range(h):
        line = rows[y]
        row = []
        for x in range(w):
            if ctype == 6:
                row.append(tuple(line[x * 4:x * 4 + 4]))
            elif ctype == 2:
                row.append(tuple(line[x * 3:x * 3 + 3]) + (255,))
            elif ctype == 0:
                v = line[x]
                row.append((v, v, v, 255))
            elif ctype == 4:
                v = line[x * 2]
                row.append((v, v, v, line[x * 2 + 1]))
            elif ctype == 3:
                if bitdepth == 8:
                    idx = line[x]
                else:
                    byte = line[(x * bitdepth) // 8]
                    shift = 8 - bitdepth - ((x * bitdepth) % 8)
                    idx = (byte >> shift) & ((1 << bitdepth) - 1)
                r, g, b = plte[idx]
                a = trns[idx] if trns is not None and idx < len(trns) else 255
                row.append((r, g, b, a))
        pix.append(row)
    return w, h, pix


def write_png(path, w, h, pix):
    """pix[y][x] = (r,g,b,a)"""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(bytes(pix[y][x]))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(out)


def upscale(w, h, pix, s, bg=None, grid=None):
    """Nearest-neighbour upscale. bg replaces transparent pixels (for viewing).
    grid=(fw, fh, color) draws frame separators."""
    W, H = w * s, h * s
    out = []
    for Y in range(H):
        y = Y // s
        row = []
        for X in range(W):
            x = X // s
            p = pix[y][x]
            if bg is not None and p[3] == 0:
                # checker background so transparency is visible
                if isinstance(bg, str) and bg == 'checker':
                    c = 200 if ((X // (s * 2) + Y // (s * 2)) % 2 == 0) else 170
                    p = (c, c, c, 255)
                else:
                    p = bg
            elif bg is not None and p[3] < 255:
                a = p[3] / 255.0
                base = bg if not isinstance(bg, str) else (185, 185, 185, 255)
                p = tuple(int(p[i] * a + base[i] * (1 - a)) for i in range(3)) + (255,)
            if grid is not None:
                fw, fh, gc = grid
                if (fw and X % (fw * s) == 0) or (fh and Y % (fh * s) == 0):
                    p = gc
            row.append(p)
        out.append(row)
    return W, H, out
