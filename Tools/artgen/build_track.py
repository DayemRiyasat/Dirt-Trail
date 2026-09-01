"""Builds a track scene from a profile and a theme. One per level."""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import templates as T
import themes as TH
import track_profile as TP
from unityasset import guid_for
from unityscene import (Document, index_scripts, prefab_instance, sprite_ref,
                        asset_ref, col, num, v2, v3, fid)

LAYER_GROUND = 7
LAYER_RIDER = 6

COLLIDER_OFFSET = 0.22        # the visible crust sits this far above the spline
SPLINE_DETAIL = 12

IMPULSE_SOURCE_GUID = "180ecf9b41d478f468eb3e9083753217"
IMPULSE_LISTENER_GUID = "00b2d199b96b516448144ab30fb26aed"

PARALLAX = "Assets/Sprites/Parallax"
PROPS = "Assets/Sprites/Props"

# name, sprite, horizontal parallax, vertical follow, scale, y, order
# Y is chosen from where the *content* sits inside each 1080px sheet, so every
# horizon lands at a deliberate height relative to the camera rather than
# wherever the art happened to be drawn.
LAYERS = [
    ("Sky",        "Sky",         0.97, 0.98, 2.10,  6.0, -100),
    ("FarRange",   "Range_Far",   0.86, 0.97, 1.70,  3.0,  -90),
    ("Mesas",      "Mesa_Mid",    0.66, 0.95, 1.45,  0.0,  -80),
    ("NearRidge",  "Ridge_Near",  0.42, 0.95, 1.30, -1.0,  -70),
]

# The foreground scrub band is deliberately absent from the track: anything
# drawn in front of the rider hides the surface they are about to land on.
# It is used in the menu scenes, where nothing is at stake.
MENU_FOREGROUND = ("Scrub", "Scrub_Fore", -0.07, 0.95, 1.15, 2.0, 60)


def mono_block(guid, go, fields):
    body = ("MonoBehaviour:\n"
            "  m_ObjectHideFlags: 0\n"
            "  m_CorrespondingSourceObject: {fileID: 0}\n"
            "  m_PrefabInstance: {fileID: 0}\n"
            "  m_PrefabAsset: {fileID: 0}\n"
            "  m_GameObject: {fileID: %d}\n"
            "  m_Enabled: 1\n"
            "  m_EditorHideFlags: 0\n"
            "  m_Script: {fileID: 11500000, guid: %s, type: 3}\n"
            "  m_Name:\n"
            "  m_EditorClassIdentifier:\n" % (go, guid))
    return body + "".join("  %s\n" % line for line in fields.strip("\n").split("\n"))


# ------------------------------------------------------------------ terrain --
def spline_block(profile, theme):
    """Closed shape: left wall, the ridge, right wall, then back along the base."""
    pts = profile.ridge()
    tans = profile.tangents()

    control = []
    first, last = pts[0], pts[-1]
    control.append(((first[0] - 30.0, profile.deep_y), (0, 0), (0, 0), 0))
    control.append(((first[0] - 30.0, first[1]), (0, 0), (0, 0), 0))
    for (x, y, _s), (lt, rt) in zip(pts, tans):
        control.append(((x, y), lt, rt, 1))
    control.append(((last[0] + 30.0, last[1]), (0, 0), (0, 0), 0))
    control.append(((last[0] + 30.0, profile.deep_y), (0, 0), (0, 0), 0))

    lines = ["  m_Spline:", "    m_IsOpenEnded: 0", "    m_ControlPoints:"]
    for (p, lt, rt, mode) in control:
        lines += [
            "    - position: %s" % v3(p[0], p[1], 0),
            "      leftTangent: %s" % v3(lt[0], lt[1], 0),
            "      rightTangent: %s" % v3(rt[0], rt[1], 0),
            "      mode: %d" % mode,
            "      height: 1",
            "      spriteIndex: 0",
            "      corner: 1",
            "      m_CornerMode: 1",
        ]
    return "\n".join(lines)


