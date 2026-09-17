"""Pure-python PNG read/write helpers (no PIL available)."""
import struct
import zlib


def _paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path):
    """Return (w, h, rows) where rows[y][x] = (r, g, b, a)."""
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
    pos = 8
    idat = b''
    plte = None
    trns = None
    w = h = depth = ctype = interlace = None
    while pos < len(data):
        (length,) = struct.unpack('>I', data[pos:pos + 4])
        ctag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctag == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
        elif ctag == b'PLTE':
            plte = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif ctag == b'tRNS':
            trns = chunk
        elif ctag == b'IDAT':
            idat += chunk
        elif ctag == b'IEND':
            break
    assert interlace == 0, 'interlaced png not supported'
    raw = zlib.decompress(idat)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bits_pp = channels * depth
    bpp = max(1, bits_pp // 8)
    stride = (w * bits_pp + 7) // 8
    rows = []
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        ft = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 0xFF
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ft == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif ft == 4:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                ul = prev[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + _paeth(left, prev[x], ul)) & 0xFF
        prev = line
        row = []
        if depth == 8:
            for x in range(w):
                o = x * channels
                if ctype == 6:
                    row.append((line[o], line[o + 1], line[o + 2], line[o + 3]))
                elif ctype == 2:
                    px = (line[o], line[o + 1], line[o + 2], 255)
                    if trns is not None and len(trns) >= 6:
                        tr = struct.unpack('>HHH', trns[:6])
                        if px[:3] == tr:
                            px = (px[0], px[1], px[2], 0)
                    row.append(px)
                elif ctype == 3:
                    idx = line[o]
                    r, g, b = plte[idx]
                    a = trns[idx] if (trns is not None and idx < len(trns)) else 255
                    row.append((r, g, b, a))
                elif ctype == 0:
                    v = line[o]
                    row.append((v, v, v, 255))
                elif ctype == 4:
                    v = line[o]
                    row.append((v, v, v, line[o + 1]))
        elif ctype == 3 and depth in (1, 2, 4):
            mask = (1 << depth) - 1
            for x in range(w):
                bitpos = x * depth
                byte = line[bitpos // 8]
                shift = 8 - depth - (bitpos % 8)
                idx = (byte >> shift) & mask
                r, g, b = plte[idx]
                a = trns[idx] if (trns is not None and idx < len(trns)) else 255
                row.append((r, g, b, a))
        else:
            raise ValueError('unsupported depth/ctype %s/%s' % (depth, ctype))
        rows.append(row)
    return w, h, rows


def write_png(path, rows):
    """rows[y][x] = (r,g,b,a). Writes 8-bit RGBA."""
    h = len(rows)
    w = len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for px in row:
            if len(px) == 3:
                raw.extend((px[0], px[1], px[2], 255))
            else:
                raw.extend(px)

    def chunk(tag, payload):
        c = struct.pack('>I', len(payload)) + tag + payload
        return c + struct.pack('>I', zlib.crc32(tag + payload) & 0xFFFFFFFF)

    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(out)


def scale(rows, k):
    out = []
    for row in rows:
        big = []
        for px in row:
            big.extend([px] * k)
        for _ in range(k):
            out.append(list(big))
    return out


def crop(rows, x0, y0, x1, y1):
    return [row[x0:x1] for row in rows[y0:y1]]


def downsample_nearest(rows, k, ox=0, oy=0):
    return [row[ox::k] for row in rows[oy::k]]


def hexc(px):
    return '#%02x%02x%02x' % px[:3]


def on_bg(rows, bg=(40, 40, 40)):
    """Composite transparent pixels onto a flat colour for viewing."""
    out = []
    for row in rows:
        r2 = []
        for px in row:
            a = px[3]
            if a == 255:
                r2.append(px)
            elif a == 0:
                r2.append(bg + (255,))
            else:
                r2.append(tuple((px[i] * a + bg[i] * (255 - a)) // 255 for i in range(3)) + (255,))
        out.append(r2)
    return out
