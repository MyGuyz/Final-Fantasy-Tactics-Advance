import sys, json, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lzss01 import lzss_decompress, lzss_decompress_ex
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROM = os.environ.get('FFTA_ROM', os.path.join(BASE, 'Final Fantasy Tactics Advance (USA).gba'))
data = open(ROM, 'rb').read()
n = len(data)
NL = chr(10)


def mc(b):
    if 0xB0 <= b <= 0xC9:
        return chr(ord('A') + (b - 0xB0))
    if 0xCA <= b <= 0xE3:
        return chr(ord('a') + (b - 0xCA))
    return None


def sc(b):
    if 0xB1 <= b <= 0xCA:
        return chr(ord('A') + (b - 0xB1))
    if 0xCB <= b <= 0xE4:
        return chr(ord('a') + (b - 0xCB))
    return None


def decode_raw(buf):
    out = []
    i = 0
    L = len(buf)
    while i < L:
        b = buf[i]
        if b == 0x80 and i + 1 < L:
            c = mc(buf[i + 1])
            out.append(c if c else '{80%02X}' % buf[i + 1])
            i += 2
        elif b == 0x40 and i + 1 < L:
            nx = buf[i + 1]
            if nx == 0x21 and i + 2 < L:
                out.append('{VOICE:%02X}' % buf[i + 2])
                i += 3
            else:
                out.append(' ' if nx == 0x73 else (NL if nx == 0x6E else '{40:%02X}' % nx))
                i += 2
        elif b == 0x00:
            i += 1
        elif b == 0x6E:
            out.append(NL)
            i += 1
        elif b == 0x73:
            out.append(' ')
            i += 1
        else:
            out.append('{u%02X}' % b)
            i += 1
    return ''.join(out)


def decode_buf(buf, start, depth=0):
    pos = start
    L = len(buf)
    out = []
    letters = 0
    mode_single = False
    if buf[pos] == 0x01 and pos + 1 < L and 0x80 <= buf[pos + 1] <= 0xFF:
        mode_single = True
        pos += 1
    elif buf[pos] == 0x80 and pos + 1 < L and 0x80 <= buf[pos + 1] <= 0xFF:
        pass
    else:
        return None
    while pos < L:
        b = buf[pos]
        if b == 0x00:
            pos += 1
            break
        if b == 0x32 and pos + 6 < L and depth < 3:
            ex = lzss_decompress_ex(buf, pos + 2, max_out=200000)
            if ex is not None:
                sub, used = ex
                r = decode_buf(sub, 0, depth + 1)
                out.append(r[0] if r else decode_raw(sub))
                pos += 2 + used
                continue
            out.append('{LZSS_FAIL}')
            pos += 6
            continue
        if mode_single:
            c = sc(b)
            if c is not None:
                out.append(c)
                pos += 1
                letters += 1
                continue
            if b == 0x6E:
                out.append(NL)
                pos += 1
                continue
            if b == 0x73:
                out.append(' ')
                pos += 1
                continue
            if b == 0x40 and pos + 1 < L:
                nx = buf[pos + 1]
                if nx == 0x21 and pos + 2 < L:
                    out.append('{VOICE:%02X}' % buf[pos + 2])
                    pos += 3
                    continue
                out.append(' ' if nx == 0x73 else (NL if nx == 0x6E else '{40:%02X}' % nx))
                pos += 2
                continue
            if 0x80 <= b <= 0xFF:
                out.append('{s%02X}' % b)
                pos += 1
                continue
            out.append('{u%02X}' % b)
            pos += 1
            continue
        else:
            if b == 0x80 and pos + 1 < L:
                nb = buf[pos + 1]
                c = mc(nb)
                if c is not None:
                    out.append(c)
                    pos += 2
                    letters += 1
                    continue
                out.append('{80%02X}' % nb)
                pos += 2
                continue
            if b == 0x6E:
                out.append(NL)
                pos += 1
                continue
            if b == 0x73:
                out.append(' ')
                pos += 1
                continue
            if b == 0x01 and pos + 1 < L:
                mode_single = True
                pos += 1
                continue
            if b == 0x40 and pos + 1 < L:
                nx = buf[pos + 1]
                if nx == 0x21 and pos + 2 < L:
                    out.append('{VOICE:%02X}' % buf[pos + 2])
                    pos += 3
                    continue
                out.append(' ' if nx == 0x73 else (NL if nx == 0x6E else '{40:%02X}' % nx))
                pos += 2
                continue
            if b == 0x72 and pos + 1 < L:
                out.append('{NAME:%02X}' % buf[pos + 1])
                pos += 2
                continue
            if b == 0x74 and pos + 1 < L:
                out.append('{DELAY:%02X}' % buf[pos + 1])
                pos += 2
                continue
            if b == 0x61:
                out.append('{WAIT}')
                pos += 1
                continue
            if b == 0x63:
                out.append('{CLEAR}')
                pos += 1
                continue
            if b == 0x70:
                out.append('{PAGE}')
                pos += 1
                continue
            out.append('{u%02X}' % b)
            pos += 1
            continue
    txt = ''.join(out)
    if letters < 2 and len(txt) < 4:
        return None
    return (txt, pos - start)


