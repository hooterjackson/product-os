#!/usr/bin/env python3
"""Re-derive favicon.png from favicon-source.png.

Measures the mark's real bounding box by decoding the PNG (no third-party
libraries on this machine), crops to it with 6% breathing room, and scales to
256. Run after replacing the master; see favicon.md for why it crops.
"""

import os
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "favicon-source.png")
OUT = os.path.join(HERE, "favicon.png")
THRESHOLD = 110      # above the glow's falloff, below the mark's ink
MARGIN = 0.06
SIZE = 256


def rows(path):
    raw = open(path, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("%s is not a PNG" % path)
    pos, idat, meta = 8, b"", None
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        kind, data = raw[pos + 4:pos + 8], raw[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            meta = struct.unpack(">IIBBBBB", data)
        elif kind == b"IDAT":
            idat += data
        pos += 12 + length
    width, height, depth, colour, _c, _f, interlace = meta
    if depth != 8 or interlace or colour not in (2, 6):
        raise SystemExit("expected an 8-bit non-interlaced RGB/RGBA PNG")
    channels = 3 if colour == 2 else 4
    buf, stride = zlib.decompress(idat), width * channels
    prev, out, i = bytearray(stride), [], 0
    for _y in range(height):
        filt, i = buf[i], i + 1
        line, i = bytearray(buf[i:i + stride]), i + stride
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = prev[x]
            c = prev[x - channels] if x >= channels else 0
            if filt == 1:
                line[x] = (line[x] + a) & 255
            elif filt == 2:
                line[x] = (line[x] + b) & 255
            elif filt == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc
                                      else b if pb <= pc else c)) & 255
        out.append(bytes(line))
        prev = line
    return out, width, height, channels


def main():
    pixels, width, height, channels = rows(SOURCE)
    minx, miny, maxx, maxy = width, height, -1, -1
    for y in range(height):
        row = pixels[y]
        for x in range(width):
            if row[x * channels] > THRESHOLD:
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
    if maxx < 0:
        raise SystemExit("found no mark above the threshold")
    side = max(maxx - minx, maxy - miny)
    side += int(side * MARGIN) * 2
    ox = max(0, (minx + maxx) // 2 - side // 2)
    oy = max(0, (miny + maxy) // 2 - side // 2)
    print("bbox %dx%d in %dx%d -> crop %d at (%d, %d)"
          % (maxx - minx, maxy - miny, width, height, side, ox, oy))
    subprocess.run(["sips", "-c", str(side), str(side),
                    "--cropOffset", str(oy), str(ox), SOURCE,
                    "--out", OUT], stdout=subprocess.DEVNULL, check=True)
    subprocess.run(["sips", "-Z", str(SIZE), OUT, "--out", OUT],
                   stdout=subprocess.DEVNULL, check=True)
    print("wrote %s at %dpx" % (os.path.relpath(OUT), SIZE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
