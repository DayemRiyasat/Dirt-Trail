using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Dust off the rear wheel while it is loaded, a roost of clods when you
    /// land hard, and nothing at all in the air. The prototype played or stopped
    /// an emitter on collision, so it ran flat out at walking pace and stuttered
    /// over every seam in the terrain; rate is now a function of speed.
    /// </summary>
    public class DirtSpray : MonoBehaviour
    {
        [SerializeField] BikeController bike;

        [Tooltip("Where the rear tyre meets the ground. Effects are built here.")]
        [SerializeField] Transform contact;

        [Header("Rate")]
        [Tooltip("Speed at which the dust trail reaches full rate.")]
        [SerializeField] float fullRateSpeed = 16f;

        [SerializeField] float maxDustRate = 46f;

        [Header("Landing roost")]
        [SerializeField] float minImpactForRoost = 4f;
        [SerializeField] int maxRoostClods = 24;

        ParticleSystem dust, clods, nitro;
        ParticleSystem.EmissionModule dustEmission;
        Color tint = new Color(0.78f, 0.62f, 0.42f, 1f);

        void Awake()
        {
            if (bike == null) bike = GetComponentInParent<BikeController>();
            if (contact == null) contact = transform;

            dust = ParticleFactory.Dust(contact, tint);
            clods = ParticleFactory.Clods(contact, tint);
            nitro = ParticleFactory.NitroFlare(contact);

            dustEmission = dust.emission;
            dust.Play();
            clods.Play();
        }

        void OnEnable()
        {
            if (bike == null) return;
            bike.Landed += OnLanded;
            bike.PowerupStarted += OnPowerup;
        }

        void OnDisable()
        {
            if (bike == null) return;
            bike.Landed -= OnLanded;
            bike.PowerupStarted -= OnPowerup;
        }

        /// <summary>Each bike throws its own colour of dirt.</summary>
        public void Tint(Color color)
        {
            tint = color;
            if (dust != null)
            {
                var main = dust.main;
                main.startColor = color;
            }
            if (clods != null)
            {
                var main = clods.main;
                main.startColor = color * 0.75f;
            }
        }

        void Update()
        {
            if (bike == null || dust == null) return;

            bool rolling = bike.Grounded && !bike.IsWiped;
            float speed01 = Mathf.Clamp01(Mathf.Abs(bike.ForwardSpeed) / fullRateSpeed);

            // Squared so a slow roll barely smokes and a hard drive really does.
            float rate = rolling ? speed01 * speed01 * maxDustRate : 0f;
            if (bike.NitroActive) rate *= 1.6f;
            dustEmission.rateOverTime = rate;

            if (nitro == null) return;
            bool burning = bike.NitroActive;
            if (burning && !nitro.isEmitting) nitro.Play();
            else if (!burning && nitro.isEmitting) nitro.Stop();
        }

        void OnLanded(LandingQuality quality, float impact)
        {
            if (impact < minImpactForRoost) return;
            float weight = Mathf.Clamp01((impact - minImpactForRoost) / 14f);
            clods?.Emit(Mathf.RoundToInt(weight * maxRoostClods) + 3);
            dust?.Emit(Mathf.RoundToInt(weight * 18f) + 4);
        }

        void OnPowerup(PickupKind kind)
        {
            if (kind == PickupKind.Nitro) dust?.Emit(14);
        }
    }
}
