using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// The rider's own collider. If any part of the rider touches the ground the
    /// run is over, regardless of what the landing-angle check thought. Kept as a
    /// separate trigger so the bike can scrape a berm without ending the run.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class RiderImpact : MonoBehaviour
    {
        [SerializeField] BikeController bike;

        void Awake()
        {
            if (bike == null) bike = GetComponentInParent<BikeController>();
            var col = GetComponent<Collider2D>();
            if (col != null) col.isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (bike == null || bike.IsWiped) return;
            if (!GameLayers.IsGround(other.gameObject.layer)) return;
            bike.Wipeout();
        }
    }
}
