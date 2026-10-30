"""Writes Vorbis comments (LOOPSTART, LOOPLENGTH) into an OGG Vorbis file: Blender's encoder can't.

The comment packet sits in the stream's header pages; those pages are rebuilt and, if their count changes, the
audio pages after them are renumbered (with their checksums redone). The audio itself is untouched."""

import struct

_TABLE = []
for _i in range(256):
    _r = _i << 24
    for _ in range(8):
        _r = ((_r << 1) ^ 0x04C11DB7) if _r & 0x80000000 else (_r << 1)
    _TABLE.append(_r & 0xFFFFFFFF)


def _crc(data):
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ _TABLE[((crc >> 24) & 0xFF) ^ b]
    return crc


def _pages(data):
    pos = 0
    while pos < len(data):
        assert data[pos:pos + 4] == b"OggS", "not an Ogg page"
        flags, granule, serial, seq = data[pos + 5], *struct.unpack_from("<qII", data, pos + 6)
        nseg = data[pos + 26]
        lacing = data[pos + 27:pos + 27 + nseg]
        start = pos + 27 + nseg
        end = start + sum(lacing)
        yield dict(flags=flags, granule=granule, serial=serial, seq=seq, lacing=bytes(lacing), body=data[start:end],
                   raw=data[pos:end])
        pos = end


def _page(flags, granule, serial, seq, lacing, body):
    head = b"OggS" + bytes([0, flags]) + struct.pack("<qII", granule, serial, seq) + b"\0\0\0\0"
    raw = bytearray(head + bytes([len(lacing)]) + bytes(lacing) + body)
    struct.pack_into("<I", raw, 22, _crc(raw))
    return bytes(raw)


def _paginate(packets, serial, seq0):
    """Header packets onto pages (granule 0), each packet's lacing kept whole."""
    segs = []
    for pk in packets:
        n = len(pk)
        segs += [(255, i * 255) for i in range(n // 255)]
        segs.append((n % 255, None))
    body_all = b"".join(packets)
    pages, cont = [], False
    i, off, seq = 0, 0, seq0
    while i < len(segs):
        chunk = segs[i:i + 255]
        size = sum(s for s, _ in chunk)
        pages.append(_page(0x01 if cont else 0x00, 0, serial, seq, [s for s, _ in chunk], body_all[off:off + size]))
        cont = chunk[-1][0] == 255
        off += size
        i += 255
        seq += 1
    return pages


def set_comments(path, tags):
    data = open(path, "rb").read()
    pages = list(_pages(data))
    packets, cur, used = [], b"", 0
    for pg in pages:
        used += 1
        off = 0
        for lv in pg["lacing"]:
            cur += pg["body"][off:off + lv]
            off += lv
            if lv < 255:
                packets.append(cur)
                cur = b""
        if len(packets) >= 3:
            break
    assert len(packets) == 3 and cur == b"", "headers must end on a page of their own"
    ident, comment, setup = packets
    assert comment[:7] == b"\x03vorbis"
    vlen = struct.unpack_from("<I", comment, 7)[0]
    vendor = comment[11:11 + vlen]
    n = struct.unpack_from("<I", comment, 11 + vlen)[0]
    pos, entries = 15 + vlen, []
    for _ in range(n):
        ln = struct.unpack_from("<I", comment, pos)[0]
        e = comment[pos + 4:pos + 4 + ln]
        pos += 4 + ln
        if e.split(b"=")[0].upper() not in {k.upper().encode() for k in tags}:
            entries.append(e)
    entries += [f"{k}={v}".encode() for k, v in tags.items()]
    new_comment = (b"\x03vorbis" + struct.pack("<I", len(vendor)) + vendor + struct.pack("<I", len(entries))
                   + b"".join(struct.pack("<I", len(e)) + e for e in entries) + b"\x01")
    serial = pages[0]["serial"]
    out = [_page(pages[0]["flags"], 0, serial, 0, pages[0]["lacing"], pages[0]["body"])]
    assert pages[0]["body"] == ident
    out += _paginate([new_comment, setup], serial, 1)
    shift = len(out) - used
    for pg in pages[used:]:
        out.append(_page(pg["flags"], pg["granule"], pg["serial"], pg["seq"] + shift, pg["lacing"], pg["body"])
                   if shift else pg["raw"])
    open(path, "wb").write(b"".join(out))


def get_comments(path):
    data = open(path, "rb").read()
    pages = list(_pages(data))
    body = pages[1]["body"]
    vlen = struct.unpack_from("<I", body, 7)[0]
    n = struct.unpack_from("<I", body, 11 + vlen)[0]
    pos, out = 15 + vlen, {}
    for _ in range(n):
        ln = struct.unpack_from("<I", body, pos)[0]
        k, _, v = body[pos + 4:pos + 4 + ln].decode().partition("=")
        out[k] = v
        pos += 4 + ln
    return out
