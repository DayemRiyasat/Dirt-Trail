"""Track dressing, pickups, particle textures and UI plates."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFilter

from draw import Canvas, bezier, rot
from palette import (INK, INK_SOFT, SAND_50, SAND_100, CLAY_200, CLAY_300,
                     CLAY_400, RUST_500, EARTH_600, BARK_700, BARK_800,
                     SAGE_300, SAGE_500, SAGE_700, ORANGE, ORANGE_HI, CREAM,
                     STEEL, STEEL_HI, CHROME, RUBBER, shade)
from unityasset import write_sprite_meta, folder_meta

PROPS = "Assets/Sprites/Props"
FX = "Assets/Sprites/FX"
UI = "Assets/Sprites/UI"
OW = 3.0


def emit(c, folder, name, ppu=100, pivot=(0.5, 0.5), wrap=0, border=(0, 0, 0, 0)):
    path = "%s/%s.png" % (folder, name)
    c.save(path)
    write_sprite_meta(path, (c.w, c.h), ppu=ppu, pivot=pivot, wrap=wrap, border=border)
    return path


# ----------------------------------------------------------- rocks ---------
def gen_rocks():
    out = []
    specs = [("Rock_Small", 128, 96, 5, 909), ("Rock_Mid", 220, 160, 7, 313),
             ("Rock_Large", 340, 250, 8, 717)]
    for name, w, h, faces, seed in specs:
        rnd = random.Random(seed)
        c = Canvas(w, h, ss=4)
        cx, base = w / 2.0, h - 6.0
        rx, ry = w * 0.42, h * 0.78
        pts = []
        for i in range(faces * 2):
            a = math.pi + i * math.pi / (faces * 2 - 1)
            pts.append((cx + math.cos(a) * rx * rnd.uniform(0.82, 1.0),
                        base + math.sin(a) * ry * rnd.uniform(0.7, 1.0)))
        pts = [(cx - rx, base)] + pts + [(cx + rx, base)]
        c.shape(pts, CLAY_300, OW)
        # lit top-left facet, shadowed right
        mid = len(pts) // 2
        c.poly(pts[1:mid + 1] + [(cx, base)], shade(CLAY_300, 0.18))
        c.poly(pts[mid:-1] + [(cx, base)], shade(CLAY_300, -0.16))
        c.line(pts[1:-1], INK, OW)
        for _ in range(rnd.randint(2, 4)):                 # cracks
            a = (rnd.uniform(0.2, 0.8), rnd.uniform(0.15, 0.7))
            p = (cx - rx + 2 * rx * a[0], base - ry * a[1])
            c.line([p, (p[0] + rnd.uniform(-20, 20), p[1] + rnd.uniform(8, 26))],
                   shade(CLAY_300, -0.32), 2.4)
        c.grain(10, seed=seed)
        c.speckle(int(w * 0.5), BARK_800, (1, 2.6), seed=seed + 1, alpha=44)
        out.append(emit(c, PROPS, name, pivot=(0.5, 0.04)))
    return out


# ------------------------------------------------------- vegetation --------
def gen_plants():
    out = []

    # dry scrub bush
    for idx, seed in enumerate((21, 42)):
        rnd = random.Random(seed)
        c = Canvas(200, 150, ss=4)
        base = 144
        for layer, col in ((0, SAGE_700), (1, SAGE_500), (2, SAGE_300)):
            n = 16 - layer * 3
            for k in range(n):
                a = -180 + k * (180.0 / max(1, n - 1)) + rnd.uniform(-8, 8)
                ln = rnd.uniform(40, 92) * (1.0 - layer * 0.16)
                x0 = 100 + rnd.uniform(-26, 26)
                tip = (x0 + math.cos(math.radians(a)) * ln,
                       base + math.sin(math.radians(a)) * ln)
                c.line([(x0, base), tip], col, 4.6 - layer * 0.9)
        c.stroke([(100, base), (98, base - 22)], BARK_700, 7, OW)
        c.grain(9, seed=seed)
        out.append(emit(c, PROPS, "Shrub_%02d" % (idx + 1), pivot=(0.5, 0.04)))

    # saguaro
    c = Canvas(220, 420, ss=4)
    body = SAGE_700
    c.stroke([(112, 410), (108, 120)], body, 42, OW)
    c.stroke([(108, 264), (62, 258), (58, 176)], body, 30, OW)
    c.stroke([(110, 214), (162, 208), (168, 148)], body, 26, OW)
    for x, y0, y1 in ((112, 140, 400), (62, 190, 250), (162, 162, 200)):
        for dx in (-9, 0, 9):
            c.line([(x + dx, y0), (x + dx, y1)], shade(body, -0.22), 2.6)
    c.disc((104, 122), 3, shade(body, 0.2))
    c.grain(9, seed=61)
    out.append(emit(c, PROPS, "Saguaro", pivot=(0.5, 0.02)))
    return out


# ------------------------------------------------ course furniture ---------
def gen_furniture():
    out = []

    # marker post with a torn pennant
    c = Canvas(160, 300, ss=4)
    c.stroke([(74, 292), (78, 40)], BARK_700, 12, OW)
    for y in range(60, 290, 40):                            # weathered banding
        c.line([(69, y), (85, y + 3)], shade(BARK_700, 0.22), 4.0)
    flag = [(80, 46), (146, 62), (128, 86), (144, 108), (80, 96)]
    c.shape(flag, ORANGE, OW)
    c.line([(86, 58), (128, 70)], shade(ORANGE, -0.28), 3.0)
    c.grain(9, seed=71)
    out.append(emit(c, PROPS, "Marker_Post", pivot=(0.47, 0.02)))

    # stack of old tyres
    c = Canvas(280, 200, ss=4)
    for i, (x, y, r) in enumerate(((78, 158, 54), (186, 158, 54), (132, 76, 54))):
        c.outlined_disc((x, y), r, RUBBER, OW)
        c.ring((x, y), r - 14, shade(RUBBER, 0.22), 5)
        c.outlined_disc((x, y), 20, shade(CLAY_300, -0.1), OW)
        for k in range(14):
            p = rot((x + r - 4, y), (x, y), k * 26)
            c.disc(p, 4, shade(RUBBER, 0.16))
    c.grain(9, seed=73)
    c.speckle(180, CLAY_200, (1, 3), seed=74, alpha=50)
    out.append(emit(c, PROPS, "Tyre_Stack", pivot=(0.5, 0.03)))

    # finish banner cloth (the posts are separate marker posts in-scene)
    c = Canvas(560, 190, ss=4)
    c.shape([(8, 20), (552, 8), (548, 150), (300, 168), (12, 152)], EARTH_600, OW)
    c.shape([(20, 34), (540, 22), (536, 62), (24, 74)], ORANGE, OW * 0.7)
    for i in range(11):                                     # hazard chevrons
        x = 30 + i * 48
        c.poly([(x, 96), (x + 26, 96), (x + 12, 138), (x - 14, 138)], CREAM)
    c.line([(16, 88), (544, 76)], INK, 3.0)
    c.grain(10, seed=77)
    c.speckle(220, BARK_800, (1, 3.4), seed=78, alpha=40)
    out.append(emit(c, PROPS, "Finish_Banner", pivot=(0.5, 0.9)))

    # a wooden kicker ramp lip, used as set dressing on the big jumps
    c = Canvas(300, 160, ss=4)
    c.shape([(8, 152), (292, 152), (292, 118), (110, 30), (30, 26)], BARK_700, OW)
    for i in range(7):
        x = 40 + i * 36
        c.line([(x, 150), (x - 6, 60 + i * 8)], shade(BARK_700, 0.2), 4.0)
    c.grain(10, seed=81)
    out.append(emit(c, PROPS, "Ramp_Lip", pivot=(0.5, 0.03)))
    return out


# ----------------------------------------------------------- pickups -------
def _pickup_backing(c, cx, cy, r, tint):
    """Shared frame so both pickups read as one family."""
    c.outlined_disc((cx, cy), r, shade(tint, 0.55), OW)
    c.ring((cx, cy), r - 4, INK, 3.0)
    for k in range(8):                                      # bolt heads
        c.disc(rot((cx + r - 9, cy), (cx, cy), k * 45 + 22), 4.2, shade(tint, -0.2))


def gen_pickups():
    out = []

    # NITRO: a strapped fuel can
    c = Canvas(190, 190, ss=4)
    _pickup_backing(c, 95, 95, 84, ORANGE)
    c.shape([(58, 52), (126, 52), (134, 74), (134, 138), (56, 138), (56, 74)], ORANGE, OW)
    c.shape([(66, 62), (120, 62), (124, 96), (62, 96)], shade(ORANGE, -0.26), OW * 0.7)
    c.stroke([(72, 52), (72, 40), (100, 38), (100, 50)], STEEL, 8, OW)   # handle
    c.outlined_disc((120, 48), 11, STEEL_HI, OW)                          # cap
    c.line([(66, 116), (124, 116)], shade(ORANGE, 0.3), 3.4)
    c.grain(9, seed=91)
    out.append(emit(c, PROPS, "Pickup_Nitro", pivot=(0.5, 0.5)))

    # AIR: goggles, for the temporary air-control boost
    c = Canvas(190, 190, ss=4)
    _pickup_backing(c, 95, 95, 84, SAGE_500)
    c.shape([(48, 74), (142, 70), (146, 116), (128, 128), (62, 130), (44, 116)],
            SAGE_500, OW)
    c.shape([(58, 84), (132, 80), (134, 110), (60, 116)], (40, 46, 54), OW * 0.8)
    c.poly([(64, 88), (126, 85), (127, 104), (64, 108)], (132, 156, 166))
    c.line([(70, 94), (112, 91)], (206, 220, 224), 3.4)
    c.stroke([(44, 92), (26, 88)], shade(SAGE_500, -0.3), 9, OW)          # strap
    c.stroke([(146, 88), (164, 84)], shade(SAGE_500, -0.3), 9, OW)
    c.grain(9, seed=93)
    out.append(emit(c, PROPS, "Pickup_Air", pivot=(0.5, 0.5)))
    return out


# ------------------------------------------------------ particle art -------
def gen_fx():
    out = []

    # soft dust puff: radial falloff, slightly lumpy so it never reads as a blur
    S = 128
    c = Canvas(S, S, ss=2)
    rnd = random.Random(5)
    for _ in range(26):
        a = rnd.uniform(0, math.tau)
        d = rnd.uniform(0, 22)
        c.disc((S / 2 + math.cos(a) * d, S / 2 + math.sin(a) * d),
               rnd.uniform(18, 34), (255, 255, 255))
    c.img = c.img.filter(ImageFilter.GaussianBlur(radius=11 * c.ss))
    out.append(emit(c, FX, "Dust_Puff"))

    # dirt clod: small irregular chunk
    c = Canvas(48, 48, ss=4)
    rnd = random.Random(6)
    pts = [(24 + math.cos(a) * rnd.uniform(11, 19), 24 + math.sin(a) * rnd.uniform(11, 19))
           for a in [k * math.tau / 7 for k in range(7)]]
    c.shape(pts, EARTH_600, 2.4)
    c.disc((20, 19), 4, shade(EARTH_600, 0.22))
    out.append(emit(c, FX, "Dirt_Clod"))

    # spark streak for scrapes and hard landings
    c = Canvas(96, 24, ss=4)
    c.line([(6, 12), (90, 12)], (255, 236, 196), 7)
    c.line([(30, 12), (90, 12)], (255, 255, 240), 3.5)
    c.img = c.img.filter(ImageFilter.GaussianBlur(radius=1.6 * c.ss))
    out.append(emit(c, FX, "Spark_Streak"))

    # soft round shadow blob dropped under the bike
    S = 160
    c = Canvas(S, S, ss=2)
    c.d.ellipse([10 * c.ss, 52 * c.ss, 150 * c.ss, 108 * c.ss], fill=(0, 0, 0, 190))
    c.img = c.img.filter(ImageFilter.GaussianBlur(radius=9 * c.ss))
    out.append(emit(c, FX, "Ground_Shadow"))
    return out


# ------------------------------------------------------------- UI ----------
def gen_ui():
    out = []
    R = 26                                                   # 9-slice inset

    def plate(name, fill, edge, seed, ow=4.0):
        S = 96
        c = Canvas(S, S, ss=4)
        # deliberately imperfect rectangle: the corners are hand-cut, not rounded
        pts = [(7, 5), (S - 6, 8), (S - 5, S - 7), (6, S - 5)]
        c.poly(pts, fill)
        c.line(pts + [pts[0]], edge, ow)
        c.grain(11, seed=seed)
        c.speckle(140, BARK_800, (1, 2.4), seed=seed + 1, alpha=26)
        return emit(c, UI, name, border=(R, R, R, R))

    out.append(plate("Plate_Dark", (38, 28, 23), INK_SOFT, 31))
    out.append(plate("Plate_Sand", SAND_100, INK, 33))
    out.append(plate("Plate_Rust", RUST_500, INK, 35))

    # thin hazard stripe strip, tiles on X, used as a rule under headings
    c = Canvas(128, 24, ss=4)
    c.rect((0, 0, 128, 24), EARTH_600)
    for i in range(-1, 7):
        x = i * 22
        c.poly([(x, 24), (x + 11, 24), (x + 22, 0), (x + 11, 0)], ORANGE)
    c.grain(10, seed=37)
    out.append(emit(c, UI, "Stripe", wrap=1))

    # chevron used as the selection marker in menus
    c = Canvas(48, 48, ss=4)
    c.shape([(12, 6), (38, 24), (12, 42), (22, 24)], ORANGE, 3.0)
    out.append(emit(c, UI, "Chevron"))

    return out


def main():
    for folder in (PROPS, FX, UI):
        os.makedirs(folder, exist_ok=True)
        folder_meta(folder)
    made = gen_rocks() + gen_plants() + gen_furniture() + gen_pickups() + gen_fx() + gen_ui()
    for p in made:
        print("  ", p)


if __name__ == "__main__":
    main()
