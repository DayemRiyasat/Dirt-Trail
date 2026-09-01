using UnityEngine;

namespace DirtTrail
{
    /// <summary>The end of the track.</summary>
    [RequireComponent(typeof(Collider2D))]
    public class FinishLine : MonoBehaviour
    {
        void Reset()
        {
            var col = GetComponent<Collider2D>();
            if (col != null) col.isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (!GameLayers.IsRider(other.gameObject.layer)) return;
            RunManager.Instance?.Finish();
        }
    }
}
