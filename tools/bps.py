"""Minimal BPS patch writer and applier (byuu's format, linear encoding)."""

import zlib


def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return out
        out.append(x)
        n -= 1


def _read_num(data, i):
    n, shift = 0, 1
    while True:
        x = data[i]
        i += 1
        n += (x & 0x7F) * shift
        if x & 0x80:
            return n, i
        shift <<= 7
        n += shift


def create(source, target):
    out = bytearray(b"BPS1")
    out += _num(len(source)) + _num(len(target)) + _num(0)
    i, n = 0, len(target)
    while i < n:
        same = i < len(source) and source[i] == target[i]
        j = i
        while j < n and (j < len(source) and source[j] == target[j]) == same:
            j += 1
        out += _num(((j - i - 1) << 2) | (0 if same else 1))
        if not same:
            out += target[i:j]
        i = j
    out += zlib.crc32(source).to_bytes(4, "little")
    out += zlib.crc32(target).to_bytes(4, "little")
    out += zlib.crc32(out).to_bytes(4, "little")
    return bytes(out)


def apply(source, patch):
    if patch[:4] != b"BPS1" or zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise ValueError("patch BPS inválido")
    if zlib.crc32(source) != int.from_bytes(patch[-12:-8], "little"):
        raise ValueError("ROM de origem diferente da esperada")
    i = 4
    _, i = _read_num(patch, i)
    tsize, i = _read_num(patch, i)
    msize, i = _read_num(patch, i)
    i += msize
    target = bytearray(tsize)
    out = src_rel = tgt_rel = 0
    end = len(patch) - 12
    while i < end:
        data, i = _read_num(patch, i)
        mode, length = data & 3, (data >> 2) + 1
        if mode == 0:
            target[out:out + length] = source[out:out + length]
        elif mode == 1:
            target[out:out + length] = patch[i:i + length]
            i += length
        else:
            d, i = _read_num(patch, i)
            delta = (-1 if d & 1 else 1) * (d >> 1)
            if mode == 2:
                src_rel += delta
                target[out:out + length] = source[src_rel:src_rel + length]
                src_rel += length
            else:
                tgt_rel += delta
                for k in range(length):
                    target[out + k] = target[tgt_rel + k]
                tgt_rel += length
        out += length
    if zlib.crc32(target) != int.from_bytes(patch[-8:-4], "little"):
        raise ValueError("resultado do patch não confere")
    return bytes(target)