results = []


def scan(buf, base, tag):
    pos = 0
    L = len(buf)
    c = 0
    while pos < L - 1:
        b = buf[pos]
        if (b == 0x80 or b == 0x01) and 0x80 <= buf[pos + 1] <= 0xFF:
            r = decode_buf(buf, pos)
            if r:
                text, consumed = r
                results.append({'src': tag, 'offset': hex(base + pos), 'text': text})
                pos += max(consumed, 1)
                c += 1
                continue
        if b == 0x32 and pos + 6 < L:
            ex = lzss_decompress_ex(buf, pos + 2, max_out=200000)
            if ex is not None and len(ex[0]) >= 8:
                sub, used = ex
                t = decode_raw(sub)
                if len(re.sub(r'\{[^}]*\}', '', t).strip()) >= 4:
                    results.append({'src': tag + '+lzemb', 'offset': hex(base + pos), 'text': t})
                    c += 1
                    pos += 2 + used
                    continue
        pos += 1
    return c


def lz77(buf, start, max_out):
    size = buf[start + 1] | (buf[start + 2] << 8) | (buf[start + 3] << 16)
    if size == 0 or size > max_out:
        return None
    out = bytearray()
    pos = start + 4
    L = len(buf)
    while len(out) < size:
        if pos >= L:
            return None
        fl = buf[pos]
        pos += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if fl & (0x80 >> bit):
                if pos + 1 >= L:
                    return None
                b1 = buf[pos]
                b2 = buf[pos + 1]
                pos += 2
                ln = (b1 >> 4) + 3
                disp = (((b1 & 0xF) << 8) | b2) + 1
                if disp > len(out):
                    return None
                for _ in range(ln):
                    out.append(out[len(out) - disp])
            else:
                if pos >= L:
                    return None
                out.append(buf[pos])
                pos += 1
    return bytes(out)


print('pass 1: full ROM, following embedded LZSS ...')
c1 = scan(data, 0, 'rom')
print('  strings:', c1)

print('pass 2: mode-0x01 standalone blocks ...')
c2 = 0
b2 = 0
for off in range(0, n - 9, 4):
    if data[off] == 0x01:
        size = (data[off + 1] << 24) | (data[off + 2] << 16) | (data[off + 3] << 8) | data[off + 4]
        if 20 <= size <= 60000:
            res = lzss_decompress(data, off + 1, max_out=60000)
            if res is not None and len(res) == size:
                b2 += 1
                c2 += scan(res, off, 'lzss01@0x%X' % off)
print('  blocks:', b2, 'strings:', c2)

print('pass 3: mode-0x11 blocks (NEVER SCANNED BEFORE) ...')
c3 = 0
b3 = 0
for off in range(0, n - 8, 4):
    if data[off] == 0x11:
        size = data[off + 1] | (data[off + 2] << 8) | (data[off + 3] << 16)
        if 32 <= size <= 100000:
            res = lz77(data, off, size)
            if res is not None and len(res) == size:
                b3 += 1
                c3 += scan(res, off, 'lz11@0x%X' % off)
print('  blocks:', b3, 'strings:', c3)

print('TOTAL:', len(results))
json.dump(results, open(os.path.join(BASE,'data','FFTA_corpus_raw.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('saved corpus3.json')
