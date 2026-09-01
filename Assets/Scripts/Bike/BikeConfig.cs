using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Everything that makes one bike feel different from another: art, mass,
    /// how hard it pulls, and how willingly it rotates. Tuned as data so the
    /// controller stays free of per-bike special cases.
    /// </summary>
    [CreateAssetMenu(fileName = "Bike", menuName = "Dirt Trail/Bike")]
    public class BikeConfig : ScriptableObject
    {
        [Header("Identity")]
        public string displayName = "SCOUT";

        [Tooltip("One short line, garage card. Lower case, no marketing.")]
        [TextArea(2, 3)]
        public string blurb = "Light. Flicks fast, lands nervous.";

        [Header("Art")]
        public Sprite body;
        public Sprite rider;
        public Sprite wheelFront;
        public Sprite wheelRear;
        public Color dust = new Color(0.78f, 0.62f, 0.42f, 1f);

        [Header("Body")]
        public float mass = 3f;
        public float gravityScale = 2.2f;

        [Tooltip("Drive force along the ground tangent, in newtons.")]
        public float enginePower = 34f;

        [Tooltip("Soft ceiling on ground speed, world units per second.")]
        public float maxSpeed = 21f;

        public float brakeForce = 26f;

        [Header("Rotation")]
        [Tooltip("Lean authority while a wheel is down. Small: the ground should win.")]
        public float groundTorque = 7f;

        [Tooltip("Lean authority in the air. This is what makes flips possible.")]
        public float airTorque = 18f;

        public float groundAngularDamping = 4.5f;
        public float airAngularDamping = 0.35f;

        [Tooltip("Hard ceiling on spin rate, degrees per second. Without one the " +
                 "torque keeps accelerating for the whole flight and the landing " +
                 "becomes a coin flip rather than a decision.")]
        public float spinCeiling = 320f;

        [Tooltip("Height above the ground at which rotation starts to settle.")]
        public float settleHeight = 7f;

        [Tooltip("Angular damping right before touchdown. High enough that the " +
                 "last moments of a flip are aiming, not accelerating.")]
        public float landingSpinDamp = 4f;

        [Header("Feel")]
        [Tooltip("Torque pulling the bike square to the slope while grounded.")]
        public float groundAlign = 22f;

        [Tooltip("Torque pulling the bike level as it approaches a landing.")]
        public float landingAssist = 6f;

        [Tooltip("Wheel travel in world units. Purely visual.")]
        public float suspensionTravel = 0.16f;

        [Header("Nitro")]
        public float nitroMultiplier = 1.65f;
        public float nitroDuration = 3.5f;

        [Header("Garage readout, 0 to 1")]
        [Range(0f, 1f)] public float statSpeed = 0.7f;
        [Range(0f, 1f)] public float statGrip = 0.5f;
        [Range(0f, 1f)] public float statAir = 0.85f;
    }
}
