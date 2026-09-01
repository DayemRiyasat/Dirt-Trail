using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// A soft blob dropped on the ground under the bike, laid flat along the
    /// surface normal. Sounds like a detail, but it is the only thing that tells
    /// you how high you actually are on a big jump, which is exactly when you
    /// need to decide whether to keep rotating.
    /// </summary>
    public class BikeShadow : MonoBehaviour
    {
        [SerializeField] BikeController bike;
        [SerializeField] SpriteRenderer blob;

        [Tooltip("Height at which the shadow has faded out entirely.")]
        [SerializeField] float fadeHeight = 16f;

        [SerializeField] float maxScale = 1.0f;
        [SerializeField] float minScale = 0.45f;
        [SerializeField] float maxAlpha = 0.34f;
        [SerializeField] float probe = 40f;

        void Awake()
        {
            if (bike == null) bike = GetComponentInParent<BikeController>();
            if (blob == null) blob = GetComponent<SpriteRenderer>();

            if (blob != null && blob.sprite == null)
            {
                var kit = FxKit.Load();
                if (kit != null) blob.sprite = kit.shadow;
            }
        }

        void LateUpdate()
        {
            if (blob == null || bike == null) return;

            var origin = (Vector2)bike.transform.position;
            var hit = Physics2D.Raycast(origin, Vector2.down, probe, GameLayers.GroundMask);
            if (!hit)
            {
                blob.enabled = false;
                return;
            }

            blob.enabled = true;

            // Detached from the bike's rotation: the shadow belongs to the
            // ground, so it stays flat while the bike flips above it.
            float t = Mathf.Clamp01(hit.distance / fadeHeight);
            transform.SetPositionAndRotation(
                hit.point + hit.normal * 0.06f,
                Quaternion.FromToRotation(Vector3.up, hit.normal));

            float scale = Mathf.Lerp(maxScale, minScale, t);
            transform.localScale = new Vector3(scale, scale * 0.7f, 1f);

            var c = blob.color;
            c.a = Mathf.Lerp(maxAlpha, 0f, t * t);
            blob.color = c;
        }
    }
}
