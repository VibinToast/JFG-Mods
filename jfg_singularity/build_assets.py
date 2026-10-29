"""The pack's own objects and HUD icon. Each of art/models/blackhole.glb and core.glb (build_models.py) becomes a new
model with new textures (jfgformats.models.import_new, decomp MSR 9a: nothing from the ROM) and a new object type whose
definition is a copy of the player's own definition 427 (GeminiPowerup: a model, one model slot) with (MSR 9c):
    +0x00 f32 scale 1.0, +0x1C s16 behaviour 0x35 (no code runs), +0xE0 u32 the model (a fixup to the appended model);
    the black hole: +0xD0 s32 0 (no physics: it hovers where it is put); the core: the grenade's physics.
art/textures/hud_icon.png becomes a sprite and its 2D textures (sprites.write, MSR 9b): the HUD icon.
Writes assets/*.bin and jfg_assets.json; the mod finds them by name (jfg_asset_number "jfg_singularity:objtype_core",
"...:objtype_blackhole", "...:sprite_icon"). Run in WSL with the decomp's tools on the path:

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
# The black hole: no code, no physics (it hovers where it is put).
add_type("blackhole", add_model("blackhole"), [(0x00, f32(1.0)), (0x1C, "0035"), (0xD0, "00000000")])
# The thrown core: no code, the grenade's physics (MSR 9c: gravity, drag limits, collision sphere radius 8).
add_type("core", add_model("core"), [(0x00, f32(1.0)), (0x1C, "0035"), (0x118, f32(0.12)), (0x11C, f32(20.0)),
                                      (0x120, f32(0.06)), (0x110, f32(8.0))])

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
doc = {"entries": entries, "objtypes": types}
(HERE / "jfg_assets.json").write_text(json.dumps(doc, indent=2) + "\n")
print("files:", " ".join(files))
