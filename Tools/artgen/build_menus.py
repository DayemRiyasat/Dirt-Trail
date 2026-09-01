"""Main menu and garage scenes.

Both use the same backdrop as the track, so the menus sit in the same place the
riding happens. The title screen scrolls the ground under a parked bike; the
garage holds still so you can look at what you picked.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bikegeom as G
import templates as T
import themes as TH
from build_track import LAYERS, MENU_FOREGROUND, PARALLAX, scene_meta
from unityscene import Document, index_scripts, col, num, v3

PROPS = "Assets/Sprites/Props"
TERRAIN = "Assets/Sprites/Terrain"
BIKE = "Assets/Sprites/Bike"

GROUND_TILE_WIDTH = 1024 / 100.0        # Dirt Edge is 1024px at 100 ppu
GROUND_SCALE = 3.0                      # 6 world units tall, covers to the frame edge
SURFACE_IN_TILE = 0.22                  # crust sits this far above the sprite centre

# Scrub_Fore draws its silhouette near the bottom of its 1080px sheet; this is
# how far below the layer centre that content actually lands.
SCRUB_CONTENT_DROP = 13.5


def ground_centre_for(surface_y):
    """Sprite centre that puts the visible crust at `surface_y`."""
    return surface_y - SURFACE_IN_TILE * GROUND_SCALE


def bike_y_for(surface_y, scale):
    from bikegeom import WHEEL_R_UNITS
    return surface_y + WHEEL_R_UNITS * scale


def camera(d, size=11.0):
    cam = d.node("Main Camera", pos=(0, 0, -10), tag="MainCamera")
    # No virtual camera here, so no Cinemachine brain - just the URP data.
    for tid in (T.CAMERA, T.AUDIO_LISTENER, T.URP_CAMERA_DATA):
        cls, body = T.block(tid)
        b = T.retarget(body, cam.go)
        if tid == T.CAMERA:
            b = T.set_field(b, "orthographic size", num(size))
            b = T.set_field(b, "m_BackGroundColor", col(0.498, 0.596, 0.647, 1))
        cam.add(cls, (lambda text: (lambda cid, go: text))(b))
    return cam


def light(d):
    node = d.node("Sun")
    cls, body = T.block(T.LIGHT_2D)
    body = T.retarget(body, node.go)
    body = T.set_field(body, "m_Color", col(1.0, 0.96, 0.9, 1))
    body = T.set_field(body, "m_Intensity", "1.06")
    node.add(cls, (lambda text: (lambda cid, go: text))(body))
    return node


def backdrop(d, y_shift=0.0, foreground_y=5.5, theme=None):
    theme = theme or TH.RIDGE
    root = d.node("Backdrop")
    fg = MENU_FOREGROUND[:5] + (foreground_y,) + MENU_FOREGROUND[6:]
    for name, art, px, py, scale, y, order in list(LAYERS) + [fg]:
        layer = d.node(name, root, pos=(0, y + y_shift, 0), scale=(scale, scale, 1))
        layer.mono("ParallaxLayer", "\n".join([
            "parallax: %s" % num(px),
            "verticalParallax: %s" % num(py),
            "wrapHorizontally: 1",
            "tileWidth: 0",
        ]))
        for i, offset in enumerate((-1, 0, 1)):
            tile = d.node("%s Tile %d" % (name, i), layer,
                          pos=(offset * 1920.0 / 40.0, 0, 0))
            tile.sprite("%s/%s/%s_%s.png" % (PARALLAX, theme["key"], theme["key"], art),
                        order=order)
    return root


def ground_strip(d, y, scale=GROUND_SCALE, wrap=True):
    """A run of the track's own edge sprite, wide enough to fill any aspect."""
    layer = d.node("Ground", pos=(0, y, 0), scale=(scale, scale, 1))
    layer.mono("ParallaxLayer", "\n".join([
        "parallax: 0",
        "verticalParallax: 0",
        "wrapHorizontally: %d" % (1 if wrap else 0),
        "tileWidth: 0",
    ]))
    for i, offset in enumerate((-1, 0, 1)):
        tile = d.node("Ground Tile %d" % i, layer,
                      pos=(offset * GROUND_TILE_WIDTH, 0, 0))
        tile.sprite("%s/Ridge/Ridge Edge.png" % TERRAIN, order=30)
    return layer


