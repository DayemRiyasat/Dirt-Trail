"""Author the playable bike prefab and the small track prefabs."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bikegeom as G
from unityasset import guid_for, folder_meta
from unityscene import (Document, Node, index_scripts, script_guid, sprite_ref,
                        asset_ref, v2, v3, col, num, AUDIO_SOURCE)

PREFABS = "Assets/Prefabs"
LAYER_RIDER = 6

REAR = G.REAR_AXLE_LOCAL      # (-0.9, 0)
FRONT = G.FRONT_AXLE_LOCAL    # ( 0.9, 0)
PEG = G.PEG_LOCAL             # (-0.12, -0.08)

# Draw order inside the bike. One Default sorting layer, explicit orders.
ORDER_SHADOW = -5
ORDER_WHEEL = -1
ORDER_BODY = 0
ORDER_RIDER = 1


def prefab_meta(path):
    with open(path + ".meta", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("fileFormatVersion: 2\nguid: %s\nPrefabImporter:\n"
                 "  externalObjects: {}\n  userData: \n  assetBundleName: \n"
                 "  assetBundleVariant: \n" % guid_for(path))


def ref(file_id):
    return "{fileID: %d}" % file_id


# ------------------------------------------------------------------ bike ----
def build_bike():
    d = Document("DirtBike")
    root = d.node("DirtBike", layer=LAYER_RIDER)

    # The chassis capsule is the envelope of the two wheels, so the bike rides
    # on its wheelbase rather than on a box that catches on every lip.
    half = abs(FRONT[0])
    d_r = G.WHEEL_R_UNITS - 0.02
    root.rigidbody2d(mass=2.7, gravity=1.6, angular_damping=5.0, linear_damping=0.05)
    # Low friction on purpose. The bike is a sliding capsule, not a rolling
    # wheel, so surface friction is pure loss: it fights the drive force on
    # every climb instead of helping. Enough is left to hold a parked slope.
    root.capsule2d(size=(half * 2 + d_r * 2, d_r * 2), offset=(0, 0),
                   direction=Node.CAPSULE_HORIZONTAL,
                   material=asset_ref("Assets/Physics/Tyre.physicsMaterial2D",
                                      file_id=6200000))

    body = d.node("Body", root, pos=(0, 0, 0))
    body.sprite("Assets/Sprites/Bike/Body_Scout.png", order=ORDER_BODY)

    rider_pivot = d.node("RiderPivot", root, pos=(PEG[0], PEG[1], 0))
    rider = d.node("Rider", rider_pivot, pos=(0, 0, 0))
    rider.sprite("Assets/Sprites/Bike/Rider_Scout.png", order=ORDER_RIDER)

    wheel_f = d.node("WheelFront", root, pos=(FRONT[0], FRONT[1], 0))
    wheel_f.sprite("Assets/Sprites/Bike/Wheel_Front_Scout.png", order=ORDER_WHEEL)

    wheel_r = d.node("WheelRear", root, pos=(REAR[0], REAR[1], 0))
    wheel_r.sprite("Assets/Sprites/Bike/Wheel_Rear_Scout.png", order=ORDER_WHEEL)

    # Fixed probe origins: these must not move with the suspension.
    axle_r = d.node("RearAxle", root, pos=(REAR[0], REAR[1], 0))
    axle_f = d.node("FrontAxle", root, pos=(FRONT[0], FRONT[1], 0))

    # Rear tyre contact patch: where dust and roost come from.
    contact = d.node("Contact", root, pos=(REAR[0] - 0.15, REAR[1] - d_r, 0))

    # Sits on the ground, not on the bike: BikeShadow writes its world pose.
    shadow = d.node("Shadow", root)
    shadow.sprite("Assets/Sprites/FX/Ground_Shadow.png", order=ORDER_SHADOW,
                  color=(0, 0, 0, 0.34))
    shadow.mono("BikeShadow", "\n".join([
        "blob: {fileID: %d}" % shadow.components[1],
        "fadeHeight: 16",
        "maxScale: 1",
        "minScale: 0.45",
        "maxAlpha: 0.34",
        "probe: 40",
    ]))

    # The rider's own body. Touch the ground with this and the run is over.
    rider_col = d.node("RiderBody", root, layer=LAYER_RIDER)
    rider_col.capsule2d(size=(0.5, 0.95), offset=(0.04, 1.0),
                        direction=Node.CAPSULE_VERTICAL, trigger=True)

    # ---- components on the root ----------------------------------------
    sensor = root.mono("GroundSensor", "\n".join([
        "rearAxle: %s" % ref(axle_r.tr),
        "frontAxle: %s" % ref(axle_f.tr),
        "probeLength: %s" % num(d_r + 0.20),
        "lookAhead: 4",
        "coyoteTime: 0.09",
    ]))

    controller = root.mono("BikeController", "\n".join([
        "config: %s" % asset_ref("Assets/Resources/Bikes/Scout.asset"),
        "ground: %s" % ref(sensor),
        "perfectAngle: 12",
        "cleanAngle: 30",
        "roughAngle: 62",
        "wipeoutSpeed: 6.5",
        "nitroBurst: 9",
        "nitroTopSpeedBonus: 1.25",
    ]))

    root.mono("TrickSystem", "\n".join([
        "bike: %s" % ref(controller),
        "flipBase: 100",
        "minPaidAir: 1.1",
        "airBonusPerHalfSecond: 25",
        "airBonusCap: 300",
        "perfectBonus: 1.5",
        "cleanBonus: 1.25",
        "comboStep: 0.25",
        "comboCap: 3",
        "comboGrace: 7",
    ]))

    visuals = root.mono("BikeVisuals", "\n".join([
        "bodyRenderer: {fileID: %d}" % body.components[1],
        "riderRenderer: {fileID: %d}" % rider.components[1],
        "riderPivot: %s" % ref(rider_pivot.tr),
        "frontWheel: %s" % ref(wheel_f.tr),
        "rearWheel: %s" % ref(wheel_r.tr),
        "frontWheelRenderer: {fileID: %d}" % wheel_f.components[1],
        "rearWheelRenderer: {fileID: %d}" % wheel_r.components[1],
        "wheelRadius: %s" % num(G.WHEEL_R_UNITS),
        "riderLeanRange: 13",
        "riderLeanSmoothing: 0.09",
        "wheelSquash: 0.08",
    ]))

    spray = root.mono("DirtSpray", "\n".join([
        "bike: %s" % ref(controller),
        "contact: %s" % ref(contact.tr),
        "fullRateSpeed: 16",
        "maxDustRate: 46",
        "minImpactForRoost: 4",
        "maxRoostClods: 24",
    ]))

    root.raw(82, AUDIO_SOURCE)
    root.mono("BikeAudio", "\n".join([
        "bike: %s" % ref(controller),
        "idlePitch: 0.62",
        "redlinePitch: 2.05",
        "redlineSpeed: 20",
        "engineVolume: 0.34",
        "airVolume: 0.16",
        "pitchSmoothing: 0.12",
        "landVolume: 0.55",
        "wipeoutVolume: 0.7",
        "pickupVolume: 0.5",
    ]))

    root.mono("BikeLoadout", "\n".join([
        "controller: %s" % ref(controller),
        "visuals: %s" % ref(visuals),
        "spray: %s" % ref(spray),
        "fallback: %s" % asset_ref("Assets/Resources/Bikes/Scout.asset"),
    ]))

    rider_col.mono("RiderImpact", "bike: %s" % ref(controller))

    path = PREFABS + "/DirtBike.prefab"
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render(scene=False))
    prefab_meta(path)
    return record("DirtBike", path, root)


# --------------------------------------------------------------- pickups ----
def build_pickup(name, config_asset, sprite):
    d = Document("Pickup_" + name)
    root = d.node("Pickup " + name)
    root.circle2d(radius=0.95, trigger=True)

    icon = d.node("Icon", root)
    icon.sprite(sprite, order=6)

    root.mono("Pickup", "\n".join([
        "config: %s" % asset_ref(config_asset),
        "icon: {fileID: %d}" % icon.components[1],
        "bobHeight: 0.22",
        "bobSpeed: 1.7",
        "spin: 14",
    ]))

    path = "%s/Pickup_%s.prefab" % (PREFABS, name)
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render(scene=False))
    prefab_meta(path)
    return record("Pickup_" + name, path, root)


# ------------------------------------------------------------ checkpoint ----
def build_checkpoint():
    d = Document("Checkpoint")
    root = d.node("Checkpoint")
    root.box2d(size=(1.4, 14.0), offset=(0, 6.0), trigger=True)

    post = d.node("Post", root)
    post.sprite("Assets/Sprites/Props/Marker_Post.png", order=8)

    cp = root.mono("Checkpoint", "\n".join([
        "sectionName:",
        "flag: {fileID: %d}" % post.components[1],
        "takenTint: %s" % col(0.85, 0.37, 0.15, 1),
    ]))

    path = PREFABS + "/Checkpoint.prefab"
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(d.render(scene=False))
    prefab_meta(path)
    out = record("Checkpoint", path, root)
    # The scene overrides this per instance to name each section.
    MANIFEST["Checkpoint"]["mono"] = cp
    return out


MANIFEST = {}


def record(key, path, root):
    entry = MANIFEST.setdefault(key, {})
    entry.update({"path": path, "go": root.go, "tr": root.tr})
    return path


def main():
    index_scripts()
    os.makedirs(PREFABS, exist_ok=True)
    folder_meta(PREFABS)

    made = [build_bike(),
            build_pickup("Nitro", "Assets/Resources/Pickups/Nitro.asset",
                         "Assets/Sprites/Props/Pickup_Nitro.png"),
            build_pickup("Air", "Assets/Resources/Pickups/AirControl.asset",
                         "Assets/Sprites/Props/Pickup_Air.png"),
            build_checkpoint()]
    with open("Tools/artgen/prefab_manifest.json", "w") as fh:
        json.dump(MANIFEST, fh, indent=2)
    for p in made:
        print("  ", p)


if __name__ == "__main__":
    main()
