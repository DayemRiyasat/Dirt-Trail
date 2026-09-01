using System;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Arcade bike physics. Deliberately not a suspension simulation: one rigid
    /// body, forces along the measured ground tangent, torque for lean. What it
    /// adds over a raw AddTorque prototype is that every force is slope-aware,
    /// runs in FixedUpdate, and reports landings well enough to score them.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class BikeController : MonoBehaviour
    {
        [SerializeField] BikeConfig config;
        [SerializeField] GroundSensor ground;

        [Header("Landing grades, degrees off the surface normal")]
        [SerializeField] float perfectAngle = 12f;
        [SerializeField] float cleanAngle = 30f;
        [SerializeField] float roughAngle = 62f;

        [Tooltip("Below this impact speed a bad angle just scrubs you, it does not end the run.")]
        [SerializeField] float wipeoutSpeed = 6.5f;

        [Header("Nitro")]
        [SerializeField] float nitroBurst = 9f;
        [SerializeField] float nitroTopSpeedBonus = 1.25f;

        Rigidbody2D body;
        Vector2 lastVelocity;
        bool wasGrounded = true;

        float nitroLeft;
        float airBoostLeft;
        float nitroCharges;

        public event Action<LandingQuality, float> Landed;
        public event Action<float> Launched;      // airborne, with launch speed
        public event Action Wiped;
        public event Action<PickupKind> PowerupStarted;

        public BikeConfig Config => config;
        public GroundSensor Ground => ground;
        public Rigidbody2D Body => body;

        public bool ControlsEnabled { get; private set; } = true;
        public bool IsWiped { get; private set; }

        public float Speed => body == null ? 0f : body.linearVelocity.magnitude;
        public float ForwardSpeed =>
            body == null ? 0f : Vector2.Dot(body.linearVelocity, Vector2.right);

        public bool NitroActive => nitroLeft > 0f;
        public bool AirBoostActive => airBoostLeft > 0f;
        public int NitroCharges => Mathf.FloorToInt(nitroCharges);

        public float AirTime => ground == null ? 0f : ground.AirTime;
        public bool Grounded => ground != null && ground.Grounded;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            if (ground == null) ground = GetComponent<GroundSensor>();
            ApplyConfig();
        }

        void OnEnable() => RideInput.Resolve();

        /// <summary>Called by the spawner after the garage selection is known.</summary>
        public void Configure(BikeConfig cfg)
        {
            config = cfg;
            ApplyConfig();
        }

        void ApplyConfig()
        {
            if (config == null || body == null) return;
            body.mass = config.mass;
            body.gravityScale = config.gravityScale;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        }

        void FixedUpdate()
        {
            if (config == null || body == null) return;

            TickTimers(Time.fixedDeltaTime);

            bool grounded = ground != null && ground.Grounded;
            DetectTransitions(grounded);

            body.angularDamping = grounded ? config.groundAngularDamping : AirDamping();

            if (ControlsEnabled && !IsWiped)
            {
                ApplyDrive(grounded);
                ApplyLean(grounded);
            }

            if (grounded) AlignToSlope();
            else AssistLanding();

            ClampSpeed();
            lastVelocity = body.linearVelocity;
        }

        void Update()
        {
            if (!ControlsEnabled || IsWiped) return;
            if (RideInput.NitroPressed) TryFireNitro();
        }

        // ------------------------------------------------------------ drive --
        void ApplyDrive(bool grounded)
        {
            if (ground == null || !ground.Effective) return;   // no bite in the air

            float throttle = RideInput.Throttle;
            float brake = RideInput.Brake;

            Vector2 tangent = grounded ? ground.Forward : (Vector2)transform.right;

            if (throttle > 0f)
            {
                float power = config.enginePower * (NitroActive ? config.nitroMultiplier : 1f);
                body.AddForce(tangent * (power * throttle));
            }

            if (brake > 0f)
            {
                // Brake against travel direction rather than blindly backwards, so
                // holding brake on a downhill actually slows you instead of reversing.
                Vector2 travel = body.linearVelocity;
                if (travel.sqrMagnitude > 0.25f)
                    body.AddForce(-travel.normalized * (config.brakeForce * brake));
            }
        }

        /// <summary>
        /// Rotation is free high up and increasingly damped as the ground comes
        /// back. Spinning fast is the fun part; spinning fast twenty centimetres
        /// off the deck is just a dice roll on the landing angle.
        /// </summary>
        float AirDamping()
        {
            if (ground == null || config.settleHeight <= 0.01f)
                return config.airAngularDamping;

            float approach = 1f - Mathf.Clamp01(ground.Height / config.settleHeight);
            return Mathf.Lerp(config.airAngularDamping, config.landingSpinDamp,
                              approach * approach);
        }

        void ApplyLean(bool grounded)
        {
            float lean = RideInput.Lean;
            if (Mathf.Approximately(lean, 0f)) return;

            float torque = grounded ? config.groundTorque : config.airTorque;

            if (!grounded)
            {
                if (AirBoostActive) torque *= 1.5f;

                // Authority tapers off on the way down, so the rider is aiming
                // the landing rather than still winding the flip up.
                if (ground != null && config.settleHeight > 0.01f)
                {
                    float room = Mathf.Clamp01(ground.Height / config.settleHeight);
                    torque *= Mathf.Lerp(0.25f, 1f, room);
                }

                // Never wind past the ceiling in the direction already spinning.
                float wanted = -lean;
                float spin = body.angularVelocity;
                if (wanted * spin > 0f && Mathf.Abs(spin) >= config.spinCeiling) return;
            }

            // Negative because +lean means nose-down, which is clockwise in 2D.
            body.AddTorque(-lean * torque);
        }

        /// <summary>Gentle PD pull toward square-with-the-slope. Keeps the bike from
        /// buzzing on rough ground without taking control away from the rider.</summary>
        void AlignToSlope()
        {
            float error = Vector2.SignedAngle(transform.up, ground.Normal);
            float damping = body.angularVelocity * 0.18f;
            body.AddTorque((error * Mathf.Deg2Rad * config.groundAlign) - damping);
        }

        /// <summary>Only bites in the last stretch before touchdown, and only when the
        /// rider is already roughly right. Rewards a good approach, does not fake one.</summary>
        void AssistLanding()
        {
            if (ground == null || config.landingAssist <= 0f) return;
            if (ground.Height > 3.0f) return;

            float error = Vector2.SignedAngle(transform.up, ground.Normal);
            if (Mathf.Abs(error) > 55f) return;

            float proximity = Mathf.InverseLerp(3.0f, 0.6f, ground.Height);
            body.AddTorque(error * Mathf.Deg2Rad * config.landingAssist * proximity);
        }

        void ClampSpeed()
        {
            float ceiling = config.maxSpeed * (NitroActive ? nitroTopSpeedBonus : 1f);
            Vector2 v = body.linearVelocity;
            float horizontal = Mathf.Abs(v.x);
            if (horizontal <= ceiling) return;

            // Soft clamp: bleed the excess rather than snapping, so hitting the
            // ceiling on a downhill does not feel like a wall.
            v.x = Mathf.Lerp(v.x, Mathf.Sign(v.x) * ceiling, 0.12f);
            body.linearVelocity = v;
        }

        // ------------------------------------------------------- transitions --
        void DetectTransitions(bool grounded)
        {
            if (grounded == wasGrounded) return;

            if (grounded) ResolveLanding();
            else Launched?.Invoke(lastVelocity.magnitude);

            wasGrounded = grounded;
        }

        void ResolveLanding()
        {
            float angle = Mathf.Abs(Vector2.SignedAngle(transform.up, ground.Normal));
            float impact = Mathf.Abs(Vector2.Dot(lastVelocity, -ground.Normal));

            LandingQuality quality;
            if (angle <= perfectAngle) quality = LandingQuality.Perfect;
            else if (angle <= cleanAngle) quality = LandingQuality.Clean;
            else if (angle <= roughAngle) quality = LandingQuality.Rough;
            else quality = impact >= wipeoutSpeed ? LandingQuality.Wipeout : LandingQuality.Rough;

            Landed?.Invoke(quality, impact);
            if (quality == LandingQuality.Wipeout) Wipeout();
        }

        // ---------------------------------------------------------- powerups --
        void TickTimers(float dt)
        {
            if (nitroLeft > 0f) nitroLeft = Mathf.Max(0f, nitroLeft - dt);
            if (airBoostLeft > 0f) airBoostLeft = Mathf.Max(0f, airBoostLeft - dt);
        }

        public void GrantPowerup(PickupKind kind, float duration)
        {
            switch (kind)
            {
                case PickupKind.Nitro:
                    // Nitro is banked, not auto-spent: choosing when to burn it
                    // is the interesting decision.
                    nitroCharges = Mathf.Min(nitroCharges + 1f, 3f);
                    break;
                case PickupKind.AirControl:
                    airBoostLeft = Mathf.Max(airBoostLeft, duration);
                    break;
            }
            PowerupStarted?.Invoke(kind);
        }

        void TryFireNitro()
        {
            if (nitroCharges < 1f || NitroActive) return;
            nitroCharges -= 1f;
            nitroLeft = config.nitroDuration;
            body.AddForce((Vector2)transform.right * nitroBurst, ForceMode2D.Impulse);
            PowerupStarted?.Invoke(PickupKind.Nitro);
        }

        // ------------------------------------------------------------- state --
        public void SetControlsEnabled(bool value) => ControlsEnabled = value;

        public void Wipeout()
        {
            if (IsWiped) return;
            IsWiped = true;
            ControlsEnabled = false;
            nitroLeft = 0f;
            airBoostLeft = 0f;
            body.angularDamping = 0.6f;
            Wiped?.Invoke();
        }

        /// <summary>Put the bike back on the trail at a checkpoint, upright and stopped.</summary>
        public void Respawn(Vector2 position, float zRotation)
        {
            IsWiped = false;
            ControlsEnabled = true;
            wasGrounded = true;
            lastVelocity = Vector2.zero;
            nitroLeft = 0f;
            airBoostLeft = 0f;

            body.linearVelocity = Vector2.zero;
            body.angularVelocity = 0f;
            body.position = position;
            body.rotation = zRotation;
            transform.SetPositionAndRotation(position, Quaternion.Euler(0f, 0f, zRotation));
            ApplyConfig();
        }
    }
}
