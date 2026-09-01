using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Everything the bike does that is not physics: wheels spin with real
    /// travel, the wheels ride up into the arches under load, and the rider
    /// shifts weight. Restrained on purpose - the bike body itself never
    /// animates, so the physics rotation stays readable.
    /// </summary>
    public class BikeVisuals : MonoBehaviour
    {
        [Header("Parts")]
        [SerializeField] SpriteRenderer bodyRenderer;
        [SerializeField] SpriteRenderer riderRenderer;
        [SerializeField] Transform riderPivot;
        [SerializeField] Transform frontWheel;
        [SerializeField] Transform rearWheel;
        [SerializeField] SpriteRenderer frontWheelRenderer;
        [SerializeField] SpriteRenderer rearWheelRenderer;

        [Header("Tuning")]
        [SerializeField] float wheelRadius = 0.54f;

        [Tooltip("Degrees the rider swings between hard braking and full throttle.")]
        [SerializeField] float riderLeanRange = 13f;

        [SerializeField] float riderLeanSmoothing = 0.09f;

        [Tooltip("Extra squash on the wheel at full compression.")]
        [SerializeField] float wheelSquash = 0.08f;

        BikeController bike;
        GroundSensor sensor;
        Rigidbody2D body;

        Vector3 frontRest, rearRest;
        float frontSpin, rearSpin;
        float riderAngle, riderAngleVel;
        float landingKick;

        void Awake()
        {
            bike = GetComponentInParent<BikeController>();
            sensor = bike != null ? bike.Ground : null;
            body = bike != null ? bike.Body : null;

            if (frontWheel != null) frontRest = frontWheel.localPosition;
            if (rearWheel != null) rearRest = rearWheel.localPosition;
        }

        void OnEnable()
        {
            if (bike != null) bike.Landed += OnLanded;
        }

        void OnDisable()
        {
            if (bike != null) bike.Landed -= OnLanded;
        }

        void Start()
        {
            if (bike != null) Apply(bike.Config);
        }

        /// <summary>Swap in the selected bike's art. Called by the spawner.</summary>
        public void Apply(BikeConfig config)
        {
            if (config == null) return;
            if (bodyRenderer != null) bodyRenderer.sprite = config.body;
            if (riderRenderer != null) riderRenderer.sprite = config.rider;
            if (frontWheelRenderer != null) frontWheelRenderer.sprite = config.wheelFront;
            if (rearWheelRenderer != null) rearWheelRenderer.sprite = config.wheelRear;
        }

        void OnLanded(LandingQuality quality, float impact)
        {
            // One number drives the whole reaction: wheels compress, rider drops.
            landingKick = Mathf.Clamp01(impact / 18f);
        }

        void LateUpdate()
        {
            float dt = Time.deltaTime;
            if (dt <= 0f) return;

            landingKick = Mathf.MoveTowards(landingKick, 0f, dt * 3.2f);

            SpinWheels(dt);
            RideSuspension();
            LeanRider(dt);
        }

        void SpinWheels(float dt)
        {
            if (body == null || wheelRadius <= 0.01f) return;

            // Wheels turn with the distance actually travelled along the bike's
            // own forward axis, so they stall when the bike is sliding sideways.
            float travel = Vector2.Dot(body.linearVelocity, transform.right) * dt;
            float degrees = -(travel / wheelRadius) * Mathf.Rad2Deg;

            frontSpin += degrees;
            rearSpin += degrees;

            if (frontWheel != null) frontWheel.localRotation = Quaternion.Euler(0f, 0f, frontSpin);
            if (rearWheel != null) rearWheel.localRotation = Quaternion.Euler(0f, 0f, rearSpin);
        }

        void RideSuspension()
        {
            if (sensor == null || bike == null || bike.Config == null) return;
            float travel = bike.Config.suspensionTravel;

            Push(frontWheel, frontWheelRenderer, frontRest,
                 Mathf.Max(sensor.FrontCompression, landingKick), travel);
            Push(rearWheel, rearWheelRenderer, rearRest,
                 Mathf.Max(sensor.RearCompression, landingKick), travel);
        }

        void Push(Transform wheel, SpriteRenderer renderer, Vector3 rest, float load, float travel)
        {
            if (wheel == null) return;
            load = Mathf.Clamp01(load);
            var p = rest;
            p.y = rest.y + load * travel;
            wheel.localPosition = p;

            if (renderer != null)
            {
                float s = 1f - load * wheelSquash;
                renderer.transform.localScale = new Vector3(1f, s, 1f);
            }
        }

        void LeanRider(float dt)
        {
            if (riderPivot == null) return;

            // Forward under throttle, back under brake, tucked in the air.
            float target = (RideInput.Brake - RideInput.Throttle) * riderLeanRange;
            if (bike != null && !bike.Grounded) target += 5f;
            if (bike != null && bike.IsWiped) target = -34f;
            target -= landingKick * 10f;

            riderAngle = Mathf.SmoothDamp(riderAngle, target, ref riderAngleVel,
                                          riderLeanSmoothing, Mathf.Infinity, dt);
            riderPivot.localRotation = Quaternion.Euler(0f, 0f, riderAngle);
        }
    }
}
