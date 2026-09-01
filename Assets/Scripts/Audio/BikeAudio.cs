using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Engine note tracks speed and throttle; it drops to a hollow idle the
    /// moment the wheels leave the ground, which is the cheapest way to make air
    /// feel like air. One-shots for the events worth hearing, and nothing else.
    /// </summary>
    [RequireComponent(typeof(AudioSource))]
    public class BikeAudio : MonoBehaviour
    {
        [SerializeField] BikeController bike;

        [Header("Engine")]
        [SerializeField] float idlePitch = 0.62f;
        [SerializeField] float redlinePitch = 2.05f;

        [Tooltip("Speed at which the engine is at full pitch.")]
        [SerializeField] float redlineSpeed = 20f;

        [SerializeField] float engineVolume = 0.34f;
        [SerializeField] float airVolume = 0.16f;
        [SerializeField] float pitchSmoothing = 0.12f;

        [Header("One shots")]
        [SerializeField] float landVolume = 0.55f;
        [SerializeField] float wipeoutVolume = 0.7f;
        [SerializeField] float pickupVolume = 0.5f;

        AudioSource engine;
        AudioSource oneShots;
        float pitch, pitchVel, volume;

        void Awake()
        {
            if (bike == null) bike = GetComponentInParent<BikeController>();

            engine = GetComponent<AudioSource>();
            engine.clip = ProceduralSfx.Engine;
            engine.loop = true;
            engine.playOnAwake = false;
            engine.spatialBlend = 0f;
            engine.volume = 0f;

            oneShots = gameObject.AddComponent<AudioSource>();
            oneShots.playOnAwake = false;
            oneShots.spatialBlend = 0f;

            pitch = idlePitch;
        }

        void OnEnable()
        {
            if (bike != null)
            {
                bike.Landed += OnLanded;
                bike.Wiped += OnWiped;
                bike.PowerupStarted += OnPowerup;
            }
            engine.Play();
        }

        void Start()
        {
            var run = RunManager.Instance;
            if (run != null) run.TrickBanked += OnTrickBanked;
        }

        void OnDisable()
        {
            if (bike != null)
            {
                bike.Landed -= OnLanded;
                bike.Wiped -= OnWiped;
                bike.PowerupStarted -= OnPowerup;
            }
            var run = RunManager.Instance;
            if (run != null) run.TrickBanked -= OnTrickBanked;
        }

        void Update()
        {
            if (bike == null) return;
            float dt = Time.unscaledDeltaTime;

            float speed01 = Mathf.Clamp01(Mathf.Abs(bike.ForwardSpeed) / redlineSpeed);
            bool grounded = bike.Grounded;

            // In the air the engine free-revs with the throttle instead of load.
            float target = grounded
                ? Mathf.Lerp(idlePitch, redlinePitch, speed01)
                : Mathf.Lerp(idlePitch * 1.15f, redlinePitch * 0.86f, RideInput.Throttle);

            if (bike.NitroActive) target *= 1.12f;
            if (bike.IsWiped) target = idlePitch * 0.7f;

            pitch = Mathf.SmoothDamp(pitch, target, ref pitchVel, pitchSmoothing,
                                     Mathf.Infinity, dt);
            engine.pitch = pitch;

            float wantVolume = bike.IsWiped ? 0.06f : (grounded ? engineVolume : airVolume);
            volume = Mathf.MoveTowards(volume, wantVolume, dt * 2.2f);
            engine.volume = volume;
        }

        void OnLanded(LandingQuality quality, float impact)
        {
            float weight = Mathf.Clamp01(impact / 18f);
            if (weight < 0.12f) return;
            oneShots.pitch = Random.Range(0.94f, 1.08f);
            oneShots.PlayOneShot(ProceduralSfx.Land, weight * landVolume);
        }

        void OnWiped()
        {
            oneShots.pitch = 1f;
            oneShots.PlayOneShot(ProceduralSfx.Wipeout, wipeoutVolume);
        }

        void OnPowerup(PickupKind kind)
        {
            oneShots.pitch = 1f;
            oneShots.PlayOneShot(
                kind == PickupKind.Nitro ? ProceduralSfx.Nitro : ProceduralSfx.Pickup,
                pickupVolume);
        }

        void OnTrickBanked(TrickAward award)
        {
            // Pitch climbs with the combo, so a run of clean landings audibly builds.
            oneShots.pitch = Mathf.Min(1f + (award.Combo - 1) * 0.09f, 1.7f);
            oneShots.PlayOneShot(ProceduralSfx.Trick, 0.45f);
        }
    }
}
