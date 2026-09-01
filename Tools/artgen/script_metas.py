"""Write a stable .meta beside every .cs under Assets, preserving existing GUIDs."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unityasset import guid_for, folder_meta

TEMPLATE = """fileFormatVersion: 2
guid: %s
MonoImporter:
  externalObjects: {}
  serializedVersion: 2
  defaultReferences: []
  executionOrder: 0
  icon: {instanceID: 0}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""


def main():
    seen = {}
    for cs in sorted(glob.glob("Assets/**/*.cs", recursive=True)):
        rel = cs.replace("\\", "/")
        meta = rel + ".meta"
        guid = None
        if os.path.exists(meta):
            for line in open(meta, encoding="utf-8"):
                if line.startswith("guid:"):
                    guid = line.split(":", 1)[1].strip()
                    break
        if not guid:
            guid = guid_for(rel)
        with open(meta, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(TEMPLATE % guid)
        seen[os.path.splitext(os.path.basename(rel))[0]] = guid
    for d in sorted({os.path.dirname(p) for p in glob.glob("Assets/Scripts/**/*", recursive=True)}):
        if d:
            folder_meta(d)
    return seen


if __name__ == "__main__":
    for name, guid in sorted(main().items()):
        print("%-28s %s" % (name, guid))
