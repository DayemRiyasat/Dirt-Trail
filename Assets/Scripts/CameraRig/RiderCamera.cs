using Unity.Cinemachine;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Drives a target transform that the Cinemachine camera follows, plus the
    /// orthographic size. Doing the framing here and leaving damping to
    /// Cinemachine keeps both jobs simple.
    ///
    /// Three things move the frame: how fast you are going (look further ahead,
    /// pull back a little), whether you are in the air (lift, so the landing is
    /// on screen before you commit to it), and impacts (impulse, briefly).
    /// </summary>
    public class RiderCamera : MonoBehaviour
    {
        [SerializeField] BikeController bike;
        [SerializeField] Transform target;
        [SerializeField] CinemachineCamera vcam;
        [SerializeField] CinemachineImpulseSource impulse;

        [Header("Look ahead")]
        [Tooltip("World units in front of the bike at full speed.")]
        [SerializeField] float maxLookAhead = 6.5f;

        [SerializeField] float lookAheadSpeed = 20f;
        [SerializeField] float lookAheadSmoothing = 0.35f;

        [Header("Vertical framing")]
        [Tooltip("How much of the bike's height above the ground the camera gives back.")]
        [SerializeField] float airLift = 0.45f;

        [SerializeField] float maxAirLift = 7f;
        [SerializeField] float verticalSmoothing = 0.22f;

        [Header("Zoom")]
        [SerializeField] float baseSize = 12.5f;

        [Tooltip("Extra orthographic size at top speed.")]
        [SerializeField] float speedZoom = 2.2f;

        [Tooltip("Extra orthographic size at maximum height above ground.")]
        [SerializeField] float airZoom = 3.4f;

        [SerializeField] float nitroZoom = 1.1f;
        [SerializeField] float zoomSmoothing = 0.5f;

        [Header("Impulse")]
        [Tooltip("Impact speed that produces a full-strength shake.")]
        [SerializeField] float impulseReference = 20f;

        [SerializeField] float maxImpulse = 0.45f;
        [SerializeField] float wipeoutImpulse = 0.6f;

        float lookAhead, lookAheadVel;
        float lift, liftVel;
        float size, sizeVel;

        void Awake()
        {
            if (bike == null) bike = FindFirstObjectByType<BikeController>();
            if (vcam == null) vcam = GetComponentInChildren<CinemachineCamera>();
            if (impulse == null) impulse = GetComponent<CinemachineImpulseSource>();
            size = baseSize;
        }

        void OnEnable()
        {
            if (bike == null) return;
            bike.Landed += OnLanded;
            bike.Wiped += OnWiped;
        }

        void OnDisable()
        {
            if (bike == null) return;
            bike.Landed -= OnLanded;
            bike.Wiped -= OnWiped;
        }

        void LateUpdate()
        {
            if (bike == null || target == null) return;
            float dt = Time.deltaTime;
            if (dt <= 0f) return;

            float speed01 = Mathf.Clamp01(Mathf.Abs(bike.ForwardSpeed) / lookAheadSpeed);
            float direction = bike.ForwardSpeed < -0.5f ? -1f : 1f;

            float wantAhead = speed01 * maxLookAhead * direction;
            lookAhead = Mathf.SmoothDamp(lookAhead, wantAhead, ref lookAheadVel,
                                         lookAheadSmoothing, Mathf.Infinity, dt);

            float height = bike.Ground != null ? bike.Ground.Height : 0f;
            float wantLift = bike.Grounded ? 0f
                : Mathf.Min(height * airLift, maxAirLift);
            lift = Mathf.SmoothDamp(lift, wantLift, ref liftVel,
                                    verticalSmoothing, Mathf.Infinity, dt);

            Vector3 p = bike.transform.position;
            target.position = new Vector3(p.x + lookAhead, p.y + lift, p.z);

            if (vcam == null) return;
            float air01 = Mathf.Clamp01(height / 14f);
            float wantSize = baseSize
                             + speed01 * speedZoom
                             + (bike.Grounded ? 0f : air01 * airZoom)
                             + (bike.NitroActive ? nitroZoom : 0f);

            size = Mathf.SmoothDamp(size, wantSize, ref sizeVel,
                                    zoomSmoothing, Mathf.Infinity, dt);

            var lens = vcam.Lens;
            lens.OrthographicSize = size;
            vcam.Lens = lens;
        }

        void OnLanded(LandingQuality quality, float impact)
        {
            if (quality == LandingQuality.Perfect) return;    // reward a good one with silence
            float strength = Mathf.Clamp01(impact / impulseReference) * maxImpulse;
            if (strength > 0.05f) Shake(strength);
        }

        void OnWiped() => Shake(wipeoutImpulse);

        public void Shake(float strength)
        {
            if (impulse == null || !Settings.ShakeOn) return;
            impulse.GenerateImpulseWithForce(strength);
        }
    }
}