def parked_bike(d, parent, pos, scale=1.0, spin=0.0, key="Scout"):
    """Same sprites and axle offsets as the playable bike."""
    root = d.node("Parked Bike", parent, pos=pos, scale=(scale, scale, 1))

    body = d.node("Display Body", root)
    body.sprite("%s/Body_%s.png" % (BIKE, key), order=40)

    rider = d.node("Display Rider", root, pos=(G.PEG_LOCAL[0], G.PEG_LOCAL[1], 0))
    rider.sprite("%s/Rider_%s.png" % (BIKE, key), order=41)

    wf = d.node("Display Wheel Front", root,
                pos=(G.FRONT_AXLE_LOCAL[0], G.FRONT_AXLE_LOCAL[1], 0))
    wf.sprite("%s/Wheel_Front_%s.png" % (BIKE, key), order=39)

    wr = d.node("Display Wheel Rear", root,
                pos=(G.REAR_AXLE_LOCAL[0], G.REAR_AXLE_LOCAL[1], 0))
    wr.sprite("%s/Wheel_Rear_%s.png" % (BIKE, key), order=39)

    display = root.mono("BikeDisplay", "\n".join([
        "body: {fileID: %d}" % body.components[1],
        "rider: {fileID: %d}" % rider.components[1],
        "frontWheel: {fileID: %d}" % wf.components[1],
        "rearWheel: {fileID: %d}" % wr.components[1],
        "rockAmount: %s" % num(0.5 if spin else 0.9),
        "rockSpeed: 1.1",
        "wheelIdleSpin: %s" % num(spin),
    ]))
    return root, display


def watermark(d):
    return d.node("Watermark").mono("Watermark", "text: Made by Dayem R.")


def event_system(d):
    node = d.node("EventSystem")
    for tid in (T.EVENT_SYSTEM, T.INPUT_MODULE):
        cls, body = T.block(tid)
        node.add(cls, (lambda text: (lambda cid, go: text))(T.retarget(body, node.go)))
    return node


def build_main_menu():
    d = Document("MainMenu")
    d.prelude = _prelude()

    surface = -7.5
    cam = camera(d, size=11.0)
    light(d)
    backdrop(d, y_shift=-1.0, foreground_y=5.5)
    ground_strip(d, y=ground_centre_for(surface))

    # Parked, not riding. An endlessly scrolling ground under a stationary bike
    # reads fine for two seconds and wrong for ten, so the title screen holds
    # still and lets the composition do the work.
    parked_bike(d, None, pos=(3.4, bike_y_for(surface, 1.35), 0), scale=1.35)

    d.node("Menu").mono("MainMenuView", "\n".join([
        "title: DIRT TRAIL",
        "subtitle: BRAAAP. ONE TRACK, TWO BIKES, NO EXCUSES.",
    ]))
    watermark(d)
    event_system(d)

    path = "Assets/Scenes/MainMenu.unity"
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render())
    scene_meta(path)
    return path


def build_garage():
    d = Document("Garage")
    d.prelude = _prelude()

    surface = -6.8
    camera(d, size=10.0)
    light(d)
    backdrop(d, y_shift=-1.0, foreground_y=4.6)
    ground_strip(d, y=ground_centre_for(surface), wrap=False)

    # Right of centre: the copy column runs down the left.
    root, display = parked_bike(d, None,
                                pos=(6.2, bike_y_for(surface, 1.55), 0), scale=1.55)

    d.node("Garage UI").mono("GarageView", "\n".join([
        "display: {fileID: %d}" % display,
        "ticksPerStat: 10",
    ]))
    watermark(d)
    event_system(d)

    path = "Assets/Scenes/Garage.unity"
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render())
    scene_meta(path)
    return path


def _prelude():
    import re
    text = open(T.SOURCE, encoding="utf-8").read()
    keep = []
    for chunk in re.split(r"(?m)^--- ", text)[1:]:
        head = re.match(r"!u!(\d+) &(-?\d+)", chunk)
        if head and int(head.group(1)) in (29, 104, 157, 196):
            keep.append("--- " + chunk.rstrip("\n"))
    return "\n".join(keep)


def build_track_select():
    d = Document("TrackSelect")
    d.prelude = _prelude()

    surface = -7.2
    camera(d, size=10.5)
    light(d)
    backdrop(d, y_shift=-1.0, foreground_y=5.0)
    ground_strip(d, y=ground_centre_for(surface), wrap=False)

    d.node("Track Select UI").mono("TrackSelectView")
    watermark(d)
    event_system(d)

    path = "Assets/Scenes/TrackSelect.unity"
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render())
    scene_meta(path)
    return path


if __name__ == "__main__":
    index_scripts()
    for p in (build_main_menu(), build_garage(), build_track_select()):
        print("  ", p)
