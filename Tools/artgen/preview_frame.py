"""Approximate what the camera sees, to check scale and composition offline.

Not the Unity renderer: it stacks the parallax layers, fills the terrain from
the sampled spline, drops the props in, and pastes the bike. Enough to catch a
bike that is too small or a horizon in the wrong place.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import bikegeom as BG
import track_profile as TP
import themes as TH
from build_track import COLLIDER_OFFSET, LAYERS, PROP_SET

TRACK = TP.TRACKS["RidgeRun"]
THEME = TH.RIDGE

PPU = 32                       # preview pixels per world unit
W, H = 1600, 900
ORTHO = 12.5                   # must match RiderCamera.baseSize


def world_to_px(cam, p):
    return ((p[0] - cam[0]) * PPU + W / 2.0,
            H / 2.0 - (p[1] - cam[1]) * PPU)


def paste_layer(img, cam, art, parallax, vertical, scale, y_offset, tiles=5):
    """Mirror ParallaxLayer: x = anchor + camX * parallax, y = origin + camY * vp."""
    src = Image.open("Assets/Sprites/Parallax/%s/%s_%s.png" % (THEME["key"], THEME["key"], art)).convert("RGBA")
    unit_w = src.width / 40.0 * scale          # parallax art is 40 ppu
    unit_h = src.height / 40.0 * scale
    layer = src.resize((max(1, int(unit_w * PPU)), max(1, int(unit_h * PPU))),
                       Image.LANCZOS)

    anchor_x = round((cam[0] - cam[0] * parallax) / unit_w) * unit_w
    cx = anchor_x + cam[0] * parallax
    cy = y_offset + cam[1] * vertical

    for i in range(-tiles // 2, tiles // 2 + 1):
        px, py = world_to_px(cam, (cx + i * unit_w, cy))
        img.alpha_composite(layer, (int(px - layer.width / 2),
                                    int(py - layer.height / 2)))


def draw_terrain(img, cam):
    d = ImageDraw.Draw(img)
    poly = TRACK.offset_polyline(TRACK.sample(16), COLLIDER_OFFSET)

    left = cam[0] - W / (2.0 * PPU) - 6
    right = cam[0] + W / (2.0 * PPU) + 6
    band = [p for p in poly if left <= p[0] <= right]
    if not band:
        return
    pts = [world_to_px(cam, p) for p in band]

    fill = Image.open("Assets/Sprites/Terrain/%s/%s Fill.png" % (THEME["key"], THEME["key"])).convert("RGBA")
    tile = fill.resize((int(2.56 * PPU), int(2.56 * PPU)), Image.LANCZOS)
    ground = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for ty in range(0, H, tile.height):
        for tx in range(0, W, tile.width):
            ground.alpha_composite(tile, (tx, ty))

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts + [(pts[-1][0], H), (pts[0][0], H)], fill=255)
    img.paste(ground, (0, 0), mask)

    # crust band and ink line, standing in for the edge sprite
    d.line([(x, y + 2) for x, y in pts], fill=(*THEME["crust"], 255), width=int(0.42 * PPU))
    d.line(pts, fill=(34, 24, 20, 255), width=max(2, int(0.14 * PPU)))


def draw_props(img, cam):
    rnd = random.Random(20260830)
    bounds = TRACK.section_bounds()
    # Same theme filter the scene builder uses, so the preview does not put
    # cacti in a quarry.
    allowed = {
        "mesa": PROP_SET,
        "quarry": [p for p in PROP_SET if p[0].startswith("Rock") or p[0] == "Tyre_Stack"],
        "dune": [p for p in PROP_SET if p[0].startswith("Rock") or p[0].startswith("Shrub")],
    }[THEME["silhouette"]]
    base_density = {"mesa": 0.55, "quarry": 0.75, "dune": 0.28}[THEME["silhouette"]]
    weights = [w for _n, w, _s in allowed]

    for section, (x0, x1) in bounds.items():
        busy = 1.5 if section in TRACK.lips else 1.0
        count = max(1, int((x1 - x0) / 26.0 * base_density * busy))
        for _ in range(count):
            x = rnd.uniform(x0, x1)
            name, _w, scale = rnd.choices(allowed, weights=weights)[0]
            behind = rnd.random() < 0.55
            s = scale * rnd.uniform(0.75, 1.25) * (0.8 if behind else 1.0)
            flip = rnd.random() > 0.5
            shade = rnd.uniform(0.82, 1.0) if behind else rnd.uniform(0.94, 1.0)
            if not (cam[0] - 30 < x < cam[0] + 30):
                continue

            src = Image.open("Assets/Sprites/Props/%s.png" % name).convert("RGBA")
            if flip:
                src = src.transpose(Image.FLIP_LEFT_RIGHT)
            src = src.resize((max(1, int(src.width / 100.0 * s * PPU)),
                              max(1, int(src.height / 100.0 * s * PPU))), Image.LANCZOS)
            src = Image.eval(src, lambda v: v)
            y = TRACK.height_at(x) + COLLIDER_OFFSET - 0.15
            px, py = world_to_px(cam, (x, y))
            img.alpha_composite(src, (int(px - src.width / 2),
                                      int(py - src.height * 0.96)))


def paste_bike(img, cam, x, key="Scout", angle=0.0, lift=0.0):
    y = TRACK.height_at(x) + COLLIDER_OFFSET + BG.WHEEL_R_UNITS + lift

    def load(name):
        s = Image.open("Assets/Sprites/Bike/%s.png" % name).convert("RGBA")
        return s.resize((max(1, int(s.width / BG.PPU * PPU)),
                         max(1, int(s.height / BG.PPU * PPU))), Image.LANCZOS)

    plate = Image.new("RGBA", (int(6 * PPU), int(6 * PPU)), (0, 0, 0, 0))
    cx, cy = plate.width / 2.0, plate.height / 2.0

    def put(im, off):
        plate.alpha_composite(im, (int(cx + off[0] * PPU - im.width / 2),
                                   int(cy - off[1] * PPU - im.height / 2)))

    put(load("Wheel_Rear_" + key), BG.REAR_AXLE_LOCAL)
    put(load("Wheel_Front_" + key), BG.FRONT_AXLE_LOCAL)

    body = load("Body_" + key)
    bp = BG.pivot_norm(BG.BODY_PIVOT, BG.BODY_W, BG.BODY_H)
    plate.alpha_composite(body, (int(cx - body.width * bp[0]),
                                 int(cy - body.height * (1 - bp[1]))))

    rider = load("Rider_" + key)
    rp = BG.pivot_norm(BG.RIDER_PEG, BG.RIDER_W, BG.RIDER_H)
    plate.alpha_composite(rider, (int(cx + BG.PEG_LOCAL[0] * PPU - rider.width * rp[0]),
                                  int(cy - BG.PEG_LOCAL[1] * PPU - rider.height * (1 - rp[1]))))

    if angle:
        plate = plate.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    px, py = world_to_px(cam, (x, y))
    img.alpha_composite(plate, (int(px - cx), int(py - cy)))


def frame(cam_x, bike_x=None, angle=0.0, lift=0.0, out="frame.png"):
    cam_y = TRACK.height_at(cam_x) + 4.0
    cam = (cam_x, cam_y)

    img = Image.new("RGBA", (W, H), (183, 178, 168, 255))
    for name, art, px, py, scale, y, _order in LAYERS:
        if name == "Scrub":
            continue
        paste_layer(img, cam, art, px, py, scale, y)

    draw_terrain(img, cam)
    draw_props(img, cam)
    if bike_x is not None:
        paste_bike(img, cam, bike_x, angle=angle, lift=lift)
    for name, art, px, py, scale, y, _order in LAYERS:
        if name == "Scrub":
            paste_layer(img, cam, art, px, py, scale, y)

    img.convert("RGB").save(out)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 6:
        TRACK = TP.TRACKS[sys.argv[6]]
        THEME = TH.ALL[TRACK.theme]
        ORTHO = TRACK.ortho
    target = sys.argv[1] if len(sys.argv) > 1 else "frame.png"
    frame(float(sys.argv[2]) if len(sys.argv) > 2 else 380.0,
          bike_x=float(sys.argv[3]) if len(sys.argv) > 3 else None,
          angle=float(sys.argv[4]) if len(sys.argv) > 4 else 0.0,
          lift=float(sys.argv[5]) if len(sys.argv) > 5 else 0.0,
          out=target)
    print(target)
