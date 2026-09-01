using UnityEngine;

namespace DirtTrail
{
    /// <summary>Moves the restart point forward as the rider gets through a section.</summary>
    [RequireComponent(typeof(Collider2D))]
    public class Checkpoint : MonoBehaviour
    {
        [Tooltip("Which section this flag opens. Editor bookkeeping only.")]
        [SerializeField] string sectionName = "";

        [SerializeField] SpriteRenderer flag;
        [SerializeField] Color takenTint = new Color(0.85f, 0.37f, 0.15f, 1f);

        bool taken;

        void Reset()
        {
            var col = GetComponent<Collider2D>();
            if (col != null) col.isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (taken) return;
            if (!GameLayers.IsRider(other.gameObject.layer)) return;

            var run = RunManager.Instance;
            if (run == null) return;

            taken = true;
            // Respawn upright at the flag, not at whatever angle the bike was.
            run.SetRespawn(transform.position + Vector3.up * 1.2f, 0f);
            // The flag changing colour is the whole notification. Nothing is
            // written on screen: the comic bursts are the only text in a level.
            if (flag != null) flag.color = takenTint;
        }
    }
}
