"""Render the 128x64 OLED framebuffer dumps (PGM) as PNGs that look like a 0.96" blue-on-black OLED."""
import sys
from PIL import Image

for src in sys.argv[1:]:
    with open(src) as f:
        tokens = f.read().split()
    w, h = int(tokens[1]), int(tokens[2])
    px = [int(v) for v in tokens[4:4 + w * h]]
    scale, border = 4, 12
    img = Image.new("RGB", (w * scale + 2 * border, h * scale + 2 * border), (8, 10, 14))
    on, off = (120, 200, 255), (14, 18, 26)
    for y in range(h):
        for x in range(w):
            colour = on if px[y * w + x] else off
            for dy in range(scale - 1):
                for dx in range(scale - 1):
                    img.putpixel((border + x * scale + dx, border + y * scale + dy), colour)
    out = src.rsplit(".", 1)[0] + ".png"
    img.save(out)
    print("wrote", out)
