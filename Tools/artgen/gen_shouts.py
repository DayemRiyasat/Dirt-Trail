"""Comic burst sprites: the noises the game makes, drawn rather than typeset.

Each one is a jagged or billowed shape with heavy outlined lettering sitting on
it, in the game's own palette rather than the primary-colour rainbow a comic
sheet would use - the bursts have to land on dirt without looking like they
came from a different game.

The lettering is DejaVu Sans Bold, which is open-licensed, sheared for lean and
then dilated into a thick ink outline. Nothing is typeset at runtime: these are
flat PNGs, so there is no font dependency in the build.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from palette import (INK, SAND_50, SAND_100, CLAY_200, CLAY_300, CLAY_400,
                     RUST_500, EARTH_600, BARK_700, BARK_800, SAGE_500,
                     SAGE_700, ORANGE, ORANGE_HI, CREAM, mix, shade)
from unityasset import write_sprite_meta, folder_meta

OUT = "Assets/Sprites/Shouts"
W, H = 620, 340
SS = 2
PPU = 110.0

FONT = None
for candidate in (
    os.path.join(os.path.dirname(__file__), "DejaVuSans-Bold.ttf"),
    r"C:\Users\duari\AppData\Local\Programs\Python\Python311\Lib\site-packages"
    r"\matplotlib\mpl-data\fonts\ttf\DejaVuSans-Bold.ttf",
):
    if os.path.exists(candidate):
        FONT = candidate
        break


# ------------------------------------------------------------- burst shapes --
def spiked(cx, cy, rx, ry, points, jag, seed, phase=0.0):
    """Classic star burst: long spikes alternating with short notches."""
    rnd = random.Random(seed)
    out = []
    for i in range(points * 2):
        a = phase + i * math.pi / points
        long_spike = i % 2 == 0
        k = 1.0 if long_spike else jag
        k *= rnd.uniform(0.88, 1.12)
        out.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return out


def billowed(cx, cy, rx, ry, lobes, seed):
    """Cloud puff: overlapping arcs, for the soft noises."""
    rnd = random.Random(seed)
    out = []
    steps = lobes * 8
    for i in range(steps):
        a = i / steps * math.tau
        wobble = 1.0 + 0.17 * math.sin(a * lobes + rnd.random() * 0.2)
        out.append((cx + math.cos(a) * rx * wobble, cy + math.sin(a) * ry * wobble))
    return out


# ---------------------------------------------------------------- lettering --
def word_image(text, fill, max_w, max_h, italic=0.22):
    """Heavy lettering with an ink outline, sheared for lean.

    Fitted to a box rather than to a target width, so a three-letter shout and a
    nine-letter one end up the same size on screen instead of one filling the
    frame and the other overflowing it.
    """
    size = 12
    font = ImageFont.truetype(FONT, size)
    while size < 400:
        probe = ImageFont.truetype(FONT, size + 4)
        b = probe.getbbox(text)
        w = (b[2] - b[0]) * (1.0 + italic * 0.5) + size * 0.5   # shear + outline
        h = (b[3] - b[1]) * 1.35
        if w > max_w or h > max_h:
            break
        size += 4
        font = probe

    box = font.getbbox(text)
    tw, th = box[2] - box[0], box[3] - box[1]
    pad = int(size * 0.55)
    img = Image.new("L", (tw + pad * 2, th + pad * 2), 0)
    ImageDraw.Draw(img).text((pad - box[0], pad - box[1]), text, font=font, fill=255)

    # lean, the way comic lettering always leans
    shear = int(img.height * italic)
    img = img.transform((img.width + shear, img.height), Image.AFFINE,
                        (1, italic, -shear * 0.5, 0, 1, 0), resample=Image.BICUBIC)

    # dilate the glyph mask into an outline by stamping it around a circle
    ring = max(3, int(size * 0.13))
    outline = Image.new("L", (img.width + ring * 4, img.height + ring * 4), 0)
    for i in range(20):
        a = i / 20.0 * math.tau
        outline.paste(img, (int(ring * 2 + math.cos(a) * ring),
                            int(ring * 2 + math.sin(a) * ring)), img)
    outline = outline.filter(ImageFilter.MaxFilter(3))

    glyph = Image.new("L", outline.size, 0)
    glyph.paste(img, (ring * 2, ring * 2), img)

    out = Image.new("RGBA", outline.size, (0, 0, 0, 0))
    # hard offset shadow, then ink, then the colour, then a top highlight
    shadow = Image.new("RGBA", outline.size, (*BARK_800, 150))
    out.paste(shadow, (int(ring * 0.9), int(ring * 1.1)), outline)
    out.paste(Image.new("RGBA", outline.size, (*INK, 255)), (0, 0), outline)
    out.paste(Image.new("RGBA", outline.size, (*fill, 255)), (0, 0), glyph)

    band = Image.new("L", outline.size, 0)
    ImageDraw.Draw(band).rectangle([0, 0, outline.size[0], int(outline.size[1] * 0.44)],
                                   fill=255)
    band = Image.composite(glyph, Image.new("L", outline.size, 0), band)
    out.paste(Image.new("RGBA", outline.size, (*mix(fill, SAND_50, 0.45), 255)), (0, 0), band)
    return out


# ------------------------------------------------------------------- bursts --
def burst(word, shape, burst_fill, rim, text_fill, seed, tilt=-6.0, ticks=True):
    canvas = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    cx, cy = W * SS / 2, H * SS / 2

    # Fixed burst radii: every shout is the same size on screen, whatever the
    # word, and nothing can grow past the edge of its own sprite.
    rx = W * SS * 0.38
    ry = H * SS * 0.36
    letters = word_image(word, text_fill,
                         max_w=rx * 2 * 0.76, max_h=ry * 2 * 0.52)

    if shape == "cloud":
        pts = billowed(cx, cy, rx, ry, lobes=9, seed=seed)
    elif shape == "blast":
        pts = spiked(cx, cy, rx * 1.06, ry * 1.12, points=8, jag=0.62, seed=seed, phase=0.2)
    else:
        pts = spiked(cx, cy, rx, ry, points=13, jag=0.71, seed=seed)

    ink_w = int(9 * SS)
    d.polygon(pts, fill=(*rim, 255))
    inner = [(cx + (x - cx) * 0.90, cy + (y - cy) * 0.90) for x, y in pts]
    d.polygon(inner, fill=(*burst_fill, 255))
    d.line(pts + [pts[0]], fill=(*INK, 255), width=ink_w, joint="curve")
    d.line(inner + [inner[0]], fill=(*shade(rim, -0.25), 255), width=int(ink_w * 0.4),
           joint="curve")

    if ticks:
        rnd = random.Random(seed + 7)
        for _ in range(14):
            a = rnd.uniform(0, math.tau)
            r0 = rnd.uniform(1.06, 1.13)
            r1 = r0 + rnd.uniform(0.05, 0.12)
            d.line([(cx + math.cos(a) * rx * r0, cy + math.sin(a) * ry * r0),
                    (cx + math.cos(a) * rx * r1, cy + math.sin(a) * ry * r1)],
                   fill=(*INK, 255), width=int(4 * SS))

    canvas.alpha_composite(letters, (int(cx - letters.width / 2),
                                     int(cy - letters.height / 2)))
    canvas = canvas.rotate(tilt, resample=Image.BICUBIC, center=(cx, cy))
    return canvas.resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ recipes --
# word, shape, burst fill, rim, text colour, tilt
SHOUTS = {
    "flip": [
        ("BRAAAP!", "star", ORANGE, ORANGE_HI, CREAM, -7),
        ("WHIP!", "blast", CREAM, SAND_100, RUST_500, 5),
        ("SEND IT!", "star", RUST_500, ORANGE, CREAM, -4),
        ("YEEHAW!", "blast", ORANGE_HI, CREAM, EARTH_600, 6),
    ],
    "bigflip": [
        ("BRAAAAAP!", "star", ORANGE, CREAM, CREAM, -8),
        ("GET SOME!", "blast", RUST_500, ORANGE_HI, CREAM, 4),
        ("BOOM!", "star", ORANGE_HI, CREAM, RUST_500, -5),
    ],
    "air": [
        ("WHOOOSH!", "cloud", SAND_100, CREAM, EARTH_600, -3),
        ("WHEEE!", "cloud", CREAM, SAND_100, RUST_500, 5),
        ("FLOATY!", "cloud", CLAY_200, SAND_100, EARTH_600, -4),
    ],
    "perfect": [
        ("STUCK IT!", "star", SAGE_500, CLAY_200, CREAM, -5),
        ("NAILED IT!", "blast", CREAM, SAGE_500, SAGE_700, 4),
        ("SMOOTH!", "star", CLAY_200, SAGE_500, EARTH_600, -6),
    ],
    "wipeout": [
        ("KRUNCH!", "blast", BARK_700, RUST_500, CREAM, -9),
        ("OOF!", "star", RUST_500, BARK_700, CREAM, 7),
        ("SMACK!", "blast", EARTH_600, ORANGE, CREAM, -6),
        ("YARD SALE!", "star", BARK_700, ORANGE, SAND_100, 5),
    ],
    "nitro": [("FWOOSH!", "cloud", ORANGE, ORANGE_HI, CREAM, -4)],
    "airPickup": [("ZIP!", "star", SAGE_500, CLAY_200, CREAM, 6)],
}


def main():
    if FONT is None:
        raise SystemExit("no bold font found for the lettering")
    os.makedirs(OUT, exist_ok=True)
    folder_meta(OUT)

    manifest = {}
    seed = 100
    for category, entries in SHOUTS.items():
        names = []
        for word, shape, fill, rim, text, tilt in entries:
            slug = "".join(ch for ch in word if ch.isalnum()) or "SHOUT"
            img = burst(word, shape, fill, rim, text, seed, tilt=tilt,
                        ticks=shape != "cloud")
            path = "%s/%s.png" % (OUT, slug)
            img.save(path)
            write_sprite_meta(path, (W, H), ppu=PPU, pivot=(0.5, 0.5))
            names.append(path)
            seed += 13
        manifest[category] = names
        print("  %-10s %s" % (category, ", ".join(os.path.basename(n) for n in names)))
    return manifest


if __name__ == "__main__":
    main()
