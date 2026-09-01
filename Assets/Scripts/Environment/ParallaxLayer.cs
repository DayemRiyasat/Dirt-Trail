using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// One scrolling backdrop band.
    ///
    /// <c>parallax</c> is 0 for a layer locked to the world and 1 for a layer
    /// pinned to the camera, so the value reads as distance. Negative values put
    /// a layer in front of the track, which is what the foreground scrub uses.
    ///
    /// Runs in LateUpdate, after the camera has moved. The prototype ran this in
    /// FixedUpdate against a LateUpdate camera, which is why the old background
    /// shimmered whenever the framerate and the physics step disagreed.
    /// </summary>
    [ExecuteAlways]
    public class ParallaxLayer : MonoBehaviour
    {
        [Range(-0.4f, 1f)]
        [SerializeField] float parallax = 0.5f;

        [Tooltip("How much of the camera's vertical travel the layer follows. " +
                 "Independent of the horizontal value: this track drops eighty " +
                 "units, so distant layers need to track Y almost exactly or " +
                 "they slide out of frame.")]
        [Range(0f, 1f)]
        [SerializeField] float verticalParallax = 0.95f;

        [Tooltip("Leave on unless the layer is a one-off backdrop.")]
        [SerializeField] bool wrapHorizontally = true;

        [Tooltip("Width of one tile. Measured from the renderer when left at zero.")]
        [SerializeField] float tileWidth;

        Transform cam;
        Vector3 origin;
        float anchorX;

        void OnEnable()
        {
            origin = transform.position;
            anchorX = origin.x;
            if (tileWidth <= 0.01f) tileWidth = MeasureWidth();
        }

        float MeasureWidth()
        {
            var sr = GetComponent<SpriteRenderer>();
            if (sr != null) return sr.bounds.size.x;

            var child = GetComponentInChildren<SpriteRenderer>();
            return child != null ? child.bounds.size.x : 0f;
        }

        Transform Cam
        {
            get
            {
                if (cam != null) return cam;

                // Camera.main only finds a camera tagged MainCamera. An untagged
                // one leaves every layer frozen at the origin, which looks like
                // the backdrop simply running out partway along the track.
                var main = Camera.main;
                if (main == null) main = FindFirstObjectByType<Camera>();
                if (main != null) cam = main.transform;
                return cam;
            }
        }

        void LateUpdate()
        {
            var c = Cam;
            if (c == null) return;

            Vector3 camPos = c.position;
            float x = anchorX + camPos.x * parallax;
            float y = origin.y + camPos.y * verticalParallax;

            if (wrapHorizontally && tileWidth > 0.01f)
            {
                // Keep the tile centred on the camera; the wrap is invisible
                // because the art is seamless on X.
                float drift = camPos.x - x;
                if (drift > tileWidth * 0.5f) anchorX += tileWidth;
                else if (drift < -tileWidth * 0.5f) anchorX -= tileWidth;
                x = anchorX + camPos.x * parallax;
            }

            transform.position = new Vector3(x, y, origin.z);
        }
    }
}
