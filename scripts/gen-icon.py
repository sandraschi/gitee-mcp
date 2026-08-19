#!/usr/bin/env python
"""Generate a 256x256 PNG icon for the MCPB bundle without PIL.

Draws a dark rounded square with a red Gitee-ish 'G' mark. Pure stdlib
(zlib + struct) so it runs anywhere uv exists.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

SIZE = 256
OUT = Path(__file__).resolve().parents[1] / "assets" / "icon.png"

BG = (20, 22, 30)  # dark slate
GREEN = (198, 44, 44)  # gitee red accent
FG = (240, 240, 244)  # near white


def in_rect(x: int, y: int, x0: int, y0: int, x1: int, y1: int) -> bool:
    return x0 <= x < x1 and y0 <= y < y1


def pixel(x: int, y: int) -> tuple[int, int, int]:
    # rounded-corner background (corner radius 40)
    r = 40
    cx = min(max(x, r), SIZE - 1 - r)
    cy = min(max(y, r), SIZE - 1 - r)
    if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
        return (0, 0, 0, 0)[:3]
    # draw a stylized 'G': outer ring + gap on the right + horizontal bar
    ring = 46
    gap = 24
    if 64 <= x <= 192 and 64 <= y <= 192:
        dx = abs(x - 128)
        dy = abs(y - 128)
        dist = (dx * dx + dy * dy) ** 0.5
        if ring <= dist <= ring + 26:
            if x > 128 and abs(dy) < gap:
                return BG  # gap in the ring, right side
            return GREEN
        if ring + 26 < dist <= ring + 30:
            return FG  # thin outer stroke
    # horizontal bar of the G
    if 128 <= x <= 168 and 128 <= y <= 160:
        return GREEN
    return BG


def main() -> None:
    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)  # filter type 0
        for x in range(SIZE):
            raw.extend(pixel(x, y))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(png)
    print(f"Wrote {OUT} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
