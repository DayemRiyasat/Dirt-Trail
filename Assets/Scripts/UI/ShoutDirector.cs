using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Decides when the game shouts. Listens to the run and throws a burst
    /// above the rider; keeps a short cooldown so a busy rhythm section does not
    /// stack four of them on top of each other.
    /// </summary>
    public class ShoutDirector : MonoBehaviour
    {
        [SerializeField] RunManager run;

        [Tooltip("World units above the bike the burst appears.")]
        [SerializeField] float height = 3.2f;

        [SerializeField] float spread = 1.1f;
        [SerializeField] float scale = 1f;

        [Tooltip("Shortest gap between two bursts.")]
        [SerializeField] float cooldown = 0.45f;

        float nextAllowed;

        void Awake()
        {
            if (run == null) run = FindFirstObjectByType<RunManager>();
        }

        void OnEnable()
        {
            if (run == null) return;
            run.TrickBanked += OnTrick;
            run.PickupTaken += OnPickup;
            run.Wiped += OnWiped;
        }

        void OnDisable()
        {
            if (run == null) return;
            run.TrickBanked -= OnTrick;
            run.PickupTaken -= OnPickup;
            run.Wiped -= OnWiped;
        }

        Vector3 Where()
        {
            var bike = run != null ? run.Bike : null;
            Vector3 at = bike != null ? bike.transform.position : transform.position;
            at.y += height;
            at.x += Random.Range(-spread, spread);
            at.z = 0f;
            return at;
        }

        bool Ready(bool important)
        {
            // A wipeout always gets through; routine tricks queue behind each other.
            if (!important && Time.time < nextAllowed) return false;
            nextAllowed = Time.time + cooldown;
            return true;
        }

        void OnTrick(TrickAward award)
        {
            if (!Ready(false)) return;

            // A perfect landing is the rarer thing to say, so it wins the slot.
            var art = award.Landing == LandingQuality.Perfect
                ? Shout.ForPerfect()
                : award.Rotations > 0 ? Shout.ForFlip(award.Rotations) : Shout.ForAir();

            ShoutBurst.Play(art, Where(), scale);
        }

        void OnPickup(PickupConfig config)
        {
            if (config == null || !Ready(false)) return;
            ShoutBurst.Play(Shout.ForPickup(config.kind), Where(), scale * 0.72f);
        }

        void OnWiped()
        {
            Ready(true);
            ShoutBurst.Play(Shout.ForWipeout(), Where(), scale * 1.15f);
        }
    }
}