def collider_points(profile, theme):
    poly = profile.offset_polyline(profile.sample(SPLINE_DETAIL), COLLIDER_OFFSET)
    # Close the loop with vertical walls so the rider cannot leave either end.
    poly = ([(poly[0][0] - 30.0, profile.deep_y), (poly[0][0] - 30.0, poly[0][1])]
            + poly
            + [(poly[-1][0] + 30.0, poly[-1][1]), (poly[-1][0] + 30.0, profile.deep_y)])
    return poly


def terrain(d, profile, theme):
    node = d.node("%s Terrain" % theme["key"], layer=LAYER_GROUND)

    cls, body = T.block(T.SPRITE_SHAPE_CONTROLLER)
    body = T.retarget(body, node.go)
    body = T.replace_section(body, "m_Spline", spline_block(profile, theme))
    body = T.set_field(body, "m_SpriteShape",
                       asset_ref("Assets/Sprites/Terrain/%s/%s Sprite Shape Profile.asset"
                                 % (theme["key"], theme["key"])))
    body = T.set_field(body, "m_FillPixelPerUnit", "64")
    body = T.set_field(body, "m_ColliderOffset", num(COLLIDER_OFFSET))
    body = T.set_field(body, "m_ColliderDetail", str(SPLINE_DETAIL))
    body = T.set_field(body, "m_SplineDetail", str(SPLINE_DETAIL * 2))
    body = T.set_field(body, "m_UpdateCollider", "1")
    body = T.replace_section(body, "m_ColliderSegment", "  m_ColliderSegment: []")
    node.add(cls, lambda cid, go: body)

    # The renderer block travels with the controller in the source scene.
    renderer_fid = _find_sprite_shape_renderer()
    rcls, rbody = T.block(renderer_fid)
    rbody = T.retarget(rbody, node.go)
    # Behind the bike and its shadow, in front of the backdrop.
    rbody = T.set_field(rbody, "m_SortingOrder", "-40")
    node.add(rcls, (lambda text: (lambda cid, go: text))(rbody))

    # Write the edge collider directly as well as leaving the sprite shape to
    # re-bake: physics then works even before the first editor import.
    ecls, ebody = T.block(T.EDGE_COLLIDER)
    ebody = T.retarget(ebody, node.go)
    pts = collider_points(profile, theme)
    ebody = T.replace_section(
        ebody, "m_Points",
        "  m_Points:\n" + "\n".join("  - %s" % v2(x, y) for x, y in pts))
    node.add(ecls, lambda cid, go: ebody)
    return node


def _find_sprite_shape_renderer():
    import re
    text = open(T.SOURCE, encoding="utf-8").read()
    m = re.search(r"--- !u!1971053207 &(\d+)", text)
    return int(m.group(1))


# ----------------------------------------------------------------- backdrop --
def backdrop(d, profile, theme):
    root = d.node("Backdrop", pos=(0, 0, 0))
    for name, art, px, py, scale, y, order in LAYERS:
        layer = d.node(name, root, pos=(0, y, 0), scale=(scale, scale, 1))
        layer.mono("ParallaxLayer", "\n".join([
            "parallax: %s" % num(px),
            "verticalParallax: %s" % num(py),
            "wrapHorizontally: 1",
            "tileWidth: 0",
        ]))
        # Three tiles so a wrap never shows an edge, whatever the aspect ratio.
        for i, offset in enumerate((-1, 0, 1)):
            tile = d.node("%s Tile %d" % (name, i), layer,
                          pos=(offset * 1920.0 / 40.0, 0, 0))
            tile.sprite("%s/%s/%s_%s.png" % (PARALLAX, theme["key"], theme["key"], art),
                        order=order)
    return root


# -------------------------------------------------------------- decoration --
PROP_SET = [
    ("Rock_Large", 0.9, 1.25), ("Rock_Mid", 1.0, 1.0), ("Rock_Small", 1.2, 0.8),
    ("Shrub_01", 1.1, 0.9), ("Shrub_02", 1.1, 0.9), ("Saguaro", 0.5, 1.1),
    ("Tyre_Stack", 0.35, 0.9),
]


