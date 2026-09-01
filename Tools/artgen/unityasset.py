"""Deterministic Unity .meta emission for procedurally generated sprites.

Every asset gets a GUID derived from its project path, so regenerating art never
breaks existing scene/prefab references.
"""
import hashlib
import os

_NS = "dirttrail.artgen.v1"


def _digest(path, salt=""):
    return hashlib.md5((_NS + "|" + salt + "|" + path.replace("\\", "/")).encode()).hexdigest()


def guid_for(path):
    return _digest(path)


def internal_id_for(path):
    h = int(_digest(path, "iid")[:16], 16)
    return (h % 8_000_000_000_000_000) + 1_000_000_000_000_000


def sprite_id_for(path):
    return _digest(path, "sid")[:16] + "0800000000000000"


_PLATFORMS = ("DefaultTexturePlatform", "Standalone", "Android", "WebGL", "iOS")


def _platform_block(max_size):
    out = []
    for target in _PLATFORMS:
        out.append(
            f"  - serializedVersion: 4\n"
            f"    buildTarget: {target}\n"
            f"    maxTextureSize: {max_size}\n"
            "    resizeAlgorithm: 0\n"
            "    textureFormat: -1\n"
            "    textureCompression: 1\n"
            "    compressionQuality: 50\n"
            "    crunchedCompression: 0\n"
            "    allowsAlphaSplitting: 0\n"
            "    overridden: 0\n"
            "    ignorePlatformSupport: 0\n"
            "    androidETC2FallbackOverride: 0\n"
            "    forceMaximumCompressionQuality_BC6H_BC7: 0"
        )
    return "\n".join(out)


def write_sprite_meta(png_path, size, ppu=100, pivot=(0.5, 0.5), wrap=1,
                      filter_mode=1, border=(0, 0, 0, 0), max_size=2048,
                      alignment=9, mesh_type=1):
    """Emit `<png_path>.meta`. `png_path` must be project-relative (Assets/...).

    alignment 9 = Custom (uses `pivot`); Unity's other values ignore the pivot,
    so we always write Custom and let `pivot` be the single source of truth.
    """
    rel = png_path.replace("\\", "/")
    name = os.path.splitext(os.path.basename(rel))[0]
    sub = f"{name}_0"
    guid = guid_for(rel)
    iid = internal_id_for(rel)
    sid = sprite_id_for(rel)
    w, h = size
    px, py = pivot
    bx, by, bz, bw = border

    meta = f"""fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable:
  - first:
      213: {iid}
    second: {sub}
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: {max_size}
  textureSettings:
    serializedVersion: 2
    filterMode: {filter_mode}
    aniso: 1
    mipBias: 0
    wrapU: {wrap}
    wrapV: {wrap}
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 2
  spriteExtrude: 1
  spriteMeshType: {mesh_type}
  alignment: {alignment}
  spritePivot: {{x: {px}, y: {py}}}
  spritePixelsToUnits: {ppu}
  spriteBorder: {{x: {bx}, y: {by}, z: {bz}, w: {bw}}}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings:
{_platform_block(max_size)}
  spriteSheet:
    serializedVersion: 2
    sprites:
    - serializedVersion: 2
      name: {sub}
      rect:
        serializedVersion: 2
        x: 0
        y: 0
        width: {w}
        height: {h}
      alignment: {alignment}
      pivot: {{x: {px}, y: {py}}}
      border: {{x: {bx}, y: {by}, z: {bz}, w: {bw}}}
      customData: 
      outline: []
      physicsShape: []
      tessellationDetail: -1
      bones: []
      spriteID: {sid}
      internalID: {iid}
      vertices: []
      indices: 
      edges: []
      weights: []
    outline: []
    customData: 
    physicsShape: []
    bones: []
    spriteID: 
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
    secondaryTextures: []
    spriteCustomMetadata:
      entries: []
    nameFileIdTable:
      {sub}: {iid}
  mipmapLimitGroupName: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
    with open(rel + ".meta", "w", newline="\n") as fh:
        fh.write(meta)
    return {"guid": guid, "fileID": iid, "path": rel}


def folder_meta(folder):
    """Emit a .meta for a folder if one does not already exist."""
    rel = folder.replace("\\", "/").rstrip("/")
    if os.path.exists(rel + ".meta"):
        return
    with open(rel + ".meta", "w", newline="\n") as fh:
        fh.write("fileFormatVersion: 2\nguid: %s\nfolderAsset: yes\n"
                 "DefaultImporter:\n  externalObjects: {}\n  userData: \n"
                 "  assetBundleName: \n  assetBundleVariant: \n" % guid_for(rel))


def text_meta(path, ext_guid_salt=""):
    rel = path.replace("\\", "/")
    with open(rel + ".meta", "w", newline="\n") as fh:
        fh.write("fileFormatVersion: 2\nguid: %s\nDefaultImporter:\n"
                 "  externalObjects: {}\n  userData: \n  assetBundleName: \n"
                 "  assetBundleVariant: \n" % guid_for(rel))
