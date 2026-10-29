"""art/frames/*.png as C data for the mod (src/frames.h): each frame FRAME x FRAME words 0xRRGGBBAA, as
jfg_overlay_image takes them. Run after make_frames.py and render_frames.py.

    python art/pack_frames.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "frames"
OUT = HERE.parent / "src" / "frames.h"


def words(path):
    im = Image.open(path).convert("RGBA")
    px = im.tobytes()
    return im.size, [(px[i] << 24) | (px[i + 1] << 16) | (px[i + 2] << 8) | px[i + 3] for i in range(0, len(px), 4)]


def array(name, paths):
    size = None
    out = []
    for p in paths:
        s, w = words(p)
        assert size in (None, s), p
        size = s
        out.append("    {\n" + "\n".join("        " + ", ".join("0x%08X" % v for v in w[i:i + 8]) + ","
                                       for i in range(0, len(w), 8)) + "\n    },")
    return size, "static const unsigned int %s[%d][%d] = {\n%s\n};\n" % (name, len(paths), size[0] * size[1],
                                                                         "\n".join(out))


swirl = sorted(FRAMES.glob("swirl_*.png"))
burst = sorted(FRAMES.glob("burst_*.png"))
(s1, a), (s2, b), (s3, c) = array("swirl_frames", swirl), array("burst_frames", burst), array("core_frames",
                                                                                                [FRAMES / "core.png"])
assert s1 == s2 == s3
OUT.write_text("// Made by art/pack_frames.py from art/frames/*.png (the mod's own art): don't edit.\n"
               "#define FRAME_SIZE %d\n#define SWIRL_FRAMES %d\n#define BURST_FRAMES %d\n\n%s\n%s\n%s"
               % (s1[0], len(swirl), len(burst), a, b, c))
print(OUT, len(swirl), len(burst))
