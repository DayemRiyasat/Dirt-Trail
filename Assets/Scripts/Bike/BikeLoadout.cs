using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Applies the bike chosen in the garage to the bike sitting in the track
    /// scene. One component so the choice enters the world at exactly one point,
    /// before anything else reads the config.
    /// </summary>
    [DefaultExecutionOrder(-200)]
    public class BikeLoadout : MonoBehaviour
    {
        [SerializeField] BikeController controller;
        [SerializeField] BikeVisuals visuals;
        [SerializeField] DirtSpray spray;

        [Tooltip("Used when no roster is found, so the scene still runs on its own.")]
        [SerializeField] BikeConfig fallback;

        void Awake()
        {
            if (controller == null) controller = GetComponent<BikeController>();
            if (visuals == null) visuals = GetComponentInChildren<BikeVisuals>();
            if (spray == null) spray = GetComponentInChildren<DirtSpray>();

            var config = BikeRoster.Selected ?? fallback;
            if (config == null)
            {
                Debug.LogWarning("BikeLoadout: no bike config available.");
                return;
            }

            controller?.Configure(config);
            visuals?.Apply(config);
            spray?.Tint(config.dust);

            Settings.Apply();
        }
    }
}
