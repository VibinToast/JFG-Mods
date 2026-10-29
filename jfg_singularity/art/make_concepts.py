"""Singularity's concept sheet, from the mod's own art (nothing from the game), into concepts/singularity_concept.png:
the models (previews/models.png), the HUD icon (textures/hud_icon_big.png), and the swirl and burst frames.

    python art/make_concepts.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parent
OUT = ART.parent / "concepts"
BG = (32, 28, 44, 255)
TEXT = (230, 220, 255, 255)


def tile(paths, size):
    """The images side by side, each fitted into a size x size square."""
    row = Image.new("RGBA", (size * len(paths), size), BG)
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGBA")
        im.thumbnail((size, size))
        row.alpha_composite(im, (i * size + (size - im.width) // 2, (size - im.height) // 2))
    return row


def main():
    models = Image.open(ART / "previews" / "models.png").convert("RGBA")
    icon = Image.open(ART / "textures" / "hud_icon_big.png").convert("RGBA")
    frames = ART / "frames"
    swirl = tile([frames / ("swirl_%02d.png" % i) for i in range(0, 16, 2)], 150)
    burst = tile([frames / ("burst_%02d.png" % i) for i in range(0, 12, 2)] + [frames / "core.png"], 150)
    w = max(models.width + icon.width + 40, swirl.width, burst.width) + 40
    h = 60 + max(models.height, icon.height) + 40 + 30 + swirl.height + 30 + 30 + burst.height + 30
    sheet = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(sheet)
    d.text((20, 20), "Singularity: a thrown black hole (the mod's own models, icon and effect frames)", fill=TEXT)
    y = 60
    sheet.alpha_composite(models, (20, y))
    sheet.alpha_composite(icon, (models.width + 60, y + (models.height - icon.height) // 2))
    y += max(models.height, icon.height) + 40
    d.text((20, y), "Swirl (looping)", fill=TEXT)
    sheet.alpha_composite(swirl, (20, y + 30))
    y += 30 + swirl.height + 30
    d.text((20, y), "Collapse burst, and the core", fill=TEXT)
    sheet.alpha_composite(burst, (20, y + 30))
    OUT.mkdir(exist_ok=True)
    sheet.convert("RGB").save(OUT / "singularity_concept.png")
    print("wrote", OUT / "singularity_concept.png", sheet.size)


if __name__ == "__main__":
    main()
