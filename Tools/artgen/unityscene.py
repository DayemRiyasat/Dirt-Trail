"""Minimal Unity YAML emitter: enough to author scenes and prefabs by hand.

Only the component types this project actually uses. Every fileID is derived
from a stable key, so regenerating a scene keeps its internal references and
diffs stay readable.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unityasset import guid_for


def fid(key):
    """Deterministic positive fileID from a name."""
    h = int(hashlib.md5(("dirttrail.fid|" + key).encode()).hexdigest()[:15], 16)
    return (h % 2000000000) + 100000


def script_guid(name):
    """GUID of a .cs by class name, read from the meta the generator wrote."""
    path = _SCRIPT_PATHS.get(name)
    if path is None:
        raise KeyError("unknown script: %s" % name)
    meta = path + ".meta"
    for line in open(meta, encoding="utf-8"):
        if line.startswith("guid:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("no guid in %s" % meta)


_SCRIPT_PATHS = {}


def index_scripts(root="Assets/Scripts"):
    """Map class name -> file path. One public type per file is assumed."""
    _SCRIPT_PATHS.clear()
    for base, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".cs"):
                _SCRIPT_PATHS[os.path.splitext(f)[0]] = os.path.join(base, f).replace("\\", "/")
    return _SCRIPT_PATHS


def sprite_ref(png_path):
    """{fileID, guid} pair for a generated sprite."""
    from unityasset import internal_id_for
    rel = png_path.replace("\\", "/")
    return "{fileID: %d, guid: %s, type: 3}" % (internal_id_for(rel), guid_for(rel))


def asset_ref(asset_path, file_id=11400000):
    return "{fileID: %d, guid: %s, type: 2}" % (file_id, guid_for(asset_path))


def v3(x, y, z=0.0):
    return "{x: %s, y: %s, z: %s}" % (num(x), num(y), num(z))


def v2(x, y):
    return "{x: %s, y: %s}" % (num(x), num(y))


def col(r, g, b, a=1.0):
    return "{r: %s, g: %s, b: %s, a: %s}" % (num(r), num(g), num(b), num(a))


def num(v):
    if isinstance(v, int):
        return str(v)
    s = ("%.6f" % float(v)).rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def quat_z(degrees):
    import math
    h = math.radians(degrees) * 0.5
    return "{x: 0, y: 0, z: %s, w: %s}" % (num(math.sin(h)), num(math.cos(h)))


class Node:
    """A GameObject plus its Transform, with children and extra components."""

    def __init__(self, doc, name, parent=None, pos=(0, 0, 0), rot_z=0.0,
                 scale=(1, 1, 1), layer=0, active=True, tag="Untagged"):
        self.doc = doc
        self.name = name
        self.go = fid(doc.key + "/go/" + name + doc.salt())
        self.tr = fid(doc.key + "/tr/" + name + doc.salt())
        self.components = [self.tr]
        self.children = []
        self.parent = parent
        self.pos = pos
        self.rot_z = rot_z
        self.scale = scale
        self.layer = layer
        self.active = active
        self.tag = tag
        doc.nodes.append(self)
        if parent is not None:
            parent.children.append(self)

    # -- component adders -------------------------------------------------
    def add(self, class_id, body):
        cid = fid(self.doc.key + "/c/%s/%d/%s" % (self.name, class_id,
                                                  str(len(self.components))))
        self.components.append(cid)
        self.doc.blocks.append((class_id, cid, body(cid, self.go)))
        return cid

    def sprite(self, sprite_path, order=0, sorting_layer=0, color=(1, 1, 1, 1),
               flip_x=False, mask_interaction=0):
        return self.add(212, lambda cid, go: SPRITE_RENDERER.format(
            go=go, sprite=sprite_ref(sprite_path), order=order,
            sorting_layer=sorting_layer, color=col(*color),
            flip_x=1 if flip_x else 0, mask=mask_interaction))

    def mono(self, script, fields=""):
        guid = script_guid(script)
        text = "".join("  %s\n" % line for line in fields.strip("\n").split("\n")) \
            if fields.strip() else ""
        return self.add(114, lambda cid, go: MONO.format(go=go, guid=guid, fields=text))

    def rigidbody2d(self, mass=1.0, gravity=1.0, angular_damping=0.05,
                    linear_damping=0.0, material=None):
        mat = material if material else "{fileID: 0}"
        return self.add(50, lambda cid, go: RIGIDBODY2D.format(
            go=go, mass=num(mass), gravity=num(gravity),
            angular=num(angular_damping), linear=num(linear_damping), material=mat))

    # Unity's CapsuleDirection2D is Vertical = 0, Horizontal = 1. Getting this
    # backwards silently produces a square: a capsule cannot be shorter than
    # twice its cap radius, so Unity clamps the minor axis up to the major one.
    CAPSULE_VERTICAL = 0
    CAPSULE_HORIZONTAL = 1

    def capsule2d(self, size, offset=(0, 0), direction=CAPSULE_VERTICAL,
                  trigger=False, material=None):
        mat = material if material else "{fileID: 0}"
        return self.add(70, lambda cid, go: CAPSULE2D.format(
            go=go, size=v2(*size), offset=v2(*offset), direction=direction,
            trigger=1 if trigger else 0, material=mat))

    def box2d(self, size, offset=(0, 0), trigger=False):
        return self.add(61, lambda cid, go: BOX2D.format(
            go=go, size=v2(*size), offset=v2(*offset), trigger=1 if trigger else 0))

    def circle2d(self, radius, offset=(0, 0), trigger=False):
        return self.add(58, lambda cid, go: CIRCLE2D.format(
            go=go, radius=num(radius), offset=v2(*offset), trigger=1 if trigger else 0))

    def raw(self, class_id, body):
        return self.add(class_id, lambda cid, go: body.format(go=go, cid=cid))


class Document:
    """Collects nodes and raw blocks, then serialises a whole .unity or .prefab."""

    def __init__(self, key):
        self.key = key
        self.nodes = []
        self.blocks = []
        self.prelude = ""
        self.extra_roots = []          # prefab instance fileIDs, kept at scene root
        self._salt = 0

    def salt(self):
        self._salt += 1
        return "#%d" % self._salt

    def node(self, *args, **kwargs):
        return Node(self, *args, **kwargs)

    def render(self, roots=None, scene=True):
        out = ["%YAML 1.1", "%TAG !u! tag:unity3d.com,2011:"]
        if self.prelude:
            out.append(self.prelude.rstrip("\n"))

        for n in self.nodes:
            out.append(self._game_object(n))
            out.append(self._transform(n))

        for class_id, cid, body in self.blocks:
            out.append("--- !u!%d &%d\n%s" % (class_id, cid, body.rstrip("\n")))

        if scene:
            top = roots if roots is not None else [n for n in self.nodes if n.parent is None]
            refs = "\n".join(["  - {fileID: %d}" % n.tr for n in top] +
                             ["  - {fileID: %d}" % r for r in self.extra_roots])
            out.append("--- !u!1660057539 &9223372036854775807\nSceneRoots:\n"
                       "  m_ObjectHideFlags: 0\n  m_Roots:\n" + refs)

        return "\n".join(out) + "\n"

    def _game_object(self, n):
        comps = "\n".join("  - component: {fileID: %d}" % c for c in n.components)
        return GAME_OBJECT.format(go=n.go, comps=comps, layer=n.layer, name=n.name,
                                  active=1 if n.active else 0, tag=n.tag)

    def _transform(self, n):
        kids = ("\n".join("  - {fileID: %d}" % c.tr for c in n.children)
                if n.children else None)
        return TRANSFORM.format(
            tr=n.tr, go=n.go, rot=quat_z(n.rot_z), pos=v3(*n.pos),
            scale=v3(*n.scale),
            children=("\n" + kids) if kids else " []",
            father=n.parent.tr if n.parent else 0,
            hint=v3(0, 0, n.rot_z))


# ---------------------------------------------------------------- templates --
GAME_OBJECT = """--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
{comps}
  m_Layer: {layer}
  m_Name: {name}
  m_TagString: {tag}
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: {active}"""

TRANSFORM = """--- !u!4 &{tr}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  serializedVersion: 2
  m_LocalRotation: {rot}
  m_LocalPosition: {pos}
  m_LocalScale: {scale}
  m_ConstrainProportionsScale: 0
  m_Children:{children}
  m_Father: {{fileID: {father}}}
  m_LocalEulerAnglesHint: {hint}"""

MONO = """MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {guid}, type: 3}}
  m_Name:
  m_EditorClassIdentifier:
{fields}"""

SPRITE_RENDERER = """SpriteRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_CastShadows: 0
  m_ReceiveShadows: 0
  m_DynamicOccludee: 1
  m_StaticShadowCaster: 0
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 0
  m_RayTraceProcedural: 0
  m_RayTracingAccelStructBuildFlagsOverride: 0
  m_RayTracingAccelStructBuildFlags: 1
  m_SmallMeshCulling: 1
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:
  - {{fileID: 2100000, guid: a97c105638bdf8b4a8650670310a4cd3, type: 2}}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {{fileID: 0}}
  m_ProbeAnchor: {{fileID: 0}}
  m_LightProbeVolumeOverride: {{fileID: 0}}
  m_ScaleInLightmap: 1
  m_ReceiveGI: 1
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 0
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {{fileID: 0}}
  m_SortingLayerID: {sorting_layer}
  m_SortingLayer: 0
  m_SortingOrder: {order}
  m_Sprite: {sprite}
  m_Color: {color}
  m_FlipX: {flip_x}
  m_FlipY: 0
  m_DrawMode: 0
  m_Size: {{x: 1, y: 1}}
  m_AdaptiveModeThreshold: 0.5
  m_SpriteTileMode: 0
  m_WasSpriteAssigned: 1
  m_MaskInteraction: {mask}
  m_SpriteSortPoint: 0"""

RIGIDBODY2D = """Rigidbody2D:
  serializedVersion: 5
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_BodyType: 0
  m_Simulated: 1
  m_UseFullKinematicContacts: 0
  m_UseAutoMass: 0
  m_Mass: {mass}
  m_LinearDamping: {linear}
  m_AngularDamping: {angular}
  m_GravityScale: {gravity}
  m_Material: {material}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_Interpolate: 1
  m_SleepingMode: 1
  m_CollisionDetection: 1
  m_Constraints: 0"""

_COLLIDER_COMMON = """  m_Enabled: 1
  serializedVersion: 3
  m_Density: 1
  m_Material: {material}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_ForceSendLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_ForceReceiveLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_ContactCaptureLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_CallbackLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_IsTrigger: {trigger}
  m_UsedByEffector: 0
  m_CompositeOperation: 0
  m_CompositeOrder: 0
  m_Offset: {offset}"""

_HEAD = """  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
"""

CAPSULE2D = ("CapsuleCollider2D:\n" + _HEAD + _COLLIDER_COMMON +
             "\n  m_Size: {size}\n  m_Direction: {direction}")

BOX2D = ("BoxCollider2D:\n" + _HEAD + _COLLIDER_COMMON.replace(
    "  m_Material: {material}", "  m_Material: {{fileID: 0}}") +
    "\n  m_SpriteTilingProperty:\n    border: {{x: 0, y: 0, z: 0, w: 0}}\n"
    "    pivot: {{x: 0, y: 0}}\n    oldSize: {{x: 0, y: 0}}\n"
    "    newSize: {{x: 0, y: 0}}\n    adaptiveTilingThreshold: 0\n"
    "    drawMode: 0\n    adaptiveTiling: 0\n  m_AutoTiling: 0\n"
    "  m_Size: {size}\n  m_EdgeRadius: 0")

CIRCLE2D = ("CircleCollider2D:\n" + _HEAD + _COLLIDER_COMMON.replace(
    "  m_Material: {material}", "  m_Material: {{fileID: 0}}") +
    "\n  m_Radius: {radius}")

AUDIO_SOURCE = """AudioSource:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  serializedVersion: 4
  OutputAudioMixerGroup: {{fileID: 0}}
  m_audioClip: {{fileID: 0}}
  m_Resource: {{fileID: 0}}
  m_PlayOnAwake: 0
  m_Volume: 1
  m_Pitch: 1
  Loop: 0
  Mute: 0
  Spatialize: 0
  SpatializePostEffects: 0
  Priority: 128
  DopplerLevel: 1
  MinDistance: 1
  MaxDistance: 500
  Pan2D: 0
  rolloffMode: 0
  BypassEffects: 0
  BypassListenerEffects: 0
  BypassReverbZones: 0
  rolloffCustomCurve:
    serializedVersion: 2
    m_Curve:
    - serializedVersion: 3
      time: 0
      value: 1
      inSlope: 0
      outSlope: 0
      tangentMode: 0
      weightedMode: 0
      inWeight: 0.33333334
      outWeight: 0.33333334
    m_PreInfinity: 2
    m_PostInfinity: 2
    m_RotationOrder: 4
  panLevelCustomCurve:
    serializedVersion: 2
    m_Curve:
    - serializedVersion: 3
      time: 0
      value: 0
      inSlope: 0
      outSlope: 0
      tangentMode: 0
      weightedMode: 0
      inWeight: 0.33333334
      outWeight: 0.33333334
    m_PreInfinity: 2
    m_PostInfinity: 2
    m_RotationOrder: 4
  spreadCustomCurve:
    serializedVersion: 2
    m_Curve:
    - serializedVersion: 3
      time: 0
      value: 0
      inSlope: 0
      outSlope: 0
      tangentMode: 0
      weightedMode: 0
      inWeight: 0.33333334
      outWeight: 0.33333334
    m_PreInfinity: 2
    m_PostInfinity: 2
    m_RotationOrder: 4
  reverbZoneMixCustomCurve:
    serializedVersion: 2
    m_Curve:
    - serializedVersion: 3
      time: 0
      value: 1
      inSlope: 0
      outSlope: 0
      tangentMode: 0
      weightedMode: 0
      inWeight: 0.33333334
      outWeight: 0.33333334
    m_PreInfinity: 2
    m_PostInfinity: 2
    m_RotationOrder: 4"""


PREFAB_INSTANCE = """PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {{fileID: 0}}
    m_Modifications:
{mods}
    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents: []
  m_SourcePrefab: {{fileID: 100100000, guid: {guid}, type: 3}}"""


def _mod(target_fid, guid, path, value, obj_ref="{fileID: 0}"):
    return ("    - target: {fileID: %d, guid: %s, type: 3}\n"
            "      propertyPath: %s\n"
            "      value: %s\n"
            "      objectReference: %s" % (target_fid, guid, path, value, obj_ref))


def prefab_instance(doc, key, prefab_path, manifest, name, pos=(0, 0, 0), rot_z=0.0,
                    extra=()):
    """Root-level instance of a generated prefab, positioned and renamed.

    `extra` is a sequence of (target_fid, propertyPath, value) applied on top.
    """
    import math
    guid = guid_for(prefab_path)
    go = manifest["go"]
    tr = manifest["tr"]

    h = math.radians(rot_z) * 0.5
    mods = [
        _mod(go, guid, "m_Name", name),
        _mod(tr, guid, "m_LocalPosition.x", num(pos[0])),
        _mod(tr, guid, "m_LocalPosition.y", num(pos[1])),
        _mod(tr, guid, "m_LocalPosition.z", num(pos[2] if len(pos) > 2 else 0)),
        _mod(tr, guid, "m_LocalRotation.w", num(math.cos(h))),
        _mod(tr, guid, "m_LocalRotation.x", "0"),
        _mod(tr, guid, "m_LocalRotation.y", "0"),
        _mod(tr, guid, "m_LocalRotation.z", num(math.sin(h))),
        _mod(tr, guid, "m_LocalEulerAnglesHint.x", "0"),
        _mod(tr, guid, "m_LocalEulerAnglesHint.y", "0"),
        _mod(tr, guid, "m_LocalEulerAnglesHint.z", num(rot_z)),
    ]
    for target, path, value in extra:
        mods.append(_mod(target, guid, path, value))

    inst = fid(doc.key + "/prefab/" + key)
    doc.blocks.append((1001, inst, PREFAB_INSTANCE.format(
        mods="\n".join(mods), guid=guid)))
    return inst