def dressing(d, profile, theme):
    """Props laid on the surface. Density varies by section so the track reads
    as a place rather than an evenly seeded strip."""
    root = d.node("Track Dressing")
    rnd = random.Random(20260830)
    bounds = profile.section_bounds()

    # Busier around the jumps, sparse across the open sections.
    # Sparse on the open flats, cluttered in the pit; the desert sits between.
    base_density = {"mesa": 0.55, "quarry": 0.75, "dune": 0.28}[theme["silhouette"]]

    # What grows here is part of what makes each level its own place.
    allowed = {
        "mesa": PROP_SET,
        "quarry": [p for p in PROP_SET if p[0].startswith("Rock") or p[0] == "Tyre_Stack"],
        "dune": [p for p in PROP_SET if p[0].startswith("Rock") or p[0].startswith("Shrub")],
    }[theme["silhouette"]]
    weights = [w for _n, w, _s in allowed]
    for section, (x0, x1) in bounds.items():
        span = x1 - x0
        busy = 1.5 if section in profile.lips else 1.0
        count = max(1, int(span / 26.0 * base_density * busy))
        for _ in range(count):
            x = rnd.uniform(x0, x1)
            name, _w, scale = rnd.choices(allowed, weights=weights)[0]
            behind = rnd.random() < 0.55

            y = profile.height_at(x) + COLLIDER_OFFSET - 0.15
            s = scale * rnd.uniform(0.75, 1.25) * (0.8 if behind else 1.0)
            node = d.node("%s %d" % (name, int(x)), root,
                          pos=(x, y, 0), rot_z=profile.slope_at(x) * rnd.uniform(0.4, 1.0),
                          scale=(s * (1 if rnd.random() > 0.5 else -1), s, 1))
            shade = rnd.uniform(0.82, 1.0) if behind else rnd.uniform(0.94, 1.0)
            node.sprite("%s/%s.png" % (PROPS, name),
                        order=-20 if behind else 20,
                        color=(shade, shade, shade, 1))

    # Ramp lips sitting on the sharpest takeoffs, so the jumps read as built.
    for section, pts in profile.sections:
        if section not in profile.lips:
            continue
        lip = min(pts, key=lambda p: p[2])
        node = d.node("Ramp Lip %s" % section.title().replace(" ", ""), root,
                      pos=(lip[0] - 3.0, profile.height_at(lip[0] - 3.0) - 0.4, 0),
                      rot_z=profile.slope_at(lip[0] - 4.0),
                      scale=(2.6, 2.4, 1))
        node.sprite("%s/Ramp_Lip.png" % PROPS, order=18)
    return root


