"""The pack's own objects and HUD icons. Each of art/models/*.glb (build_models.py) becomes a new model with new
textures (jfgformats.models.import_new, decomp MSR 9a: nothing from the ROM) and a new object type whose definition is a
copy of the player's own definition 427 (a model, one model slot) with (MSR 9c):
    +0x00 f32 scale 1.0, +0x1C s16 behaviour 0x35 (no code runs), +0xD0 s32 0 (no physics: it stays where it is put),
    +0xE0 u32 the model (a fixup to the appended model).
The objects: the blast's wave, the wall-slam impact, the charge orb, and the cannon itself (for the hero's hand).
art/textures/hud_icon.png becomes a sprite and its 2D textures (sprites.write, MSR 9b): the HUD icon; hud_icon_big.png
becomes src/icon_big.h (the sharp icon for mods' HUDs, jfg_weapon_set_icon_image).
Writes assets/*.bin and jfg_assets.json; the mod finds them by name (jfg_asset_number
"jfg_concussion_cannon:objtype_wave", ..., "...:sprite_icon"). Run in WSL with the decomp's tools on the path:

    python3 build_assets.py ~/jfg/tools
"""
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "jfg" / "tools"))
from jfgformats import models, sprites  # noqa: E402
from jfgformats.png import read_png  # noqa: E402

TEX_TABLE, TEX_DATA = 1, 0            # the 3D texture set
TEX2D_TABLE, TEX2D_DATA = sprites.TEX2D_TABLE_ASSET, sprites.TEX2D_DATA_ASSET   # the 2D texture set (3 / 2)
SPRITE_TABLE, SPRITE_DATA = sprites.SPRITE_TABLE_ASSET, sprites.SPRITE_ASSET    # the sprites (0x16 / 0x15)
MODEL_TABLE, MODEL_DATA = 0x26, 0x27
OBJDEF_TABLE, OBJDEF_DATA = 0x2E, 0x2F
HOST_DEF = 427

out = HERE / "assets"
out.mkdir(exist_ok=True)
entries, files = [], []



def add_model(name):
    """A .glb as a new model with its new textures; returns the model's append name."""
    r = models.import_new(str(HERE / "art" / "models" / (name + ".glb")), name=name, log=print)
    for t in r["textures"]:
        tname = "tex_%s_%s" % (name, t["key"])
        path = out / (tname + ".bin")
        path.write_bytes(t["entry"])
        entries.append({"table": TEX_TABLE, "data": TEX_DATA, "append": tname, "file": "assets/" + path.name})
        files.append("assets/" + path.name)
        print(name, "texture", t["key"], t["width"], "x", t["height"], "format", t["format"], "alpha", t["alpha"])
    path = out / ("model_%s.bin" % name)
    path.write_bytes(r["packed"])
    files.append("assets/" + path.name)
    entries.append({"table": MODEL_TABLE, "data": MODEL_DATA, "append": "model_" + name, "file": "assets/" + path.name,
                    "packed": True,
                    "fixups": [{"at": f["at"], "type": f["type"], "ref": "tex_%s_%s" % (name, f["texture"]),
                                "add": f["or"]} for f in r["textureRefs"]]})
    return "model_" + name


def add_type(name, model, sets):
    entries.append({"table": OBJDEF_TABLE, "data": OBJDEF_DATA, "append": "objdef_" + name, "copyOf": HOST_DEF,
                    "set": [{"at": at, "hex": hx} for at, hx in sets],
                    "fixups": [{"at": 0xE0, "type": "u32", "ref": model}]})
    types.append({"append": "objtype_" + name, "def": "objdef_" + name})


def f32(v):
    return struct.pack(">f", v).hex()


types = []
HOVER = [(0x00, f32(1.0)), (0x1C, "0035"), (0xD0, "00000000")]
# The wave and the impact fade out: behaviour 0x7E (no code; its draw copies the low byte of obj +0x8C into the opacity
# each frame, where 0x35 resets it to 0xFF: decomp MSR 11). The mod writes the opacity there (0 = not drawn).
FADING = [(0x00, f32(1.0)), (0x1C, "007E"), (0xD0, "00000000")]
for name in ("wave", "impact"):
    add_type(name, add_model(name), FADING)
for name in ("charge", "cannon"):
    add_type(name, add_model(name), HOVER)

# The HUD icon (MSR 9b): a sprite of one frame, its 2D texture pieces appended in order after it is numbered.
w, h, rgba = read_png((HERE / "art" / "textures" / "hud_icon.png").read_bytes())
icon = sprites.write([(w, h, rgba)], anchor=sprites.HUD_ICON_ANCHOR, origin=(39 - w // 2, 13 - h // 2))
for k, e in enumerate(icon["entries"]):
    path = out / ("tex2d_icon_%d.bin" % k)
    path.write_bytes(e)
    files.append("assets/" + path.name)
    entries.append({"table": TEX2D_TABLE, "data": TEX2D_DATA, "append": "tex2d_icon_%d" % k, "file": "assets/" + path.name})
path = out / "sprite_icon.bin"
path.write_bytes(icon["sprite"])
files.append("assets/" + path.name)
entries.append({"table": SPRITE_TABLE, "data": SPRITE_DATA, "append": "sprite_icon", "file": "assets/" + path.name,
                "fixups": [{"at": f["at"], "type": f["type"], "ref": "tex2d_icon_%d" % f["texture"]}
                           for f in icon["fixups"]]})
print("icon", w, "x", h, len(icon["entries"]), "piece(s)")
# The big icon, as a C array of 0xRRGGBBAA.
w, h, rgba = read_png((HERE / "art" / "textures" / "hud_icon_big.png").read_bytes())
words = ["0x%02X%02X%02X%02X" % tuple(rgba[i:i + 4]) for i in range(0, len(rgba), 4)]
lines = ["// Made from art/textures/hud_icon_big.png (art/make_textures.py; the mod's own art): don't edit.",
         "#define ICON_BIG_W %d" % w, "#define ICON_BIG_H %d" % h,
         "static const unsigned int icon_big[%d] = {" % len(words)]
lines += ["    " + ", ".join(words[i:i + 8]) + "," for i in range(0, len(words), 8)]
lines.append("};")
(HERE / "src" / "icon_big.h").write_text("\n".join(lines) + "\n")
print("big icon", w, "x", h)
doc = {"entries": entries, "objtypes": types}
(HERE / "jfg_assets.json").write_text(json.dumps(doc, indent=2) + "\n")
print("files:", " ".join(files))
