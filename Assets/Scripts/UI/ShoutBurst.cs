using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// One comic burst thrown into the world above the bike. Punches in past
    /// full size, holds, then drifts up and fades.
    ///
    /// World space rather than the HUD on purpose: the shout belongs to the
    /// thing that just happened, so it should sit where that happened and be
    /// left behind as you ride away from it.
    /// </summary>
    public class ShoutBurst : MonoBehaviour
    {
        const float PunchTime = 0.14f;
        const float HoldTime = 0.55f;
        const float FadeTime = 0.45f;
        const float Overshoot = 1.16f;
        const float Rise = 1.9f;

        SpriteRenderer sprite;
        Vector3 origin;
        float born;
        float scale = 1f;
        float spin;

        /// <summary>Throws a burst at a world position. Does nothing if unavailable.</summary>
        public static void Play(Sprite art, Vector3 where, float scale = 1f,
                                int sortingOrder = 80)
        {
            if (art == null) return;

            var go = new GameObject("Shout " + art.name);
            go.transform.position = where;

            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sprite = art;
            renderer.sortingOrder = sortingOrder;

            var burst = go.AddComponent<ShoutBurst>();
            burst.sprite = renderer;
            burst.origin = where;
            burst.born = Time.time;
            burst.scale = scale;
            burst.spin = Random.Range(-7f, 7f);
            go.transform.localScale = Vector3.zero;
            go.transform.localRotation = Quaternion.Euler(0f, 0f, burst.spin);
        }

        void LateUpdate()
        {
            float age = Time.time - born;
            float total = PunchTime + HoldTime + FadeTime;
            if (age >= total)
            {
                Destroy(gameObject);
                return;
            }

            float grow;
            if (age < PunchTime)
            {
                // Overshoot and settle: the pop is what makes it read as a comic
                // panel rather than a label fading in.
                float t = age / PunchTime;
                grow = Mathf.LerpUnclamped(0f, Overshoot, 1f - (1f - t) * (1f - t));
            }
            else
            {
                float t = Mathf.Clamp01((age - PunchTime) / 0.12f);
                grow = Mathf.Lerp(Overshoot, 1f, t);
            }
            transform.localScale = Vector3.one * (grow * scale);

            float fade = age - PunchTime - HoldTime;
            if (fade > 0f)
            {
                float t = Mathf.Clamp01(fade / FadeTime);
                var c = sprite.color;
                c.a = 1f - t * t;
                sprite.color = c;
                transform.position = origin + Vector3.up * (t * Rise);
            }
        }
    }
}
