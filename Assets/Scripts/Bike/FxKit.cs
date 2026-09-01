using UnityEngine;

namespace DirtTrail
{
    /// <summary>Textures the effects need, in one Resources asset.</summary>
    [CreateAssetMenu(fileName = "FxKit", menuName = "Dirt Trail/FX Kit")]
    public class FxKit : ScriptableObject
    {
        public const string ResourcePath = "FxKit";

        public Sprite dust;
        public Sprite clod;
        public Sprite spark;
        public Sprite shadow;

        static FxKit cached;

        public static FxKit Load()
        {
            if (cached == null) cached = Resources.Load<FxKit>(ResourcePath);
            return cached;
        }
    }
}