# ------------------------------------------------------------------- scene --
def build(profile, theme):
    index_scripts()
    manifest = json.load(open("Tools/artgen/prefab_manifest.json"))
    d = Document(profile.key)
    d.prelude = _environment_prelude()

    # --- camera ---------------------------------------------------------
    cam = d.node("Main Camera", pos=(0, 0, -10), tag="MainCamera")
    for tid in (T.CAMERA, T.AUDIO_LISTENER, T.URP_CAMERA_DATA, T.CINEMACHINE_BRAIN):
        cls, body = T.block(tid)
        b = T.retarget(body, cam.go)
        if tid == T.CAMERA:
            b = T.set_field(b, "m_BackGroundColor", col(*theme["clear"], 1))
        cam.add(cls, (lambda text: (lambda cid, go: text))(b))

    rig = d.node("Camera Rig")
    target = d.node("Camera Target", rig)
    vcam = d.node("Ridge Camera", rig, pos=(0, 0, -10))

    cls, body = T.block(T.CINEMACHINE_CAMERA)
    body = T.retarget(body, vcam.go)
    body = T.set_field(body, "TrackingTarget", "{fileID: %d}" % target.tr, indent="    ")
    body = T.set_field(body, "OrthographicSize", num(profile.ortho), indent="    ")
    vcam.add(cls, (lambda text: (lambda cid, go: text))(body))

    cls, body = T.block(T.CINEMACHINE_FOLLOW)
    body = T.retarget(body, vcam.go)
    # Tighter on X than Y: the horizon should feel stable while the bike drops.
    body = T.set_field(body, "PositionDamping", v3(0.45, 0.85, 0), indent="    ")
    body = T.set_field(body, "FollowOffset", v3(0, 0, -10))
    vcam.add(cls, (lambda text: (lambda cid, go: text))(body))

    vcam.add(114, lambda cid, go: mono_block(IMPULSE_LISTENER_GUID, go, "\n".join([
        "ApplyAfter: 1",
        "ChannelMask: 1",
        "Gain: 1",
        "Use2DDistance: 1",
        "UseCameraSpace: 1",
        "ReactionSettings:",
        "  AmplitudeGain: 1",
        "  FrequencyGain: 1",
        "  Duration: 0.35",
    ])))

    impulse = rig.add(114, lambda cid, go: mono_block(
        IMPULSE_SOURCE_GUID, go, "DefaultVelocity: %s" % v3(0, -1, 0)))

    rig.mono("RiderCamera", "\n".join([
        "target: {fileID: %d}" % target.tr,
        "vcam: {fileID: %d}" % vcam.components[1],
        "impulse: {fileID: %d}" % impulse,
        "maxLookAhead: 6.5",
        "lookAheadSpeed: 20",
        "lookAheadSmoothing: 0.35",
        "airLift: 0.45",
        "maxAirLift: 7",
        "verticalSmoothing: 0.22",
        "baseSize: %s" % num(profile.ortho),
        "speedZoom: 2.2",
        "airZoom: 3.4",
        "nitroZoom: 1.1",
        "zoomSmoothing: 0.5",
        "impulseReference: 20",
        "maxImpulse: 0.45",
        "wipeoutImpulse: 0.6",
    ]))

    # --- light ----------------------------------------------------------
    light = d.node("Sun", pos=(0, 0, 0))
    cls, body = T.block(T.LIGHT_2D)
    body = T.retarget(body, light.go)
    body = T.set_field(body, "m_Color", col(1.0, 0.96, 0.9, 1))
    body = T.set_field(body, "m_Intensity", "1.06")
    light.add(cls, (lambda text: (lambda cid, go: text))(body))

    backdrop(d, profile, theme)
    terrain(d, profile, theme)
    dressing(d, profile, theme)

    # --- markers and finish ---------------------------------------------
    start_y = profile.height_at(profile.start_x) + COLLIDER_OFFSET
    start = d.node("Start", pos=(profile.start_x, start_y, 0))

    finish_y = profile.height_at(profile.finish_x) + COLLIDER_OFFSET
    finish = d.node("Finish", pos=(profile.finish_x, finish_y, 0))
    finish.box2d(size=(2.0, 26.0), offset=(0, 11.0), trigger=True)
    finish.mono("FinishLine")

    banner = d.node("Finish Banner", finish, pos=(0, 13.5, 0), scale=(2.2, 2.2, 1))
    banner.sprite("%s/Finish_Banner.png" % PROPS, order=24)
    for side in (-5.6, 5.6):
        post = d.node("Post %d" % int(side * 10), finish, pos=(side, 0, 0),
                      scale=(2.0, 4.6, 1))
        post.sprite("%s/Marker_Post.png" % PROPS, order=23)

    # --- run host --------------------------------------------------------
    game = d.node("Game")
    game.mono("RunManager", "\n".join([
        "startMarker: {fileID: %d}" % start.tr,
        "finishMarker: {fileID: %d}" % finish.tr,
        "trackKey: %s" % profile.key,
        "trackName: %s" % profile.name,
        "respawnDelay: 1.15",
        "killHeight: %s" % num(profile.deep_y * 0.8),
        "finishBonus: 500",
    ]))
    game.mono("ShoutDirector", "\n".join([
        "height: 3.2",
        "spread: 1.1",
        "scale: 1",
        "cooldown: 0.45",
    ]))
    game.mono("HudView")
    game.mono("PauseMenu")
    game.mono("ResultsView")

    d.node("Watermark").mono("Watermark", "text: Made by Dayem R.")

    # --- event system ----------------------------------------------------
    events = d.node("EventSystem")
    for tid in (T.EVENT_SYSTEM, T.INPUT_MODULE):
        cls, body = T.block(tid)
        events.add(cls, (lambda text: (lambda cid, go: text))(T.retarget(body, events.go)))

    # --- prefab instances -------------------------------------------------
    d.extra_roots.append(prefab_instance(
        d, "bike", manifest["DirtBike"]["path"], manifest["DirtBike"],
        "DirtBike", pos=(profile.start_x, start_y + 1.4, 0)))

    for i, (name, x) in enumerate(checkpoints(profile, theme)):
        inst = prefab_instance(
            d, "cp%d" % i, manifest["Checkpoint"]["path"], manifest["Checkpoint"],
            "Checkpoint %s" % name,
            pos=(x, profile.height_at(x) + COLLIDER_OFFSET - 0.3, 0),
            extra=[(manifest["Checkpoint"]["mono"], "sectionName", name)])
        d.extra_roots.append(inst)

    for i, (kind, x, lift) in enumerate(pickup_spots(profile, theme)):
        key = "Pickup_" + kind
        d.extra_roots.append(prefab_instance(
            d, "pk%d" % i, manifest[key]["path"], manifest[key],
            "Pickup %s %d" % (kind, i),
            pos=(x, profile.height_at(x) + lift, 0)))

    os.makedirs("Assets/Scenes", exist_ok=True)
    scene = "Assets/Scenes/%s.unity" % profile.key
    with open(scene, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render())
    scene_meta(scene)
    return scene


