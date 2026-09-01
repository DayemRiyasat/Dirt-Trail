using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// The burst sprites, grouped by the moment they belong to. Loaded from
    /// Resources so anything that wants to shout can find them without wiring.
    /// </summary>
    [CreateAssetMenu(fileName = "ShoutKit", menuName = "Dirt Trail/Shout Kit")]
    public class ShoutKit : ScriptableObject
    {
        public const string ResourcePath = "ShoutKit";

        [Tooltip("Single rotation landed.")] public Sprite[] flip;
        [Tooltip("Two or more rotations landed.")] public Sprite[] bigFlip;
        [Tooltip("Airtime with no rotation.")] public Sprite[] air;
        [Tooltip("Landed square on the slope.")] public Sprite[] perfect;
        [Tooltip("Ended the run.")] public Sprite[] wipeout;
        public Sprite[] nitro;
        public Sprite[] airPickup;

        static ShoutKit cached;

        public static ShoutKit Load()
        {
            if (cached == null) cached = Resources.Load<ShoutKit>(ResourcePath);
            return cached;
        }
    }
}
