import struct, sys
def lzw_decode(data, min_code):
    clear = 1 << min_code; eoi = clear + 1
    code_size = min_code + 1
    table = [[i] for i in range(clear)] + [[], []]
    out = []; prev = None
    bitpos = 0; nbits_total = len(data) * 8
    val = int.from_bytes(data, 'little')
    while bitpos + code_size <= nbits_total:
        code = (val >> bitpos) & ((1 << code_size) - 1); bitpos += code_size
        if code == clear:
            table = [[i] for i in range(clear)] + [[], []]; code_size = min_code + 1; prev = None; continue
        if code == eoi: break
        if code < len(table):
            entry = table[code]
            if prev is not None: table.append(prev + [entry[0]])
        else:
            entry = prev + [prev[0]]; table.append(entry)
        out.extend(entry); prev = entry
        if len(table) == (1 << code_size) and code_size < 12: code_size += 1
    return out
def read_gif(path):
    d = open(path, 'rb').read()
    assert d[:6] == b'GIF89a'
    w, h, flags, bgi, asp = struct.unpack('<HHBBB', d[6:13]); pos = 13
    gct = []
    if flags & 0x80:
        n = 2 << (flags & 7); gct = [tuple(d[pos + 3*i:pos + 3*i + 3]) for i in range(n)]; pos += 3 * n
    frames = []; delay = None; loops = None
    while True:
        b = d[pos]; pos += 1
        if b == 0x21:
            label = d[pos]; pos += 1
            blocks = []
            while True:
                sz = d[pos]; pos += 1
                if sz == 0: break
                blocks.append(d[pos:pos + sz]); pos += sz
            if label == 0xF9: delay = struct.unpack('<H', blocks[0][1:3])[0]
            if label == 0xFF and blocks[0] == b'NETSCAPE2.0': loops = struct.unpack('<H', blocks[1][1:3])[0]
        elif b == 0x2C:
            x, y, fw, fh, fl = struct.unpack('<HHHHB', d[pos:pos + 9]); pos += 9
            min_code = d[pos]; pos += 1
            data = bytearray()
            while True:
                sz = d[pos]; pos += 1
                if sz == 0: break
                data += d[pos:pos + sz]; pos += sz
            idx = lzw_decode(bytes(data), min_code)
            assert len(idx) >= fw * fh, (len(idx), fw * fh)
            frames.append((delay, [[gct[idx[r * fw + c]] for c in range(fw)] for r in range(fh)]))
        elif b == 0x3B: break
        else: raise ValueError('bad block %x' % b)
    return w, h, loops, frames
if __name__ == '__main__':
    from lib import *
    import frames as FR
    w, h, loops, fr = read_gif(sys.argv[1]); s = int(sys.argv[2])
    src = FR.build_frames()
    bg = (58, 64, 84)
    print('size', w, h, 'loop', loops, 'frames', len(fr))
    ok = True
    for i, ((delay, px), (name, dur, cv)) in enumerate(zip(fr, src)):
        rgba = to_rgba(cv)
        mism = 0
        for y in range(64):
            for x in range(64):
                exp = rgba[y][x][:3] if rgba[y][x][3] == 255 else bg
                if px[y * s][x * s] != exp: mism += 1
        print('frame %d %-8s delay %dcs (want %dms) mismatches %d' % (i, name, delay, dur, mism))
        ok = ok and mism == 0 and delay * 10 == dur
    print('ALL OK' if ok else 'PROBLEM')