def checkpoints(profile, theme):
    """One at the start of each section that is genuinely a fresh attempt."""
    bounds = profile.section_bounds()
    wanted = ["ROLLERS", "FIRST KICKER", "WHOOPS", "THE BOWL", "THE CLIMB",
              "STEP DOWN", "RHYTHM", "TABLETOP", "THE LONG ONE"]
    return [(name, bounds[name][0] - 4.0) for name in wanted if name in bounds]


def pickup_spots(profile, theme):
    """Nitro laid along the trail at a height you ride straight through, and an
    air canister hanging over every takeoff where the extra rotation is worth
    something. Generated from the profile so it stays right when the track moves.

    Returns (kind, x, height above the surface).
    """
    spots = []

    # A nitro roughly every fifty units, skipped where the ground is too steep
    # to collect one cleanly or where a lip would launch you straight past it.
    lips = set()
    for name, pts in profile.sections:
        if name in profile.lips:
            lips.add(round(min(pts, key=lambda p: p[2])[0]))

    x = 34.0
    while x < profile.finish_x - 20.0:
        near_lip = any(abs(x - lx) < 14.0 for lx in lips)
        if not near_lip and abs(profile.slope_at(x)) < 26.0:
            spots.append(("Nitro", x, 2.6))
            x += 48.0
        else:
            x += 8.0

    # Air control over each takeoff, on the flight path rather than the ground.
    for name, pts in profile.sections:
        if name not in profile.lips:
            continue
        lip = min(pts, key=lambda p: p[2])
        spots.append(("Air", lip[0] + 6.0, 7.0))

    return spots


def scene_meta(path):
    with open(path + ".meta", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("fileFormatVersion: 2\nguid: %s\nDefaultImporter:\n"
                 "  externalObjects: {}\n  userData: \n  assetBundleName: \n"
                 "  assetBundleVariant: \n" % guid_for(path))


def _environment_prelude():
    """Scene settings lifted from the original so lighting and physics match."""
    import re
    text = open(T.SOURCE, encoding="utf-8").read()
    keep = []
    for chunk in re.split(r"(?m)^--- ", text)[1:]:
        head = re.match(r"!u!(\d+) &(-?\d+)", chunk)
        if head and int(head.group(1)) in (29, 104, 157, 196, 1001480554):
            keep.append("--- " + chunk.rstrip("\n"))
    return "\n".join(keep)


if __name__ == "__main__":
    for key in TP.ORDER:
        track = TP.TRACKS[key]
        print("  ", build(track, TH.ALL[track.theme]))
