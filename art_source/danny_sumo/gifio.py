"""Minimal pure-python animated GIF89a writer (no PIL).

write_gif(path, frames, durations_ms, bg=(r,g,b))
  frames        list of pixel grids pix[y][x] = (r,g,b,a); all the same size
  durations_ms  list of per-frame durations in milliseconds
Transparent pixels are flattened onto `bg` (GIF transparency + disposal is
more trouble than it is worth for a design preview).
Colours are quantised to <=256 by exact-match first, then nearest.
"""
import struct


def _lzw(indices, min_code_size):
    clear = 1 << min_code_size
    eoi = clear + 1
    out = bytearray()
    bitbuf = 0
    bitcnt = 0

    def emit(code, width):
        nonlocal bitbuf, bitcnt
        bitbuf |= code << bitcnt
        bitcnt += width
        while bitcnt >= 8:
            out.append(bitbuf & 0xFF)
            bitbuf >>= 8
            bitcnt -= 8

    # keyed by (prefix_code << 8) | byte -- avoids building bytes objects,
    # which is what makes a pure-python encoder unusably slow
    def reset():
        return {}, clear + 2, min_code_size + 1

    table, nxt, width = reset()
    emit(clear, width)
    it = iter(indices)
    try:
        prev = next(it)
    except StopIteration:
        emit(eoi, width)
        if bitcnt:
            out.append(bitbuf & 0xFF)
        return bytes(out)
    for b in it:
        key = (prev << 8) | b
        nxtc = table.get(key)
        if nxtc is not None:
            prev = nxtc
            continue
        emit(prev, width)
        if nxt < 4096:
            table[key] = nxt
            nxt += 1
            if nxt > (1 << width) and width < 12:
                width += 1
        else:
            emit(clear, width)
            table, nxt, width = reset()
        prev = b
    emit(prev, width)
    emit(eoi, width)
    if bitcnt:
        out.append(bitbuf & 0xFF)
    return bytes(out)


def _blocks(data):
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i:i + 255]
        out.append(len(chunk))
        out += chunk
    out.append(0)
    return bytes(out)


def _quantise(frames, bg):
    counts = {}
    for f in frames:
        for row in f:
            for p in row:
                c = (p[0], p[1], p[2]) if p[3] >= 128 else bg
                counts[c] = counts.get(c, 0) + 1
    cols = sorted(counts, key=lambda c: -counts[c])
    if bg in cols:
        cols.remove(bg)
    pal = [bg] + cols[:255]
    idx = {c: i for i, c in enumerate(pal)}
    if len(cols) > 255:
        for c in cols[255:]:
            best = min(range(len(pal)), key=lambda i: (pal[i][0] - c[0]) ** 2
                       + (pal[i][1] - c[1]) ** 2 + (pal[i][2] - c[2]) ** 2)
            idx[c] = best
    return pal, idx


def write_gif(path, frames, durations_ms, bg=(24, 20, 37), loop=0):
    assert frames and len(frames) == len(durations_ms)
    h = len(frames[0])
    w = len(frames[0][0])
    pal, idx = _quantise(frames, bg)
    bits = 1
    while (1 << bits) < max(2, len(pal)):
        bits += 1
    tbl_size = 1 << bits
    table = bytearray()
    for i in range(tbl_size):
        c = pal[i] if i < len(pal) else (0, 0, 0)
        table += bytes(c)

    out = bytearray(b'GIF89a')
    out += struct.pack('<HHBBB', w, h, 0xF0 | (bits - 1), 0, 0)
    out += table
    out += b'\x21\xFF\x0BNETSCAPE2.0\x03\x01' + struct.pack('<H', loop) + b'\x00'

    mcs = max(2, bits)
    for f, ms in zip(frames, durations_ms):
        delay = max(1, int(round(ms / 10.0)))     # GIF ticks = 1/100 s
        out += b'\x21\xF9\x04\x04' + struct.pack('<H', delay) + b'\x00\x00'
        out += b'\x2C' + struct.pack('<HHHHB', 0, 0, w, h, 0)
        data = bytearray()
        for row in f:
            for p in row:
                data.append(idx[(p[0], p[1], p[2]) if p[3] >= 128 else bg])
        out += bytes([mcs]) + _blocks(_lzw(bytes(data), mcs))
    out += b'\x3B'
    with open(path, 'wb') as fh:
        fh.write(bytes(out))
    return path
