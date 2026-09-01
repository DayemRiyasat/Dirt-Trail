"""Dirt bike: body, rider and wheels, two liveries."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import bikegeom as G
from draw import Canvas, bezier, jitter_path, rot
from palette import (INK, INK_SOFT, LIVERY, CHROME, STEEL, STEEL_HI, RUBBER,
                     RUBBER_HI, CLAY_300, EARTH_600, shade)
from unityasset import write_sprite_meta, folder_meta

OUT = "Assets/Sprites/Bike"
OW = 3.2                      # the single outline weight used across the game

RA, FA = G.REAR_AXLE, G.FRONT_AXLE


def _disc_mask(c, center, r):
    m = Image.new("L", c.img.size, 0)
    md = ImageDraw.Draw(m)
    s = c.ss
    md.ellipse([(center[0] - r) * s, (center[1] - r) * s,
                (center[0] + r) * s, (center[1] + r) * s], fill=255)
    return m


# ---------------------------------------------------------------- body ------
def draw_body(key):
    L = LIVERY[key]
    c = Canvas(G.BODY_W, G.BODY_H, ss=4)

    prim, prim_d = L["primary"], L["primary_d"]
    plate = L["plate"]

    # rear fender + side number plate, drawn first so the frame overlaps them
    c.shape([(268, 150), (222, 148), (168, 158), (138, 174),
             (146, 190), (186, 176), (232, 168), (270, 168)], prim, OW)
    c.shape([(214, 166), (272, 158), (280, 208), (222, 216)], plate, OW)
    c.line([(226, 176), (272, 170)], shade(plate, -0.25), 2.4)

    # swingarm
    c.shape([(300, 240), (312, 258), (214, 310), (192, 296)], STEEL, OW)
    c.shape([(300, 256), (306, 268), (212, 314), (200, 304)], shade(STEEL, -0.3), OW * 0.7)

    # countershaft sprocket, rear sprocket, chain runs
    c.outlined_disc((300, 252), 20, shade(STEEL, 0.2), OW)
    c.outlined_disc(RA, 34, shade(STEEL, 0.15), OW)
    c.outlined_disc(RA, 16, STEEL, OW * 0.7)
    for i in range(18):
        c.disc(rot((RA[0] + 34, RA[1]), RA, i * 20), 3.4, INK_SOFT)
    c.line([(300, 232), (RA[0], RA[1] - 34)], INK_SOFT, 4.2)
    c.line([(300, 272), (RA[0], RA[1] + 34)], INK_SOFT, 4.2)

    # rear shock with a visible spring
    c.stroke([(322, 168), (296, 246)], STEEL_HI, 7, OW)
    for i in range(7):
        t = i / 6.0
        y = 182 + t * 52
        x = 318 - t * 20
        c.line([(x - 11, y + 5), (x + 11, y - 5)], shade(prim, -0.15), 5.0)
    c.stroke([(292, 250), (272, 268), (300, 262)], STEEL, 5, OW * 0.8)

    # exhaust: header out the front of the cylinder, sweeping down and back
    hdr = bezier((350, 168), (404, 190), (388, 240), (322, 240), 26)
    hdr += bezier((322, 240), (296, 240), (288, 224), (276, 212), 14)
    c.stroke(hdr, CHROME, 9, OW)
    c.line(hdr, shade(CHROME, 0.35), 3.0)
    c.shape([(276, 226), (280, 210), (214, 190), (206, 202), (212, 216)],
            shade(STEEL, 0.05), OW)
    c.line([(218, 199), (270, 216)], shade(STEEL, -0.3), 2.6)

    # engine cases, cylinder, head
    c.shape([(286, 214), (352, 206), (372, 246), (356, 282), (300, 286), (280, 254)],
            shade(STEEL, -0.05), OW)
    for i in range(5):
        x = 296 + i * 14
        c.line([(x, 232), (x + 6, 274)], shade(STEEL, -0.35), 2.4)
    c.shape([(326, 208), (362, 200), (372, 152), (338, 146)], shade(STEEL, 0.1), OW)
    for i in range(6):
        y = 156 + i * 9
        c.line([(332 + i * 0.6, y + 4), (368, y - 2)], shade(STEEL, -0.3), 2.2)
    c.shape([(336, 150), (376, 142), (380, 128), (334, 134)], shade(STEEL, 0.2), OW)

    # frame: hand-wobbled so the tubes are not laser straight
    tubes = [
        [(492, 152), (430, 176), (378, 190)],
        [(492, 158), (438, 214), (372, 236)],
        [(300, 244), (300, 190), (352, 172)],
        [(300, 190), (262, 168)],
        [(378, 190), (322, 178), (300, 190)],
    ]
    for i, t in enumerate(tubes):
        c.stroke(jitter_path(t, 0.8, seed=i + len(key), subdiv=4), prim_d, 9, OW)

    # tank + radiator shrouds
    c.shape([(370, 178), (406, 158), (452, 152), (474, 162), (462, 190), (410, 200)], prim, OW)
    c.line([(392, 168), (452, 161)], shade(prim, 0.28), 3.0)
    c.shape([(392, 156), (462, 148), (486, 168), (468, 214), (416, 210), (394, 186)], prim, OW)
    c.shape([(408, 166), (462, 158), (470, 178), (418, 188)], L["accent"], OW * 0.7)

    # seat
    c.shape([(262, 162), (300, 150), (372, 144), (416, 148), (404, 162),
             (330, 168), (272, 176)], L["seat"], OW)
    c.line([(276, 168), (398, 152)], shade(L["seat"], 0.22), 2.6)

    # forks and triple clamp
    c.stroke([(500, 146), (556, 268)], shade(STEEL, 0.15), 11, OW)
    c.stroke([(534, 220), (FA[0], FA[1])], CHROME, 7, OW)
    c.shape([(486, 138), (516, 132), (520, 156), (490, 162)], STEEL, OW)
    c.outlined_disc(FA, 13, STEEL, OW)

    # front fender + rounded number plate raked back with the forks
    c.stroke(bezier((470, 214), (512, 186), (582, 188), (614, 212), 18), prim, 11, OW)
    c.shape([(486, 152), (500, 144), (516, 146), (524, 162), (522, 188),
             (510, 200), (494, 198), (484, 182)], plate, OW)
    c.line([(492, 164), (516, 168)], shade(plate, -0.22), 2.4)

    # bars, pad, grip, lever
    c.stroke([(500, 140), (496, 112)], STEEL, 8, OW)
    c.stroke([(496, 112), (472, 100), (444, 96)], shade(STEEL, 0.25), 8, OW)
    c.stroke([(486, 104), (462, 100)], prim, 6, OW * 0.7)
    c.stroke([(452, 96), (430, 94)], RUBBER, 10, OW)
    c.stroke([(468, 104), (446, 112)], CHROME, 4, OW * 0.7)

    # footpeg
    c.stroke([(346, 312), (368, 318)], STEEL, 7, OW)

    # wear pass: grain plus asymmetric mud, heavier low and to the rear
    c.grain(9, seed=7)
    c.speckle(90, EARTH_600, (1.5, 4.5), box=(150, 230, 620, 340), seed=11, alpha=70)
    c.speckle(40, CLAY_300, (1, 3), box=(180, 140, 560, 240), seed=13, alpha=45)

    path = "%s/Body_%s.png" % (OUT, key.capitalize())
    c.save(path)
    write_sprite_meta(path, (G.BODY_W, G.BODY_H), ppu=G.PPU,
                      pivot=G.pivot_norm(G.BODY_PIVOT, G.BODY_W, G.BODY_H))
    return path


# --------------------------------------------------------------- wheels -----
def draw_wheel(key, rear):
    L = LIVERY[key]
    c = Canvas(G.WHEEL_W, G.WHEEL_H, ss=4)
    C, R = G.WHEEL_C, G.WHEEL_R

    c.outlined_disc(C, R, RUBBER, OW)
    for i in range(26):
        a = i * (360 / 26) + (3 if i % 2 else -3)
        p = rot((C[0] + R - 5, C[1]), C, a)
        q = rot((C[0] + R + 4.5, C[1]), C, a)
        c.line([p, q], RUBBER_HI if i % 3 else shade(RUBBER, 0.18), 7.5)
    c.ring(C, R - 13, shade(RUBBER, 0.14), 2.2)
    c.ring(C, R - 1, INK, 2.6)

    # rim, then punch the wheel interior back to transparent so spokes read
    c.outlined_disc(C, R - 26, shade(STEEL, 0.3), OW)
    c.img.paste(Image.new("RGBA", c.img.size, (0, 0, 0, 0)), (0, 0), _disc_mask(c, C, R - 33))
    c.d = ImageDraw.Draw(c.img)

    for i in range(20):
        a = i * 18 + (6 if i % 2 else -6)
        p = rot((C[0] + R - 30, C[1]), C, a)
        q = rot((C[0] + 20, C[1]), C, a)
        c.line([p, q], STEEL_HI if i % 2 else STEEL, 2.6)

    if rear:
        c.outlined_disc(C, 34, shade(STEEL, 0.1), OW)
        for i in range(18):
            c.disc(rot((C[0] + 34, C[1]), C, i * 20), 3.4, INK_SOFT)
    else:
        c.outlined_disc(C, 33, shade(STEEL, 0.22), OW * 0.7)
        for i in range(6):
            c.disc(rot((C[0] + 24, C[1]), C, i * 60 + 12), 4.2, INK_SOFT)
    c.outlined_disc(C, 19, shade(STEEL, 0.35), OW)
    c.disc(C, 7, INK_SOFT)
    # one painted spoke, so wheel rotation is legible at speed
    c.line([rot((C[0] + 15, C[1]), C, 40), rot((C[0] + 74, C[1]), C, 40)], L["primary"], 4)

    c.grain(8, seed=3)
    c.speckle(60, EARTH_600, (1, 3.5), seed=5, alpha=75)

    name = "Wheel_Rear" if rear else "Wheel_Front"
    path = "%s/%s_%s.png" % (OUT, name, key.capitalize())
    c.save(path)
    write_sprite_meta(path, (G.WHEEL_W, G.WHEEL_H), ppu=G.PPU, pivot=(0.5, 0.5))
    return path


# ---------------------------------------------------------------- rider -----
def draw_rider(key):
    """Attack position: standing on the pegs, knees bent, elbows up."""
    L = LIVERY[key]
    c = Canvas(G.RIDER_W, G.RIDER_H, ss=4)
    ow = 3.6
    peg = G.RIDER_PEG
    boot = (48, 44, 42)
    skin = (206, 156, 118)

    # far leg and far arm first, in shadow, offset back a touch
    c.stroke([(190, 292), (166, 352), (184, 410)], shade(L["pants"], -0.3), 26, ow)
    c.stroke([(184, 410), (212, 422)], shade(boot, -0.25), 23, ow)
    c.stroke([(232, 216), (268, 232), (288, 216)], shade(L["jersey"], -0.32), 19, ow)

    # near leg: knee bent hard, boot planted flat on the peg
    c.stroke([(206, 296), (190, 352), (212, 414)], L["pants"], 29, ow)
    c.shape([(182, 334), (222, 328), (228, 370), (188, 376)], shade(STEEL, 0.2), ow * 0.8)
    c.stroke([(212, 414), peg, (250, 420)], boot, 26, ow)
    c.line([(196, 402), (240, 398)], shade(boot, 0.28), 3.4)

    # torso, chest pitched forward over the tank
    c.shape([(180, 300), (186, 240), (212, 202), (250, 190), (272, 214),
             (262, 258), (232, 302)], L["jersey"], ow)
    c.shape([(196, 224), (250, 212), (262, 244), (208, 258)], L["jersey_d"], ow * 0.8)
    c.line([(202, 236), (256, 224)], shade(L["jersey"], -0.2), 2.4)
    c.stroke([(214, 208), (244, 200)], shade(L["jersey"], 0.16), 13, ow * 0.8)   # shoulder
    c.stroke([(214, 208), (250, 200)], shade(L["pants"], 0.15), 10, ow * 0.8)   # neck brace

    # near arm: elbow up and out, hand closing on the grip
    c.stroke([(246, 200), (284, 212), (292, 202)], L["jersey"], 21, ow)
    c.stroke([(290, 204), (298, 202)], skin, 14, ow)
    c.outlined_disc((300, 202), 11, shade(L["pants"], 0.1), ow)

    # helmet drawn as one silhouette: dome, brow peak and chin bar are one shell
    shell = [(220, 148), (224, 128), (240, 116), (266, 114), (286, 124),
             (296, 138), (322, 140), (324, 156), (300, 158), (302, 178),
             (294, 196), (274, 204), (250, 200), (236, 188), (226, 170)]
    c.shape(shell, L["helmet"], ow)
    c.line([(296, 140), (322, 145)], shade(L["helmet"], -0.3), 2.8)      # peak seam
    c.shape([(262, 146), (298, 152), (296, 174), (260, 168)], (40, 46, 54), ow * 0.9)
    c.poly([(266, 152), (292, 157), (291, 168), (265, 163)], (128, 150, 160))
    c.line([(268, 156), (286, 159)], (196, 212, 216), 2.4)               # lens glint
    for i in range(3):                                                    # chin vent
        c.line([(258 + i * 9, 186), (261 + i * 9, 194)], shade(L["helmet"], -0.35), 2.6)
    c.line([(226, 136), (250, 122)], shade(L["helmet"], -0.22), 3.2)     # shell seam

    c.grain(8, seed=17)
    c.speckle(70, EARTH_600, (1.5, 4), box=(150, 300, 280, 440), seed=19, alpha=80)

    path = "%s/Rider_%s.png" % (OUT, key.capitalize())
    c.save(path)
    write_sprite_meta(path, (G.RIDER_W, G.RIDER_H), ppu=G.PPU,
                      pivot=G.pivot_norm(G.RIDER_PEG, G.RIDER_W, G.RIDER_H))
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    folder_meta(OUT)
    for key in ("scout", "mule"):
        for p in (draw_body(key), draw_wheel(key, True), draw_wheel(key, False), draw_rider(key)):
            print("  ", p)


if __name__ == "__main__":
    main()
