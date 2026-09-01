using TMPro;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// The whole visual language of the interface in one asset: three plates, a
    /// stripe rule, a chevron, and the palette. Loaded from Resources so screens
    /// built in code can find it without inspector wiring.
    /// </summary>
    [CreateAssetMenu(fileName = "UISkin", menuName = "Dirt Trail/UI Skin")]
    public class UISkin : ScriptableObject
    {
        public const string ResourcePath = "UISkin";

        [Header("Plates, 9-sliced")]
        public Sprite plateDark;
        public Sprite plateSand;
        public Sprite plateRust;

        [Header("Marks")]
        public Sprite stripe;
        public Sprite chevron;

        [Header("Type")]
        public TMP_FontAsset font;

        static UISkin cached;

        public static UISkin Load()
        {
            if (cached == null) cached = Resources.Load<UISkin>(ResourcePath);
            return cached;
        }

        // --- palette, mirrored from the art generator ------------------------
        public static readonly Color Ink = Hex(0x221814);
        public static readonly Color Sand = Hex(0xF3E4C7);
        public static readonly Color SandDim = Hex(0xC9B491);
        public static readonly Color Clay = Hex(0xBC8450);
        public static readonly Color Rust = Hex(0x834C2F);
        public static readonly Color Bark = Hex(0x2E1F18);
        public static readonly Color Orange = Hex(0xD85E26);
        public static readonly Color Sage = Hex(0x6C774C);

        public TMP_FontAsset Font =>
            font != null ? font
            : TMP_Settings.defaultFontAsset != null ? TMP_Settings.defaultFontAsset
            : Resources.Load<TMP_FontAsset>("Fonts & Materials/LiberationSans SDF");

        static Color Hex(int rgb) => new Color(
            ((rgb >> 16) & 0xFF) / 255f,
            ((rgb >> 8) & 0xFF) / 255f,
            (rgb & 0xFF) / 255f, 1f);
    }
}
