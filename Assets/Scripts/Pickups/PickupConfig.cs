using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// A pickup, typed. The prototype matched on a free-text field and switched
    /// on the string "torque"; the kind is now an enum, so an unhandled case is
    /// a compile-time problem rather than a silent no-op.
    /// </summary>
    [CreateAssetMenu(fileName = "Pickup", menuName = "Dirt Trail/Pickup")]
    public class PickupConfig : ScriptableObject
    {
        public PickupKind kind = PickupKind.Nitro;

        public Sprite icon;
        public Color tint = new Color(0.85f, 0.37f, 0.15f, 1f);

        [Tooltip("Seconds. Ignored by pickups that bank a charge instead of ticking down.")]
        public float duration = 6f;

        [Tooltip("Points awarded for collecting it at all.")]
        public int bonus = 50;
    }
}
