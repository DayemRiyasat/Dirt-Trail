"""Lift component blocks verbatim from the original scene.

Camera, Cinemachine, Light2D, Sprite Shape and the event system are all long,
version-specific blobs. Rather than retype them and risk a stale field, the new
scenes reuse the ones Unity itself wrote, with the ids swapped.
"""
import os
import re

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_source.unity")
_docs = None


def _load():
    global _docs
    if _docs is not None:
        return _docs
    text = open(SOURCE, encoding="utf-8").read()
    _docs = {}
    for chunk in re.split(r"(?m)^--- ", text)[1:]:
        head = re.match(r"!u!(\d+) &(-?\d+)( stripped)?\n", chunk)
        if not head:
            continue
        cls, fid = int(head.group(1)), int(head.group(2))
        body = chunk[head.end():].rstrip("\n")
        _docs[fid] = (cls, body)
    return _docs


def block(fid):
    """(class_id, body) for a component in the source scene."""
    return _load()[fid]


def retarget(body, game_object):
    """Point a lifted component at a new GameObject."""
    return re.sub(r"^  m_GameObject: \{fileID: -?\d+\}$",
                  "  m_GameObject: {fileID: %d}" % game_object, body, flags=re.M)


def set_field(body, key, value, indent="  "):
    """Replace a top-level scalar or inline-mapping field."""
    pattern = r"(?m)^%s%s: .*$" % (re.escape(indent), re.escape(key))
    replacement = "%s%s: %s" % (indent, key, value)
    new, count = re.subn(pattern, replacement, body, count=1)
    if count == 0:
        raise KeyError("field not found: %s" % key)
    return new


def replace_section(body, key, new_text, indent="  "):
    """Replace a nested block that runs until the next line at `indent` depth."""
    lines = body.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.startswith(indent + key + ":") and not line.startswith(indent + " "):
            start = i
            break
    if start is None:
        raise KeyError("section not found: %s" % key)

    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i]
        if stripped.strip() == "":
            continue
        depth = len(stripped) - len(stripped.lstrip())
        if depth <= len(indent) and not stripped.lstrip().startswith("-"):
            end = i
            break
    return "\n".join(lines[:start] + new_text.split("\n") + lines[end:])


# --- fileIDs of the blocks worth reusing, from the original Level1 scene -----
CAMERA = 519420031
AUDIO_LISTENER = 519420029
URP_CAMERA_DATA = 519420030          # UniversalAdditionalCameraData
CINEMACHINE_BRAIN = 519420033        # CinemachineBrain
CINEMACHINE_CAMERA = 1945048590
CINEMACHINE_FOLLOW = 1945048592
LIGHT_2D = 619394801
SPRITE_SHAPE_CONTROLLER = 2088706568
EDGE_COLLIDER = 2088706571
EVENT_SYSTEM = 206771917
INPUT_MODULE = 206771918
